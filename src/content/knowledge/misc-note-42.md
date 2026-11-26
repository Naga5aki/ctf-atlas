---
title: "PLTE调色板隐写"
summary: "PLTE 是 PNG 的调色板数据块。在索引色 PNG 中，像素保存的不是直接的 RGB 颜色，而是一个调色板索引：像素索引 → PLTE 中的颜色条目 → RGB…"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

PLTE 是 PNG 的调色板数据块。在索引色 PNG 中，像素保存的不是直接的 RGB 颜色，而是一个调色板索引：像素索引 → PLTE 中的颜色条目 → RGB 颜色。

Misc中重点不是普通像素 LSB，而是检查 PLTE 本身的 RGB 数据、未使用的调色板条目、调色板与像素索引的映射、tRNS 透明度数据。

## 一、核心原理

PLTE 每个颜色条目固定占 3 字节（R G B），最多 256 个条目

PNG 规范明确允许 PLTE 中存在没有被图片实际使用的颜色条目，这给隐写提供了空间

对于索引色 PNG，PLTE 必须位于第一个 IDAT 前，标准 PNG 最多只能有一个 PLTE

## 二、常见考法

### 1. PLTE 颜色数据隐藏

最常见的是直接修改调色板的 RGB 字节，把数据藏在 R/G/B 最低位、某一固定 bit 或连续 RGB 字节中。只改变 RGB 最低位通常只造成极轻微颜色变化，肉眼难以发现。

这类题不要优先使用普通 LSB 工具扫像素，而是直接检查 PLTE 原始字节。

**推荐工具：** TweakPNG

打开后主界面直接列出 IHDR、PLTE、tRNS、IDAT、IEND

找到 PLTE 即可重点查看其长度、调色板内容及是否存在异常数据

如需直接分析十六进制，用 010 Editor 搜索 ASCII PLTE，后面的数据区就是连续的 R G B R G B...，直接观察是否出现 flag{、CTF{、PK、Base64 字符串、明显 ASCII。

### 2. 未使用调色板条目隐写

这是 PLTE 很有代表性的考法。PNG 可能建立 256 个 PLTE 颜色，但实际图片只使用其中几十个，剩余颜色根本不会被像素索引引用，因此修改这些颜色不会改变图片显示。

**核心判断：** 调色板很多 + 实际使用颜色很少 = 优先检查未使用 PLTE 条目

实战中用 TweakPNG 查看 PLTE 条目，配合 StegSolve 观察图片的索引色结构和颜色数量。如果发现 PLTE 有 256 色但图片实际只有少量颜色，重点检查调色板尾部数据。例如 010 Editor 中看到 66 6C 61 67 7B 就是 flag{。

### 3. 调色板映射隐写

有些题不直接存 ASCII，而是利用像素索引 ↔ 调色板颜色之间的对应关系隐藏图案。例如图片大量使用 index 0 和 index 1，但这两个颜色在 PLTE 中非常接近（如 (120,120,120) 和 (121,121,121)），肉眼看起来几乎一样。

此时使用 TweakPNG 的 Palette Editor，把对应颜色强行修改成强对比色（index 0→黑色，index 1→白色），重新查看图片，原本隐藏的二值图（FLAG、二维码、字符、图案）就可能直接显现。

颜色太接近 → TweakPNG 改成强对比色 → 看隐藏图案。

## 三、标准工具流

**第一步：** pngcheck 判断是否存在 PLTE

pngcheck -v test.png

**典型输出：**

chunk IHDR

chunk PLTE

chunk IDAT

chunk IEND

如果出现 8-bit colormap、PLTE ... 256 palette entries，就应进入调色板分析。

**第二步：** TweakPNG 查看 PLTE /tRNS

Windows 打开 TweakPNG，载入图片后重点看：

**PLTE：** RGB 调色板，检查条目数量是否异常多、RGB 是否存在规律、是否出现大量非常接近的颜色、调色板尾部是否存在明显异常

**tRNS：** 调色板对应透明度，索引色 PNG 的透明度也可能成为隐藏载体

**第三步：** 010 Editor 看原始字节

如果 TweakPNG 看不出结果，010 Editor 打开 PNG → 搜索 PLTE。PNG 块结构是 Length → Chunk Type → Chunk Data → CRC，找到 PLTE 后，它后面的 Chunk Data 就是 RGB RGB RGB...。

**重点：** 直接查看 ASCII、查看十六进制规律、查看尾部未使用颜色、查看重复 / 近似 RGB 值。

**第四步：** StegSolve 辅助观察

StegSolve 不应作为 PLTE 题的唯一解题工具，但适合辅助判断图片是否存在颜色层差异、是否只有少量近似颜色、改变显示方式后是否出现隐藏轮廓。尤其当 PLTE 中存在两组肉眼接近的颜色时，可结合 StegSolve 判断隐藏图案。

真正要看、改 PLTE 本身，优先 TweakPNG + 010 Editor。

## 四、tRNS 与异常 PNG 必须一起检查

如果 PLTE 没结果，不要马上放弃。索引色 PNG 还可能有 tRNS，保存每个调色板颜色对应的透明度，因此可能出现 PLTE 正常但 tRNS 异常（如把两个几乎相同颜色设置成 alpha 254 和 alpha 255，肉眼难以发现但可编码二进制信息）。使用 TweakPNG → tRNS 查看透明度条目即可。

异常 PNG 结构

标准 PNG 要求：

PLTE 最多一个

PLTE 必须在第一个 IDAT 之前

所有 IDAT 必须连续

如果 pngcheck 发现多个 PLTE、PLTE 位于 IDAT 之后、PLTE 插入多个 IDAT 之间，应判断为人为构造的异常 PNG 结构，而不是正常的 "多调色板机制"，直接用 pngcheck + TweakPNG + 010 Editor 逐块分析。
