---
title: "GIF帧XY偏移量隐写"
summary: "GIF 的每一帧都有自己的 Image Descriptor，其中包含 Image Left Position（X 偏移）、Image Top Position（Y…"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

GIF 的每一帧都有自己的 Image Descriptor，其中包含 Image Left Position（X 偏移）、Image Top Position（Y 偏移）、Image Width、Image Height。X、Y 表示当前帧相对于整个 GIF 逻辑画布左上角的绘制位置。CTF 可以利用这些位置值编码数据，把每一帧对应成一个 bit，每 8 bit 转 ASCII 得到 flag。

正常 GIF 并不是所有帧都必须 +0+0，局部帧动画本来就可能使用非零 X/Y 偏移。判断隐写的关键不是 "出现非零偏移"，而是偏移值呈现明显的二值、ASCII 或其他编码规律。

## 一、识别特征

遇到以下组合时，应检查帧偏移：

GIF 有大量帧，但肉眼看起来几乎静止

各帧内容高度相似甚至完全一样

文件体积或帧数量明显异常

StegSolve 分帧后看不出隐藏图像

题目出现 frame、offset、position、XY、坐标、偏移等提示

**典型结构：** 几十 / 几百帧 + 帧内容几乎一致 + X/Y 只出现少数几个值 = 高度怀疑偏移量编码。

## 二、首选工具：ImageMagick

ImageMagick 可以直接读取每一帧的 page/canvas offset。官方格式转义：

%X → X offset

%Y → Y offset

%O → X、Y offset 组合

%s → scene/frame 序号

同时输出 X 和 Y（推荐第一条命令）

magick identify -format "%s: X=%[fx:page.x] Y=%[fx:page.y]\n" flag.gif

这样不会漏掉 "X 全 0、Y 才是隐藏数据" 的情况。

旧版 ImageMagick 6

identify -format "%s: %wx%h %O\n" flag.gif

**输出例如：**

0: 500x500 +0+0

1: 500x500 +1+0

2: 500x500 +1+0

其中 +1+0，第一个是 X 偏移，第二个是 Y 偏移。如果 X 只出现 0/1，就应直接考虑二进制。

只提取 X 或 Y

\# 只看 X

magick identify -format "%[fx:page.x]\n" flag.gif

\# 只看 Y

magick identify -format "%[fx:page.y]\n" flag.gif

适合快速观察是否只有 0/1、是否存在奇偶规律、是否落在 ASCII 范围。

## 三、常见编码方式

### 1. 两种偏移值表示 0/1

**最常见：** X=0 → 0，X=1 → 1。也可能 X=1 → 0，X=2 → 1。

**判断规则：** 如果某个偏移字段长期只出现两个值，就尝试把两种值分别映射为 0/1。

得到二进制后每 8 位转 ASCII，例如 01100110 → 0x66 → f。如果乱码，再尝试 0↔1 对调。

### 2. 奇偶性编码

例如 10 11 14 17 20 21，偶→0，奇→1，得到 0 1 0 1 0 1。

不能只盯着 0 和 1，还要看奇偶、固定差值、高低两组数值。

### 3. X/Y 联合编码

同时利用 (X,Y)，例如 (0,0)、(1,0)、(0,1)、(1,1) 分别对应 00、01、10、11，那么 1 帧 = 2 bit。

单独看 X、Y 都像乱码时，就应该把两列组合起来分析。

### 4. 偏移值直接作为字符或数值

偏移量出现 102 108 97 103 123，正好对应 ASCII f l a g {，可能是 X offset → ASCII。

这种方式受画布尺寸限制（Left/Top Position 本质是实际坐标，不能任意设置而完全不影响显示），比二值小偏移更值得作为 "发现规律后尝试" 的方向，而不是固定套路。

## 四、拆帧时的坑

不要一开始就 GIF → 批量导出 PNG → 再分析，因为真正需要的是原始 GIF Image Descriptor 中的位置信息。很多图像软件在导出、优化、合并或重新编码 GIF 时，会重新构造每一帧的画布和位置参数，原始 offset 可能被规范化或改变。

**最稳妥原则：**

原始 GIF → 直接 identify → 先记录 XY → 再考虑拆帧

不能绝对说 "所有拆帧工具一定会把偏移变成 0"，但重新编码确实有丢失原始结构信息的风险，所以不要拿处理后的 GIF 作为证据源。

## 五、010 Editor 底层验证

如果 ImageMagick 输出异常，可以直接看 GIF 结构。每个图像帧的 Image Descriptor 以 2C 开始，随后是：

2 字节 Image Left Position

2 字节 Image Top Position

2 字节 Width

2 字节 Height

这些 Left/Top 字段都是相对于 Logical Screen 的坐标。

ImageMagick → 快速解题；010 Editor → 底层验证。通常不需要手工逐帧解析。
