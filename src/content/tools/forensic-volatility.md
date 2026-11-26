---
title: Volatility 2/3：启动与证据验证
summary: 先确认镜像可解析，再按进程、命令行和网络线索建立时间与对象关系。
module: Forensics
topic: 工具参数与插件
locationPaths: ['D:\CTF_MISC_Tools\Forensics\volatility']
sourceIds: [web-forensics-wiki-volatility, web-hello-memory, web-goodlunatic-761da51]
updated: 2026-10-03
---

## 适用场景

完整全局参数、所有官方内置插件及其参数、用途与场景集中于[Volatility 2/3 完整速查](/knowledge/forensic-memory-volatility/)。本页用于准备分析环境和验证首轮结果；系统流程从[内存取证模块](/module/forensics/#memory)进入。
拿到 Windows 内存镜像，需要定位运行过的进程、命令行、加载模块或连接线索时使用。本机目录已定位 Volatility 2；Volatility 3 使用前需另行确认可用环境。以下首轮命令以 **Volatility 3** 为准，二者的插件名称和参数不要混用。分析前记录镜像哈希、采集时间、主机时区与镜像来源，在只读副本上操作。

## 01 先验证解析条件

在 Kali/Linux 环境进入 Volatility 3 目录后，确认 Python 依赖已满足，再查看插件帮助。下面的 `memory.raw` 是示例名称，应替换为检材副本的实际路径。

```bash
sha256sum memory.raw
python3 vol.py --help | head -40
python3 vol.py -f memory.raw windows.info
```

`windows.info` 能提供内核、层和符号等基础信息；若报“无法满足符号/层要求”，先核对镜像格式、路径、权限和符号下载状态。它不等于“镜像中没有 Windows 进程”。内存工具本身不负责采集，采集链和哈希记录需要另行保存。

## 02 建立三张基础表

```bash
python3 vol.py -f memory.raw windows.pslist
python3 vol.py -f memory.raw windows.pstree
python3 vol.py -f memory.raw windows.cmdline
```

| 表 | 主要用途 | 易错点 |
|---|---|---|
| `pslist` | 当前可遍历的进程、PID/PPID、创建与退出时间 | 未列出不等于从未运行 |
| `pstree` | 父子关系与可疑启动链 | PID 可复用，需结合时间与进程对象 |
| `cmdline` | 启动参数、脚本与目标路径 | 参数可能为空、被覆盖或已不在内存 |

先按 PID、PPID、创建时间和镜像路径连接三张表，再结合磁盘、事件日志、网络证据确认行为。单个可疑进程名不能直接证明恶意执行。

## 03 对目标进程深入

选定候选 PID 后再按需查看 DLL、文件对象、网络连接和可疑内存区域。插件是否存在及参数以当前 `python3 vol.py --help` 的输出为准，不把旧版 Volatility 2 的 `--profile` 参数套到 Volatility 3。若提取文件或进程内存，指定**独立输出目录**并记录导出文件哈希；导出结果是内存重建物，不一定与磁盘原文件完全一致。

## 04 输出证据链

写成“镜像哈希 → 插件及版本 → 进程对象/PID → 时间与命令行 → 交叉证据”。时间线需标明时区和采集边界。需要完整的检材处理流程时，回到 [内存与运行痕迹分析](/knowledge/forensic-memory/)；工具输出是线索，最终判断应有另一类证据印证。

## 05 版本与插件环境

Volatility 2 使用 Python 2 与旧 profile，Volatility 3 使用 Python 3、层和符号表。分别放到独立环境，记录框架/插件版本；不使用同一个 `vol.py` 路径含糊表示两个版本。

```bash
# Volatility 3：在分析机准备独立环境
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install volatility3
vol -h
vol -f memory.raw windows.info

# Volatility 2：已准备好的旧版隔离环境
python2 ./volatility2/vol.py --info
python2 ./volatility2/vol.py -f memory.raw imageinfo
python2 ./volatility2/vol.py -f memory.raw --profile=Win7SP1x64 kdbgscan
```

`Win7SP1x64` 仅示例。imageinfo 推荐多个 profile 时核对架构、KDBG、内核与进程结构，不能直接取第一项。Win-Profiles 等补充包需匹配构建；支持列表不等于所有插件都支持该构建。Volatility 3 的 Windows PDB/ISF 与 Linux/macOS 的符号条件不同。

Volatility 2 第三方插件可用 `--plugins=./plugins-extra` 指定可信目录，先核对代码/依赖与帮助，再对工作副本分析。`mimikatz`、`ndispktscan`、`usbstor`、`bitlocker`、VolDiff 等不应假设每个安装都有；它们的操作系统和对象支持需单独确认。

## 06 Volatility 2 的实用命令顺序

```bash
mkdir -p ./output/files ./output/process ./output/registry
profile=Win7SP1x64
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" pslist
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" psscan
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" pstree
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" cmdline
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" cmdscan
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" consoles
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" filescan > ./output/filescan.txt
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" dumpfiles -Q 0x12345678 -D ./output/files
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" memdump -p 1234 -D ./output/process
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" procdump -p 1234 -D ./output/process
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" hivelist
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" printkey -K 'SAM\Domains\Account\Users\Names'
python2 ./volatility2/vol.py -f memory.raw --profile="$profile" dumpregistry -D ./output/registry
```

PID/地址从同一镜像当前输出取得。`dumpfiles -Q` 指 FILE_OBJECT 物理地址，`printkey/hivedump -o` 的 Hive 偏移按插件帮助确认，不能混用。`hivedump` 列键不是导出完整 Hive；完整重建用相应 dumpregistry。缺页、层/符号错误、解密失败和提取报错均应保留，不能写成“报错不影响”。

## 07 插件按问题索引

以下是 Volatility 2 常用插件的任务入口，系统支持和可选参数以所用版本的 `插件 -h` 为准。基本调用模板为 `python2 vol.py -f memory.raw --profile=<匹配配置> <插件> [该插件参数]`，按问题选择，避免无目的地执行全部插件。

### 7.1 镜像识别与转换

| 插件 | 用途与边界 |
| --- | --- |
| `imageinfo`、`kdbgscan`、`kpcrscan` | 识别候选 profile、调试器块和处理器控制区；多种证据匹配 |
| `crashinfo`、`hibinfo` | 崩溃/休眠格式与元信息，支持范围有限 |
| `vboxinfo`、`vmwareinfo`、`qemuinfo`、`machoinfo` | 对应虚拟化或容器结构；不是所有同后缀文件都适用 |
| `hpakinfo`、`hpakextract` | Fast Dump/HPAK 信息与其中的内存提取 |
| `imagecopy`、`raw2dmp` | 将可解析物理层导出 RAW 或适用的崩溃格式；输出为派生物 |

### 7.2 进程、身份与运行参数

| 插件 | 用途与边界 |
| --- | --- |
| `pslist`、`psscan`、`pstree`、`psxview` | 列表/池扫描/父子/多视图交叉；差异未必是隐藏进程 |
| `psdispscan` | 旧版调度对象扫描，架构与系统支持有限 |
| `cmdline`、`cmdscan`、`consoles` | 启动参数、历史与控制台；不能互相等同 |
| `envars`、`getsids`、`privs` | 环境变量、身份与权限；持有权限不证明已使用 |
| `handles`、`joblinks`、`sessions` | 句柄、Job 与会话关联；核对对象位置和有效性 |
| `svcscan`、`servicediff`、`getservicesids` | 服务扫描/比较与 SID；结合磁盘定义和日志 |

### 7.3 模块、内存区与候选恶意活动

| 插件 | 用途与边界 |
| --- | --- |
| `dlllist`、`ldrmodules`、`verinfo`、`enumfunc` | 加载模块、映射差异、版本与函数信息 |
| `dlldump`、`procdump`、`impscan` | 重建 DLL/PE、导入调用线索；PE 导出不是 minidump |
| `memmap`、`memdump` | 虚拟/物理映射与进程页导出 |
| `vadinfo`、`vadwalk`、`vadtree`、`vaddump` | VAD 属性、结构、遍历与区域导出 |
| `malfind`、`apihooks`、`yarascan` | 可疑代码、Hook 和特征命中；JIT/合法软件可能触发 |
| `threads`、`thrdscan` | 线程结构与扫描候选，关联起点和所属进程 |

### 7.4 内核、设备与对象

| 插件 | 用途与边界 |
| --- | --- |
| `modules`、`modscan`、`moddump`、`unloadedmodules` | 内核模块枚举/扫描/导出及已卸载记录 |
| `driverscan`、`drivermodule`、`driverirp`、`devicetree` | 驱动对象、模块映射、IRP 与设备树 |
| `ssdt`、`gdt`、`idt`、`callbacks`、`timers` | 系统表、回调与定时器；正常扩展和版本差异需核对 |
| `filescan`、`dumpfiles` | 文件对象与缓存页恢复，文件对象不代表全部文件内容 |
| `mutantscan`、`symlinkscan`、`objtypescan` | 互斥、符号链接与对象类型候选 |
| `bigpools`、`poolpeek`、`multiscan`、`pagecheck` | 池/页面与批量扫描，偏移和有效性校验 |
| `patcher` | 对分析层打补丁的特定用途，会改变分析视图；常规证据检查无需使用 |

### 7.5 网络与用户界面

| 插件 | 用途与边界 |
| --- | --- |
| `connections`、`connscan`、`sockets`、`sockscan` | 主要用于旧 XP/2003 网络对象，不能套到所有 Windows |
| `netscan` | 支持系统中的网络对象扫描；残留不等于实时连接 |
| `atoms`、`atomscan`、`deskscan`、`wndscan` | 会话/桌面/窗口站与 atom 对象 |
| `windows`、`wintree`、`userhandles`、`gahti` | 窗口树、用户句柄和类型 |
| `gditimers`、`eventhooks`、`messagehooks` | GUI 计时器与事件/消息 Hook |
| `clipboard`、`editbox`、`notepad`、`screenshot`、`bioskbd` | 剪贴板/控件/旧编辑器/窗口图/旧键盘缓冲；版本限制明显 |

### 7.6 注册表、凭据与文件系统

| 插件 | 用途与边界 |
| --- | --- |
| `hivelist`、`hivescan`、`printkey`、`hivedump`、`dumpregistry` | Hive 枚举/扫描、读键、列树与重建 |
| `userassist`、`shellbags`、`shimcache`、`amcache` | 用户与兼容性痕迹；单个条目不能证明具体操作者 |
| `auditpol`、`shutdowntime` | 审计策略与关机线索，结合事件日志 |
| `hashdump`、`cachedump`、`lsadump`、`dumpcerts` | 哈希、缓存域凭据、LSA 与证书材料；并非都能得到明文 |
| `truecryptsummary`、`truecryptpassphrase`、`truecryptmaster` | 匹配旧版 TrueCrypt 的状态、口令/主密钥候选 |
| `mbrparser`、`mftparser` | MBR/MFT 残留与元数据，不保证完整删除恢复 |
| `evtlogs`、`iehistory` | 旧系统事件/IE 缓存记录，不覆盖全部 EVTX/现代浏览器 |
| `strings`、`timeliner`、`volshell` | 偏移关联、时间线和对象交互；保留上下文与原始字段 |

## 08 Volatility 3 对应入口

| 问题 | 常见插件 |
| --- | --- |
| 系统基线 | `windows.info`；Linux 用 `banners` 配合符号信息 |
| 进程 | `windows.pslist`、`windows.psscan`、`windows.pstree` |
| 参数与模块 | `windows.cmdline`、`windows.envars`、`windows.dlllist`、`windows.handles` |
| 内存区 | `windows.memmap`、`windows.vadinfo`、相应版本的 malfind 入口 |
| 文件 | `windows.filescan`、`windows.dumpfiles` |
| 网络 | `windows.netscan`、`windows.netstat` |
| 注册表 | `windows.registry.hivelist`、`windows.registry.printkey` |
| 凭据/异常候选 | 对应版本的 registry 或 malware 命名空间插件 |

新版本可能调整命名空间或停用旧入口，先看完整帮助及弃用提示。`banners` 不是 Windows 版本识别的通用替代；用 `windows.info` 核对内核。详细导出、文本和画布线索见 [对象与数据恢复](/knowledge/forensic-memory-recovery/)，Linux/macOS profile/ISF 见 [Unix 内存知识](/knowledge/forensic-memory-unix/)。
