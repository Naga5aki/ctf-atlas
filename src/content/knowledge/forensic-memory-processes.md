---
title: "内存进程与攻击行为：连接、注入和持久化"
summary: "从活动链与扫描差集追踪进程、网络、模块、线程和内核异常，验证自启动与实际运行，排除残留和合法行为。"
module: "Forensics"
track: "内存取证"
topic: "进程与攻击行为"
tags: ["时间线"]
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42", "web-forensics-wiki", "web-forensics-wiki-skilltree", "web-goodlunatic-761da51", "web-hello-memory", "web-memory-volatility2-261", "web-memory-volatility3-2282"]
challengeIds: []
relatedIds: ["forensic-memory", "forensic-memory-recovery", "forensic-memory-unix", "forensic-memory-volatility", "forensic-memory-practice"]
updated: "2026-10-03"
---

## 01 从可读镜像建立进程调查范围

先完成[内存采集与镜像识别](/knowledge/forensic-memory/)中的格式、架构、内核、符号和时间核验，再分析进程行为。这里的命令处理已有工作副本，不采集或启动目标设备。建立镜像哈希、工具版本、符号标识、命令、完整输出和错误的对应关系；换工具或修正符号后保留前一轮结果，不能让新结果覆盖调查过程。

以下使用 Volatility 3 的完整插件名。全局参数放在插件名之前，插件参数放在之后；PID 必须替换为本镜像中已核验的对象。当前环境是否支持插件，以实际帮助和依赖检查为准，工具安装不完整、符号不匹配、镜像缺页与“没有找到对象”是不同情况。

```bash
mkdir -p output/processes output/network output/modules
sha256sum work/memory.raw > output/memory.sha256
python3 vol.py -f work/memory.raw windows.info.Info > output/windows-info.txt
python3 vol.py -f work/memory.raw windows.pslist.PsList > output/processes/pslist.txt
python3 vol.py -f work/memory.raw windows.psscan.PsScan > output/processes/psscan.txt
python3 vol.py -f work/memory.raw windows.pstree.PsTree > output/processes/pstree.txt
python3 vol.py -f work/memory.raw windows.cmdline.CmdLine > output/processes/cmdline.txt
```

首轮输出先回答“有哪些对象、它们属于哪个时间与地址空间”，再回答“它们是否异常”。主机上的磁盘日志、虚拟机快照、休眠文件和交换文件可能来自不同采集时点；不要把不同材料拼成一个瞬间。操作系统名称、分析机的系统版本与镜像内系统版本也应分别记录。

## 02 用对象和时间识别进程

`pslist` 沿可枚举的进程结构取得结果；`psscan` 扫描内存中的进程对象残留；`pstree` 根据父 PID 组织关系。三者观察的范围不同，差集是调查入口。仅在扫描结果出现的对象，可能是已退出、已释放后尚未覆盖、不可枚举或损坏的结构，不自动等于隐藏进程。列表可见也不自动等于正常程序。

对可疑对象建立一张证据卡，至少保存以下字段。字段不可读时明确写“不可读”，不要补猜测值。

| 字段 | 用途与复核 |
| --- | --- |
| 镜像标识、对象地址及地址类型 | 关联本次解析的实际进程对象，防止不同镜像的同一 PID 被混用 |
| 进程名、PID、PPID、创建与退出时间 | 区分同名进程、PID 复用、退出对象与采集时活动对象 |
| 用户、会话与可得的令牌信息 | 说明运行上下文，不按目录用户名直接推定进程拥有者 |
| 命令行、映像路径、工作目录线索 | 分开记录实际解析值和字符串候选，核对路径是否截断 |
| 模块、句柄、文件对象、内存区间 | 关联打开的资源与执行内容，不把同名文件视为同一对象 |
| 连接对象、端点、状态与相关时间 | 与抓包、DNS、代理、防火墙和服务日志互证 |
| 磁盘对应文件的大小、哈希、签名状态 | 区分删除、替换、不同版本与内存重建差异 |

父 PID 可能指向后来复用这个编号的进程。核验父进程的创建时间是否早于子进程，父子是否在合理时间重叠，命令行与执行日志是否支持该关系。父进程已经退出不等于父子关系不存在；解析出的父节点缺失也可能来自缺页。将进程名、PID、对象地址、开始时间一起使用，比单独用 PID 更稳。

日志关联时，优先保存已有的进程唯一标识、事件时间及完整命令行；事件只提供数字 PID 时，必须对齐生命周期。Sysmon 的 ProcessGuid、Windows 进程创建事件与内存对象各有覆盖条件。未启用相应审计、日志轮转、采集较晚都可能使日志缺失；不能由缺少创建事件否认内存中的进程对象。

需要结构化结果时，先确认所用版本支持相应 renderer。Volatility 2 的以下模板只适用于已配置的旧运行环境和已核验 profile，不可加到 Volatility 3 命令上：

```bash
profile='REPLACE_WITH_VERIFIED_PROFILE'
volatility -f work/memory.raw --profile="$profile" pslist \
  --output=json --output-file=output/processes/vol2-pslist.json
python3 -m json.tool output/processes/vol2-pslist.json \
  > output/processes/vol2-pslist-readable.json
```

JSON 可解析只证明语法完整。继续核对实际列名、字段类型、对象 offset 和文本版输出；插件不支持 renderer 时保存原始文本和报错，不把报错文件当成 JSON。Volatility 2 的 profile 选择、KDBG 和时间基准见[内存采集与镜像识别](/knowledge/forensic-memory/)。

## 03 关联命令行、路径、模块和环境

先按已确认的 PID 缩小范围，再提取命令行、模块、句柄和环境。以下 `1234` 是待替换的示意 PID。

```bash
python3 vol.py -f work/memory.raw windows.cmdline.CmdLine --pid 1234 \
  > output/processes/pid-1234-cmdline.txt
python3 vol.py -f work/memory.raw windows.dlllist.DllList --pid 1234 \
  > output/modules/pid-1234-dlllist.txt
python3 vol.py -f work/memory.raw windows.handles.Handles --pid 1234 \
  > output/processes/pid-1234-handles.txt
python3 vol.py -f work/memory.raw windows.envars.Envars --pid 1234 \
  > output/processes/pid-1234-envars.txt
```

命令行说明取得的参数，不保证每个参数对应的操作已完成。控制台历史、PowerShell 脚本块、PSReadLine 与进程命令行是不同对象，应分别解释。[对象与数据恢复](/knowledge/forensic-memory-recovery/)补充控制台、编辑器和字符串的归属方法。

模块记录至少包含名称、路径、实际加载基址、大小和取得范围。静态 PE 导入表表示映像声明的依赖；延迟导入、运行时 LoadLibrary、API Set 转发和加载器行为可能改变实际模块集合。不能用导入表数量替代内存模块数量，也不能把调试器某一断点看到的模块列表冒充历史镜像里的状态。

地址要注明是哪一层：模块的 RVA 是相对地址；加载后的 VA 通常为实际加载基址加 RVA，ASLR 可能改变基址；磁盘文件偏移由节表布局换算。进程虚拟地址、物理地址和导出文件偏移还属于不同坐标系。同一个数值相等不足以允许跨层使用，缺页时也不能假定相应磁盘字节已在内存中。

磁盘 PE 与内存映像的哈希可能不同，原因包括重建方式、重定位、导入修复、缺页及运行时修改。先定位不同区间，记录哪些字节来自原镜像、哪些由工具重建，再判断是否发生替换或改写。签名、目录位置和程序名只是复核点；恶意程序可使用正常名称，合法升级也可能产生不同哈希。

进程环境是对象内的一份环境值，不能代表此后每次设置或所有子进程的环境。CPU 相关字段可用于核验系统描述：

```bash
python3 vol.py -f work/memory.raw windows.envars.Envars \
  > output/processes/all-envars.txt
rg -i 'PROCESSOR_IDENTIFIER|PROCESSOR_ARCHITECTURE|NUMBER_OF_PROCESSORS' \
  output/processes/all-envars.txt
```

`Family/Model/Stepping` 不能单独唯一对应零售 CPU 型号，`NUMBER_OF_PROCESSORS` 不等于物理插槽数量，虚拟机可能提供虚拟 CPU。品牌字符串可能来自驱动、说明文档或安装包；先保存对象归属和上下文，优先核验有结构的系统信息。相同页面被多个进程映射不构成多份独立硬件证据。`cpuinfo` 不是所有 Windows Volatility 2 安装都提供的标准命令；同名 Linux 或社区插件须记录提供者、版本与支持范围，命令不存在不证明镜像中没有硬件线索。

## 04 将网络对象还原到对应进程

```bash
python3 vol.py -f work/memory.raw windows.netscan.NetScan \
  > output/network/netscan.txt
python3 vol.py -f work/memory.raw windows.netstat.NetStat \
  > output/network/netstat.txt
```

扫描网络对象与遍历网络跟踪结构的结果可以比较，但仍读取同一份镜像。保存协议、本地和远端地址、端口、状态、拥有者及可得的创建时间；对象地址用于复核，PID 用于候选关联。将进程生命周期与对象时间对齐后，再找独立的流量或日志记录。输出中的创建时间也不等同于每次报文的时间。

| 发现 | 可以先描述 | 还需验证 |
| --- | --- | --- |
| 对外监听对象 | 镜像中存在相应监听结构 | 服务配置、进程、监听时段和实际请求 |
| TCP 对象含远端端点 | 找到该端点关联的网络对象 | 是否残留、状态含义、抓包方向与完整连接 |
| UDP 端口对象 | 取得本地端点或相关对象 | 无连接协议的对端与报文需另证 |
| 浏览器或脚本进程关联端点 | 进程与通信线索有交集 | 命令参数、DNS、代理、会话与请求内容 |
| 扫描对象损坏或字段异常 | 结构不完整或解析异常 | 符号、缺页、释放后内容与工具兼容性 |

不要为获得更多行而默认开启包含损坏对象的选项。确需检查时，将该轮结果单列并标识其可信度，逐项核验地址与拥有者。网络对象可能在连接关闭后残留；公网 IP 还可能属于共享代理、CDN 或 NAT 出口，不能仅凭地址确定业务主体。

抓包没有某连接，不等于没有通信：捕获位置、起止时间、过滤条件、加密及路由均限制覆盖。反过来，抓包中出现连接也不证明某个同 PID 的进程负责它。按 `镜像对象 → 进程实例 → 端点 → 时间区间 → 报文/日志` 保存关联链，流量解码详见[网络流量分析](/knowledge/forensic-network-traffic/)。

## 05 排查用户态注入与无文件活动

先收集进程 VAD、加载器模块信息及可疑内存区间。`malfind` 给出可能含注入代码的候选区域，不是自动恶意判定器；这里不执行导出的程序。

```bash
python3 vol.py -f work/memory.raw windows.vadinfo.VadInfo --pid 1234 \
  > output/modules/pid-1234-vadinfo.txt
python3 vol.py -f work/memory.raw windows.malware.ldrmodules.LdrModules --pid 1234 \
  > output/modules/pid-1234-ldrmodules.txt
python3 vol.py -f work/memory.raw windows.malware.malfind.Malfind --pid 1234 \
  > output/modules/pid-1234-malfind.txt
python3 vol.py -f work/memory.raw windows.thrdscan.ThrdScan \
  > output/processes/thrdscan.txt
```

按区间建立记录：起止虚拟地址、页保护、是否私有页、关联文件、可读字节、线程起点和映像布局。模块链表与内存映射不一致时，检查卸载、加载中的瞬态、损坏、缺页和解析兼容性。扫描线程可能包含退出或残留对象；根据所属进程对象、生命周期和可读结构再次限定范围。

可执行私有页、RWX 权限或 PE 头都可以成为线索，但 JIT、浏览器、运行时、解压执行及安全软件也可能产生类似现象。先核验合法模块、程序用途和代码形态，再描述异常。缺少 PE 头不排除执行代码；具有 PE 头也不直接证明已经执行。

将候选线程起点与模块区间、VAD 和实际字节对照：起点位于何处，是否能读取连续内容，有无合理的映像/函数映射。只有同时得到内容、映射与执行上下文，才提高结论强度。若只是某个扫描器的候选，报告为“待核验的可执行区域”，保留合法解释和不可读范围。

需要导出候选区间时，先查看当前插件帮助并在独立目录使用支持的 `--dump`；保留起止地址与输出偏移映射，再做静态检查。[对象与数据恢复](/knowledge/forensic-memory-recovery/)说明进程页、映像和 minidump 的差异；静态 PE、Go、ARM64、RC4/AES 和容器解密仍在[程序结构与恶意代码分析](/knowledge/fic-case-07/)，不能用静态逆向结论代替历史执行证据。

## 06 检查内核模块、驱动和回调

内核对象异常要在已匹配的内核符号上分析。先比较可枚举模块与扫描模块，再看驱动对象、设备树、回调和系统调用表；逐项记录对象地址、目标函数地址、所属模块及字节可读性。

```bash
python3 vol.py -f work/memory.raw windows.modules.Modules > output/modules/kernel-modules.txt
python3 vol.py -f work/memory.raw windows.modscan.ModScan > output/modules/kernel-modscan.txt
python3 vol.py -f work/memory.raw windows.driverscan.DriverScan > output/modules/driverscan.txt
python3 vol.py -f work/memory.raw windows.devicetree.DeviceTree > output/modules/devicetree.txt
python3 vol.py -f work/memory.raw windows.callbacks.Callbacks > output/modules/callbacks.txt
python3 vol.py -f work/memory.raw windows.ssdt.SSDT > output/modules/ssdt.txt
```

模块枚举与扫描差异可能涉及卸载残留或损坏，不能只用差集宣布 rootkit。回调本身是系统和驱动的正常机制；检查地址是否落在可解释的模块中、模块与驱动是否匹配、签名与系统角色是否合理，再和磁盘驱动、服务配置、加载日志互证。系统调用入口或指针看起来偏离预期时，先排除版本、架构、符号和合法安全产品差异。

不要把“名字像系统驱动”作为正常证明，也不要把“无名字”作为恶意证明。报告区分已确认的对象、可疑关系和未能读取的字段；没有匹配符号或关键页时，应停止对应结构推断，保留需要补足的材料。Linux/macOS 的内核模块、hook 与符号处理见[Linux 与 macOS 内存分析](/knowledge/forensic-memory-unix/)。

## 07 自启动、远控与工具视图的证据边界

自启动调查按类别记录注册表 Run、服务、计划任务、启动文件夹以及对应程序。内存可以保存相关配置、进程和服务对象，磁盘则提供 hive、任务文件和安装目录；两者要对齐采集时点。`autoruns` 可能是社区插件或工具集成，不假定每次安装都覆盖全部类别。先核对提供者、版本、帮助、支持系统及未覆盖类别，不在无对应插件时编造参数。

LovelyMem 和 MemProcFS 的系统、硬件、进程或启动视图可辅助定位。若两个工具读取同一个对象，这属于解析复核；同一个对象被多个界面呈现不增加独立证据数量。应保存实际插件/功能标识、工具日志、底层路径或对象地址，不能只交付一张按钮截图。

发现远控客户端的自启动配置与磁盘安装目录时，先确认“配置存在、程序存在”。进一步取得一致的活动进程、服务记录和端点日志，才描述在相应时段运行或连接。Jump List 说明最近交互线索，不能直接等同自启动成功；安装、配置、加载、执行、网络成功分别有不同判据。

可采用 `对象/路径 → 配置类别 → 进程实例 → 执行/连接证据 → 时间 → 对照材料 → 限制` 的记录格式。账户名称与 RID/SID 的内存核验见[对象与数据恢复](/knowledge/forensic-memory-recovery/)，磁盘账户与常见自动运行位置仍见[Windows 系统痕迹](/knowledge/forensic-windows-artifacts/)。

## 08 实战：下载进程、异常内存区与对外连接

**场景与材料：** 在隔离训练环境中取得 Windows 内存工作副本、同机磁盘副本、进程创建日志和一段网络抓包。磁盘上某下载程序已被移走；调查目标是判断采集时哪个进程实例关联该程序、是否存在异常内存区，以及通信能确认到哪一步。训练材料只使用构造的文件名和测试端点。

### 08.1 操作与证据位置

1. 固定镜像和日志哈希，记录内存采集窗口、磁盘采集时点、抓包范围及系统时间偏差。先验证 `windows.info.Info` 与活动结构可解析，保留符号和依赖失败。
2. 保存本页首轮进程输出，选定候选实例后，按其 PID、创建时间与对象地址建立证据卡。父 PID 指向另一个较晚创建的对象时，标记复用或不确定关系，继续查日志。
3. 读取该进程命令行、模块、句柄和 VAD。文件对象与下载目录只是定位线索，按[对象与数据恢复](/knowledge/forensic-memory-recovery/)另行导出，不能将句柄路径当作已恢复文件。
4. 对异常区间记录权限、私有/映射属性、内容和线程关联；分别检验合法 JIT、安全软件、缺页与注入解释。导出字节供静态检查，禁止执行候选程序来“验证历史”。
5. 将网络对象关联到同一进程实例，再与抓包五元组、DNS、代理及服务日志的时段对齐。抓包只覆盖部分时段时，以覆盖区间内的通信作为可确认范围。
6. 将磁盘已删除/替换的文件记录、模块路径与导出字节比较。重建映像和磁盘文件哈希不同，先查字节范围和重建过程，保留缺页。

### 08.2 判读与验证

若进程创建日志、内存进程实例和通信日志相互匹配，可以确认相应程序实例在限定时段运行并关联通信。若还找到不属于正常模块的可执行区与一致线程起点，可以报告异常执行区域及其证据；仍需解释内容和合法替代情况，不能只凭 `malfind` 一行写成已确认注入。

若只找到退出进程和关闭后残留网络对象，描述为历史对象线索；若抓包中没有响应，不能将通信尝试写成操作成功。若磁盘文件缺失但内存映像可读，可以确认取得了相应内存内容，不能据此保证磁盘曾有同一完整文件。

最终复核：每个结论有明确对象与时间；每个地址注明类型；PID 复用已处理；导出过程有输入到输出映射；空结果与错误已区分；磁盘、日志和流量的采集边界均已说明。完整证据链编排见[内存取证综合实战](/knowledge/forensic-memory-practice/)。
