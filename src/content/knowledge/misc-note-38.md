---
title: "DeEgger Embedder隐写"
summary: "DeEgger Embedder 是一款 Windows 平台的文件嵌入 / 提取型隐写工具，可把秘密文件隐藏进 JPG、PNG、MP3、AVI、PDF 等宿主文件…"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、基本定位

DeEgger Embedder 是一款 Windows 平台的文件嵌入 / 提取型隐写工具，可把秘密文件隐藏进 JPG、PNG、MP3、AVI、PDF 等宿主文件中，生成后的宿主文件通常仍能被原查看器、播放器正常打开。隐藏文件本身可以是任意类型。

宿主文件 Host + 秘密文件 Secret → DeEgger Embedder → 表面正常的宿主文件

**解题时反向操作：**

可疑宿主文件 → DeEgger Embedder → Extract Files → 恢复隐藏文件

## 二、原理

DeEgger 的基本功能是把一个文件与宿主媒体文件进行组合，并允许之后用同一个工具把隐藏文件重新提取出来。

正常 JPG/PNG/MP3/AVI/PDF + secret.zip → Combine → challenge.jpg

此时 challenge.jpg 仍可能正常打开、正常显示 / 播放，file 命令仍识别为原格式。因此表面 "完全正常" 并不能排除 DeEgger。

## 三、工具使用

**主界面有五个标签：** Combine Files、Extract Files、Quick Edit、Settings、Help。Misc 解题只需区分前两个：

| 标签 | 作用 | 解题用不用 |
| --- | --- | --- |
| Combine Files | 选择宿主 + 选择秘密文件 → Combine → 制作隐写文件 | ❌ 出题人用的 |
| Extract Files | DeEgger 隐写文件 → 恢复其中隐藏的原始文件 | ✅ 解题核心 |

## 四、识别方法

实战判断主要依靠题目线索 + 文件表现 + 常规检查结果 + DeEgger 工具验证。

### 1. 最强识别特征：题目名称或描述

看到以下关键词都应想到 DeEgger：

DeEgger / DeEgger Embedder / egg / deegg / egged / embed / embedded / combine / extract / hidden file

尤其 egg / deegg 属于非常值得注意的文字提示。例如题名 deegg、Egg、Hidden Egg、Egg in picture，同时给 jpg/png/mp3/avi/pdf，就应把 DeEgger 放到很高优先级。

### 2. 宿主文件的典型表现

**可正常打开：** file 识别为原格式，双击正常显示 / 播放

**体积可能异常：** 一张 800×600 JPG 正常几百 KB，题目文件却 5MB/20MB/50MB，应考虑附加数据 / 嵌入文件 / DeEgger / 文件拼接。但 "大" 只能作为辅助特征，不能单独证明是 DeEgger

**载体格式不限制：** JPG、PNG、MP3、AVI、PDF 都可能是 DeEgger 考点

### 3.多文件隐藏

DeEgger 支持多个隐藏文件，Extract 后可能得到多个文件
