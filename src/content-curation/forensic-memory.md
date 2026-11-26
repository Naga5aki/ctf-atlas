拿到内存检材时，先确认手里是完整物理内存镜像、虚拟机运行态文件、崩溃转储、休眠/交换文件还是单进程转储，再匹配对应的解析器与符号表。原始镜像保持只读，所有对象导出与恢复均在独立工作目录中进行。

## 01 先识别内存材料类型与采集条件

内存是易失性证据。活体采集本身会改变部分内存页并在内存中留下采集程序与驱动自身的对象，因此开始分析前先记录设备时间、系统版本、采集工具及驱动版本、采集起止时间窗、输出容器格式、字节大小和 SHA-256 哈希。

Volatility 是离线分析框架，本身不负责采集物理内存。先看清手里拿到的是哪一类材料，再决定能回答什么问题；休眠文件、交换文件和崩溃转储可作补充，但不能默认它们与物理内存镜像属于同一时刻：

| 材料 | 可分析方向 | 必须核对的边界 |
| --- | --- | --- |
| 完整物理内存 RAW | 页表、内核、活动与残留进程、网络连接与文件缓存 | 实际大小、物理地址范围、缺页、加密与采集扰动 |
| 虚拟机 VMEM、快照状态 | 虚拟机运行态内存 | 配套状态文件（`.vmsn`/`.vmss`）、快照链、架构与采集时点；只改扩展名不改变内部格式 |
| Windows 完整/内核/小型崩溃转储 | 按转储保留范围分析内核或进程 | 转储头（`PAGE`/`DU64`）、目录和保存页面；小型转储通常不包含全部用户空间 |
| 休眠文件 `hiberfil.sys` | 休眠时压缩保存的内存页面 | 系统版本、压缩与封装格式、恢复支持和休眠时间；不是普通 RAW |
| `pagefile.sys`、`swapfile.sys`、Linux swap | 换出的页面和文本片段 | 页面已脱离进程上下文且可能跨多个时间点；不能当完整物理镜像套用全部插件 |
| 进程转储、core、minidump | 某一进程和指定流/映射 | 进程范围、架构、有效结构；无法由此获得全系统进程树 |
| 虚拟磁盘或离线磁盘镜像 | 交换/休眠文件、日志和持久化痕迹 | 普通磁盘不保存完整 `procfs` 运行视图，不能拿分析机 `/proc` 代替目标 |

完整内存、进程页和 minidump 的导出区别见[对象与数据恢复](/knowledge/forensic-memory-recovery/)；虚拟机磁盘链与外层镜像识别分别见[云与虚拟化](/knowledge/forensic-cloud-vm/)与[取证镜像与文件系统识别](/knowledge/disk-evidence/)。

## 02 分清镜像偏移、物理地址、虚拟地址与页表根

不同插件输出的“地址”可能处于完全不同的地址空间。把虚拟地址直接传给要求物理偏移的参数，或把导出件内部偏移当成物理内存地址，都会导致提取错位：

| 表示 | 含义 | 实战核对方式 |
| --- | --- | --- |
| 镜像文件偏移 | 输入容器内的字节位置 | 仅当 RAW 为连续线性物理映射时才可能与物理地址相同；崩溃转储与稀疏容器有各自的段映射 |
| 物理地址 PA | 目标物理内存地址 | 扫描类插件（`*scan`）常输出物理地址；用物理层读字节并记录转换关系 |
| 虚拟地址 VA | 进程或内核地址空间中的地址 | 指明所属进程或内核上下文及页表；同一 VA 在不同进程中指向不同物理页 |
| DTB / CR3 | 地址转换所用页表根线索 | 与架构、进程对象、KDBG/内核位置共同验证；不是镜像哈希或文件偏移 |
| 对象地址 | `EPROCESS`、`FILE_OBJECT`、hive 等结构位置 | 先确认插件给出的是 VA 还是 PA，再选择接收该地址类型的参数 |
| 导出件偏移 | 恢复文件内的位置 | 若插件做过拼接、稀疏跳过或补零，需依导出映射回查，不能直接当作镜像地址 |

Volatility 3 的物理/容器层、Intel 地址转换层、符号表（ISF）及对象层相互配合。识别镜像格式、建立地址层与匹配符号是三个独立步骤；错误符号可能产生“看似合理”的单行输出。Volatility 2 则常需要 Profile、KDBG 或 DTB 辅助定位；Profile 描述内核类型布局与系统支持范围，并不改变镜像本身的容器格式。

**常考辨析：** `psscan` 的池扫描位置（常为物理地址）与 `pslist` 的活动双向链表对象地址（常为内核虚拟地址）不同，对比前先按插件字段解释映射；Vol2 `dumpfiles -Q` 接收物理地址，而 Vol3 `windows.dumpfiles` 则通过 `--virtaddr` 与 `--physaddr` 明确区分。转储页面缺失（paged out）时，应如实报告对象不可读范围，不能把读取失败写成对象不存在。

## 03 Volatility 2 历史镜像：Profile 识别与内存时钟核对

**场景与材料：** 拿到一份历史 Windows 内存镜像，需要识别系统 Profile、列出进程与注册表配置单元，并核对内存中的系统时间。先判断用 Volatility 2 的 Profile 模式还是 Volatility 3 的符号模式——两代插件名和参数不同，不能把 `imageinfo`、`--profile` 直接加到 Volatility 3 命令中。

### 03.1 先跑 imageinfo，再验证候选 Profile

以下命令在已配置 **Volatility 2 启动命令 `volatility`**（Python 2 隔离环境）的分析机上运行；普通辅助脚本仍使用 Python 3：

```bash
mkdir -p ./output/vol2
volatility --info > ./output/vol2/tool-info.txt
volatility -f ./work/memory.raw imageinfo > ./output/vol2/imageinfo.txt
```

`imageinfo` 给出的 `Suggested Profile(s)` 只是候选列表，不是无需复核的最终结论。核对架构（x86/x64）、KDBG 地址、系统 Build 与活动对象是否合理，再从 `tool-info.txt` 已注册的列表中选定匹配的 Profile（切勿盲目照搬其他题目的 `Win10x64_10586`）：

```bash
# 先将下方变量替换为当前镜像经核对且 tool-info 中实际存在的 Profile
profile='REPLACE_WITH_VERIFIED_PROFILE'
volatility -f ./work/memory.raw --profile="$profile" pslist \
  > ./output/vol2/pslist.txt
volatility -f ./work/memory.raw --profile="$profile" hivelist \
  > ./output/vol2/hivelist.txt
```

若 `pslist` 输出为空，优先排查 Profile 选择错误、KDBG 地址未命中或镜像头部封装格式（如 `.dmp`/`.vmem`），不要立即断定现场没有进程。

### 03.2 区分内存系统时钟与实际采集时间

`imageinfo` 中的 `Image date and time` 反映镜像内内核维护的系统时间候选（同时保留 UTC 与目标时区显示）。由于目标机系统时钟可能不准或被人为修改，且内存采集需要持续一段时间，**该字段不能单独证明镜像文件的实际制作完成时刻**：

1. 对照外部可信采集记录、内存中的采集程序进程对象、文件容器元信息与时间窗口，优先用外部固定记录描述采集起止。
2. 若在内存中搜到 `lasttime=` 或 `vmtoolsd` 日志字符串，先记录字节偏移、所属进程/文件与字段语义——它可能只是应用上次运行、宿主机同步或日志写入时间，且同一日志缓冲在物理内存和进程页中被扫到两次仍属于同一条底层证据。
3. 核对开机时间、关键进程创建时间与磁盘事件日志是否处于合理区间，如实记录时钟漂移与时区偏差。

## 04 Volatility 3 识别与 ISF 符号管理

Volatility 3 基于 Python 3、分层内存模型和 ISF（Intermediate Symbol Format）JSON 符号表运行：Windows 镜像通常根据内核调试目录中的 PDB GUID/Age 匹配符号；Linux 与 macOS 镜像则必须精确核对完整内核 banner、架构与发行版构建号。

```bash
mkdir -p output/baseline symbols cache
python3 vol.py --help > output/baseline/tool-help.txt
python3 vol.py -f work/memory.raw windows.info > output/baseline/windows-info.txt
python3 vol.py -s ./symbols --cache-path ./cache isfinfo.IsfInfo \
  > output/baseline/isf-list.txt
```

准备好匹配的符号表与缓存后可加上 `--offline` 运行，但 `--offline` 只禁止联网下载，不会自动生成缺失的 ISF。每次更换符号文件、插件目录或缓存后应另建输出批次，并记录工具版本与符号文件 SHA-256。

Windows 首轮用 `windows.info` 核对内核基址、地址层、符号表与系统 Build；Linux 与 macOS 的 `vmlinux` + `System.map` / `dwarf2json` 符号制作流程集中在[Linux 与 macOS 内存](/knowledge/forensic-memory-unix/)；两代完整 CLI 参数与 462 个内置插件清单见[Volatility 2/3 参数与插件速查](/knowledge/forensic-memory-volatility/)。

## 05 首轮排查路线、重点场景与常见误判

拿到一份可解析的内存镜像后，按以下五步建立基线并分流到对应专页：

1. **保全与识别：** 记录文件类型、字节数、SHA-256、采集时间窗、操作系统架构与符号表；若报层或符号错误，先按第 06 节排错。
2. **建立进程与服务基线：** 对比活动链表（`pslist`）、池扫描（`psscan`）与父子关系（`pstree`），结合命令行（`cmdline`）、用户会话与服务，按进程对象地址与启动时间对齐，不只看进程名称。
3. **定位异常行为与通信：** 检查父子进程启动时间倒置、可疑路径、模块链表与 VAD 映射差异、私有可执行页（`malfind`）、线程起点与网络连接（`netscan`/`netstat`），排除合法 JIT 编译器与安全软件干扰。
4. **恢复关键对象与凭据：** 按对象地址导出文件缓存（`dumpfiles`）、进程内存页、重建 PE、内存注册表 hive、控制台历史、便签文本与画布像素；分别记录地址类型、缺页范围与导出件哈希。
5. **跨介质交叉印证：** 将内存中的进程、连接与提取文件同磁盘 `$MFT`/日志、浏览器记录、PCAP 抓包的哈希和时间对齐，严格区分“代码存在”“命令输入”“进程运行”与“操作成功”。

| 调查目标与重点场景 | 首轮观察点 | 复核点与深入专页 |
| --- | --- | --- |
| 系统身份与采集时刻 | Profile/ISF、Build、架构、内存时钟与外部采集窗口 | 本页第 03、04 节 |
| 异常进程、网络连接、注入与持久化 | 对象地址、PID 复用、父子时间、模块/VAD 映射、端点状态 | 排除已退出残留与合法 JIT → [进程与攻击行为](/knowledge/forensic-memory-processes/) |
| 文件缓存、注册表、便签、画布与密钥 | `FILE_OBJECT` 地址类型、hive 虚拟地址、真实格式与解密回验 | 区分文件缓存、进程页与 LSASS minidump → [对象与数据恢复](/knowledge/forensic-memory-recovery/) |
| Linux / macOS 内核与运行态 | 完整 banner、同构建调试内核、bash/lsof/sockstat/mountinfo | 先验符号再查进程与挂载 → [Linux 与 macOS 内存](/knowledge/forensic-memory-unix/) |
| 全局参数与内置插件选择 | Vol2/Vol3 命令名、输入/输出、筛选开关、可选依赖 | 查阅 265+197 个官方插件参数 → [Volatility 2/3 速查](/knowledge/forensic-memory-volatility/) |
| 多检材联合取证与报告交付 | 内存 + 磁盘 + 日志 + 流量证据链、缺口与报告措辞 | 串联完整案例 → [内存取证综合实战](/knowledge/forensic-memory-practice/) |

## 06 实战：首轮 pslist 输出为空时如何逐层排错

**场景与材料：** 拿到一份标称 Windows 物理内存的镜像文件，首轮运行 `pslist` 没有任何进程输出。不要直接下结论“现场无进程”，按以下四步在工作副本上排查：

1. **查外层容器与截断：** 用 `file`、`xxd -l 64` 和 `stat` 查看文件头与实际字节数，排除 ZIP/7z 压缩包、E01、虚拟磁盘（VMDK/VHD）、休眠文件（`hiberfil.sys`）、崩溃转储（`PAGE`/`DU64`）或单进程 minidump（`MDMP`），以及传输截断。
2. **查架构、层与符号要求：** 在 Vol2 中，`imageinfo` 的 Suggested Profile 只是候选，需配合 `kdbgscan` 核对真实 Build 与 32/64 位架构；在 Vol3 中，观察报错是停在 `Automagic` 地址层构建、内核 PDB 下载（`unsatisfied requirements`）还是可选 Python 依赖缺失。
3. **用多类对象交叉验证 Profile/ISF：** 选定正确的容器转换或符号表后，同时运行 `windows.info`、`pslist`、`psscan` 与 `hivelist`。只有内核信息、活动进程链、注册表配置单元等多个结构都能合理读出，才算符号匹配成功；单一 banner 字符串命中不算数。
4. **记录缺页与不可解析边界：** 若镜像本身被截断或关键内核页缺失，改用 `psscan`、`filescan` 或物理层字符串/YARA 扫描提取残留对象，并在报告中写明：`输入哈希 → 工具及版本 → 参数/符号哈希 → 可解析层与缺失范围 → 原始输出与派生文件哈希`。
