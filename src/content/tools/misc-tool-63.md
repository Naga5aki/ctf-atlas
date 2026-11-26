---
title: "BPG Windows工具包"
summary: "BPG Windows工具包不是 \"隐写工具\"，而是 BPG 图片格式的编码、解码和查看工具集。官方提供 bpg-0.9.8-win64.zip，核心程序有三个："
module: "Misc"
topic: "图像与视觉"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

BPG Windows工具包不是 "隐写工具"，而是 BPG 图片格式的编码、解码和查看工具集。官方提供 bpg-0.9.8-win64.zip，核心程序有三个：

| 程序 | 功能 | 方向 |
| --- | --- | --- |
| bpgenc.exe | 编码器 | PNG/JPG → BPG |
| bpgdec.exe | 解码器 | BPG → PNG/PPM |
| bpgview.exe | 查看器 | 直接打开 / 查看 BPG |

CTF 中最常用的是 bpgdec，做题主要是 "解码 BPG"，不是制作 BPG。

## 二、核心程序使用方法

### 1. bpgdec.exe

如果题目给 challenge.bpg，最实用的就是先转成 PNG：

bpgdec.exe -o output.png challenge.bpg

得到 output.png 之后，再按普通图片题继续分析。

查看基本信息（不输出图片）：

bpgdec.exe -i challenge.bpg

**适合先看：** 宽高、颜色格式、位深、Alpha、动画等信息。

指定输出 PNG 位深：

bpgdec.exe -b 8 -o output.png challenge.bpg

bpgdec.exe -b 16 -o output.png challenge.bpg

-b 控制的是输出 PNG 的 8/16 bit 位深，与 BPG 内部位深不是一回事。官方说明 bpgdec 可以输出 PNG 或 PPM。

### 2. bpgview.exe（直接看 BPG）

**如果只是想先确认图片内容：**

bpgview.exe challenge.bpg

会直接弹出窗口显示图片，还支持 BPG 动画（基于 SDL）。如果直接双击 .bpg Windows 不认识，就可以用它查看。

| 需求 | 选择 |
| --- | --- |
| 只想看内容 | bpgview |
| 想继续做隐写分析 | bpgdec 转 PNG（更实用） |

### 3. bpgenc.exe（把普通图片编码成 BPG）

bpgenc.exe -o output.bpg input.png

官方说明 bpgenc 接受 JPEG 或 PNG 输入。

**质量参数：**

bpgenc.exe -q 28 -o output.bpg input.png

-q 是量化参数 / 压缩质量相关：q 较低 → 质量更高 → 文件更大；q 较高 → 压缩更强 → 文件更小。

**无损压缩：**

bpgenc.exe -lossless -o output.bpg input.png

官方建议无损压缩最好从 PNG 输入，因为 JPEG 本身已经经过有损处理。
