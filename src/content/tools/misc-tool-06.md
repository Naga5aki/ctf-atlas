---
title: "strings"
summary: "strings是Linux下提取可打印字符串的工具，尤其适合快速扫图、包、二进制文件里的明文信息。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

strings是Linux下提取可打印字符串的工具，尤其适合快速扫图、包、二进制文件里的明文信息。

## 一、基础用法

### 1.命令格式

strings[选项]文件名

**常用选项：**

-n数字：只显示长度≥该数字的字符串（默认4）

-t进制：显示字符串在文件中的偏移（d十进制/x十六进制/o八进制）

-e编码：指定编码（b16位/l32位/S7位等，适合中文/Unicode）

### 2.典型场景示例

### 1）直接查看文件中所有可打印字符串

strings target.jpg

### 2）只看长度≥8的字符串（过滤短垃圾信息）

strings -n 8 target.zip

### 3）显示字符串在文件中的十六进制偏移

strings -t x target.bin

### 4）直接grep找flag/密码/关键词

strings target.png | grep -i "flag"

strings target.docx | grep -E "password|key|ctf"

## 二、核心应用场景

### 1.图片隐写题

很多题目会把flag、密码、提示直接写在图片文件末尾（JPG/PNG等格式允许在文件尾追加数据）。

strings target.jpg | grep"flag"

### 2.压缩包/文档题

压缩包（ZIP/RAR）：可能在文件头/尾藏解压密码

strings secret.zip | grep -i"pass"

**Office/PDF：** 文档元数据或隐藏文本会被strings扫出

**固件/二进制文件：** 提取版本号、后门密码、API Key等敏感信息

### 3.流量包/日志题

Wireshark导出的pcap文件：用strings快速扫出明文协议中的账号密码、flag

strings traffic.pcap | grep"flag{"

**日志文件：** 提取异常访问、命令执行记录

### 4.其他二进制文件

可执行文件（ELF/EXE）：提取硬编码的密码、提示、版本信息

**音频/视频文件：** 部分题目会把信息藏在音视频文件的字符串段里

## 三、注意事项与进阶技巧

1.垃圾信息过滤：默认会输出很多无意义短字符串，用-n 6/8过滤长度，或结合grep-v排除噪音。

strings -n 8 target.jpg | grep -v"JFIF" | grep -v"Exif"

### 2.编码问题：如果是中文/Unicode字符串，用-e S/-e l尝试不同编码：

strings -e S target.png

#尝试7位编码

3.局限性：只能提取可打印字符，如果是LSB隐写、base64/hex编码数据，需要配合zsteg/binwalk/steghide等工具。
