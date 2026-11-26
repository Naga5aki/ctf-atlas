# 服务器取证模块逐项核查与变更清单

日期：2026-10-06。范围：21 篇知识文章、533 个真实章节；8 行代码内 SQL 注释不计章节。
文章 ID、标题、分类、层级、元数据、全部原命令/代码、全部表格及原内联技术参数保留；未新增文章，未删除不确定内容。

## 1. 文件及章节范围

| 文章/主题 | 维护稿（绝对路径） | 章节 | 实际改写段落 |
| --- | --- | --- | --- |
| Docker 取证 01｜环境、服务与配置 / Docker 与容器 | [docker-evidence-01.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-01.md) | 37 | 3 |
| Docker 取证 02｜现场流程与操作边界 / Docker 与容器 | [docker-evidence-02.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-02.md) | 32 | 2 |
| Docker 取证 03｜容器与镜像 / Docker 与容器 | [docker-evidence-03.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-03.md) | 32 | 4 |
| Docker 取证 04｜日志、文件与持久化 / Docker 与容器 | [docker-evidence-04.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-04.md) | 28 | 5 |
| Docker 取证 05｜网络与 Compose / Docker 与容器 | [docker-evidence-05.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-05.md) | 16 | 3 |
| Linux 系统与服务识别 / 主机与服务 | [fic-case-03.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-03.md) | 18 | 4 |
| Web 应用取证 / Web 与数据库 | [fic-case-04.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-04.md) | 34 | 5 |
| 数据库取证 / Web 与数据库 | [fic-case-05.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-05.md) | 23 | 6 |
| 云服务与虚拟机证据定位 / 云与虚拟化 | [forensic-cloud-vm.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-cloud-vm.md) | 10 | 5 |
| MySQL 数据目录与表恢复 / Web 与数据库 | [forensic-database-recovery.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-database-recovery.md) | 70 | 9 |
| 服务器取证：从主机到云端的证据链 / 主机与服务 | [forensic-guide-server.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-guide-server.md) | 8 | 3 |
| Kubernetes 集群取证：概念、命令与实战 / 服务器集群 | [forensic-kubernetes-cluster.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-kubernetes-cluster.md) | 55 | 4 |
| 服务器面板、网站与账户证据 / Web 与数据库 | [forensic-server-panel.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-server-panel.md) | 24 | 4 |
| Linux 服务、账户与持久化排查 / 主机与服务 | [forensic-server-services.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-server-services.md) | 44 | 8 |
| 网站重构：宝塔面板与三要素实战 / 网站重构 | [forensic-website-reconstruction.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-website-reconstruction.md) | 26 | 4 |
| Git 基础与仓库识别 / 版本与源码 | [git-docker-03.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-03.md) | 13 | 4 |
| Git 提交历史分析 / 版本与源码 | [git-docker-04.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-04.md) | 14 | 4 |
| Git 文件与版本恢复 / 版本与源码 | [git-docker-05.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-05.md) | 13 | 3 |
| Git 深度取证与对象恢复 / 版本与源码 | [git-docker-06.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-06.md) | 14 | 3 |
| Git 分支 Tag Stash 分析 / 版本与源码 | [git-docker-07.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-07.md) | 11 | 3 |
| Git CTF 与源码取证完整流程 / 版本与源码 | [git-docker-08.md](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-08.md) | 11 | 3 |

生成正文对应 D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge 中同名文件，维护稿与生成正文同步。

## 2. 逐文件实际变更

### Docker 取证 01｜环境、服务与配置

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-01.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/docker-evidence-01.md`。

- **04.4 `Environment` 与代理配置**：补齐daemon直接代理配置优先级，将环境存在与真正采用/访问分层，给出下一份核对材料。
  - 改写要点：> **不要误判**：systemd 文件中存在变量，只能证明留下过该配置；`systemctl show` 对应已加载的单元属性，`/proc/<PID>/environ` 对应所选进程的启动环境。还要核对该进程使用的 `daemon.json` 和代理启动参数：daemon 直接配置的代理优先于环境变量，环境中的地址不一定是最终采用的路线。将候选代理地址与对应时段的代理访问日志、仓库请求记录交叉验证，不靠一份环境输出确认实际外联。
  - 保留内容：原systemctl与/proc命令；daemon/容器代理作用域；原代理示例及五项价值；全部标题与表格
  - 核查依据：2530fdc7be10:代理环境与日志交叉核对；official-docker-proxy:直接配置优先于环境变量
- **05.2 重点字段**：明确info是daemon默认值而非所有容器当前日志值，解释默认配置修改的作用时间。
  - 改写要点：查看 Docker 实际报告的根目录、存储驱动和**daemon 当前默认日志驱动**。默认值用于新建容器，修改它不会自动更换既有容器的日志配置；分析某个容器时，仍回到该对象 inspect 的 `HostConfig.LogConfig` 与 `LogPath`，不能把下面的全局输出套给全部历史对象：
  - 保留内容：原docker info两条命令；原JSON示例与字段表；存储数据根说明；全部标题
  - 核查依据：2530fdc7be10:info与容器LogPath分别核对；context7-docker-logging:单容器配置可覆盖默认值；official-docker-logging:既有容器不自动采用新默认配置
- **05.3 配置冲突与当前生效值**：将含糊的可能失败改为官方重复选项规则，并补错误记录与原件不改配置的操作判读。
  - 改写要点：同一选项同时通过启动参数和 `daemon.json` 设置时，Docker 会拒绝启动；即使两处填写相同值，也不能用“一致”排除冲突。先把启动命令、实际配置文件与 journal 中的重复选项报错对应起来，保存错误发生时间；不要在原件删掉一处配置或重启来消除差异。检查：
  - 保留内容：原三条查询命令；现有主单元/drop-in/进程三视角；配置冲突主题与段落位置
  - 核查依据：2530fdc7be10:配置冲突查询链；official-docker-daemon:同一选项同时来自flag与JSON时daemon不启动

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Docker 取证 02｜现场流程与操作边界

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-02.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/docker-evidence-02.md`。

- **03 服务器取证快速定位表**：为表内原有多PID不成立的代入方式增加精确使用前提与失败下一步，不修改命令块。
  - 改写要点：> 表内命令使用 HTML 的预格式化代码块，以便在 Markdown 表格中保持可复制性。读取启动参数那一行的 `/proc/$(pidof dockerd)/cmdline` 仅在 `pidof` 返回一个已核对的 PID 时有效；返回多个 PID 时逐个读取对应目录，无 PID 时保存服务状态与错误，转查单元和离线记录。不要把路径读取失败当作没有安装 Docker。
  - 保留内容：全部HTML命令及表格行；快速定位字段；原格式说明
  - 核查依据：2530fdc7be10:启动参数查询；docker-evidence-01:04.3已维护的多PID核对边界
- **05.1 一句话方法论**：把抽象回答问题/落到证据改为可执行动作和输出，限定接口不能证明完整运行历史。
  - 改写要点：> 先查包事务、systemd 单元和当前进程参数，分别记录安装来源与启动方式；再保存 Docker/CRI 可见对象的完整 ID 和原始 JSON。按每个对象的 `Mounts`、日志驱动、网络及实际数据根找到对应文件，记录采集时间、原路径和哈希。接口清单只能覆盖采集时仍可见的对象，较早的运行记录和已删除实例另用节点日志、磁盘元数据补证。
  - 保留内容：包管理/systemd→运行时→磁盘原顺序；Mounts/日志/网络/根目录；时间/ID/路径/哈希四类字段
  - 核查依据：2530fdc7be10:首轮对象与磁盘证据流程；c7613f4a6214:现场完整流程；docker-evidence-02:现有首轮与11.3时间字段

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Docker 取证 03｜容器与镜像

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-03.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/docker-evidence-03.md`。

- **01.3 时间、状态与进程**：在首个状态/进程入口补最近字段、空值与停止对象失败的具体判读，减少向后找边界的成本。
  - 改写要点：上面的 `StartedAt`、`FinishedAt` 只描述最近一次启动或退出，不能当作完整运行历史；零值、未运行状态和查询失败分别保留，旧运行需另查日志与事件。下面的 `docker top` 读取查询时的容器进程，停止容器可能报错；保存错误与状态后继续分析静态文件，不为补进程列表而启动它：
  - 保留内容：原时间字段表；原inspect格式化命令；原docker top命令；完整生命周期主题
  - 核查依据：2530fdc7be10:容器时间与状态字段；c7613f4a6214:top宿主视角；docker-evidence-03:08.2已有top失败与历史限制
- **07 Docker 镜像与容器导入导出**：明确export采集缺项并指向08.4唯一详解，避免两处重复扩写卷遮蔽细节。
  - 改写要点：**取证重点：** 容器的 Volume 内容不随 `export` 的文件系统归档导出，日志驱动数据和完整运行元数据也不会随归档保留。分别保存卷、原 inspect 和日志；卷覆盖底层目录时如何判读归档成员，统一见本章第 08.4 节，不用归档中的目录替代卷采集。
  - 保留内容：save/load/export/import原命令与表；层历史与合并文件系统区别；原日志/元数据不随export事实
  - 核查依据：c7613f4a6214:save/export范围原说明；official-docker-export:排除卷并导出底层被遮目录
- **07.1 docker commit**：补默认暂停运行进程与新建镜像影响，消除临时保留现场可能引导原件执行的歧义。
  - 改写要点：【仅在副本/仿真/授权环境执行】`commit` 把容器可写层和部分配置保存为新镜像，可用于保留副本中的调试结果，但不等于完整取证镜像，也不包含挂载 Volume 的数据。对运行中的容器，默认还会在提交期间暂停其进程；它不是无影响的现场读取。记录提交前后容器状态、新镜像 ID 与独立卷采集结果。与 Dockerfile 相比，它难以复现构建步骤，因此生产构建仍应优先使用版本化 Dockerfile。
  - 保留内容：原docker commit代码块；可写层/部分配置/不含卷事实；版本化Dockerfile建议
  - 核查依据：c7613f4a6214:commit非完整镜像及无卷；official-docker-commit:默认提交时暂停进程
- **08.4 对比 save、export、load、import 与 commit**：将查询时快照具体化为导出期间采集，说明底层目录来源并强化活体一致性与归档验收。
  - 改写要点：`export` 保存导出期间可读取的合并文件系统，没有原镜像层链；挂载卷的数据不随归档保存。卷覆盖已有目录时，归档取到的是被遮住的底层目录，而不是卷当前内容，应沿 `Mounts` 单独核对和采集卷。活体导出可能跨越文件变化，不保证数据库一致性；记录导出开始/结束时间与实际归档成员，不能只凭退出成功认定是同一时刻的完整快照。
  - 保留内容：原export/tar/sha256命令；合并视图无层链；挂载卷独立采集与数据库一致性限制
  - 核查依据：official-docker-export:底层目录导出；docker-evidence-03:08.3归档清单核验；c7613f4a6214:容器合并文件系统范围

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Docker 取证 04｜日志、文件与持久化

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-04.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/docker-evidence-04.md`。

- **01.1 先问运行时**：原句未区分活体daemon日志和离线集合，补读取位置与原文件保护，保留空路径分支。
  - 改写要点：先记录所指路径和轮转配置。现场优先通过 Docker CLI 保全可读日志；需要逐文件解析 json-file 或 local 的原日志集合时，在只读快照或已经保全的副本上操作，不直接修改或轮转 daemon 正在管理的文件。如果 `LogPath` 为空，查看日志驱动，并寻找 journald、容器运行时或 [集群节点日志位置](/knowledge/forensic-kubernetes-cluster/)。证明“某次请求发生过”时，继续核对日志时间、完整容器 ID、服务配置和相同时段的其他记录。
  - 保留内容：原inspect命令；轮转与空LogPath分支；K8s承接链接；请求证明需多源对应
  - 核查依据：context7-docker-logging:json-file由daemon专用管理；official-docker-logging:日志驱动范围；docker-evidence-04:08.2只读日志集合路线
- **02.3 Web 访问分析**：补正则候选、请求完整上下文、代理来源和成功状态码的结论边界，而不是只有关键词命令。
  - 改写要点：先从原始访问行提取时间、源 IP、方法、URI、状态码、User-Agent、Referer、响应字节数和上游地址，再用下面的正则缩小候选范围。命中 `cmd=`、`.env` 或注入词只说明记录出现了这些文本；保留完整请求行及前后错误日志，核对返回内容、实际文件和应用行为后再判断结果。代理后的源 IP 还需按当时的转发链解释，HTTP 200 也不能单独证明代码执行。
  - 保留内容：全部原访问字段；两块grep命令和正则；Web访问主题
  - 核查依据：2530fdc7be10:Web访问日志字段与URI筛选；docker-evidence-04:08.2已有200不证明执行；docker-evidence-05:代理/NAT与时间归属
- **02.5 攻击痕迹分析**：为既有攻击关键词筛选增加误报与执行确认条件，不扩大攻击技术主题。
  - 改写要点：先用反弹 Shell、下载执行、挖矿和提权关键词定位候选行，保留所在日志、时间和前后文。日志中出现 `curl`、`base64` 或 `docker.sock` 也可能来自正常运维输出或被记录的请求文本；继续对应实际进程参数、文件哈希及执行/访问记录，不按一个关键词直接写成已经执行：
  - 保留内容：原关键词grep块；原五类附加证据清单；原攻击痕迹分类
  - 核查依据：2530fdc7be10:攻击关键词与多源检查；c7613f4a6214:日志/进程/文件交叉验证；docker-evidence-03:08.2文件存在不等于执行
- **04.3 stats top diff events**：保留原表格用途全文，在表前补events窗口与256条保留边界，不改表格单元。
  - 改写要点：### 04.3 stats top diff events

`docker events` 可关联创建、启动、停止和删除事件，但历史回溯最多最近 256 条；未给截止时间时还会等待新事件。记录查询窗口与采集时间，缺少一条不能证明它未发生，旧事件继续核对节点和业务日志。
  - 保留内容：表内docker events原命令；整个表结构与其他五行；创建/启动/停止/删除四类事件
  - 核查依据：c7613f4a6214:events既有时间线用途；official-docker-events:最近256条及since/until跟踪语义
- **05 Docker 文件提取**：把笼统属性需验证细化为默认owner、-a、-L和父目录前提，避免复制后属性被当原证据。
  - 改写要点：`docker cp` 可从运行或停止容器提取，但不会自动创建缺失的目标父目录，先确认输出目录存在。复制结果记录完整容器 ID、原路径、提取时间和哈希；默认提取到主机后的 UID/GID 属于执行复制的本机用户，不能据此推断原文件所有者。需要保留源 UID/GID 时核对 `-a` 的结果，使用 `-L` 时另记录软链目标；权限、扩展属性和稀疏特性仍需与原记录逐项比较。
  - 保留内容：原四行cp命令表；停止容器提取事实；原路径/时间/哈希与扩展属性/稀疏验证；后续主机到容器操作影响
  - 核查依据：c7613f4a6214:文件提取与属性需复核；official-docker-cp:停止容器可读、目标owner、-a/-L与父目录

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Docker 取证 05｜网络与 Compose

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/docker-evidence-05.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/docker-evidence-05.md`。

- **01.3 还原容器通信关系**：为现有宿主ss查询补namespace范围与空输出判读，保留ID/IP的时间关联。
  - 改写要点：> `bridge` 网络中的容器 IP 可能在重建后变化，记录“时间点 + 容器完整 ID + 网络 ID + IP”，不能只记 IP。宿主机上的 `ss` 只显示该会话所在网络命名空间的套接字，不能仅凭没有列出容器内监听就判断应用未启动；继续对照容器网络模式、端口发布、转发规则与应用日志。
  - 保留内容：原ss/ip/bridge/iptables/nft命令块；时间/完整容器ID/网络ID/IP组合；网络模式与发布路径
  - 核查依据：2530fdc7be10:宿主监听与网络关系核对；docker-evidence-05:01.2网络命名空间模式与05.3分层入口
- **03 Docker Compose**：补Compose ps运行状态/项目集合范围，不改原表命令；保留down精确删除范围并统一变更提示。
  - 改写要点：`docker compose ps` 默认只显示所选项目的运行中容器；首轮还需包含已停止对象，并把输出的完整容器 ID 与 Docker 全局清单对应。查询前核对工作目录、Compose 文件与项目名，同名服务可能属于不同项目，项目列表不等于主机所有容器。

**操作影响：** docker compose down -v 删除项目声明的命名 Volume 及所移除容器附带的匿名卷，但不删除 external 卷；down --rmi all 会删除服务镜像。它可能破坏卷、可写层与复现条件，【仅在副本/仿真/授权环境执行】，须先保全相关卷、可写层与配置，只在隔离副本中演练并记录实际对象范围。
  - 保留内容：原13条Compose命令；原stop/down对比表；命名/匿名/external卷与rmi范围；保全隔离副本及记录对象要求
  - 核查依据：c7613f4a6214:Compose ps及stop/down原对比；official-docker-compose-ps:默认只运行中、--all包括停止对象
- **05.4 Compose 定义与运行状态比较**：将环境变量来源细化为多文件顺序和shell覆盖，给出实际比较字段，防止分析机环境改变解析结论。
  - 改写要点：在副本用 `docker compose config` 展开时，记录工作目录、项目名、Compose 版本、按顺序使用的 `-f` 文件和 `--env-file`，以及参与变量替换的 shell 环境。多个 Compose 文件会合并，shell 变量可覆盖环境文件中的同名值；不要让分析机预先设置的变量悄悄替换历史地址或镜像名。输出可能含秘密，受控保存后逐项比较 ports、volumes、网络和原容器 inspect。展开结果只说明这一组输入在解析时生成的定义，差异应保留，不通过重建容器消除。
  - 保留内容：原只读cat/hash命令；定义与运行实例不同步的边界；工作目录/文件集合/版本/敏感输出；不重建消除差异
  - 核查依据：c7613f4a6214:Compose服务定义；official-docker-compose-config:多-f合并与变量解析；official-docker-compose-interpolation:shell优先及env-file顺序

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Linux 系统与服务识别

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-03.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/fic-case-03.md`。

- **01 分析目标与操作顺序**：把抽象的可信清单改为先列对象、再查运行痕迹的直接操作说明，四个目标完整保留。
  - 改写要点：拿到 Linux 主机镜像后，先列出系统身份、分区对应关系和已发现的服务，再沿账户记录和启动配置查运行痕迹。重点回答四件事：**这是什么系统、哪些文件系统属于它、部署过哪些服务、有哪些操作与运行痕迹**。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：0047c3d2f371:主机与系统取证相关段
- **02.3 实战：核对根文件系统 UUID**：补齐现有探测命令参数及失败判读，防止空输出被误当成没有文件系统。
  - 改写要点：**示例：** `fstab` 中根目录挂载项使用 `UUID=3231e52f-5e15-44c4-b224-e29cb4201c0e`；对相应分区探测得到相同 `UUID` 和 `TYPE=btrfs`。这说明**配置中的文件系统标识与该分区元数据一致**，可作为分区对应关系的证据。

`blkid -p` 直接探测所给对象，不依赖普通缓存查询；`-o export` 将结果按 `键=值` 输出，便于保留 UUID 和类型原值。同时保存退出状态和错误：无可识别结果、读取错误和多个冲突签名不是同一种情况。非零退出时先核对分区边界、文件可读性及工具提示，不擦除签名来让输出变得单一。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`fstab`；`UUID=3231e52f-5e15-44c4-b224-e29cb4201c0e`；`UUID`；`TYPE=btrfs`
  - 核查依据：official-blkid:OPTIONS与EXIT STATUS
- **03.2 离线查询安装记录**：解释路径隔离、引号和状态字段的操作关系，不增加安装流程。
  - 改写要点：**判读重点：** 同时看包名、`Status` 和版本。`install ok installed` 表示该包被数据库登记为已安装；仅有配置残留、未完整安装或查询未命中的情况，应分别记录。查询未命中也不能排除手工部署、容器内安装或软件包数据库缺失。

`--admindir` 指定检材的软件包数据库，`--showformat` 决定每行展示的字段；包名通配符外的单引号让它们交给 dpkg-query 匹配，而不是被当前目录的 Shell 展开。保存完整输出、错误和退出状态，再区分“包未匹配”“数据库路径不存在/不可读”和“已登记但未安装完成”。本步只查记录，不执行检材内的安装或维护脚本。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`Status`；`install ok installed`
  - 核查依据：official-dpkg-query:--admindir与--showformat
- **03.4 运行现场的补充核对**：把现场补充核对接到可操作参数和非零结果判读。
  - 改写要点：记录执行环境、观察时间、监听地址、端口和关联进程。`ss` 的进程信息可能受权限限制；systemd 的总服务单元也不一定代表每个数据库实例，需继续核对实际实例与日志。仿真启动后出现的监听，只能证明仿真时的状态。

这里 `ss -tlnp` 的 `-t/-l/-n/-p` 分别限定 TCP、监听、数字地址/端口和可见进程；没有某进程字段时先检查权限，不能据此判定端口没有归属。`systemctl status` 会因单元不存在、未运行或失败而返回非零状态，保留其 Loaded/Active 与日志内容后再分类，不把所有非零结果都写成“命令没执行”。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`ss`
  - 核查依据：web-ssh-server-fc58f455acfa:ss参数；context7-systemd；web-server-doc-4458108bb741:systemctl状态与退出码

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Web 应用取证

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-04.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/fic-case-04.md`。

- **04.1 读取格式与轮转范围**：补足日志覆盖与转义，避免仅凭grep结果否定历史访问。
  - 改写要点：常见 combined 格式为 `IP - - [时间] "方法 URI 协议" 状态码 字节数 "Referer" "User-Agent"`，但实际字段由 Nginx `log_format` 或 Apache `LogFormat` 及站点日志指令决定。先从配置确认字段，再读取当前、轮转及压缩日志；Apache 日志路径与运行排错复用 [网站重构第 04.4 节](/knowledge/forensic-website-reconstruction/#044-apachehttpd-与-apachectl-的实例核对与恢复)。 对 Nginx 还要核对 `access_log off`、条件日志与最终处理 location：关闭记录、筛选条件或内部跳转都可能改变本次请求是否记录以及落在哪个日志。读取 URI、Referer、User-Agent 时按 `log_format` 的转义方式解释，保留原始行，另列解码/归一化视图；单次关键词未命中不能证明该时间段没有访问。
  - 保留内容：保留combined格式、log_format/LogFormat、轮转压缩与现有Apache交叉链接。
  - 核查依据：official-nginx-log；0047c3d2f371
- **05.4 隔离重构的独立入口**：修正只有泛化第06.2链接时具体绕密内容不易发现的问题，保持唯一详细章节。
  - 改写要点：页面、路由与业务的重构步骤集中在[网站重构](/knowledge/forensic-website-reconstruction/)，按已识别技术栈进入对应运行分支，并统一处理认证及外部依赖、验收和回滚。本页保留未修改的配置、代码与日志取证；实验结果通过材料清单和变更记录关联回来。PHP后台的字节派生、来源/角色/会话门禁、登录字段副作用与改动边界集中在[网站重构第06节](/knowledge/forensic-website-reconstruction/#062-旧式摘要复算函数名实际参数和字节链)，不新建平行操作章节。 四种具体修改前后片段及门禁验收直接进入[PHP网站后台密码绕过：四种方法与副本复现](/knowledge/forensic-website-reconstruction/#065-php网站后台密码绕过四种方法与副本复现)；本页只把未修改的代码、原摘要/配置和日志关联到该实验，不复制第二套绕过步骤，也不把成功提示或跳转等同已认证会话。
  - 保留内容：保留现有网站重构/06.2链接和字节派生、门禁、副作用、证据关联解释。
  - 核查依据：rivers-cqtkti10lne6bf932pi0；repo-website-reconstruction-065
- **06.2 不运行 JAR，也能定位包内配置**：增强包内候选配置的可复核定位，不解包执行、不改现有安全枚举示例。
  - 改写要点：候选配置另行按具体成员导出并保存摘要；同名重复成员、异常归档或缺失配置应停止自动选择。`Main-Class`、`Start-Class`、依赖名称支持入口和框架识别，但不证明其中代码曾在目标时刻运行。只取得编译包时，称其为部署包或字节码材料，不称完整源码。 每个导出的配置记录归档哈希、完整成员路径、未压缩大小和导出文件哈希，再按该路径回到包内核对。包内存在多份同名配置时按成员路径分别列为候选，不能让导出目录中的同名覆盖结果代替原归档结构。
  - 保留内容：保留重复成员停止自动选择、manifest字段、部署包/字节码非完整源码等全部内容。
  - 核查依据：official-spring-package；0047c3d2f371
- **06.3 生效配置要连到启动条件**：将外部配置原理落实为字段级证据矩阵，避免找到一个YAML就声称生效。
  - 改写要点：Spring Boot 可从包内和外部配置、活动 profile、环境变量、JVM 系统属性及应用参数取值，规则须匹配包中版本，不能找到第一个 `application.yml` 就结束。参考[外部配置机制](https://docs.spring.io/spring-boot/reference/features/external-config.html)，同时保存配置文件与参数；旧版本的 profile/YAML 分段语法需按旧实现解释。 逐个需要回答的字段列出“来源路径或启动参数—声明值—适用 profile—覆盖条件—采集是否完整”，再按对应版本的优先级判断。包内默认值、包外 profile 配置与应用参数不同值不是立即判冲突；必须先确认目标进程启动时哪些来源实际加载，以及高优先级来源是否覆盖该字段。
  - 保留内容：保留全部配置来源、版本/profile/YAML条件及现有官方链接。
  - 核查依据：official-spring-config
- **03.2 实战：证明两个名称下的内容关系**：消除查询无需checkout即绝无程序调用的含糊承诺；明确目标仓库配置作用域与低权限隔离前提。
  - 改写要点：**材料：** 网站完整工作副本与 `.git/`，目标日志。下列命令针对分析副本 `./work/site`，以直接读取树和 blob 字节为目标，无需 checkout。执行前静态审阅目标仓库的配置、include、hooks 和 attributes，在低权限隔离会话使用可信 Git；显式指定 `--git-dir` 时，配置与过滤器检查也须指向同一目标，不能只检查当前终端目录里的另一仓库。查询入口及限制见[Git首轮识别](/knowledge/git-docker-03/)，不把“没有切换工作树”当作所有配置都不会触发外部程序的保证。
  - 保留内容：原四组查询/导出/比对命令及示例关系判读不改；保留工作副本、.git、日志与./work/site对象。
  - 核查依据：本轮根读取Git show官方blob原内容说明；当前Git首轮识别既有config/include/hooks/attributes和查询入口限制

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### 数据库取证

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/fic-case-05.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/fic-case-05.md`。

- **01.2 固定 SQLite 主库、WAL 与 SHM**：补足离线和活体复制差别以及保留时间与完整性并非同义。
  - 改写要点：WAL 可能含主库尚未 checkpoint 的已提交更新，单拷贝 `.db` 会丢失对应视图。SHM 是 WAL 索引辅助文件，不是业务行的主存储；采集时仍应一起保全并记录缺失。副本目录允许工具生成必要辅助文件，原件不打开、不 checkpoint、不 VACUUM。只读打开失败时记录错误，再核对三份文件的一致采集关系与权限，不删除 WAL 后将结果称为完整数据。详细事务边界见 [SQLite WAL 说明](https://www.sqlite.org/wal.html)。

这组复制命令针对已经固定的离线材料；活体应用仍在写入时，先后复制三份文件并不自动得到同一时点，需另行取得一致快照并记录采集方式。`cp --preserve=timestamps` 保留文件时间，不替代哈希校验或一致性判断；`sqlite3 -readonly` 限定数据库连接，工具仍可能在可写的副本目录生成辅助文件。打开前保存一套未打开副本，打开后把辅助文件变化单列。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`.db`
  - 核查依据：official-sqlite-wal:WAL文件与只读数据库
- **02.2 实战：从文件名关系核对候选密钥**：说明设置密钥与验证密钥的区别，避免未知PRAGMA无输出被误判成功。
  - 改写要点：`PRAGMA key` 应在读表前设置，兼容参数必须根据目标实现确定。不要在原件执行 `rekey`、`cipher_migrate` 或导出覆盖。表结构可读且检查没有报错支持参数正确；不能由此证明采集完整，或把所有未显示的历史记录判定为从未存在。

设置 `PRAGMA key` 没有立即报错，不表示口令已经验证；随后读 schema 或表页成功才检验到实际解密。`PRAGMA integrity_check` 检查数据库结构，`PRAGMA cipher_integrity_check` 检查加密页认证，二者结果分别保留；先确认工具确实包含 SQLCipher、支持对应 PRAGMA，并记录版本，不能把普通 SQLite 对未知 PRAGMA 的空输出当成检查通过。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`PRAGMA key`；`rekey`；`cipher_migrate`
  - 核查依据：official-sqlcipher-api:Testing the Key与cipher_integrity_check
- **04.2 实战：在数据副本中定位候选记录**：补足现有原始页命令参数、偏移所属对象和定位不等于结构解析。
  - 改写要点：示例 JSON 含 `version`、`git_hash`、`ip` 和 `status_port`，可提供集群组件候选版本与地址。需要结合程序、配置和日志判定它属于哪个实例、哪次部署；重复副本或旧配置不能直接代表采集时版本。

`grep -aob` 中 `-a` 按文本读取二进制输入、`-o` 仅输出命中片段、`-b` 同时给出字节偏移；`LC_ALL=C` 固定字节级匹配环境。偏移属于当前输入文件，不是分区或整盘的全局偏移。`xxd -s 4096 -l 256` 从示例偏移读取 256 字节，真实使用时先换成命中附近的实际偏移，保留前后上下文；这两个命令只是定位，没有解析页和事务。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`version`；`git_hash`；`ip`；`status_port`
  - 核查依据：0047c3d2f371:数据库原始页段；official-grep；official-xxd
- **05.2 最近记录、关联表与分类层次**：现有注释提到同时间多条，但仍需讲清LIMIT 1与保留全部并列的不同目标。
  - 改写要点：`vod_en` 是视频自身的标识，`type_en` 是分类标识；不能因为同为拼音样式就互换。`type_id` 与 `type_id_1` 可能表示不同层级，需要由应用逻辑核对。连接前后比较行数及主键去重数，防止一对多连接放大计数。LEFT JOIN 可保留没有匹配对象的左表行；若在 WHERE 中要求右表字段等于某值，这些 NULL 行仍可能被过滤掉。参数占位符 `?` 适用于准备语句接口，不应直接作为普通客户端 SQL 的字面值执行。[MySQL JOIN 语义](https://dev.mysql.com/doc/refman/8.4/en/join.html)说明无匹配行的处理。

“最近记录”示例的 `LIMIT 1` 用于按时间、再按稳定主键选出一条确定展示行；若要回答“同一最新时间的全部记录”，先取最大时间，再保留该时间下全部主键。主键只打破展示并列，不证明同一时间戳的真实先后；时间精度不足或来源日志另有顺序时，把这些限制随结果交付。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`vod_en`；`type_en`；`type_id`；`type_id_1`；`?`
  - 核查依据：web-server-doc-52b5433c2059；web-mysql-command-c31a8e1e47f3:排名与稳定顺序
- **06.1 安装、服务与实例身份**：解释既有全盘搜索的错误隐藏和未命中边界，不删命令。
  - 改写要点：容器内原有 `lxc-attach -n <容器> -- dpkg -l` 及实例清点操作统一见[Docker 与 LXC 命令速查](/knowledge/docker-evidence-02/)。常见端口包括 MySQL/MariaDB `3306`、TiDB `4000`、PostgreSQL `5432`、TiDB 状态端口 `10080`、PD `2379/2380`、TiKV `20160`。它们只辅助定位：状态端口不是业务查询端口，客户端包不等于服务端已部署，文件搜索未命中也不能排除手工改名或容器内部安装。

最后一条 `find /` 会扫描该会话可访问的文件树；`2>/dev/null` 隐藏的是标准错误，不是证明搜索完整。首轮可以保留这种快速定位写法，但形成“未发现”的结论前，要另行记录不可读目录、未挂载卷、未进入的容器根目录或挂载命名空间和实际搜索根。需要完整审计时把错误另存分析目录，而不是继续忽略。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`lxc-attach -n <容器> -- dpkg -l`；`3306`；`4000`；`5432`；`10080`；`2379/2380`；`20160`
  - 核查依据：0047c3d2f371:4.6数据库服务清点；原命令的Shell重定向语义
- **06.2 实战：比较主库与备份库的图片记录**：补足跨实例快照与路径值/图片实体的衔接。
  - 改写要点：输出“主库未命中、备份库保存一条相关记录”时，同时给出两端 SQL、条件、行数和时间范围。只有备份中的旧版本和主库变化过程相互印证，才进一步讨论记录删除或替换；单一差异仍有其他解释。

先冻结两端各自可读状态，再使用相同字段、条件和排序比较；两次独立连接或两个实例并不共享同一事务快照。图片路径是数据库值，文件哈希是实体内容证据，分别记录路径解析基准、实际文件所在卷、文件大小及读取错误。任何一端缺卷或只取得旧备份时，差异结论限定在已经读取的两份材料，而不提升为实时主备不同步。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：0047c3d2f371:4.5全端点枚举；context7-mysql:快照边界

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### 云服务与虚拟机证据定位

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-cloud-vm.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-cloud-vm.md`。

- **04 虚拟机常见陷阱**：增加从当前顶层盘落实父链及内存覆盖的实际检查节点。
  - 改写要点：虚拟磁盘可能由增量盘、快照链和差分层组成；只分析基础盘会漏掉后续写入。动态内存、休眠与快照并非总在同一时刻。报告中应写明导出方式、快照链完整性、缺失日志及权限盲区，不从单条日志推断全部行为。 先从实例/虚拟机配置确定当前连接的顶层盘，再按磁盘元数据逐层核对父盘；逐层记录路径、格式、大小、哈希和采集范围，而不是按文件名、编号或修改时间猜链条顺序。磁盘快照是否包含内存状态要另查采集/快照条件，不能从“有快照”直接推定。
  - 保留内容：保留增量盘/快照链、时间错位和缺日志/权限边界。
  - 核查依据：official-qemu-img；0197f50d-372d-7ae5-958a-63652e6ae830；0197f50d-397f-78ce-b6d1-f9a48254c80f
- **07 磁盘仿真的分层流程**：区分离线固定副本和活体变化，给出防误接原盘的实际核对位置。
  - 改写要点：先做静态解析，再决定是否需要交互仿真。仿真会写入系统盘，应使用工作副本和差分盘/快照，记录宿主与来宾时间、网络状态及修改。不要直接启动唯一镜像，或将宿主真实磁盘误选为虚拟机设备。 【仅在副本/仿真/授权环境执行】 新写入层和格式转换目标应放在与证据基础盘分开的输出目录，启动前核对实际虚拟机磁盘路径/写入模式。`qemu-img` 查询使用中的盘也可能读到变化中的不一致状态，转换或修改更应针对停机后固定的副本链；不能仅凭只读查询命令就称活体结果为一致快照。
  - 保留内容：保留静态优先、唯一镜像/宿主盘警示及宿主/来宾时间和网络记录。
  - 核查依据：official-qemu-img；context7-qemu
- **07 磁盘仿真的分层流程**：补齐三个现有命令的关键参数判读及格式层/逻辑内容验证区别，纠正资料常见-O/-o混用。
  - 改写要点：转换格式写新文件；差分盘命令创建新的写入层并依赖指定基础盘。E01 先由支持工具导出 RAW；记录导出校验、逻辑扇区大小与整个快照链。创建 VMware VM 时匹配 BIOS/UEFI、磁盘控制器和系统类型，在启动前建立快照并关闭外部网络。 其中 `convert -f raw` 指定输入为 RAW，`-O vmdk` 指定输出格式；`create -f qcow2` 创建 QCOW2 写入层，`-F raw` 声明基础盘格式，`-b` 指向基础盘。输入格式须先核实，`-O` 与 `-o` 不能互换。格式转换后的容器字节/哈希通常不同，应记录转换命令、版本与输出哈希，并按逻辑磁盘内容复核，不把两种格式的文件哈希不相同直接判为证据内容改变。
  - 保留内容：保留全部qemu-img代码、E01/RAW导出、逻辑扇区、快照链和固件/控制器条件。
  - 核查依据：official-qemu-img；context7-qemu；0197f50d-372d-7ae5-958a-63652e6ae830
- **08 PVE 集群与 Ceph 的入口**：将已有PVE配置入口落实为逐项资源映射，保持Ceph全文受限边界。
  - 改写要点：corosync 可提供集群名、节点名/ID 与 ring 地址；storage.cfg 连接存储类型、节点和路径，VM/LXC 配置连接虚拟机 ID 与磁盘。Ceph 是分布式存储，只取得一个宿主磁盘不能假设包含完整虚拟盘；先按可读配置识别池、节点与已有备份范围，再记录缺失条件，不自拟重建参数。 实际核对时把 VM/LXC 配置中的存储 ID、卷/磁盘标识与 `storage.cfg` 的对应条目逐一关联，再记录节点限制与路径/池名；出现的磁盘名只是定位线索，不替代卷内容采集。若缺少父盘、节点或存储数据，将其列为待补材料，而不是在唯一材料上启动集群尝试补齐。
  - 保留内容：保留corosync、storage.cfg、VM/LXC、池/节点/备份范围及不自拟参数。
  - 核查依据：原第08节已存在的VM/LXC/storage.cfg字段与路径对应方法，仅细化操作组织；不匹配预览不作为新增版本细节依据
- **09 仿真副本中的口令恢复**：补齐口令恢复的修改前材料、改变字段和实验日志分离。
  - 改写要点：对 PVE 7.2 的隔离仿真副本，可按其系统条件在安装介质 Debug 环境中激活 LVM、挂载系统卷、进入 chroot 后运行 passwd。这个过程是**改变副本以恢复访问**，不会提取原口令，也不能在现役节点上当成取证读取操作。 【仅在副本/仿真/授权环境执行】 执行前保存副本配置、认证文件及哈希，记录 LVM 卷和挂载目标；`passwd` 会改写副本认证数据，启动仿真还会产生新日志。恢复后核对访问结果，并把密码重置时间、文件变化和新增登录单独登记，不据恢复后登录反推原口令或历史登录行为。
  - 保留内容：保留PVE 7.2版本前提、Debug/LVM/chroot/passwd步骤及重置非提取。
  - 核查依据：0197f50d-32ef-7472-b176-d344b993d9a8

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### MySQL 数据目录与表恢复

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-database-recovery.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-database-recovery.md`。

- **02 `.frm` 与 `.ibd` 的旧版恢复路径**：补足第一个恢复命令缺输出目录的实际前提及重定向失败判读。
  - 改写要点：创建表才会生成相应结构；discard 并不是“生成 frm 的方法”。缺少一致性导出元信息时有些版本仍可尝试导入，但结果不保证完整。所有复制、权限改动和实例启动都保留记录。

运行 `mysqlfrm --diagnostic` 前先创建示例中的 `./output` 目录。`>` 把解析输出写到分析机文件，已有同名输出会被截断；每轮使用新的输出名并记录 stderr/退出状态。成功生成文件只得到候选 DDL，随后仍按字段、索引和版本核验，不把重定向生成的空文件当作解析完成。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：既有mysqlfrm示例与Shell重定向语义
- **07.1 解码用于分析的文本**：补齐解码与grep筛选之间的实际衔接，不改伪SQL示例。
  - 改写要点：`TZ=UTC` 固定本次解析的显示时区，不能改变应用字段原本的时区语义。保存退出状态和标准错误；出现格式错误、加密或损坏时先核对版本、密钥材料与日志完整性，不跳过失败记录后声称完整恢复。`rg` 是候选定位，必须阅读其前后的 Table_map、完整行事件和事务边界，不能只抄单条命中。

先确认两个输入都属于同一已排序日志链，并把完整解码结果作为主记录。后续关键词筛选只用于导航：删除和更新的列值可能没有业务关键词，事务结束也可能落在轮转后的文件中；无命中时继续检查已经读取的范围和事件类型，不直接判定没有删除。分析文本、错误和输入哈希分别保留，避免反复执行时覆盖上一轮失败证据。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`TZ=UTC`；`rg`
  - 核查依据：web-mysql-command-a032d8cdcf91:mysqlbinlog多文件及事件过滤
- **15 实例、账户、变量、状态与只读会话**：把一致快照概念落实到具体连接/事务与跨表读取顺序。
  - 改写要点：这保证的是适用事务引擎的一致读取；MyISAM、DDL、其他实例和文件日志不在同一快照内。READ ONLY也不是“整个服务器绝不写盘”。本机5.5样本不验证该现代READ ONLY语法。连接中断后重建快照，不把跨会话输出伪装成同一时点。

在同一连接、同一事务中完成相互比较的表查询，并保留开始和结束位置；客户端自动重连、手动换连接或事务外的导出不自动继承该快照。先用 DDL 确认涉及表的引擎，其他引擎的结果另标采集时点。`COMMIT` 在这里结束只读事务，不表示服务端从未产生日志或缓存写入。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：context7-mysql:一致快照边界；web-mysql-command-46b63f434fb5
- **21.1 mysqldump：结构、全库和条件数据分别导出**：补足第三种dump的退出记录、导出目标和一致性验收步骤。
  - 改写要点：`--single-transaction`适合InnoDB一致快照，不保证MyISAM或并发DDL一致；`--quick`只影响读取方式。`--hex-blob`保护二进制值表示。`--no-tablespaces`抑制表空间管理语句，并非跳过业务数据；`--set-gtid-purged=OFF`控制dump内GTID语句，不改变原历史GTID。MySQL5.5、MariaDB或不同客户端可能没有部分选项，按实际帮助与权限组合使用。MySQL8客户端导出旧服务器时`--column-statistics=0`可处理特定兼容问题，先确认该客户端支持；旧客户端不支持此选项。例程、事件、触发器/DEFINER可能需要额外权限，失败逐项记录，别用--force制造完整备份印象。

三种导出分别命名并保存各自 stdout、stderr 和退出状态；第三个条件导出也须记录状态。先列出被导出表的引擎，再决定能否用单事务快照；导出过程中有并发建表、改表、删表、重命名或 TRUNCATE 时，记录失败或一致性缺口，不把非事务表结果包装为同一时点。后续重导入核验使用对应导出文件，不把条件子集当整库备份。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`--single-transaction`；`--quick`；`--hex-blob`；`--no-tablespaces`；`--set-gtid-purged=OFF`；`--column-statistics=0`
  - 核查依据：context7-mysql:--single-transaction；web-mysql-command-14019c0d0a4c
- **21.3 客户端TSV与服务端OUTFILE**：突出SELECT INTO OUTFILE的写文件对象并把常见错误接回实际步骤。
  - 改写要点：OUTFILE由服务端进程写，既有文件不会覆盖，需要FILE权限并受secure_file_priv限制。以上OUTFILE转义规则下SQL NULL通常写作`\N`，读回时按同样ESCAPED BY约定解释，别与文字NULL/含反斜线字符串混淆；服务端目录须事先按实验用户建立。`LOAD DATA [LOCAL] INFILE`是写入表的另一操作，默认不为查询开启LOCAL；若必须加载构造分析表，明确编码、分隔、转义、列顺序、NULL和LOCAL传输对象，不把任意日志原样导入证据表。

【仅在副本/仿真/授权环境执行】`INTO OUTFILE` 会在数据库服务端创建文件，即使语句主体是 SELECT 也属于新增输出状态。执行前确认服务端实际文件系统、目标目录、权限与剩余空间；记录服务器路径和文件摘要，再与客户端导出的分析机路径分别交付。错误若属于 FILE 权限、secure_file_priv 或同名文件已存在，不解释为业务查询没有结果。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`\N`；`LOAD DATA [LOCAL] INFILE`
  - 核查依据：web-mysql-command-1e23a57f7798:SELECT INTO OUTFILE
- **21.5 派生分析表、CRUD与事务验证**：保留原CRUD模板，补足可写状态与真正回滚核验，避免ENUM占位执行失败。
  - 改写要点：ID和状态是构造占位。ROW_COUNT只对应最近语句，不表示此前每一步的影响；需要逐步记录时在每个DML后立即查询。LIKE不完整复制触发器/外键等关联对象，派生表不作为原库结构完全保全；MyISAM的非事务写入不由ROLLBACK撤销。重建历史记录应另带输入文件哈希、事件位置、当时DDL及未知字段列，而非把推导值写成原始事实。

执行练习前确认两个主键存在、状态列能保存构造值，并记录原值。状态若为 ENUM、长度不足或有检查约束，先按已审阅的分析表 DDL 选择可存的实验值，不为套示例改原业务库。ROLLBACK 后重新查询同一主键，将行是否恢复及字段是否回到原值分别核对；仅看到 ROLLBACK 没报错不等于所有变化已撤销。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：web-mysql-command-46b63f434fb5:事务边界；本节DDL与构造占位
- **22.1 完整数据目录：启动前写独立配置**：把路径检查与ping/身份核查串成可执行验证链。
  - 改写要点：创建目录、复制、属主/权限调整仅针对核验过的实验根。复制常用`cp -a`/`rsync -a`，应记录符号链接和外部路径，确保恢复配置没有把写入重定向到原件。socket/PID不复用原服务；数据库系统用户须能访问其专用目录。MySQL8.0自动升级数据目录及跨产品不兼容尤其需控制，绝不让“较新版启动成功”替代原版本恢复说明。错误日志缺redo/undo/表空间/密钥时补齐对应材料，别直接删除文件尝试启动。

启动前逐项核对配置中的 basedir、datadir、socket、PID、日志和临时目录是否实际属于这个副本，软链及外置表空间也要检查最终实体。`mysqladmin ping` 只探测服务响应，不替代成功认证或目标身份查询；随后查询实际 datadir/socket，并与进程、日志对应，再开始业务读取。停止时只使用已经核实的实验端点。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`cp -a`；`rsync -a`
  - 核查依据：web-mysql-command-11c52255e5f7；official-mysqladmin:ping
- **23.2 只读显示、时间筛选、位置筛选**：补足时间区间闭开边界与事务截断风险，保持原坐标模板。
  - 改写要点：先解析完整链，再缩小范围。datetime按工具运行环境时区解释，秒级筛选不能单独确定同秒多个事务的先后；最终回放用经核验的事务边界位置/GTID。多文件的start/stop-position作用于输入首/末文件，位置不跨文件全局唯一。`--database`在statement/row事件、默认库与跨库语句中的筛选含义不同，先完整读取后过滤更便于审计。

`--start-datetime` 从首个时间戳达到起点的事件开始，`--stop-datetime` 在首个时间戳达到终点的事件前停止；这种窗口不自动按事务整组截取。先在完整输出中找 BEGIN/GTID、行事件及 Xid/COMMIT，再确定目标边界。筛选不到目标也要核对输入文件的实际起止范围、工具时区和解析错误，不能把“窗口无输出”当作完整阴性结论。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`--database`
  - 核查依据：web-mysql-command-a032d8cdcf91:--start-datetime与--stop-datetime
- **23.3 回放需要可执行日志和正确基线**：补足多日志同连接要求以及生成失败/部分执行的重试分支。
  - 改写要点：`--binary-mode`用于兼容包含特殊字节的回放输入，不把原SQL变为只读或去掉写操作。重放目标须隔离复制、事件调度和外部依赖，禁止把未知跨库操作送往既有实例。GTID模式、已执行GTID与重复事务须另核对；默认保留可执行日志的GTID语义，不随意加`--skip-gtids`“解决”报错。回放期间新产生的日志属于实验记录。恢复后按目标主键、状态、金额和历史镜像复核；不是“运行命令没有错误就完整还原”。

【仅在副本/仿真/授权环境执行】多文件回放按已核对的顺序生成同一份可执行输入，并由同一个 mysql 连接执行，避免跨文件语句依赖的临时表随中间断开而丢失。生成失败时保留部分输出但不执行；执行失败时保留目标副本和已到达的位置，下一轮从新的同一基线开始，不能在部分完成的目标上盲目重复回放。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`--binary-mode`；`--skip-gtids`
  - 核查依据：web-mysql-command-a032d8cdcf91:Processing multiple files；web-mysql-command-ec045c06e33c

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### 服务器取证：从主机到云端的证据链

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-guide-server.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-guide-server.md`。

- **02 有活机时建立最小现状清单**：纠正监听快照与全部连接混称，给出从端口到实际服务的记录顺序，避免照抄示例日期。
  - 改写要点：先把每个监听端口对应到 PID，再记录启动命令、执行文件、用户、systemd 单元和配置路径。这里的 `ss` 使用 `-tulpn`，显示采集瞬间的 TCP/UDP 监听套接字，不是全部已建立连接；进程字段还受采集权限影响。当前没有监听不能推定服务过去没运行，继续查 journal、轮转日志、单元配置和应用日志。`journalctl` 的时间输入按主机本地时区理解；示例起始日期须换成目标调查区间，跨主机比较时换算时区并保留原始时间。
  - 保留内容：五条原命令完整保留；PID/路径/用户/systemd/journal/轮转日志/原始时区仍全部保留。
  - 核查依据：本轮 Context7 iproute2 官方源码与 ss(8) 已读：-l 为 listening，-t/-u 为 TCP/UDP；沿原段落的活机时间与历史日志逻辑细化。
- **03 从登录与请求追到数据变动**：把抽象的层间关联改成字段到字段的记录方法。
  - 改写要点：在记录表中写清哪两个原始字段把上下两步连起来：例如请求 ID 对应用日志、会话 ID 对用户、容器 ID 对挂载、文件路径对数据库主键。保存字段所在的日志行或记录位置；只有时间接近而没有共同标识时，标为候选关系，不把它写成已经证实的执行链。
  - 保留内容：原有五种关联标识及关联不足应标为假设的结论全部保留。
  - 核查依据：本节既有请求/会话/容器/路径/主键与末节上传场景，保持同一证据链，不引入来源外事件。
- **07 不同服务架构如何归入同一条主线**：拆解多类对象挤在一起的长句，按定位路径、存储、网络和内存实际问题衔接。
  - 改写要点：定位 Linux 路径时，先确认发行版和包管理，再把用户/系统配置、启动加载器、systemd、桌面环境及日志对应到实际文件。遇到数据盘或删除文件问题，再核对分区、超级块、inode、权限及数据/元数据；缓存/swap 与网络证据分别记录采集范围。无线、VPN、防火墙和抓包要说明观察的是哪段网络、哪段时间。可疑 ELF、内核模块、凭据与动态库继续用 [Unix 内存](/knowledge/forensic-memory-unix/) 和磁盘记录交叉核验，不按工具名称新建重复题型。
  - 保留内容：发行版、包管理、配置、启动、桌面、存储元数据、swap、无线/VPN、防火墙、ELF等清单不删减。
  - 核查依据：原章节对象范围与既有 Unix 内存链接；只调整操作顺序与表达。

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Kubernetes 集群取证：概念、命令与实战

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-kubernetes-cluster.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-kubernetes-cluster.md`。

- **06.2 各类卷留下的痕迹不同**：在既有卷内相对路径主题补表达式字段和实例值核对，避免实际后端路径算错。
  - 改写要点：`subPath` 还会增加卷内相对路径，例如 PV 根 `/srv/nfs/lab/site-data`、`subPath: portal`、`mountPath: /app` 对应的候选路径是 `/srv/nfs/lab/site-data/portal/.env`。若实际字段是 `subPathExpr`，先按该 Pod 实例的环境变量引用和 Downward API 值确认展开后的子目录，不能把 `$(POD_NAME)` 之类表达式原样拼到后端路径；这两个字段不能同时设置。随后核对软链、NFS 导出映射和真实文件，路径计算只是候选位置，不是文件存在或被访问的证明。
  - 保留内容：原subPath/NFS根/mountPath示例及候选路径；全部卷类型表；软链/导出映射/实际文件核对
  - 核查依据：cd60ad7b2b42:按业务挂载定位NFS目录；official-k8s-volumes:subPathExpr由环境展开且与subPath互斥
- **08.3 按目标读取字段、事件与日志**：把通常受轮转限制细化为最新文件和前一实例，补具体采集字段与缺失下一步。
  - 改写要点：Events 通常有保留期限并可能聚合，creationTimestamp 排序不等于精确的每次发生顺序，还要读 first/lastTimestamp、eventTime、series 等实际字段。`kubectl logs` 默认只能取得该容器最近日志文件的可用内容，不能覆盖节点上的全部轮转文件；`--previous` 指向该 Pod 中同名容器的前一个实例，默认保留范围也不是所有重启历史。记录 Pod UID、容器名、当前/前一实例、采集时刻和查询错误，较早记录继续查节点轮转文件和集中日志；对象删除、驱逐或权限不足时保留缺口。命令语法见 [kubectl 速查](https://kubernetes.io/docs/reference/kubectl/quick-reference/)，日志范围见 [日志架构](https://kubernetes.io/docs/concepts/cluster-administration/logging/)。
  - 保留内容：原get/describe/logs与--previous命令；事件时间与聚合字段；原官方链接；节点文件/集中日志的承接
  - 核查依据：context7-k8s-logging:前一容器实例及默认保留一个终止实例；official-k8s-logging:logs只返回latest文件
- **09.1 配置、日志与数据位置**：默认路径表缺少kubelet两类自定义根的前提，补准确字段及空目录的下一步。
  - 改写要点：下面列的是常见路径，先从该节点 kubelet 服务参数和所用配置确认实际位置：`--root-dir` 可改变 kubelet 管理卷与 Pod 文件的根目录，`podLogsDir` 可改变 Pod 日志根。记录参数、配置路径和原始值后再映射到检材根，不因默认目录为空就认定没有 Pod 或日志。Kubernetes 常见配置目录：
  - 保留内容：原全部路径块和路径表；原containerd config/插件命令；版本和实例核对要求
  - 核查依据：2530fdc7be10:节点配置与常见目录；official-k8s-kubelet:--root-dir管理卷/文件根；official-k8s-kubelet-config:podLogsDir默认与可覆盖
- **09.4 静态日志与快照关联**：将自定义根前提接入实际离线查询，防止默认路径无输出被当删除或无活动。
  - 改写要点：`/var/log/containers` 常有软链。记录链接本身，把绝对目标重新定位到 `$EVIDENCE_ROOT` 下再读取，不能跟随到分析机自己的 `/var/log/pods`。若默认日志或 Pod 目录为空，先按前节确认的 `podLogsDir`、kubelet `--root-dir` 和 CRI inspect 日志路径继续查；自定义目录与清理缺失要分别记录。将目录中的 Pod UID、容器名、重启序号与同一节点、同一时间的 inspect 对应，部分文件未保留时只报告已取得的范围。
  - 保留内容：原find/ls/cat和ctr查询块；绝对软链检材重定位；UID/容器名/重启序号关联与清理缺口
  - 核查依据：official-k8s-kubelet-config:自定义日志根；official-k8s-kubelet:自定义Pod文件根；forensic-kubernetes-cluster:既有软链与CRI日志路径关联

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### 服务器面板、网站与账户证据

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-server-panel.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-server-panel.md`。

- **01 先识别面板与实际服务**：把面板与实际业务服务的抽象对应改为可填写的配置/进程/端口记录。
  - 改写要点：面板是管理入口，网站和数据库仍由具体服务运行。先记录操作系统、面板/服务版本、配置路径、实际端口和数据目录，再将面板中的站点记录对应到 vhost、程序路径和监听进程。分别记录面板端口、网站端口及数据库端口，避免用“面板能打开”替代网站服务确认。宝塔旧版常用 8888，较新版可能采用其他端口；错误页或端口只能提示，不能单独确定产品。
  - 保留内容：原操作系统、版本、配置、端口、目录、8888版本限制与产品识别边界保留。
  - 核查依据：原第01、02、07节与网站重构三要素，沿既有证据位置细化。
- **03 加密字段的定位与验证**：补充字段判读失败时应回查的参数，避免仅凭可打印输出下结论。
  - 改写要点：把解密结果放回原记录核对：字段预期是口令、地址还是其他配置，账户和连接地址是否对应，相邻记录是否采用同一格式。保留原密文及每层输入/输出，发现乱码或格式冲突时回查版本、密钥和 IV，不以“可打印字符串”判定成功，也不为验证口令连接检材中记录的真实远程服务器。
  - 保留内容：历史 AES 常量和 IV、全部定位符与禁止将真实远端连接当解密验证的边界保留。
  - 核查依据：原第03节的版本/密钥/IV/分层处理要求；不推扩历史固定常量适用范围。
- **06 工具与结果表**：补足工具输出为空时的具体复核动作。
  - 改写要点：[PanelForensics 与综合辅助工具](/tool/forensic-assist-tools/) 可辅助解析宝塔、1Panel 和小皮面板，但产品支持范围和已测试版本有限。把工具导出的账号、站点、任务与对应数据库表逐项对照。 先记录工具版本、输入库文件哈希和实际 schema；遇到空列表、空字段或解析报错，回到原表确认是无记录、材料缺失还是版本不支持，不把工具默认值写成取证结论。
  - 保留内容：PanelForensics/宝塔/1Panel/小皮和按表复核的既有说明保留；不新增工具支持承诺。
  - 核查依据：本轮已读综合取证与面板辅助工具第02/03/05节，未知版本与空值判读边界一致。
- **10.1 先辨别拦截位置，保存文件基线**：统一状态变更提示，明确备份/修改/重启与静态原件读取不同。
  - 改写要点：【仅在副本/仿真/授权环境执行】下列备份、修改和重启步骤针对已核对 `/www` 挂载与面板版本的仿真副本。分析原件时只读取相应路径，不执行面板代码。先把实际文件位置与软链目标对应起来，确认待修改文件及其父目录都留在这个副本的面板树内。
  - 保留内容：全部绑定方法、七文件备份/回滚、软链范围及跨版本限制保留。
  - 核查依据：原10.1—10.7仿真操作范围与当前两篇绑定来源的分支方法，不修改补丁。

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Linux 服务、账户与持久化排查

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-server-services.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-server-services.md`。

- **04 活机首轮定位示例**：补足活体命令环境、journal窗口参数和时区解释。
  - 改写要点：`systemctl cat` 展示主单元与覆盖片段；`ExecStart` 只是服务管理器配置，实际启动参数还要对照运行进程。`journalctl -u` 找不到记录时，检查持久化 journal 是否启用、日志是否轮转，以及应用是否写入独立日志目录。常见落点还包括 `/etc/systemd/system/`、`/usr/lib/systemd/system/`、`/var/log/`、`/etc/cron*`、`/var/spool/cron/` 和用户目录中的 SSH 配置。

这组命令查询当前会话的服务管理器和网络空间；离线挂载目录不运行它们来代替检材状态。`-u nginx` 按单元筛选，`--since` 限定起始时间，`--no-pager` 直接输出；没有明确时区的时间文字按分析环境解释。查询前记下环境时区，若采用 UTC 窗口，在时间参数中显式标明 UTC；输出显示的时区与输入窗口的解释分别核对。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`systemctl cat`；`ExecStart`；`journalctl -u`；`/etc/systemd/system/`；`/usr/lib/systemd/system/`；`/var/log/`；`/etc/cron*`；`/var/spool/cron/`
  - 核查依据：context7-systemd；official-journalctl:--since与--utc
- **07 登录、sudo 与 systemd journal**：让离线journal命令从直接运行变成范围/来源/空输出可核查的步骤。
  - 改写要点：压缩轮转日志另行读取，时间基准与启动周期分别保留。SSH 消息、登录记录及其版本/证据边界统一见[第 14.7 节](#147-ssh日志取证)；本节保留通用 journal 与 sudo 分析。sudo 的命令记录还需执行结果、audit 或应用日志支持，不单独证明动作完成。

`--directory` 将读取范围改为给定的 journal 目录，不合并分析机默认日志；`--list-boots` 列出材料中可见的启动周期，`--utc` 统一输出显示，`-o short-iso-precise` 保留更细的时间表示。先保存不筛选的结果，再按目标 boot/unit/time 缩小；需要判断来源时从完整字段中保留 `_MACHINE_ID`、`_BOOT_ID`、`_SYSTEMD_UNIT`、`_UID`、`_PID` 及原始时间。目录错误、权限错误、格式不兼容与确实无匹配条目分别记录，空结果不等于目标期间没有事件。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：context7-systemd:journal文件和导出字段；official-journalctl:--directory与输出模式
- **09.1 将事件时间与材料时间分开**：解释现有rg通配符和失败分类，避免检索未命中冒充全部日志阴性。
  - 改写要点：分析输出目录需先创建。压缩的轮转日志另外解读并保持原始文件，二进制 journal 通过对应解析器读取。传统 syslog 的月日/时分秒可能缺年份、时区，结合轮转、启动周期和同一账户其他日志补足；不要只提取 `09:xx:xx` 而省略日期与时区。

先按实际文件清单区分未压缩日志、压缩轮转和二进制 journal。`rg` 的命中与未命中、文件不存在/不可读是不同结果，记录 stdout、stderr 和退出状态；不要把通配符覆盖到的每个文件都当作已成功读取。压缩轮转须用对应方式读取后再检索，与当前日志保持相同的事件字段和时间基准。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`09:xx:xx`
  - 核查依据：0047c3d2f371:账户活动；cd60ad7b2b42:日志/改密段；official-ripgrep
- **12.1 先建立字段语义表**：保留原SQL并补足COALESCE隐藏空集合与全NULL的实际统计问题。
  - 改写要点：若统计不同用户数，核对稳定用户 ID 后使用 `COUNT(DISTINCT user_id)` 并列出重复与 NULL 范围；认证库的群名字段也需与关联表/配置对应，不能把 chat ID、用户 ID 和群名当同一种值。状态为成功但缺成功时间的记录单独审查，不把状态数字直接等同于每项业务都完成。

示例金额使用 `COALESCE(SUM(actual_price), 0)` 便于展示，但不能用这个 0 抹去金额缺失。汇总前单列目标记录中金额为 NULL 的数量；“没有目标记录”“有记录但金额全未知”和“已知金额合计确为零”分别交付。只在业务口径已经允许时，才把没有记录显示为 0。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`COUNT(DISTINCT user_id)`
  - 核查依据：web-server-doc-fa4aee07ee16:SUM与COUNT的NULL语义
- **14.2 sshd服务与进程**：补足未运行、查询环境错误和socket按需启动的排障分流。
  - 改写要点：`cat` 展示当前单元及覆盖片段，`show` 是服务管理器掌握的属性，不直接证明历史加载配置。Ubuntu 部分版本采用 **socket activation**：监听可显示为 systemd/PID 1，sshd 按需启动，**不是查不到 sshd 就判定 SSH 不可用**。同时核对 socket 的 `ListenStream`、触发服务、生成器/覆盖配置与实际监听；不能假定只重启 ssh.service 就改变 socket 的端口。版本差异见 [Ubuntu socket 激活说明](https://discourse.ubuntu.com/t/sshd-now-uses-socket-based-activation-ubuntu-22-10-and-later/30189/1)，单元属性见 [systemctl 手册](https://github.com/systemd/systemd/blob/main/man/systemctl.xml)。非 systemd 系统、容器或自定义启动方式按实际管理机制记录。

`systemctl status` 的 Loaded/Active 与退出状态一起保存；未安装单元、inactive、failed 和缺服务管理器不是同一结果。`pgrep -a sshd` 未命中只说明当前可见进程集合没有匹配项，先看退出状态、权限和会话归属，再走 socket 与监听分支。不要为让两条查询都出现 sshd 而重复安装或启动服务。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`cat`；`show`；`ListenStream`
  - 核查依据：context7-systemd；web-server-doc-4458108bb741；web-ssh-server-21f8328fda0a
- **14.4 sshd_config分析**：补足配置测试的进程影响和既有管道对退出状态的遮蔽。
  - 改写要点：`addr` 是客户端来源，`host` 是其解析名称，`laddr/lport` 是服务端接受连接的本地地址/端口；按版本补充所需条件。未给 `-C` 的全局结果不能代替特定 Match 分支，占位参数也不能证明真实连接会命中该策略。对照运行时 `-f`、`-o`、`-p`、socket 监听与日志，参见 [sshd 测试参数](https://man.openbsd.org/sshd.8)。离线复制配置时，`Include` 相对路径的基准通常是 `/etc/ssh`，绝对引用也可能读到分析机文件；先建立路径映射/隔离副本，不直接把一个离线主文件交给分析机默认环境解析。

测试不会启动新的监听；`-T` 输出的是本次解析得到的配置，`-t` 只做检查，两种结果均保存原始退出状态。管道后的 grep 可能返回“没有匹配行”，也可能遮住前面的 sshd 失败，因此先单独保存完整测试输出与错误，再过滤查看；不能只凭过滤结果中的一个 yes 判定整个测试成功。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`addr`；`host`；`laddr/lport`；`-C`；`-f`；`-o`；`-p`；`Include`；`/etc/ssh`
  - 核查依据：context7-openssh:sshd测试模式；web-server-doc-b997c8b05d0d:-T与-t
- **14.8.1 受控副本的协商与最小路径验证**：为已有ssh调试示例逐参数补说明，保持隧道与实验身份分支不变。
  - 改写要点：已有许可转发的 SSH 会话可访问服务端回环入口；只绑定分析机回环，右侧目标属于 **SSH 服务端所在网络空间**，容器回环不等于宿主机回环：

上一条调试命令中，`-vvv` 输出协商和认证细节，`ConnectTimeout=5` 限定连接及初始协议协商等待，`ConnectionAttempts=1` 不反复重试；`IdentitiesOnly=yes` 限制所用身份，`-i` 指定实验私钥，`-p` 指定 SSH 外部端口。这些参数不跳过服务端认证或主机身份核验。按连接、协商、认证、会话四阶段对照错误位置，只有同窗口服务端日志支持时再判断关闭原因。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改
  - 核查依据：web-server-doc-4bb49725d2ad:ssh参数
- **14.9 SSH暴力破解分析**：补足聚合之前的事件粒度和去重实操，保留阈值和入侵互证内容。
  - 改写要点：候选证据链为：大量失败 → 同账户/关联来源成功 → 异常命令/提权 → 新账户/SSH Key/Cron/systemd 等变化 → 可能发生 SSH 入侵。成功可为 `Accepted password` 或 `Accepted publickey`，但后者也可能是正常运维或另一认证路径，不能把一次公钥成功自动当密码破解结果。

先逐条标记动作和连接阶段，再计算统计量；同一连接的多次失败、同一失败在两类日志中的重复显示和不同连接是三个粒度。用原始路径/条目、时间、boot、PID/会话及客户端端口建立关联依据，记录去重规则和仍不能关联的条目；不要用去重后的 IP 数代替尝试次数，也不要把不同账户的失败直接拼成某个账户的破解链。
  - 保留内容：本节既有完整命令块、表格、示例原值及标题不改；`Accepted password`；`Accepted publickey`
  - 核查依据：web-server-doc-b997c8b05d0d:认证与日志；本页14.7既有原始事件字段

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### 网站重构：宝塔面板与三要素实战

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/forensic-website-reconstruction.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/forensic-website-reconstruction.md`。

- **01 先固定证据，再恢复可解释的业务**：统一整章变更命令的显著提示，不降低原有快照和隔离前提。
  - 改写要点：【仅在副本/仿真/授权环境执行】本文中的启停、配置、认证和数据变更命令仅适用于已建立快照、限制外联的恢复副本；静态分析阶段读取检材文件，不启动检材中的可执行程序。示例路径、域名、表名和服务名均需替换为实际核对的对象，操作流程不代表已对某份材料完成复跑。
  - 保留内容：现有所有流程、命令、恢复场景和副本操作前提完整保留。
  - 核查依据：原第01节及既有恢复流程，来源的仿真场景保持但不采用关闭整防火墙的默认步骤。
- **02 网站重构三要素：三条匹配链**：将服务链落到实际配置与连接发起位置，便于多站点排错。
  - 改写要点：先做一张部署表：`入口名称 → Web 配置文件及上下文 → 程序目录/上游地址 → 运行时实例 → 生效配置 → 数据库/缓存/存储`。有多个域名、网站或数据库时各建一行；不能从一份配置取域名、另一份配置取根目录、第三份配置取口令，再拼成一条服务链。 每行另记配置文件路径、include 上下文和材料/快照编号；连接地址注明从宿主、应用容器还是分析机发起。出现页面或数据库不一致时，先沿这一行回查，不从另一站点借配置补空缺。
  - 保留内容：三条匹配链、技术栈识别表、原始配置优先原则和全部跨章节链接不删改。
  - 核查依据：原三要素表、容器端口与SSH隧道说明，强化同一实例链而非另建流程。
- **05 数据库、容器和访问地址一起匹配**：明确隧道参数能验证哪一步，避免把转发监听成功误当数据库恢复成功。
  - 改写要点：隧道的远端地址是 SSH 服务器能够到达的地址；数据库若只监听 Unix socket，该 TCP 示例不能直接使用。转发建立不保证数据库目标可达，见 [SSH 本地转发](https://man.openbsd.org/ssh)。SSH 认证、转发许可、数据库认证及权限分别诊断；GUI 客户端采用相同路径，启用 SSH 选项时“数据库主机”从远端 SSH 主机视角填写。不要把 SSH 账户与数据库账户混为一个 root。 `ExitOnForwardFailure=yes` 让 SSH 在请求的转发无法建立（如本地端口绑定失败）时退出，不负责保证最终数据库 TCP 连接成功；仍需保留数据库客户端的实际连接结果。
  - 保留内容：两条可复制隧道/数据库命令、Unix socket限制、远端视角、GUI和不同账户体系全部保留。
  - 核查依据：本轮 OpenSSH ssh_config 官方 ExitOnForwardFailure 已读；沿现有隧道与数据库分别诊断逻辑补充。
- **08 用业务 SQL 验收，并把每处变化带回结论**：消除“第二条查询”相对编号含糊，明确基表基线、字典唯一性、连接的先后顺序。
  - 改写要点：先看基表的行数与独立订单数，再运行 `product_types` 的分组查询检查字典键是否重复。若字典重复，暂停金额合计，查时间范围/版本/语言等额外键，而不是随便取一行。确认连接键后再执行以下 `LEFT JOIN`，保留缺失关联的订单并标出缺失字段；不能用内连接默默删掉孤立业务记录。
  - 保留内容：全部SQL、LEFT JOIN、原始枚举/时间、金额精度/币种、主键和回滚细节保留；06.5四种绕密方法一字不改。
  - 核查依据：本轮已读网站恢复原博客的代码/页面/业务查询关联意图；现有SQL明确提供基表及重复字典检测，保留泛化与精度修正。

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git 基础与仓库识别

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-03.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-03.md`。

- **01.1 首轮只读检查**：补充首轮输出的实际判读，避免把暂存、未暂存和冲突混读。
  - 改写要点：`git status` 查看当前分支、暂存区和工作区变化。加上 `--no-optional-locks` 可避免部分命令为刷新索引而执行的可选写入，但不把可写文件系统变成只读证据介质。普通工作树的 `--show-toplevel` 给出根目录；`--absolute-git-dir` 给出元数据实际位置，二者应分开记录。 本页 `--porcelain=v1` 在非冲突的已跟踪路径上以 `XY` 的第一位表示索引相对 HEAD 的变化、第二位表示工作树相对索引的变化；`??` 表示未跟踪。合并冲突时两位表示各合并头的状态，应按冲突表解释，不能沿用普通两层比较；忽略文件默认不列出。
  - 保留内容：保留原status/rev-parse/可选锁解释和全部既有命令。
  - 核查依据：official-git-status；c7613f4a6214
- **02.2 在副本中检查布局**：补齐三类相对路径基准，避免副本迁移后错误指向另一个仓库。
  - 改写要点：解析相对 `gitdir:` 时，相对的是该 `.git` 文件所在目录。若指针越出已复制范围，先定位并保全依赖目录，不应在缺失副本中运行 `git init` 来“修好”证据。 依赖路径应分别解析：`commondir` 的相对值基于实际 `$GIT_DIR`，`objects/info/alternates` 的相对值基于对象库，而不是工作树或当前终端目录；在证据表中同时记录原始指针内容、解析后的路径与是否已采集。
  - 保留内容：保留gitdir解析、外置依赖保全及不得init修复的原有内容。
  - 核查依据：official-git-layout；context7-git
- **03.1 初始化、克隆与提交**：把示范操作具体落实到元数据/索引/引用变化，便于与历史记录隔离。
  - 改写要点：以下用于独立练习目录 `/work/lab/git-basics/`，用来理解命令会改哪些状态。它们不属于原始材料的识别步骤。 【仅在副本/仿真/授权环境执行】 `init` 新建仓库元数据，`add` 改写暂存索引，`commit` 创建对象并更新引用/引用日志；练习前先留存目录清单、HEAD、索引与引用状态，完成后将新对象和新时间标记为分析活动。
  - 保留内容：保留练习目录及现有完整初始化/提交代码。
  - 核查依据：c7613f4a6214；official-git-layout；official-git-commit
- **03.2 远程配置与同步**：明确同步对本地/远程证据状态的不同影响，不把取证查询与恢复训练混用。
  - 改写要点：以下是训练副本中的配置与同步写法，其中远程占位地址须替换为实际训练仓库。 【仅在副本/仿真/授权环境执行】 修改远程配置会写本地 `config`；`fetch` 更新远程跟踪引用及对象，`pull` 还可能改变本地分支、索引和工作树，`push` 可改变对端引用。现场识别只读取已保全的配置和引用，不以同步结果替换采集时状态。
  - 保留内容：保留远程占位地址、训练前提和全部同步代码。
  - 核查依据：c7613f4a6214；official-git-layout

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git 提交历史分析

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-04.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-04.md`。

- **01.2 记录作者、提交者与时间**：强化身份和多种时间来源边界，不从提交元数据单独指认操作者。
  - 改写要点：作者时间和提交者时间含义不同；rebase 或补丁导入可能保留作者时间而改变提交者时间。比较时优先保留完整哈希、父哈希与带时区时间，统一时区后再与外部日志排序。提交说明中“remove secret”“debug backup”等词只决定检查优先级，不直接证明泄露或入侵。 作者/提交者的姓名、邮箱与日期可由 Git 配置或环境变量指定；它们是对象中的声明，不等于 Linux 账户或某次 SSH 登录身份。原始 commit 时间、reflog 引用变动时间、工作树文件时间和外部日志时间分别留列，先核对各自时区与时钟条件，再判断是否能关联同一事件。
  - 保留内容：保留rebase、父哈希、时区与提交说明只作优先级的内容。
  - 核查依据：official-git-commit；official-git-log；c7613f4a6214
- **02.1 查看历史补丁**：修正默认历史补丁覆盖的隐藏边界，保留已有-p/--all/--follow示例。
  - 改写要点：`git log --no-ext-diff --no-textconv -p` 显示当前可达历史补丁，`-p --all` 扩展到现存全部引用。路径前的 `--` 区分选项与文件名。路径限定默认按该名称检查；重命名场景需在目录结构和补丁中核对旧路径，必要时对单个路径补充 `git log --no-ext-diff --no-textconv --follow -- app/config.yml`。它也不能自动跨越一切复制、拆分或复杂合并。 特别检查 merge：默认的 `-p` 不会自动展示每个合并提交相对各父提交的差异。若候选属于合并结果，先从父哈希确认父树，再按本页 `show`/`diff` 的两个明确提交比较分别核验，不能把普通补丁列表未显示该改动解释成“合并未改变文件”。
  - 保留内容：保留所有路径、参数、原始历史补丁代码和重命名限制。
  - 核查依据：official-git-log；context7-git
- **02.2 对候选提交使用 `show`**：补齐实际导出验收，防止错误命令生成空文件后被当恢复内容。
  - 改写要点：导出的文件与原始 blob 内容有关，输出文件的创建时间是分析时间，不是历史版本的修改时间。证据表应保存提交哈希、仓库路径、导出路径和文件哈希。 Shell 重定向可能先创建或截断目标输出，再发现 Git 读取失败；因此先检查该次命令的退出状态和标准错误、确认对象类型/长度及实际导出内容，再为输出文件生成哈希。只有“生成了文件且有 SHA-256”不等于导出成功。
  - 保留内容：保留提交哈希/仓库路径/导出路径/文件哈希和分析时间说明。
  - 核查依据：official-git-show；c7613f4a6214
- **04.3 搜索可达历史树的内容**：修正|| true仅处理无命中的不严谨表述，同时保留原代码及错误边界。
  - 改写要点：这里的 `|| true` 让遍历在命令返回非零时继续，但它也会掩盖对象缺失、参数或其他读取错误，并非只处理“无命中”。保留每次搜索的标准错误和原 Git 退出状态；命中、无匹配和无法读取应分别计数，不能以整个循环最终返回成功证明历史树都已检查。
  - 保留内容：保留内联|| true、遍历用途、对象缺失、标准错误及无命中/读取失败区别。
  - 核查依据：official-git-grep；c7613f4a6214

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git 文件与版本恢复

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-05.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-05.md`。

- **01.1 两种记录的含义**：补齐稳定对象身份与原始引用变动记录之间的证据关联。
  - 改写要点：这里只能先提出候选：HEAD 曾从 `9f24ac7` 移到 `6a03c11`，当前 log 中不见的提交可能仍在对象库。reflog 的日期是引用变动记录时间，不能直接替代 commit 内的作者/提交者时间。`HEAD@{1}` 会随后续操作变化，记录结果时应将其解析成完整对象哈希。 同一对象也可能出现在多次引用移动中；除了解析后的哈希，还应保留原始 reflog 文件及候选那条记录的引用名、旧/新哈希、记录时间和操作说明。仅保存 `HEAD@{1}` 的解析结果会丢掉“它如何成为候选”的本地操作证据。
  - 保留内容：保留示例短哈希、时间区别与HEAD@{1}易变结论。
  - 核查依据：official-git-reflog；official-git-layout
- **02.2 只在练习副本中观察模式**：把三副本实验与三种具体状态/记录变化关联。
  - 改写要点：以下命令分别展示语法，不能依次在同一仓库运行来比较，因为每次都会再后退一次。比较时应从同一初始副本分出三个独立目录，记录各自 HEAD 和状态。 【仅在副本/仿真/授权环境执行】 提交形式的三种 `reset` 都可能移动当前 HEAD/分支并留下引用变动；`--mixed` 还改索引，`--hard` 还改工作树。分别留存每个副本的操作前后 HEAD、索引差异、工作树差异与 reflog，使模式比较和“恢复了哪个版本”可复核。
  - 保留内容：保留同基线三目录、不能连续后退比较及原有模式表/命令。
  - 核查依据：official-git-reset；c7613f4a6214
- **03.2 工作副本中的切换与恢复命令**：补充实际选择节点，避免用版本切换替代单文件读取。
  - 改写要点：这些命令用于说明各自影响，不是必须按顺序执行的恢复流程。工作树有冲突时，切换可能拒绝执行；先保存冲突状态，不应为了继续而随手加 force。detached HEAD 表示 HEAD 直接指向提交；在此状态创建新提交后若没有建立引用，切走可能使新提交失去可达分支。 【仅在副本/仿真/授权环境执行】 按上表先明确目标是切换 HEAD/分支，还是只从指定版本恢复某一路径；记录该次命令实际影响的引用、索引和工作树。只需提取内容时继续使用上一节的只读对象导出，不为了取一份配置而切换整个分析仓库。
  - 保留内容：保留force禁止、冲突状态、detached HEAD风险及checkout/restore/switch完整示例。
  - 核查依据：official-git-reset；c7613f4a6214

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git 深度取证与对象恢复

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-06.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-06.md`。

- **02.1 基本命令与输出**：使损坏报告从抽象错误落实到受阻对象关系和覆盖范围。
  - 改写要点：这条命令忽略 reflog 作为可达性起点并报告不可达对象，用于发现只靠 reflog 保留的候选。它不删除对象。若输出为 missing 或 corrupt，先记录损坏与缺失，不能把检查失败解读为“未发现残留”。 对每次检查同时保存 Git 版本、命令、退出状态、标准输出和标准错误；将缺失/损坏哈希回连到引用它的 commit/tree 或当前索引，指出受阻的是哪段路径/祖先。一个候选能读取，只证明该次对象链已验证，不抵消同次检查中的其他 missing/corrupt。
  - 保留内容：保留--no-reflogs可达性起点、只读及原缺失/损坏解释。
  - 核查依据：official-git-fsck；context7-git
- **02.3 `--lost-found` 的影响**：明确lost-found写元数据但不等于工作树恢复，防止分析产物误归历史。
  - 改写要点：`--lost-found` 会把部分悬空对象写到实际 Git 目录下的 `lost-found/commit/` 或 `lost-found/other/`；对 blob 可写出其内容。它属于现场变更，而且不能自动还原所有原始文件名和目录。正式恢复记录仍应保留对象哈希、类型和 tree 映射，不能只保留 lost-found 文件。 【仅在副本/仿真/授权环境执行】 写出这些文件不等于移动 HEAD 或恢复原工作树，但会增加 Git 目录文件并改变该副本的目录清单/哈希；在执行前后记录新增路径和文件哈希，将它们标为工具输出而不是原仓库遗留物。
  - 保留内容：保留lost-found路径、blob行为及对象/树映射要求。
  - 核查依据：official-git-fsck；c7613f4a6214
- **04.2 沿 commit 与 tree 重建**：把前文对象模式知识接入实际树映射步骤，而不重复建立对象表。
  - 改写要点：`ls-tree -r` 对已确认 commit 的目录树展开，适合记录路径、模式与 blob 哈希。若只有 dangling blob 而找不到引用它的 tree，报告应写“恢复内容对象，原路径未确定”，不凭内容里的一段文件名猜测原位置。 导出前按 tree 的模式区分普通文件、符号链接与 gitlink：符号链接 blob 保存的是链接目标字节，gitlink 指向子模块提交而非普通文件内容。静态恢复先记录模式和对象，不因路径存在就跟随链接或启动子模块；需要复现文件系统形态时另在独立副本验证。
  - 保留内容：保留ls-tree -r、commit路径/模式/blob和孤立blob原路径不确定。
  - 核查依据：official-git-layout；c7613f4a6214

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git 分支 Tag Stash 分析

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-07.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-07.md`。

- **01.1 清点引用**：区分只读清点与实际切换并给出可复核的验收字段。
  - 改写要点：`switch <branch>` 用于分支切换；`checkout <branch>` 是兼具切换和路径恢复功能的旧式命令。它们可能改变工作树与索引，遇到未提交冲突先保全，不应强制覆盖。明确写 `refs/heads/backup` 可降低同名标签造成的歧义。 【仅在副本/仿真/授权环境执行】 清点引用时只记录完整名称和完整对象 ID；确需切换时，在独立目录先留存 HEAD、索引和工作树状态，再核对切换后的对象 ID，不以终端显示的短分支名作为恢复成功依据。
  - 保留内容：保留switch/checkout及refs/heads/backup等原token和冲突解释。
  - 核查依据：c7613f4a6214；official-git-layout
- **03.1 先列出，再查看补丁**：提供stash父链实际判读，不把一个show补丁称整个原暂存状态。
  - 改写要点：`--include-untracked` 用于把已保存在 stash 中的未跟踪部分也纳入显示，不会让从未保存过的文件出现。忽略文件是否被保存还取决于当时创建 stash 的选项。通常 stash 连接原 HEAD、索引状态和工作树状态，某些记录还有未跟踪内容父对象；不要固定假设每条都具有三个父提交。 解析时先从 stash 提交的原始父哈希核实关联对象：通常第一父对应创建时的 HEAD，第二父保存索引树，stash 自身树保存工作树。将这些树分别与当时 HEAD 比较，才能分清“已暂存修改”和“未暂存修改”；额外未跟踪父树只在该条记录确实存在时读取。
  - 保留内容：保留--include-untracked、忽略文件创建选项及不固定三个父提交的现有结论。
  - 核查依据：official-git-stash；c7613f4a6214
- **03.2 应用 stash 的改变**：补齐--index实际含义及冲突验收，原apply代码不改。
  - 改写要点：`apply` 将保存的修改应用到工作树并保留 stash 记录，可能产生冲突。默认不等于完整重建原来的暂存区状态；它还可能根据 attributes 选用 `merge.<驱动>.driver`，恢复前在独立副本静态审阅并取消不可信自定义合并驱动，不能仅凭禁用 textconv 就直接 apply。仅查看线索时优先 show，确需复现时记录应用前后的 status、diff 与冲突。分析原目录不运行 stash drop/pop/clear。 【仅在副本/仿真/授权环境执行】 若目标还包括暂存状态，`apply --index` 是尝试恢复索引和工作树，不是保证成功；冲突可能使索引恢复失败。保留本次退出状态、未合并条目和前后差异，不因 stash 记录仍存在就宣称已经还原原现场。
  - 保留内容：保留apply/show/drop/pop/clear、merge.<驱动>.driver风险及所有已有命令。
  - 核查依据：official-git-stash；c7613f4a6214

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

### Git CTF 与源码取证完整流程

涉及文件：`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content-curation/git-docker-08.md`；`D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/src/content/knowledge/git-docker-08.md`。

- **01.2 固定未提交状态**：明确流程首轮的盲区及不改索引的补采方式。
  - 改写要点：status 中的未跟踪文件需随目录保全；两份补丁不等于完整备份。不要先 reset 或清理，再检查现有修改。 普通 status 默认也不展示忽略文件；两份 diff 面向已跟踪内容，不能据“补丁为空”认定站点目录没有变化。将工作目录实际文件清单（含被忽略的配置/上传材料）与索引、HEAD 分开核对，按已有文件采集流程保全，不以 add 将遗漏文件写入索引来凑齐状态。
  - 保留内容：保留未跟踪保全、两补丁不完整及先保全不reset/清理。
  - 核查依据：official-git-status；c7613f4a6214
- **05 不可达对象与内容恢复**：把两种可达性检查的前提固定到同一证据基线，避免实验污染比对。
  - 改写要点：`rev-list --objects --all` 是可达对象枚举；`fsck` 提供不可达候选与连通性错误。普通 fsck 的起点包含 reflog 等记录，忽略 reflog 的第二份结果用于比较，不能将两份输出的差异当成矛盾。 比较两次输出时保持同一分析副本和同一批已固定引用/索引/日志，分别记录命令、起点选项、退出状态和错误；若中间进行过 reset、stash 或同步，先单列这些变更，再解释差异，不能把变更后的结果倒填为采集时状态。
  - 保留内容：保留rev-list --objects --all、fsck与忽略reflog对比原结论和命令。
  - 核查依据：official-git-fsck；official-git-reflog；context7-git
- **06.3 独立恢复与结果表**：统一恢复流程中的状态变更标记与原分析链隔离。
  - 改写要点：需要重建版本时先复制分析目录到 `/work/lab/repository-recovered/`，在该目录执行： 【仅在副本/仿真/授权环境执行】 下面的恢复分支会新建引用、移动该副本的 HEAD，并更新索引/工作树；先记录复制来源和原分析目录 HEAD，将生成的引用与文件时间标为本次恢复实验。
  - 保留内容：保留独立恢复路径及完整原始恢复命令块。
  - 核查依据：official-git-reset；c7613f4a6214

未列出的章节保持原样；逐节判断及来源状态详见同名 JSON 的 sections、sources 字段。

## 3. 仍需确认（内容已保留）

用户已于 2026-10-06 确认“暂按现有版本保留，完成本轮核查”；这些来源限制不阻断其他章节的本轮验收。

- docker-evidence-03：本轮web open不可访问且HTTP521，未取得可读关键正文。
- docker-evidence-05：本轮web open不可访问且HTTP521，未取得可读关键正文。
- fic-case-04：151725686 本轮HTTP521，知乎712211191本轮未取得正文；保留既有相关内容，不据不可见截图新增事实。140823396及jishuzhan已由同轮其他分支HTTP200实际读关键正文。
- fic-case-04：scope还关联Redis/Consul/RabbitMQ/Apache/WordPress/Django等官方URL；本轮未逐一重读其全部内容，这些完整既有节保留，本轮无对应新命令或版本结论。
- fic-case-04：跨页Git查询入口在显式--git-dir场景的配置作用域已在03.2说明；若要统一升级共享wrapper，需另按当前Git版本做构造验证。本轮保留既有查询代码块，不将入口设置写成零执行保证。
- fic-case-05：原网页当前HTTP521，现有JAVA案例细节先完整保留；本轮未重新核对不可见DDL/截图。
- forensic-cloud-vm：来源 0198c111-35d4-7e8c-a8c4-802c1dc80e87 的当前缓存哈希与registry不匹配，待核对原始保存版本与旧登记记录；保留现有有效正文，本轮不据此新增版本细节。actual=2d78f7a8bab39b768fddeb1ffc8e97b755c6ba5bdb7bf4ccfe6bf6011d1b2895；registry=5545a7a43322bdd9feecab975da091fed7d1feb6c6236bd8e334558843a46ff3
- forensic-cloud-vm：来源 pve-ceph 的当前缓存哈希与registry不匹配，待核对原始保存版本与旧登记记录；保留现有有效正文，本轮不据此新增版本细节。actual=8f2ac9ef4c5ec70f19429769b02b053bd648a549f32217c2331966550791766a；registry=c582eb27f91f3b79f173be36f6ff2be31334b3b815972111c8caef91b8efee57
- forensic-cloud-vm：PVE/Ceph页面登录后全文未读取，保留缺失节点/池/卷范围结论，不新增完整重建命令。
- forensic-cloud-vm：Proxmox pmxcfs官方页面本轮返回403；现有静态配置与集群运行态区别保留，不扩写未核验版本细节。
- forensic-cloud-vm：scope中的泛化web-goodlunatic/web-hello-memory来源ID未逐一关联全文URL；本轮新改写仅基于三份匹配Wiki缓存、PVE公开预览和QEMU官方文档。
- forensic-database-recovery：原网页当前HTTP521，现有JAVA案例细节先完整保留；本轮未重新核对不可见DDL/截图。
- forensic-database-recovery：来源URL已找回且当前相关段已读；旧缓存raw SHA256 83c624ff8ecda6e277054c15d7def7d484d9f3bb3f442da1e5773ebd0dc2088e与registry旧摘要2f248ae…不一致，仍待版本/归一化差异核对。
- forensic-server-panel：宝塔 CLI 官方页面本轮访问失败，菜单编号仍需按目标构建现场核对。
- forensic-server-services：原网页当前HTTP521，现有JAVA案例细节先完整保留；本轮未重新核对不可见DDL/截图。
- forensic-server-services：来源URL已找回且当前相关段已读；旧缓存raw SHA256 83c624ff8ecda6e277054c15d7def7d484d9f3bb3f442da1e5773ebd0dc2088e与registry旧摘要2f248ae…不一致，仍待版本/归一化差异核对。

来源访问失败、缓存校验不一致或仅公开预览的内容不据此删除，也不新增未核实版本细节。若要修订这些版本专属细节，请提供可读正文或对应构建/样本；保留现有版本限定内容。

## 4. 保全、去重及验证

全部既有标题/代码/表格逐项比对；保留原示例与技术参数，不用泛泛说明替代命令。PHP 后台四种绕密方法及旧链接锚点原样保留。
本轮只在已有段落细化实际操作与判读，没有复制新命令块、定义表或并行恢复流程。入口页承担导航，专题页承担操作细节，既有必要交叉引用不算重复文章。
完整构建、测试、隔离导入、回滚及已存在环境缺项的实际结果见 [VERIFICATION.txt](D:/winoptimizeDir/Desktop/Misc学习/ctf-atlas/.work/server-practical-review-20261006/VERIFICATION.txt)；本表不将未执行的原服务器操作写成实测。
