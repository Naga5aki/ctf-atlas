---
title: "工具与命令速查"
summary: "按取证任务检索常用命令、参数、工具用途与脚本处理方法。"
module: "Forensics"
track: "综合取证"
topic: "工具与路径"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

## 01 使用范围与执行环境

本页用于按“要取得什么证据”查找命令、参数和工具。每项操作都要先确定对象属于**离线检材、目标运行现场还是隔离仿真副本**。命令的输出仅描述它实际读取的对象：在分析机上运行 `uname`、包查询或端口查询，不会自动变成目标系统的结果。

| 环境 | 适用操作 | 需要记录的边界 |
| --- | --- | --- |
| 离线镜像与只读挂载目录 | 读取配置、历史、日志、元数据、二进制与应用数据 | 使用检材根路径；软链可能越出挂载目录；解析输出写到工作目录 |
| 已确认身份的目标现场 | 采集当前内核、进程、监听、挂载和服务状态 | 记录采集时间、账户、主机或容器归属；采集命令本身可能留下痕迹 |
| 隔离仿真副本 | 观察启动和应用行为、连接副本内服务 | 标记仿真新增日志、端口和文件；结果不能替代历史状态 |

### 01.1 示例对象与路径

以下离线示例使用 `/mnt/evidence` 作为检材根目录，`./work` 作为输出目录，`root-partition.dd` 表示已定位的单个分区镜像，`image.dd` 表示整盘镜像。`sample.exe`、`video.mp4`、`sample.apk` 都是通用示例文件名，使用时换成实际副本。

```bash
EVIDENCE_ROOT=/mnt/evidence
mkdir -p ./work
ls -ld "$EVIDENCE_ROOT/etc" "$EVIDENCE_ROOT/var"
```

`mkdir -p` 只创建分析工作目录，不在检材内写入。先检查挂载状态与路径归属，再读取文件；遇到绝对软链时，不能直接让分析机替你解析到自身的 `/etc`、`/usr` 或 `/var`。

### 01.2 参数必须按命令解释

相同短参数在不同程序中没有统一含义。下面是查表提示，实际使用以该工具的帮助及版本为准。

| 参数 | 本页出现的具体含义 | 避免混用 |
| --- | --- | --- |
| `-l` | `ls -l` 长格式；`ss -l` 仅监听；`crontab -l` 列任务 | 不把它统称为“列表”后套到其他程序 |
| `-a` | `uname -a` 所有可用系统字段；`rpm -qa` 所有包；`exiftool -a` 保留重复标签 | “全部”的对象分别不同 |
| `-n` | `ss -n` 保持数字地址/端口；`findmnt -n` 去掉表头；`strings -n 6` 设置最短长度 | `strings -n` 后必须有长度值 |
| `-t`、`-T` | `ss -t` 选 TCP；`df -T` 显示类型；`btrfs subvolume list -t` 表格输出 | `findmnt` 的输出字段用 `-o`，不是 `-t` |
| `-p` | `ss -p` 显进程；`blkid -p` 低层探测；Btrfs 列表的 `-p` 显父 ID | 三者读取完全不同的数据 |
| `-h` | `df -h` 使用易读容量单位；`readelf -h` 读取 ELF 文件头 | 不以参数形状推断作用 |
| `-o` | `findmnt`、LVM 工具选择字段；`mount` 给挂载选项；`guestmount` 给 FUSE 选项 | `guestmount` 的源镜像只读模式使用 `--ro` |
| `-f` | `lsblk -f` 文件系统信息；`lxc-ls -f` 格式化清单；`readlink -f` 规范化路径；QEMU 的 `--format` 选择镜像格式 | 先确认程序，再解释字母 |
| `--state=` | `systemctl list-unit-files` 按单元文件启用状态过滤 | enabled 是启用状态，不代表当前正在运行 |

## 02 系统身份与存储命令

### 02.1 系统与硬件标识

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `cat "$EVIDENCE_ROOT/usr/lib/os-release"` | `cat` 输出指定文件内容，无选项 | 读取 `PRETTY_NAME`、`ID`、`VERSION_ID`。先核对 `/etc/os-release` 是否为普通文件或指向此文件的软链；两份独立文件存在时优先 `/etc`，不拼接字段。此文件是发行版标识，不是内核版本，也不必是软链目标 |
| `uname -a`；单项 `uname -r`、`uname -m`、`uname -n` | `-a` 输出可用的系统字段；`-r` 内核 release、`-m` 架构、`-n` 节点名 | 仅在目标现场或仿真会话执行。内核版本与发行版版本分开记录；缺失字段可能不在 `-a` 输出中 |
| `hostnamectl` | 无选项，查询 systemd 主机信息 | 适用于目标现场；可能显示静态/临时主机名、系统、内核与架构。不能当成离线镜像读取器 |
| `cat "$EVIDENCE_ROOT/etc/hostname"` | 读取主机名配置 | 对照 hosts、日志与运行现场，区分配置名称、解析别名和采集时名称 |
| `cat "$EVIDENCE_ROOT/etc/hosts"` | 读取静态名称映射 | 示例 `10.20.0.15 db-node` 只说明配置映射；还需核对应用配置、容器定义或历史连接，不等于成功连接记录 |
| `readlink "$EVIDENCE_ROOT/etc/localtime"` | 输出软链文本，不递归跟随 | 离线先看它是否指向 `/usr/share/zoneinfo/<地区>`（如 `zoneinfo/Asia/Shanghai`）。普通文件没有输出时要继续比对时区数据；不能判成没有时区 |
| `readlink -f /etc/localtime` | `-f` 规范化并解析软链 | 仅用于明确的目标现场。离线绝对软链可能指向分析机，不能直接用其结果归属目标 |
| `cat "$EVIDENCE_ROOT/etc/timezone"` | 读取文本时区名 | 部分 Debian 系使用此位置；与 localtime、应用日志时区互证，不假定每个发行版都有 |
| `cat "$EVIDENCE_ROOT/etc/fstab"` | 读取持久化挂载配置 | 提取挂载点、`UUID=`/`PARTUUID=`、类型、选项。配置与超级块一致支持对象对应；不能证明成功挂载或唯一机器身份 |
| `cat /proc/filesystems` | 读取当前内核注册的文件系统 | 仅目标现场或已采集的 proc 视图；`nodev` 表示无需块设备，不表示“未使用”。离线镜像里的空 `/proc` 不提供这项状态 |

系统字段与软链的完整判读见[Linux 系统身份与服务清单](/knowledge/fic-case-03/)。

### 02.2 块设备、挂载与容量

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `lsblk -f` | `-f` 给出文件系统信息，包括类型、标签、UUID、挂载信息；列因版本而异 | 在现场或分析机区分物理盘、分区、映射设备。记录它正在查询哪一台机器；对镜像需先明确对应设备 |
| `blkid -p -o export ./root-partition.dd` | `-p` 绕过缓存做低层探测；`-o export` 输出 `KEY=VALUE` | 读取已定位分区的类型、UUID等。整盘镜像需先定位分区，不能用外层分区表识别结果代替内部文件系统 |
| `blkid -o value -s TYPE /dev/loop0p1` | `-s TYPE` 只选类型；`-o value` 只输出字段值 | 示例设备须确认为检材对应的设备；空结果可能是权限、加密或类型不支持，不直接判成无文件系统 |
| `findmnt -no FSTYPE,TARGET,SOURCE \| sort -u` | `-n` 无表头；`-o` 选类型/目标/来源；`sort -u` 排序去重 | 清点**当前会话**已挂载对象。对“是否使用”分开判断当前挂载、配置痕迹和历史使用；缺席当前列表不能证明从未使用 |
| `df -Th /mnt/evidence` | `-T` 类型、`-h` 易读容量；指定路径限制范围 | 查看该挂载点对应容量和用量；若未真正挂载，可能显示分析机父文件系统，须结合 findmnt |
| `mount` | 无参数显示当前挂载 | 检查当前选项；进一步用 `findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS /mnt/evidence` 明确对象和 `ro`。仅有 `ro` 不保证所有类型都不回放日志 |

### 02.3 Btrfs、LVM、ZFS 与 RAID

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `btrfs subvolume list -p -u -t /mnt/evidence` | `subvolume list` 列子卷；`-p` 父 ID；`-u` UUID；`-t` 表格输出 | 路径相对于查询文件系统的顶层关系，需结合实际挂载子卷解释；在已完成只读挂载的分析副本上使用，不能把路径名称当快照证明 |
| `btrfs subvolume show /mnt/evidence/root/history` | `show` 查询给定路径的子卷属性 | 普通目录会失败。核对子卷 ID、UUID、Parent UUID、Received UUID、创建时间、标志及相关快照；“是子卷”与“具有快照来源”分开判断，路径仅为示例 |
| `pvs -o pv_name,pv_uuid,vg_name` | 列物理卷并选字段 | 关联 PV、卷组与目标设备；默认扫描作用于当前可见设备，避免混入分析机存储 |
| `vgs -o vg_name,vg_uuid,vg_size` | 列卷组并选字段 | 将卷组身份与配置副本、设备元数据核对；同名卷组或克隆 UUID 需独立标记 |
| `lvs --segments -o lv_name,vg_name,segtype,devices` | `--segments` 每段输出；`-o` 选字段 | 还原 LV 到成员设备的结构。`pvs --segments` 可看 PV 分段；不要给 `vgs` 套用此选项 |
| `cat "$EVIDENCE_ROOT/etc/lvm/backup/data"` | 读取名为 data 的卷组文本备份 | 查 LV 名、大小、UUID、creation_time 等字段；副本可能过期，字段时间不是业务文件创建时间。LVM 是卷管理层，LV 内部仍需识别文件系统 |
| `zpool status -v` | `status` 查池与成员；`-v` 显详细错误信息 | 对已经隔离导入的分析副本或明确现场查询；不自动导入池，不把池健康状态当成历史数据完整性的保证 |
| `zfs list -r -t filesystem,volume,snapshot -o name,type,used,mountpoint data` | `-r` 递归；`-t` 明确包括快照；`-o` 选字段；data 是示例池名 | 清点文件系统、卷与快照；无 `-t snapshot` 的默认列表通常不能作为完整快照清单 |
| `mdadm --detail /dev/md0` | `--detail`（`-D`）查询已组装阵列 | 读取级别、成员、状态及适用类型的条带信息；`/dev/md0` 必须是明确对象，不在原介质上创建、修复或重建阵列 |

Btrfs 列表和属性含义可对照[官方子卷手册](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html)。存储层复核路线见[镜像与文件系统取证](/knowledge/fic-case-02/)。

## 03 服务、端口与启动项

### 03.1 包记录与服务运行

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `dpkg --admindir="$EVIDENCE_ROOT/var/lib/dpkg" -l '*postgresql*'` | `--admindir` 指离线包数据库；`-l` 列包状态；模式限定包名 | `ii` 等组合要按状态列解释，`rc` 是已删除且有配置残留；客户端包不足以确认服务端，配合配置、数据和日志 |
| `dpkg -l \| grep -i postgres` | `-l` 列当前系统包；`grep -i` 忽略大小写过滤 | 仅用于目标现场/仿真；过滤结果容易遗漏手工部署和容器服务，不能代替部署清单 |
| `rpm -qa \| grep -i mariadb` | `-q` 查询；`-a` 所有已登记包 | RHEL 系现场包清单；离线需指定目标数据库并核对版本适配，不能查询分析机后归属目标 |
| `ss -tlnp` | TCP、监听、数字地址/端口、进程信息 | 记录监听地址、端口、PID与程序；权限可能隐藏进程信息。默认端口只作线索，须核对进程和实例 |
| `netstat -tlnp` | net-tools 中同样选择 TCP、监听、数字表示、进程 | `ss` 缺失时的现场备用；不要为了查询在原目标上临时安装工具 |
| `systemctl list-unit-files --type=service --state=enabled` | `--type` 仅服务；`--state` 仅 enabled | 给出启用的服务单元文件；与 active、运行日志、实际进程分开记录。离线优先读取 unit 和链接 |
| `lxc-ls -f` | `-f`（`--fancy`）输出格式化容器清单，可包含名称、状态、自启、组及 IP 等字段 | 仅用于已确认的目标会话或隔离副本。核对容器配置与 rootfs；离线目录存在不证明运行，LXC 与 Incus/LXD 的 CLI 不混用 |

LXC 格式化清单参数见[官方 lxc-ls 手册](https://linuxcontainers.org/lxc/manpages/man1/lxc-ls.1.html)；它查询的是相应会话/路径下的容器，不自动读取任意磁盘中的历史状态。

### 03.2 定时任务与启动链路

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `cat "$EVIDENCE_ROOT/etc/crontab"` | 静态读取系统任务 | 五个时间字段之后通常还有执行用户和命令；提取账户、脚本、参数、环境及日志输出位置 |
| `crontab -l`；`crontab -u analyst -l` | `-l` 列任务；`-u` 指定示例账户，权限须满足 | 目标现场查询；离线读取对应 `/var/spool/cron/` 布局。用户任务通常没有单独的“执行用户”列 |
| `ls -l "$EVIDENCE_ROOT/etc/cron.d/"` | `-l` 显文件属性与软链 | 定位分片任务后逐个读取；目录中有文件不等于任务执行。实际格式通常与系统 crontab 一致 |

例如发现 `ngrok http 80`，先记录它的启动位置、运行账户和引用配置，再查历史日志与访问记录。重启隧道得到的新端点无法回答历史端点问题。

容器命令统一见[Docker 现场流程与操作边界](/knowledge/docker-evidence-02/)；Docker 的镜像、实例、存储与日志细节沿对应专题检索。本页不重复容器命令表。

## 04 Web 配置、日志与摘要

### 04.1 沿配置定位真实文件

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `cat "$EVIDENCE_ROOT/etc/nginx/sites-available/default"` | 读取已确认的普通文件 | 提取 `root`、`location`、`rewrite`、`access_log`、`include`。站点可能从其他文件载入，不能只看此默认名称 |
| `readlink "$EVIDENCE_ROOT/etc/nginx/sites-enabled/default"` | 读取离线软链目标文本 | 把相对或绝对目标重新定位到检材根内，再读取实体；两个路径可能同一实体，也可能独立文件 |
| `readlink -f /etc/nginx/sites-enabled/default` | 规范化现场实际路径 | 仅在目标现场使用；先确认本命令不会解析到分析机。哈希对象是实体字节，不是软链文本 |
| `cat "$EVIDENCE_ROOT/var/log/nginx/access.log"` | 读取当前留存日志 | 核对路径、状态码、来源与日志时区；请求路径变化支持访问行为，单独不能证明文件改名或成功登录 |
| `zcat "$EVIDENCE_ROOT"/var/log/nginx/access.log.*.gz` | 顺序输出 gzip 日志解压内容 | 覆盖轮转记录；通配符无命中时会报错，应先检查实际文件。输出顺序按文件展开，不等于全局时间顺序 |
| `openssl dgst -sm3 ./work/rewrite.conf` | `dgst` 摘要命令；`-sm3` 选算法；可用 `-md5`、`-sha256` | 对完整副本字节计算摘要；保留换行、BOM、空格和注释。不要把抽出的规则文本当原文件摘要 |

### 04.2 哈希、编码与输出格式

```bash
md5sum ./work/sample.exe
sha256sum ./work/sample.exe
printf '%s' 'aHR0cHM6Ly9hcGkuZXhhbXBsZS5pbnZhbGlkL2NvbGxlY3Q=' | base64 -d
```

`md5sum`、`sha256sum` 读取完整文件，输出摘要和文件名。摘要十六进制大小写是表示差别；文件末尾换行则属于输入字节，会改变结果。MD5 可用于既有标识比对，但不要把相同 MD5 单独当成抗篡改保证。Base64 的 `-d` 是解码；示例使用 `printf '%s'` 避免额外换行，解码得到 `https://api.example.invalid/collect`，它是说明编码格式的示例地址，不能直接访问检材里的端点。

在 Windows 分析环境，可使用 `certutil -hashfile .\work\sample.exe MD5`：`-hashfile` 指文件摘要任务，后面的路径和 `MD5` 分别指定对象和算法，也可用 `SHA256`，既有 SHA-1 标识比对可使用算法名 `SHA1`。保存工具完整输出，再明确采用的摘要值；不因输出大小写而重新修改输入文件。

## 05 文件结构、二进制与媒体

### 05.1 类型识别、字节与字符串

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `file ./work/sample.bin` | 通过签名和结构规则识别文件 | 扩展名不可信；识别结果仍要与头部、尾部和结构解析互证，特别是残缺或嵌套文件 |
| `xxd -l 64 -s 0 ./work/sample.bin` | `-l` 限 64 字节；`-s` 从指定字节偏移读取 | 输出偏移、字节和字符预览；默认 `xxd file \| head` 也能预览，但限长更明确 |
| `strings -n 6 ./work/sample.bin` | `-n 6` 最短六字符 | 搜候选路径、函数名、域名；输出只是字节片段，不能证明程序使用过它 |
| `strings -e l -n 6 ./work/sample.bin` | `-e l` 以小端 16 位编码扫描 | 补充 UTF-16LE 字符串线索；中文 GBK/UTF-8 等还需按实际编码解码，不能假定 strings 会完整还原全部中文 |
| `readelf -h ./work/libsecurity.so` | `-h` ELF 文件头 | 核对架构、位数和字节序，避免按错误 ABI 反汇编 |
| `readelf -S ./work/libsecurity.so`；`readelf -x .rodata ./work/libsecurity.so` | `-S` 节表；`-x` 十六进制显示指定节 | 定位只读常量候选；`.rodata` 不是唯一密钥来源，需回到代码引用验证 |
| `objdump -d ./work/libsecurity.so` | `-d` 反汇编可执行节 | 静态查看逻辑；无符号、未知架构或混合代码数据时要核对解码设置，不执行样本 |

以上字符串与 ELF 参数可对照[GNU Binutils 官方手册](https://sourceware.org/binutils/docs/binutils/)。

### 05.2 媒体、嵌入内容与元数据

| 命令与实际示例 | 参数作用 | 取证用途与验证 |
| --- | --- | --- |
| `ffprobe -v error -show_format -show_streams ./work/video.mp4` | `-v error` 只显示错误级日志；两个 `-show` 选容器与流信息 | 查看流、时长、编码和结构异常；能解析头部不等于每个采样都能播放 |
| `mp4dump ./work/video.mp4` | 列 MP4 box 树 | 查 `stco`、`stsz` 等偏移和采样表；修复必须对副本定位具体字段并验证采样落点，不能把所有数值统一加减 |
| `binwalk ./work/sample.bin`；`binwalk -E ./work/sample.bin` | 默认签名扫描；`-E` 熵分析（先核对安装版本帮助） | 定位嵌入结构和高熵区；高熵可能来自压缩、加密或已压缩媒体，不能据此确定算法 |
| `binwalk -e ./work/sample.bin` | `-e` 启用提取，可能调用提取器或写出大量文件 | 只在隔离工作目录中针对副本使用；先签名扫描，再按需要提取，不执行输出程序。不同版本的提取行为需核对[项目文档](https://github.com/ReFirmLabs/binwalk) |
| `exiftool -a -u ./work/image.jpg` | `-a` 允许重复标签；`-u` 显示可解析的未知标签 | 提取相机、时间、定位等元数据；标签可能修改、复制或缺失，保留组别、原始值与时区，不直接归属拍摄者 |
| `zbarimg ./work/qr.png` | 扫描二维码图像 | 记录码制和完整载荷；若内容是 URL，先作为文本与应用/下载记录核对，不自动打开 |

## 06 镜像访问与只读验证

### 06.1 裸盘镜像的偏移挂载

下面仅示范**已确认分区为 ext4、逻辑扇区 512 字节、起始扇区 2048**的分析副本。实际使用前必须从分区表核对这三个条件，并确认挂载点是分析机的空目录。

```bash
sudo mount -t ext4 -o ro,noload,loop,offset=$((512*2048)) ./work/image.dd /mnt/evidence
findmnt -no SOURCE,TARGET,FSTYPE,OPTIONS /mnt/evidence
```

`-t ext4` 指定类型；`-o` 后的 `ro` 只读、`noload` 不加载日志、`loop` 通过回环访问文件、`offset` 为字节偏移。起始偏移是“逻辑扇区大小 × 起始扇区”；不要默认所有磁盘都是 512 字节。`ro` 单独用于脏的 ext3/ext4 时仍可能回放日志，官方挂载说明建议结合 `noload` 或设备层只读；其他文件系统要使用它自身的保护方式，不能套用 ext4 选项。见[util-linux 挂载手册](https://github.com/util-linux/util-linux/blob/master/sys-utils/mount.8.adoc)。

挂载失败时先记录错误并检查布局、文件系统与工具支持，不对原介质运行修复。需要写入性恢复或日志回放时另建副本，写明修改条件，完成后与未修改对象核对。

### 06.2 虚拟磁盘与 NBD

`qemu-nbd` 可把虚拟磁盘导出为块设备。下例假设 `disk.vhd` 已确认是传统 VHD（QEMU 格式名 `vpc`），`/dev/nbd0` 已准备且空闲；VHDX 与 QCow2 分别要使用实际对应格式，不能仅凭扩展名选择。

```bash
sudo qemu-nbd --read-only --format=vpc --connect=/dev/nbd0 ./work/disk.vhd
lsblk -f /dev/nbd0
# 完成读取并卸载其所有挂载分区后断开
sudo qemu-nbd --disconnect /dev/nbd0
```

`--read-only` 将导出设为只读；`--format` 明确格式；`--connect` 连接设备；`--disconnect` 解除连接。只读 NBD 仍不免除核对挂载选项和宿主内核解析风险；不可信镜像优先在隔离分析环境用 libguestfs 读取，详见[QEMU NBD 官方手册](https://www.qemu.org/docs/master/tools/qemu-nbd.html)。

```bash
guestmount --format=vpc -a ./work/disk.vhd -i --ro /mnt/evidence
# 完成后解除 FUSE 挂载
guestunmount /mnt/evidence
```

`-a` 加入镜像；`-i` 探测操作系统并按其布局挂载；`--ro` 对镜像与挂载明确禁止写入。`-o` 是 FUSE 选项，不能用 `-o ro` 取代源镜像的 `--ro`。自动探测失败时按实际分区指定挂载，不把“无法自动识别”解释成无数据。命令语义见[guestmount 手册](https://libguestfs.org/guestmount.1.html)。

## 07 工具选择速查

### 07.1 静态解析与数据读取

| 工具 | 输入与用途 | 应保留的验证结果 |
| --- | --- | --- |
| DIE、PE-bear、pestudio | PE 结构、资源、调试与时间字段 | 字段所在目录、原始值；PE 时间字段只作候选，不能单独认定实际编译日期 |
| IDA Pro | PE、ELF、Go 等反汇编/反编译 | 入口、关键调用、数据引用及离线复现条件，区分代码常量与运行输出 |
| Capstone | 脚本化反汇编，包含 ARM64 | 选定架构、位数、模式和输入范围，核对函数边界与反汇编一致性 |
| jadx、JEB | DEX 反编译 | 方法、权限调用、桥接与数据流；反编译失败时回看字节码 |
| apktool | APK 资源与 Manifest 解包、资源还原 | 包名、资源 ID、assets 与 native 文件；需重打包时只在副本上，原 APK 哈希独立保存 |
| DB Browser for SQLCipher | 加密 SQLite 读取 | 密钥/兼容参数来源、表结构和有效记录；能打开一页不等于全库解密正确 |
| DB Browser for SQLite | 普通 SQLite 查询 | 携带相关 WAL/SHM，记录表名、字段、筛选、计数及缺失值处理 |
| 010 Editor、HxD | 字节查看、模板解析与副本编辑 | 原偏移、原字节、新字节与修复后结构；“脚本运行成功”需实际字节复核 |
| olefile、oletools | OLE 复合文档和流解析 | 流名、偏移、BIFF 记录链与长度边界，不把整个复合文件当一条平坦记录流 |
| zbarimg | 图像二维码读取 | 原图与完整载荷，乱码或缺失时回到图像质量与编码核对 |
| ffprobe、MP4Box | 媒体容器和流检查 | box/采样结构、错误与实际播放验证，修复结果另存 |
| dji-log-parser-js | DJI 飞行记录解析 | 解析版本、时间/坐标单位、轨迹范围；解码失败与加密记录分开记录 |
| PyCryptodome、hashlib、struct | 算法、摘要、二进制结构复现 | 算法参数、字节序、密钥编码、分组/填充、输入输出哈希 |
| sympy、libnum | RSA 数论分析 | n/e 的来源、可用攻击条件、结果对公钥关系与文件结构的复核 |

### 07.2 综合取证与现场补充

| 工具 | 用途 | 操作边界 |
| --- | --- | --- |
| FinalShell | 连接仿真副本或明确目标会话 | 先确认宿主/容器归属，记录登录和任何新增组件；连接成功不是历史服务运行证明 |
| Autopsy、FTK Imager、X-Ways | 镜像采集、文件系统与综合分析 | 保留镜像标识、哈希、分区/时区设置、导出路径与解析限制 |
| Sleuth Kit：fls、icat、mactime | 文件列表、按元数据对象导出、时间线 | 记录文件系统和分区偏移、元数据编号、时间字段语义；删除条目可恢复性单独判断 |
| btrfs、pvs/vgs/lvs、zpool | 子卷、卷管理与池结构 | 先确认对象、只读或隔离访问条件，不做创建、修复或重建 |
| Registry Explorer、RegRipper、RECmd | 离线注册表 hive | 连同事务日志解析；核对 ControlSet、键更新时间与字段语义 |
| EZ 工具：PECmd、AmcacheParser、MFTECmd、EvtxECmd | Windows 痕迹批量解析 | 解析器版本和输出字段需对应系统；Amcache/缓存条目不直接等于执行证明 |
| Volatility 2/3 | 已采集内存镜像 | 版本、符号与平台匹配；插件结果结合对象关系和其他痕迹复核 |
| KAPE | 已授权的批量采集与解析 | 区分采集动作和解析动作，记录目标范围及采集新增痕迹 |
| Wireshark、Zeek | 已采集流量 | 记录过滤、会话、时间和加密可见性，不凭无命中断言无网络行为 |
| binwalk、ExifTool | 嵌入结构、熵和元数据 | 高熵/标签均只作线索，回到内容和结构验证 |
| MobSF | 移动应用静态分析 | 将报告项回定位到 APK 文件与调用；动态功能须在隔离副本内另行设置 |

## 08 可复用的小脚本与校验

以下脚本只读取传入副本，不执行检材。它们分别用于关键词残留、记录链和熵值三个既有任务；输出必须带位置或范围，才能回到原始字节复核。

### 08.1 大文件关键词与上下文

按固定字节关键词扫描，保留绝对偏移和前后各 40 字节。跨块留存长度至少覆盖“关键词 + 两侧上下文”，并避免重复输出同一命中。

```python
def scan_keyword(path, needle, chunk_size=64 * 1024 * 1024, context=40):
    if not needle:
        raise ValueError("keyword must not be empty")
    overlap = len(needle) - 1 + context * 2
    if chunk_size <= overlap:
        raise ValueError("chunk_size must exceed overlap")
    carry, consumed, emitted_until = b"", 0, -1
    with open(path, "rb") as stream:
        while True:
            part = stream.read(chunk_size)
            final = not part
            buf = carry + part
            base = consumed - len(carry)
            limit = len(buf) if final else max(0, len(buf) - context)
            start = 0
            while True:
                pos = buf.find(needle, start)
                if pos < 0:
                    break
                absolute = base + pos
                if pos + len(needle) <= limit and absolute > emitted_until:
                    snippet = buf[max(0, pos - context):pos + len(needle) + context]
                    print(hex(absolute), repr(snippet))
                    emitted_until = absolute
                start = pos + 1
            if final:
                break
            consumed += len(part)
            carry = buf[-overlap:]

scan_keyword("root-partition.dd", b"db-node")
```

查中文时使用同一词的 UTF-8、GBK、UTF-16LE 字节分别扫描，并保留命中编码。某个主机名命中原始介质后，先判上下文是否是完整 hosts 行、旧版本、日志或随机片段，不能自动覆盖当前配置。

### 08.2 长度型记录链解析

适用于“2 字节类型 + 2 字节长度 + 指定长度载荷”的小端记录布局。BIFF 应先从 OLE 导出正确工作簿流；其他格式只有确认布局相同后才可复用。

```python
def parse_records(data):
    out, offset = [], 0
    while offset < len(data):
        if len(data) - offset < 4:
            raise ValueError(f"truncated header at {offset:#x}")
        kind = int.from_bytes(data[offset:offset + 2], "little")
        size = int.from_bytes(data[offset + 2:offset + 4], "little")
        end = offset + 4 + size
        if end > len(data):
            raise ValueError(f"payload exceeds input at {offset:#x}")
        out.append((offset, kind, size, data[offset + 4:end]))
        offset = end
    return out

example = bytes.fromhex("01 00 03 00 41 42 43")
print(parse_records(example))
```

示例应产生偏移 0、类型 1、长度 3、载荷 `ABC`。截断时保留失败偏移与尾部字节，不能静默把短载荷当完整记录；大端或不同长度字段格式需明确改解析规则。

### 08.3 熵值分析

```python
import math

def entropy(data):
    if not data:
        return 0.0
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    size = len(data)
    return -sum((count / size) * math.log2(count / size)
                for count in counts if count)

print(entropy(b"AAAA"))
print(entropy(bytes(range(256))))
```

示例分别为 0 与 8 bit/byte。分析飞行日志或混合文件时按窗口保存起始偏移、窗口长度与熵，而不只报全文件平均。高熵只支持继续检查压缩/加密区的判断；短窗口、随机数据和压缩媒体都会影响结果，应结合魔数、记录边界与可解码内容。

## 09 实战：核对原始分区中的主机名残留

### 09.1 场景、材料与读取顺序

已取得单个 Linux 根分区副本 `root-partition.dd`，当前 `/etc/hosts` 为大量零字节，应用连接配置仍出现 `db-node`。目标是寻找映射候选，并判断它是否能与服务配置对应。材料包括分区镜像、hosts 导出件、业务配置及相关容器/网络定义；先分别记录路径、大小与 SHA-256，不能直接在检材里重写 hosts。

```bash
sha256sum ./root-partition.dd
blkid -p -o export ./root-partition.dd
xxd -l 64 ./work/hosts
```

识别结果仅适用于这份已定位的分区。确认格式后，把 08.1 的完整扫描脚本保存为 `keyword_scan.py`，使末行读取该分区并查找 `b"db-node"`，在同一工作目录执行：

```bash
python3 keyword_scan.py
```

脚本应输出命中偏移与字节上下文。例如下列是解释输出格式的示意，偏移与内容不能用于其他镜像：

```text
0x120000 b'...198.51.100.20 db-node\n...'
```

再回到实际命中偏移，用 `xxd -s <实际偏移> -l <检查长度> root-partition.dd` 读取完整上下文，区分完整 hosts 行、日志片段、旧文件残留或无结构片段。若主机名跨扫描块边界，脚本的重叠保留逻辑也应给出同一绝对偏移；不要只保存脱离位置的一段可读字符串。

### 09.2 交叉验证与限制

把候选行与业务配置的主机名、对应端口、容器定义/rootfs 和已有连接日志相互核对。完整映射行支持“介质留存此映射候选”；只有对象身份、配置版本和使用痕迹进一步对应，才能评估历史使用。默认 `lxcbr0` 网段、一个整数 IP 或静态字符串均不足以独立判断服务归属。

保存扫描输入哈希、关键词字节/编码、绝对偏移、上下文、工具参数与采用/排除理由。该流程不修改分区和当前配置；需要给仿真副本补映射时，另存修复前后的文件，标记仿真改变，不能用新日志证明旧映射已被使用。本页示例未针对读者的检材复跑，缺失分区、已覆写数据、压缩/加密区域或采集范围不足都应作为结果限制。

## 10 按实战任务选择工具与输出口径

| 任务 | 工具或入口 | 应保留的输出 | 详细步骤 |
| --- | --- | --- | --- |
| 集群数据映射 | kubectl 读取 Pod/PVC/PV/ConfigMap，静态 YAML 对照 | 对象 UID、命名空间、挂载和实际路径 | [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/) |
| 删除行解析 | 匹配版本 mysqlbinlog，ROW 事件与表结构 | 文件/事件偏移、事务、列映射、before image | [数据库恢复](/knowledge/forensic-database-recovery/) |
| 无线握手验证 | Wireshark、hcxtools、Hashcat 22000 | AP/STA、会话组、EAPOL/MIC、候选验证结果 | [无线网络](/knowledge/forensic-wireless/) |
| HTTP/FTP 与反向会话 | Wireshark Follow Stream、方向选择及 Raw 导出 | 请求响应、数据通道、文件哈希、真实命令行 | [网络流量](/knowledge/forensic-network-traffic/) |
| Android 动态参数 | JADX、Frida，匹配进程和类加载器 | 方法签名、调用条件、参数、时间及 URL 字节 | [Android 程序分析](/knowledge/fic-case-06/) |
| PE 解密与运行行为 | DIE/IDA/x64dbg，隔离环境 | 实际映射基址、EP RVA、模块列表和派生产物 | [逆向分析](/knowledge/fic-case-07/) |
| 内存记录与系统身份 | Volatility 的匹配版本和可用插件 | 时间语义、PID/RID、对象及注册表上下文 | [内存取证](/knowledge/forensic-memory/) |
| Office 与分卷恢复 | 格式解析、归档工具、Passware 的限定候选任务 | 完整分卷清单、恢复验证和解密对象 | [文档取证](/knowledge/forensic-documents/) |
| 助记词词序 | BTCRecover 的 tokenlist 和已知地址 | 约束、路径、搜索范围和地址匹配 | [密码学取证](/knowledge/fic-case-08/) |
| GCM 偏好记录 | APK 调用链、XML 解析、PyCryptodome 认证解密 | 字段布局、AAD、标签和明文语义 | [手机应用](/knowledge/forensic-mobile-apps/) |

**执行顺序：** 先静态读取与保全 → 明确版本和字段 → 在副本做最小复现 → 用独立结构或对象验证。工具界面显示的数量应注明当前范围：导入库数量、握手有效对数、运行时模块数和进程列表条数不能互相替代。
