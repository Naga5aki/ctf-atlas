拿到 Windows 磁盘镜像或导出的配置单元、事件日志与用户目录时，先识别系统盘、Windows 版本、时区与账户 SID，并在工作副本上按“系统基线与账户 → 事件日志与命令历史 → 外设与客户端痕迹 → 程序执行与文件落地”的顺序推进。不要将文件的访问时间（`atime`）直接当作用户操作时间；复制、扫描、同步和提取过程都可能改变文件系统时间字段。

## 01 首轮证据保全与离线排查顺序

优先在只读挂载或工作副本中保全四大类核心材料，并分别记录 SHA-256 哈希：

| 证据类别 | 检材内常见路径 | 首轮用途与深入专页 |
| --- | --- | --- |
| 注册表配置单元 | `Windows\System32\config\`（`SYSTEM`/`SOFTWARE`/`SAM`/`SECURITY`）、用户 `NTUSER.DAT` 与 `UsrClass.dat` 及同名 `.LOG1`/`.LOG2` | 系统版本、时区、本地账户、USB、启动项与目录交互 → [注册表取证](/knowledge/forensic-registry/)、[ShellBags 取证](/knowledge/forensic-shellbags/) |
| Windows 事件日志 | `Windows\System32\winevt\Logs\`（`Security.evtx`、`System.evtx`、PowerShell、Sysmon、TerminalServices 等） | 开机/关机区间、登录认证、服务安装与进程创建 → [事件日志取证](/knowledge/forensic-windows-logs/) |
| 用户与客户端目录 | `Users\<用户名>\`（`Recent`、Jump Lists、`AppData` 下的浏览器、远程控制与 SSH/数据库客户端） | 访问/下载记录、外联会话与保存凭据 → [浏览器取证](/knowledge/forensic-browser/)、[远程连接痕迹](/knowledge/forensic-remote-connections/) |
| 文件系统与卷快照 | `$MFT`、`$Extend\$UsnJrnl:$J`、`$LogFile`、`$Recycle.Bin\<SID>\` 与卷影副本（VSS） | 文件创建、改名、移入回收站及历史版本恢复 → [NTFS 取证](/knowledge/forensic-fs-ntfs/) |

在 Windows 分析环境中，可用 PowerShell 对离线导出的 `.evtx` 副本做首轮枚举（事件详情仍需核对原始 XML 字段）：

```powershell
Get-WinEvent -Path .\Security.evtx -MaxEvents 20 |
  Select-Object TimeCreated, Id, ProviderName
Get-WinEvent -Path .\System.evtx -MaxEvents 20 |
  Select-Object TimeCreated, Id, ProviderName
```

首轮串联时遵循四条底线：
1. **先定启动周期，再排登录与执行：** 从 `System.evtx` 确定开机、关机、时间校准和异常重启区间；将 `Security.evtx` 中的 `4624`/`4625` 与账户 SID、登录类型、来源地址对齐（多次失败不代表已进入系统），`7045` 提示服务安装，`4688` 提供进程创建线索（未开启审计时缺席不代表未执行）。
2. **区分“存在”“缓存”与“执行”：** 对照 Prefetch（`Windows\Prefetch\*.pf`）、`Amcache.hve`、ShimCache、计划任务、服务配置和 LNK/Jump List。Prefetch 命中说明系统留下了程序执行相关痕迹，但不能直接推断自然人身份；`Amcache`/ShimCache 单独出现仅证明文件存在或兼容性扫描。
3. **浏览器主库与 WAL 同批复制：** 查询下载与历史前，连同同目录的 `-wal`、`-shm` 一起复制到工作目录，区分“网页被访问”“文件被下载”与“文件被打开/运行”三个不同层级。
4. **每个结论配两条独立印证：** 统一转换到同一时区（保留原始整数时间值），标明夏令时与时钟偏差；无法确认自然人时，如实表述为“该账户会话或设备留有以下活动记录”。

## 02 离线确认 Windows Build 与本地口令策略

**场景与材料：** 已取得 Windows 系统盘副本及 `SOFTWARE`、`SYSTEM`、`SAM` 配置单元，需要确认系统版本和本地密码策略。先记录各配置单元哈希，使用 Registry Explorer、RegRipper 或 RECmd 的离线解析功能；不要将目标配置单元覆盖到分析机系统目录。

### 02.1 版本字段分别回答什么

在 `SOFTWARE\Microsoft\Windows NT\CurrentVersion` 中完整导出以下字段及其类型：

| 字段 | 判读 | 核验与限制 |
| --- | --- | --- |
| `CurrentBuild` / `CurrentBuildNumber` | 已安装系统的 Build 主编号候选 | 同时核对内核文件版本、内存系统信息，保留差异 |
| `UBR` | 更新修订号，可与主编号组成 `Build.UBR` | 缺失不能随意补零；注意配置单元与内核是否来自同一状态 |
| `DisplayVersion` | 可读的版本标识 | 不等同于 Build 整数，也不能替代补丁号 |
| `ProductName` | 产品名称字符串 | 升级或兼容性可能保留旧标识，不宜单独判断 Windows 10/11 |
| `BuildLab` / `BuildLabEx` | 构建分支、基线等附加信息 | 不能把其中数字自动当成当前已安装补丁版本 |

**示例判读：** 若主编号为 `22631`、`UBR` 为 `3007`，可记录配置单元给出的组合版本为 `22631.3007`；这些是示意值。是否与当前内存或系统文件一致，应分别核对，不能只取 GUI 显示的版本名称。

### 02.2 SAM 中的最大密码期限是相对时长

常见 `SAM\Domains\Account` 的二进制 `F` 结构中，最大密码期限位于 `0x18`、最短期限位于 `0x20`；**这是对应结构布局下的值偏移，不是整个 SAM 文件的绝对偏移**。先核对结构版本与长度，再将 `F` 值导出为 `work/domain-account-F.bin`。期限通常是小端有符号 64 位的负值，以 `100 ns` 为单位；它是相对时长，不能按从 1601 年开始的绝对 FILETIME 转日期。

```bash
python3 - ./work/domain-account-F.bin <<'PY'
from pathlib import Path
from decimal import Decimal
import struct
import sys

data = Path(sys.argv[1]).read_bytes()
if len(data) < 0x28:
    raise ValueError('F 值不足以读取已核对结构中的期限字段')
for name, offset in [('MaxPasswordAge', 0x18), ('MinPasswordAge', 0x20)]:
    raw = data[offset:offset + 8]
    value = struct.unpack('<q', raw)[0]
    print(name, 'offset=', hex(offset), 'raw_le=', raw.hex(), 'signed=', value)
    if value in (0, -(1 << 63)) or value > 0:
        print('特殊值或不符预期，按该结构/策略语义另行核对')
        continue
    seconds = Decimal(-value) / Decimal(10_000_000)
    print('seconds=', seconds, 'days=', seconds / Decimal(86400))
PY
```

**结果示例：** `-25920000000000` 换算为 `2592000` 秒，即 `30` 天。脚本报告原字节和整数，避免只留下一个天数。零值、无限期限哨兵值和结构版本差异应单独确认；最短期限为零可具有有效策略含义，不能与最大期限不加区分。

**交叉核验：** 在独立的 Windows 仿真副本中，可用 `net accounts` 或 `secpol.msc` 查看当次生效策略，并注明运行环境。这些结果可能受域策略或重启后的配置影响，不自动等同于离线本地 SAM 在采集时的全部有效域策略。系统级最大期限也不等于某个账户一定会过期，还应检查账户自身的密码永不过期标志。

## 03 SAM 哈希、RID 与 ControlSet 的版本边界

**材料：** 同一系统状态的 `SYSTEM` 和 `SAM` 副本、解析器版本以及用户清单。先从 `SYSTEM\Select\Current` 选择有效 `ControlSet00x`；不要固定写 `ControlSet001`，也不要把运行系统中的 `CurrentControlSet` 视为离线 hive 必然存在的独立实体。

1. 从有效 ControlSet 的 `Control\Lsa\JD`、`Skew1`、`GBG`、`Data` 读取键的 **Class 元信息**。它们不是普通默认值；按实际格式拼接、十六进制解码、置换后得到 bootkey 候选。
2. 解析 SAM 域级密钥结构的 revision 和 salt/data 长度，再处理用户 `Users\<RID>\V` 中哈希记录的 offset、length 与 revision。旧式 RC4 分支和较新的 AES 分支不能混为同一公式。
3. 旧式用户哈希链包含 SAM 域密钥、RID 小端字节及算法常量的派生，RC4 解开后还要执行 RID 派生的两组 DES 解包。常见较新用户哈希记录先按自身 salt/AES 结构解开，再同样执行 RID 派生的 DES 解包；域级密钥结构与用户哈希结构的 revision 应分别核对。**`MD5(bootkey)` 或 `RC4(MD5(hbk+RID+密文), 密文)` 都不足以描述完整通用链。**可对照 [Impacket SAMHashes 实现](https://github.com/fortra/impacket/blob/master/impacket/examples/secretsdump.py)核验目标结构的处理顺序。
4. 将用户名、RID、完整 SID 与解析输出关联。`Users\Names` 与 RID 项是相互对应的不同结构；RID 十六进制、十进制和 SID 尾段需分别表示，不能把末四个十六进制字符当成十进制 RID。
5. 校验配置单元匹配、结构长度和域密钥校验信息；仅输出一段 16 字节数据不代表已经取得正确 NT 哈希。哈希也不是明文口令，不能据此断言某个口令或认证行为。

**实战判读：** 两个解析器都能解出同一 RID 的哈希，但使用的是同一对 hive。这是实现层面的复核；若再从内存恢复相关用户对象、以 SID 和时间状态匹配磁盘账户，可补充另一证据方向。受损 hive、不同快照的 SYSTEM/SAM、错误 ControlSet 或不支持的 revision 应报告为解析限制，不能将空值解释成无口令。

实际操作参数与凭据保护统一见[加密数据与凭据](/knowledge/forensic-protected-data/)，此处保留系统身份和结构核验入口。

## 04 PowerShell 历史与 Base64 编码脚本还原

PSReadLine 常见用户路径为 `AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`，配置可以改变保存路径和行为。保留用户归属、文件时间、完整内容和编码。历史文本通常没有逐条时间戳，不能强行给每行分配执行时刻。

命令行中的 `-EncodedCommand`（常简写为 `-enc` / `-e`）通常承载 UTF-16LE 文本的 Base64；先在副本上静态解码，再检查脚本逻辑，不执行未知命令：

```python
import base64
from pathlib import Path
encoded = Path('work/encoded-command.txt').read_text(encoding='ascii').strip()
decoded = base64.b64decode(encoded, validate=True).decode('utf-16le')
Path('output/decoded-command.ps1').write_text(decoded, encoding='utf-8')
```

脚本内部二次解码的内容可能另有 UTF-8 Base64、Gzip/Deflate 压缩或 XOR 封装，不应全部硬套 UTF-16LE。将静态解码结果与进程命令行（4688 / Sysmon 1）、PowerShell 脚本块日志（4104）、下载 URL 和落地文件哈希关联。

## 05 USB 与蓝牙设备：标识、关联与时间分开取

| 对象 | 证据位置 | 首轮取值 | 不能直接推出 |
| --- | --- | --- | --- |
| USB 存储实例 | 有效 `SYSTEM\ControlSet00x\Enum\USBSTOR` | 厂商/产品、实例 ID、序列号候选 | 每次插入/拔出时间或实际使用者 |
| 蓝牙配对线索 | `SYSTEM\ControlSet00x\Services\BTHPORT\Parameters\Devices` | 地址键、名称/属性 | 目录为空即从未连接 |
| 设备枚举与软件视图 | SOFTWARE / SYSTEM 中相关设备实例、属性及 `SWD#WPDB#...` 等候选字符串 | 设备标识、关联 GUID、原始字符串 | 任意 GUID 尾部都可当蓝牙 MAC |
| 插拔/安装事件 | `Windows\System32\winevt\Logs\`、设备安装相关日志 | Provider、Channel、EventID、XML 设备字段和时间 | 单凭 `20001` / `20003` 等整数解释全部活动 |

**独立实战：** 从 USBSTOR 导出某实例，例如尾部为 `EXAMPLE123&0`。保留完整实例值，再依据该设备和解析器定义区分序列号与实例后缀；不要对所有值盲目删除末两字符。把设备实例与卷标识、挂载记录、LNK/Jump List 和事件 XML 对照，确定涉及哪个卷与用户视图。完整 U 盘与 MFT 证据链见[U盘取证](/knowledge/forensic-usb-evidence/)。

查蓝牙时先记录有效 ControlSet；如 BTHPORT 记录为空，继续检查枚举与软件层属性。原始字符串扫描只提供候选：MAC 可能采用无分隔字节串或不同字节顺序，先核对结构和设备名称，再以对应设备属性印证。设备地址、随机地址、连接时刻与物理设备归属是不同结论。

**时间判读：** 将事件的 Provider 和 Channel 一并导出，确认事件是否表示安装、配置、启动、连接或删除。记录的 UTC 时间与工具显示本地时间同时保留；注册表键最后写入时间不一定等于设备最后插入时间。详细事件分析见[Windows 事件日志](/knowledge/forensic-windows-logs/)。

## 06 Xshell 会话与 Anytype 版本历史

### 06.1 Xshell 的会话名和连接目标

常见位置为 `Users/<用户>/Documents/NetSarang Computer/<版本>/Xshell/Sessions/*.xsh`，也可能由用户配置改动。文件名可提供会话名称，内容中的 `[CONNECTION]`、`Host=`、`Port=` 等字段提供保存目标；它们证明配置内容，不单独证明成功连接或真实操作者。

```bash
python3 - ./work/session.xsh <<'PY'
from pathlib import Path
import sys
data = Path(sys.argv[1]).read_bytes()
encoding = 'utf-16' if data[:2] in (b'\xff\xfe', b'\xfe\xff') else 'utf-16le'
text = data.decode(encoding, errors='strict')
for line in text.splitlines():
    if line.startswith('[') or line.startswith(('Host=', 'Port=')):
        print(line)
PY
```

示例假定已经检查字节头、确认是 UTF-16 系列；没有 BOM 时用 UTF-16LE 仍需由实际字节及版本核实，不能对所有文件强行采用该编码。保留原文件哈希，解码失败先查编码和截断；会话文件名相同也可能指向不同历史内容。连接行为再结合日志、网络与服务器认证记录，完整专题见[远程连接与客户端](/knowledge/forensic-remote-connections/)。

### 06.2 Anytype 对象与历史时间

定位对应用户的 `AppData\Roaming\anytype\`，枚举实际版本的账户、空间与 `objectstore\objects.db` 候选路径。文件名后缀 `.db` 不能证明是 SQLite；先检查头、应用版本及存储实现，再使用匹配解析方式或断网界面副本，不能用未知数据库结构直接拼 SQL。

**场景：** 当前页面包含一个多层编码文本，需要判断页面何时创建、哪些内容曾修改。先固定对象库、关联索引/日志和应用配置；按对象 ID、空间 ID 和修订标识定位当前对象及版本历史，分别记录创建、修改、同步和导入时间的字段含义。界面“版本历史”只是一个读取入口，截图应关联到底层对象和修订，不能把数据库文件 mtime 当成页面创建时间。

多重编码可用 CyberChef 的识别提示提出候选，但每层都要保存输入、变换、输出字节和编码。Magic 得到可读串只表明某种解释可能；地址归属、账户身份及历史使用要另以对应结构和行为证据验证。启动副本客户端可能迁移库或同步，操作前后分别固定哈希并注明变化，不能让副本新增记录混入历史结论。

## 07 Windows 11 的版本与新痕迹边界

先记录精确 Build、补丁、设备类型、用户和功能启用状态。不能认为每台 Windows 11 都有 Recall，也不能把早期测试版路径/明文结构套用于当前版本。

| 功能 | 证据方向 | 条件与限制 |
| --- | --- | --- |
| Recall | 本地屏幕快照、检索关联信息、配置与保留范围 | 仅适用设备和启用状态；较新版快照/索引加密，涉及 Windows Hello ESS、TPM 和 VBS Enclave |
| Copilot | 浏览器/App 包、缓存、登录和同步线索 | 产品版本与账户不同；不能推定对话必然完整落盘或全部只在本地 |
| 历史 WSA | 应用包 LocalCache 中候选 `userdata.vhdx`、Android 数据 | 已结束支持的历史组件仍可能留痕；VHDX 内 Linux 文件系统不能简单分配 Windows 盘符读取 |
| Phone Link | 相应应用包 LocalState、配对信息、缓存与数据库 | 消息/照片可能从关联手机同步，需确认设备标识 |
| 截图工具 | 用户图片/截图目录、应用包缓存、图片元信息 | 截图保存时间与画面中事件时间分开 |
| 资源管理器标签页 | ShellBags、LNK、Jump Lists、最近访问及版本相关状态 | 不保证存在完整的每标签页历史 |

在工作副本中按真实应用包标识定位 LocalState/LocalCache，再检查文件头、schema 与版本。Pluton/TPM 和 VBS 的存在不表示全部文件都可由同一密钥解密。Recall 的离线可见范围受到加密与用户认证约束，缺少解密条件时记录限制，不能将空目录解释为未使用。

## 08 实战一：下载、执行与删除的分层证据链

**场景与材料：** Windows 磁盘镜像中有浏览器下载、Prefetch、回收站和部分事件日志，需要核对一个程序文件的处理过程。先固定版本、账户 SID、分区与时间范围。

1. 从浏览器数据库确认下载任务和跳转链，用实际落地文件大小、内容哈希与记录状态核对下载完成。
2. 将程序路径与 4688/Sysmon 1 进程事件、Prefetch 和 UserAssist 对应，保留会话、父进程及时间；Amcache/ShimCache 作为不同语义的辅助材料。
3. 在回收站元信息（`$I`/`$R`）、MFT/USN 和历史副本中核对相同对象。当前路径缺失可能是删除、移动、未采集或卷未读取，不能只以缺失下结论。
4. 对编码 PowerShell 参数静态解码，将脚本逻辑与 4104、进程命令行、请求和文件哈希关联；历史文本不提供逐条准确执行时刻。

| 已取得的材料 | 先能确认的层级 | 需补的环节 |
| --- | --- | --- |
| 下载任务与文件对应 | 下载到目标路径的证据 | 是否运行、由谁运行 |
| 进程创建与文件相符 | 某账户会话中的程序启动 | 程序后续业务行为 |
| 回收站或删除元数据对应 | 删除/移入回收站相关记录 | 内容是否完整恢复及实际操作人 |

每一层都有独立记录才连成完整过程。日志未启用、系统功能不支持或采集范围缺失时明确记录，避免把“没有记录”自动解释为“没有行为”。

## 09 实战二：快捷方式、计划任务与图片载荷加载链

**场景与材料：** 桌面快捷方式指向一个 PE，程序可能下载图片、从图中提取载荷并创建计划任务。先离线解析快捷方式的 Target、Arguments、WorkingDirectory、相对路径与卷标识，再按这些条件解析目标；**快捷方式所在目录、目标直接父目录和当前工作目录可以不同**。

1. 固定 LNK、目标 PE、用户和文件路径。目标字符串只能证明保存的指向，结合进程创建、Prefetch 和日志判断是否执行。
2. 对 Go PE 检查构建/模块元数据、函数引用和数据流。HTTP 与隐写相关包名可提示功能，**它们可能来自 Go 元数据或字符串，不能都称作 PE 导入表条目**；包名出现也不证明该路径实际执行。
3. 按 `请求 URL → 保存/读取图片 → 图像隐写解码 → 产物写入 → 启动或持久化` 追踪调用、长度和返回值。`.rdata` 的 URL 是静态候选，与历史抓包、缓存及落地文件哈希对应后才能提升证据级别。
4. 保全 `Windows\System32\Tasks\` 的任务文件、`SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache` 及相关事件；旧式任务还可能位于 `Windows\Tasks`。区分任务名、动作程序路径、参数和触发器，不把“Tasks Scheduler”当成通用实际文件夹。
5. 从已经固定的图片副本提取候选程序，检查文件头、PE 结构、长度和哈希，并与计划任务动作、磁盘和内存模块对应。提取成功证明图中有可解析载荷，不证明它已启动或联网成功。

确需观察时采用独立 Windows 快照，明确沙箱网络、权限、调试时点和新增任务；云沙箱上传未知样本可能披露内容，应先确认材料可对外提交。实验报告是该次实验的行为证据，不能代替原设备的历史日志。PE 算法与模块时点的技术细节统一见[程序样本与恶意代码取证](/knowledge/fic-case-07/)，隐藏载荷结构见[文件格式与隐写](/knowledge/fic-case-09/)。
