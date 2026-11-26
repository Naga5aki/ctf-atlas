---
title: "bkcrack"
summary: "bkcrack专门针对ZIP传统加密（ZipCrypto）。它的核心价值在于：只要知道明文的一部分（哪怕只有12字节），就能还原出完整的加密密钥，从而解密整个压缩包。"
module: "Misc"
topic: "压缩与口令"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

bkcrack专门针对ZIP传统加密（ZipCrypto）。它的核心价值在于：只要知道明文的一部分（哪怕只有12字节），就能还原出完整的加密密钥，从而解密整个压缩包。

## 一、核心定位

### 1.唯一攻击目标

它只支持ZIP传统加密（ZipCrypto），不支持AES加密（WinRAR/7-Zip的现代加密）。

### 2.核心原理

利用流加密（Stream Cipher）的弱点（如RC4）：

\text{密文}=\text{明文}\oplus\text{密钥流}

只要知道明文和对应的密文，就能反推出密钥流，进而解密整个文件。z二、应用场景

### 1.已知明文攻击（Known-Plaintext Attack）

### 2.固定文件头攻击（File Header Attack）

## 二、实战命令

| 命令示例 | 核心参数说明 | 功能用途 |
| --- | --- | --- |
| bkcrack -L target.zip | -L 后跟目标压缩包 | 列出包内文件、加密类型、压缩方式、CRC 等信息，攻击前校验是否为ZipCrypto 加密 |
| bkcrack -C 加密.zip -c 加密内文件 -P 明文.zip -p 明文内文件 | -C 加密压缩包；-c 加密文件名；-P 明文压缩包；-p 明文文件名 | 标准明文攻击，通过完整明文文件计算解密密钥 |
| bkcrack -C target.zip -c flag.png -x 0 89504E470D0A1A0A | -x 偏移量 十六进制明文，指定偏移位置的已知明文片段 | 偏移明文攻击，利用文件头固定格式直接发起攻击，CTF 高频用法，无需完整明文文件 |
| bkcrack -C target.zip -c flag.png -k 密钥1 密钥2 密钥3 -d out.png | -k 三组解密密钥；-d 解密后输出文件名 | 密钥解密文件，用已得到的内部密钥直接解密导出单个目标文件 |
| bkcrack -k 密钥1 密钥2 密钥3 -r 4..8 ?l?d | -r 长度范围 字符集掩码，掩码规则：?l小写、?u大写、?d数字、?s特殊符号 | 反推原始密码，从内部密钥枚举还原压缩包原始解压密码 |
