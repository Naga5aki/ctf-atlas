---
title: "NTLMv2 流量分析"
summary: "典型题目给 secret.pcap/secret.pcapng，Wireshark 中看到 SMB/SMB2、HTTP、SMTP、LDAP 等协议里存在 NTLMS…"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、题型定位与核心概念

典型题目给 secret.pcap/secret.pcapng，Wireshark 中看到 SMB/SMB2、HTTP、SMTP、LDAP 等协议里存在 NTLMSSP 认证过程。

**核心解题链：**

PCAP → 定位 NTLMSSP → 找 Type 2 Challenge → 提取 Server Challenge

→ 找 Type 3 Authentication → 提取 Username/Domain/NTProofStr/Blob

→ 组合成 Net-NTLMv2 格式 → hashcat -m 5600 → 恢复候选密码

它不是从流量中直接提取 "用户的 NT Hash"，而是提取 Net-NTLMv2 Challenge/Response 数据，再利用候选密码离线计算响应与抓包比较。

三个易混淆概念（最重要基础）

| 名称 | 本质 | 来源 | Hashcat |
| --- | --- | --- | --- |
| NT Hash / NTLM Hash | Windows 本地口令派生哈希 | SAM、LSASS、NTDS.dit | -m 1000 |
| Net-NTLMv1 | NTLMv1 网络认证 Challenge/Response | 网络流量 | -m 5500 |
| Net-NTLMv2 | NTLMv2 网络认证 Challenge/Response | 网络流量 | -m 5600 |

**密码派生：** Password → UTF-16LE → MD4 → NT Hash，然后 NTLMv2 再利用 NT Hash 派生认证密钥。NT Hash ≠ Net-NTLMv2，截图中 "提取 NTLMv2 哈希" 更准确叫提取 Net-NTLMv2 Challenge/Response。

## 二、NTLM 认证机制与承载协议

NTLM 不是独立传输协议

NTLM 本质是 Windows 挑战 — 响应认证机制，嵌套在其他协议中：

SMB → SPNEGO → NTLMSSP

HTTP → Authorization: NTLM ...

SMTP → AUTH NTLM

还可能出现在 LDAP、RPC、IMAP、POP3

CTF 中不能只看 Protocol=SMB2 就认为没有 NTLM，真正要找的是 NTLMSSP。Wireshark 过滤器：ntlmssp。

Type 1 / 2 / 3 消息

客户端 → Type 1 NEGOTIATE → 服务器

服务器 → Type 2 CHALLENGE → 客户端

客户端 → Type 3 AUTHENTICATE → 服务器

| 消息 | 方向 | 作用 | CTF重点 |
| --- | --- | --- | --- |
| Type 1 NEGOTIATE | C→S | 协商 NTLM 功能、能力和 Flags | 一般非重点 |
| Type 2 CHALLENGE | S→C | 发出挑战 | Server Challenge |
| Type 3 AUTHENTICATE | C→S | 提交身份和响应 | Username、Domain、NTLMv2 Response |

**口诀：** Type 2 找 Challenge，Type 3 找身份和 Response。Type 1 不只是 "确认协议版本"，而是协商功能、能力和 Flags。

## 三、Type 2/3 关键字段与 NTLMv2 计算原理

Type 2：Server Challenge

核心字段 Server Challenge 是 8 字节（64 bit）随机质询值，转十六进制是 16 个字符，如 9a88373dbb4f5e36。

⚠️ 不是 16 字节，准确是 8 bytes = 64 bits = 16 hex characters。

Type 3：Authenticate

包含 Domain Name、User Name、Workstation、LM Response、NT Response 等。CTF 分析 NTLMv2 最重要的是 Username、Domain、NTLMv2 Response。SMB 中常见于 SMB2 Session Setup Request → Security Blob → NTLMSSP → NTLMSSP_AUTH。

NTLMv2 计算原理

① NT Hash：NT Hash = MD4(UTF-16LE(password))（16 字节）

② NTLMv2 Key（ResponseKeyNT）：

NTLMv2Key = HMAC-MD5(NT_Hash, UTF-16LE(UPPERCASE(username) + domain))

参与计算的包括密码、用户名、域，因此 Hashcat 输入必须正确填写 username 和 domain。

③ NTLMv2 Blob：包含 Response Type、Timestamp、Client Challenge、AV Pairs（Computer Name、Domain Name、DNS Name 等）、Terminator。NTLMv2 不只是 "密码 + ServerChallenge"，还考虑客户端 Challenge、时间戳、目标信息等上下文。

④ NTProofStr：

NTProofStr = HMAC-MD5(NTLMv2Key, ServerChallenge || Blob)

得到 16 字节（32 hex 字符）。

⑤ 最终 NTLMv2 Response：

NTLMv2 Response = NTProofStr || Blob

即前 16 字节是 NTProofStr，后面是 Blob。

为什么要从 Response 中删除 NTProofStr

Wireshark 有时同时给出 NTProofStr 和 NTLMv2 Response，但后者 = 前者 + Blob。Hashcat 格式需要分开填写，因此若已单独复制 NTProofStr，最后一段不能再复制整个 Response，否则 NTProofStr 重复。应从完整 Response 去掉前面 32 个 hex 字符（=16 字节），剩余部分才是 Blob。

"modifiedntlmv2response" 不是标准字段名，准确叫 NTLMv2 Blob。

## 四、Hashcat 格式与 SMB 流量实操

Hashcat 5600 格式

**username:** :domain:ServerChallenge:NTProofStr:Blob

**示例：**

administrator::WIN2008:9a88373dbb4f5e36:4eb74543b9962bb2ca36e938909bb930:0101000000000000...

**命令：** hashcat -m 5600 hash.txt rockyou.txt

-m 5600=NetNTLMv2，-m 1000=NT Hash，-m 5500=NetNTLMv1，不要混。

--show 正确用法

\# 第一次破解

hashcat -m 5600 hash.txt rockyou.txt

\# 查看已恢复结果

hashcat -m 5600 hash.txt --show

--show 是从 potfile 显示此前已恢复结果，不是爆破参数，第一次破解不建议加。

Hashcat 本质

不是 "解密 NTLMv2 Response"（不存在逆运算），而是：候选密码→算 NT Hash→算 NTLMv2Key→结合 Username/Domain/ServerChallenge/Blob 重算 NTProofStr→与抓包比较→相等则得到密码。本质是离线口令猜测 / 验证。

抓一次认证即可离线验证，因为已获得全部所需数据（Username、Domain、Server Challenge、NTProofStr、Blob），服务器关机也不影响。

SMB 流量实操步骤

① 找 Type 2，提取 Server Challenge：过滤 ntlmssp，找 NTLMSSP_CHALLENGE → NTLM Server Challenge，如 9a88373dbb4f5e36。

② 找 Type 3，提取 Username/Domain：找 NTLMSSP_AUTH（一般在 SMB2 → Session Setup Request → Security Blob → NTLMSSP），记录 User name（如 administrator）、Domain name（如 WIN2008）。

③ 提取 NTProofStr：展开 NTLM Response → NTLMv2 Response → NTProofStr，如 4eb74543b9962bb2ca36e938909bb930（16 字节 = 32 hex）。

④ 提取 Blob：从完整 NTLMv2 Response 去掉前面 32 个 hex 字符，剩余部分即 Blob。

⑤ 组合并破解：按格式组合保存为 hash.txt，执行 hashcat -m 5600 hash.txt rockyou.txt。

## 五、多协议承载与版本对比

多协议承载（区别只在外层）

NTLMSSP

│

┌──────────┼───────────┐

↓          ↓           ↓

SMB        HTTP          SMTP

│          │             │

Security     NTLM Header   AUTH NTLM

Blob         Base64       Base64

打开外层后，Type1/2/3 是相同的 NTLM 认证体系。

**HTTP：** 401 Unauthorized + WWW-Authenticate: NTLM → Authorization: NTLM <Type1> → WWW-Authenticate: NTLM <Type2> → Authorization: NTLM <Type3>，Type1/2/3 通常 Base64 编码，解码后仍是 NTLMSSP，后半部分分析原理完全一样。

**SMTP：** AUTH NTLM <Base64 Type1> → 334 <Base64 Type2> → <Base64 Type3>，有时需手动 Base64 解码再分析。

不应分别死背 SMB/HTTP/SMTP 破解方法，应掌握找到协议里的 NTLMSSP → 提取 Type2/Type3。

NTLMv1 vs NTLMv2

| 特征 | NTLMv1 | NTLMv2 |
| --- | --- | --- |
| Server Challenge | 8 字节 | 8 字节 |
| 客户端 Challenge | 通常没有 | 有（Blob 结构） |
| 时间戳 | 无 | 有 |
| Target Info | 无 AV Pair 结构 | 有 |
| 核心算法 | DES 相关 | HMAC-MD5 |
| 安全性 | 很弱 | 明显更强 |

**对应：** NetNTLMv1→-m 5500，NetNTLMv2→-m 5600。

Type 3 中 LM Response 和 NT Response 随认证版本不同填充不同数据（LM/NTLMv1/LMv2/NTLMv2），现代题最常见 NTLMv2。

LmCompatibilityLevel

Windows 安全策略，控制客户端发送什么响应、服务器接受什么旧式响应：

| 值 | 客户端行为 |
| --- | --- |
| 0 | LM + NTLM |
| 1 | LM + NTLM，可协商 NTLMv2 Session Security |
| 2 | 只发送 NTLM |
| 3 | 只发送 NTLMv2 |
| 4 | NTLMv2，服务端拒绝 LM |
| 5 | NTLMv2，服务端拒绝 LM 和 NTLMv1 |

## 六、自动化工具

NTLMRawUnHide

python NTLMRawUnHide.py -i secret.pcapng

**本质是自动化手工步骤：** 扫描 PCAP→发现 Type1→发现 Type2→提取 ServerChallenge→发现 Type3→提取 Username/Domain/NTProofStr/Blob→生成 Net-NTLMv2 格式。它是NTLM 网络认证数据提取工具，不是破解工具，真正密码验证一般还是 Hashcat。
