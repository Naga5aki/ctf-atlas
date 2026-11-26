---
title: "GIF拆帧与修改帧"
summary: "GIF为优化体积，允许单帧仅保存变化的局部矩形区域，通过偏移量定位到画布对应位置，而非每帧都是完整图片。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心基础认知

### 1.局部帧机制

GIF为优化体积，允许单帧仅保存变化的局部矩形区域，通过偏移量定位到画布对应位置，而非每帧都是完整图片。

逻辑画布（Canvas Size）：动画整体的显示区域尺寸，全局唯一

帧矩形（Frame Rectangle Size）：单帧实际保存的图像区域尺寸，每帧可不同

实际播放画面=前序帧状态+当前帧局部更新+Disposal规则

### 2.两个核心区分

| 操作类型 | 作用 |
| --- | --- |
| coalesce | 根据偏移、Disposal、前后帧关系，将局部优化帧还原为完整画布大小的显示帧 |
| resize/scale | 修改图像内容的像素尺寸，可能拉伸变形 |
| pad/extent | 修改画布尺寸，不改变内容大小，空余区域补边 |

## 二、GIF拆帧

### 1.基础拆帧

直接导出原始帧，适合结构完整、每帧尺寸一致的GIF。

### 1）FFmpeg方式

mkdir-p frames

ffmpeg-i input.gif frames/frame_%04d.png

%04d表示四位数字编号，保证文件排序正确。

### 2）ImageMagick方式

mkdir-p frames

magick input.gif frames/frame_%04d.png

### 2.完整合成帧拆帧

局部优化帧直接导出会是碎片，必须先还原为完整显示帧再分析。

核心参数-coalesce：按照帧偏移、Disposal Method、前后帧依赖关系，将每帧还原为完整画布大小的实际播放画面

**命令：**

mkdir-p frames

magick input.gif-coalesce frames/frame_%04d.png

**适用场景：** 人工逐帧观察、多帧叠加/XOR/差分分析

### 3.帧信息查看

### 1）查看所有帧的尺寸、偏移、格式

magick identify input.gif

**输出格式示例：** 100x40+320+150，代表「宽度×高度+左偏移+上偏移」。

### 2）统计总帧数

ffprobe-v error-select_streams v:0-count_frames\

-show_entries stream=nb_read_frames\

-of default=nokey=1:noprint_wrappers=1 input.gif

### 4.提取指定范围帧

通过FFmpeg select过滤器提取部分帧，减少分析量：

ffmpeg-i input.gif\

-vf"select='between(n,10,20)'"\

-vsync 0 frames/frame_%04d.png

帧编号n从0开始计数。

### 5.快速人工排查

StegSolve快速逐帧浏览

**重点关注：** 突然出现的文字、二维码片段、异常黑白块、与其他帧差异极大的内容、极短时长帧。

### 6.拆帧核心用途

定位肉眼不可见的极短闪帧

提取拆分到多帧的隐藏内容

为帧间差分、XOR、叠加分析准备素材

## 三、帧几何分析

### 1.两套尺寸结构（二进制层面）

GIF存在全局画布和单帧两套独立的宽高定义，均为2字节小端存储。

### 1）逻辑画布描述符（全局）

**紧跟GIF文件头之后：**

| 相对偏移 | 长度 | 字段 |
| --- | --- | --- |
| +0x06 | 2字节 | Logical Screen Width（画布宽度） |
| +0x08 | 2字节 | Logical Screen Height（画布高度） |

**示例：** 80 02 E0 01→宽度0x0280=640，高度0x01E0=480。

### 2）图像描述符（单帧）

每帧对应一个，起始标志为0x2C：

| 相对0x2C偏移 | 长度 | 字段 |
| --- | --- | --- |
| +0x01 | 2字节 | Left Position（帧左偏移） |
| +0x03 | 2字节 | Top Position（帧上偏移） |
| +0x05 | 2字节 | Width（帧宽度） |
| +0x07 | 2字节 | Height（帧高度） |

### 2.Disposal Method（处置方式）

定义当前帧播放结束后，画布的处理规则，是影响帧合成的关键参数：

**0/1：** 保留当前帧，下一帧在其基础上叠加

2：恢复为背景色

3：恢复为上一帧的状态

这也是原始局部帧不能直接代表显示效果的核心原因，-coalesce会自动按规则完成帧合成。

## 四、帧尺寸批量统一

拆帧后若尺寸不一致，做帧间XOR、差分、叠加分析前需要先标准化尺寸。分为内容缩放和画布扩展两类操作。

### 1.FFmpeg方式

（1）强制固定尺寸（拉伸变形）

直接拉伸到指定宽高，不保持比例，适合已知原图被故意压缩/拉伸的恢复场景。

mkdir-p resized

ffmpeg-framerate 1-i frames/%04d.png\

-vf"scale=800:600"resized/%04d.png

（2）统一宽度，保持比例

固定宽度，高度自动计算，保持宽高比；最终高度可能不一致。

ffmpeg-framerate 1-i frames/%04d.png\

-vf"scale=800:-2"resized/%04d.png

-2表示自动计算高度并保证为偶数，仅PNG输出时无强制要求。

（3）固定画布，不拉伸（CTF首推）

按比例缩放至目标范围内，空余区域补黑边居中，所有输出尺寸完全一致，无变形。

ffmpeg-framerate 1-i frames/%04d.png\

-vf"scale=800:600:force_original_aspect_ratio=decrease,pad=800:600:(ow-iw)/2:(oh-ih)/2:black"\resized/%04d.png

（4）最近邻缩放（二维码/像素图专用）

黑白二维码、像素字体等硬边图形，使用最近邻插值避免模糊：

ffmpeg-framerate 1-i frames/%04d.png\

-vf"scale=800:600:force_original_aspect_ratio=decrease:flags=neighbor,pad=800:600:(ow-iw)/2:(oh-ih)/2:white"\resized/%04d.png

### 2.ImageMagick方式

批量处理更便捷，使用mogrify批量操作指定路径文件。

（1）强制拉伸固定尺寸

mkdir-p resized

magick mogrify-path resized-resize 800x600!frames/*.png

!表示忽略原始比例，强制适配目标尺寸。

（2）保持比例+固定画布（推荐）

mkdir-p resized

magick mogrify-path resized\

-resize 800x600\

-background black-gravity center-extent 800x600\

frames/*.png

-resize：按比例缩放到800×600范围内

-extent：扩展画布到固定尺寸

-gravity center：内容居中

（3）仅扩展画布，不缩放内容

若内容尺寸正确，仅画布大小不同，直接补边即可，避免缩放损失精度：

magick mogrify-path resized\

-background black-gravity center-extent 1024x768\

frames/*.png

（4）最近邻缩放（二维码）

magick mogrify-path resized\

-filter point-resize 800x600\

-background white-gravity center-extent 800x600\

frames/*.png

-filter point即最近邻插值，适合整数倍放大像素图。

## 五、异常宽高修复

**注意：** 修改导出图片的尺寸≠修改GIF文件结构宽高；前者是视觉处理，后者是二进制结构修复。只有确认字段被篡改时，才需要二进制级修改。

### 1.整体画布宽高损坏

**现象：** 显示裁剪、画布异常、部分帧超出边界

**修复位置：** GIF头后+0x06~+0x09的Logical Screen Width/Height

**操作：** 根据实际内容、其他帧推测正确画布尺寸，用010 Editor修改对应小端数值

### 2.单帧宽高/偏移损坏

**现象：** 单帧错位、截断、花屏、后续帧解析失败

**修复位置：** 对应帧0x2C图像描述符中的Width、Height、Left、Top字段

**修改禁忌：** 不可随意放大帧宽高，帧数据由LZW压缩生成，数据量与尺寸匹配，改大会导致解码报错、数据截断

**Offset异常：** 若Left/Top被改得过大，内容会移出画布范围，肉眼不可见，修正偏移即可显现隐藏内容
