---
title: "bftools视觉编程语言隐写"
summary: "图片 → Brainloller / Braincopter 解码 → Brainfuck 代码（<>+-.,[]）→ 执行 Brainfuck → flag /…"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理

**核心流程：**

图片 → Brainloller / Braincopter 解码 → Brainfuck 代码（<>+-.,[]）→ 执行 Brainfuck → flag / Base64 / Hex / 其他数据

BrainTools 官方工具同时支持 Brainloller、Braincopter 的编码 / 解码以及普通 Brainfuck 程序执行。

遇到一张看起来正常或颜色异常的图片，同时题目提示 brain、brainfuck、bf、braincopter、brainloller，应优先想到这类考点

## 二、Brainloller 与 Braincopter 的准确区别

### 1. Brainloller：固定颜色表示指令

Brainloller 使用一组固定 RGB 颜色表示 Brainfuck 指令，不是根据色相、亮度计算指令，而是特定颜色直接对应特定指令：

| 颜色 | RGB | 指令 |
| --- | --- | --- |
| 红色 | (255,0,0) | > |
| 暗红 | (128,0,0) | < |
| 绿色 | (0,255,0) | + |
| 暗绿 | (0,128,0) | - |
| 蓝色 | (0,0,255) | . |
| 暗蓝 | (0,0,128) | , |
| 黄色 | (255,255,0) | [ |
| 暗黄 | (128,128,0) | ] |
| 青色 | — | 指令指针顺时针转 90° |
| 暗青色 | — | 指令指针逆时针转 90° |
| 其他颜色 | — | NOP |

### 2. Braincopter：RGB 整体数值模 11

Braincopter 更适合把程序藏在一张看起来正常的图片中。每个像素 (R,G,B) 先计算：

65536 × R + 256 × G + B

**然后：**

command = (65536R + 256G + B) mod 11

得到 0～10：

| 结果 | 含义 |
| --- | --- |
| 0 | > |
| 1 | < |
| 2 | + |
| 3 | - |
| 4 | . |
| 5 | , |
| 6 | [ |
| 7 | ] |
| 8 | 向右旋转 90° |
| 9 | 向左旋转 90° |
| 10 | NOP |

即 8 个 Brainfuck 指令 + 2 个方向指令 + 1 个 NOP = 11 种状态。

**注意：** Braincopter 不是 "灰度值模 9"，而是 (65536R + 256G + B) % 11。BrainTools 的编码实现还会寻找与原像素非常接近、但满足目标 %11 结果的颜色，因此可以只产生很小的视觉变化，把程序嵌进普通图片中。

## 三、程序不是简单 "逐行扫描"

Brainloller / Braincopter 都有右转 90°、左转 90° 两个特殊指令，因此真正读取路径可能绕成复杂二维路线。

BrainTools 的 Braincopter 解码器从左上角 (0,0) 开始，初始方向向右（east），遇到 8 或 9 后改变方向，直到指令指针走出图片边界才结束。

不能理解成 "永远从左到右、从上到下逐像素转换"，更准确的是：从左上角向右开始，根据图片中的转向指令沿二维路径读取像素。

## 四、bftools 标准解题方法

**官方用法：**

decode → 图片转 Brainfuck

run → 执行 Brainfuck

bftools decode brainloller <image>

bftools decode braincopter <image>

bftools run <program>

默认结果输出到 stdout。

### 1. 优先尝试 Braincopter

.\bftools.exe decode braincopter "challenge.png" > "code.bf"

查看 code.bf，如果成功，内容应该主要由 > < + - . , [ ] 组成。再执行：

.\bftools.exe run "code.bf"

例如输出 ZmxhZ3thYmNkZWZ9 明显像 Base64，就继续 Base64 Decode 得到 flag。

### 2. Braincopter 不行再尝试 Brainloller

.\bftools.exe decode brainloller "challenge.png" > "code.bf"

.\bftools.exe run "code.bf"

模式判断

decode 后出现大量正常 Brainfuck 指令 → 模式大概率正确

只有极少指令 / 程序结构异常 /run 无正常结果 → 换另一种模式

## 五、图片格式与常见坑

### 1. PNG 最稳，JPG 不应当作为可靠载体

BrainTools 读取可以读取 .NET Framework 支持的图片格式，生成图片时工具保存为 PNG。JPG 可以被 bftools 读取不等于 JPG 适合保存 Braincopter 程序。

尤其 Braincopter 依赖精确 RGB 值 %11，JPEG 是有损压缩，重新编码后 RGB 很容易变化，从而直接把指令 4→5、7→2 等破坏。

**实战原则：** PNG 最可靠；JPG 可以尝试 decode，但不要重新压缩、转码或保存。如果题目本身给 JPG，直接对原文件尝试即可。

### 2. 不要先修改图片

不要缩放、截图、JPEG 重新保存、调色、滤镜、压缩、格式转换，尤其 Braincopter 对像素值非常敏感。应始终原题文件 → 直接 bftools decode。

### 3. 不要死记 "90% 都是 Braincopter"

没有可靠的固定占比。更合理的判断：

普通照片 / 大量自然颜色 → Braincopter 优先

明显只有红绿蓝黄等固定纯色 → Brainloller 优先

因为 Brainloller 使用固定颜色，而 Braincopter 可以利用任意颜色。

### 4. 其他 Brainfuck 解释器并非不能使用

bftools decode 得到的是普通 <>+-.,[] Brainfuck 程序，理论上也可以交给其他兼容的 Brainfuck 解释器运行。bftools run 的优势只是同一个工具直接完成、操作方便、减少兼容问题。不能说 "其他 Brainfuck 解释器都会运行失败"。
