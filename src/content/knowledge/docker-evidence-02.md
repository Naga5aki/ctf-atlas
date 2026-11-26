---
title: "Docker 取证 02｜现场流程与操作边界"
summary: "按保全、枚举、定位、提取、复核的顺序分析容器，并避开会改变证据的操作。"
module: "Forensics"
track: "服务器取证"
topic: "Docker 与容器"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "2530fdc7be10", "c7613f4a6214"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

手里是一台容器主机或它的离线镜像，Docker 服务器取证还没开始。本页给出首轮定位、整体流程、快速定位表、现场检查清单和可复核清单的固定顺序；原始材料保持只读，容器内执行、启动、停止、清理只在副本上做。

**先标明环境 → 按整体流程与首轮顺序采集 → 用定位表和检查清单固定现场 → 按问题选入口 → 分开只读查询与会改状态的动作 → 把首轮输出变成可复核清单。**

<span id="01-docker-服务器取证首轮定位"></span>

## 01 首轮定位：先标明环境与顺序

**先做这几件事：** 记录主机时间，确认 Docker/containerd/CRI，列出全部容器与镜像，再保存 inspect、日志、挂载和网络。`docker ps -a --no-trunc`、`docker info`、`docker inspect <容器ID>` 用来记录这次查询的状态；旧容器被删除后，要另外查磁盘和事件日志。

【仅在副本/仿真/授权环境执行】容器内执行、启动、停止、重启、恢复和清理会改变状态。目标现场先采集，离线材料直接读文件。提取或导出时记录取得了哪些文件、开始/结束时间及未取得内容。

手里是一台还没固定运行时的主机，容器清单也还没留下。下面先标明环境，再按顺序做第一轮采集。

操作顺序：先标明离线、现场或仿真，再列出容器和镜像，对上这次查询的对象 ID。


### 01.1 先标明分析环境

命令还没跑，终端属于分析机、目标现场还是仿真副本还没写明。环境没标，同名容器会把两台机器的结果混在一起。

操作顺序：先对三种环境，再确认终端属于目标主机，对上这条输出能解释的边界。

**1. 按下表选定本页命令怎么用。** 离线镜像不连接分析机的 daemon 来充当目标结果。目标现场只代表采集那一刻。隔离仿真只代表副本上的行为。

| 环境 | 本页命令的使用方式 | 结论边界 |
| --- | --- | --- |
| 离线镜像 | 以检材根读取配置、JSON、卷、日志；不连接分析机 daemon 充当目标结果 | 镜像中存在的记录与残留 |
| 目标现场 | 身份与连接目标已确认后，查询容器、镜像、网络、日志和进程 | 采集时刻可见状态，多个查询之间可能变化 |
| 隔离仿真 | 副本与快照基线已记录后，运行需要改变状态的操作 | 仿真行为，不能替代原现场历史 |

**2. 先确认终端属于目标主机，再运行没有检材路径前缀的命令。** 分析机上同名容器或服务的输出不要填进目标清单。

**3. 会改状态的动作另放。** 【仅在副本/仿真/授权环境执行】`exec`、`lxc-attach`、`start`、`restart`、`stop`、`kill`、`remove` 和仓库恢复会改变状态，执行前后都留记录。

本节已核对这次查询属于离线、目标现场还是隔离仿真；终端身份还没核对时，先不要把输出写进目标清单。表里的结论边界，和实际读取的路径或连接目标一致，一并留存环境类别、终端身份，以及执行前后的状态记录。

### 01.2 首轮顺序

环境已经标明，还没把容器、日志路径和数据根收成一份清单。按这个顺序做，缺了 daemon 就改走 CRI。

操作顺序：先记时间和运行时，再列出容器并做 inspect，对上日志路径、挂载和网络。

**1. 按这个顺序做第一轮。** 先记录系统时间、主机信息和已知检材来源，保留原始日志或磁盘副本。再识别实际运行时：Docker、containerd，或 Kubernetes 节点的 CRI。然后列出容器、镜像与状态，记录容器 ID、创建和退出时间。再用 `docker inspect` 确认日志驱动、`LogPath`、挂载和网络配置。最后把容器、卷、镜像和宿主机路径联系起来，再进入具体文件分析。

**2. 在已经确认的目标会话里保存这三份输出。** 容器 ID 换成清单里的完整值。

```bash
docker ps -a --no-trunc
docker info
docker inspect CONTAINER_ID
```

**3. 现场没有 Docker daemon 时改道。** 先转到 `crictl` 或 containerd 的视角。不要假定每台 Kubernetes 节点都有 `/var/lib/docker`。

本节已核对运行时种类、容器 ID，以及日志路径、挂载和网络配置；没有 daemon 时，Docker 清单还空着，要改用 CRI 和节点上的实际数据目录。inspect 里的 `LogPath`、挂载和网络，能对上清单中的同一个容器 ID，一并留存时间、主机信息、容器与镜像清单、inspect 原文。

<span id="02-docker-服务器取证整体流程"></span>

## 02 按整体流程走一遍

第一轮范围还没排成顺序，容易只查容器，漏掉安装和数据根。下面先看流程，再对每一步要回答的问题。

操作顺序：先按流程往下走，每一步只回答一个问题，对上该阶段的主要证据。


### 02.1 主流程图

步骤还是散的，不知道安装、配置、容器、网络和恢复谁先谁后。先按图把顺序固定下来。

操作顺序：先确定环境，再确认安装、服务和配置，对上容器、镜像、网络、日志和可恢复的数据。

**1. 按图从上往下走。** 环境没定时，不要跳到容器或数据恢复。每一步的输出留下来，再进入下一格。

```text
+--------------+
|  确定环境    |
| OS/时间/权限 |
+------+-------+
       |
       v
+--------------+
|  确认 Docker |
| 包/二进制/进程|
+------+-------+
       |
       v
+--------------+
|  分析服务    |
| systemd/参数 |
+------+-------+
       |
       v
+--------------+
|  分析配置    |
| daemon.json  |
+------+-------+
       |
       v
+--------------+
|  分析容器    |
| Env/Mount/IP |
+------+-------+
       |
       v
+--------------+
|  分析镜像    |
| 来源/时间/层 |
+------+-------+
       |
       v
+--------------+
|  分析网络    |
| 网络/端口/通信|
+------+-------+
       |
       v
+--------------+
|  分析日志    |
| 容器/守护进程|
+------+-------+
       |
       v
+--------------+
|  数据恢复    |
| overlay/卷/备份|
+--------------+
```

本节已核对当前停在流程的哪一格，以及上一格已经留下的材料；跳过的格子要补上，或写明这一格没有对应材料。每一格都有一份原始输出或文件路径，一并留存这张流程图，以及每一格的采集结果。

### 02.2 每一步要回答的问题

流程有了，还没把每一格要回答的问题和证据路径对上。按下表逐格填。

操作顺序：先看这一格的问题，再打开表里的证据，对上能回答的那一句。

**1. 按下表填每一阶段。** 路径和命令以表内原文为准，实际数据根若被改过，再回到配置里的路径。

| 阶段 | 核心问题 | 主要证据 |
|---|---|---|
| 确定环境 | 哪台主机、什么发行版、什么时区、是否为虚拟机/节点 | `/etc/os-release`、`timedatectl`、主机名、磁盘信息 |
| 确认 Docker | 是否安装、何时安装、来自哪个仓库 | RPM 数据库、YUM/DNF 历史、二进制版本 |
| 分析服务 | 守护进程如何启动、监听哪里、继承了什么环境变量 | systemd 主单元、drop-in、进程命令行、journal |
| 分析配置 | 数据根、镜像仓库、代理、日志驱动是否被改动 | `/etc/docker/daemon.json`、启动参数 |
| 分析容器 | 运行过哪些容器、何时停止、使用什么秘密和挂载 | `docker ps -a`、`docker inspect` |
| 分析镜像 | 镜像从哪里来、何时创建、包含哪些构建信息 | `docker images`、镜像 inspect、history |
| 分析网络 | 暴露了哪些端口、容器如何互通、是否使用 host 网络 | network inspect、iptables/nftables、连接状态 |
| 分析日志 | 有哪些访问、异常、攻击和重启痕迹 | 容器日志、daemon journal、应用日志卷 |
| 数据恢复 | 数据在可写层还是卷、是否有残留层或备份 | `overlay2/`、`volumes/`、数据库文件、快照 |

本节已核对某一阶段的核心问题，以及表里指出的主要证据；证据路径不存在时，这一格先留空，并记下实际去过的目录。问题、证据路径和读到的字段写在同一行，一并留存填过的阶段表，以及 `/etc/os-release`、`timedatectl`、`/etc/docker/daemon.json`、`docker ps -a`、`docker inspect`、`docker images`、`overlay2/`、`volumes/` 里实际打开的那几项。

<span id="03-服务器取证快速定位表"></span>

## 03 用定位表跳到查看位置

问题已经变成“安装时间、数据根、日志在哪”，还不知道第一条命令该打在包数据库、单元还是容器上。先用这张表跳到查看位置。

操作顺序：先看 pidof 有几个 PID，再按问题选查看位置，对上命令输出和这个问题是同一件事。

**1. 先看 `pidof` 返回几个 PID。** 一个已确认的 PID，才能用 `/proc/$(pidof dockerd)/cmdline`。多个就逐个读取。没有 PID 时查服务状态、单元文件和离线安装记录，保存读取错误，不判定为“未安装”。

**2. 先按下表从问题找到查看位置，再按问题复制下面的命令。** 事务 ID、容器 ID 和网络名先换成清单里确认过的值。

<details>
<summary>展开快速定位表</summary>

| 问题 | 查看位置 |
|---|---|
| Docker 是否安装 | RPM 数据库、PATH、systemd |
| Docker 安装时间 | RPM `INSTALLTIME`、YUM/DNF history、日志 |
| Docker 版本 | Client/Server、RPM 包、二进制 |
| Docker 安装来源 | YUM/DNF 事务、repo 文件、RPM 厂商 |
| Docker 启动参数 | systemd 主单元、drop-in、进程命令行 |
| 代理配置 | systemd 环境、drop-in、`daemon.json` |
| Docker 数据根 | `daemon.json`、启动参数、Docker info |
| 容器列表 | Docker daemon |
| 容器密码/API Key | 容器 `Config.Env`、挂载配置 |
| 容器数据 | `Mounts`、卷、可写层 |
| 容器日志 | `LogPath`、日志驱动、应用日志卷 |
| 镜像信息 | 镜像列表、inspect、history |
| 网络信息 | Docker network、端口、宿主机规则 |
| 集群对象与节点关联 | API、CRI 与节点快照，见 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/) |
| containerd 容器 | CRI、containerd 服务，见[节点运行时与容器关联](/knowledge/forensic-kubernetes-cluster/) |

</details>

**3. 按问题复制命令。** 下表问题对应的命令可整体复制，逐条对照查看位置执行。

```bash
# 是否安装 / 版本
rpm -qa | grep -Ei 'docker|containerd|moby|runc'
command -v docker dockerd containerd runc
systemctl status docker
docker version
dockerd --version
rpm -qi docker-ce

# 安装时间 / 来源事务
yum history
yum history info 事务ID
grep docker /var/log/yum.log*
grep -Rni docker /etc/yum.repos.d/

# 启动参数与代理
systemctl cat docker
systemctl show docker -p ExecStart
tr '\0' ' ' < /proc/$(pidof dockerd)/cmdline
systemctl show docker -p Environment
grep -RniE 'HTTP_PROXY|HTTPS_PROXY|NO_PROXY' /etc/systemd/system /etc/docker

# 数据根
docker info --format '{{.DockerRootDir}}'
cat /etc/docker/daemon.json

# 容器
docker ps -a --no-trunc
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' 容器ID
docker inspect --format '{{json .Mounts}}' 容器ID | jq .
docker volume ls
docker inspect --format '{{json .GraphDriver.Data}}' 容器ID | jq .
docker logs --timestamps 容器ID
docker inspect --format '{{.LogPath}}' 容器ID

# 镜像与网络
docker images --no-trunc --digests
docker inspect 镜像ID
docker history --no-trunc 镜像ID
docker network ls
docker network inspect 网络名
docker port 容器ID
ss -lntup
```

本节已核对当前问题对应的查看位置，以及命令打到的那一份输出；没有 PID，或表内命令报错时，改查服务状态、单元和离线安装记录。问题、查看位置和原始输出写在一起，一并留存这张定位表里实际跑过的命令输出，以及读取错误。

### 03.1 结果冲突时的证据优先级

配置、进程、磁盘和日志各说各的。先按冲突类型决定先复核哪一份，两份都留下。

操作顺序：先认出冲突属于哪一种，再按表里的优先项复核，对上两份材料为什么不一样。

**1. 按下表选择先复核的材料。** 两份都保存。磁盘残留可能是已删除容器，也可能是 daemon 用了另一个 data-root。

| 冲突场景 | 优先复核 |
|---|---|
| 配置文件与实际进程参数不同 | `/proc/<PID>/cmdline`、`/proc/<PID>/environ`、`systemctl show` |
| `docker ps` 与磁盘残留不同 | 先保存两者；磁盘可能是删除容器残留，也可能是 daemon 使用了不同 data-root |
| `docker logs` 无输出但应用有流量 | 检查日志驱动、应用日志挂载、journald、远程日志平台 |
| 容器 IP 与日志 IP 不同 | 结合 NAT、代理、负载均衡、Pod 网络和时间点 |
| 镜像标签与摘要不一致 | 以内容摘要和层哈希为主，标签仅作线索 |

本节已核对冲突的两份材料，以及表里要求优先复核的那一项；还没复核进程参数、日志驱动或摘要时，先不要选其中一边当成最终事实。`/proc/<PID>/cmdline`、`/proc/<PID>/environ`、`systemctl show`，或日志驱动、`LogPath`、内容摘要，和冲突的另一份并排在一起，一并留存冲突的两边原文，以及优先复核项的输出。

<span id="04-现场检查清单"></span>

## 04 按检查清单固定现场

现场时间有限，还没按固定顺序把版本、容器、单元、配置、网络和日志都留下。已停止的服务先不要启动。

操作顺序：先按清单往下采，每一步保存原始输出，对上容器 ID、数据根和日志路径。

**1. 建议按顺序执行。** 已停止的 Docker 或 containerd 服务，不要在未评估影响前启动。

**2. 记录主机名、系统版本、时间和时区。**

```bash
date -Is
timedatectl
hostnamectl
cat /etc/os-release
```

**3. 检查 Docker Client 和 Server 版本。** Client 与 Server 不一致时，两半都留下。

```bash
docker version
```

**4. 查看全部容器。** 只要运行中的列表时，退出容器会漏掉，这里用带 `-a` 的那条。

```bash
docker ps -a
```

**5. 查看镜像。**

```bash
docker images
```

**6. 检查重点容器和镜像详情。** 容器 ID 和镜像 ID 换成清单里的值。

```bash
docker inspect 容器ID
docker inspect 镜像ID
```

**7. 检查 Docker 的 systemd 状态。**

```bash
systemctl status docker
```

**8. 检查完整 systemd 单元和 drop-in。**

```bash
systemctl cat docker
```

**9. 检查 Docker 配置。** 文件不存在时，把错误输出留下，再回到启动参数。

```bash
cat /etc/docker/daemon.json
```

**10. 检查 Docker 数据根和目录。** info 给出的根如果不是默认目录，下一步的 `ls` 改到那个根上。默认目录仍按下面先看一眼。

```bash
docker info --format '{{.DockerRootDir}}'
ls -lah /var/lib/docker
```

**11. 查看 Docker 网络。**

```bash
docker network ls
```

**12. 查看重点容器日志和实际日志路径。** 两条都留，日志命令没有输出时仍要看 `LogPath`。

```bash
docker logs --timestamps 容器ID
docker inspect --format '{{.LogPath}}' 容器ID
```

**13. 核对是不是集群节点。** 沿 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/) 关联对象、运行时与节点证据。

**14. 保存关键输出并计算哈希。** 把“证据文件”换成这次实际保存的路径。

```bash
sha256sum 证据文件
```

本节已核对时间、版本、全部容器、数据根、单元、配置、网络和日志路径；某一步报错或文件不存在时，这一项留在缺口里，不跳过不记。每一步的命令和原始输出还在，关键文件有哈希，一并留存这十四步的输出、哈希，以及集群节点的关联入口。

### 04.1 首轮时间分配

只有大约五分钟，还没排好先看环境还是先看日志。按分钟把动作和目标对齐，超时就先把已经采到的留下。

操作顺序：先用一分钟定环境，再列资产和 inspect，对上配置、日志和可恢复数据。

**1. 按下表分配这五分钟。** 到点仍没做完时，先保存已有输出，再回到没做的那一行。

| 分钟 | 动作 | 目标 |
|---|---|---|
| 0—1 | 系统、时间、Docker/containerd 版本与服务状态 | 确认环境与工具链 |
| 1—2 | 容器、镜像、网络列表 | 建立全局资产清单 |
| 2—3 | inspect 重点容器的 Env、Mounts、NetworkSettings | 找密码、数据和通信关系 |
| 3—4 | 查 daemon 配置、systemd、代理、data-root | 发现隐藏目录、代理和远程 API |
| 4—5 | 查日志、卷、overlay2、Kubernetes/CRI | 锁定攻击痕迹和可恢复数据 |

本节已核对每一分钟实际做了表里的哪一个动作；没做到的分钟写成未完成，不把后面的结论提前写上。该分钟的命令输出，和表里的目标一致，一并留存五分钟内实际保存的清单、inspect、配置和日志。

### 04.2 必须停止并重新评估的情况

下一步可能是删除、启动或读取高权限凭据。先看下面这些情况在不在，在的话停下来重新评估。

操作顺序：先对照危险动作和危险发现，再停止继续操作，对上已经保全的材料还在。

**1. 出现下面任一情况就停。** 准备执行会删除数据的 prune、remove 或 volume 删除；准备启动已停止容器或数据库卷；准备修改 `/var/lib/docker/` 或 `/var/lib/containerd/`。这些都会改变或删掉还没采完的材料。

**2. 发现暴露和挂载也停。** 发现 `2375` 上未经授权的 Docker API；发现 Docker Socket 被可疑容器挂载；发现容器运行在 privileged、host PID 或 host network 模式。先把 inspect 和监听留下，再决定是否还要继续查询。

**3. 发现代理和集群凭据也停。** 发现 `HTTP_PROXY` 或 `HTTPS_PROXY` 指向未知主机；发现 Kubernetes 管理员 kubeconfig、ServiceAccount Token 或私钥。凭据只记位置和哈希，不把内容扩散到记录以外。

本节已核对当前准备做的动作，或已经看到的暴露、挂载、代理和凭据；还没评估影响时，删除、启动和修改数据根都先不做。停下来之前的 inspect、监听或凭据位置已经保存，一并留存触发停止的那条发现，以及当时已经采到的输出。

<span id="05-docker-取证核心思想总结"></span>

## 05 按问题类型选入口

问题类型还没对应到该打开的命令或目录。先按这张对照把安装、启动、配置、运行、数据、日志和网络分开。

操作顺序：先认出问题属于哪一类，再打开该类的命令或目录，对上文件，而不是停在清单上。

**1. 按下图把问题送进对应的工具和路径。** 一类问题只先走这一类的入口，缺的材料再回头补。

```text
安装问题  → rpm / yum / dnf
启动问题  → systemd / journal / 进程命令行
配置问题  → /etc/docker / daemon.json / drop-in
运行问题  → docker ps / inspect / top / events
数据问题  → /var/lib/docker / /var/lib/containerd / Mounts / volumes / overlay2
日志问题  → docker logs / LogPath / journald / 应用日志 / 远程日志平台
网络问题  → docker network / 端口映射 / NAT / 代理 / DNS
```

本节已核对当前问题落在安装、启动、配置、运行、数据、日志、网络的哪一类；入口命令没有输出时，改查图里并列的下一种材料。问题类型和图中的命令或路径来自同一次查找，一并留存选中的那一类命令输出或目录列表。

### 05.1 把清单落到文件

清单已经有了，还没落到文件上。已删除的容器也不会自动出现在当前清单里。

操作顺序：先记安装和启动，再保存完整 ID，对上挂载、日志、网络和数据根里的文件。

**1. 把清单落实到文件。** 查包事务、systemd 单元和进程参数，分别记安装来源和启动方式。保存 Docker 或 CRI 清单中的完整 ID 和原始 JSON。按 `Mounts`、日志驱动、网络配置和实际数据根找到文件，记录原路径、采集时间和哈希。想查更早或已删除的容器，补读节点日志和磁盘元数据，当前清单不会自动列出它们。

本节已核对完整 ID、原始 JSON，以及挂载或日志对应的文件路径；对象已删除、当前清单里没有时，还要节点日志和磁盘元数据。文件的原路径、采集时间和哈希，能对上同一个 ID 的 `Mounts` 或日志配置，一并留存包事务、单元、进程参数、原始 JSON、文件哈希。

### 05.2 常见误判与复核动作

同一条命令常常只看到一半。停止容器、改过的数据根、别的日志驱动和集群运行时，都会让少跑的那一步得出偏的结论。

操作顺序：先认出少看了哪一项，再按表补查，对上补出来的那份材料。

**1. 按下表改复核动作。** 表里的“正确做法”是下一步要补的命令或目录，两边的输出都留。

| 误区 | 正确做法 |
|---|---|
| 只执行 `docker ps` | 必须执行 `docker ps -a`，停止容器往往更有价值 |
| 只查 `/var/lib/docker` | 检查 `data-root`、启动参数及 `/var/lib/containerd` |
| 认为 `docker logs` 一定对应 JSON 文件 | 先查容器日志驱动和 `LogPath` |
| 只看 systemd 主单元 | 同时看 drop-in、`systemctl show` 和实际进程环境 |
| 把镜像 `Created` 当成本机下载时间 | 用 daemon/代理日志和本机元数据补证 |
| 在 Kubernetes 节点只查 Docker | 优先确认 CRI，使用 `crictl` 和 containerd 配置 |
| 直接启动原数据库卷恢复 | 在副本上、使用匹配版本恢复并记录所有写入 |
| 为了释放空间执行 prune | 取证阶段禁止清理潜在证据 |

本节已核对误区对应的那一次补查，以及补出来的容器、目录或日志驱动；只做了表左列的那一条时，复核还没完成。补查命令的输出和原先那份并排在一起，一并留存原命令输出，以及 `docker ps -a`、数据根、`/var/lib/containerd`、`LogPath`、`systemctl show`、`crictl` 或副本恢复记录中实际补上的那一份。

<span id="06-docker-清理与风险命令"></span>

## 06 认清会改现场的清理命令

磁盘空间不够，手里已经有人准备跑清理。这些命令会删掉停止的容器、镜像或卷，证据主机上先不要为了腾空间执行。

操作顺序：先看占用和版本支持的选项，再在副本上选择具体删除，对上要删的对象已经另存。

**1. 先按下表分清每条命令会动什么。** 清理前用占用查询看空间。证据主机上不要为了释放空间直接执行高风险清理。

<details>
<summary>展开清理命令风险表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker system df | 显示镜像、容器、Volume 和构建缓存占用 | 清理前先评估空间 |
| docker container prune | 删除所有已停止容器 | 批量清理；会丢失容器可写层 |
| docker image prune | 默认删除悬空镜像 | 清理无 Tag 镜像；仍需核对分析价值 |
| docker volume prune | 当前版本默认删除未使用的匿名本地 Volume | 旧版范围和 API 支持需按版本核对；命名卷另有 --all/-a 选项 |
| docker volume prune --all | 删除符合筛选条件且未被任何容器引用的匿名与命名本地 Volume | 命名卷也在删除范围；不是业务数据价值判断 |
| docker system prune | 清理停止容器、未使用网络、悬空镜像和构建缓存 | 综合清理；默认不清理 Volume |
| docker system prune -a | 额外删除所有未被容器使用的镜像 | 高风险大范围清理 |
| docker system prune --volumes | 再加入未被容器使用的匿名 Volume | 不等于删除全部命名卷；先移除停止容器可使其卷变成未引用 |

</details>

**2. 先记住高风险的那一条。** `docker system prune -a` 可删除仍有复现或取证价值、但当前未被容器引用的镜像。证据主机上不要为了释放空间直接执行。

**3. 副本上的清理要先列出对象。** 【仅在副本/仿真/授权环境执行】先用 `docker system df` 看占用，再列出要处理的镜像、文件和卷。确认这些内容及运行依赖已保存后，选择具体 `rm/rmi`。prune 的“未使用”只表示 daemon 目前没有引用；停止容器、旧镜像和卷仍可能有调查价值。原件不做清理。

**4. 只读取版本和本机支持的选项，这里没有执行清理。**

```bash
# 读取版本与本机支持的选项；这里没有执行清理
docker version
docker volume prune --help
docker system prune --help
docker system df
docker volume ls
```

**5. 引用关系会随删除容器而变。** 卷被已停止但尚未删除的容器引用时，仍不属于“未使用”。先删容器再 prune 会改变符合条件的卷集合。不要用当前引用清单推断过去清理动作的全部删除范围。命名卷和匿名卷的默认范围按采集时的 Engine 或 API 版本核对，见 [Docker prune 说明](https://docs.docker.com/engine/manage-resources/pruning/)。

本节已核对当前版本支持的选项、占用，以及准备处理的具体对象；对象和运行依赖还没另存时，清理先不做。`docker system df`、帮助输出和对象清单在删除之前已经留下，一并留存版本、帮助、占用、卷列表，以及副本上每次具体删除的对象和结果。

<span id="07-docker-服务器取证完整流程"></span>

## 07 完整流程与阶段产物

目标会话和离线文件还混在一条路上。先把只读查询和会改状态的分支分开，再往下取文件。

操作顺序：先在目标会话保存状态，再读宿主机和容器文件，对上提取范围和采集时间。

**1. 读图时先分两条路。** 目标会话先查状态、配置、日志和进程，保存输出后再读宿主机与容器文件。

**2. 会改状态的步骤只用于演练。** 【仅在副本/仿真/授权环境执行】图中的 exec、内部检查，以及停止、commit、清理只用于演练。cp、save、export 用于提取。提取后另查文件清单、卷是否单独保存，以及采集期间是否还在写入。

```text
docker ps -a
      ↓
docker images
      ↓
docker inspect <container>
      ↓
docker logs <container>
      ↓
docker top <container>
      ↓
副本分支：docker exec -it <container> sh
      ↓
副本分支：env / ps / 文件目录检查
      ↓
docker cp 提取证据
      ↓
Volume / Network / Image Layer 深入分析
```

**3. 按下表把阶段、命令和目的对齐。** 退出容器要出现在资产枚举里。提取到分析主机之后再算哈希。

| 阶段 | 命令或证据 | 目的 |
| --- | --- | --- |
| 资产枚举 | docker ps -a、docker images、docker network ls、docker volume ls | 确定分析范围并避免遗漏退出容器 |
| 元数据 | docker inspect | 保存启动配置、环境、挂载、网络、端口和状态 |
| 运行态 | docker logs、docker top、docker stats --no-stream | 建立事件、进程和资源异常线索 |
| 文件变化 | docker diff、只读目录检查 | 定位新增、修改和删除路径 |
| 证据提取 | docker cp、docker save、Volume 备份 | 在分析主机离线处理并计算哈希 |
| 深入关联 | Network、Mounts、Image Layers、宿主机日志 | 还原攻击路径和持久化位置 |

**4. 把时间基准分开记。** 记录宿主机时间与容器日志时间戳的时区和偏差。容器日志、应用日志、Docker 事件和文件时间可能使用不同时间基准。

本节已核对资产清单、inspect、日志或进程、以及提取文件的路径；卷没单独保存，或采集期间文件还在写入时，提取范围还要注明限制。表里该阶段的命令输出，和提取文件的清单、哈希在一起，一并留存流程图上实际跑过的输出、文件清单、哈希，以及时间基准和时区偏差。

<span id="08-git-docker-易混命令对比"></span>

## 08 Docker 易混命令对比

Docker 的成对命令容易用错对象，下面分清镜像、容器、卷和清理命令各自作用在哪个对象。Git 的易混命令（log/reflog、show/diff、checkout/restore、软/混合/硬 reset）见 [提交与差异](/knowledge/git-docker-04/)与 [log、reflog 与 reset 模式](/knowledge/git-docker-05/)。

操作顺序：先看命令作用在哪个对象，再看它会不会改现场，对上该用的那一条。


### 08.1 Git 易混命令（见 Git 取证）

Git 的 log/reflog、show/diff、checkout/restore、软/混合/硬 reset，以及 commit/tree/blob/tag 对象类型，唯一正文在 [提交与差异](/knowledge/git-docker-04/)、[log 与 reflog](/knowledge/git-docker-05/)与 [对象模型](/knowledge/git-docker-06/)；本节不再重复。现场只用一条原则：**取证现场避免 reset，尤其会连工作区一起重置的 hard**；选命令前先分清读的是提交图、引用移动、单个对象还是工作区差异。

本节已核对当前要看的是提交图、引用移动、单个对象，还是工作区差异；还没分清对象类型时，先不要恢复或重置。选中的命令和表里这一行的对象一致，一并留存命令的原始输出，以及对象类型和哈希。

### 08.2 Docker 易混命令

镜像和容器、停止和删除、导出镜像和导出容器还容易混用。对象选错，证据会跟着被删掉。

操作顺序：先看命令作用在镜像、容器、卷还是网络，再看它会不会删除对象，对上取证该留的那一条。

**1. 按下表选命令。** 取证列容器用能看到全部容器的那一条。导出镜像优先用保留层的那一条。会删除对象的命令留到副本，并先把另一边的材料保存下来。

<details>
<summary>展开 Docker 易混命令表</summary>

| 比较 | A | B | 关键区别 |
| --- | --- | --- | --- |
| Image vs Container | 镜像是只读模板 | 容器是运行实例和可写层 | 同一镜像可创建多个容器 |
| stop vs kill | 先给应用停止机会 | 默认立即 SIGKILL | kill 更容易造成数据不一致 |
| rm vs rmi | 删除容器 | 删除镜像 | 对象不同；二者都可能破坏证据 |
| exec vs run | 在现有运行容器执行命令 | 从镜像创建新容器 | run 不是进入旧容器 |
| save vs export | 导出镜像及其层 | 导出容器合并文件系统 | 镜像取证优先 save |
| load vs import | 恢复镜像归档 | 把文件系统 tar 转为新镜像 | import 不恢复原分层历史 |
| Volume vs Bind Mount | Docker 管理存储位置 | 用户指定主机路径 | 两者都独立于容器可写层 |
| compose stop vs down | 停止并保留容器 | 停止并移除容器和默认网络 | down 可能丢失容器可写层 |
| ps vs ps -a | 只看运行中容器 | 看全部容器 | 取证首选 ps -a |

</details>

本节已核对命令作用的对象，以及它会停止、删除还是只读取；还没保存 inspect、日志和层时，删除和 down 先不做。表里这一行的对象，和清单里的镜像 ID 或容器 ID 一致，一并留存选择依据，以及执行前保存的对象清单。

<span id="09-现场命令与记录速查"></span>

## 09 只读命令与记录字段速查

要动手查了，还没把只读命令和会改现场的命令分开。下面按 Docker 命令、风险命令和记录字段往下用；Git 命令另见 [Git 取证系列](/knowledge/git-docker-03/)。

操作顺序：先跑只读查询，再决定要不要进副本，对上每条命令留下的原始输出。


### 09.1 Git 核心命令（见 Git 取证）

Git 仓库的静态配置/钩子检查、只读历史与对象命令（log/show/diff/reflog/fsck/cat-file）、发现到下一步的对照表，以及 log→show→reflog→fsck→cat-file 的读取顺序，唯一正文在 [识别仓库与元数据](/knowledge/git-docker-03/)、[提交与差异](/knowledge/git-docker-04/)、[log 与 reflog](/knowledge/git-docker-05/)与 [对象与恢复](/knowledge/git-docker-06/)；现场只用一条原则：不要在唯一仓库副本上执行会覆盖工作区的 reset、clean、检出或恢复。

本节已核对可疑提交、历史文件、引用移动或悬空对象，以及下一条只读命令；钩子和属性还没静态看过时，先不要看补丁或切换分支。下一条命令的输出，和表里的“发现”是同一个对象，一并留存只读命令的原始输出、对象哈希，以及改动前的状态。

### 09.2 Docker 核心命令

容器已经列出来，还没决定只保存日志，还是要进容器。进容器会新增进程，放在副本分支。

操作顺序：先保存只读查询，再决定是否在副本里进入容器，对上现象和下一条命令。

**1. 进入容器的那一条单独标注。** 【仅在副本/仿真/授权环境执行】下面的 exec 会在容器里新增进程。其他只读查询先保存，再决定是否在实验副本进入容器。

```bash
docker ps -a
docker images
docker inspect <container>
docker logs --tail 100 -t <container>
docker top <container>
docker stats --no-stream <container>
docker diff <container>
docker exec -it <container> sh
docker cp <container>:/path/file .
docker volume ls
docker network ls
docker compose ps
docker compose logs
```

**2. 三条路分开记。** 目标查询、离线分析和仿真分支不要混成一次结果。

```text
目标查询：docker ps -a → inspect → logs/top/stats/diff → 单独提取
离线分析：容器元数据 → 挂载数据 → 镜像层 → 时间线
仿真分支：保全基线 → exec/内部检查 → 保存副本改动 → 与原记录核对
```

**3. 目标原件到此为止。** 目标原件不执行 stop、kill、rm、down 或 prune。采集完成也不把这些操作当成当然的下一步。运行态和元数据继续保全，需要复现时另用副本。

**4. 看到现象后按下表选优先命令。** 退出容器先看退出码和日志。服务访问不到时看发布端口、监听地址、服务名和网络。

| 现象 | 优先命令 | 检查重点 |
| --- | --- | --- |
| 容器反复退出 | docker ps -a；docker logs | ExitCode、启动参数、错误日志 |
| 服务访问不到 | docker inspect；docker network inspect | 端口发布、监听地址、服务名和网络 |
| 资源异常 | docker stats --no-stream；docker top | CPU、内存、I/O 和异常进程 |
| 怀疑 WebShell | docker diff；docker cp | 新增或修改文件、离线哈希和源码比对 |
| 容器删了数据还在 | docker volume ls；inspect | Named Volume、Bind Mount 和主机路径 |

本节已核对现象对应的优先命令，以及退出码、端口、进程或文件差异；容器已经删了、数据还在时，还要卷和绑定目录的宿主机路径。表里的检查重点能在 inspect、日志或 diff 里指到同一处，一并留存只读查询输出、提取文件和哈希。仿真里的新进程单独记。

### 09.3 风险命令清单

下一步的命令会覆盖工作区、删容器或删卷。执行前先核对表里要求先留下的材料。

操作顺序：先认出命令会破坏什么，再按表核对已保存的材料，对上副本和审批还在。

**1. 按下表核对。** 表里的动作只放在副本。原件上先把 HEAD、容器元数据、日志、卷和镜像摘要留下。

| 命令 | 主要风险 | 仅在副本操作前核对 |
| --- | --- | --- |
| docker kill | 立即中断进程，丢失内存态和未落盘数据 | 先采集 logs、top、stats 和必要运行态 |
| docker rm -f | 停止并删除容器可写层 | inspect、logs、diff、cp 或 export |
| docker rmi -f | 移除镜像引用并影响复现 | 记录摘要并 docker save |
| docker compose down | 移除容器与默认网络 | 保全容器元数据和可写层 |
| docker compose down -v | 额外删除项目 Volume | 单独备份 Volume 并核对范围 |
| docker system prune -a | 大范围删除未使用镜像等对象 | 逐项清单、导出、审批与复核 |

本节已核对准备执行的命令，以及表里要求事先核对的材料已经在；材料没保存、还没复制仓库或导出镜像时，这条命令先不跑。核对项的路径、哈希或清单，和这条命令要动的对象是同一个，一并留存核对清单、副本标识，以及事后的结果。

### 09.4 现场记录最小字段

输出已经有了，还缺时间、位置、状态、证据和动作这五类，后面的人无法复核。按这五类把记录补全。

操作顺序：先写时间和位置，再写状态和证据，对上每一次会改现场的动作。

**1. 时间写下宿主机时间、时区，以及容器日志的时间基准。** 两边不一致时，偏差一起留下。

**2. 位置写下主机名、当前目录、仓库根、容器 ID、镜像 ID 或摘要。** 名字会复用，ID 和摘要要完整。

**3. 状态写下分支和 HEAD、容器状态、PID、端口、挂载和网络。** 这是采集这一刻的状态。

**4. 证据写下原路径、提取命令、输出文件、大小、哈希和保管位置。** 缺哈希的文件补上再进入结论。

**5. 动作写下任何 exec、stop、export 或清理操作及其结果。** 没有这类动作时，写明这次只做了读取。Git 侧的 checkout、restore、commit 动作另记，见 [log、reflog 与 reset 模式](/knowledge/git-docker-05/)。

本节已核对五类字段里已经填上的时间、位置、状态、证据和动作；缺哈希、缺容器 ID 或缺时区时，对应那一类还不能收尾。每一类都能指回一条命令输出或一个文件，一并留存这五类记录，以及它们指向的原始输出。

<span id="10-docker-与-lxc-的命令归属核对"></span>

## 10 容器地址归属核对（回链主线）

数据库配置里有一个容器地址，Docker 清单里没有对应服务。**app-db LXC 租约识别的完整主线在 [Docker 取证 01 §09.2](/knowledge/docker-evidence-01/#092-实战沿数据库配置追到-lxc-根目录)**；本节只保留清点命令与归属结论，详细的 LXC 定义、租约与 `lxc-attach` 解析回到主线核对。

操作顺序：先清点 Docker 和 LXC，再读定义和根目录，对上地址属于哪一个对象。


### 10.1 清点与静态定义

地址已经出现，还不能凭默认网段判断运行时。先清点，再读定义文件，把地址、桥、根目录和时间接到同一个对象上。

操作顺序：先清点两类运行时，再读 LXC 定义和镜像时间，对上根目录和桥。

**1. 场景先固定。** 数据库配置里出现一个容器内地址，Docker 清单没有对应服务。先清点两类运行时，读取定义文件，再关联地址、桥、根目录和时间，避免直接用默认网段判断运行时。

**2. 在目标现场做查询。** 地址命令的输出范围不同，都留下。

```bash
docker ps
docker ps -a
docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}'
lxc-ls -f
ip addr
ip a
ip -br addr
ip -4 addr
ip -br addr show type bridge
brctl show
```

**3. 离线定义、租约与字段判读回到主线。** 从检材根读 LXC 定义、匹配租约、解释 `lxc.rootfs.path` 与 `lxc.net.0.*`、以及把地址归到某个对象，完整步骤见 [Docker 取证 01 §09.2](/knowledge/docker-evidence-01/#092-实战沿数据库配置追到-lxc-根目录)。本节不重复这些解析，只保留上面的清点命令和结论。`brctl show` 依赖 bridge-utils，缺工具时换查接口和配置；桥名可改、IP 可复用，容器内接口可能与宿主机不同。

本节已核对Docker 或 LXC 的对象、定义里的根目录，以及地址所连的桥；只有网段相似、没有定义或元数据时，归属还没确认。表里的字段和下一步打开的文件是同一个对象，一并留存清点输出、LXC 定义、镜像创建字段和数据根路径。

### 10.2 容器内执行只放在仿真分支

进入 LXC 会启动新进程，只能在仿真副本里做，完整步骤见 [Docker 取证 01 §09.4](/knowledge/docker-evidence-01/#094-仿真连接与容器内命令)。本节不重复 `lxc-attach` 示例：现场原则是先在静态根文件系统里读，确需在副本执行时再记下容器名、执行时间、完整命令和新增进程。

本节已核对容器名、完整命令，以及容器内读到的系统信息；工具缺失或还在原件上时，改回静态根文件系统，不安装软件。仿真输出和静态根里的同一文件内容一致，新增进程已经单独记录，一并留存容器名、执行时间、完整命令、副本状态，以及静态文件的路径。

<span id="11-实战将首轮输出变成可复核清单"></span>

## 11 把首轮输出变成可复核清单

首轮命令已经有输出，还没变成能复核的清单。下面按退出容器、日志和卷、时间表、收尾条件往下做。

操作顺序：先固定容器字段，再分开提取日志、卷和层，对上同一时区里的事件。


### 11.1 容器反复退出时先固定字段

一项 Web 服务间歇不可达，当前清单显示对象已经退出。要判断启动配置、退出原因和证据位置，同时避免用重启掩盖原来的状态。

操作顺序：先保存完整 inspect 和日志，再读退出字段，对上配置错误、内存不足或重启记录。

**1. 先固定材料和输出目录。** 材料是已确认目标会话中的容器对象、只读主机快照 `/mnt/evidence` 和保全目录 `/work/input/web-inspect.json`。输出写入 `/work/output/container-first-pass/`。下面是构造示例，实际操作从清单确认完整 ID，不表示已对某份实际检材复跑。

```bash
OUT=/work/output/container-first-pass
EVIDENCE_ROOT=/mnt/evidence
mkdir -p "$OUT"
docker ps -a --no-trunc > "$OUT/containers.txt"
CID=$(docker inspect --format '{{.Id}}' web)
docker inspect "$CID" > "$OUT/container-inspect.json"
docker logs --timestamps "$CID" > "$OUT/stdout.log" 2> "$OUT/stderr.log"
sha256sum "$OUT/container-inspect.json" "$OUT/stdout.log" "$OUT/stderr.log"
```

**2. 只有离线材料时改读文件。** 改复制 `/work/input/web-inspect.json` 并解析其字段，读取 `$EVIDENCE_ROOT` 下对应配置和日志。不要执行 Docker CLI 去查分析机上的同名对象。标准错误里既可能有容器的 stderr，也可能有工具报错，结合退出状态和内容判断。

**3. 目标会话里可以再看这几条定位输出。** 容器名 `web` 只是演示名，先从清单确认名字和完整 ID。停止的容器如果不能提供进程或资源快照，保存报错和当时状态，接着读静态文件，不用启动它来补一份进程列表。

```bash
# 从清单确认容器名和完整 ID；下列 web 仅为演示名
docker ps -a --no-trunc
docker inspect web
docker logs --tail 100 -t web
docker top web
docker stats --no-stream web
docker diff web
```

**4. 输出这样用。** 先保存完整 inspect JSON，再筛选时间、状态、Mounts、网络和配置。尾部 100 行只用来找最近错误，完整日志和轮转文件另存。

**5. 三种字段分开判断。** `ExitCode=1` 再加上配置解析报错，说明这次启动因应用错误退出；继续查配置错误位置，不直接写成受到攻击。`OOMKilled=true` 时查看内存记录、宿主机内核和 daemon 日志，核对是否内存不足。RestartCount 非零说明有重启记录；每次原因和时间仍到日志中找。

本节已核对完整容器 ID、inspect、退出码或内存不足标志，以及日志文件；停止容器没有进程列表时，进程那一项留着报错，不靠启动来补。inspect 字段和日志里的同一时段、同一次退出对得上，一并留存容器列表、inspect JSON、标准输出、标准错误和哈希。

### 11.2 把日志、卷与层分开提取

退出原因有了线索，日志、网站文件和可写层还堆在一起。先按 inspect 把三类位置分开。

操作顺序：先读日志路径、挂载和存储驱动，再按空路径改查别的位置，对上文件来自卷、绑定目录还是可写层。

**1. 先取出这三处位置，并列出卷和网络。** 容器名换成清单里确认过的名字。

```bash
docker inspect --format '{{.LogPath}}' web
docker inspect --format '{{json .Mounts}}' web | jq .
docker inspect --format '{{json .GraphDriver.Data}}' web | jq .
docker volume ls
docker network ls
```

**2. 按输出找位置。** Mounts 指出 `/var/www/html` 来自卷，就单独查卷。`docker diff` 只查可写层，没列出卷里的文件时仍要检查 WebShell。LogPath 为空，就查该容器的日志驱动、应用日志文件和远程发送配置。GraphDriver.Data 没有 overlay2 路径，就按实际存储模式查 snapshot，不硬套层目录。

**3. 复制出去的文件要能对回原处。** 记录对象完整 ID、原路径、输出路径、时间、大小和哈希。对运行中的数据库或持续写入的日志，普通逐文件复制不保证同一时间的一致快照。应保存采集时间范围、文件集合和一致性限制，后续在副本用匹配版本解析。文件来自卷、绑定目录还是可写层，必须写进清单。

本节已核对日志路径、挂载来源，以及可写层或 snapshot 的实际路径；LogPath 为空或没有 overlay2 路径时，改查日志驱动和实际存储，不留空路径充数。每个复制文件的原路径、来源类型和哈希都在清单里，一并留存inspect 的三段输出、卷和网络列表、文件清单和一致性限制。

### 11.3 建立同一时区的事件表

日志、文件时间和网络记录用的时间基准可能不同。先按事件类型记下该留的字段，再处理对不上的地方。

操作顺序：先按事件类型记原始时间，再把差异分列，对上采集时刻和历史记录。

**1. 按下表记录每一类事件。** 创建时间、最近一次启停、日志时间、文件时间、当前 IP 和仿真动作不要互相代替。

| 事件类型 | 优先记录 | 解释边界 |
| --- | --- | --- |
| 容器对象创建 | Created、完整容器 ID、镜像 ID | 不等同于镜像本机构建或拉取 |
| 最近一次启动/退出 | StartedAt、FinishedAt、ExitCode、OOMKilled | 不是完整生命周期记录 |
| 日志事件 | 原始时间、时区、stdout/stderr 或应用日志类别 | 应用与 daemon 时间可能不同 |
| 文件变化 | 原路径、层或卷、哈希、文件时间 | 文件时间可被改写，复制也可能改变属性 |
| 网络活动 | 容器/网络 ID、时间、端口发布、连接或代理记录 | 当前 IP 不自动代表过去 IP |
| 仿真动作 | 副本标识、命令、快照、新增日志与结果 | 与原现场历史分开解释 |

**2. 出现差异就分开记。** 例如配置写 `/data/docker`，进程参数却指向另一目录，就查两处文件并确定进程使用哪一处，不删旧目录。网络输出与日志 IP 不同，依次查采集时间、NAT、代理和负载均衡。一个 IP 还不能直接确定操作者。

本节已核对某一事件的原始时间、对象 ID，以及它属于表里的哪一类；时区还没统一，或 IP 还没对上 NAT 和代理时，先后和操作者先不要写死。表里的优先字段能在 inspect、日志或配置原文里找到，一并留存事件表、原始时间字符串、两处数据根的文件列表。

### 11.4 复核完成的条件

材料已经抽出一些，还没检查 ID、日志范围、镜像包和哈希是否都能对回去。按四项收尾。

操作顺序：先对容器 ID 和 inspect，再对日志、挂载和镜像包，对上哈希和归档成员。

**1. 首轮收尾逐项检查。** 完整容器 ID 能找到保存的 inspect JSON。日志有来源驱动和起止时间，挂载能找到卷或宿主机目录。镜像 ID 或摘要能对应导出包。对包计算 `sha256sum` 后，再列归档成员并读取代表文件。空包或缺文件要记为提取未完成。

**2. 失败和缺失留在记录里。** 失败输出和缺失文件都留下。只有配置而没有日志时，注明尚未确认运行。仿真服务启动后，把新日志、改动和结果单独保存，再回看原配置与历史日志。不要把这次启动写成过去也成功运行。

本节已核对容器 ID 对得上 inspect，日志和挂载有来源，镜像包里能读到代表文件；空包、缺文件，或只有配置没有日志时，对应项记为未完成或尚未确认运行。`sha256sum`、归档成员和代表文件来自同一个导出包，一并留存inspect、日志范围、挂载路径、导出包、哈希，以及仿真新产生的日志和改动。
