---
title: "BMP Padding / Invoke-PSImage / ImageMask"
summary: "这三个考点都属于 \"图片看起来正常，但数据藏在图像底层结构里\"，但隐藏位置完全不同："
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

这三个考点都属于 "图片看起来正常，但数据藏在图像底层结构里"，但隐藏位置完全不同：

| 考点 | 隐藏位置 |
| --- | --- |
| BMP Padding | 数据藏在 BMP 每一行末尾的对齐填充字节 |
| Invoke-PSImage | PowerShell 脚本藏在 PNG 像素颜色的低位 |
| ImageMask | 普通文本 / 文件藏在 PNG 像素颜色的若干低位 |

## 一、BMP Padding 隐写

核心原理

BMP 的每一行扫描线通常要求按 4 字节（DWORD）对齐。如果一行真实像素数据长度不是 4 的倍数，就需要在行尾加入 Padding。除 RLE 压缩 BMP 外，扫描线都要进行 DWORD 对齐。

以 24 位 BMP 为例：

一行真实像素数据 = Width × 3

Padding = (4 - (Width × 3) % 4) % 4

例如 Width = 3：3×3 = 9 字节，不是 4 的倍数，实际一行 = 12 字节（9 字节像素 + 3 字节 Padding）。

这些 Padding 不参与正常图像显示，CTF 可以把 00 00 00 替换成 66 6C 61、67 7B...，然后把每一行的 Padding 顺序连接起来得到 flag{...}。

识别方法

拿到 BMP，尤其是普通 LSB、binwalk 都没有结果时，检查 BitDepth、Width、Compression：

如果是未压缩 BMP，并且计算出来 Padding > 0，就值得检查

如果是 24-bit 且 Width × 3 % 4 = 0，则 Padding = 0，常规 "行尾 Padding 隐写" 不存在

PuzzleSolver 解法

图像处理 → ImageTools / 对应隐写菜单 → [3] BMP填补字节 - (BMP)

→ 导入 challenge.bmp → 执行提取 → 查看输出

结果直接是 flag{...} → 结束

结果是 50 4B 03 04... → 可能是 ZIP

结果是 Base64/Hex → 继续二次解码

**关键词：** BMP + 行对齐 + Padding + 每行末尾

## 二、Invoke-PSImage 隐写

核心原理

Invoke-PSImage 是专门把 PowerShell 脚本编码到图片像素中的工具，可以直接根据脚本生成 PNG，也可以把脚本嵌入现有图片，输出最终都是 PNG。

对于最常见的 "嵌入现有图片" 模式：每个像素取两个颜色分量，各使用最低 4 bit，因此一个像素正好可以存储一个脚本字节。

例如 PowerShell 字节 10110110 拆成 1011 和 0110，分别写进某颜色分量低 4 bit 和另一个颜色分量低 4 bit。

虽然属于低位隐写，但和普通 R bit0 / G bit0 / B bit0 经典 LSB 不一样。

识别方法

Invoke-PSImage 的指纹主要来自题目语境而不是图片外观：

PNG + 题目提示 PowerShell / PS / ps1 / Invoke / payload

**流量取证题里尤其值得注意：** 主机下载一张 PNG + 紧接着出现 PowerShell

图片看起来可能完全正常（官方本身设计成把脚本嵌进正常图片中）

另一种不使用载体图片、直接由 Payload 生成的 PNG，视觉上可能更像随机像素图

PuzzleSolver 解法

[4] Invoke-PSImage - (PNG)

→ 导入 challenge.png → Invoke-PSImage 提取 → 查看提取结果

正确时通常恢复出 PowerShell 代码：

$xxx = ...

IEX ...

FromBase64String(...)

CTF 中接下来不是直接运行，而是继续静态分析脚本：Base64、Hex、Gzip、XOR、字符串拼接，逐层还原即可。如果提取的是未知脚本，尤其来自真实取证样本，不要直接执行。

**一句话识别：** PNG + PowerShell 提示 → 第一时间试 Invoke-PSImage

## 三、ImageMask 隐写

核心原理

ImageMask 和 Invoke-PSImage 都是在像素低位藏东西，但它不是专门藏 PowerShell，而是可以直接隐藏 Text / File。官方支持 hideText/revealText 和 hideFile/revealFile 两套接口。

核心参数叫 mixCount，表示使用每个颜色值的多少个最低位保存数据：

**范围：** 1～5

**默认：** 2

超过 3 bit 后图像失真会比较明显

例如原像素 xxxxxxxx，mixCount = 2 时，隐藏数据写入 xxxxxxDD（最低 2 bit）。

ImageMask-Text

用于图片 → 提取隐藏文本。

PuzzleSolver → [7] ImageMask - Text - (PNG)

→ 导入 PNG → 执行 → 查看文本输出

可能直接得到 flag{...}

或者得到 ZmxhZ3s... → 继续 Base64

ImageMask-File

用于图片 → 恢复完整文件。

PuzzleSolver → [8] ImageMask - File - (PNG)

原版 ImageMask 的 revealFile() 不仅恢复文件数据，还保存文件名称信息，所以可能直接恢复 flag.txt、secret.zip、1.png、data.bin，提取后继续根据文件类型处理。

Text 和 File 不知道选哪个

先 ImageMask-Text → 没有有效结果 → 再 ImageMask-File

二者是同一个 ImageMask 体系的不同载荷类型，不用当成两个完全独立的考点。
