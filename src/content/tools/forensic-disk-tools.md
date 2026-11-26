---
title: 镜像采集、挂载与文件恢复工具
summary: 区分采集、文件系统解析、仿真和恢复，使用 FTK Imager、Autopsy、DiskGenius 与 libewf。
module: Forensics
topic: 镜像与文件系统
locationPaths: ['D:\CTF_MISC_Tools\Forensics\FTK Imager', 'D:\CTF_MISC_Tools\Forensics\Autopsy', 'D:\CTF_MISC_Tools\Forensics\DiskGenius', 'D:\CTF_MISC_Tools\Forensics\DumpIt', 'D:\CTF_MISC_Tools\Forensics\qemu-img-win']
sourceIds: [web-goodlunatic-761da51, web-hello-memory, web-forensics-wiki-image]
updated: 2026-10-01
---

## 1. 工具对应的任务

| 工具 | 任务 | 关键操作 |
| --- | --- | --- |
| FTK Imager | 磁盘/逻辑材料采集、查看、导出和挂载 | 添加 Evidence Item 或创建镜像，选择对象、格式、校验和目标位置 |
| Autopsy / Sleuth Kit | 案件式镜像分析、文件系统与用户痕迹 | 新建案件、添加数据源、选择 ingest、查看失败项并导出 |
| DiskGenius | 识别分区、虚拟磁盘与恢复候选文件 | 打开镜像/虚拟磁盘，恢复输出另存；避免直接修复分区 |
| R-Studio / UFS Explorer | 镜像扫描、RAID 参数重组与恢复 | 在副本中识别布局，导出候选后验证 |
| libewf | E01 元信息、校验、挂载与导出 | 多段保持同目录和原命名，从首段进入 |
| qemu-img | 虚拟磁盘格式、快照链与转换 | `info` 只读查看，`convert` 写新文件 |
| DumpIt、WinPmem、Magnet RAM Capture、Belkasoft RAM Capturer | 活体内存采集 | 记录权限、系统支持、变更、大小与哈希 |

Volatility、Rekall 和 MemProcFS 主要用于分析；不能把它们统一列作“内存采集命令”。工具目录存在不代表依赖满足或已运行。

## 2. FTK Imager 的可复查流程

1. 记录待采集介质标识和状态，磁盘离线采集优先使用经核对的写保护条件。
2. 选择整盘、分区或逻辑文件范围，明确未分配空间是否包含。
3. 设置案件信息、镜像格式、分段、压缩和独立输出路径；记录坏扇区/读失败。
4. 完成后运行校验，保存采集报告与校验结果。活体数据变化可能导致前后状态差异，不能仅凭校验按钮认为采集覆盖全部数据。
5. 查看时添加镜像的首段，保留全套分段。AD1 是逻辑证据，未包含的数据不能通过“挂载”自动补回。

## 3. libewf 与虚拟盘

```bash
ewfinfo ./evidence/disk.E01 > ./output/ewf-info.txt
ewfverify ./evidence/disk.E01 > ./output/ewf-verify.txt
mkdir -p ./mnt/ewf
ewfmount ./evidence/disk.E01 ./mnt/ewf
mmls ./mnt/ewf/ewf1
qemu-img info --backing-chain ./evidence/disk.vmdk
qemu-img convert -f raw -O vmdk ./work/disk.raw ./output/disk.vmdk
```

先创建输出目录。EWF 文件内可保存描述、采集时间、介质信息和校验值；这些字段是记录信息，需要与实际材料交叉核对。只读挂载和格式转换不改变“加密卷仍需密钥”的事实。

## 4. Autopsy、恢复与格式检验

Autopsy 先建立案件与数据源标识，再选需要的模块。逐项查文件系统、用户目录、注册表、浏览器、时间线和删除文件；解析失败与不支持的格式单独记录。恢复结果按逻辑路径导出，保存文件 ID、偏移与哈希。

雕刻可找格式签名，通常不能恢复完整目录和准确文件时间。扩展名、预览图和成功导出都不足以保证文件完整，应使用格式解析器、结构字段、应用样本和关联证据验证。文件系统细节见 [镜像与文件系统识别](/knowledge/disk-evidence/)；仿真条件见 [虚拟机证据定位](/knowledge/forensic-cloud-vm/)。
