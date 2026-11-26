---
title: "Volatility 2/3：完整参数、插件与场景速查"
summary: "按明确的官方版本列全局参数和内置插件及其选项，区分两代命令、依赖与旧名，并提供任务选择和实战模板。"
module: "Forensics"
track: "内存取证"
topic: "工具参数与插件"
tags: ["程序校验"]
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42", "web-forensics-wiki", "web-forensics-wiki-skilltree", "web-goodlunatic-761da51", "web-hello-memory", "web-memory-volatility2-261", "web-memory-volatility3-2282"]
challengeIds: []
relatedIds: ["forensic-memory", "forensic-memory-processes", "forensic-memory-recovery", "forensic-memory-unix", "forensic-memory-practice"]
updated: "2026-10-03"
---

## 01 阅读范围与版本

按任务选方向，再按操作系统查插件，最后展开对应参数；覆盖全局命令行参数、每个内置插件的参数、用途与应用场景，不要无目的地对镜像执行所有插件。

清单固定为 **Volatility 2.6.1** 和 **Volatility 3 Framework 2.28.2**。Volatility 3 是框架名称，发布版本仍可能从 2 开始；`2.28.2` 不属于 Volatility 2。完整性指这两个官方版本的可调用内置命令和其公开 CLI 选项；不断增加的社区插件、GUI 按钮与任意第三方包不属于一个可以穷尽的统一集合。

| 对比 | Volatility 2 | Volatility 3 |
| --- | --- | --- |
| 运行环境 | Python 2 的历史隔离环境 | Python 3，依赖以安装版本为准 |
| Windows 识别 | Profile、KDBG、DTB 等；imageinfo 只提供候选 | 地址层、内核/PDB 标识与 ISF；windows.info 检查基线 |
| Linux/macOS | 同构建 DWARF/System.map 或对应 Mac Profile | 同构建调试材料生成 ISF，并核对完整 banner |
| 命令名 | `pslist`、`linux_pslist`、`mac_pslist` 等 | `windows.pslist.PsList`、`linux.pslist.PsList` 等命名空间 |
| 参数组织 | 全局选项及插件 add_option，存在继承与条件要求 | 全局选项在插件名前，插件参数在后；内部层/符号要求不是普通 CLI 开关 |
| 导出和表格 | `-D/-O` 等由插件定义；`--output/--output-file` 依 renderer 支持 | `-o` 指派生文件目录；`-r` 控制表格显示，重定向保存表格 |
| 兼容性 | 旧系统、旧 GUI/历史对象插件较多；新系统不保证支持 | 同一版本仍有 OS/符号限制、重命名兼容入口和可选依赖 |

仅安装框架，不代表所有插件依赖都已齐备；完整目录也不表示每个插件可分析每份镜像。帮助里缺少命令时，先查可选依赖、加载错误、版本与系统范围，不能直接判断镜像中没有对应对象。

目录共 **265 个 Vol2 内置命令、197 个 Vol3 内置命令**；Vol3 其中 28 个为兼容旧名。两代各列 23 / 23 项全局选项，每个插件展开后可查继承后的全部专用参数。Vol3 的独立 volshell 参数另列，不混入插件命令数量。

## 02 调用、配置与输出的顺序

以下两个 `vol.py` 路径明确区分工具目录，工作副本为 `work/memory.raw`。示例 PID、地址和 Profile 均需用本镜像的验证结果替换。

```bash
mkdir -p output/vol2 output/vol3 output/dumps symbols cache

# Vol2：已准备好 Python 2 隔离环境。
python2 ./volatility2/vol.py --info > output/vol2/tool-info.txt
python2 ./volatility2/vol.py -f work/memory.raw imageinfo \
  > output/vol2/imageinfo.txt
profile='REPLACE_WITH_VERIFIED_PROFILE'
python2 ./volatility2/vol.py -f work/memory.raw --profile="$profile" pslist -h

# Vol3：全局参数 → 插件完整名 → 插件参数。
python3 ./volatility3/vol.py --help > output/vol3/tool-help.txt
python3 ./volatility3/vol.py -f work/memory.raw windows.info.Info \
  > output/vol3/info.txt
python3 ./volatility3/vol.py windows.pslist.PsList --help
python3 ./volatility3/vol.py -f work/memory.raw -q -r json \
  windows.pslist.PsList --pid 1234 > output/vol3/pslist.json
python3 -m json.tool output/vol3/pslist.json > output/vol3/pslist-readable.json
```

Vol3 可以用唯一匹配的简写；`pslist` 同时匹配多个系统，`windows.pslist` 通常较明确，完整名称最便于保存与复查。`--pid 1234 5678` 只适用于声明列表参数的插件；不能把一个插件的筛选参数复制给所有插件。布尔开关一般直接出现，不要写成 `--dump true`，除非该项实际声明为有值参数。

Vol2 可通过 `VOLATILITY_` 环境变量和配置文件提供选项，帮助应保存实际生效值；不同镜像切换前核对 Profile、LOCATION、KDBG、DTB。Vol3 的用户 CLI 配置、显式 `-c` JSON 和 `-e` 配置扩展各有用途；保存实际配置树并核对覆盖关系，不把旧插件的配置路径移给新插件。全局输出目录与数据表输出文件分别记录。

`--offline` 限制联网取符号，不会自动生成缺失的 ISF。缓存、符号与输入材料分目录保全；清缓存属于分析环境变更，应另记一轮。加载额外插件目录会运行其中的 Python 代码，只加入已经核对的可信插件，不把检材附件目录当插件目录。

## 03 先按问题选择插件

| 问题 | Vol2 入口 | Vol3 入口 | 主要验证 |
| --- | --- | --- | --- |
| 是什么系统、镜像是否可读 | `imageinfo/kdbgscan`；对应格式 info | `windows.info.Info`；`banners.Banners/isfinfo.IsfInfo` | 架构、内核、层、符号与多个合理结构；banners 不是 Windows 识别替代 |
| 进程与父子关系 | `pslist/psscan/pstree/psxview` | `windows.pslist.PsList`、`windows.psscan.PsScan`、`windows.pstree.PsTree`，`windows.malware.psxview.PsXView` | 进程实例、对象地址、起止时间和 PID 复用 |
| 命令、环境、身份 | `cmdline/cmdscan/consoles/envars/getsids/privs` | `windows.cmdline.CmdLine`、`windows.envars.Envars`、`windows.getsids.GetSIDs`、`windows.privileges.Privs` 等 | 参数、历史、会话和权限分开；权限存在不证明使用 |
| 连接与拥有者 | 旧系统 `connections/connscan/sockets/sockscan`；支持系统 `netscan` | `windows.netscan.NetScan`、`windows.netstat.NetStat` | 对象生命周期、端点与实际流量/日志；残留不等于实时连接 |
| 加载模块、注入候选 | `dlllist/ldrmodules/vadinfo/malfind/threads` | `windows.dlllist.DllList`、`windows.vadinfo.VadInfo`、`windows.malware.ldrmodules.LdrModules`、`windows.malware.malfind.Malfind` | 内容、映射、线程起点、合法 JIT 和软件解释 |
| 导出文件、进程或 PE | `filescan/dumpfiles/memdump/procdump/dlldump` | `windows.filescan.FileScan`、`windows.dumpfiles.DumpFiles`、`windows.memmap.Memmap` 及支持的 `--dump` | FILE_OBJECT 地址类型、映射、缺页和真实格式；导出物不是天然 minidump |
| 注册表与账户 | `hivelist/hivescan/printkey/dumpregistry/hashdump` | `windows.registry.hivelist.HiveList`、`windows.registry.printkey.PrintKey`、`windows.registry.hashdump.Hashdump` 等 | hive VA、键路径、账户 RID/SID、版本和实际解析范围 |
| 内核驱动与 hook | `modules/modscan/driverscan/ssdt/callbacks` | `windows.modules.Modules`、`windows.modscan.ModScan`、`windows.driverscan.DriverScan`、`windows.ssdt.SSDT`、`windows.callbacks.Callbacks` | 指针归属、符号、正常驱动和独立加载记录 |
| Linux 行为与文件 | `linux_pslist/linux_bash/linux_lsof/linux_find_file` | `linux.pslist.PsList`、`linux.bash.Bash`、`linux.lsof.Lsof`，`linux.pagecache` 对应插件 | 同构建符号、UID/PID、inode/路径、缓存与日志 |
| macOS 行为 | `mac_pslist/mac_psaux/mac_lsof/mac_netstat` | `mac.pslist.PsList`、`mac.psaux.Psaux`、`mac.lsof.Lsof`、`mac.netstat.Netstat` | Darwin 构建、架构、符号及支持范围 |
| 关键字与规则、时间 | `strings/yarascan/timeliner/volshell` | `yarascan.YaraScan`、`timeliner.Timeliner`、相应进程规则扫描及 volshell | 偏移、编码、规则、对象归属、时区与缺页 |

表中的 Vol2 `/` 分隔多个插件，不是可直接执行的合并命令；Vol3 入口使用完整名称。Vol3 的旧 `windows.malfind`、`windows.psxview`、部分凭据和 Linux 检查入口存在兼容别名，优先用下方列出的有效新名称，不将两种入口当成独立检测器。

## 04 参数使用中最容易出错的地方

1. **平台与版本：** Vol2 的 `--profile`、`-p PID` 与 Vol3 的符号机制、`--pid` 分属两代；Vol3 全局 `-p` 是插件目录。
2. **地址类型：** Vol2 `dumpfiles -Q` 接受 FILE_OBJECT 物理地址；Vol3 `--virtaddr/--physaddr` 分别处理不同地址。hive VA、DTB、PE RVA、进程 VA、镜像文件偏移不能互换。
3. **筛选范围：** 未传 PID 不一定表示所有对象；插件可能仅处理活动链、扫描结果或指定结构。列表、正则和排除筛选各自影响覆盖，必须保存实际条件。
4. **数据完整性：** `--dump`、`-D` 或 `-o` 只选择导出动作/位置。导出成功不保证缓存完整、格式合法、密钥有效或历史行为成立。
5. **显示与分析：** 隐藏列、输出过滤、JSON/CSV renderer 影响交付视图；保留未筛选原表。解析报错文件不应冒充结构化结果。
6. **强制与修复：** 强制 Profile、unsafe、损坏对象开关或 patcher 会放宽条件或改变分析视图。只在有明确问题和单独批次时使用，结果不能沿用默认可信度。
7. **内部依赖：** Vol3 的 layer、kernel、symbol table、组件版本要求经 automagic/配置满足，不能机械变成 `--kernel 地址` 这类不存在的 CLI 参数。

完整参数表包含默认值和类型。动态路径、依平台值、条件必填与可选依赖会注明；表中的 `None` 是未设置，不是一个应照抄的字符串。所有自定义规则、配置、符号、插件及输出保存摘要与来源记录，便于复查同一批分析。

## 05 实战：文件恢复与进程关联的两代差异

**场景与材料：** 给定已固定的 Windows 内存副本，目标是恢复浏览器曾打开的候选文档，并核对哪个进程实例关联该对象。先建立系统/符号和进程基线，再找 FILE_OBJECT，不使用示例地址作为结果。

```bash
# Vol3：对象清单与实际参数帮助。
python3 ./volatility3/vol.py -f work/memory.raw windows.filescan.FileScan \
  > output/vol3/filescan.txt
python3 ./volatility3/vol.py windows.dumpfiles.DumpFiles --help

# 将下方 VA 和 PID 换为本次输出中确认的对象。
mkdir -p output/vol3/files output/vol2/files
python3 ./volatility3/vol.py -f work/memory.raw -o output/vol3/files \
  windows.dumpfiles.DumpFiles --virtaddr 0xffff800012345678
python3 ./volatility3/vol.py -f work/memory.raw windows.memmap.Memmap \
  --pid 1234 > output/vol3/pid-1234-map.txt

# Vol2：先核对 Profile；-Q 必须是 FILE_OBJECT 物理地址。
python2 ./volatility2/vol.py -f work/memory.raw --profile="$profile" filescan \
  > output/vol2/filescan.txt
python2 ./volatility2/vol.py -f work/memory.raw --profile="$profile" dumpfiles \
  -Q 0x12345678 -D output/vol2/files
```

两代输出使用独立目录或批次，记录派生物与输入的对应关系。把对象、路径、进程实例和时间一起关联；没有缓存页时仍可报告路径对象线索，不填造完整文档。

**结果验证：** 保存导出大小、哈希、地址类型、恢复的页/空洞、文件头与格式解析。PE 重建和进程页导出另记，不能改名后作为 LSASS minidump。出现部分 PDF、部分图像或旧缓存版本时报告恢复范围，并与磁盘、下载记录和日志对照；更完整的恢复步骤见[对象与数据恢复](/knowledge/forensic-memory-recovery/)。

## 06 第三方扩展与空结果的边界

Vol2 常见社区扩展名称包括 `mimikatz`、`autoruns`、`ndispktscan`、`usbstor`、`bitlocker`、VolDiff 等；它们不应被默认列作这两个官方版本的内置命令。补充 Profile 包也不同于插件。LovelyMem、Volatility Workbench、MemProcFS 的菜单与视图不是一个可互换的 CLI 参数集合，应核对实际底层引擎和功能。

YARA、反汇编、加密与 PE 解析等可选依赖缺失时，相关模块可能无法导入；帮助中消失的插件仍可能存在于该版本。安装依赖、取得符号、修复输入层和观察没有命中是不同步骤。下面保留完整官方目录，参数与用途按固定版本解释；空结果的结论先限定为本次方法、范围与时间内未取得对应对象。

只有实际镜像上的对象、页面、输出与独立材料验证后，才能报告运行、恢复或解密成功。插件目录和参数核对不等于真实检材已复跑。

## 07 Volatility 2 全部参数与内置插件

### 使用环境与目录范围

Volatility 2.6.1 使用 Python 2 的历史运行环境，常见为 Python 2.7；下列调用模板写作 `python2 vol.py`。Python 3 不能直接运行这一版本。先准备与目标系统内核和构建匹配的 profile，再核对命令的地址空间与输出约束。

```bash
python2 vol.py --info
python2 vol.py -h
python2 vol.py pslist -h
python2 vol.py -f memory.raw --profile=PROFILE pslist
```

这里的 `PROFILE` 是待替换的匹配项。`--info` 列出运行环境成功导入的注册对象；未安装可选依赖、未提供 Linux/macOS profile 或目标版本不受支持时，可见与可执行命令会减少。本目录固定 2.6.1，列出 265 个非 Abstract 的内置 Command 候选键；不把额外插件、地址空间类、扫描器类或 profile 类算作命令。命令是否可运行仍以该环境中的帮助、依赖和目标 profile 为准。

全局参数在下面集中列出，每个命令继续共享这些配置；后续各表完整列出命令构造器实际保留的新增与继承参数。默认值是代码默认，配置文件或环境可以改变实际值。`None` 表示未设置，不能直接推导“必填”。“必填/运行条件”区分 CLI 声明与执行阶段的条件检查，导出参数也可能只在导出分支需要。

### 全局参数（23 项）

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--help` | `-h` | 布尔标志 | False | CLI 未声明必填；可选 | 显示帮助及默认值；置于命令后可查看该命令新增参数。 | 全局 |
| `--info` | — | 布尔标志 | None | CLI 未声明必填；可选 | 列出所有已注册对象，包括命令、profile、地址空间与扫描器；不是单纯的 Windows 插件清单。 | 全局 |
| `--cache-directory` | — | 字符串 | 当前用户的 .cache/volatility（受环境影响） | CLI 未声明必填；可选 | 指定结果缓存目录；与证据输出目录区分，默认由当前用户环境决定。 | 全局 |
| `--cache` | — | 标志（callback） | False | CLI 未声明必填；可选 | 启用框架结果缓存；可能使用旧结果，变更镜像或参数后应核对缓存键与工作目录。 | 全局 |
| `--conf-file` | — | 字符串 | 当前用户的 .volatilityrc（受环境影响） | CLI 未声明必填；可选 | 选择用户配置文件；配置值会影响默认参数，记录实际文件及内容哈希。 | 全局 |
| `--debug` | `-d` | 整数；重复累计 | 0 | CLI 未声明必填；可选 | 增加调试输出级别；count 动作，重复 -d 会累加。 | 全局 |
| `--plugins` | — | 字符串 | 空字符串 | CLI 未声明必填；可选 | 额外插件/profile 搜索目录；Linux 使用冒号、Windows 使用分号分隔。第三方扩展另行核验版本。 | 全局 |
| `--filename` | `-f` | 字符串 | None | CLI 未声明必填；装载证据通常需 -f 与正确 profile | 本地镜像文件路径，内部转换为文件位置；常用 -f memory.raw。 | 全局 |
| `--tz` | — | 字符串 | None | CLI 未声明必填；可选 | 显示时间戳所用时区名称；影响时间呈现，不改变证据中的原始时间。 | 全局 |
| `--profile` | — | 字符串 | WinXPSP2x86 | CLI 未声明必填；装载证据通常需 -f 与正确 profile | 选择目标结构 profile；默认旧系统值不能当自动识别结果。Linux/macOS 需匹配目标内核的 profile。 | 全局 |
| `--location` | `-l` | 字符串 | None | CLI 未声明必填；可选 | 指定地址空间的 URN 位置；离线分析使用本地文件位置，避免引入外部输入。 | 全局 |
| `--output` | — | 字符串 | text | CLI 未声明必填；可选 | 选择输出格式，默认 text；格式必须由当前命令实际实现，不能对所有插件假定 JSON 可用。 | 全局 |
| `--output-file` | — | 字符串 | None | CLI 未声明必填；可选 | 保存渲染结果；常规输出拒绝覆盖既有文件，"." 使用时间与命令名生成文件名。sqlite/xlsx 有单独约束。 | 全局 |
| `--verbose` | `-v` | 整数；重复累计 | 0 | CLI 未声明必填；可选 | 增加详细级别；count 动作，重复 -v 会累加。cmdline 也读取此共享配置显示完整路径。 | 全局 |
| `--dtb` | — | 整数 | 0 | CLI 未声明必填；可选 | 手工指定页表根/DTB 地址；通常是物理地址，必须与架构及目标地址空间核对。 | 全局 |
| `--write` | `-w` | 标志（callback） | False | CLI 未声明必填；可选 | 启用可写地址空间；会要求确认，只有专门副本及明确修改步骤才启用，常规取证不需要。 | 全局 |
| `--kdbg` | `-g` | 整数 | None | CLI 未声明必填；可选 | 指定 KDBG 虚拟地址；64 位 Windows 8 及后续受支持构建指向 KdCopyDataBlock，不能照搬旧布局。 | 全局 |
| `--force` | — | 布尔标志 | False | CLI 未声明必填；可选 | 强制使用可疑 profile；绕过核验可能产生貌似合理的错误对象，应保留多对象验证。 | 全局 |
| `--kpcr` | `-k` | 整数 | None | CLI 未声明必填；可选 | 手工指定 KPCR 地址，辅助处理器及内核定位。 | 全局 |
| `--physical_shift` | — | 整数 | 0 | CLI 未声明必填；可选 | Linux 内核的物理随机化偏移；由 linux_aslr_shift 等线索校准。 | 全局 |
| `--virtual_shift` | — | 整数 | 0 | CLI 未声明必填；可选 | Linux 内核的虚拟随机化偏移；与物理偏移分开设置。 | 全局 |
| `--shift` | — | 整数 | 0 | CLI 未声明必填；可选 | macOS 内核 KASLR 偏移；Linux 应用独立的 physical_shift/virtual_shift。 | 全局 |
| `--cookie` | — | 整数 | None | CLI 未声明必填；可选 | 指定 Windows 10 ObHeaderCookie 数值。虽然旧帮助写 address，实现直接使用配置数值，不是变量地址；0 受基类真值判断影响，不能据此可靠强制零值。 | 全局 |
### 渲染器与输出约束

`--output` 选择渲染器，`--output-file` 选择渲染结果路径，`--dump-dir` 等插件参数通常选择提取物目录，二者用途不同。不能把重定向文本视为机器结构化数据，也不能把导出的内存块当完整原始文件。

| 格式 | 用途 | 兼容与限制 |
| --- | --- | --- |
| `text` | 默认人工阅读表或插件定制文本 | 需要实际文本实现或统一输出实现；交互 shell、文件导出等可能有专用行为。 |
| `greptext` | 便于检索的文本输出 | 基类形式依赖插件的 `unified_output`；不能仅凭继承 render 方法判定可用。 |
| `json` | 保存列名及行数据 | 基类形式依赖 `unified_output`；不保证包含 text 中全部附加解释。 |
| `html` | 表格浏览 | 依赖统一输出与 renderer 实现；注意特殊文本的呈现和外部查看环境。 |
| `sqlite` | 将表写入 SQLite 数据库 | 依赖统一输出，需 `--output-file`；数据库写入行为不同于普通文本文件覆盖保护。 |
| `dot` | Graphviz 图描述 | 统一输出或插件自定义实现；节点与边语义取决于插件，不统一等于进程树。 |
| `xlsx` | 工作表导出 | 统一输出或插件自定义实现；需要与历史 Python 2 环境兼容的 OpenPyXL，且需输出文件。 |
| 插件专用格式 | 如 `body`、`idc`、`dot` | 以各插件实际方法为准；不能作为全局通用能力。 |

各命令的“静态输出方法路径”表示存在相应方法，并未对镜像逐个执行。统一输出存在时也仍受具体对象生成逻辑、可选库、缺页和目标 profile 限制；继承的统一输出若与当前插件数据结构不同，还可能失败。仅继承基类 renderer，而没有 `unified_output` 的命令，不因此获得 JSON 等格式。

### 参数判读的共同规则

`--pid` 并非统一类型：大部分进程列表插件接收逗号分隔的字符串；`impscan` 与 `userhandles` 的声明是单个整数。`--offset` 可能是 EPROCESS 物理偏移、内核虚拟地址或插件专用对象地址，必须根据该行含义使用。文件对象物理地址、vnode 虚拟地址和文件数据偏移也不能互换。

扫描命中只产生候选。活动链表、多视图扫描、页表、模块范围、导出字节及外部日志应互相验证；已释放对象、分页缺失、采集竞态、JIT、调试与安全软件都可能造成差异。严格离线分析时不启用 `linux_route_cache --resolve`。修改镜像的 `patcher` 与 `--write` 仅用于专门副本，先后保留哈希及字节差异。

`timeliner --type` 默认包含 `_CMHIVE`、`_CM_KEY_BODY`、`_HBASE_BLOCK`、`EvtLog`、`IEHistory`、`ImageDate`、`LoadTime`、`Process`、`Shimcache`、`Socket`、`Symlink`、`Thread`、`TimeDateStamp`、`Timer`、`Userassist`，不含 `Registry`。指定 `--hive` 或 `--user` 时，应在类型中显式包含 `Registry`；旧帮助中的 `--registry` 报错文字不表示本版本注册了该标志。

### Windows 命令（112 项）

<details>
<summary>展开 Volatility 2 Windows 内置插件目录（112 项）</summary>

#### `amcache`

解析 AmCache 注册表中的程序记录。适用场景：核对程序路径、文件属性与其他执行痕迹；出现记录不单独证明程序执行。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |

</details>

#### `apihooks`

检查用户态与内核 API 的跳转、导入和导出钩子。适用场景：定位落到异常模块或私有可执行区的函数指针，并排除安全软件和兼容组件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 导出 PE 时放宽部分结构检查；可能导出损坏或误识别的数据。 | 继承 ProcDump |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 继承 ProcDump |
| `--no-whitelist` | `-N` | 布尔标志 | False | CLI 未声明必填；可选 | 关闭钩子白名单，显示所有候选；结果需要更多正常软件排除。 | 本插件 |
| `--skip-kernel` | `-R` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过内核态 API 钩子检查。 | 本插件 |
| `--skip-process` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过用户进程 API 钩子检查。 | 本插件 |
| `--quick` | `-Q` | 布尔标志 | False | CLI 未声明必填；可选 | 仅分析关键进程与 DLL 以加快检查；会降低覆盖面。 | 本插件 |

</details>

#### `atoms`

列出会话与窗口站的 atom 表。适用场景：关联窗口消息、字符串和桌面对象，补充 GUI 进程上下文。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `atomscan`

从内存池扫描 atom 表。适用场景：活动链表缺失时寻找残留表，与 atoms 的活动视图交叉核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |
| `--sort-by` | `-s` | 枚举字符串：atom, refcount, offset | offset | CLI 未声明必填；可选 | 按 offset、atom 或 refcount 排序；保留合法枚举值的原拼写。 | 本插件 |

</details>

#### `auditpol`

解析内存中 SECURITY hive 的审计策略。适用场景：判断哪些行为应有审计日志，为日志缺失解释提供配置依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hex` | `-H` | 布尔标志 | False | CLI 未声明必填；可选 | 显示审计策略键的原始十六进制数据。 | 本插件 |

</details>

#### `bigpools`

列出大页内存池分配及标签。适用场景：发现异常大块内核分配，并用标签、地址和驱动映射验证用途。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--tags` | `-t` | 字符串 | None | CLI 未声明必填；可选 | 待扫描的池标签；应核对目标系统中的标签字节。 | 本插件 |

</details>

#### `bioskbd`

读取实模式内存中的 BIOS 键盘缓冲区。适用场景：在含低地址物理页的镜像中寻找残留输入；不将残片当完整会话。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `cachedump`

提取缓存的域登录凭据摘要。适用场景：授权核验缓存登录痕迹；区分 DCC/MSCache 与本地账户 NT 哈希。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--sys-offset` | `-y` | 整数 | None | CLI 未声明必填；可选 | 指定 SYSTEM hive 的虚拟地址。 | 本插件 |
| `--sec-offset` | `-s` | 整数 | None | CLI 未声明必填；可选 | 指定 SECURITY hive 的虚拟地址。 | 本插件 |

</details>

#### `callbacks`

枚举进程、线程、镜像等系统通知回调。适用场景：检查回调归属驱动及地址范围，追查异常内核监控或持久化线索。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `clipboard`

恢复 Windows 剪贴板内容。适用场景：寻找复制的文本或对象，结合会话、进程与时间范围验证归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `cmdline`

读取进程命令行。适用场景：核对启动参数、脚本路径与父子进程关系，注意已结束进程与被修改的 PEB。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--verbose` | `-v` | 整数；重复累计 | 0 | CLI 未声明必填；可选 | 增加详细级别；count 动作，重复 -v 会累加。cmdline 也读取此共享配置显示完整路径。（全局同键声明优先；插件重复声明被忽略。） | 共享全局 |

</details>

#### `cmdscan`

扫描控制台命令历史结构。适用场景：寻找命令输入残留；命令存在不直接证明执行成功。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--max_history` | `-M` | 整数 | 50 | CLI 未声明必填；可选 | 命令历史结构的最大命令数候选，默认 50；应匹配控制台设置。 | 本插件 |

</details>

#### `connections`

遍历 XP/2003 的活动 TCP 连接。适用场景：在受支持旧系统中关联进程与端点，并与 connscan、日志核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 指定物理对象偏移；结合当前插件的对象类型使用。 | 本插件 |

</details>

#### `connscan`

扫描旧版 Windows 的 TCP 连接池对象。适用场景：寻找活动表之外的连接残留；释放对象不代表采集时仍在线。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `consoles`

恢复控制台历史及屏幕缓冲区。适用场景：把输入命令与屏幕输出联系起来，区分命令输入、返回结果和残片。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--max_history` | `-M` | 整数 | 50 | CLI 未声明必填；可选 | 命令历史结构的最大命令数候选，默认 50；应匹配控制台设置。 | 继承 CmdScan |
| `--history_buffers` | `-B` | 整数 | 4 | CLI 未声明必填；可选 | 控制台历史缓冲区最大数量候选，默认 4；应匹配目标设置。 | 本插件 |

</details>

#### `crashinfo`

读取 Windows 崩溃转储头与页布局。适用场景：确认转储类型及覆盖范围，解释物理页缺失和地址转换限制。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `deskscan`

扫描桌面对象。适用场景：活动桌面链表不完整时补充窗口站、会话与 GUI 对象线索。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `devicetree`

显示驱动设备与附加设备树。适用场景：检查过滤驱动的附加关系，与驱动模块和 IRP 处理地址互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `dlldump`

从进程内存恢复 DLL 的 PE 文件。适用场景：导出指定进程或基址的库作静态分析；重建文件可能缺页或与磁盘布局不同。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 恢复可执行文件的输出目录。 | 继承 ProcDump |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 导出 PE 时放宽部分结构检查；可能导出损坏或误识别的数据。 | 继承 ProcDump |
| `--memory` | `-m` | 布尔标志 | False | CLI 未声明必填；可选 | 按内存映像布局雕刻，而非默认可执行文件/磁盘布局。 | 继承 ProcDump |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 继承 ProcDump |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅导出名称匹配正则表达式的 DLL。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 正则表达式匹配时忽略大小写。 | 本插件 |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 根据 EPROCESS 的物理对象偏移定位进程并导出 DLL。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定进程虚拟基址的 DLL。 | 本插件 |

</details>

#### `dlllist`

遍历进程加载器链表中的 DLL。适用场景：建立模块、路径和基址基线，与 VAD 和 ldrmodules 检查脱链模块。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 本插件 |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 本插件 |

</details>

#### `driverirp`

检查驱动 IRP 分发表。适用场景：定位处理函数落到异常地址的驱动，结合设备树排除正常过滤驱动。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅分析名称匹配正则表达式的驱动。 | 本插件 |

</details>

#### `drivermodule`

关联驱动对象与内核模块。适用场景：把扫描到的驱动对象落到模块地址范围，寻找无正常模块归属的对象。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该地址的内核模块。 | 本插件 |

</details>

#### `driverscan`

扫描驱动对象的内存池分配。适用场景：活动列表可疑时寻找驱动残留，与 modules、modscan 和设备树对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `dumpcerts`

扫描并导出 RSA 私钥、公钥证书相关结构。适用场景：授权核验 TLS 身份材料；用外部证书解析核对导出内容而不假定完整密钥。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 恢复可执行文件的输出目录。 | 继承 ProcDump |
| `--memory` | `-m` | 布尔标志 | False | CLI 未声明必填；可选 | 按内存映像布局雕刻，而非默认可执行文件/磁盘布局。 | 继承 ProcDump |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 继承 ProcDump |
| `--ssl` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 使用 OpenSSL 解析候选证书；依赖外部解析组件及有效证书结构。 | 本插件 |
| `--physical` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描物理空间中的已释放存储，而非只遍历活动进程页。 | 本插件 |

</details>

#### `dumpfiles`

恢复文件对象关联的缓存与映射数据。适用场景：根据文件对象物理地址、进程或路径提取缓存，核对缺页、重叠区间与文件长度。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅处理路径或名称匹配正则表达式的文件。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 正则表达式匹配时忽略大小写。 | 本插件 |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 使用 EPROCESS 物理对象偏移定位进程并恢复其文件。 | 本插件 |
| `--physoffset` | `-Q` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的文件对象物理地址导出文件缓存；不是文件内容偏移。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 提取文件的输出目录。 | 本插件 |
| `--summary-file` | `-S` | 字符串 | None | CLI 未声明必填；可选 | 保存恢复文件概要及页范围等信息的文件路径。 | 本插件 |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |
| `--name` | `-n` | 布尔标志 | False | CLI 未声明必填；可选 | 把提取到的原文件名加入输出文件名；需防止同名与路径混淆。 | 本插件 |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 放宽恢复数据的安全检查；可能得到损坏或误识别字节。 | 本插件 |
| `--filter` | `-F` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的缓存/映射来源筛选：SharedCacheMap、DataSectionObject、ImageSectionObject、HandleTable、VAD。 | 本插件 |

</details>

#### `dumpregistry`

把内存中的注册表 hive 导出为文件。适用场景：使用离线注册表工具复核键值；保存导出哈希并记录缺失单元。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 提取文件的输出目录。 | 本插件 |

</details>

#### `editbox`

读取 GUI 编辑框内容，列表框支持具有实验性。适用场景：定位用户界面中的文本残留，与窗口、进程和会话信息核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `table`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 将找到的文本保存到该目录。 | 本插件 |

</details>

#### `envars`

读取进程环境变量。适用场景：寻找路径、代理、运行环境和启动上下文；环境变量可被修改且不一定代表系统配置。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--silent` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 过滤常见或非持久环境变量；可能隐藏有用上下文。 | 本插件 |

</details>

#### `eventhooks`

列出 Windows 事件钩子。适用场景：检查监听 GUI 事件的回调归属，排除辅助功能和正常桌面软件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `evtlogs`

恢复 XP/2003 的传统 EVT 日志。适用场景：从进程映射恢复历史事件，并用日志解析器核对记录边界和时间。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--save-evt` | `-S` | 布尔标志 | False | CLI 未声明必填；可选 | 同时导出原始传统 EVT 文件；须提供输出目录。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；使用 --save-evt 时需要有效目录 | 恢复可执行文件的输出目录。 | 本插件 |

</details>

#### `filescan`

扫描文件对象的内存池分配。适用场景：按路径发现打开或残留的文件对象，为 dumpfiles 提供物理对象地址。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `gahti`

读取 USER 句柄类型信息。适用场景：理解 GUI 句柄表类型，为 userhandles 等结果解释提供类型依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `gditimers`

列出 GDI 定时器及回调。适用场景：检查桌面定时回调归属，补充 GUI 异常行为调查。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `gdt`

读取全局描述符表。适用场景：检查低层执行环境与描述符异常；须结合系统架构和合法基线解释。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `getservicesids`

由注册表服务名计算服务 SID。适用场景：关联服务身份与进程、访问控制记录；计算结果不证明服务曾运行。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `getsids`

列出进程令牌所属的 SID。适用场景：核对用户、组和服务身份，为权限与进程归属调查提供依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |

</details>

#### `handles`

枚举进程对象句柄。适用场景：检查文件、注册表、互斥量、进程等访问关系，与目标对象内容交叉验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 指定物理对象偏移；结合当前插件的对象类型使用。 | 本插件 |
| `--object-type` | `-t` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的对象类型筛选句柄。 | 本插件 |
| `--silent` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 减少插件认为信息量低的结果；应保留完整结果作对照。 | 本插件 |

</details>

#### `hashdump`

从 SYSTEM/SAM 提取本地账户 LM/NT 摘要。适用场景：授权验证本地账户记录；NT 哈希与网络认证挑战响应不是同一种材料。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--sys-offset` | `-y` | 整数 | None | CLI 未声明必填；可选 | 指定 SYSTEM hive 的虚拟地址。 | 本插件 |
| `--sam-offset` | `-s` | 整数 | None | CLI 未声明必填；可选 | 指定 SAM hive 的虚拟地址。 | 本插件 |

</details>

#### `hibinfo`

读取休眠文件头信息。适用场景：确认休眠格式与压缩页覆盖范围，为地址空间装载失败定位原因。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `hivedump`

遍历指定注册表 hive 的键及时间。适用场景：核对 hive 内部结构与键最后写入时间，和磁盘 hive 或事件日志对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |

</details>

#### `hivelist`

从注册表活动链表列出 hive。适用场景：获取 hive 名称与虚拟地址，为 printkey、dumpregistry 或账户材料解析定位。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `hivescan`

扫描注册表 hive 内存池对象。适用场景：寻找活动列表之外的 hive 残留，与 hivelist 互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `hpakextract`

从 HPAK 容器提取物理内存。适用场景：把容器内的内存载荷转换为分析副本，核对输出大小和哈希。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `hpakinfo`

读取 HPAK 容器信息。适用场景：确认采集容器的分段与元数据，判断是否需要先提取物理内存。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `idt`

读取中断描述符表。适用场景：检查中断入口和模块归属，结合架构及正常内核基线排除合法差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `iehistory`

恢复 Internet Explorer 缓存和历史结构。适用场景：追查访问及缓存残留；区分普通、重定向与删除记录，不把缓存时间当唯一访问时间。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`csv`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--leak` | `-L` | 布尔标志 | False | CLI 未声明必填；可选 | 加入 IE 缓存 LEAK 删除记录；残留不表示当前有效访问。 | 本插件 |
| `--redr` | `-R` | 布尔标志 | False | CLI 未声明必填；可选 | 加入 IE 缓存 REDR 重定向记录。 | 本插件 |

</details>

#### `imageinfo`

提出 Windows profile 候选并显示镜像信息。适用场景：先筛选 profile，再用进程、KDBG 和页表结果验证，避免把建议当唯一识别结论。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `impscan`

扫描内存区域中的导入函数调用。适用场景：对缺少正常导入表的 PE 或代码块恢复候选导入，结合反汇编验证调用语义。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `idc`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 整数 | None | CLI 未声明必填；可选 | 选择单个 PID 的进程地址空间；不指定时分析内核空间。 | 本插件 |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；内核模式必填；PID/OFFSET 模式可默认主模块 | 给出待扫描区域基址；指定 PID 时是进程地址，否则是内核地址。 | 本插件 |
| `--size` | `-s` | 整数 | None | CLI 未声明必填；无法由模块、PE 头或 VAD 推定长度时必填 | 待扫描内存长度，单位字节，与区域基址配合。 | 本插件 |

</details>

#### `joblinks`

列出进程与 Windows Job 的关联。适用场景：核对进程分组、限制与父子关系，调查隔离运行或批量启动行为。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 在输出中显示对象的物理偏移，代替虚拟地址；不改变输入镜像字节。 | 本插件 |

</details>

#### `kdbgscan`

扫描并校验 KDBG 候选。适用场景：在 profile 或内核定位不确定时交叉检查候选，注意新系统的编码 KDBG。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `kpcrscan`

扫描 KPCR 处理器控制区候选。适用场景：辅助定位处理器与内核环境；候选必须与 profile 和有效指针互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `ldrmodules`

比较加载器链表与 VAD 映射中的模块。适用场景：寻找脱链或伪装加载记录，结合映射类型与导出文件排除正常差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |

</details>

#### `lsadump`

从注册表材料解密 LSA secrets。适用场景：授权核验服务或系统身份材料；提取结果需结合账户类型与配置解释。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--sys-offset` | `-y` | 整数 | None | CLI 未声明必填；可选 | 指定 SYSTEM hive 的虚拟地址。 | 本插件 |
| `--sec-offset` | `-s` | 整数 | None | CLI 未声明必填；可选 | 指定 SECURITY hive 的虚拟地址。 | 本插件 |

</details>

#### `machoinfo`

显示 Mach-O 内存容器的结构信息。适用场景：确认采集容器分段；命令继承 Windows 公共框架不代表容器里的系统必为 Windows。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `malfind`

寻找潜在隐藏或注入代码区域。适用场景：检查私有可执行映射、字节和反汇编，结合模块链与正常 JIT 排除误报。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 导出 VAD 内存区域的目录。 | 继承 VADDump |
| `--max-size` | `-M` | 长整数（Python 2） | 1073741824 | CLI 未声明必填；可选 | 限制处理或导出区域最大大小，默认 1 GiB；更大区域可能被跳过。 | 继承 VADDump |
| `--refined` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 仅显示含 MZ 头或常见指令开头的区域以减少噪声；会漏掉擦头、NOP 起始等代码，应保留未筛选结果。 | 本插件 |

</details>

#### `memdump`

导出进程可寻址内存。适用场景：保存进程页面用于字符串与静态分析，记录可寻址范围和不可恢复页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 导出内存字节的目录。 | 本插件 |

</details>

#### `memmap`

显示进程虚拟页与物理页映射。适用场景：核对区域驻留与字符串归属，支持定位和导出范围解释。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |

</details>

#### `messagehooks`

列出桌面和线程窗口消息钩子。适用场景：定位消息监听链的模块与进程，排除合法输入法、辅助功能和桌面程序。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`block`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mftparser`

扫描并解析内存中的 MFT 记录。适用场景：恢复文件属性、路径和时间线；残留记录与驻留数据需验证签名和记录边界。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`body`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 字符串 | None | CLI 未声明必填；可选 | 以逗号分隔的 MFT 记录物理偏移，定向解析候选。 | 本插件 |
| `--nocheck` | `-N` | 布尔标志 | False | CLI 未声明必填；可选 | 放宽 MFT 校验以包括空时间戳等条目；结构误报可能增加。 | 本插件 |
| `--entrysize` | `-E` | 整数 | 1024 | CLI 未声明必填；可选 | MFT 单条记录大小，单位字节；默认 1024，须按目标卷结构验证。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 导出 MFT 驻留文件数据的目录；非驻留内容不由此完整恢复。 | 本插件 |
| `--machine` | — | 字符串 | 空字符串 | CLI 未声明必填；可选 | 给时间线添加机器标记；它是人工标签，不代表自动识别主机身份。 | 本插件 |
| `--debugout` | — | 布尔标志 | False | CLI 未声明必填；可选 | 输出该插件调试消息，便于解释扫描与结构判定。 | 本插件 |

</details>

#### `moddump`

从内核内存恢复驱动 PE。适用场景：按基址或名称导出驱动作静态分析，核对缺页、修复和磁盘差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 恢复可执行文件的输出目录。 | 继承 ProcDump |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 导出 PE 时放宽部分结构检查；可能导出损坏或误识别的数据。 | 继承 ProcDump |
| `--memory` | `-m` | 布尔标志 | False | CLI 未声明必填；可选 | 按内存映像布局雕刻，而非默认可执行文件/磁盘布局。 | 继承 ProcDump |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 继承 ProcDump |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅导出名称匹配正则表达式的内核模块。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 正则表达式匹配时忽略大小写。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |

</details>

#### `modscan`

扫描内核模块池对象。适用场景：与正常模块链表比较，寻找卸载残留或脱链候选。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `modules`

遍历 Windows 已加载内核模块。适用场景：建立驱动基址与范围基线，为回调、SSDT、IRP 和扫描结果归属分析服务。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 指定物理对象偏移；结合当前插件的对象类型使用。 | 本插件 |

</details>

#### `multiscan`

一次扫描多种内存池对象。适用场景：在物理扫描成本较高时同时搜集对象候选，再用各对象结构验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `mutantscan`

扫描互斥量对象。适用场景：寻找程序协调或单实例标识，结合对象名和进程句柄核对，不能单凭名称归因。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |
| `--silent` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 减少插件认为信息量低的结果；应保留完整结果作对照。 | 本插件 |

</details>

#### `netscan`

扫描 Vista 及后续受支持 Windows 的网络对象。适用场景：关联 TCP/UDP 端点、状态与进程，注意已释放对象及具体 profile 支持范围。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `notepad`

恢复旧版 Notepad 当前显示文本。适用场景：在适配进程与应用布局时寻找文本，核对字符编码与缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 将命中区域的二进制字节保存到该目录。 | 本插件 |

</details>

#### `objtypescan`

扫描 Windows 对象类型结构。适用场景：核对对象类型定义和布局，辅助句柄与池对象解释。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `poolpeek`

按标签和大小范围扫描内存池。适用场景：已知可疑对象标签时定向找候选，核对池类型、大小和结构内容。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--tag` | `-t` | 字符串 | None | CLI 未声明必填；可选 | 待扫描的池标签；应核对目标系统中的标签字节。 | 本插件 |
| `--min-size` | `-m` | 整数 | 0 | CLI 未声明必填；可选 | 筛选内存池块的最小大小，默认 0 字节。 | 本插件 |
| `--max-size` | `-M` | 整数 | 4096 | CLI 未声明必填；可选 | 筛选内存池块的最大大小，默认 4096 字节。 | 本插件 |
| `--paged` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 包含分页内存池搜索；默认不启用。 | 本插件 |

</details>

#### `pooltracker`

统计内存池标签分配与使用情况。适用场景：寻找异常资源使用，再把标签、地址与合法驱动对应。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `whitelist`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--tags` | `-t` | 字符串 | None | CLI 未声明必填；可选 | 待扫描的池标签；应核对目标系统中的标签字节。 | 本插件 |
| `--tagfile` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 池标签说明文件路径，用于解释标签归属。 | 本插件 |
| `--whitelist` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 应用内置标签白名单，仅显示第三方标签；第三方标签不等同恶意。 | 本插件 |
| `--show-free` | `-F` | 布尔标志 | False | CLI 未声明必填；可选 | 包含当前没有分配的池标签。 | 本插件 |

</details>

#### `printkey`

读取注册表键、子键和键值。适用场景：定位持久化或配置痕迹，关联 hive 与键时间而不把键值当行为执行证据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |
| `--key` | `-K` | 字符串 | None | CLI 未声明必填；可选 | 指定注册表键路径，省略时按插件默认逻辑显示根键。 | 本插件 |

</details>

#### `privs`

列出进程令牌特权及启用状态。适用场景：调查高权限上下文与特权变化，区分持有特权和实际使用特权。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--silent` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 减少插件认为信息量低的结果；应保留完整结果作对照。 | 本插件 |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅显示名称匹配正则表达式的特权。 | 本插件 |

</details>

#### `procdump`

恢复进程主 PE 可执行文件。适用场景：导出候选程序静态分析，核对 PE 头修复、缺页和内存/磁盘布局差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 恢复可执行文件的输出目录。 | 本插件 |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 导出 PE 时放宽部分结构检查；可能导出损坏或误识别的数据。 | 本插件 |
| `--memory` | `-m` | 布尔标志 | False | CLI 未声明必填；可选 | 按内存映像布局雕刻，而非默认可执行文件/磁盘布局。 | 本插件 |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 本插件 |

</details>

#### `pslist`

沿 EPROCESS 活动链表列出进程。适用场景：建立活动进程基线，与扫描、线程和多视图结果比较。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 在输出中显示对象的物理偏移，代替虚拟地址；不改变输入镜像字节。 | 本插件 |

</details>

#### `psscan`

扫描物理内存中的 EPROCESS 对象。适用场景：寻找已退出或脱链候选，核对时间、有效字段和地址空间。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `pstree`

显示 Windows 进程树。适用场景：重建启动关系并检查异常父子组合，结合启动时间和 PID 复用验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `psxview`

比较多种 Windows 进程枚举视图。适用场景：发现差异后排除退出、采集竞态、结构损坏和已知正常差异规则。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 指定物理对象偏移；结合当前插件的对象类型使用。 | 本插件 |
| `--apply-rules` | `-R` | 布尔标志 | False | CLI 未声明必填；可选 | 应用已知正常进程视图差异规则；规则可能隐藏异常，须保留未过滤对照。 | 本插件 |

</details>

#### `qemuinfo`

显示 QEMU 内存保存格式信息。适用场景：核对虚拟机采集容器、版本及内存块覆盖，定位装载问题。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `screenshot`

从 GDI 窗口对象重建桌面布局示意图。适用场景：理解窗口位置与会话关系；伪截图通常不恢复真实像素或完整屏幕内容。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `servicediff`

比较服务扫描结果与注册表服务记录。适用场景：调查内存服务和配置不一致，结合卸载、删除和采集时序排除正常差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `sessions`

枚举 Windows 会话空间及进程。适用场景：关联用户登录会话与 GUI 对象，区分会话编号、身份与进程归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `shellbags`

解析 ShellBags 注册表记录。适用场景：恢复资源管理器目录浏览线索，核对路径、时间来源和操作系统差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`body`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--machine` | — | 字符串 | 空字符串 | CLI 未声明必填；可选 | 给时间线添加机器标记；它是人工标签，不代表自动识别主机身份。 | 本插件 |

</details>

#### `shimcache`

解析应用兼容缓存记录。适用场景：建立程序路径和兼容处理线索；不同系统的缓存记录不能一律证明执行。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `shutdowntime`

读取注册表中的 ShutdownTime。适用场景：与事件日志和采集时间核对关机线索，注意更新语义及时间区。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |

</details>

#### `sockets`

遍历旧版 Windows 的活动套接字。适用场景：关联端口与进程，受支持系统上与连接扫描及抓包对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--physical-offset` | `-P` | 布尔标志 | False | CLI 未声明必填；可选 | 指定物理对象偏移；结合当前插件的对象类型使用。 | 本插件 |

</details>

#### `sockscan`

扫描旧版 Windows 套接字池对象。适用场景：寻找活动表外的套接字残留，核对字段和对象生命周期。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `ssdt`

读取系统服务描述符表与处理函数归属。适用场景：定位异常系统调用入口，结合架构、合法补丁和驱动范围验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `strings`

将物理偏移字符串关联到进程虚拟地址。适用场景：用带偏移的 strings 结果查归属，注意共享页和释放进程残留。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--string-file` | `-s` | 字符串 | None | CLI 未声明必填；需存在的 strings 文件 | 输入带物理偏移的 strings 结果文件；必须保留正确的偏移单位与基数。 | 本插件 |
| `--scan` | `-S` | 布尔标志 | False | CLI 未声明必填；可选 | 没有给出对象偏移时用 psscan 视图关联字符串，以纳入退出或脱链候选。 | 本插件 |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 本插件 |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |
| `--lookup-pid` | `-L` | 布尔标志 | False | CLI 未声明必填；可选 | 在字符串归属结果中查找 PID 对应的进程名。 | 本插件 |

</details>

#### `svcscan`

扫描服务对象和配置信息。适用场景：发现内存服务状态与路径，与注册表和服务日志互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `symlinkscan`

扫描内核符号链接对象。适用场景：调查设备名和路径映射线索，核对目标和正常设备配置。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `thrdscan`

扫描线程池对象。适用场景：补充活动线程链表之外的候选，核对进程关联与退出时间。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `threads`

联合线程扫描和活动结构调查线程。适用场景：通过标签筛选异常线程，结合入口地址、模块、状态和进程归属验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--filter` | `-F` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的标签筛选。 | 本插件 |
| `--listtags` | `-L` | 布尔标志 | False | CLI 未声明必填；可选 | 列出可用于线程筛选的标签。 | 本插件 |

</details>

#### `timeliner`

汇总多种内存对象的时间信息。适用场景：建立候选事件序列，区分创建、退出、键写入和映像编译时间等不同语义。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`body`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive` | `-H` | 字符串 | None | CLI 未声明必填；给定时 --type 须含 Registry | 筛选指定 hive 的注册表时间；须在 --type 中包含 Registry。 | 本插件 |
| `--user` | `-U` | 字符串 | None | CLI 未声明必填；给定时 --type 须含 Registry | 筛选指定用户 hive 的注册表时间；须在 --type 中包含 Registry。 | 本插件 |
| `--machine` | — | 字符串 | 空字符串 | CLI 未声明必填；可选 | 给时间线添加机器标记；它是人工标签，不代表自动识别主机身份。 | 本插件 |
| `--type` | — | 字符串 | 15 类对象；不含 Registry（详见共同规则） | CLI 未声明必填；可选 | 选择逗号分隔的时间线对象类型；默认列表不含 Registry，注册表时间须显式加入。 | 本插件 |

</details>

#### `timers`

列出内核定时器及 DPC 处理程序。适用场景：检查周期执行回调归属，排除正常驱动计时器。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--listhead` | `-L` | 整数 | None | CLI 未声明必填；可选 | 指定 nt!KiTimerTableListHead 的虚拟地址。 | 本插件 |

</details>

#### `truecryptmaster`

寻找 TrueCrypt 7.1a 主密钥相关结构。适用场景：授权恢复候选密钥，在隔离容器副本上验证，不能保证所有版本与驻留状态可恢复。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 导出密钥材料的目录；保存为授权分析材料。 | 本插件 |
| `--version` | `-T` | 字符串 | 7.1a | CLI 未声明必填；可选 | TrueCrypt 版本选择字符串，默认 7.1a；不能推定任意版本布局兼容。 | 本插件 |

</details>

#### `truecryptpassphrase`

扫描 TrueCrypt 缓存口令候选。适用场景：按最小长度筛选残留，再在隔离副本中验证；不展示真实口令。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--min-length` | `-M` | 整数 | 5 | CLI 未声明必填；可选 | 口令候选最小字符数；较短值可能增加误报。 | 本插件 |

</details>

#### `truecryptsummary`

汇总 TrueCrypt 相关进程、服务和设备线索。适用场景：判断是否有加密容器使用上下文，结合密钥候选与磁盘容器验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `unloadedmodules`

列出内核记录的已卸载模块。适用场景：补充历史驱动活动，注意记录槽有限、名称截断和时间范围。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `userassist`

解析 UserAssist 注册表记录。适用场景：关联用户界面程序使用线索，核对版本、计数与时间语义。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hive-offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定注册表 hive 的虚拟地址，与文件偏移或物理地址区分。 | 本插件 |

</details>

#### `userhandles`

枚举会话 USER 对象句柄。适用场景：检查窗口、钩子和菜单等 GUI 对象，结合对象类型与桌面进程验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 整数 | None | CLI 未声明必填；可选 | 按 PID 筛选；该声明为单个整数，不能照搬多 PID 字符串语法。 | 本插件 |
| `--type` | `-t` | 字符串 | None | CLI 未声明必填；可选 | 按 USER 句柄类型筛选。 | 本插件 |
| `--free` | `-F` | 布尔标志 | False | CLI 未声明必填；可选 | 包含空闲或已释放的 USER 句柄候选。 | 本插件 |

</details>

#### `vaddump`

按 VAD 区域导出进程内存。适用场景：定向保存异常映射，核对区域基址、权限、最大长度和缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 导出 VAD 内存区域的目录。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 仅导出给定十六进制 VAD 起始虚拟地址的区域。 | 本插件 |
| `--max-size` | `-M` | 长整数（Python 2） | 1073741824 | CLI 未声明必填；可选 | 限制处理或导出区域最大大小，默认 1 GiB；更大区域可能被跳过。 | 本插件 |

</details>

#### `vadinfo`

显示 VAD 的权限、映射与文件信息。适用场景：判断私有、映射与可执行区域，作为注入或模块检查的证据入口。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 本插件 |

</details>

#### `vadtree`

以树结构展示 VAD。适用场景：检查地址区间与树关系，结合 vadwalk 和映射内容判断结构差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 VADInfo |

</details>

#### `vadwalk`

遍历 VAD 并显示节点。适用场景：核对 VAD 链接和边界，为异常映射或结构损坏分析提供视图。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 VADInfo |

</details>

#### `vboxinfo`

显示 VirtualBox 内存保存容器信息。适用场景：确认容器元数据与内存块覆盖，定位地址空间装载限制。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `verinfo`

读取内存 PE 的版本资源。适用场景：核对模块产品名、公司和版本线索，结合哈希和签名排除伪造资源。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 恢复可执行文件的输出目录。 | 继承 ProcDump |
| `--unsafe` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 导出 PE 时放宽部分结构检查；可能导出损坏或误识别的数据。 | 继承 ProcDump |
| `--memory` | `-m` | 布尔标志 | False | CLI 未声明必填；可选 | 按内存映像布局雕刻，而非默认可执行文件/磁盘布局。 | 继承 ProcDump |
| `--fix` | `-x` | 布尔标志 | False | CLI 未声明必填；可选 | 把导出 PE 的 ImageBase 修正为内存加载基址；保留未修正对照以解释差异。 | 继承 ProcDump |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定待读取版本资源的模块地址；地址层次以该插件实现为准。 | 本插件 |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅导出名称匹配正则表达式的内核模块。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 模块名正则匹配忽略大小写。 | 本插件 |

</details>

#### `vmwareinfo`

显示 VMware VMSS/VMSN 元数据，可导出相关数据。适用场景：核对虚拟机保存状态与内存布局，记录容器及伴随文件关系。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 保存 GDI 桌面布局示意图的目录。 | 本插件 |

</details>

#### `volshell`

在 Windows 镜像地址空间中交互检查。适用场景：只读核验 EPROCESS、结构与字节，交互输出不能等同统一结构化表。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定内核虚拟地址空间中的 EPROCESS 地址，使用十六进制。 | 本插件 |
| `--imname` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名选择交互检查上下文。 | 本插件 |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |

</details>

#### `win10cookie`

定位 Windows 10 的 ObHeaderCookie。适用场景：为对象头解码提供正确参数，结合目标构建及多个对象验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `windows`

显示桌面窗口的详细信息。适用场景：关联标题、类、句柄与进程，为 GUI 文本和窗口布局解释提供依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`block`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |

</details>

#### `wintree`

按窗口 Z 顺序显示桌面树。适用场景：理解前后窗口与父子关系，核对会话和桌面对象有效性。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`block`, `dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `wndscan`

扫描窗口站对象。适用场景：活动窗口站链表不完整时补充会话及桌面线索。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--virtual` | `-V` | 布尔标志 | False | CLI 未声明必填；可选 | 从虚拟/内核空间扫描，代替默认物理空间扫描。 | 继承 AbstractScanCommand |
| `--show-unallocated` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过对象类型校验以纳入未分配对象候选；实际设置 skip_type_check，并非排除未分配对象。 | 继承 AbstractScanCommand |
| `--start` | `-A` | 整数 | None | CLI 未声明必填；可选 | 扫描起始地址；其地址层次随物理/虚拟扫描模式而定。 | 继承 AbstractScanCommand |
| `--length` | `-G` | 整数 | None | CLI 未声明必填；可选 | 从起始地址起扫描的字节数，用于限制扫描范围。 | 继承 AbstractScanCommand |

</details>

#### `yarascan`

用 YARA 扫描 Windows 进程或内核内存。适用场景：以自有规则定位候选字节，再结合进程、映射和上下文排除误报。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 同时扫描进程与内核空间；扩大范围会增加耗时和重复命中。 | 本插件 |
| `--case` | `-C` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则搜索时忽略大小写。 | 本插件 |
| `--kernel` | `-K` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描内核模块/内核地址空间，而非默认进程范围。 | 本插件 |
| `--wide` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则包含宽字符匹配。 | 本插件 |
| `--yara-rules` | `-Y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 直接提供 YARA 字符串规则表达式；核对生成规则、转义与误报。 | 本插件 |
| `--yara-file` | `-y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 提供本地 YARA 规则文件；验证规则语法和所需模块。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 恢复文件的输出目录。 | 本插件 |
| `--size` | `-s` | 整数 | 256 | CLI 未声明必填；可选 | 命中点十六进制预览的字节数；默认 256。 | 本插件 |
| `--reverse` | `-R` | 整数 | 0 | CLI 未声明必填；可选 | 向命中点之前回退指定字节数作为显示或导出起点；不是字节顺序反转。 | 本插件 |
| `--max-size` | `-M` | 长整数（Python 2） | 1073741824 | CLI 未声明必填；可选 | 限制处理或导出区域最大大小，默认 1 GiB；更大区域可能被跳过。 | 本插件 |

</details>

</details>

### Linux 命令（72 项）

<details>
<summary>展开 Volatility 2 Linux 内置插件目录（72 项）</summary>

#### `limeinfo`

读取 LiME 容器的物理地址分段。适用场景：确认 Linux 采集区间、空洞和格式，为 raw 转换与地址解释提供依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_apihooks`

检查 Linux 用户态函数钩子。适用场景：核对跳转目标、映射归属和正常库基线，排除插桩或性能分析工具。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_arp`

读取内核 ARP 缓存。适用场景：关联局域网 IP 与链路层地址；缓存残留不能独立证明连接或攻击者身份。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_aslr_shift`

推定 Linux 内核地址随机化偏移。适用场景：profile 符号不能直接定位时计算物理与虚拟偏移，再以多个内核对象验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_banner`

读取 Linux 内核 banner。适用场景：识别内核版本线索，仍须以匹配编译配置和符号的 profile 验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_bash`

恢复 Bash 历史条目。适用场景：寻找会话命令与历史时间；输入残留不等于执行成功或唯一操作者。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--printunalloc` | `-P` | 布尔标志 | None | CLI 未声明必填；可选 | 包含未分配历史条目；输出可能很大且误报增加。 | 本插件 |
| `--history_list` | `-H` | 长整数（Python 2） | None | CLI 未声明必填；可选 | 指定 Bash history_list 的内存地址，用于目标版本无法自动定位时的手工校准。 | 本插件 |
| `--scan_all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描所有进程，代替仅选择名称为 bash 的进程；增加耗时和误报。 | 本插件 |

</details>

#### `linux_bash_env`

恢复 Bash 动态环境变量。适用场景：补充 shell 会话路径与运行环境，和静态启动环境对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_bash_hash`

恢复 Bash 命令路径缓存表。适用场景：判断命令名可能解析到哪些路径，不能把缓存项当一次执行记录。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--scan_all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描所有进程，代替仅选择名称为 bash 的进程；增加耗时和误报。 | 本插件 |

</details>

#### `linux_check_afinfo`

检查网络协议操作函数指针。适用场景：发现回调落到未知模块的协议结构，结合内核模块与合法扩展验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_creds`

检查进程共享凭据结构的情况。适用场景：发现异常凭据共享后结合线程、克隆关系和权限变化排除正常共享。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_check_evt_arm`

检查 ARM 异常向量表。适用场景：调查异常入口被改写的线索，必须使用支持目标 ARM 内核的 profile。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_fop`

检查文件操作结构的函数指针。适用场景：定位可疑 file_operations 或指定 inode，和路径、模块地址范围互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--inode` | `-i` | 整数 | None | CLI 未声明必填；可选 | 指定待检查文件操作指针的 inode 地址。 | 本插件 |

</details>

#### `linux_check_idt`

检查 Linux 中断描述符表。适用场景：排查指向未知处理程序的入口，结合架构和内核基线验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_inline_kernel`

检查内核函数内联跳转钩子。适用场景：寻找代码开头的异常跳转或补丁，排除合法热补丁与调试组件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_modules`

比较内核模块链表与 sysfs 模块信息。适用场景：发现列表差异后检查残留对象和采集一致性，避免直接归因为隐藏模块。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_syscall`

检查 Linux 系统调用表。适用场景：定位系统调用入口的异常模块归属，结合符号与内核版本验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_syscall_arm`

检查 ARM Linux 系统调用表。适用场景：在适配 ARM 的 profile 中检查入口归属，不套用 x86 表布局。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_check_tty`

检查 TTY 操作指针。适用场景：排查终端处理链中的异常回调，结合终端会话与内核模块验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_cpuinfo`

读取活动处理器信息。适用场景：核对架构、处理器与镜像环境，辅助 profile 选择和一致性检查。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_dentry_cache`

枚举 dentry slab 缓存中的目录项。适用场景：补充文件名和路径残留，与 inode、挂载点及文件内容核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--unallocated` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 包含 slab 缓存中未分配或已释放的对象；须区分残留与活动对象。 | 本插件 |

</details>

#### `linux_dmesg`

恢复内核环形日志。适用场景：寻找设备、模块与异常日志线索，注意环形覆盖与时间基准。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_dump_map`

导出选定进程映射。适用场景：对指定 VMA 恢复内存字节，核对映射边界、缺页和权限后静态分析。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--vma` | `-s` | 长整数（Python 2） | None | CLI 未声明必填；可选 | 只处理给定起始虚拟地址的 VMA。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `linux_dynamic_env`

恢复进程动态环境变量。适用场景：检查会话中后续修改的运行环境，与 linux_psenv 的启动环境对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_elfs`

发现进程映射中的 ELF 对象。适用场景：定位可执行文件和共享库，比较文件头、映射路径与导出的字节。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_enumerate_files`

枚举文件系统缓存引用的文件。适用场景：寻找缓存路径和对象关系，作为恢复文件或调查删除痕迹的入口。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_find_file`

按路径或 inode 查找并恢复缓存文件。适用场景：先列举有效 inode 再导出内容，核对缓存页不足导致的不完整恢复。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--find` | `-F` | 字符串 | None | CLI 未声明必填；可选 | 查找的文件路径，用缓存对象验证路径归属。 | 本插件 |
| `--inode` | `-i` | 整数 | None | CLI 未声明必填；可选 | 指定待恢复文件的 inode 地址；先用枚举结果验证对象。 | 本插件 |
| `--outfile` | `-O` | 字符串 | None | CLI 未声明必填；可选 | 恢复文件的输出路径。 | 本插件 |
| `--listfiles` | `-L` | 整数；重复累计 | None | CLI 未声明必填；可选 | 列举缓存文件；这是 count 动作，重复标志会累计数值。 | 本插件 |

</details>

#### `linux_getcwd`

读取进程当前工作目录。适用场景：解释相对路径命令与文件访问，注意进程目录已变化的可能。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_hidden_modules`

雕刻内存中的模块结构。适用场景：活动模块链表外发现候选后，核对结构、地址和 sysfs 证据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_ifconfig`

读取网络接口与地址配置。适用场景：重建采集时网络环境，与路由、连接及抓包对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_info_regs`

读取线程保存的寄存器状态。适用场景：定位执行上下文和栈指针，结合映射及反汇编分析异常线程。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_iomem`

读取类似 /proc/iomem 的资源映射。适用场景：识别 RAM、设备与保留区，解释物理采集空洞和扫描边界。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_kernel_opened_files`

列出内核持有的打开文件。适用场景：发现不由普通用户进程句柄解释的文件使用，关联模块及路径。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_keyboard_notifiers`

枚举键盘通知回调链。适用场景：检查输入监控回调归属，排除正常输入法和辅助功能。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_ldrmodules`

比较进程映射与动态加载器库列表。适用场景：寻找脱链库或匿名可执行映射，与 ELF 内容和正常加载差异互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_library_list`

读取动态加载器中的库记录。适用场景：建立共享库链表基线，与 proc_maps 对照隐藏或残留映射。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_librarydump`

恢复进程共享库的 ELF 字节。适用场景：按基址导出可疑库，核对可读映射与缺页后作静态分析。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |

</details>

#### `linux_list_raw`

列出持有 RAW/PACKET 类套接字的应用。适用场景：寻找抓包或特殊网络操作线索；RAW 套接字本身不证明混杂模式或恶意行为。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_lsmod`

列出内核模块，可附参数与节区。适用场景：核对模块基址、大小和参数，与隐藏模块、sysfs 和导出文件对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--sections` | `-T` | 布尔标志 | None | CLI 未声明必填；可选 | 显示内核模块各节区地址。 | 本插件 |
| `--params` | `-P` | 布尔标志 | None | CLI 未声明必填；可选 | 显示内核模块参数；目标 profile 必须提供相应结构支持。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |
| `--idc` | `-c` | 字符串 | None | CLI 未声明必填；可选 | 为模块生成 IDC 辅助文件的路径；用于离线反汇编标注。 | 本插件 |

</details>

#### `linux_lsof`

列出进程文件描述符及路径。适用场景：关联进程与文件、管道和套接字，补充文件访问和通信上下文。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_malfind`

定位可疑进程映射并显示字节或反汇编。适用场景：对异常权限或匿名代码区进一步导出与比对，不能仅凭权限判定注入。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_memmap`

列出进程虚拟页到物理页映射。适用场景：判断哪些页面可从镜像恢复，并定位字符串或代码的物理归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_moddump`

恢复已加载内核模块。适用场景：导出指定基址或名称的模块，核对重定位、缺页和原始文件差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 恢复文件的输出目录。 | 本插件 |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅导出名称匹配正则表达式的内核模块。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 正则表达式匹配时忽略大小写。 | 本插件 |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |

</details>

#### `linux_mount`

遍历活动挂载信息。适用场景：重建文件系统和设备关系，解释路径与缓存 inode 的归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_mount_cache`

从 slab 缓存寻找挂载结构。适用场景：补充活动链表之外的挂载残留，与 linux_mount 比较。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--unallocated` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 包含 slab 缓存中未分配或已释放的对象；须区分残留与活动对象。 | 本插件 |

</details>

#### `linux_netfilter`

列出 Netfilter 钩子。适用场景：检查包过滤回调归属和顺序，结合合法防火墙模块排除正常配置。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_netscan`

从内存雕刻连接结构。适用场景：活动套接字列表不完整时寻找端点残留，结合进程映射及其他证据验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_netstat`

遍历进程打开的套接字。适用场景：关联进程与网络端点和状态，注意连接状态为采集瞬间或残留。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--ignore_unix` | `-U` | 布尔标志 | None | CLI 未声明必填；可选 | 忽略 Unix 域套接字，仅保留其他套接字类型。 | 本插件 |

</details>

#### `linux_pidhashtable`

从 PID 哈希表枚举进程。适用场景：与 task 链表及扫描视图对照，发现结构差异和潜在脱链进程。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_pkt_queues`

导出进程套接字收发队列数据。适用场景：恢复尚在队列中的包片段，与端点和外部抓包核对边界。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--ignore_unix` | `-U` | 布尔标志 | None | CLI 未声明必填；可选 | 忽略 Unix 域套接字，仅保留其他套接字类型。 | 继承 linux_netstat |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 恢复网络包的输出目录。 | 本插件 |

</details>

#### `linux_plthook`

检查 ELF PLT 槽的目标归属。适用场景：发现导入跳转落到非依赖映像时核对加载器状态、预加载和合法插桩。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--all` | `-a` | 布尔标志 | False | CLI 未声明必填；可选 | 显示所有 PLT 槽，包括没有被标为钩子的槽，便于完整对照。 | 本插件 |
| `--ignore` | — | 字符串；可重复追加 | [] | CLI 未声明必填；可选 | 忽略给定路径支持的映射；可重复指定，用于排除已解释的 PLT 差异。 | 本插件 |

</details>

#### `linux_proc_maps`

遍历进程内存映射。适用场景：建立 VMA 的地址、权限与路径基线，支持库检查和区域导出。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_proc_maps_rb`

从映射红黑树读取 VMA。适用场景：与链表视图比较，排查链表损坏、采集竞态或隐藏映射。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_procdump`

恢复进程主可执行 ELF。适用场景：对候选进程导出可恢复映射，验证 ELF 结构和缺页情况。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `linux_process_hollow`

把内存 ELF 函数字节与已知良好文件比较。适用场景：指定目标基址及可信参考副本，定位差异并排除重定位、补丁和缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--base` | `-b` | 长整数（Python 2） | None | CLI 未声明必填；比较必填 | 被比较 ELF 的内存基址，通常是进程 VMA 起始虚拟地址。 | 本插件 |
| `--path` | `-P` | 字符串 | None | CLI 未声明必填；比较必填 | 用于字节比较的可信参考 ELF 文件路径。 | 本插件 |

</details>

#### `linux_psaux`

列出进程完整命令行与启动时间。适用场景：关联命令参数、进程链和其他时间线，核对参数可变与残留限制。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_psenv`

读取进程静态启动环境。适用场景：检查启动时的路径和变量，与动态环境恢复结果互证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_pslist`

从 task_struct 活动链表枚举进程。适用场景：建立活动进程基线，和 PID 哈希、slab 与物理扫描视图比较。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |

</details>

#### `linux_pslist_cache`

从 task_struct slab 缓存枚举进程对象。适用场景：发现活动链表外的任务候选，区分已释放残留与隐藏进程。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |
| `--unallocated` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 包含 slab 缓存中未分配或已释放的对象；须区分残留与活动对象。 | 本插件 |

</details>

#### `linux_psscan`

从物理内存扫描进程结构。适用场景：补充链表遍历结果，必须核对结构有效性和对象生命周期。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_pstree`

显示进程父子关系。适用场景：重建启动链，结合 PID 复用、命令行和启动时间避免错误关联。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_psxview`

比较多种 Linux 进程枚举视图。适用场景：发现视图差异后检查退出、采集竞态、损坏与脱链可能。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_recover_filesystem`

恢复内存缓存中的文件系统内容。适用场景：导出可恢复文件到隔离目录，记录稀疏页、缺页与路径不完整。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `linux_route_cache`

读取路由缓存。适用场景：关联历史网络目的地与路由线索；缓存不等于一条已成功建立的会话。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--resolve` | `-R` | 整数；重复累计 | None | CLI 未声明必填；可选 | 对远端地址进行 DNS 名称解析；严格离线分析时不启用此参数。 | 本插件 |

</details>

#### `linux_sk_buff_cache`

从 sk_buff slab 缓存恢复包数据。适用场景：寻找活动队列之外的包残留，与协议头、长度和抓包核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--unallocated` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 包含 slab 缓存中未分配或已释放的对象；须区分残留与活动对象。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 恢复网络包的输出目录。 | 本插件 |

</details>

#### `linux_slabinfo`

列出 slab 缓存统计。适用场景：识别对象缓存数量与布局，为缓存扫描和异常内核分配调查提供依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `linux_strings`

把物理偏移字符串关联到进程虚拟地址。适用场景：使用带偏移的字符串结果定位归属；同一物理页可能被多进程共享。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--string-file` | `-s` | 字符串 | None | CLI 未声明必填；需存在的 strings 文件 | 输入带物理偏移的 strings 结果文件；必须保留正确的偏移单位与基数。 | 继承 Strings |
| `--scan` | `-S` | 布尔标志 | False | CLI 未声明必填；可选 | 没有给出对象偏移时用 psscan 视图关联字符串，以纳入退出或脱链候选。 | 继承 Strings |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 Strings |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 Strings |
| `--lookup-pid` | `-L` | 布尔标志 | False | CLI 未声明必填；可选 | 在字符串归属结果中查找 PID 对应的进程名。 | 继承 Strings |

</details>

#### `linux_threads`

枚举进程线程。适用场景：核对线程 ID、执行上下文及进程关系，补充异常执行调查。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_tmpfs`

列出 tmpfs 超级块并恢复缓存文件。适用场景：先选有效超级块再恢复临时文件，核对内存驻留和缺页限制。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 恢复缓存文件的输出目录。 | 本插件 |
| `--sb` | `-S` | 整数 | None | CLI 未声明必填；可选 | 选择要恢复的 tmpfs 超级块编号，先用 -L 列表确定有效编号。 | 本插件 |
| `--list_sbs` | `-L` | 布尔标志 | None | CLI 未声明必填；可选 | 列出可供选择的 tmpfs 超级块。 | 本插件 |

</details>

#### `linux_truecrypt_passphrase`

寻找 TrueCrypt 缓存口令候选。适用场景：授权检查加密容器解密材料，必须在隔离副本上验证候选而不展示真实口令。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 linux_pslist |

</details>

#### `linux_vma_cache`

从 vm_area_struct slab 缓存恢复 VMA。适用场景：比较活动映射与缓存残留，不能把释放 VMA 当采集时有效映射。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--unallocated` | `-u` | 布尔标志 | False | CLI 未声明必填；可选 | 包含 slab 缓存中未分配或已释放的对象；须区分残留与活动对象。 | 本插件 |

</details>

#### `linux_volshell`

在 Linux 镜像地址空间中提供交互检查。适用场景：对结构、地址和字节做受控只读核验；交互命令不能概括为可统一表格导出。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定内核虚拟地址空间中的 EPROCESS 地址，使用十六进制。 | 继承 volshell |
| `--imname` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名选择交互检查上下文。 | 继承 volshell |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 volshell |

</details>

#### `linux_yarascan`

用 YARA 规则扫描 Linux 进程或内核内存。适用场景：用自有规则定位候选字节，再通过映射、上下文与规则误报分析验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 同时扫描进程与内核空间；扩大范围会增加耗时和重复命中。 | 继承 YaraScan |
| `--case` | `-C` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则搜索时忽略大小写。 | 继承 YaraScan |
| `--kernel` | `-K` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描内核模块/内核地址空间，而非默认进程范围。 | 继承 YaraScan |
| `--wide` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则包含宽字符匹配。 | 继承 YaraScan |
| `--yara-rules` | `-Y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 直接提供 YARA 字符串规则表达式；核对生成规则、转义与误报。 | 继承 YaraScan |
| `--yara-file` | `-y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 提供本地 YARA 规则文件；验证规则语法和所需模块。 | 继承 YaraScan |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 恢复文件的输出目录。 | 继承 YaraScan |
| `--size` | `-s` | 整数 | 256 | CLI 未声明必填；可选 | 命中点十六进制预览的字节数；默认 256。 | 继承 YaraScan |
| `--reverse` | `-R` | 整数 | 0 | CLI 未声明必填；可选 | 向命中点之前回退指定字节数作为显示或导出起点；不是字节顺序反转。 | 继承 YaraScan |
| `--max-size` | `-M` | 长整数（Python 2） | 1073741824 | CLI 未声明必填；可选 | 限制处理或导出区域最大大小，默认 1 GiB；更大区域可能被跳过。 | 继承 YaraScan |

</details>

</details>

### macOS 命令（77 项）

<details>
<summary>展开 Volatility 2 macOS 内置插件目录（77 项）</summary>

#### `mac_adium`

恢复 Adium 进程中的消息残留。适用场景：在适配应用版本的内存中寻找消息片段，与会话、编码和外部记录核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；写出提取物时需目录；查看模式以插件为准 | 结果输出目录。 | 本插件 |
| `--wide` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | 应用文本搜索使用宽字符模式。 | 本插件 |

</details>

#### `mac_apihooks`

检查 macOS 用户态 API 钩子。适用场景：定位异常跳转及目标映射，排除合法插桩和应用补丁。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_apihooks_kernel`

检查系统调用和内核或 kext 函数钩子。适用场景：对选定符号表中的代码检查异常跳转，结合版本、扩展与合法补丁验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--checkkexts` | `-X` | 布尔标志 | False | CLI 未声明必填；可选 | 检查 kext 与内核符号表中的函数钩子；扩大覆盖也增加耗时和合法补丁候选。 | 本插件 |
| `--checkkernel` | `-K` | 布尔标志 | False | CLI 未声明必填；可选 | 仅检查内核符号表函数的钩子。 | 本插件 |

</details>

#### `mac_arp`

读取 ARP 缓存。适用场景：补充局域网端点关系，与接口配置和抓包对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_bash`

恢复 macOS Bash 历史。适用场景：寻找会话命令残留，结合进程及时间证据而不推定执行成功。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--scan_all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描所有进程，代替仅选择名称为 bash 的进程；增加耗时和误报。 | 本插件 |

</details>

#### `mac_bash_env`

恢复 Bash 动态环境变量。适用场景：还原 shell 会话的路径与运行上下文，与启动环境对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_bash_hash`

恢复 Bash 命令路径缓存。适用场景：检查命令名解析路径；缓存项不能直接当执行事件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--scan_all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描所有进程，代替仅选择名称为 bash 的进程；增加耗时和误报。 | 本插件 |

</details>

#### `mac_calendar`

恢复 Calendar.app 的事件残留。适用场景：寻找日程片段，核对应用版本、时间区和相关数据库记录。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_check_fop`

检查文件操作函数指针。适用场景：发现指向未知模块的 VFS 回调后，结合 kext 与符号验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_check_mig_table`

列出内核 MIG 消息接口表。适用场景：检查 Mach IPC 处理入口归属，核对正常内核符号和扩展。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_check_syscall_shadow`

寻找影子系统调用表线索。适用场景：对候选表核对入口、地址引用与正常表，避免仅凭相似布局下结论。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_check_syscalls`

检查系统调用表入口。适用场景：可用目标头文件映射调用名，检查处理地址归属并排除版本差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--syscall-indexes` | `-i` | 字符串 | None | CLI 未声明必填；可选 | 目标系统对应 unistd 头文件路径，用于系统调用编号到名称的映射。 | 本插件 |

</details>

#### `mac_check_sysctl`

检查 sysctl 处理回调。适用场景：定位未知处理程序，结合 kext 和合法系统配置验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_check_trap_table`

检查 Mach trap 表入口。适用场景：核对 trap 处理函数归属，调查异常内核跳转线索。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_compressed_swap`

读取 VM compressor 统计并恢复压缩页。适用场景：分析压缩内存可恢复性；统计、解压测试与写出阶段分开记录。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--skip-writing` | `-t` | 布尔标志 | False | CLI 未声明必填；可选 | 不写出解压页，只显示统计并验证解压。 | 本插件 |

</details>

#### `mac_contacts`

恢复 Contacts.app 的联系人名称残留。适用场景：检查字符串与对象上下文，和联系人数据库副本核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_dead_procs`

扫描已经释放的进程对象。适用场景：补充已退出进程线索，区分残留数据与采集时活动进程。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_dead_sockets`

扫描已经释放的套接字对象。适用场景：寻找历史端点残留，结合有效结构与外部网络证据验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_dead_vnodes`

扫描已经释放的 vnode。适用场景：恢复文件名或路径线索，不能把残留 vnode 当当前打开文件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_devfs`

检查设备文件对应的字符设备操作回调。适用场景：把设备 vnode 映射到 cdevsw 处理函数，核对异常驱动归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_dmesg`

恢复内核调试日志缓冲区。适用场景：寻找启动、设备或异常日志，注意环形覆盖和时间信息不足。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_dump_file`

按 vnode 地址恢复指定缓存文件。适用场景：由 mac_list_files 获取对象地址，核对导出页范围与文件完整性。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--file-offset` | `-q` | 整数 | None | CLI 未声明必填；恢复指定文件时需要 | 指定 mac_list_files 给出的 vnode 虚拟地址；不是文件数据偏移。 | 本插件 |
| `--outfile` | `-O` | 字符串 | None | CLI 未声明必填；恢复指定文件时需要 | 恢复文件的输出路径。 | 本插件 |

</details>

#### `mac_dump_maps`

导出进程映射，可包含压缩内存页。适用场景：指定映射或进程输出内存副本，记录压缩页解压失败与缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--map-address` | `-s` | 长整数（Python 2） | None | CLI 未声明必填；可选 | 仅导出给定起始虚拟地址的映射。 | 本插件 |
| `--outputfile` | `-O` | 字符串 | None | CLI 未声明必填；导出必填；拒绝覆盖既有文件 | 恢复数据的输出文件路径。 | 本插件 |
| `--decompress-swap` | — | 布尔标志 | False | CLI 未声明必填；可选 | 同时解压压缩内存中的页面；恢复结果仍受压缩槽与页面完整性限制。 | 本插件 |
| `--only-decompressed-swap` | — | 布尔标志 | False | CLI 未声明必填；可选 | 仅写出成功解压的压缩内存页，跳过其他页面。 | 本插件 |
| `--skip-writing` | `-t` | 布尔标志 | False | CLI 未声明必填；可选 | 不写出页面，只显示统计，并按其他选项测试解压。 | 本插件 |

</details>

#### `mac_dyld_maps`

从 dyld 结构读取映像映射。适用场景：与内核 proc_maps 比较加载库记录，发现脱链、残留或采集竞态。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_find_aslr_shift`

推定 macOS 10.8+ 的内核随机化偏移。适用场景：符号地址不可直接使用时求偏移，以多个内核对象复核。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_get_profile`

检测镜像中的 macOS profile 候选。适用场景：先匹配已安装 profile，再用内核版本和对象解析结果确认。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_ifconfig`

列出网络接口信息。适用场景：还原接口、地址和链路层配置，与路由和连接视图核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_interest_handlers`

列出 IOKit interest 回调。适用场景：检查设备兴趣通知处理函数的模块归属，排除合法设备扩展。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_ip_filters`

检查 IP 过滤回调。适用场景：定位异常网络过滤处理程序，结合合法防火墙与 kext 验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 mac_lsmod |

</details>

#### `mac_kernel_classes`

列出内核已加载 C++ 类。适用场景：辅助解释 IOKit 对象与扩展加载关系，与模块和符号核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_kevents`

枚举进程的 kqueue/kevent knote 订阅。适用场景：检查文件、进程等事件监听关系；它并非普通进程树命令。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

结果的核心对象为 knote 事件订阅，应检查过滤类型、标识、标志及订阅进程，不按进程树解释。

</details>

#### `mac_keychaindump`

寻找可能的 keychain 解密密钥。适用场景：授权核验密钥候选，再与对应 keychain 文件离线验证；候选不等于已成功解密。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_ldrmodules`

比较内核映射与 dyld 库列表。适用场景：寻找加载记录差异，结合 Mach-O 与映射权限验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_librarydump`

恢复进程映射中的 Mach-O 库。适用场景：按库基址导出可恢复字节，检查 Mach-O 布局和缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_list_files`

枚举文件缓存 vnode 及路径。适用场景：为指定文件恢复提供 vnode 地址，注意孤立节点与不完整路径。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--show_orphans` | `-s` | 布尔标志 | False | CLI 未声明必填；可选 | 包含没有可解析父节点的孤立 vnode；路径可能不完整。 | 本插件 |

</details>

#### `mac_list_kauth_listeners`

列出 Kauth 授权监听器。适用场景：检查授权回调归属，排除合法安全产品与系统扩展。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_list_kauth_scopes`

列出 Kauth 授权域及状态。适用场景：建立授权机制基线，与监听器和相关 kext 对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_list_raw`

列出持有 RAW 类套接字的应用。适用场景：寻找特殊网络访问线索，不单凭套接字类型推定混杂抓包或恶意行为。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_list_sessions`

枚举用户会话结构。适用场景：关联进程、登录会话和桌面上下文，核对残留结构。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_list_zones`

列出活动内核 zone 分配器。适用场景：理解对象缓存布局，为释放对象扫描与内核分配调查提供依据。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_lsmod`

遍历已加载内核扩展。适用场景：建立 kext 基线，与 IOKit、kext_map 和扫描视图对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 本插件 |

</details>

#### `mac_lsmod_iokit`

从 IOKit 视图枚举内核扩展。适用场景：与常规模块列表比较，查找加载记录差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_lsmod_kext_map`

从 kext_map 枚举内核扩展。适用场景：通过另一映射视图核对基址、大小与模块归属。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 mac_lsmod |

</details>

#### `mac_lsof`

列出进程打开的文件。适用场景：关联应用与文件、管道、设备和套接字，结合缓存内容验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_machine_info`

读取镜像的机器与内核信息。适用场景：核对平台和采集环境，辅助 profile 与地址偏移检查。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_malfind`

定位可疑进程映射。适用场景：对异常可执行映射显示字节并进一步导出，排除 JIT 和正常匿名代码。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_memdump`

导出进程可寻址内存页。适用场景：保存指定进程的内存副本，记录页表覆盖和缺页限制。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_moddump`

导出指定内核扩展。适用场景：恢复 kext 进行静态比对，核对内存布局、重定位及不完整页面。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--base` | `-b` | 整数 | None | CLI 未声明必填；可选 | 导出指定十六进制内核基址的驱动。 | 本插件 |
| `--regex` | `-r` | 字符串 | None | CLI 未声明必填；可选 | 仅导出名称匹配正则表达式的内核模块。 | 本插件 |
| `--ignore-case` | `-i` | 布尔标志 | False | CLI 未声明必填；可选 | 正则表达式匹配时忽略大小写。 | 本插件 |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_mount`

列出已挂载设备和文件系统。适用场景：重建路径与缓存文件归属，结合磁盘或采集记录验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_netstat`

枚举进程的活动网络连接。适用场景：关联进程、端点和协议，与内核连接列表和抓包交叉核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_network_conns`

从内核网络结构枚举连接。适用场景：补充不依赖进程描述符的连接视图，验证端点与对象有效性。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_notesapp`

恢复 Notes.app 消息内容残留。适用场景：检查应用内存中的文本片段，结合编码和数据库副本验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_notifiers`

检查 IOKit 通知回调。适用场景：调查设备通知链的异常模块归属，不能把任意第三方回调直接归为 rootkit。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 mac_lsmod |

</details>

#### `mac_orphan_threads`

列出无法对应正常进程或模块的线程线索。适用场景：核对线程入口、栈和退出状态，排除采集竞态与合法内核线程。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_pgrp_hash_table`

从进程组哈希表枚举进程。适用场景：与活动进程链表和 PID 哈希表比较，检查结构差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_pid_hash_table`

从 PID 哈希表枚举进程。适用场景：与 pslist、tasks 及扫描视图交叉验证，避免单视图遗漏。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_print_boot_cmdline`

读取内核启动参数。适用场景：解释安全、调试或硬件启动选项，结合配置和日志核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_proc_maps`

遍历进程内存映射。适用场景：建立地址、权限和路径基线，为导出及加载器对比定位区域。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_procdump`

恢复进程主 Mach-O 可执行文件。适用场景：导出候选程序静态分析，核对结构、重定位与缺页。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_psaux`

读取进程用户态参数。适用场景：重建启动命令与进程链，注意 argv 可被修改或不可读。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_psenv`

读取进程用户态环境变量。适用场景：核对启动上下文和路径线索，与 shell 动态环境比较。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_pslist`

遍历活动进程列表。适用场景：建立 macOS 进程基线，与 tasks、哈希表和释放对象视图核对。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 本插件 |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 本插件 |

</details>

#### `mac_pstree`

显示 macOS 进程父子关系。适用场景：重建启动链，结合启动时间、参数与 PID 复用验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_psxview`

比较多种 macOS 进程枚举视图。适用场景：发现视图差异后分析退出、损坏、采集竞态或脱链可能。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_recover_filesystem`

恢复内存缓存中的文件系统。适用场景：保存缓存可恢复内容，核对缺页、孤立路径与原始文件大小。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；执行导出分支时需有效目录 | 结果输出目录。 | 本插件 |

</details>

#### `mac_route`

读取路由表。适用场景：还原采集时路由环境，与接口和网络端点对照。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_socket_filters`

检查 socket 过滤器及回调。适用场景：调查套接字监控或过滤模块，排除正常安全与网络软件。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 mac_lsmod |

</details>

#### `mac_strings`

把物理字符串偏移关联到进程虚拟地址。适用场景：定位字符串归属及共享页，结合映射验证上下文。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--string-file` | `-s` | 字符串 | None | CLI 未声明必填；需存在的 strings 文件 | 输入带物理偏移的 strings 结果文件；必须保留正确的偏移单位与基数。 | 继承 Strings |
| `--scan` | `-S` | 布尔标志 | False | CLI 未声明必填；可选 | 没有给出对象偏移时用 psscan 视图关联字符串，以纳入退出或脱链候选。 | 继承 Strings |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 Strings |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 Strings |
| `--lookup-pid` | `-L` | 布尔标志 | False | CLI 未声明必填；可选 | 在字符串归属结果中查找 PID 对应的进程名。 | 继承 Strings |

</details>

#### `mac_tasks`

从内核 task 结构枚举活动任务。适用场景：与 BSD 进程列表比较，补充多视图进程调查。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_threads`

列出进程线程及执行信息。适用场景：核对线程上下文和映射归属，支持异常执行分析。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_threads_simple`

列出线程启动时间、优先级等概要。适用场景：快速筛选异常线程，再用完整线程与寄存器上下文验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 mac_pslist |
| `--task` | `-T` | 字符串 | None | CLI 未声明必填；可选 | 使用 mac_psxview 给出的进程对象虚拟地址选择目标。 | 继承 mac_pslist |

</details>

#### `mac_timers`

列出内核驱动设置的定时器。适用场景：检查到期回调与 kext 归属，排除正常驱动调度。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_trustedbsd`

检查 TrustedBSD 策略及回调。适用场景：核对策略来源和处理地址，不能把第三方策略直接等同恶意策略。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--addr` | `-a` | 整数 | None | CLI 未声明必填；可选 | 仅显示位于或包含该虚拟地址的 VAD。 | 继承 mac_lsmod |

</details>

#### `mac_version`

读取 macOS 内核版本信息。适用场景：为 profile 与编译版本匹配提供线索，再用结构解析确认。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_vfsevents`

列出接收文件系统事件的进程。适用场景：调查文件监控与订阅关系，关联应用用途和文件访问记录。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

无独立或继承的插件新增参数；使用前述全局配置。

</details>

#### `mac_volshell`

在 macOS 镜像地址空间中交互检查。适用场景：只读核验对象与字节；交互会话输出不自动兼容统一 JSON 表。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定内核虚拟地址空间中的 EPROCESS 地址，使用十六进制。 | 继承 volshell |
| `--imname` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名选择交互检查上下文。 | 继承 volshell |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 volshell |

</details>

#### `mac_yarascan`

使用 YARA 扫描 macOS 进程或内核内存。适用场景：以自有规则寻找候选字节，结合映射、应用上下文和误报分析验证。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。继承统一输出路径；当前插件的数据契约未逐个运行验证，不能据此直接确认 JSON 等格式可用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定 EPROCESS 的物理对象偏移，使用十六进制。 | 继承 DllList |
| `--pid` | `-p` | 字符串 | None | CLI 未声明必填；可选 | 按逗号分隔的 PID 筛选进程；这是字符串列表，不是单个整数。 | 继承 DllList |
| `--name` | `-n` | 字符串 | None | CLI 未声明必填；可选 | 按进程名正则表达式筛选。 | 继承 DllList |
| `--all` | `-A` | 布尔标志 | False | CLI 未声明必填；可选 | 同时扫描进程与内核空间；扩大范围会增加耗时和重复命中。 | 继承 YaraScan |
| `--case` | `-C` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则搜索时忽略大小写。 | 继承 YaraScan |
| `--kernel` | `-K` | 布尔标志 | False | CLI 未声明必填；可选 | 扫描内核模块/内核地址空间，而非默认进程范围。 | 继承 YaraScan |
| `--wide` | `-W` | 布尔标志 | False | CLI 未声明必填；可选 | YARA 字符串规则包含宽字符匹配。 | 继承 YaraScan |
| `--yara-rules` | `-Y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 直接提供 YARA 字符串规则表达式；核对生成规则、转义与误报。 | 继承 YaraScan |
| `--yara-file` | `-y` | 字符串 | None | CLI 未声明必填；规则来源至少选择一种 | 提供本地 YARA 规则文件；验证规则语法和所需模块。 | 继承 YaraScan |
| `--dump-dir` | `-D` | 字符串 | None | CLI 未声明必填；给定时校验目录是否有效 | 恢复文件的输出目录。 | 继承 YaraScan |
| `--size` | `-s` | 整数 | 256 | CLI 未声明必填；可选 | 命中点十六进制预览的字节数；默认 256。 | 继承 YaraScan |
| `--reverse` | `-R` | 整数 | 0 | CLI 未声明必填；可选 | 向命中点之前回退指定字节数作为显示或导出起点；不是字节顺序反转。 | 继承 YaraScan |
| `--max-size` | `-M` | 长整数（Python 2） | 1073741824 | CLI 未声明必填；可选 | 限制处理或导出区域最大大小，默认 1 GiB；更大区域可能被跳过。 | 继承 YaraScan |

</details>

</details>

### 通用/格式 命令（4 项）

<details>
<summary>展开 Volatility 2 通用/格式内置插件目录（4 项）</summary>

#### `imagecopy`

将可装载的物理地址空间复制为 raw 镜像。适用场景：在工作副本上规范化容器格式，记录源格式、缺页处理与输出哈希。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--blocksize` | `-b` | 整数 | 5242880（5 MiB） | CLI 未声明必填；可选 | 镜像复制分块大小，单位字节，默认 5 MiB。 | 本插件 |
| `--output-image` | `-O` | 字符串 | None | CLI 未声明必填；导出必填；拒绝覆盖非空既有文件 | 输出镜像文件路径；raw2dmp 会在此路径写出崩溃转储，不能按继承帮助误称 raw。 | 本插件 |
| `--count` | `-c` | 布尔标志 | False | CLI 未声明必填；可选 | 显示复制进度字节数。 | 本插件 |

</details>

#### `mbrparser`

扫描并解析可能的主引导记录。适用场景：把候选引导代码与可信磁盘副本比较，核对分区表、指令和距离指标。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`dot`, `greptext`, `html`, `json`, `sqlite`, `text`, `xlsx`。具有本插件统一输出实现；格式仍需满足依赖、目标结构与数据生成条件。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--hex` | `-H` | 布尔标志 | False | CLI 未声明必填；可选 | 用十六进制显示引导代码，代替默认反汇编。 | 本插件 |
| `--hash` | `-M` | 字符串 | None | CLI 未声明必填；可选 | 按截至 RET 的引导代码摘要筛选候选；必须确认所用摘要范围。 | 本插件 |
| `--fullhash` | `-F` | 字符串 | None | CLI 未声明必填；可选 | 按完整引导代码摘要筛选候选。 | 本插件 |
| `--disoffset` | `-D` | 整数 | None | CLI 未声明必填；可选 | 指定引导代码反汇编的起始偏移。 | 本插件 |
| `--offset` | `-o` | 整数 | None | CLI 未声明必填；可选 | 指定候选 MBR 的物理偏移。 | 本插件 |
| `--nocheck` | `-N` | 布尔标志 | False | CLI 未声明必填；可选 | 跳过 MBR 分区表校验；候选误报可能增加。 | 本插件 |
| `--disk` | `-m` | 字符串 | None | CLI 未声明必填；使用 --maxdistance 时必填 | 用于比较的可信磁盘镜像或已提取 MBR 文件路径。 | 本插件 |
| `--maxdistance` | `-x` | 整数 | None | CLI 未声明必填；可选 | 设置候选 MBR 与参考引导代码的最大编辑距离；必须提供参考文件。 | 本插件 |
| `--zerostart` | `-z` | 布尔标志 | False | CLI 未声明必填；可选 | 输出引导代码时从零显示偏移，便于参考文件对比。 | 本插件 |

</details>

#### `patcher`

按 XML 规则扫描并修改内存镜像字节。适用场景：仅在专门的分析副本上验证补丁位置；该命令会修改文件，须保留原镜像与前后差异。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--xml-input` | `-x` | 字符串 | None | CLI 未声明必填；规则输入必填 | 包含扫描与补丁规则的 XML 文件；与 --write 配合会修改分析副本。 | 本插件 |

</details>

#### `raw2dmp`

把物理内存转换为 WinDbg 崩溃转储。适用场景：在副本上创建调试器可读容器，核对头、profile 和输出页覆盖。

<details>
<summary>参数、输出与运行条件</summary>

静态输出方法路径：`text`。没有统一输出实现；基类 JSON 等方法不能单凭继承使用。

| 参数 | 短别名 | 类型/动作 | 代码默认 | 必填/运行条件 | 中文作用 | 归属 |
| --- | --- | --- | --- | --- | --- | --- |
| `--blocksize` | `-b` | 整数 | 5242880（5 MiB） | CLI 未声明必填；可选 | 镜像复制分块大小，单位字节，默认 5 MiB。 | 继承 ImageCopy |
| `--output-image` | `-O` | 字符串 | None | CLI 未声明必填；导出必填；拒绝覆盖非空既有文件 | 输出镜像文件路径；raw2dmp 会在此路径写出崩溃转储，不能按继承帮助误称 raw。 | 继承 ImageCopy |
| `--count` | `-c` | 布尔标志 | False | CLI 未声明必填；可选 | 显示复制进度字节数。 | 继承 ImageCopy |

继承的 --output-image 帮助文字提到 raw；本命令实际写出 Windows 崩溃转储容器，转换后验证转储头及页覆盖。

</details>

</details>

## 08 Volatility 3 全部参数、内置插件与 volshell

### Volatility 3：固定版本的完整命令与参数目录

此目录固定在 **v2.28.2**（commit `881e970121c16f0932fb9d16fbd5fb258cbcbf75`），包含 **197 个内置命令：169 个规范命令与 28 个兼容旧名**。Windows 105、Linux 60、macOS 23、通用 9。兼容旧名保留在对应系统目录并注明替代命令。

参数按此固定版本的 CLI 与插件需求定义整理。插件适用性仍取决于依赖、符号、系统结构和采集完整性；命令存在不代表适用于任意镜像。例如 `--verbosity` 是计数开关，`--parallelism` 接受 processes/threads/off，旧示例的拼写或用法可能不同。

```bash
python3 vol.py --help
python3 vol.py windows.pslist.PsList --help
python3 vol.py -f memory.raw -o output -r csv windows.pslist.PsList > pslist.csv
```

全局选项写在插件名之前，插件选项写在名称之后；下面的完整名称避免缩写匹配歧义。`-o` 保存插件生成的文件，结果表通过渲染器与重定向保存。Volatility 3 使用层与符号，不使用 Volatility 2 的 `--profile`。

#### 导出对象与地址语义

| 目标 | 插件或选项 | 地址与输出含义 | 验证要点 |
| --- | --- | --- | --- |
| 镜像内存层 | `layerwriter.LayerWriter --list/--layers` | 依所选层导出；底层物理映像、封装解码层与虚拟层含义不同 | 记录层名、地址上界、缺页与是否已解封装 |
| 进程主程序 | Windows `pslist/psscan --dump`；Linux `pslist --dump` | 重建主 PE 或主 ELF | 不等于进程所有虚拟内存，也不保证与磁盘原件逐字节相同 |
| 进程映射区段 | `windows.memmap --dump` | 依映射顺序串接可读区段；结果表提供 Virtual/Physical/Offset in File | 保留映射表，不能把输出文件偏移直接作为虚拟地址 |
| 单个虚拟区域 | `windows.vadinfo --dump`、`windows.malware.malfind --dump`；Linux/Mac Maps | 导出筛选后的 VAD/VMA 字节；Linux malfind 使用 `--dump-regions` | 核对区域权限、映射来源、大小阈值、缺页及内容格式 |
| 单个 PE/ELF 或模块 | `dlllist/modules/modscan --dump`、`pedump --base`、Linux `elfs/lsmod/module_extract` | 按相应进程或内核的虚拟基址重建文件 | 重定位、修改、缺页可能使重建文件与原文件不同 |
| Windows 文件缓存 | `dumpfiles --virtaddr/--physaddr` | 参数是 FILE_OBJECT 地址；dat/img/vacb 分别来自三种缓存视图 | 比较各视图、文件偏移与空洞；有文件对象不代表仍有缓存数据 |
| Linux 文件页缓存 | `pagecache.InodePages --dump`、`pagecache.RecoverFs` | 只恢复仍驻留的缓存页与目录关系 | 不能称完整磁盘恢复；RecoverFs 不复刻原元数据，导出时间为运行时间 |
| 注册表、证书与帧缓冲 | 对应插件的 `--dump` | 对象专用格式或字节 | 按对象格式检查完整性，不能套用进程内存导出的语义 |

`--physical` / `--physical-offsets` 通常只改变对象偏移显示。整数参数是否接受列表、地址属于物理层还是虚拟层，都应按下面的逐插件表判断。`None` 保留源码默认值的含义，不擅自改写为 `False` 或空列表。


#### 全局 CLI：23 项选项与插件位置参数

| 选项 | 类型 | 默认值 | 必填 | 作用与场景 |
| --- | --- | --- | --- | --- |
| `-h` / `--help` | 无值帮助开关 | 不存入配置 | 否 | 显示全局帮助；插件名后使用 -h/--help 查看该插件选项。 |
| `-c` / `--config` | 字符串/JSON 文件路径 | None | 否 | 载入 JSON 配置；用于保存并复核层和符号配置。 |
| `--parallelism` | 可选值：processes/threads/off | None（运行时按 off） | 否 | 启用并行；单独提供选项且不跟值时 const=processes，完全省略时关闭。 |
| `-e` / `--extend` | 可重复字符串 | None | 否 | 覆盖配置路径：conf.path=value；等号右侧按 JSON 解析，字符串需保留 JSON 引号。 |
| `-p` / `--plugin-dirs` | 字符串/目录列表 | 空字符串 | 否 | 追加插件目录，多个路径用分号分隔；目录中的第三方插件不属于本目录内置清单。 |
| `-s` / `--symbol-dirs` | 字符串/目录列表 | 空字符串 | 否 | 追加符号目录，多个路径用分号分隔。 |
| `-v` / `--verbosity` | 计数开关 | 0 | 否 | 每提供一次增加日志详细级别，例如 -vv；不改变证据采集范围。 |
| `-l` / `--log` | 字符串/文件路径 | None | 否 | 把日志同时写到指定文件；表格结果与日志是不同输出。 |
| `-o` / `--output-dir` | 字符串/目录路径 | 当前工作目录 | 否 | 插件生成文件的存放目录；表格结果另用 renderer 与 shell 重定向保存。 |
| `-q` / `--quiet` | 布尔开关 | False | 否 | 隐藏进度反馈；不会隐藏结果表。 |
| `-f` / `--file` | 字符串/本地文件路径 | None | 否 | single-location 未设置时，把本地镜像路径转换为 file:// URI。 |
| `--write-config` | 布尔开关 | False | 否 | 保存到 config.json；此选项已弃用，改用 --save-config 文件名。 |
| `--save-config` | 字符串/文件路径 | None | 否 | 把生成配置保存到指定 JSON 文件。 |
| `--clear-cache` | 布尔开关 | False | 否 | 清理 Volatility 的短期缓存；缓存目录由 cache-path 决定。 |
| `--cache-path` | 字符串/目录路径 | 依平台的用户缓存目录 | 否 | 改变框架缓存位置；隔离分析时可指定独立工作目录。 |
| `--offline` | 布尔开关 | False | 否 | 与 remote-isf-url 互斥，不在线搜索补充 ISF JSON；仍须准备匹配的本地符号，不应把它当作网络隔离机制。 |
| `-u` / `--remote-isf-url` | 字符串/URL | None | 否 | 指定用于查询 ISF JSON 地址的远端索引 URL；此固定版本常量默认是 None。 |
| `--filters` | 可重复字符串 | [] | 否 | 对输出结果施加过滤，格式 [+-]columnname,pattern[!]；不改变插件实际遍历证据的范围。 |
| `--hide-columns` | 字符串列表；0 个或多个值 | None | 否 | 按不区分大小写的列名前缀隐藏结果列，多个前缀用空格分隔。 |
| `-r` / `--renderer` | 可用渲染器名称 | quick | 否 | 输出格式依安装环境确定；基础渲染器包括 quick、none、csv、pretty、json、jsonl、mermaid，pyarrow 可用时另有 arrow/parquet。 |
| `--single-location` | URI/本地路径 | None | 否 | 用于构建内存层的基础位置；本地路径会转换成 URI，可由 -f 提供。 |
| `--stackers` | 字符串列表；0 个或多个值 | None | 否 | 限定用于构建层的 stacker 类名列表；省略时由框架按系统选择。 |
| `--single-swap-locations` | URI 字符串列表；0 个或多个值 | None | 否 | 给 single-location 提供交换层 URI 列表；此版本实际验证要求数量小于 16。仍取决于层支持和交换文件匹配。 |
| `PLUGIN`（位置参数） | 完整插件名 | 无 | 是（查看帮助除外） | 选择要运行的插件命令 |

所有插件另共用 `-h` / `--help`；这不是插件需求参数。布尔开关不接 `true/false` 值，提供即启用。可选列表一般接受零个或多个值，必填列表接受一个或多个值。表中的“必填”按 CLI 需求定义；实际运行仍可能要求选择规则文件、定位对象或满足其他语义条件。

### Windows：105 个命令

<details>
<summary>展开 Volatility 3 Windows 内置插件目录（105 项）</summary>

<details>
<summary>Windows 完整插件总表</summary>

| 完整命令 | 中文作用 | 典型应用 | 依赖与兼容旧名 |
| --- | --- | --- | --- |
| `windows.amcache.Amcache` | 解析 Amcache 中应用程序相关记录 | 寻找路径、文件属性及应用关联线索；记录存在不能单独证明执行。 | 兼容旧名，此固定版仍提供；优先使用 `windows.registry.amcache.Amcache`。 |
| `windows.bigpools.BigPools` | 列出大页池分配 | 按 pool tag 定位内核分配，区分在用与已释放区域。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.cachedump.Cachedump` | 提取缓存域登录凭据记录 | 在授权镜像中核对缓存账户与域信息；结果不同于 SAM 哈希及通用 LSA secrets。 | 兼容旧名，此固定版仍提供；优先使用 `windows.registry.cachedump.Cachedump`。 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.callbacks.Callbacks` | 列出内核回调与通知函数 | 核对进程、线程、映像等通知入口，关联驱动和符号判断异常。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.cmdline.CmdLine` | 列出进程命令行 | 从启动参数寻找脚本、下载地址或路径线索；命令行字段可被修改。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.cmdscan.CmdScan` | 扫描 Windows 命令历史结构 | 恢复命令行历史候选，和控制台缓冲、进程及时间线核验。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.consoles.Consoles` | 恢复控制台结构、历史与屏幕缓冲 | 查找命令执行及输出残留；缓冲内容可能截断或混合。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.crashinfo.Crashinfo` | 提取 Windows 崩溃转储元数据 | 确认转储类型、处理器及内核信息，解释采集覆盖范围。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.debugregisters.DebugRegisters` | 检查线程陷阱帧中的硬件调试寄存器 | 寻找启用的 Dr7 与 Dr0–Dr3 硬件断点；结合调试器与线程状态排除正常调试。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.deskscan.DeskScan` | 扫描窗口站中的 Desktop 对象 | 补充常规桌面枚举，发现残留或隐藏桌面对象。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.desktops.Desktops` | 沿窗口站结构枚举 Desktop | 建立交互会话桌面基线，和 deskscan、窗口结果交叉比较。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.devicetree.DeviceTree` | 展示驱动与附加设备树 | 检查设备栈关联和可疑附加设备，核对所属驱动。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.direct_system_calls.DirectSystemCalls` | 寻找直接系统调用技术的代码特征 | 定位可疑代码区域并反汇编验证；特征命中不等于恶意行为。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.direct_system_calls.DirectSystemCalls`。 需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。 |
| `windows.dlllist.DllList` | 列出加载器记录的 DLL 并可重建 PE | 定位库路径、基址与加载时间；结合 ldrmodules 排查不一致，dump 只重建选中的 DLL。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.driverirp.DriverIrp` | 列出驱动 IRP 派遣函数 | 将派遣入口映射到模块，寻找异常设备处理钩子。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.drivermodule.DriverModule` | 比较驱动对象与模块归属 | 寻找缺少合法加载模块对应的驱动对象，调查隐藏驱动候选。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.drivermodule.DriverModule`。 |
| `windows.driverscan.DriverScan` | 扫描驱动对象 | 补充内核模块清单，核对驱动对象、设备栈与模块归属。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.dumpfiles.DumpFiles` | 从文件对象恢复缓存文件内容 | 利用 DataSection、ImageSection、SharedCacheMap 分别恢复 dat、img、vacb；缺页与不同缓存视图会产生不完整或不同结果。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.envars.Envars` | 列出进程环境变量 | 查找用户目录、临时目录、代理和配置线索，结合命令行复核。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.etwpatch.EtwPatch` | 检查关键 ETW 函数入口的异常补丁 | 调查 ntdll/advapi32 中 RET、JMP 等入口修改；合法软件改动也需排除。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.filescan.FileScan` | 扫描内存中的 FILE_OBJECT | 寻找文件路径及对象地址，为 dumpfiles 选取物理或虚拟对象地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.getservicesids.GetServiceSIDs` | 从服务配置计算服务 SID | 把服务名映射到服务 SID，与进程 token、注册表配置交叉核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.getsids.GetSIDs` | 列出进程 token 的 SID | 核对进程身份、组成员与服务上下文。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.handles.Handles` | 列出进程打开的内核对象句柄 | 关联进程与文件、注册表、事件、互斥体等对象。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.hashdump.Hashdump` | 提取 SAM 本地账户口令哈希 | 在授权镜像中核对本地账户证据；不把提取结果写进公开笔记。 | 兼容旧名，此固定版仍提供；优先使用 `windows.registry.hashdump.Hashdump`。 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.hollowprocesses.HollowProcesses` | 查找进程主映像被替换的异常 | 比较进程主映像结构与内存映射，复核挖空候选与合法加载差异。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.hollowprocesses.HollowProcesses`。 |
| `windows.iat.IAT` | 解析进程 PE 导入地址表 | 核对导入 API 与解析地址，辅助调查导入表异常或程序依赖。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.indirect_system_calls.IndirectSystemCalls` | 寻找间接系统调用技术特征 | 定位跳转到系统调用指令的候选代码，结合模块、线程和反汇编复核。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.indirect_system_calls.IndirectSystemCalls`。 需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。 |
| `windows.info.Info` | 列出操作系统、内核、层与符号信息 | 首次分析时核验系统架构、内核和符号匹配，再运行具体证据插件。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.joblinks.JobLinks` | 列出进程与 Job 对象关系 | 调查进程组控制、限制和组织关系；physical 只改变地址显示。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.kpcrs.KPCRs` | 列出各处理器 KPCR 结构 | 核对每 CPU 内核控制结构及地址，辅助内核层异常调查。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.ldrmodules.LdrModules` | 比较 PE 映射与加载器模块链表 | 识别未进入部分加载器链表的模块；正常手动映射和损坏结构需排除。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.ldrmodules.LdrModules`。 |
| `windows.lsadump.Lsadump` | 提取 SECURITY hive 中的 LSA secrets | 在授权镜像中核对服务或系统凭据相关证据；与域登录缓存分开判读。 | 兼容旧名，此固定版仍提供；优先使用 `windows.registry.lsadump.Lsadump`。 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.malfind.Malfind` | 查找可能含注入代码的 VAD | 关联权限、内容、进程与线程；dump 输出候选 VAD 字节，不能直接当作磁盘 PE。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.malfind.Malfind`。 |
| `windows.malware.direct_system_calls.DirectSystemCalls` | 寻找直接系统调用技术的代码特征 | 定位可疑代码区域并反汇编验证；特征命中不等于恶意行为。 | 需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。 |
| `windows.malware.drivermodule.DriverModule` | 比较驱动对象与模块归属 | 寻找缺少合法加载模块对应的驱动对象，调查隐藏驱动候选。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.hollowprocesses.HollowProcesses` | 查找进程主映像被替换的异常 | 比较进程主映像结构与内存映射，复核挖空候选与合法加载差异。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.indirect_system_calls.IndirectSystemCalls` | 寻找间接系统调用技术特征 | 定位跳转到系统调用指令的候选代码，结合模块、线程和反汇编复核。 | 需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。 |
| `windows.malware.ldrmodules.LdrModules` | 比较 PE 映射与加载器模块链表 | 识别未进入部分加载器链表的模块；正常手动映射和损坏结构需排除。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.malfind.Malfind` | 查找可能含注入代码的 VAD | 关联权限、内容、进程与线程；dump 输出候选 VAD 字节，不能直接当作磁盘 PE。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.pebmasquerade.PebMasquerade` | 比较 EPROCESS 与 PEB 中的进程标识 | 发现名称或路径伪装候选，结合主映像映射与命令行核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.processghosting.ProcessGhosting` | 检查删除挂起、缺失文件对象和 DeleteOnClose 映像 | 寻找进程映像文件生命周期异常，结合文件对象与 VAD 判读。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.psxview.PsXView` | 交叉比较四种进程发现视图 | 发现链表外或某视图遗漏的进程；结束进程、采集不同步也会产生差异。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.malware.skeleton_key_check.Skeleton_Key_Check` | 检查 Skeleton Key 相关内存异常特征 | 在适用系统中复核认证组件的候选篡改，不能仅凭一个特征判定感染。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.malware.suspicious_threads.SuspiciousThreads` | 枚举有可疑启动位置等异常的用户线程 | 把线程入口与所属 VAD、模块对齐，寻找注入执行链。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.malware.svcdiff.SvcDiff` | 交叉比较服务链表与扫描结果 | 识别链表遗漏的服务记录；残留与停止服务需进一步核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.malware.unhooked_system_calls.UnhookedSystemCalls` | 检测进程 ntdll 系统调用 stub 的钩子 | 核对函数入口异常；插件名不代表输出规避检测的操作。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.mbrscan.MBRScan` | 扫描并解析潜在 MBR 分区与引导代码 | 寻找引导记录残留并检查分区结构；内存命中不等于当前磁盘引导扇区。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.memmap.Memmap` | 列出进程虚拟页到物理页的映射并可导出 | 导出可读映射区段并用 Offset in File 反查；文件偏移不能直接当成进程虚拟地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.mftscan.ADS` | 扫描 MFT 记录中的备用数据流 | 查找 ADS 名称及关联记录，结合磁盘 MFT 验证。 | 需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。 |
| `windows.mftscan.MFTScan` | 扫描内存残留的 MFT FILE 记录 | 恢复文件名、时间与记录号线索；不承诺完整磁盘 MFT。 | 需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。 |
| `windows.mftscan.ResidentData` | 扫描并提取 MFT 驻留数据 | 恢复内存 MFT 记录中的小文件数据，区别于非驻留文件和缓存文件导出。 | 需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。 |
| `windows.modscan.ModScan` | 扫描内核模块并可重建 PE | 发现模块链表外或卸载残留候选，和 modules、驱动对象交叉核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.modules.Modules` | 沿加载链表枚举内核模块并可重建 PE | 建立驱动加载基线，按基址或名称导出内存态模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.mutantscan.MutantScan` | 扫描内核互斥体对象 | 查找进程同步标记或特定命名对象，再关联句柄与进程。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.netscan.NetScan` | 扫描网络端点和连接对象 | 恢复活动与残留连接，核对 PID、时间与地址；宽松模式增加误报。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.netstat.NetStat` | 遍历内核网络跟踪结构 | 获得结构枚举的网络视图，与 netscan 的扫描结果比较覆盖。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.orphan_kernel_threads.Threads` | 寻找启动地址无法归属已知模块的内核线程 | 关联 System 及相关内核进程的活动线程，复核入口字节和模块缺口。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.pe_symbols.PESymbols` | 在内核或进程 PE 中解析符号与地址 | 按模块解析函数名或反查地址，辅助解释回调、导入和线程入口。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.pedump.PEDump` | 按指定地址空间与基址重建 PE | 从已定位的进程或内核虚拟基址恢复 PE；基址不是镜像物理偏移。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.poolscanner.PoolScanner` | 执行内核池对象扫描 | 理解池标签扫描覆盖并寻找对象候选；对象有效性需由对应专用插件核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.privileges.Privs` | 列出进程 token 特权 | 检查调试、备份等高权限及启用状态，结合身份与合法用途判断。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.processghosting.ProcessGhosting` | 检查删除挂起、缺失文件对象和 DeleteOnClose 映像 | 寻找进程映像文件生命周期异常，结合文件对象与 VAD 判读。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.processghosting.ProcessGhosting`。 |
| `windows.pslist.PsList` | 沿活动进程链表枚举并可重建主 PE | 建立进程基线；dump 从进程主映像重建 PE，不导出全部进程内存。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.psscan.PsScan` | 扫描进程对象并可重建主 PE | 发现链表外、结束或隐藏进程候选；dump 与 pslist 一样重建主 PE。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.pstree.PsTree` | 按父 PID 展示进程树 | 追踪启动链；指定 PID 时保留其祖先和后代，PID 重用须结合时间核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.psxview.PsXView` | 交叉比较四种进程发现视图 | 发现链表外或某视图遗漏的进程；结束进程、采集不同步也会产生差异。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.psxview.PsXView`。 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.registry.amcache.Amcache` | 解析 Amcache 中应用程序相关记录 | 寻找路径、文件属性及应用关联线索；记录存在不能单独证明执行。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.cachedump.Cachedump` | 提取缓存域登录凭据记录 | 在授权镜像中核对缓存账户与域信息；结果不同于 SAM 哈希及通用 LSA secrets。 | 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.registry.certificates.Certificates` | 列出注册表证书存储并可导出证书 | 核对证书主体、指纹与异常证书植入，再与系统证书配置交叉验证。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.getcellroutine.GetCellRoutine` | 检查 hive 的 GetCellRoutine 回调 | 发现注册表取单元路径上的异常处理函数，关联合法模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.hashdump.Hashdump` | 提取 SAM 本地账户口令哈希 | 在授权镜像中核对本地账户证据；不把提取结果写进公开笔记。 | 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.registry.hivelist.HiveList` | 枚举已挂载 hive 并可导出 | 建立 SYSTEM、SOFTWARE、用户 hive 等证据入口，恢复可读 hive 内容。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.hivescan.HiveScan` | 扫描注册表 hive 结构 | 寻找枚举遗漏或残留 hive，与 hivelist 核对可读性和名称。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.lsadump.Lsadump` | 提取 SECURITY hive 中的 LSA secrets | 在授权镜像中核对服务或系统凭据相关证据；与域登录缓存分开判读。 | 需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。 |
| `windows.registry.printkey.PrintKey` | 读取 hive 中指定键和值 | 从明确 hive 偏移与键路径检查启动项、服务或配置，递归时注意覆盖范围。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.scheduled_tasks.ScheduledTasks` | 解析注册表计划任务信息 | 核对触发器、动作及时间，和任务文件、日志交叉验证持久化。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.registry.userassist.UserAssist` | 解析用户 UserAssist 项 | 提取 GUI 应用交互相关线索；计数和时间需结合系统版本及其他执行证据。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.scheduled_tasks.ScheduledTasks` | 解析注册表计划任务信息 | 核对触发器、动作及时间，和任务文件、日志交叉验证持久化。 | 兼容旧名，此固定版仍提供；优先使用 `windows.registry.scheduled_tasks.ScheduledTasks`。 |
| `windows.sessions.Sessions` | 从进程环境变量提取会话信息 | 区分交互用户与会话背景，和 SID、命令行关联。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.shimcachemem.ShimcacheMem` | 从 ahcache.sys 的 AVL 树读取 Shimcache | 恢复应用兼容性缓存路径与时间线索；不能单凭缓存记录确认执行。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.skeleton_key_check.Skeleton_Key_Check` | 检查 Skeleton Key 相关内存异常特征 | 在适用系统中复核认证组件的候选篡改，不能仅凭一个特征判定感染。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.skeleton_key_check.Skeleton_Key_Check`。 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.ssdt.SSDT` | 列出系统调用表及函数归属 | 把表项映射到模块与符号，复核异常入口。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.statistics.Statistics` | 统计内存空间有效、无效、交换及大页等情况 | 评估地址空间解析覆盖与缺页，解释其他插件无法读取的区域。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.strings.Strings` | 把带物理偏移的字符串结果映射到进程 | 将外部字符串提取的地址关联到进程；字符串文件格式和偏移基准必须正确。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.suspended_threads.SuspendedThreads` | 枚举挂起线程 | 寻找异常挂起状态及相关进程；正常应用也可能合法挂起线程。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.suspicious_threads.SuspiciousThreads` | 枚举有可疑启动位置等异常的用户线程 | 把线程入口与所属 VAD、模块对齐，寻找注入执行链。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.suspicious_threads.SuspiciousThreads`。 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.svcdiff.SvcDiff` | 交叉比较服务链表与扫描结果 | 识别链表遗漏的服务记录；残留与停止服务需进一步核验。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.svcdiff.SvcDiff`。 |
| `windows.svclist.SvcList` | 沿 services.exe 服务链表枚举服务 | 建立结构枚举的服务视图，和 svcscan、注册表配置交叉核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.svcscan.SvcScan` | 扫描服务记录 | 寻找残留或链表外服务，关联状态、映像路径与进程。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.symlinkscan.SymlinkScan` | 扫描对象管理器符号链接 | 调查设备名或对象路径重定向，和设备树、句柄对应。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.thrdscan.ThrdScan` | 扫描线程对象 | 恢复活动及残留线程候选，核对拥有进程、入口与时间。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.threads.Threads` | 列出进程线程 | 建立线程视图，和 thrdscan、可疑线程插件交叉核验。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.timers.Timers` | 列出内核定时器及 DPC 模块归属 | 调查定时执行入口是否指向未知模块或异常地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.truecrypt.Passphrase` | 查找 TrueCrypt 缓存口令候选 | 在适用旧版软件的授权镜像中恢复候选；最小长度筛选不保证命中正确口令。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.unhooked_system_calls.unhooked_system_calls` | 检测进程 ntdll 系统调用 stub 的钩子 | 核对函数入口异常；插件名不代表输出规避检测的操作。 | 兼容旧名，此固定版仍提供；优先使用 `windows.malware.unhooked_system_calls.UnhookedSystemCalls`。 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.unloadedmodules.UnloadedModules` | 列出已卸载内核模块记录 | 补充驱动生命周期线索；记录数量有限，缺失不代表从未加载。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.vadinfo.VadInfo` | 列出 VAD 范围、权限、文件并可导出 | 定位进程虚拟地址对应区域；导出是 VAD 字节，大小阈值会跳过较大区域。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.vadregexscan.VadRegExScan` | 在进程 VAD 中搜索正则表达式 | 按 PID 查找配置、路径或文本，保留虚拟地址与上下文核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.vadwalk.VadWalk` | 遍历进程 VAD 树 | 核对虚拟地址空间树结构与范围，辅助调查损坏或异常映射。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.vadyarascan.VadYaraScan` | 在进程 VAD 中执行 YARA 扫描 | 定位规则命中所在进程与虚拟地址，再和 VAD 属性、线程入口对应。 | 需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。 |
| `windows.verinfo.VerInfo` | 提取内存 PE 的版本资源 | 核对模块产品、版本与名称；extensive 扫描物理层，结果可含残留。 | 需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。 |
| `windows.virtmap.VirtMap` | 列出内核虚拟映射分区 | 了解内核虚拟空间区域与布局，辅助解释内核地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.windows.Windows` | 枚举桌面中的窗口对象 | 恢复窗口标题和关联对象线索，结合桌面、窗口站与进程核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `windows.windowstations.WindowStations` | 扫描顶层窗口站对象 | 建立会话图形对象入口，为桌面及窗口枚举提供上下文。 | 需匹配的层、内核符号及对应镜像结构。 |

</details>

完整参数表（含从父类或替代类继承的需求）：

<details>
<summary>windows.amcache.Amcache — 解析 Amcache 中应用程序相关记录</summary>

寻找路径、文件属性及应用关联线索；记录存在不能单独证明执行。

兼容旧名，规范命令为 `windows.registry.amcache.Amcache`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.bigpools.BigPools — 列出大页池分配</summary>

按 pool tag 定位内核分配，区分在用与已释放区域。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--tags` | 字符串 | None（未显式设置） | 否 | 用逗号分隔的 pool tag 筛选大页池。 |
| `--show-free` | 布尔开关 | false | 否 | 包含已释放区域，默认只显示在用分配。 |

</details>

<details>
<summary>windows.cachedump.Cachedump — 提取缓存域登录凭据记录</summary>

在授权镜像中核对缓存账户与域信息；结果不同于 SAM 哈希及通用 LSA secrets。

兼容旧名，规范命令为 `windows.registry.cachedump.Cachedump`；下面列出其继承的全部 CLI 参数。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.callbacks.Callbacks — 列出内核回调与通知函数</summary>

核对进程、线程、映像等通知入口，关联驱动和符号判断异常。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.cmdline.CmdLine — 列出进程命令行</summary>

从启动参数寻找脚本、下载地址或路径线索；命令行字段可被修改。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.cmdscan.CmdScan — 扫描 Windows 命令历史结构</summary>

恢复命令行历史候选，和控制台缓冲、进程及时间线核验。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--no-registry` | 布尔开关 | false | 否 | 不从注册表寻找历史缓冲参数候选，改用给定或默认值。 |
| `--max-history` | 整数列表（空格分隔） | [50] | 否 | 要搜索的 CommandHistorySize 候选值列表。 |

</details>

<details>
<summary>windows.consoles.Consoles — 恢复控制台结构、历史与屏幕缓冲</summary>

查找命令执行及输出残留；缓冲内容可能截断或混合。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--no-registry` | 布尔开关 | false | 否 | 不从注册表寻找历史缓冲参数候选，改用给定或默认值。 |
| `--max-history` | 整数列表（空格分隔） | [50] | 否 | 要搜索的 CommandHistorySize 候选值列表。 |
| `--max-buffers` | 整数列表（空格分隔） | [4] | 否 | 要搜索的 HistoryBufferMax 候选值列表。 |

</details>

<details>
<summary>windows.crashinfo.Crashinfo — 提取 Windows 崩溃转储元数据</summary>

确认转储类型、处理器及内核信息，解释采集覆盖范围。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.debugregisters.DebugRegisters — 检查线程陷阱帧中的硬件调试寄存器</summary>

寻找启用的 Dr7 与 Dr0–Dr3 硬件断点；结合调试器与线程状态排除正常调试。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.deskscan.DeskScan — 扫描窗口站中的 Desktop 对象</summary>

补充常规桌面枚举，发现残留或隐藏桌面对象。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.desktops.Desktops — 沿窗口站结构枚举 Desktop</summary>

建立交互会话桌面基线，和 deskscan、窗口结果交叉比较。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.devicetree.DeviceTree — 展示驱动与附加设备树</summary>

检查设备栈关联和可疑附加设备，核对所属驱动。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.direct_system_calls.DirectSystemCalls — 寻找直接系统调用技术的代码特征</summary>

定位可疑代码区域并反汇编验证；特征命中不等于恶意行为。

兼容旧名，规范命令为 `windows.malware.direct_system_calls.DirectSystemCalls`；下面列出其继承的全部 CLI 参数。

需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--wide` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |

</details>

<details>
<summary>windows.dlllist.DllList — 列出加载器记录的 DLL 并可重建 PE</summary>

定位库路径、基址与加载时间；结合 ldrmodules 排查不一致，dump 只重建选中的 DLL。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--offset` | 整数（十进制或 0x） | None（未显式设置） | 否 | 指定 EPROCESS 对象的物理偏移，不能填进程虚拟基址。 |
| `--base` | 整数（十进制或 0x） | None（未显式设置） | 否 | 要重建 ELF/PE 的虚拟基址，必须属于已选地址空间；不是物理偏移。 |
| `--name` | 字符串 | None（未显式设置） | 否 | 按 DLL 名正则表达式筛选。 |
| `--ignore-case` | 布尔开关 | false | 否 | 正则表达式名称或路径筛选忽略大小写。 |
| `--dump` | 布尔开关 | false | 否 | 重建筛选后的内存 DLL PE；可能与磁盘原文件不同。 |

</details>

<details>
<summary>windows.driverirp.DriverIrp — 列出驱动 IRP 派遣函数</summary>

将派遣入口映射到模块，寻找异常设备处理钩子。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.drivermodule.DriverModule — 比较驱动对象与模块归属</summary>

寻找缺少合法加载模块对应的驱动对象，调查隐藏驱动候选。

兼容旧名，规范命令为 `windows.malware.drivermodule.DriverModule`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.driverscan.DriverScan — 扫描驱动对象</summary>

补充内核模块清单，核对驱动对象、设备栈与模块归属。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.dumpfiles.DumpFiles — 从文件对象恢复缓存文件内容</summary>

利用 DataSection、ImageSection、SharedCacheMap 分别恢复 dat、img、vacb；缺页与不同缓存视图会产生不完整或不同结果。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数（十进制或 0x） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--virtaddr` | 整数列表（空格分隔） | None（未显式设置） | 否 | 指定 FILE_OBJECT 的虚拟地址列表；不是文件内容起始地址。 |
| `--physaddr` | 整数列表（空格分隔） | None（未显式设置） | 否 | 指定 FILE_OBJECT 的物理地址列表；不是文件内容的物理页地址。 |
| `--filter` | 字符串 | None（未显式设置） | 否 | 按文件路径正则表达式筛选缓存文件；与 ignore-case 配合。不能与 virtaddr/physaddr 同时使用。 |
| `--ignore-case` | 布尔开关 | false | 否 | 正则表达式名称或路径筛选忽略大小写。 |

</details>

<details>
<summary>windows.envars.Envars — 列出进程环境变量</summary>

查找用户目录、临时目录、代理和配置线索，结合命令行复核。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--silent` | 布尔开关 | None（未显式设置） | 否 | 隐藏常见及非持久环境变量；源码默认 None，提供选项时为 True。 |

</details>

<details>
<summary>windows.etwpatch.EtwPatch — 检查关键 ETW 函数入口的异常补丁</summary>

调查 ntdll/advapi32 中 RET、JMP 等入口修改；合法软件改动也需排除。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.filescan.FileScan — 扫描内存中的 FILE_OBJECT</summary>

寻找文件路径及对象地址，为 dumpfiles 选取物理或虚拟对象地址。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.getservicesids.GetServiceSIDs — 从服务配置计算服务 SID</summary>

把服务名映射到服务 SID，与进程 token、注册表配置交叉核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.getsids.GetSIDs — 列出进程 token 的 SID</summary>

核对进程身份、组成员与服务上下文。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.handles.Handles — 列出进程打开的内核对象句柄</summary>

关联进程与文件、注册表、事件、互斥体等对象。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--offset` | 整数（十进制或 0x） | None（未显式设置） | 否 | 指定 EPROCESS 对象的物理偏移，不能填进程虚拟基址。 |

</details>

<details>
<summary>windows.hashdump.Hashdump — 提取 SAM 本地账户口令哈希</summary>

在授权镜像中核对本地账户证据；不把提取结果写进公开笔记。

兼容旧名，规范命令为 `windows.registry.hashdump.Hashdump`；下面列出其继承的全部 CLI 参数。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.hollowprocesses.HollowProcesses — 查找进程主映像被替换的异常</summary>

比较进程主映像结构与内存映射，复核挖空候选与合法加载差异。

兼容旧名，规范命令为 `windows.malware.hollowprocesses.HollowProcesses`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.iat.IAT — 解析进程 PE 导入地址表</summary>

核对导入 API 与解析地址，辅助调查导入表异常或程序依赖。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.indirect_system_calls.IndirectSystemCalls — 寻找间接系统调用技术特征</summary>

定位跳转到系统调用指令的候选代码，结合模块、线程和反汇编复核。

兼容旧名，规范命令为 `windows.malware.indirect_system_calls.IndirectSystemCalls`；下面列出其继承的全部 CLI 参数。

需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--wide` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |

</details>

<details>
<summary>windows.info.Info — 列出操作系统、内核、层与符号信息</summary>

首次分析时核验系统架构、内核和符号匹配，再运行具体证据插件。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.joblinks.JobLinks — 列出进程与 Job 对象关系</summary>

调查进程组控制、限制和组织关系；physical 只改变地址显示。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--physical` | 布尔开关 | false | 否 | 把结果中的对象偏移显示为物理偏移；不改变导出对象，也不表示导出物理层。 |

</details>

<details>
<summary>windows.kpcrs.KPCRs — 列出各处理器 KPCR 结构</summary>

核对每 CPU 内核控制结构及地址，辅助内核层异常调查。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.ldrmodules.LdrModules — 比较 PE 映射与加载器模块链表</summary>

识别未进入部分加载器链表的模块；正常手动映射和损坏结构需排除。

兼容旧名，规范命令为 `windows.malware.ldrmodules.LdrModules`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.lsadump.Lsadump — 提取 SECURITY hive 中的 LSA secrets</summary>

在授权镜像中核对服务或系统凭据相关证据；与域登录缓存分开判读。

兼容旧名，规范命令为 `windows.registry.lsadump.Lsadump`；下面列出其继承的全部 CLI 参数。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.malfind.Malfind — 查找可能含注入代码的 VAD</summary>

关联权限、内容、进程与线程；dump 输出候选 VAD 字节，不能直接当作磁盘 PE。

兼容旧名，规范命令为 `windows.malware.malfind.Malfind`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 导出注入候选 VAD 字节；不自动还原成有效磁盘 PE。 |

</details>

<details>
<summary>windows.malware.direct_system_calls.DirectSystemCalls — 寻找直接系统调用技术的代码特征</summary>

定位可疑代码区域并反汇编验证；特征命中不等于恶意行为。

需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--wide` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |

</details>

<details>
<summary>windows.malware.drivermodule.DriverModule — 比较驱动对象与模块归属</summary>

寻找缺少合法加载模块对应的驱动对象，调查隐藏驱动候选。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.malware.hollowprocesses.HollowProcesses — 查找进程主映像被替换的异常</summary>

比较进程主映像结构与内存映射，复核挖空候选与合法加载差异。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.malware.indirect_system_calls.IndirectSystemCalls — 寻找间接系统调用技术特征</summary>

定位跳转到系统调用指令的候选代码，结合模块、线程和反汇编复核。

需要 YARA 引擎与 capstone；缺失时可能无法导入或不产生检测结果。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--wide` | 布尔开关 | false | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 共享 YARA 需求声明的选项；此版本该插件使用内置规则和固定区域筛选，没有读取此配置，不应依靠它改变检测行为。 |

</details>

<details>
<summary>windows.malware.ldrmodules.LdrModules — 比较 PE 映射与加载器模块链表</summary>

识别未进入部分加载器链表的模块；正常手动映射和损坏结构需排除。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.malware.malfind.Malfind — 查找可能含注入代码的 VAD</summary>

关联权限、内容、进程与线程；dump 输出候选 VAD 字节，不能直接当作磁盘 PE。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 导出注入候选 VAD 字节；不自动还原成有效磁盘 PE。 |

</details>

<details>
<summary>windows.malware.pebmasquerade.PebMasquerade — 比较 EPROCESS 与 PEB 中的进程标识</summary>

发现名称或路径伪装候选，结合主映像映射与命令行核验。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.malware.processghosting.ProcessGhosting — 检查删除挂起、缺失文件对象和 DeleteOnClose 映像</summary>

寻找进程映像文件生命周期异常，结合文件对象与 VAD 判读。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.malware.psxview.PsXView — 交叉比较四种进程发现视图</summary>

发现链表外或某视图遗漏的进程；结束进程、采集不同步也会产生差异。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--physical-offsets` | 布尔开关 | None（未显式设置） | 否 | 把进程对象偏移显示为物理偏移；源码默认 None，提供选项时为 True。 |

</details>

<details>
<summary>windows.malware.skeleton_key_check.Skeleton_Key_Check — 检查 Skeleton Key 相关内存异常特征</summary>

在适用系统中复核认证组件的候选篡改，不能仅凭一个特征判定感染。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.malware.suspicious_threads.SuspiciousThreads — 枚举有可疑启动位置等异常的用户线程</summary>

把线程入口与所属 VAD、模块对齐，寻找注入执行链。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.malware.svcdiff.SvcDiff — 交叉比较服务链表与扫描结果</summary>

识别链表遗漏的服务记录；残留与停止服务需进一步核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.malware.unhooked_system_calls.UnhookedSystemCalls — 检测进程 ntdll 系统调用 stub 的钩子</summary>

核对函数入口异常；插件名不代表输出规避检测的操作。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.mbrscan.MBRScan — 扫描并解析潜在 MBR 分区与引导代码</summary>

寻找引导记录残留并检查分区结构；内存命中不等于当前磁盘引导扇区。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--full` | 布尔开关 | false | 否 | 显示完整分区记录与引导代码十六进制信息，输出较多时适合 CSV。 |

</details>

<details>
<summary>windows.memmap.Memmap — 列出进程虚拟页到物理页的映射并可导出</summary>

导出可读映射区段并用 Offset in File 反查；文件偏移不能直接当成进程虚拟地址。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数（十进制或 0x） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 按映射顺序写出可读进程虚拟内存区段；保留 Offset in File 与虚拟地址对应表。 |

</details>

<details>
<summary>windows.mftscan.ADS — 扫描 MFT 记录中的备用数据流</summary>

查找 ADS 名称及关联记录，结合磁盘 MFT 验证。

需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.mftscan.MFTScan — 扫描内存残留的 MFT FILE 记录</summary>

恢复文件名、时间与记录号线索；不承诺完整磁盘 MFT。

需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.mftscan.ResidentData — 扫描并提取 MFT 驻留数据</summary>

恢复内存 MFT 记录中的小文件数据，区别于非驻留文件和缓存文件导出。

需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.modscan.ModScan — 扫描内核模块并可重建 PE</summary>

发现模块链表外或卸载残留候选，和 modules、驱动对象交叉核验。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |
| `--base` | 整数（十进制或 0x） | None（未显式设置） | 否 | 仅提取此内核模块虚拟基址的模块。 |
| `--name` | 字符串 | None（未显式设置） | 否 | 按内核模块名称或子串筛选。 |

</details>

<details>
<summary>windows.modules.Modules — 沿加载链表枚举内核模块并可重建 PE</summary>

建立驱动加载基线，按基址或名称导出内存态模块。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |
| `--base` | 整数（十进制或 0x） | None（未显式设置） | 否 | 仅提取此内核模块虚拟基址的模块。 |
| `--name` | 字符串 | None（未显式设置） | 否 | 按内核模块名称或子串筛选。 |

</details>

<details>
<summary>windows.mutantscan.MutantScan — 扫描内核互斥体对象</summary>

查找进程同步标记或特定命名对象，再关联句柄与进程。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.netscan.NetScan — 扫描网络端点和连接对象</summary>

恢复活动与残留连接，核对 PID、时间与地址；宽松模式增加误报。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--include-corrupt` | 布尔开关 | false | 否 | 放宽网络对象有效性检查，包含部分覆盖或损坏数据；需额外核验误报。 |

</details>

<details>
<summary>windows.netstat.NetStat — 遍历内核网络跟踪结构</summary>

获得结构枚举的网络视图，与 netscan 的扫描结果比较覆盖。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--include-corrupt` | 布尔开关 | false | 否 | 放宽网络对象有效性检查，包含部分覆盖或损坏数据；需额外核验误报。 |

</details>

<details>
<summary>windows.orphan_kernel_threads.Threads — 寻找启动地址无法归属已知模块的内核线程</summary>

关联 System 及相关内核进程的活动线程，复核入口字节和模块缺口。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.pe_symbols.PESymbols — 在内核或进程 PE 中解析符号与地址</summary>

按模块解析函数名或反查地址，辅助解释回调、导入和线程入口。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--source` | 字符串枚举：kernel, processes | None（未显式设置） | 是 | 选择在 kernel 或 processes 地址空间中解析 PE 符号。 |
| `--module` | 字符串 | None（未显式设置） | 是 | 要解析的模块名；基础内核可用 ntoskrnl.exe。 |
| `--symbols` | 字符串列表（空格分隔） | None（未显式设置） | 否 | 要解析的符号名称列表。 |
| `--addresses` | 整数列表（空格分隔） | None（未显式设置） | 否 | 要反查符号的地址列表，整数可用十进制或 0x 前缀。 |

</details>

<details>
<summary>windows.pedump.PEDump — 按指定地址空间与基址重建 PE</summary>

从已定位的进程或内核虚拟基址恢复 PE；基址不是镜像物理偏移。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--base` | 整数（十进制或 0x） | None（未显式设置） | 是 | 要重建 ELF/PE 的虚拟基址，必须属于已选地址空间；不是物理偏移。 |
| `--kernel-module` | 布尔开关 | false | 否 | 从内核地址空间重建 PE；默认使用相应进程地址空间。 |

</details>

<details>
<summary>windows.poolscanner.PoolScanner — 执行内核池对象扫描</summary>

理解池标签扫描覆盖并寻找对象候选；对象有效性需由对应专用插件核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.privileges.Privs — 列出进程 token 特权</summary>

检查调试、备份等高权限及启用状态，结合身份与合法用途判断。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.processghosting.ProcessGhosting — 检查删除挂起、缺失文件对象和 DeleteOnClose 映像</summary>

寻找进程映像文件生命周期异常，结合文件对象与 VAD 判读。

兼容旧名，规范命令为 `windows.malware.processghosting.ProcessGhosting`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.pslist.PsList — 沿活动进程链表枚举并可重建主 PE</summary>

建立进程基线；dump 从进程主映像重建 PE，不导出全部进程内存。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--physical` | 布尔开关 | false | 否 | 把结果中的对象偏移显示为物理偏移；不改变导出对象，也不表示导出物理层。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 重建进程主可执行 PE；不导出完整进程地址空间。 |

</details>

<details>
<summary>windows.psscan.PsScan — 扫描进程对象并可重建主 PE</summary>

发现链表外、结束或隐藏进程候选；dump 与 pslist 一样重建主 PE。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 重建扫描到的进程主可执行 PE；不导出全部进程内存。 |
| `--physical` | 布尔开关 | false | 否 | 把结果中的对象偏移显示为物理偏移；不改变导出对象，也不表示导出物理层。 |

</details>

<details>
<summary>windows.pstree.PsTree — 按父 PID 展示进程树</summary>

追踪启动链；指定 PID 时保留其祖先和后代，PID 重用须结合时间核验。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--physical` | 布尔开关 | false | 否 | 把结果中的对象偏移显示为物理偏移；不改变导出对象，也不表示导出物理层。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 包含指定 PID 及其祖先与后代；不是只输出该 PID。 |

</details>

<details>
<summary>windows.psxview.PsXView — 交叉比较四种进程发现视图</summary>

发现链表外或某视图遗漏的进程；结束进程、采集不同步也会产生差异。

兼容旧名，规范命令为 `windows.malware.psxview.PsXView`；下面列出其继承的全部 CLI 参数。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--physical-offsets` | 布尔开关 | None（未显式设置） | 否 | 把进程对象偏移显示为物理偏移；源码默认 None，提供选项时为 True。 |

</details>

<details>
<summary>windows.registry.amcache.Amcache — 解析 Amcache 中应用程序相关记录</summary>

寻找路径、文件属性及应用关联线索；记录存在不能单独证明执行。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.cachedump.Cachedump — 提取缓存域登录凭据记录</summary>

在授权镜像中核对缓存账户与域信息；结果不同于 SAM 哈希及通用 LSA secrets。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.certificates.Certificates — 列出注册表证书存储并可导出证书</summary>

核对证书主体、指纹与异常证书植入，再与系统证书配置交叉验证。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 导出列出的证书。 |

</details>

<details>
<summary>windows.registry.getcellroutine.GetCellRoutine — 检查 hive 的 GetCellRoutine 回调</summary>

发现注册表取单元路径上的异常处理函数，关联合法模块。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.hashdump.Hashdump — 提取 SAM 本地账户口令哈希</summary>

在授权镜像中核对本地账户证据；不把提取结果写进公开笔记。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.hivelist.HiveList — 枚举已挂载 hive 并可导出</summary>

建立 SYSTEM、SOFTWARE、用户 hive 等证据入口，恢复可读 hive 内容。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--filter` | 字符串 | None（未显式设置） | 否 | 按 hive 名称中的字符串筛选，不是正则表达式。 |
| `--dump` | 布尔开关 | false | 否 | 导出列出的注册表 hive 可读内容。 |

</details>

<details>
<summary>windows.registry.hivescan.HiveScan — 扫描注册表 hive 结构</summary>

寻找枚举遗漏或残留 hive，与 hivelist 核对可读性和名称。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.lsadump.Lsadump — 提取 SECURITY hive 中的 LSA secrets</summary>

在授权镜像中核对服务或系统凭据相关证据；与域登录缓存分开判读。

需要兼容 Crypto/Cryptodome 的加密依赖及匹配 hive；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.printkey.PrintKey — 读取 hive 中指定键和值</summary>

从明确 hive 偏移与键路径检查启动项、服务或配置，递归时注意覆盖范围。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--offset` | 整数（十进制或 0x） | None（未显式设置） | 否 | 指定 hive 的内存偏移，使用 hivelist/hivescan 的对应地址语义。 |
| `--key` | 字符串 | None（未显式设置） | 否 | 从指定注册表键路径开始枚举。 |
| `--recurse` | 布尔开关 | false | 否 | 递归枚举子键；未提供时只枚举当前层。 |

</details>

<details>
<summary>windows.registry.scheduled_tasks.ScheduledTasks — 解析注册表计划任务信息</summary>

核对触发器、动作及时间，和任务文件、日志交叉验证持久化。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.registry.userassist.UserAssist — 解析用户 UserAssist 项</summary>

提取 GUI 应用交互相关线索；计数和时间需结合系统版本及其他执行证据。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--offset` | 整数（十进制或 0x） | None（未显式设置） | 否 | 指定 hive 的内存偏移，使用 hivelist/hivescan 的对应地址语义。 |

</details>

<details>
<summary>windows.scheduled_tasks.ScheduledTasks — 解析注册表计划任务信息</summary>

核对触发器、动作及时间，和任务文件、日志交叉验证持久化。

兼容旧名，规范命令为 `windows.registry.scheduled_tasks.ScheduledTasks`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.sessions.Sessions — 从进程环境变量提取会话信息</summary>

区分交互用户与会话背景，和 SID、命令行关联。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.shimcachemem.ShimcacheMem — 从 ahcache.sys 的 AVL 树读取 Shimcache</summary>

恢复应用兼容性缓存路径与时间线索；不能单凭缓存记录确认执行。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.skeleton_key_check.Skeleton_Key_Check — 检查 Skeleton Key 相关内存异常特征</summary>

在适用系统中复核认证组件的候选篡改，不能仅凭一个特征判定感染。

兼容旧名，规范命令为 `windows.malware.skeleton_key_check.Skeleton_Key_Check`；下面列出其继承的全部 CLI 参数。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.ssdt.SSDT — 列出系统调用表及函数归属</summary>

把表项映射到模块与符号，复核异常入口。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.statistics.Statistics — 统计内存空间有效、无效、交换及大页等情况</summary>

评估地址空间解析覆盖与缺页，解释其他插件无法读取的区域。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.strings.Strings — 把带物理偏移的字符串结果映射到进程</summary>

将外部字符串提取的地址关联到进程；字符串文件格式和偏移基准必须正确。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--strings-file` | URI/本地路径 | None（未显式设置） | 是 | 外部 strings 输出文件，必须含该插件可识别的物理偏移与字符串；不同输出格式不能混用。 |

</details>

<details>
<summary>windows.suspended_threads.SuspendedThreads — 枚举挂起线程</summary>

寻找异常挂起状态及相关进程；正常应用也可能合法挂起线程。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.suspicious_threads.SuspiciousThreads — 枚举有可疑启动位置等异常的用户线程</summary>

把线程入口与所属 VAD、模块对齐，寻找注入执行链。

兼容旧名，规范命令为 `windows.malware.suspicious_threads.SuspiciousThreads`；下面列出其继承的全部 CLI 参数。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.svcdiff.SvcDiff — 交叉比较服务链表与扫描结果</summary>

识别链表遗漏的服务记录；残留与停止服务需进一步核验。

兼容旧名，规范命令为 `windows.malware.svcdiff.SvcDiff`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.svclist.SvcList — 沿 services.exe 服务链表枚举服务</summary>

建立结构枚举的服务视图，和 svcscan、注册表配置交叉核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.svcscan.SvcScan — 扫描服务记录</summary>

寻找残留或链表外服务，关联状态、映像路径与进程。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.symlinkscan.SymlinkScan — 扫描对象管理器符号链接</summary>

调查设备名或对象路径重定向，和设备树、句柄对应。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.thrdscan.ThrdScan — 扫描线程对象</summary>

恢复活动及残留线程候选，核对拥有进程、入口与时间。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.threads.Threads — 列出进程线程</summary>

建立线程视图，和 thrdscan、可疑线程插件交叉核验。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.timers.Timers — 列出内核定时器及 DPC 模块归属</summary>

调查定时执行入口是否指向未知模块或异常地址。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.truecrypt.Passphrase — 查找 TrueCrypt 缓存口令候选</summary>

在适用旧版软件的授权镜像中恢复候选；最小长度筛选不保证命中正确口令。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--min-length` | 整数（十进制或 0x） | 5 | 否 | 口令候选最小字符长度；增加长度可减少短字符串误报。 |

</details>

<details>
<summary>windows.unhooked_system_calls.unhooked_system_calls — 检测进程 ntdll 系统调用 stub 的钩子</summary>

核对函数入口异常；插件名不代表输出规避检测的操作。

兼容旧名，规范命令为 `windows.malware.unhooked_system_calls.UnhookedSystemCalls`；下面列出其继承的全部 CLI 参数。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.unloadedmodules.UnloadedModules — 列出已卸载内核模块记录</summary>

补充驱动生命周期线索；记录数量有限，缺失不代表从未加载。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.vadinfo.VadInfo — 列出 VAD 范围、权限、文件并可导出</summary>

定位进程虚拟地址对应区域；导出是 VAD 字节，大小阈值会跳过较大区域。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--address` | 整数（十进制或 0x） | None（未显式设置） | 否 | 只显示包含该进程虚拟地址的 VAD，参数是单个整数。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 导出筛选后的 VAD 原始区域字节；受 maxsize 限制。 |
| `--maxsize` | 整数（十进制或 0x） | 1073741824 | 否 | 可导出 VMA/VAD 区域的最大字节数，超限区域跳过。 |

</details>

<details>
<summary>windows.vadregexscan.VadRegExScan — 在进程 VAD 中搜索正则表达式</summary>

按 PID 查找配置、路径或文本，保留虚拟地址与上下文核验。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--pattern` | 字符串 | None（未显式设置） | 是 | 要匹配的正则表达式；在 shell 中正确引用特殊字符。 |
| `--maxsize` | 整数（十进制或 0x） | 128 | 否 | 命中后显示的上下文字节上限；不是扫描范围大小。 |

</details>

<details>
<summary>windows.vadwalk.VadWalk — 遍历进程 VAD 树</summary>

核对虚拟地址空间树结构与范围，辅助调查损坏或异常映射。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.vadyarascan.VadYaraScan — 在进程 VAD 中执行 YARA 扫描</summary>

定位规则命中所在进程与虚拟地址，再和 VAD 属性、线程入口对应。

需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 构建字符串规则时忽略大小写；显式规则文件仍以文件内定义为准。 |
| `--wide` | 布尔开关 | false | 否 | 构建字符串规则时匹配宽字符字符串；显式规则文件仍以规则定义为准。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 提供字符串模式；以 { 开头按十六进制模式、以 / 开头按正则模式处理，其他内容会包成引号字符串；完整规则使用 yara-file。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | YARA 规则文件路径或 URI。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 已编译 YARA 规则文件路径或 URI，须兼容当前 YARA 引擎。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 源码声明的最大大小选项，但此版本相关扫描实现未读取该配置；不要依靠它改变扫描上限。Linux VMA/Windows VAD 扫描另用固定 1 GiB 检查。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>windows.verinfo.VerInfo — 提取内存 PE 的版本资源</summary>

核对模块产品、版本与名称；extensive 扫描物理层，结果可含残留。

需要 pefile 及对应依赖（可为传递依赖）；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--extensive` | 布尔开关 | false | 否 | 在物理层扫描 PE 版本资源，可能包含不属于当前加载模块的残留。 |

</details>

<details>
<summary>windows.virtmap.VirtMap — 列出内核虚拟映射分区</summary>

了解内核虚拟空间区域与布局，辅助解释内核地址。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.windows.Windows — 枚举桌面中的窗口对象</summary>

恢复窗口标题和关联对象线索，结合桌面、窗口站与进程核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>windows.windowstations.WindowStations — 扫描顶层窗口站对象</summary>

建立会话图形对象入口，为桌面及窗口枚举提供上下文。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

</details>

### Linux：60 个命令

<details>
<summary>展开 Volatility 3 Linux 内置插件目录（60 项）</summary>

<details>
<summary>Linux 完整插件总表</summary>

| 完整命令 | 中文作用 | 典型应用 | 依赖与兼容旧名 |
| --- | --- | --- | --- |
| `linux.bash.Bash` | 恢复进程内 Bash 命令历史 | 关联可疑 shell 的命令、PID 与时间；未命中不能证明命令没有执行。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.boottime.Boottime` | 提取系统启动时间 | 与进程创建、日志和取证采集时间交叉检查时间线。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.capabilities.Capabilities` | 列出进程 Linux capabilities | 调查高权限进程或能力配置异常；结合 UID、命令行与合法服务配置判读。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.check_afinfo.Check_afinfo` | 检查网络协议操作函数指针 | 寻找指向异常模块或未知地址的协议回调，结合符号和模块范围核验。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.check_afinfo.Check_afinfo`。 |
| `linux.check_creds.Check_creds` | 检查进程共享的凭据结构 | 发现不寻常的凭据共享或篡改线索；正常共享及线程关系也需排除。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.check_creds.Check_creds`。 |
| `linux.check_idt.Check_idt` | 检查中断描述符表处理函数 | 将中断入口与合法内核、模块范围比对，调查内核级钩子。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.check_idt.Check_idt`。 |
| `linux.check_modules.Check_modules` | 比较模块链表与 sysfs 模块视图 | 发现视图不一致和隐藏模块候选；sysfs 不可用会降低证据覆盖。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.check_modules.Check_modules`。 |
| `linux.check_syscall.Check_syscall` | 检查系统调用表的函数指针 | 查找表项是否偏离预期符号或模块，调查系统调用钩子。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.check_syscall.Check_syscall`。 |
| `linux.ebpf.EBPF` | 枚举内存中的 eBPF 程序 | 调查异常网络或内核观测逻辑，关联程序类型、名称及挂载上下文。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.elfs.Elfs` | 列出进程映射的 ELF 并可重建文件 | 识别共享库、内存映射 ELF 与可疑模块；重建结果是内存态文件，可能与磁盘原件不同。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.envars.Envars` | 列出进程环境变量 | 寻找运行目录、代理、加载器和配置线索；环境值可被进程修改。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.graphics.fbdev.Fbdev` | 枚举并导出 fbdev 帧缓冲 | 采集显示残留作为辅助界面证据；只适用于可解析的 fbdev，不承诺现代 GPU 完整画面。 | 需要 Pillow/PIL 才能实际解析并导出帧缓冲；还需匹配 fbdev 内核结构。 |
| `linux.hidden_modules.Hidden_modules` | 通过内存扫描寻找隐藏内核模块 | 补充链表枚举遗漏的模块候选；扫描命中可能包含残留或损坏对象。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.hidden_modules.Hidden_modules`。 |
| `linux.iomem.IOMem` | 列出类似 /proc/iomem 的资源映射 | 了解物理地址区域与设备资源，辅助解释镜像中的内存空洞。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.ip.Addr` | 列出网络设备的地址信息 | 核对接口、IPv4/IPv6 地址和网络命名空间线索。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.ip.Link` | 列出网络接口链路属性 | 识别容器、虚拟接口和异常链路，结合 Addr 与套接字结果分析。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.kallsyms.Kallsyms` | 枚举内核、模块、ftrace 与 BPF 符号 | 把回调或可疑指针解析到符号；不带筛选选项时包含全部四类。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.keyboard_notifiers.Keyboard_notifiers` | 解析键盘通知回调链 | 调查异常键盘监听，核对回调地址的模块与合法用途。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.keyboard_notifiers.Keyboard_notifiers`。 |
| `linux.kmsg.Kmsg` | 读取内核日志缓冲 | 查找模块加载、设备故障等时间线索；环形缓冲覆盖会造成缺口。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.kthreads.Kthreads` | 枚举内核线程及其函数 | 识别不熟悉的内核线程入口，关联模块与符号验证。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.library_list.LibraryList` | 枚举进程加载的库 | 比较预期依赖与实际加载库，检查可疑库路径和进程关联。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.lsmod.Lsmod` | 枚举已加载内核模块并可导出 | 建立模块清单，和扫描、sysfs 视图交叉比较；导出是内存态重建。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.lsof.Lsof` | 列出进程打开的文件描述符 | 关联可疑进程与文件、管道等对象；需文件时用 files-only 筛选。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malfind.Malfind` | 查找可疑进程 VMA 与脏页 | 调查注入或修改后的可执行区域；结合 VMA 权限、映射来源和字节验证，启发式命中不是恶意定论。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.malfind.Malfind`。 |
| `linux.malware.check_afinfo.Check_afinfo` | 检查网络协议操作函数指针 | 寻找指向异常模块或未知地址的协议回调，结合符号和模块范围核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.check_creds.Check_creds` | 检查进程共享的凭据结构 | 发现不寻常的凭据共享或篡改线索；正常共享及线程关系也需排除。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.check_idt.Check_idt` | 检查中断描述符表处理函数 | 将中断入口与合法内核、模块范围比对，调查内核级钩子。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.check_modules.Check_modules` | 比较模块链表与 sysfs 模块视图 | 发现视图不一致和隐藏模块候选；sysfs 不可用会降低证据覆盖。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.check_syscall.Check_syscall` | 检查系统调用表的函数指针 | 查找表项是否偏离预期符号或模块，调查系统调用钩子。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.hidden_modules.Hidden_modules` | 通过内存扫描寻找隐藏内核模块 | 补充链表枚举遗漏的模块候选；扫描命中可能包含残留或损坏对象。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.keyboard_notifiers.Keyboard_notifiers` | 解析键盘通知回调链 | 调查异常键盘监听，核对回调地址的模块与合法用途。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.malfind.Malfind` | 查找可疑进程 VMA 与脏页 | 调查注入或修改后的可执行区域；结合 VMA 权限、映射来源和字节验证，启发式命中不是恶意定论。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.modxview.Modxview` | 交叉展示模块枚举、扫描与 taint 信息 | 统一比较 lsmod、check_modules、hidden_modules 的覆盖差异，优先复核不一致模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.netfilter.Netfilter` | 列出 Netfilter 钩子 | 调查网络过滤路径的异常回调，关联模块、命名空间与合法防火墙组件。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.process_spoofing.ProcessSpoofing` | 比较可执行文件路径、cmdline 与 comm | 发现进程名称伪装；合法改名和启动参数差异需结合实际映射文件排除。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.malware.tty_check.Tty_Check` | 检查 TTY 设备操作钩子 | 调查终端输入监控或篡改，核验函数指针所属模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.module_extract.ModuleExtract` | 按内核虚拟基址重建 ELF 模块 | 已定位模块地址但常规枚举遗漏时导出；给出内核地址而非镜像文件偏移。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.modxview.Modxview` | 交叉展示模块枚举、扫描与 taint 信息 | 统一比较 lsmod、check_modules、hidden_modules 的覆盖差异，优先复核不一致模块。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.modxview.Modxview`。 |
| `linux.mountinfo.MountInfo` | 列出进程挂载命名空间与挂载点 | 解释容器中的路径视图，结合 PID 和 mount namespace 过滤比较。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.netfilter.Netfilter` | 列出 Netfilter 钩子 | 调查网络过滤路径的异常回调，关联模块、命名空间与合法防火墙组件。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.netfilter.Netfilter`。 |
| `linux.pagecache.Files` | 枚举内存页缓存相关文件 | 按路径和类型寻找文件证据，为 InodePages 提供 inode 地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pagecache.InodePages` | 列出并导出指定 inode 的缓存页 | 恢复仍驻留页缓存的文件片段；缓存缺页不能据此推断原文件完整内容。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pagecache.RecoverFs` | 把可恢复缓存目录、文件和符号链接写入压缩包 | 批量恢复内存仍保留的文件系统视图；不保留原元数据，导出对象时间为运行时间。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pidhashtable.PIDHashTable` | 通过 PID 哈希表枚举任务 | 与任务链表和扫描结果交叉核验隐藏或残留进程。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.proc.Maps` | 列出并可导出进程 VMA | 定位地址对应区域、权限与映射文件；导出是区域字节，不能当作整个进程镜像。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.psaux.PsAux` | 列出进程及命令行参数 | 建立启动参数视图，关联进程树与环境变量解释可疑运行行为。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pscallstack.PsCallStack` | 枚举任务调用栈 | 调查线程正在执行的路径；未解析栈值需结合符号和栈地址复核。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pslist.PsList` | 沿任务链表枚举进程和可选用户线程 | 建立活动任务基线；dump 重建主 ELF，不导出完整进程地址空间。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.psscan.PsScan` | 在内存中扫描任务结构 | 发现链表外的隐藏、结束或残留任务；和 pslist、PID 哈希表核验对象有效性。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.pstree.PsTree` | 按父进程关系展示任务树 | 追踪 shell、下载器或服务的派生链；父子关系需结合创建时间与命令行。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.ptrace.Ptrace` | 枚举 ptrace 跟踪者与被跟踪任务 | 调查调试、注入或异常进程控制关系，排除合法调试器。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.sockscan.Sockscan` | 扫描内存中的套接字与连接对象 | 补充常规枚举遗漏的网络对象；注意关闭连接和残留对象。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.sockstat.Sockstat` | 枚举进程套接字及网络命名空间 | 把端点与拥有进程关联，区分宿主和容器网络视图。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.tracing.ftrace.CheckFtrace` | 检查 ftrace 注册回调和钩子 | 定位内核函数追踪路径的异常回调，结合 flags 与符号复核。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.tracing.perf_events.PerfEvents` | 列出任务相关性能事件 | 调查性能监控、探针及异常追踪用途；合法观测工具也会产生事件。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.tracing.tracepoints.CheckTracepoints` | 检查 tracepoint 探针与回调 | 寻找追踪子系统的异常挂载点，核对回调模块和合法用途。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.tty_check.tty_check` | 检查 TTY 设备操作钩子 | 调查终端输入监控或篡改，核验函数指针所属模块。 | 兼容旧名，此固定版仍提供；优先使用 `linux.malware.tty_check.Tty_Check`。 |
| `linux.vmaregexscan.VmaRegExScan` | 在任务 VMA 中搜索正则表达式 | 针对指定进程寻找路径、文本或配置线索，并保留 PID 和虚拟地址。 | 需匹配的层、内核符号及对应镜像结构。 |
| `linux.vmayarascan.VmaYaraScan` | 在任务 VMA 中执行 YARA 扫描 | 按 PID 搜索恶意代码特征或文本，和 Maps、malfind 的区域属性交叉核验。 | 需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。 |
| `linux.vmcoreinfo.VMCoreInfo` | 枚举 VMCoreInfo 表 | 寻找内核布局与转储相关元数据，辅助确认内核信息和镜像解析边界。 | 需匹配的层、内核符号及对应镜像结构。 |

</details>

完整参数表（含从父类或替代类继承的需求）：

<details>
<summary>linux.bash.Bash — 恢复进程内 Bash 命令历史</summary>

关联可疑 shell 的命令、PID 与时间；未命中不能证明命令没有执行。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>linux.boottime.Boottime — 提取系统启动时间</summary>

与进程创建、日志和取证采集时间交叉检查时间线。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.capabilities.Capabilities — 列出进程 Linux capabilities</summary>

调查高权限进程或能力配置异常；结合 UID、命令行与合法服务配置判读。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pids` | 整数列表（空格分隔） | None（未显式设置） | 否 | 按 PID 列表筛选；与同版本插件的 pid 参数拼写不同。 |

</details>

<details>
<summary>linux.check_afinfo.Check_afinfo — 检查网络协议操作函数指针</summary>

寻找指向异常模块或未知地址的协议回调，结合符号和模块范围核验。

兼容旧名，规范命令为 `linux.malware.check_afinfo.Check_afinfo`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.check_creds.Check_creds — 检查进程共享的凭据结构</summary>

发现不寻常的凭据共享或篡改线索；正常共享及线程关系也需排除。

兼容旧名，规范命令为 `linux.malware.check_creds.Check_creds`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.check_idt.Check_idt — 检查中断描述符表处理函数</summary>

将中断入口与合法内核、模块范围比对，调查内核级钩子。

兼容旧名，规范命令为 `linux.malware.check_idt.Check_idt`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.check_modules.Check_modules — 比较模块链表与 sysfs 模块视图</summary>

发现视图不一致和隐藏模块候选；sysfs 不可用会降低证据覆盖。

兼容旧名，规范命令为 `linux.malware.check_modules.Check_modules`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |

</details>

<details>
<summary>linux.check_syscall.Check_syscall — 检查系统调用表的函数指针</summary>

查找表项是否偏离预期符号或模块，调查系统调用钩子。

兼容旧名，规范命令为 `linux.malware.check_syscall.Check_syscall`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.ebpf.EBPF — 枚举内存中的 eBPF 程序</summary>

调查异常网络或内核观测逻辑，关联程序类型、名称及挂载上下文。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.elfs.Elfs — 列出进程映射的 ELF 并可重建文件</summary>

识别共享库、内存映射 ELF 与可疑模块；重建结果是内存态文件，可能与磁盘原件不同。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 重建列出的内存映射 ELF。 |

</details>

<details>
<summary>linux.envars.Envars — 列出进程环境变量</summary>

寻找运行目录、代理、加载器和配置线索；环境值可被进程修改。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>linux.graphics.fbdev.Fbdev — 枚举并导出 fbdev 帧缓冲</summary>

采集显示残留作为辅助界面证据；只适用于可解析的 fbdev，不承诺现代 GPU 完整画面。

需要 Pillow/PIL 才能实际解析并导出帧缓冲；还需匹配 fbdev 内核结构。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 导出可解析的 fbdev 帧缓冲。 |

</details>

<details>
<summary>linux.hidden_modules.Hidden_modules — 通过内存扫描寻找隐藏内核模块</summary>

补充链表枚举遗漏的模块候选；扫描命中可能包含残留或损坏对象。

兼容旧名，规范命令为 `linux.malware.hidden_modules.Hidden_modules`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |

</details>

<details>
<summary>linux.iomem.IOMem — 列出类似 /proc/iomem 的资源映射</summary>

了解物理地址区域与设备资源，辅助解释镜像中的内存空洞。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.ip.Addr — 列出网络设备的地址信息</summary>

核对接口、IPv4/IPv6 地址和网络命名空间线索。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.ip.Link — 列出网络接口链路属性</summary>

识别容器、虚拟接口和异常链路，结合 Addr 与套接字结果分析。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.kallsyms.Kallsyms — 枚举内核、模块、ftrace 与 BPF 符号</summary>

把回调或可疑指针解析到符号；不带筛选选项时包含全部四类。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--core` | 布尔开关 | false | 否 | 包含核心内核符号。四类筛选均未提供时包含全部。 |
| `--modules` | 布尔开关 | false | 否 | 包含内核模块符号。 |
| `--ftrace` | 布尔开关 | false | 否 | 包含 ftrace 符号。 |
| `--bpf` | 布尔开关 | false | 否 | 包含 BPF 符号。 |

</details>

<details>
<summary>linux.keyboard_notifiers.Keyboard_notifiers — 解析键盘通知回调链</summary>

调查异常键盘监听，核对回调地址的模块与合法用途。

兼容旧名，规范命令为 `linux.malware.keyboard_notifiers.Keyboard_notifiers`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.kmsg.Kmsg — 读取内核日志缓冲</summary>

查找模块加载、设备故障等时间线索；环形缓冲覆盖会造成缺口。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.kthreads.Kthreads — 枚举内核线程及其函数</summary>

识别不熟悉的内核线程入口，关联模块与符号验证。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.library_list.LibraryList — 枚举进程加载的库</summary>

比较预期依赖与实际加载库，检查可疑库路径和进程关联。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pids` | 整数列表（空格分隔） | None（未显式设置） | 否 | 按 PID 列表筛选；与同版本插件的 pid 参数拼写不同。 |

</details>

<details>
<summary>linux.lsmod.Lsmod — 枚举已加载内核模块并可导出</summary>

建立模块清单，和扫描、sysfs 视图交叉比较；导出是内存态重建。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |

</details>

<details>
<summary>linux.lsof.Lsof — 列出进程打开的文件描述符</summary>

关联可疑进程与文件、管道等对象；需文件时用 files-only 筛选。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--files-only` | 布尔开关 | false | 否 | 仅保留文件类型的描述符，排除其他描述符类型。 |

</details>

<details>
<summary>linux.malfind.Malfind — 查找可疑进程 VMA 与脏页</summary>

调查注入或修改后的可执行区域；结合 VMA 权限、映射来源和字节验证，启发式命中不是恶意定论。

兼容旧名，规范命令为 `linux.malware.malfind.Malfind`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--hexdump-size` | 整数（十进制或 0x） | 64 | 否 | 每个命中区域或页面显示的字节数；不控制导出大小。 |
| `--show-all-dirty-pages` | 布尔开关 | false | 否 | VMA 中至少发现一脏页时，显示该 VMA 的全部脏页；配合 dump-regions 时也导出这些脏页。 |
| `--dump-regions` | 布尔开关 | false | 否 | 导出可疑区域；配合 show-all-dirty-pages 可包含该 VMA 的全部脏页。 |
| `--dump-maxsize` | 整数（十进制或 0x） | 1073741824 | 否 | 可导出区域的最大字节数；超过阈值的区域跳过。 |

</details>

<details>
<summary>linux.malware.check_afinfo.Check_afinfo — 检查网络协议操作函数指针</summary>

寻找指向异常模块或未知地址的协议回调，结合符号和模块范围核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.check_creds.Check_creds — 检查进程共享的凭据结构</summary>

发现不寻常的凭据共享或篡改线索；正常共享及线程关系也需排除。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.check_idt.Check_idt — 检查中断描述符表处理函数</summary>

将中断入口与合法内核、模块范围比对，调查内核级钩子。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.check_modules.Check_modules — 比较模块链表与 sysfs 模块视图</summary>

发现视图不一致和隐藏模块候选；sysfs 不可用会降低证据覆盖。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |

</details>

<details>
<summary>linux.malware.check_syscall.Check_syscall — 检查系统调用表的函数指针</summary>

查找表项是否偏离预期符号或模块，调查系统调用钩子。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.hidden_modules.Hidden_modules — 通过内存扫描寻找隐藏内核模块</summary>

补充链表枚举遗漏的模块候选；扫描命中可能包含残留或损坏对象。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--dump` | 布尔开关 | false | 否 | 重建并导出列出的内核模块；内存态结果不能当作磁盘原件。 |

</details>

<details>
<summary>linux.malware.keyboard_notifiers.Keyboard_notifiers — 解析键盘通知回调链</summary>

调查异常键盘监听，核对回调地址的模块与合法用途。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.malfind.Malfind — 查找可疑进程 VMA 与脏页</summary>

调查注入或修改后的可执行区域；结合 VMA 权限、映射来源和字节验证，启发式命中不是恶意定论。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--hexdump-size` | 整数（十进制或 0x） | 64 | 否 | 每个命中区域或页面显示的字节数；不控制导出大小。 |
| `--show-all-dirty-pages` | 布尔开关 | false | 否 | VMA 中至少发现一脏页时，显示该 VMA 的全部脏页；配合 dump-regions 时也导出这些脏页。 |
| `--dump-regions` | 布尔开关 | false | 否 | 导出可疑区域；配合 show-all-dirty-pages 可包含该 VMA 的全部脏页。 |
| `--dump-maxsize` | 整数（十进制或 0x） | 1073741824 | 否 | 可导出区域的最大字节数；超过阈值的区域跳过。 |

</details>

<details>
<summary>linux.malware.modxview.Modxview — 交叉展示模块枚举、扫描与 taint 信息</summary>

统一比较 lsmod、check_modules、hidden_modules 的覆盖差异，优先复核不一致模块。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--plain-taints` | 布尔开关 | false | 否 | 显示模块 taint 的原始字符串，便于核对标记。 |

</details>

<details>
<summary>linux.malware.netfilter.Netfilter — 列出 Netfilter 钩子</summary>

调查网络过滤路径的异常回调，关联模块、命名空间与合法防火墙组件。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.malware.process_spoofing.ProcessSpoofing — 比较可执行文件路径、cmdline 与 comm</summary>

发现进程名称伪装；合法改名和启动参数差异需结合实际映射文件排除。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>linux.malware.tty_check.Tty_Check — 检查 TTY 设备操作钩子</summary>

调查终端输入监控或篡改，核验函数指针所属模块。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.module_extract.ModuleExtract — 按内核虚拟基址重建 ELF 模块</summary>

已定位模块地址但常规枚举遗漏时导出；给出内核地址而非镜像文件偏移。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--base` | 整数（十进制或 0x） | None（未显式设置） | 是 | 要重建 ELF/PE 的虚拟基址，必须属于已选地址空间；不是物理偏移。 |

</details>

<details>
<summary>linux.modxview.Modxview — 交叉展示模块枚举、扫描与 taint 信息</summary>

统一比较 lsmod、check_modules、hidden_modules 的覆盖差异，优先复核不一致模块。

兼容旧名，规范命令为 `linux.malware.modxview.Modxview`；下面列出其继承的全部 CLI 参数。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--plain-taints` | 布尔开关 | false | 否 | 显示模块 taint 的原始字符串，便于核对标记。 |

</details>

<details>
<summary>linux.mountinfo.MountInfo — 列出进程挂载命名空间与挂载点</summary>

解释容器中的路径视图，结合 PID 和 mount namespace 过滤比较。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pids` | 整数列表（空格分隔） | None（未显式设置） | 否 | 按 PID 列表筛选；与同版本插件的 pid 参数拼写不同。 |
| `--mntns` | 整数列表（空格分隔） | None（未显式设置） | 否 | 仅显示指定挂载命名空间标识的结果。 |
| `--mount-format` | 布尔开关 | false | 否 | 使用类似旧版 /proc/[pid]/mounts 或 mount -l 的简要格式。 |

</details>

<details>
<summary>linux.netfilter.Netfilter — 列出 Netfilter 钩子</summary>

调查网络过滤路径的异常回调，关联模块、命名空间与合法防火墙组件。

兼容旧名，规范命令为 `linux.malware.netfilter.Netfilter`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.pagecache.Files — 枚举内存页缓存相关文件</summary>

按路径和类型寻找文件证据，为 InodePages 提供 inode 地址。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--type` | 字符串列表（空格分隔） | None（未显式设置） | 否 | 按空格分隔的文件类型筛选，例如 REG DIR；不是正则表达式。 |
| `--find` | 字符串 | None（未显式设置） | 否 | 要查找的文件完整路径。 |

</details>

<details>
<summary>linux.pagecache.InodePages — 列出并导出指定 inode 的缓存页</summary>

恢复仍驻留页缓存的文件片段；缓存缺页不能据此推断原文件完整内容。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--find` | 字符串 | None（未显式设置） | 否 | 要查找的文件完整路径。 |
| `--inode` | 整数（十进制或 0x） | None（未显式设置） | 否 | 指定内存中的 inode 地址；不是磁盘 inode 编号。 |
| `--dump` | 布尔开关 | false | 否 | 导出该 inode 的驻留缓存内容；缺页与空洞需单独记录。 |

</details>

<details>
<summary>linux.pagecache.RecoverFs — 把可恢复缓存目录、文件和符号链接写入压缩包</summary>

批量恢复内存仍保留的文件系统视图；不保留原元数据，导出对象时间为运行时间。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--tmpfs-only` | 布尔开关 | false | 否 | 只恢复 tmpfs 文件系统中的缓存文件。 |
| `--compression-format` | 字符串枚举：gz, bz2, xz | "gz" | 否 | 输出 tar 归档的压缩格式。 |

</details>

<details>
<summary>linux.pidhashtable.PIDHashTable — 通过 PID 哈希表枚举任务</summary>

与任务链表和扫描结果交叉核验隐藏或残留进程。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--decorate-comm` | 布尔开关 | false | 否 | 用户线程 comm 用花括号标记，内核线程用方括号标记。 |

</details>

<details>
<summary>linux.proc.Maps — 列出并可导出进程 VMA</summary>

定位地址对应区域、权限与映射文件；导出是区域字节，不能当作整个进程镜像。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 导出筛选后的 VMA 原始区域字节；受 maxsize 限制。 |
| `--address` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含覆盖这些进程虚拟地址的 VMA/映射区段；多个地址用空格分隔。 |
| `--maxsize` | 整数（十进制或 0x） | 1073741824 | 否 | 可导出 VMA/VAD 区域的最大字节数，超限区域跳过。 |

</details>

<details>
<summary>linux.psaux.PsAux — 列出进程及命令行参数</summary>

建立启动参数视图，关联进程树与环境变量解释可疑运行行为。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>linux.pscallstack.PsCallStack — 枚举任务调用栈</summary>

调查线程正在执行的路径；未解析栈值需结合符号和栈地址复核。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--unresolved` | 布尔开关 | false | 否 | 同时显示无法解析为符号的栈值，便于人工复核。 |

</details>

<details>
<summary>linux.pslist.PsList — 沿任务链表枚举进程和可选用户线程</summary>

建立活动任务基线；dump 重建主 ELF，不导出完整进程地址空间。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--threads` | 布尔开关 | false | 否 | 在进程结果中包含用户线程。 |
| `--decorate-comm` | 布尔开关 | false | 否 | 用户线程 comm 用花括号标记，内核线程用方括号标记。 |
| `--dump` | 布尔开关 | false | 否 | 从主映像对应 VMA 重建进程主 ELF；不导出全部进程内存。 |

</details>

<details>
<summary>linux.psscan.PsScan — 在内存中扫描任务结构</summary>

发现链表外的隐藏、结束或残留任务；和 pslist、PID 哈希表核验对象有效性。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.pstree.PsTree — 按父进程关系展示任务树</summary>

追踪 shell、下载器或服务的派生链；父子关系需结合创建时间与命令行。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--threads` | 布尔开关 | false | 否 | 在进程结果中包含用户线程。 |
| `--decorate-comm` | 布尔开关 | false | 否 | 用户线程 comm 用花括号标记，内核线程用方括号标记。 |

</details>

<details>
<summary>linux.ptrace.Ptrace — 枚举 ptrace 跟踪者与被跟踪任务</summary>

调查调试、注入或异常进程控制关系，排除合法调试器。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.sockscan.Sockscan — 扫描内存中的套接字与连接对象</summary>

补充常规枚举遗漏的网络对象；注意关闭连接和残留对象。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.sockstat.Sockstat — 枚举进程套接字及网络命名空间</summary>

把端点与拥有进程关联，区分宿主和容器网络视图。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pids` | 整数列表（空格分隔） | None（未显式设置） | 否 | 按根 PID 命名空间中的 PID 列表筛选进程。 |
| `--netns` | 整数（十进制或 0x） | None（未显式设置） | 否 | 仅显示指定网络命名空间标识的结果。 |

</details>

<details>
<summary>linux.tracing.ftrace.CheckFtrace — 检查 ftrace 注册回调和钩子</summary>

定位内核函数追踪路径的异常回调，结合 flags 与符号复核。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--show-ftrace-flags` | 布尔开关 | false | 否 | 显示 ftrace_ops 对应的 flags。 |

</details>

<details>
<summary>linux.tracing.perf_events.PerfEvents — 列出任务相关性能事件</summary>

调查性能监控、探针及异常追踪用途；合法观测工具也会产生事件。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.tracing.tracepoints.CheckTracepoints — 检查 tracepoint 探针与回调</summary>

寻找追踪子系统的异常挂载点，核对回调模块和合法用途。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.tty_check.tty_check — 检查 TTY 设备操作钩子</summary>

调查终端输入监控或篡改，核验函数指针所属模块。

兼容旧名，规范命令为 `linux.malware.tty_check.Tty_Check`；下面列出其继承的全部 CLI 参数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>linux.vmaregexscan.VmaRegExScan — 在任务 VMA 中搜索正则表达式</summary>

针对指定进程寻找路径、文本或配置线索，并保留 PID 和虚拟地址。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--pattern` | 字符串 | None（未显式设置） | 是 | 要匹配的正则表达式；在 shell 中正确引用特殊字符。 |
| `--maxsize` | 整数（十进制或 0x） | 128 | 否 | 命中后显示的上下文字节上限；不是扫描范围大小。 |

</details>

<details>
<summary>linux.vmayarascan.VmaYaraScan — 在任务 VMA 中执行 YARA 扫描</summary>

按 PID 搜索恶意代码特征或文本，和 Maps、malfind 的区域属性交叉核验。

需要 YARA 引擎及对应可选依赖；缺失可导致插件无法导入。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 构建字符串规则时忽略大小写；显式规则文件仍以文件内定义为准。 |
| `--wide` | 布尔开关 | false | 否 | 构建字符串规则时匹配宽字符字符串；显式规则文件仍以规则定义为准。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 提供字符串模式；以 { 开头按十六进制模式、以 / 开头按正则模式处理，其他内容会包成引号字符串；完整规则使用 yara-file。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | YARA 规则文件路径或 URI。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 已编译 YARA 规则文件路径或 URI，须兼容当前 YARA 引擎。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 源码声明的最大大小选项，但此版本相关扫描实现未读取该配置；不要依靠它改变扫描上限。Linux VMA/Windows VAD 扫描另用固定 1 GiB 检查。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>linux.vmcoreinfo.VMCoreInfo — 枚举 VMCoreInfo 表</summary>

寻找内核布局与转储相关元数据，辅助确认内核信息和镜像解析边界。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

</details>

### macOS：23 个命令

<details>
<summary>展开 Volatility 3 macOS 内置插件目录（23 项）</summary>

此版本已标记 macOS 支持弃用。下面仍完整列出已有命令；其存在不代表支持 Apple Silicon 或新版 macOS。分析前须核对旧版 Intel 内核与匹配 ISF。

<details>
<summary>macOS 完整插件总表</summary>

| 完整命令 | 中文作用 | 典型应用 | 依赖与兼容旧名 |
| --- | --- | --- | --- |
| `mac.bash.Bash` | 恢复 Bash 历史残留 | 关联旧版 Intel macOS 进程中的 shell 命令与其他时间证据。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.check_syscall.Check_syscall` | 检查系统调用表入口 | 核对入口是否属于预期内核或模块，调查内核钩子。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.check_sysctl.Check_sysctl` | 检查 sysctl 处理函数 | 发现配置查询处理路径的异常函数指针。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.check_trap_table.Check_trap_table` | 检查 Mach trap 表 | 核验 Mach 系统调用入口，调查异常内核处理函数。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.dmesg.Dmesg` | 读取内核日志缓冲 | 恢复启动、模块和错误线索；缓冲覆盖与内核支持范围影响完整性。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.ifconfig.Ifconfig` | 列出网络接口信息 | 核对内存中的接口和地址，补充网络连接调查。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.kauth_listeners.Kauth_listeners` | 列出 kauth 监听器及状态 | 调查授权事件监听与异常回调，关联所属模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.kauth_scopes.Kauth_scopes` | 列出 kauth 授权作用域 | 检查作用域与监听关系，辅助定位授权路径异常。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.kevents.Kevents` | 列出进程注册的事件处理项 | 调查进程监听的文件、套接字等事件及相关行为。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.list_files.List_Files` | 枚举内存中的 vnode 文件及路径 | 寻找文件名、路径残留并和进程文件描述符结果交叉核验。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.lsmod.Lsmod` | 列出已加载内核模块 | 建立扩展模块清单，核对回调和钩子的模块归属。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.lsof.Lsof` | 列出各进程打开的文件描述符 | 把文件、管道等对象与 PID 关联，定位进程操作的文件。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.malfind.Malfind` | 查找可能含注入代码的进程映射区域 | 复核可疑权限、字节与映射来源；结果是启发式候选。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.mount.Mount` | 列出内存中的文件系统挂载信息 | 解释路径所在卷、设备及挂载上下文。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.netstat.Netstat` | 列出进程网络连接 | 关联端点、套接字和进程，结合接口信息判断网络行为。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.proc_maps.Maps` | 列出并可导出进程虚拟映射区域 | 按虚拟地址定位映射与文件；普通映射枚举本身不等于注入检测。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.psaux.Psaux` | 恢复程序命令行参数 | 核对进程实际启动参数，和进程名、父进程交叉比较。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.pslist.PsList` | 以多种内核结构枚举进程 | 切换 tasks、allproc 等方法对比覆盖；方法不一致需核验对象状态。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.pstree.PsTree` | 展示进程父子关系树 | 追踪 shell 与应用派生关系，配合命令行和时间证据。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.socket_filters.Socket_filters` | 枚举内核套接字过滤器 | 定位网络数据路径上的过滤回调和异常模块。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.timers.Timers` | 检查内核定时器及回调 | 调查指向异常地址或模块的定时执行入口。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.trustedbsd.Trustedbsd` | 检查 TrustedBSD 策略模块 | 核对安全策略回调归属，寻找异常模块与钩子。 | 需匹配的层、内核符号及对应镜像结构。 |
| `mac.vfsevents.VFSevents` | 列出过滤文件系统事件的进程 | 调查文件活动监控与异常事件过滤。 | 需匹配的层、内核符号及对应镜像结构。 |

</details>

完整参数表（含从父类或替代类继承的需求）：

<details>
<summary>mac.bash.Bash — 恢复 Bash 历史残留</summary>

关联旧版 Intel macOS 进程中的 shell 命令与其他时间证据。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.check_syscall.Check_syscall — 检查系统调用表入口</summary>

核对入口是否属于预期内核或模块，调查内核钩子。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.check_sysctl.Check_sysctl — 检查 sysctl 处理函数</summary>

发现配置查询处理路径的异常函数指针。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.check_trap_table.Check_trap_table — 检查 Mach trap 表</summary>

核验 Mach 系统调用入口，调查异常内核处理函数。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.dmesg.Dmesg — 读取内核日志缓冲</summary>

恢复启动、模块和错误线索；缓冲覆盖与内核支持范围影响完整性。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.ifconfig.Ifconfig — 列出网络接口信息</summary>

核对内存中的接口和地址，补充网络连接调查。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.kauth_listeners.Kauth_listeners — 列出 kauth 监听器及状态</summary>

调查授权事件监听与异常回调，关联所属模块。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.kauth_scopes.Kauth_scopes — 列出 kauth 授权作用域</summary>

检查作用域与监听关系，辅助定位授权路径异常。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.kevents.Kevents — 列出进程注册的事件处理项</summary>

调查进程监听的文件、套接字等事件及相关行为。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.list_files.List_Files — 枚举内存中的 vnode 文件及路径</summary>

寻找文件名、路径残留并和进程文件描述符结果交叉核验。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.lsmod.Lsmod — 列出已加载内核模块</summary>

建立扩展模块清单，核对回调和钩子的模块归属。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.lsof.Lsof — 列出各进程打开的文件描述符</summary>

把文件、管道等对象与 PID 关联，定位进程操作的文件。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.malfind.Malfind — 查找可能含注入代码的进程映射区域</summary>

复核可疑权限、字节与映射来源；结果是启发式候选。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.mount.Mount — 列出内存中的文件系统挂载信息</summary>

解释路径所在卷、设备及挂载上下文。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.netstat.Netstat — 列出进程网络连接</summary>

关联端点、套接字和进程，结合接口信息判断网络行为。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.proc_maps.Maps — 列出并可导出进程虚拟映射区域</summary>

按虚拟地址定位映射与文件；普通映射枚举本身不等于注入检测。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |
| `--dump` | 布尔开关 | false | 否 | 导出筛选后的虚拟映射区域字节；受 maxsize 限制。 |
| `--address` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含覆盖这些进程虚拟地址的 VMA/映射区段；多个地址用空格分隔。 |
| `--maxsize` | 整数（十进制或 0x） | 1073741824 | 否 | 可导出 VMA/VAD 区域的最大字节数，超限区域跳过。 |

</details>

<details>
<summary>mac.psaux.Psaux — 恢复程序命令行参数</summary>

核对进程实际启动参数，和进程名、父进程交叉比较。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.pslist.PsList — 以多种内核结构枚举进程</summary>

切换 tasks、allproc 等方法对比覆盖；方法不一致需核验对象状态。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pslist-method` | 字符串枚举：tasks, allproc, process_group, sessions, pid_hash_table | "tasks" | 否 | 选择进程枚举结构；不同方法的覆盖可能不同。 |
| `--pid` | 整数列表（空格分隔） | None（未显式设置） | 否 | 只包含指定 PID；省略时不按 PID 筛选。 |

</details>

<details>
<summary>mac.pstree.PsTree — 展示进程父子关系树</summary>

追踪 shell 与应用派生关系，配合命令行和时间证据。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.socket_filters.Socket_filters — 枚举内核套接字过滤器</summary>

定位网络数据路径上的过滤回调和异常模块。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.timers.Timers — 检查内核定时器及回调</summary>

调查指向异常地址或模块的定时执行入口。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.trustedbsd.Trustedbsd — 检查 TrustedBSD 策略模块</summary>

核对安全策略回调归属，寻找异常模块与钩子。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>mac.vfsevents.VFSevents — 列出过滤文件系统事件的进程</summary>

调查文件活动监控与异常事件过滤。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

</details>

### 通用：9 个命令

<details>
<summary>展开 Volatility 3 通用内置插件目录（9 项）</summary>

<details>
<summary>通用 完整插件总表</summary>

| 完整命令 | 中文作用 | 典型应用 | 依赖与兼容旧名 |
| --- | --- | --- | --- |
| `banners.Banners` | 搜索潜在 Linux 内核 banner | 镜像内核版本未知时定位版本字符串，再与精确匹配的 ISF 核验；命中字符串不能单独证明系统版本。 | 需要可读取的扫描层；扫描 banner 本身不要求匹配内核符号。 |
| `configwriter.ConfigWriter` | 运行自动识别并导出层、符号等配置 | 记录一次分析的已解析配置，便于同一镜像复核；配置中的路径需随环境迁移调整。 | 需要可构建的基础层；导出配置不等于证据插件均已满足需求。 |
| `frameworkinfo.FrameworkInfo` | 列出框架的模块化组件 | 检查可用层、扫描器、插件等组件，定位环境与组件版本问题。 | 检查框架组件，不要求加载内存镜像或匹配内核符号。 |
| `isfinfo.IsfInfo` | 检查可用或指定 ISF 符号文件信息 | 核对符号文件元数据、格式与验证状态，处理符号不匹配；通过格式验证不代表匹配检材。 | 读取 ISF 元数据，不要求加载内存镜像。 |
| `layerwriter.LayerWriter` | 导出指定内存层的字节 | 转换封装镜像或保存已构建的层；先列层再选择，所导出的层决定地址语义。 | 需要可构建且可读取的层；整层写出不要求进程符号。 |
| `regexscan.RegExScan` | 在所选 primary 内存层搜索正则表达式 | 寻找路径、配置标记等文本残留；先确认该层的地址语义，再核验命中地址与所属结构，显示上下文长度不等于匹配长度。 | 需要可读取的 primary 层与有效正则；扫描本身不要求匹配内核符号。 |
| `timeliner.Timeliner` | 汇总支持时间线接口的插件事件 | 把进程、文件等时间证据按时间排序；只覆盖实现时间线接口且可运行的插件。 | 依赖各时间线插件的层、符号与结构支持；不包含未实现时间线接口的插件。 |
| `vmscan.Vmscan` | 扫描 Intel VMCS 虚拟化控制结构 | 怀疑宿主内存包含虚拟机时寻找 VMCS、EPT 与客体 CR3；结构匹配仍需验证客体层。 | 需要可扫描的基础层与匹配 VMCS 布局；结果仍需验证客体地址转换。 |
| `yarascan.YaraScan` | 在所选 primary 内存层执行 YARA 规则扫描 | 搜索已知字节特征或文本标记，再核对命中上下文；实际范围由层决定，与进程 VMA/VAD 扫描不同。 | 需要可读取的 primary 层、YARA 引擎与规则；不要求先构建所有进程层。 |

</details>

完整参数表（含从父类或替代类继承的需求）：

<details>
<summary>banners.Banners — 搜索潜在 Linux 内核 banner</summary>

镜像内核版本未知时定位版本字符串，再与精确匹配的 ISF 核验；命中字符串不能单独证明系统版本。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>configwriter.ConfigWriter — 运行自动识别并导出层、符号等配置</summary>

记录一次分析的已解析配置，便于同一镜像复核；配置中的路径需随环境迁移调整。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--extra` | 布尔开关 | false | 否 | 输出整个配置树，而非只输出与当前分析相关的部分。 |

</details>

<details>
<summary>frameworkinfo.FrameworkInfo — 列出框架的模块化组件</summary>

检查可用层、扫描器、插件等组件，定位环境与组件版本问题。

无插件专属 CLI 参数；可使用全局选项与共用 `-h` / `--help`。

</details>

<details>
<summary>isfinfo.IsfInfo — 检查可用或指定 ISF 符号文件信息</summary>

核对符号文件元数据、格式与验证状态，处理符号不匹配；通过格式验证不代表匹配检材。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--filter` | 字符串列表（空格分隔） | [] | 否 | 只显示文件 URI 中含给定字符串的 ISF；可提供多个字符串。 |
| `--isf` | URI/本地路径 | None（未显式设置） | 否 | 仅检查指定 ISF；本地路径会转换为 URI。 |
| `--validate` | 布尔开关 | false | 否 | 尝试按 ISF schema 验证文件格式；格式正确不代表匹配镜像。 |
| `--live` | 布尔开关 | false | 否 | 遍历符号文件而非只使用缓存记录。 |

</details>

<details>
<summary>layerwriter.LayerWriter — 导出指定内存层的字节</summary>

转换封装镜像或保存已构建的层；先列层再选择，所导出的层决定地址语义。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--block-size` | 整数（十进制或 0x） | 5242880 | 否 | 复制层时每次读写的块大小，单位字节。 |
| `--list` | 布尔开关 | false | 否 | 只列可用内存层，用于先确认层名和地址语义。 |
| `--layers` | 字符串列表（空格分隔） | None（未显式设置） | 否 | 要写出的层名列表；省略时由插件选择最高的非映射层。 |

</details>

<details>
<summary>regexscan.RegExScan — 在所选 primary 内存层搜索正则表达式</summary>

寻找路径、配置标记等文本残留；先确认该层的地址语义，再核验命中地址与所属结构，显示上下文长度不等于匹配长度。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--pattern` | 字符串 | None（未显式设置） | 是 | 要匹配的正则表达式；在 shell 中正确引用特殊字符。 |
| `--maxsize` | 整数（十进制或 0x） | 128 | 否 | 命中后显示的上下文字节上限；不是扫描范围大小。 |

</details>

<details>
<summary>timeliner.Timeliner — 汇总支持时间线接口的插件事件</summary>

把进程、文件等时间证据按时间排序；只覆盖实现时间线接口且可运行的插件。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--record-config` | 布尔开关 | false | 否 | 时间线生成后记录各相关插件配置，便于复核。 |
| `--plugin-filter` | 字符串列表（空格分隔） | [] | 否 | 仅运行名称包含给定子串的时间线插件，可提供多个子串。 |
| `--create-bodyfile` | 布尔开关 | false | 否 | 生成时间线时同时创建 bodyfile。 |

</details>

<details>
<summary>vmscan.Vmscan — 扫描 Intel VMCS 虚拟化控制结构</summary>

怀疑宿主内存包含虚拟机时寻找 VMCS、EPT 与客体 CR3；结构匹配仍需验证客体层。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--log-threshold` | 整数（十进制或 0x） | 2 | 否 | 失败条件数不超过此值的 VMCS 候选才写调试日志；不是候选接受条件或虚拟机可信度。 |

</details>

<details>
<summary>yarascan.YaraScan — 在所选 primary 内存层执行 YARA 规则扫描</summary>

搜索已知字节特征或文本标记，再核对命中上下文；实际范围由层决定，与进程 VMA/VAD 扫描不同。

需要可读取的 primary 层、YARA 引擎与规则；不要求先构建所有进程层。

| 参数 | 类型 | 默认值 | 必填 | 作用与判读 |
| --- | --- | --- | --- | --- |
| `--insensitive` | 布尔开关 | false | 否 | 构建字符串规则时忽略大小写；显式规则文件仍以文件内定义为准。 |
| `--wide` | 布尔开关 | false | 否 | 构建字符串规则时匹配宽字符字符串；显式规则文件仍以规则定义为准。 |
| `--yara-string` | 字符串 | None（未显式设置） | 否 | 提供字符串模式；以 { 开头按十六进制模式、以 / 开头按正则模式处理，其他内容会包成引号字符串；完整规则使用 yara-file。 |
| `--yara-file` | URI/本地路径 | None（未显式设置） | 否 | YARA 规则文件路径或 URI。 |
| `--yara-compiled-file` | URI/本地路径 | None（未显式设置） | 否 | 已编译 YARA 规则文件路径或 URI，须兼容当前 YARA 引擎。 |
| `--max-size` | 整数（十进制或 0x） | 1073741824 | 否 | 源码声明的最大大小选项，但此版本相关扫描实现未读取该配置；不要依靠它改变扫描上限。Linux VMA/Windows VAD 扫描另用固定 1 GiB 检查。 |

</details>

</details>

### 独立入口 volshell.py：交互分析与 25 项选项

`volshell.py` 是独立交互 CLI，不属于上面的 197 个插件命令，也不需要 `PLUGIN` 位置参数。选择 Windows、Linux 或 macOS 模式，未选择时进入通用模式。它没有一次执行全部插件的 `ALL` 命令；`vol.py` 也没有 Volatility 2 同名概念的 `ALL` 参数。

```bash
python3 volshell.py --help
python3 volshell.py --windows --help
python3 volshell.py --linux --help
python3 volshell.py --mac --help
```

此入口有 **25 项 CLI 选项**：19 项基础/模式开关（含帮助）、3 项自动构层选项和 3 项 script/script-only/pid 选项。它的 `-l` 表示 Linux，日志只能用 `--log`；`vol.py -l` 则表示日志。volshell 没有 `--parallelism`、`--renderer`、`--filters` 或 `--hide-columns`。

<details>
<summary>volshell 完整 CLI 选项</summary>

| 选项 | 类型 | 默认值 | 必填 | 作用与模式边界 |
| --- | --- | --- | --- | --- |
| `-h` / `--help` | 无值帮助开关 | 不存入配置 | 否 | 显示 volshell 入口帮助并退出。 |
| `-c` / `--config` | 字符串/JSON 文件路径 | None | 否 | 载入 JSON 配置；用于保存并复核层和符号配置。 |
| `-e` / `--extend` | 可重复字符串 | None | 否 | 覆盖配置路径：conf.path=value；等号右侧按 JSON 解析，字符串需保留 JSON 引号。 |
| `-p` / `--plugin-dirs` | 字符串/目录列表 | 空字符串 | 否 | 追加插件目录，多个路径用分号分隔；目录中的第三方插件不属于本目录内置清单。 |
| `-s` / `--symbol-dirs` | 字符串/目录列表 | 空字符串 | 否 | 追加符号目录，多个路径用分号分隔。 |
| `-v` / `--verbosity` | 计数开关 | 0 | 否 | 每提供一次增加日志详细级别，例如 -vv；不改变证据采集范围。 |
| `-o` / `--output-dir` | 字符串/目录路径 | 入口实现所在的 volatility3 包目录 | 否 | 生成文件的目录；默认值与 vol.py 的当前工作目录不同，实际导出宜显式指定。 |
| `-q` / `--quiet` | 布尔开关 | False | 否 | 隐藏进度反馈；不会隐藏结果表。 |
| `--log` | 字符串/文件路径 | None | 否 | 日志文件路径；此入口没有 -l 简写，因为 -l 选择 Linux。 |
| `-f` / `--file` | 字符串/本地文件路径 | None | 否 | single-location 未设置时，把本地镜像路径转换为 file:// URI。 |
| `--write-config` | 布尔开关 | False | 否 | 保存到 config.json；此选项已弃用，改用 --save-config 文件名。 |
| `--save-config` | 字符串/文件路径 | None | 否 | 把生成配置保存到指定 JSON 文件。 |
| `--clear-cache` | 布尔开关 | False | 否 | 清理 Volatility 的短期缓存；缓存目录由 cache-path 决定。 |
| `--cache-path` | 字符串/目录路径 | 依平台的用户缓存目录 | 否 | 改变框架缓存位置；隔离分析时可指定独立工作目录。 |
| `--offline` | 布尔开关 | False | 否 | 与 remote-isf-url 互斥，不在线搜索补充 ISF JSON；仍须准备匹配的本地符号，不应把它当作网络隔离机制。 |
| `-u` / `--remote-isf-url` | 字符串/URL | None | 否 | 指定用于查询 ISF JSON 地址的远端索引 URL；此固定版本常量默认是 None。 |
| `-w` / `--windows` | 布尔开关 | False | 否 | 选择 Windows 特化交互环境，与 linux/mac 互斥。 |
| `-l` / `--linux` | 布尔开关 | False | 否 | 选择 Linux 特化交互环境，与 windows/mac 互斥。 |
| `-m` / `--mac` | 布尔开关 | False | 否 | 选择 macOS 特化交互环境，与 windows/linux 互斥；此版本 macOS 支持已弃用。 |
| `--single-location` | URI/本地路径 | None | 否 | 用于构建内存层的基础位置；本地路径会转换成 URI，可由 -f 提供。 |
| `--stackers` | 字符串列表；0 个或多个值 | None | 否 | 限定用于构建层的 stacker 类名列表；省略时由框架按系统选择。 |
| `--single-swap-locations` | URI 字符串列表；0 个或多个值 | None | 否 | 给 single-location 提供交换层 URI 列表；此版本实际验证要求数量小于 16。仍取决于层支持和交换文件匹配。 |
| `--script` | URI/本地脚本路径 | None | 否 | 启动时在分析上下文执行指定 Python 脚本；应使用自编且已审阅的分析脚本。 |
| `--script-only` | 布尔开关 | False | 否 | 指定 script 执行完成后退出；没有 script 时不自动产生分析结果。 |
| `--pid` | 整数（十进制或 0x） | None | 否 | Windows/Linux/macOS 特化模式在启动时切换到此 PID 的进程层；通用模式没有进程枚举语义。 |

</details>

#### 交互辅助函数与上下文变量

函数使用 Python 调用形式，地址属于当前或显式指定的内存层。通用模式有 21 个辅助函数与 2 个变量；Windows/Linux 模式各有 24 个辅助函数与 3 个变量，macOS 模式有 23 个辅助函数与 3 个变量。这里只统计交互环境直接暴露的辅助项，别名不重复计数。

<details>
<summary>全部模式共有的 21 个辅助函数与 2 个变量</summary>

| 名称/别名 | 调用形式 | 用途与注意事项 |
| --- | --- | --- |
| `bc` / `breakpoint_clear` | `breakpoint_clear(offset=None, layer_name=None)` | 清除分析层读取断点；offset/layer_name 为 None 时覆盖相应全部断点。 |
| `bl` / `breakpoint_list` | `breakpoint_list(layer_names=None)` | 列出所选层的读取断点；省略层列表时列全部层。 |
| `bp` / `breakpoint` | `breakpoint(address, layer_name=None, lowest=False)` | 当分析代码读取覆盖地址的字节时进入 Python 调试器；lowest=True 尝试向最低层映射。它不是给检材中的进程设置执行断点。 |
| `dt` / `display_type` | `display_type(object, offset=None)` | 查看结构类型成员，或按地址构建并展示对象；特化模式可补全当前符号表前缀。 |
| `db` / `display_bytes` | `display_bytes(offset, count=128, layer_name=None)` | 按字节显示十六进制与 ASCII；count 默认 128 字节。 |
| `dw` / `display_words` | `display_words(offset, count=128, layer_name=None, byteorder='@')` | 按 2 字节值展示内容；count 是字节数，byteorder 控制字节序。 |
| `dd` / `display_doublewords` | `display_doublewords(offset, count=128, layer_name=None, byteorder='@')` | 按 4 字节值展示内容；count 是字节数，byteorder 控制字节序。 |
| `dq` / `display_quadwords` | `display_quadwords(offset, count=128, layer_name=None, byteorder='@')` | 按 8 字节值展示内容；count 是字节数，byteorder 控制字节序。 |
| `dis` / `disassemble` | `disassemble(offset, count=128, layer_name=None, architecture=None)` | 反汇编指定层的字节；需要 capstone。可指定 intel/intel64/arm/arm64 解码模式，但不代表整个镜像支持这些平台。 |
| `cl` / `change_layer` | `change_layer(layer_name=None)` | 切换默认读取层；改变后 offset 的地址语义随所选层变化。 |
| `cs` / `change_symboltable` | `change_symbol_table(symbol_table_name=None)` | 切换当前符号表；先检查该符号表是否在 context 中。 |
| `ck` / `change_kernel` | `change_kernel(kernel_name=None)` | 切换当前内核模块名称；用于已存在的模块对象。 |
| `context` | 上下文变量 | 框架 context，包含层、模块、配置和符号空间。 |
| `self` | 上下文变量 | 当前 Volshell 对象，可查看 current_layer、current_symbol_table、current_kernel_name 与 kernel 等属性。 |
| `dpo` / `display_plugin_output` | `display_plugin_output(plugin, **kwargs)` | 构建并显示插件结果；内部使用 NullFileHandler，插件文件输出不会由此自动保存。需要导出时使用常规 CLI。 |
| `gt` / `generate_treegrid` | `generate_treegrid(plugin, **kwargs)` | 用插件类和关键字配置生成 TreeGrid；需满足插件需求，内部文件输出由 NullFileHandler 丢弃。 |
| `rt` / `render_treegrid` | `render_treegrid(treegrid, renderer=None)` | 渲染已有 TreeGrid，默认 QuickTextRenderer；本身不构建插件。 |
| `ds` / `display_symbols` | `display_symbols(symbol_table=None)` | 按字母顺序列出指定符号表的地址与名称；特化模式省略时使用当前符号表。 |
| `hh` / `help` | `help(*args)` | 无参数列出交互帮助；有参数时查看相应对象帮助。 |
| `cc` / `create_configurable` | `create_configurable(clazz, **kwargs)` | 以简单配置值创建框架可配置组件，并将新层或符号表加入 context。 |
| `lf` / `load_file` | `load_file(location)` | 把本地文件加入 FileLayer 并返回层名；加入文件层不等于已正确识别内核或构建进程层。 |
| `rs` / `run_script` | `run_script(location)` | 在当前 shell 分析上下文执行指定 Python 脚本。 |
| `rx` / `regex_scan` | `regex_scan(pattern, count=128, layer_name=None)` | 在指定或当前层扫描 bytes 类型的正则模式，例如 rx(b'marker')；count 控制命中后的显示字节数。 |

</details>

<details>
<summary>Windows、Linux 与 macOS 的特化辅助项</summary>

| 模式 | 名称/别名 | 调用形式 | 用途与注意事项 |
| --- | --- | --- | --- |
| windows | `cp` / `change_process` | `change_process(pid=None)` | 按 PID 切换到 Windows 进程层；不存在或无法构层时需检查进程对象与缺页。 |
| windows | `lp` / `list_processes` / `ps` | `list_processes()` | 返回内核层中的 EPROCESS 对象列表；不会自动切换当前层。 |
| windows | `gp` / `get_process` | `get_process(pid=None, virtaddr=None, physaddr=None)` | 按 PID 查找，或按物理/虚拟地址构建进程对象；pid、virtaddr、physaddr 必须只给一项。Windows 返回 EPROCESS，Linux 返回 task_struct。 |
| windows | `symbols` | 符号表变量 | 当前内核符号表对象，供结构和地址解析。 |
| linux | `ct` / `change_task` / `cp` | `change_task(pid=None)` | 按 PID 切换到 Linux/macOS 任务层；不能构层时仍需检查任务有效性。 |
| linux | `lt` / `list_tasks` / `ps` | `list_tasks()` | 返回 Linux/macOS 任务对象列表；macOS 可用 method 指定枚举方式。 |
| linux | `gp` / `get_process` / `get_task` | `get_process(pid=None, virtaddr=None, physaddr=None)` | 按 PID 查找，或按物理/虚拟地址构建进程对象；pid、virtaddr、physaddr 必须只给一项。Windows 返回 EPROCESS，Linux 返回 task_struct。 |
| linux | `symbols` | 符号表变量 | 当前内核符号表对象，供结构和地址解析。 |
| mac | `ct` / `change_task` / `cp` | `change_task(pid=None)` | 按 PID 切换到 Linux/macOS 任务层；不能构层时仍需检查任务有效性。 |
| mac | `lt` / `list_tasks` / `ps` | `list_tasks(method=None)` | 返回 Linux/macOS 任务对象列表；macOS 可用 method 指定枚举方式。 |
| mac | `symbols` | 符号表变量 | 当前内核符号表对象，供结构和地址解析。 |

</details>

Windows/Linux/macOS 还覆盖 `dt` 与 `ds` 的符号表默认行为：未写表名前缀的结构名使用当前内核符号表，`ds()` 默认列当前表。`bp` 是分析程序的读取断点，`dis` 是静态字节解码；两者都不是连接设备或执行检材中代码。

## 09 结果复核与使用边界

逐项保存版本、插件完整名、命令参数、配置/符号标识、输入哈希、原始表、派生物及错误。检查地址类型、时间、页面覆盖、对象身份和实际文件结构；界面能展开目录、帮助能显示参数、JSON 能解析均不等于镜像分析已成功。

同一内存对象由两种入口或两个工具读取属于解析复核。命令行、历史、服务配置、PE 导入和 API 代码都需要实际对象与其他材料印证。按[综合实战](/knowledge/forensic-memory-practice/)的事件表关联磁盘、日志、网络和采集窗口，再形成有边界的结论。
