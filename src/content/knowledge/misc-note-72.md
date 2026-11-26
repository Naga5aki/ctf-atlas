---
title: "文件格式明文攻击"
summary: "EXE 明文攻击 ≠ 利用 MZ。4D 5A 只有 2 字节，远远不够。真正利用的是很多 Windows PE 文件中由链接器生成的默认 DOS Stub。"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、速查表

| 文件格式 | 可利用的典型已知明文 | 常见-o | 实战可靠性 | 使用要点 |
| --- | --- | --- | --- | --- |
| PE / EXE / DLL | 默认 DOS Stub，如 This program cannot be run in DOS mode. 前后的机器码 | 常见 64 / 0x40 | ★★★★☆ | 很多 MSVC 链接生成的 PE 在 0x40 附近存在标准 DOS Stub，但不是所有 EXE 都固定如此 |
| PCAPNG | Section Header Block 中的 Byte-Order Magic、版本号、Section Length | 常见 8/ 6 | ★★★★☆ | 很适合 little-endian、Section Length=-1 的常见 pcapng；必须确认字节序 |
| XML | <?xml version="1.0" | 通常 0 | ★★★★☆ | XML 声明存在时非常好用；可能存在 UTF-8 BOM、不同 encoding 或完全没有声明 |
| SVG | <?xml version="1.0" | 通常 0 | ★★★★☆ | SVG 本质上是 XML；若无 XML 声明，可尝试 <svg ...，但属性顺序不稳定 |
| VMDK Sparse | 4B444D56 01000000 ... | 0 | ★★★☆☆ | KDMV + version 只有 8 字节；图中继续假定 flags=03 00 00 00 才达到 12 字节，这个值并非永远固定 |
| VMDK Descriptor | # Disk DescriptorFile | 0 | ★★★★★ | 如果 ZIP 中是文本描述符 VMDK，这比猜二进制 Sparse Header 更可靠 |
| PNG | 89504E470D0A1A0A0000000D49484452 | 0 | ★★★★★ | PNG 前 16 字节高度固定，是非常理想的格式型已知明文 |
| HTML | <!DOCTYPE html> | 通常 0 | ★★★☆☆ | 有些 HTML 没有 DOCTYPE，可能先有 BOM、注释 |
| robots.txt | User-agent: * | 常见 0 | ★★☆☆☆ | 只是常见写法，不属于严格固定格式头，优先级应低于 XML/PNG |

## 二、各文件格式明文构造详解

### 1. EXE / PE：利用 DOS Stub

核心纠正

EXE 明文攻击 ≠ 利用 MZ。4D 5A 只有 2 字节，远远不够。真正利用的是很多 Windows PE 文件中由链接器生成的默认 DOS Stub。

Microsoft PE 文档明确说明，链接器默认会在这里放置 DOS Stub，并输出类似：

This program cannot be run in DOS mode.

Stub 可以被自定义，因此 "所有 EXE 偏移 64 都一样" 说法过于绝对。

经典 DOS Stub

从偏移 0x40 = 64 开始的经典固定字节：

0E1FBA0E00B409CD21B8014CCD21546869732070726F6772616D2063616E6E6F742062652072756E20696E20444F53206D6F64652E0D0D0A24

构造与攻击

echo -n "0E1FBA0E00B409CD21B8014CCD21546869732070726F6772616D2063616E6E6F742062652072756E20696E20444F53206D6F64652E0D0D0A24" \

| xxd -r -p > exe_plain

bkcrack -C flag.zip -c nc64.exe -p exe_plain -o 64

记忆要点

利用的是 PE 默认 DOS Stub 的大段固定字节，不是 MZ 头

偏移通常是 64（0x40），但自定义 Stub 可能不同

### 2. PCAPNG：利用 Section Header Block

开头结构

| Offset | 字节 | 含义 |
| --- | --- | --- |
| 00 | 0A 0D 0D 0A | Block Type |
| 04 | xx xx xx xx | Block Total Length |
| 08 | 4D 3C 2B 1A | Byte-Order Magic（little endian） |
| 0C | 01 00 | Major Version = 1 |
| 0E | 00 00 | Minor Version = 0 |
| 10 | FF FF FF FF | Section Length 高 4 字节 |
| 14 | FF FF FF FF | Section Length 低 4 字节（= -1，常见情况） |

推荐猜法（从偏移 8）

echo -n "4D3C2B1A01000000FFFFFFFFFFFFFFFF" \

| xxd -r -p > pcap_plain

bkcrack -C flag.zip -c capture.pcapng -p pcap_plain -o 8

另一种猜法（从偏移 6）

00004D3C2B1A01000000FFFFFFFFFFFFFFFF

-o 6，原理是在 Byte-Order Magic 前再利用 Block Total Length 的两个高位通常为 00 00。能用，但比 -o 8 更依赖具体文件。

注意变数

PCAPNG 可能是另一种字节序

Section Length 不保证永远是 FFFFFFFFFFFFFFFF

应理解为根据 PCAPNG 结构推测一段长固定字段，而不是死背某一串 hex

### 3. XML：利用 XML Declaration

最经典明文

<?xml version="1.0"

已经足够长（≥12 字节）。

构造与攻击

printf '%s' '<?xml version="1.0"' > xml_plain

bkcrack -C flag.zip -c '123/web.xml' -p xml_plain -o 0

如果题目明显使用 UTF-8，还可以扩大：

printf '%s' '<?xml version="1.0" encoding="UTF-8"?>' > xml_plain

易错点

-c 填写的是 ZIP 内部 entry 的完整路径，不是本地文件系统路径。先 bkcrack -L flag.zip 直接复制文件名最稳

文件可能以 UTF-8 BOM（EF BB BF）开头，此时声明从偏移 3 开始

encoding 可能是 utf-8、UTF-8、GBK 等，不固定

XML 声明本身可以省略

因此 <?xml version="1.0" 通常比把整个 encoding 也猜进去更稳。

### 4. SVG：本质上还是 XML

**首选：** XML Declaration

SVG 是 XML 文档，首选：

printf '%s' '<?xml version="1.0" ' > plain.txt

bkcrack -C flag.zip -c spiral.svg -p plain.txt -o 0

这正是 bkcrack 官方教程使用的示例：对一个 ZipCrypto + Store 的 SVG 猜测 XML 声明并恢复 key。

**备选：** <svg 开始标签

如果文件没有 XML declaration，有时可以尝试：

<svg xmlns="http://www.w3.org/2000/svg"

但可靠性更低，因为 SVG 属性顺序不固定：

<svg width="..." xmlns="...">

<svg xmlns="..." width="...">

都合法。

优先级

XML Declaration → <svg 开始标签

### 5. VMDK：要区分两种文件

Binary Sparse VMDK

**常见开头：**

4B 44 4D 56    （ASCII: KDMV）

01 00 00 00    （version）

4B444D5601000000 只有 8 字节，不够。进一步猜 flags = 03000000，形成 12 字节：

echo -n "4B444D560100000003000000" | xxd -r -p > plain

bkcrack -C flag.zip -c flag.vmdk -p plain -o 0

flags = 3 并不是所有 VMDK 都保证成立，属于格式结构 + 常见字段值猜测，可靠性低于 PNG/XML。

Text Descriptor VMDK

如果是描述符文本，非常舒服：

\# Disk DescriptorFile

已经超过 12 字节。

printf '%s' '# Disk DescriptorFile' > plain

bkcrack -C flag.zip -c disk.vmdk -p plain -o 0

判断方法

遇到 VMDK 先判断类型，再决定攻击方式：

file xxx.vmdk

head xxx.vmdk

xxd -l 64 xxx.vmdk

## 三、通用命令模板

① 十六进制固定头

echo -n "HEX字符串" | xxd -r -p > plain.bin

例如 PNG：

echo -n "89504E470D0A1A0A0000000D49484452" | xxd -r -p > plain.bin

② ASCII 固定头（更推荐）

printf '%s' '已知字符串' > plain.bin

**例如：**

printf '%s' '<?xml version="1.0"' > plain.bin

③ 攻击

bkcrack \

-C flag.zip \

-c 'ZIP内部文件名' \

-p plain.bin \

-o 偏移
