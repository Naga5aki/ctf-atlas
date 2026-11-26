---
title: "ZIP双密码漏洞"
summary: "ZIP\"双密码\" 现象出现在采用 WinZip AES（AE-1/AE-2） 方案的 ZIP 中。"
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

ZIP"双密码" 现象出现在采用 WinZip AES（AE-1/AE-2） 方案的 ZIP 中。其本质不是 WinRAR 写错导致的漏洞，而是 HMAC 对超长密钥进行标准化处理所产生的等价密钥现象。

## 一、核心原理

WinZip AES 使用 PBKDF2 进行密钥派生，其中 PRF 是 HMAC-SHA1（WinRAR 从 5.50 起也默认使用 AES-256 CTR 创建加密 ZIP）。关键不在 AES，而在：

PBKDF2 → HMAC-SHA1

HMAC-SHA1 的内部块大小是 64 字节，RFC 2104 明确规定：

密码长度 ≤ 64 字节 → 直接作为 HMAC 密钥

密码长度 > 64 字节 → 先 SHA1(password) → 得到 20 字节摘要 → 将这 20 字节作为 HMAC 实际密钥

因此对于超长密码 P：

HMAC-SHA1(P, data) = HMAC-SHA1(SHA1(P), data)

而 PBKDF2 内部反复调用 HMAC，进一步得到：

PBKDF2-HMAC-SHA1(P, salt) = PBKDF2-HMAC-SHA1(SHA1(P), salt)

这就是所谓 "ZIP 双密码" 的真正来源。

## 二、最重要考点

**假设原密码：**

Nev1r-G0nna-G2ve-Y8u-Up-N5v1r-G1nna-Let-Y4u-D1wn-N8v4r-G5nna-D0sert-You

按 ASCII/UTF-8 计算实际长度是 71 字节，已经 > 64。

SHA1 十六进制表示：

706b4838613041714e62486364773847726d5370

长度 40 字符。

但 HMAC 真正使用的是这些原始字节：

70 6b 48 38 61 30 41 71 4e 62 48 63 64 77 38 47 72 6d 53 70

它们碰巧全部属于可打印 ASCII，转换为字符：

pkH8a0AqNbHcdw8GrmSp

所以真正的第二密码是 20 个字符，不是 40 个字符。

| 错误 | 正确 |
| --- | --- |
| 第二密码 = SHA1(password).hexdigest() | 第二密码 = SHA1(password).digest() |

只有当这 20 个原始字节刚好能作为密码输入时，才能方便地直接使用。

## 三、CTF 识别与解题流程

典型题型

AES 加密 ZIP

给出一个 > 64 字节的超长密码

直接使用超长密码不方便，或题目提示 SHA1/HMAC

SHA1 原始摘要恰好全部是可打印字符

解题流程

得到原超长密码

↓

确认字节长度 > 64

↓

计算 SHA1

↓

不要使用 40 字符 Hex

↓

把 20 个摘要字节按 ASCII 解释

↓

如果全部可打印

↓

将这 20 个字符作为第二密码

↓

解压 ZIP

可用 CyberChef 查看 SHA1 的原始字节 / ASCII 表示（而不是直接复制常见的 Hex Digest），也可以使用 010 Editor、HxD 等查看摘要字节对应的 ASCII。

## 四、大坑一：不能暴力破解 "第二密码"

40 个十六进制字符意味着：

16^40 = 2^160

这是 160 bit 搜索空间，不存在 "秒解"。即使正确理解成 20 字节 SHA1 摘要，搜索空间仍然是 2^160，没有变小。WinZip 也指出，由于 KDF 使用 HMAC-SHA1，其密钥搜索空间上限大致受 SHA1 的 160-bit 输出限制，而不是变成容易暴破的小密码。

Hashcat 什么时候有用？

Hashcat 的 -m 13600 对应 WinZip AES，但只能用于：

有字典

有已知密码格式

有短候选范围

有题目线索

例如怀疑密码是 flag{??????} 这种才适合 mask/dictionary。不能用 ?h?h?h... 共 40 位直接爆破完整 SHA1 Hex 空间。

## 五、大坑二：已知明文不能像 ZipCrypto 那样秒破

| 对比项 | ZipCrypto | WinZip AES |
| --- | --- | --- |
| 已知明文攻击 | 可以利用已知明文 → bkcrack → 恢复内部密钥 | 不存在此类攻击 |
| 加密结构 | 传统 ZipCrypto 结构弱点 | PBKDF2-HMAC-SHA1 + AES + 认证码，含 salt、password verification value 和认证码 |

知道 readme.txt 的内容并不会让你直接恢复密码，也不存在 "已知明文 → CRC32 → 秒破 160-bit 第二密码" 这样的攻击。因此看到 AES ZIP + 已知明文，不要拿 bkcrack 的思路硬套。

## 六、实战必须记住的限制

必须是使用 HMAC-SHA1 作为 PBKDF2 PRF 的 WinZip AES 类 ZIP

临界值是 > 64 字节，不是 "超过 64 个字符"

64 字节整不会触发 HMAC 长密钥预哈希，65 字节开始触发

等价密钥是 SHA1 原始 20 字节

不是 SHA1 的 40 字符十六进制文本

只有 20 字节摘要恰好可以作为密码输入时，才会形成 CTF 中方便利用的 "第二密码"

这不是把 160-bit 密码空间变成容易暴破的空间

与 ZipCrypto 明文攻击完全不同

**尤其注意：** 字符数 ≠ 字节数。ASCII 中 A = 1 字节，但 UTF-8 中文 中 = 3 字节。真正影响 HMAC 的是密码编码后的字节长度。
