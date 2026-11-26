---
title: "binwalk"
summary: "Binwalk专门用来分析、提取、恢复嵌入在文件/固件中的隐藏数据，是解决图片隐写、固件分析、文件格式混淆类题目的核心工具。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

Binwalk专门用来分析、提取、恢复嵌入在文件/固件中的隐藏数据，是解决图片隐写、固件分析、文件格式混淆类题目的核心工具。

## 一、核心功能

### 1）自动识别文件类型

Binwalk会扫描文件的文件头/魔数（Magic Number），识别出真实格式，尤其适合处理被改后缀、嵌套的文件：

例：一张看似.png的图片，实际内部藏了一个.zip压缩包

**命令：**

binwalk target.file

#扫描并列出所有识别到的文件结构

**输出会显示：** 偏移地址、文件类型、大小等信息，帮你定位隐藏数据。

### 2）检测隐写与嵌入数据

**识别常见隐写格式：** PNG IDAT块、JPEG注释段、ZIP/7z/rar压缩包、ELF/PE可执行文件等

**发现异常数据段：** 比如在图片末尾追加的文本、base64/hex编码数据、加密容器

## 二、核心作用

### 1）一键提取所有识别到的文件

这是Misc题最常用的操作，直接把嵌套在目标文件里的所有子文件导出：

Binwalk -e target.file

#-e=extract，提取所有可识别的文件

Binwalk -Me target.file

#-M=递归提取，适合多层嵌套（如zip里套png，png里又藏txt）

会自动创建_target.file.extracted目录，存放所有提取出的文件

**适用场景：** 图片藏压缩包、固件藏配置文件、音频藏脚本等

### 2）按偏移地址手动提取

如果自动提取失败，可以手动指定偏移地址提取：

Binwalk -D="zip:zip" -o 0x1234 target.file

#从0x1234偏移处提取zip文件

dd if=target.file of=hidden.zip  bs=1  skip=0x1234

#用dd命令手动切割

**适用场景：** binwalk识别到文件但自动提取失败，或需要精准提取某一段数据

## 三、常用参数速查表

-e提取所有识别到的文件binwalk -e file

-M递归提取（嵌套文件）binwalk -Me file

-E熵分析（可视化）binwalk -E file

-A扫描可执行代码binwalk -A file

-D按格式手动提取binwalk -D="png:png"file

-o指定偏移地址binwalk -o 0x100 file

-H计算哈希值binwalk -H file

## 四、注意事项

**自动提取不一定完美：** 部分加密/特殊格式的文件可能需要手动用dd或foremost辅助提取

**依赖问题：** 部分格式提取需要安装额外工具（如7z、unrar、squashfs-tools）

**配合其他工具：** 常与foremost、scalpel、strings、xxd搭配使用，解决复杂隐写题
