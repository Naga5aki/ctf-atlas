---
title: "dd"
summary: "dd是Linux下的二进制数据读写工具，在CTF-Misc中，它的核心价值是精准切割、提取、拼接二进制数据，专门用来处理「文件中藏文件」「数据片段分离」这类隐写场景。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

dd是Linux下的二进制数据读写工具，在CTF-Misc中，它的核心价值是精准切割、提取、拼接二进制数据，专门用来处理「文件中藏文件」「数据片段分离」这类隐写场景。

## 一、核心定义与原理

**本质：** dd是「按字节/块读写」的底层工具，不关心文件格式，只对原始二进制数据操作。

**核心参数：**

if=FILE：输入文件（input file）

of=FILE：输出文件（output file）

skip=N：从输入文件的开头位置，跳过 N 个数据块，再开始读取数据

seek=N：从输出文件的开头位置，跳过 N 个数据块，再开始写入数据

bs=SIZE：设置读写块大小（默认512字节，常用bs=1实现字节级操作）

**关键优势：** 可以精确到单个字节，完美适配CTF中「偏移量提取」的需求。

## 二、典型应用场景

### 1.提取隐藏在文件中的数据

当binwalk扫描出文件中存在隐藏数据（如ZIP、PNG、文本）并给出十进制偏移量时，用dd精准提取：

#从QR_code.png中提取偏移471字节开始的ZIP包

dd if=~/桌面/QR_code.png of=hidden.zip skip=471 bs=1

if=~/桌面/QR_code.png：原始图片作为输入

of=hidden.zip：输出为新的压缩包文件

skip=471：跳过前471字节（对应binwalk给出的DECIMAL偏移）

bs=1：每次读写1字节，保证精确到字节级

### 2.切割文件片段

当题目给出「从第X字节到第Y字节」的片段是有效数据时，用dd截取：

#提取从偏移100开始、长度200字节的数据

dd if=input.bin  of=output.bin  skip=100  count=200  bs=1

count=200：只复制200个块（这里块大小为1字节，即复制200字节）

### 3.拼接/恢复损坏的文件

当文件被拆分、截断或头部被污染时，用dd拼接恢复：

#把两个片段拼接成完整文件

dd if=part1.bin  of=full.bin  bs=1

dd if=part2.bin  of=full.bin  bs=1  seek=1024

#从第1024字节开始写入part2

### 4.制作/修改镜像文件

在固件分析、磁盘镜像题中，用dd读写磁盘镜像的特定分区：

#提取磁盘镜像的第2个分区（假设块大小为512，分区从2048块开始）

dd if=disk.img  of=partition2.img  skip=2048  bs=512

### 5.处理字节序/编码转换

配合conv参数实现简单转换：

#把文件转为大写（仅对ASCII有效）

dd if=input.txt of=output.txt conv=ucase

#按字节反转（用于某些异或/反转题）

dd if=input.bin of=rev.bin conv=swab

## 三、使用注意事项

**精确性：** bs=1时操作最慢但最精确，适合CTF场景；大文件可适当调大bs提升速度。

**备份意识：** 操作前备份原始文件，避免误操作覆盖数据。

**偏移单位：** binwalk给出的DECIMAL是十进制偏移，直接用skip=N即可；如果是十六进制（如0x1D7），需要先转成十进制（0x1D7=471）。
