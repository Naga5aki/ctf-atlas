---
title: "OpenPuff隐写"
summary: "OpenPuff 是面向多媒体载体的隐写工具，v4.01 支持图片、音频、视频、PDF 等多种载体。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心本质与原理

OpenPuff 是面向多媒体载体的隐写工具，v4.01 支持图片、音频、视频、PDF 等多种载体。Misc 核心不是某一种固定 LSB 算法，而是 Carrier Chain（载体链）+ 密码 + Bits Selection Level。

**处理过程：** 秘密文件 → 加密 → 数据打乱 → Whitening 白化 → 自适应编码 → 一个或多个 Carrier。不建议简单记成 "PNG=LSB、JPG=DCT"，OpenPuff 会按载体格式自行编码，Misc 中无需手工复现。

## 二、三大核心参数

### 1. Carrier Chain

支持单载体和多载体链，秘密数据分布在多个 Carrier 中

载体顺序是恢复条件的一部分，A→B→C 与 C→A→B 不同

最后一个 Carrier 剩余容量填充随机数据，无法按数据量识别

单载体同样存在，不要认为必须多文件

### 2. 密码机制

| 密码 | 作用 | 状态 |
| --- | --- | --- |
| Password A | Cryptography keys | 必须存在 |
| Password B | Cryptography CSPRNG | 可启用 / 禁用，禁用后用 A |
| Password C | Scrambling CSPRNG | 可启用 / 禁用，禁用后用 A |

不是固定需要三个独立密码，可能是仅 A、A+B、A+B+C，需按隐藏时启用状态恢复。密码派生使用 KDF4，不是简单 SHA-256。

### 3. Bits Selection Level

7 级：Minimum → Very Low → Low → Medium → High → Very High → Maximum，对应数据与 Whitening 比例不同。解密时必须与隐藏时一致，密码 / 载体 / 顺序都对还失败就优先查这个。

真正的 "密钥条件" = 密码 + Carrier 集合 + Carrier 顺序 + Bits Selection Level。

## 三、支持载体与识别

支持格式

图片（BMP/JPG/PCX/PNG/TGA）、音频（AIFF/MP3/AU/WAV）、视频（3GP/FLV/MP4/MPG/SWF/VOB）、文档（PDF）。格式不同的文件可能共同组成一个 Carrier Chain。

识别方法

无通用文件头特征，靠题目提示 + 文件组合 + 常规分析：

**关键词：** OpenPuff / Puff / carrier / chain / order / sequence / A B C / decoy / bits selection

**典型表现：** 一次给多个媒体文件，题目提示 "缺一不可"" 顺序很重要 ""串起来"

单文件也可能是 OpenPuff，多文件不是必要条件

## 四、工具与解题步骤

首选 OpenPuff v4.01，界面中 Hide 是制作，Unhide 是解题。

**标准五步：**

点击 Unhide 进入提取界面

**输入密码：** 按题目给的分别填 A/B/C，只给一个密码时考虑 B/C 禁用，不要乱填三遍

添加 Carrier：点 Add 全部加入，按隐藏时正确顺序排列（界面可上下移动）

设置 Bits Selection Level：无提示先 Reset Options，出题改过则对应恢复

Unhide!：选输出位置，CRC 通过后得到秘密文件，回 Kali 继续分析

Carrier 顺序判断

从文件名、题目描述、数字编号、EXIF、时间信息、文本提示找线索（如 first/second/third 明显按序）。完全无提示且数量少才排列组合（3 个 = 6 种，4 个 = 24 种），多了优先找线索。
