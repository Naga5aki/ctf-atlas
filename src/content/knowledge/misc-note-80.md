---
title: "WinRM 流量分析"
summary: "WinRM（Windows Remote Management）是 Windows 的远程管理服务，可远程执行命令、PowerShell、查询系统信息和管理服务器。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、WinRM 基础与流量识别

### 1. WinRM 是什么

WinRM（Windows Remote Management）是 Windows 的远程管理服务，可远程执行命令、PowerShell、查询系统信息和管理服务器。

PowerShell 的 Enter-PSSession、Invoke-Command 以及 Python 的 pywinrm 都通过 WinRM 通信。

**协议栈：**

TCP → HTTP → WS-Man（WS-Management，基于 SOAP）→ WinRM → PowerShell / CMD

### 2. 两个核心端口

| 端口 | 协议 | 含义 |
| --- | --- | --- |
| TCP 5985 | HTTP | WinRM HTTP |
| TCP 5986 | HTTPS | WinRM HTTPS |

看到 TCP 5985 + POST /wsman 要立刻想到 WinRM / WS-Management。/wsman 基本就是 WinRM 服务入口，典型请求头：

POST /wsman HTTP/1.1

Host: 192.168.162.144:5985

Content-Type: application/soap+xml

### 3. Python WinRM client 特征

User-Agent: Python WinRM client 通常说明客户端使用 pywinrm 库。端口 + URI+User-Agent 组合是很强的 WinRM 特征，但 User-Agent 可人为修改，最可靠还是结合端口、URI、认证过程和 WS-Man SOAP 判断。

## 二、认证机制：401、Negotiate 与 NTLM

### 1. 大量 401 是正常现象

NTLM/Negotiate 需要挑战 — 响应过程，401 不代表登录失败：

客户端 POST /wsman + Authorization: Negotiate Type1 → 服务器

服务器 HTTP 401 + WWW-Authenticate: Negotiate Type2 → 客户端

客户端 POST /wsman + Authorization: Negotiate Type3 → 服务器

服务器 HTTP 200 → 客户端

### 2. Negotiate = SPNEGO

Negotiate 不是具体密码算法，而是通过 SPNEGO 协商使用 Kerberos 还是 NTLM：

Negotiate / SPNEGO

├─ Kerberos

└─ NTLM

过滤 ntlmssp 能看到 NTLMSSP_NEGOTIATE、NTLMSSP_CHALLENGE、NTLMSSP_AUTH，则确定实际使用 NTLM。

### 3. Base64 认证 Token

Authorization: Negotiate TlRMTVNTUA... 中 TlRMTVNTUA 是 Base64 编码后的认证 Token，解码后开头是 NTLMSSP。Wireshark 通常已自动解析，不一定需手动解码。

### 4. 与 SMB NTLM 的关系

WinRM 中的 NTLM 仍是 Type 1/2/3，和 SMB NTLM 是同一认证体系，区别只在承载协议：

SMB → Session Setup → Security Blob → SPNEGO → NTLMSSP

HTTP → Authorization/WWW-Authenticate: Negotiate → SPNEGO → NTLMSSP

学过 NTLM 后不需要重新学 WinRM 的 NTLM 算法。

## 三、NT Hash 与 Net-NTLMv2 的关键区分

### 1. Mimikatz mz.log 中的 NTLM = NT Hash

截图中 mz.log 类似 Mimikatz 输出：

User Name : admin

Domain    : DESKTOP-...

NTLM      : 209c...

这里的 NTLM 字段更准确说是 Windows NT Hash：

NT Hash = MD4(UTF-16LE(password))

通常 16 字节 = 32 个十六进制字符，Hashcat 模式 -m 1000。

| 数据 | 来源 | 格式 | Hashcat |
| --- | --- | --- | --- |
| NT Hash | Mimikatz/LSASS/SAM | 32 hex | -m 1000 |
| Net-NTLMv2 | 网络抓包 | user::domain:challenge:proof:blob | -m 5600 |

### 2. 与 Net-NTLMv2 不是一回事

这是 WinRM 题里非常重要的区分，不能混淆。

## 四、消息级加密与会话密钥派生

### 1. 5985 HTTP 不等于业务明文

WinRM 即使运行在普通 HTTP（5985）上，也可通过 NTLM/Kerberos 提供 Message Encryption（应用层消息级加密）：

HTTP 明文头

↓

WinRM / WS-Man

↓

NTLM Session Security

↓

加密后的 SOAP 内容

因此可能明明看到 POST /wsman、User-Agent、Authorization、HTTP 200，却看不到实际执行了什么 PowerShell，因为 SOAP Body 已被保护。

### 2. 5985 与 5986 要分开

| 端口 | 外层 | 说明 |
| --- | --- | --- |
| 5985 | HTTP | 可能存在 NTLM/Kerberos 消息加密，获得认证密钥材料有机会恢复 |
| 5986 | HTTPS/TLS | 最外层已被 TLS 加密，仅拥有 NT Hash 不能直接解密 TLS |

图中方法主要针对 5985 + NTLM + WinRM Message Encryption，不是所有 WinRM。

### 3. NT Hash 如何恢复会话密钥

这是最核心的密码学考点。NTLMv2 派生链：

Password → NT Hash → 结合 Username+Domain → NTLMv2 Key

→ 结合 Server Challenge + NTLMv2 Blob → NTProofStr

→ SessionBaseKey → Session Key → Signing Key / Sealing Key

最后的 Signing Key / Sealing Key 用于保护会话。

**如果拥有：**

① 完整 NTLM 认证流量

② 正确 Username/Domain

③ Server Challenge

④ NTLMv2 Response

⑤ 用户 NT Hash

就可按 NTLMv2 算法重新计算 SessionBaseKey → Session Key → Signing/Sealing Key，从而恢复 NTLM 消息级保护的数据。

### 4. CTF-NETA 等工具在干什么

**这类工具本质是自动化：** 识别 WinRM → 提取 NTLM Type1/2/3 → 得到 Username/Domain/ServerChallenge/NTLMv2 Response → 结合已知 NT Hash → 计算 NTLM Session Key → 计算 Signing/Sealing Key → 解密 WinRM Message Encryption → 恢复 SOAP → 提取命令和结果。

CTF-NETA 不是把 NT Hash"直接拿来当 AES 密钥解密"，而是利用 NTLM 标准密钥派生过程恢复会话密钥。换一个工具，底层分析逻辑仍然一样。

## 五、解密后内容分析

### 1. 重点找什么

解开 WinRM 数据后，重点不是所有 XML，而是：

Command / CommandLine / Arguments：可能出现 cmd.exe、powershell.exe、whoami、ipconfig、type flag.txt

PowerShell EncodedCommand：常见 powershell.exe -EncodedCommand AAAA...，通常是 PowerShell 脚本 → UTF-16LE → Base64，需 Base64 Decode → UTF-16LE Decode 恢复

**Stream：** 返回结果经常位于 <rsp:Stream Name="stdout">...</rsp:Stream>，内容可能又经 Base64，需解码恢复 stdout/stderr

### 2. 典型命令执行流程

Create Shell → Command → Receive → stdout/stderr → Command → Receive → Delete Shell

分析时不要只找一条 POST，应把整个 tcp.stream 连起来看。

### 3. 为什么常和 PowerShell 一起出现

WinRM 是 PowerShell Remoting 的重要传输基础：

PowerShell Remoting → PSRP（PowerShell Remoting Protocol）→ WS-Man → WinRM → HTTP 5985

看到 5985、/wsman、PowerShell、Python WinRM client，通常意味着题目重点是远程命令执行记录。pywinrm 中常有 Session(...)、run_cmd(...)、run_ps(...)，题目可能模拟 Python 脚本连接 Windows 远程执行命令，最终让你找执行了什么命令、下载了什么文件、密码或 Flag。

## 六、Wireshark 实战与标准解题流程

### 1. 常用过滤器

| 目的 | 过滤表达式 |
| --- | --- |
| 找 WinRM 端口 | tcp.port == 5985 或 tcp.port == 5986 |
| 找 /wsman | http.request.uri == "/wsman" |
| 找 Python WinRM | http.user_agent contains "WinRM" |
| 找 NTLM | ntlmssp |
| 找认证挑战 | http.response.code == 401 |
| 找成功会话 | http.response.code == 200 |

### 2. 为什么找 HTTP 200 和追踪 TCP 流

401 是认证协商阶段，往后找到 200 OK 说明某个 WS-Man 请求已被服务器正常接受处理，可锁定成功的 WinRM 会话对应 tcp.stream（HTTP 200 不等于一定完成远程命令执行，具体还需看 SOAP 响应）。

找到 POST /wsman 后右键 → 追踪 → TCP 流，可把同一 TCP 会话按时间连续显示，容易看到 POST /wsman → 401 Negotiate → POST /wsman → 200 → POST /wsman → SOAP/encrypted data → Response，比逐包看方便。

### 3. 标准解题流程

xxx.pcapng

↓

tcp.port == 5985 → http.request.uri == "/wsman"

↓

检查 POST /wsman、Host、User-Agent

↓

ntlmssp → 确认 Type1/2/3

↓

http.response.code == 401（看挑战）→ 200（找成功会话）

↓

右键追踪 TCP 流

↓

若业务数据加密，检查题目是否提供 NT Hash/密码/Mimikatz日志/LSASS结果

↓

NT Hash + PCAP 中 NTLM 认证 → WinRM 消息解密工具 → SOAP

↓

搜索 Command、PowerShell、EncodedCommand、Stream、stdout、stderr、flag、password

### 4. 最常见完整链条

PCAP → tcp.port==5985 → POST /wsman → User-Agent: Python WinRM client

→ HTTP 401 + Negotiate → NTLMSSP Type1/2/3 → HTTP 200

→ 锁定成功 WinRM 会话 → 业务数据受 NTLM Message Encryption 保护

→ 从题目其他证据获得目标用户 NT Hash

→ 根据 NTLM 认证数据派生 Session Key → 恢复 Signing/Sealing Key

→ 解密 WinRM → 恢复 WS-Man SOAP → 找到远程命令

→ 解码 EncodedCommand / Stream → 获得 Flag

### 5. 多证据关联题设计

**题目常设计为：** 第一阶段从其他证据获得 mz.log（Mimikatz 输出）→ 找到目标用户 NT Hash；第二阶段分析 WinRM PCAP → 识别 NTLM 会话；第三阶段 NT Hash + NTLM 认证数据 → 恢复 NTLM Session Key；第四阶段解密 WinRM → 恢复远程命令 / 数据。这是典型的多证据关联题。
