## 01 用问题选择 Hive

注册表由 Hive、键、子键、值名、值类型和数据组成。离线分析先找对应配置单元，不把运行中系统的 `HKCU` 自动当成目标用户。

| 配置单元 | 常见位置 | 优先回答 |
| --- | --- | --- |
| `SYSTEM` | `Windows/System32/config/` | 计算机名、时区、服务、网络、USB、控制集 |
| `SOFTWARE` | 同上 | 系统版本、软件安装、机器级启动项 |
| `SAM` | 同上 | 本地账户、RID、账户状态、组 |
| `SECURITY` | 同上 | 策略、LSA 相关数据；需要适当密钥材料解释 |
| `DEFAULT` | 同上 | `.DEFAULT` 系统上下文设置；不是新用户模板目录 |
| `NTUSER.DAT` | `Users/<用户>/` | UserAssist、Run、RecentDocs、TypedPaths |
| `UsrClass.dat` | `Users/<用户>/AppData/Local/Microsoft/Windows/` | ShellBags、COM、资源管理器行为 |
| `Amcache.hve` | `Windows/AppCompat/Programs/` | 程序清单、路径、版本相关哈希与时间 |

每个用户分别记录 SID、目录与 Hive 哈希。同步导出 `.LOG1`、`.LOG2` 等事务日志；它们可能包含尚未合入主 Hive 的数据。先保存不可变副本，再由支持 replay 的解析器在工作目录重放，保存重放前后哈希与日志。RegRipper 3.0 不会自动完成这一步。

## 02 系统基线与 ControlSet

离线 `SYSTEM\Select` 的 `Current`、`Default`、`LastKnownGood`、`Failed` 含义不同。若 `Current=1`，通常按 `ControlSet001` 查询；不能写成不存在的 `CurrentControlSet001`，也不能一律固定为 001。

| 问题 | Hive 内相对位置 | 记录内容 |
| --- | --- | --- |
| 计算机名 | `SYSTEM\ControlSet00x\Control\ComputerName\ComputerName` | `ComputerName`，与日志主机名比对 |
| 时区 | `SYSTEM\ControlSet00x\Control\TimeZoneInformation` | `TimeZoneKeyName`、Bias、夏令时规则 |
| 系统环境变量 | `SYSTEM\ControlSet00x\Control\Session Manager\Environment` | PATH、TEMP 等；与进程环境区分 |
| 系统版本与登记信息 | `SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `ProductName`、构建号、`RegisteredOwner` |
| 用户目录映射 | `SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList` | SID 与 `ProfileImagePath` |
| Firefox 版本线索 | `SOFTWARE\Mozilla\Mozilla Firefox` | 可能存在 `CurrentVersion`；便携版或不同安装方式可能无此项 |

`RegisteredOwner` 是登记信息，不必然是实际操作人；`ProductName` 要与构建号核对。时区 Bias 的方向与工具显示规则需确认，历史夏令时不能只靠采集时的 `ActiveTimeBias` 推算。

## 03 账户、外设与网络

### 03.1 本地账户

`SAM\Domains\Account\Users` 与 `...\Users\Names` 提供本地账户映射。结合 RID、账户状态、最后登录相关字段和组成员关系识别异常账户。账户名可改，SID/RID 更适合关联；注册表键时间不能简单当作账户创建时间。

“账户属于管理员组”与“此次操作使用了管理员权限”不同。后者还要结合登录类型、令牌、特权事件或进程信息。密码材料的离线处理见 [凭据与加密](/knowledge/forensic-protected-data/)。

### 03.2 USB 与盘符

| 位置 | 主要线索 | 交叉核对 |
| --- | --- | --- |
| `SYSTEM\ControlSet00x\Enum\USBSTOR` | 存储设备类型、厂商、实例标识 | 实际序列号可能受设备实现影响 |
| `SYSTEM\ControlSet00x\Enum\USB` | VID/PID、设备实例 | 不限于 U 盘 |
| `SYSTEM\MountedDevices` | `\DosDevices\E:`、卷 GUID 等二进制映射 | 盘符会复用，需对应卷和时间 |
| `SOFTWARE\Microsoft\Windows Portable Devices\Devices` | 便携设备名称、标识 | 结合 USB 实例与用户活动 |

验证顺序：设备实例 → 卷标识 → 当时盘符 → 用户 LNK/Jump List → 文件哈希和时间。只看到 USBSTOR，最多确认设备识别痕迹；要证明复制了某文件，还需文件操作证据。

### 03.3 网络配置

`SYSTEM\ControlSet00x\Services\Tcpip\Parameters\Interfaces` 可提供网卡的 DHCP/静态 IP、DNS、网关线索。`SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList` 下的 `Profiles`、`Signatures` 可用于网络名称、类型与连接时间分析。

这些字段并非完整流量历史。将接口 GUID、网络名称、时间和日志对应；当前保留的 IP 不一定是事件发生时使用的 IP。

## 04 程序执行与文件访问

| 痕迹 | Hive 内路径或文件 | 解释边界 |
| --- | --- | --- |
| UserAssist | `NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist` | 部分 GUI 程序活动；名称常为 ROT13，次数与时间结构随版本变化 |
| ShimCache | `SYSTEM\ControlSet00x\Control\Session Manager\AppCompatCache` | 程序存在或兼容性处理线索，不可单独断言执行 |
| Amcache | `Amcache.hve` | 软件/文件清单；不同版本记录含义不同，哈希可能仅覆盖部分数据 |
| TypedPaths | `NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths` | 地址栏输入路径，可能含 UNC、盘符或 FTP |
| RecentDocs | `...\Explorer\RecentDocs` | 最近文档及分类 MRU，需解码二进制结构和顺序 |
| 打开/保存对话框 | `...\Explorer\ComDlg32\OpenSavePidlMRU`、`LastVisitedPidlMRU` | 文件选择对话框相关目录与对象 |
| ShellBags | `Software\Microsoft\Windows\Shell`、`ShellNoRoam` 或 `UsrClass.dat\Local Settings\Software\Microsoft\Windows\Shell` | 目录视图、BagMRU/Bags；不能据此证明目录内文件被打开 |

```python
import codecs
print(codecs.decode(r'P:\Jvaqbjf\Flfgrz32\pnyp.rkr', 'rot_13'))
```

ROT13 只处理键值名称的编码，不解析 UserAssist 的二进制统计字段。MRUListEx 的顺序也不等于每项都有独立时间。将 UserAssist 与 Prefetch、4688、Amcache 对应；把 ShellBags 与 LNK、USB、MFT 对应。

## 05 启动项和服务

机器级启动项位于 `SOFTWARE\Microsoft\Windows\CurrentVersion\Run` / `RunOnce`；用户级对应 `NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Run` / `RunOnce`。记录值名、完整命令、参数、路径、签名与哈希，核对 WOW64 视图和环境变量展开。

服务集中在 `SYSTEM\ControlSet00x\Services`，检查 `ImagePath`、`Start`、`Type`、`ObjectName`、`DisplayName`、`Description`。`Start` 常见值：0 引导、1 系统、2 自动、3 按需、4 禁用；仍需结合服务/驱动类型和触发条件。

可疑路径、空描述、类似系统的名称只能用于筛选。把服务项与 7045、进程命令行和磁盘程序对应。计划任务还应检查任务文件与事件日志，不能只查 Run 后就认定没有持久化。

## 06 时间分析与结果记录

**Key LastWrite 是键的最后写入时间，通常不是某个 Value 的独立修改时间。** Run 键在某时变化，不足以证明当前某一启动项就在该时创建。

保存：`Hive 哈希 / 是否重放日志 / SID / ControlSet / 完整键路径 / 值名及类型 / 数据 / LastWrite UTC / 工具版本 / 交叉证据`。对不同时区的显示先统一，再比对；原始整数时间不要丢弃。

## 07 离线工具操作

Registry Explorer 适合多 Hive、事务日志和书签浏览；RECmd 适合批量导出；RegRipper 用插件提取固定痕迹；FTK Imager、Autopsy、KAPE 分别辅助导出、综合解析和按目标采集。操作入口见 [注册表工具指南](/tool/forensic-registry-tools/)。

必要时可在 Windows **工作副本**上临时加载 Hive。该方式需要权限并会挂入分析机注册表，优先采用独立解析器。用独立名称，结束后卸载，且不要把 `reg load` 当作保证零写入的解析方式。

```powershell
reg load HKLM\CaseSystem C:\Case\Working\SYSTEM
reg query HKLM\CaseSystem\Select
reg unload HKLM\CaseSystem

reg load HKU\CaseUser C:\Case\Working\NTUSER.DAT
reg query "HKU\CaseUser\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
reg unload HKU\CaseUser
```

## 08 补齐系统版本、安装与用户操作

以下是离线 Hive 内的候选相对路径，使用前先确认 Hive 和版本。

| 信息 | Hive / 相对路径 | 解释边界 |
| --- | --- | --- |
| 系统与登记信息 | SOFTWARE：`Microsoft\Windows NT\CurrentVersion` | ProductName、Build、版本字段合看；RegisteredOwner 不等于当前登录者 |
| 安装时间 | 同上 InstallDate / InstallTime | InstallDate 常为 Unix 秒，InstallTime 常为 FILETIME；升级可能更新，不能直接当首次安装 |
| 关机时间 | SYSTEM：对应 ControlSet 的 `Control\Windows\ShutdownTime` | 二进制 FILETIME，与 System 日志核对 |
| 环境变量 | SYSTEM：`ControlSet00n\Control\Session Manager\Environment` | 实体 ControlSet00n；不是 `CurrentControlSet001` |
| 登录界面历史用户 | SOFTWARE：`Microsoft\Windows\CurrentVersion\Authentication\LogonUI` | LastLoggedOnUser 等是界面状态，不保证采集时该用户仍登录 |
| 程序路径与卸载 | SOFTWARE：`Microsoft\Windows\CurrentVersion\App Paths`、`Uninstall` 及 Wow6432Node | 存在/安装信息不单独证明执行 |
| 运行对话框 | NTUSER.DAT：`Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU` | 区别运行框历史与 cmd/PowerShell 历史 |
| Firefox 版本候选 | SOFTWARE 的 Mozilla 产品键、程序 application.ini、Profile 版本记录 | 便携或升级后信息可能不一致 |

HKCU 对应当前用户 Hive 的视图；HKCR 是类注册的合并视图，HKCC 对应当前硬件配置。离线分析直接读取对应 Hive 和路径，不把这些逻辑根当成独立磁盘文件。

SAM 的用户名、RID 和账户字段可用于账户枚举，无法仅据一项认定最后登录者；结合 SID、ProfileList、LogonUI、会话与 4624。组名会随语言变化，管理员组应以 SID/RID 等稳定标识判断。

## 09 实战：核对 U 盘识别与文件访问

**场景与材料：** Windows 镜像中有 USBSTOR、MountedDevices 以及用户 LNK/Jump List。目标是判断某移动介质是否被识别，以及目标文件是否被访问。材料包括 SYSTEM/SOFTWARE、用户 Hive 与日志、快捷方式和文件系统记录。

### 09.1 建立设备到文件的映射

1. 从 Select 确认使用的实体 ControlSet；记录事务日志是否重放和前后哈希。
2. 保存 USBSTOR/USB 的实例、序列号候选、VID/PID 与时间字段，再查 MountedDevices 的卷标识和盘符。盘符复用时以卷信息和时期限定关系。
3. 在相应 SID 的用户记录中解析 LNK/Jump List，保留目标路径、卷信息、应用关联和记录时间；不能用分析机 HKCU 代替目标 Hive。
4. 沿目标卷查文件元数据、内容哈希与操作日志，再与登录会话、设备接入和服务日志核验。

### 09.2 示例判读

USBSTOR 中有设备实例，但没有与目标文件相符的 LNK 或操作记录：可确认设备识别痕迹，文件访问和复制尚未证实。存在指向 E: 的快捷方式也要确认当时 E: 是否为该卷。RecentDocs/MRU 顺序、键 LastWrite 与每个文件的打开时间不能互换。

输出设备实例→卷→盘符→用户 SID→文件对象的证据表，每条记录保留完整路径和时间来源。某一环缺失时明确限制，不依据一个友好名称认定设备或操作人身份。

**目录交互专项：** ShellBags 的层次、MRU、时间推导、Windows 版本差异及 ShellBags Explorer 操作集中在 [ShellBags 取证](/knowledge/forensic-shellbags/)，本页保留注册表或 U 盘的通用证据链。

## 10 RegRipper：参数、插件与注册表实操

### 10.1 先理解工具的输入与执行单元

RegRipper 是**离线 Hive 的插件式提取器**：读取某个配置单元，由 Perl 插件定位键、解码数据、输出文本或时间线。它适合快速回答“系统是什么版本”“某用户输入过哪些路径”“有哪些启动项”等明确问题，不替代任意键浏览、事务日志恢复或完整文件系统分析。

| 执行单元 | 作用 | 使用方式 |
| --- | --- | --- |
| `rip.exe` / `rip.pl` | 命令行驱动器；Kali 包的入口为 `regripper` | 指定 `-r` 输入 Hive，再选 `-p`、`-f`、`-a` 或 `-aT` |
| `rr.exe` / `rr.pl` | 图形界面，选择 Hive 与报告位置 | 3.0 自动识别 Hive 并运行适用插件，不要套用旧版必须选择 profile 的截图 |
| `plugins/*.pl` | 单个插件，通常只处理一个或几个固定痕迹 | `-p typedpaths` 对应 `plugins/typedpaths.pl`；名称不要加 `.pl` |
| `plugins/ntuser` 等无扩展名文件 | profile：一行一个插件名，按清单顺序执行 | `-f ntuser` 是选择 profile，不是输入 NTUSER 文件 |
| `Base.pm`、`File.pm`、`Key.pm` 等 | 注册表解析模块及版本相关修改 | `.pm` 不是交给 `-p` 的取证插件 |

**一个 `-r` 对应一个 Hive 文件。** 不是目录、E01、VMDK、`.reg` 文本导出或逻辑根 `HKCU`。先从镜像导出 SYSTEM/SOFTWARE/SAM、各用户 NTUSER/UsrClass 等；SID 与用户名另行映射。插件由代码实现，连 `-l` 列表操作也会加载插件代码，不向工具目录混入未检查的脚本。

以下以 **RegRipper 3.0** 的 13 项 CLI 参数及插件为主要操作基线；4.0 的差异单列。工具版本、驱动器、插件目录、插件版本号/哈希应一起记录：同样的“3.0”标签可能包含不同日期的插件，更新 `rip.pl` 不代表已编译的 `rip.exe` 同步更新。

### 10.2 Kali/Linux 准备与 Windows 对照

Kali 的包管理入口使用以下命令；安装与帮助检查不代表已经解析检材：

```bash
sudo apt install regripper
command -v regripper
dpkg-query -W regripper perl libparse-win32registry-perl
regripper -h
regripper -l > plugins.txt 2> plugins.stderr
regripper -l -c > plugins.csv 2> plugins-csv.stderr
```

Kali 包依赖 Perl 与 `Parse::Win32Registry` 对应模块。源码模式是 `perl rip.pl ...`，应在已经核对模块依赖的工具目录内运行；某些版本需要相应修改版的 Base/File/Key 模块。按实际版本配置隔离环境，保留原模块，不直接覆盖全局解析库后假定行为相同。

```bash
cd "$HOME/tools/RegRipper3.0"
perl -MParse::Win32Registry -e 'print "$Parse::Win32Registry::VERSION\n"'
perl rip.pl -h
perl rip.pl -l
```

Windows 编译版不要求单独安装 Perl。工具目录与 `plugins` 放在一起；路径包含空格时完整加引号：

```powershell
& 'C:\Tools\RegRipper3\rip.exe' -h
& 'C:\Tools\RegRipper3\rip.exe' -l
& 'C:\Tools\RegRipper3\rip.exe' -r 'C:\Case\Working\UserA\NTUSER.DAT' -p typedpaths > 'C:\Case\Reports\typedpaths.txt' 2> 'C:\Case\Reports\typedpaths.stderr'
$LASTEXITCODE
```

Windows/Linux 重定向编码和换行可能不同，尤其 Windows PowerShell 5.1 与 PowerShell 7 的输出编码。保存 Shell 版本与原始报告，检查中文、NUL、换行与时间列再导入其他工具，不因文本乱码认定数据不存在。

### 10.3 全部常用 CLI 参数：作用、例子与边界

以下短参数逐项核对 3.0 驱动器；4.0 同名参数仍要看所用构建的 `-h`。

| 参数 | 具体作用与例子 | 注意事项 |
| --- | --- | --- |
| `-r HIVE` | 指定输入：`regripper -r work/SYSTEM -p compname` | 选离线工作副本；重命名文件不改变真实 Hive 类型 |
| `-d` | 检查 Hive 是否 dirty：`regripper -r work/SYSTEM -d` | 检查头部序列一致性；不是修复、清洗、恢复或重放日志。不要省略 `-r` |
| `-g` | 启发式猜测 Hive 类型：`regripper -r work/sample.hive -g` | 结合内部嵌入文件名与特征键识别；损坏、精简、特殊 Hive 可无结果或有歧义，不是仅按文件名识别 |
| `-a` | 自动识别后运行 Hive 对应的非 TLN 插件：`regripper -r work/SOFTWARE -a` | 不是对所有用户/所有文件扫描；声明为通用 `All` 的插件不能假定自动全覆盖 |
| `-aT` | 自动识别后运行名称以 `tln` 结尾的适用插件 | 大写 `T`；没有猜到类型或没有合适插件时可能空输出；不处理 `.LOG1/.LOG2` |
| `-f PROFILE` | 运行插件清单：`regripper -r work/NTUSER.DAT -f ntuser` | profile 放于插件目录；每行写插件 basename，不写任意系统路径或 `.pl` 文件名 |
| `-p PLUGIN` | 定向解析：`regripper -r work/NTUSER.DAT -p userassist` | 单插件通常最快；驱动器不替你验证该插件是否适用该 Hive |
| `-l` | 列出插件及描述：`regripper -l` | 也会加载代码；描述只供筛选，实际键/字段以插件实现为准 |
| `-c` | 与 `-l` 合用：`regripper -l -c` | **不是注册表数据 CSV**；是 Plugin/Version/Hive/Description 清单，不能给普通解析结果加此参数就变成 CSV |
| `-s HOST` | TLN 第 3 字段 `system` 的主机标签 | 手工上下文，不是从 Hive 自动读计算机名，也不选择目标系统 |
| `-u USER` | TLN 第 4 字段 `user` 的用户标签 | 手工上下文，不选择用户、不解析 SID；设置任一标签时另一字段也会重新组装，建议二者同时给出 |
| `-uP` | 按当前插件元数据重新生成默认 profiles | **不是联网更新**；会写工具目录并改变清单，仅在工具副本上使用，执行前后保存清单/哈希 |
| `-h` | 显示帮助：`regripper -h` | 已核对 Windows `rip.exe` 也支持 `/?`；不要默认支持 GNU 风格 `--help`、`--version` |

**不要组合多个执行模式。** `-p/-f/-a/-aT` 在驱动器里不是严格互斥开关；混用可执行多条分支，输出混杂或重复。帮助、列插件、更新 profiles 等分支还可能提前退出。每次调用只解决一个目的，把 `-d/-g` 检查、解析和生成清单分别运行。

本机 3.0 的无参、`-h`、`/?` 返回帮助且 exit 0；`--help` 虽会显示帮助，同时 STDERR 出现 `Unknown option: -help`，仍可能 exit 0。单给 `-a/-aT/-g` 而没有 `-r` 也可能无输出 exit 0。因此“命令退出为 0”不是参数有效或解析成功的充分证明。

### 10.4 第一轮操作：固定输入，再定向提取

假设已经导出 Hive 与对应日志，`work/` 是工作副本，`reports/` 为当前独立报告目录。日志恢复如需执行，必须先由支持 replay 的解析器生成派生 Hive，不能把事务日志当 `-r` 输入。

```bash
mkdir -p reports
sha256sum work/SYSTEM work/SOFTWARE work/NTUSER.DAT > reports/input.sha256

regripper -r work/SYSTEM -d > reports/system-dirty.txt 2> reports/system-dirty.stderr
regripper -r work/SYSTEM -g > reports/system-type.txt 2> reports/system-type.stderr

regripper -r work/SYSTEM -p compname > reports/compname.txt 2> reports/compname.stderr
regripper -r work/SOFTWARE -p winver > reports/winver.txt 2> reports/winver.stderr
regripper -r work/NTUSER.DAT -p userassist > reports/userassist.txt 2> reports/userassist.stderr
printf 'userassist exit=%s\n' "$?"

sha256sum --check reports/input.sha256
```

每个报告同时查看 **STDOUT、STDERR、exit、预期字段、对应原键**。`Launching ...` 常是正常插件启动日志，不等于失败；`Error in ...`、缺模块、缺文件、无法读值则必须逐项处理。上面的 exit 只对应最后一次 userassist 命令，不能代替前面所有命令的状态记录。

`not found` 只能说明**此输入状态下、该插件查找的那个路径没有返回目标键**，不能推出“该用户从未执行过程序”或“此机器没有 USB”。先排查 Hive/SID、日志状态、Windows 版本、插件覆盖、ControlSet、WOW64、历史副本和删除痕迹。

### 10.5 按题目问题选插件

下表的 basename 可直接用于 `-p`；它是精选入口，不是要求把整张表在每个 Hive 上全部跑一遍。先用 `-l` 核对插件在当前目录中存在，再看 `getHive()` 和实际路径。**声明的适用 Hive 不表示所有 Windows 版本的所有布局都受支持。**

| 插件 | 输入 Hive | 主要位置与输出 | 适用考点与解释边界 |
| --- | --- | --- | --- |
| `compname` | SYSTEM | Select/Current 对应控制集；ComputerName 与 TCP/IP Hostname | 建立主机标签；不同字段可能不一致，结合日志与系统版本 |
| `timezone` | SYSTEM | 对应控制集的 Control/TimeZoneInformation，键时间及时区值 | 时区、Bias、夏令时；不把 ActiveTimeBias 固定套到历史事件 |
| `shutdown` | SYSTEM | Control/Windows/ShutdownTime，二进制时间与键时间 | 关机线索；两种时间分别解释，再与 System 日志核对 |
| `environment` | SYSTEM / NTUSER | 系统 Session Manager/Environment 或用户 Environment | PATH/TEMP 等配置，不代表每个进程实际环境 |
| `services` | SYSTEM | 当前控制集 Services；Name、Display、ImagePath、Type、Start、Group，按键时间组织 | 服务/驱动与持久化筛选；不是服务安装事件日志，重要字段回原键检查 |
| `usbstor` | SYSTEM | 当前控制集 Enum/USBStor；设备实例、描述及 Properties 时间 | 存储设备识别、接入候选；不能据此证明复制文件 |
| `usb` | SYSTEM | 当前控制集 Enum/USB；设备实例与 Properties 数据 | 不限存储介质；VID/PID、友好名称不能单独当唯一身份 |
| `usbdevices` | SYSTEM | Enum/USB 的 USB/WPD 设备信息与子键时间 | 便携设备补充；同设备在多个枚举分支的记录需关联去重 |
| `mountdev` / `mountdev2` | SYSTEM | MountedDevices；盘符、卷名称与二进制映射的不同输出实现 | 盘符到卷关联；并非全部数据都可当硬件序列号，盘符会复用 |
| `nic2` | SYSTEM | Select/Current → Services/Tcpip/Parameters/Interfaces；接口、DHCP/网络配置及相关时间 | 事件网络背景；不是完整连接/流量历史 |
| `appcompatcache` | SYSTEM | Select/Current → Control/Session Manager 的 AppCompatCache/AppCompatibility 候选；按结构解码文件条目 | ShimCache 路径与时间；支持结构按版本核对，不能单独证明执行 |
| `bam` | SYSTEM | 当前控制集 Services/bam/State/UserSettings；SID、程序路径与时间数据 | 程序活动线索；该固定路径可能漏其他版本布局，字段不等于完整执行历史 |
| `winver` | SOFTWARE | Microsoft/Windows NT/CurrentVersion 的版本、构建、登记/安装相关字段 | 系统基线；安装/升级时间和登记用户不得替代实际操作者 |
| `profilelist` | SOFTWARE | CurrentVersion/ProfileList；SID、ProfileImagePath、相关键时间；另查部分 Winlogon 数据 | Hive到用户映射；目录名不等于稳定账户身份 |
| `networkcards` | SOFTWARE | CurrentVersion/NetworkCards；网卡描述与子键LastWrite；GUID/ServiceName等标识回原键补查 | 接口关联；与 SYSTEM 的接口 GUID/配置核对 |
| `networklist` | SOFTWARE | CurrentVersion/NetworkList 的 Profiles、Signatures 等；网络名称、类型、时间与关联信息 | 网络配置/连接线索；不是网络包或完整会话日志 |
| `run` | SOFTWARE / NTUSER | 各自 Run、RunOnce、Policies/Explorer/Run、WOW64等候选；值名、数据、键时间 | 自启动筛选；会先猜 Hive，猜测不匹配也可能无结果；3/4覆盖不同 |
| `runonceex` | SOFTWARE | Microsoft/Windows/CurrentVersion/RunOnceEx 子项与 Depend | 另一路启动配置；不能认为普通 run 已必然覆盖 |
| `uninstall` | SOFTWARE / NTUSER | Uninstall及相应WOW64/用户分支；软件登记字段 | 软件名称/版本清单；安装路径与卸载命令回原键补查，便携版、残留另判 |
| `appcompatflags` | SOFTWARE / NTUSER | AppCompatFlags 的 Layers、Custom、InstalledSDB等适用分支 | 兼容性配置/辅助执行线索；声明两个Hive不表示每个路径在两者均存在 |
| `samparse` | SAM | SAM/Domains/Account/Users 及 Builtin/Aliases；账户名、RID、状态/时间、组成员 | 账户与管理员组枚举；与SOFTWARE的SID映射、4624关联，不证明某次登录权限 |
| `userassist` | NTUSER | Explorer/UserAssist 的 GUID/Count；ROT13名称，适配结构的次数/时间 | GUI程序活动；该实现区分16/72字节布局，无时间字段也要保留，不代表所有程序执行 |
| `runmru` | NTUSER | Explorer/RunMRU；值内容、MRUList与键时间 | Win+R输入历史；不是cmd/PowerShell命令历史，也不证明命令成功 |
| `typedpaths` | NTUSER | Explorer/TypedPaths；url编号与路径、键LastWrite | 地址栏输入路径；不直接证明文件读取、UNC认证或传输 |
| `typedpaths_tln` | NTUSER | 同键，只取url1并生成TLN | 与普通输出并用；不能把它当所有url的逐项访问时间 |
| `recentdocs` | NTUSER | Explorer/RecentDocs及扩展名子键；文件名、MRUListEx与键时间 | 最近对象线索；顺序不是每项独立时间，需LNK/Jump List验证 |
| `comdlg32` | NTUSER | Explorer/ComDlg32 的 LastVisited/OpenSave 的MRU/PIDL等适用子项 | 打开/保存对话框对象与目录线索；按实际实现/版本核对，不证明内容读写完成 |
| `shellbags` | UsrClass | Local Settings/Software/Microsoft/Windows/Shell/BagMRU 遍历 | 目录交互提取；该插件不是NTUSER通用入口，也不等于完整SBE解析；详见[ShellBags取证](/knowledge/forensic-shellbags/) |
| `amcache` | Amcache.hve | Root/InventoryApplicationFile、InventoryApplication及旧Root/File、Programs候选 | 文件/软件清单、路径与版本相关字段；不是SYSTEM或SOFTWARE插件，不单独断言执行 |


#### 典型定向命令

```bash
regripper -r work/SYSTEM -p usbstor > reports/usbstor.txt 2> reports/usbstor.stderr
regripper -r work/SYSTEM -p mountdev > reports/mountdev.txt 2> reports/mountdev.stderr
regripper -r work/SOFTWARE -p profilelist > reports/profilelist.txt 2> reports/profilelist.stderr
regripper -r work/NTUSER.DAT -p runmru > reports/runmru.txt 2> reports/runmru.stderr
regripper -r work/NTUSER.DAT -p recentdocs > reports/recentdocs.txt 2> reports/recentdocs.stderr
regripper -r work/NTUSER.DAT -p typedpaths > reports/typedpaths.txt 2> reports/typedpaths.stderr
regripper -r work/SAM -p samparse > reports/samparse.txt 2> reports/samparse.stderr
```

USB 问题按照 USBSTOR/USB → 卷映射 → 用户痕迹 → 文件对象比对，不只抄一个序列号。程序执行问题以 UserAssist 与 Prefetch/4688 等交叉验证，ShimCache、Amcache 不单独当作执行证明。某些 SYSTEM 插件遍历各 ControlSet，另一些硬编码某个控制集；把输出中的实际 `ControlSet00n` 与 `Select` 对照，不能把它们都归为“当时正在使用的控制集”。

### 10.6 自动运行、profile 与批量解析

自动运行适合首轮扫描；重要考点再用单插件复查：

```bash
regripper -r work/SYSTEM -a > reports/system-auto.txt 2> reports/system-auto.stderr
regripper -r work/NTUSER.DAT -f ntuser > reports/ntuser-profile.txt 2> reports/ntuser-profile.stderr
```

两者覆盖不必相同。`-a` 根据猜测类型与插件的 Hive 声明筛选；`-f` 按清单顺序运行，不为每项重新验证 Hive。一个插件失败后，后续插件仍可能继续；“最后显示 complete”不代表整个清单成功。

已核对的 3.0 插件目录有 **257 个 `.pl`、60 个 TLN 插件、9 个 profile**，这些是一个特定目录快照，不是所有3.0发行包的固定数量。默认清单也可能过期，例如该目录 `ntuser` 含缺失的 `adoberdr`、`link_click`，其他清单也有缺失项。按 `-l` 和实际文件逐项核对，不能因为 profile 名为 `ntuser` 就假定完整、最新且无错误。

在**新建的工具副本**中，可以保存精简、可复现的 profile。以下假设已在该副本工具根目录，`CASE` 是绝对案件工作目录：

```bash
printf '%s\n' userassist runmru typedpaths recentdocs > plugins/triage_ntuser
perl rip.pl -r "$CASE/work/NTUSER.DAT" -f triage_ntuser > "$CASE/reports/triage.txt" 2> "$CASE/reports/triage.stderr"
sha256sum plugins/triage_ntuser plugins/userassist.pl plugins/runmru.pl plugins/typedpaths.pl plugins/recentdocs.pl
```

`-uP` 不是下载插件；它按 `getHive()` 等元数据重建默认 profile，并影响顺序与覆盖。该3.0实现写出时跳过名称以 `tln` 结尾的插件，`All` 是独立分组，不自动混入每个 Hive。其源码还使用 Windows 式写出路径，Linux 包是否修订过需另查；更新前先保留整个 profile，更新后检查差异。自定义名称与默认名称分开，不把当前案件清单写成全局默认。

多用户批量处理的关键是**不覆盖同名 NTUSER 报告**。下列 Bash 模板在全新报告子目录内记录每次状态；SID/路径关系另外建立证据表：

```bash
mkdir -p reports
report=$(mktemp -d ./reports/run.XXXXXX)
for hive in work/SYSTEM work/SOFTWARE work/SAM work/users/*/NTUSER.DAT; do
    [ -f "$hive" ] || continue
    name="${hive#work/}"
    name="${name//\//_}"
    regripper -r "$hive" -a > "$report/$name.txt" 2> "$report/$name.stderr"
    status=$?
    printf '%s\t%s\n' "$hive" "$status" >> "$report/status.tsv"
done
```

处理报告时查看每个 STDERR 和对应内容，不只统计文件数量；猜测失败的 Hive 可改用已验证的单插件。不要将所有用户输出合并后失去 SID、Hive 哈希与日志状态。

### 10.7 TLN 时间线：字段、标签与覆盖范围

TLN 是插件使用的时间线文本格式，**不是注册表事务日志，也不是逐次访问日志**。常见五字段如下：

```text
epoch|source|system|user|description
```

| 字段 | 含义与核对 |
| --- | --- |
| `epoch` | Unix 秒；事件意义取决于插件究竟用哪个时间，不能只看排序结果 |
| `source` | 痕迹来源类别，例如 REG；`-s` 不修改此字段 |
| `system` | 主机上下文，第3字段；`-s` 写入指定标签 |
| `user` | 用户上下文，第4字段；`-u` 写入指定标签 |
| `description` | 插件形成的描述；仍须反查 Hive、键与字段 |

```bash
regripper -r work/NTUSER.DAT -p typedpaths_tln -s HOST_SAMPLE -u USER_SAMPLE > reports/typedpaths.tln 2> reports/typedpaths-tln.stderr
regripper -r work/NTUSER.DAT -aT -s HOST_SAMPLE -u USER_SAMPLE > reports/ntuser-auto.tln 2> reports/ntuser-auto-tln.stderr
```

不要把 `-s/-u` 加到普通文本报告上：驱动器会按竖线拆分并重组字段，可能损坏非 TLN 文本。标签是分析者输入的数据，先从计算机名和 SID/ProfileList 核实，不用标签反证身份。

**TLN 与普通插件未必覆盖相同条目。** 例如已核对 `typedpaths` 输出多个 url 值，但 `typedpaths_tln` **只输出 `url1`**，并使用 TypedPaths 键的 LastWrite。转换时间线时，不能把这个时间分给所有 url，更不能以“TLN 没有 url2”证明 url2 从未存在。其他 `_tln` 插件也要逐个检查，不假设它们只是普通输出换了分隔符。

合并前去除/单独保存 banner、错误和非 TLN 行；用固定五字段及整数 epoch 校验，不要把 STDERR 混入时间线。原始 TLN 保留，排序/转换后的文件作为派生件；UTC 与显示时区分开记录，空标签不等于用户未知事实。

### 10.8 如何读插件源码与输出

1. 查 **`getHive()` / `%config{hive}`**：确认适用 Hive，逗号分隔可能代表多个候选，`All` 是通用声明。
2. 查 **`getVersion()` / `%config{version}`**：通常是日期式代码版本号，**不是检材事件日期**；插件未必有 `getDate()`。
3. 查 `pluginmain` 内的 `get_subkey` / `get_value`：记录完整路径、遍历方式、ControlSet、WOW64、硬编码名称及异常处理。
4. 查二进制字段解码：`unpack`、时间转换、计数/MRU、ROT13 等是否适配当前 Windows 数据结构。
5. 查 `rptMsg` / `logMsg` 与时间来源：正文、STDERR、alerts、TLN 所用时间分别核对。
6. 回到 Hive 独立查看关键键值，保留键时间与值数据。插件将字段称为“last execution”或附 ATT&CK 标签，也不替代对实际结构和交叉证据的审查。

```bash
grep -nE 'getHive|getVersion|pluginmain|get_subkey|get_value|rptMsg|logMsg' plugins/typedpaths.pl
sed -n '1,160p' plugins/typedpaths.pl
sed -n '1,160p' plugins/typedpaths_tln.pl
```

`-l -c` 的输出是插件目录清单；驱动器直接拼接逗号时，描述中带逗号可能产生额外列，不能默认是严格转义的 RFC CSV。先看原始行，再选择读取规则。插件普通报告即便含逗号，也不自动成为同一种结构化表。

### 10.9 Windows GUI：操作与容易遗漏的文件

1. 在工具副本启动 `rr.exe`；CLI 的参数表不适用于 GUI 程序。
2. **Hive File** 选择已经导出的工作 Hive，而不是运行中系统的逻辑根。
3. **Report File** 选择本轮独立的报告 `.txt` 路径；它是报告文件，不只是一个目录。输出目录预先创建，每个 Hive/用户使用不同名称。
4. 执行 **Rip!**，观察界面日志与结束提示；随后分别打开报告和同基名 `.log`，核对启动插件、错误与实际结果。
5. 3.0 GUI 自动选适用插件，不把旧 profile 下拉框当必经步骤；定向、TLN 或自定义清单优先用 CLI。

GUI 的报告及对应日志采用**追加**方式。同一路径重复运行可能混入旧输出或多个用户；每轮选择全新文件名，保留旧文件，不只看最后一行。导出文件存在、界面提示完成，都不证明所有插件成功。

本轮 GUI 步骤经过实现核对，**未运行 GUI**；不得把界面使用说明当作真实检材实测结果。

### 10.10 3.0 与 4.0 的差异怎样处理

| 差异 | 实用处理 |
| --- | --- |
| 时间格式、分析提示、部分 ATT&CK 映射 | 标签和提示是辅助分析，不增加证据强度；保存实际插件版本和原始输出 |
| 增加/修改插件 | 3.0、4.0 同名插件不一定查询相同路径或输出同样字段；先比较 `-l` 与源码 |
| `run` 的覆盖变化 | 已核对3.0会查看 StartupApproved，而4.0同名实现没有这部分；不要只按工具“大版本更高”判断覆盖更全 |
| `usbstor` 的标签变化 | 两版某些属性时间的输出名称不同；依据实际 Properties 编号/FILETIME 与结构解释，不仅抄列标题 |
| Yara 整合 | 是 `run_yara` 等插件调用外部 Yara 的能力，不是新增 `-y` 通用参数；需要匹配的可执行文件与规则文件，核对插件路径/实际调用 |
| 事务日志 | **3.0/4.0 都不自动重放事务日志**；`-d` 和 `-aT` 都不能代替恢复 |

本机已验证的是3.0编译 CLI；4.0差异属于源码核验，未执行4.0、Yara或真实案件恢复。Yara匹配只是规则命中，不单独证明恶意、持久化或执行。规则、插件和外部可执行工具都纳入版本记录。

### 10.11 自建实测：同一 Hive 的普通、TLN 和空结果

**材料与目的：** 纯自建的 8192 字节 regf Hive，不含真实用户数据，也不是比赛检材。包含 TypedPaths 的 `url1=E:\Lab\Reports`、`url2=\\fileserver\Lab`，该键 LastWrite 为 `2024-01-01 00:00:00Z`；另建一个缺少 TypedPaths 键的 Hive。已用本机3.0 `rip.exe` 实际解析，并比对输入前后 SHA-256，一致。

| 执行 | 观察到的实际结果 | 正确结论 |
| --- | --- | --- |
| `-p typedpaths`，键存在 | 报告输出两个 url 值与 LastWrite；STDERR 为正常 `Launching typedpaths ...`；exit 0 | 可提取地址栏路径值；不能给每项赋独立输入时刻 |
| `-p typedpaths_tln -s HOST_SAMPLE -u USER_SAMPLE` | 只输出下面一条 TLN；exit 0 | 插件只取 url1 的结果，不是丢失了 url2 |
| `-p typedpaths`，键缺失 | 报告包含 `TypedPaths not found.`；仍 exit 0 | 插件运行完成但该键不存在，不是全局无活动 |
| `-d`，相等头部序列 | `Hive is not dirty.`；exit 0 | 此项头部检查通过；不表示所有日志/历史状态已完整覆盖 |
| `-g`，有效但特征不足的最小 Hive | 只输出换行；exit 0 | 猜测规则未识别；不能推断文件必然损坏 |

```text
1704067200|REG|HOST_SAMPLE|USER_SAMPLE|TypedPaths - E:\Lab\Reports
```

实际观察与模板区分：上述测试只验证插件读取、自建路径、TLN标签和空结果；没有执行用户行为重放，不能从自建字段反推出真的有人在该时访问了文件。Hive 文件类型、键存在、工具状态和行为结论是不同层次。

### 10.12 考点、排错与最小交付

| 现象或考点 | 先处理什么 | 不应直接下的结论 |
| --- | --- | --- |
| 提示 `Can't locate ...pm` | Perl/解析模块路径与工具版本，隔离环境重验 | 检材损坏 |
| 插件 `.pl` not found | basename、文件是否存在、工具副本目录、profile过期 | 目标痕迹不存在 |
| `Error in ...` 后仍完成 | STDOUT/STDERR、具体失败插件、继续运行情况 | 全部成功 |
| 自动报告为空 | `-r`、猜测类型、`getHive`匹配、适用插件，再单插件查实际键 | 用户没有活动 |
| 键 not found | 用户Hive、路径、日志状态、版本/ControlSet/WOW64、历史副本 | 从未使用/从未插入 |
| 只有键 LastWrite | 区分键更新与值数据时间，回到实际二进制字段 | 每个文件的打开时间 |
| 看到 URL/UNC/命令字符串 | LNK/Jump List、网络/进程/文件证据交叉核对 | 已连接成功、已执行或已外传 |
| 报告用户名来自 `-u` | SID、ProfileList、Hive采集关系 | 工具自动确认了操作者 |
| TLN 条目少于普通报告 | 源码提取范围及时间来源 | 缺少的普通记录被删除了 |
| `-uP` 或GUI重复运行后结果变化 | 工具清单/profile变化及报告追加 | 检材必然发生变化 |

交付至少包括：`原始与派生Hive哈希 / 是否重放日志 / 用户SID与Hive位置 / 实体ControlSet / 工具及插件版本/哈希 / 完整命令或profile内容 / STDOUT与STDERR / exit / 原键与时间来源 / 独立解析器复核 / 行为结论及限制`。

**首轮顺序：固定副本与日志状态 → 核对帮助/插件清单 → `-d/-g` 分别检查 → 问题对应单插件 → 自动或精简profile补扫 → 原键复查与多证据交叉验证。** RegRipper的优势是定向、可重复、快速提取；它的插件覆盖、日志状态和结论边界也必须同报告一起交付。


第 03.3 节已经指出接口里有网关线索。抄无线网卡时，先确认 `{GUID}` 属于无线接口，再读 `DefaultGateway` 或 `DhcpDefaultGateway`，不要把接口自己的 IPv4 填进去。 `MountPoints2` 的键名形如 `##<主机>#<共享名>` 时，`##` 表示 UNC 的两个反斜杠，第一段是当时映射的主机。
