---
title: "蓝牙流量分析"
summary: "蓝牙流量分析不是单独协议题，而是几类协议和密码学考点混合。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、蓝牙类型区分与总览

蓝牙流量分析不是单独协议题，而是几类协议和密码学考点混合。第一步必须先分清 Classic Bluetooth（经典蓝牙） 和 BLE（Bluetooth Low Energy）：

| 类型 | 偏向 | CTF重点 |
| --- | --- | --- |
| Bluetooth Classic | 文件传输、耳机、串口、OBEX、RFCOMM | OBEX → 传 ZIP/JPG/TXT → 导出 → 继续压缩包 / 隐写 / 密码题 |
| BLE | 广播、传感器、IoT、智能手环、低功耗设备 | ATT、GATT、SMP、BLE Link Layer |

**总关系：**

```text
蓝牙流量分析
```

```text
├─ Bluetooth Classic → OBEX → 文件/对象传输
```

```text
└─ BLE
```

```text
├─ ATT/GATT → 应用数据、特征值、Flag、密文、公钥
```

```text
├─ SMP → 配对、认证、密钥分发
```

```text
└─ Link Layer Encryption → BLE 链路层 AES-CCM 加密
```

## 二、OBEX：经典蓝牙文件传输

### 1. OBEX 基础

OBEX（Object Exchange Protocol，对象交换协议）主要用于对象 / 文件交换，Bluetooth Classic 中经常运行在 OBEX → RFCOMM → L2CAP → Bluetooth，和 BLE 的 ATT/SMP 不是同一体系。

### 2. CTF 考点与恢复流程

Wireshark 过滤 obex，重点看 CONNECT、PUT、GET、BODY、END-OF-BODY、NAME、TYPE。例如 PUT + Name: secret.zip + Body: ... 说明通过 OBEX 上传了 secret.zip。

**标准流程：**

PCAP → Wireshark → 过滤 obex → 确定传输文件名

→ 找到 Body/End-of-Body → 导出或重组文件

→ 得到 ZIP/JPG/TXT → 继续分析

有些 Wireshark 版本可通过 File → Export Objects 直接导出；没有对应功能时需根据 OBEX Body 数据自行重组。

### 3. 关于 "PIN Code" 的正确理解

导出压缩包后搜索 PIN Code 找解压密码时，这个 PIN Code 不一定是蓝牙配对 PIN，可能只是题目把 ZIP 密码藏在某个蓝牙数据包的字符串字段里。正确思路：导出的 ZIP 有密码 → 回到 PCAP → 搜索 PIN、PIN Code、password、passwd、key → 检查可打印字符串。不要形成 "OBEX 文件密码 = 蓝牙 PIN" 的固定印象，两者协议上没有必然关系。

## 三、ATT/GATT 与 Nordic UART

### 1. ATT 与 GATT 的关系

ATT（Attribute Protocol，属性协议）：BLE 里非常重要的协议，设备应用数据很多最终以 Attribute 形式读写，通过 Read、Write、Notification、Indication 等操作传输

GATT（Generic Attribute Profile）：利用 ATT 组织出 Service/Characteristic 的框架

**关系：**

```text
GATT
```

```text
├─ Service
```

```text
│   └─ Characteristic
```

```text
│       ├─ Value
```

```text
│       └─ Descriptor
```

```text
└─ 实际读写 → ATT
```

**类比：** GATT = 数据库结构，ATT = 查询 / 修改数据库的方法。Wireshark 里可能同时看到 BT ATT 和 BT GATT。

### 2. ATT 必须认识的 Opcode

| Opcode | 名称 | 作用 |
| --- | --- | --- |
| 0x0A | Read Request | 请求读取 |
| 0x0B | Read Response | 返回读取值 |
| 0x12 | Write Request | 写入并要求响应 |
| 0x13 | Write Response | 写入响应 |
| 0x1B | Handle Value Notification | 服务端主动通知 |
| 0x1D | Handle Value Indication | 服务端指示 |
| 0x52 | Write Command | 写入但不要求响应 |

btatt.opcode == 0x12 是 ATT Write Request，btatt.opcode == 0x52 是 ATT Write Command，这两个在 CTF 中经常用于提取客户端发往 BLE 设备的数据。

### 3. 为什么用 btatt.value

ATT 中真正的数据经常就在 Value 字段里。tshark 常见提取：

tshark -r capture.pcapng -T fields -e btatt.value -Y 'btatt.opcode == 0x12'

本质是找所有 Write Request，然后把其中的 Attribute Value 导出来。

### 4. Nordic UART Service（NUS）

Nordic UART Service 是 Nordic Semiconductor 定义的 BLE"虚拟串口" 服务，可理解成电脑串口的 TX/RX 在 BLE 里对应 Nordic UART TX/RX Characteristic。很多设备通过 Nordic UART 传字符串、命令、密文、公钥、Flag。

Wireshark 识别成功时可能出现 btgatt.nordic.uart_rx、btgatt.nordic.uart_tx 字段，-e btgatt.nordic.uart_tx 就是直接导出这个 BLE UART Characteristic 里的数据。这些字段依赖 Wireshark 实际解析结果，不要假定所有 BLE UART 题都有。

## 四、ATT 题型与 RSA 弱密钥

### 1. ATT 流量题两大类型

**类型一：** 直接藏 Flag（最基础）

PCAP → 过滤 btatt → 找到 Write/Notification → 提取 btatt.value

→ Hex Decode → flag{...}

例如 66 6c 61 67 7b 31 32 33 7d 转 ASCII 得 flag{123}。

**类型二：** 传输密文（密码学题）

ATT Write 的 Value 不是可打印字符（如 8f3a...），需继续判断是压缩、Base64、AES、RSA、XOR 还是自定义编码。BLE ATT 只是数据载体，真正难点是密码学。

### 2. BLE + RSA 题结构

**题目数据链大概是：**

```text
BLE ATT 流量
```

```text
├─ 一部分 Characteristic → RSA Public Key
```

```text
└─ 另一部分 Characteristic → RSA Ciphertext
```

ATT 只负责把 RSA 公钥和密文从抓包中找出来，然后：

ATT → 提取公钥 + 提取密文 → RSA 分析 → 恢复明文

### 3. 导出与 Hex Decode

用 tshark 导出公钥和密文时，不要机械照抄 opcode，应先在 Wireshark 中确定哪一个 Characteristic + 哪一种 ATT 操作才携带公钥 / 密文，再写过滤条件。Opcode 是根据题目流量确定的，不是 "RSA 公钥固定用 0x12"。

tshark 得到的如 2d2d2d2d2d424547494e205055424c4943204b45592d2d2d... 是十六进制形式的 ASCII，Hex Decode 后变成：

-----BEGIN PUBLIC KEY-----

MIIB...

-----END PUBLIC KEY-----

这才是真正的 PEM RSA Public Key，保存为 pub.key。

### 4. 检查 RSA 公钥

openssl rsa -in pub.key -text -pubin

\# 或更通用

openssl pkey -pubin -in pub.key -text

得到 Public-Key、Modulus、Exponent: 65537。核心参数：n = modulus，e = public exponent，RSA 公钥本质就是 (n, e)。

### 5. 弱 RSA 与 Fermat 分解

截图用 yafu 把 n 因式分解 n = p × q，然后根据 p、q、e 恢复 d 最终得到私钥。但必须纠正：正常安全生成的 RSA-1024/2048 公钥不能这样轻松分解，CTF 题能成功是因为故意生成了弱素数、素数过近、可被 Fermat Factorization 或其他有缺陷的 RSA 参数。

**正确知识点：**

RSA 公钥 → 检查 n 是否存在弱点 → 若可分解 n = p × q → 恢复私钥

不是 "任何 RSA 公钥 → YAFU → 得到私钥"。

截图出现 factoring 并很快得到 p、q，通常意味着 p ≈ q（两个素数距离过近）。Fermat 方法利用 n = a² - b² = (a-b)(a+b)，当 p 和 q 很接近时非常高效。这道 CTF 实际又考了 RSA 近素数 / Fermat 分解。

### 6. 恢复私钥与解密

有 p、q、e 后用 rsatool.py 重建私钥，基本原理：

φ(n) = (p-1)(q-1)

d = e⁻¹ mod φ(n)

最终 (n,e,d,p,q,...) 组成私钥，得到 priv.key。

解密时注意 rsautl 在新版 OpenSSL 已弃用，推荐：

openssl pkeyutl -decrypt -inkey priv.key -in ciphertext.bin -out plaintext.bin

padding 需根据题目判断（PKCS#1 v1.5、OAEP、Raw RSA），不能所有 RSA 密文都固定用同一参数。

## 五、SMP、链路层加密与 Crackle

### 1. SMP 是什么

全称Security Manager Protocol（SMP），是 BLE 中负责配对、认证、密钥生成 / 分发、安全参数协商的协议。

### 2. SMP 与 ATT 的区别（核心）

ATT → 传应用数据

SMP → 建立安全关系

**例如：**

SMP → 双方完成配对 → 产生/获得加密密钥

→ BLE Link Layer 启用加密 → ATT 内容开始被加密保护

因此 SMP ≠ 数据加密协议本身，更准确：SMP 负责配对和密钥管理，真正的 BLE 空口数据加密发生在 Link Layer，BLE 使用 AES-CCM。

### 3. BLE 加密完整关系

ATT/GATT → 应用数据 → L2CAP → Link Layer → AES-CCM 加密 → 无线传输

而 SMP 负责帮助双方得到 STK/LTK 等密钥材料。

### 4. TK、STK、LTK

| 密钥 | 全称 | 说明 |
| --- | --- | --- |
| TK | Temporary Key | Legacy Pairing 中使用；Just Works 时 TK=0，Passkey Entry 时是 6 位数字 |
| STK | Short Term Key | BLE Legacy Pairing 中由配对过程产生，保护初始配对阶段的连接 |
| LTK | Long Term Key | 长期密钥，用于后续连接加密 |

**简单记：** TK → 配对阶段输入；STK → 首次配对期间；LTK → 以后重新连接时长期使用。具体流程因 BLE 版本和配对方法不同而变化。

### 5. Crackle 破解什么

crackle -i xxx.pcapng -o dec.pcapng

输出 TK found: 000000、LTK found: ...、Decrypted ...。它主要针对 BLE Legacy Pairing 中存在弱 TK 的场景，例如 Just Works 时 TK=0，所以 Crackle 可以很容易恢复后续密钥。截图里 TK found: 000000 实际上就是典型的 Just Works 场景。

### 6. Crackle 能力范围

Crackle 不是万能 BLE 解密器。经典适用场景：

BLE Legacy Pairing

完整抓到了配对过程

Just Works 或低熵 Passkey

它不意味着任意 BLE 加密 PCAP → crackle → 必定解密。尤其 BLE 4.2 引入的 LE Secure Connections 使用 ECDH，与 Legacy Pairing 安全模型明显不同，普通 Crackle 经典攻击思路不能直接套用到所有 Secure Connections 流量。

### 7. 为什么必须抓到配对过程

假如 PCAP 只有已经加密后的 ATT 数据，但没有 Pairing Request、Pairing Response、Confirm、Random、Encryption Start，那么 Crackle 通常缺少必要信息。比赛中能不能解密 BLE，第一件事不是运行 Crackle，而是看抓包里有没有完整或足够的配对过程。

### 8. SMP 流量重点看什么

Wireshark 过滤 bt smp 或直接展开 Bluetooth SMP，常见：Pairing Request、Pairing Response、Pairing Confirm、Pairing Random、Encryption Information、Master Identification、Identity Information。CTF 主要关注：Pairing Method、是否 Legacy Pairing、TK 来源、是否 Just Works、密钥交换过程。

### 9. Crackle 流程与解密后继续分析

encrypted BLE PCAP → Crackle → dec.pcapng

原 PCAP 链路层 ATT 等内容被加密，dec.pcapng 恢复出明文 ATT/GATT 内容。

Crackle 解决的只是链路层加密，真正 Flag 很可能还藏在 ATT Value 里，所以解密后继续：

tshark -r dec.pcapng -T fields -e btatt.value -Y 'btatt.opcode == 0x52'

从解密后的抓包中提取所有 ATT Write Command 的 Value。

btatt.value 通常显示为十六进制（如 666c61677b3132337d），需要 CyberChef → From Hex 得到 flag{123}。很多蓝牙题最终链路：

BLE 加密 PCAP → Crackle → decrypted.pcap → ATT → btatt.value → Hex Decode → Flag

## 六、三类题型与wireshark过滤

### 1. 三类题型分开

**类型一：** OBEX 文件传输（Classic Bluetooth）

Classic Bluetooth → OBEX → 文件传输 → 导出 ZIP → 寻找密码 → 解压 → Flag

**重点：** OBEX、文件重组、密码线索。

**类型二：** ATT + RSA（BLE）

BLE → ATT/GATT → 提取 Characteristic Value → 得到 RSA 公钥 + RSA 密文

→ 分析弱 RSA → 分解 n → 恢复私钥 → 解密 → Flag

**重点：** ATT 字段提取、Hex 转码、RSA 弱密钥。

**类型三：** SMP + Crackle（BLE）

BLE → SMP Legacy Pairing → 弱 TK / Just Works → Crackle → 恢复 STK/LTK

→ 解密 Link Layer → ATT → 提取 Value → Flag

**重点：** SMP、TK、STK/LTK、Legacy Pairing、Crackle、ATT。

### 2. Wireshark/tshark 实用过滤

| 目的 | 过滤/命令 |
| --- | --- |
| OBEX | obex |
| ATT | btatt |
| Write Request | btatt.opcode == 0x12 |
| Notification | btatt.opcode == 0x1b |
| Write Command | btatt.opcode == 0x52 |
| 提取 ATT Value | tshark -r file.pcapng -T fields -e btatt.value |
| 指定 Opcode 提取 | tshark -r file.pcapng -T fields -e btatt.value -Y 'btatt.opcode == 0x52' |

Nordic UART 可能有 btgatt.nordic.uart_rx、btgatt.nordic.uart_tx，但依赖 Wireshark 实际解析。
