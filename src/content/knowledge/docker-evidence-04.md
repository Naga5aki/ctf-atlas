---
title: "Docker 取证 04｜日志、文件与持久化"
summary: "从日志驱动和 LogPath 找到真实日志，再核对应用文件、卷与宿主机持久化数据。"
module: "Forensics"
track: "服务器取证"
topic: "Docker 与容器"
tags: ["日志"]
status: "已整理"
sourceIds: ["2530fdc7be10", "c7613f4a6214"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

手里是容器主机的离线快照或已确认的现场会话，日志可能落在容器目录、卷、宿主机或远程日志系统。本页回答：日志与文件的真实路径、存储目录结构、元数据与事件、文件提取、卷的持久化，以及怎么把一次可疑请求对到日志、文件和卷。原始材料保持只读，写回、清理、新建卷只在副本上做。

**先问运行时要路径 → 按访问、异常与攻击痕迹筛日志 → 从数据根分开元数据、层与卷 → 按问题选 logs/inspect/events → 只做容器到主机的提取 → 把可疑请求对到日志、文件和卷。**

<span id="01-查找容器真实日志路径"></span>

## 01 先问运行时要日志路径

先用 `docker inspect --format '{{.HostConfig.LogConfig.Type}} {{.LogPath}}' <容器ID>` 核对当前容器的日志驱动与路径。`json-file` 的常见位置不能代替实际配置；LogPath 为空时继续查 journald、其他驱动或编排平台。容器标准输出、应用自有日志和宿主机日志分开保全，再按时间及容器 ID 关联。

日志命令已经会跑，但还不知道这个容器的文件到底在哪。下面先问它自己的日志驱动和路径。

操作顺序：先问 LogConfig 和 LogPath，再按驱动找文件，对上之后才按时间读。


### 01.1 先问运行时

手里是一个容器 ID，还不能按默认目录去翻日志。驱动和数据根会把文件放到别的地方。

操作顺序：先问这个容器的驱动和路径，再决定读文件、journal 还是外部系统，对上容器 ID 之后再筛请求。

**1. 用当前容器的配置取路径，不要猜默认目录。** Docker 的 `json-file` 日志常见于容器目录，但实际位置受运行时、数据根目录和日志驱动影响。用当前容器的配置取证。命令失败就留下报错，不要改到 `/var/lib/docker/containers/` 去碰运气。

```bash
docker inspect --format '{{.HostConfig.LogConfig.Type}} {{.LogPath}}' CONTAINER_ID
```

**2. 拿到路径后按这四步保存。**

1. 记下路径和轮转配置。现场先用 Docker CLI 保存可读日志。
2. 要逐文件读 json-file 或 local，就读只读快照或已保存副本；不修改、轮转 daemon 正在管理的文件。
3. `LogPath` 为空时看日志驱动，转查 journald、运行时或节点日志；若材料来自 Kubernetes，使用[集群取证流程](/knowledge/forensic-kubernetes-cluster/)定位 Pod 与节点。
4. 找到请求后，把日志时间、完整容器 ID 和服务配置一起记录，再看同一时段的应用记录。

路径为空又不是 journald 时，停在第 3 步，不要把别的容器的 `*-json.log` 拿来当这一份。

本节已核对这个容器的日志驱动，以及 `LogPath` 或它为空的原因；`LogPath` 为空时，还要写明改查的是 journald、节点日志还是编排平台。inspect 里的驱动、路径和完整容器 ID 是同一条，一并留存这条 inspect 输出、轮转配置，以及只读副本上的日志文件。

<span id="02-docker-日志分析"></span>

## 02 按访问、异常与攻击痕迹筛日志

路径还没定时，不要先按访问、报错或攻击词去搜。下面先用 CLI 看驱动里的标准输出，再按访问、异常和攻击痕迹分开筛。

操作顺序：先读带时间的日志，再按访问、异常、攻击词筛选，对上同一容器和同一时段。


### 02.1 使用 Docker CLI 查看容器日志

驱动里的标准输出还没读出来。先按容器 ID 取日志，时间范围和跟踪要分开。

操作顺序：先读全部或一段时间，再看末尾，持续跟踪只用于活体排障。

**1. 先按容器 ID 读驱动保存的标准输出和标准错误。** 容器 ID 对不上或驱动是 `none` 时，命令会空或报错，改回上一节的 `LogPath`，不要换成另一个容器。

```bash
docker logs 容器ID
```

**2. 要卡时间时，带上时间戳和起止。** 起止要写成带时区的时间。窗口里没有行，只说明这段没有留下标准输出，应用自己的日志还要另找。

```bash
docker logs --timestamps --since '2026-09-25T00:00:00+08:00' --until '2026-09-26T00:00:00+08:00' 容器ID
```

**3. 末尾和持续跟踪分开用。** 查看末尾并持续跟踪，适合活体排障，但持续跟踪不适合静态证据采集。`--follow` 会一直等新行，静态材料用 `--tail` 留下已经有的末尾即可。

```bash
docker logs --timestamps --tail 200 容器ID
docker logs --timestamps --follow 容器ID
```

本节已核对这个容器在所选时间窗里的标准输出，以及每行的时间戳；窗口为空时，应用日志和宿主机日志还没读。命令里的容器 ID、`--since` 和 `--until` 与输出时间戳是同一次查询，一并留存带时间戳的日志输出；活体跟踪另记开始和结束时间。

### 02.2 默认日志目录与实际日志路径

默认目录只是常见位置。这个容器的 `LogPath` 还没查询之前，不要把文件当成已经找到。

操作顺序：先看默认长什么样，再查这个容器的 LogPath，对上驱动表里的实际位置。

**1. 先认识常见目录，但不靠它定案。** Docker 元数据常见目录：

```text
/var/lib/docker/containers/
```

默认 `json-file` 驱动常见文件：

```text
/var/lib/docker/containers/<容器完整ID>/<容器完整ID>-json.log
```

目录不在或 ID 对不上时，继续第 2 步，不要新建这个路径。

**2. 直接查这一个容器。** 不要仅凭默认路径猜测。`LogPath` 和 `LogConfig` 一起看，轮转参数也在配置里。

```bash
docker inspect --format 'LogPath={{.LogPath}} LogConfig={{json .HostConfig.LogConfig}}' 容器ID
```

**3. 再看守护进程的默认驱动。** 它是全局默认，容器自己的 `LogConfig` 可以不同。两者不一致时以容器这条为准。

```bash
docker info --format '{{.LoggingDriver}}'
```

**4. 按驱动到对应位置找，对不上就改查下一行。**

| 日志驱动 | 常见证据位置 | 注意事项 |
|---|---|---|
| `json-file` | 容器目录中的 `*-json.log` | 可能配置 `max-size`、`max-file` 而轮转 |
| `local` | 数据根下 `containers/<完整ID>/local-logs/` 内部日志文件 | 不应自行用文本编辑器修改；文件名由 Docker 管理，先列目录再读 |
| `journald` | systemd journal | 用容器 ID、名称、单位字段筛选 |
| `syslog` | 本机或远程 syslog | 需查 `/etc/rsyslog*` 和远端日志平台 |
| `fluentd`、`gelf`、`splunk` 等 | 外部日志系统 | 本机可能只残留配置和发送失败日志 |
| `none` | 无标准输出日志 | 继续查应用挂载目录、审计和网络证据 |

本节已核对这个容器的 `LogPath`、`LogConfig`，以及和全局 `LoggingDriver` 是否相同；驱动是 `fluentd`、`gelf`、`splunk` 或 `none` 时，本机文件可能只有配置或根本没有标准输出。按该容器实际日志驱动核对：本地文件与 inspect 指定路径一致，journal 或外部日志按容器标识和时间关联；不要求所有驱动都把完整 ID 写进文件名，一并留存两条 inspect/info 输出，以及按表找到或确认缺失的日志位置。

### 02.3 Web 访问分析

标准输出里混着访问行，还没判断这些请求真正做了什么。先把字段留下，再搜可疑 URI。

操作顺序：先留访问字段，再用正则找可疑 URI，HTTP 200 还要看响应和文件。

**1. 先筛选，再判断请求结果。**

1. 从原访问行保留时间、源 IP、方法、URI、状态码、User-Agent、Referer、响应字节数和上游地址。
2. 用下面正则找 `cmd=`、`.env` 和注入词，保存整行及前后错误日志。
3. 看返回内容、实际文件和应用行为，确认请求做了什么。HTTP 200 只给状态码，仍要找执行或响应记录。
4. 经代理的源 IP，沿当时的转发链查，不直接归给操作者。

某一项在行里没有，就记成该行缺少这个字段，不要用别的日志补一个来源 IP。

**2. 先把像访问记录的行滤出来。** 没有命中只说明标准输出里没有这些方法或状态行，访问日志可能在挂载目录。

```bash
docker logs --timestamps 容器ID 2>&1 | grep -Ei 'GET |POST |PUT |DELETE |HEAD |HTTP/[0-9.]+'
```

**3. 再在同一份输出里找常见攻击 URI。** 命中后保存整行。正则没有覆盖到的路径，回到原始访问行继续看，不要只留命中行。

```bash
docker logs --timestamps 容器ID 2>&1 | grep -Ei '(\.\./|%2e%2e|/etc/passwd|\.env|wp-login|xmlrpc|actuator|jndi|cmd=|shell|union[[:space:]]+select)'
```

本节已核对带时间的访问行，以及其中的方法、URI 和状态码；只有 HTTP 200、没有响应内容或文件时，不写成请求已经执行成功。可疑 URI 的整行仍能在原始日志里找到同一时间和同一容器，一并留存筛选出来的整行、前后错误日志，以及代理场景下的转发链。

### 02.4 服务异常分析

服务在重启或退出，访问日志解释不了是应用报错、内存不足还是守护进程把它停了。三条记录要分开对。

操作顺序：先在容器日志里找报错词，再读退出和重启字段，对上同一时段的 daemon 日志。

**1. 在带时间戳的容器日志里找异常词。** 没有命中只说明这些词不在标准输出里，还要看第 2 步的状态字段。

```bash
docker logs --timestamps 容器ID 2>&1 | grep -Ei 'error|fatal|panic|exception|denied|timeout|refused|oom|killed|segfault'
```

**2. 把容器状态和 Docker 单元日志放在同一时段。** `ExitCode`、`OOMKilled`、`Error`、`RestartCount` 是这个容器的状态。`journalctl` 是宿主机上 docker 单元的日志，时间要和容器日志用同一时区来对。单元日志为空就改查轮转和上一节的日志驱动，不要写成没有异常。

```bash
docker inspect --format 'ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} Error={{.State.Error}} RestartCount={{.RestartCount}}' 容器ID
journalctl -u docker --since '2026-09-25 00:00:00' --no-pager
```

本节已核对容器日志里的报错行，以及 `ExitCode`、`OOMKilled` 和 `RestartCount`；journal 没有覆盖该时段时，退出原因仍可能只在容器日志或轮转文件里。报错行的时间戳和 inspect 的退出时间落在同一个已记录窗口，一并留存筛选后的日志、这条 format 输出，以及 `journalctl -u docker` 的原输出。

### 02.5 攻击痕迹分析

日志里可能有下载、反弹或挖矿的词，但这些词也会出现在正常运维里。先留下命中和前后文，再对进程和文件。

操作顺序：先按关键词留下候选行，再对同一时段的进程和文件，词出现在哪一段日志里要写明。

**1. 用关键词找候选，不把命中直接当成入侵。** 下面关键词用于找反弹 Shell、下载执行、挖矿和提权的候选日志。命中后保存文件名、时间和前后文，再查同一时段的进程参数、文件哈希及执行/访问记录。`curl`、`base64`、`docker.sock` 也可能是正常运维或请求文字，要看它出现在哪一段日志里。没有前后文时，只记命中了这个词。

```bash
docker logs --timestamps 容器ID 2>&1 | grep -Ei 'curl|wget|bash -c|/dev/tcp|nc |ncat|socat|chmod \+x|base64 -d|xmrig|stratum|sudo|nsenter|docker\.sock'
```

**2. 同时检查这些相邻记录。** 某一类日志不在材料里，就在结论里写缺失，不要用标准输出代替。

- Web 容器访问日志与应用错误日志；
- 容器内新增账号、计划任务、SSH Key、WebShell；
- 宿主机 `auditd`、SSH、sudo、systemd 和防火墙日志；
- 代理、DNS、镜像仓库和负载均衡器日志；
- 日志轮转、截断、时间跳变和缺口。

本节已核对候选行的时间、所在日志段落，以及同一时段的进程或文件；只有 `curl`、`base64` 或 `docker.sock` 这些词、没有前后文和执行记录时，不写成已经执行。命中行能回到原日志，并能对上同一时段的进程参数或文件哈希，一并留存命中行和前后文，以及上面五类记录里已经找到或确认缺失的部分。

---

<span id="03-docker-存储目录取证"></span>

## 03 从数据根分开元数据、层与卷

日志路径对上之后，网站文件和数据库可能不在日志旁边。下面从数据根往下，把容器目录、层、卷和 containerd 分开。

操作顺序：先确认 DockerRootDir，再分 containers、overlay2、volumes，对上容器 ID 和层目录。


### 03.1 `/var/lib/docker/` 目录总览

还不知道数据根是不是默认的 `/var/lib/docker/`。先问运行时，再看目录里各放什么。

操作顺序：先问数据根和启动参数，再看目录占用，对上表里的子目录之后才进层和卷。

**1. 先确认真实数据根。** 三条都记下。`daemon.json` 没有 `data-root` 时，空输出只说明这份配置没写这个键，仍以 `DockerRootDir` 为准。

```bash
docker info --format '{{.DockerRootDir}}'
systemctl show docker -p ExecStart
jq -r '."data-root" // empty' /etc/docker/daemon.json 2>/dev/null
```

**2. 默认目录长这样，实际位置以上一步为准。**

```text
/var/lib/docker/
```

**3. 只看这一层目录，不跨文件系统递归。** `du` 报错或跳过挂载点时保留错误，不要改成无 `-x` 的全盘统计。

```bash
ls -lah /var/lib/docker
du -xhd1 /var/lib/docker 2>/dev/null | sort -h
```

**4. 按子目录决定下一步去哪。** 目录不在这张表里时，先记下名字，不要删掉或改名。

<details>
<summary>展开数据根子目录总览表</summary>

| 目录 | 用途 | 取证价值 |
|---|---|---|
| `containers/` | 容器配置、主机配置、日志等元数据 | 容器创建参数、日志路径、名称、网络和状态线索 |
| `image/` | 镜像元数据、层数据库 | 镜像、层、父子关系和仓库摘要 |
| `overlay2/` | OverlayFS 镜像层与容器可写层 | 恢复容器内新增、修改或删除的文件 |
| `volumes/` | Docker 命名卷 | 数据库、上传文件、网站内容、应用状态 |
| `network/` | Docker 网络状态和本地数据库 | 网络、端点、IP、容器连接关系 |
| `plugins/` | Docker 插件数据 | 第三方存储/网络插件线索 |
| `swarm/` | Swarm 状态、证书和 Raft 数据 | Swarm 节点角色、服务和集群证据 |
| `buildkit/` | BuildKit 缓存与元数据 | 构建过程、上下文和镜像来源线索 |

</details>

**5. 原始证据上不要清理。** 不要在原始证据上删除 `overlay2` 子目录、手工改名层目录或运行清理命令。`docker system prune`、`docker image prune`、`docker volume prune` 会直接毁掉潜在证据。

本节已核对 `DockerRootDir`、启动参数，以及数据根下实际存在的子目录；`data-root` 为空或某个子目录不在时，分别写明，不改用默认路径顶上。`docker info` 的数据根和 `ls` 看到的目录是同一条路径，一并留存三条查询的输出、`du` 结果，以及没有执行清理命令的记录。

### 03.2 `containers/`：容器元数据与日志

数据根已经确认，还没把某个容器的配置、主机名和 json 日志对上它的完整 ID。

操作顺序：先按完整 ID 找到目录，再在副本里读 JSON，缺字段就查配套文件。

**1. 先按这个结构找目录。** 目录名必须是完整容器 ID。对不上 ID 就回到 inspect，不要按修改时间挑一个目录。

```text
/var/lib/docker/containers/<完整容器ID>/
├── config.v2.json
├── hostconfig.json
├── hostname
├── hosts
├── resolv.conf
└── <完整容器ID>-json.log
```

**2. 先保存原 JSON，再在副本里读。** 先保存容器目录中的原 JSON，再在副本读名称、镜像、Env、命令、Mounts 和网络。记录字段所在文件；不同版本字段位置可能不同，缺字段时继续查配套文件和日志，不改原 JSON 补值。某个文件不在树里就记缺失。

本节已核对完整容器 ID 对应的目录，以及名称、镜像、Env、命令、Mounts 和网络所在的文件；某一字段不在 `config.v2.json` 时，写明还查了哪一个配套文件。目录名、日志文件名和容器 ID 是同一个完整 ID，一并留存原 JSON 的副本，以及字段所在文件的记录。

### 03.3 `overlay2/`：恢复容器文件

容器里的文件改过，但还没对上它落在哪一层。`merged` 不一定还挂着，要先从 inspect 找层目录。

操作顺序：先分清层目录的名字，再用 GraphDriver 对上容器，只在副本里找新增和修改的文件。

**1. 先认识这些目录各自是什么。** 名字对不上这张表时，回到第 2 步的路径，不要按目录时间猜哪一层是容器。

| 名称 | 作用 |
|---|---|
| `lower` | 只读镜像层链 |
| `upper` / `diff` | 容器或层的新增、修改内容 |
| `merged` | 运行时合并视图；容器停止后可能未挂载 |
| `work` | OverlayFS 工作目录 |
| `l/` | 缩短层路径的符号链接目录 |

**2. 在线时用 inspect 把容器映射到层目录。** 输出里没有这些键，就记驱动不是 overlay2，不要仍去默认目录找。

```bash
docker inspect --format '{{json .GraphDriver.Data}}' 容器ID | jq .
```

**3. 先读四个路径，再决定看增量还是完整视图。** 先从 inspect 找 `LowerDir`、`UpperDir`、`MergedDir`、`WorkDir`。查容器运行后新增或修改的文件，重点读 `UpperDir`；要还原完整目录，还需把 lower 层和删除标记一起看。`MergedDir` 为空时，不要把 `merged` 当成还有一份完整副本。

**4. 在副本上按时间找新增或修改过的文件。** 路径换成第 3 步对上的层。`find` 跨出文件系统或权限不够时，保留错误，不要去掉 `-xdev`。

```bash
find /取证副本/overlay2/目标层/diff -xdev -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' | sort
```

**5. 再按脚本和凭据文件名缩小范围。** 命中的是候选路径，还要做哈希，不能只凭扩展名当结论。

```bash
find /取证副本/overlay2/目标层/diff -xdev -type f \( -name '*.php' -o -name '*.jsp' -o -name '*.py' -o -name '*.sh' -o -name '.env' \) -print
```

**6. 恢复时按这四条核对。**

1. `merged` 是运行时挂载视图，不等于独立完整副本；离线时可能为空或不可用。
2. OverlayFS 删除可能用 whiteout 表示，不能简单把 `diff` 当成完整根文件系统。
3. 先用容器 inspect 映射 ID 与层目录；不要只按目录时间猜测。
4. 文件恢复后计算哈希，并记录来源层、原路径、时间和采集方式。

本节已核对容器 ID 对应的 `UpperDir` 或 `diff`，以及其中的候选文件；`merged` 不可用或只有 whiteout 时，完整目录视图还要连同 lower 一起看。`GraphDriver.Data` 里的路径和副本上的层目录是同一条，一并留存inspect 的层路径、find 输出、文件哈希、来源层和采集方式。

### 03.4 `volumes/`：寻找持久化业务数据

容器可写层里没有数据库或上传文件。它们可能在命名卷里，要先问卷的实际目录。

操作顺序：先列出卷并 inspect，再到 `_data`，按应用的常见路径核对。

**1. 先列出卷，再看某一个卷的挂载点。** 卷名来自容器的 Mounts，不要按目录名猜测。

```bash
docker volume ls
docker volume inspect 卷名
```

**2. 命名卷的数据通常在这个目录。** 实际 `Mountpoint` 与下面不同时，以 inspect 为准。

```text
/var/lib/docker/volumes/<卷名>/_data/
```

**3. 按应用对照常见容器路径。** 容器里的路径还要和 Mounts 的 Destination 对上，表只是常见位置。

| 目标 | 常见容器路径 | 典型文件或目录 |
|---|---|---|
| MySQL/MariaDB | `/var/lib/mysql` | `ibdata1`、`ib_logfile*`、`#innodb_redo/`、数据库目录、binlog |
| PostgreSQL | `/var/lib/postgresql/data` | `PG_VERSION`、`base/`、`global/`、`pg_wal/` |
| Redis | `/data` | `dump.rdb`、`appendonly.aof`、`appendonlydir/` |
| 网站文件 | `/var/www/html`、`/usr/share/nginx/html` | PHP/JSP、上传目录、静态资源、WebShell |
| 应用配置 | `/etc/<应用>`、`/app/config` | `.env`、YAML、JSON、证书、密钥 |
| 应用日志 | `/var/log/<应用>` | 访问日志、错误日志、审计日志 |

**4. 在卷目录里找这些文件名。** 没有命中只说明这些名字不在已搜索的卷里，绑定挂载还要另查 Source。

```bash
find /var/lib/docker/volumes -xdev -type f \( -name 'ibdata1' -o -name 'dump.rdb' -o -name 'appendonly.aof' -o -name 'PG_VERSION' -o -name '.env' -o -name '*.sql' \) -print 2>/dev/null
```

**5. 数据库要启动时，只启动复制出来的卷。** 【仅在副本/仿真/授权环境执行】数据库恢复先复制卷，尽量使用相同大版本软件。启动前再留一套未启动副本，因为启动会回放日志、可能升级并写数据；原卷保持只读。

本节已核对卷名、`Mountpoint` 或 `_data`，以及里面的数据库、网站或配置文件；find 没有命中时，还要查绑定挂载的 Source，不写成没有业务数据。inspect 的卷名和 `_data` 路径，与容器 Mounts 的 Destination 是同一份数据，一并留存 `docker volume inspect` 输出、找到的文件路径；若启动过数据库，另留启动前副本。

### 03.5 新版 containerd image store 提醒

镜像层不在 `overlay2/` 里时，Docker 可能把镜像交给了 containerd。先确认用的是哪一个实例，再读它的快照目录。

操作顺序：先看 docker info 和 containerd 根，再读 config dump，对上进程实际使用的 root。

**1. 先看 Docker 是否在用 containerd 存镜像，并列出常见目录。** 目录存在不等于这个进程在用它。

```bash
docker info
ls -lah /var/lib/containerd
containerd config dump 2>/dev/null
```

**2. 先找所用实例，再找快照。** 从 dockerd/containerd 启动参数确认 Docker 接的是哪个 containerd，读该实例的 `root` 和 snapshotter 配置。`data-root` 可能没有包含它的快照目录。对不上 `root` 时，不要把 Docker 的 `overlay2/` 当成镜像层已经找齐。

**3. 找到目录后还要看是哪一个实例。** 独立 containerd、Docker 管理实例和嵌入布局可能不同；找到 `/var/lib/containerd` 后还要看进程是否使用它。进程参数指向别的根时，以进程为准。

**4. 看 dump 时把命令本身的范围记下来。** `containerd config dump` 解析本次指定的磁盘配置和 imports，再补上这个二进制的默认值。先保存 `--config` 路径、版本、启动参数和配置哈希。

**5. 再和插件、进程、日志比较。** 把结果与插件、进程和日志比较：配置可能在进程启动后被改过，分析机的默认值也可能不同。离线 dump 只能说明这份文件怎样被当前工具解析，不能代替历史加载记录。dump 和进程不一致时，两份都留，不合并成一份“当前配置”。

本节已核对Docker 使用的 containerd 实例、它的 `root`，以及 snapshotter；只有 `/var/lib/containerd` 目录、没有进程参数时，还不能确定快照就在这里。`--config`、启动参数和 `containerd config dump` 指的是同一次配置，一并留存 `docker info`、目录列表、dump、配置哈希，以及和进程不一致的地方。

---

<span id="04-docker-日志与元数据取证"></span>

## 04 按问题选 logs、inspect 或 events

同一份容器的日志、inspect 和运行状态还散在不同命令里。下面按要查的问题选命令，不把它们合成一次采集。

操作顺序：先按问题选 logs、inspect 或 events，再保存原输出，对上容器 ID 和时间窗口。


### 04.1 docker logs

标准输出要看，但 Nginx 或数据库的日志不一定在这里。先认清每条命令读到哪、会不会一直跟踪。

操作顺序：先选只读的一条命令，再另找应用自己的日志路径，对上时间之后再解释访问。

**1. 按这张表选命令。** `-f` 会持续跟踪，静态材料不要用它代替一次保存。

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker logs &lt;container&gt; | 读取容器标准输出和标准错误日志 | 查看启动、访问和错误线索 |
| docker logs -f &lt;container&gt; | 持续跟踪新日志 | 现场排障；Ctrl+C 退出跟踪 |
| docker logs --tail 100 &lt;container&gt; | 只显示最后 100 行 | 快速查看近期异常 |
| docker logs -t &lt;container&gt; | 为日志显示时间戳 | 建立事件时间线 |
| docker logs --tail 100 -f &lt;container&gt; | 先显示最近 100 行再持续跟踪 | 复现 CTF 环境问题 |

**2. 驱动日志和应用日志分开读。** 先用 docker logs 读取日志驱动保存的 stdout、stderr。还想看 Nginx、应用或数据库日志，就读各自配置中的日志位置：可能在 /var/log、挂载目录，也可能发送到外部日志系统。`docker logs` 为空时，改查那些路径，不要写成没有访问。

**3. Web 访问要把几份日志放在一起。** Web 攻击分析应同时检查访问日志、错误日志、应用日志、反向代理日志和主机时间偏差。缺一份就写明缺的是哪一份。

本节已核对驱动里的 stdout/stderr，以及应用配置里写下的日志路径；只有 `docker logs`、没有访问日志或反向代理日志时，请求链还不完整。时间戳和主机时间偏差已经记下，日志行能回到同一个容器，一并留存所选 logs 命令的输出，以及 /var/log 或挂载目录中的应用日志路径。

### 04.2 docker inspect

容器从哪来、数据在主机哪里、端口有没有发布，都还在原始 JSON 里。先留完整 JSON，再摘字段。

操作顺序：先保存完整 inspect，再按表看字段，IP 模板只作补充。

**1. 先留下原始 JSON。** 容器名对不上就换完整 ID。这份输出是后面摘字段的底稿。

```bash
docker inspect <container>
```

**2. 按表看这些字段能回答什么。** 字段缺失就记缺失，不要用镜像默认值填上。

**关键字段**

| 字段 | 重点内容 | 取证问题 |
| --- | --- | --- |
| Image | 镜像 ID 或摘要 | 容器来源是否与预期一致 |
| Config.Cmd | 默认参数 | 应用实际启动了什么 |
| Config.Entrypoint | 入口程序 | 是否被替换或注入脚本 |
| Config.Env | 环境变量 | 是否暴露密码、Token、Flag 或配置 |
| Mounts | Volume 与 Bind Mount | 数据实际位于主机哪里 |
| NetworkSettings.Networks | 网络、别名、IP | 容器能与哪些服务通信 |
| NetworkSettings.Ports | 端口发布与绑定 | 服务是否意外暴露 |
| State | 状态、PID、启动和退出时间 | 构建运行时间线 |

**3. 只想快速看 IP 时再用模板，多网要小心。** 格式化模板可快速提取 IP，但多网络容器可能输出多个地址且缺少分隔。完整取证仍应保留原始 inspect JSON。地址粘在一起时，回到 JSON 里按网络名拆开。

```bash
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>
```

本节已核对镜像、入口、环境变量、挂载、网络和状态来自同一份 inspect；模板把多个 IP 粘在一起时，以原始 JSON 里的网络名为准。表里要回答的问题能指回 JSON 中的同一个字段，一并留存完整 inspect JSON；环境变量按敏感材料保存。

### 04.3 stats top diff events

资源、进程、文件变化和启停时间是四件不同的事。先选对命令，再看它能覆盖多长的历史。

操作顺序：按要查的内容选命令，再记下查询窗口，旧事件不在 events 里就改查业务日志。

**1. 按要查的内容选命令。** 资源异常看 stats，进程看 top，新增/修改/删除路径看 diff，创建/启停/删除时间看 `docker events`。下面原表列出各自用法。容器已经停止时，stats 和 top 会失败，保存错误并改用 inspect 的状态，不为了看进程去启动它。

<details>
<summary>展开 stats/top/diff/events 对照表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker stats | 持续显示全部运行容器的资源使用 | 发现异常 CPU、内存、网络或 I/O |
| docker stats &lt;container&gt; | 只监控指定容器 | 聚焦可疑服务 |
| docker stats --no-stream | 输出一次资源快照 | 保存可重复引用的现场记录 |
| docker top &lt;container&gt; | 从宿主机视角列出容器进程 | 与容器内 ps 交叉验证 |
| docker diff &lt;container&gt; | 列出容器可写层中新增、修改、删除的路径 | 定位运行后文件变化和 WebShell 线索 |
| docker events --since &lt;time&gt; | 显示 Docker 守护进程事件 | 分析容器创建、启动、停止和删除时间线 |

</details>

**2. 查 events 时写明窗口。** 查 events 时写明查询窗口和采集时间。`docker events` 只保留有限的近期事件缓冲，历史范围受 daemon 缓冲大小与运行时长限制，不能当成完整审计日志；没给截止时间时它会持续等待新事件。找不到旧事件时，改查节点日志和业务日志，不据此认定事件没有发生。

本节已核对所选命令对应的资源快照、进程、可写层差异或事件时间；events 没有旧记录时，还要查节点和业务日志，不写成事件没发生。查询窗口、采集时间和容器 ID 写在同一次输出上，一并留存 `--no-stream` 的 stats、top、diff 或带 since 的 events 原输出。

<span id="05-docker-文件提取"></span>

## 05 只做容器到主机的提取

文件在容器里，要拿到分析机上，但不能把复制回去和复制出来混成一步。

操作顺序：先确认方向是容器到主机，再记下哈希和属主，写回只在另一份副本上做。

**1. 按表确认这条命令是在取出还是写入。** 取证只用从容器复制到主机的那几条。

<details>
<summary>展开 docker cp 方向对照表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker cp &lt;container&gt;:/path/file . | 从容器复制文件或目录到当前目录 | 提取日志、源码、配置或可疑样本 |
| docker cp localfile &lt;container&gt;:/path/ | 从主机复制文件到容器 | 调试或修复；会改变现场 |
| docker cp web:/var/log/nginx/access.log . | 提取 Nginx 访问日志 | 离线分析请求和攻击源 |
| docker cp web:/var/www/html/index.php . | 提取 Web 源码 | 检查后门、注入和版本差异 |

</details>

**2. 从容器提取时按这四步做。**

1. 先建立目标父目录，`docker cp` 不会替你创建缺失父目录；运行或停止容器都能提取。
2. 记下完整容器 ID、原路径、提取时间和哈希。
3. 默认落到主机的 UID/GID 属于本机执行用户。要保留源 UID/GID，用 `-a` 后核对结果；`-L` 会跟随软链，另记目标。
4. 权限、扩展属性和稀疏特性逐项与原记录比较，不从复制后的属主反推原属主。

父目录还没建好就失败时，先补目录再提取，不要改到容器里创建路径。

**3. 往容器里复制会改可写层。** 【仅在副本/仿真/授权环境执行】主机文件复制进容器会修改可写层。取证只按前面的“容器 → 主机”提取；需要写回或修复时换到另一份副本，记录改了哪个路径。

本节已核对完整容器 ID、容器内原路径，以及提取文件的哈希；没用 `-a` 时，主机上的 UID/GID 不能当成容器里的属主。提取时间和哈希对应同一次“容器 → 主机”复制，一并留存提取出的文件、哈希、原路径；若用了 `-L`，另记软链目标。

<span id="06-docker-volume-与数据持久化"></span>

## 06 先查卷，别先建卷

容器删了之后，数据库和上传文件还可能在。先查卷，不要先创建新卷。

操作顺序：先用 inspect 看现有卷，再区分命名卷和绑定挂载，创建和挂载只在副本里做。

**1. 先分清哪些命令只查询、哪些会新建。** 【仅在副本/仿真/授权环境执行】下表的 volume create 新建卷，挂载示例的 run 新建并启动容器；当前数据位置先用 inspect 查询。

**2. 卷的寿命和容器不是同一条。** 容器可写层随容器删除而丢失，但 Volume 和 Bind Mount 独立于容器生命周期。命名 Volume 默认不会因为 docker rm 或普通 docker compose down 自动删除，因此数据库和上传文件可能继续存在。容器目录没了就改查卷清单，不要当成数据已经没了。

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker volume ls | 列出 Volume | 发现容器删除后的持久化数据 |
| docker volume create &lt;name&gt; | 创建命名 Volume | 搭建持久化环境 |
| docker volume inspect &lt;name&gt; | 显示驱动、挂载点、标签和作用域 | 定位数据存储与 Compose 归属 |

已经存在的卷名和挂载点，以及容器删除后这些卷是否还在；容器目录没了、还没跑 `docker volume ls` 时，不能写成数据已经消失。卷清单来自查询，不是 `docker volume create` 新建出来的，一并留存 `docker volume ls` 和 `docker volume inspect` 的输出；副本里新建过的卷另记。

### 06.1 Named Volume 与 Bind Mount

知道有持久化数据，还分不清它在 Docker 管理的卷里，还是在用户指定的主机目录。

操作顺序：先看类型，再在副本里看挂载示例，用 inspect 的 Mounts 核对真实路径。

**1. 按类型看主机位置。** 容器内路径相同，主机位置仍可能完全不同。

| 类型 | 示例 | 主机位置 | 取证特点 |
| --- | --- | --- | --- |
| Named Volume | -v mysql-data:/var/lib/mysql | 由 Docker 管理 | 生命周期独立，inspect 可定位 |
| Bind Mount | -v /host/path:/container/path | 用户指定路径 | 直接映射主机目录，主机与容器修改相互可见 |
| Windows Bind Mount | -v D:\web:/usr/share/nginx/html | D:\web | 注意路径共享、权限和 PowerShell 引号 |

**2. 挂载示例只说明写法，会新建容器。** 【仅在副本/仿真/授权环境执行】下面的 `docker run` 会创建并启动新容器。目标上的现有数据不要靠再跑一遍来确认。

**挂载示例**

```bash
docker run -d -v mysql-data:/var/lib/mysql mysql
docker run -d -v /host/path:/container/path nginx
```  
```powershell
docker run -d -v D:\web:/usr/share/nginx/html nginx
```

**3. 真实位置以 Mounts 为准。** 使用 docker inspect &lt;container&gt; 查看 Mounts，重点核对 Type、Source、Destination、RW 和 Name。不要仅凭容器内路径判断真实数据位置。Source 和表里的示例不同时，以 Source 为准。

本节已核对Mounts 里的 Type、Source、Destination、RW 和 Name；只有容器内路径、没有 Source 时，主机上的数据位置仍未知。inspect 的 Type 和表里的 Named Volume 或 Bind Mount 是同一类，一并留存Mounts 原文；若在副本里跑过 run，另记新容器 ID。

<span id="07-docker-环境变量与敏感信息排查"></span>

## 07 分开读 inspect 与 exec 的环境

配置里可能有口令和密钥，但 inspect 和 exec 看到的不是同一份环境。先分开读，再决定要不要进容器。

操作顺序：先保存 inspect，再决定是否 exec env，对上变量名之后才到受控目录看值。

**1. 两条命令的输出不要合成一份。** inspect 可以在宿主机做。exec 会在运行中的容器里新起进程。容器没在跑时，exec 会失败，只保留 inspect。

```bash
docker exec <container> env
docker inspect <container>
```

**2. 两种环境输出分开读。** docker inspect 的 Env 是容器创建配置，可从宿主机保存。docker exec env 会新建一个 env 进程，通常沿用创建环境，也受本次 exec 覆盖参数影响。两份不同或相同，都不能直接代替应用当时使用的值。

**3. 先搜变量名，再确认值从哪份配置来。** 入口脚本或应用后来设置的变量，要另查对应应用进程。先搜索 DB_PASSWORD、MYSQL_ROOT_PASSWORD、SECRET_KEY、API_KEY、TOKEN、FLAG，再确认这些值来自哪份配置；两份输出相同或不同都不能直接代替实际用值。应用进程的环境不在这两条命令里时，改查该进程，不要把 env 的空缺写成没有口令。

**4. 确需 exec 时单独记录。** 【仅在副本/仿真/授权环境执行】确需 exec env 时先保存原状态，实验输出单独记录。

**5. 来源不同，限制也不同。** 公开场合不要贴原值。

| 来源 | 优点 | 限制 |
| --- | --- | --- |
| docker inspect | 无需进入容器，可保存完整 JSON | 显示创建配置，不保证应用仍按原值运行 |
| docker exec &lt;container&gt; env | 显示新增 exec 进程收到的环境 | 需要容器运行；新增进程；不代表已有应用进程环境 |
| Compose 文件或 .env | 解释变量来源和服务关系 | 文件可能与当前运行实例不同步 |

**6. 输出按敏感材料保存。** 不要把 inspect、env 或 Compose 输出直接粘贴到公开工单和聊天中。先脱敏并保留受控证据副本。

本节已核对变量名来自 inspect 的创建配置，还是这次 exec 的新进程；应用后来设置的变量不在这两份输出里时，还要查对应进程。DB_PASSWORD、MYSQL_ROOT_PASSWORD、SECRET_KEY、API_KEY、TOKEN、FLAG 这些名字能指回具体那一份配置，一并留存受控副本里的 inspect JSON 和 env 输出，公开文本只留变量名。

<span id="08-实战将一次可疑请求对应到日志文件和卷"></span>

## 08 实战：把一次可疑请求对到日志、文件和卷

一次上传请求已经在日志里，还没对上文件在站点目录还是卷里。下面按日志、挂载和卷分开取。

操作顺序：先读 inspect 里的 LogPath 和 Mounts，再保全日志和文件，对上同一次请求。


### 08.1 场景与材料

手里是只读快照和已经保全的 inspect，还不知道日志和网站根在不在默认路径。

操作顺序：先复制 inspect，再读 LogPath 和 Mounts，对上之后再决定去哪个目录。

**1. 先认材料和这份构造示例的边界。** 材料为只读主机快照 `/mnt/evidence`，另有现场保全的容器 inspect JSON 和日志驱动记录。示例容器名为 `web`，实际完整 ID 从保全清单读取；应用根目录 `/var/www/html` 是 bind mount，上传目录使用命名卷，标准输出由 json-file 保存。目标是定位可疑访问和对应文件，明确它们属于哪个存储面。以下时间和输出为构造示例，不代表实际检材已复跑。

**2. 把已保存的 inspect 复制到输出目录，并抽出身份、挂载和日志路径。** `CID` 用 JSON 里的完整 ID，不用容器名代替。

```bash
EVIDENCE_ROOT=/mnt/evidence
OUT=/work/output/container-logs
mkdir -p "$OUT"
cp -a /work/input/web-inspect.json "$OUT/container-inspect.json"
jq '.[0] | {Id,Name,Created,State,Mounts,LogPath,LogConfig:.HostConfig.LogConfig}' "$OUT/container-inspect.json"
CID=$(jq -r '.[0].Id' "$OUT/container-inspect.json")
```

**3. 按读到的路径走，不要退回默认数据根。** 示例 `LogPath=/data/docker/containers/<完整ID>/<完整ID>-json.log`，Mounts 指定主机 `/srv/site` 到 `/var/www/html`。这时不能再按默认 `/var/lib/docker` 寻找，也不能把 `/var/www/html` 的变化归到容器 overlay 可写层。路径和示例不同时，以这份 JSON 为准。

本节已核对完整容器 ID、`LogPath`，以及 `/var/www/html` 对应的主机路径；JSON 里没有 LogPath 或 Mounts 时，先补 inspect，不要改用默认目录。jq 抽出的 LogPath、Mounts 和 `CID` 来自同一份 inspect，一并留存 `$OUT/container-inspect.json` 和这条 jq 输出。

### 08.2 确认路径并保全日志集合

LogPath 已经指向数据根下的容器目录。下一步是把日志文件复制出来，再读里面的时间和请求。

操作顺序：先按 CID 定位日志目录，再复制并做哈希，对上请求时间之后再看文件。

**1. 用快照里的数据根和完整 ID 找到日志，并复制出来。** 目录不在 `$EVIDENCE_ROOT/data/docker` 时，回到 inspect 的 `LogPath`，不要改找 `/var/lib/docker`。

```bash
DOCKER_ROOT="$EVIDENCE_ROOT/data/docker"
LOG_DIR="$DOCKER_ROOT/containers/$CID"
ls -lah "$LOG_DIR"
stat "$LOG_DIR/$CID-json.log"
cp -a "$LOG_DIR/$CID-json.log" "$OUT/stdout-json.log"
find "$LOG_DIR" -maxdepth 1 -type f -name '*-json.log*' -print > "$OUT/log-members.txt"
sha256sum "$OUT/stdout-json.log" > "$OUT/log-copy.sha256"
```

**2. 轮转文件按清单另存。** 按清单另复制实际轮转文件并记录哈希；压缩副本先解码到输出目录，不改检材。容器 JSON 日志每条含 `time`、`stream`、`log`，可用以下方式保留时间与 stdout/stderr 来源再筛选。解析失败就留下原始行，不要丢弃。

```bash
jq -r '[.time,.stream,.log] | @tsv' "$OUT/stdout-json.log" > "$OUT/log-events.tsv"
grep -nEi 'POST |upload|error|denied|timeout|shell|cmd=' "$OUT/log-events.tsv" > "$OUT/log-candidates.txt"
```

**3. 先读这两条构造日志，再决定找什么文件。** `2025-05-18T03:10:00Z` 的 `POST /upload` 返回 200；`03:10:02Z` 又访问 `/uploads/check.php`。先找上传文件和错误日志，再看响应内容及执行记录；仅有 200 还不能确认执行。

**4. 驱动时间和应用时间分开留。** json-file 的 `time` 是驱动记录时间，`log` 内可能另有应用时间。两者分别保留，排时间线时先确认时区。

**5. 路径为空或驱动不是 json-file 时换来源。** 若材料只提供日志驱动为 journald 而 LogPath 为空，改分析保全 journal，并以完整容器 ID 等字段筛选；若是远程驱动，则查对应平台与发送错误。空路径、日志缺口或解析失败都要记入限制。

本节已核对完整 ID 对应的 json 日志、它的哈希，以及 `POST /upload` 和 `/uploads/check.php` 的时间；只有 HTTP 200、没有上传文件或执行记录时，不写成文件已经执行。`time`、`stream`、`log` 来自同一条 JSON，并和 `CID` 的日志文件对应，一并留存日志副本、成员清单、哈希、事件表和候选行；journald 或远程驱动另记来源。

### 08.3 提取应用日志与实际文件

请求指向 `/uploads/check.php`，这个目录可能是站点下的子目录，也可能是卷盖在上面。先分清挂载，再复制文件。

操作顺序：先清点 bind 目录，再读 Mounts，卷里的文件单独做哈希。

**1. 先清点绑定到站点根的目录。** 这里先清点 bind 目录。`uploads` 如果不是普通子目录，不要在这一步就认定文件缺失。

```bash
SITE_ROOT="$EVIDENCE_ROOT/srv/site"
ls -ld "$SITE_ROOT" "$SITE_ROOT/uploads"
find "$SITE_ROOT" -xdev -type f \( -name '*.php' -o -name '*.jsp' -o -name '*.sh' -o -name '.env' \) -print > "$OUT/site-file-candidates.txt"
```

**2. 卷和子目录分开处理。** uploads 如果是命名卷，就从 Mounts 取 Source，映射到 `$EVIDENCE_ROOT` 下的 `_data`，再读目标文件。只有确认 uploads 是普通子目录时，才从站点 bind 目录直接提取。挂载可能遮住底层目录，站点目录中没找到文件时继续查卷。未知脚本只读源码，不通过服务端 URL 试运行。

**3. 把挂载列成表，确认示例是不是这一条。**

```bash
jq -r '.[0].Mounts[] | [.Type,.Name,.Source,.Destination,.RW] | @tsv' "$OUT/container-inspect.json"
```

示例记录为 `volume upload-data /data/docker/volumes/upload-data/_data /var/www/html/uploads true`。Type 不是 volume 时，不要仍去 `_data` 找。

**4. 再保全卷里的文件，并核对副本哈希。** 继续保全卷中的访问/应用日志与样本。`check.php` 不在时，保留 find 清单，不要从站点目录复制一个同名文件顶上。

```bash
UPLOAD_ROOT="$EVIDENCE_ROOT/data/docker/volumes/upload-data/_data"
find "$UPLOAD_ROOT" -xdev -type f -printf '%TY-%Tm-%TdT%TH:%TM:%TS %s %p\n' | sort > "$OUT/upload-files.txt"
stat "$UPLOAD_ROOT/check.php"
cp -a "$UPLOAD_ROOT/check.php" "$OUT/check-from-volume.php"
file "$OUT/check-from-volume.php"
sha256sum "$UPLOAD_ROOT/check.php" "$OUT/check-from-volume.php"
```

本节已核对上传目录是命名卷还是站点子目录，以及 `check.php` 的哈希；站点目录没有文件时，还要查卷；两边都没有就记缺失。Mounts 的 Source 和 `$UPLOAD_ROOT` 是同一路径，原文件和副本哈希一致，一并留存站点候选清单、Mounts 表、卷内文件清单、`check.php` 副本和哈希。

### 08.4 在线采集分支与副本差异

离线快照已经有了。若还有一个已确认的目标会话，可以补运行态输出，但不能把分析机上的同名容器当成目标。

操作顺序：先确认是目标会话，再把 logs、diff、stats、top 和 cp 写入独立目录，两路输出都留。

**1. 只在已确认的目标会话上补这些逻辑输出。** 若另有已确认的目标会话，可以补充以下逻辑输出，仍写入独立采集目录，不把离线分析机的同名容器当目标。容器已停止导致 top 或 logs 失败时，保留错误，不要为了补齐去启动它。

```bash
SINCE='2025-05-18T03:00:00Z'
UNTIL='2025-05-18T04:00:00Z'
docker inspect "$CID" > "$OUT/live-inspect.json"
docker logs --timestamps --since "$SINCE" --until "$UNTIL" "$CID" > "$OUT/cli-stdout.log" 2> "$OUT/cli-stderr.log"
docker diff "$CID" > "$OUT/live-diff.txt"
docker stats --no-stream "$CID" > "$OUT/live-stats.txt"
docker top "$CID" > "$OUT/live-top.txt"
docker cp "$CID:/var/log/nginx/access.log" "$OUT/access.log"
```

**2. 把标准输出、标准错误和退出状态分开解释。** 两路 CLI 输出都保存，stderr 可能含容器标准错误，也可能含 CLI 报错，应结合退出状态与消息内容区分。运行中日志会持续增长，逐文件复制不保证一致时间点；数据库卷更不能靠普通 cp 声称已取得可启动的一致快照。保留采集开始/结束时间，后续在副本与匹配版本下解析。

本节已核对目标会话在 `SINCE` 到 `UNTIL` 之间的 inspect、日志、diff、stats 和 top；普通 cp 没有覆盖数据库卷的一致时间点时，不写成已经取得可启动快照。stdout、stderr 和退出状态分开保存，并且容器 ID 属于目标会话，一并留存 `live-inspect.json`、两路日志、diff、stats、top、访问日志，以及采集起止时间。

### 08.5 可复核结论

请求、路径和文件已经分别取到，还要把它们放进同一张表，并写清结论停在哪一层。

操作顺序：先把时间、路径和哈希列到一张表，再按证据写到“找到文件”或“已经执行”，对不上就记缺哪一份。

**1. 先做对照表。** 将请求时间、日志来源、完整容器 ID、实际挂载路径、样本哈希和文件时间列到同一表中。至少核对原样本与副本哈希一致、路径来自 Mounts、对应时间的访问记录仍保留；文件时间可能被修改，只作辅助线索。哈希不一致就停，不要继续解释文件内容。

**2. 结论按已经对上的那一层来写。** 可以写“保全日志记录该 URI 访问，卷里找到这个哈希的脚本”。若还要写“脚本已执行”，继续找执行日志、程序行为或响应内容。只有访问记录时，就写到访问为止。

**3. 没命中时先记缺什么。** 日志没命中、diff 没列出卷文件或 LogPath 为空时，先记缺少哪份记录。容器已删但卷仍在，核对卷 labels、历史 Mounts、Compose 定义和日志，再确认它原来属于哪个容器，不只按卷名选择。

**4. 命令和字段可以回到这几份说明核对。** 可核对 [Docker 日志驱动文档](https://docs.docker.com/engine/logging/configure/)、[Docker cp 文档](https://docs.docker.com/reference/cli/docker/container/cp/)及 [containerd 配置说明](https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md)。已有进程环境的读取限制见 [Linux proc_pid_environ 手册](https://man7.org/linux/man-pages/man5/proc_pid_environ.5.html)。

本节已核对同一次请求的时间、日志来源、完整容器 ID、挂载路径和样本哈希；没有执行日志或响应内容时，不写成脚本已经执行。原样本和副本哈希一致，路径来自 Mounts，访问记录的时间仍在，一并留存这张对照表，以及日志未命中、diff 未列出或 LogPath 为空时的缺口记录。
