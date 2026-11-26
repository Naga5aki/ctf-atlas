---
title: "msoffcrypto-tool"
summary: "msoffcrypto-tool 是 Kali 软件源里就有的 Microsoft Office 加密文档解密工具。"
module: "Misc"
topic: "文档与取证"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

msoffcrypto-tool 是 Kali 软件源里就有的 Microsoft Office 加密文档解密工具。它的定位很明确：你已经知道 Office 文档密码时，用它把加密的 Word / Excel / PowerPoint 解密成正常文件。

Kali 当前仓库维护 python-msoffcrypto-tool，对应可执行命令就是 msoffcrypto-tool

支持现代 Office OOXML：.docx、.xlsx、.pptx

**也支持一部分老式格式：** .doc、.xls、.ppt

涵盖 ECMA-376 Agile / Standard Encryption、部分 RC4 / RC4 CryptoAPI、XOR Obfuscation 等，但老格式里有些支持仍标为 experimental /partial

它不是密码爆破工具。主要作用是 "已知密码 → 解密 Office"，而不是 "不知道密码 → 自动爆破密码"。

## 二、核心命令及参数

| 用途 | 命令 | 参数说明 |
| --- | --- | --- |
| 检测是否加密 | msoffcrypto-tool document.docx --test -v | 返回 1 = 已加密；返回 0 = 未加密 |
| 已知密码解密 | msoffcrypto-tool encrypted.docx decrypted.docx -p Passw0rd | 结构：输入文件 输出文件 -p 密码 |
| 交互模式解密（推荐） | msoffcrypto-tool encrypted.docx decrypted.docx -p | 工具提示 Password: 后输入，密码不会出现在 shell history |
| 加密（了解） | msoffcrypto-tool -e -p Passw0rd plain.docx encrypted.docx | OOXML 加密功能目前仍是 experimental，CTF 主要记解密 |

各格式解密示例

\# Word

msoffcrypto-tool secret.docx result.docx -p Passw0rd

\# Excel

msoffcrypto-tool secret.xlsx result.xlsx -p 123456

\# PowerPoint

msoffcrypto-tool secret.pptx result.pptx -p flag123

解密完成后用 libreoffice result.docx 或文件管理器直接打开。

## 三、应用场景

典型场景

challenge.docx

↓

双击提示输入密码

↓

已通过题目线索 / John / Hashcat 得到密码

↓

msoffcrypto-tool 解密

↓

decrypted.docx

完整实战流程

**第一步：** 检测是否加密

msoffcrypto-tool flag.xlsx --test -v

确认加密（返回 1）后继续。

**第二步：** 分情况处理

| 情况 | 处理方式 |
| --- | --- |
| 题目已给密码 | 直接 msoffcrypto-tool flag.xlsx decrypted.xlsx -p 密码，然后 libreoffice 打开 |
| 密码未知 | 先 office2john flag.xlsx > office.hash，再 john office.hash --wordlist=/usr/share/wordlists/rockyou.txt，john --show office.hash 得到密码，最后用 msoffcrypto-tool 解密 |

**标准流程：**

加密 Office → office2john 提取 Hash → John / Hashcat / PKF 恢复密码 → msoffcrypto-tool 解密

Office 加密后为什么有时看起来不像 ZIP

正常 .docx/.xlsx/.pptx 本质是 ZIP，文件头通常是 50 4B 03 04。但 Office 使用现代密码加密整个 OOXML 包后，外层可能变成 OLE Compound File 容器，里面保存 EncryptionInfo 和 EncryptedPackage。

所以一个加密的 secret.docx 用 file / 010 Editor 看，可能开头是：

D0 CF 11 E0 A1 B1 1A E1

即 OLE Compound File，而不是 50 4B。这不代表 "它不是 DOCX"，而可能意味着这是一个被 Office 加密封装后的 OOXML 文档。

msoffcrypto-tool 就是专门解析这种 Office 加密结构并恢复原始 OOXML 的。解密之后的 decrypted.docx，文件头会重新是 50 4B 03 04。

## 四、补充说明

### 1. 常见报错处理

| 报错 | 含义 | 处理方式 |
| --- | --- | --- |
| 密码校验失败 | 密码错误 | 重新确认密码，注意大小写，检查是否多了空格 / 换行 |
| not encrypted | 文件本身没有使用 msoffcrypto 支持的文档加密 | 可能是普通 Office、只设置编辑保护、VBA 工程保护、工作表保护、文件损坏，这些和 "打开密码加密" 不是一回事 |
| Unsupported encryption | 加密机制不在完整支持范围 | 老式 .doc/.xls/.ppt 尤其可能遇到，官方对部分旧 Office RC4、XLS/PPT 支持仍标为 experimental/partial，可换 LibreOffice、oletools、John、Passware Kit 根据题型处理 |

### 2. 与相关工具的区别

| 工具 | 作用 |
| --- | --- |
| msoffcrypto-tool | 已知密码后解密 Office |
| office2john | 从 Office 提取密码 Hash |
| John / Hashcat | 破解 Office 密码 |
| PKF（Passware Kit Forensic） | GUI 式综合密码恢复 |
| oletools | Office/OLE 结构、宏、恶意文档分析 |

### 3. 使用建议

推荐使用交互模式 msoffcrypto-tool challenge.docx decrypted.docx -p（-p 后不直接跟密码），避免密码出现在 shell history 中

拿到 Office 文件先 --test 检测是否真的加密，不要浪费时间爆破没有打开密码的文件

解密后如果仍无法打开，检查是否是编辑保护、工作表保护等其他类型限制，而非文档加密
