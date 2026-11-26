---
title: "业余无线电AFSK1200/AX.25信号处理"
summary: "Flag → Destination → Source → Digipeater → Control → PID → Information → FCS → Flag"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理

三层关系

| 层级 | 协议 | 说明 |
| --- | --- | --- |
| 物理调制 | AFSK1200（Bell 202） | 1200 baud，1200 Hz / 2200 Hz 双音 |
| 数据链路层 | AX.25 | 基于 HDLC 的帧协议，不是 TCP/IP |
| 应用层 | APRS | 常运行在 AX.25 UI 帧上 |

NRZI 编码

AX.25 使用 NRZI 线路编码：

音调发生切换 → bit 0

音调保持不变 → bit 1

AX.25 帧结构

Flag → Destination → Source → Digipeater → Control → PID → Information → FCS → Flag

Misc 中真正关心的是 Information（数据载荷）。

## 二、识别方法

### 1. 听感

快速的 "吱吱 / 嘟嘟 / 数字噪声"，不是正常语音或音乐。

### 2. 频谱特征（最重要）

1200 Hz 和 2200 Hz 附近出现明显两组频率成分并快速交替。

sox audio.wav -n spectrogram -o spectrum.png

或用 Audacity 看频谱图。

### 3. 题目关键词

APRS / AX.25 / packet radio / ham radio / AFSK / 1200 baud / Bell 202 / callsign / latitude / longitude / GPS

APRS + WAV 基本直接尝试 AFSK1200。

## 三、工具与解法

**核心工具：** SoX + multimon-ng

### 1. 首选：直接解 WAV

当前 multimon-ng 支持 -t wav，会自动调用 SoX，不需要先转 RAW：

multimon-ng -q -A -a AFSK1200 -t wav audio.wav

-a AFSK1200：指定解调器

-A：APRS/TNC2 格式输出

-q：减少无关信息

### 2. 排错：转标准 RAW

直接解没结果时，用 SoX 标准化：

sox audio.wav -c 1 -r 22050 -b 16 -e signed-integer -t raw audio.raw

multimon-ng -q -A -t raw -a AFSK1200 audio.raw

16-bit 是 multimon-ng RAW 输入要求，不是 AFSK1200 的 "标准位深"。

### 3. 一步管道

sox audio.wav -c 1 -r 22050 -b 16 -e signed-integer -t raw - | \

multimon-ng -q -A -t raw -a AFSK1200 -

## 四、输出解读与常见考点

输出格式（TNC2/APRS）

N0CALL>APRS,WIDE1-1:!4044.52N/07400.24W-Test

**N0CALL：** 源呼号

**APRS：** 目的地址

WIDE1-1：Digipeater 路径

冒号 : 后是 Information 字段（重点）

考点

| 考点 | 说明 |
| --- | --- |
| 直接 Flag | N0CALL>APRS:flag{...}，直接提取 |
| APRS 坐标 | !4044.52N/07400.24W → 度 + 分 / 60，W/S 为负 |
| 多包拼接 | 一段 WAV 多个 burst，按顺序拼接，tee decoded.txt 保存全部 |
| 信息字段套娃 | 可能是 Base64 / Hex / 坐标 / 文本，继续按正常 Misc 处理 |

APRS 坐标格式不只有 !DDMM.hhN/DDDMM.hhW，开头还可能是 =、/、@，也有压缩坐标，不要死记。

## 五、排错与注意事项

解不出来的排查顺序

确认是不是 AFSK1200：频谱看 1200/2200 Hz，不是就换 AFSK2400/FSK9600/POCSAG/DTMF 等

直接解 WAV：multimon-ng -q -A -a AFSK1200 -t wav audio.wav

标准化转 RAW：单声道 / 16-bit signed / 22050 Hz

**检查声道：** 立体声强制 -c 1，左右差异大时分别 remix 1 / remix 2 单独解

**检查音量：** sox audio.wav fixed.wav gain -n，但不要一开始就降噪滤波（会破坏音调切换）

CRC 错误

能看到数据包但 CRC error，说明已识别到部分帧，重点查信噪比、削波、声道、采样转换，而不是怀疑编码。

音频格式

.mp3 / .flac / .ogg 先用 soxi 查看，SoX 支持就直接转 RAW 再解。
