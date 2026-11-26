---
title: "UDP 视频流恢复（MPEG-TS / H.264）"
summary: "典型题目给 xxx.pcap / xxx.pcapng，打开后发现大量 UDP、MPEG TS、H.264、PAT、PMT、video-stream。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、题型定位

典型题目给 xxx.pcap / xxx.pcapng，打开后发现大量 UDP、MPEG TS、H.264、PAT、PMT、video-stream。最终目标不是分析协议，而是：

PCAP → 恢复视频 → 播放视频 → 画面/字幕/声音中获得信息 → Flag / 密码 / 下一阶段文件

属于流量分析 + 文件恢复 + 多媒体取证。

## 二、四层关系

UDP

↓

MPEG-TS

↓

PES

↓

H.264

↓

NAL Unit

↓

视频画面

| 层次 | 内容 | 作用 |
| --- | --- | --- |
| UDP | 网络传输 | 把数据通过网络发送 |
| RTP（可选） | 媒体传输层 | 给媒体增加序号、时间戳 |
| MPEG-TS | 媒体封装 | 把音视频等数据组织起来 |
| PES | 中间封装 | 承载具体音视频 Elementary Stream |
| H.264 / AVC | 视频编码 | 对视频画面进行压缩编码 |
| NAL Unit | 编码单元 | H.264 内部基本数据单元 |

UDP ≠ MPEG-TS ≠ H.264。最简单理解：UDP = 快递运输，MPEG-TS = 快递箱，H.264 = 箱子里面压缩后的视频内容。

## 三、两种常见网络结构

### 1. MPEG-TS 直接跑在 UDP 上

Ethernet → IP → UDP → MPEG-TS → H.264

**恢复思路：** 提取 UDP Payload → 直接拼接 → .ts

### 2. MPEG-TS 跑在 RTP/UDP 上

Ethernet → IP → UDP → RTP → MPEG-TS → H.264

不能简单把整个 UDP Payload 全部拼起来，因为前面还有 RTP Header，必须去除 RTP 头，只拼 RTP Payload。

做题前第一件事不是 "直接提取 UDP"，而是判断 UDP → TS 还是 UDP → RTP → TS。

## 四、MPEG-TS 基础特征

### 1. 188 字节固定包

MPEG-TS（MPEG Transport Stream）本来为电视广播、实时视频、IPTV 等不稳定传输环境设计，由很多固定长度小包组成：

标准 MPEG-TS Packet = 188 Bytes

```text
┌───────────────────────────┐
```

```text
│ TS Header                   │
```

```text
├───────────────────────────┤
```

```text
│ Adaptation Field（可选）   │
```

```text
├───────────────────────────┤
```

```text
│ Payload                     │
```

```text
└───────────────────────────┘
```

### 2. 最重要特征：0x47 Sync Byte

标准 TS Packet 第一个字节 = 0x47（Sync Byte）。正常 TS：

Offset 0   → 47

Offset 188 → 47

Offset 376 → 47

Offset 564 → 47

即每隔 188 字节出现一个 47。提取出数据后检查这个周期，是极强的 MPEG-TS 特征。

### 3. 为什么 UDP 包经常不是 188 字节

一个 TS Packet = 188 Bytes，但不代表一个 UDP Packet = 一个 TS Packet。发送方通常一次把多个 TS Packet 放进一个 UDP 包，最经典：

188 × 7 = 1316 Bytes

因此经常看到 UDP Payload = 1316 Bytes，里面是 7 个 TS Packet。UDP 包长度不是判断 TS Packet 长度的依据，真正的 TS 内部单位还是 188 Bytes。

## 五、MPEG-TS 内部结构

### 1. PAT（Program Association Table，节目关联表）

固定使用 PID = 0x0000

**作用：** 告诉播放器这个 TS 里有哪些节目、这些节目的 PMT 在哪里

可以理解为 MPEG-TS 的总目录

### 2. PMT（Program Map Table，节目映射表）

PAT 找到 PMT 后，PMT 再告诉播放器视频在哪里、音频在哪里、分别是什么编码

**例如：** Video PID = 0x0100（H.264），Audio PID = 0x0101（AAC）

**逻辑链：**

PAT → 找到 PMT → PMT → 找到视频 PID → H.264

### 3. PID（Packet Identifier）

13 bit 标识，用于区分 TS 中不同数据流（PAT、PMT、H.264 视频、AAC 音频、字幕、PCR 等）

具体 PID 不固定，只有 PAT PID = 0x0000 是标准固定值

### 4. PAT + PMT + H.264 识别组合

如果 Wireshark 同时出现 PAT、PMT、H.264，逻辑几乎就是：这不是普通 UDP 数据，而是 MPEG-TS，里面包含视频节目，视频编码是 H.264。这是 MPEG-TS 视频流非常强的识别组合。

### 5. TS Header 核心字段

188 字节 TS Packet 前面 4 字节 Header，CTF 最值得掌握：

Sync Byte = 0x47

PID

PUSI（Payload Unit Start Indicator）：当前 TS Packet 的 Payload 是否包含新的上层结构起点（PES 开始、PAT 开始、PMT 开始）

Continuity Counter：4 bit，0→1→2→...→15→0，每个 PID 维护一个

### 6. Continuity Counter 进阶考点

如果某个 PID 的 CC 从 5 6 7 变成 5 6 9，说明中间有包丢失。恢复视频后卡顿、花屏、无法解码时，可以检查 CC，这是区分 "提取方式错了" 和 "原抓包本身丢包" 的方法。

### 7. PES（Packetized Elementary Stream）

MPEG-TS 不是直接把完整 H.264 塞进去，结构是 TS Packet → PES → H.264。PES 把 H.264、AAC 等 Elementary Stream 再包装一层。

典型 PES 起始码：00 00 01

后面跟 Stream ID、PES Length、PTS、DTS 等

00 00 01 E0 中 E0 经常表示视频 Stream ID

### 8. H.264 NAL Unit

H.264 内部主要由 NAL Unit 组成，常见起始形式：00 00 01 或 00 00 00 01。

典型 H.264 Annex B：

00 00 00 01 67 ...  → SPS（Sequence Parameter Set）

00 00 00 01 68 ...  → PPS（Picture Parameter Set）

00 00 00 01 65 ...  → IDR（关键帧）

| NAL类型 | 含义 |
| --- | --- |
| SPS | Sequence Parameter Set |
| PPS | Picture Parameter Set |
| IDR | 关键帧 |
| Slice | 普通视频片段 |

## 六、Wireshark 识别与目标流定位

### 1. 核心识别特征

Statistics → Protocol Hierarchy：看 UDP 是否占大量流量

Statistics → Conversations → UDP：找 Packets 多、Bytes 大、持续时间长的 UDP 流

Wireshark Protocol 列出现 MPEG TS、H.264、RTP

Info 中出现 Program Association Table、Program Map Table、video-stream

### 2. 常用过滤器

| 目的 | 过滤表达式 |
| --- | --- |
| 看所有 UDP | udp |
| 按端口过滤 | udp.port == 5555 |
| 指定完整方向 | ip.src == 192.168.1.10 && udp.srcport == 5000 && udp.dstport == 5555 |
| 指定 UDP 流 | udp.stream eq 3 |

### 3. udp.stream 字段

Wireshark 给不同 UDP 会话编号，可右键 Follow → UDP Stream 或过滤 udp.stream eq 3。相比 udp.port == 5555，如果同一端口同时存在多个会话，可以只锁定其中一条。

## 七、数据提取与重组

### 1. 确定真正要提取哪一层（恢复成败关键）

| 结构 | 提取内容 |
| --- | --- |
| UDP → MPEG-TS | UDP Payload |
| UDP → RTP → MPEG-TS | RTP Payload（去 RTP Header） |
| UDP → 自定义协议 → MPEG-TS | 去自定义协议 Header |

**原则：** 最终写入 .ts 的内容必须尽可能只包含 MPEG-TS 原始字节。

### 2. 为什么不能直接把整个 UDP 包写进 .ts

如果把 [Ethernet][IP][UDP][TS] 整个写入，TS 解码器会看到大量非 TS 数据，无法正常解析。正确做法是只提取 Payload。

### 3. TShark 提取 UDP Payload

tshark -r capture.pcapng \

-Y "udp.port == 5555" \

-T fields \

-e udp.payload > udp_payload.txt

得到的是原始二进制的十六进制表示（如 4740111000...），不是 ASCII 视频。

### 4. Hex → Binary（unhexlify）

文件里存的是字符 '4' '7' '4' '0'...，而真正 TS 要的是字节 47 40 11 10，需要转换：

from pathlib import Path

hex_data = Path("udp_payload.txt").read_text()

hex_data = "".join(hex_data.split())   # 删除换行/空格

data = bytes.fromhex(hex_data)

Path("video.ts").write_bytes(data)

**关键步骤：** 读取 hex → 删除换行 / 空格 → hex → bytes → 二进制写入 .ts。

### 5. 为什么直接拼 UDP Payload 有时成立

发送方把 TS1 TS2 放进 UDP1，TS3 TS4 放进 UDP2，提取后 Payload1 + Payload2 + Payload3 = 原始 TS 序列，恢复成功。

### 6. UDP 直接拼接的三个风险

UDP 无连接、不保证可靠、不保证顺序、不保证到达，理论上可能存在：

乱序

丢包

重复

CTF 中特别是 127.0.0.1 → 127.0.0.1 本机通信往往非常稳定，按 PCAP 捕获顺序拼接就能恢复；真实网络环境则不能完全依赖。

### 7. RTP 的顺序优势

RTP Header 有 Sequence Number、Timestamp、SSRC、Payload Type。其中 Sequence Number（100→101→102→103）可以帮助判断顺序、检测丢包、重新排序。

### 8. IP 分片坑

UDP 数据包超过 MTU 可能发生 IP Fragmentation，一个 UDP Datagram 被拆成多个 Fragment。不能简单把某一个 IP Fragment 当成完整 UDP Payload。Wireshark/TShark 一般能在条件允许时 Reassemble fragmented IP datagrams，恢复时应尽量使用重组后的 UDP Payload。

## 八、验证与转封装

### 1. 验证恢复出的 .ts（三类验证）

方法 1：检查 0x47 周期

offset 0   → 47

offset 188 → 47

offset 376 → 47

方法 2：ffprobe

ffprobe video.ts

正常显示 Input #0, mpegts、Stream #0:0: Video: h264，能识别 mpegts + h264 基本说明数据结构正确。

方法 3：ffmpeg

ffmpeg -i video.ts

出现 Program、Stream、Video: h264，说明 PAT、PMT、PES、H.264 基本都能正常解析。

### 2. .ts 直接能播放

VLC、ffplay、PotPlayer 通常都能直接播放 .ts，所以 .ts → .mkv 不是恢复视频的必需步骤，更多是提高兼容性、方便播放器打开、方便后续处理。

### 3. ffmpeg -c copy（转封装 Remux）

ffmpeg -i video.ts -c copy video.mkv

**表示：** 输入容器 MPEG-TS、视频编码 H.264 → 重新封装 → 输出容器 MKV、视频编码 H.264。H.264 没变，只是 TS → MKV，这叫 Remux / 转封装。

### 4. 不要和转码混淆

| 操作 | 是否重新编码 | 速度 |
| --- | --- | --- |
| -c copy | 否 | 非常快 |
| -c:v libx264 | 是 | 较慢 |

CTF 恢复优先 -c copy，因为不破坏原流。

## 九、常见错误

| 错误 | 表现 | 解决 |
| --- | --- | --- |
| 提取成了整个 Packet | 0x47 不规律，ffprobe 识别失败 | 只提取 UDP Payload |
| RTP 头没有去除 | 188-byte 对齐被不断破坏，0x47 周期异常，大量 sync byte 错误 | 去 RTP Header，只拼 RTP Payload |
| TS 起点错位 | 如 AA BB CC DD 47...，真正 TS 从 offset 4 开始 | 寻找 offset 使 data[offset]==0x47 且 data[offset+188]==0x47、data[offset+376]==0x47 连续成立（TS synchronization / 对齐） |
| 抓包从视频中途开始 | 开头缺 PAT/PMT 或 SPS/PPS，播放器一开始无法播放 | MPEG-TS 通常周期性发送 PSI 表，过一段时间后可能恢复 |
| 丢包造成花屏 | 画面块状、花屏、短暂卡顿，但文件依然可以播放 | UDP 视频即使丢一部分数据仍可能有较强容错性，不要认为恢复一定失败 |

## 十、进阶内容

### 1. PAT/PMT 找目标视频 PID（TS Demux）

如果一个 TS 里面多个 PID，只想提 H.264：PAT → PMT PID → PMT → H.264 PID，然后只分析该 Video PID。这属于更高级的 TS demux（把 Multiplexed Transport Stream 中的不同流拆开）。

### 2. Mux / Demux

Mux（复用）：Video + Audio + Subtitle → MPEG-TS

Demux（解复用）：MPEG-TS → Video + Audio + Subtitle

这也是 FFmpeg 常见操作。

### 3. 单独提 H.264

ffmpeg -i video.ts -map 0:v:0 -c:v copy video.h264

得到裸 H.264 elementary stream，结构从 TS → PES → H.264 变成 H.264，在分析 SPS、PPS、NALU 时很有用。

### 4. 与普通文件 Carving 的关系

普通文件 carving：磁盘镜像 → 找 JPEG/ZIP/PNG 文件头 → 恢复文件。

**网络视频恢复：** PCAP → 找到目标 Stream → 提取 Payload → 重组原始媒体文件。

本质非常相似，都是在更底层的数据中恢复高层文件结构，这类题也可理解为 Network File Carving。
