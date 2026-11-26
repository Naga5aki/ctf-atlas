---
title: "BMP宽高爆破"
summary: "在常见 Windows BMP 中，尺寸位于 DIB Header。对于最常见的 BITMAPINFOHEADER："
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理

文件头结构

在常见 Windows BMP 中，尺寸位于 DIB Header。对于最常见的 BITMAPINFOHEADER：

宽度 biWidth：文件偏移 0x12，4 字节小端整数

高度 biHeight：文件偏移 0x16，4 字节小端整数

像素数据位置应读取 BITMAPFILEHEADER.bfOffBits（偏移 0x0A，4 字节小端），不能永远假定从第 54 字节开始。

典型出题方式

完整 BMP（如 800×600）→ 只修改文件头 height=50 → 像素数据基本未动

→ 查看器只按错误尺寸解释 → flag 所在区域看不到

与 PNG 的区别

| 格式 | 宽高修改 |
| --- | --- |
| BMP | 没有按块 CRC 机制，直接篡改尺寸更方便 |
| PNG | 宽高位于 IHDR，IHDR 本身带 CRC，直接改宽高不更新 CRC 会产生 CRC 错误；同时正确更新 CRC 也可以修改 |

## 二、题目识别特征

遇到以下现象，应优先检查 BMP 宽高：

BMP 能打开，但只显示一小条、半张图或明显缺少区域

图像严重横向错位、斜纹、重复

显示尺寸很小，但文件体积明显偏大

010 Editor 中宽高值与文件实际数据量明显不匹配

题目提示 width、height、size、dimension、图片不完整

binwalk、strings、LSB 等常规分析没有有效结果

表现判断

| 错误类型 | 常见表现 |
| --- | --- |
| 高度错误 | 只显示部分纵向内容 |
| 宽度错误 | 每行切分位置错误，图片斜着、错位、重复 |
| 宽高都错 | 用自动工具或 Raw 预览最方便 |

## 三、首选：PuzzleSolver 一键爆破

使用思路

打开 PuzzleSolver → ImageTools / 图片工具

→ 找到图片宽高修复 / BMP 宽高爆破 / 类似尺寸恢复功能

→ 导入 challenge.bmp

→ 选择 BMP 宽高爆破/修复

→ 执行自动分析

→ 查看候选图片或预览

→ 找到正常宽高

→ 保存恢复图片

如果版本要求设置搜索范围，可以先给合理范围（宽 1~3000，高 1~3000）。出现图像比例正常、文字不再错位、flag 完整出现即可确定正确尺寸。

实战优先级

PuzzleSolver → 一键恢复成功 → 直接看 flag

→ 失败 → GIMP Raw 预览

→ 仍失败 → 010 Editor 手工分析 BMP 头

## 四、GIMP Raw 法：宽高都不知道时最好用

### 1. 先找真正的像素数据偏移

不要死记 "BMP 头 = 54 字节"。54 字节只是最典型的 14 字节 BITMAPFILEHEADER + 40 字节 BITMAPINFOHEADER，且中间没有调色板、Bitfields 等附加数据时才成立。BMP 有多种 DIB Header，像素数据偏移应读取文件头中的 bfOffBits。

在 010 Editor 中：偏移 0x0A，长度 4 字节，小端，就是 bfOffBits。例如 36 00 00 00 转换为 0x36 = 54，这时才说明像素从第 54 字节开始。

### 2. 提取 Raw 像素数据

用 010 Editor 从 bfOffBits 开始一直选到像素数据末尾，另存为 raw.data。确认是简单 24-bit BMP 也可以直接删掉头部再另存，但推荐按 bfOffBits 提取，而不是固定删除 54 字节。

### 3. 使用 GIMP 导入 Raw

文件 → 打开 → raw.data → 选择 Raw 图像导入

根据原 BMP 信息设置（24-bit BMP → RGB 24bit），重点就是不断改变 Width/Height 观察实时预览。宽度错误常看到斜纹和错行，调整到正确宽度后画面会突然正常对齐、人物 / 文字完整、flag 可读。

**恢复后可能上下颠倒：**

正常的未压缩 Windows BMP，如果 biHeight > 0，通常按照 bottom-up 保存（像素数组中的第一行实际上是图像最下面的一行）；如果 biHeight < 0，则是 top-down。

因此 Raw 数据导入后如果方向不对，通常应该上下翻转（Vertical Flip），而不是旋转 180°。因为 BMP 每一行内部仍然是从左向右保存的，问题主要在行的上下顺序。

画面正常但上下倒置 → 上下翻转

画面左右也反了 → 才进一步检查导入方式

## 五、很多题根本不用 "爆破"：直接算高度

如果宽度正确、只有高度被改，往往可以直接算出高度。BMP 每一行要求按 DWORD（4 字节）对齐。

以 24-bit BMP 为例，1 像素 = 3 字节，但不能简单使用 每行 = width × 3，因为存在 Padding。正确公式：

RowSize = ((width × 3 + 3) // 4) × 4

| width | 计算 | RowSize |
| --- | --- | --- |
| 100 | 100×3=300，已被 4 整除 | 300 |
| 101 | 101×3=303，补 1 字节 Padding | 304 |

如果文件是简单未压缩 BMP 且像素后没有额外尾部数据：

PixelSize = FileSize - bfOffBits

Height = PixelSize / RowSize

例如 PixelSize=2592000，Width=1200，24bit，RowSize=3600，Height=2592000/3600=720，正确尺寸很可能就是 1200×720，直接修改 height 即可。

## 六、010 Editor 手工恢复

如果已经知道正确尺寸，最快的是直接修改文件头。对于常见 BITMAPINFOHEADER：

0x12 ~ 0x15：Width

0x16 ~ 0x19：Height

均采用 4 字节 Little Endian。例如正确高度 720，十六进制 0x000002D0，文件中写 D0 02 00 00，保存副本 fixed.bmp 重新打开即可。

这个方法适用于已经知道正确宽高；不知道尺寸时还是 PuzzleSolver 或 GIMP Raw 预览更快。
