拿到无法按 NTFS、FAT/exFAT 或 ext 解析的分区或镜像时，不要强行套用 MFT、FAT 目录项或 ext inode 模板。应先通过特征位置的魔数识别它属于现代写时复制文件系统（Btrfs、APFS）、高性能日志文件系统（XFS）、固件只读文件系统（SquashFS、UBI/UBIFS），还是下层的逻辑卷/阵列容器（LVM、RAID），再挂载或导出对应的只读视图。分区起点与扇区单位换算见[卷与引导扇区](/knowledge/forensic-fs-volume/)；原始镜像保持只读。

## 01 Btrfs 和 XFS

Btrfs 的超级块在卷内 `0x10000`，魔数 `_BHRfS_M` 在超级块内偏移 `0x40`，也就是 `0x10040`。`history` 这类名字可能是子卷或快照，不一定是普通目录。只读挂载时同时加上 `ro` 和 `nologreplay`，并先看子卷号 5 的顶层树。

```bash
xxd -s 0x10040 -l 8 ./work/partition.img
btrfs restore -l ./work/partition.img
```

`btrfs restore -l` 可以在不挂载时列出树根。多块成员盘先对文件系统 ID。缺一块时，列得出来的名字不等于每个文件都能读出。不要在唯一检材上做修复。

XFS 的卷首是 `XFSB`。空间按分配组管理，inode 在 B+ 树里。删除恢复看剩余 inode 和日志，没有 FAT 链，也没有主文件表。`xfs_db` 只对工作副本使用只读参数；它若要求写日志，就停下来改用只读枚举。

## 02 APFS、HFS+ 和 SquashFS

APFS 容器第 0 块是 `NXSB`。先分清容器、卷和快照。FileVault 没解开时，后面的目录不在明文里。未分配空间按整个容器理解，不要按单个卷的大小去切。密钥来自其他检材；没有密钥时，只记录容器标识和加密状态。

HFS+ 在卷偏移 1024 处的签名是 `H+` 或 `HX`。目录是目录 B 树。时间从 1904 年 1 月 1 日算起，和 Unix 秒、FILETIME 都不同。先把时间起点换对，再和日志比较。

SquashFS 的小端魔数是 `hsqs`，大端是 `sqsh`。它是只读根文件系统，常见于固件。

```bash
unsquashfs -ll ./work/rootfs.bin
unsquashfs -d ./work/rootfs ./work/rootfs.bin
sha256sum ./work/rootfs.bin
```

先列清单，再解到新目录。解出来的文件逐个核验哈希。不要执行固件里的程序。UBI 是擦除块管理层，UBIFS 是里面的文件系统，两者不要当成同一种裸格式。

## 03 实战：先读 LVM 和 RAID 的元数据

LVM 的物理卷前部有 `LABELONE`。顺序是物理卷、卷组、逻辑卷，文件系统在逻辑卷里面。只在某个物理卷中间看到 `53 EF` 或 `NTFS    `，还不能挂载。DiskGenius 加载镜像后，左侧会出现卷组和逻辑卷；命令行则先读 LVM 元数据，得到逻辑卷的段映射，再对映射出来的只读设备做 `fsstat`。

RAID 成员盘中部的文件系统签名不能当成已经组好的卷。Linux mdadm 的 1.2 超级块在成员偏移 `0x1000`，魔数是小端 `0xA92B4EFC`，磁盘上为 `FC 4E 2B A9`。这里能读到级别、成员序号、块大小和布局。0.9 和 1.0 的超级块靠近成员尾部，`0x1000` 没有魔数时再查尾部。

```bash
xxd -s 0x1000 -l 16 ./work/member-a.img
sudo losetup --find --show --read-only ./work/member-a.img
sudo mdadm --examine /dev/loop0
```

`--examine` 只读。不要对检材执行会创建阵列的命令。盘序、条带和校验方向的图形重组在[文件系统图形工具](/knowledge/forensic-fs-gui/)。重组结果要能列出分区，并且一个跨过两个条带的大文件能通过格式核验，才算参数对了。只看到几个小文件，说明盘序或校验方向仍可能是错的。阵列参数的手工重组细节见[RAID 重组取证](/knowledge/forensic-raid-reconstruction/)。
