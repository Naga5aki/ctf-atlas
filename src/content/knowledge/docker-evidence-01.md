---
title: "Docker 取证 01｜环境、服务与配置"
summary: "确认运行时、安装方式、守护进程、配置和数据根目录，建立容器取证的基础边界。"
module: "Forensics"
track: "服务器取证"
topic: "Docker 与容器"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "2530fdc7be10", "c7613f4a6214", "web-server-csdn-151725686"]
challengeIds: []
relatedIds: []
updated: "2026-10-07"
---

手里是一台容器主机或它的离线镜像：Docker Engine、containerd/CRI 或 LXC 可能并存。本页回答六件事：装了什么、怎么启动、运行了什么、数据在哪里、访问了哪里、还能恢复什么。默认目录只作起点，最后以配置和实际文件位置为准；原始材料保持只读。

**先分清环境与取证边界 → 认出运行时组件与调用链 → 定位安装记录、版本与来源 → 读服务单元与 daemon 配置 → 按问题选第一条查询 → 按元数据独立识别 Docker 与 LXC → 离线复核安装、服务与数据根。**

<span id="01-使用原则与取证边界"></span>

## 01 先分清环境与取证边界

手里是一台还没分清现场、离线和仿真的容器主机。现在还回答不了装了什么、怎么启动、运行了什么、数据在哪里、访问了哪里、还能恢复什么。

操作顺序：先分清材料属于哪一种环境，再只读保全，对上这条结论能管到哪一层。

**1. 先写下这页要回答的范围。** 适用场景是 CTF Misc、Linux 服务器取证、应急响应和企业容器主机分析。后面每一节都回到这六个问题。

本节已核对这页要回答的六个问题，以及结论准备落在哪一种材料上；还没有检材、也还没标明环境时，下面的命令先不要开跑。每条结论旁边写明它来自离线镜像、目标现场，还是隔离仿真副本，一并留存场景和目标，以及后面各节保存的原始输出。

### 01.1 明确执行环境

终端已经打开，还没标明它是检材挂载、目标现场，还是仿真副本。环境写错，后面的时间、包和服务都会串到另一台机器上。

操作顺序：先对三种环境，再确认命令打在哪台机器，对上这条输出能解释的范围。

**1. 先按下表选定环境。** 离线镜像只解释保存时留下的状态和历史记录。目标现场只解释查询那一刻，对象还可能继续变。隔离仿真副本只解释副本上新启动的行为，新日志和改动要单独记。

| 环境 | 观察对象 | 结论范围 |
| --- | --- | --- |
| 离线镜像 | 只读挂载的配置、元数据与持久化日志 | 镜像保存时留下的状态与历史记录 |
| 目标现场 | 已核对身份的目标 shell 与 Docker/CRI 接口 | 查询时刻的运行状态，对象可能持续变化 |
| 隔离仿真副本 | 从副本启动的服务、容器和网络 | 仿真条件下的行为，新日志与改动单独记录 |

**2. 没有检材路径前缀的命令，只在目标现场或仿真会话里跑。** 本页的 `date`、`rpm`、`systemctl`、`docker`、`ss` 和 `/proc` 都属于这一类。在分析机上直接执行，得到的是分析机的信息。离线示例统一把只读挂载的 `/mnt/evidence` 当作根：

```bash
EVIDENCE_ROOT=/mnt/evidence
ls -ld "$EVIDENCE_ROOT/etc" "$EVIDENCE_ROOT/var"
```

**3. 读文件前先看是不是软链。** 绝对软链指向的文件，要在检材根下重新找，避免读到分析机文件。解析输出放在独立工作目录。

**4. 准备启动、重启、删除服务或进入容器时先停一下。** 【仅在副本/仿真/授权环境执行】这些操作会改变现场。原件只读，不运行检材里的二进制来查版本。

本节已核对这次读取落在三种环境的哪一种，离线根是不是 `/mnt/evidence`；软链越出检材根，或现场和仿真还没分开时，先不要写结论。表里的观察对象、结论范围，和实际打开的路径一致，一并留存环境类别、检材根，以及独立工作目录里的解析输出。

### 01.2 先保全，再分析

材料还在活体系统上，一启动已停止的容器就会改写日志、文件和网络。先把时间和原始输出留下，再继续看对象。

操作顺序：先记时间基准，再做只读查询，对上原始输出，不改数据根。

**1. 按下表做保全。** 时间、只读、原始输出、不改数据根、离线优先和脱敏都要留下。报告里的密码、令牌、私钥只记录位置和哈希。

| 原则 | 实战要求 | 原因 |
|---|---|---|
| 记录时间基准 | 记录当前时间、时区、主机名 | 日志关联依赖统一时间线 |
| 优先只读 | 先执行查询类命令，不启动已停止容器 | 启动容器会改写日志、文件和网络状态 |
| 保存原始输出 | 将命令、时间、标准输出、错误输出一并留存 | 便于复核与形成证据链 |
| 不直接编辑数据根目录 | 不手工修改 `/var/lib/docker/` 或 `/var/lib/containerd/` | 可能破坏元数据、层映射和恢复机会 |
| 离线优先 | 条件允许时先做磁盘快照或镜像，再在副本上分析 | 减少活体系统持续变化造成的证据污染 |
| 敏感信息脱敏 | 报告中隐藏密码、令牌、私钥，只记录位置与哈希 | 防止二次泄露 |

**2. 先记下这台机器的时间和身份。** 后面的日志都靠这个时间线往上对。

```bash
date -Is
timedatectl
hostnamectl
uname -a
cat /etc/os-release
id
```

**3. 确认授权后再碰 Docker。** 加入 `docker` 组通常等价于获得宿主机高权限。目标现场上执行 Docker 命令前，应确认授权范围。守护进程不可用时，优先做离线文件分析，不要为了方便查看而启动服务。

本节已核对当前时间、时区、主机名，以及这次只做了查询；守护进程起不来时，还没有在线容器清单，改走离线文件。命令、时间、标准输出和错误输出留在一起，一并留存上面这组基础环境输出。不手工修改数据根目录。

<span id="02-docker-整体架构"></span>

## 02 认出运行时组件与调用链

手里已经知道这台机器在用容器，还分不清客户端、守护进程和运行时各管哪一层。下面先对组件，再看调用链，最后看有没有另一套集群运行时。

操作顺序：先对组件角色，再顺着调用链往下，对上实际进程和数据根。


### 02.1 核心组件速查

进程名已经看到几个，还对不上谁负责镜像、谁负责把容器跑起来。先用这张表把角色和取证价值分开。

操作顺序：先对组件名，再看进程或套接字，对上它能证明的那一类痕迹。

**1. 按下表认组件。** 客户端、守护进程、containerd、shim、runc、容器和仓库分开记。某一层的输出不能代替整条调用链。

<details>
<summary>展开运行时组件速查表</summary>

| 组件 | 角色 | 常见进程或接口 | 取证价值 |
|---|---|---|---|
| Docker Client | 用户侧命令行客户端，将请求发送给 Docker API | `docker`、Unix Socket `/var/run/docker.sock` | 命令使用痕迹、远程上下文、连接目标 |
| `dockerd` | Docker 守护进程，管理镜像、容器、网络、卷 | `dockerd`、`docker.service` | 启动参数、代理、数据根目录、日志驱动、远程 API |
| `containerd` | 管理镜像内容、快照、容器生命周期 | `containerd`、`containerd.sock` | 现代 Docker/Kubernetes 的运行时证据核心 |
| `containerd-shim` | 每个运行中容器与 `containerd` 之间的中间层 | `containerd-shim-runc-v2` | 将容器生命周期与 PID、命名空间关联；守护进程重启后仍可维持容器 |
| `runc` | 按 OCI 规范创建容器进程、命名空间和 cgroup | `runc`，通常短时出现 | 底层运行时版本、运行时替换和逃逸风险调查 |
| Container | 镜像的可运行实例 | 容器进程、可写层、挂载、网络命名空间 | 应用、攻击痕迹、凭据、运行时数据 |
| Registry | 存放和分发镜像 | Docker Hub、Harbor、私有仓库 | 镜像来源、供应链、外联目标、账号凭据 |

</details>

本节已核对每个名字对应的进程或接口，以及它能证明什么；表里没有出现的进程，要到服务单元和数据根里继续找。进程名、套接字路径和组件角色写在同一行，一并留存这张对照，以及后面采到的进程和接口。

### 02.2 Docker 调用链 ASCII 架构图

组件名字有了，还看不出一条命令要经过谁才落到容器进程。先按这张图从上往下对。

操作顺序：先从客户端往下看，再对套接字和运行时，对上容器主进程那一层。

**1. 按图从上往下读。** 用户、脚本或 Compose 先到客户端，再到 dockerd，然后是 containerd、shim 和 runc，最后才是容器里的进程。

```text
用户 / 脚本 / Docker Compose
            |
            | docker CLI / REST API
            v
+---------------------------+
| Docker Client             |
+---------------------------+
            |
            | /var/run/docker.sock 或 TCP API
            v
+---------------------------+
| dockerd                   |
| 镜像 / 容器 / 网络 / 卷   |
+---------------------------+
            |
            | gRPC
            v
+---------------------------+
| containerd                |
| 内容存储 / 快照 / 生命周期 |
+---------------------------+
            |
            | 每个任务对应 shim
            v
+---------------------------+
| containerd-shim-runc-v2   |
+---------------------------+
            |
            | OCI runtime
            v
+---------------------------+
| runc                      |
+---------------------------+
            |
            | namespaces + cgroups + rootfs
            v
+---------------------------+
| Container 主进程及子进程  |
+---------------------------+
```

**2. 图是结构，不是这台机器此刻的进程表。** 实际有没有这些进程，回到服务状态和 `/proc` 里核对。

本节已核对一条调用从客户端落到容器进程要经过的层次；图上有的层次，这台机器上可能并没有对应进程。后面采到的套接字、进程名和这张图的某一层对得上，一并留存这张调用链，以及实际进程命令行。

### 02.3 集群运行时的识别入口

同一台机器上可能既有 Docker Engine，也有 Kubernetes 节点的运行时。现在还不知道端点和数据根是哪一套。

操作顺序：先核对服务、端点和数据根，再决定是不是集群节点，对上 CRI，而不是默认目录。

**1. 先把两套运行时分开。** Docker Engine 与 Kubernetes 节点的运行时可能并存。集群层级、Node / Pod / Container 的关系及 CRI 关联流程见 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/)。

**2. 在已确认的目标会话或仿真副本里核对端点与数据根。**

```bash
systemctl status kubelet containerd crio 2>/dev/null
ls -ld /var/lib/containerd /var/lib/docker /var/lib/kubelet 2>/dev/null
command -v crictl && crictl info
crictl ps -a
```

`crictl` 缺省端点可用 `--runtime-endpoint`/`--image-endpoint` 指定；数据根以进程参数、配置和实际目录三者对账为准，默认目录只是起点。

本节已核对这台机器上实际的服务、端点和数据根；只看到一套目录时，还不能排除另一套 CRI。服务名、端点和数据根来自同一台节点，一并留存核对过的服务、端点和数据根路径。

<span id="03-docker-安装信息定位"></span>

## 03 定位安装记录、版本与来源

包名对不上时，还不能判断装没装、何时装、从哪来。下面按 RPM、安装日志和事务记录往下对。

操作顺序：先查包记录，再对安装日志和事务，对上时间、版本和来源。


### 03.1 RPM 查询

发行版像 RPM 系，但包名不一定叫 docker。只搜一个名字，会把别的安装方式漏掉。

操作顺序：先列相关包，再读版本和安装时间，对上二进制是不是同一次安装。

**1. 在 RHEL、CentOS、Rocky Linux、AlmaLinux 等 RPM 系上先列出名字里带 docker 的包。**

```bash
rpm -qa | grep docker
```

**2. 扩大范围。** 把 `containerd.io`、`moby-engine` 以及 containerd、moby、runc 都搜进去，避免只命中其中一个名字。

```bash
rpm -qa | grep -Ei 'docker|containerd|moby|runc'
```

**3. 查看指定包的版本、安装时间、厂商和来源包。** 包不存在时，错误输出也留下，再回到上一步的实际包名。

```bash
rpm -qi docker-ce
rpm -qi docker-ce-cli
rpm -qi containerd.io
```

**4. 需要制表时，改读精确字段。** 名字、版本、架构、安装时间、厂商、打包者和源码包各占一行。

```bash
rpm -q --qf 'NAME=%{NAME}\nVERSION=%{VERSION}-%{RELEASE}\nARCH=%{ARCH}\nINSTALLTIME=%{INSTALLTIME:date}\nVENDOR=%{VENDOR}\nPACKAGER=%{PACKAGER}\nSOURCERPM=%{SOURCERPM}\n' docker-ce
```

**5. 只发现二进制、没有 RPM 记录时，继续查静态包、安装脚本和手工复制痕迹。** 下面先找命令位置，再看版本。这些版本命令只在已确认的目标会话或仿真副本执行，不运行离线检材里的程序。

```bash
command -v docker dockerd containerd runc
readlink -f "$(command -v dockerd)"
docker version
dockerd --version
containerd --version
runc --version
```

**6. Debian/Ubuntu 系改用 dpkg 与 apt 日志。** 发行版是 Debian/Ubuntu 时，RPM 命令不适用；离线检材要指定它自己的包数据库和日志根。

```bash
dpkg -l | grep -iE 'docker|containerd|moby|runc'
# 离线检材改读它自己的 dpkg 数据库
dpkg --admindir="$EVIDENCE_ROOT/var/lib/dpkg" -l | grep -iE 'docker|containerd'
grep -nEi 'docker|containerd|runc' "$EVIDENCE_ROOT"/var/log/dpkg.log*
ls "$EVIDENCE_ROOT"/var/log/apt/history.log* 2>/dev/null
```

包名、版本、安装时间和命令实际路径；没有 RPM/dpkg 记录时，还要静态包、安装脚本或手工复制才能说明来源。`rpm -qi`（或 dpkg）的字段和 `command -v` 的路径写在一起。版本输出来自已确认的目标会话或仿真副本；包查询、精确字段和版本命令的原始输出。

### 03.2 YUM 安装日志

包已经列出来，还分不清是首次安装、升级还是卸载。当前日志和轮转文件要一起搜。

操作顺序：先搜当前日志，再搜压缩日志和 DNF 日志，对上安装、升级或卸载。

**1. 搜索当前日志和轮转文件。** 记录命中的文件名、行号和完整上下文。

```bash
grep docker /var/log/yum.log*
```

**2. 历史日志已经 gzip 压缩时，改用下面这条。** 仍然记下文件名和上下文。

```bash
zgrep -iE 'docker|containerd|runc' /var/log/yum.log*.gz
```

**3. 较新的 RHEL 系里，`yum` 可能由 DNF 实现。** 再查 DNF 的两处日志。权限或路径错误单独留下。

```bash
grep -iE 'docker|containerd|runc' /var/log/dnf.log* /var/log/dnf.rpm.log* 2>/dev/null
```

**4. 按时间线表解释命中行。** 日志缺失时，去查 journal、shell history、RPM 数据库和文件时间，并写明哪些轮转文件没打开。

| 现象 | 可能含义 | 复核方式 |
|---|---|---|
| `Installed` | 首次安装或重新安装 | 与 RPM `INSTALLTIME`、history 事务时间比对 |
| `Updated` | 包升级 | 对照旧版本、当前版本和事务 ID |
| `Erased` | 包被卸载 | 查卸载后是否残留 `/var/lib/docker/` |
| 日志缺失 | 被轮转、清理、改用 DNF 或非包管理器安装 | 查 journal、shell history、RPM 数据库、文件时间 |

本节已核对某一行是 `Installed`、`Updated` 还是 `Erased`，以及它落在哪个日志文件；日志被轮转、清理或改走 DNF 时，这一段安装历史还没补全。命中行和 RPM `INSTALLTIME`、history 事务时间能对上。`Erased` 之后还要看 `/var/lib/docker/` 是否残留，一并留存命中的文件名、行号和完整上下文。

### 03.3 YUM History

日志行有了，还缺事务号、执行用户和当时的命令行。用 history 把同一次安装收成一条。

操作顺序：先列事务，再筛相关包，对上某一次事务的时间和来源。

**1. 先列出安装事务。** 记下编号、时间和命令概要。

```bash
yum history
```

**2. 再筛 Docker 相关的包。** 包名按上一步实际装过的名字替换；下面是常见的三个。

```bash
yum history packages-list docker-ce docker-ce-cli containerd.io
```

**3. 打开某一个事务。** 看时间、用户、命令行、来源和包变更。把命令里的事务 ID 换成上一步看到的编号，占位文字不能直接敲进 shell。

```bash
yum history info 事务ID
```

**4. DNF 系统再补两条。** 同样先列表，再打开具体事务。

```bash
dnf history
dnf history info 事务ID
```

本节已核对某一次事务的时间、用户、命令行、来源和包变更；history 打不开或工具版本对不上时，回到日志文件和 RPM 数据库。`yum history info` 或 `dnf history info` 的原文，和日志里的同一时段对得上，一并留存事务列表和这一次 info 的完整输出。

### 03.4 如何确定安装时间、版本和来源

时间、版本和来源还各说各的。最近一次 RPM 时间可能只是重装或做镜像的时间。

操作顺序：先对安装时间，再对客户端和守护进程版本，对上仓库和厂商字段。

**1. 按下表选择证据。** 升级时间不等于首次安装时间。Client 与 Server 版本可能不同。RPM 厂商字段只能说明包元数据，不能单独证明下载 URL。

| 要回答的问题 | 首选证据 | 辅助证据 | 注意事项 |
|---|---|---|---|
| 安装时间 | RPM `INSTALLTIME`、`yum history info` | `/var/log/yum.log*`、`/var/log/dnf*` | 升级时间不等于首次安装时间 |
| Docker 版本 | `docker version` 的 Client/Server、`rpm -qi` | `dockerd --version`、二进制哈希 | Client 与 Server 版本可能不同 |
| 安装来源 | YUM/DNF 事务仓库、RPM Vendor/Packager | repo 文件、shell history、下载缓存 | RPM 厂商字段只能说明包元数据，不能单独证明下载 URL |

**2. 再看仓库配置和已安装包的来源信息。** 仓库文件、`yum info` 和 `dnf repoquery` 分开保存。

```bash
grep -RniE 'docker|download\.docker\.com|moby|containerd' /etc/yum.repos.d/ 2>/dev/null
yum info installed docker-ce
dnf repoquery --installed --info docker-ce 2>/dev/null
```

**3. 把 RPM 安装时间和 YUM/DNF 安装事务放在一起比。** 最近的 RPM 时间可能来自重装或镜像制作。要找首次安装，继续找更早的事务和日志。日志缺失时写明哪些轮转文件未取得。

本节已核对最早留存的安装记录、当前版本，以及仓库或厂商字段；没有更早事务或下载缓存时，下载 URL 还不能定。`INSTALLTIME`、`yum history info`、`/var/log/yum.log*`、`/var/log/dnf*`、`docker version`、`rpm -qi` 和 `dockerd --version` 里实际读到的字段，一并留存上表用到的命令输出、仓库文件命中行，以及未取得的轮转文件名单。

<span id="04-docker-服务systemd分析"></span>

## 04 从单元文件读到进程命令行

安装记录有了，还不知道 dockerd 实际是怎么被拉起来的。下面从单元文件读到进程命令行。

操作顺序：先读单元和 drop-in，再对已加载属性和进程参数，对上这次真正的启动命令。


### 04.1 定位服务文件

主单元可能在两个目录，管理员还可能用 drop-in 把启动命令改掉。只读一份主文件，会漏掉实际配置。

操作顺序：先读发行版主单元，再读 drop-in，对上被覆盖的启动命令。

**1. RPM 系常见主单元在这里。**

```text
/usr/lib/systemd/system/docker.service
```

**2. Debian/Ubuntu 等系统也可能在另一处。** 以检材里真实存在的那份为准。

```text
/lib/systemd/system/docker.service
```

**3. 管理员覆盖通常在 drop-in 或同名单元。** 两个位置都要列出来。

```text
/etc/systemd/system/docker.service.d/*.conf
/etc/systemd/system/docker.service
```

**4. 先读 `/usr/lib/systemd/system/docker.service`，再读管理员的 drop-in。** 重点找 `ExecStart`、环境变量和依赖项的覆盖值。

本节已核对主单元路径，以及有没有 drop-in 覆盖启动命令；只读了主文件时，实际 `ExecStart` 还可能在 drop-in 里。主文件和每一份 `*.conf` 的路径都打开过，一并留存主单元、drop-in 和 `/etc/systemd/system/docker.service` 的原文。

### 04.2 核心命令

磁盘上的单元和正在跑的进程可能不是同一套参数。状态、拼接结果、已加载属性和进程命令行要一起留。

操作顺序：先看状态和 PID，再读拼接后的单元，对上进程命令行和 journal。

**1. 查看当前状态、PID、最近日志和失败原因。** 失败原因留在这条输出里，先不要重启。

```bash
systemctl status docker
```

**2. 查看 systemd 最终拼接后的主单元和 drop-in。** 这里能看到磁盘上的覆盖关系。

```bash
systemctl cat docker
```

**3. 查看单元实际加载路径、环境变量和启动命令。** 这是服务管理器已经记下的属性。

```bash
systemctl show docker -p FragmentPath -p DropInPaths -p ExecStart -p Environment -p EnvironmentFiles
```

**4. 查看进程实际命令行，防止磁盘配置和当前运行状态不一致。** 先从 ps 确认一个 dockerd PID，再把演示值换成这个 PID。多个 PID 要逐个读。

```bash
ps -ef | grep '[d]ockerd'
# 从 ps 输出确认一个 dockerd PID，替换下面的演示值
DOCKER_PID=1234
tr '\0' ' ' < "/proc/$DOCKER_PID/cmdline"
```

**5. 查看守护进程日志。** 第二条的时间窗口换成这次要看的起止时间。没有输出时，再查持久化 journal 和轮转，不先写成服务没运行过。

```bash
journalctl -u docker --no-pager
journalctl -u docker --since '2026-09-25 00:00:00' --until '2026-09-26 00:00:00' --no-pager
```

本节已核对服务状态、加载路径、启动命令，以及进程实际收到的参数；没有 PID 时，还没有运行中的命令行，改查单元和安装记录。`systemctl cat`、`systemctl show` 和 `/proc` 里的 cmdline 三份都在，一并留存状态、拼接单元、属性、命令行和这段 journal。

### 04.3 `ExecStart` 取证重点

启动参数里的数据根、配置文件和监听地址，会改变后面去哪找容器和日志。先把参数认全，再对三份输出。

操作顺序：先读参数表，再看 drop-in 有没有清空启动命令，对上 cat、show 和 cmdline。

**1. 按下表解释参数或形态。** TCP 监听参数本身不证明认证或 TLS 已经启用。写了数据根之后，不能只查默认的 `/var/lib/docker`。

<details>
<summary>展开 ExecStart 参数表</summary>

| 参数或形态 | 含义 | 取证关注点 |
|---|---|---|
| `-H fd://` | 通过 systemd socket 激活或监听文件描述符 | 同时检查 `docker.socket` |
| `-H unix:///var/run/docker.sock` | 本地 Unix Socket | 权限、Socket 所属组、是否被容器挂载 |
| `-H tcp://0.0.0.0:2375` | TCP API 监听线索 | 仅该参数不证明认证状态；继续核对 TLS、访问控制和请求日志 |
| `-H tcp://...:2376` | 常见 TLS 端口约定 | 端口号本身不能证明 TLS 已启用，核对参数和证书 |
| `--data-root` | 修改 Docker 数据根目录 | 后续不能只查 `/var/lib/docker` |
| `--config-file` | 指定非默认配置文件 | 以该路径为主分析 |
| `--registry-mirror` | 指定镜像加速/镜像源 | 关联供应链与外联日志 |
| `--insecure-registry` | 允许不安全仓库 | 中间人攻击、恶意镜像和内网仓库风险 |
| `--log-driver` | 设置默认日志驱动 | 决定日志是否在容器 JSON 文件中 |

</details>

**2. 若 drop-in 清空并重定义 `ExecStart`，常见写法是先出现一个空值。** 空值那一行也要留下，它表示把原来的命令清掉。

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --data-root=/data/docker
```

**3. 三份输出各看各的。** `systemctl cat docker` 看磁盘上的主单元和 drop-in。`systemctl show docker` 里，`show` 读取 systemd 已加载的属性。`/proc` 中的 `/proc/<PID>/cmdline` 看这个 dockerd 进程实际收到的参数。三份不一致时都保存，先查加载时间和进程身份，不靠重启把差异消掉。

**4. 先看 `pidof dockerd` 返回几个 PID。** 只有一个且身份已确认时，旧式 `/proc/$(pidof dockerd)/cmdline` 才指向一个进程目录。多个 PID 要逐个读取。没有 PID 就查服务状态和安装记录，写成“当前没有这个进程”，不写成“未安装”。

本节已核对数据根、配置文件、监听参数和日志驱动分别来自哪一份输出；三份不一致，或没有 PID 时，生效参数还不能收成一条。cat、show 和 cmdline 里的同一参数能并排对上，一并留存参数表的命中项、drop-in 原文，以及三份不一致时的全部输出。

### 04.4 `Environment` 与代理配置

单元里出现了代理地址，还不知道拉取镜像时有没有真的走它。配置、进程环境和代理日志要分开对。

操作顺序：先读环境变量，再对进程环境和 daemon 配置，对上同一时段的代理访问。

**1. 先看典型写法。** 示例里的地址只说明配置指向哪里，要换成检材里的实际值。

```ini
[Service]
Environment="HTTP_PROXY=http://192.168.0.99:4780"
Environment="HTTPS_PROXY=http://192.168.0.99:4780"
Environment="NO_PROXY=localhost,127.0.0.1,.corp.local"
```

**2. 验证已经加载的环境，再看这个进程自己的环境。** `DOCKER_PID` 用上一节确认过的 PID。

```bash
systemctl show --property=Environment docker
tr '\0' '\n' < "/proc/$DOCKER_PID/environ" | grep -iE '^(http|https|no)_proxy='
```

**3. 按下表解释三个变量。** 示例中的 `192.168.0.99:4780` 表明 `dockerd` 的部分外联可能经该代理转发。

| 字段 | 功能 | 取证意义 |
|---|---|---|
| `HTTP_PROXY` | Docker 守护进程访问 HTTP 目标时使用的代理 | 可解释镜像拉取为何经过特定主机；代理日志可补全访问时间线 |
| `HTTPS_PROXY` | Docker 守护进程访问 HTTPS 目标时使用的代理 | 可关联外部仓库、域名和下载行为 |
| `NO_PROXY` | 指定不经过代理的主机、域名或网段 | 暴露内部仓库、服务域名和信任边界 |

**4. 再在单元、drop-in 和 Docker 配置里搜同一组变量和地址，并看现在有没有连到这个代理。** 没有连接时，只说明采集这一刻没看到，不说明过去没用过。

```bash
grep -RniE 'HTTP_PROXY|HTTPS_PROXY|NO_PROXY|192\.168\.0\.99|4780' /etc/systemd/system /usr/lib/systemd/system /etc/docker 2>/dev/null
ss -ntp | grep '192.168.0.99:4780'
```

**5. 记下这组配置能解释的五件事。** 镜像拉取的完整日志可能只在代理上。未知代理可能是转发通道，或被改过的运维配置。仓库看到的来源 IP 可能是代理 IP。代理 URL 里若有用户名或密码，脱敏保存，这些凭据可能已出现在配置、进程环境或备份里。`dockerd` 的代理用于守护进程拉取镜像等操作，不等于自动给容器内应用设置代理；容器自身的 `Env` 仍要单独检查。

**6. 再确认代理是否真被用过。** 读 systemd 文件，记下配置过的地址。用 `systemctl show` 看已加载属性，用 `/proc/<PID>/environ` 看所选进程的启动环境。再读该进程使用的 `daemon.json` 和代理启动参数。daemon 里的直接代理配置优先于环境变量，不能只按环境输出选地址。到该地址的代理日志和镜像仓库请求记录中找同一时段的访问。找到了再说明实际外联；只有配置时，就只记录配置。

本节已核对配置过的代理地址，以及它出现在单元、已加载属性还是进程环境里；没有同一时段的代理日志或仓库请求时，还不能写成实际外联。环境变量、`daemon.json` 和代理日志里的地址、时间能对上，一并留存单元片段、Environment 输出、进程环境、配置检索和连接检查。凭据只留位置和哈希。

<span id="05-docker-配置文件分析"></span>

## 05 定位 daemon 配置与生效字段

启动参数还要和 daemon 配置对上，否则数据根、仓库和日志位置都会找错。下面先定位文件，再读字段，最后看冲突。

操作顺序：先定位配置文件，再读数据根、仓库和日志字段，对上当前留下的值。


### 05.1 默认位置与定位

还没打开 daemon 配置，数据根和仓库设置都可能不在习惯的路径上。先确认文件在不在、什么时候改过。

操作顺序：先找默认配置路径，再看时间和内容，检查 JSON 格式，先不改文件。

**1. Linux 常规 rootful Docker 的默认配置在这个路径。** 文件不存在就回到启动参数里的 `--config-file`。

```text
/etc/docker/daemon.json
```

**2. 查看文件和元数据。** 修改时间、权限和内容一起留。

```bash
ls -l --full-time /etc/docker/daemon.json
cat /etc/docker/daemon.json
stat /etc/docker/daemon.json
```

**3. 只验证 JSON 语法，不修改原文件。** `jq` 能解析，只说明语法过得去，不说明守护进程已经加载它。

```bash
jq . /etc/docker/daemon.json
```

本节已核对配置文件的路径、修改时间和原文；文件不存在，或 `jq` 报错时，还要改找启动参数里的配置路径。`ls`、`stat` 和文件原文指向同一路径，一并留存文件元数据、原文和语法检查输出。

### 05.2 重点字段

文件打开了，还要把字段翻译成后面去哪找容器、日志和镜像。默认目录只是没改配置时的起点。

操作顺序：先读字段，再分清默认日志和单个容器的日志，对上实际数据根。

**1. 下面是一份示例。** 字段以你手里的文件为准，示例地址不要当成这台机器的真实仓库。

```json
{
  "data-root": "/data/docker",
  "registry-mirrors": ["https://mirror.example.com"],
  "insecure-registries": ["192.168.10.20:5000"],
  "proxies": {
    "http-proxy": "http://192.168.0.99:4780",
    "https-proxy": "http://192.168.0.99:4780",
    "no-proxy": "localhost,127.0.0.1,.corp.local"
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "5"
  }
}
```

**2. 按下表看每个字段把证据带到哪里。** 监听、仓库、代理、日志和存储驱动分开记。

<details>
<summary>展开 daemon 配置字段表</summary>

| 字段 | 作用 | 取证要点 |
|---|---|---|
| `data-root` | 修改 Docker 数据根目录 | 后续容器、卷、元数据应从该目录定位 |
| `registry-mirrors` | 设置镜像加速器或镜像代理 | 关联镜像来源、DNS、证书和代理日志 |
| `insecure-registries` | 允许不安全或非受信 TLS 仓库 | 检查恶意镜像、明文传输和内部仓库 |
| `proxies` | 配置 daemon 的 HTTP/HTTPS/NO_PROXY | 关联外联与代理服务器证据 |
| `hosts` | 设置 Docker API 监听端点 | 特别关注 `tcp://0.0.0.0:2375` |
| `log-driver`、`log-opts` | 设置容器默认日志驱动与轮转 | 决定日志位置和可恢复时间范围 |
| `storage-driver` | 指定存储驱动 | 决定文件层目录结构和恢复方法 |

</details>

**3. 全局输出先看三项：数据根目录、存储驱动、daemon 当前默认日志驱动。** 默认日志驱动只用于新建容器，改默认值不会自动改已有容器。要找某个容器的日志，再看它自己 inspect 中的 `HostConfig.LogConfig` 与 `LogPath`。

```bash
docker info
docker info --format 'DockerRootDir={{.DockerRootDir}} StorageDriver={{.Driver}} LoggingDriver={{.LoggingDriver}}'
```

**4. 没有改数据根时，默认 Docker 数据目录是：**

```text
/var/lib/docker
```

**5. 另找 containerd 的实际存储目录。** 从 Docker 连接参数找出它使用的 containerd 实例。读这个实例的配置，记下根目录和 snapshotter，再去找镜像内容与快照。`data-root` 不能代替外部 containerd 的根目录。独立实例常用 `/var/lib/containerd`，Docker 管理的实例也可能放在 Docker 数据根下。目录存在时还要核对进程是否正在使用。

**6. 在线以 `docker info`、进程参数和挂载对应，离线以 daemon 配置与实际元数据目录对应。** 若只找到配置，写“存在此配置”，不能写成“已生效”。默认目录和重复选项规则见 [Docker daemon 配置](https://docs.docker.com/engine/daemon/)。

本节已核对数据根、存储驱动、默认日志驱动，以及某个容器自己的 `LogPath`；只有配置、还没对上进程或元数据目录时，这些字段还只是“存在此配置”。`docker info` 的三项和配置文件里的同一字段一致，或已经记下差异，一并留存配置原文、info 输出、容器 LogPath，以及 containerd 根目录和 snapshotter。

### 05.3 配置冲突与当前生效值

同一选项可能同时写在启动参数和配置文件里，服务会因此起不来。先把冲突找出来，不先改文件。

操作顺序：先并排保存启动命令、配置和 journal，再看重复选项，对上失败时间。

**1. 先找重复配置，不先改文件。** 同一选项同时写在启动参数和 `daemon.json` 中会让 Docker 拒绝启动，两处值相同也会冲突。把启动命令、实际配置文件和 journal 报错一起保存，记下失败时间。下面的命令用于读取这些材料；原件不删配置、不重启。

```bash
systemctl cat docker
cat /etc/docker/daemon.json
journalctl -u docker -b --no-pager
```

本节已核对启动参数和 `daemon.json` 里有没有同一选项，以及 journal 里的失败时间；还没看到报错时，不能把“文件里写了”写成服务曾经启动成功。三份材料里的选项原文和报错时间，一并留存拼接后的单元、配置文件原文和这次启动的 journal。

<span id="06-docker-参考规范"></span>

## 06 按问题查官方说明页

字段含义还拿不准时，用下面几页核对架构、数据目录、代理、存储驱动和日志驱动的说明。这些页用来对照你手里的版本，不代替检材里的路径。

操作顺序：先按卡住的问题选一页，再核对默认路径和字段名，对上检材里的实际文件。

**1. 按问题打开对应说明。** 架构、daemon 默认数据目录、代理、overlay2、json-file 日志和 containerd 配置各看各的页。

- [Docker 架构概览](https://docs.docker.com/get-started/docker-overview/)
- [Docker daemon 配置与默认数据目录](https://docs.docker.com/engine/daemon/)
- [Docker daemon 代理配置](https://docs.docker.com/engine/daemon/proxy/)
- [Docker OverlayFS/overlay2 存储驱动](https://docs.docker.com/engine/storage/drivers/overlayfs-driver/)
- [Docker json-file 日志驱动](https://docs.docker.com/engine/logging/drivers/json-file/)
- [containerd 配置文件说明](https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md)

本节已核对卡住的字段在说明里的默认含义；说明里的默认路径和检材里的实际路径还没对上时，以检材为准。检材中的参数或字段名，和所选说明页讲的是同一项，一并留存用过的说明页，以及检材里对应的配置原文。

<span id="07-从问题定位到证据对象"></span>

## 07 按问题选第一条查询（Git 与容器分开）

问题已经落到容器对象（或 Git 仓库），还没决定先读哪条命令。下面先保全，再按问题选第一条查询；Git 取证的读取链从 [识别仓库与保全元数据](/knowledge/git-docker-03/) 开始，历史与对象分别在 [提交与差异](/knowledge/git-docker-04/)、[log 与 reflog](/knowledge/git-docker-05/)、[对象与恢复](/knowledge/git-docker-06/)；两类对象的命令分开跑。

操作顺序：先保全状态和副本，再按问题选第一条命令，对上对象 ID 和下一步材料。


### 07.1 保全与工作副本

还没保存状态，就准备重置仓库、进入容器或清理对象。这些动作会改掉现场。先留一套未改副本。

操作顺序：先保存状态、日志、配置和哈希，再在副本里演练会改数据的命令，对上对象 ID 和文件范围。

**1. 先保存状态、日志、配置、挂载关系和文件哈希。**

**2. 会改容器的命令另放。** 【仅在副本/仿真/授权环境执行】Docker 的 `exec` 新增进程，`stop`、`rm`、`prune` 会停止或删除内容。需要演练这些操作时，先留一套未改副本，再逐次记录命令和结果。Git 的 `reset`、`checkout`、`stash apply` 会改索引、工作树或引用，其处置见 [log、reflog 与 reset 模式](/knowledge/git-docker-05/)与 [stash 与引用](/knowledge/git-docker-07/)。

**3. 记录主机、时间、目录、仓库根、完整容器 ID、镜像 ID 与仓库摘要。** 导出成功后还要检查文件大小、哈希、路径和内容范围。命令退出成功不能证明证据完整。所有示例容器名、事务 ID、路径和哈希使用前应从实际材料确认，尖括号占位符不能直接输入 shell。

**4. 查询陌生 `.git` 前先做静态检查。** 在低权限隔离副本里静态读 config、hooks、include 和 attributes，禁用不可信 fsmonitor、clean/process 驱动，看补丁时加 `--no-ext-diff --no-textconv`；完整方法与限制见 [识别仓库与元数据](/knowledge/git-docker-03/)。

本节已核对未改副本还在，对象 ID、路径和哈希已经记下；只看到命令退出成功、还没核对文件范围时，证据还不算完整。导出文件的大小、哈希、路径和内容范围，和记录里的对象 ID 一致，一并留存状态、日志、配置、挂载、哈希，以及副本上每次演练的命令和结果。

### 07.2 首个命令与下一步

问题已经有了，第一条命令选错就会漏掉退出容器、旧提交或悬空对象。先按问题选，再保存原始输出。

操作顺序：先按下表选第一条查询，再保存容器读取链，对上下一步该去的对象；Git 对象另走 Git 取证。

**1. 按下表从问题走到下一条命令，并记住限制。** 占位路径和容器名先换成清单里确认过的值。

| 分析目标 | 首个查询 | 下一步与限制 |
| --- | --- | --- |
| 容器服务不可达 | `docker ps -a` | 查状态、监听、端口发布、网络与应用日志 |
| 容器启动失败或异常 | `docker logs --tail 100 web` | 尾部只是定位，继续保全完整时间范围和日志驱动 |
| 提取日志或源码 | `docker cp web:/path/file .` | 输出到工作目录，核对原路径、软链、内容与哈希 |
| 删除容器后数据仍存在 | `docker volume ls` | 用卷 inspect 和历史 Mounts 关联，绑定目录回到主机 |
| 首轮最短路径 | `docker ps -a --no-trunc` | 再枚举镜像、卷、网络，按对象 ID 保存原始 JSON |

**2. 容器读取链在已确认的目标会话里跑。** Git 侧先在 [识别仓库与保全元数据](/knowledge/git-docker-03/) 固定状态，两类对象不要混在同一条记录里。

```bash
# 容器读取链，目标会话已确认
docker ps -a
docker logs --tail 100 web
```

**3. 按问题选下一步。** 清单缺少退出容器，先补全容器列表。发现挂载，去找其卷或宿主机目录。发现异常日志，保全原日志再查相同时间的文件和进程。各篇入口：[现场流程](/knowledge/docker-evidence-02/)、[容器与镜像](/knowledge/docker-evidence-03/)、[日志与持久化文件](/knowledge/docker-evidence-04/)、[网络与 Compose](/knowledge/docker-evidence-05/)。

本节已核对当前问题对应的第一条命令，以及命中的提交、容器、卷或日志；尾部日志、空的容器列表或过期的 reflog，都还要按表里的限制继续补。原始输出里的对象 ID、路径或哈希，和表中“下一步”要打开的材料是同一个，一并留存两条读取链的原始输出，以及选中的下一步对象。

<span id="08-docker-基础概念与环境识别"></span>

## 08 分清对象并核对命令版本

Dockerfile、镜像和容器还混在一起，环境里也不确定用的是哪一版 Compose。下面先分清对象，再查命令版本。

操作顺序：先分清镜像、容器和卷，再查 CLI 与 Compose 版本，对上实际用的那一份程序。


### 08.1 Dockerfile Image Container 关系

三个词还叠在一起，不知道该去构建文件、镜像层，还是容器可写层里找数据。先把关系和每个对象分开。

操作顺序：先看谁构建出谁，再对表里的对象，对上该去层、可写层还是卷。

**1. 关系按这个顺序走。** 构建得到镜像，运行才得到容器。

Dockerfile  
   ↓ docker build  
Image  
   ↓ docker run  
Container

**2. 按下表分开记。** 构建文件、镜像、容器、卷、网络和 Compose 各留各的痕迹。删掉容器之后，卷里的数据仍可能还在。

| 概念 | 定义 | 取证关注点 |
| --- | --- | --- |
| Dockerfile | 构建镜像的指令文件 | 复制文件、安装软件、环境变量、入口命令 |
| Image | 只读镜像层与配置的组合 | 层历史、摘要、构建痕迹和残留敏感数据 |
| Container | 镜像的运行实例，另有可写层 | 进程、日志、文件变化、端口和运行参数 |
| Volume | 由 Docker 管理的持久化数据区域 | 数据库、上传文件和删除容器后的残留 |
| Network | 容器间和主机间通信边界 | 服务发现、IP、端口与横向访问路径 |
| Docker Compose | 用 Compose 文件定义多服务应用 | 服务关系、变量、挂载、网络和启动顺序 |

本节已核对手里的对象是构建文件、镜像、容器、卷、网络，还是 Compose 定义；只有镜像、没有容器清单时，运行参数和可写层还要另找。对象类型和表里的取证关注点一致，一并留存这张关系，以及后续按对象保存的路径或 ID。

### 08.2 环境检查

命令名有带空格和带连字符的两种 Compose，还不知道这台机器实际跑的是哪一份程序。版本要落到路径和输出上。

操作顺序：先看客户端、守护进程和插件版本，再找独立程序的路径，对上采集时的那一版。

**1. 先按下表分清三条版本命令各自回答什么。** 新版环境优先使用 docker compose。`docker-compose` 是旧式独立命令，历史环境可能仍保留；两者不要在同一操作记录中无说明地混用。

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker --version | 显示 Docker CLI 版本 | 确认客户端是否安装 |
| docker info | 显示 Docker Server、存储驱动与运行概况 | 确认守护进程、平台和资源概况 |
| docker compose version | 显示 Compose 插件版本 | 确认可使用新版 docker compose 子命令 |

**2. 旧环境的 Compose 版本这样查。** 在已经确认身份、程序来源可信的目标会话或仿真副本中，先找实际命令位置，再查看独立程序的版本。

```bash
command -v docker-compose
# 只在上一步已确认程序实体与来源后执行
# 输出完整保存，不只抄文件名或界面缩写
docker-compose version
```

**3. 分清两条命令各查什么。** 上表的 `docker compose version` 查当前 CLI 插件，新增命令查独立程序。旧 Python 版 Compose v1 常用 `docker-compose`；现代独立版或兼容包装也可能保留这个命令名，不能只凭连字符断定 v1。插件方式的后续版本仍使用 `docker compose`，具体版本以实际输出为准。

**4. 离线材料不运行检材程序查版本。** 先静态核对安装记录、安装或升级日志、保存过的版本输出，以及实际程序或插件路径和文件哈希。常见独立程序候选在 `/usr/local/bin/docker-compose`；插件还可能在用户的 `.docker/cli-plugins/`、系统的 `docker/cli-plugins/` 或额外配置目录。路径只作查找起点，结合 PATH、Docker CLI 配置和启动材料确定使用哪一份。只有文件名或历史安装命令时，分别写“发现该程序候选”或“曾安装该版本”，不填成采集时有效版本。

**5. 文件头里的版本标记另算。** `compose.yaml` 顶层的 `version: '3.8'` 等值是旧文件格式标记，不是 Compose 程序的版本号。记录 CLI 或独立程序版本、实际路径、配置文件哈希和查询环境。分析机自己的 Compose 版本单独列为解析工具信息，不代替目标版本。

本节已核对实际命令路径、CLI 插件或独立程序的版本输出；只有文件名或历史安装命令时，采集时的有效版本还没确认。版本输出、程序路径和文件哈希来自同一份候选程序，一并留存版本全文、路径、哈希、配置文件哈希，以及查询是在目标会话、仿真还是离线静态核对。

<span id="09-docker-与-lxc-的独立识别流程"></span>

## 09 按元数据独立识别 Docker 与 LXC

主机上有容器痕迹，但还不能凭网段判断它属于 Docker 还是 LXC。下面先比元数据，再沿配置追根目录。

操作顺序：先比运行时元数据，再对根目录和地址，对上定义文件，而不是默认网段。


### 09.1 运行时元数据比网段更接近归属证据

主机上有数据库连接配置，Docker 清单里却没有对应实例。现在要确定它属于宿主机、Docker 还是 LXC。

操作顺序：先查配置、根文件系统和运行时对象，再解释桥和 IP，对上定义文件。

**1. 先看元数据，再解释网络。** 默认网桥名、常见网段、空容器清单都只提供线索。按下表比目录、根文件系统、镜像、网络、命名和辅助证据。多个运行时可以在同一主机并存。

| 维度 | Docker 常见痕迹 | LXC 常见痕迹 | 复核要求 |
| --- | --- | --- | --- |
| 元数据目录 | data-root 下的 `containers/<ID>/config.v2.json`、`hostconfig.json` | `/var/lib/lxc/<name>/config` | 先确认实际根目录，再保存完整对象标识 |
| 根文件系统 | overlay2 或所选 snapshotter 管理的层与快照 | `lxc.rootfs.path` 指向 dir、ZFS、Btrfs 等后端 | 跟踪真实路径和挂载，不能仅按目录名认定 |
| 镜像信息 | 传统 image store 的 `imagedb` 或 containerd 内容/元数据 | 模板或其他根文件系统；LXD 的存储组织另行核对 | 不把 Docker 专用布局套到所有容器 |
| 网络 | 常见 `docker0`、自定义 bridge 与网络元数据 | 可配置 `lxcbr0`、veth、dnsmasq | 桥名和 IP 网段均可改，需要对应配置、端点与时间 |
| 命名 | 完整容器 ID 与可读名 | 容器名和相应定义目录 | 名称可变，应同时保存 ID 或定义文件标识 |
| 辅助证据 | dockerd、containerd、容器状态与日志 | LXC 定义、进程、租约和服务日志 | 多个运行时可以在同一主机并存 |

**2. 到目标现场做清点。** 下面几条地址命令的输出范围不一样，都留下，再逐条对照。

```bash
docker ps
docker ps -a
lxc-ls -f
ip addr
ip a
ip -br addr
ip -4 addr
ip -br addr show type bridge
brctl show
```

**3. 清点结果按下面读。** `docker ps` 为空：补查 `-a`，再确认连接的是哪个 daemon、使用哪个数据根。已删除容器不会重新出现在清单里。`lxc-ls -f` 记录当前工具看到的容器状态和 IP。`brctl show` 需有 bridge-utils；缺工具时另查接口，不判定为“没有网桥”。`ip addr` 显示当前会话所在网络命名空间。在容器里查到的接口可能与宿主机不同。

本节已核对元数据目录或定义文件，以及它和哪一个运行时对应；只有桥名或网段、没有定义文件时，归属还只是线索。表里的目录、根文件系统路径和清点输出指向同一个对象，一并留存清点命令的原始输出、实际数据根和定义文件路径。

### 09.2 实战：沿数据库配置追到 LXC 根目录

应用配置指向一个名字，Docker 清单里没有它。材料是只读挂载的主机快照，要追到 LXC 的根目录，而不是先改网络。

本节是 app-db LXC 租约识别的完整主线；docker-evidence-02、docker-evidence-05 中的同类片段回到本节核对。

操作顺序：先读 hosts 和 LXC 定义，再解释根目录和租约，对上地址属于哪一个容器。

**1. 先固定材料和时间。** 证据在应用配置与 hosts、LXC 定义、网桥配置、容器状态及 DHCP 租约。材料只读挂载在 `/mnt/evidence`，采集记录固定为 `2025-05-18T03:20:00Z`，输出写入 `/work/output/lxc-identify/`。演示中应用连接 `app-db`，hosts 将其映射为 `10.20.3.41`，采集时的 `lxcbr0` 地址为 `10.20.3.1/24`。这些配置、时间和输出是构造示例，不表示对实际检材已复跑。

**2. 离线读取已经定位的定义、hosts 和租约。**

```bash
EVIDENCE_ROOT=/mnt/evidence
mkdir -p /work/output/lxc-identify
cat "$EVIDENCE_ROOT/etc/hosts"
ls -ld "$EVIDENCE_ROOT/var/lib/lxc/app-db"
cat "$EVIDENCE_ROOT/var/lib/lxc/app-db/config"
cat "$EVIDENCE_ROOT/var/lib/misc/dnsmasq.lxcbr0.leases"
```

**3. 对定义片段。** 看根文件系统、网卡类型、所连的桥和 MAC。

```ini
lxc.rootfs.path = dir:/srv/app-db
lxc.net.0.type = veth
lxc.net.0.link = lxcbr0
lxc.net.0.hwaddr = 00:16:3e:20:03:41
```

**4. 租约和固定采集时间一起读，并计算哈希。**

```text
1747540800 00:16:3e:20:03:41 10.20.3.41 app-db *
```

```bash
date -u -d '@1747540800' '+%Y-%m-%dT%H:%M:%SZ'
sha256sum "$EVIDENCE_ROOT/var/lib/lxc/app-db/config" \
  "$EVIDENCE_ROOT/var/lib/misc/dnsmasq.lxcbr0.leases" \
  > /work/output/lxc-identify/metadata.sha256
```

**5. 先解释租约时间。** 输出到期时间为 `2025-05-18T04:00:00Z`，比固定采集时间晚 40 分钟。租约的第一列是到期时刻，不是地址分配开始时间。MAC、IP、主机名与定义可相互印证。这条记录不证明该时间段内发生过某次数据库连接。

**6. 再解释根目录。** `dir:/srv/app-db` 指定目录形式的根文件系统，离线实际位置是 `$EVIDENCE_ROOT/srv/app-db`。数据库配置从这个根目录或它的额外挂载继续查找。若定义使用 ZFS、Btrfs 或其他后端，跟踪相应存储，不把 `dir:` 示例当成通用格式。

**7. 找出地址属于哪个容器。** 先读 `lxc.net.0.link=lxcbr0`，确认定义连接的桥。再比较租约中的 IP、MAC、主机名和时间，与定义、现场 IP 和访问日志对应。应用地址与桥同网段时，先把它作为待查地址。

**8. 租约文件是空的时候继续查。** 静态 IP 可能没有 DHCP 租约。空 leases 文件不能说明没有网络活动，也不能说明 dnsmasq 正在运行，或某个 IP 就属于该容器。继续查静态地址、租约清理、配置路径、服务进程和日志，并记录未取得的材料。

**9. 把已经查到的事实写出来。** 例如：LXC 定义指定 app-db 的根目录，并连接 lxcbr0；应用配置指向该地址。要补上某一时刻运行过或连接过，还要该时刻的运行状态或日志。Docker 清单为空，不能单独确认它是 LXC。

本节已核对LXC 定义里的根目录、桥、MAC，以及 hosts 和租约里的同一地址；没有该时刻的运行状态或访问日志时，还不能写成当时连接过数据库。定义、租约和 hosts 里的名字、MAC、IP 相互一致，哈希留在输出目录，一并留存hosts、config、租约、到期时间换算和 `metadata.sha256`。

### 09.3 实战：离线比较镜像创建字段

Docker 服务没有运行。配置把传统 image store 的 data-root 指到 `/data/docker`，要比较镜像配置里的创建记录。不要为了补一条 CLI 输出去启动 daemon。

操作顺序：先列出镜像配置文件，再读创建字段，对上原始时间字符串。

**1. 静态读取元数据。** 服务没运行时就停在文件上，不启动守护进程。

```bash
DOCKER_ROOT="$EVIDENCE_ROOT/data/docker"
ls -ld "$DOCKER_ROOT/image/overlay2/imagedb/content/sha256"
find "$DOCKER_ROOT/image/overlay2/imagedb/content/sha256" -maxdepth 1 -type f -print

# 对已确认的 JSON 配置逐个记录文件名和 created 字段
find "$DOCKER_ROOT/image/overlay2/imagedb/content/sha256" -maxdepth 1 -type f \
  -exec jq -r '[input_filename, (.created // "missing")] | @tsv' {} \;
```

**2. 扩展名可能不存在。** 传统 `imagedb` 配置文件可能没有 `.json` 扩展名，只匹配 `*.json` 会漏掉对象。保留原 JSON、文件哈希、配置字段和对应镜像 ID。标签从同一存储的引用记录关联，不凭一个配置文件编出镜像名。

**3. 按下表演示记录判读。** 这些是构造示例，用来看时间字符串怎么比。

| 演示记录 | `created` 原值 | 判读 |
| --- | --- | --- |
| 配置 A | `2025-07-08T11:20:30.123456789Z` | UTC 字符串，可保留纳秒精度 |
| 配置 B | `2025-07-09T02:10:00Z` | 在这两条有效记录中创建字段较晚 |
| 配置 C | 字段缺失 | 单独记录，不能自动排成最早或最新 |

**4. 换到同一时间基准后再比。** RFC3339 中 `Z` 表示 UTC。偏移或精度不同的字段要转换成同一时间基准后比较，仍保留原始字符串。这里比较的是配置内创建字段，不能替代本机拉取时间或容器最后运行时间。

**5. 在线时，可以用下面的格式核对展示内容。** 它核对的是 CLI 怎么显示，不改离线文件。

```bash
docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}'
```

**6. 没有这条传统路径时，先确认存储布局。** 若 Docker 使用 containerd image store，没有这个传统路径是可能的正常布局，应沿已确认的存储继续定位。不能据此认定没有镜像。

本节已核对每个配置文件的路径，以及它的创建字段原值；字段缺失，或还没换成同一时间基准时，先不要排先后。原 JSON、文件哈希和创建字段原值留在一起。标签来自同一存储的引用记录，一并留存配置文件、哈希、创建字段原值，以及在线核对时的 CLI 输出。

### 09.4 仿真连接与容器内命令

仿真后的远程会话里缺工具，还不确定这是宿主机的 SSH，还是 LXC 里的另一套 SSH。先确认会话，再决定要不要进容器。

操作顺序：先确认连到了谁，再只在副本里执行容器内命令，对上离线配置里的根目录。

**1. 先确认会话属于谁。** 看主机名、目标地址、进程命名空间和挂载。宿主机和 LXC 可能各自运行 SSH。切换终端前保存当前输出，再用离线配置核对这个会话对应的根目录和账户。

**2. 容器内命令只放在副本里。** 【仅在副本/仿真/授权环境执行】下面的命令会在 LXC 内启动新进程。`-n` 选择容器，`--` 后面才是容器内要执行的命令。

```bash
lxc-attach -n app-db -- cat /etc/os-release
```

**3. 进入容器不是在读静态磁盘。** 它可能改变访问时间或应用状态。不得在证据原件执行 `lxc-attach` 或 Docker `exec`，也不要通过卸载或删除 SSH 服务来修复连接。仿真结束时记录新增进程、日志和服务修改，再与原有配置和历史日志核对。

本节已核对当前会话对应的主机名、根目录和账户，以及容器内读到的系统信息；会话还没和离线根目录对上时，容器内输出先不要写成历史事实。离线配置里的根目录、账户，和这个会话的主机名、挂载一致，一并留存切换前的输出、容器名、完整命令，以及仿真新增的进程、日志和修改。

<span id="10-安装服务与数据根的离线复核"></span>

## 10 离线复核安装、服务与数据根

服务已经停了，在线命令不能当成历史。下面用检材里的包日志、单元和数据目录做离线复核。

操作顺序：先读安装日志，再对启动配置和数据根，对上文件里实际留下的记录。


### 10.1 建立安装时间线

检材中 Docker 服务停止，需要确定组件、版本和部署来源。分析机如果是 Kali，直接跑 `rpm -qa` 查到的仍是分析机自己的数据库。

操作顺序：先确认发行版，再读检材里的日志和仓库，对上最早安装记录和当前版本。

**1. 在检材根下搜安装日志和仓库文件。** 路径都挂在检材根上，不要改去查分析机的包数据库。

```bash
grep -nEi 'docker|containerd|moby|runc' "$EVIDENCE_ROOT"/var/log/yum.log*
zgrep -nEi 'docker|containerd|runc' "$EVIDENCE_ROOT"/var/log/yum.log*.gz
grep -nEi 'docker|containerd|runc' \
  "$EVIDENCE_ROOT"/var/log/dnf.log* "$EVIDENCE_ROOT"/var/log/dnf.rpm.log*
grep -rniE 'docker|download\.docker\.com|moby|containerd' \
  "$EVIDENCE_ROOT/etc/yum.repos.d"
```

**2. 没有命中要单独记。** 日志缺失、轮转文件未匹配或权限错误，不能把没有命中等同于没有安装。RPM 数据库位置和格式随检材版本核对。YUM/DNF history 的读取还受工具兼容性影响。不在原件执行安装、升级或修复数据库。

**3. 示例按三条分开写。** 日志先记录安装 `docker-ce` 与 `docker-ce-cli`，后来升级其中一个包；RPM 当前版本对应升级后的版本。应分别记录“最早留存安装记录”“当前登记版本”“升级事务”，不能把最近的 INSTALLTIME 当成必然的首次安装时间。仓库 URL 和 Vendor/Packager 支持来源线索，实际下载来源还要事务、缓存或代理日志。

本节已核对检材日志里的安装或升级行，以及当前登记的包版本；日志没覆盖，或还没有事务和缓存时，下载来源和首次安装时间还不能定。命中的日志路径、行号和 RPM 版本字段来自检材根，而不是分析机的 `rpm -qa`，一并留存日志命中、仓库文件命中，以及未匹配的轮转文件和权限错误。

### 10.2 对应启动配置与实际目录

单元、drop-in 和 daemon 配置都在检材里，还不知道数据根是默认目录还是另一条路径。先确认软链没有跑出检材。

操作顺序：先确认路径在检材内，再读启动命令和配置，对上候选数据根里的元数据。

**1. 先确认路径存在，软链没有越出检材根，再读主单元、drop-in 和配置。** `jq` 只检查这份 JSON 能不能解析。

```bash
# 先确认路径存在，软链没有越出检材根
cat "$EVIDENCE_ROOT/usr/lib/systemd/system/docker.service"
find "$EVIDENCE_ROOT/etc/systemd/system/docker.service.d" -type f -name '*.conf' -print
cat "$EVIDENCE_ROOT/etc/docker/daemon.json"
jq . "$EVIDENCE_ROOT/etc/docker/daemon.json"
```

**2. 路径跟着实际配置走。** 主单元若在 `/lib/systemd/system`，换成相应检材路径。若命令有 `--config-file=/srv/docker/daemon.json`，沿此路径读取；默认文件只是另一个留存记录。示例中 drop-in 清空 `ExecStart` 并指定 `--data-root=/data/docker`，代理指向 `192.168.0.99:4780`。这只能说明存在这些配置，尚不证明启动成功或代理实际被访问。

**3. 再看候选数据根里有什么。** 查看 `$EVIDENCE_ROOT/data/docker` 中的容器、卷和镜像元数据，确认这些文件是否属于候选数据根。journal 若报重复选项，保存报错、配置和发生时间。`jq` 成功只说明 JSON 能解析。Docker 是否支持这些字段、进程是否加载它们，还要看版本和启动记录。

本节已核对主单元、drop-in、配置文件路径，以及候选数据根里确有元数据；还没有启动成功或代理访问的记录时，配置只记为“存在”。启动参数里的数据根，和该目录下的容器、卷或镜像元数据对得上，一并留存单元、drop-in、daemon 配置、`jq` 输出、数据根目录列表，以及重复选项的报错和时间。

### 10.3 可复核结果的最小字段

前面的记录已经有了，复核的人还对不上环境、安装、服务和限制各缺哪一项。按最小字段把结果收拢。

操作顺序：先按表填字段，再分成四类结果，对上路径、原值和时间。

**1. 每项按下表保存。** 缺少的日志、已清理的对象、还没核对是否生效的配置、仿真产生的修改，都写进限制。

| 项目 | 保存内容 |
| --- | --- |
| 环境 | 离线、目标或仿真；主机、会话身份、时间与时区 |
| 安装 | 包名、版本、安装或事务时间、来源字段、对应日志路径 |
| 服务 | 主单元、drop-in、加载属性、PID、命令行差异与失败记录 |
| 配置 | 实际文件路径和哈希、数据根、代理、仓库、API 监听、日志与存储驱动 |
| 对象归属 | Docker/LXC/CRI 元数据、完整 ID 或定义、根目录与网络对应 |
| 限制 | 缺少日志、已清理对象、配置生效尚未核对、仿真生成的修改 |

**2. 结果按四类填写：安装记录、保存的配置、历史运行日志、当前运行状态。** 每类都写清文件路径、字段原值和时间。缺少运行日志时就记“只取得配置”。不要用仿真结果补成历史运行。

本节已核对四类结果里已经有原文和路径的那些项；缺运行日志时，当前运行状态这一类还空着。每一类旁边都有文件路径、字段原值和时间，一并留存这张最小字段表，以及未取得项的名单。
