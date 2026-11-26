# ctf-atlas Web 模块组成方案（升级后）

升级后 Web 模块共 **52 个知识点页面**：站内原有 17 个 + 本次新增/增强 35 个（SQL 基础页与进阶页已合并）。按 8 个分类组织，每个分类内“基础 → 进阶 → 实战”排序。

## 一、分类总览

| 分类 | 页面数 | 定位 |
|---|---:|---|
| 协议、环境与工具 | 5 | 报文、抓包、脚本、容器与本地环境 |
| 信息收集与源码 | 5 | 泄露、指纹、JS、源码与审计入口 |
| 注入与执行 | 15 | SQL/NoSQL、命令/代码、文件、反序列化、模板、SSRF/XXE |
| 客户端与浏览器 | 6 | XSS、CSRF、XS-Leaks、缓存、原型链 |
| 认证、会话与逻辑 | 4 | 越权、业务逻辑、并发、JWT |
| 语言与框架 | 5 | PHP/Java/JS/Python 与框架审计 |
| 协议层与高级 | 4 | 走私、WAF、密码学应用、解析差异 |
| 云、内网与实战 | 8 | 云容器、流程、内网、多层、域、Pwn、Nday、AWD |
| **合计** | **52** | |

## 二、分类明细

### 1. 协议、环境与工具（5）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 1 | `web-http-message` | HTTP 报文：请求、响应与状态 | 原有 |
| 2 | `web-burp` | Burp：代理、重放与批量对照 | 原有 |
| 3 | `web-local-lab` | 实验环境：附件、容器与网络隔离 | 原有 |
| 4 | `web-python-script` | Python 脚本：从基线请求到盲注采集 | 新增 |
| 5 | `web-docker-lab` | Docker 与虚拟网络：单点复现到多网段 | 新增 |

### 2. 信息收集与源码（5）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 6 | `web-leak-files` | 源码与元数据泄露：从单文件到还原 | 新增 |
| 7 | `web-js-reverse` | JS 逆向：从请求反推签名 | 新增 |
| 8 | `web-info` | 敏感信息与指纹：先被动再主动 | 原有 |
| 9 | `git-history` | Git/SVN 泄露：从元数据到历史 | 原有 |
| 10 | `web-source-route` | 代码审计：路由表与数据流 | 原有 |

### 3. 注入与执行（15）

**SQL / NoSQL**

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 11 | `web-data-query` | SQL 注入：从原理到实战 | 原有增强 |
| 13 | `web-nosql` | NoSQL 注入：MongoDB 操作符与盲注 | 新增 |

> 原 `order 12`（SQL 注入进阶）已合并至 `web-data-query`，该编号留空不复用。

**命令、代码与反序列化**

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 14 | `web-runtime-boundary` | 命令执行与反序列化：先分清哪一层 | 原有 |
| 15 | `web-rce-bypass` | RCE 绕过与利用链 | 新增 |
| 16 | `web-php-features` | PHP 特性与绕过 | 新增 |
| 17 | `web-php-unserialize` | PHP 反序列化：格式、POP 链与 phar | 新增 |
| 18 | `web-python-security` | Python 应用安全：pickle、沙箱与 Flask | 新增 |

**文件、上传与包含**

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 19 | `web-file-boundary` | 文件上传与包含：从校验层到解析层 | 原有 |
| 20 | `web-upload-bypass` | 文件上传绕过：校验层与解析链 | 新增 |
| 21 | `web-path-tricks` | 路径与文件读取：从穿越到下一跳 | 新增 |
| 22 | `web-file-include` | 文件包含：LFI、RFI 与代码执行 | 新增 |

**模板、SSRF 与 XXE**

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 23 | `web-template-injection` | 模板注入：引擎识别与对象链 | 原有 |
| 24 | `web-ssti-python` | SSTI 模板注入：探测与利用链 | 新增 |
| 25 | `web-server-fetch` | SSRF 与 XXE：让服务器替你取资源 | 原有 |
| 26 | `web-server-fetch-advanced` | SSRF 与 XXE 进阶：协议、内网与盲打 | 新增 |

### 4. 客户端与浏览器（6）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 27 | `web-browser-output` | XSS 基础：类型、输出与影响验证 | 原有 |
| 28 | `web-xss-vectors` | XSS：上下文与向量选择 | 新增 |
| 29 | `web-csrf` | CSRF：借用身份的请求 | 新增 |
| 30 | `web-xs-leaks` | XS-Leaks：侧信道读跨站状态 | 新增 |
| 31 | `web-cache-poisoning` | 缓存投毒与缓存欺骗 | 新增 |
| 32 | `web-prototype-pollution` | 原型链污染：从 __proto__ 到 RCE | 新增 |

### 5. 认证、会话与逻辑（4）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 33 | `web-request-auth` | 越权与访问控制：三组身份对照 | 原有 |
| 34 | `web-logic` | 业务逻辑漏洞：金额、步骤与次数 | 原有 |
| 35 | `web-session-jwt` | 会话与 JWT：固定、伪造与校验缺口 | 新增 |
| 36 | `web-race-logic` | 业务并发：把一次成功变成多次 | 新增 |

### 6. 语言与框架（5）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 37 | `web-language-reading` | PHP、Java、Python：读源码的三种规则 | 原有 |
| 38 | `web-java-security` | Java 安全：反序列化与 JNDI | 新增 |
| 39 | `web-spring-audit` | Spring 与 Java 代码审计 | 新增 |
| 40 | `web-js-sandbox` | JS 沙箱逃逸：vm、vm2 与宿主对象 | 新增 |
| 41 | `web-php-audit` | PHP 代码审计：从入口追到 sink | 新增 |

### 7. 协议层与高级（4）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 42 | `web-parser-gap` | 缓存与解析差异：同一字节的不同理解 | 原有 |
| 43 | `web-http-smuggling` | HTTP 请求走私：CL、TE 与代理链 | 新增 |
| 44 | `web-waf-bypass` | WAF 绕过：先定位拦截层 | 新增 |
| 45 | `web-crypto-app` | 密码学应用题：分组模式与随机数 | 增强替换 |

### 8. 云、内网与实战（8）

| order | 页面 | 标题 | 来源 |
|---:|---|---|---|
| 46 | `web-cloud-container` | 云与容器：从元数据到宿主边界 | 新增 |
| 47 | `web-pentest-flow` | 渗透流程与立足点 | 新增 |
| 48 | `web-internal-recon` | 内网信息收集与代理隧道 | 新增 |
| 49 | `web-layer-practice` | 多层网络实战：路由、SOCKS 与级联 | 新增 |
| 50 | `web-ad-lateral` | 域渗透与横向移动 | 新增 |
| 51 | `web-pwn-combo` | Web 与 Pwn 组合题 | 新增 |
| 52 | `web-nday` | Nday 利用：识别、改写、验证 | 新增 |
| 53 | `web-awd-practice` | AWD 攻防：开局、打点与止损 | 新增 |

## 三、学习路径建议

1. **入门**：HTTP → Burp → 实验环境 → 敏感信息 → Git 泄露。
2. **单点漏洞**：SQL/NoSQL → 命令执行 → 文件上传/包含 → XSS/CSRF → 模板/SSRF/XXE。
3. **进阶**：反序列化（PHP/Python/Java）→ 框架审计 → 走私/WAF/密码学 → 缓存/原型链/XS-Leaks。
4. **实战**：Docker/虚拟机 → 内网/多层/域 → Nday/AWD/Pwn 组合。

## 四、模块页 `/module/web/` 建议结构

- 顶部：模块简介 + “本模块只用于本地题目或授权环境”的边界说明。
- 01 学习路径：按上面四阶段给 6–8 个入口链接。
- 02 知识地图：8 个分类卡片，显示页面数与代表页面。
- 03 按分类浏览：8 个 `<section>`，每节内按 order 列页面，卡片显示 title + summary + tags。
- 04 实战路线：`/knowledge/web-pentest-flow/`、`/knowledge/web-layer-practice/`、`/knowledge/web-awd-practice/`。
- 05 工具与题目：`/tools/?module=Web`、`/challenges/?module=Web`。

## 五、工具索引建议（`/tools/?module=Web`）

| 工具 | 用途 | 关联页面 |
|---|---|---|
| Burp Suite | 抓包/改包/重放/爆破 | `web-burp`、`web-http-message` |
| sqlmap | SQL 注入检测与利用 | `web-data-query` |
| hashcat / john | 哈希与 JWT 爆破 | `web-session-jwt`、`web-crypto-app` |
| jwt_tool / flask-unsign | JWT/Flask session | `web-session-jwt`、`web-python-security` |
| ysoserial / phpggc | 反序列化链生成 | `web-java-security`、`web-php-unserialize` |
| Gopherus | gopher 构造 | `web-server-fetch-advanced` |
| fscan / nmap / proxychains | 内网扫描与代理 | `web-internal-recon`、`web-layer-practice` |
| frp / nps / chisel | 隧道 | `web-internal-recon` |
| mimikatz / impacket | 域与横向 | `web-ad-lateral` |
| docker / vulhub | 环境复现 | `web-docker-lab` |

## 六、写作与边界

- 每页统一 `00 速查 → 01 原理与成立条件 → 02 判断与分型 → 03 利用阶梯（L0–L4）→ 04 绕过与边界 → 05 非典型入口 → 06 差异速查 → 07 工具与验证 → 08 实战流程 → 09 失败分支 → 10 记录与复现 → 相关` 结构。
- 不写“防御/修复/训练与记录”独立章节，不写结构解释或题目 walkthrough。
- 命令与 payload 均标注“仅本地题目/授权环境”。
- 未验证的版本差异标注为“需本地验证”，不写成确定结论。
- 不收录具体题目的完整 walkthrough；只保留可迁移的知识点与工具用法。
