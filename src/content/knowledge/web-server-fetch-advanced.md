---
title: "SSRF 与 XXE 进阶：协议、内网与盲打"
summary: "从“能请求”推进到 gopher 打 Redis/FastCGI、云元数据、DNS 重绑定；XXE 从回显读取推进到参数实体、OOB 与错误外带。"
module: Web
topic: "Web漏洞"
tags: ["流量"]
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-server-fetch", "web-cloud-container", "web-path-tricks", "web-parser-gap"]
updated: "2026-10-29"
---

基础的回显读取见 [SSRF 与 XXE](/knowledge/web-server-fetch/)。这一页只处理三类“看到了请求但拿不到结果”的场景：协议不对、目标只在内网、回显被关。

> 只对本地题目或授权环境发起内网请求；元数据与 Redis/FastCGI 利用会改变目标状态，先确认范围。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 确认出网 | 自建接收端 | Host/来源 IP |
| 绕 IP 黑名单 | 十进制/八进制/IPv6/短写 | 解析后比较 |
| 绕域名白名单 | `@`/`#`/302/再绑定 | 看校验时机 |
| 打 Redis | `gopher://` + RESP | 写文件/主从 |
| 打 FastCGI | `gopher://` + FCGI | 9000/Unix socket |
| 云凭证 | `169.254.169.254`/`100.100.100.200` | 看云厂商 |
| 盲 XXE | 参数实体 + 外部 DTD | 看接收端 |
| 无外带 | 错误回显/时间 | 非法 URL |
| 读源码 | `php://filter` | 实体里用 |

## 01 原理与成立条件

```text
SSRF：URL → 校验 → DNS → 连接 → 重定向
                         ├─ 内网服务
                         └─ 元数据/Redis/FPM
XXE：XML → DTD → 实体 → 取资源
                       ├─ 回显
                       └─ OOB/错误
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 可控 URL/XML | 参数进入客户端 | 找其他入口 |
| 可出网/达内网 | ACL/网络位置 | 打本机 |
| 协议可用 | curl/gopher/file | 换客户端 |
| 有通道 | 回显/OOB/错误/时间 | 建通道 |

## 02 判断与分型

```text
有回显吗？
 ├─ 有 → 直接读
 └─ 无
     ├─ 能自定义协议 → gopher
     ├─ 只能 HTTP → 内网探测/元数据
     └─ XML → OOB/错误
校验在哪？
 ├─ 字符串 → @/IP 变形
 ├─ DNS 后 → 再绑定
 └─ 只查初始 URL → 302
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 接收端收到请求 | 出网成立 | 打内网 |
| 302 被跟 | 可绕白名单 | 跳内网 |
| `gopher://` 报错 | 协议可用/构造错 | 修长度 |
| Redis 返回 `+OK` | 可写 | 写文件/主从 |
| FPM 返回 PHP 输出 | 可执行 | 读源码 |
| 元数据 200 | 云环境 | 取凭证 |
| DTD 外带收到 | 盲 XXE | 读文件 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 目标超时 | ACL/端口 | 换目标 |
| `gopher` 无响应 | 协议未编译 | 换客户端 |
| Redis 写失败 | 权限/目录 | 换目录 |
| 元数据 401 | 需 token/头 | IMDSv2/自定义头 |
| 盲 XXE 无请求 | DTD 禁 | 换解析器 |

## 03 利用阶梯

### L0 确认出网与协议

**前提**：有 SSRF/XXE 入口。

**步骤**：
1. 自建 HTTP/DNS 接收端，确认请求到达。
2. 试 `http/https/file/dict/gopher`。
3. 看客户端库/编译选项。
4. 测是否跟随 302。

**成功标志**：知道能出网、能用哪些协议。

**失败分支**：无出网→打本机；协议少→换入口/换客户端。

### L1 内网与云元数据

**前提**：能发 HTTP。

**步骤**：
1. 扫本机/内网常见端口。
2. 云元数据：AWS `169.254.169.254`、阿里云 `100.100.100.200`、腾讯云 `169.254.0.23`、GCP/Azure 需特定头。
3. AWS IMDSv2：先 `PUT /latest/api/token` 取 token。
4. 用临时凭证调 STS 验证。

**成功标志**：读到元数据/凭证。

**失败分支**：需头→找能自定义头的入口；IMDSv2→先取 token。

### L2 gopher 打 Redis

**前提**：`gopher://` 可用，内网 Redis 未授权/弱口令。

**步骤**：
1. 用 Gopherus 生成 RESP。
2. 清理当前库 → `set` 写 payload → `config set dir` → `config set dbfilename` → `save`。
3. 写 Web 目录/ cron/SSH key，或主从加载模块。
4. 长度声明必须与字节一致。

**成功标志**：文件写入/命令执行/数据读取。

**失败分支**：权限不足→换目录；有密码→先 `AUTH`；保护模式→从本机连。

### L3 gopher 打 FastCGI

**前提**：PHP-FPM 监听 9000/Unix socket，`gopher` 可用。

**步骤**：
1. 确认 `SCRIPT_FILENAME` 存在的 `.php`。
2. 设 `PHP_VALUE=auto_prepend_file=php://input`、`PHP_ADMIN_VALUE=allow_url_include=On`。
3. POST body 放 PHP 代码。
4. 用 Gopherus 生成 FCGI 记录，避免长度错位。

**成功标志**：PHP 代码执行。

**失败分支**：`allow_url_include=Off`→`data://`/临时文件；端口不同→读 FPM 配置。

### L4 盲 XXE 与解析差异

**前提**：XML 解析但无回显，或校验严格。

**步骤**：
1. 参数实体 + 外部 DTD 外带。
2. 文件含特殊字符→先 base64。
3. 无外带→把内容拼进非法 URL，看报错。
4. SSRF 校验：`@`、IP 变形、302、DNS 再绑定。

**成功标志**：外带/报错带出内容，或绕过校验。

**失败分支**：DTD 禁用→内部实体/换入口；无 DNS→HTTP 外带。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| IP 黑名单 | 十进制/八进制/IPv6 | `2130706433`、`[::1]` |
| 域名白名单 | `expected.com.evil.com` | 字符串校验 |
| 只查初始 URL | 302 | 跳内网 |
| 只查一次 DNS | 再绑定 | 短 TTL |
| 禁 `gopher` | `dict`/`file` | 看库 |
| DTD 禁用 | 内部实体/其他解析器 | 换入口 |
| 外带被禁 | 错误/时间 | 非法 URL |

边界：`requests` 无 gopher；PHP curl 协议看编译；元数据需特定头/方法；Redis 写文件受运行用户权限限制；XXE 参数实体只能在 DTD 内。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 图片抓取 | `url=` | 常见 |
| Webhook | 回调 | 盲打 |
| PDF 渲染 | HTML→PDF | 内网 |
| 代理下载 | `file=` | 协议 |
| SOAP/RSS | XML | XXE |
| docx/xlsx | 解压后 XML | XXE |
| 云函数 | 元数据 | 凭证 |

## 06 差异速查

| 云 | 地址 | 头/方法 |
|---|---|---|
| AWS | `169.254.169.254` | IMDSv2 token |
| 阿里云 | `100.100.100.200` | 无 |
| 腾讯云 | `169.254.0.23` | 无 |
| GCP | `metadata.google.internal` | `Metadata-Flavor: Google` |
| Azure | `169.254.169.254` | `Metadata: true` |

| 客户端 | gopher | file |
|---|---|---|
| PHP curl | 常见 | 常见 |
| Python requests | 否 | 否 |
| Java URL | 看 handler | 看 JDK |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| gopher | Gopherus |
| Redis | redis-cli（授权） |
| 元数据 | curl + 头 |
| XXE | 手工 XML/外部 DTD |
| 接收端 | 自建 HTTP/DNS |
| 记录 | URL/响应/日志 |

验证顺序：出网 → 协议 → 内网 → 利用 → 盲打。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | URL/XML | 可控点 |
| 2 出网 | 接收端 | 协议 |
| 3 目标 | 内网/云 | 可达 |
| 4 利用 | gopher/元数据 | 数据/执行 |
| 5 盲打 | OOB/错误 | 内容 |
| 6 记录 | 请求/结果 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 接收端无请求 | 未进客户端 | 换入口 |
| gopher 无响应 | 协议/长度 | 换客户端/修 RESP |
| Redis 写失败 | 权限/目录 | 换目录 |
| FPM 无输出 | 路径/配置 | 修 `SCRIPT_FILENAME` |
| 元数据 401 | 头/token | IMDSv2/自定义头 |
| 盲 XXE 无外带 | DTD/出网 | 错误/换通道 |
| 302 不跟 | 客户端 | 换跳转 |

## 10 记录与复现

- [ ] 入口与客户端
- [ ] 协议与最终 URL
- [ ] 内网/云目标
- [ ] 利用链（Redis/FPM）
- [ ] 盲打通道
- [ ] 限制与绕过

| 记录项 | 内容 |
|---|---|
| 入口 | URL/XML |
| 协议 | http/gopher/file |
| 目标 | 内网/元数据 |
| 链 | Redis/FPM/XXE |
| 通道 | 回显/OOB/错误 |

相关： [SSRF 与 XXE 基础](/knowledge/web-server-fetch/)、[云与容器](/knowledge/web-cloud-container/)、[路径与文件读取](/knowledge/web-path-tricks/)、[缓存与解析差异](/knowledge/web-parser-gap/)。
