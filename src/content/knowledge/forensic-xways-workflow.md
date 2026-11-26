---
title: "X-Ways Forensics 使用方法：配置、分析与交付"
summary: "串联案件、过滤、快照、搜索、注册表、Excire、事件列表、标签与协作，逐条说明八个指定链接的覆盖和差异。"
module: "Forensics"
track: "综合取证"
topic: "工具与路径"
tags: ["文件系统", "时间线"]
status: "已整理"
sourceIds: ["web-xwf-wiki-introduction", "web-xwf-wiki-excire", "web-xwf-wiki-tips", "web-xwf-csdn-wenku", "web-xwf-cnblogs-outline", "web-xwf-wiki-instances", "web-xwf-wiki-events", "web-xwf-wiki-labels"]
challengeIds: []
relatedIds: ["forensic-method-index", "forensic-usb-evidence", "disk-evidence"]
updated: "2026-10-04"
---

XWF（X-Ways Forensics）的标准操作顺序为：**配置工作环境 → 创建案件并添加检材 → 浏览与过滤 → 精炼磁盘快照 → 搜索、注册表及图片分析 → 事件列表 → 标签、恢复与报告 → 多实例协作**。第 01～16 节按可验证的界面入口展开实操步骤；延伸提纲或待实测主张单列在第 17 节。

## 01 工具定位与准备

XWF 是 Stefan Fleischmann 编写的 WinHex 法证版本，既提供十六进制和文件系统层面的查看，也提供文件过滤、文本搜索、注册表报告、图像分析、哈希比对、恢复、RAID 重组和线索分析。功能概述常提及病毒查杀，但取证分析核心在于底层结构与痕迹解析。它可分析计算机、服务器及手机底层镜像；手机底层镜像分析与手机数据采集是两道工序，移动设备采集仍需配合专门的提取工具。

运行可使用 `setup.exe` 安装后启动，或直接运行 `xwforensics.exe`；便携配置使用 `xwforensics64.exe`。XWF 通常附带 WinHex，将可执行文件改为 `WinHex.exe` 等对应名称即可切换运行模式，日常取证直接启动 XWF 即可。

基础运行环境为 Windows、至少 1 GB RAM、足够的镜像存储空间及许可密钥。选择容量较大、数据较少的输出分区，预先分开案件、镜像和临时文件目录。涉及 Excire 图片识别时需满足第 09 节的更高硬件与系统条件。

## 02 路径、语言、查看器与编码

| 配置对象 | 操作与用途 |
| --- | --- |
| 语言 | `Help → Setup → 中文`（切换后下次启动继续生效） |
| 默认目录 | `Options → General` 设置案件、镜像、临时文件及哈希库目录；例如独立划分为 `E:\xway\case`、`E:\xway\images`、`E:\xway\temp`、`E:\xway\HashDB`，脚本目录保持默认 |
| 外部查看器 | `Options → Viewer Programs` 添加查看器，再从右键菜单调用；常用 DB Browser for SQLite、SQLCipher 查看数据库，MPlayer 预览多媒体 |
| 文字视图 | 同时配置 ANSI ASCII、UTF-8、UTF-16、GBK；视图设置也可配置案件栏与数据解释器 |
| 数据解释器 | 右键菜单的 `Options...` 配置类型；可按需切换 `Big Endian`、`Hexadecimal`、`Octal`、`Decimal ASCII Timestamps` 及 `Timestamps based on UTC +8:00` |

旧版 Windows 示例中的 `C:\Documents and Settings\...\Temp` 不作为现代系统的默认路径。Office 文件可以先内置预览大致内容，需要完整查看时用 `Associated Program` 或导出到工作目录后查看；SQLite/SQLCipher 数据库优先配置外部专用查看器打开，避免依赖内置预览漏看 WAL 或表结构。

入门页数据解释器截图展示：8/16/24/32 位有符号及无符号整数、48/64 位有符号整数；Single 32、Real 48、Double 64、Long Double Extended 80 浮点类型；DOS 32、FILETIME 64、OLE 2.0 64、ANSI SQL 64、UNIX/C 32、Mac Absolute 32、HFS 32、APFS 64、Java 64 日期类型；以及 Binary 8、Assembler opcodes、SID/GUID、IP address、Packed 7-bit ASCII。它们是该截图中的选择项，不扩写为所有版本的固定清单。

## 03 便携现场配置与处理速度

在容量较大的可移动磁盘上放置 XWF，并配置 Viewer、MPlayer；Tesseract、Excire 是教程列出的可选组件。新建 `Cases`、`Images`、`Temp`、`HashDB`，在 General 中以相对路径设置这些目录。About 中检查是否采用可移动配置、配置文件是否在当前目录。打开帮助文件可能触发在目标系统创建临时文件的提示，便携运行不等于绝不写入系统。

指定技巧页列出 XWF 可用于 XP/2003/Vista/2008/7/8/8.1/2012/10/2016/2019/11 的环境，其中 11 后原文带未解释的星号；这不改变 Excire 的独立系统要求。配置完成后，插入移动磁盘和加密狗，运行 `xwforensics64.exe`。

| 目标 | 设置 |
| --- | --- |
| 加快快照 | “选项 → 磁盘快照”中完全选中“当没有簇分配表时加速磁盘快照，适用所有文件系统” |
| 加快时间排序 | 完全选中“在内存中保存更多的磁盘快照数据” |
| 加快大案件加载 | “选项 → 目录浏览器”中启用“启动时无排序设置”，减少初始排序 |
| 加快同步搜索 | 增加搜索线程，数量结合 CPU 逻辑核心；多实例操作时给其他实例保留资源，不把所有核心都分给搜索 |

技巧页的同步搜索示例同时进行了 16 个搜索，不把这个数量当成线程字段值或固定推荐。线程与压缩设置是处理选项，不把教程中的个别速度或压缩率观察当作固定性能保证。

## 04 创建案件、添加检材与制作镜像

从案件栏 `Case Data` 的 `File → Create New Case` 创建案件，填写名称、描述、调查员及机构等案件信息，再添加检材；添加镜像用该案件栏的 `File → Add Image...`，不要与顶栏的主 File 菜单混淆。案件名建议使用英文或数字，以确保屏幕快照图片在案件日志和报告中正常显示。

| 添加方式 | 典型用途 |
| --- | --- |
| 镜像文件 | 添加已有镜像，是常用方式 |
| `Add Medium...` | 添加物理设备 |
| `Add Directory...` | 添加目录，也是常用方式 |
| `Add File...` | 添加文件 |
| `Add Memory Dump` | 添加内存镜像；不据此扩写成实时内存采集步骤 |

VMFS 与各类加密分区支持欠佳，需要结合其他软件。20.0 SR-7 演示的文件选择框列出 `Raw Image/Container (.001, .dd, .img, .ctr)`、`Evidence File (.e01)`，以及 `All Types of Images (.001, .dd, .img, .ctr, .e01, .vhd, .vhdx, .vmdk, .vdi)`；这不是全版本格式支持承诺。加载后用 `Compute Hash`（`Ctrl+F2`）计算、查看哈希及校验信息。加载分析不直接修改镜像数据，但不等于所有后续导出或快照操作绝不产生宿主写入。

制作磁盘镜像使用“文件 → 创建磁盘镜像”（`Alt+C`）：选择输入磁盘与输出位置，选择 RAW 或 E01；E01 可压缩。设备选择需综合考虑容量、数据优先级、硬件兼容性及驱动检查。需要同步副本时选择边制作边写入副本，而不是完成后另行复制；还可选择成像后用镜像替换当前打开的磁盘。压缩级别与压缩线程一并设置。

同步副本约可节省 50% 时间，较好压缩率约节省 30%～40% 空间，同时会损失一定成像速度。制作过程中记录 MD5/SHA-1，随后比较镜像与采集数据哈希，不匹配时重新采集。另见提及的 `File → Image a drive`、`Ctrl+I` 不作为本篇的标准制作入口。

## 05 浏览范围、过滤、列与定位

先在案件栏选中要分析的目录或分区，再使用递归浏览/平铺。可以在用户目录等特定层级展开后再平铺，不必每次针对整个案件。

| 动作 | 操作 |
| --- | --- |
| 文件名过滤 | 在名称过滤器输入模式，例如 `Wechat*`，激活后查看匹配文件 |
| 文件类型过滤 | 在 Type 漏斗中选择类别或子类型，例如 Windows Registry，再点 `Activate` |
| 取消过滤 | 右键漏斗选择 `Deactivate` |
| 退出平铺 | 左键点击案件栏某层级，跳转到该层级 |
| 回到文件目录 | 对选中文件右键使用“定位”，返回其所属目录；必要时再取消过滤 |
| 临时显示名称 | `Shift+右键`修改显示名；Wiki 明确说明此动作不修改镜像中的数据 |

列不显示时，点击列表上方空栏，打开“目录浏览及过滤设置，列宽以像素为单位”。点击列名控制显示，隐藏表现为列宽 0 像素，显示则为其他宽度；用像素值或拖拽调整宽度，选中列描述右侧圆圈，再用上下按钮排序。下方 Details/“详细”也可查看信息；`IM` 选项只显示 Internal Metadata。

## 06 同步搜索与结果查看

使用 `Search → Simultaneous Search`，快捷键 `Alt+F10`。入门页正文存在 `Simulataneous` 拼写差异，本篇统一采用其功能标题的拼写。搜索可以选不同编码，也可针对文本或 Hex 值；Wiki 的文字示例搜索 `BitLocker`，Hex 搜索可帮助在文件系统损坏时定位某类文件。

操作顺序：确定范围与搜索词 → 配置编码和条件 → 开始搜索 → 处理中查看已有命中 → 搜索结束进入结果界面 → 点击案件栏目录缩小结果范围。多个搜索词的结果在目录列表下方区分，教程提及可以指定逻辑关系；补充页面还列出通配符、正则及 AND/OR/NOT，但未给出可直接照抄的完整表达式，不补造语法。

同步搜索不是只对磁盘字节进行未经处理的扫描，Wiki 将它描述为经过一定解析后的搜索。文库给出的组合方向还包括内容、名称模式、扩展名、大小及创建/修改时间；其商业数据调查示例使用特定短语与文件名模式找线索。

## 07 精炼磁盘快照

`Specialist → Refine Volume Snapshot`，快捷键 `F10`，用于对已添加的检材进行更深入解析。精炼后可查看 Metadata 列，过滤解析出的信息，悬停查看预览。

这里的“磁盘快照”是后续浏览、元数据和事件列表使用的解析结果，不是另做一份完整磁盘镜像。面向事件分析时，在快照选项中选择“解析文件元数据、浏览器历史记录和事件日志”等相关项目；面向图片和视频时分别用第 09、10 节的图片处理与抽帧选项。

## 08 注册表离线查看与报告

通过类型过滤或目录定位找到 Hive，双击在 XWF 内置离线查看器中打开；最小化查看器后打开其他 Hive，可把多个 Hive 加入左侧列表。Wiki 示例查看 `SOFTWARE\Microsoft\Windows NT\CurrentVersion`。

从注册表查看器左上菜单 `Create Report...` 创建报告，选择相应的 `.txt` 规则配置文件，生成 HTML 后用浏览器搜索。图示规则包括 Reg Report Amcache、Autorun、Devices、Free Space、Histories、Identity、Networks、Printer、Software、System。教程介绍“全部 Hive + 全部规则”的快速查看方式，同时强调单个 Hive 对应适合的规则更精准。

| 查询目标 | 报告检索项 |
| --- | --- |
| CPU、磁盘 | `CPU`、`IDE Device` |
| Windows 与安装 | `Windows internal version`、`Windows installation date`、`Windows product ID`、`Windows CD key`、`Windows name`、`Windows build number`、`Service pack` |
| 主机及语言 | `Active computer name`、`Windows installation language`；后者在教程中未被确认等于当前使用语言 |
| 设备、服务、默认浏览器 | `Windows portable devices`、`Services installed`、`Default Internet Browser` |
| 软件 | `Install date of`、`Name of program`、`Name of program Uninstall`、`Install date of Uninstall`、`Location of program Uninstall`、`Source of program Uninstall` |
| 网络 | `Default Gateway MAC`、`This computer's MAC address`、`DHCP assigned IP Address`、`Network connection`、`Tcpip host name`、`Model description of installed network card` |
| 用户访问 | `URLs typed in Internet Explorer`、`Documents opened`、`Recent File List` |
| 用户与登录 | `User Account`、`Last logged on user`、`Last Computer Name`、`User ID of Administrator`；教程说明 User Account 只显示 SID，Last Computer Name 的确切含义未说明 |
| 用户配置 | `Country`、`User-specific directories`，针对 NTUSER.DAT |

## 09 Excire 配置与图片分类

指定 Wiki 的模块条件：XWF 20.5 已有该功能，建议 20.7 及以后；HEIC 支持从 20.6 起。系统为 64 位 Windows 10/11 或 Server 2016/2019/2022。内存建议至少 8 GiB、优先 16 GiB 及以上并配较好 CPU。该页记录解压体积约 395 MiB；入门页约 100 MiB 指的是配置好 MPlayer 后的程序总体积，不能当作 Excire 模块体积。

该页介绍 Excire 早期付费、后免费发布并集成到 XWF。它用于识别人脸、衣着与年龄分层、人数、车辆、建筑、武器、Drug、色调或文字等图片要素；支持 JPEG、PNG、Bitmap、TIFF、静态 WEBP、GIF、HEIC。

在资源目录 `res` 获取对应版本压缩包，解压到适当目录，在“选项 → 文件查看”配置模块地址。添加待分析目录 → 递归浏览 → 选中全部或部分图片 → 精炼磁盘快照 → 勾选“图片分析和处理”。未选“基于签名和算法验证文件的真实类型”时，教程说明 XWF 会自动选中它。

分析输出可选标签、注释或元数据。以标签输出时，显示“标签”列并按结果筛选。武器示例用 Ctrl 多选 `Weapon`、`Handgun`、`Long Gun`（21.1 新增）。暴露图片示例列 `Nudity`、`Nude Pornography`，总清单另列 `Nude Photography`；两种后项在同一页写法不同，不能在未核对界面时当作同一个确定标签。

作者简单测试中，部分隐蔽携枪图片也被筛出；该页未给出量化样本或通用检出率，不据此作整体识别能力保证。

## 10 特定人脸、视频与分类清单

查找特定人脸：图片分析详细设置 →“查找特定人脸”→ 选择参考照片目录 → 设置严格程度 → 在弹出的照片窗口框选人脸 → 用 PageUp/PageDown 翻页 → 关闭窗口开始分析 → 根据标签过滤命中。参考目录有多张照片时，可以得到对应的多种过滤结果。帮助文件位于 `Excire\marker-help`。

教程以 Marit Larsen 的参考照片演示：严格程度 5 命中两张、仍漏一张；改为 3 后，该测试集合全部命中且未见误识别。这是作者测试结果，不作为其他案件的阈值或准确率。暴露分类也有误识别；`Violin` 例把摆放的几支 56 半步枪识别为小提琴。

视频先选一个或多个目标视频，在精炼快照中同时选“从视频中抽取静态图像帧”和“图片分析和处理”；该页说明处理较慢，建议缩小对象范围。

下面保留教程测试出现的标签名称，并按用途重组；它们由实际分析结果生成，不是所有版本、所有案件固定出现的清单。

| 组别 | 标签名称 |
| --- | --- |
| 类型、自然和场景 | `Animated GIF`、`Nature`、`Plant`、`Desert`、`Sand`、`Beach`、`Rain` |
| 色彩、明暗和质感 | `white`、`cyan`、`Color teal`、`Colorful`、`gray`、`Black and White`、`Colorless`、`Sepia Tones`、`brown`、`Bright`、`Texture`、`Ice Texture` |
| 物品与交通 | `Pills`、`Powder`、`Apricot`、`Food`、`Fruit`、`Vehicle`、`Ship`、`Violin` |
| 武器与群体场景 | `Soldier`、`Weapon`、`Handgun`、`Long Gun`、`Parade` |
| 人与人数 | `Person`、`Face`、`One Face`、`Two Faces`、`Many Faces`、`Group`、`Adult`、`Teenager / Young Adult`、`Baby`、`Child`、`Male`、`Female` |
| 人脸与外观 | `Frontal Face`、`No Glasses`、`Glasses`、`Beard`、`No Beard`、`Smile`、`No Smile`、`Eyes Open`、`Eyes Closed`、`Eye`、`Blond Hair`、`Brown Hair`、`Black Hair` |
| 服饰、身体和动作 | `Body Part`、`Hand`、`Underwear`、`Dress`、`Bikini`、`Ballet Dancer`、`Standing`、`Sitting`、`Lying`、`Drink`、`Nudity`、`Nude Photography` |
| 构图 | `Portrait`、`Front View`、`Close-Up` |

教程对一些标签给出特定解释：`Pills` 为药片、`Powder` 为粉末，均在 Drug 相关分类中；`Texture` 在该次测试主要归入 Drug；`Colorless` 包含黯淡颜色而不限于黑白；`Sand` 可以是背景有沙；`Parade` 的例子为阅兵；`Drink` 可以是正在喝的动作或可喝的物品。

`Two Faces` 结果可能超过两张脸，`Soldier` 涵盖军警/武器相关图片，`Ship` 也会因背景轮廓出现。`Eyes Open`、`Eye` 的中文释义在该页有疑似文字问题，本篇仅保留英文，不自行修成另一条事实。该页转述外部 IMFDB 图片对比，称其多数场景的 XWF Excire 结果优于 AXIOM，同时也有不及的场景；它不是作者独立复测，更不能当作普遍产品排名。保留多工具互相补充、人工查看分类结果的使用边界。

## 11 事件列表与时间字段

Wiki 说明 Events List 在 16.9 引入，它整合快照解析的注册表、事件日志、文件系统日志、部分浏览器等信息，支持排序、过滤与搜索。填充内容还包括文件内部时间戳、电子邮件和快捷方式数据；文件时间与内部时间戳可用于重建镜像获取前的系统变化及近期用户活动。点击搜索结果按钮旁的事件列表入口切换；若尚未解析相关项目，列表可能为空。

“时间轴”针对当前文件浏览器列出的文件，用于过滤与定位；Events List 以已解析事件为基础，但显示范围仍受当前目录及是否递归浏览影响。先解析所需项目，再递归浏览整个目录或案件，不能把当前目录的事件当成所有子目录结果。

事件行可以显示时间信息、文件类型、分类描述、具体描述与记录所属的文件名。按时间排序或过滤范围，在文件类型列用漏斗筛选事件类别；Ctrl 选择多项，Shift 选择连续范围。

| 分类 | Wiki 插图展示的部分过滤项 |
| --- | --- |
| 文件系统 | `Creation`、`Modification`、`Access`、`Record change`、`Deletion`、`Recycle bin`、`Added`、`Rename`、`Mount`、`Unmount`、`Permission change`、`Ext attr modification`、`Ext attr deletion`、`Document revision`、`Exchange`、`Metadata modification`、`Hard link`、`Symbolic link`、`End of transaction` |
| 文件内部元数据 | `Other`、`Creation`、`Modification`、`Access`、`Record change`；EXIF 例另有 `Last saved`、`Attached`、`Content created (Exif)` |
| 互联网相关 | `Other`、`Visited`、`Cookie`、`Remote`、`Fetch`、`Sign-on created`、`Sign-on last used`、`Modified` |
| 通信信息 | `Sent`、`Received`、`Created`、`Record change`、`Account created`、`Last online`、`Last activity`、`File transfer`、`VoIP call`、`Chat`、`Instant message` |
| 操作系统 | `Other`、`Program started`、`Program ended`、`OS shutdown`、`OS startup`、`Session start`、`OS update`、`Encrypted volume creation`、`Encryption key modification`、`Network connection`、`Network data`、`Windows network data`、`Application resource`、`Energy usage` |
| 事件日志 | `Interactive log-on`、`Log-off`、`Failed log-on`、`User account created`、`User account deleted`、`System time changed`、`User account enabled`、`User account disabled` |
| 注册表 | `Key changed`、`Value changed`、`Other`、`Clean-up`、`StartMenu start`、`Timestamp`、`Default`、`Log-on`、`Failed log-on`、`MRU list`、`Profile loaded`、`SlowInfoCache`、`AppCompatCache`、`Device attached` |

这些是页面截图中的部分选择项，不能据此宣布全量支持。其示例中，注册表 `Device Attached` 接入设备信息来自 SYSTEM；通信信息出现 main.db 与 eml；`文件内部元数据: Content created (Exif)` 显示照片内部时间与相机信息；SAM 提供 `Log-on` / `Failed log-on`；INFO2 的 `Recycle bin` 描述包含原路径。

专有应用可能无法充分解析，列表只包含快照已经解析出的内容。过滤对话框左上系统菜单的“保存设置...”与“加载设置...”可复用窗口布局、过滤选择；同菜单还展示“文本对话框表示 → 剪贴板”（Ctrl+C）、仅 ASCII 明文字符与忽略未选择项目选项。

| 时间列 | Wiki 技巧页给出的说明 |
| --- | --- |
| 创建时间 | 卷内文件/目录创建日期和时间，不含 Linux |
| 创建时间 2 | 以前可追溯的有效时间戳，也用于 HFS+ |
| 修改时间 / 修改时间 2 | 最后修改时间 / 以前可追溯的有效时间戳 |
| 记录更新时间 | NTFS 文件记录或 Linux inode 的修改时间 |
| 记录更新时间 2 | 以前可追溯的有效时间戳 |
| 访问时间 | 最后读取或访问日期和时间；FAT 只提供日期 |
| 删除时间 | 文件/目录删除日期和时间 |
| 内容创建时间 | 文件内部元数据记录的创建日期和时间 |

## 12 标签与报告表

20.6 及以前的 `Report table associations`（“包含报告表”）在 20.7 及以后称为 `Labels`（“标签”），Wiki 以 2022-11-15 为名称切换时间界限。旧教程截图名称不同，不代表另一个独立功能。

显示标签列，递归浏览后过滤图片类型，按大小降序（从大到小）排列，再用缩略图寻找目标。用空格标记目标，再右键“选择 → 已标记的项目”批量选择；右键“报告表关联 → 新建(N)...”，填写标签并点“创建”。可以一次新建多个标签，只添加一个时也可双击该标签。已有标签再用于分类与过滤；将具有某标签的文件以表格输出时，结果仍称 report table。

一个文件可有多个标签。Wiki 示例给实际 JPG、扩展名为 MP3 的对象另加“故意修改拓展名”标签，用来演示多标签分类。快照也可能已经自动生成其他标签；初筛得到的图片不包含全部加密或隐写对象，仍需进一步分析。标签只是该例的分析标注，本篇不复述具体文件名或把该例扩写为新案件。

| 操作 | 结果或边界 |
| --- | --- |
| `Ctrl+1`～`Ctrl+9` | 添加对应标签 |
| `Alt+1`～`Alt+9` | 移除对应标签 |
| `Ctrl+0` | 一次性移除所选文件全部标签 |
| 调整标签顺序 | 影响显示优先级；教程只在 20.0 验证它不改快捷键和既有文件关联 |
| 删除标签定义 | 对应文件上的该标签也消失 |
| 标签过滤 | Ctrl 多选标签，选 AND 并激活可筛同时具有这些标签的对象 |

绿色标记来自用户手工添加，灰色来自 XWF 自动添加，棕色来自 Excire；哈希库命中也可形成标签标记。标记数量反映关联标签数量，教程还把它作为图片内容复杂程度的粗略观察，不把数量当作已确认内容。

## 13 恢复、复制、报告与证据容器

用 Ctrl/Shift 选多个目标 → 右键 `Recover/Copy...` → 选择输出路径 → 导出。入门页的默认输出是案件目录下按分区名称/编号命名的目录，通常保留目录结构。指定链接涉及已删除、未分配空间、损坏及特定类型恢复，但没有提供统一的完整修复算法，不补写恢复脚本。

案件窗口“文件 → 创建报告”可把手工标记对象加入报告表并生成报告。结合补充页面的报告要求，交付内容应说明案件目标、取证步骤、发现及结论，采用准确术语、图表或时间线；保留详细过程而不把主观推测写为事实。呈证说明还涵盖镜像过程、搜索准确性、恢复方法、报告的可信性与相关性，不把来源的泛称标准理解为司法采信保证。

导出证据容器时，是否携带标签采用三态选项：全选包含全部，半选只含人工创建，不选不含标签。打开容器后可在 XWF/XWI 中查看这些标签。选择“记录证据文件管理器并添加至报告表”后，成功加入容器的文件会得到以容器名称命名的标签。

## 14 嵌套镜像分析

发现镜像中的 VMDK 时，不能把压缩包内容提取流程直接当成嵌套磁盘解析。Wiki 给出的步骤是：对该文件选择右键菜单中的第二个“打开”，进入新的十六进制 Tab →“专业工具 → 将镜像文件转换为磁盘”→ 浏览其中分区。

该页区分 `xxx-flat.vmdk` 的原始磁盘数据与另一个 VMDK 描述文件；普通 VMDK 显示形式与 flat 数据文件不同。第一项“打开”是文件查看，教程报告在此场景可能卡住；不要把两个入口合并。

## 15 多实例与 XWI 浏览

在设置中启用“允许同时运行多个程序”。添加检材并保存案件后，打开第二实例并加载同一案件，按提示使用第二身份；再开实例时选新的用户身份。Wiki 图示选择“允许分布式分析及磁盘快照”，案件区标题显示身份和模式。提示说明分布式快照仅适用于证据存储在不同磁盘的情况：案件文件只读、快照协同。不要与另一个“只读模式（保护案件防止被修改）”选项混同。Wiki 示例在一个实例浏览、另一个精炼快照、第三个同步搜索，也允许不同电脑上的用户使用共享目录案件。

作者观察其测试中三个用户后更多实例以只读打开，但明确表示尚待继续测试，不能写成软件硬性上限。只读实例仍能同步搜索；快照修改可能无法写入案件数据或共享给其他实例。搜索线程要留出浏览与其他处理的资源。

XWF 设置可切换为 XWI 简化界面，标题显示 `X-Ways Investigator*`；软件仍是 XWF。保留案件管理、同步搜索、打开磁盘、哈希库、磁盘快照与 CTR 案件容器，移除十六进制显示并提供最多三个编码栏。教程还列出 XWI 在导出/恢复、镜像转磁盘、直接注册表分析方面的限制，并说明需要先购买 XWF 才能购买 XWI 套件。

该页的组合方法是复制 XWF 程序目录，将其中一份切换为 XWI 界面；主 XWF 分析，XWI 打开同案件作快速编码浏览，需要完整功能再切回 XWF。关于预览卡顿及 21.0 及以上改善是作者体验，不是零故障保证。

## 16 标签协作与综合操作路线

需要分工时，将相应文件通过证据容器分发，协作者在 XWF/XWI/XWI CTR 中处理并增加标签。右键案件名称，使用旧版“导出报告表关联”或新版“导出标签”；旧版图示导出扩展名为 `.rtd`，导入菜单为“导入关联报告表(I)...”。汇总时选导出文件所在目录导入；Wiki 明确说明导入成功后这些标签文件会被删除。原段落一次写作“汇总人将导出的标签文件导出”，同段后文与图示均指向导入，本篇据此整理为导入。

案件属性“多用户支持选项...”可设置标签后方用户全名/缩写、仅显示自己的关联报告表，以及新增文件和注释的姓名缩写。容器分发汇总与第 15 节同案多实例是两条协作路线，不合并为一种操作。

结合上述功能，可以把指定教程的操作组合为：

1. 配置目录、查看器与编码，创建案件并添加检材，查看哈希。
2. 按目录递归浏览，用 `Wechat*` 或 Type 缩小范围；用同步搜索查关键词与 Hex。
3. 精炼需要的元数据、浏览器与事件日志；注册表采用相应规则生成 HTML 报告。
4. 对图片启用 Excire；特定人脸用参考目录与框选；视频先抽帧再分析。
5. 打开事件列表，核对递归范围、事件类别与时间列；按文件内容与分析结果添加标签。
6. 恢复/复制目标，生成报告或证据容器；有分工时通过标签导出与导入汇总。

这些是指定页面方法的组合，不代表本篇已在真实检材上执行了上述流程。

## 17 补充页面的范围提示与未确认主张

为避免删掉补充链接的主题，同时不把泛化描述写成已确认操作，以下单列它们独有的提纲或功能主张。指定六篇 Wiki 未给出对应的完整实现/入口时，本文不编造步骤，也不反向断言软件必然没有该能力。

| 补充主题 | 保留的要点及处理 |
| --- | --- |
| 采集与比较 | 补充两页提出物理/逻辑、标准/逐位镜像、raw/dd、密码保护、分区与设备选择、文件差异、数据完整性与写保护；文库还列 `Compare hash values`、`File → Image a drive` / `Ctrl+I` 和“工具 → 物理镜像”。成像操作入口采用第 04 节 Wiki 的 `Alt+C`，不把文库未获确认的入口或选项写为已验证步骤 |
| 文件系统与恢复 | NTFS/FAT/exFAT/EXT/HFS+、VHD/VMDK、分区表分析、坏道扫描、未分配空间、删除/格式化、碎片及损坏恢复；文库列 `Analyze file systems`、`Deep scan`、`File recovery`、`Carving` 和“文件 → 修复”，本篇未核对其具体菜单与能力。博客园的历史修改记录、多次快照对文件/目录变化检测，也只保留为该页主张，不混同第 07 节精炼快照 |
| 类型与文档 | 文件头尾/真实类型、Office/PDF 文本、缩略图、切片、元数据及所有者；“哈希与数字签名”的分类保留为补充页概括，不混同第 04 节哈希操作 |
| RAM 与虚拟机 | 文库声称 `Live RAM Memory` 捕获、进程/连接/会话、映射文件/内核对象、最近访问文件和删除日志残留，并提出内存与磁盘互证；博客园提纲包含密钥、物理/虚拟内存和虚拟机快照。Wiki 明确的入口是添加内存镜像，本篇不扩写其采集或进程解析步骤 |
| 网络与云 | pcap、TCP/IP/HTTP/DNS、异常端口/包序列、网络环境记录、云存储及元数据、数据泄露追踪；这些是补充链接的方向或主张，未补入指定 Wiki 未给的操作细节 |
| 隐藏与加密 | 隐写、数字水印、格式/文件头检查、算法识别、用候选密钥/密码及内外部工具尝试处理；文库还主张列出加密文件、用哈希库识别加密类型和暴力破解。这些缺少指定 Wiki 的具体依据，只保留来源主张，不宣称所有加密内容都能解密 |
| 宏、脚本及扩展 | 批处理、JavaScript/Python、变量/控制语句、模块化/错误处理/调试、API/插件/外部库；文库的“多硬盘搜索→筛选→CSV 元数据→测试优化”是方案描述，未提供可验证接口或代码，因此不新增代码 |
| 关联与报告 | 索引、哈希值检索、关系/链接可视化、因果模型、时间线、HTML/PDF/CSV、自定义工作流、大数据集/数据挖掘与去重；博客园提出“删除重复数据”，但未说明删除对象与实现步骤，不转写为修改检材的操作。第 11～13 节采用 Wiki 明确的事件/标签/报告方式，其他格式与关联动作只保留学习方向 |
| 擦除与保全 | 文库概览提到安全擦除；两篇强调哈希、时间记录、封存介质、操作日志、证据关联和审计。本文只保留主题，不新增擦除命令 |
| 平台、版本与规范 | 博客园声称部分 Linux 支持、专业版/法医版、法庭标准及法医级支持；指定 Wiki 未给对应依据。补充两页讨论授权、隐私、伦理与证据可接受性，保留为规范主题，不补写适用法规或采信保证 |
| 实战与学习 | 商业数据窃取场景按采集→搜索→恢复→报告组织；模拟环境涵盖入侵、篡改、恶意软件；需求分析→选工具→接口集成→测试→持续评估，配合培训、书籍、课程、社区和实践总结，持续跟踪技术/工具/法规、认证与职业学习目标 |

## 18 来源说明

本篇逐条处理以下 8 个地址；没有以第三方手册、其他网页或既有知识点的事实补齐它们未提及的内容。菜单与示例按这些页面描述整理，未宣称验证当前安装版本。下表也说明图片和专栏范围。

前三篇 Wiki 的正文均已完整读取；入门页另核对 8 张关键配置/案件/镜像/报告插图，这三篇其余 110 张插图未逐图读取，不推断未读图片中的附加字段与结果。后三篇 Wiki 的 72 张插图均已读取。镜像格式与解释器清单按已核对截图限定，未穷举所有版本选项。

| 链接 | 阅读与对应章节 |
| --- | --- |
| [Wiki：XWF 入门](https://www.forensics-wiki.com/node/0197f5eb-59ea-7d5d-a88f-d997aac44bdc) | 正文已读取；配置、案件、过滤、搜索、快照、预览、注册表、复制恢复对应 01～08、13、16 |
| [Wiki：Excire 图片分析](https://www.forensics-wiki.com/node/0197f603-6725-7f16-9edb-87c885033916) | 正文已读取；条件、图片/人脸/视频、标签清单与测试限制对应 09～10、12 |
| [Wiki：XWF 实用技巧](https://www.forensics-wiki.com/node/0197f606-44de-70fa-840c-6ed2c0462d5c) | 正文已读取；便携、速度、成像、列、名称、嵌套镜像、XWI、时间字段对应 03～05、11、14～15 |
| [CSDN 文库：XWF 全面攻略](https://wenku.csdn.net/column/45z64793a5) | 直接抓取失败，浏览器取得该地址可见主文章与概览；对应 01～02、04、06、13、17。未把专栏另列的其他文章或付费附件当作已读取材料 |
| [博客园：基础至高级使用提纲](https://www.cnblogs.com/suv789/p/18304375) | 正文已读取；功能分类和多级提纲交叠合并，对应 01、06、13、17；不是与其他地址完全重复的整篇文章 |
| [Wiki：多开与 XWI](https://www.forensics-wiki.com/node/0197f612-4279-7699-a18b-3ca961f7b7bb) | 实时正文与 13 张插图均已读取；多身份、只读、线程、XWI 组合对应 03、15 |
| [Wiki：事件列表](https://www.forensics-wiki.com/node/0197fd30-0ac9-7077-b4a6-bb8badd8accf) | 实时正文与 23 张插图均已读取；解析前提、目录范围、分类过滤、保存设置对应 07、11 |
| [Wiki：标签与报告表](https://www.forensics-wiki.com/node/0197fd4e-1ec0-7f00-a3a9-aa54a0705086) | 实时正文与 36 张插图均已读取；名称版本、标记、快捷键、报告、证据容器及协作对应 09、12～13、16 |

没有发现整篇完全重复的地址，重复的配置、过滤、时间线、恢复和报告主题已归并到单一章节。资源推荐、售价、代理联系与推广评价不作为操作要点。页面中的历史首发年份有 2001 与回忆性 2003 两种表述，不据此写成确定的软件发行历史。

冲突处理：磁盘快照、成像入口与事件列表采用 Wiki；数据库查看采用其外部查看器方式；Wiki 本身的 Excire 标签拼写和翻译差异在第 09～10 节保留说明。补充页面独有但未被指定 Wiki 确认的主张保留在第 17 节，不当作已经实测的工具能力。
