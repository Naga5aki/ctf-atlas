---
title: "TestDisk"
summary: "TestDisk： 依赖分区表和文件系统元数据，可保留文件名、目录结构；"
module: "Misc"
topic: "文档与取证"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

TestDisk 是开源的分区与文件系统修复工具，主要用于：

恢复丢失或误删分区；

修复 FAT、NTFS 等引导扇区；

查找 ext 文件系统备份超级块；

恢复仍保留元数据的已删除文件；

从无法挂载的分区中复制文件；

分析磁盘、U 盘、SD 卡及 RAW/IMG/DD 镜像。

与 PhotoRec 的区别：

**TestDisk：** 依赖分区表和文件系统元数据，可保留文件名、目录结构；

**PhotoRec：** 按文件特征雕刻，不依赖文件系统，通常不保留原文件名和目录。

**启动命令：**

sudo testdisk

testdisk disk.img

testdisk /log disk.img

## 二、使用方法

### 1. 基本流程

选择日志

→ 选择磁盘或镜像

→ 选择分区表类型

→ Analyse

→ Quick Search

→ Deeper Search

→ P 预览文件

→ C 复制文件或 Write 写入分区表

### 2. 常用菜单

| 功能 | 作用 |
| --- | --- |
| Analyse | 搜索丢失分区 |
| Quick Search | 快速查找分区 |
| Deeper Search | 深度扫描分区残留 |
| Advanced | 文件系统修复与文件恢复 |
| Boot | 修复 FAT/NTFS 引导扇区 |
| List | 查看文件和目录 |
| Undelete | 恢复已删除文件 |
| Superblock | 查找 ext 备份超级块 |
| Write | 写入新的分区表 |

### 3. 常用按键

| 按键 | 作用 |
| --- | --- |
| P | 查看分区内文件 |
| C | 复制文件或目录 |
| : | 选择文件 |
| a | 全选 |
| q | 返回 |
| 左右方向键 | 修改分区状态 |

**分区状态：**

*  可启动主分区

P  主分区

L  逻辑分区

E  扩展分区

D  删除或不写入

| 类型 | 场景 |
| --- | --- |
| Intel | MBR 磁盘 |
| EFI GPT | GPT 磁盘 |
| None | 镜像从偏移 0 直接是文件系统 |
| Mac | Apple 分区表 |

### 4. 分区表选择

通常采用 TestDisk 自动检测结果。

## 三、应用场景

### 1. 分区丢失或分区表损坏

Analyse

→ Quick Search

→ Deeper Search

→ P 检查文件

→ Write

**适用于：**

分区被误删；

MBR/GPT 分区项损坏；

磁盘显示未分配；

原分区突然消失。

### 2. FAT/NTFS 引导扇区损坏

**进入：**

Advanced

→ Boot

**常见功能：**

Backup BS：用备份引导扇区恢复主引导扇区；

Rebuild BS：重建引导扇区；

Repair MFT：尝试修复 NTFS 的 $MFT。

### 3. 文件恢复

**通过：**

P 查看文件

C 复制文件

**适合：**

文件系统无法挂载，但目录仍可读取；

已删除文件的元数据仍存在；

需要先复制重要文件，再考虑修复。

### 4. ext 文件系统修复

**通过：**

Advanced

→ Superblock

查找备份超级块，再结合 fsck 使用。

### 5. CTF 和磁盘取证

**常见考点：**

删除分区恢复；

分区类型被修改；

FAT32 主备 VBR 不一致；

NTFS Boot Sector 损坏；

隐藏分区；

ext 超级块损坏；

已删除文件恢复；

IMG 镜像无法挂载。

## 四、补充点

### 1. 取证原则

**优先分析镜像副本：**

sha256sum disk.img

cp disk.img working.img

testdisk working.img

恢复文件应保存到其他磁盘或目录，不能写回源介质。

### 2. 故障磁盘先成像

磁盘存在坏道、掉盘或异响时，先使用：

sudo ddrescue -f -n /dev/sdb disk.img disk.map

sudo ddrescue -d -r3 /dev/sdb disk.img disk.map

再分析镜像。

### 3. 写入操作风险

**以下操作会修改磁盘或镜像：**

Write

Backup BS

Rebuild BS

Repair MFT

MBR Code

Delete

**执行前应确认：**

分区边界正确；

分区不重叠；

P 能正常查看文件；

已保存原始镜像。

### 4. 搜索结果判断

不能只看 TestDisk 是否找到分区，还要检查：

起始扇区和容量是否合理；

文件系统类型是否正确；

是否能正常列目录；

文件内容是否可信；

是否存在重叠或历史分区候选。
