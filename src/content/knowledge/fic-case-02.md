---
title: "证据介质与文件系统"
summary: "识别检材形态、分区与文件系统，并处理 Btrfs、LVM、ZFS 和嵌套镜像。"
module: "Forensics"
track: "计算机取证"
topic: "镜像与文件系统"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

## 01 识别介质与存储层次

文件扩展名不能确定检材结构。一个 `.dd` 可能是整盘、单分区或 RAID 重组结果；一个没有扩展名的高熵文件可能是加密卷；一份解密出的 VHD 内还可能包含其他文件。先把各层对应起来，再谈路径、快照或恢复。

### 01.1 介质形态与所需材料

| 形态 | 结构与识别目标 | 需要保留的材料 |
| --- | --- | --- |
| 裸盘镜像 `.dd/.img` | 判断整盘还是单分区、扇区大小与起始偏移 | 大小、哈希、采集清单与分区表 |
| RAID0 成员或重组镜像 | 成员顺序、条带大小、数据起点决定重组结果 | 每个成员及哈希、阵列参数与重组记录 |
| 分区和文件系统 | 分区表描述范围，超级块描述内部文件系统 | 起始扇区、长度、类型、UUID与超级块 |
| LVM 逻辑卷 | PV → VG → LV → 文件系统 | PV 元数据、VG 备份与归档、LV 映射 |
| VeraCrypt/TrueCrypt 卷 | 加密卷头验证成功后才能解析内部结构 | 原密文、候选口令、PIM和密钥文件来源 |
| VHD/VHDX | 文件中的虚拟磁盘与内部扇区映射 | 格式信息、虚拟容量、内部分区与派生关系 |

**实战：** 一份标为 `disk.dd` 的服务器镜像与一个高熵用户文件同时出现。先确认镜像是否已经完成 RAID0 重组；若只有成员盘，不能直接把成员内的偶然魔数当作可完整挂载的文件系统。对于加密文件，先追踪凭据与程序逻辑，不能把它当作裸分区扫描后就认定“没有文件”。

所有以下命令以工作副本或只读检材为输入，输出写入分析目录。`/mnt/evidence` 表示已经完成只读挂载的根目录；`root-partition.dd` 表示已定位并提取的单个分区。

## 02 通过结构识别文件系统

### 02.1 魔数位置与解释边界

| 结构 | 特征 | 相对位置及注意事项 |
| --- | --- | --- |
| Btrfs | ASCII `_BHRfS_M` | 第一超级块起点为分区内 `0x10000`，魔数字段在超级块内 `+0x40`，即 `0x10040` |
| ext2/3/4 | 小端魔数字节 `53 EF` | 主超级块在分区内 `1024`，`s_magic` 在其 `+0x38`，即 `1080` |
| NTFS | ASCII `NTFS    ` | 分区引导扇区内 `+3`，还需验证 BPB 与分区范围 |
| XFS | ASCII `XFSB` | 主超级块从文件系统起点开始，需继续核对版本和块大小 |
| LVM2 PV | ASCII `LABELONE` | 通常在设备前部标签扇区，需核对标签扇区与 `LVM2 001` 类型 |
| ZFS | uberblock magic `0x00bab10c` | vdev 标签区域存在副本，设备首尾均可能有标签；按字节序与结构验证 |
| VeraCrypt/TrueCrypt | 解密后的 `VERA`/`TRUE` | 处于卷头解密后的字段；原密文没有可供直接定位的明文签名 |

魔数命中是候选。文件内容、旧分区、重复超级块和嵌套磁盘也可能包含相同字节。先记录绝对偏移，再减去结构相对偏移得到候选文件系统起点，核对分区边界、块大小、UUID和其他备份结构。[Btrfs 超级块位置](https://btrfs.readthedocs.io/en/latest/On-disk-format.html)、[ext 超级块字段](https://www.kernel.org/doc/html/latest/filesystems/ext4/super.html)说明了这些偏移关系；VeraCrypt 的无明文签名设计见[卷格式说明](https://veracrypt.io/en/VeraCrypt%20Volume%20Format%20Specification.html)。

### 02.2 实战：验证一个 Btrfs 分区

```bash
# 单分区副本：读取第一超级块中的魔数，不修改输入
xxd -s 0x10040 -l 8 ./root-partition.dd
blkid -p -o export ./root-partition.dd
btrfs inspect-internal dump-super -f ./root-partition.dd
```

示例十六进制输出中的 `5f42 4852 6653 5f4d` 对应 `_BHRfS_M`。再核对 `fsid`、`bytenr`、校验与设备信息；探测到 `TYPE=btrfs` 后，才能把后续子卷分析建立在 Btrfs 结构上。对于整盘镜像，偏移应为“分区起点 + `0x10040`”，不能直接套用单分区命令。

对已提取的 ext 候选分区，可以在 `1024+0x38=1080` 处读取魔数，再用文件系统探测复核。以下命令输入应是相应 ext 分区，不能沿用一个已经确认为 Btrfs 的对象。

```bash
xxd -s 1080 -l 2 ./ext-partition.dd
blkid -p -o export ./ext-partition.dd
```

若输出字节为 `53 ef`，仍需核对超级块版本、块大小、UUID和分区边界，才能确认 ext 系文件系统。魔数是超级块内的字段，不是超级块起始字节。

**运行现场补充：** `lsblk -f`、`blkid`、`findmnt`、`df -Th` 分别观察块设备、标识、实际挂载和已挂载容量，只在明确的目标会话中使用。离线检材则读取分区、`/etc/fstab` 与存储元数据。配置中写过某种文件系统，不等于采集时正在使用；当前未挂载也不等于从未使用。

## 03 Btrfs 子卷、快照与旧数据

### 03.1 结构与恢复价值

Btrfs 子卷是可独立挂载的树。快照保存某个子卷在相应事务时刻的树状态，可以只读或可写。写时复制 COW 使共享的旧块在修改时仍可能被其他树引用，但无引用的块会被回收；删除或覆盖后能否恢复取决于引用、事务、分配和后续写入，不能承诺一定存在完整旧版本。

| 元数据对象 | 用途 | 核对重点 |
| --- | --- | --- |
| `ROOT_ITEM` | 子卷根、UUID、代际与相关属性 | 确认目标确是子卷根及其事务关系 |
| `DIR_ITEM` / `DIR_INDEX` | 名称和目录关联 | 名称长度、父目录、location key 与对象类型 |
| `EXTENT_ITEM` | 空间占用与引用 | 区分仍引用数据与已释放残留 |
| `CHUNK_ITEM` | 逻辑地址到设备条带映射 | 多设备、条带与物理偏移转换 |

### 03.2 实战：确认 `history` 是快照还是普通目录

**材料：** 已确认的 Btrfs 分区副本，或安全只读挂载的顶层目录 `/mnt/btrfs-top`。Btrfs 即使指定 `ro` 也可能重放 tree-log，因此挂载时还需 `nologreplay`；挂载对象必须是已验证的只读映射或副本。[Btrfs 挂载选项](https://btrfs.readthedocs.io/en/latest/Administration.html)明确说明这一点。

```bash
# /dev/loop7 为提前确认的只读分区映射，目录已建立
sudo mount -t btrfs -o ro,nologreplay,subvolid=5 /dev/loop7 /mnt/btrfs-top
btrfs subvolume list /mnt/btrfs-top
btrfs subvolume show /mnt/btrfs-top/root/history
```

需要单独挂载某个已确认子卷时，使用它相对顶层的实际路径，并继续保留只读与禁止日志重放条件。例如 `sudo mount -t btrfs -o ro,nologreplay,subvol=root/history /dev/loop7 /mnt/btrfs-history`；挂载点应先建立且为空，映射和子卷路径均已核对，不能把 `mount -o subvol=<name>` 当成无需设备与挂载点的完整命令。

示例列表为 `ID 312 ... path root/history`；详情包含 `Subvolume ID`、`UUID`、`Parent UUID`、`Creation time` 与只读标志。结合 UUID 和 parent UUID、根对象及实际路径判断快照来源。`@rootfs`、`default` 可能只是子卷名；单独看到 `/root/history` 的路径，无法确认它是快照。

**不能挂载时：** 使用元数据解析工具建立树和目录关联。搜索 `history` 后，验证它位于有效 `DIR_ITEM`/`DIR_INDEX` 中，长度为 7，且 location key 指向相应根对象。Btrfs 目录项头含 `data_len`、`name_len` 和类型字段，名称前紧邻的并非固定“两字节长度”；必须从结构起点解析。命中次数只能说明候选数量，不能证明其中每一处都是子卷，也不能代替完整路径重建。

## 04 LVM 的卷映射与配置历史

### 04.1 PV、VG、LV 分层

LVM 是卷管理层，不是文件系统。一个 LV 内可以使用 ext4、XFS 或其他文件系统。离线检材中优先查看 `/etc/lvm/backup/<vg>` 与 `/etc/lvm/archive/`，这些文本记录卷组 UUID、PV、LV、段映射及部分创建信息。

```bash
find /mnt/evidence/etc/lvm/backup /mnt/evidence/etc/lvm/archive \
  -maxdepth 1 -type f -print
grep -nE 'id =|creation_time|physical_volumes|logical_volumes|device =|extent_size|segment_count' \
  /mnt/evidence/etc/lvm/backup/root
```

**判读示例：** 备份中卷组名为 `root`，逻辑卷为 `data`，设备映射可能显示 `/dev/mapper/root-data`。需与实际 PV 元数据、UUID和大小交叉验证；`device` 路径是保存时提示，克隆或换盘后可能改变。归档中的创建时间描述配置记录或对象字段，不能自动认定为系统安装时间。

目标现场可用 `pvs`、`vgs`、`lvs` 清点现状；离线恢复若需要激活卷组，应在受控副本环境完成，避免卷组同名或 UUID 冲突。判断是否使用 NTFS、XFS 或 LVM 时，逐项列出正向证据，不能根据“Linux 通常不用 NTFS”排除候选。

## 05 ZFS 池与业务数据定位

### 05.1 池结构与证据路径

ZFS 将 vdev 组合为存储池，池内的数据集可以承载数据库文件。uberblock 记录事务相关状态，块指针描述数据树；压缩、校验、分配和多设备布局会影响原始字节检索。设备尾部不是唯一元数据位置，首尾标签与多个副本应共同检查。

**实战：** 启动历史记录 `zpool create db /media/zfs`，镜像中也保存一个大文件 `/media/zfs`。把这条命令视为部署线索，固定该文件后验证 vdev 标签、池名和事务；不要在分析机复制执行 `zpool create`。目标现场的 `zpool status`、`zfs list` 描述对应会话；离线仅有文件时先解析标签，确需导入时在隔离环境中限制设备范围并使用只读导入。

```bash
# 在隔离分析环境，work-vdevs/ 仅含已核对的副本；无池名仅列出候选
zpool import -d ./work-vdevs
# 示例池名已由标签确认：不挂载数据集，以只读属性导入
sudo zpool import -N -o readonly=on -d ./work-vdevs db
zpool status db
zfs list -r db
```

`-N` 避免自动挂载，`readonly=on` 限制池写入。不要为方便加 `-f`，先核实池是否在别处活动、设备是否完整和名称冲突。只读导入的条件与限制见[OpenZFS 导入说明](https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Operations/Troubleshooting.html)。

### 05.2 原始检索必须返回结构验证

可在池副本中搜索已知表名、用户别名和 JSON 配置，记录命中偏移。例如 `mac_user`、`mac_vod`、`"version":` 可分别引向业务表和集群版本线索。每次命中都读取前后文，再用所属文件、页结构、表定义和时间判定意义。

原始池中的可读姓名和 IP 字节可能来自日志、旧版本、备份或未引用块；压缩后的记录也可能无法直接命中。只有验证字段边界、编码和对象归属后，才能转成业务结论；IP整数转换详见[数据库取证](/knowledge/fic-case-05/)。

## 06 虚拟磁盘与多层保护

### 06.1 实战：密文解出 VHD 后继续取证

**场景：** 程序静态分析显示 `RC4 解密 → OpenVirtualDisk/AttachVirtualDisk → 删除临时文件`。需要保存内层流水文件，应先固定原密文和样本，再离线复现已确认的密钥、密钥流初始化与长度；不依赖运行程序留下临时文件。

1. 保存原密文与解密脚本输入，输出为独立派生文件 `recovered.vhd`。
2. 检查输出长度、VHD 标识或页脚及结构；高熵降低或出现少量文本不足以证明解密成功。
3. 使用支持格式的只读解析工具读取分区；Linux 可使用 libguestfs 的只读模式，或谨慎配置 `qemu-nbd` 只读映射。不要把动态 VHD 文件直接当作线性裸盘。
4. 固定内层导出的文件，记录 `原密文 → recovered.vhd → 内部分区 → ledger.csv` 的完整派生链。
5. 对流水先确定地址、方向、资产、时间和去重口径，再统计金额，见[虚拟货币与资金流](/knowledge/fic-case-12/)。

Windows 的 `OpenVirtualDisk` 与 `AttachVirtualDisk` 是虚拟磁盘打开和附加接口，具体访问与只读标志决定行为；程序调用了它们只证明代码路径存在，是否成功还需返回值和运行痕迹。整个分析中，原镜像保持只读，修复、解密和仿真产生的材料都单独编号并计算哈希。
