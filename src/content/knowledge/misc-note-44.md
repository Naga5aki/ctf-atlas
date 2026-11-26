---
title: "MIDI隐写"
summary: "MIDI（Musical Instrument Digital Interface）不是音频波形文件，它记录的是演奏事件：音符音高 Note、音符力度 Veloci…"
module: "Misc"
topic: "音频与信号"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

MIDI（Musical Instrument Digital Interface）不是音频波形文件，它记录的是演奏事件：音符音高 Note、音符力度 Velocity、事件时间、乐器 Program Change、控制器 Control Change、弯音 Pitch Bend、SysEx、文本 / 歌词 / 标记等 Meta Event。CTF 隐写通常就是利用这些事件的参数、时间关系或额外事件数据保存信息。

遇到 .mid / .midi + 可正常播放 + 听起来无异常 + strings/binwalk 无结果，不要按 WAV/MP3 的波形 / 频谱 / 音频 LSB 方向分析，而应解析 MIDI 事件本身。

## 一、MIDI 文件结构

标准 MIDI 文件大致可理解为：

MThd（文件头）→ MTrk（轨道1）→ MTrk（轨道2）→ ...

每条轨道内部由大量事件构成：时间间隔（Delta Time）+ MIDI/Meta/SysEx 事件。

## 二、四类主要考法

### 1. 时间间隔 / Delta Time 隐写

MIDI 轨道中每个事件前都有一个 Delta Time，表示当前事件距离前一个事件经过了多少 MIDI ticks。出题人对时间间隔做极小幅调整（如 120→121），利用偶数→0、奇数→1，或最后 1bit / 最后 2bit、两种特定时间间隔编码信息。只改变极少量 tick，音乐整体听感几乎无区别。

**重要坑：** midi2csv 输出中的 Time 字段通常是该轨道中的绝对 MIDI 时间位置，不是直接的 delta_time。真正的 Delta Time = 当前事件 Time - 上一个事件 Time，不能看到 Time 列后直接提取最低位。

### 2. Velocity 力度隐写

Note On 事件包含 Channel、Note、Velocity。如果力度只在 64/65 之间有规律变化，就很值得怀疑，可能编码 64→0、65→1，或直接取 Velocity & 1。也可能使用 60/61、80/81、100/101，本质相同。

**注意：**

MIDI Velocity 是 7-bit 数据（0～127），不存在把普通 velocity 的 "第 8 位最高位" 当信息位的做法

Note On + Velocity = 0 在 MIDI 中通常等价于 Note Off，不能简单把所有 Velocity=0 的事件都当成普通音符力度数据

### 3. Control Change / 其他事件参数隐写

MIDI 支持大量控制器（Modulation、Volume、Pan、Expression、Sustain 等），一个 Control Change 包含 Controller Number 和 Controller Value。如果发现大量重复 Controller 事件、控制器编号始终相同、数值只在两个相邻值之间变化、某些事件对音乐几乎不起作用，就应重点分析这些参数。

类似思路还可出现在 Program Change、Pitch Bend、Aftertouch、Channel Pressure 等事件中。

### 4. Meta Event / SysEx 直接藏数据

MIDI 中存在很多 Meta Event：Text、Copyright、Track Name、Instrument Name、Lyrics、Marker、Cue Point、Sequencer Specific，里面本身就可以保存字符串或任意数据。拿到 MIDI 后第一遍就应检查所有 Meta Event，可能直接看到 Text_t, "flag{...}"，或 Lyric/Marker/Sequencer_specific 中存在 Base64、Hex、压缩数据、flag 片段。

SysEx（System Exclusive）是 MIDI 标准定义的系统专用消息，不是 "非标准未知事件"，可携带厂商或设备专用数据。真正值得怀疑的是异常长 SysEx、大量重复 SysEx、SysEx 数据呈 ASCII/Base/ 文件头特征。

## 三、实战第一步：midi2csv

这是 MIDI 题最实用的第一步，把 MIDI 变成人能看的事件列表。

sudo apt install midicsv

midicsv input.mid output.csv

\# 或 midicsv input.mid > output.csv

然后用 VS Code / Notepad++ / 010 Editor / LibreOffice Calc 打开 CSV，典型格式：

1, 0, Header, ...

2, 0, Start_track

2, 0, Tempo, 500000

2, 0, Note_on_c, 0, 60, 64

2, 120, Note_off_c, 0, 60, 0

2, 120, Note_on_c, 0, 62, 65

**前三列：** 轨道号、事件时间、事件类型，后面是对应事件参数。

## 四、标准排查顺序

MIDI → midi2csv

↓

① 先搜明显文本（Text/Lyric/Marker/Track_name/Copyright/Sequencer_specific/System_exclusive，以及 flag/CTF/Base64/PK）

↓

② 检查 Velocity（搜 Note_on_c，看最后一个字段是否两个相邻值反复出现、奇偶分布有规律）

↓

③ 分析事件时间（同轨当前Time - 上一个Time = Delta Time，关注Note On之间/Note Off之间/同类型事件之间/连续所有事件之间的时间差）

↓

④ 检查 Control Change（搜 Control_c，看最后一个字段是否两个相邻值规律变化）

↓

⑤ 其他 MIDI 参数

## 五、多轨 MIDI 是重点坑

标准 MIDI 可能存在多个 Track，其中：

Track 1 经常只放 Tempo、Time Signature、Track Name

真正的音符可能在 Track 2、Track 3

隐写数据甚至可能专门藏在一个几乎不参与演奏的轨道中

不要只分析第一个 Track，应逐轨检查事件数量、事件类型、时间规律、Velocity、Controller、Meta Event。一个轨道如果正常轨道有几千个音符，异常轨道只有几十 / 几百个规律事件，后者反而很值得关注。

## 六、010 Editor 的作用

如果 midi2csv 看不出来，用 010 Editor 分析 MIDI 原始结构：

MIDI 文件头：4D 54 68 64（MThd）

**轨道：** 4D 54 72 6B（MTrk）

主要用于检查文件结构异常、额外数据、轨道块长度、SysEx 原始内容、Meta Event 原始内容、文件尾附加数据。

不建议一开始就在十六进制里手拆 Delta Time，因为 Delta Time 使用 Variable Length Quantity（VLQ，可变长度数量编码），可能占 1~4 字节（字节最高位 1 表示后面还有 VLQ 字节，0 表示当前 VLQ 结束），手工解析很容易错位。事件分析 midi2csv 优先，原始结构 010 Editor 补充。

## 七、其他实用可视化工具

| 工具 | 用途 |
| --- | --- |
| midi2csv | 最重要，查看事件数据 |
| MIDIEditor / Sekaiju | 查看 Piano Roll、Velocity、Controller、不同轨道、事件列表；Velocity 隐写（64 65 64 65）在编辑区域可能直接表现规则变化 |
| 010 Editor | 底层文件结构 |
| MuseScore | 查看乐谱、观察异常音符、判断某轨道是否明显不自然（不是专门隐写分析工具） |

## 八、高频误区

| 错误认知 | 正确结论 |
| --- | --- |
| MIDI 当普通音频用 Audacity 分析 | Audacity 导入渲染得到的是合成后 PCM 波形，原始 Velocity/Meta/SysEx/Control Change/Delta Time 编码信息已无法按原结构分析；MIDI 隐写首先分析事件，不是声音 |
| midi2csv 的 Time 列就是 Delta Time | Time 是绝对时间位置，Delta Time = 相邻事件时间差 |
| 90%/70% 都是 Delta Time | CTF 没有可靠固定占比，应按低成本优先：文本 / Meta/SysEx → Velocity → 时间规律 → Controller → 其他事件 |
| Velocity 可以取第 8 位 | Velocity 是 7-bit（0~127），不存在第 8 位 |
| SysEx 是非标准未知事件 | SysEx 是 MIDI 标准定义的系统专用消息 |
| Note On Velocity=0 是普通力度数据 | 通常等价于 Note Off |
| 只分析第一个 Track | 隐写可能藏在几乎不参与演奏的异常轨道中 |
