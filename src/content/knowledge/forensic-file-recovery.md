---
title: 删除文件、文件雕刻与格式校验
summary: 结合文件系统元数据与文件特征恢复内容，并判定恢复结果的完整性。
module: Forensics
track: 文件与多媒体取证
topic: 文件恢复与格式
tags: []
status: 已整理
sourceIds: [web-forensics-wiki, web-goodlunatic-761da51, web-hello-memory]
updated: "2026-10-01"
---

拿到需要恢复删除文件或校验残损文件的磁盘镜像时，先确定分区偏移、文件系统类型与簇大小。**优先查回收站、目录项、主文件表（MFT）、inode 和文件系统日志**——有元数据时能一并恢复文件名、原路径、时间戳与逻辑长度；只有元数据已被清空或覆盖时，才对未分配空间（Unallocated Space）按文件头尾魔数进行雕刻（Carving）。原始镜像保持只读，所有提取与修复输出均写入独立工作目录。

## 01 从分区目录项导出已删除文件（优先于雕刻）

先用 `mmls` 获取目标分区的起始**扇区号**（`Start` 列，注意不是字节偏移），再用 `fls -r -d -p` 枚举已删除目录项，复制完整元数据地址交给 `icat` 提取文件内容（外层镜像识别见[取证镜像与文件系统识别](/knowledge/disk-evidence/)，NTFS/FAT/exFAT/ext 底层字节布局见对应文件系统专页）：

```bash
mmls disk.dd
start_sector=2048   # 替换为 mmls 输出的实际起始扇区
fls -r -d -p -o "$start_sector" disk.dd
metadata_addr=12345 # 替换为 fls 显示的完整元数据地址
icat -o "$start_sector" disk.dd "$metadata_addr" > recovered.bin
file recovered.bin
sha256sum recovered.bin
```

若 `fls` 显示的元数据地址带有属性与流后缀（如 NTFS 的 `49-128-2`），应完整复制该值。导出后必须用格式解析器校验内部结构：
- **ZIP / OOXML 文档**：核对末尾中央目录（EOCD）与各成员 CRC，不能只看开头有 `PK`（`50 4B 03 04`）就认定完整。
- **PNG / JPEG 图像**：PNG 核对块边界、CRC 与末尾 `IEND`；JPEG 核对开头 `FF D8` 与结尾 `FF D9`。
- **SQLite 数据库**：检查页大小、B-tree 页结构与伴随的 `-wal` 日志。
- **元数据槽复用排查**：MFT 记录号或 inode 号在文件删除后可能被新文件复用，不能单凭 `icat` 成功导出字节就认定它一定是删除前的历史目标文件。

## 02 ext3/ext4 与 FAT 删除恢复的边界

针对 ext3/ext4 分区副本，除使用 `debugfs` 的 `ls -d` 与 `logdump` 排查日志残留外，也可在独立输出目录中运行 `extundelete`（输入必须是文件系统从偏移 0 开始的分区镜像，而非带分区表的整盘镜像）：

```bash
mkdir -p ./output/ext-recovery
cd ./output/ext-recovery
extundelete ../../work/ext4-partition.img --restore-all
```

保存标准错误输出与恢复文件清单，逐一校验恢复文件的大小、文件头与 SHA-256（详细 extent 树与日志块手工提取见[ext 取证](/knowledge/forensic-fs-ext/)）。

针对 FAT16/FAT32 分区，删除操作会将短目录项首字节改为 `0xE5` 并将 FAT 表中的簇链清零。若文件原本连续存放，可按目录项残留的起始簇号与文件大小连续导出；若文件原本存在碎片，连续读取会把其他文件的簇拼入后半段，必须通过文件尾部结构与内部校验确认完整性（详见[FAT 取证](/knowledge/forensic-fs-fat/)）。

此外，SSD/闪存介质上的 TRIM、垃圾回收（GC）和全盘/文件级加密会导致已释放数据块清零或不可读；未恢复出文件不等于该文件历史上从未存在。移动端数据库删除残留的恢复见[手机应用、通信与定位证据](/knowledge/forensic-mobile-apps/)。

## 03 实战：区分目录项提取件与未分配空间雕刻件

**场景与材料：** 在同一份磁盘镜像中，既通过 `fls` 发现了一条已删除目录项，又在未分配空间中用 `foremost` 雕刻出了一个同类型的候选文件。目标是判断两者是否指向同一份内容，并分别评价其完整性。

1. **保存两条独立恢复链：** 目录项提取件记录 `分区偏移 → 原路径 → 完整元数据地址 → icat 输出哈希`；未分配空间雕刻件记录 `物理扇区区间 → 雕刻规则 → 输出哈希`。在没有元数据印证前，不要把删除目录项的文件名硬套给雕刻件。
2. **比对大小、结构与内容哈希：** 若两份输出 SHA-256 不同，作为两个独立候选保留，不能因为图片缩略图相似就合并。
3. **逐层核验格式与外部验证：** 对照 ZIP 成员 CRC、PNG 块边界或 SQLite 页结构进行格式验证，再与系统快照、缩略图缓存、聊天附件记录或日志哈希交叉复核。

**示例判读：** 若目录项提取件字节长度与记录相符但后半段簇已被新文件覆盖，而雕刻件画面可预览却缺失尾部结构，两者均应报告为**部分恢复（Partial Recovery）**，不能用雕刻件的可预览性充当目录项提取件完整的证明。
