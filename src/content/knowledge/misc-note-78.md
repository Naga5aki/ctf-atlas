---
title: "SNMP 流量分析"
summary: "SNMP（简单网络管理协议）用于网络设备监控管理，CTF 中从 .pcap/.pcapng 恢复认证信息、解密 PDU、提取 OID 数据或 Flag。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、SNMP 基础与版本对比

SNMP（简单网络管理协议）用于网络设备监控管理，CTF 中从 .pcap/.pcapng 恢复认证信息、解密 PDU、提取 OID 数据或 Flag。

**常见端口：** UDP 161（查询 / 响应）、UDP 162（Trap/Inform 告警）。

**版本是第一考点：**

| 版本 | 认证方式 | 加密 | CTF关注点 |
| --- | --- | --- | --- |
| v1 | Community String | 否 | 直接找 community |
| v2c | Community String | 否 | 直接找 community |
| v3 | 用户 + 认证 + 可选加密 | 是 | Engine ID、用户名、认证参数、密码、加密 PDU |

v1/v2c 较简单（如 community=public 可直接看到），v3 出现 encryptedPDU 是重点难点。

## 二、SNMPv3 安全级别与报文结构

安全级别（核心考点）

| 模式 | 认证 | 加密 | 理解 |
| --- | --- | --- | --- |
| noAuthNoPriv | × | × | 只有用户名 |
| authNoPriv | √ | × | 用户名 + 身份认证 |
| authPriv | √ | √ | 用户名 + 身份认证 + PDU 加密 |

出现 encryptedPDU 通常说明启用 Privacy，接近 authPriv。

**报文结构：**

```text
SNMPv3 报文
```

```text
├── Header
```

```text
├── Security Parameters（多为明文）
```

```text
│   ├── Engine ID
```

```text
│   ├── Engine Boots
```

```text
│   ├── Engine Time
```

```text
│   ├── Username
```

```text
│   ├── Authentication Parameters
```

```text
│   └── Privacy Parameters
```

```text
└── Scoped PDU → encryptedPDU
```

Security Parameters 很多是明文，因此任意报文都能看到 Engine ID 和 Username。

## 三、Engine ID 与认证验证原理

Engine ID

唯一标识 SNMP Engine（如 80001f8880xxxxxxxx），不仅是设备编号，更是 USM 认证密钥本地化的重要输入。

密钥派生（为什么需要 Engine ID）

不是简单 MD5(password)，而是经过 "密码→主密钥→本地化密钥"：

password → 密码扩展并 Hash → Ku（主密钥）

→ Hash(Ku || EngineID || Ku) → Kul（本地化密钥）

同一密码在不同 Engine ID 上生成的最终认证密钥不同，因此 Engine ID 是离线验证候选密码的重要输入。

Authentication Parameters 与离线字典验证

Authentication Parameters 保存认证摘要，机制为：SNMP报文 + Kul → HMAC → Authentication Parameters。

**爆破本质：** 候选密码→算 Ku→结合 Engine ID 算 Kul→算报文 HMAC→与抓包中 Authentication Parameters 比较→匹配则找到口令。这是基于已捕获报文的离线字典验证，不是在线请求服务器，因此适合放进 Misc。

## 四、snmpv3brute 工具使用

命令

python3 snmpv3brute.py -w wordlist.txt -p net.pcapng

-w 指定字典，-p 指定抓包文件。

执行流程

Looking for SNMPv3 packets... — 寻找可用于验证的报文

Tasks to be processed — 列出识别出的目标（IP、Username）

Results — 输出找到的口令（IP、Username、Alg、Password）

关于 Alg=MD5

表示 USM 认证使用 MD5 系列算法，但不是简单 MD5(password)，而是密钥派生 / HMAC 体系中的 Hash 算法。

SyntaxWarning 不影响结果

SyntaxWarning: invalid escape sequence 只是 Python 新版本对字符串转义写法的警告（如 ASCII Banner 中的 \_），程序仍正常执行，与破解结果无关。

## 五、Auth/Priv 密码区别与 OID/Value

Auth Password ≠ Priv Password（重要易错点）

得到认证密码不代表一定能解密 encryptedPDU，USM 可分别配置：

| 密码 | 用途 | 典型算法 |
| --- | --- | --- |
| Auth Password | 验证报文真实性 / 完整性 | HMAC-MD5、HMAC-SHA-1、SHA-2 扩展 |
| Priv Password | 解密 encryptedPDU | DES、AES |

两者理论上可以不同，只是 CTF 常简化为 Auth=Priv 或题目提供其中一个。

**正确逻辑：** 恢复 Auth Password→判断是否 authPriv→若有 encryptedPDU→确定 Privacy 算法和 Priv Password→解密 Scoped PDU。

OID 与 Value（解密后关键）

未加密 SNMP 数据本质是 OID + Value：

**OID：** 对象标识，设备属性的 "路径"（如 1.3.6.1.2.1....）

**Value：** OID 对应的值

CTF 最终找异常 OID 或其对应字符串，如 OCTET STRING: flag{...}；若 flag 分散在多个包中，需按包序号、request-id、OID、时间顺序重新组合。

## 六、Wireshark 分析与 Engine Boots/Time

Wireshark 分析方法

先过滤 snmp，协议未识别时检查 udp.port==161 / udp.port==162。点击 SNMPv3 报文展开：

```text
Simple Network Management Protocol
```

```text
├── version
```

```text
├── msgGlobalData
```

```text
├── msgAuthoritativeEngineID
```

```text
├── msgAuthoritativeEngineBoots
```

```text
├── msgAuthoritativeEngineTime
```

```text
├── msgUserName
```

```text
├── msgAuthenticationParameters
```

```text
├── msgPrivacyParameters
```

```text
└── encryptedPDU
```

不同版本字段名 / 层级可能有区别，不要死记字段名，直接展开数据结构更可靠。

Engine Boots / Engine Time

属于 USM 时间窗口 / 重放保护机制：

Engine Boots：Engine 启动过多少次

Engine Time：本次启动后运行时间

CTF 通常不需手算，但要知道其作用是防止攻击者重放以前捕获的 SNMPv3 报文。
