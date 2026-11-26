---
title: "wbStego4open隐写"
summary: "不建议死记 \"PDF 就是空格 = 0、Tab=1\"，官方资料只明确其 PDF 使用专门的 PDFInsert 模块，并没有支持这种简单概括。"
module: "Misc"
topic: "文档与取证"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理

支持的载体与格式

| 载体 | 支持格式 | 处理模块 |
| --- | --- | --- |
| BMP | 4-bit（16 色）、8-bit（256 色）、24-bit（真彩色） | BMPReplace |
| TXT | ASCII / ANSI，有 Standard 和 Compatible 两种模式 | ASCIIReplace / ASCIIInsert |
| HTML | 按文本 Compatible 方式处理 | ASCIIInsert |
| PDF | 专门的插入式处理，正常阅读器无可见变化 | PDFInsert |

不建议死记 "PDF 就是空格 = 0、Tab=1"，官方资料只明确其 PDF 使用专门的 PDFInsert 模块，并没有支持这种简单概括。

## 二、实战解法

界面选择

**官方提供两种界面：**

Wizard Mode（向导模式）：适合 CTF 直接解题，推荐使用

Flowchart Mode（流程图模式）：适合一次设置全部参数

解密流程

打开程序 → Welcome → Continue >>

→ 选择 Decode / Extract 隐藏数据

→ 选择题目载体（PDF / BMP / TXT / HTML）

→ 设置恢复文件的保存位置

→ 如果要求密码，输入题目给出的密码

→ 开始 Decode

→ 得到隐藏文件

恢复后处理

恢复出来的不一定是 flag.txt，也可能是 ZIP、RAR、图片、PDF、二进制文件。解出文件后应：

直接打开 → 打不开 → 010 Editor / file 判断文件头 → 按真实格式继续处理

## 三、密码和加密

wbStego4open 确实支持真正的数据加密，不是单纯 "访问控制密码"。官方支持：

Blowfish

Twofish

CAST128

Rijndael（AES）

**处理流程：**

原始秘密文件 → 可选加密（Blowfish / Twofish / CAST / AES）→ wbStego 编码 → 写入载体

没有正确密码时，即使发现并提取了载荷，也可能只能得到无意义数据。

## 四、不同载体的判断与处理

### 1. BMP

官方支持 4-bit（16 色）、8-bit（256 色）、24-bit（真彩色），并不是只有 24-bit BMP。不同色深容量不同，且经过隐写的 BMP 不应随意转换为 JPEG 等有损格式，否则隐藏数据可能丢失。

**典型特征：** BMP 正常显示 + 没有明显视觉异常 + 怀疑 wbStego → 直接用 wbStego4open Decode。

zsteg 辅助检测：

zsteg -a challenge.bmp

**修正误区：** zsteg 并非完全不认识 wbStego，其源码中实际上包含专门的 WBStego checker，并参考了 wbStego4open 源码，因此部分 wbStego BMP 可以被 zsteg 识别。

**工具关系：** wbStego4open → 专用解码首选；zsteg → BMP 辅助检测。

### 2. TXT / HTML

TXT 官方有两种模式：Standard 和 Compatible。其中 Compatible 会增加文件大小，但在正常应用中不产生明显视觉变化；HTML 直接按照 Compatible 文本方式处理。

遇到 TXT / HTML 内容完全正常，但文件结构或空白字符异常，可以想到 wbStego。

不要为了 "清理格式" 执行自动格式化 HTML、删除多余空格、文本清洗、复制粘贴后重新保存，这些操作可能破坏隐写数据。

### 3. PDF

PDF 是 CTF 中很值得重点考虑的载体。官方说明 wbStego4 对 PDF 没有特殊载体限制，嵌入后正常 PDF 阅读器显示不会出现可见变化，但文件大小会增加。

看到正常 PDF + strings /binwalk 没直接结果 + 题目提示隐写或 wbStego → 直接 wbStego4open → Decode → 导入 PDF，比手动研究 PDF 对象结构效率高得多。

## 五、实战避坑

| 坑 | 正确做法 |
| --- | --- |
| 不要修改原文件 | PDF 重新打印 / 优化 / 重新保存、BMP 转 JPEG / 重新压缩、TXT 自动格式化、HTML Beautify 都可能重写载体数据，使 wbStego 无法正确恢复 |
| 不要固定认为只有 PDF 和 24 位 BMP | 实际支持 BMP（4/8/24 bit）、TXT、HTML、PDF |
| 不要把 "密码" 理解成假的 | 支持真正的 Blowfish / Twofish / CAST128 / AES 加密 |
| 不要把所有 wbStego 都理解成普通 LSB | 针对不同载体有 BMPReplace、ASCIIReplace、ASCIIInsert、PDFInsert 不同实现 |
