---
title: "分卷压缩包合并"
summary: "分卷不能缺失、不能乱序、不能随意改名。少一卷或顺序错误，最终文件通常都会损坏。"
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原则

必须保证所有分卷完整，并按正确顺序组合。

分卷不能缺失、不能乱序、不能随意改名。少一卷或顺序错误，最终文件通常都会损坏。

## 二、Windows 命令行合并

**适用于类似：**

topic.zip.001

topic.zip.002

topic.zip.003

topic.zip.004

在分卷所在目录打开 CMD，执行：

copy /B topic.zip.001+topic.zip.002+topic.zip.003+topic.zip.004 topic.zip

| 参数 | 含义 |
| --- | --- |
| copy | 复制 / 合并文件 |
| /B | 按二进制文件处理，避免压缩数据被修改 |
| + | 按顺序拼接各分卷 |
| topic.zip | 合并后的完整压缩包 |

如果有 6 个分卷，同理把所有分卷依次列出：

copy /B topic.zip.001+topic.zip.002+topic.zip.003+topic.zip.004+topic.zip.005+topic.zip.006 topic.zip

合并完成后，再使用 Bandizip、7-Zip、WinRAR 打开 topic.zip。

## 三、Kali 使用 cat

cat topic.zip.001 topic.zip.002 topic.zip.003 topic.zip.004 > topic.zip

分卷较多且编号规范时，可以用通配符：

cat topic.zip.0* > topic.zip

**然后解压：**

unzip topic.zip

\# 或

7z x topic.zip

## 四、使用压缩软件自动处理

很多标准分卷压缩包实际上不需要手动合并。

适用格式

flag.zip.001 / flag.zip.002 / flag.zip.003

flag.7z.001  / flag.7z.002  / flag.7z.003

操作步骤

将所有分卷放在同一个目录

保持原文件名不变

使用 Bandizip 或 7-Zip 打开 .001 第一卷

直接解压

**软件会自动按顺序读取：** 001 → 002 → 003 → ...

RAR 分卷

flag.part1.rar

flag.part2.rar

flag.part3.rar

直接打开 flag.part1.rar 即可。

## 五、两种情况区分

| 类型 | 特征 | 处理方式 |
| --- | --- | --- |
| 标准分卷压缩包 | flag.7z.001 / flag.7z.002 / flag.7z.003 | 优先直接打开 .001，通常无需手动合并 |
| 单纯文件切片 | flag.zip.001 / flag.zip.002 / flag.zip.003 | 如果压缩软件不能识别，则用 copy /B ... 或 cat ... 手动恢复原始 zip |
