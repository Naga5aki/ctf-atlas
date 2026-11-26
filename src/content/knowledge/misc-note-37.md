---
title: "PixelJihad隐写"
summary: "PixelJihad 是一种基于 LSB（最低有效位）的图像隐写工具，主要把文本消息隐藏到图片像素的 RGB 数据中。"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、原理

PixelJihad 是一种基于 LSB（最低有效位）的图像隐写工具，主要把文本消息隐藏到图片像素的 RGB 数据中。

与普通顺序 LSB 不同，PixelJihad 会利用密码参与隐藏位置的选择，因此隐藏数据并不一定从第一个像素开始按 RGB 顺序连续排列。

## 二、主要特点

| 特点 | 说明 |
| --- | --- |
| 基于 LSB | 只修改像素颜色值的最低位（xxxxxxx0），每次变化通常 ±1，肉眼基本看不出区别 |
| 主要隐藏文本 | 图片 + 文本 → 隐写图片，不是典型的 "图片藏图片" 工具 |
| 可无密码 | 有密码时密码影响位置 + 可参与消息加密；无密码时 Password 留空一样可正常编解码，CTF 中经常就是无密码 |
| 非顺序 LSB | 位置选择与密码的 SHA-256 结果有关，普通 zsteg 没直接扫出来 ≠ 不存在 LSB 隐写 |

## 三、核心规则

PixelJihad 可简单理解为：

隐藏文本 → 16 bit 字符数据 → 前面保存消息长度 → 根据密码生成位置序列 → 写入 RGB 通道 LSB→ 生成隐写图片

| 规则项 | 内容 |
| --- | --- |
| 修改位置 | RGB 通道 |
| 修改位 | bit 0，即 LSB |
| Alpha | 不用于保存主要隐藏数据 |
| 密码 | 可以为空 |
| 密码作用 | ① 决定数据位置 ② 有密码时可参与消息加密 |

## 四、识别方法

PixelJihad 没有像 PNG、ZIP 那样固定的文件头特征，不能单靠十六进制直接判断，主要依靠题目提示 + 图片类型 + 常规隐写分析结果。

### 1. 题目关键词

PixelJihad / Pixel / Jihad / LSB / 像素 / 像素隐写 / 隐藏文本如果题目

### 2. 文件表现

一般是一张视觉完全正常的图片

file challenge.png 可能只是正常 PNG image data

exiftool / strings / binwalk 通常无明显异常元数据、无文件尾 ZIP、无直接字符串 Flag

这时应考虑像素层隐写。

## 五、工具使用

### 1.PixelJihad 原工具，在线地址：sekao.net/pixeljihad/

操作流程

打开 PixelJihad→选择 Decode / 解码→载入题目图片→输入密码→Decode→

得到隐藏文本

无密码题处理

如果题目没有给密码，Password 直接留空然后执行 Decode。这是 PixelJihad 题非常常见的情况。

### 2.本地离线工具

比赛环境不能访问外网时，可把 PixelJihad 项目提前保存到 Kali：

**项目：** oakes/PixelJihad（GitHub 获取源码）

因为 PixelJihad 本身是前端 JavaScript 工具，很适合离线保存，比赛时 Kali 本地浏览器打开即可离线 Decode。
