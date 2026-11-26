---
title: "grep"
summary: "grep是Linux下的文本搜索神器，在Misc题中主要用于从海量文本/二进制数据中精准定位关键词（如flag、密码、提示、敏感信息等），是strings的最佳搭档。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

grep是Linux下的文本搜索神器，在Misc题中主要用于从海量文本/二进制数据中精准定位关键词（如flag、密码、提示、敏感信息等），是strings的最佳搭档。

## 一、基础用法与核心参数

### 1.命令格式

grep[选项]"搜索词"目标文件

### 2.高频实用选项

**选项作用典型场景：**

-i：忽略大小写匹配Flag/FLAG/flag等变体

-n：显示行号定位字符串在文件中的位置

-o：只输出匹配部分精准提取flag{...}本身

-E：启用正则表达式匹配复杂格式（如flag{.*}）

-v：反向匹配（排除）过滤噪音字符串（如JFIF/Exif）

-r：递归搜索目录在解压后的文件夹中批量找flag-A n/

-B/A n：显示匹配行后/前n行查看flag上下文提示

-c：统计匹配次数确认是否存在敏感信息

## 二、核心应用场景

### 1.图片/文件隐写：快速定位flag

配合strings使用，从图片、压缩包等文件中直接提取flag：

### 1)从图片中找flag（忽略大小写）

strings target.jpg | grep -i"flag"

### 2)精准提取完整flag（正则匹配）

strings target.png | grep -oE "flag\{.*\}"

### 3)过滤噪音，只看有效信息

strings target.jpg | grep -v"JFIF" | grep -v"Exif" | grep -i "pass"

### 2.压缩包/文档题：找密码或提示

**从压缩包中提取解压密码：**

strings secret.zip | grep -i "password\|pass\|key"

**批量扫描解压后的文件夹：**

#递归搜索当前目录下所有文件中的flag

grep -r"flag{"./

### 3.流量包/日志分析：提取明文敏感信息

从pcap流量包中提取flag或账号密码：

strings traffic.pcap | grep -i "flag{"

strings http.pcap | grep -E "username|password"

**从日志文件中定位异常操作：**

grep -n "POST/admin" access.log

grep -B 5 -A 5 "error" system.log

### 4.二进制/固件分析：提取硬编码信息

从ELF/EXE可执行文件中找硬编码密码/提示：

strings app.exe | grep -E "key|secret|token"

从固件镜像中定位版本号或后门账号：

strings firmware.bin | grep -E "version|admin|root"

### 5.进阶：结合正则表达式的复杂匹配

当flag格式不固定时，用正则表达式精准匹配：

#匹配所有以flag{开头、}结尾的内容

grep -oE "flag\{[a-zA-Z0-9_]+\}" target.txt

### 6.批量处理：递归搜索目录

在解压后的文件夹中批量查找flag：

#递归搜索当前目录，只输出匹配的文件名

grep -rl "flag{"./

#递归搜索并显示匹配内容

grep -r "flag{"./
