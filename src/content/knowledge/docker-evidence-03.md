---
title: "Docker 取证 03｜容器与镜像"
summary: "区分容器运行态、可写层与镜像构建层，核对进程、文件变化和镜像来源。"
module: "Forensics"
track: "服务器取证"
topic: "Docker 与容器"
tags: []
status: "已整理"
sourceIds: ["2530fdc7be10", "c7613f4a6214", "web-csdn-140823396", "web-server-csdn-151725686"]
challengeIds: []
relatedIds: []
updated: "2026-10-07"
---

手里是运行中或已退出的容器，以及对应的镜像和 Dockerfile。本页回答：容器身份与状态、镜像身份与构建层、容器管理命令动的对象、容器内证据、镜像导入导出的取舍，以及怎么把配置对应到业务数据。原始材料保持只读，创建、启停、删除、exec、commit、load/import 只在副本上做。

**先读容器清单与 inspect → 固定镜像身份与构建层 → 分清管理与执行的改动 → 分开保全状态、可写层与镜像层 → 把配置对应到业务数据。**

<span id="01-docker-容器分析"></span>

## 01 从容器清单读到权限与逃逸面

先保存完整容器 ID、镜像摘要、创建/启动时间及原始 inspect JSON，再分别分析容器可写层与镜像历史。`docker diff` 只描述可写层变化，挂载卷中的内容要回到卷或宿主机路径。

手里有运行中或已经退出的容器，还没把完整 ID、状态和挂载分开。下面按清单、详情、时间、环境变量、挂载、网络和权限逐项查看。

操作顺序：先列出全部容器，再保存原始 inspect，对上时间、环境、挂载和网络。


### 01.1 查看容器

只看到正在跑的容器时，退出和创建失败的会漏掉。先把范围定成全部容器，再留完整 ID。

操作顺序：先看运行中的，再列出全部，对上完整 ID 之后再 inspect。

**1. 需要只看当前还在跑的容器时，用不带 `-a` 的列表。** 这份输出不能当成全部容器。

```bash
docker ps
```

**2. 取证要包含退出、创建失败和已停止的容器。** 仍只有运行中的几行时，检查是不是忘了 `-a`。

```bash
docker ps -a
```

**3. 建议留下完整 ID、镜像、状态、端口和名称。** `--no-trunc` 避免 ID 和命令被截断。格式行对不齐时，保留第一条不带 `--format` 的完整输出。

```bash
docker ps -a --no-trunc
docker ps -a --no-trunc --format 'table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}'
```

**4. 要快速记下容器 ID 时，只输出完整 ID。** 这一行没有名称和状态，不能代替上面的清单。

```bash
docker ps -aq --no-trunc
```

本节已核对全部容器的完整 ID、镜像、状态、端口和名称；只有 `docker ps`、没有 `-a` 时，已退出容器还没列入。`--no-trunc` 的 ID 和后面 inspect 用的是同一个容器，一并留存四条命令里实际跑过的原输出。

### 01.2 查看容器详情

清单里已经有容器 ID，还没有它的原始配置。先把 JSON 存到取证目录，不要写进 Docker 数据根。

操作顺序：先 inspect 这个 ID，再把 JSON 和哈希存到输出目录，对上文件哈希之后再摘字段。

**1. 按容器 ID 读完整配置。** ID 对不上就回到上一节的完整 ID，不要用截断 ID 碰运气。

```bash
docker inspect 容器ID
```

**2. 把原始 JSON 存成证据副本并计算哈希。** 重定向文件应写入单独的取证输出目录，而不是 `/var/lib/docker/`。命令输出是逻辑采集结果，不是磁盘原始镜像的替代品。写进数据根时停下来，把文件移到输出目录再算哈希。

```bash
CID=$(docker inspect --format '{{.Id}}' 容器ID)
docker inspect "$CID" > "container-$CID-inspect.json"
sha256sum "container-$CID-inspect.json"
```

本节已核对这个容器 ID 的原始 inspect JSON，以及文件哈希；只有屏幕上的节选、没有保存的 JSON 时，后面的字段摘取还没有底稿。`sha256sum` 的文件就是刚写出的那份 inspect，一并留存输出目录里的 JSON 和哈希。分析机上的输出不能代替磁盘镜像。

### 01.3 时间、状态与进程

JSON 已经有了，还没把创建、最近一次启停和查询当时的进程分开。时间字段对不上时，不要合成一个“部署时间”。

操作顺序：先读状态字段，再看查询时的进程，容器已停就转读静态文件。

**1. 先按这张表读时间、退出和入口。** 字段缺失或是零值时按原样留下，不要换算成另一个事件的时间。

| 字段 | 意义 | 判断示例 |
|---|---|---|
| `Created` | 容器对象创建时间 | 与镜像拉取、部署操作、攻击时间关联 |
| `State.StartedAt` | 最近启动时间 | 识别重启或攻击后启动 |
| `State.FinishedAt` | 最近停止时间 | 与异常退出或删除前行为关联 |
| `State.ExitCode` | 退出码 | 非 0 常提示应用或运行时异常 |
| `State.OOMKilled` | 是否因内存不足被杀 | 区分资源问题与主动停止 |
| `RestartCount` | 重启次数 | 高频重启可解释日志爆量或服务不稳定 |
| `Path`、`Args` | 容器入口进程和参数 | 识别恶意替换、反弹 Shell、挖矿命令 |

**2. 用一条 format 把核心状态摘出来。** 摘出来的值要能回到上一份原始 JSON。

```bash
docker inspect --format 'Created={{.Created}} Started={{.State.StartedAt}} Finished={{.State.FinishedAt}} Status={{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}}' 容器ID
```

**3. 先读状态，再看进程。** `StartedAt`、`FinishedAt` 是最近一次启动/退出时间，早期运行到日志和事件中查。零值、未运行和查询报错分别记录。

**4. 下面的 `docker top` 看的是查询时的进程。** 容器已停止时报错，就保存状态并转读静态文件，不启动它补进程列表。

```bash
docker top 容器ID -eo pid,ppid,user,lstart,cmd
```

本节已核对 `Created`、`State.StartedAt`、`State.FinishedAt`、`State.ExitCode`、`State.OOMKilled`、`RestartCount`，以及查询当时的进程；容器已停止、`docker top` 报错时，进程列表改为静态文件，不启动容器。format 输出和原始 JSON 的同一字段一致；早期运行另有日志或事件，一并留存format 输出、`docker top` 的输出或它的报错，以及 `Path`、`Args`。

### 01.4 `Env`：密码、API Key 与配置线索

状态已经看过，环境变量里还有没有口令、地址和代理还不知道。先把变量列出来，空的时候继续找文件。

操作顺序：先列出 Env，再按表筛变量名，没有明文就改查挂载和启动参数。

**1. 查看这个容器创建配置里的环境变量。** 输出按敏感材料保存，不要贴进公开记录。

```bash
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' 容器ID
```

**2. 按类别搜变量名，再决定下一步去哪。** 表里的名字只是常见写法，实际名字不同就按读到的键继续。

| 类别 | 常见变量名 | 后续动作 |
|---|---|---|
| 数据库密码 | `MYSQL_ROOT_PASSWORD`、`POSTGRES_PASSWORD`、`DB_PASSWORD` | 脱敏记录；关联数据库卷、连接日志 |
| API Key/Token | `API_KEY`、`TOKEN`、`SECRET`、`ACCESS_KEY` | 检查是否已被滥用；不要在报告正文泄露完整值 |
| 配置文件位置 | `CONFIG_FILE`、`SPRING_CONFIG_LOCATION` | 继续检查挂载和容器文件系统 |
| 数据库地址 | `DB_HOST`、`REDIS_HOST`、`DATABASE_URL` | 还原容器通信关系和依赖拓扑 |
| 代理 | `HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY` | 与 daemon 代理区分，分析应用层外联 |

**3. 用一条筛选把常见敏感名字留下。** 没有命中只说明这些片段不在 `Env` 里，不说明没有凭据。

```bash
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' 容器ID | grep -iE 'pass|secret|token|key|credential|database|redis|config|proxy'
```

**4. `Env` 没有明文密码时，继续往下找。** 继续读 bind mount 的应用配置、Docker secrets 和启动参数。若是集群应用，再找 [Secret 与配置挂载](/knowledge/forensic-kubernetes-cluster/)；先定位实际文件，不把空环境变量当作搜索终点。

**上面的 Env 里还有 SQL Server。** 管理员口令变量是 `MSSQL_SA_PASSWORD`。容器没在跑时，读该容器 `config.v2.json` 的 `Env`，不要等 `docker inspect`。JSON 里的 `\u003c`、`\u003e`、`\u0026` 还原成 `<`、`>`、`&`。镜像个数和镜像 ID 用镜像列表；容器 ID 用容器列表。Compose v2 用 `docker compose version`，系统里可以没有旧的 `docker-compose` 命令。

本节已核对 `Env` 里实际出现的变量名，以及它属于口令、地址、配置路径还是代理；没有 `MYSQL_ROOT_PASSWORD` 这类明文时，还要查挂载、secrets 和启动参数。筛选命中的行能在完整 `Env` 列表里找到同一条，一并留存受控保存的环境变量列表；报告正文只留变量名和后续要查的路径。

### 01.5 `Mounts`：宿主机与容器目录映射

环境变量指向了数据，但文件可能不在容器可写层里。先读挂载，再判断容器能不能改宿主机上的文件。

操作顺序：先把 Mounts 列成 JSON，再按字段看类型和路径，将高危挂载单独标出。

**1. 查看挂载。** `jq` 失败时保留原始 JSON，不要手改字段。

```bash
docker inspect --format '{{json .Mounts}}' 容器ID | jq .
```

**2. 按字段解释每一条挂载。** `Source` 对不上磁盘上的目录时，记缺失，不要改成容器里的 `Destination`。

| 字段 | 含义 | 取证价值 |
|---|---|---|
| `Type` | `bind`、`volume`、`tmpfs` 等 | 判断数据由宿主机目录、命名卷还是内存提供 |
| `Source` | 宿主机源路径或卷实际路径 | 定位数据库、网站文件、配置与日志 |
| `Destination` | 容器内挂载点 | 判断数据在应用中的用途 |
| `RW` | 是否可写 | 判断容器能否篡改宿主机文件 |
| `Propagation` | 挂载传播方式 | 高权限容器和宿主机影响面分析 |

**3. 看到下面这些映射时，单独记下影响面。** 这些映射可能使容器控制 Docker、读取宿主机或破坏其他容器证据。路径只是部分相同时，仍留下原始 `Source` 和 `Destination`，不要抹成这四行之一。

```text
/var/run/docker.sock -> /var/run/docker.sock
/ -> /host
/etc -> /host/etc
/var/lib/docker -> /var/lib/docker
```

本节已核对每条挂载的 `Type`、`Source`、`Destination`、`RW` 和 `Propagation`；`Source` 在这块盘上不存在时，写成缺口，不改用容器内路径。JSON 里的源路径和目的路径成对出现，高危映射能对上上面的示例或被排除，一并留存Mounts 的原始 JSON，以及单独标出的 docker.sock 或根目录映射。

### 01.6 `NetworkSettings`：IP、端口和网络模式

挂载已经分开，容器地址和发布端口还在网络字段里。模式、IP 和端口映射要各留一份。

操作顺序：先读 NetworkSettings，再读网络模式和端口，对上 IP、网关和别名。

**1. 查看容器网络详情。** 多张网络都在这份 JSON 里，不要只抄第一个 IP。

```bash
docker inspect --format '{{json .NetworkSettings}}' 容器ID | jq .
```

**2. 单独看网络模式。** 它在 `HostConfig` 里，和上一份网络详情一起对照。

```bash
docker inspect --format 'NetworkMode={{.HostConfig.NetworkMode}}' 容器ID
```

**3. 再看端口映射。** `docker port` 没有输出时，仍保留 Ports 的 JSON，确认是没有发布还是查询失败。

```bash
docker port 容器ID
docker inspect --format '{{json .NetworkSettings.Ports}}' 容器ID | jq .
```

**4. 按表把字段对到要回答的问题上。** 字段为空就留空。

| 字段 | 分析目标 |
|---|---|
| `IPAddress` / `Networks.*.IPAddress` | 容器在各 Docker 网络中的 IP |
| `Ports` | 容器端口与宿主机监听地址、端口的映射 |
| `Gateway` | 容器默认网关 |
| `MacAddress` | 与邻居表、抓包或日志关联 |
| `HostConfig.NetworkMode` | `bridge`、`host`、`container:<id>`、自定义网络 |
| `Aliases` | 服务别名和容器间名称解析关系 |

本节已核对 `IPAddress`、`Ports`、`Gateway`、`MacAddress`、`HostConfig.NetworkMode` 和 `Aliases`；`docker port` 为空时，以 `NetworkSettings.Ports` 说明是没有发布还是查询失败。模式、各网络里的 `Networks.*.IPAddress` 和端口 JSON 来自同一个容器 ID，一并留存NetworkSettings JSON、NetworkMode 和 `docker port` 的输出。

### 01.7 权限与逃逸面补充

网络和挂载之外，还要看这个容器是不是特权、是否共用宿主机命名空间、有没有关掉安全模块。

操作顺序：先一条 format 读权限字段，再对照特权、能力和安全选项，对上 docker.sock 挂载。

**1. 把特权、命名空间、能力和安全选项一次摘出。** 摘取失败就回到完整 inspect，不要只留 `Privileged`。

```bash
docker inspect --format 'Privileged={{.HostConfig.Privileged}} PidMode={{.HostConfig.PidMode}} IpcMode={{.HostConfig.IpcMode}} UsernsMode={{.HostConfig.UsernsMode}} CapAdd={{json .HostConfig.CapAdd}} SecurityOpt={{json .HostConfig.SecurityOpt}}' 容器ID
```

**2. 重点看这些组合。** 重点关注 `Privileged=true`、宿主机 PID/IPC/网络、危险 capability（如 `SYS_ADMIN`、`SYS_PTRACE`、`SYS_MODULE`、`DAC_READ_SEARCH`、`NET_ADMIN`、`NET_RAW`）、关闭 seccomp/AppArmor/SELinux，以及挂载 Docker Socket。某一项是空或 false，就写明没看到，不要和挂载节的 docker.sock 互相代替。

本节已核对 `Privileged=true` 与否、PidMode、IpcMode、UsernsMode、CapAdd 和 SecurityOpt；安全选项为空时，还要回到挂载节看有没有 Docker Socket，不能互相补成“没有逃逸面”。format 的每一项都能在原始 inspect 的 `HostConfig` 里找到，一并留存这条 format 输出，以及和挂载清单的对照。

---

<span id="02-docker-镜像结构与取证"></span>

## 02 固定镜像身份与构建层

容器已经对上某个镜像，还不知道标签、摘要和构建层各算什么。下面先列镜像，再读详情和构建历史。

操作顺序：先按完整镜像 ID 列清单，再读 inspect 和 history，对上摘要、标签和层。


### 02.1 列出镜像

容器清单里的镜像名可能有多个标签。计数之前先定按 ID、仓库还是 Registry 算。

操作顺序：先列出镜像和摘要，再按口径去重，对上清单文件之后才报数量。

**1. 先看本地镜像的常用列表。** 这行可能截断 ID，也不能代替带摘要的清单。

```bash
docker images
```

**2. 再显示完整摘要，并把中间镜像也纳入另一次列表。** 两次范围不同，数量不要混着报。

```bash
docker images --no-trunc --digests
docker images -a --no-trunc
```

**3. 清单数量先定口径，再计数。** 用已经保全的完整清单统计，不把终端显示行数直接当对象数。

- **容器数**：按完整容器ID去重，说明是否包含已停止对象。现有 `docker ps -a` 是该daemon当前可见清单，不包含已删除且只剩磁盘残留的容器。
- **镜像数**：按完整镜像ID去重。同一个ID有多个标签仍是一份镜像；有无标签、是否使用 `-a` 纳入中间镜像，都写清楚。
- **镜像仓库数**：按不同Repository名称去重，不把同一仓库的多个Tag算成多个仓库。`<none>` 表示没有相应命名引用，不是一家仓库；它对应的镜像仍可计入镜像ID数量。
- **Registry地址数**：按镜像引用中的Registry端点归类，和Repository数量分开。`registry.example:5000/team/mysql:8.0` 中，Registry是 `registry.example:5000`，Repository是 `registry.example:5000/team/mysql`，Tag是 `8.0`。不能把所有冒号都当Tag分隔符；Registry自己也能带端口。

**4. 没有写主机名的引用，不要当成已经知道仓库数。** 无显式Registry主机名的常规镜像引用通常按Docker Hub命名规则解释，仍要保存原引用。镜像可以本地构建或重新打标签，`registry-mirrors` 是加速/代理配置，`insecure-registries` 是访问策略，两者的条目数都不等于“实际使用过的镜像仓库数”；实际来源继续核对RepoDigests、拉取或代理日志。配置里有几条镜像加速，不能写成用过几个仓库。

**5. 用构造例子核对去重。** 两行分别为 `team/db:8.0` 和 `team/db:stable`，完整镜像ID相同，则镜像数为1、Repository数为1、标签数为2。每个数量都附清单文件、采集时间、筛选范围和去重键，才便于复核。ID 不同就不要套这个 1、1、2。

本节已核对完整镜像 ID、标签、`<none>` 和 Registry 各自的数量口径；没有 RepoDigests 或拉取日志时，不把 `registry-mirrors` 的条数当成使用过的仓库数。每个数量旁边都有清单文件、采集时间、筛选范围和去重键，一并留存 `--no-trunc --digests` 和 `-a` 两份清单。

### 02.2 查看镜像详情

镜像 ID 已经从清单里取出，标签仍可能被改掉。用摘要和层来认这是哪一份镜像。

操作顺序：先 inspect 镜像，再按表读身份和入口，对上 RepoDigests 和层摘要。

**1. 查看镜像详情。** 传入的是镜像 ID 或能够唯一命中的引用。命中多份时停下来，不要取第一份。

```bash
docker inspect 镜像ID
```

**2. 按表看这些字段能证明什么、不能证明什么。** `RepoTags` 不能单独证明内容。

| 字段 | 取证意义 |
|---|---|
| `Id`、`RepoDigests` | 用内容摘要唯一关联镜像，标签可被移动或覆盖 |
| `RepoTags` | 显示仓库和标签，但不能单独证明镜像内容 |
| `Created` | 镜像配置创建时间，不等于拉取到本机的时间 |
| `Config.Env` | 构建时保留的环境变量，可能含凭据或代理 |
| `Config.Cmd`、`Entrypoint` | 默认启动命令，识别异常执行逻辑 |
| `Config.Labels` | 构建系统、源仓库、版本、维护者线索 |
| `RootFS.Layers` | 内容层摘要，用于镜像关联和完整性分析 |
| `Architecture`、`Os` | 平台信息，识别不一致或异常镜像 |

**3. 把核心字段摘到一行，值仍要能回到完整 JSON。** `Created` 只是配置里的创建时间。

```bash
docker inspect --format 'ID={{.Id}} Created={{.Created}} RepoTags={{json .RepoTags}} RepoDigests={{json .RepoDigests}} Env={{json .Config.Env}} Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}} Labels={{json .Config.Labels}}' 镜像ID
```

本节已核对镜像 `Id`、`RepoDigests`、`RepoTags`、`Created`、入口、`Config.Env`、`Config.Labels` 和 `RootFS.Layers`；只有 `RepoTags` 时，内容是否同一份还要看 `Id` 或 `RepoDigests`。format 里的 `Id` 和完整 inspect 的 `Id` 相同，一并留存镜像 inspect JSON；`Config.Env` 按敏感材料保存。

### 02.3 构建历史

镜像身份已经固定，还要看每一层的命令里有没有下载、写入口令或事后删除文件。history 只是线索。

操作顺序：先跑 history，再标出下载、口令和删除，本机何时拉到要另查日志。

**1. 查看构建层和命令。** `--no-trunc` 把命令留全。镜像 ID 对不上就回到上一节的 `Id`。

```bash
docker history --no-trunc 镜像ID
```

**2. 在历史命令里重点找这些情况。** 找到一行只说明构建命令里写过，文件是否还在层里要到导出的层里看。

- `RUN curl`、`wget`、远程脚本或未知仓库；
- `ENV`、`ARG` 误写入的令牌或密码；
- 新增用户、SSH Key、SUID 文件；
- 删除后仍可能残留在旧层中的敏感文件；
- 可疑入口点、加密矿工、下载器或持久化脚本。

**3. 分清配置时间和本机拉取时间。** 镜像 `Created` 是镜像配置内的时间；本机首次拉取时间通常需要结合 Docker/containerd 元数据、daemon 日志、代理日志和文件时间综合判断。这些材料没有时，不要把 `Created` 写成拉取时间。

本节已核对 `docker history --no-trunc` 里的层命令，以及其中的 `RUN curl`、`wget`、`ENV` 或 `ARG`；没有 daemon 或代理日志时，`Created` 不能写成本机首次拉取时间。历史里的命令行能对上该镜像 `Id`，删除文件是否残留要另看层内容，一并留存未截断的 history 输出，以及拿来对照时间的元数据或日志范围。

---

<span id="03-docker-镜像分析命令"></span>

## 03 分清镜像命令的只读与删除

要在分析机上补镜像或删镜像时，先看这条命令会不会改存储。证据主机上还没导出的镜像不能删。

操作顺序：先看命令是只读、拉取还是删除，再保存摘要，对上之后才在副本里 pull 或 rmi。

**1. 先看每条命令的副作用。** 【仅在副本/仿真/授权环境执行】下表中的 pull 会写入镜像存储，rmi 会删除镜像引用或层；先保存镜像摘要和归档。search 需要网络，采集主机先读已有本地镜像。

<details>
<summary>展开镜像命令副作用表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker images | 列出本地镜像 | 快速查看仓库名、Tag、镜像 ID 和大小 |
| docker image ls | 列出本地镜像，语义同 docker images | 脚本或文档中使用对象式命令 |
| docker search &lt;term&gt; | 搜索镜像注册表中的公开镜像 | 搭建环境前查找基础镜像；需要网络 |
| docker pull &lt;image&gt; | 拉取镜像 | 复现环境；会写入本地主机 |
| docker rmi &lt;image&gt; | 删除镜像引用及可清理层 | 清理测试镜像 |
| docker rmi -f &lt;image&gt; | 强制移除镜像引用 | 处理冲突引用；可能破坏复现条件 |
| docker image inspect &lt;image&gt; | 读取镜像配置和元数据 | 检查 Env、Entrypoint、Cmd、层和架构 |

</details>

**2. 删除只放在已经导出之后。** 不要在尚未导出或记录摘要的证据主机上执行 docker rmi 或 docker rmi -f。镜像可能是重建容器和分析层内容的唯一来源。还没保存摘要就不要执行表里的删除行。

本节已核对本地镜像清单，以及准备执行的是只读、拉取还是删除；摘要和归档还没保存时，不能在证据主机上 rmi。删除前的镜像 ID 或摘要已经留下，search 的网络需求和 pull 的写入分开记录，一并留存 `docker images` 或 `docker image inspect` 的输出，以及导出归档的哈希。

### 03.1 镜像层与历史

history 里看到后一层删过文件，最终视图里也找不到。要到更早的层里找，而不是只靠 history 断定文件还在。

操作顺序：先看 history，再定位 COPY 和后面的 rm，层还在归档里才去早层读。

**1. 先看这一份镜像的历史。** 把 `<image>` 换成已经固定的镜像 ID。

```bash
docker history <image>
```

**2. 怎样找被后层删除的文件。** 镜像由只读层组成，docker history 给出命令、时间和大小。先定位 COPY flag.txt /，再定位后层的 RUN rm /flag.txt。最终容器看不到文件时，去导出的早层归档找它。history 里没有这两步时，不要假定文件一定被这样删过。

**3. 层不在了就记缺层。** 相关层仍在包里才可能恢复；经过 squash、缓存清理或层重写时，记录缺层情况，不只靠 history 推定文件还在。

**4. 深入看内容时先导出。** history 只是线索；深入分析时应先 docker save 导出镜像，记录文件哈希，再离线检查 manifest 和 layer tar。还没导出就不要把 history 的一行当成层里的字节。

本节已核对history 里的 COPY 和后层 RUN rm，以及导出包里是否还有对应早层；squash、缓存清理或层重写之后，文件是否还能恢复要记成未知。早层归档里的路径和 history 里的命令指的是同一次构建顺序，一并留存 `docker history` 输出、save 归档的哈希、manifest 和 layer tar。

<span id="04-docker-容器管理"></span>

## 04 分清创建、启停与删除的对象

容器已经能列出来，接下来会碰到创建、启停和删除。这些命令会改运行状态，下面先分清每条命令动的是哪一层。

操作顺序：先分清列出、创建、启停和删除，再看它改不改现场，对上才能在副本里做。


### 04.1 列出容器

管理命令会改状态，列清单本身不改。先选对范围，避免只看到还在跑的容器。

操作顺序：先选范围，再留下这份清单，对上对象式命令和 docker ps 是不是同一次范围。

**1. 按范围选命令。** 取证用包含已退出容器的那两行。只跑第一行会漏掉停止的容器。

| 命令 | 范围 | 常用场景 |
| --- | --- | --- |
| docker ps | 仅运行中容器 | 快速确认当前服务 |
| docker ps -a | 全部容器，包括已退出容器 | 取证首选，避免遗漏失败或停止的容器 |
| docker container ls -a | 与 docker ps -a 等价 | 对象式命令写法 |

本节已核对这次列表是只含运行中容器，还是包含已退出容器；只跑了 `docker ps` 时，已退出容器还没看。`docker container ls -a` 和 `docker ps -a` 的容器集合一致，一并留存所选列表命令的原输出。

### 04.2 docker run 与端口映射

要从镜像再起一个容器时，这条命令会新建容器并可能把端口发布到主机。先留当前清单。

操作顺序：先保存清单，再看 run 会不会发布端口，对上主机端口和容器端口。

**1. 这些命令都会创建并启动新容器。** 【仅在副本/仿真/授权环境执行】下面的 docker run 会从镜像创建并启动新容器，还会发布端口；先保存当前清单，实验结果另记。

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker run &lt;image&gt; | 从镜像创建并启动新容器 | 临时运行或复现；每次可创建新容器 |
| docker run -d &lt;image&gt; | 后台运行容器 | 启动 Web 或数据库服务 |
| docker run -d --name web &lt;image&gt; | 指定容器名称 | 便于后续 logs、exec 和 cp |
| docker run -d -p 8080:80 &lt;image&gt; | 发布容器端口到主机 | 将主机 8080 转发到容器 80 |

**2. 端口映射按这个方向读。** `-p` 的完整格式是 `主机IP:主机端口:容器端口`（省略主机 IP 时写作 `主机端口:容器端口`）；下面要写全，单独的 `127.0.0.1:8080` 不是合法 `-p` 参数。

-p 127.0.0.1:8080:80  
→ Host 127.0.0.1:8080  
→ Container 80  
→ Nginx

**3. 没写主机 IP 时，不要当成只监听本机。** 若不指定主机 IP，发布端口通常绑定到 Docker 配置允许的主机接口。只需本机访问时，可显式使用 -p 127.0.0.1:8080:80，减少外部暴露。实际绑到哪块网卡，用发布之后的端口列表核对，配置里写了地址也不等于已经能连上。

本节已核对新容器来自哪一个镜像，以及主机端口和容器端口的对应；没写主机 IP 时，还要看实际绑定的接口，不写成只对本机开放。`-p` 的主机端口和容器端口与运行后的发布项一致，一并留存运行前的容器清单、实际执行的 run 命令，以及实验容器 ID。

### 04.3 start stop restart kill

容器已经存在，要不要把它拉起或停掉。这四条都会改原来的运行状态，不能当首轮采集。

操作顺序：先保存 inspect、日志和进程，再按表选一条，stop 和 kill 的清理机会不同。

**1. 先留下状态，再选操作。** 【仅在副本/仿真/授权环境执行】start、stop、restart、kill 会改变原容器运行状态。先保存 inspect、日志和进程信息；按需要选一个操作，不把它们当首轮采集步骤。

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker start &lt;container&gt; | 启动已存在的停止容器 | 保留原配置继续运行 |
| docker stop &lt;container&gt; | 先发停止信号并等待，超时后强制终止 | 正常维护和保留应用收尾机会 |
| docker restart &lt;container&gt; | 停止后重新启动 | 应用配置未变时快速重启 |
| docker kill &lt;container&gt; | 默认立即发送 SIGKILL | 进程无响应时使用；可能导致数据不一致 |

**2. 停和杀不要混用。** 还没保存日志和进程时，不要执行 kill。

| 比较项 | docker stop | docker kill |
| --- | --- | --- |
| 默认行为 | 优雅停止，超时后强制终止 | 立即发送 SIGKILL |
| 应用清理 | 通常有机会刷新缓冲区并退出 | 通常没有清理机会 |
| 取证影响 | 改变运行状态，可能触发退出逻辑 | 突然中断，可能丢失内存态和未落盘数据 |
| 建议 | 维护场景优先；先采集日志、进程和内存相关线索 | 仅在明确需要且已保全关键证据时使用 |

本节已核对操作前的 inspect、日志和进程，以及实际选的是 start、stop、restart 还是 kill；还没采集就 kill 时，内存态和未落盘数据可能已经不在。操作前后的状态分开保存，stop 和 kill 的差异按表解释，一并留存操作前的 inspect、日志、进程，以及这条命令的执行时间。

### 04.4 删除容器

容器要删掉之前，可写层和一部分元数据会跟着没。卷里的数据不一定一起消失，所以先看挂载。

操作顺序：先保存 ID、inspect 和挂载，再在副本里 rm，删完再查卷还在不在。

**1. 先看这两条命令的差别。** 第一条删除已停止容器，第二条会先停掉还在跑的容器再删。

```bash
docker rm <container>
docker rm -f <container>
```

**2. 只在副本里删，并且先留挂载。** 【仅在副本/仿真/授权环境执行】docker rm 删除已停止容器，-f 会强制停止并删除运行容器。删除后可写层和部分元数据会丢失。再查命名 Volume 和 Bind Mount，里面的数据可能仍保留；先保存 Mounts，别只找容器目录。容器目录没了而 Mounts 还没保存时，数据位置就对不上了。

**3. 取证主机不要先删再分析。** 取证主机上不要先 rm 再分析。至少先 inspect、logs、diff、导出或复制关键文件，并记录容器 ID 和镜像摘要。这些还没有时，不要执行上面的命令。

本节已核对删除前的容器 ID、镜像摘要和 Mounts；只剩容器目录、没有 Mounts 时，卷和绑定目录里的数据可能还在别处。inspect、logs 或 diff 的保存时间早于 `docker rm`，一并留存容器 ID、镜像摘要、Mounts，以及删除前导出的文件。

<span id="05-docker-容器内部分析"></span>

## 05 分清 exec 与宿主机侧证据

容器还在，要看里面的进程和文件。下面先分清 exec 会新起进程，再决定进不进容器。

操作顺序：先从宿主机保存状态，再决定要不要 exec，对上进程和目录之后再读文件。


### 05.1 docker exec

要从外面在容器里执行命令。exec 不新建容器，但会在已经运行的容器里新起进程。

操作顺序：先从宿主机保存 top 和 inspect，再按镜像选 shell 或单条命令，交互留下的变化单独记。

**1. 按目的选命令。** 精简镜像没有 bash 时，改用 sh，不要因为 bash 失败就换一个容器。

<details>
<summary>展开 exec 命令对照表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker exec -it &lt;container&gt; bash | 在运行容器中启动交互式 Bash | 进入 Debian、Ubuntu 等常见镜像 |
| docker exec -it &lt;container&gt; sh | 在运行容器中启动 POSIX shell | Alpine 或精简镜像通常没有 bash |
| docker exec &lt;container&gt; &lt;command&gt; | 在运行容器中执行单条命令 | 减少交互式改动并保存输出 |
| docker exec web ls /var/www/html | 列出 Web 根目录 | 检查源码和异常文件 |
| docker exec web cat /etc/nginx/nginx.conf | 读取 Nginx 配置 | 确认日志路径、代理和站点配置 |
| docker exec -it mysql mysql -uroot -p | 进入 MySQL 客户端并交互输入密码 | 授权范围内检查数据库 |

</details>

**2. 先保存外部能拿到的状态。** 【仅在副本/仿真/授权环境执行】exec 在已有的运行容器中启动命令，不创建新容器。先从宿主机保存 top、inspect 和静态文件；确需进入副本时，只执行必要命令并保存输出。交互 shell 可能新增历史、临时文件和访问时间，实验结束把这些变化单列。容器未运行导致 exec 失败时，保持停止，改读已经保存的文件。

本节已核对执行的是单条命令还是交互 shell，以及输出对应的容器；交互 shell 新产生的历史和临时文件还没单列时，不要写进原来的现场。宿主机上的 top、inspect 早于这次 exec，命令输出单独保存，一并留存exec 的命令和输出，以及结束后新增文件的清单。

### 05.2 进入容器后的基本检查

已经决定在副本里看容器内部。容器自己的命令可能不完整，要和宿主机上的证据对一下。

操作顺序：先看进程和这次 env，再列应用目录，和 docker top、inspect 交叉核对。

**1. 在容器里做这几项基本查看。** 某一条命令不存在，就记下镜像里没有这个工具，不要改用宿主机的结果冒充容器内输出。

```bash
ps aux
env
ls /
ls /app
ls /var/www
ls /var/www/html
```

**2. 进程列表看异常入口。** ps aux：识别异常进程、启动参数、父子关系和可疑解释器。精简镜像可能没有完整 ps。没有 ps 时，回到宿主机的 `docker top`。

**3. env 看的是谁。** 它显示这次新启动的 env 进程的环境。`docker exec` 通常沿用容器创建配置，可由本次 `-e` 覆盖。入口脚本后来只给应用进程设置的变量，不会自动出现在这里。这次 env 里没有的变量，不要写成应用进程也没有。

**4. 要查已经在跑的应用进程，先定 PID。** 要查已有应用进程，先确认它的 PID 再读对应环境；本次 env 输出按敏感材料保存，不写成整个应用的完整环境。

**5. 应用目录里看新增和上传。** 关注新增脚本、WebShell、备份压缩包、上传目录和近期修改文件。目录不存在就记缺失，不要创建。

**6. 容器里的命令要和外面的证据对上。** 容器内命令通过容器自身工具运行，可能不完整或已被篡改。将 docker top、inspect 和宿主机侧证据交叉验证。对不上时，以宿主机侧为准，并记下容器内工具的差异。

本节已核对这次 `ps` 或 `docker top` 的进程，以及这次 `env` 和目录列表；`env` 没有入口脚本后来设置的变量时，还要按 PID 读那个进程的环境。容器内输出和宿主机的 docker top、inspect 能对上同一个进程或同一条配置，一并留存上述命令输出；`env` 按敏感材料保存，不写成应用的完整环境。

<span id="06-dockerfile-与镜像构建"></span>

## 06 构建前先看上下文与分层残留

当前目录里有 Dockerfile，要在副本里做成镜像并起容器。构建前先看目录里有什么会被打进去。

操作顺序：先看构建上下文，再 build 和 run，对上镜像名和发布端口。

**1. 这两条命令先构建，再创建容器并发布端口。** 【仅在副本/仿真/授权环境执行】这组命令先用 docker build 读取当前目录的 Dockerfile，-t 设置镜像名称和可选 Tag；再用 docker run 创建容器并发布端口。

```bash
docker build -t ctf-web .
docker run -d -p 8080:80 ctf-web
```

构建失败时看 Dockerfile 和当前目录，不要换到别的目录重跑来凑一个同名镜像。

**2. 构建前先看上下文里有哪些文件。** 构建前检查当前目录有哪些文件，用 .dockerignore 排除版本库、密钥和本地备份，避免它们进入镜像。没有忽略文件时，先列出目录再决定要不要构建。

本节已核对这次构建用的当前目录、镜像名，以及 `8080:80` 这条发布；没有 .dockerignore 时，版本库、密钥和本地备份有没有进镜像，还要先列出目录。`docker build -t ctf-web .` 和后面的 `docker run` 用的是同一个镜像名，一并留存构建前的目录列表、镜像名，以及这次 run 产生的容器。

### 06.1 分层残留示例

镜像能构建，但后一条指令删掉的文件可能还在早一层里。最终容器看不到，不等于层里没有。

操作顺序：先看这两条指令各成一层，再去早层归档找文件，不要靠后层删除来消除秘密。

**1. 这两条指令通常是两层。** 后层删除只会在联合文件系统视图中隐藏早期文件。

```dockerfile
COPY flag.txt /
RUN rm /flag.txt
```

**2. 早层还在时，文件可能仍在归档里。** 早期层归档仍可能包含 flag.txt。长期解决方式是避免把秘密放入构建上下文或镜像层，而不是在后续层删除。视图里没有 flag.txt 时，去早层找，不要写成文件已经不存在。

**3. 秘密可能在参数、变量和层里。** 构建参数、环境变量、历史命令和层内容都可能泄露秘密。检查 docker history、image inspect 和离线导出的 layer tar。history 有删除命令但层归档不在时，记成未能从层里读到字节。

本节已核对COPY 和后面的 RUN rm 分成两层，早层归档里是否还有 flag.txt；只有 history、没有 layer tar 时，不能证明文件字节还在或已经没了。history、image inspect 和早层 tar 里的路径指的是同一次构建，一并留存Dockerfile 片段、history 和导出的 layer tar。

<span id="07-docker-镜像与容器导入导出"></span>

## 07 分清 save/export 与卷的保全

手里是镜像或容器，要做成可以离线看的包。load、import 会在分析机上新增镜像，只检查包时不必导入。

操作顺序：先分清 save、load、export、import，只读包就列成员，卷和日志另存。

**1. 导入会改分析机，只读检查不必导入。** 【仅在副本/仿真/授权环境执行】下面 load/import 会在分析机新增镜像。只是检查归档时，先列成员并离线读取，不必导入或运行。

```bash
docker save -o image.tar image
docker load -i image.tar
docker export container -o container.tar
docker import container.tar repository:tag
```

**2. 按对象和保留内容选命令。** 要层和元数据用 save/load，只要合并后的文件系统用 export/import。

<details>
<summary>展开 save/export 对照表</summary>

| 命令 | 操作对象 | 保留内容 | 适用场景 |
| --- | --- | --- | --- |
| docker save | Image | 镜像层、Tag 和镜像元数据 | 镜像备份、离线层分析和迁移 |
| docker load | Image archive | 恢复 save 产生的镜像结构 | 加载完整镜像归档 |
| docker export | Container 文件系统 | 合并后的文件系统快照，不保留原镜像层历史 | 提取容器文件系统 |
| docker import | 文件系统 tar | 生成新的单层镜像及指定变更 | 把文件系统快照转成镜像 |

</details>

**3. 按要留下的内容选一对命令。** 要保留镜像分层和元数据，使用 save/load；只需要容器合并后的文件系统，使用 export/import。选错一对时，层历史或可写层会丢，回到表里重选，不要连做四种。

**4. 导出前先分三份保存。** `export` 只取容器文件系统，Volume 数据另存；原 inspect 和日志驱动数据也另存。不要把归档中的一个目录当成已经保存了挂载卷。包里有个和挂载点同名的目录时，仍以 Mounts 另存卷。

本节已核对这次用的是 save/load 还是 export/import，以及 `export` 之外另存的卷；归档里有同名目录但 Mounts 还没另存时，卷不能算已经保全。所选命令和表里的操作对象一致；只读检查时没有执行 load 或 import，一并留存归档和成员列表，以及分开保存的 Volume、inspect 和日志。

### 07.1 docker commit

调试副本上的可写层想留成镜像。commit 不包含卷，也不能代替完整采集。

操作顺序：先记容器状态，再在副本里 commit，卷单独保存，并记下新镜像 ID。

**1. 提交前先知道这条命令留什么。** 把 `<container>` 换成已经记录的容器。

```bash
docker commit <container> backup:v1
```

**2. 只在副本里提交，卷另外保存。** 【仅在副本/仿真/授权环境执行】`commit` 保存容器可写层和部分配置，适合留存副本的调试结果。执行前后记录容器状态和新镜像 ID，并单独保存 Volume 数据。新镜像 ID 没记下来之前，不要删原容器。

**3. 不要用 commit 包代替完整采集。** 运行容器默认会在提交期间暂停进程，Volume 也不会进入新镜像，因此不能用 commit 包代替完整采集。它难以复现构建过程；生产构建仍优先使用版本化 Dockerfile。卷里的数据不在新镜像里时，回到 Mounts 去取。

本节已核对提交前后的容器状态，以及新镜像 ID；Volume 没有单独保存时，新镜像里没有这份额外数据。`commit` 前后的容器状态和新镜像 ID 是先后两份记录，一并留存新镜像 ID、提交时的容器状态，以及单独保存的卷。

<span id="08-实战分别保全容器状态可写层与镜像历史"></span>

## 08 实战：分开保全状态、可写层与镜像层

配置文件在容器里看不到了，还分不清是运行后删的，还是镜像后层藏起来的。下面先固定容器和镜像，再分开可写层和镜像层。

操作顺序：先保存容器 ID 和镜像，再对可写层，最后离线读镜像层。


### 08.1 场景与材料

Web 容器里一个配置文件不见了。材料是已确认的主机会话和一份镜像包，输出要放到独立目录。

操作顺序：先确认 web 的完整 ID，再保存 inspect、history、diff 和挂载，三个时间不要合成一个部署时间。

**1. 先认场景和路径。** 目标是判断 Web 容器中一个消失的配置文件属于容器运行后变化，还是镜像构建时在后层删除。材料包括已确认主机会话中的 `web` 容器、容器清单与 inspect 结果，以及保全目录 `/work/input/web-image.tar`。分析输出位于 `/work/output/container-image/`。下面名称、时间、路径和输出为构造示例，用于说明操作与判读，不表示实际附件已复跑。

**2. 从清单确认完整 ID，标签不能代替镜像 ID。** 先从清单确认 `web` 对应的完整 ID，并保存原始 JSON；标签可能移动，后续以实际镜像 ID 或摘要定位。容器名对不上时，改用清单里的 ID，不要在分析机上找同名 `web`。

```bash
OUT=/work/output/container-image
mkdir -p "$OUT"
docker ps -a --no-trunc > "$OUT/containers.txt"
CID=$(docker inspect --format '{{.Id}}' web)
docker inspect "$CID" > "$OUT/container-inspect.json"
IMAGE_ID=$(docker inspect --format '{{.Image}}' "$CID")
printf '%s\n' "$CID" > "$OUT/container-id.txt"
printf '%s\n' "$IMAGE_ID" > "$OUT/image-id.txt"
docker image inspect "$IMAGE_ID" > "$OUT/image-inspect.json"
docker history --no-trunc "$IMAGE_ID" > "$OUT/history.txt"
docker diff "$CID" > "$OUT/container-diff.txt"
docker inspect --format '{{json .Mounts}}' "$CID" > "$OUT/mounts.json"
```

**3. 这三个值不要合成“部署时间”。** 容器 `2025-05-18T02:00:00Z` 是最近启动时间；镜像 `Created` 的 `2025-05-17T10:00:00Z` 是镜像配置创建时间；Mounts 把 `/var/www/html/uploads` 指向独立卷。查上传文件时沿这个卷找，查旧启动时另读日志。三个值对不上同一件事时，分开写。

本节已核对 `web` 的完整容器 ID、镜像 ID、history、diff 和 Mounts；上传文件不在 diff 里时，还要沿 `/var/www/html/uploads` 的卷去找。容器启动时间、镜像 `Created` 和卷路径分属三条记录，没有合成一个部署时间，一并留存 `/work/output/container-image/` 下的清单、inspect、history、diff 和 mounts。

### 08.2 对应可写层与进程证据

diff 里已经有新增、修改和删除。还要分清脚本有没有在跑，以及环境变量属于哪一次进程。

操作顺序：先读 A/C/D，再复制文件并看 top，环境按创建配置、exec 和进程分开。

**1. 先按构造出来的 diff 认路径。** `A/C/D` 分别为新增、修改、删除的可写层路径。

```text
A /tmp/worker.sh
C /etc/nginx/nginx.conf
D /app/config.yml
```

对 `/tmp/worker.sh` 先复制并静态读取，不执行样本；卷中的 uploads 变化另从卷保全，diff 没有列出不代表未修改。diff 和这三行不同时，以实际 `container-diff.txt` 为准。

**2. 把新增脚本和改过的配置复制出来，并看查询时的进程。** 复制失败就留下错误和容器状态。

```bash
docker cp "$CID:/tmp/worker.sh" "$OUT/worker.sh"
docker cp "$CID:/etc/nginx/nginx.conf" "$OUT/nginx.conf"
file "$OUT/worker.sh"
sha256sum "$OUT/worker.sh" "$OUT/nginx.conf"
docker top "$CID" -eo pid,ppid,user,lstart,cmd > "$OUT/processes.txt"
```

**3. 容器已停止就不要为了进程列表去启动它。** 若容器已停止，top 会失败，保存错误与容器状态，继续离线分析，不为取得进程列表而启动它。脚本存在、可执行或名称可疑不等于已经运行；需将进程参数、日志与文件哈希对应。对不上就停在“文件存在”。

**4. 查环境按下面分开。**

- inspect 的 `Config.Env`：容器创建时配置。
- exec env：这次新增进程的环境。
- `/proc/<PID>/environ`：所选进程启动时的环境内存区；进程后来在自身内存改的变量可能不在其中。

**5. 先用 top 找应用的宿主机 PID，再读那份环境。** 先用 top 找应用的宿主机 PID，再在允许读取时保存该文件和采集时间。[Linux proc_pid_environ 手册](https://man7.org/linux/man-pages/man5/proc_pid_environ.5.html)

```bash
# 目标现场；State.Pid 是容器主进程，不一定是实际业务子进程
MAIN_PID=$(docker inspect --format '{{.State.Pid}}' "$CID")
test "$MAIN_PID" -gt 0 && tr '\0' '\n' < "/proc/$MAIN_PID/environ" > "$OUT/main-process-environ.txt"
```

访问受限、PID 已退出或重用时应记录失败；不能把空结果写成没有凭据。只需查看文件和配置时优先静态副本，不启动 exec。`State.Pid` 不是业务子进程时，改用 top 里的那个 PID。

本节已核对diff 里的 `A/C/D` 路径、复制文件的哈希，以及查询时的进程；top 失败或 environ 读不到时，不写成进程没跑过或没有凭据。文件哈希、进程参数和 `Config.Env` 或 `/proc/<PID>/environ` 各有来源，一并留存 `worker.sh`、`nginx.conf`、哈希、`processes.txt` 和主进程环境；失败的命令保留错误。

### 08.3 镜像归档的离线层分析

可写层已经看过。配置若是构建时删的，要到镜像包的早层里找，不必先 load 或运行。

操作顺序：先导出或核对已有 tar，再读 manifest 和层，看到 whiteout 就回早层取原字节。

**1. 在线保全时再导出镜像。** 在线保全镜像时可执行以下导出，输出到独立目录；它保留镜像结构，不采集容器可写层或挂载卷。导出的包里没有卷是预期结果，卷仍按 Mounts 另存。

```bash
docker save -o "$OUT/image.tar" "$IMAGE_ID"
sha256sum "$OUT/image.tar"
tar -tf "$OUT/image.tar" > "$OUT/archive-members.txt"
```

**2. 已经有保全包时，不要 load。** 若只有 `/work/input/web-image.tar`，先复制到输出目录并核对保全哈希，不需要 load 或运行容器。归档可能包含 Docker manifest 与 OCI 布局；先列成员，再选择实际存在的结构，不能假定层文件都叫 `layer.tar`。成员名单里没有 `layer.tar` 这个名字时，按名单里的实际路径读。

**3. 确认只有一条镜像记录，再取配置和层列表。** 先列归档成员，确认确有 `manifest.json`。下面代码只用于已核对 manifest **仅含一条目标镜像记录**的归档；读 `Config`、`RepoTags`、`Layers`，逐项与 image inspect 对应。若 manifest 有多条，不运行这段固定取 `.[0]` 的示例；先按配置摘要、标签和层列表确定目标，再单独提取该记录。

```bash
tar -xOf "$OUT/image.tar" manifest.json > "$OUT/manifest.json"
jq . "$OUT/manifest.json"
jq -r '.[0].Layers[]' "$OUT/manifest.json" > "$OUT/layer-members.txt"
config_member=$(jq -r '.[0].Config' "$OUT/manifest.json")
tar -xOf "$OUT/image.tar" "$config_member" > "$OUT/image-config.json"
jq '{created, config, rootfs, history}' "$OUT/image-config.json"
```

**4. 逐层列出成员，再找配置文件和删除标记。** 逐层输出到固定工作文件，先列成员再读取目标路径；这种定向读取无需把未知归档的全部路径解包到文件系统。

```bash
n=0
while IFS= read -r layer; do
  n=$((n + 1))
  printf -v layer_out '%s/layer-%03d.tar' "$OUT" "$n"
  tar -xOf "$OUT/image.tar" "$layer" > "$layer_out"
  tar -tf "$layer_out" > "$layer_out.members.txt"
done < "$OUT/layer-members.txt"
grep -nE '(^|/)(config.yml|\.wh\.config.yml)$' "$OUT"/layer-*.members.txt
```

某一层解不开时，停下看这一层的格式，不要把后面的层编号提前。

**5. 看白化文件判断删除。** 示例早层有 `app/config.yml`，后层有 `app/.wh.config.yml`。whiteout 让后层视图隐藏早层文件；早层归档仍在时，到早层读取原字节。

**6. 不透明 whiteout 还要单独看。** opaque whiteout 还会隐藏目录中的下层条目。逐层看删除标记，再还原视图，不能只把各层直接覆盖解包。[OCI 镜像层与 whiteout 规范](https://github.com/opencontainers/image-spec/blob/main/layer.md)

**7. 从已经确认的早层抽出文件并做哈希。** 编号不是 002 时，换成层清单里的实际编号。

```bash
# 这里 002 是已从层清单确认的早层编号，实际材料需替换
tar -xOf "$OUT/layer-002.tar" app/config.yml > "$OUT/config-from-earlier-layer.yml"
file "$OUT/config-from-earlier-layer.yml"
sha256sum "$OUT/config-from-earlier-layer.yml"
```

**8. 读不出 tar 时先核对格式。** 如果层内容压缩方式与 tar 读取能力不匹配，先核对 media type 与文件格式，再在工作目录解码；保留原始 blob 哈希。构建经过扁平化、层重写或相关层缺失时，history 中的 COPY/RUN 线索不保证内容仍能恢复。解码失败就留下原始 blob，不要写成文件不存在。

本节已核对归档成员、单条 manifest 的 `Config`、`RepoTags`、`Layers`，以及早层里的 `app/config.yml` 或后层的 `app/.wh.config.yml`；manifest 有多条、层被压扁或 media type 读不出时，不运行取 `.[0]` 的示例，也不凭 history 断定文件还在。抽出的文件哈希来自层清单里确认过的那一层，并和 image inspect 的层顺序一致，一并留存 `image.tar` 的哈希、manifest、逐层成员名单和早层文件；原始 blob 哈希保留。

### 08.4 对比 save、export、load、import 与 commit

镜像包已经能离线看。还要分清 export 拿到的是合并后的文件系统，不是层历史，也不是卷。

操作顺序：先 export 并列出成员，再按三条检查包里有什么，load、import、commit 只在副本里选做。

**1. 导出容器文件系统并列出成员、计算哈希。** 这一包没有镜像层链。

```bash
docker export "$CID" -o "$OUT/container-filesystem.tar"
tar -tf "$OUT/container-filesystem.tar" > "$OUT/container-filesystem-members.txt"
sha256sum "$OUT/container-filesystem.tar"
```

**2. 按这三条检查 export 包。**

1. `export` 取导出期间读到的合并文件系统，没有原镜像层链。
2. 卷挂载在已有目录上时，包里保存被遮住的底层目录，卷当前内容仍沿 `Mounts` 单独采集。
3. 记录导出开始/结束时间并列出归档成员。活体文件可能边读边变，特别是数据库；退出成功还要检查文件集合和一致性。

退出码是 0 但成员清单和预期不一致时，不要把这次导出当成一致快照。

**3. 另外三种命令都会改分析机上的 Docker。** 【仅在副本/仿真/授权环境执行】`docker load -i image.tar` 读取镜像包，`docker import container.tar repository:tag` 新建文件系统镜像，`docker commit <container> backup:v1` 保存可写层和部分配置。它们都会新增或改变分析机 Docker 内容。

**4. 包以外的材料仍要留着。** 恢复包之外仍保留原容器 inspect、日志、运行记录和独立卷；先查包内容，再选择需要的命令，不连做三种操作。

**5. 最后能写到哪一层，按字节和路径来。** 最终记录完整容器 ID、镜像 ID/仓库摘要、时间字段、可写层差异、挂载清单、层顺序、归档成员路径和恢复文件哈希。可以确认“某字节内容来自某镜像早层”或“某路径在容器可写层被修改”，不能凭文件残留直接声称它在事件时执行或被外部访问。

可核对 [Docker exec 文档](https://docs.docker.com/reference/cli/docker/container/exec/)、[save 文档](https://docs.docker.com/reference/cli/docker/image/save/)与 [export 文档](https://docs.docker.com/reference/cli/docker/container/export/)。

本节已核对export 包的成员和哈希，以及它和 save、load、import、commit 各留什么；包里没有卷的当前内容时，还要沿 `Mounts` 另采；没有执行记录时，不写成事件时已经运行。文件哈希能指回某一早层或某一条可写层差异，导出起止时间已经记下，一并留存 `container-filesystem.tar`、成员清单、哈希，以及没有连做 load/import/commit 的记录。

<span id="09-实战把数据库容器配置对应到业务数据"></span>

## 09 实战：把数据库容器配置对应到业务数据

数据库容器的配置、初始化变量和数据目录还叠在一起。先只读已经保存的 JSON，分清镜像身份、变量名和持久目录。

操作顺序：先从 JSON 认容器和镜像，再只列环境变量名，对上挂载之后才到那个目录找数据。

**1. 先认材料和边界。** 保全材料包含数据库容器与镜像 inspect、启动日志、挂载清单和网站连接配置。目标是核对镜像身份、凭据字段的层级及实际持久目录。下列命令只分析已保存 JSON；实例恢复使用另一个隔离副本。

**2. 从已保存的 JSON 抽出身份，并且只列环境变量的键名。** 文件打不开或不是预期结构时停，不要改去查现场容器。

```bash
OUT=/work/output/docker-database
umask 077
mkdir -p "$OUT"
jq '.[0] | {Id,Name,Image,Created,State,
    ImageReference:.Config.Image,Mounts}' \
  /work/input/mysql-inspect.json > "$OUT/container-identity.json"
# 只列键名，避免在普通展示中输出凭据
jq '.[0].Config.Env // [] | map(split("=")[0])' \
  /work/input/mysql-inspect.json > "$OUT/environment-key-names.json"
```

**3. 具体值到受控目录里读，身份不要互相代替。** 具体值需要在受控目录读取完整材料。容器 ID、镜像 ID、标签和仓库摘要是不同对象；短 ID 或标签不能代替完整身份。容器顶层 `Image` 与 `Config.Image` 分别核对镜像内容身份和创建时引用。两个字段不同时，两个都留。

**4. 需要镜像 ID 前几位时，先保存完整 ID。** 从数据库容器的顶层 `Image` 取出完整镜像 ID，再与对应镜像 inspect 的 `Id` 对照。容器顶层 `Id` 是容器 ID，`Config.Image` 可能只是 `mysql:8.0` 这样的创建引用，`RepoDigests` 则是仓库 manifest 摘要，三者都不能代替所问的镜像 ID。

**5. 下面只读已经保存、且只有一个数据库容器的 inspect。** 下面只读取已经保存、且只包含一个数据库容器的 inspect JSON。去掉算法前缀后取前 6 位，完整值仍保留；材料结构或 ID 格式不符就停止，不截取别的字段。脚本退出就留下原始 `Image`，不要换字段硬取 6 位。

```bash
python3 - /work/input/mysql-inspect.json <<'PY'
from pathlib import Path
import json
import re
import sys

records = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
    raise SystemExit('Expected one saved container record')
image_id = records[0].get('Image', '')
if not isinstance(image_id, str):
    raise SystemExit('Image field is not a string')
digest = image_id[7:] if image_id.startswith('sha256:') else image_id
if not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
    raise SystemExit('Unexpected image ID; keep original field and inspect its format')
print('image_id=' + image_id)
print('image_id_first6=' + digest[:6])
PY
```

前 6 位只是题目或展示要求，可能发生碰撞；证据关联、导出和复核始终使用完整 ID，不能据此选择同名前缀的另一个容器或镜像。

**6. 按线索核对它能说明到哪一层。** 右列的边界没有满足时，不要把变量值写成当前口令或把 Running 写成业务正常。

| 线索 | 核对位置 | 结论边界 |
| --- | --- | --- |
| `MYSQL_ROOT_PASSWORD`、`MYSQL_USER`、`MYSQL_PASSWORD` | 创建配置、该镜像入口脚本、初始化日志 | 不一定等于采集时的有效账号/口令 |
| `MYSQL_DATABASE` | 初始化意图、实际 schema、网站连接库名 | 不证明该库始终存在或包含全部业务数据 |
| `*_FILE` / Secret 引用 | 对应挂载、文件与入口读取规则 | 环境中无明文值不等于无凭据 |
| `Mounts` 的 Source/Destination | 数据目录的绑定挂载或卷 | 镜像层旧文件不等于当前数据库内容 |
| `State`、数据库日志 | 初始化、恢复与接受连接状态 | Running 不保证数据库或业务正常 |

**7. 初始化变量不等于当前口令。** 官方 MySQL 镜像的初始化变量主要参与首次初始化；已有数据库目录时不会依这些变量重新设置原有数据库账号。后续改密、不同入口脚本或复用数据卷都可能造成差异，不能读到一个值便认定为当前口令。规则见 [MySQL 官方镜像说明](https://hub.docker.com/_/mysql)，其他镜像按实际入口逻辑核对。

**8. 数据库入口这样对应。**

1. 构造挂载把 `/srv/lab/mysql-data` 指向容器 `/var/lib/mysql`，先到宿主机这个目录找持久数据。
2. 网站配置 `db:3306/lab_site` 中，先用容器网络别名确认 `db`，再核对数据库版本、schema 和表结构。
3. 宿主机客户端改用发布项的实际 HostIp/HostPort；容器内地址不能直接套给分析机。

挂载路径或别名和这三步不同时，以这份材料的 Mounts 和网络别名为准。

**9. 要恢复实例时换隔离副本，并留启动前的一份。** 【仅在副本/仿真/授权环境执行】持久目录和日志链保存后，再恢复另一个数据库副本。`docker start` 会产生新运行状态，数据库还可能写恢复日志和数据页。先留启动前副本，交付时把配置值、实际目录、实验认证和历史业务记录分别列出。

本节已核对容器 `Id`、顶层 `Image`、`Config.Image`、`RepoDigests`，以及数据目录的 Source 和 Destination；只有 `MYSQL_ROOT_PASSWORD` 或 `MYSQL_DATABASE`、没有初始化日志和实际目录时，不写成当前口令或库一定还在。脚本留下的完整镜像 ID 与镜像 inspect 的 `Id` 一致，前 6 位只作展示，一并留存 `container-identity.json`、变量键名、完整镜像 ID；启动过的数据库另留启动前副本。
