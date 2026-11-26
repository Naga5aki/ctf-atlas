---
title: "OurSecret"
summary: "OurSecret 是 SecureKit.net 推出的一款老牌 Windows 文件隐写工具，旧名为 Steganography，常见版本为 2.5 / 2.5.5。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: ["D:\\CTF_MISC_Tools\\图像隐写\\OurSecret.exe"]
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

OurSecret 是 SecureKit.net 推出的一款老牌 Windows 文件隐写工具，旧名为 Steganography，常见版本为 2.5 / 2.5.5。它可以把文本或其他文件隐藏到一个正常载体文件中，并提供可选的密码保护；允许一个载体中隐藏多个文件，隐藏内容本身也基本不受文件类型限制。

**核心机制：** EOF Data Injection（文件尾追加数据）

OurSecret 的核心不是 PNG 像素、LSB 或 IDAT 压缩位，而是把隐藏内容及自身控制数据追加到载体文件末尾：

原始载体文件

│

├─ 原始正常数据

│

└─ EOF 之后

├─ OurSecret 控制信息

├─ 隐藏文件信息

├─ 密码相关数据

└─ 隐藏内容

公开取证研究已确认这种 EOF Injection 机制，并发现 OurSecret 修改后的文件中存在固定特征数据（稳定的 40 字节特征序列），可用于识别。

与其他隐写工具的区别

| 工具 | 隐藏位置 |
| --- | --- |
| zsteg | PNG/BMP 像素低位 |
| JSteg | JPEG DCT 系数 |
| OurSecret | 文件尾追加隐藏内容 |

载体格式

OurSecret 对载体格式依赖较低，图片、音频、视频以及其他文件都可以作为 carrier，软件甚至允许选择任意文件类型作为载体。

"软件允许选择任意文件" 不代表所有文件格式都同样适合。EOF 追加法依赖目标格式或对应程序容忍文件末尾存在额外数据；某些程序重新保存、转码或严格校验文件时，尾部隐藏数据可能被删除。

## 二、使用方法

### 1. 提取隐藏内容（Unhide）

打开 OurSecret → 进入 Unhide → 选择可疑载体文件

↓

无密码 → 密码留空直接尝试

有密码 → 填写对应密码

↓

执行 Unhide → 工具列出隐藏的文本或文件

↓

文件类型 → 选择保存出来

文本内容 → 直接查看

### 2. 嵌入内容（Hide）

选择 Carrier File

↓

Add → 选择要隐藏的文件

或 New Message → 添加文本

↓

可选设置密码

↓

Hide → 保存新的载体文件

支持一次加入多个隐藏文件，也可以同时加入文本信息

生成后的文件通常外观 / 播放内容基本不变，文件大小增大

**例如：** cover.jpg（200 KB）+ secret.zip（500 KB）→ stego.jpg（> 700 KB），因为隐藏内容并没有被塞进 JPEG 的像素 / DCT 空间，而是主要增加到了载体尾部

## 三、应用场景

### 1. 无密码基础题

题目直接给 jpg / png / bmp / wav / mp4 / ...，图片或媒体本身完全正常，又没有明显的 LSB、DCT、元数据异常。如果题目暗示 OurSecret、our secret、secret、hide、carrier，可以直接：

OurSecret → Unhide → 密码留空 → 尝试提取

"secret" 这个单词本身不能作为 OurSecret 的可靠识别特征，只能算题目提示。真正有效的判断应结合文件尾异常数据和 OurSecret 特征结构。

### 2. 有密码题

OurSecret 提供密码保护，题目可能要求先从其他位置取得密码。密码线索常常可能来自：

题目描述、文件名、图片内容

EXIF、压缩包、另一附件

上一层解码结果

**然后：**

OurSecret → Unhide → 输入密码 → 提取

### 3. 嵌套隐写题

这一类在 Misc 中更有价值：

carrier.jpg → OurSecret → secret.zip → 解压 → flag.png → zsteg/StegSolve → flag

MP4 → OurSecret → WAV → 频谱 → 二维码/文本

OurSecret 提取成功不代表题目结束，只代表拆掉一层。 提取结果一律先 file，再决定下一步。

## 四、补充说明

### 1. 识别重点是 EOF，不是 PNG

这是最需要修正的知识点。OurSecret 不是 PNG IDAT、zlib、DEFLATE padding bit，而是 EOF Data Injection。

公开研究对 OurSecret 2.5.5 做逆向取证后发现，OurSecret 修改过的文件会在原始载体结束位置之后增加固定结构，并存在一个稳定的 40 字节特征序列。因此它实际上可以通过签名和 EOF 异常进行检测，不能说 "目前没有检测方法，只能排除法判断"。

### 2. 010 Editor 是很实用的辅助工具

**JPEG：** 正常逻辑结束位置通常涉及 FF D9。如果看到正常 JPEG 数据 → FF D9 → 后面还有大量数据（数十 KB / 数 MB），就应该警惕 EOF 追加

**PNG：** 同理，可以检查 IEND 之后是否还有异常大量数据

**可能来源：** OurSecret、StegoStick、文件拼接、自定义 Append 隐写、其他 EOF 型工具。

### 3. 不要重新保存、转码载体

原因不是 DEFLATE padding bit 会改变，而是因为原文件 EOF 之后的 OurSecret 数据可能被编辑软件重新编码时直接截掉。例如：

stego.jpg → Photoshop/Photopea 重新导出 JPG → 重新生成 JPEG 文件 → 原来的 EOF 追加数据可能消失

视频转码也是同理。始终保留原始附件，在副本上操作。
