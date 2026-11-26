---
title: Linux 取证命令：文件、账户、传输与归档
summary: 按任务使用文件和权限命令，区分离线检视、工作目录操作及会改变系统状态的管理命令。
module: Forensics
topic: 主机与服务
locationPaths: []
sourceIds: [web-forensics-wiki-linux-commands]
updated: 2026-10-01
---

## 1. 先确定命令作用的对象

分析目录约定：`./evidence/` 保存不可变副本，`./mnt/` 是核对过的只读挂载，`./work/` 是工作副本，`./output/` 保存结果。以下命令中的目录和文件名均为示例，执行前替换成实际对象。

| 任务 | 常用命令 | 结果与限制 |
| --- | --- | --- |
| 查看文件、定位对象 | `cat`、`find`、`mdir` | 内容、路径或目录项；读取也可能影响未只读保护的 atime |
| 理解权限与属性 | `chmod`、`chgrp`、`chattr` | 这些是修改命令；分析时先读 `stat`、`lsattr` |
| 整理工作目录 | `cd`、`dirs`、`mkdir`、`mv` | 创建、移动或覆盖；仅操作工作区和输出区 |
| 识别传输与服务行为 | `ftp`、`tftp`、`ncftp`、`ftpwho`、`ftpcount`、`ftpshut` | 客户端、服务状态和停服指令不是同一类证据 |
| 理解账户与进程管理 | `adduser`、`useradd`、`sudo`、`kill` | 结合账户文件、权限配置和日志；不在待分析系统上试改 |
| 检查压缩与归档 | `gzip`、`tar`、`gzexe` | 先列出内容，再定向解压；不执行其中的未知程序 |

命令的发行版、实现和版本会影响参数。先用本机 `man` 或帮助确认；shell 内建命令如 `cd`、`dirs` 可用 `help cd`、`help dirs`。显示结果为空可能来自权限、路径或工具支持范围，需要分别排查。

## 2. 文件内容与查找

### 2.1 cat：逐行读文本

```bash
cat -n ./mnt/etc/os-release
cat -b ./work/auth.log
cat -A ./work/config.txt
```

`-n` 为全部行编号，`-b` 只给非空行编号，`-s` 合并连续空行。`-A` 相当于 `-vET`，辅助识别非打印字符、制表符和行尾；它改变的是显示，不是文件字节。中文文本在该显示模式下可能难读，不能把显示转义当作实际内容。

`>` 写新内容并截断已存在的目标，`>>` 追加。保存结果前确认输出路径；用 `cat` 重定向到设备是写盘操作，不属于普通检视，也不提供完整采集报告和坏扇区处理。

### 2.2 find：按路径、属性与时间缩小范围

```bash
find ./mnt/var/log -type f -name '*.log' -print
find ./mnt/home -type f -iname '*history*' -print
find ./mnt -type f -size +10M -print
find ./mnt -type f -perm /4000 -print
find ./mnt/var/log -type f -mtime -7 -print
find ./mnt -type f -print0 > ./output/file-paths.nul
```

| 条件 | 含义 | 使用要点 |
| --- | --- | --- |
| `-name` / `-iname` | 文件名模式，后者忽略大小写 | 用引号防止 shell 提前展开 `*` |
| `-type f` / `d` / `l` | 普通文件、目录、符号链接 | 默认不跟随符号链接；改变策略可能离开目标树 |
| `-size +10M` | 按指定单位及取整规则比较大小 | 查精确字节时用 `c` 单位 |
| `-perm 0644` | 权限位恰好匹配 | `-perm -MODE` 要求所有指定位置位；`/MODE` 任一置位 |
| `-mtime` / `-atime` / `-ctime` | 修改、访问、元数据状态变化时间 | 以分析机当前时间计算天数，ctime 不是文件创建时间 |
| `-print0` | 以 NUL 分隔路径 | 正确处理空格、换行和特殊文件名 |

`-exec`、`-ok` 执行外部操作，`-delete` 删除对象。做检视时使用输出路径的动作，避免把删除示例带入检材。多个条件的组合注意 `-a` / `-o` 优先级，复杂表达式用转义括号。

### 2.3 mdir：查看 FAT 镜像目录

`mdir` 属于 mtools，查看 DOS/FAT 目录；它不是 Linux 的通用目录命令。对已切出的 FAT 分区副本可使用：

```bash
mdir -i ./work/fat-partition.img ::/
mdir -i ./work/fat-partition.img -a ::/
```

`-a` 显示隐藏项。整盘包含分区表时需先确定分区范围，不能将整盘起点当作 FAT 文件系统起点。目录条目时间还需核对 FAT 的本地时间含义与精度。

## 3. 权限、属性与工作目录

### 3.1 chmod、chgrp、chattr

权限分为 owner/group/other；读、写、执行分别对应 4、2、1。目录的 `x` 表示可穿越，`r` 表示可列出名称，`w` 涉及目录项变更；不能照搬普通文件含义。setuid、setgid 与 sticky 位另行解释。

先读取状态：

```bash
stat ./mnt/etc/passwd
lsattr ./mnt/etc/passwd
```

仅对自己的工作副本使用以下修改示例：

```bash
chmod u=rw,go= ./work/config-copy.txt
chmod 0600 ./work/config-copy.txt
chgrp --reference=./work/reference.txt ./work/config-copy.txt
chattr +i ./work/config-copy.txt
chattr -i ./work/config-copy.txt
```

`chmod` 支持符号模式和八进制；`chgrp` 修改所属组，不修改 owner，普通用户还受文件所有权与组成员限制。`chattr +i` 设置 immutable，`+a` 设置 append-only；能否设置取决于权限、文件系统及挂载方式。

不能把 `chattr` 属性当作硬件写保护。历史资料中的 `s` / `u` 等属性不代表当前文件系统已实现安全擦除或自动恢复；不要凭一个属性声称“删除后可恢复”。`-R` 的递归范围也须单独确认。

### 3.2 cd、dirs、mkdir、mv

```bash
mkdir -p ./work/extracted ./output
cd ./work
dirs -v
mv -i ./report-draft.txt ../output/report-draft.txt
```

`cd` 只切换当前 shell 目录，`cd -` 返回上次目录。`dirs` 显示 Bash 等支持的目录栈；没有使用目录栈时通常仅见当前目录。`mkdir -p` 建立缺失的父目录，目标已存在仍需核对权限。

`mv` 可移动和改名，目标已存在时可能覆盖；`-i` 交互确认，`-n` 在常见实现中避免覆盖。跨文件系统移动可能发生复制再删除，不能用于保持检材不变的“保全”。重定向、目录权限和复制工具也会影响元数据。

## 4. 文件传输与 FTP 服务

### 4.1 ftp、tftp、ncftp

| 工具 | 常见操作 | 条件与取证关注点 |
| --- | --- | --- |
| `ftp` | `open`、`ls`、`pwd`、`binary`、`get`、`put`、`bye` | FTP 控制与数据连接分开；主动/被动模式、账户和传输日志需关联 |
| `tftp` | `get`、`put`、`binary`、`quit` | 一般不含 FTP 的用户认证；基于 UDP，客户端语法与超时因实现而异 |
| `ncftp` | 交互浏览、下载、上传、书签 | 不是 SFTP；书签和客户端配置可包含连接信息 |

只在明确的练习服务上验证下载，并将本地目录切到输出区。以传统 FTP 客户端的交互会话为例：

```text
ftp> open 192.0.2.10
ftp> binary
ftp> pwd
ftp> ls
ftp> get sample.bin sample-download.bin
ftp> bye
```

`192.0.2.10` 是文档示例地址，须替换成自己练习服务地址。`binary` 避免 ASCII 模式换行转换，下载后用大小和哈希核对完整性。`put` 会写远端，不能用于只读采集。FTP/TFTP 本身不提供与 SFTP 相同的加密保护，口令和数据的可见性需按实际协议核对。

### 4.2 ftpwho、ftpcount、ftpshut

这些是部分传统 FTP 服务配套的管理工具，未必随现代服务安装。`ftpwho` 查看当前会话，`ftpcount` 统计在线数量，`ftpshut` 安排服务关闭；不能用它们替代历史日志。

先识别服务软件、版本、状态文件与帮助，避免把不同服务器的同名指令参数混用。在线会话反映查询时点；统计人数不等于历史独立用户数量。分析登录、上传、下载与异常重试时，优先关联 FTP 日志、认证记录、网络会话和目标文件。

`ftpshut` 会改变服务可用性，保留为管理行为的解释入口，不在取证流程中执行停服操作。

## 5. 账户、提权与进程管理

### 5.1 adduser 与 useradd

`useradd` 常是底层账户管理工具；Debian/Kali 的 `adduser` 通常是较高层的配置封装。其他发行版可能将其实现成不同程序或链接，不能普遍给 `adduser` 套用 `useradd` 参数。

在练习环境识别命令含义时：

| useradd 参数 | 作用 | 证据对应 |
| --- | --- | --- |
| `-u UID` | 指定 UID | passwd 的 UID 与文件所有者 |
| `-g GROUP` / `-G GROUPS` | 主组 / 附加组 | passwd、group，后者不替代主组 |
| `-d DIR` / `-m` | home 路径 / 创建 home | 指定路径不一定已创建目录 |
| `-s SHELL` | 登录 shell | shell 为 nologin 不等于该账户不能运行任何服务 |
| `-r` | 系统账户 | UID 分配范围依发行版配置 |

账户创建会修改 `/etc/passwd`、`shadow`、`group` 等及可能的 home；因此离线分析使用文件读取，并关联备份、认证日志和时间线。单凭一个账户条目不能确定创建命令、创建者或创建时间。

### 5.2 sudo 与 kill

`sudo` 按 sudoers 策略以指定身份执行命令，`-u` 指定目标用户；`sudo -l` 反映查询时点的授权。成功或失败的 sudo 行为需关联日志、会话、账户和执行对象，而不是把历史命令视为已执行成功。

`kill` 向 PID 发信号，不等于必然终止。省略信号通常发送 TERM，HUP 的处理由程序决定，KILL 无法被程序捕获；强制终止可能丢失缓存和未刷盘状态。`kill -l` 查看信号列表，不改变进程。

不要将包含 `ps | grep` 的整行输出当作 PID，也不能把其他工具的 `-u 用户` 参数当作通用 `kill` 用法。命令行中的 PID、进程树、启动时间与可执行文件需相互核对。更多位置和日志见 [服务器主机与服务](/knowledge/forensic-server-services/)。

## 6. gzip、tar 与 gzexe

### 6.1 gzip：验证与输出到新文件

```bash
gzip -l ./work/archive.gz
gzip -t ./work/archive.gz
gzip -dc ./work/archive.gz > ./output/archive.raw
```

`-l` 查看压缩元信息，`-t` 检查数据，`-d` 解压，`-c` 输出到标准输出；`-k` 在支持的实现中保留输入。默认原地压缩/解压可能删除输入或改变文件名，分析时使用副本和新输出。CRC 通过说明压缩流校验符合，不能证明内容来源或所有上层文件正确。

### 6.2 tar：先列清单，再解到空目录

```bash
tar -tvf ./work/archive.tar
tar -tzvf ./work/archive.tar.gz
mkdir -p ./work/extracted
tar -xzf ./work/archive.tar.gz -C ./work/extracted --no-same-owner --no-same-permissions
```

`-t` 列表，`-x` 解包，`-c` 创建，`-f` 指定归档，`-z` 使用 gzip，`-v` 输出过程，`-C` 指定目标目录。先检查绝对路径、`..`、链接和已有文件冲突，再在隔离的空目录解包。解包会写文件；内部所有者与时间属于归档记录，不能不经验证当作采集文件系统的当前属性。

### 6.3 gzexe：识别压缩可执行包装

`gzexe` 将可执行对象压缩成带 shell 解包启动逻辑的包装，`-d` 用于还原。包装文件出现并不改变内部程序行为是否可信。先保全包装、备份文件、文件头和脚本内容；不通过直接启动包装来“解压”。

需要验证历史行为时仅在独立练习副本上按本版帮助操作，并比较包装前后的大小、哈希和类型。压缩可执行文件、普通 gzip 数据和 tar 归档是三个层次，不能使用同一判断方式。

## 7. 输出如何回到取证结论

保存命令、版本、工作目录、输入哈希、退出状态、标准输出和错误输出。读取权限不足、解析失败、没有匹配项和对象确实不存在应分别记录。文件列表用于定位；要证明内容、行为和时间，还需回到具体字节、应用字段及关联日志。
