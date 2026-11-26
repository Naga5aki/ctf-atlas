## 01 把材料和结论拆成可验证的证据链

内存实战从固定材料、识别镜像与限定时间开始，再关联进程、对象、内容、日志和流量。以下均为可在隔离训练环境构造的场景与分析模板，不代表已复跑某份检材；不执行候选附件，不启动检材系统，也不把副本中的实验活动并入历史事件。

| 材料 | 固定与定位 | 主要覆盖与缺口 |
| --- | --- | --- |
| 内存镜像 | 哈希、字节数、采集方法/窗口、架构、系统、符号 | 对象与页面状态；缺页、缓存回收、采集变化 |
| 磁盘与虚拟盘链 | 镜像标识、完整父链、卷与文件路径、哈希 | 持久化文件与元数据；不能自动代表 RAM |
| 休眠、交换、崩溃或 minidump | 容器结构、生成条件、页覆盖和时点 | 可能补充部分状态；不能统一当完整物理内存 |
| 事件/应用/容器日志 | 原格式、时区、范围、轮转集合、对象标识 | 已记录事件；缺失可能来自配置、轮转或覆盖 |
| 流量和云网络记录 | 捕获位置、时间、过滤/采样、加密条件 | 可见通信；不直接代表进程与所有业务动作 |
| 代码和实验结果 | 样本哈希、静态字节、实验快照、环境与新增写入 | 解释逻辑与可达行为；不单独证明历史成功 |

先用[采集与识别](/knowledge/forensic-memory/)确认镜像能解析，再选择[进程与攻击行为](/knowledge/forensic-memory-processes/)、[对象与数据恢复](/knowledge/forensic-memory-recovery/)和[Linux 与 macOS](/knowledge/forensic-memory-unix/)的相应流程。完整工具参数以[Volatility 2/3 速查](/knowledge/forensic-memory-volatility/)为单一入口。

建立事件表时同时保留原时间与统一时间，标明系统漂移和采集持续区间。内存时钟、应用 `lasttime=`、vmtoolsd 日志和文件容器时间语义不同；两处相同缓存文本仍只有一条底层证据。资源名称、PID、账户名和路径可能复用，用标识、对象与时间共同连接。

## 02 Windows：把下载、执行、通信与删除分别证明

**场景与材料：** 一台训练工作站取得 Windows 内存副本、系统磁盘副本、浏览器数据库、进程创建日志和部分抓包。某下载文件当前不在原路径，目标是判断下载、执行、通信和删除各能确认到哪一步。

### 02.1 操作与证据位置

先在 Kali/Linux 分析目录固定材料，不因文件名相同就认定来自同机或同一时间：

```bash
mkdir -p output/processes output/network output/files
sha256sum work/memory.raw work/disk.raw work/traffic.pcapng \
  > output/input-hashes.txt
python3 vol.py -f work/memory.raw windows.info.Info > output/windows-info.txt
python3 vol.py -f work/memory.raw windows.pslist.PsList > output/processes/pslist.txt
python3 vol.py -f work/memory.raw windows.psscan.PsScan > output/processes/psscan.txt
python3 vol.py -f work/memory.raw windows.pstree.PsTree > output/processes/pstree.txt
python3 vol.py -f work/memory.raw windows.cmdline.CmdLine > output/processes/cmdline.txt
python3 vol.py -f work/memory.raw windows.netscan.NetScan > output/network/netscan.txt
python3 vol.py -f work/memory.raw windows.filescan.FileScan > output/filescan.txt
```

1. 从浏览器下载记录保存来源 URL、目标路径、开始/结束时间、状态与可得的大小；磁盘上查文件对象、目录、MFT/USN、回收站或已取得文件内容。访问页面、点击下载和文件落地分别确认。
2. 按路径和进程实例核对内存命令行、模块与句柄，保存 PID、PPID、对象地址及创建时间；再找进程创建日志与可用执行痕迹。Prefetch、兼容性缓存等各有语义，不能把所有记录统一写成执行证明。
3. 将网络对象与该进程生命周期对齐，按五元组、DNS、代理及抓包时段互证。远端 IP 可能是 CDN、共享代理或 NAT；抓包缺响应时只描述可见请求或通信尝试。
4. 从 USN、回收站、日志和目录变化核验删除/移动，不把“当前路径不存在”直接写成“执行后自删”。如果只取得缓存文件，另存地址类型、导出参数、缺页和格式验证。
5. 比较下载内容、磁盘候选与内存映像的字节范围。内存重建受重定位、导入、缺页和工具布局影响，不要求整文件哈希相同；有实际差异后再解释版本或替换。

### 02.2 判读、验证与边界

| 证据组合 | 可以确认 | 仍不能单独确认 |
| --- | --- | --- |
| 浏览器有记录，未取得完整文件 | 相应下载记录/状态 | 完整文件落地或已执行 |
| 文件内容、路径与下载信息一致 | 相应材料在限定位置存在 | 谁点击、是否执行 |
| 创建日志与内存进程实例一致 | 限定实例及运行线索 | 程序全部功能执行成功 |
| 内存端点与对应抓包/服务日志一致 | 覆盖时段内相应通信 | 未捕获时段及全部业务结果 |
| 删除记录与路径/对象/时间一致 | 对应删除或移动操作 | 所有副本都已消失 |

PID 被复用、父进程已退出、磁盘与内存采集较远时，在事件表中保留断点。若扫描只取得残留进程，不描述采集时持续运行。只有文件、进程实例、内容和时间均能连接，才将其编排为下载—执行—通信—删除过程；无法连接的记录仍分开交付。

## 03 Windows：缓存文档、画布与加密文件处理链

**场景与材料：** 训练场景中给定的镜像包含浏览器下载对象、旧便签、绘图进程和脚本文本，同机磁盘有一个扩展名伪装的加密文件。目标是提取可读信息，并验证它们是否指向同一文件处理过程。

### 03.1 按对象分开恢复

1. 先确认各应用实际版本与进程实例。旧便签可能是 `.snt`，新版可能是 `plum.sqlite`；旧 IE/GUI 插件也不能套用所有现代程序。
2. 保存 filescan 清单，从其实际 FILE_OBJECT 地址按虚拟/物理类型导出缓存；另行保存进程页与地址映射，另行重建可执行映像。三类输出各建目录和记录，不能把任意 `.dmp` 当成 minidump。
3. 对镜像或进程页分别扫描 ASCII 与 UTF-16LE，保存输入哈希、字节偏移、邻近内容和对象归属。便签提示、命令行与脚本字符串各只能支持其本身的范围。
4. 画布按候选像素区间恢复，保留偏移、宽高、行跨度、颜色通道、方向和可读页面。窗口布局辅助估计，不将旧 screenshot 输出当作完整桌面图。
5. 对脚本已确认的算法做离线字节复现，每次转换后重新核验真实格式。重复密钥 XOR、GIF 尺寸修正的可记录模板见[对象与数据恢复](/knowledge/forensic-memory-recovery/)，不执行未知脚本。

### 03.2 判读与验证

下载路径、提示文字与同名容器相互呼应，只能形成候选链；需要实际字节、算法材料、时间和目标验证才能提高结论。PDF 仅恢复前几页时报告部分内容，不将同名字符串填入缺页；画布存在缺页或方向未确定时保存多种解释，不推定模糊文字。

容器可只读打开后，检查卷大小、文件系统、多个目标文件及完整性。派生图像、解密输出与修正 GIF 均保存前后哈希、字节变化与验证范围。某一帧可显示、文件头看似正常或口令工具提示命中，都不足以宣布完整恢复。

## 04 历史 Windows：账户、硬件与自启动互证

**场景与材料：** 一份历史 Windows 镜像、同机磁盘 SAM/SYSTEM 与用户配置、任务/服务材料和执行日志，需要核验一个账户标识、CPU 描述及远控程序的启动情况。工具使用旧版 Volatility 2 或当前可支持的 Volatility 3，各自记录环境；不将 profile 加进 Vol3。

### 04.1 账户与会话

按[采集与识别页](/knowledge/forensic-memory/)核验 Profile 或 ISF 符号，保存进程与注册表 hive 列表。按[对象与数据恢复页第 05 节](/knowledge/forensic-memory-recovery/)从 `SAM\Domains\Account\Users\Names` 和 `Users` 键读取用户名到 RID 的映射，将该 RID 十六进制值转为十进制后，与完整 SID 末段、磁盘 `ProfileList` 及登录会话对照。

“账户存在”“账户曾登录”与“某进程在该会话中运行”需分别证明。内存 hive 可能有缺页，磁盘 hive 也可能采集时点不同，两者状态分开保存；磁盘密码哈希与 LSASS minidump 凭据提取按各自容器格式处理，不混用普通进程内存导出。

### 04.2 CPU 与时间

按[进程与攻击行为页第 03 节](/knowledge/forensic-memory-processes/)从进程环境变量（`PROCESSOR_IDENTIFIER`、`PROCESSOR_ARCHITECTURE`、`NUMBER_OF_PROCESSORS`）和结构化系统信息核验处理器线索：

```bash
profile='REPLACE_WITH_VERIFIED_PROFILE'
volatility -f work/memory.raw --profile="$profile" envars \
  > output/processes/vol2-envars.txt
rg -i 'PROCESSOR_IDENTIFIER|PROCESSOR_ARCHITECTURE|NUMBER_OF_PROCESSORS' \
  output/processes/vol2-envars.txt
```

逻辑处理器数量不等于物理插槽数，文档或驱动中的 CPU 品牌字符串也不能按出现次数投票。同样，内存系统时间（`Image date and time`）与 `lasttime=`、`vmtoolsd` 等日志字符串按[采集与识别页第 03.2 节](/knowledge/forensic-memory/)区分，以外部采集记录限定镜像制作时间窗，保留时钟漂移与时区偏差。

### 04.3 启动、运行和连接

从 Run、服务、计划任务、启动文件夹等类别保存实际配置，再关联程序路径与哈希、进程实例、服务运行信息和端点日志。`autoruns` 可能是社区插件，先查覆盖类别与不可读范围；LovelyMem/MemProcFS 视图提供定位，底层同一对象不因工具数量而成为独立证据。

自启动配置与安装目录存在时，确认到配置和程序；另有活动进程/执行日志才描述运行；有一致网络证据才描述连接。Jump List 代表交互线索，不能当作自动运行成功。验证表分别记录配置、运行、通信和限制，避免把安装存在写成采集时已远控。

## 05 Linux 与容器：宿主进程、命名空间和持久化文件

**场景与材料：** 一份 Linux 宿主内存镜像、同时间段 Docker 元数据/日志导出、宿主磁盘副本和少量流量记录。容器已退出，目标是解释一条脚本外连与部分临时文件是否有可核验关联。这里只分析已有导出，不启动容器或执行 exec 来补历史状态。

### 05.1 符号有效后再关联对象

按[Linux 与 macOS 内存分析](/knowledge/forensic-memory-unix/)核验完整 banner、架构和调试材料，用匹配 ISF 解析多个对象。没有匹配符号时保存错误和字符串，不编造进程/网络结果。以下只作为完成符号验证后的分析模板：

```bash
mkdir -p output/linux
python3 vol.py -s ./symbols -f work/memory.raw linux.pslist.PsList \
  > output/linux/pslist.txt
python3 vol.py -s ./symbols -f work/memory.raw linux.pstree.PsTree \
  > output/linux/pstree.txt
python3 vol.py -s ./symbols -f work/memory.raw linux.psaux.PsAux \
  > output/linux/psaux.txt
python3 vol.py -s ./symbols -f work/memory.raw linux.lsof.Lsof \
  > output/linux/lsof.txt
python3 vol.py -s ./symbols -f work/memory.raw linux.sockstat.Sockstat \
  > output/linux/sockstat.txt
python3 vol.py -s ./symbols -f work/memory.raw linux.mountinfo.MountInfo \
  > output/linux/mountinfo.txt
```

保存 PID/UID、进程开始时间、对象地址、路径、映射、打开文件及网络/挂载命名空间。将这些字段与已保存的 Docker State、top、Mounts、NetworkSettings、容器 ID 和启动/退出时间对应。top 通常提供宿主 PID，容器内 PID 与宿主 PID 不能直接等同；PID 重用或退出后不可读要单列。

配置和运行环境也不等同：inspect 的 Config.Env 是创建配置，exec env 属于后来新增进程，取得的 `/proc/<PID>/environ` 主要对应所选进程启动时的环境区域，不能保证包含所有后来修改。对已有 environ 导出可按 NUL 分隔查看，不访问真实主机：

```bash
tr '\0' '\n' < work/captured-environ.bin > output/linux/environ-readable.txt
```

### 05.2 挂载与临时数据

bind mount、named volume、可写层与 tmpfs 的证据位置不同。tmpfs 由内存支持，可能涉及交换，不能假定普通容器层归档包含其历史完整内容；磁盘上空目录不否认采集较早时的临时数据。Kubernetes `emptyDir` 还须核验介质、Pod UID、节点与生命周期，详细内容保留在[服务器集群](/knowledge/forensic-kubernetes-cluster/)。

Docker stats 是资源指标，不是 RAM 镜像；OOMKilled 是状态线索，应与内核、daemon、容器日志及时间核验。stats、top、日志、导出可写层和完整内存各覆盖不同对象；不能用一份当前统计补成过去内存状态。停止、kill、重启和 exec 会改变进程或易失数据，已经退出的容器不能为了得到 top 结果而在检材上重启。

### 05.3 判读与验证

进程参数有脚本、Bash 缓冲有类似命令、套接字有外部端点：三项仍是线索。取得同一脚本内容、进程时间、打开文件/映射和实际请求日志一致时，才描述限定执行与通信。Bash 可能包含未执行输入，旧套接字不证明仍活动。

缓存恢复的 inode/文件页须保留地址类型、缺页与零填充，再与磁盘版本比较；符号和文件恢复命令仍见 Unix 页。容器启动、停止、层/卷提取、保存导出与运行时命令保持在 Docker 专题，内存页只负责运行对象与跨层关联。最终记录 `宿主镜像 → 进程实例 → 命名空间/容器标识 → 挂载/文件对象 → 日志/流量 → 时间与限制`。

## 06 程序与 Web 流量：功能请求不等于已加载或执行

**场景与材料：** 一份 Java 服务磁盘副本、应用日志、可见 Web 请求和已取得的主机内存；请求中出现组件加载或命令调用线索。另有一个构造的 PE 样本及隔离调试记录，用于说明静态能力、当次实验和历史运行状态的差异。

### 06.1 Java 运行时与请求互证

网络正文的编码、加密和分层解码仍按[网络流量分析](/knowledge/forensic-network-traffic/)执行；不把可疑字节送进 Java 反序列化器。操作名称、长 Cookie、HTTP 200 或特殊返回符号只说明请求/响应线索。内存组件是否已经加载，需要相应运行时类、Servlet/Filter/Listener 注册或内存内容，并与服务进程实例、加载上下文、应用日志及时间对应。

主机内存可先核验 Java 进程参数、映射、打开文件和端点；通用 Volatility 进程结果不保证直接枚举 JVM 所有类或 Servlet 注册表。若材料与工具不能解析这些运行时结构，明确记录缺口，不编造 Java 插件参数或以一个类名字符串代替有效注册对象。

同名类、文件、脚本或流量中的“内存模块”字样不足以证明实际驻留。验证链至少区分请求到达、加载/注册、调用、结果与后续影响；命令执行另需进程/审计与输出，文件写入另需内容和文件对象。只有通信机制证据时，结论止于通信机制；没有运行时材料时，不确认内存驻留组件已成功加载。

### 06.2 PE 模块与受控实验

静态 PE 的 COFF/PDB、导入、RVA/VA、Go/JNI、RC4/AES 逻辑仍保留在[程序与恶意代码分析](/knowledge/fic-case-07/)。内存实战关注取得时的实际模块基址、大小、路径、内容和进程实例；ASLR 后实际 VA 由实际加载基址加 RVA，不能拿首选基址直接定位。

调试器的系统断点、程序入口、载荷加载后的断点，以及附加到已有进程是不同观察时点。记录架构、工具、启动/附加方式、断点、模块列表及按基址/路径去重的计数口径；静态导入项和运行时模块数不能互相替代。只在实验快照中出现的落地文件、任务或网络请求，属于当次实验结果。

**判读与验证：** 文件含 URL 并调用网络 API，但断网实验请求失败，可以描述静态请求逻辑与当次失败；不能写成历史主机已下载。另一环境联网后产生新程序/任务，比较其哈希、路径与参数，再说明实验新增状态。相同样本具有某项能力，不保证历史设备在不同配置和依赖条件下已经成功执行该功能。

## 07 内存密钥与保护层：最终验证目标数据

**场景与材料：** 同机磁盘副本含一个加密容器、一组账户材料与 DPAPI blob，另取得内存镜像或有效 LSASS minidump。目标是恢复必要文件；不把所有可用口令和密钥混为一种材料。

1. 固定容器、卷元数据、账户材料、DPAPI 主密钥文件与内存的标识和时间。区分完整物理内存、进程页、内核转储和 minidump，按格式选择解析器。
2. 从字符串、有效凭据容器或匹配密钥扫描中取得候选，记录进程/会话、字节位置、算法/格式、目标账户或卷，以及工具支持和缺页情况。无命中不证明没有加密或没有登录。
3. 分开验证账户哈希、DPAPI 主密钥、容器密码/PIM/keyfile、BitLocker 恢复/内存密钥与 EFS 私钥。对每种材料只描述已成立的条件，不把账户口令扩展为全盘已解。
4. 在副本上进行相应离线解密或只读验证；完整方法见[对象与数据恢复](/knowledge/forensic-memory-recovery/)和[加密数据与凭据](/knowledge/forensic-protected-data/)。派生镜像写新路径，保全密文与输出映射。
5. 检查真实文件系统、目录、多个目标内容、格式和完整性。外层卷与隐藏卷分别记录，不能因外层正常就认定无隐藏数据；也不能因一次失败就认定目标不存在。

**判读与验证：** 一个账户口令成功解开对应 DPAPI 主密钥，但容器仍打不开，可以确认该 DPAPI 条件成立；容器仍可能依赖不同口令、keyfile、PIM 或格式。密钥候选产生数个可打印字节也不构成成功，数据库需有合理 schema/记录，压缩包需通过结构与完整性检查。公开结果只保留必要材料标识和验证范围，秘密本体单独受控。

## 08 交付可复核的事件表与未解决项

每个结论使用同一记录结构，保留中间提取物和完整工具错误：

| 记录项 | 内容 |
| --- | --- |
| 事实或假设 | 分别写对象存在、配置存在、进程运行、请求发出、结果成功等 |
| 材料与定位 | 镜像/文件哈希、插件、对象地址类型、PID 与生命周期、路径/键/帧号 |
| 原时间与统一时间 | 时区、系统漂移、采集窗口与独立时间依据 |
| 提取/变换 | 完整参数、输入范围、缺页、填零、重建、修复及输出哈希 |
| 互证与替代解释 | 磁盘、日志、流量、格式结构及合法软件/JIT/缓存等解释 |
| 结论强度与边界 | 已确认、候选、不可读、不支持、覆盖缺口与下一步所需材料 |

交付前抽查同 PID 是否发生复用、对象是否属于同一镜像、VA/物理/文件偏移是否混用、相同缓存是否被重复计票、实验状态是否误并入历史，以及插件错误是否被当成空结果。字符串、名称与工具标签用于定位；完整行为需要对象、内容、时间与结果的连接。

缺少一类材料时仍能交付已确认范围：只有磁盘可以分析持久化痕迹，只有内存可以记录可读对象，只有流量可以描述可见通信。明确缺口后停止扩大结论，后续补得材料使用相同镜像标识与验证方法重新对照。
