---
title: 综合取证与面板辅助工具
summary: 按证据对象选择 PanelForensics、ForensicsTool、综合分析与口令恢复工具，并逐项核验输出。
module: Forensics
topic: 工具与路径
locationPaths: ['D:\CTF_MISC_Tools\Forensics\PanelForensics', 'D:\CTF_MISC_Tools\Forensics\ForensicsTool.exe', 'D:\CTF_MISC_Tools\Forensics\Magnet AXIOM', 'D:\CTF_MISC_Tools\Forensics\Inseyets PA', 'D:\CTF_MISC_Tools\Forensics\弘连取证', 'D:\CTF_MISC_Tools\压缩包\Passware Kit Forensic(Eusrc)', 'D:\CTF_MISC_Tools\Forensics\火眼哈希值计算工具']
sourceIds: [web-forensics-wiki-toolbox, web-forensics-wiki-paneltools, web-forensics-wiki-passware, web-goodlunatic-761da51]
updated: 2026-10-01
---

## 1. 先按对象选工具

| 对象 | 工具方向 | 输出复核 |
| --- | --- | --- |
| Windows/Linux 镜像与应用 | AXIOM、火眼、X-Ways、Autopsy 等 | 文件系统、账户、痕迹与对应位置 |
| 手机和备份 | Inseyets PA、Oxygen、相关移动取证平台 | 采集方式、解锁条件、应用版本、数据库/附件 |
| 仿真 | 火眼仿真、虚拟机工具 | 副本/快照、写入变化与环境差异 |
| 面板数据 | PanelForensics、ForensicsTool | 与数据库表、配置和版本相互核对 |
| 加密容器、压缩包与口令 | Passware、对应格式恢复器 | 密钥/口令条件与成功打开的真实数据 |
| 哈希校验 | 系统哈希命令、HashMyFiles、火眼哈希工具 | 算法、对象范围、大小和稳定材料 |

美亚、弘连、盘古石、龙信、平航等产品的支持范围与授权不同，不能仅按品牌推定所有采集或解析能力。工具目录只说明可定位，首次使用还需核对版本、依赖、授权和输入支持。

## 2. PanelForensics

面板辅助解析可覆盖特定宝塔、1Panel、小皮样本。将面板目录或所需配置/数据库副本按工具要求导入，先确认产品和版本，再解析网站、数据库账户、FTP、任务等。

工具曾对有限服务器样本测试，未知版本、加密字段或迁移目录可能不兼容。保留工具日志和未识别字段，回到 [服务器面板与账户证据](/knowledge/forensic-server-panel/) 的路径和 schema 逐项核验。

## 3. ForensicsTool

图形工具可汇集配置/账户解析、时间/编码和常见取证辅助功能。先确认所用功能需要的材料，而非将整个检材随意拖入：输入文件类型 → 支持版本 → 必需字段/密钥 → 输出路径 → 实际解析结果。

密码恢复、时间转换和格式识别分别核对前提。导出的账户、时间或关键词命中应保留对应输入记录和算法；工具提示“成功”后仍检查实际结果，报错、空值和默认值不能视为正常答案。

## 4. Passware Kit Forensic

加密卷选择对应磁盘/容器任务，压缩包选择对应文件类型；有内存镜像时使用相应内存分析或磁盘解密功能。确定容器格式、加密方案、口令/PIM/keyfile 条件，再设置候选字典/规则/掩码、资源与停止条件。

VeraCrypt 案例可能同时需要口令与密钥文件；BitLocker 可能使用恢复口令或可用内存密钥。不能将所有磁盘解密都称为“爆破”。口令候选命中后必须验证整个卷的文件系统和已知内容。

压缩包示例可先确认格式和加密内容，按已知线索缩小搜索。保存任务状态和攻击范围；没有找到口令只能说明该搜索范围未命中，不等于口令不存在。输出解密镜像写新路径并计算哈希，原件保留。

## 5. 工具组合与报告

用一个工具定位、另一个方法核对关键结构或字段。两工具都依赖同一解析库时，不应将相同输出当成独立证据。记录工具版本、配置、成功/失败项、偏移/表/主键与数据覆盖。

核心入口：[镜像工具](/tool/forensic-disk-tools/) · [内存工具](/tool/forensic-volatility/) · [注册表/事件](/tool/forensic-registry-tools/) · [浏览器](/tool/forensic-browser-tools/) · [加密数据](/knowledge/forensic-protected-data/)。

## 6. 常见辅助工具的角色

| 任务 | 工具名称 | 选择条件 |
| --- | --- | --- |
| 镜像挂载、转换 | Arsenal Image Mounter、OSFMount、CSI Mounter、GHO2VMDK、QEMU | 支持输入格式、只读策略、驱动与快照链；GHO 转换不是普通 raw 转换 |
| 案件式解析 | EnCase、Autopsy/Sleuth Kit、Magnet AXIOM | 支持的文件系统、解析模块、报告记录与授权 |
| 内存图形入口 | Volatility Workbench、LovelyMem | 查看实际调用的 Volatility/MemProcFS 版本、Profile/符号和错误日志 |
| 配置与文件系统 | Plist Editor、Linux Reader、Linux File Systems for Windows、LVM/mdadm | 二进制/文本 plist、分区与卷布局；可写驱动不等于只读取证挂载 |
| 权限与 USB 观察 | Removable Access Tool、usbblock、USB 痕迹解析器 | 软件策略与硬件写保护分别验证，且不证明过去从未写入 |
| 静态、动态与调试 | IDA、OllyDbg/OllyICE、EDB、WinDbg、反编译/脱壳工具、C32Asm | 平台、架构、调试权限与受控运行条件 |
| 进程与启动观察 | Process Monitor、Process Explorer、火绒剑、Autoruns、Dependency Walker | 运行态、持久化入口和依赖是不同视角，离线数据支持范围另查 |
| 二进制编辑与辅助分析 | Hex Workshop、程序结构/加壳识别工具 | 优先只读查看；修改后保存工作副本及字节差异 |
| 统计与日志 | AWStats 等日志分析器 | 日志字段、时间范围和统计口径，计数不直接代表攻击次数 |

这里按任务登记工具角色，不把版本压缩包名当作独立知识分类。非本机工具需另行确认可用安装、版本与许可；不能因名称出现在列表就声称已测试。对于未知程序、修复工具和自解压包，先检查用途与来源，不在检材环境运行。
