拿到的是一台还开着的 Linux，或一份离线根目录。要分清现在还在听的服务、配置落在哪一层，以及某次登录、定时任务或 SSH 会话有没有留下记录。

**记下当前端口和进程 → 把单元、日志和账户对到文件 → 服务起不来时先读配置 → 只在目标会话上采集这一刻 → 把异常接到同一次登录 → 离线再读发行版、账户和定时任务 → 然后按现场核对代理、网站配置、口令派生、业务记录、FTP 和 SSH。**

启停服务、改配置和登录，只在已经做好快照、并且限制外联的副本上做。原始材料保持只读。分析机上的 `systemctl` 和 `ss` 不能当成离线镜像的状态。

<span id="01-从现状建立服务清单"></span>

## 01 记下现在还在听的端口和进程

服务对不上时，先把采集这一刻还在跑的东西记下来。已经退出的进程，不靠这次的进程表。

**固定时间和主机 → 记下进程、端口和单元 → 退出的进程改查日志和计划任务。**

**1. 先固定这一刻的范围。** 保全系统时间、主机名、网络配置和磁盘快照后，记录进程、监听端口、服务单元与容器运行时。活体结果只反映采集时刻。

**2. 每个可疑端口单独写一行。** 记下对应进程、启动命令、执行文件、工作目录和用户。端口还在听，只说明采集时有进程占用它。

**3. 已经退出的进程改查留下的痕迹。** 靠日志、计划任务和磁盘痕迹补充。这次 `ps` 里没有，不能写成从来没有运行过。

这一步对上的是采集时刻的主机、时间、监听端口和对应进程。已经退出的进程，要等日志或计划任务补上。用来核对的是端口、进程、启动命令和用户写在同一行。保存系统时间、主机名、网络配置、磁盘快照，以及这次的进程和监听输出。

<span id="02-逐层定位配置和日志"></span>

## 02 把单元、日志和账户对到文件

进程已经记下，还不知道配置和日志在哪一层。按下面的顺序往下对，不要只打开一个目录。

**对单元和启动参数 → 定日志的时间和时区 → 对账户和登录 → 查周期任务 → 把配置里的路径对到磁盘。**

**1. 核对单元和实际启动参数。** 看 systemd 单元、覆盖配置和实际启动参数。单元文件、环境文件与进程命令行可能不一致。

**2. 先定日志的时间范围和时区。** 查看 `journal`、`/var/log/`、服务自有日志和日志轮转文件。时间对不上时，先不要解释事件先后。

**3. 对照账户和登录记录。** 看账户文件、SSH 公钥、登录记录、sudo 日志和 shell 历史。历史文件可能未写入、被清理或由其他会话覆盖，不能单独定案。

**4. 找出还会再次执行的任务。** 检查 cron、systemd timer、用户启动项、服务自动重启配置和应用层任务队列，识别持久化与周期执行。

**5. 把配置里的路径对到磁盘上的文件。** 数据目录、上传目录、数据库连接和反向代理路径，都要和磁盘实际内容核对。配置里写了路径，不表示那个目录已经在这份材料里。

这一步对上的是单元、实际启动参数、日志时段，以及配置路径在磁盘上的对应文件。历史文件缺失、轮转日志没打开，或路径指向这份材料以外时，分别写明。用来核对的是进程命令行和单元里的 `ExecStart` 已经对照过；日志时间范围和时区已经记下。保存单元文件、覆盖配置、日志范围和路径核对记录。

<span id="03-处理异常与输出"></span>

## 03 服务起不来时先读配置和日志

服务无法启动。先读已经留下的配置和日志，不为了“方便查看”去重启检材。

**离线读配置和日志 → 给变更留下哈希 → 把三层结论分开写。**

**1. 先离线读。** 打开配置和已有日志。不在原始检材上重启服务。

**2. 可疑变更先留下文件本身。** 记录文件哈希、权限、所有者、时间和完整路径，再与软件部署记录比较。

**3. 结论分成三层，各写各的证据。** “配置存在”“服务曾运行”“请求实际到达”不能互相代替。

这一步对上的是这份配置在，以及它和部署记录相比改过的文件。只有配置、没有运行日志或请求记录时，不写成服务曾经处理过请求。用来核对的是每一层结论旁边都有对应的文件、日志或请求。保存配置哈希、权限、所有者和时间，以及拿来比较的部署记录。

<span id="04-活机首轮定位示例"></span>

## 04 在目标会话里采集这一刻的服务

需要看现在还在跑的服务时，先确认这台终端属于目标会话。离线镜像不跑这组命令，改从挂载后的工作副本读对应文件。

**确认是目标会话 → 记下时间和监听 → 读单元和 journal → 没有 journal 再查别的日志。**

【仅在副本/仿真/授权环境执行】下面只在已获授权、并且需要采集运行态时执行。保存命令、执行时间和原样输出。以 Nginx 为例，服务名按目标系统中的实际服务替换。这组命令查询当前服务管理器和网络空间，不能在分析机上运行后把结果当离线检材状态。

```bash
date -Is
ss -tulpn
systemctl cat nginx
systemctl show nginx -p FragmentPath -p DropInPaths -p ExecStart
journalctl -u nginx --since '2026-01-01 00:00:00' --no-pager
```

**1. 先看时间和现在的监听。** `date -Is` 留下采集时间。`ss -tulpn` 是当前监听，不是历史端口。

**2. 读单元，再对运行中的参数。** `systemctl cat` 读主单元和覆盖片段，从中找到 `ExecStart`。`systemctl show` 是服务管理器当前记下的路径和启动命令。再对照运行进程的启动参数：单元配置不等于实际执行记录。

**3. 按单元和时间看 journal。** `-u nginx` 筛选这个单元，`--since` 给起始时间，`--no-pager` 直接输出。查询前记录环境时区；没有时区的时间文字按该环境解释。使用 UTC 窗口时在时间参数中明确写 UTC，再分别核对输入窗口和输出显示的时区。示例里的日期要换成这次要看的起点。

**4. journal 没有结果时，改查别的日志。** 检查持久化 journal、轮转和应用独立日志，不先认定服务没运行。配置与任务继续查 `/etc/systemd/system/`、`/usr/lib/systemd/system/`、`/var/log/`、`/etc/cron*`、`/var/spool/cron/` 及用户目录的 SSH 配置。

这一步对上的是这次采集的时间、当前监听、单元里的 `ExecStart`，以及这段 journal。`journalctl -u` 为空时，写明还查了哪些轮转日志和应用日志。命令、执行时间和原样输出留在一起。分析机上的输出不能当成离线镜像的状态。保存这组命令的输出、时区，以及单元文件和覆盖片段。

<span id="05-将服务异常接到登录与请求"></span>

## 05 把异常接到同一次登录或请求

服务异常已经看到，还要把它接到同一次登录或请求上。同名服务和后来复用的 PID，不能靠名字单独串起来。

**先排时间表 → 每项证据分开记 → 只有计划任务时不写成已经执行。**

**1. 先做时间表。** 按顺序放上：登录成功、sudo 提权、单元文件改动、服务重启、端口开始监听、首个异常请求。

**2. 每项证据分开记。** 用户 ID、来源地址、PID、服务名、请求 ID 和文件哈希各写各的。同名服务或 PID 复用时要加时间约束。

**3. 只有配置时，停在“配置存在”。** 若只看到计划任务或可疑公钥，最多说明持久化配置存在。要证明执行或登录成功，还需进程和认证或应用日志印证。

这一步对上的是同一时间约束下的登录、改动、重启和请求。只有计划任务或公钥、没有进程和认证日志时，不写成已经登录或已经执行。用来核对的是用户、来源、PID、服务名和请求 ID 能放进同一张时间表。保存时间表，以及每一项对应的日志或文件哈希。

<span id="06-离线-linux-的发行版账户与定时任务"></span>

## 06 从离线根目录读发行版、账户和定时任务

手里是一份离线 Linux 根目录，发行版、账户和定时任务还各看各的文件。登录提示可以改，不能拿它单独当系统版本。

**先确认 os-release 的实际文件 → 再分开账户和口令材料 → 对上 cron 与 timer 的字段。**

**1. 确认软链还在检材根里，再读发行版字段。** `/etc/os-release` 用来识别发行版；它可能指向 `/usr/lib/os-release`。`/etc/issue` 是可修改的登录提示，不要单独当作系统版本依据。

```bash
ls -ld ./work/etc/os-release ./work/usr/lib/os-release
readlink ./work/etc/os-release
# 确认软链目标在检材根内后，读取对应实际文件
grep -nE '^(ID|PRETTY_NAME|VERSION_ID)=' ./work/usr/lib/os-release
awk -F: '{print $1, $3, $4, $6, $7}' ./work/etc/passwd
find ./work/etc/cron* ./work/var/spool/cron -type f
rg -n 'ExecStart|User=|Environment=|OnCalendar|OnBootSec' ./work/etc/systemd/
```

若 `etc/os-release` 是普通文件，优先读它。示例假定它已经确认指向检材内的 `usr/lib/os-release`。其他软链也要先确认目标在检材根内，再读实际文件。命令里的路径可能不存在，把实际搜索范围留下。

**2. 账户和定时任务按文件种类分开。** 用户账户看 passwd/group，口令材料看 shadow。账户什么时候新增，还要日志、备份或文件系统记录，不能只数 passwd 的行。

系统 crontab 和 cron.d 有用户字段，用户 crontab 通常没有。前五项是分钟、小时、日、月、周。再一起看 `@reboot`、anacron、systemd timers、对应脚本和日志，不要只打开一个 `/etc/crontab`。

这一步对上的是发行版字段来自检材内的 os-release 实际文件，账户名和定时任务条目各有来源。软链越出检材根、路径不存在，或只有 passwd 没有新增时间的记录时，分别写明。`ID`、`PRETTY_NAME`、`VERSION_ID` 来自实际文件；cron 的用户字段和前五项没有跟命令混在一起。保存 os-release 实体、passwd 摘要、cron 与 systemd 单元里命中的任务行。

### 06.1 系统品牌、主机身份与云环境分别判断

发行版名字、这台机器叫什么、它是不是某朵云，现在还叠在一起。仓库配置里出现一个厂商品牌，不能直接写成这台服务器属于那家云。

**发行版用系统文件互证 → 主机名注明是哪一种 → 云环境再查初始化材料。**

**1. 发行版用 os-release、版本文件和软件包材料互证。** 三者对得上，才写发行版。只看到一个文件时，写明还缺哪一份。

**2. 主机身份按采集时刻分开写。** `/etc/hostname` 是磁盘上的配置。运行时 hostname、日志里的主机字段、容器主机名可以不同，各自注明采集时刻和作用范围。

**3. 云环境不靠仓库域名单独认定。** `/etc/yum.repos.d/` 里出现某品牌域名，只说明软件包镜像或仓库配置有这条线索。仓库可以被迁移、模板留下，或被管理员改写。

继续核对已经保全的 cloud-init datasource、实例元数据缓存、初始化日志、虚拟化或网卡材料，以及资源 ID。本地 NoCloud 等 datasource 也可以来自自建环境。要确定资源实际归属时，用有授权的资源记录或调证材料互证，不要向镜像里记下的云端点发请求。

最后分开写三句：发行版、主机身份、云平台。每一句带依据、对应时段和还没确认的项。

这一步对上的是发行版有系统文件互证；主机名已经标明是磁盘配置、运行时还是日志字段。只有仓库域名、没有 cloud-init 或资源记录时，不写成已确认云厂商。三句判断各有自己的文件，没有用 `/etc/yum.repos.d/` 代替资源归属。保存 os-release 与版本文件、hostname 的采集说明、datasource 和初始化日志的范围。

<details>
<summary>展开可用账户的口径与 shadow 字段</summary>

### 06.2 可用账户的口径与 shadow 字段

passwd 里有很多行，但还没说清要统计的是“有记录的账户”还是“能登录的账户”。口径不先说死，后面的数字会对不上。

**先声明口径 → 再逐个看 shadow 字段 → 对上了才说这个账户能走哪种认证。**

**1. 先声明“可用账户”指哪一种。** 是本地记录、可交互账户，还是允许某项服务登录的账户。`passwd` 的行数只是本地账户记录数。

每个候选核对账户名、UID、家目录、shell、shadow 锁定和过期，再查 PAM 和 SSH 或服务策略。UID 范围只是发行版惯例，不能靠它排除服务账户、额外的 UID 0，或目录服务账户。

| 统计口径 | 能回答什么 | 必须另核对 |
| --- | --- | --- |
| 本地账户记录 | passwd 中有多少名称/UID | NSS/目录服务来源、重复 UID 与服务账户 |
| 可交互 shell 候选 | shell 指向交互解释器的本地记录 | shell 实体、访问策略、锁定/过期与 PAM |
| 某服务允许继续认证的账户 | 该时段策略没有拒绝的候选身份 | 实际认证方法、密钥/口令、服务与会话结果 |
| 历史认证成功账户 | 所存目标时段日志中的成功事件 | 日志覆盖、映射账户、重复事件及自然人归属 |

**2. 按字段读 shadow，不要把日期当成登录时间。** 第 2 字段是口令材料和特殊标记。后面的字段是按天计算的改密、老化和过期，不能直接当成精确到秒的登录时间。以 `!` 开头通常表示口令锁定。`!`、`*` 这类不是有效 crypt 结果的值，表示不能用这份 UNIX 口令认证。其他认证还能不能用，仍看服务、PAM 和账户检查。空字段怎么处理，也依策略而异。字段含义见 [shadow 字段手册](https://man7.org/linux/man-pages/man5/shadow.5.html)。

**3. 哈希只拆格式，不把它当成明文或可逆密文。** 按目标算法的存储格式拆开方法标识、参数、盐和校验结果。例如 `$6$salt$hash` 或 `$6$rounds=N$salt$hash` 对应 SHA-512-crypt。`$y$params$salt$hash` 对应 yescrypt，参数字段不是盐。其他格式按目标 libcrypt 或 libxcrypt 的文档核对，不要一律按“第几个 `$` 字段”来切。盐不是明文密码。保存的口令哈希也不是可逆密文。认出格式，不能证明已经知道口令，也不能证明账户可以登录。格式依据见 [crypt 哈希格式](https://github.com/besser82/libxcrypt/blob/develop/doc/crypt.5)。

在受控记录里保全原始字段和格式解析结果，展示时脱敏。不要把真实哈希提交到外部查询，也不要用候选口令去试真实账户。若只有 passwd 和 shadow，就报告所采用口径下的账户候选和材料缺口，不能写成已经验证过的可登录集合。

**登录时还有脚本会拿整份 shadow 做比较。** 离线先读 `/etc/profile`、`/etc/bashrc` 和 `/etc/profile.d/`。有的脚本计算 `/etc/shadow` 的 SHA-256，与一个隐藏基准文件比较；不一致就在登录时清理容器、家目录和命令历史。这和上面的口令格式、也和 Windows EFS 的证书失效，是不同的事。**【仅在副本/仿真/授权环境执行】**三选一：启动前离线或单用户移开该脚本；使用其他检材里已经得到的原口令登录，不改 shadow；若副本已经改了口令，在脚本开始执行时中断它，然后移走脚本。不要把脚本里的删除动作再执行一遍。

统计口径已经声明，候选账户的 shadow 第 2 字段和哈希格式已经分开。没有 PAM、服务策略或认证日志时，不写成这些账户已经登录成功。表里每一行的“能回答什么”和“必须另核对”都有对应材料。哈希只识别到方法和盐，没有被写成明文。保存口径说明、脱敏后的字段解析、crypt 格式和仍缺的认证记录。

</details>

<span id="07-登录sudo-与-systemd-journal"></span>

## 07 用保全的 journal 核对登录和 sudo

认证日志和 journal 都在，但还不知道这次 sudo 有没有做完，也不知道空的查询是“没有事件”还是“目录没指对”。

**先按发行版找到日志 → 用保全的 journal 目录列出启动周期 → 空结果先分清是错误还是确实没有。**

**1. 先按记录种类找到文件，不要把 SSH 字段再定义一遍。**

| 系统或记录 | 常见路径 | 重点字段 |
| --- | --- | --- |
| 认证与 sudo | 按目标发行版的日志/转发配置定位；SSH 路径统一见[第 14.7 节](#147-ssh日志取证) | sudo 调用/目标用户、TTY、目录、命令和会话；SSH 字段不在此重复定义 |
| 系统日志 | syslog/messages/kern.log | 开关机、服务、内核与时钟变化 |
| 包管理 | dpkg.log、yum/dnf 日志 | 软件安装/升级，不能单独证明执行 |
| journal | `/var/log/journal` 或运行时目录 | boot ID、unit、UID/PID、实时与单调时间 |

SSH 的路径统一在[第 14.7 节](#147-ssh日志取证)，这里不重复那些字段。包管理日志里的安装或升级，不能单独证明程序已经执行。

**2. 把 journalctl 指到保全目录，再读启动周期。**

```bash
journalctl --directory=./work/var/log/journal --list-boots
journalctl --directory=./work/var/log/journal --utc --no-pager -o short-iso-precise
```

`--directory` 只读这个保全目录，不把分析机自己的默认日志混进来。`--list-boots` 看可见的启动周期。`--utc` 统一输出显示。`-o short-iso-precise` 保留细时间。先保全压缩的轮转日志，另外读取，并留下时间基准和启动周期。

SSH 消息要分别查认证、会话，以及和版本相关的登录数据库。不能用一条文本命中代替整条登录链。sudo 日志里已经有命令名称之后，还要查执行结果、audit 或应用日志，确认动作有没有完成。

**3. 先保存不筛选的结果，再缩小范围。** 需要确认事件来源时，保留完整字段里的 `_MACHINE_ID`、`_BOOT_ID`、`_SYSTEMD_UNIT`、`_UID`、`_PID` 和原始时间。

空输出先查错误：目录不对、权限不足、格式不兼容，和确实没有匹配条目，分开记。不能一概写成该时段没有事件。

**4. 远程勘验只固定易失信息，不把关历史写成没有痕迹。** 先固定易失信息和关键目录，记录终端会话及命令时间。关闭 Shell history 只影响这部分历史，不会消除审计、服务或其他日志，不能当成“无痕取证”。

材料里如果还有面板和网站，按[服务器面板与网站](/knowledge/forensic-server-panel/)分清面板账户、站点配置和日志。Docker 材料归入既有容器分类，不要把不同入口的记录写成同一次登录。

这一步对上的是 journal 来自保全目录，启动周期和 sudo 命令名称已经和对应字段放在一起。查询为空时，写明是路径、权限、格式还是确实无记录。只有命令名称、没有执行结果时，不写成动作已经完成。`--list-boots` 的周期和 `-o short-iso-precise` 的时间能对上要查的那一次。分析机默认 journal 没有混入。保存不筛选的 journal 输出、boot ID、相关单元字段，以及轮转日志的范围。

<span id="08-实战验证一项可疑定时任务"></span>

## 08 核对一条定时任务有没有执行过

离线 Linux 镜像里有一条 cron 记录和相关脚本。要判断这条配置现在是否还能执行、以前有没有执行过、执行了什么。

**先看来源和字段 → 找到脚本 → 看输入输出和日志 → 对上别的事件时间 → timer 再分开核对。**

**1. 先记录这条来自哪里。** 是系统 crontab、cron.d，还是某账户的 crontab。核对时间字段、执行账户、命令路径和环境。不能把系统级的用户列当成命令的一部分。

**2. 找到账户和脚本，只静态阅读。** 根据 `/etc/passwd` 和服务配置定位账户家目录、工作目录及所引用脚本。保存完整路径、权限、所有者、哈希与软链关系。不执行未知脚本。

**3. 沿脚本看它读写什么。** 查看脚本中的输入和输出路径、数据和日志。检查 cron、journal 或对应应用是否留存运行结果。任务启动和业务动作成功分开写。

**4. 把时间对到别的记录上。** 将任务执行时间与登录、sudo、文件变动和服务日志对应。没有时间的 shell 历史不能用来给任务创建日期定点。文件 mtime 也不能直接等于首次部署时间。

**5. 如果是 systemd timer，再拆开看。** 分别核对 timer 和它触发的 service、User、ExecStart 和实际日志。存在配置与曾经执行是两条独立结论。

发现一个每小时触发的配置，但引用脚本已经缺失，日志也未覆盖目标期间。可以记录“存在周期任务配置，当前有效性和历史执行结果尚未确认”，不能直接认定已持续执行。

【仅在副本/仿真/授权环境执行】需要仿真验证时，在隔离快照副本中记录启动前后变化。不要等待或启动任务，再把新产生的记录写成历史证据。系统身份、安装和运行的区分见[Linux 系统与服务识别](/knowledge/fic-case-03/)。

这一步对上的是这条任务的来源、时间字段、执行账户和脚本哈希。脚本缺失或日志没覆盖目标时段时，历史有没有执行过仍然未确认。运行结果来自 cron、journal 或应用日志，而不只是配置文件还在。保存条目原文、脚本哈希和软链、相关日志范围。仿真里新启动的变化单独记。

<span id="09-实战核对密码修改软件安装和服务代理配置"></span>

## 09 把改密、装软件和代理配置分开

快照里同时有认证日志、包管理日志和服务配置。改密、装软件、配代理不是同一件事，时间也不能先混成一条。

**先把事件时间和材料时间分开 → 再找到代理写在哪一层 → 对上启动参数才写当时实际在用。**

### 09.1 将事件时间与材料时间分开

Linux 快照里有认证日志、包管理日志、服务单元和 shell 历史。要判断某账户何时改了密码、某组件何时安装，以及服务有没有配置代理。下面只读挂在 `/mnt/evidence` 的保全材料，路径按实际发行版调整。

**先分清日志是文本、压缩还是 journal → 再给传统 syslog 补上年份和时区 → 对上了才写改密或安装已经发生。**

**1. 先建输出目录，再按实际文件检索。** 压缩轮转另作解读，原文件保留。二进制 journal 交给对应解析器，不要直接当文本搜。

```bash
EVIDENCE_ROOT=/mnt/evidence
OUT=/work/output/server-services
mkdir -p "$OUT"
rg -n 'passwd|password changed|chauthtok' "$EVIDENCE_ROOT/var/log/secure"*
rg -n 'passwd|password changed|chauthtok' "$EVIDENCE_ROOT/var/log/auth.log"*
rg -n 'Installed:|Updated:' "$EVIDENCE_ROOT/var/log/yum.log"*
rg -n 'install|upgrade' "$EVIDENCE_ROOT/var/log/dpkg.log"*
journalctl --directory="$EVIDENCE_ROOT/var/log/journal" --utc --no-pager \
  -o short-iso-precise > "$OUT/server-journal.txt"
```

**2. 传统 syslog 只有月日和时分秒时，先补年份和时区。** 用轮转关系、启动周期，以及同一账户的其他日志核对，再排时间线。不要只留下 `09:xx:xx`。

按实际文件清单区分未压缩日志、压缩轮转和二进制 journal。`rg` 的命中、未命中、文件不存在或不可读，是不同结果。记录 stdout、stderr 和退出状态。不要把通配符碰到的每个文件都当成已经成功读过。压缩轮转要用对应方式解开后再检索，事件字段和时间基准与当前日志保持一致。

**3. 密码命中要分成失败、验证、改密成功和操作者。** `passwd` 出现在历史里，不证明改密已经完成。shadow 的日期字段也不是精确到秒的操作记录。shell 历史有时带时间戳，也可能缺失、延迟写入或被改过。不能说“history 永远不记时间”，更不能凭没有时间的命令行推定事件时间。

**4. 安装记录和启动记录分开。** 包管理日志里的 Installed 或 upgrade 支持安装或升级事件。文件系统 mtime、镜像创建时间、进程启动时间各有含义。有安装记录，不证明服务已经启动。启动还要和服务日志、监听端口、请求记录核对。日志范围不全时，不能把留下的第一条记录当成首次安装。

这一步对上的是改密、安装各自命中的日志文件、退出状态，以及已经补上的年份和时区。只有 `passwd` 历史或 shadow 日期、没有成功改密记录时，不写成口令已经改完。安装日志没覆盖全程时，不把首条记录写成第一次安装。命中行的事件种类已经分成失败、验证、成功或安装。压缩日志和 journal 没有被当成普通文本硬搜。保存检索的 stdout、stderr、退出状态，journal 导出，以及用来补年份的轮转关系。

<details>
<summary>展开找到代理配置的实际层级</summary>

### 09.2 找到代理配置的实际层级

服务出网异常，配置里又像有代理。还不知道这行写在单元、覆盖片段，还是进程自己的环境里。

**沿服务名静态找代理变量 → 记下路径和层级 → 只有磁盘配置时不写成当时已经在用。**

**1. 沿单元、覆盖和 EnvironmentFile 往下找。** 代理可能在 `/etc/systemd/system/` 的覆盖片段，也可能在 `/lib/systemd/system/` 或 `/usr/lib/systemd/system/` 的单元，或被引用的 EnvironmentFile 里。运行时进程环境还可能不同。按服务名静态查找 `Environment=`、`EnvironmentFile=`、`HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY`，记下完整路径和来源层级。

**2. 代理地址不是应用监听端口。** URL 里的主机和端口是代理服务器端点。只有磁盘配置时，可以写“该单元配置了代理”。要写“某时刻服务实际采用了代理”，还需要启动参数、采集到的环境、网络或日志。容器运行时的专用配置见 [Docker 环境、服务与配置](/knowledge/docker-evidence-01/)。站点代理、守护进程代理和容器内代理不要写成同一条配置。

这一步对上的是代理变量出现在哪一个文件、哪一层，以及它指向的是代理端点。没有启动参数或运行环境时，不写成服务当时已经走了这个代理。用来核对的是 `Environment=` 或 `EnvironmentFile=` 的路径和变量名在同一条记录里。保存单元、覆盖片段或环境文件的完整路径。

</details>

<span id="10-实战独立读取-laravel-网站与机器人配置"></span>

## 10 从数据目录找回 Laravel 和机器人配置

代码、卷里的应用目录和数据库副本都在，应用现在起不来。先从数据目录找回应用根，再分清磁盘配置和当时生效的配置。

**从数据目录回到应用根 → 静态读配置和路由 → 对上缓存、邮件和机器人各在哪一层。**

### 10.1 从数据目录回到应用根目录

拿到的是网站代码、NFS 或其他卷上的应用目录、数据库副本和保全日志。应用目前无法启动。要识别缓存和数据库连接、后台入口、邮件发件人、机器人配置，并核对应用版本。下面的名称和地址都是通用示例。

**先把隐藏的 `.env` 找到 → 再按表核对入口和版本 → 对上路由以后才写后台地址。**

**1. 用能看见隐藏文件的办法找配置，找到后只静态读。** 普通 `ls` 不显示隐藏文件。用 `ls -a`、`find` 或明确路径找 `.env`。找到后不要把它加载成环境，也不要执行里面的内容。

```bash
SITE=/mnt/evidence/data/k8s_data/apps/site-data
OUT=/work/output/site-config
mkdir -p "$OUT"
ls -lah "$SITE"
find "$SITE" -maxdepth 3 -type f \
  \( -name '.env' -o -name 'composer.lock' -o -name 'composer.json' -o -name 'config.php' \) -print
rg -n 'CACHE_|DB_|QUEUE_|MAIL_|ADMIN_|TELEGRAM_|BOT_|PROXY' "$SITE/.env"
rg -n 'env\(|prefix|admin|auth/login|MAIL_|telegram|api_url|proxy' \
  "$SITE/config" "$SITE/routes" "$SITE/app"
```

口令、token 和密钥只保存到受控分析目录。示例里不复制真实凭据。报文件不存在时，记下当前材料和搜索范围，再查其他配置位置，不要写成“应用无配置”。

**2. 按目标核对落点，路由和后台前缀分开记。**

<details>
<summary>展开按目标核对落点，路由和后台前缀分开记：字段表</summary>

| 目标 | 主要落点 | 如何验证 |
| --- | --- | --- |
| 数据库、缓存、队列 | `.env`、`config/database.php`、`config/cache.php` 等 | 实际代码使用的配置键、卷路径、服务日志 |
| 后台前缀与登录路径 | `routes/`、后台配置、控制器/中间件 | 路由声明与实际重定向分别记录 |
| 邮件发件人 | `.env`、`config/mail.php`、数据库设置表 | 代码读取优先级、历史设置与邮件日志 |
| 机器人代理/API 域名 | 机器人卷的 `config/`、配置数据库 | 域名是配置值还是实际请求目标、所对应时段 |
| 机器人群名/推送目标 | 业务表字段、设置表及配置 | 群名称、chat ID、用户 ID 各自字段语义 |
| 应用版本 | 代码版本常量、部署材料、后台模板/仪表盘 | 应用版本与框架/依赖版本分别核对 |

</details>

**3. 前缀和登录路由可以同时成立。** 构造例子里 `.env` 有 `CACHE_DRIVER=redis`，后台设置的前缀是 `/admin`，路由里的登录入口是 `/admin/auth/login`。可以记“后台根前缀为 `/admin`，登录路由为 `/admin/auth/login`”。二者不是互相排斥的结果。只看 URL 的名字，不能证明这个地址打得开。仿真请求后的跳转要留下状态码、Location 和最终页面。

这一步对上的是 `.env` 的实际路径，以及后台前缀和登录路由各自对应的文件。搜索范围内没有配置文件时，写明还查过哪里，不写成应用没有配置。只看到 URL 名称时，不写成页面已经能访问。表里每一行的配置键能在代码或设置表里找到读取位置。`/admin` 和 `/admin/auth/login` 没有被写成只能有一个。保存配置文件路径、受控目录里的敏感字段副本、路由和版本核对记录。

<details>
<summary>展开磁盘配置不一定等于历史生效配置</summary>

### 10.2 磁盘配置不一定等于历史生效配置

`.env`、`config/` 和配置缓存可能互相不一致。还不知道请求当时读的是哪一份。

**先读 `.env`，再读配置和缓存 → 不一致的字段单列 → 不要清缓存来抹平差异。**

**1. 三份配置按顺序读，谁也不先覆盖谁。** 先读 `.env`，再读 `config/` 和常见缓存文件 `bootstrap/cache/config.php`，最后和进程或容器环境比对。不一致的字段单独列出。

Laravel 启用配置缓存之后，请求过程不一定会重新读 `.env`。不要运行 `config:clear`，也不要重新缓存来消除差异，那会改变副本状态。代码版本、配置结构和缓存路径按目标部署确认。机制见 [Laravel 配置缓存](https://laravel.com/docs/12.x/configuration#configuration-caching)。

**2. PHP 配置先当文本。** 不要在分析机上 `include`、启动 Artisan，或把整个未知应用拉起来。框架代码和依赖的启动钩子可能还会做别的事。机器人访问不了外部 API 时，配置里的域名、群名或目标 ID 仍可以从卷文件和表记录里分析。不要让恢复环境向真实外部服务发消息。

**3. 版本和发信分开核对。** `composer.lock` 主要用于识别依赖版本。里面的 Laravel 版本不等于网站自己的版本。页面上的标识也可能被改过或被缓存。把部署文件、版本常量和历史页面或日志合在一起核对。只能看到后台显示时，就写“该页面显示的版本”。邮件设置记下的是发件人配置，不自动证明邮件已经发出。实际发送还要邮件日志、队列状态或邮件材料。

这一步对上的是 `.env`、`config/` 和 `bootstrap/cache/config.php` 里不一致的字段已经并列。没有进程环境或请求日志时，不写成历史请求用的就是磁盘上这一份。没有邮件日志时，不写成信已经发出。差异字段来自静态阅读，不是清缓存之后的新文件。`composer.lock` 里的框架版本没有被写成网站版本。保存三份配置的路径和不一致字段。页面上看到的版本单独注明来源。

</details>

<span id="11-实战从定制密码校验中复算派生参数"></span>

## 11 按定制校验复算口令派生参数

登录校验不在控制器这一行结束，下面还有 hasher，以及可能被改过的预处理。先把字节链读完，再决定复算到哪一步。

**先对上标准实现和定制改动 → 再按代码做最小复算 → 要进后台就转到网站重构。**

### 11.1 先确定标准实现与定制改动

控制器里能看到校验调用，还不知道口令在进 bcrypt 之前有没有被改写。不先读这条链，复算会对错对象。

**从调用往下追到 hasher → 按顺序列出字节怎么变 → 对上了才复算。**

**1. 从控制器的校验调用往下查认证服务和 hasher。** 常见实现在 `vendor/laravel/framework/src/Illuminate/Hashing/BcryptHasher.php`。还要查应用有没有注册其他驱动、加了包装函数，或改过依赖。

**2. 先保存哈希、版本、调用链和它读过的配置。** 按调用顺序列出：输入是什么字符串或字节，怎样派生或拼接，送进 bcrypt 还是哪种校验，最后返回什么布尔值。这条链确定之后再复算。

标准 bcrypt 的盐信息编码在保存的 hash 里。如果看到定制的 `getSalt()`、固定常量或 XOR 预处理，不能据此说所有 Laravel 站点都用这套算法。必须按当前应用的代码确认它作用在口令、盐、编码，还是别的参数上。常见校验接口见 [Laravel hashing](https://laravel.com/docs/12.x/hashing)。

这一步对上的是当前应用实际调用的 hasher 文件、版本，以及口令在比较前经过的步骤。只看到标准类名、没有读到定制包装时，不写成这个站点使用了固定盐或 XOR。调用顺序里写明了输入、派生、校验函数和返回的布尔值。文件哈希和代码对得上。保存 hasher 路径、文件哈希、调用链和配置读取点。

<details>
<summary>展开提炼最小的字节级复算</summary>

### 11.2 提炼最小的字节级复算

代码里的定制步骤已经读到：先取 SHA-256 原始二进制的前一段，再和掩码做 XOR，最后做 Base64。示例常量只说明算法，真实取值还得从已经核对的代码里拿。

**按代码的三步复算长度 → 再核对 XOR 的对象是字节 → 两种实现对不上就查长度和编码。**

**1. 构造示例先跑这三步，长度要对上。** 步骤是：SHA-256 原始二进制取前 16 字节，与一段 Base64 解码后的掩码做字符串 XOR，再把结果 Base64 编码。实际取值和截断规则都从已核对的代码取得。

```bash
python3 - <<'PY'
import base64
import hashlib

constant = b"lab-hash-input"
mask_b64 = "AAECAwQFBgcICQo="  # 讲解用的 11 字节掩码
digest_prefix = hashlib.sha256(constant).digest()[:16]
mask = base64.b64decode(mask_b64, validate=True)

# 对应 PHP 两个字符串进行 ^ 时的较短长度；不是补零到 16 字节
derived = bytes(left ^ right for left, right in zip(digest_prefix, mask))
print("digest_prefix_bytes:", len(digest_prefix))
print("mask_bytes:", len(mask))
print("derived_bytes:", len(derived))
print("derived_hex:", derived.hex())
print("derived_base64:", base64.b64encode(derived).decode("ascii"))
PY
```

先核对三步输出长度，依次应为 `16`、`11`、`11`。取原始摘要用 `.digest()`，不能改成 64 字符的 `.hexdigest()`。

**2. XOR 的两边必须是字节。** 不是整数值，也不是 Unicode 字符。PHP 代码如果有循环或补齐，就按它的步骤复算，不能固定取较短的那一边。字符串和长度规则对照实际代码及 [PHP 位运算](https://www.php.net/manual/en/language.operators.bitwise.php)。

**3. 只在隔离目录运行审过的纯算法。** 不加载未知依赖，也不连接业务库。分别记下原始常量、掩码的字节表示、编码、截断点、中间 hex、最终字节数和 Base64。再用目标语言的最小等价实现交叉比对。两种实现对不上时，先查字符串长度、严格 Base64 校验、二进制还是文本，以及拼接顺序。不要改证据值去凑预期输出。

这一步对上的是摘要前缀、掩码和 XOR 结果的字节数，以及最终 Base64。代码里还有补齐或循环、而示例用了较短长度时，以代码为准重算，不保留这个示例长度。用来核对的是输出长度依次是 `16`、`11`、`11`，并且用的是 `.digest()` 的原始字节。保存审过的最小脚本、中间 hex、两种实现对得上或对不上的差异点。

</details>

### 11.3 认证重构进入独立流程

字节链已经能复算，但如果要在副本里打开后台，登录、会话和缓存是另一套步骤。这里不要另起一个登录实验。

**先用未改的认证代码核对输入和结果 → 要展示后台就转入网站重构 → 实验登录单独记录。**

**1. 先不要改认证代码。** 用未修改的代码核对输入字节、派生值和校验结果。

**2. 需要在副本里看后台时，转到专门流程。** 认证、会话、缓存和数据库按[网站重构的认证与离线依赖流程](/knowledge/forensic-website-reconstruction/#06-找到后台后区分身份恢复与离线依赖障碍)处理。

【仅在副本/仿真/授权环境执行】实验登录和它带来的状态变化单独记录。登录成功只说明这个副本的当前流程走通了，不证明历史密码或历史权限。

这一步对上的是未修改代码下，输入字节、派生值和校验结果一致。没有按网站重构记录会话和缓存时，不写成后台业务已经恢复。用来核对的是校验结果来自原来的认证代码。副本上的实验登录另有时间和变更记录。保存输入字节、派生值、校验结果。若做了实验登录，附上变更和回滚记录。

<span id="12-实战按业务状态软删与日期口径统计记录"></span>

## 12 按业务状态和日期口径统计记录

库里有订单和机器人认证记录，要统计的是某个月的成功业务和金额。成功、删除、用哪个时间，还没定下来之前不要先出总数。

**先建立字段语义 → 再按约定的月份边界筛选 → 用构造数据核对哪些行不该进去。**

### 12.1 先建立字段语义表

业务库里有订单和机器人认证记录，需要统计某个月的成功业务和金额。先读 DDL、模型枚举、控制器和样本记录，明确什么叫成功、什么叫逻辑删除，以及该用哪个时间字段。

**先对上字段含义 → 再按这个示例的状态数字查询 → 人数、金额和空值分开算。**

**1. 每个统计对象先对上字段，再写 SQL。**

<details>
<summary>展开每个统计对象先对上字段，再写 SQL：字段表</summary>

| 判定对象 | 应核对的字段/代码 | 常见混淆 |
| --- | --- | --- |
| 认证成功 | `captcha_status`、`captcha_success_time` 与状态定义 | 发起验证不等于成功入群 |
| 已完成订单 | `status` 枚举、`actual_price` 等业务金额 | 支付发起、付款成功、发货完成可能是不同状态 |
| 删除口径 | `deleted_at`、SoftDeletes 或定制逻辑 | 是否排除软删须先确定统计目的 |
| 日期 | 成功时间、付款时间、更新时间和其时区 | `updated_at` 可能被后续维护改变 |
| 人数/记录数 | 用户标识、订单标识与重复记录 | `COUNT(*)` 不自动等于不同人数 |
| 金额单位 | DECIMAL 元、整数分、币种、退款 | 浮点、NULL、不同币种或退款会改变总额 |

</details>

**2. 下面的数字只属于这个构造应用。** 已经核对过：认证状态 `1` 是成功，订单状态 `4` 是已完成，`actual_price` 是同一币种的 DECIMAL 金额，未软删用 `deleted_at IS NULL`。SQL 在已恢复的隔离库或授权的只读连接上执行。这些数字不是所有业务的通用定义。

```sql
-- 示例：统计 2026 年 6 月成功的认证记录数；这不是自动去重后的人数
SELECT COUNT(*) AS successful_records
FROM bot.user_captcha_record
WHERE captcha_status = 1
  AND captcha_success_time >= '2026-06-01 00:00:00'
  AND captcha_success_time <  '2026-07-01 00:00:00';

-- 若该应用确实以 updated_at 表示所要求业务时间，且本统计排除软删
SELECT COUNT(*) AS completed_orders,
       COALESCE(SUM(actual_price), 0) AS completed_amount
FROM shop.orders
WHERE status = 4
  AND deleted_at IS NULL
  AND updated_at >= '2026-06-01 00:00:00'
  AND updated_at <  '2026-07-01 00:00:00';
```

**3. 先把“6 月内”“6 月起”“6 月之后”说清楚。** “6 月内”用左闭右开的月范围，避免漏掉带小数秒的月末。“6 月起”从 `6 月 1 日 00:00:00` 起，没有这个月的上界。“6 月之后”如果是指 7 月起，边界又不一样。数据库会话时区、字段是 TIMESTAMP 还是 DATETIME、应用怎么转换，都要记下。日期列里的 NULL 或无效值另列，不要自动算成范围外的已完成记录。

统计不同用户数时，核对稳定的用户 ID 之后再用 `COUNT(DISTINCT user_id)`，并列出重复和 NULL 的范围。认证库里的群名字段也要和关联表或配置对应。chat ID、用户 ID 和群名不是同一种值。状态已经是成功、但没有成功时间的记录单独看，不要把状态数字直接当成每项业务都完成了。

**4. 金额缺失不要被 0 盖住。** 示例用 `COALESCE(SUM(actual_price), 0)` 是为了能展示。不能用这个 0 抹掉金额缺失。汇总前先单列目标记录里金额为 NULL 的数量。“没有目标记录”“有记录但金额全未知”和“已知金额合计确为零”分开交付。只有业务口径已经允许时，才把没有记录显示成 0。

成功状态、软删条件和时间字段已经按这个应用的代码核对过，月份边界是左闭右开还是别的语义也已经写明。状态是成功但没有成功时间、金额为 NULL，或时区没确认时，这些行单独列出，不塞进总数。`COUNT(*)` 没有被写成人数。人数来自 `COUNT(DISTINCT user_id)`。`actual_price` 的币种和单位写在结果旁边。保存字段语义表、实际 SQL、纳入和排除的主键样本、NULL 金额的数量。

<details>
<summary>展开用可核对的构造数据验证筛选边界</summary>

### 12.2 用可核对的构造数据验证筛选边界

SQL 的月份边界容易把月初、月末、软删和未完成算错。下面用内存里的构造行检查筛选，不拿它代替真实库。

**在内存库插入边界行 → 看哪些 ID 入选 → 对上了再把同一口径用回实际查询。**

**1. 只在 Python 进程里新建 SQLite。** 示例金额用整数分，用来检查筛选和统计口径。它不验证实际 MySQL 的引擎、binlog 或恢复结果，也不读取或修改检材数据库。

```bash
python3 - <<'PY'
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("""CREATE TABLE orders (
    id INTEGER PRIMARY KEY, status INTEGER, actual_price INTEGER,
    updated_at TEXT, deleted_at TEXT)""")
db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", [
    (1, 4, 4990, "2026-06-01 00:00:00", None),
    (2, 4, 2000, "2026-05-31 23:59:59", None),
    (3, 4, 1000, "2026-06-02 10:00:00", "2026-06-03 10:00:00"),
    (4, 2, 3000, "2026-06-02 10:00:00", None),
    (5, 4, 5010, "2026-06-30 23:59:59", None),
    (6, 4, 7000, "2026-07-01 00:00:00", None),
])
rows = db.execute("""SELECT id, actual_price FROM orders
    WHERE status = 4 AND deleted_at IS NULL
      AND updated_at >= ? AND updated_at < ? ORDER BY id""",
    ("2026-06-01 00:00:00", "2026-07-01 00:00:00")).fetchall()
total_minor = sum(price for _, price in rows)
print("included_ids:", [record_id for record_id, _ in rows])
print("count:", len(rows))
print("total_minor:", total_minor)
print("total_major:", f"{total_minor // 100}.{total_minor % 100:02d}")
assert rows == [(1, 4990), (5, 5010)]
assert total_minor == 10000
db.close()
PY
```

**2. 先看预期输出，再解释每一行为什么在里面或不在。** 入选 ID 为 `[1, 5]`，记录数 `2`，金额 `10000` 分，也就是 `100.00` 元。ID 2 在月界之前，ID 6 刚好在下月起点，ID 3 被软删，ID 4 没到完成状态。逐行解释之后再核对总数和总额。实际查询要同时导出纳入和排除的主键样本，避免只交一个数字。

**3. 当前表里已经看不到的行，不要靠这次查询补回来。** 要统计被硬删的历史交易，先定目标时刻和恢复范围，再查同一时点的备份和 binlog。当前表的查询覆盖不了已经消失的行。

binlog 里找到候选之后，先核对事务有没有提交、业务状态、币种、退款和重复范围，再决定是否纳入这个历史口径。不要把历史候选直接加进当前交易总数。

这一步对上的是构造数据里入选的是 ID 1 和 5，金额是 10000 分。硬删的历史行不在当前表里。没有备份或 binlog 时，不把当前总数写成历史总数。用来核对的是输出是 `[1, 5]`、`2`、`10000` 和 `100.00`。月界前后、软删和未完成各有一行被排除的理由。保存构造脚本的输出，以及实际查询导出的纳入、排除主键。

</details>

<span id="13-实战从-vsftpd-名单到认证与传输证据"></span>

## 13 从 vsftpd 名单核对认证和传输

镜像里有 FTP 配置、账户名单和轮转日志。名单上有一个名字，还不等于这个账户登录过，也不等于文件已经传完。

**先只读定位配置 → 再分开 chroot 名单和登录控制 → 用日志区分认证成功和传输成功。**

### 13.1 首轮保全与只读配置定位

一份 Linux 服务器镜像里有 FTP 配置、账户名单和轮转日志。要分清哪些名字只是配置候选、哪些账户在某一时段认证成功、哪些文件确实传完。先固定镜像和分区身份、配置版本、账户材料、日志时间范围和哈希。不要靠连接真实 FTP、试登录、重启服务或改配置来验证历史行为。

**先只读挂上已确认的分区 → 再按启动参数找配置文件 → 对上实体以后才解释指令。**

**1. 只在分析机上挂已经确认格式的 RAW 工作副本。** 先确认格式、扇区大小和分区布局。E01、LVM、RAID、加密卷和其他文件系统走各自的访问路线，不能套这个 ext4 示例。挂载点应为空且没被占用。先保全原件，输出放在分析机的工作目录。

```bash
sha256sum ./work/server.dd
FTP_LOOP=$(sudo losetup --find --show --read-only --partscan ./work/server.dd)
lsblk -o NAME,TYPE,FSTYPE,SIZE,RO,MOUNTPOINTS "$FTP_LOOP"
# 仅当上步实际返回 /dev/loop3，且已确认第 2 分区为目标 ext4 时使用下一行
sudo mount -t ext4 -o ro,noload /dev/loop3p2 /mnt/evidence
findmnt --mountpoint /mnt/evidence -no SOURCE,TARGET,FSTYPE,OPTIONS
```

先核对块设备和挂载结果，再读配置。`--read-only` 限制镜像对应块设备的写入。`--partscan` 解析分区。镜像不是默认扇区大小时，按已经记录的值指定。

ext4 只用 `ro` 仍可能回放日志，所以示例再加 `noload`。跳过回放可能让目录或文件视图不一致。保存错误，另建恢复件处理。

看 `findmnt --mountpoint`：必须确认 SOURCE 是目标分区，OPTIONS 里有 `ro`。没有结果就停止把这个目录当检材，先查挂载是否成立。参数见 [losetup 官方手册](https://github.com/util-linux/util-linux/blob/master/sys-utils/losetup.8.adoc)、[findmnt 官方手册](https://github.com/util-linux/util-linux/blob/master/misc-utils/findmnt.8.adoc)和 [ext4 官方挂载说明](https://cdn.kernel.org/doc/html/latest/admin-guide/ext4.html)。

**2. 挂载确认之后，再找 vsftpd 实际用的配置。**

```bash
FTP_ROOT=/mnt/evidence
find "$FTP_ROOT/etc" -maxdepth 3 -name '*vsftpd*' -print
ls -ld "$FTP_ROOT/etc/vsftpd.conf" "$FTP_ROOT/etc/vsftpd/vsftpd.conf"
rg -n 'vsftpd|ExecStart|Environment' "$FTP_ROOT/etc/systemd/system" "$FTP_ROOT/usr/lib/systemd/system"
```

常见入口是 `/etc/vsftpd.conf` 或 `/etc/vsftpd/vsftpd.conf`。启动参数可以指定另一个文件，多实例也可能各用一份。先核对服务单元、覆盖片段、inetd/xinetd 材料和已经取得的进程记录，再确定历史时段对应的是哪一份。前者是上游默认入口，后者见 [Red Hat 服务说明](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/10/html/securing_networks/securing-network-services)。当前磁盘上的配置不能自动代表旧日志时段的生效值。

**3. 读之前先看是不是软链。** 绝对链接 `/etc/...` 或 `/var/log/...` 要重定位到 `$FTP_ROOT` 里的实体。相对链接按检材内的目录解析，不要顺着链接去读分析机上的同名文件。下面假定已经确认实际实体是检材内的 `etc/vsftpd/vsftpd.conf`。真实路径不同就替换，并保留文件全文和哈希。搜索只是定位。

```bash
FTP_CONF="$FTP_ROOT/etc/vsftpd/vsftpd.conf"
sha256sum "$FTP_CONF"
rg -n '^(local_enable|anonymous_enable|chroot_local_user|chroot_list_enable|chroot_list_file|userlist_enable|userlist_deny|userlist_file|pam_service_name|guest_enable|guest_username|virtual_use_local_privs|user_config_dir|local_root|xferlog_enable|xferlog_std_format|dual_log_enable|vsftpd_log_file|xferlog_file|syslog_enable|log_ftp_protocol|session_support)=' "$FTP_CONF"
```

配置里没有某一行时，按目标软件包版本的手册或实现确认编译默认值。不要把“没有这一行”一律解释成 NO。重复指令、未知参数、权限问题或名单读不了，都可能影响启动。不要为了消除异常去整理检材配置。

镜像哈希、只读挂载的 SOURCE，以及实际读到的 vsftpd 配置实体。`findmnt --mountpoint` 没有结果，或配置是软链且目标还没落到 `$FTP_ROOT` 内时，先停下，不解释指令。用来核对的是 OPTIONS 里有 `ro`，并且用了 `noload`。配置哈希来自 `etc/vsftpd/vsftpd.conf` 或现场替换后的实际路径。保存镜像哈希、losetup 和 findmnt 输出、配置全文和哈希。

<details>
<summary>展开 chroot 名单、登录控制与账户来源分别判读</summary>

### 13.2 chroot 名单、登录控制与账户来源分别判读

配置里有一份名单。它可能只决定登录后关在哪个目录里，不是已经登录过的人，也不是谁可以登录。

**先按两个开关读 chroot 表 → 再分开 userlist 和 PAM → 对上了才填候选账户那一行。**

**1. `chroot_list_file` 是目录隔离名单。** 它不是已登录账户名单，也不是通用登录白名单。下面针对普通本地用户、已经生效的配置，并且没有其他覆盖。表里的“默认隔离”对应 `chroot_local_user`，“启用名单”对应 `chroot_list_enable`。

| 默认隔离 | 启用名单 | 名单与隔离的关系 |
| --- | --- | --- |
| NO | NO | 这两个选项不把本地用户放入 chroot；名单未启用 |
| NO | YES | 名单内用户登录后被 chroot；不表示这些用户一定能够认证 |
| YES | NO | 本地用户默认被 chroot；名单未启用 |
| YES | YES | 名单内用户是**不被 chroot 的例外**，名单外用户默认被 chroot |

因此，在 `chroot_local_user=YES` 和 `chroot_list_enable=YES` 下看到 `acct_a`，应记“隔离例外名单包含该名称”。不能写“该账户曾登录”或“只有该账户能登录”。`userlist_enable=YES` 时，`userlist_deny=YES` 拒绝名单内的名称；`userlist_deny=NO` 只让名单内的名称继续进入后面的认证检查。`userlist_enable=NO` 时，这份列表的控制没有启用。依据见 [vsftpd 官方配置手册](https://security.appspot.com/vsftpd/vsftpd_conf.html)。

**2. 路径已经核对，再读名单和 passwd。** 例如配置已经写明 `chroot_list_file=/etc/vsftpd/chroot_list`，软链和实体也核对完，可以从只读挂载读完整名单。其他取值按实际路径重定位。名单没启用时仍可保全残留，但不赋予“当时生效”的含义。

```bash
FTP_CHROOT_LIST="$FTP_ROOT/etc/vsftpd/chroot_list"
sha256sum "$FTP_CHROOT_LIST"
cat -- "$FTP_CHROOT_LIST"
awk -F: '{print $1, $3, $4, $6, $7}' "$FTP_ROOT/etc/passwd"
```

**3. 账户来源继续分开。** 本地账户可以和 `/etc/passwd` 的 UID、主目录及 PAM 规则对应。非匿名登录还受 `local_enable` 等条件控制。虚拟账户可能由 PAM 引用的用户数据库或其他认证后端验证，并映射到 `guest_username` 对应的本地身份。不能因为 passwd 里没有原来的登录名就排除。按照 `pam_service_name` 找实际的 `/etc/pam.d/<服务名>`，沿 include、substack、模块参数和引用文件读下去。名单里的名称也可能过期，或只是配置残留。local、guest 和 PAM 的语义见 [Debian 发布的 vsftpd.conf 手册](https://manpages.debian.org/trixie/vsftpd/vsftpd.conf.5.en.html)。

为每个候选填一行：`名单来源 / 登录名称 / 账户类型 / UID或映射身份 / 配置时段 / chroot策略 / userlist结果 / PAM与账户状态 / 认证证据`。

先读名单和配置，再核对用户配置覆盖、锁定状态、文件权限和其他限制。userlist 没有拒绝，只说明这一项通过了，不等于完整登录许可。口令、哈希和认证数据库保全但不公开，不发送真实认证请求。

这一步对上的是 chroot 两个开关的组合，以及 `acct_a` 在例外名单里的含义。没有认证日志时，不写成该名称登录过。userlist 没拒绝时，也不写成已经允许登录。一行候选里同时有名单来源、userlist 结果和 PAM 状态。`chroot_list_enable=YES` 没有被写成登录白名单。保存名单全文和哈希、passwd 摘要、实际的 pam.d 文件。

</details>

<details>
<summary>展开按日志模式查完整时段</summary>

### 13.3 按日志模式查完整时段

配置里的日志开关还没对上文件。只按文件名去搜，会把没启用的 `vsftpd.log` 当成“没有登录”。

**先从配置确定格式和目的地 → 再对实体文件做哈希和检索 → 轮转和 syslog 都算进时段。**

**1. 先看配置把日志写到哪里。** `xferlog_enable=YES` 且 `xferlog_std_format=NO` 时，通常写原生 vsftpd 日志，路径由 `vsftpd_log_file` 定义。标准格式启用时看 `xferlog_file` 所指的传输日志。`dual_log_enable=YES` 可以同时有原生和标准传输日志。`syslog_enable=YES` 把原生输出交给 FTPD facility 的系统日志，未必还有独立的 `vsftpd.log`。`log_ftp_protocol` 可以提供命令和响应，但受日志格式条件影响，不能假定它一直都在。组合见 [vsftpd 日志参数](https://manpages.debian.org/trixie/vsftpd/vsftpd.conf.5.en.html#vsftpd_log_file)。

```bash
find "$FTP_ROOT/var/log" -maxdepth 2 -type f \( -name 'vsftpd.log*' -o -name 'xferlog*' -o -name 'auth.log*' -o -name 'secure*' -o -name 'syslog*' -o -name 'messages*' \) -print
# 路径已确认且为普通文件时，分别保留当前与轮转日志的摘要
sha256sum "$FTP_ROOT/var/log/vsftpd.log" "$FTP_ROOT/var/log/vsftpd.log.1"
rg -n 'CONNECT|OK LOGIN|FAIL LOGIN|OK (UPLOAD|DOWNLOAD)|FAIL (UPLOAD|DOWNLOAD)' "$FTP_ROOT/var/log/vsftpd.log" "$FTP_ROOT/var/log/vsftpd.log.1"
```

**2. `.1` 只是轮转候选，不是“最新”的保证。** 一并检查 `.2.gz`、按日期命名的文件、logrotate 配置、外置日志目录、rsyslog 路由和已经采集的 journal。压缩文件在分析工作区读取或解压，保留压缩原件的哈希和输出对应关系。没有独立日志时，按实际的 syslog 或 journal 配置去找，不要立刻认定没有登录。

每份日志记下首末时间、缺年、缺时区、截断、轮转交叠、大小和读取范围。按原始条目定位。双日志里的同一次传输不要数两次。`wtmp` 只作补充。会不会写入，还取决于 `session_support`、PAM 编译和部署。

这一步对上的是配置里的日志格式、目的地，以及实际读到的当前日志和 `.1`。独立的 `vsftpd.log` 不存在时，写明还查了 syslog、journal 和哪些轮转名。没查到，只说明这些文件里没有。`xferlog_enable`、`syslog_enable` 和实际文件路径写在同一条记录里。同一传输没有在双日志里计两次。保存日志实体哈希、首末时间、读取范围和轮转配置。

</details>

<details>
<summary>展开构造日志的正反例与输出边界</summary>

### 13.4 构造日志的正反例与输出边界

下面是教学用的模拟日志，不是某次真实传输的结果。要分清连接、登录失败、登录成功和上传成功各能证明什么。

**先按动作和结果读样例 → 再对照证据层级表 → 输出时把四类事件分开。**

**1. 样例是模拟的原生格式，传输速度字段省略了。** 账号、地址、时间和文件名都是占位，不能当成真实结果。原生日志里的 `OK/FAIL` 和 `LOGIN/UPLOAD/DOWNLOAD` 是不同的动作和结果。格式可对照 [vsftpd logging.c](https://sources.debian.org/src/vsftpd/3.0.5-0.2/logging.c/)。

```text
Wed Jul  1 09:00:00 2026 [pid 2101] CONNECT: Client "192.0.2.10"
Wed Jul  1 09:00:02 2026 [pid 2101] [acct_a] FAIL LOGIN: Client "192.0.2.10"
Wed Jul  1 09:01:00 2026 [pid 2110] [acct_a] OK LOGIN: Client "192.0.2.10"
Wed Jul  1 09:01:10 2026 [pid 2111] [acct_a] FAIL UPLOAD: Client "192.0.2.10", "/incoming/sample.bin", 1024 bytes
Wed Jul  1 09:02:00 2026 [pid 2111] [acct_a] OK UPLOAD: Client "192.0.2.10", "/incoming/sample.bin", 4096 bytes
Wed Jul  1 09:05:00 2026 [pid 2140] [acct_b] OK LOGIN: Client "198.51.100.20"
```

| 证据层级 | 示例能支持的结论 | 还不能证明 |
| --- | --- | --- |
| 账户候选 | 配置名单出现某名称，能作为查认证记录的入口 | 该名称仍有效、允许完整登录或曾登录 |
| 配置许可 | 该时段 userlist/PAM/账户条件中已核对的规则允许继续认证 | 口令已通过、会话已建立 |
| 认证成功 | `acct_a` 在 09:01 的原生日志中出现 `OK LOGIN`；先前 `FAIL LOGIN` 不计成功 | 此名称对应哪位自然人、上传或下载已发生 |
| 传输成功 | 09:02 的 `OK UPLOAD` 记录一次服务器判定成功的上传与字节数 | 文件内容与当前同路径实体完全相同、其他终端已收到/使用它 |

**2. 连接和失败上传都不是传输成功。** `CONNECT` 只说明连接到达了。失败上传即使写了字节数，也不是完整成功。`acct_b` 只见 `OK LOGIN`，应报告认证记录，而不是传输记录。标准 xferlog 按目标版本的字段布局解析方向、登录类型、账户、路径、字节数和完成状态，不能沿用原生的 `OK LOGIN` 关键词去筛。目录列表、一次 RETR 或 STOR 请求、初始响应，都不能单独代替传输完成。要关联同一会话后面的结果和文件实体。

`acct_a` 在样例 09:01 的 `OK LOGIN` 之前还有 `FAIL LOGIN`。失败那条不计成功。表里这一层只支持认证成功，不支持“已经上传”。

**3. 先按时间、客户端地址、账户和已经取得的控制会话关联，再看进程。** 连接、认证、传输可能由不同的父子进程记录。PID 还会复用。不要强求 PID 相同，也不要把同一个 IP 当成同一个人。

上传路径先按当时的 chroot 或 local_root 解析到真实目录和数据卷。再比历史快照、尺寸、哈希和独立的传输材料，确认内容。当前的同名文件可能已经被覆盖。

分四份输出：候选账户集合、配置判读、成功认证事件、成功传输事件。每条附上 `日志实体路径 / 行号或偏移 / 原始时间与时区 / 动作 / 结果 / 登录名称 / 来源地址 / PID / 文件路径与字节数 / 关联依据`，让记录能回到原日志。

唯一账户数和成功次数分开算。失败、匿名、映射账户、重复日志分别标出。时间比较先保留原值和时区，再统一展示。有冲突时不覆盖原记录，按材料来源和事件上下文核对。

没覆盖到的轮转时段、未知的配置版本、缺卷、缺原文件、未知的时间基准，列为缺口。没有命中，只说明在已经取得并且已经读过的范围内没发现。

这一步对上的是样例里 `acct_a` 的 `FAIL LOGIN`、`OK LOGIN` 和 `OK UPLOAD` 已经分成三件事。`acct_b` 只有 `OK LOGIN` 时，不补一条传输。`CONNECT` 不写成登录或上传。四份输出各自能回到日志行。标准 xferlog 没有用原生 `OK LOGIN` 去筛。保存原始日志行、关联依据，以及没覆盖的时段和缺卷说明。

</details>

## 14 SSH与远程访问取证

主机已经从[Linux 系统与服务识别](/knowledge/fic-case-03/#051-ssh与远程访问取证)对上，远程访问还没拆开。账户、进程、监听和认证日志现在还不能互相代替。

**先保存只读状态 → 再对应账户、sshd 和实际监听 → 最后查认证与会话日志。**

**1. 进程和端口用来确认入口。** 账户锁定和口令字段用来解释认证。sudo 和 journal 用来追会话之后的操作。计划任务用来查持久化。下面几节分别展开这些证据，不另写一篇同义文章。

**2. 原始服务器检材优先只读。** 先保存镜像哈希、磁盘或快照标识、时间和时区，再清点这些材料：

- 网络：IP、路由、监听端口和防火墙状态。
- 运行：进程、服务及 socket 单元。
- 认证：sshd 配置及 Include、账户、authorized_keys。
- 历史：认证、会话及相关服务日志。

活体查询、sudo、远程登录和仿真启动也可能产生日志、触发任务或改状态。每次操作记下环境、时间和原样输出，让新痕迹能和原记录分开。

**3. 会改状态的操作只放在副本里。** 【仅在副本/仿真/授权环境执行】安装组件、修改 SSH 配置、修改账户、密码或密钥、启动或重启服务、设置开机启动、调整网络和访问规则，都会改变状态。原始检材不能直接改。修改前保存完整配置链，以及权限、所有者和哈希，并建立可回退的快照。修改后记下操作时间、改了哪些文件、差异、命令、验证和回滚结果。不要为了“方便连接”去改原始证据。实验产生的登录、命令和日志与历史证据分开保存。

这一步对上的是镜像或快照标识、时间与时区，以及网络、运行、认证、历史四类材料各查到哪一步。只有进程或只有配置时，不写成登录已经成功。实验里新产生的日志要和历史记录分开。每项材料注明是历史保全还是这次操作新产生的。原始检材的配置哈希在修改前已经留下。保存镜像哈希、时间与时区、四类清点结果。若在副本里改过，附上差异和回滚记录。

先按要回答的问题展开一节，不必把后面的命令全跑一遍：

- 装的是客户端还是 sshd：看包名，以及 `systemctl status ssh` 或 `systemctl status sshd`。
- 端口通不通：看 `ss -lntp` 里的 22，或配置里写的实际端口。
- 允许哪种登录：读 `/etc/ssh/sshd_config` 和 `sshd_config.d`。
- 账户和密钥：对 passwd、shadow 和 `authorized_keys`。
- 这次登录成没成：查 `journalctl -u ssh`、`/var/log/auth.log` 或 `/var/log/secure`。
- FinalShell 连不上、只有失败记录，或要把失败和入侵分开：按现象打开后面的排障、爆破、入侵和速查。

<details>
<summary>展开 SSH/OpenSSH基础</summary>

### 14.1 SSH/OpenSSH基础

客户端能连上，还不说明本机装的是哪一种 SSH，也不说明 FinalShell 里填的账户是 Linux 账户。先把协议、程序和账户体系分开。

**先对上表里的名称 → 再核对包是客户端还是服务端 → 最后确认登录用的是哪一套账户。**

| 名称 | 含义 | 取证时对应什么 |
| --- | --- | --- |
| SSH | Secure Shell 协议，提供加密的远程登录、命令执行及文件传输等能力 | 网络协议，不是账户、软件包或固定端口 |
| OpenSSH | Linux 中最常见的 SSH 协议实现 | 核对具体版本、安装方式与发行版构建；也可能有其他实现 |
| `sshd` | OpenSSH 服务器守护进程，接受 SSH 连接并处理认证与会话 | 服务器程序、子进程、启动参数及监听；可能由 socket 按需激活 |
| `ssh` | OpenSSH 客户端命令 | 当前主机连接别的服务器，不代表本机提供 SSH 服务 |
| FinalShell | 图形化 SSH/SFTP 客户端 | 连接 Linux 的终端与文件传输工具，不是服务器账户管理系统 |
| `openssh-client` / `openssh-clients` | 客户端组件；前者常见于 Debian/Ubuntu，后者常见于 RHEL 系 | 仅有客户端包不能证明本机可接受远程连接 |
| `openssh-server` | 服务器组件，包含 sshd 及相应部署材料 | 安装记录仍须与服务、监听和日志互证 |

包名和客户端、服务端配置的区别见 [RHEL OpenSSH 说明](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/securing_networks/index)。FinalShell 的产品定位见 [官方说明](https://www.hostbuf.com/t/988.html)。

**FinalShell 登录使用的是 Linux 账户。** **Linux root ≠ MySQL root ≠ 宝塔账户 ≠ 网站后台账户。**数据库账户、面板账户和网站账户各有自己的认证。同名，甚至口令也设成一样，也不会因此变成同一个账户。Linux 身份还可能由 NSS、LDAP 等目录服务提供，不只来自本地的 passwd 和 shadow。

这一步对上的是目标上的是协议、OpenSSH 程序，还是仅仅一个客户端包；登录名属于哪一套账户。只有 `openssh-client` 或 `openssh-clients` 时，不写成这台机器能接受远程连接。还要有 `openssh-server`、服务和监听互相印证。`sshd` 和 `ssh` 没有被写成同一个程序。FinalShell 没有被写成服务器上的账户管理系统。保存包名、版本，以及账户所属体系的说明。

</details>

<details>
<summary>展开 sshd服务与进程</summary>

### 14.2 sshd服务与进程

要确认这台机器能不能接受 SSH。包查询、单元、进程和端口现在还是四件不同的事。查不到 sshd 进程，也不等于 SSH 不可用。

**先查目标自己的安装记录 → 再分开单元、进程和监听 → socket 激活时继续读 ListenStream。**

**1. 运行现场先确认控制台属于目标，再查包。** 离线镜像改读检材里的软件包数据库。Debian 系要明确指定检材的 dpkg 数据库目录。RHEL 系读目标的包数据库。不要把分析机的默认查询结果填进服务器清单。

```bash
# Debian / Ubuntu：同时核对包名、安装状态、版本
dpkg -l | grep openssh
# CentOS / RHEL / Rocky / AlmaLinux
rpm -qa | grep openssh
```

只发现 `openssh-client` 或 `openssh-clients`，表示有客户端组件记录，不代表能够接受 FinalShell 登录。还要排查手工安装、容器或其他 SSH 实现。不要因为包查询没命中就认定没有 SSH。

**2. 安装示例只在副本里做，而且只选一种包管理器。** 【仅在副本/仿真/授权环境执行】先保存快照和包基线。下面按实际发行版择一，不要全部执行。安装可能产生服务、主机密钥和自动启动。这些新增痕迹单独列出。

```bash
# Ubuntu / Debian
sudo apt install openssh-server
# CentOS / RHEL 系旧环境
sudo yum install openssh-server
# 使用 dnf 的 RHEL / Rocky / AlmaLinux 等环境
sudo dnf install openssh-server
```

**3. 单元、enabled、进程、监听分四项记。** `systemctl` 查询或控制的是 systemd 单元。`ps` 和 `pgrep` 查询的是实际进程。四项不能互相代替。下面按目标发行版选命令。在仿真副本里执行时，结果注明仿真时点，不写成历史状态。

```bash
# Ubuntu / Debian 常见服务名
systemctl status ssh --no-pager --full
# CentOS / RHEL 系常见服务名
systemctl status sshd --no-pager --full
ps -ef | grep '[s]shd'
pgrep -a sshd

# 服务别名、socket 激活与覆盖配置也要保存
systemctl list-unit-files --type=service --no-pager | grep -E 'ssh|sshd'
systemctl list-unit-files --type=socket --no-pager | grep -E 'ssh|sshd'
systemctl list-sockets --all --no-pager
```

清单确认之后再设置实际单元名。示例是 `ssh.service`。RHEL 系按现场替换。保存执行文件的可信来源和版本。不要执行从检材导出的未知程序。

```bash
SSH_UNIT=ssh.service
systemctl cat "$SSH_UNIT"
systemctl show "$SSH_UNIT" -p Names -p FragmentPath -p DropInPaths \
  -p ExecStart -p MainPID -p ActiveState -p SubState
# 仅当发现 ssh.socket 时读取其 ListenStream 和覆盖片段
systemctl cat ssh.socket
```

先读 `cat` 的主单元和覆盖片段，再读 `show` 的服务管理器属性。这些是当前配置或当前属性，不直接证明历史加载过的值。

**4. Ubuntu 部分版本使用 socket activation（socket 激活）。** 不是查不到 sshd 就判定 SSH 不可用。监听进程可能是 systemd 或 PID 1，sshd 要等连接来了才启动。继续核对 socket 的 `ListenStream`、它触发的服务、生成器、覆盖配置和实际监听。只重启 ssh.service，不一定会改变 socket 的端口。

版本差异见 [Ubuntu socket 激活说明](https://discourse.ubuntu.com/t/sshd-now-uses-socket-based-activation-ubuntu-22-10-and-later/30189/1)。属性见 [systemctl 手册](https://github.com/systemd/systemd/blob/main/man/systemctl.xml)。不是 systemd、跑在容器里，或自定义启动的，按实际管理机制记录。

`systemctl status` 的 Loaded、Active 和退出状态一起保存。未安装单元、inactive、failed，以及没有服务管理器，不是同一个结果。`pgrep -a sshd` 没命中，只说明当前可见的进程集合里没有匹配项。先看退出状态、权限和会话归属，再走 socket 和监听这一支。不要为了让两条查询都出现 sshd，而重复安装或启动服务。

**5. 启动、重启、enable 各是独立操作。** 【仅在副本/仿真/授权环境执行】下面每一行按已经确认的服务名和目的择一。启动产生的是运行态。重启可能中断访问。`enable` 改变的是开机启动配置，不等于立刻启动。改完配置之后的重启，必须先过第 14.4 节的语法门禁。保留控制台或快照回退，不要依赖唯一的 SSH 会话自救。

```bash
# Ubuntu / Debian
sudo systemctl start ssh
sudo systemctl restart ssh
sudo systemctl enable ssh
# CentOS / RHEL 系
sudo systemctl start sshd
sudo systemctl restart sshd
sudo systemctl enable sshd
```

包名来自目标的包数据库；单元名、`cat` 和 `show` 的属性、进程查询结果已经分开。只有客户端包，或 `pgrep -a sshd` 为空时，写明还查了 socket 和 `ListenStream`。不要写成 SSH 不可用，也不要写成服务历史上在运行。用来核对的是 `ssh.service` 或现场替换后的单元名，和 `systemctl status` 的退出状态在同一条记录里。仿真输出标明了时点。保存包查询、单元文件、show 属性、进程和 socket 清单。副本里的安装或启动另记快照。

</details>

<details>
<summary>展开 SSH端口与网络</summary>

### 14.3 SSH端口与网络

SSH 不一定在 22。客户端 ping 得通，也不等于端口开着，更不等于能登录。先把地址、端口和访问控制拆开。

**先读目标和路由 → 再测已经确认的端口 → 对上监听地址和防火墙之后才解释连不上。**

**1. 服务器的 IP 和路由从目标控制台读。** 仿真 IP 可以和历史地址不同。

```bash
ip a
hostname -I
ip route
```

`ip a` 看接口、IP 和链路状态。`hostname -I` 快速列出本机地址，可能包含多个接口或容器地址，不会自动决定客户端该连哪一个。`ip route` 看路由、默认网关和下一跳。可以按实际地址族继续核对 IPv6 路由。先确认目标属于宿主机、虚拟机，还是容器的网络空间。

**2. 客户端测试只打已经确认的副本或授权端点。** 下面的文档地址是示例，换成真实目标和实际的外部 SSH 端口。

```bash
ping -c 4 192.0.2.20
```

```powershell
# Windows PowerShell；先核对实际 SSH 端口，不默认永远为 22
ping 192.0.2.20
Test-NetConnection 192.0.2.20 -Port 22
Test-NetConnection 192.0.2.20 -Port 27692
```

`ping` 测的是 ICMP。`Test-NetConnection -Port` 的 `TcpTestSucceeded` 测的是指定 TCP 端点，不是 SSH 协议，也不是登录验收。**ping 不通 ≠ SSH 一定不通；ping 通 ≠ SSH 一定可登录。** ICMP 可以被单独禁止。端口、服务、监听、防火墙、认证和账户限制仍要核对。字段依据见 [Microsoft TCP 连通测试说明](https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection?view=windowsserver2025-ps)。

**3. 监听和实际端口分开看。** SSH 不一定使用 22。先保存完整输出，再过滤，避免 grep 结果丢掉上下文。

```bash
ss -lntp
# 进程名过滤只是辅助；权限不足或 socket 激活可能不显示 sshd
ss -lntp | grep ssh
# 原有快速写法可能误匹配 :2222；下面给出精确端口边界
ss -lntp | grep ':22'
ss -lntp | grep -E ':(22|27692)([[:space:]]|$)'
# 仅在旧系统已存在 netstat 时使用，不为分析在原始检材安装
netstat -lntp | grep ssh
```

`ss -lntp` 和 `netstat -lntp` 看的是监听中的 TCP socket，以及可见的关联进程。不是服务器的全部进程、全部服务或全部 UDP 端口。PID 信息受权限影响。参见 [ss 参数手册](https://man7.org/linux/man-pages/man8/ss.8.html)。

| 监听例子 | 地址含义 | 远程访问判读 |
| --- | --- | --- |
| `0.0.0.0:22` | IPv4 通配地址 | 监听所有可用 IPv4 接口；仍受路由与访问规则约束 |
| `[::]:22` | IPv6 通配地址 | 不保证同时接受 IPv4，须核对 socket 的双栈/IPv6-only 行为 |
| `127.0.0.1:22` / `[::1]:22` | 回环地址 | 另一主机不能直接连接；已有代理/隧道是另一条路径 |
| `192.168.1.10:22` | 指定本地地址 | 核对该地址确实属于目标接口，以及客户端到它的路径 |
| `0.0.0.0:27692 ... sshd` | 自定义监听候选 | 在进程身份与配置互证后记录本地 SSH 端口为 27692 |

先确认客户端走的是直连还是端口映射。最后一例如果没有映射，FinalShell 填服务器 IP 和 `27692`，不是默认的 22。有 NAT 或转发时，填外部映射端口。它可能和 sshd 的本地监听端口不同。

按 **IP → 端口 → PID → 进程名及执行路径 → 配置文件** 逐项对应。只有端口号或进程显示名，还不能确认协议身份。要定位配置时，按第 14.4 节读实际启动所用的文件。

**4. 防火墙按实际安装的组件读，不要先关掉。**

```bash
# Ubuntu 常见 UFW
sudo ufw status
# RHEL 系常见 firewalld；省略 --zone 时通常只查询默认 zone
firewall-cmd --list-services
firewall-cmd --list-ports
firewall-cmd --get-active-zones
firewall-cmd --list-all-zones
firewall-cmd --permanent --list-all-zones
# 目标采用的规则后端；同一规则可能通过多个前端显示
sudo iptables -S
sudo iptables -t nat -S
sudo nft list ruleset
# SELinux 状态与被登记的 SSH 端口；工具缺失时记录缺口
getenforce
sudo semanage port -l | grep ssh_port_t
```

firewalld 要确认入口接口或来源实际匹配哪个 zone。当前运行规则和永久配置分别保存。默认 zone 里有 `ssh`，不代表自定义端口已经放行。iptables 和 nftables 的前端和后端可能对应同一套规则，不要把重复显示当成两套独立证据。查询含义见 [firewall-cmd 手册](https://firewalld.org/documentation/man-pages/firewall-cmd.html)。

同时核对 SELinux 的拒绝和端口标签、云服务器安全组、网络 ACL、宿主机防火墙、宝塔防火墙、Fail2ban、NAT 和路由。限制可能不在检材系统里面。sshd 或服务正常、正确的地址和端口也在监听、客户端仍然超时，就优先逐段查网络路径和访问控制。但超时不能单独证明是哪一层丢掉的。旧系统可以检查 `/etc/hosts.allow` 和 `/etc/hosts.deny`。上游 OpenSSH 从 6.7 起移除了 TCP Wrappers 和 libwrap。只有这两个文件，不证明当前 sshd 还在用它们。要核对目标构建或额外的包装层。见 [OpenSSH 6.7 说明](https://www.openssh.org/txt/release-6.7)。

**5. 虚拟化先保存网卡模式，再决定是不是网络问题。** VMware、VirtualBox、Hyper-V 和取证仿真，先保存虚拟网卡模式、虚拟交换机或 VMnet、IP 和路由。VMware 核对 `Connected` 和 `Connect at power on`。界面名称按产品和版本核对，不要把其他产品称作 VMnet。

**6. 旧的网络重启命令不是每个发行版都有。** 先看目标实际用的是 NetworkManager、systemd-networkd，还是旧的 network 服务，并对应它的连接配置、单元和启动日志。某些旧的 RHEL 系使用 `network.service`。其他系统可能根本没有这个单元。`systemctl restart network` 失败，不等于网卡损坏。离线分析只读相应配置，不要用分析机上的服务代替目标。

【仅在副本/仿真/授权环境执行】更改 IP 或重启网络会断开当前 SSH 会话，也会改变地址、路由和日志。确需恢复连接时，先保存旧配置，并留好虚拟机控制台。在副本上采用已经确认的网络管理方式。不要依次重启多个网络管理器。恢复后重新核对 IP、路由和目标 TCP 端口，不要只看 ping。

| 模式 | 主要核对 | 判断边界 |
| --- | --- | --- |
| NAT | 客户端是否处于可达的虚拟网段、外部到来是否有端口映射、宿主机规则 | 来宾能访问外网不代表外部客户端能直接进入；宿主机到来宾可能经虚拟适配器直达 |
| Bridged | 来宾桥接到哪块物理网卡、地址/网段、DHCP 与网络准入 | 桥接不自动保证处于可达网络，也不意味着绕过防火墙 |
| Host-only | 宿主机虚拟网卡、来宾/宿主机网段与路由 | 通常面向宿主机与该隔离网段，不默认从外部网络可达 |

来宾先查 IP、路由和实际监听。宿主机再测试同一个目标 IP 和外部 SSH 端口的 TCP 连通。来宾的 sshd 和监听正常，宿主机仍然连不上时，优先查虚拟网卡、VMnet 或虚拟交换机、地址族、IP、路由、NAT、访问规则和监听地址。不要先改密码。

磁盘或快照可能不完整时，再核对差分链和副本启动条件。这一支的深入说明见 [云与虚拟化取证](/knowledge/forensic-cloud-vm/#04-虚拟机常见陷阱)。

这一步对上的是目标的 `ip a`、`ip route`，以及 `ss -lntp` 里实际监听的地址和端口。ping 通但 TCP 不通，或监听在 `127.0.0.1:22` 这类回环地址时，写明路径还差哪一段。超时不单独归给某一个防火墙。`TcpTestSucceeded` 只说明那个 TCP 端口。`27692` 这类非 22 端口已经和配置、NAT 对照过。`network.service` 不存在时没有被写成网卡损坏。保存地址和路由、ss 或 netstat 全文、防火墙与安全组的查询、虚拟网卡模式。

</details>

<details>
<summary>展开 sshd_config分析</summary>

### 14.4 sshd_config分析

主配置在 `/etc/ssh/sshd_config`，旁边还有 `/etc/ssh/sshd_config.d/`。目录里有文件，还不等于它参加了解析。要先看 `Include`，再看启动参数有没有用 `-f` 指到别处。

**先静态保全配置链 → 用 sshd -T 看这次解析 → 改完必须先过 sshd -t 再重启。**

**1. 离线先保全主配置、所有 Include 片段、启动参数和单元覆盖。**

```bash
grep -Ei '^[[:space:]]*(Port|ListenAddress)' /etc/ssh/sshd_config
grep -rniE '^[[:space:]]*(Include|Match|Port|ListenAddress|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|PermitEmptyPasswords|AllowUsers|DenyUsers|AllowGroups|DenyGroups|AuthenticationMethods|MaxAuthTries|MaxStartups|UsePAM|KbdInteractiveAuthentication|AuthorizedKeysFile)' \
  /etc/ssh/sshd_config /etc/ssh/sshd_config.d/
```

检索结果只告诉你候选行在哪，不能直接当成最终策略。先按 `Include` 的路径读文件。它可以用通配符，按路径字典顺序展开，也可能位于 Match 里面。

许多单值指令取最先取得的值。`Port` 和 `ListenAddress` 可以声明多次，不要用“最后一行覆盖”解释全部配置。再按用户、来源等条件读 `Match`。一行 `PasswordAuthentication yes` 不足以证明该账户能登录，还要核对对应策略和 PAM。

按目标版本核对语义，见 [OpenSSH Portable 配置手册](https://manpages.ubuntu.com/manpages/noble/man5/sshd_config.5.html)。

| 字段 | 含义 | 取证判读重点 |
| --- | --- | --- |
| `Port` | sshd 候选监听端口，可多项 | 与启动覆盖、socket 单元、NAT 外部端口及实际监听区分 |
| `ListenAddress` | 本地监听地址，可附端口 | 通配/回环/指定接口、地址族与端口限定一起判断 |
| `PermitRootLogin` | root 的 SSH 登录策略 | `no` 禁止；`prohibit-password` 禁止 root 的 password 和 keyboard-interactive，不等于所有公钥均可登录 |
| `PasswordAuthentication` | SSH password 方法是否允许 | `no` 不必然关闭由 PAM 提供的 keyboard-interactive 口令提示 |
| `PubkeyAuthentication` | 用户公钥认证是否允许 | 与实际公钥、算法、权限和密钥限制共同核对 |
| `PermitEmptyPasswords` | password 方法是否接受空口令 | 不等于账户一定能登录，仍受账户、PAM 和其他策略约束 |
| `AllowUsers` | 允许的用户/匹配模式 | 若设置，候选必须通过；可含来源条件，不只精确用户名 |
| `DenyUsers` | 拒绝的用户/匹配模式 | 与 Allow、Match 及来源条件共同检查 |
| `AllowGroups` | 允许的组/匹配模式 | 实际主组/附加组及 NSS 解析结果必须对应 |
| `DenyGroups` | 拒绝的组/匹配模式 | 用户同时涉及允许与拒绝规则时不能只取允许行 |
| `AuthenticationMethods` | 规定认证组合 | 逗号连接表示依次完成的方法，空格分开的组合是候选路径；密码/公钥之一成功可能还未完成组合 |
| `MaxAuthTries` | 单个连接的认证尝试上限 | 不是全站失败总数，也不同于 Fail2ban 的封禁阈值 |
| `MaxStartups` | 并发未认证连接的限制 | 可导致握手阶段丢弃/断开，不是已认证会话总数限制 |
| `UsePAM` | Linux Portable 构建中启用 PAM | 认证接口及账户/会话检查分开；公钥认证也可能被 PAM 账户检查拒绝 |

还要检查 `KbdInteractiveAuthentication`、实际的 `AuthorizedKeysFile`，以及 SFTP、强制命令、转发等条件。不要为了兼容客户端直接关掉加密策略。RHEL 还可能通过系统加密策略和 drop-in 影响算法协商。失败时保存双方日志和版本。

**2. 有效配置只在隔离的分析虚拟机或副本里核对。** 使用已经确认可信的工具。下面假定程序是 `/usr/sbin/sshd`，配置和 HostKey 都属于这个副本。简称 `sshd -T` 的意思是解析并输出这次配置，它不是运行中进程的状态查询，也不是历史状态。

```bash
sudo /usr/sbin/sshd -T -f /etc/ssh/sshd_config
# 常用输出过滤；另保存未过滤输出及原始退出状态
sudo /usr/sbin/sshd -T -f /etc/ssh/sshd_config | \
  grep -Ei '^(port|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication)[[:space:]]'
# 计算特定账户/来源对应的 Match 分支；全部值按实际连接替换
sudo /usr/sbin/sshd -T -f /etc/ssh/sshd_config \
  -C user=analyst,addr=192.0.2.10,host=analyst.lab,laddr=192.0.2.20,lport=27692
```

先按真实连接填写测试条件。`addr` 是客户端来源，`host` 是它的解析名称，`laddr/lport` 是服务端接受连接的本地地址和端口。还缺哪些条件，按版本补齐。

不带 `-C` 的全局结果不能代表某个 Match 分支。占位参数也不证明真实连接会命中。再对照运行时的 `-f`、`-o`、`-p`、socket 监听和日志。参数见 [sshd 测试参数](https://man.openbsd.org/sshd.8)。

离线配置先建立路径映射，或放到隔离副本里。`Include` 的相对路径通常以 `/etc/ssh` 为基准。绝对引用也可能碰到分析机上的文件。不要直接让分析机的默认环境去解析一份孤立的主配置。

测试不会启动新的监听。`-T` 输出的是这次解析得到的配置。`-t` 只做检查。两种结果都保存原始退出状态。管道后面的 grep 可能返回“没有匹配行”，也可能把前面的 sshd 失败遮住。所以先单独保存完整测试输出和错误，再过滤查看。不能只凭过滤结果里的一个 yes 判定整个测试成功。

**3. 语法通过才允许重启。** `sshd -t` 检查配置有没有效，以及主机密钥条件，不启动服务。没有输出，并且退出码为 0，才表示这次检查通过。有报错或非零状态，就去定位配置、权限、密钥或路径问题。语法通过，不等于监听、网络或账户认证已经通过。

【仅在副本/仿真/授权环境执行】配置修改和服务重启：先完成本节开头的配置和快照保全。下面的变量必须对应已经确认的同一个实例和单元。校验失败时不要重启。单元如果采用 `-o/-p` 等参数，测试也要带上同样的参数。socket 激活时还要单独核对 socket 和生成器，不能盲目沿用服务重启示例。

```bash
# SSH replay syntax gate：确认实例后设置；可通过环境变量指定实际值
SSHD_BIN=${SSHD_BIN:-/usr/sbin/sshd}
SSHD_CONF=${SSHD_CONF:-/etc/ssh/sshd_config}
SYSTEMCTL_BIN=${SYSTEMCTL_BIN:-/usr/bin/systemctl}
SSH_UNIT=${SSH_UNIT:-ssh.service}       # RHEL 系按实际替换为 sshd.service
: "${SSHD_BIN:?}" "${SSHD_CONF:?}" "${SYSTEMCTL_BIN:?}" "${SSH_UNIT:?}"
if sudo "$SSHD_BIN" -t -f "$SSHD_CONF"; then
  sudo "$SYSTEMCTL_BIN" restart "$SSH_UNIT"
else
  printf 'SSH_CONFIG_INVALID\n' >&2
  exit 1
fi
```

默认值是常见实例的示例。先按自己的受控副本确认，或改成实际值。恢复后再核对实际进程、监听，以及一次指定账户的认证，保存新窗口的日志。Ubuntu 同样要求先做配置检查再重启，见 [OpenSSH Server 操作说明](https://ubuntu.com/server/docs/how-to/security/openssh-server/)。

这一步对上的是主配置、被 `Include` 引用的片段，以及 `sshd -T` 对这次连接条件解析出的 `Port` 和 `ListenAddress`。没有 `-C` 的用户和来源时，不把全局结果写成该账户的 Match 结果。`sshd -t` 非 0 时，不重启。`-T` 和 `-t` 的原始退出状态都在。`PasswordAuthentication yes` 没有被单独写成该账户可以登录。`no` 和 `prohibit-password` 按表里的含义解释。保存配置链哈希、未过滤的 sshd -T 输出、语法检查的退出码。副本里的重启另记日志。

</details>

<details>
<summary>展开 Linux账户与认证</summary>

### 14.5 Linux账户与认证

FinalShell 里要填的主机、端口、用户名和密码还没和 Linux 账户对上。系统登录、数据库和客户端同步是三套凭据。

**先填已经确认的 Linux 账户 → 再读 passwd、shadow 和 group → 对上 NSS 和锁定策略之后才解释登不进去。**

**1. 逐项填 FinalShell。** 主机填目标 IP 或明确的主机名。端口填实际的 SSH 外部端口。用户名填 Linux 系统账户或 NSS 账户。密码填该账户的认证口令。

用密钥认证时，用私钥和它的口令。不要换成数据库 root 密码，也不要换成 FinalShell 的同步密码。三套体系里账户同名，也不说明凭据相同。

**2. 现场或副本上，先看当前会话，再查候选账户。**

```bash
# 目标现场/副本：whoami 和 id 只说明当前会话身份
whoami
id
cat /etc/passwd
getent passwd
# 指定候选账户，替换为目标实际用户名
getent passwd analyst
id analyst
```

`whoami` 和 `id` 只说明当前会话是谁。先读本地三个文件：`/etc/passwd` 看用户名、UID/GID、家目录和 shell；`/etc/shadow` 看敏感的口令哈希、老化和过期策略；`/etc/group` 看本地组。

**3. `getent` 可能还会返回目录服务里的身份。** 在线结果不等于离线文件的内容。确认查询环境属于目标。不能在分析机的默认 NSS 下，把检材用户查成另一套结果。判断账户锁定时保留原字段，并继续核对实际认证策略。

逐项核对：账户是否存在、UID 和附加组、shell 实体、锁定和过期、PAM、Allow/Deny 与 Match、认证组合、密钥或口令、会话限制。shadow 里的口令锁定，不自动等于所有认证方法都被禁用。Ubuntu 通常保留 root 账户，但禁用它的口令直接登录，不是“没有 root”。管理员可以调整。见 [Ubuntu 账户说明](https://ubuntu.com/server/docs/how-to/security/user-management/)。先用已经确认的正常账户。不要为了连通，在原始证据上启用 root、解锁或改密。

这一步对上的是 FinalShell 用的用户名能在 `/etc/passwd` 或 `getent` 的目标结果里找到，端口是实际 SSH 外部端口。只有 shadow 锁定、没有 PAM 和认证策略时，不写成所有登录方式都不可用。分析机上的 `getent` 不能当成检材用户。passwd、shadow、group 三份本地文件和 NSS 查询结果分开保存。保存三个账户文件的摘要、指定用户的 getent 和 id 输出。不在原始证据上改密。

</details>

<details>
<summary>展开 SSH Key取证</summary>

### 14.6 SSH Key取证

家目录里的公钥、known_hosts 和私钥容易被当成同一种“钥匙”。它们能证明的事不一样，而且不能只查 root。

**按已确认的家目录找 `.ssh` → 用表分开每种文件能证明什么 → 私钥只保全，不拿去登录别的系统。**

**1. 按 passwd 或 NSS 已经确认的家目录逐个定位。** 常见位置是 `/root/.ssh/` 和 `/home/*/.ssh/`。不能只查 root，也不能假定所有用户都在 /home。服务端配置里的 `AuthorizedKeysFile`、`AuthorizedKeysCommand`，或证书和可信 CA，可能把授权材料放到别处。

| 材料 | 直接支持什么 | 不能直接推出什么 |
| --- | --- | --- |
| `authorized_keys` | 当前账户允许哪些公钥及行级限制 | 公钥存在不证明曾被使用；异常需与基线、部署和登录日志互证 |
| `known_hosts` | 保存的远端主机名/IP 与主机公钥 | **不是成功登录清单**；可预置/复制、可能哈希化，也可在用户认证前写入 |
| `config` | 用户客户端目标、端口、身份文件、代理/跳板等设置 | 不是 sshd 服务端策略，不证明实际连接成功 |
| `id_rsa` / `id_ed25519` | 用户私钥材料，算法/名称可变化 | 不证明属于哪位自然人，也不代表获准使用它访问其他主机 |
| `*.pub` | 对应的用户公钥候选 | 与实际私钥、授权条目和日志指纹分别核对 |
| `/etc/ssh/ssh_host_*_key` 及 `.pub` | SSH 服务器主机身份材料 | 区别于用于用户登录的私钥/authorized_keys；不能混成同一认证层 |

**2. 先确认起始路径和软链目标都在检材根内。** 文件可能不存在，把缺失范围留下。只做静态列举，输出写到独立的分析目录。

```bash
EVIDENCE_ROOT=/mnt/evidence
find "$EVIDENCE_ROOT/root" "$EVIDENCE_ROOT/home" -maxdepth 4 -type f \
  \( -path '*/.ssh/*' -o -name authorized_keys \) -print
# 对已选定的一份公钥授权材料记录元数据与哈希，不输出私钥正文
stat -- "$EVIDENCE_ROOT/home/analyst/.ssh/authorized_keys"
sha256sum -- "$EVIDENCE_ROOT/home/analyst/.ssh/authorized_keys"
```

**3. 再看授权行本身，而不只看文件在不在。** 检查授权公钥是不是异常新增，所有者、权限和父目录，以及 `from=`、`command=`、`restrict` 等行级限制。再看 `.ssh` 的创建或修改时间、异常私钥、客户端配置和外部授权机制。mtime 和 ctime 不是可靠的首次植入时间。文件系统没有 birth time 时不要编造。注释不能证明自然人是谁。私钥属于高敏感证据，不得用于登录其他系统。单独保全，限制展示和访问。需要仿真时，另用明确授权的实验身份材料。

这一步对上的是已确认家目录下的 `authorized_keys` 路径、哈希，以及行级限制。文件不存在时留下搜索范围。`known_hosts` 不能写成成功登录清单。`id_rsa` 或 `id_ed25519` 不能写成已经知道是谁。表里每种材料的“不能直接推出什么”都还在。主机密钥 `/etc/ssh/ssh_host_*_key` 和用户私钥没有混成一层。保存列举结果、选定公钥的 stat 和 sha256。私钥正文不写入公开记录。

</details>

<details>
<summary>展开 SSH日志取证</summary>

### 14.7 SSH日志取证

认证日志的路径随发行版变化，journal 和文件日志还可能各有一份。要找最早一次成功登录时，不能从“最近 50 行”往回猜。

**先按发行版保全全量日志 → 再提取成功和失败字段 → 和 wtmp 一类记录互证。**

**1. 先确认这份系统把认证日志写到哪里。** Debian 和 Ubuntu 常见 `/var/log/auth.log*`。CentOS 和 RHEL 常见 `/var/log/secure*`。文件在不在，取决于日志服务和转发配置。只有 journal、容器日志或远端集中日志时，按实际来源保全。不要因为某个文件缺失就认定没有登录。

```bash
# Ubuntu / Debian 常见单元和认证日志
journalctl -u ssh -n 50 --no-pager
tail -f /var/log/auth.log
# CentOS / RHEL 系
journalctl -u sshd -n 50 --no-pager
tail -f /var/log/secure
```

先保全全量和轮转日志，再做实时观察。`tail -f` 会一直跟踪，采集窗口结束用 Ctrl+C。它不改写日志，但也不是全量保全工具。

单元名按实际实体选。socket 激活、程序标签不同，或日志集中转发时，单一的 `-u` 查询可能漏记录。离线 journal 先指定保全目录，再限定事件窗口，保留 boot ID、PID 和时间基准。“最近 50 行”只说明这次窗口，不代表全部历史。

**2. 在已经保全的未压缩副本里检索这些事件。**

```bash
# 已保全的未压缩日志工作副本；不存在的发行版路径按现场缩小
rg -n 'Accepted password|Accepted publickey|Failed password|Invalid user|Connection closed|Disconnected from|session opened|session closed|sudo:|pam_' \
  ./work/var/log/auth.log* ./work/var/log/secure*
```

压缩轮转另行解压到分析副本，或用可信工具读取，不改原日志。保留原始行、路径、行号和哈希。传统 syslog 可能缺年份或时区，用轮转、boot、journal 和其他材料校准。汇总时避免把同一事件在文件日志和 journal 里的两份显示算两次。

| 日志片段 | 含义 | 后续核对 |
| --- | --- | --- |
| `Accepted password` | SSH password 方法认证成功 | Linux 账户、来源/会话与后续行为；不等于一定启动交互 Shell |
| `Accepted publickey` | 公钥认证成功 | 算法/指纹、当时授权配置与会话；不凭注释认定操作者 |
| `Failed password` | 一次口令认证失败 | 失败计数、账户、IP、时间窗；不等于已经入侵 |
| `Invalid user` | 尝试的账户未被当时系统解析为有效用户 | 原样账户名、NSS/账户变化与后续事件 |
| `Connection closed` | 连接关闭 | 关闭发生在协商、认证还是会话阶段，不能直接归因攻击 |
| `Disconnected from` | 对端/会话断开信息 | 用户、来源、原因与对应 PID/会话 |
| `session opened` / `session closed` | PAM 等记录的会话开启/关闭 | PID、会话类型与时段；也可能是 sudo/其他服务的会话 |
| PAM 错误 | PAM 认证、账户或会话策略异常 | 模块、锁定/过期、目录服务与对应连接阶段 |

每个事件提取：原始时间或时区、源 IP、源端口、用户名、认证方式、成功或失败、服务、PID、boot ID、会话开启与关闭。字段没出现就记缺失，不要补成假定值。一次连接可以有多次失败。源端口用来关联连接，但不证明自然人。同一个公网 IP 也可能是 NAT 后面的多个客户端。

**3. 找最早一次 SSH 成功时，先限定保留范围。** 要从完整认证日志、轮转文件和 journal 里提取 `Accepted password` 和 `Accepted publickey`。不要从“最近 50 行”或 lastlog 的最近记录倒推。

先把每行的原始时间、文件或行号、账户、来源 IP、端口、PID 和 boot 记在事件表里。确认年份和时区之后，另列统一的 UTC 时间，再按该列升序排序。文件日志和 journal 里的同一事件只算一次。同一个最早时刻有多条时，并列保留。无法确认年份的传统 syslog 先列为待核，不要和已经确定年份的记录强行排序。

结果写成“在已取得的某时段日志中，最早保留的 SSH 认证成功事件为……”，并附上用户、完整时间、来源 IP 和原始行位置。它不等于服务器创建之后的第一次登录。`Accepted` 也不自动证明已经打开了交互 Shell，还要对应会话记录。如果问的是全部系统登录而不只是 SSH，再结合下面的 wtmp、控制台和其他认证记录，不要混成同一种事件。

**4. 登录数据库和 SSH 文本日志互证。** 下面默认读的是当前目标现场或副本，不是任意离线镜像。

```bash
last
lastb
lastlog
# 传统 wtmp/btmp 已保全副本：使用兼容格式的可信分析工具
last -f ./work/var/log/wtmp
lastb -f ./work/var/log/btmp
```

先分清三个库各记什么。`last` 从 wtmp 读成功登录、退出和重启，不限于 SSH。`lastb` 从 btmp 读失败登录，可能需要读取权限。`lastlog` 只是每个账户最近一次登录的摘要。

这些记录依赖系统实际写入，也可能缺失、被清理、被篡改或被轮转。不要对二进制格式直接做文本 grep。离线的 lastlog 先指定证据数据库，再选兼容的解析器，防止读到分析机的默认库。依据见 [传统 last/lastb](https://manpages.ubuntu.com/manpages/noble/man1/last.1.html) 和 [lastlog 手册](https://man7.org/linux/man-pages/man8/lastlog.8.html)。

新系统可能改用 `wtmpdb` 的 `/var/log/wtmp.db`，或 `lastlog2` 的 `/var/lib/lastlog/lastlog2.db`。命令名和选项也可能不同。先核对目标的包、文件和版本。不要把旧命令缺失解释成没有人登录。见 [Debian wtmpdb 说明](https://manpages.debian.org/trixie/wtmpdb/last.1.en.html) 和 [lastlog2 说明](https://manpages.debian.org/trixie/lastlog2/lastlog2.8.en.html)。所有登录记录与 SSH 原始日志、journal、audit、sudo 和后续行为交叉核对。

这一步对上的是认证日志的实际路径、最早一条 `Accepted password` 或 `Accepted publickey` 的原始行，以及它和会话记录的关系。只有最近 50 行，或年份没确认时，不写成这是服务器的第一次登录。`Accepted` 没有会话记录时，不写成已经打开交互 Shell。事件表里有原始时间、文件行号、账户、来源 IP 和 boot。文件日志和 journal 的同一事件只算了一次。保存全量日志哈希、检索命中、last、lastb、lastlog 或替代格式的输出范围。

</details>

<details>
<summary>展开 FinalShell连接排障</summary>

### 14.8 FinalShell连接排障

FinalShell 报错了，还不知道停在网络、端口、认证还是会话。不要靠反复重启把每一层混成一次失败。

**先确认所填的 IP 和端口 → 再按报错进入对应层 → 认证拒绝时先读账户和同窗口日志。**

**1. 先把失败放回连接层。** 确认 FinalShell 所填的目标 IP、路由和 TCP 上的 SSH 端口。目标侧再核对 OpenSSH Server，或已经确认的其他 SSH 实现，sshd 进程或 socket 激活，以及正确地址和端口上的监听。

网络到达之后，继续核对防火墙和 ACL、sshd 的认证策略、Linux账户存在与否，以及密码、密钥或所需的组合认证。通过全部认证与会话检查后才建立SSH会话。

这是一组条件，不是“必须先启动守护进程再逐层检查”的脚本。访问控制可以在路径上的多个位置拦截。

**2. 按这个顺序查，但已经出现认证拒绝时可以先跳到账户和日志。** 标准排查顺序：网络 → 端口 → OpenSSH安装情况 → sshd 进程 → systemd 服务或 socket → 监听地址 → SSH 配置 → 防火墙 → Linux 账户 → 认证方式 → SSH 日志 → 客户端配置。网络和端口从客户端检查。进程、服务和监听到目标侧核对。

网络超时，先找路由或端口。已经有认证拒绝，就先读策略、账户和日志，不要靠重复重启排错。第 14.11 节的一分钟表列出各层对应的命令，可以从失败现象进入需要的小节。

| FinalShell/SSH 报错 | 优先检查 | 取证边界 |
| --- | --- | --- |
| `Connection timed out` | IP、路由、地址族、端口、网络丢弃、云安全组/ACL、NAT、虚拟网卡 | 超时不单独证明是密码错误或某一个防火墙责任 |
| `Connection refused` | 目标地址是否正确、端口是否监听、sshd 是否启动/绑定其他地址 | 常见于无监听，也可能是防火墙或中间设备主动 REJECT；不证明已找到正确服务器 |
| `Permission denied` | 若已确认来自 SSH 认证阶段，核对用户名、口令/密钥、root/方法/Allow/Deny/Match/PAM | TCP/SSH 有响应但认证未完成；SFTP 文件权限的同名错误是另一层问题 |
| `Host key verification failed` | 重装、快照回退、IP 复用、实际主机身份、潜在中间人 | 通过可信控制台/已保全公钥核对指纹，不直接忽略或关闭主机身份校验 |
| `Connection closed` / `Connection reset` | 服务端同窗口日志、PAM、Fail2ban、防火墙、Shell/强制命令、访问控制、MaxStartups 和服务状态 | 先确定发生阶段；策略丢弃、进程异常或中间设备都可能造成关闭 |

**3. 客户端本身也要核对，但不要为了兼容去放宽策略。** 核对 FinalShell 的主机、端口、Linux 用户、认证模式、私钥格式和口令、代理或跳板、地址解析，以及客户端支持的算法。不得把协议兼容报错一律改成启用 root 或弱算法。终端通了但文件浏览失败时，另外检查 SFTP subsystem、chroot 和路径权限。监控空白可能是命令、权限或解析兼容问题，不表示 SSH 登录失败。一个客户端可以建立多个终端或传输连接。日志计数按实际的连接和认证事件统计。参见 [FinalShell 常见问题](https://www.hostbuf.com/t/1088.html)。

这一步对上的是报错属于超时、拒绝、认证失败、主机密钥还是中途断开，以及这一层已经核对的对象。`Connection timed out` 不单独证明是密码错误。`Connection refused` 不证明已经找到正确服务器。`Permission denied` 若来自 SFTP 文件权限，不要写成 SSH 账户认证失败。表里的优先检查项有对应输出。`Host key verification failed` 时，指纹来自可信控制台或已保全公钥，没有直接关掉校验。保存客户端所填的主机、端口、用户，目标侧的监听和同窗口日志。

#### 14.8.1 受控副本的协商与最小路径验证

旧的 SSH 仿真要留在副本里做。还没核对指纹和实验账户之前，不要用检材里取出的私钥去连别的系统。

**先核对副本、端口和实验账户 → 用 -vvv 看停在哪一阶段 → 转发成功仍要单独做应用认证。**

**1. 连接前先确认副本身份、快照、实际端口和已授权的实验账户。** 通过可信控制台或主机公钥核对指纹。不执行从检材导出的未知程序，也不试用取出的私钥访问其他系统。客户端调试结果可能含敏感环境信息，保存在受控分析记录里。

```bash
# 在分析机使用已经取得并核对的实验私钥；文档地址与账户按副本替换
ssh -vvv -o ConnectTimeout=5 -o ConnectionAttempts=1 \
  -o IdentitiesOnly=yes -i /work/keys/lab_id_ed25519 \
  -p 27692 analyst@192.0.2.20
```

已经许可转发的 SSH 会话，可以访问服务端的回环入口。只绑定分析机的回环。右侧目标属于 SSH 服务端所在的网络空间。容器回环不等于宿主机回环。

先用 `-vvv` 看错误停在连接、协商、认证还是会话。`ConnectTimeout=5` 限制连接和初始协商的等待。`ConnectionAttempts=1` 避免反复重试。

身份参数另看：`IdentitiesOnly=yes` 限制所用身份，`-i` 选实验私钥，`-p` 选 SSH 外部端口。它们不跳过服务端认证，也不跳过主机身份核验。拿同窗口的服务端日志对照之后，再判断连接为什么关闭。

**2. 需要访问服务端回环上的端口时，再做本地转发。**

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18888:127.0.0.1:8888 \
  -p 27692 analyst@192.0.2.20
```

先在分析机的另一个终端用 `ss -tlnp` 检查本地监听。入口存在之后，再验证目标协议是否响应。

读 `-L` 时分两端：左侧监听在分析机，右侧目标由 SSH 服务端去连。转发失败就核对 `AllowTcpForwarding`、`PermitOpen` 和密钥行限制。转发成功，仍然必须做应用或数据库认证。

`ExitOnForwardFailure` 只帮助发现监听没建立，不保证之后能连到目标。参数见 [ssh 参数](https://man.openbsd.org/ssh.1)。

客户端监听、SSH 认证成功、转发目标可达、应用认证成功，分别记录。保存客户端结果、服务端同窗口日志、实际 IP 和端口、账户、快照标识，以及全部调整。新的 Accepted 或访问记录标为仿真操作，不用来推断历史首次登录或入侵来源。结束后停止这次实验连接，按记录回滚副本变更，并再次核对状态。

这一步对上的是 `-vvv` 停住的阶段，以及 `-L` 左侧监听和右侧目标是否分别成功。转发成功但应用认证没做时，不写成业务已经能访问。实验连接不写成历史入侵来源。用来核对的是 `IdentitiesOnly=yes`、`-i` 和 `-p` 用的是实验材料。`ss -tlnp` 能看到分析机上的本地监听。保存客户端调试输出、服务端同窗口日志、快照标识和回滚结果。

</details>

<details>
<summary>展开 SSH暴力破解分析</summary>

### 14.9 SSH暴力破解分析

日志里有大量失败，还不等于已经入侵。阈值也不能用一个固定失败次数套所有环境。

**先按来源、账户和连接聚合 → 再看失败之后有没有成功 → 成功会话和行为对上了才写入侵。**

**1. 在日志覆盖范围内聚合，不先下入侵结论。** 按源 IP、账户、连接或 PID、认证方法，以及声明的时间窗聚合。记下总事件数、独立连接数、首末时间和时间窗长度，再和正常运维、扫描或巡检的基线比较。关注大量 `Failed password` 和 `Invalid user`、单 IP 多账户、单账户多 IP、短时间密集失败，以及失败后成功的账户和来源。阈值由环境和日志完整性确定。不用固定失败次数直接裁定入侵。

**2. 候选链要逐段有证据。** 大量失败，然后同一账户或关联来源成功，然后异常命令或提权，然后新账户、SSH Key、Cron 或 systemd 等变化，才可能发生 SSH 入侵。成功可以是 `Accepted password`，也可以是 `Accepted publickey`。后者也可能是正常运维或另一条认证路径。不能把一次公钥成功自动当成密码破解的结果。

先逐条标出动作和连接阶段，再计算统计量。同一连接的多次失败、同一失败在两类日志里的重复显示、不同连接，是三个粒度。用原始路径或条目、时间、boot、PID 或会话，以及客户端端口建立关联依据。记下去重规则，以及仍然不能关联的条目。不要用去重后的 IP 数代替尝试次数。也不要把不同账户的失败直接拼成某个账户的破解链。

**3. 一次 Failed password 不能证明已入侵。** 多次失败只支持异常尝试这种模式。入侵结论还需要成功会话、源 IP 与连接关系、行为日志、进程、文件变化和账户变化互相印证。源 IP 可能受 NAT 或跳板影响。防止 PID复用、轮转覆盖、时钟偏差和日志重复造成错误关联。缺口和未确认的行为单独列出。不用“没有日志”证明没有发生。

这一步对上的是时间窗内的失败次数、独立连接数，以及失败后是否出现 `Accepted password` 或 `Accepted publickey`。只有 `Failed password` 或 `Invalid user`、没有成功会话和行为时，不写成已经入侵。去重规则写明了。尝试次数没有被 IP 个数代替。公钥成功没有被自动写成口令破解。保存聚合表、原始日志位置、不能关联的条目。

</details>

<details>
<summary>展开 SSH入侵分析</summary>

### 14.10 SSH入侵分析

要沿入口、认证、会话、执行、持久化和数据后果把历史证据串起来。不要为了连得方便去改检材上的账户、策略或服务。

**先保全状态和日志 → 按清单把每一段对上材料 → 当前进程只说明现在，不代替已经退出的行为。**

**1. 进程和网络确认入口，认证日志确认会话，命令历史和任务配置找后续动作。** 原始材料的保全要求仍按这一章开头执行。下面的清单用来串历史证据：

1. 确认服务器 IP、路由、网络空间、时间与时区，标明历史或当前状态（第 14.3 节）。
2. 关联 sshd 进程、服务或 socket、实际监听和端口映射（第 14.2 到 14.3 节）。
3. 保全 sshd_config、Include、Match、启动参数和单元覆盖，分别分析当前和历史策略（第 14.4 节）。
4. 提取 SSH 原始日志、轮转日志、journal 和集中日志，固定覆盖范围与哈希（第 14.7 节）。
5. 提取认证成功的源 IP、源端口、账户、方式及会话，不只搜 Accepted 后面的一列（第 14.7 节）。
6. 提取失败登录的源 IP、不存在的账户和连接阶段，去掉重复显示（第 14.7 节）。
7. 分时间窗判断暴力破解或异常尝试，并寻找失败后成功的关联（第 14.9 节）。
8. 检查异常 Linux 账户、UID 0 或附加组、创建、改密、锁定变化和 NSS（第 06.2、14.5 节）。
9. 单独核对 root 登录与来源、认证方法、策略变化和对应行为（第 14.4 到 14.7 节）。
10. 对比 authorized_keys 的基线、指纹、行级限制和授权机制，查异常植入（第 14.6 节）。
11. 检查各账户 .ssh 目录的元数据、私钥、客户端配置和主机身份变化（第 14.6 节）。
12. 检查 sudo 的调用用户、目标用户、TTY、目录、命令和结果。沿第 07 节及既有 audit 材料追踪。sudo 命令记录不单独证明已经完成。
13. 静态分析 Shell 历史和对应脚本。按家目录、时间戳和执行结果核对，沿 [第 15.2 节](#152-历史文件是线索计划任务按来源解释)。
14. 将 last / lastb / lastlog 或实际替代格式，与认证、会话、重启和日志覆盖互证（第 14.7 节）。
15. 查看 `ps -ef`，关联当前用户、PID、父子关系、执行路径和启动时间。当前进程不代替已经退出的行为。
16. 查看 `ss -antp` 的当前 TCP 状态和 `ss -lntp` 的监听，关联进程、远端端点和防火墙或流日志。注意权限和网络空间。
17. 检查 `crontab -l`、各账户任务、`/etc/crontab`、`/etc/cron.d/`。复用 [第 08 节](#08-实战验证一项可疑定时任务) 和第 15.2 节。当前账户的清单不等于所有任务。
18. 检查 systemd 的 service 和 timer、覆盖配置、用户单元和其他持久化。配置存在和曾经执行，分别论证（第 02、08、15.2 节）。
19. 对异常脚本、WebShell、上传目录和工具目录做静态取证。保全哈希、权限和时间，与登录、sudo 和 [Web 应用日志](/knowledge/fic-case-04/#04-访问日志与活动时间线) 关联。不试运行未知文件。
20. 建立 `尝试 → 认证/会话 → 提权/命令 → 持久化/文件变化 → 外联/清理` 这条时间线。每个连接标识和结论注明证据、时间基准、反证和缺口。

**2. 下面的查询只看当前状态。** 它不直接证明历史操作。只在已授权的目标或副本上执行，并记下时间。同时把进程对应到服务管理单元和监听端口，再查系统和用户的 cron 配置、Shell 历史，找启动和持久化线索。

```bash
ps -ef
ss -antp
```

这一步对上的是时间线上每一段所用的日志或当前查询，以及 `ps -ef`、`ss -antp` 属于哪一次采集。当前进程和 `crontab -l` 覆盖不了已经退出的行为，也覆盖不了其他账户的任务。缺的段写入缺口，不用“没有日志”证明没发生。20 项里已完成的项能回到第 14 章对应小节的原始材料。sudo 命令记录没有被单独写成动作已经完成。保存清单完成情况、当前查询的时间和输出、静态文件的哈希。未知文件没有被执行。

</details>

<details>
<summary>展开 SSH取证速查表</summary>

### 14.11 SSH取证速查表

材料还没收齐时，用这张表查缺哪一类。某一项已经有了，不能代替其他项。排障时一行命令只回答这一行的问题。

**先按证据类别收齐 → 再按一分钟表逐行查 → 现场、配置和仿真分开写。**

**1. 按类别收集文件或输出。** 配置、运行和历史证据分别记录。清单用来查缺项。

| 证据类别 | 保全对象/工具 | 回到哪里判读 |
| --- | --- | --- |
| 网络证据 | `ip a`、`ip route`、`ss`、旧系统 `netstat`；NAT/虚拟网卡 | 第 14.3 节：观察时间、地址族与网络空间 |
| 服务证据 | `systemctl`、`ps`、`pgrep`，service/socket、执行路径及参数 | 第 14.2 节：安装、进程、服务、监听分开 |
| 配置证据 | `/etc/ssh/sshd_config`、`/etc/ssh/sshd_config.d/` 与其他 Include | 第 14.4 节：启动覆盖、顺序和 Match |
| 账户证据 | `/etc/passwd`、`/etc/shadow`、`/etc/group` 及 NSS 材料 | 第 06.2、14.5 节：身份、策略与认证分开 |
| 密钥证据 | `~/.ssh/`、authorized_keys、known_hosts、客户端配置及主机公钥 | 第 14.6 节：授权、信任、实际使用分开 |
| 日志证据 | auth.log、secure、journalctl/journal、轮转/集中日志 | 第 07、14.7 节：原始字段、PID、boot 与时区 |
| 登录记录 | last、lastb、lastlog 对应数据库及实际替代格式 | 第 14.7 节：覆盖、篡改/轮转与 SSH 互证 |
| 命令历史 | `.bash_history` 等各账户历史、sudo/audit | 第 07、15.2 节：文本存在不等于成功执行 |
| 防火墙 | UFW、firewalld、iptables、nftables；SELinux/Fail2ban/云规则 | 第 14.3 节：本机、宿主机、云和中间路径分别保全 |

**SSH服务器取证 + FinalShell故障排查一分钟速查表**

按下面十行做一轮。 先保存镜像、时间和配置基线。把 `IP/SSH端口/用户名` 换成实际目标值，按发行版选对应命令。

每条命令只回答本行的问题。服务状态不代替监听。端口可达不代替认证。出现报错就记下这一层的结果，再查相邻层，不要因为一个报错改写已经有的结论。

| 顺序 | 一分钟检查动作 | 判读与下一步 |
| --- | --- | --- |
| 1 | `ip a`、`hostname -I`、`ip route`；客户端 `ping IP`（14.3） | 核对正确对象和地址；ICMP 失败不等于 SSH 失败 |
| 2 | 第 14.3 节 `Test-NetConnection IP -Port SSH端口` | TCP 不通先查端口/路径；TCP 通不代表协议/认证通过 |
| 3 | `systemctl status ssh` / `systemctl status sshd`；`ps -ef \| grep '[s]shd'`；包和 socket 清单见14.2 | 按 Debian/Ubuntu 与 RHEL 系区别，避免只看 status 或 pgrep |
| 4 | `ss -lntp`（14.3） | 检查回环、IPv4/IPv6、非 22 端口、外部映射和 PID |
| 5 | 第 14.4 节 `sshd -T` 及对应 `-C` 条件 | 核对完整 Include/Match、启动覆盖与 socket，不把解析结果当实时服务 |
| 6 | `sudo ufw status` / `firewall-cmd --get-active-zones`；ACL/安全组/NAT/虚拟网卡见14.3 | 有监听仍超时，沿实际路径逐段验证，不先停防火墙 |
| 7 | `getent passwd 用户名`、`id 用户名`；认证组合/密钥见14.5—14.6 | 已进入 SSH 认证却 Permission denied，优先账户/凭据/策略 |
| 8 | `journalctl -u ssh -n 50 --no-pager` / RHEL系用 `-u sshd`；文件日志/客户端见14.7—14.8 | closed/reset 查 PAM、Shell、访问控制和服务状态；主机密钥变化先核实身份 |
| 9 | `last`、`lastb`、`lastlog` 及第14.9—14.10节失败/成功、密钥和行为时间线 | 多次失败只支持尝试；成功后的行为/文件/账户变化才继续支持入侵判断 |
| 10 | 仅在副本按第 14.4 节通过 `sshd -t` 后变更/验证 | **【仅在副本/仿真/授权环境执行】**，保存差异、命令、实验日志与回滚；原始证据保持不改 |

**3. 看完十行之后，按现象回到对应层。** IP 或路由异常，查网络对象和路径，但不要用 ping 单独裁定。IP 和 ICMP 可达，而 SSH 的 TCP 不通，查 sshd 或 socket、端口、监听和访问规则。TCP 或 SSH 有响应，但认证被拒绝，查 Linux 账户和认证策略。连接后马上断开，结合日志查 sshd、PAM、账户或 Shell、访问控制和客户端。现场事实、配置推断和仿真验证分别记录。

这一步对上的是十行里每一行的命令输出，以及它回答的是网络、监听、认证还是日志。某一行报错时，只记下这一层，不改写其他层已经成立的结论。第 10 行的变更没有做语法检查时，不要执行。`IP/SSH端口/用户名` 已经换成实际值。服务状态和 `ss -lntp` 没有互相代替。保存两张表对应的原始输出。副本里的变更、实验日志和回滚单独保存。

</details>

<span id="15-从目录挂载与历史命令复核任务路径"></span>

## 15 先确认挂载，再解释历史命令里的路径

目录名是 `/www`，里面却可能是空的；历史里又出现过进入这个目录的命令。先确认这个路径挂的是哪一块，再解释命令和计划任务。

**先确认挂载实体 → 再把历史命令当线索 → 计划任务按来源解释，不把命令出现写成已经执行。**

### 15.1 先确认挂载实体，再理解目录内容

当前终端里看得到 `/www`，还不等于这块数据就是检材里的网站卷。仿真之后设备名也会变。

**先读当前挂载 → 再读 fstab 和 mount 单元 → 目录是空的时候分清缺卷、挂错、未采集还是已删除。**

**1. 当前会话的命令只说明采集这一刻。** `pwd` 是当前会话目录。`ls -la` 能显示隐藏文件。`df -T` 是当前已挂载文件系统的类型和空间。设备名在仿真后可能变化。先把磁盘或分区标识、UUID、文件系统和挂载实体关联起来。不要因为目录名叫 `/www` 就认定里面的数据已经齐全。

```bash
# 在已授权的仿真副本控制台读取当前状态
pwd
ls -la /www
lsblk -o NAME,TYPE,FSTYPE,UUID,SIZE,RO,MOUNTPOINTS
findmnt --mountpoint /www -o SOURCE,TARGET,FSTYPE,OPTIONS
df -T

# 已确认软链不会越出检材根后，在只读材料中读取静态挂载线索
EVIDENCE_ROOT=/mnt/evidence
cat -- "$EVIDENCE_ROOT/etc/fstab"
rg -n 'What=|Where=|Type=|Options=' "$EVIDENCE_ROOT/etc/systemd/system" \
  "$EVIDENCE_ROOT/usr/lib/systemd/system"
```

**2. 先看 `findmnt --mountpoint /www`。** 没有结果时，`findmnt -T /www` 可能只返回上层的根文件系统，不能把它当成 `/www` 的独立数据卷。

目录是空的时候，依次比对网站和数据库配置、fstab、mount 单元、容器 Mounts 和历史快照。分清是缺卷、挂错、没采集到，还是已经删除。需要读分区时，按[镜像与文件系统](/knowledge/fic-case-13/)核对只读条件，另建空挂载点。不要把候选分区直接挂到唯一检材的 `/www` 上，也不要卸掉正在使用的目录。

**3. Last mounted on 不是上一次 mount 命令的记录。** ext 文件系统的 `dumpe2fs -h` 里，Last mounted on 是超级块保留的目录线索，可能陈旧，也可能被副本启动改过。不能单凭它确定现在应该挂到哪里。两个都像 Linux 根目录的树，也可能是备份、容器层或重复导出。服务和数据库是不是分开的，要由部署配置、数据卷对应关系和日志等材料支持。

`/www` 当前挂在哪个 SOURCE 上，或 findmnt 说明它并不是独立数据卷。目录为空时，写明是缺卷、挂错、未采集还是已删除。`dumpe2fs -h` 的 Last mounted on 不写成上一次 `mount` 的记录。`findmnt --mountpoint /www` 的 SOURCE、FSTYPE 和 OPTIONS 与 `ls -la` 的目录内容放在一起。没有结果时，没有用 `findmnt -T /www` 冒充独立卷。保存当前挂载输出、fstab、mount 单元检索，以及空目录时核对过的配置和快照范围。

<details>
<summary>展开历史文件是线索，计划任务按来源解释</summary>

### 15.2 历史文件是线索，计划任务按来源解释

历史里有 `cd /www`，仿真里的 `/www` 却是空的。命令出现了，还不等于当时执行成功，也不等于这个挂载就是现在看到的这一块。

**先找各账户的历史文件 → 再按来源读计划任务 → 没有执行结果时只保留“命令里有这条路径”。**

**1. `history` 只显示当前 shell 的历史列表。** 离线分析按 passwd 里的家目录、shell 和配置去找 `.bash_history`、`.zsh_history`，并检查面板的任务或终端日志。历史可能有时间戳，也可能还没写回、被覆盖、被清理或被修改。`cd`、`mkdir`、`mount` 或备份命令可以提供路径候选。出现一条命令，不证明它执行成功，不证明当前目录曾经存在，也不证明所用的挂载是对的。

```bash
find "$EVIDENCE_ROOT/root" "$EVIDENCE_ROOT/home" -maxdepth 3 -type f \
  \( -name '.bash_history' -o -name '.zsh_history' \) -print
find "$EVIDENCE_ROOT/etc" -maxdepth 2 -type f \
  \( -name 'crontab' -o -path '*/cron.d/*' \) -print
find "$EVIDENCE_ROOT/var/spool/cron" -type f -print
# 活体/仿真读取当前账户；它不是所有账户的任务清单
crontab -l
systemctl list-timers --all --no-pager
```

先确认任务来源。`crontab -l` 只列当前账户的任务。系统 crontab 和 cron.d 通常有执行用户这一列，用户 crontab 通常没有，不能混用同一种解析。

**2. 宝塔终端历史要另找实际文件。** 部分构建用 `history.pl` 保存终端命令线索。它不保证在固定目录，也不保证和 Linux 用户的 `.bash_history` 在内容、时间或操作者上一致。先静态定位候选，再读当前面板代码和日志，确认文件格式和是谁写入的。

```bash
# 已确认面板树与软链边界；不存在时保留查找错误和范围
find "$EVIDENCE_ROOT/www/server/panel" -type f -name 'history.pl' -print
```

找到之后保存原文件哈希、完整上下文和可用的时间字段。核对命令引用的 JAR、启动脚本、工作目录和配置。文件不存在时，继续查面板终端、任务日志和各账户历史。不要制造同名文件。历史里的服务名、启动命令或数据库口令只是线索。命令是否成功、历史凭据是否仍然有效，仍要其他记录验证。

**3. 把任务字段和它引用的文件对上。** 逐项记下 `@reboot`、周期、环境、执行账户和完整命令，再找命令引用的文件。`.sh` 和 `.bat` 只是扩展名。任务也能直接调用二进制、解释器或内联命令。只搜脚本扩展名会漏掉任务。

历史里出现 `cd /www` 和压缩某个网站目录的命令，但仿真的 `/www` 是空的。先核对原来的 fstab、任务或 vhost 里的路径、所采集的卷和备份文件。备份候选要确认格式、大小、哈希和实际内容。如果找到了同路径的数据卷或备份，可以记下对应关系。没有执行结果时，保留“历史命令包含该路径”这一句。任务曾经运行，还需要 cron、journal、输出文件或应用日志。任务启动和业务动作成功，继续分开写。

路径链至少覆盖 `命令/任务来源 → 执行身份与目录 → 引用脚本/应用 → 输入输出路径 → 卷或备份实体 → 时间与日志`。未知脚本只静态阅读，不用试运行代替历史证明。查询输出、恢复件和仿真日志与保全材料分开保存。

这一步对上的是历史文件或 `history.pl` 的实际路径，以及任务来自当前账户、系统 crontab 还是 cron.d。只有 `cd /www` 或压缩命令、没有执行结果时，不写成任务已经跑过，也不写成现在的空目录就是当时的数据。`.bash_history` 和面板的 `history.pl` 没有被当成同一份记录。`crontab -l` 没有被写成全部账户的任务。保存历史文件哈希、任务原文、引用文件的路径。仿真输出单独存放。

</details>
