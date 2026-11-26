---
title: "跨平台系统目录与关键文件"
summary: "按 Linux、Windows、Android 和应用层检索目录、日志及证据落点。"
module: "Forensics"
track: "综合取证"
topic: "工具与路径"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

**阅读范围与材料约定**

本页是跨平台证据路径索引，用来回答某类系统中的文件、日志和痕迹通常位于何处、能提取什么。它不依赖某场比赛或某台机器的固定路径；实际取证仍须在检材上核对。

本页串联 Linux、Windows、Android 的系统目录、用户痕迹与应用数据位置，结合 FHS、注册表配置单元和事件日志建立可复用的翻找路线。位置是定位线索，只有确认文件属于哪个设备、用户、应用实例与时间范围后，才能用于结论。需要按具体分析任务选择路径时，查看[取证任务与证据路径索引](/knowledge/forensic-method-index/)；iOS 内容见[iOS 备份与系统痕迹分析](/knowledge/forensic-ios-backup/)。

**阅读顺序：** Linux（02–03）→ Windows（04–06）→ Android（07）→ 应用层（08）→ 按检材翻找（09）→ 关联模式、易混辨析、工具与顺序（10–12）。

## 01 用途与读法

- **按证据对象查位置**：从系统身份、用户账户与挂载关系进入，再查业务配置、数据与日志；过程示例见[Linux 主机分析](/knowledge/fic-case-03/)、[Web 应用与 Git 痕迹](/knowledge/fic-case-04/)、[数据库分析](/knowledge/fic-case-05/)、[移动应用](/knowledge/fic-case-06/)和[网络关联](/knowledge/fic-case-10/)。
- **三层读法**：
  1. **系统层**（02–07）：操作系统自带的目录与文件——结构、痕迹、日志；
  2. **应用层**（08）：第三方软件把数据放在哪——浏览器、IM、邮件、云盘、钱包、远程工具；
  3. **方法层**（09–12）：拿到某类检材先翻哪、怎么跨层串联、哪些路径容易混、用什么工具。
- **通用性约定**：
  - 路径取**主流默认值**（Debian/Ubuntu 系、Windows 10/11、Android 10+）；实检可能因发行版差异、自定义安装路径、多用户偏移而不同；
  - 标 **⚠** 者为"随版本变化较大，使用前先确认实际存在性"；
  - 时间戳语义（`mtime` / `atime` / `btime`）与文件系统相关，跨文件系统比较前先确认。
- **拿到检材的第一动作**：先确认对象身份和只读访问，再读取目录。先按 09 的"按检材类型清单"扫一遍目录树，建立"这台机器上有什么"的整体认识，再决定往哪一层深挖。

## 02 Linux 目录全景（FHS 视角）

| 目录 | 作用 | 关键内容 | 通用取证要点 |
|---|---|---|---|
| `/` | 根目录 | 一切路径起点 | — |
| `/bin`、`/sbin` | 基础命令（新版多软链至 `/usr/bin`） | `ls`、`mount`、`ss`、`ip` | 判断发行版与工具链版本 |
| `/lib`、`/lib64` | 基础共享库、内核模块软链 | `modules/<内核版本>/` | 内核模块决定**能否识别某文件系统** |
| `/usr` | 只读程序、库与共享数据 | `bin/`、`sbin/`、`lib/`、`share/`、**`lib/os-release`** | 发行版标识的候选位置；核对 `/etc/os-release` 的存在性与软链 |
| `/usr/local` | 管理员手工安装 | 自编译程序 | 非包管理器部署的痕迹 |
| `/etc` | **系统与服务配置**（结构层核心） | 见 02.1 | 回答"是什么、指向谁、监听什么" |
| `/var` | 可变数据（日志、缓存、服务状态） | 见 02.2 | 回答"发生了什么、何时发生" |
| `/home/<u>` | 普通用户家目录 | 见 03 | 用户行为痕迹 |
| `/root` | root 家目录 | 同 03 | 管理员行为；**该路径可能被设为独立子卷/快照** |
| `/opt` | 第三方或商业软件 | 自定义应用目录 | 非常规部署 |
| `/srv` | 服务数据（FHS 约定） | Web / 文件服务数据 | 运维常在此放站点 |
| `/tmp`、`/var/tmp` | 临时目录（**易失，先取**） | 程序临时文件、自解压残留、崩溃转储 | 运行痕迹；重启或清理即失 |
| `/boot` | 内核与引导 | `vmlinuz-*`、`initrd*`、`grub/`、`config-*` | 内核版本（**≠ 发行版版本**） |
| `/dev` | 设备节点 | `sd*`、`mapper/<vg>-<lv>`、`nbd*`、`loop*` | LVM / 镜像挂载类取证的入口 |
| `/proc` | 内核与进程运行时视图（procfs） | `version`、`filesystems`、`mounts`、`net/tcp`、`<pid>/cmdline`、`environ`、`fd/` | 在目标运行现场或已采集运行视图中读取；内存镜像需相应解析器，普通离线磁盘不会保存完整 procfs 状态 |
| `/sys` | 设备与内核对象 | `block/`、`class/net/`、`fs/` | 硬件、网卡、已注册文件系统 |
| `/run`、`/var/run` | 运行时状态（tmpfs） | `*.pid`、`utmp`、`nginx.pid`、`systemd/` | 运行中的服务证据；重启即失 |
| `/media`、`/mnt` | 外部介质挂载点 | 自动 / 手动挂载点 | 外接 U 盘、移动硬盘证据 |
| `/lost+found` | 孤儿文件恢复区（ext 系） | 编号文件 | 可能含文件系统检查重新连接的孤儿文件；不能据此认定所有删除文件都在这里 |
| `/snap`（Ubuntu） | Snap 包目录 | 各 snap 独立子目录 | 沙盒化安装的软件 |
| `/selinux`、`/etc/apparmor.d` | 强制访问控制 | 策略文件 | — |
| `/data`、`/db`、`/media/<name>` 等 | **自定义挂载点**（非 FHS 标准） | 业务数据、数据库、存储池 | 非常规部署；先看 `/etc/fstab` 确认挂载关系 |

### 02.1 `/etc` 重点条目

| 类别 | 路径 | 说明 |
|---|---|---|
| 系统标识 | `os-release`、`lsb-release`、`issue`、`machine-id` | 发行版、版本、机器标识；镜像克隆可重复，不单独证明唯一设备 |
| 挂载与加密卷 | `fstab`、`crypttab`、`mtab` | UUID 与文件系统；加密卷映射关系 |
| 主机与解析 | `hostname`、`hosts`、`resolv.conf`、`nsswitch.conf`、`hosts.allow`、`hosts.deny` | 主机名与 DNS |
| 账户与提权 | `passwd`、`shadow`、`group`、`gshadow`、`sudoers`、`sudoers.d/`、`login.defs`、`pam.d/` | 账户、口令哈希（`$6$`=SHA-512、`$y$`=yescrypt）、提权 |
| 时区与区域 | `localtime`（软链）、`timezone`、`locale.conf` | **时间线解读的前提** |
| 环境变量 | `environment`、`profile`、`profile.d/`、`bash.bashrc`、`skel/` | 常藏代理设置；`skel/` 是新建用户模板 |
| Web 与数据库 | `nginx/`、`apache2/`、`httpd/`、`php/`、`mysql/`、`postgresql/`、`redis/`、`mongod.conf` | 应用配置（配置与实例需一起核对） |
| 服务管理 | `systemd/system/`、`systemd/system-preset/`、`init.d/`、`rc.local`、`xinetd.d/` | 自启与持久化（结合启动日志验证） |
| 定时任务 | `crontab`、`cron.d/`、`cron.{hourly,daily,weekly,monthly}/`、`anacrontab`、`at.deny` | 定时行为 |
| 日志策略 | `rsyslog.conf`、`rsyslog.d/`、`syslog-ng/`、`logrotate.conf`、`logrotate.d/`、`journald.conf`（同时核对 `/etc/systemd/journald.conf`） | 日志去向与轮转规则 |
| 网络与防火墙 | `network/interfaces`、`NetworkManager/`、`netplan/`、`nftables.conf`、`iptables/` | 网络与访问控制 |
| 包管理 | `apt/sources.list`、`apt/sources.list.d/`、`yum.repos.d/`、`dnf/`、`pacman.conf` | 软件源与安装来源 |
| 存储管理 | `lvm/backup/`、`lvm/archive/`、`mdadm.conf`、`zfs/` | LVM / RAID / ZFS 元数据（与成员设备及挂载关系核对） |
| 容器 | `docker/`、`containerd/`、`kubernetes/` | 容器运行时配置；沿 Docker 专题核对实际数据根、存储后端与实例 |
| 证书与密钥 | `ssl/`、`pki/`、`letsencrypt/`、`ca-certificates/` | 证书与私钥 |
| 远程访问 | `ssh/`（`sshd_config`、`ssh_host_*_key`）；`authorized_keys` 通常在各用户 `.ssh/` 或由配置另指定 | 远程管理痕迹、横向移动线索 |
| 其他 | `motd`、`security/`、`alternatives/`、`xdg/` | — |

### 02.2 `/var` 重点条目

| 路径 | 内容 | 取证价值 |
|---|---|---|
| `lib/` | 服务的**状态数据** | 判断"服务是否真的初始化过"（不把残留目录当运行证明） |
| `lib/docker/`、`lib/containerd/` | 容器与镜像数据根 | 镜像创建时间、容器配置 |
| `lib/lxc/`、`lib/libvirt/` | 容器与虚机定义 | `lxc/<name>/config` 是纯文本 |
| `lib/mysql/`、`lib/postgresql/<ver>/`、`lib/redis/` | 数据库数据目录 | 服务数据是否初始化过；目录残留需与包记录、配置及日志核对 |
| `lib/systemd/`、`lib/NetworkManager/` | 系统与网络状态 | 连接历史 |
| `log/` | 系统与应用日志 | **时间线主轴** |
| `log/journal/` | systemd 二进制日志 | 需 `journalctl --file` 解析 |
| `log/wtmp`、`btmp`、`lastlog`、`faillog` | 登录记录（二进制格式） | 用 `last` 读取 wtmp、`lastb` 读取 btmp、`utmpdump` 解析适用的 utmp/wtmp 格式；lastlog/faillog 使用各自格式解析器，不能统一套用 |
| `spool/cron/` | 用户级 cron 的**落地文件** | `crontab -l` 的实体，离线可直读 |
| `spool/mail/`、`spool/abrt/`、`spool/cups/` | 邮件、崩溃报告、打印 | 辅助证据 |
| `www/` | 网站根目录（约定） | CMS 源码（沿站点配置定位） |
| `crash/`、`lib/systemd/coredump/` | 崩溃转储 | 内存残留 |
| `backups/` | 配置备份（Debian 系） | 历史配置版本 |
| `cache/` | 应用缓存 | 缓存数据与缩略图 |

## 03 Linux 用户痕迹文件清单（家目录）

| 文件 / 目录 | 内容 | 取证价值 |
|---|---|---|
| `.bash_history`、`.zsh_history`、`.sh_history` | 命令历史（通常不带完整时间戳；Bash 可有 `#<epoch>` 条目，zsh 扩展历史也可记录时间） | 环境搭建与操作过程（结合启动日志验证） |
| `.python_history`、`.mysql_history`、`.psql_history`、`.rediscli_history`、`.node_repl_history`、`.sqlite_history` | 各交互式工具的历史 | 数据库操作、脚本调试痕迹 |
| `.viminfo`、`.vim/` | 编辑记录 | **含最近打开文件的标记** |
| `.lesshst`、`.wget-hsts`、`.curl_history`（仅在包装器或环境实际生成时） | 查看与下载痕迹 | 访问过的站点 |
| `.ssh/` | `known_hosts`、`authorized_keys`、`id_*`、`config` | **连接过 / 被连接过的主机与密钥** |
| `.gnupg/` | 密钥环、`random_seed` | 加密与签名 |
| `.config/` | 现代应用配置 | 代理（Clash/Mihomo、v2ray/xray）、ngrok、`autostart/`、编辑器、浏览器 |
| `.local/share/` | 应用数据 | `recently-used.xbel`（**最近使用文件**）、`Trash/` / `.Trash/`（回收站）、`Keyrings/`（大小写须实检，常见为 `keyrings/`） |
| `.cache/` | 应用缓存 | 缩略图、会话缓存 |
| `.mozilla/`、`.thunderbird/`、`.config/google-chrome/`、`.config/chromium/` | 浏览器与邮件客户端 | 落点与关键文件见 **08.1 / 08.3** |
| `.gitconfig`、`.git-credentials`、`.npmrc`、`.pypirc`、`.docker/config.json`、`.aws/credentials`、`.kube/config`、`.my.cnf`、`.pgpass` | **开发与运维凭据文件** | 明文凭据（高危泄露点）；逐类落点见 **08.6** |
| `.bashrc`、`.profile`、`.bash_profile`、`.bash_logout` | 用户级环境 | 别名与启动命令（**可能被植入后门**） |
| `.Xauthority`、`.ICEauthority` | 图形会话凭据 | — |
| `.sudo_as_admin_successful` | sudo 使用标记 | 提权痕迹 |

## 04 Windows 目录全景

| 目录 | 作用 | 关键内容 | 通用取证要点 |
|---|---|---|---|
| `C:\` | 系统盘根 | `pagefile.sys`、`hiberfil.sys`、`swapfile.sys`、`$MFT`、`$LogFile`、`$UsnJrnl`、`$Boot`、`$Bitmap`、`$Extend\`（`$ObjId` / `$Quota` / `$Reparse`） | 内存残留 + NTFS 元数据（删除与改名痕迹） |
| `Windows\System32\config` | **注册表 hive 存放地** | `SAM`、`SYSTEM`、`SOFTWARE`、`SECURITY`、`DEFAULT`、`BBI`、`DRIVERS`、`COMPONENTS`、`RegBack\`、`*.LOG1/LOG2` | **结构层核心**，见 05 |
| `Windows\System32\winevt\Logs` | 事件日志 | `Security.evtx`、`System.evtx`、`Application.evtx`、PowerShell、Sysmon 等 | **时间线主轴**，见 05.4 |
| `Windows\System32\Tasks` | 计划任务（现代任务为 XML 内容，文件常无扩展名） | `*.xml` 导出件；遗留 `At*.job` 另查 `Windows\Tasks` | 定时行为；比注册表更易读 |
| `Windows\Prefetch` | 预读取 | `*.pf` | 运行计数与留存的运行时间集合 ⚠；字段随格式版本变化，缺失可因策略、清理或系统配置，不能保证包含真正首次运行 |
| `Windows\AppCompat\Programs` | 程序兼容性 | `Amcache.hve`、`RecentFileCache.bcf` | 程序与安装/库存线索、路径与适用格式的哈希；单独出现条目不证明执行 |
| `Windows\System32\sru` | 系统资源使用 | `SRUDB.dat`（ESEDB 格式） | 应用与网络使用统计（Win8+） |
| `Windows\System32\wbem\Repository` | WMI 库 | `OBJECTS.DATA`、`INDEX.BTR` | **WMI 持久化后门** |
| `Windows\INF` | 驱动安装日志 | `setupapi.dev.log`、`setupapi.setup.log` | **USB 等设备插拔历史**（含 VID/PID 与序列号） |
| `Windows\System32\LogFiles` | IIS 与组件日志 | `W3SVC*`、`WMI\RtBackup\*.etl` | Web 访问、WMI 活动 ⚠ |
| `Windows\Logs` | 组件安装日志 | `CBS\CBS.log`、`DISM\`、`WindowsUpdate\` | 补丁与组件变更 |
| `Windows\Temp`、`Windows\SoftwareDistribution\Download` | 临时与更新缓存 | 安装包残留 | 软件来源与更新时间 |
| `Windows\Minidump`、`MEMORY.DMP` | 崩溃转储 | `*.dmp` | 按转储类型和页覆盖分析内核或进程；小型/内核转储不能预设包含 LSASS 用户态页，格式与恢复见[内存对象恢复](/knowledge/forensic-memory-recovery/) |
| `Windows\WinSxS` | 组件存储 | 各组件的多版本副本 | 组件级历史 |
| `Windows\CSC` | 离线文件缓存 | 网络共享文件的本地副本 | 访问过的共享目录 |
| `Windows\Panther` | 安装日志 | `setupact.log`、`setuperr.log` | 装机时间与过程 |
| `Windows\System32\drivers\etc\hosts` | 主机名映射 | — | 常被恶意软件篡改（需与解析与连接痕迹交叉） |
| `ProgramData`（隐藏） | 全局应用数据 | `Microsoft\Windows\Start Menu\Programs\StartUp`（**全局自启**）、`Microsoft\Windows Defender\Scans\`、`Package Cache\` | 自启、杀软扫描记录 |
| `Program Files`、`Program Files (x86)` | 已安装程序 | 程序目录 | 软件清点 |
| `Users\<u>` | 用户目录 | 见 05.3 | 用户行为全量 |
| `Users\Public`、`Users\Default` | 公共目录、新用户模板 | 共享文件、默认配置 | — |
| `$Recycle.Bin\<SID>` | 回收站 | `$I*`（**原路径 + 删除时间**）、`$R*`（内容） | 删除行为还原 |
| `System Volume Information` | 系统保护 | VSS 卷影副本、`$MFT` 早期副本 | 历史版本恢复（**对应 btrfs 快照思路**） |
| `Recovery`、`$WinREAgent` | 恢复环境 | WinRE 映像 | — |
| `PerfLogs`、`Windows.old` | 性能日志、升级前系统 | — | 升级前状态 |
| `Documents and Settings` | 遗留软链 | 指向 `C:\Users` | 识别软链，勿重复统计 |

## 05 Windows 注册表与痕迹文件

### 05.1 注册表 hive 文件与挂载点

| 文件 | 挂载为 | 主要回答 |
|---|---|---|
| `System32\config\SYSTEM` | `HKLM\SYSTEM` | 计算机名、时区、服务、驱动、USB 历史、网络配置、ShimCache |
| `System32\config\SOFTWARE` | `HKLM\SOFTWARE` | 已装软件、全局自启、Windows 版本、网络历史 |
| `System32\config\SAM` | `HKLM\SAM` | 本地账户与口令哈希（需从 SYSTEM 取 boot key 解密） |
| `System32\config\SECURITY` | `HKLM\SECURITY` | 安全策略、缓存域凭据（需 SYSTEM） |
| `System32\config\DEFAULT` | `HKU\.DEFAULT` | 系统账户默认配置 |
| `Users\<u>\NTUSER.DAT` | `HKU\<SID>` | **用户级**：自启、最近文档、输入痕迹、ShellBags |
| `Users\<u>\AppData\Local\Microsoft\Windows\UsrClass.dat` | `HKU\<SID>_Classes` | ShellBags、文件与扩展名关联 |
| `Windows\AppCompat\Programs\Amcache.hve` | 独立解析 | 文件或程序库存、路径、适用格式的 SHA1 与时间字段；字段语义随版本变化，不直接认定首次执行 |
| `Windows\System32\sru\SRUDB.dat` | ESEDB | 应用与网络使用统计 |
| `System32\config\RegBack\*` | — | 注册表自动备份 ⚠（Win10 1803 后默认不再更新） |

### 05.2 高频注册表键（通用）

| 要找什么 | 键路径 |
|---|---|
| Windows 版本与安装时间 | `SOFTWARE\Microsoft\Windows NT\CurrentVersion` |
| 计算机名 | `SYSTEM\ControlSet001\Control\ComputerName\ComputerName` |
| 时区 | `SYSTEM\ControlSet001\Control\TimeZoneInformation` |
| 全局自启 | `SOFTWARE\Microsoft\Windows\CurrentVersion\Run`（含 `RunOnce`、`Wow6432Node` 对应项） |
| 用户级自启 | `NTUSER.DAT\...\CurrentVersion\Run`、`RunOnce` |
| 服务与驱动 | `SYSTEM\ControlSet00x\Services\<name>`（`ImagePath`、`Start`、`ObjectName`） |
| USB 存储历史 | `SYSTEM\...\Enum\USBSTOR`、`Enum\USB`、`MountedDevices` |
| 执行痕迹缓存 | `SYSTEM\...\Control\Session Manager\AppCompatCache`（ShimCache） |
| 已装软件 | `SOFTWARE\...\Uninstall\*`、`App Paths` |
| 网络历史 | `SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles`（历史 SSID、网关） |
| 防火墙与策略 | `SOFTWARE\Policies\`、`SYSTEM\...\FirewallPolicy` |
| 远程桌面历史 | `NTUSER.DAT\...\Terminal Server Client\Servers`、`Default` |
| 映射网络盘 | `NTUSER.DAT\...\MountPoints2`、`Map Network Drive MRU` |
| 最近文档 | `NTUSER.DAT\...\Explorer\RecentDocs` |
| 程序使用次数与时间 | `NTUSER.DAT\...\Explorer\UserAssist\<GUID>\Count`（**ROT13 编码**） |
| 文件对话框痕迹 | `NTUSER.DAT\...\ComDlg32\OpenSavePidlMRU`、`LastVisitedPidlMRU`、`CIDSizeMRU` |
| 路径输入痕迹 | `NTUSER.DAT\...\Explorer\TypedPaths` |
| 搜索历史 | `NTUSER.DAT\...\Explorer\WordWheelQuery` |
| 运行框命令 | `NTUSER.DAT\...\Explorer\RunMRU` |
| 目录浏览痕迹 | `NTUSER.DAT\...\Shell\BagMRU`、`Bags`；`UsrClass.dat\Local Settings\Software\Microsoft\Windows\Shell\` |
| WMI 持久化 | `SOFTWARE\Microsoft\Wbem\`（需配合 `OBJECTS.DATA` 解析） |

### 05.3 用户目录痕迹文件

| 文件 / 目录 | 内容 |
|---|---|
| `NTUSER.DAT`、`UsrClass.dat`（及 `.LOG1` / `.LOG2`） | 用户注册表 hive 与事务日志 |
| `AppData\Roaming\Microsoft\Windows\Recent\*.lnk` | 最近打开的文件 / 目录快捷方式（**含原路径与卷序列号**） |
| `...\Recent\AutomaticDestinations\*.automaticDestinations-ms` | **跳转列表**：按程序统计的最常用文件 |
| `...\Recent\CustomDestinations\*.customDestinations-ms` | 自定义跳转列表 |
| `AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` | **PowerShell 命令历史** |
| `AppData\Roaming\Microsoft\Windows\PowerShell\Transcripts\` | PowerShell 转录（若启用） |
| `AppData\Local\Microsoft\Windows\Explorer\thumbcache_*.db`、`iconcache_*.db` | 缩略图与图标缓存（**可能还原已删除图片**） |
| `AppData\Local\Microsoft\Windows\WebCache\WebCacheV01.dat` | IE / 旧版 Edge 的历史、缓存、Cookie 索引；Chromium Edge 使用自己的用户数据目录 |
| `AppData\Local\Microsoft\Windows\INetCache\`、`INetCookies\` | IE 缓存与 Cookie |
| `AppData\Local\ConnectedDevicesPlatform\` | **跨设备活动与连接相关缓存（CDP，Win10+）** |
| `AppData\Local\Packages\<pkg>\` | UWP / 商店应用数据 |
| `AppData\Local\CrashDumps\` | 应用崩溃转储 |
| `AppData\Local\Temp\` | 临时文件（安装包、解压残留） |
| `AppData\Roaming\<app>\`、`AppData\Local\<app>\` | 第三方应用配置与数据（见应用层目录表） |
| `Desktop`、`Documents`、`Downloads`、`Pictures`、`Videos`、`Music`、`Favorites`、`Links`、`Contacts`、`Searches`、`OneDrive` | 用户文件、收藏与同步目录 |

### 05.4 事件日志关键 ID（通用速查）

| 日志 | 事件 ID | 含义 |
|---|---|---|
| Security | 4624 / 4625 | 登录成功 / 失败（含登录类型与来源 IP） |
| Security | 4634 / 4647 | 注销 |
| Security | 4648 | 使用显式凭据登录（runas） |
| Security | 4672 | 分配特殊特权 |
| Security | 4688 | 进程创建（需启用审核策略） |
| Security | 4720 / 4726 / 4732 / 4756 | 创建 / 删除用户、加入组 |
| Security | 1102 | **审核日志被清空** |
| System | 6005 / 6006 / 104 | 日志服务启动 / 停止 / 日志清空 |
| System | 7045 | 服务安装 |
| System | 7031 / 7034 | 服务异常终止 |
| System | 20001 / 20003 / 219 | UserPnp 20001/20003 与设备安装过程相关；Kernel-PnP 219 为驱动加载失败线索，不能仅凭 ID 认定成功安装或插拔 |
| Application | 1000 / 1001 | 应用崩溃 / 错误报告 |
| PowerShell | 400 / 403 / 4103 / 4104 | 400/403 在经典 Windows PowerShell 日志记录引擎启停；4103/4104 在 Operational 频道记录模块/脚本块（需相应策略） |
| RDP | 21 / 22 / 25 / 1149 | LocalSessionManager 21 为会话登录、22 为 Shell 启动、25 为重连；断开查 24；RemoteConnectionManager 1149 为认证相关事件，结合频道与字段核对 |
| Sysmon | 1 / 3 / 7 / 11 / 12–14 / 22 | 进程、网络、镜像加载、文件创建、注册表、DNS |

## 06 双平台对照（同一件事的两处落点）

| 要取什么 | Linux | Windows |
|---|---|---|
| 系统版本 | `/etc/os-release` | `SOFTWARE\Microsoft\Windows NT\CurrentVersion` |
| 主机名 | `/etc/hostname` | `SYSTEM\ControlSet001\Control\ComputerName` |
| 时区 | `/etc/localtime`（软链） | `SYSTEM\...\TimeZoneInformation` |
| 计划任务 | `/etc/crontab`、`/etc/cron.d/`、systemd timer | `System32\Tasks` + `SOFTWARE\...\Schedule` |
| 自启项 | systemd unit、`~/.config/autostart/` | `Run` 键（HKLM / HKCU）、`StartUp` 文件夹、服务 |
| 命令历史 | `~/.bash_history` | `ConsoleHost_history.txt` |
| 程序执行痕迹 | `~/.bash_history`、进程审计 | `Prefetch`、`Amcache`、`UserAssist` |
| 回收站 | `~/.local/share/Trash/` | `$Recycle.Bin` |
| 最近文件 | `~/.local/share/recently-used.xbel` | `Recent\*.lnk`、跳转列表 |
| 图形会话与输入线索 | `~/.Xauthority` 是 X 会话认证文件；输入法配置需单独解析 | `NTUSER.DAT` 相应键、输入法词库；不凭这些位置直接还原剪贴板内容 |
| 浏览器数据 | `~/.config/google-chrome/`、`~/.mozilla/` | `AppData\...\User Data\` |
| 应用配置与密钥 | `~/.config/<app>/`、`~/.local/share/<app>/` | `AppData\Roaming\<app>\`、`AppData\Local\<app>\` |
| 网络配置 | `/etc/resolv.conf`、`/etc/hosts`、NetworkManager | `NetworkList`、`netsh` 导出 |
| 日志 | `/var/log/*` | `winevt\Logs\*.evtx` |
| 账户 | `/etc/passwd`、`/etc/shadow` | `SAM` |
| 文件系统元数据 | btrfs 子卷 / 快照、`/etc/fstab` | `$MFT`、`$UsnJrnl`、VSS 卷影 |
| 内存残留 | `/proc/kcore`（受限）、swap 分区 | `hiberfil.sys`、`pagefile.sys`、`.dmp` |
| 挂载关系 | `/etc/fstab`、`/proc/mounts` | `MountedDevices`、`HKLM\SYSTEM\MountedDevices` |

## 07 Android 目录全景

应用沙盒的 `databases/`、`shared_prefs/`、`files/` 与 SQLCipher、APK 分析见[Android 应用数据定位](/knowledge/forensic-android-storage/)和[移动应用证据](/knowledge/forensic-mobile-apps/)。这里按系统层目录建立设备与用户范围。

| 路径 | 内容 | 取证要点 |
|---|---|---|
| `/data/app/`、`/data/app-private/`（遗留布局） | 已安装 APK | 应用版本与安装包本体 |
| `/data/data/<pkg>/`、`/data/user/0/<pkg>/` | 应用沙盒；`/data/data` 通常为用户 0 别名，其他用户需查 `/data/user/<userId>/` | 数据库、偏好、文件 |
| `/data/user_de/0/<pkg>/` | 设备加密存储的应用数据（Android 7+） | 部分应用数据分两处存放 |
| `/data/system/` | 系统与包管理状态（按用户及版本核对布局） | `packages.xml` / `packages.list`（字段分工不同：前者含包管理元数据，后者偏向 UID、路径等清单；权限、安装时间与签名需按实际字段核对）、`usagestats/`（使用时长与最后使用）、`accounts.db`、`sync/`、`tasks/`、`notification_log.db`、`appops.xml`、`device_policies.xml`、`netpolicy.xml`、`dropbox/` |
| `/data/misc/` | 杂项系统数据 | `keystore/`（密钥库）、`wifi/`（`WifiConfigStore.xml`：**历史 SSID 与口令**）、`vpn/`、`bluetooth/`、`user/` |
| `/data/tombstones/`、`/data/anr/` | 崩溃与无响应日志 | 异常行为证据 |
| `/data/local/tmp/` | 临时目录（部分机型可写） | 工具与脚本残留 |
| `/data/property/` | 持久化属性 | `persist.*` 配置 |
| `/data/adb/` | 某些 root 方案（如 Magisk）的管理数据 | 核对模块与服务配置；目录名中的 adb 不能直接证明使用 ADB 调试 |
| `/storage/emulated/0/`（`/sdcard`） | 内部共享存储；现代 Android 的分区存储和授权会限制访问，`Android/data/` 不保证可直接读取 | `Android/data/<pkg>/`（应用外部数据）、`Android/media/`、`DCIM/`、`Download/`、`Documents/`、`Pictures/`、各应用自建目录 |
| `/storage/<uuid>/`、`/mnt/media_rw/<uuid>/` | 外置存储卡 | 外部介质证据 |
| `/system/`、`/vendor/`、`/product/` | 只读系统分区 | `build.prop`（**型号、系统版本、指纹**）、预装应用 |
| `/proc/`、`/sys/` | 运行时视图 | 仅在线可得 |

## 08 应用层数据落点（通用）

> 系统层目录记牢后，继续定位第三方应用的数据与账户。以下按**默认安装路径**归纳；自定义路径需按进程、快捷方式、服务配置反推。

### 08.1 浏览器

| 浏览器 | Linux | Windows |
|---|---|---|
| Chrome | `~/.config/google-chrome/Default/` | `AppData\Local\Google\Chrome\User Data\Default\` |
| Chromium | `~/.config/chromium/Default/` | `AppData\Local\Chromium\User Data\Default\` |
| Edge | `~/.config/microsoft-edge/Default/` | `AppData\Local\Microsoft\Edge\User Data\Default\` |
| Firefox | `~/.mozilla/firefox/<profile>/` | `AppData\Roaming\Mozilla\Firefox\Profiles\<profile>\` |
| Brave | `~/.config/BraveSoftware/Brave-Browser/Default/` | `AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\` |

**Chromium 系 `Default/` 下关键文件**

| 文件 | 内容 |
|---|---|
| `History` | SQLite：`urls`、`visits`、`downloads`、`keyword_search_terms` |
| `Cookies` | SQLite；较新 Chromium 常在 `Network/Cookies`，值可能受 OS 加密保护 |
| `Login Data` | **保存的账号口令**（加密） |
| `Web Data` | 自动填充、表单历史 |
| `Bookmarks` | JSON |
| `Preferences` | JSON：默认搜索引擎、扩展、下载目录 |
| `Top Sites`、`Sessions/`、`Current Session` | 常访问站点、会话恢复 |
| `Cache/`、`Code Cache/`、`Service Worker/` | 网络缓存（**可能还原已删页面**） |
| `Extensions/` | 扩展程序（含钱包类插件） |
| `Local State` | 通常在 `User Data` 或浏览器配置根而非 `Default/` 内，保存 OS 加密相关材料/引用；仍需设备与用户保护上下文 |

**Firefox 关键文件**：`places.sqlite`（历史 + 书签）、`cookies.sqlite`、`formhistory.sqlite`、`downloads.sqlite`（旧版，现代下载记录位置需核对）、`logins.json` + `key4.db`（**保存的口令：密文与密钥分离**）、`sessionstore-backups/`、`extensions.json`。

### 08.2 IM / 社交

| 应用 | Windows | Linux |
|---|---|---|
| 微信 | `Documents\WeChat Files\<wxid>\`（旧）、`Documents\xwechat_files\` + `AppData\Roaming\Tencent\xwechat\`（新） | `~/Documents/xwechat_files/`、`~/.config/wechat` |
| QQ（NT） | `Documents\Tencent Files\`、`AppData\Roaming\Tencent\QQ\` | — |
| 钉钉 | `AppData\Roaming\DingTalk\`（含 `main.db`） | — |
| Telegram | `AppData\Roaming\Telegram Desktop\tdata\` | `~/.local/share/TelegramDesktop/tdata/` |
| Discord | `AppData\Roaming\discord\` | `~/.config/discord/` |
| Signal | `AppData\Roaming\Signal\` | `~/.config/Signal/` |

通用要点：桌面版 IM 多为 SQLite（`*.db`）或加密容器；图片与文件可能以摘要或日期命名；只有重算字节摘要或核对应用逻辑后，才能认定文件名是哈希；移动端 IM 见[聊天与移动应用数据](/knowledge/forensic-mobile-apps/)。

### 08.3 邮件客户端

| 客户端 | 落点 | 关键文件 |
|---|---|---|
| Outlook | `AppData\Local\Microsoft\Outlook\` | `*.ost`、`*.pst`（归档） |
| Thunderbird | `AppData\Roaming\Thunderbird\Profiles\<p>\` | `Mail/`、`ImapMail/`、`prefs.js`、`logins.json` |
| Foxmail | 安装目录 `Storage\<账号>\` | `*.box` |
| Evolution（Linux） | `~/.local/share/evolution/`、`~/Mail/`、`/var/mail/` | mbox / Maildir |

### 08.4 云盘与远程控制

| 类别 | 应用 | 落点与要点 |
|---|---|---|
| 云盘 | OneDrive | `~/OneDrive`、`AppData\Local\Microsoft\OneDrive\`（同步日志含账号与文件清单） |
| 云盘 | Dropbox / 坚果云 | Dropbox 可查 `AppData\Local\Dropbox\` 与实际版本的 `filecache.db` 文件索引；坚果云应依据安装/配置单独定位，不能沿用 Dropbox 的目录作为共同路径 |
| 远程控制 | TeamViewer | `AppData\Roaming\TeamViewer\`：`Connections_incoming.txt`（**连接历史**） |
| 远程控制 | AnyDesk | `AppData\Roaming\AnyDesk\`：`ad.trace`、`user.conf` |
| 远程控制 | 向日葵 | `AppData\Roaming\Oray\SunLogin\` |

内网穿透（ngrok / frp / Cloudflare Tunnel）与代理（Clash / v2ray / xray）的配置与历史端点见[网络配置与远程连接](/knowledge/forensic-remote-connections/)，按应用实际账户与启动参数定位。

### 08.5 虚拟货币钱包

| 类型 | 落点 |
|---|---|
| Bitcoin Core | `~/.bitcoin/wallet.dat`、`AppData\Roaming\Bitcoin\wallet.dat` |
| Electrum | `~/.electrum/wallets/`、`AppData\Roaming\Electrum\wallets\` |
| Ethereum（Geth） | `~/.ethereum/keystore/` |
| 浏览器插件钱包（MetaMask 等） | 浏览器 `Extensions/` 与扩展存储区 |
| 通用 | 钱包文件多加密；**地址与流水常同时存在于 IM、截图文件名与本地账本** |

### 08.6 开发与运维工具（凭据高发区）

| 工具 | 落点 | 内容 |
|---|---|---|
| Git | `~/.gitconfig`、`~/.git-credentials`、仓库 `.git/` | 身份、凭据、提交历史 |
| SSH | `~/.ssh/`、`/etc/ssh/` | 密钥与连接记录 |
| Docker | `~/.docker/config.json` | 镜像仓库凭据 |
| Kubernetes | `~/.kube/config` | 集群凭据；[身份与配置核对](/knowledge/forensic-kubernetes-cluster/) |
| 云厂商 | `~/.aws/credentials`、`~/.aliyun/config.json` | 云凭据 |
| 数据库客户端 | `~/.my.cnf`、`~/.pgpass`、`~/.dbshell` | 可能保存凭据；格式和保护方式需核对 |
| 包管理 | `~/.npmrc`、`~/.pypirc`、`~/.cargo/credentials` | 仓库 token |
| VS Code | `~/.config/Code/User/`（`settings.json`、`History/`、`globalStorage/`、`workspaceStorage/`） | **本地历史可还原已删代码** |
| Vim / Neovim | `~/.viminfo`、`~/.local/share/nvim/` | 最近文件 |
| AI 客户端 | `~/.config/<app>/`、`AppData\Roaming\<app>\`、`~/.cache/<app>/` | API Key、会话数据库、本地模型（`models/`） |

## 09 按检材类型的翻找清单（通用）

| 检材类型 | 先翻这五处 | 再往哪深挖 |
|---|---|---|
| 桌面（Windows） | `System32\config`、`winevt\Logs`、`Prefetch`、各用户 `NTUSER.DAT`、`AppData` | `$UsnJrnl`、`$Recycle.Bin`、VSS 卷影、`pagefile.sys` |
| 桌面（Linux） | `/etc`、`/var/log`、`/home/*`（含隐藏文件）、`/var/lib`、`/tmp` | btrfs 子卷 / 快照、`/root/.bash_history`、应用 `.config` |
| 服务器 | 服务配置 `/etc/<svc>`、数据目录 `/var/lib/<svc>`、`/var/log`、`/etc/crontab`、`/root` | 容器、存储池（LVM / ZFS / btrfs）、原始介质残留 |
| 手机（Android） | `/data/user/0/<pkg>/`、`/data/system/`、`/data/misc/`、`/storage/emulated/0/`、APK 本体 | SQLCipher、`shared_prefs/`、应用外部目录 |
| 应用 / API 层 | 站点源码与配置、数据库、访问日志、凭据与密钥文件、备份文件（`*.sql` / `*.zip` / `*.bak`） | 版本库 `.git/`、上传点、跨端口实例 |
| 二进制样本 | 文件头与编译时间、字符串与常量、导入表 / 符号、资源段、同目录伴随文件 | 反编译关键函数、算法离线复现 |

## 10 关联模式：把孤立路径串成证据链

关联时保留每一端的对象身份、完整路径与时间范围。具体任务与证据链见[取证任务与证据路径索引](/knowledge/forensic-method-index/)。

| 模式 | 说明 |
|---|---|
| **凭据迁移** | 一台设备的解锁口令常在另一台设备的便签 / 聊天 / 浏览器里 |
| **主机名 → IP → 归属** | 应用配置只写主机名，真实 IP 在 hosts，网桥与容器定义、rootfs 及进程归属共同验证部署方式，默认网段不能独立定性 |
| **多端点枚举** | 同一服务可能多端口 / 多实例（主库 vs 备份库、读写分离） |
| **时间线互证** | 文件系统时间 ↔ 日志时间 ↔ 数据库时间 |
| **层级递进** | 容器 → 卷 → 文件系统 → 文件 → 应用数据 |
| **密钥三段式** | 种子（资源 / 配置）→ 派生（哈希 / KDF）→ 密文（数据文件） |
| **主备通道** | 分别检查主服务配置与代码/native 库内的备用候选；用实际调用链确认启用条件，不因存在字符串认定已连接 |
| **介质链** | 裸盘 → 分区 → 文件系统 → 子卷 / 快照 |

## 11 易混路径辨析（通用）

| 易混 A | 易混 B | 关键差别 |
|---|---|---|
| `/etc/os-release` | `/usr/lib/os-release` | 先区分普通文件与软链；存在独立 `/etc/os-release` 时优先该份，不假定总是指向后者 |
| `/etc/nginx/sites-available/<site>` | `sites-enabled/<site>` | 后者常是软链，也可为独立文件；先读取链接文本并定位检材内实体，现场可用 `readlink -f`，离线绝对软链不能解析到分析机 |
| `/data/data/<pkg>/` | `/data/user/0/<pkg>/` | 通常对应 0 号用户；其他用户或工作资料需按真实 userId 定位 |
| `/data/user/0/<pkg>/` | `/data/user_de/0/<pkg>/` | 后者是设备加密存储，部分应用数据分两处 |
| `/etc/<svc>` | `/var/lib/<svc>` | 前者=**配置（结构）**，后者=**数据（事实）** |
| `/var/log/<svc>/` | `/var/lib/<svc>/` | 前者=**时间线**，后者=业务记录 |
| `System32\config\SYSTEM` | `System32\config\SOFTWARE` | 前者=系统 / 硬件 / 服务，后者=软件 / 设置 |
| `Users\<u>\NTUSER.DAT` | `System32\config\DEFAULT` | 前者=用户 hive，后者=系统账户默认配置 |
| `Recent\*.lnk` | `AutomaticDestinations\*.automaticDestinations-ms` | 前者=单个最近文件，后者=**按程序聚合的跳转列表** |
| `$Recycle.Bin\$I*` | `$Recycle.Bin\$R*` | 前者=元数据（原路径 + 删除时间），后者=文件内容 |
| `/proc`、`/sys`、`/run` | `/etc`、`/var` | 前者是**内存视图**，重启即失，离线检材读不到 |
| 普通目录 | btrfs 子卷 / 快照 | 同名路径可能是子卷；用 `btrfs subvolume show` 核对子卷 UUID 与 Parent UUID，再判断快照来源 |
| `docker0`（172.17/16） | `lxcbr0`（10.0.3/24） | 网桥网段是容器技术判据之一（且可被自定义） |
| 镜像 `imagedb/**/*.json` | 容器 `containers/<id>/config.v2.json` | 前者=**镜像**，后者=**容器实例** |
| APK `resources.arsc` | APK `assets/` | 前者=资源索引（**字符串常量残留**），后者=原始文件 |
| APK `classes*.dex` | `lib/<abi>/lib*.so` | 前者=Java 层，后者=Native 层（密钥常在 `.rodata`） |
| `prefs.js` / `Preferences` | `logins.json` / `Login Data` | 前者=界面设置，后者=**保存的凭据** |
| `~/.bash_history` | 日志文件 | 时间字段是否存在需检查历史格式；写盘可延迟、条目可编辑，顺序及绝对时间均需与日志等交叉 |

## 12 取数顺序与工具索引

**取数顺序**：先确认设备/分区/用户，再从配置建立结构、从数据提取记录、从日志还原时间线，最后到元数据、快照或原始字节寻找残留。完整保全边界见[证据保全与质量检查](/knowledge/forensic-quality/)。

**只读原则**：取得镜像并记录哈希，先核对设备层和文件系统层的只读保护，再解析副本。现场采集会新增进程、访问与工具痕迹，必须记录；读取文件可能影响 atime，软件运行还可能新增日志、配置或注册表，不能统称为所有读取都会改写 mtime。ext3/ext4 的 `ro` 仍可能回放日志，使用经确认的 `ro,noload` 或设备层只读；其他文件系统按其语义处理。

逐参数命令与工具选择见[取证命令与工具速查](/knowledge/fic-case-13/)。Docker 的配置、镜像、实例、日志与只读检查集中在[Docker 现场流程](/knowledge/docker-evidence-02/)及[Docker 存储与日志](/knowledge/docker-evidence-03/)，这里仅保留目录入口。

## 13 实战：从目录表生成可复核的证据清单

### 13.1 Linux 镜像：身份、挂载与日志三端对照

**场景与材料：** 已取得 Linux 系统镜像及一份 `/var/log` 目录导出，需要确定系统归属、服务配置和活动时间范围。以下 `/mnt/evidence` 是已核实的只读检材根，`./work` 是分析机输出目录；系统目录缺席也要记录，不能自动补为默认布局。

```bash
EVIDENCE_ROOT=/mnt/evidence
mkdir -p ./work
ls -ld "$EVIDENCE_ROOT/etc/os-release" "$EVIDENCE_ROOT/usr/lib/os-release"
readlink "$EVIDENCE_ROOT/etc/os-release"
cat "$EVIDENCE_ROOT/etc/hostname" "$EVIDENCE_ROOT/etc/fstab"
find "$EVIDENCE_ROOT/var/log" -maxdepth 2 -type f -print
```

`ls -ld` 查看条目本身，`readlink` 只读链接文本。假如链接指向 `/usr/lib/os-release`，实际读取检材内的 `$EVIDENCE_ROOT/usr/lib/os-release`；不要让分析机 `/usr/lib` 成为目标。`fstab` 的 UUID 与超级块对应后，确认挂载点是否遗漏独立的 `/var`、`/home`、`/data`、`/db` 或 `/media/<name>`。目录空可能是分区未挂入，不能直接判无业务数据。

持久化 journal 留存时，在分析机读它的副本；下面只读一个明确 journal 文件，并把格式化输出存入工作目录。实际文件名由前面的目录清单确定。

```bash
journalctl --file=./work/system.journal --utc --no-pager > ./work/journal-utc.txt
last -f ./work/wtmp
lastb -f ./work/btmp
utmpdump ./work/wtmp > ./work/wtmp-records.txt
```

`journalctl --file` 指指定文件，`--utc` 用 UTC 展示时间，`--no-pager` 禁分页。`last`/`lastb` 的 `-f` 是登录文件输入，`utmpdump` 的输出适合逐字段核对，三者不替代对 `lastlog` 或 `faillog` 的专用格式读取。系统时钟错误、日志轮转、二进制格式/架构差异或只采集部分文件，都要列为限制。每个事件回到原记录编号、时间及字段，不能把仿真新日志混入历史清单。

### 13.2 Windows 镜像：用户、执行线索与事件相互核对

**场景与材料：** 获得 Windows 卷镜像和离线导出的 `SYSTEM`、`SOFTWARE`、用户 hive 及 `.evtx`，需要确认某个程序路径与某用户活动之间的关系。先按 `Users\<u>` 建立账户目录清单，将 `NTUSER.DAT`、`UsrClass.dat` 及事务日志绑定同一 SID；机器 hive 的 `Select` 值决定实际 ControlSet，不能固定把 `ControlSet001` 当当前控制集。

在 Kali 中对已导出的目录副本检查文件存在性。下面路径大小写和账户名都为示例，应保持检材中实际名称。

```bash
find ./work/windows/Windows/System32/config -maxdepth 1 -type f -print
find ./work/windows/Windows/System32/winevt/Logs -maxdepth 1 -type f -name '*.evtx' -print
find ./work/windows/Users/analyst/AppData/Roaming/Microsoft/Windows/Recent -type f -print
```

随后分别用注册表解析器读 hive、用事件解析器读 `.evtx`，导出字段而不在分析机加载为自身注册表。对同一程序建立“路径与文件哈希 → Amcache/兼容缓存 → Prefetch 或 UserAssist → 进程/登录事件”的对应表；Amcache 或 ShimCache 有条目时，只能先写发现缓存线索，不能直接写运行成功。LNK/跳转列表需核对原路径、卷序列号和记录时间，网络路径或外部盘可能尚未取得文件内容。

事件 ID 只在相应 Provider、Channel 和系统版本范围内解释。比如 Security 4624 需同时读 LogonType、账户、来源及 LogonId；RDP 1149 与会话 21/22/24/25 要按用户、会话 ID 和时间串联。日志缺席可能来自未启用策略、覆盖或采集遗漏；事件显示的账户也不能单独替代操作者归属判断。

### 13.3 Android 镜像：以用户 ID 和加密状态限定范围

**场景与材料：** 已取得 Android 文件系统提取和 APK 副本，要定位某应用的数据库、偏好与模型/媒体。先记录采集方式、Android 版本、用户/工作资料 ID、解锁状态与可见分区，再核对包名；不要把某个包目录的文件名与另一用户的数据库直接混合。

```bash
find ./work/android/data/user -mindepth 1 -maxdepth 2 -type d -print
find ./work/android/data/user_de -mindepth 1 -maxdepth 2 -type d -print
find ./work/android/data/user/0/com.example.app -maxdepth 2 -type f -print
find ./work/android/storage/emulated/0/Android/data -maxdepth 2 -type d -print
```

以上均读已取得副本。`/data/user/0/<pkg>/` 属用户 0 的凭据加密存储候选，`/data/user_de/0/<pkg>/` 属设备加密存储候选；用户未解锁或采集权限不足时，目录不可读不等于没有数据。`/data/data/<pkg>/` 的别名关系要实检，对其他用户使用对应 ID。系统 `accounts.db`、`usagestats/` 与 `sync/` 的布局可随版本移动，先从 `/data/system/` 延伸到实际每用户目录，不把缺一个旧位置写成没有账号或使用记录。CE/DE 与多用户边界可核对[Android 文件级加密说明](https://source.android.com/docs/security/features/encryption/file-based)。

数据库复制时带上相关 `-wal`、`-shm`，保留原文件组合与哈希；对工作副本查询表结构和业务记录。`shared_prefs/` 的标识/密钥候选与 `files/` 的模型/密文对象要结合代码使用关系；拥有同名文件、Model 文件名或权限声明，只支持进一步定位，不能直接确定用户行为与实际加载版本。

### 13.4 交叉验证与应用关联记录

每个命中保存“设备/分区 → 用户或服务账户 → 应用/实例 → 完整路径 → 原始字段/字节 → 时间语义 → 解析输出 → 验证与限制”。例如浏览器 `History` 与下载文件对应时，同时核对 Profile、下载目标路径、保留的 URL/时间和文件哈希；`Local State` 必须从浏览器根取，不能只导出 `Default/`。IM 附件摘要式名称先重算内容摘要；钱包地址须与聊天上下文、截图交易标识和账本记录对照，不把截图文件名当链上确认。

路径表内同一文件可能被多个账户读取或经同步复制。文件内容相同支持字节一致，时间不一定仍是创建时间；配置显示某个远程地址也不证明已经连接。只有把配置、内容、日志/数据库和文件系统对象相互关联，才能写清支持的事实范围。本文的示例用于说明读取路线，未针对读者的附件实际复跑；最终清单应包含不存在、权限不足、格式不支持与无法验证的条目。

## 14 集群、虚拟空间与应用密钥的定位补充

| 分析对象 | 候选位置或关联入口 | 下一步核验 |
| --- | --- | --- |
| Kubernetes 应用持久数据 | Pod volumeMount → PVC → PV → NFS server/path 或 CSI 信息 | 目录与挂载关系按对象配置核对；见[Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/) |
| MySQL 删除行 | 数据目录中的 binlog 与 binlog index、表结构及备份 | 区分软删字段和 ROW 事件，保留轮转顺序；见[数据库备份与恢复](/knowledge/forensic-database-recovery/) |
| Laravel 应用配置 | 站点 `.env`、路由、配置缓存、实际 Hashing 实现 | 配置文本与生效值分别核验；见[服务器服务与配置](/knowledge/forensic-server-services/) |
| Xshell 会话 | 用户 Documents 下的 `NetSarang Computer/<版本>/Xshell/Sessions/*.xsh` | 核对 UTF-16/BOM、版本、会话名称与连接字段 |
| Anytype 对象与历史 | 用户 `AppData/Roaming/anytype/` 下真实账户目录 | 搜索 `objects.db`、历史和附件，按应用版本解析；不能从目录 mtime 推断创建时间 |
| Windows 计划任务 | 镜像中 `Windows/System32/Tasks` 与注册表 TaskCache | 任务 XML、登记信息和执行日志互证，不能只看任务名 |
| Android 虚拟实例 | 宿主应用 `vprom/sys/<实例>/` 及内层应用/共享目录 | 区分宿主、实例、账号，见[Android 文件系统](/knowledge/forensic-android-storage/) |
| Hawk 偏好设置 | 对应包名的 `shared_prefs/Hawk2.xml` 与 `crypto.KEY_256.xml` | 完整 XML、APK 序列化、KeyChain 和认证上下文共同解析 |
| 应用加密附件 | 数据库引用、共享存储和应用自定义 `files/zip/` | 路径映射、真实格式、口令字段及解密后内容交叉验证 |

**使用规则：** 上表是定位入口，不是固定目录承诺。按真实卷、用户、应用版本和导出布局替换路径；Docker 的完整容器 ID 与 overlay2 缓存目录不能等同，具体追踪集中在容器专题，避免在多个分类重复维护。
