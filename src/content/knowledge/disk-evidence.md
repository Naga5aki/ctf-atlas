---
title: 取证镜像与文件系统识别
summary: 从镜像类型、分区偏移到文件系统逐层识别，再检查 Btrfs 子卷。
module: Forensics
track: 计算机取证
topic: 镜像与文件系统
tags: [文件系统]
status: 已整理
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
updated: "2026-10-01"
---

## 01 固定证据与识别外层格式

拿到镜像后先记录哈希、字节数与开头字节，区分**整盘镜像、单分区镜像、虚拟磁盘、归档或容器文件**。扩展名只能提示用途，不能代替结构检查。

```bash
sha256sum evidence.img
stat -c '%n %s bytes' evidence.img
file evidence.img
xxd -l 512 evidence.img
```

记录镜像路径、哈希算法、哈希值和获取时间。后续提取分区、解析文件都另存为派生结果，不在镜像上运行修复命令。`file` 只给初步识别；遇到虚拟磁盘先确认镜像类型，再选择能读取该格式的工具。

U 盘的 NTFS、FAT32 与 exFAT 需分别分析；设备接入、MFT 记录、XFW/MFTECmd 操作和文件恢复统一见[U盘取证](/knowledge/forensic-usb-evidence/)。

## 02 从分区偏移进入文件系统

若是整盘镜像，用 `mmls` 查看分区表，记下目标分区的 `Start` 和 `Length`。两者以输出所标注的**扇区**为单位，不是字节。把实际起始扇区代入下例；`2048` 仅作示例。

```bash
mmls evidence.img
start_sector=2048
fsstat -o "$start_sector" evidence.img
fls -o "$start_sector" evidence.img
```

`fsstat` 的 `-o` 接受文件系统起点的扇区偏移。若拿到的本来就是单分区镜像，先试 `fsstat evidence.img`，不要再套一层整盘分区偏移。若工具提示不支持该文件系统，记录限制并换对应文件系统工具；不能把“不支持”写成“镜像损坏”。

| 现象 | 优先核对 |
| --- | --- |
| `mmls` 没有可信分区 | 它是否本来就是分区镜像、虚拟磁盘或嵌套镜像 |
| 文件系统识别失败 | 扇区大小、起始扇区、LVM 或加密层 |
| 目录为空或内容错位 | 传给工具的偏移单位是否为扇区、是否选错分区 |
| 挂载失败 | 文件系统支持、偏移、加密与损坏状态，逐项排查 |

## 03 Btrfs 子卷与快照的首轮识别

识别出 Btrfs 后（超级块在卷内 `0x10000`，魔数 `_BHRfS_M` 在 `0x10040`），`@rootfs`、`history` 等名字可能是子卷，不一定是普通目录。`btrfs subvolume list` 只能针对**已挂载的目标文件系统**使用；对当前系统的 `/` 运行查到的是分析机自身。完整的 Btrfs 元数据对象（`ROOT_ITEM`/`DIR_ITEM`）、`ro,nologreplay,subvolid=5` 只读挂载与子卷/快照判读详见[证据介质与文件系统 §02–03](/knowledge/fic-case-02/)及[其他文件系统](/knowledge/forensic-fs-other/)。

若已得到单独的 Btrfs 分区镜像，可先用不会修改镜像的命令列出子卷树根：

```bash
btrfs restore -l partition.img
```

若手头只有整盘镜像，先按 `mmls` 输出提取目标分区。下例中的起始扇区、长度和每扇区字节数都必须取自该镜像的实际信息：

```bash
start_sector=2048
length_sectors=409600
sector_size=512
dd if=evidence.img of=partition.img bs="$sector_size" \
  skip="$start_sector" count="$length_sectors" oflag=excl status=progress
stat -c '%s bytes' partition.img
sha256sum partition.img
btrfs restore -l partition.img
```

如果已通过可靠的只读方式挂载到 `/mnt/evidence`，再运行 `btrfs subvolume list /mnt/evidence`、`btrfs subvolume show /mnt/evidence/实际子卷路径` 核对 ID、父子关系与快照属性。无法挂载时可继续使用 `btrfs restore` 的只读列举能力；仅凭字符串搜索到子卷名，不能认定快照仍可完整读取。

## 04 镜像格式与可见范围

| 材料 | 范围与检查 | 常见误区 |
| --- | --- | --- |
| DD / RAW / IMG | 字节流，可能是整盘或分区 | 没有分区表不一定损坏 |
| E01 / Ex01 | 证据容器，可分段、压缩和记录元信息 | 分段不是独立磁盘；须保留完整序列 |
| AD1 / L01 等逻辑材料 | 选定文件/目录及可保存的元数据 | 不等同全盘镜像，未分配空间可能未包含 |
| VMDK / VDI / QCOW2 / VHD(X) | 虚拟盘，可能依赖父盘/快照 | 只拿基础盘可能漏掉当前状态 |
| 内存 RAW / VMEM / DMP | 进程、缓存与内核对象 | 扩展名不能决定格式或完整性 |
| SquashFS、UBI/UBIFS | 固件或闪存相关文件系统 | 普通分区工具未必能直接处理 |

E01 先用 `ewfinfo` 读采集描述、时间、扇区数、错误信息和校验值，用 `ewfverify` 检查；挂载/导出时从首段进入。元信息可提供采集方式、设备和错误范围；这些记录与镜像内容、校验和实际可读性需分别核对。AD1 用支持该容器的工具打开和导出，不能默认它包含整盘扇区。

```bash
mkdir -p ./output ./mnt/ewf
ewfinfo ./evidence/disk.E01 > ./output/ewf-info.txt
ewfverify ./evidence/disk.E01 > ./output/ewf-verify.txt
ewfmount ./evidence/disk.E01 ./mnt/ewf
qemu-img info --backing-chain ./evidence/disk.vmdk
```

## 05 RAID 重组先用元信息

完整的成员识别、RAID5 校验布局、NTFS 手工参数分析、工具重组与跨条带验证集中在独立知识点 [RAID 重组取证：参数分析、重建与验证](/knowledge/forensic-raid-reconstruction/)。下面保留软件阵列的首轮识别步骤。

RAID0 的成员顺序、条带大小、成员起点和缺失盘决定重组结果；“可看到几个目录”不足以证明布局正确。每个成员先算哈希，再在隔离分析系统中绑定只读 loop。记录命令实际返回的设备名，避免照抄固定 loop 编号。

```bash
member_a=$(sudo losetup --find --show --read-only --partscan ./work/member-a.img)
member_b=$(sudo losetup --find --show --read-only --partscan ./work/member-b.img)
sudo mdadm --examine "$member_a" "$member_b"
cat /proc/mdstat
```

若阵列元数据在成员分区中，将实际分区设备代入 examine。核对 UUID、级别、成员编号、事件计数、数据偏移和条带参数。**已有元数据优先只读 assemble；`mdadm --create` 会写入或改变阵列元数据，不是常规恢复第一步。**

```bash
# 仅在确认设备属于本次工作副本、元信息和成员顺序匹配后执行
sudo mdadm --assemble --readonly /dev/md/forensic "$member_a" "$member_b"
sudo blockdev --getro /dev/md/forensic
```

没有元数据时，使用 UFS Explorer 等工具在虚拟布局中设定参数，比较分区结构、文件系统一致性和已知文件哈希。不要为了“让阵列出现”对检材 create。缺盘 RAID0 通常不能完整恢复；缺失范围要明确记录。卸载和 detach 仅针对本次创建、已记录的设备，不停止其他阵列。

## 06 Btrfs 多设备、快照与挂载边界

多个 `.btr` 成员应先核对共同 FSID、设备 ID、设备总数、chunk 分配和数据/元数据配置。多设备文件系统不等于 RAID0；数据与元数据可以采用不同冗余配置。缺设备时，`degraded` 也不能保证所有块可读。

将成员只读绑定，记录实际设备名，用 `btrfs inspect-internal dump-super` 等只读信息确认，再在独立分析环境注册对应成员。挂载时采用 `ro,nologreplay`，只有确认缺失条件允许时再考虑 `degraded`。内核或 WSL 不支持相关功能时，应换支持的分析环境，不能据此认定镜像损坏。

对正常挂载的工作副本枚举子卷、默认子卷、只读快照与删除候选，分别导出结果。检查 top-level subvolid=5 与目标子卷，避免只看默认视图。`btrfs check --repair`、写入式恢复和普通读写挂载均不用于唯一检材。

## 07 APFS、ext4 与 F2FS 的首轮识别

NTFS、FAT、exFAT、ext2/3/4 及 APFS/XFS/Btrfs 的完整扇区/块偏移表与恢复流程已按文件系统拆分为独立专页（见[卷与引导扇区](/knowledge/forensic-fs-volume/)、[ext 取证](/knowledge/forensic-fs-ext/)与[其他文件系统](/knowledge/forensic-fs-other/)）。本节保留三类移动与桌面常见文件系统的首轮结构对比：

| 文件系统 | 结构线索 | 实用检查与恢复边界 |
| --- | --- | --- |
| APFS | 容器、多卷、空间共享、对象映射、写时复制和快照 | 先识别容器/卷/快照，确认 FileVault 与密钥条件；未分配空间不能仅按单卷解释 |
| ext4 | superblock、块组、inode、目录项、extent 与 journal | 查看 inode/extent、目录与日志；删除恢复依赖剩余元数据和未覆盖块 |
| F2FS | 面向闪存的 segment、checkpoint、NAT、SIT 与 node | 确认有效 checkpoint 和版本；垃圾回收、TRIM 和加密会降低恢复可见性 |

```bash
# 对已分离的 ext4 分区副本只读查看，不加 -w
debugfs -R 'stats' ./work/ext4-partition.img
debugfs -R 'ls -l /' ./work/ext4-partition.img
debugfs -R 'stat <1234>' ./work/ext4-partition.img
```

`1234` 仅为 inode 示例。文件系统 journal 反映事务，未必保存完整文件内容；APFS 快照和 ext4 日志也不是同一种历史机制。F2FS 的旧节点/段可以提供候选片段，但需要记录解析版本、地址和有效性判据。

## 08 SquashFS 与 UBI/UBIFS

先按文件头识别层次。小端 SquashFS 常见 `68 73 71 73`（hsqs）；用 unsquashfs 先列内容，再解到新目录。UBI 是擦除块/卷管理层，UBIFS 是卷内文件系统，不能把二者当成同一种裸格式。

```bash
unsquashfs -s ./work/rootfs.bin
unsquashfs -ll ./work/rootfs.bin
unsquashfs -d ./output/rootfs ./work/rootfs.bin
ubireader_display_info ./work/flash.bin
ubireader_extract_files -o ./output/ubi ./work/flash.bin
```

根据 UBIReader 的识别结果记录页/块尺寸、卷和偏移。遇到 NAND 的 OOB/ECC、坏块或截断镜像，先核对采集形态，再决定解析参数。导出后查配置、账户、服务、数据库和日志，保存提取件哈希与卷路径；不执行固件中的未知程序。

## 09 实战：验证分区提取是否正确

**场景与材料：** 获得一个整盘 RAW 镜像，需要提取其中的 Btrfs 分区并检查子卷。先记录分区工具输出、逻辑扇区大小、Start 与 Length，再按本页 `dd` 示例生成新的分区文件。

1. 假设实际输出经核对为起始扇区 `2048`、长度 `409600`、每扇区 `512` 字节，则镜像内起点为 `1048576` 字节，提取件应为 `209715200` 字节。这些数值只是演示，不能在未知镜像上直接套用。
2. 提取后用本页 `stat` 核对大小并计算哈希；尺寸不符时先查路径、空间、读取错误和参数，不能直接继续挂载。
3. 用 `btrfs restore -l` 检查文件系统及树根信息；若不识别，重新核对偏移、格式、加密/卷管理层和工具支持。
4. 对确需挂载的分析，使用已确认的只读映射并避免日志回放；子卷枚举必须指向目标挂载点，分别核对 top-level、默认子卷和快照视图。
5. 保存导出的子卷 ID、父子关系、可读目录和恢复错误，选取已有元数据能定位的文件进行格式与内容核对。

**结果判读：** 提取件大小正确只能说明长度符合设定；还需要文件系统结构和目录关系正确，才能支持偏移选择合理。看到 `history` 字符串不能证明存在可读取快照；缺失设备或块错误时，应分开记录“能列出的对象”和“能恢复的内容”。

**交付记录：** 整盘哈希、分区起始扇区与扇区大小、提取命令、分区哈希、FSID、子卷/快照标识和可读性。涉及多设备 Btrfs 或 RAID 时，另附成员清单与缺失范围，不把单分区流程作为通用重组方案。

## 10 VHD 文件尾与分配 run：先说明坐标系

**场景与材料：** NTFS 系统盘中发现一个 VHD 文件，需要定位它在外层介质中的末扇区并提取验证。先取得外层镜像、目标分区起点、实际逻辑扇区大小、簇大小、文件逻辑长度以及对应 `$DATA` 属性的 run 列表。WinHex 等工具显示的“偏移”可能是字节、分区相对扇区或整盘扇区，记录窗口与单位后再计算。

### 10.1 四种“结束位置”不能互换

| 位置 | 所属层次 | 正确理解 |
| --- | --- | --- |
| VHD 文件最后一个有效字节 | 文件逻辑坐标 | 非空文件为 `L - 1`，`L` 是文件长度 |
| 最后有效字节对应的外层扇区 | NTFS run 映射后的介质坐标 | 先定位逻辑簇，再按其 run 换算 LCN 和扇区 |
| 最后逻辑簇的分配末扇区 | 文件系统分配坐标 | 包含簇 slack，可能在有效内容末端之后 |
| VHD 内部的最后虚拟扇区 | 虚拟磁盘坐标 | 由 VHD 格式与虚拟容量决定，不能从宿主文件大小直接推导 |

VHD 可为固定、动态或差分形式。动态块、BAT、footer/元数据及父盘依赖属于**文件内部格式**；外层 NTFS 簇位置描述这个文件怎样存放，两者不是同一个地址空间。

### 10.2 用 run 映射计算，避免无条件“加 7”

设分区起始扇区为 `P`，每扇区 `S` 字节，每簇 `C` 字节，`k=C/S`。普通、非稀疏且未压缩的非驻留 `$DATA` run 已由解析器正确解码为 `(VCN起点, LCN起点, 簇数)` 时：

1. 文件最后逻辑簇为 `v = (L-1)//C`；选择包含 `v` 的 run，而非物理 LCN 最大的 run。
2. 对该 run，最后有效字节对应的 LCN 为 `LCN起点 + v - VCN起点`。
3. 该逻辑簇在整盘中的首扇区为 `P + LCN*k`。
4. 最后有效字节所在整盘扇区为 `P + LCN*k + ((L-1)%C)//S`。
5. **这个簇**的分配末扇区为 `P + LCN*k + k-1`。只有 `C=4096`、`S=512`，且已知位置确为该簇首扇区时，才适用“首扇区加 7”。

某一连续 run 的分配范围末扇区为 `P + (LCN起点+簇数)*k - 1`，减一表示末端也计入范围。该值描述 run 范围，不自动等于整个文件的最后逻辑字节或物理地址最大的全部范围。

```python
# 演示坐标换算；参数需从已核对的目标文件元数据取得。
partition_start_sector = 2048
sector_bytes, cluster_bytes = 512, 4096
logical_size = 9000
runs = [(0, 100, 2), (2, 300, 1)]  # 已解码的 VCN/LCN/length，非 raw runlist
if logical_size <= 0 or cluster_bytes % sector_bytes:
    raise ValueError('非空长度、扇区和簇参数不符合当前示例条件')
vcn = (logical_size - 1) // cluster_bytes
matches = [(v, l, n) for v, l, n in runs if v <= vcn < v + n]
if len(matches) != 1:
    raise ValueError('run 缺失或重叠；不能继续映射')
v, l, n = matches[0]
spc = cluster_bytes // sector_bytes
lcn = l + vcn - v
cluster_first = partition_start_sector + lcn * spc
logical_last = cluster_first + ((logical_size - 1) % cluster_bytes) // sector_bytes
allocated_last = cluster_first + spc - 1
print('last_logical_vcn=', vcn, 'last_lcn=', lcn)
print('whole_disk_last_valid_sector=', logical_last)
print('whole_disk_last_cluster_allocated_sector=', allocated_last)
print('partition_relative_allocated_sector=', allocated_last - partition_start_sector)
```

**示例输出判读：** 最后 VCN 为 `2`，映射 LCN 为 `300`；末有效字节所在整盘扇区为 `4449`，最后逻辑簇的分配末扇区为 `4455`。这两个值不同是正常的。示例文件碎片跨两个 run，不能用首 run 起点加文件总长度代替映射。

### 10.3 提取与交叉核验

用支持 NTFS 的解析器按文件属性导出逻辑 VHD，再核对导出长度等于 `L`、文件哈希和 VHD 结构。另一方面保存 run 列表、原始 MFT/属性记录、VCN/LCN 单位和相关扇区片段，复算有效字节位置与分配范围。工具显示的整盘末扇区减去分区起始扇区，应与分区相对值一致；不要重复加分区偏移。

稀疏 run、压缩单元、驻留属性、多属性扩展、截断/损坏 run、逻辑材料缺少未分配空间时，本节普通映射有明确限制；不能把稀疏空洞解释为实际分配 LCN。取证软件若只给“文件尾偏移”，先确认显示单位与是否包含 slack，之后再报告结论。最后用虚拟盘解析器检查内部容量与父盘链，不能仅靠末尾看到签名就认定已取得完整可用虚拟磁盘。

## 11 BitLocker 的标识、状态与解锁材料

**场景：** 某数据卷出现 `System Volume Information\FVE2.{...}` 等文件，并在图像或文档中发现一串候选口令。此类路径是筛查线索，**不能仅凭一个 FVE 命名文件断言卷当前已完整加密或仍启用保护**。继续检查卷的 FVE 元数据、保护器类型、转换/加密状态及采集环境；历史残留和保护暂停都需要区分。

| 材料 | 含义 | 取值与使用边界 |
| --- | --- | --- |
| 用户密码 | 配置的口令保护器输入 | 长度与字符按实际密码处理，不能从恢复材料反推出它 |
| 48 位恢复密码 | 通常显示为 8 组、每组 6 位数字 | 常被界面称为恢复密钥；应记录其实际类型并匹配保护器/卷标识 |
| 外部恢复密钥 | 通常为与保护器关联的 `.bek` 文件 | 文件型材料，与 48 位恢复密码不同 |
| 卷密钥及相关解密材料 | 由保护器解封或从其他可用状态取得 | 不等于用户口令；适用性依赖卷、算法与元数据 |

**具体操作顺序：** 固定卷/镜像与候选材料 → 核对材料类型及对应卷 → 在具备只读保障的工作副本中验证解锁 → 记录工具、保护器、结果和可见范围 → 导出文件并核对文件系统与内容。若只有候选字符串，报告候选；若能解锁并稳定解析结构，报告该材料可用于该工作副本，不公布秘密值，也不称它为用户原始密码。

来自图片隐写、邮件附件或文末文字的口令应保留载体哈希、提取方式和输出映射。解锁后的“最后修改文件”要明确比较范围：哪个卷、哪些目录、哪个时间字段、是否包含删除项、并列时间如何处理。排序结果是文件系统字段的相对顺序，不自动等于用户最后实际编辑行为。

解密链和工具条件统一见[加密数据与凭据](/knowledge/forensic-protected-data/)。本页负责介质结构、卷状态和坐标判断，避免将解锁材料与虚拟盘分配范围混成同一个步骤。
