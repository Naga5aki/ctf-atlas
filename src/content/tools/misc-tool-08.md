---
title: "file"
summary: "原理： file命令不依赖文件后缀名，而是通过读取文件头部的魔数（Magic Number）、文件结构及系统信息，来确定文件的真实格式。"
module: "Misc"
topic: "文件结构与提取"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、核心功能

**原理：** file命令不依赖文件后缀名，而是通过读取文件头部的魔数（Magic Number）、文件结构及系统信息，来确定文件的真实格式。

**作用：** 解决“文件被改名”“后缀名被修改”“隐写伪装”等常见问题，是确认文件本体的第一步。

## 二、常用参数速查

file  filename识别文件类型最基础、最常用的命令。

file -i filename输出MIME类型用于精确判断文件真实格式，尤其是后缀伪装时。

file -b filename不显示文件名，只显示类型,脚本自动化处理时使用。

file -z filename读取压缩文件内数据分析损坏文件或嵌套压缩包。

file --mime -encoding filename显示文件编码处理文本类隐写时确认编码格式。
