---
title: "文件系统取证：卷、分区和损坏的引导扇区"
summary: "从镜像分层到引导扇区识别、损坏后的反向定位，以及导出前的十项核验。"
module: Forensics
track: 计算机取证
topic: 卷与引导扇区
tags: [文件系统]
status: 已整理
sourceIds: []
relatedIds: ["forensic-fs-ntfs", "forensic-fs-fat", "forensic-fs-exfat", "forensic-fs-ext", "forensic-fs-other", "forensic-fs-gui", "disk-evidence", "forensic-file-recovery"]
updated: "2026-10-15"
---

拿到镜像后先分清容器、分区、卷、元数据和文件内容。文件系统各页分别处理 NTFS、FAT、exFAT、ext 以及其他格式；菜单操作集中在图形工具页。下面的扇区号 `2048` 只是占位，必须换成 `mmls` 对这份镜像的实际输出。原始镜像只读，导出写到 `./work/`。要改引导扇区或分区表时，只改工作副本。

## 01 先分开五层

| 层 | 要拿到的数 | 单位 |
| --- | --- | --- |
| 镜像容器 | RAW、E01、VMDK、VHD 的字节流从哪开始 | 字节 |
| 分区表 | 每个分区的起点和长度 | `mmls` 标的是扇区 |
| 卷 | 簇大小、根目录、文件表在卷内的位置 | 相对卷起点 |
| 文件元数据 | 名字、时间、起始簇或 run、逻辑长度 | 记录号、目录项、inode、工具虚拟地址 |
| 文件内容 | 按文件内部顺序拼出的字节，到逻辑长度为止 | 字节 |

```bash
sha256sum disk.dd
file disk.dd
xxd -l 512 disk.dd
mmls disk.dd
```

`mmls` 表头里的 Sector Size 是后面换算的依据，常见 512，也可能是 4096。分区在整盘镜像中的字节起点等于起始扇区乘以每扇区字节数。Sleuth Kit 的 `-o` 填扇区。`mount` 和 `losetup` 的 `offset`、`sizelimit` 填字节。单分区镜像的文件系统从文件头开始，`-o` 用 0，不要再套整盘的 2048。

E01 先挂成只读字节流，再分析里面的节点：

```bash
mkdir -p /mnt/ewf ./work
ewfinfo disk.E01
ewfmount disk.E01 /mnt/ewf
mmls /mnt/ewf/ewf1
```

要分析的是 `/mnt/ewf/ewf1`。没有可信分区时，它可能本来就是单分区，或者中间还有虚拟磁盘、LVM、RAID、BitLocker。加密卷在解锁前没有明文签名。

```bash
sec=512
start=2048
length=409600
sudo losetup --find --show --read-only \
  --offset $((start * sec)) --sizelimit $((length * sec)) disk.dd
```

拆掉的只能是这次新建的 loop。

## 02 用引导扇区认出文件系统

魔数只有出现在规定位置，才进入下一步。文件内容和旧分区残留里也会有同样的字节。命中后还要核对簇大小、总扇区和分区长度是否装得下这块卷。

| 看到的字节 | 位置（相对卷起点） | 当前结构 |
| --- | --- | --- |
| `NTFS    ` | 引导扇区偏移 3 | NTFS |
| `FAT32   ` | 引导扇区偏移 `0x52` | FAT32 |
| `FAT16   ` 或 `FAT12   ` | 引导扇区偏移 `0x36` | FAT16 或 FAT12 |
| `EXFAT   ` | 引导扇区偏移 3 | exFAT |
| `53 EF` | 字节 1080 | ext2/3/4。超级块在 1024，魔数在超级块内偏移 `0x38` |
| `_BHRfS_M` | `0x10040` | Btrfs |
| `XFSB` | 卷起点 | XFS |
| `NXSB` | 容器第 0 块 | APFS |
| `EFI PART` | 整盘 LBA 1 | GPT 分区表，还不是文件系统 |

GPT 的 LBA 0 是保护性 MBR，分区类型 `0xEE`。分区项一般从 LBA 2 开始，每项 128 字节，起始 LBA 在项内偏移 32，小端 8 字节。MBR 分区项从 `0x1BE` 开始，每项 16 字节：偏移 4 是类型，偏移 8 是起始 LBA，偏移 12 是扇区数。类型 `0x07` 既可能是 NTFS 也可能是 exFAT，必须再读引导扇区里的 OEM 名。分区之间留出约 2048 个 512 字节扇区，通常只是 1MiB 对齐，单独出现不算隐藏分区。

FAT12/16 的类型串只在扩展引导签名为 `0x29` 时才可靠。字符串对不上时，用根目录项数和簇数量继续判断。

```bash
start=2048
fsstat -o "$start" disk.dd
fls -r -p -o "$start" disk.dd > ./work/files.txt
fls -r -d -p -o "$start" disk.dd > ./work/deleted.txt
```

`fsstat` 给出类型、簇大小和关键结构位置。它说不支持，只说明这个工具不认这种格式，换对应文件系统那一页的读法，不要写成镜像损坏。

| 现象 | 先查 |
| --- | --- |
| `mmls` 没有可信分区 | 是不是单分区、虚拟磁盘，或引导扇区已被抹掉 |
| 文件系统识别失败 | 扇区大小、起始扇区、LVM、RAID、加密 |
| 目录为空或内容错位 | `-o` 是否填了扇区，是否选错分区 |
| 挂载程序要求修复或回放日志 | 停止挂载，改用 `fls`、`icat` 或 `debugfs` |

## 03 引导扇区被抹掉时反向定位

分区第 0 扇区的 512 字节若被写成全 `00` 或全 `FF`，系统会提示需要格式化，`fsstat` 和图形工具的默认识别也会失败。从分区表拿起点，再在本分区内部找还活着的分配表。搜索停在本分区的结束扇区。

```bash
python3 - << 'PY'
from pathlib import Path
img = Path('disk.dd').read_bytes()
sec = 512
part_start, part_len = 2048, 409600
base = part_start * sec
blob = img[base:(part_start + part_len) * sec]
sig = bytes.fromhex('F8FFFF0F')
hits = []
i = 0
while True:
    j = blob.find(sig, i)
    if j < 0:
        break
    if j % sec == 0:
        hits.append(part_start + j // sec)
    i = j + 1
print('\n'.join(map(str, hits)))
PY
```

FAT32 的表头是小端 `0x0FFFFFF8`，磁盘上就是 `F8 FF FF 0F`，后面常跟着 `FF FF FF 0F` 或 `FF FF FF FF`。只保留扇区对齐、并且后面一大段也像分配表的命中。本分区里互不重叠的命中有几处，就是几张 FAT。常见是两张：第 1 处是 FAT1，第 2 处是 FAT2。两处开头若干扇区应一致。

```text
保留扇区数 = FAT1 的整盘扇区号 - 本分区起始扇区号
每份 FAT 扇区数 = FAT2 的整盘扇区号 - FAT1 的整盘扇区号
数据区起始扇区（相对本分区，簇 2 从这里开始）
    = 保留扇区数 + FAT 份数 × 每份 FAT 扇区数
```

计算分区内部结构时使用相对本分区的**保留扇区数**；定位整盘介质偏移时则使用 **FAT1 的整盘绝对扇区号**，两者恰好相差一个本分区起始扇区号。每簇扇区数可按 `1、2、4、8、16` 依次代入验证：按正确簇大小从数据区读出的文件，其文件头魔数应当准确落在簇的起始边界上。

FAT32 备份引导扇区常见在本分区第 6 扇区，但字段 `0x32` 已经被抹掉，不能再从它读取。到工作副本的分区内第 6 扇区看有没有 `FAT32   `。有，才把这 512 字节抄回副本的分区第 0 扇区，再重新 `fsstat`。这一抄写只做在副本上。

NTFS 把特征换成 `46 49 4C 45`。下一条记录的距离常见是 1024；若加 1024 不是 `FILE`，再试 4096。两条都对不上的字符串是文件内容，丢掉。

用连续条数区分两份表。`$MFTMirr` 通常只存放记录 0 到 3，后面不再以记录大小为步长接着出现 `FILE`。主 `$MFT` 是成千上万条记录连在一起。Windows 常见布局是主表在卷前部、镜像在卷中部。前部第一处若已经是长串，它就是主 `$MFT`；只有前部仅仅四条、长串出现在更靠后的位置时，前部那处才是镜像。镜像里的记录 0 是主表记录 0 的副本，它的无名 `$DATA` runlist 指向主 `$MFT` 的簇。fixup 改的是每个 512 字节扇区的最后 2 字节，开头 32 字节不受影响，可以用这 32 字节到卷后部再搜一次。

```text
主 $MFT 相对本分区的扇区号 = 主 $MFT 的整盘扇区号 - 本分区起始扇区号
主 $MFT 的起始 LCN = 相对扇区号 / 每簇扇区数
```

除法必须整除。每簇字节数等于记录 0 里 `$DATA` 的分配字节数除以 runlist 总簇数；再除以每扇区字节数得到每簇扇区数。两个除法都要整除。算出来的 LCN 乘每簇字节数，应回到主 `$MFT` 相对卷起点的字节偏移。字段怎么解，按 NTFS 那一页的记录头和 runlist 做。

## 04 未分配空间和簇尾

目录项、MFT、inode 或 exFAT 的流扩展项还能指出簇时，先走对应文件系统那一页。那条路保留名字、路径、时间和逻辑长度。雕刻只看文件头，不知道原名，也不知道文件是否曾经碎片化。

```bash
blkls -o "$start" disk.dd > ./work/unalloc.bin
blkls -o "$start" -s disk.dd > ./work/slack.bin
foremost -i ./work/unalloc.bin -o ./work/carve
```

`blkls` 默认输出未分配数据单元。`-s` 输出各文件最后一个簇里、逻辑长度之后的 slack。`foremost` 的 `-o` 目录必须是新的。NTFS 常驻文件在 `$MFT` 记录里，不在 `unalloc.bin` 中。

每个雕刻命中单独记录偏移、规则和哈希。它和 `icat` 导出的已删除文件哈希不同，就保留成两个候选。PNG 要查每块 CRC 和最后的 `IEND`，JPEG 以 `FF D8` 开始、以 `FF D9` 结束，ZIP 要有中央目录，SQLite 要查页结构。签名正确只说明开头像这个格式。TRIM 会让已释放簇变成全 0；没有雕刻到，不能写成这个文件从未存在。更完整的目录项与雕刻对照见[删除文件、文件雕刻与格式校验](/knowledge/forensic-file-recovery/)。

## 05 实战：一份镜像的处理顺序

1. 计算哈希，看 `file` 和前 512 字节，再跑 `mmls`。记下扇区大小、Start 和 Length。
2. 引导扇区正常时对每个分区 `fsstat`。第 0 扇区是全 `00` 或全 `FF` 时，先做第 03 节。
3. `fls -r -p` 看现存名字，`fls -r -d` 看已删除名字。NTFS 地址是“记录号-属性类型-属性 ID”。FAT 和 exFAT 的行首号码是虚拟地址。ext 的号码是 inode。
4. `istat` 看在用状态、时间和分配。`icat` 或按偏移 `dd` 导出到 `./work/`。长度等于逻辑大小，再查文件头、文件尾和哈希。
5. 仍然没有位置信息，才做第 04 节。雕刻结果与元数据导出分开记录。
6. 时间统一标时区。NTFS 的 FILETIME 是 UTC。FAT 的位域是本地时间。ext 的秒是 UTC。exFAT 先看时区字节的最高位。

挂载只用于浏览已经确认的工作副本。NTFS 若提示修复或回放日志，停下来，继续用 `fls` 和 `icat`。ext4 使用 `ro,noload`。

## 06 导出前的十项核验

1. `mmls` 的 Start 是扇区。`mount` 和 `losetup` 的 offset 是字节。扇区大小是 4096 时不能沿用 512。
2. 整盘镜像要加分区起点。单分区镜像从 0 开始。
3. FAT 和 exFAT 的 2 号簇才是数据区第一簇。NTFS 的 LCN 0 是卷的第一簇。
4. NTFS 引导扇区偏移 `0x40`、`0x44` 是有符号单字节。`0xF6` 表示 1024 字节。`0x01` 乘的是簇大小。`$MFT` 碎片化以后，不能用第一段物理起点一直线性加。
5. 无名 `$DATA` 之外还有备用流。Win32 长名和 DOS 短名仍然是同一个文件。
6. 笔记里的“记录号-序列号”不能直接交给 `istat`。Sleuth Kit 的第二段是属性类型，`128` 表示 `$DATA`。
7. 簇尾 slack 不能拼进文件。导出长度用逻辑大小核验。
8. FAT 链已经被清成 0 时，连续读取会把碎片文件的后半段接错。JPEG、PNG 和 ZIP 都要看到结束结构。
9. NTFS 的 UTC 不能直接当成 FAT 的本地时间。exFAT 时区字节的最高位没有置上时，不要自行减 8 小时。
10. 文件头正确还要查 CRC、中央目录或页结构，并确认记录槽、目录项或 inode 没有被后来的文件占用。
