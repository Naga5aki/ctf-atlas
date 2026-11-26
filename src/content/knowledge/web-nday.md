---
title: "Nday 利用：识别、改写、验证"
summary: "从响应头/favicon/路径/版本确定组件与版本，再检索 CVE 与 EXP；按路径、参数、编码、回连改写，最后用只读命令验证不是回显。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-spring-audit", "web-java-security", "web-waf-bypass", "web-runtime-boundary"]
updated: "2026-10-29"
---

Nday 题不考“发现新漏洞”，而考**识别 + 检索 + 改写 + 验证**。目标跑的是公开组件，EXP 网上都有，卡点通常在版本判断、路径差异、回连地址和 payload 适配。

> 只对本地题目或授权环境测试；EXP 可能破坏数据，先确认版本与影响面。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 组件 | 响应头/favicon/静态路径 | 两条证据 |
| 版本 | `?ver=`/报错/锁文件 | 决定 CVE |
| CVE | 厂商公告/NVD | 版本范围 |
| EXP | Exploit-DB/GitHub/vulhub | 看维护 |
| 入口路径 | EXP 的 base_url | 常要改 |
| 参数 | 抓包对照 | 字段名 |
| 回连 | DNS/HTTP/正向 | 看网络 |
| 验证 | 只读命令/回显 | 非回显 |
| 失败 | 版本/路径/编码 | 换点 |

## 01 原理与成立条件

```text
指纹 → 组件/版本 → CVE → EXP
                          ├─ 改路径/参数
                          ├─ 改编码/payload
                          └─ 改回连/命令
目标 → 验证 → 影响
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 组件/版本可识别 | 指纹/锁文件 | 猜/换路径 |
| CVE 版本匹配 | 公告范围 | 换 CVE |
| 入口可达 | 路径/认证 | 找路径/凭据 |
| EXP 可适配 | 参数/编码 | 手写请求 |

## 02 判断与分型

```text
先看像什么：
 ├─ Cookie rememberMe → Shiro
 ├─ JSON @type → Fastjson
 ├─ `?s=` → ThinkPHP
 ├─ `/actuator` → Spring
 ├─ 7001/console → WebLogic
 └─ `.action` → Struts2
版本怎么定？
 ├─ 响应头/报错
 ├─ 静态文件版本
 ├─ 锁文件/源码
 └─ 行为差异
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `rememberMe=deleteMe` | Shiro | 反序列化 |
| `@type` 报错 | Fastjson | 版本 |
| `X-Powered-By: ThinkPHP` | ThinkPHP | `?s=` |
| `/actuator/env` | Spring | 配置 |
| `.action` | Struts2 | OGNL |
| 7001 | WebLogic | T3 |
| 版本页 | 组件 | 查 CVE |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| favicon 相同 | 同模板/CDN | 第二证据 |
| 版本页旧 | 反代缓存 | 行为确认 |
| EXP 跑通 | 只回显 payload | 只读命令验证 |
| 端口开放 | 非目标组件 | banner |

## 03 利用阶梯

### L0 指纹与版本

**前提**：有目标 URL。

**步骤**：
1. 看 `Server`/`X-Powered-By`/Cookie/错误页。
2. favicon hash、静态资源路径、默认页。
3. 试版本路径/`?ver=`/锁文件。
4. 用 whatweb/nuclei 只作候选，逐条人工确认。

**成功标志**：组件 + 版本范围有两条证据。

**失败分支**：指纹弱→换路径/行为；版本不明→按范围试。

### L1 检索 CVE 与 EXP

**前提**：组件/版本已知。

**步骤**：
1. 厂商公告/NVD 确认版本范围与前置条件。
2. Exploit-DB/GitHub/vulhub 找可复现 EXP。
3. 选“有验证步骤、参数可改、近期维护”的。
4. 读依赖/网络/认证要求。

**成功标志**：候选 CVE 与 EXP 匹配目标。

**失败分支**：无 EXP→手写请求；版本不符→换 CVE。

### L2 改写适配

**前提**：有 EXP。

**步骤**：
1. 改 `base_url`/路径前缀/认证 Cookie。
2. 对照抓包改参数名/Content-Type。
3. 改编码/加密/payload 版本。
4. 回连不出网→DNS/HTTP 外带/正向。
5. 先跑只读命令。

**成功标志**：请求到达漏洞点并产生预期响应。

**失败分支**：路径错→扫/报错；编码错→本地对照；WAF→见 WAF 页。

### L3 验证与无回显

**前提**：EXP 已发出。

**步骤**：
1. 只读命令 `id`/`echo`，确认不是页面回显。
2. 无回显：写 Web 目录/外带/时间。
3. 记录请求/响应/时间，三次复现。
4. 失败换版本/路径/编码，不重复同一 payload。

**成功标志**：命令/文件/请求证据稳定。

**失败分支**：只回显→换利用点；无出网→时间/文件。

### L4 组合与限制

**前提**：单点 EXP 不够。

**步骤**：
1. 组件链：Shiro→CC、Fastjson→JNDI、Log4j→LDAP。
2. 版本限制：JDK/依赖/补丁，换本地工厂/链。
3. 权限限制：Web 用户→提权/横向。
4. 只验证到读文件/固定回显。

**成功标志**：在限制下拿到目标数据。

**失败分支**：链断→回 L1；版本已修→换 CVE。

## 04 绕过与边界

| 差异 | 处理 |
|---|---|
| 路径不同 | 改 base_url/前缀 |
| 版本不同 | 换 payload/编码 |
| 回连不出网 | DNS/HTTP/正向 |
| 参数名不同 | 抓包对照 |
| 需要认证 | 加 Cookie/Token |
| WAF | 编码/分块/换协议 |

边界：EXP 可能写文件/改配置；版本页可能被缓存；回显 payload 不等于执行；组件指纹需第二证据；只在授权环境跑。

## 05 非典型入口

| 组件 | 类型 | 识别 |
|---|---|---|
| ThinkPHP 5.x | RCE | `?s=` |
| Shiro | 反序列化 | `rememberMe` |
| Fastjson | 反序列化 | `@type` |
| Log4j2 | JNDI | `${jndi:` |
| Spring | Actuator/SpEL | `/actuator` |
| Confluence | OGNL | `/pages/` |
| WebLogic | T3 | 7001 |
| Struts2 | OGNL | `.action` |
| Jenkins | 脚本 | `/script` |
| Redis | 未授权 | 6379 |

## 06 差异速查

| 组件 | 版本边界 | 注意 |
|---|---|---|
| Shiro | 默认密钥 | 反序列化 |
| Fastjson | 1.2.24-1.2.68 | autoType |
| Log4j2 | 2.0-2.14.1 | JNDI |
| Spring | 5.3/5.2 | Spring4Shell |
| WebLogic | 多版本 | T3/IIOP |
| Struts2 | 2.x | OGNL |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 指纹 | whatweb/nuclei |
| EXP | searchsploit/vulhub |
| 回连 | DNSLog/HTTP |
| 验证 | 只读命令 |
| 记录 | 组件/版本/CVE/请求 |

验证顺序：指纹 → CVE → EXP → 改写 → 验证。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 指纹 | 头/路径/版本 | 组件 |
| 2 检索 | 公告/EXP | CVE |
| 3 改写 | 路径/参数/编码 | 请求 |
| 4 验证 | 只读命令 | 证据 |
| 5 扩展 | 链/权限 | 影响 |
| 6 记录 | 请求/结果 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 版本不匹配 | 指纹/缓存 | 行为确认 |
| 路径 404 | 前缀/认证 | 改 base_url |
| EXP 报错 | 依赖/参数 | 读代码 |
| 只回显 | 未执行 | 换利用点 |
| 无回连 | 出网 | DNS/正向 |
| WAF | 规则 | 编码/降速 |
| 链断 | 版本/依赖 | 换 CVE |

## 10 记录与复现

- [ ] 组件/版本/证据
- [ ] CVE/公告
- [ ] EXP 来源/改动
- [ ] 请求/响应
- [ ] 验证方式
- [ ] 影响/限制

| 记录项 | 内容 |
|---|---|
| 组件 | 名称/版本 |
| 漏洞 | CVE/类型 |
| EXP | 来源/改动 |
| 验证 | 请求/回显 |
| 影响 | 命令/文件/权限 |

相关： [Spring 审计](/knowledge/web-spring-audit/)、[Java 安全](/knowledge/web-java-security/)、[WAF 绕过](/knowledge/web-waf-bypass/)、[命令执行与反序列化](/knowledge/web-runtime-boundary/)。
