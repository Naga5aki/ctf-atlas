# RAID 重组独立知识点核对记录

核对日期：2026-10-02。本文件只供维护，不生成网站正文。

## 1. 用户范围与归档

新增一个独立知识点 `forensic-raid-reconstruction`，标题为“RAID 重组取证：参数分析、重建与验证”，归入 **Forensics → 计算机取证 → 磁盘与文件系统**，内部 topic 沿用“镜像与文件系统”。该页面有独立列表入口、URL、目录和搜索结果。没有新增主模块、题型或标签。

文字要求沿用“规划 CTF 知识库网站”聊天中经用户确认的独立实用教程写法：不出现具体题目、比赛名称、题号、真实人名和固定答案；保留适用场景、材料、证据位置、操作、结果判读、验证和限制。详细正文统一维护于 `src/content-curation/forensic-raid-reconstruction.md`，通过已有补充注册表生成网站页面。计算机指南和镜像页面各新增一个导航段落，原有正文与代码继续保留。

## 2. 三篇指定资料的覆盖

| 指定资料 | 阅读范围 | 提炼落点 |
| --- | --- | --- |
| [小谢取证：历年美亚杯RAID重组解析汇总](https://blog.csdn.net/m0_37867238/article/details/143604850) | 公开文字；图片只按文字说明定位，没有把全部截图逐项 OCR | RAID 级别与名词、成员识别、UFS / R-Studio / 取证大师自动重组、FTK 与仿真、静态文件分析；归入 §01–05、§10–12 |
| [Xiaohao：RAID重组取证各类工具实操方法](https://blog.enxiaohao.cn/posts/Forensics/RAIDReconstruction/) | 公开文字、工具流程说明；未运行所示软件或附件 | 完整参数表、工具配置/导出、X-Ways 名称、虚拟机磁盘与启动关系；归入 §03、§05、§10 |
| [0xL4k1d：Raid重组复习](https://www.cnblogs.com/0xl4k1d/p/15449572.html) | 公开文字与排列示例；实际查看一张 NTFS 记录编号配图，没有全部配图 OCR | XOR 原理、四种布局、NTFS 启动结构、记录差值与块大小、周期及首盘约束、跨条带验证；归入 §06–09 |

三篇资料是整理范围和流程线索，不将其经验性结论直接当作通用保证。博客中具体检材的盘序、容量、循环方式及比赛结果没有进入正文；正文数值、记录编号和失败场景为独立构造示例。没有下载或执行博客提供的工具包、未公开附件及原题检材。

## 3. 官方资料核对与修正

| 核对项 | 使用的主资料 | 正文处理 |
| --- | --- | --- |
| 成员与阵列检查 | [mdadm 上游手册](https://github.com/md-raid-utilities/mdadm/blob/main/mdadm.8.in) | 区分 examine 与 detail，不提供 create、zero-superblock 或强制写入作为恢复步骤 |
| loop 区域映射 | [util-linux 的 losetup 手册](https://github.com/util-linux/util-linux/blob/master/sys-utils/losetup.8.adoc) | 只读、实际设备名、字节 offset / sizelimit 与仅释放本次设备 |
| RAID5 方向与数据顺序 | [Linux RAID5 地址映射](https://github.com/torvalds/linux/blob/master/drivers/md/raid5.c) | 在递增成员编号下明确左旋校验位置递减，分开说明对称/不对称；保留厂商及起始相位边界 |
| 工具字段和布局名称 | [X-Ways / WinHex 官方手册](https://x-ways.net/winhex/manual.pdf)，§10.15；[R-Studio RAID 帮助](https://www.r-studio.com/Mac_Help/basic_raid_operations.html?nav=index) | 区分 strip 和整组 stripe，块大小单位及 per-member header/footer；对应四种基础名称，不把厂商延迟布局硬套基本模型 |
| UFS 功能范围 | [UFS Explorer RAID Recovery 用户手册](https://www.ufsexplorer.com/manual/raid/) | 用官方索引/可检索正文核对虚拟 RAID、配置保存、成员与区域；精确菜单与输出格式按当前版本支持 |
| NTFS 字段 | [Linux NTFS3 磁盘结构](https://github.com/torvalds/linux/blob/master/fs/ntfs3/ntfs.h) | 0x30 为 MFT LCN；0x40 为有符号记录大小编码；现代记录 0x2C 的记录编号与 0x10 序列号分开 |
| 逻辑镜像分析 | [mmls](https://www.sleuthkit.org/sleuthkit/man/mmls.html)、[fsstat](https://www.sleuthkit.org/sleuthkit/man/fsstat.html)、[fls](https://www.sleuthkit.org/sleuthkit/man/fls.html)、[icat](https://www.sleuthkit.org/sleuthkit/man/icat.html) 官方手册 | -b 指定扇区字节数，-o 使用逻辑镜像内文件系统起始扇区；单分区导出重新核对偏移 |

先按项目要求使用 Context7 查找 `mdadm` 与 `The Sleuth Kit`。返回结果为无关库，没有选择错误 ID 或伪造 query-docs 覆盖；其后使用上游/官方手册核对。UFS 直接打开接口未稳定返回全文，使用官方手册搜索正文确认可核对范围，没有声称验证全部版本的菜单和导出能力。

主要技术校正：

- 多文件不等于多成员；E01 分段必须按一个逻辑镜像处理。
- 软件 RAID、硬件 RAID和驱动辅助 RAID分开；不保留“软件 RAID没有性能提升”的概括。
- 成员分区起点、Data Offset、超级块位置、逻辑盘分区起点分开，并记录各 sector 字段单位。
- RAID5 左/右旋方向按明确的成员编号约定解释；同步/异步只描述数据排列。
- XOR 满足交换律，整组 XOR为零不能确定盘序或校验成员；校验可能同样保留 FILE 魔数和可读内容。
- MFT记录编号差只在经过验证的连续/对齐数据段内支持候选块大小；不固定记录大小，也不把签名或 GUI行号当成编号。
- MBR命中、能列目录、大文件能打开和虚拟机能启动分别对应不同证据强度，不能直接代表全阵列恢复。
- 缺盘保留原成员槽位，容错能力有状态一致、可读范围和同步完成的前提。
- 仿真写入只发生在独立实验副本或可靠覆盖层；SATA0:0不是通用硬性规则。

## 4. 持久维护与验证范围

三篇网页以 `web-csdn-143604850`、`web-enxiaohao-raid-reconstruction`、`web-cnblogs-15449572` 登记到 `src/data/forensics-supplements.json`，只关联新 RAID 页面；它们加入隐藏的 sourceIds，不显示在网站。原有知识点、工具指南、题目、WP与网页覆盖历史记录保持各自范围。

需核验：新页面分类与独立入口、正文完整生成、三条来源关系、重复导入、现有内容保全、构造脚本与公式、项目检查、构建与链接、实际浏览器目录和搜索。构造样本验证不能代替实际镜像恢复，也不能代替工具软件或虚拟机实操。

## 5. 最终验收记录

- 导入后知识点从 158 增至 159，Forensics 从 57 增至 58。三条网页来源只登记在新 RAID 知识点上；正文和注册表可持续生成页面。
- 再次完整导入后 159 篇知识点的 SHA-256 均与首次导入结果一致。原有 158 篇中仅计算机指南与镜像页增加导航段落，其余 156 篇逐字节不变，没有删除知识点，两个导航页原有正文行全部保留。
- 单元测试 29 项通过，界面测试 5 项通过。项目检查结果为 18 个文件、0 错误、0 警告、0 提示。
- 最终顺序执行生成、构建和审计：生成 318 页，搜索索引包含 309 页；站点审计核验 6,946 条本地链接、159 篇知识点及 79 篇工具指南，错误为 0。取证覆盖审计记录 117 页、50 项标准，错误列表为空。
- 7 个 Bash 示例块通过语法检查，2 个内嵌 Python 示例通过构造输入验证。NTFS 解析覆盖正负记录大小编码、不同扇区大小、短输入和无效偏移。四成员 RAID5 构造样本恢复 1,572,864 字节逻辑数据，与独立排列的预期字节完全一致；错误盘序、布局和块大小得到不同结果，缺失槽位 2 的数据/校验行恢复正确。
- 构造验证同时证明：错误盘序与半块大小仍可能通过 XOR 抽样，全零样本不能证明参数，三个相同 FILE 魔数的异或仍为 FILE。只读脚本运行后成员文件哈希不变。这些结果用于验证解释与示例，不代表真实文件系统恢复成功。
- 实际浏览器显示独立页面的分类路径为“ Forensics / 计算机取证 / 镜像与文件系统 ”，计算机取证列表的“磁盘与文件系统”组有独立链接。正文完整显示 12 个一级章节、11 张表格、7 个代码块，代码换行保留，常规视口没有页面横向溢出，RAID 布局表实际可读，控制台没有错误。
- 搜索界面按 Forensics、计算机取证筛选并输入 RAID，返回 4 项，新页面排在第 1 项；实际点击后进入正确标题和分类页面。网站可见正文没有网页来源标识或具体比赛名称。

验收材料保存在 `.work/forensics-raid/`：导入前备份及哈希、导入后哈希、`examples-validation.json`、最终 `build.log`、页面截图 `page-preview.jpg` 与布局表截图 `layout-table-preview.jpg`。预览入口为 `http://127.0.0.1:4321/knowledge/forensic-raid-reconstruction/`。没有执行真实检材的重组、挂载、GUI 工具恢复或虚拟机仿真。
