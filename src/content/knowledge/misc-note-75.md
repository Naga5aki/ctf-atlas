---
title: "avif相关考点"
summary: "AVIF 全称 AV1 Image File Format，是一种基于 AV1 编码的现代图像文件格式。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、基本概念与格式识别

### 1. 基本定义

AVIF 全称 AV1 Image File Format，是一种基于 AV1 编码的现代图像文件格式。

**AV1：** 负责图像压缩编码

HEIF / ISO-BMFF：负责文件组织和封装

**AVIF：** 使用 ISO-BMFF/HEIF 体系封装 AV1 图像

AV1 是编码方式，AVIF 是图像文件格式。

AVIF 不只是 "新版 JPG"，还支持：单张图片、多帧动画、透明 Alpha、高位深、HDR、宽色域、Grid 网格图像、多层 / 渐进式图像、元数据。

### 2. 内部结构

AVIF 由多个 Box 组成，不是简单的 "文件头 + 像素"：

AVIF

│

├─ ftyp      → 文件类型/兼容品牌

├─ meta      → 图像属性、索引、位置、关系

│   ├─ pitm

│   ├─ iloc

│   ├─ iinf

│   ├─ iprp

│   │   ├─ av1C

│   │   ├─ ispe

│   │   └─ pixi

│   └─ ...

└─ mdat / idat → 实际 AV1 编码数据

最需要掌握的三个 Box：

**ftyp：** 文件类型识别

**meta：** 图像属性、索引、位置、关系

**mdat：** 实际 AV1 编码数据

### 3. 文件识别

AVIF 属于 ISO-BMFF，文件前部可发现 ftyp（十六进制 66 74 79 70）。

AVIF 常见品牌：

avif → AVIF Image

avis → AVIF Image Sequence

**示例十六进制：**

00 00 00 20 66 74 79 70 61 76 69 66

f  t  y  p  a  v  i  f

CTF 里看到 ftypavif 应立刻想到 AVIF 图像。但不要死记成 "AVIF 固定文件头就是 ftypavif"，更准确是：ISO-BMFF 的 ftyp Box + AVIF 相关 brand。

### 4. 文件后缀不可信

flag.bin 但十六进制发现 ftyp avif → 实际是 AVIF，复制为 flag.avif 再解码

flag.avif 也不意味着一定是 AVIF

## 二、多帧与时间层

### 1. 单帧 vs 多帧

AVIF 既能保存静态图片，也能保存动态图像序列：

静态 AVIF → 一张图

多帧 AVIF → Frame 0 / Frame 1 / Frame 2 /...

多帧 AVIF 类似 GIF、Animated WebP，但使用 AV1 编码和 ISO-BMFF 时间轴。这是 CTF 中非常重要的考点。

### 2. 判断是否多帧

avifdec --info test.avif

**重点观察：** 图像数量、Image Sequence、帧数量、Progressive。如果确认存在多帧，不要只用普通图片查看器看第一帧。

### 3. 多帧拆帧

使用 libavif 自带的 avifdec：

\# 全部拆帧

avifdec --index all test.avif frame.png

\# 得到 frame-0000000000.png、frame-0000000001.png ...

\# 单独提取某帧（帧编号从 0 开始）

avifdec --index 0 test.avif frame0.png

avifdec --index 1 test.avif frame1.png

### 4. 帧间隔查看

ffprobe -v error \

-select_streams v:0 \

-show_frames \

-show_entries frame=pts_time,pkt_duration_time \

-of csv input.avif

**输出示例：**

frame,0.000000,0.100000

frame,0.100000,0.100000

frame,0.200000,0.500000

frame,0.700000,0.100000

**核心字段：**

pts_time → 帧出现时间

pkt_duration_time → 帧持续时间

**换算：** 秒 × 1000 = 毫秒（0.1s = 100ms，0.5s = 500ms）。

### 5. 帧间隔隐写

这是非常值得关注的 AVIF Misc 考点。例如：

100 ms = 0

500 ms = 1

得到序列 100 500 500 100 100 100 500 500 → 0 1 1 0 0 0 1 1 → 二进制 01100011 = 0x63 = c。

多帧 AVIF 不能只检查每一帧是什么，还必须检查每一帧什么时候出现、持续多久。

## 三、AVIF → PNG 转换

### 1. 重要考点

很多 CTF 工具不直接支持 AVIF（隐写分析、像素分析脚本、二维码工具、图像通道工具、LSB 工具、图片差分工具），而 PNG 兼容性非常好。常见流程：

AVIF → 解码 → PNG → 进一步分析

有些题不会直接要求 "分析 AVIF"，而是设计成：flag.avif → 普通隐写工具打不开 → 转成 PNG → 再使用图像分析工具 → 发现真正 flag。隐藏的考点是格式转换是分析链的一部分。

### 2. 为什么优先转 PNG 而不是 JPG

AVIF → JPG：JPG 又会进行一次有损压缩，可能破坏像素细节、细微颜色变化、边缘特征、透明通道、隐写特征

AVIF → PNG：PNG 本身采用无损编码，不会引入新的有损压缩

**注意：** 如果原 AVIF 本身就是有损压缩的，转换成 PNG 并不能恢复已经丢失的信息，它只是把当前解码出来的像素无损保存为 PNG。

### 3. 单帧转 PNG

**方法一：** avifdec（首选）

avifdec input.avif output.png

**方法二：** ImageMagick

magick input.avif output.png

是否能成功读取 AVIF 取决于本机 ImageMagick 是否包含对应 AVIF/HEIF 解码支持。比赛环境中 avifdec 通常更专业直接。

**方法三：** FFmpeg

ffmpeg -i input.avif output.png

FFmpeg 在 AVIF 上更适合查看帧、查看时间轴、批量处理；单纯做解码推荐优先 avifdec。

### 4. 多帧转 PNG 的特殊性

假设 animation.avif 有 100 帧，不能简单理解为 animation.avif → animation.png（普通 PNG 只是一张静态图）。正确思路是逐帧解码：

avifdec --index all animation.avif frame.png

\# 得到 frame000.png、frame001.png、frame002.png ...

### 5. 转换 PNG 后会丢掉什么信息

原 AVIF 各帧有不同延时（如 Frame 0→100ms，Frame 1→500ms），拆成 PNG 后，PNG 文件本身通常不会保存原 AVIF 的帧时间轴。因此：

AVIF 拆帧 ≠ 完整保留 AVIF 全部信息

如果题目可能涉及帧延时，必须：拆帧（avifdec）+ 单独保存时间信息（ffprobe），二者配合。

### 6. 高位深问题

AVIF 可保存 8-bit / 10-bit / 12-bit。如果原文件是 10-bit AVIF，直接转 8-bit PNG 可能把细微像素差异量化掉，这对隐写非常危险。

怀疑高位深隐写、微小像素差、HDR 信息时：

avifdec -d 16 input.avif output.png

保存成 16-bit PNG，更有利于保留高精度像素信息。

普通查看 → 8-bit PNG；像素隐写 / 高位深 / HDR → 优先尝试 16-bit PNG。

### 7. Alpha 透明通道

AVIF 支持 Alpha。表面看到纯白图、透明图、什么都没有，并不一定真的没有信息：

RGB → 正常图像，Alpha → flag

RGB → 白色，Alpha → QR Code

PNG 本身支持 Alpha，所以 AVIF RGBA → PNG RGBA 是非常适合进一步分析的形式。转换后单独检查 R、G、B、Alpha 四个通道，不要无意中丢掉 Alpha 通道。

### 8. 转 PNG 后做 LSB 的坑

如果原 AVIF 使用有损 AV1 编码，编码过程中像素可能已经发生变化。因此不能简单认为：

PNG 像素最低位 = 原始图片像素最低位

如果 flag 是在原始像素 LSB 中写入，然后再进行有损 AVIF 压缩，LSB 信息很可能已经被破坏。

## 四、帧差隐写

多帧 AVIF 中尤其值得注意。例如 Frame0/Frame1/Frame2/Frame3 肉眼看几乎完全相同，但实际上：

Frame0 XOR Frame1 → 二维码 / 字符 / flag

**典型分析方式：**

AVIF → 逐帧 PNG → 像素比较 → 差值 / XOR / absdiff

**逻辑：** diff = abs(frame1 - frame0)，再放大差值、二值化，可能直接出现隐藏图案。

## 五、组织层特殊结构

### 1. 多层与多帧不要混淆

AVIF 支持 Image Sequence，也支持 Progressive / Layered Image：

| 类型 | 维度 | 说明 |
| --- | --- | --- |
| 多帧 | 时间维度 | Frame0 → Frame1 → Frame2 → Frame3 |
| 多层 | 质量 / 空间层级 | Layer0（模糊）→ Layer1（更清晰）→ Layer2（完整图像） |

avifdec --info 中看到 progressive/layer 信息时不要误认为一定是动画。

### 2. Grid 网格图像

AVIF 可将一张完整图片拆成 A B C / D E F / G H I，通过 Grid 元数据告诉解析器 3×3，最终重新组合成完整图片。

如果直接分析底层数据发现很多小图片块，不要立即认为是多帧，还可能是 Grid Derived Image。

## 六、元数据与附加数据

### 1. 元数据分析

AVIF 可能携带 Exif、XMP、ICC、颜色信息、时间、设备信息、描述。

exiftool input.avif

**重点观察：** Comment、Description、Software、Date、GPS、XMP、Exif、ICC Profile。2. 文件附加与拼接

AVIF 本身正常打开，不代表文件只有图片。例如：

AVIF + ZIP

... mdat

PK 03 04    ← ZIP 常见文件头（50 4B 03 04）

**依然可以：**

binwalk input.avif

strings input.avif

检查 ZIP、RAR、文本、URL、flag。

## 七、Box 结构损坏与工具

### 1. Box 结构损坏

AVIF 作为 ISO-BMFF 格式，基本结构是：

Box

├─ Size

├─ Type

└─ Payload

例如 00 00 00 20 66 74 79 70 ... 表示 Size + ftyp + Payload。

如果题目故意修改 Box size、Box type、item offset、iloc、brand，可能导致浏览器打不开、avifdec 报错。这时进入 010 Editor / HxD 手工分析结构。

### 2. 工具选择

| 工具 | 主要用途 |
| --- | --- |
| file | 文件类型初步识别 |
| ExifTool | 元数据 |
| avifdec | AVIF 解码、信息查看、拆帧 |
| ffprobe | 帧时间轴、帧间隔 |
| FFmpeg | 转换、批量处理 |
| ImageMagick | 图片格式转换、像素处理 |
| 010 Editor | Box 结构分析 |
| HxD | 十六进制检查 |
| binwalk | 嵌入 / 附加文件 |
| strings | 字符串 |
| Python/OpenCV/Pillow | 帧差、通道、像素分析 |

## 八、AVIF 考点总表

| 考点 | 典型现象 | 处理 |
| --- | --- | --- |
| 文件格式伪装 | 后缀不是 AVIF | 查 ftyp /avif |
| 单帧 AVIF | 工具打不开 | 转 PNG |
| 多帧 AVIF | 只看到一张图 | 全部拆帧 |
| 指定帧藏 flag | 动画闪得很快 | 逐帧查看 |
| 帧间隔隐写 | 图像内容正常 | ffprobe |
| 帧差隐写 | 各帧几乎一样 | PNG 后做差 / XOR |
| Alpha 隐写 | 图像透明 / 空白 | 提取 Alpha |
| 高位深隐写 | 8-bit 看不出异常 | 转 16-bit PNG |
| Grid | 多个碎图片 | 分析 Grid |
| Progressive | 像多帧但其实是层 | 区分帧与层 |
| 元数据 | 图片本身正常 | ExifTool |
| 尾部追加 | AVIF 正常但仍无 flag | binwalk |
| 字符串隐藏 | 二进制中藏文本 | strings |
| Box 损坏 | 文件无法解码 | 010 Editor |
| 格式转换链 | AVIF 工具支持差 | AVIF → PNG → 后续分析 |
