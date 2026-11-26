手里是容器网络与宿主机连接记录：网络清单、端口发布、DNS/别名、桥与租约，以及 Compose 定义。本页回答：网络与模式、通信关系、命令的对象、Compose 的对象、三层入口核对，以及怎么把 IP 限定到某一次记录。原始材料保持只读，创建网络、up/down、发布端口只在副本上做。

**先列网络、看模式与端点 → 分清只读与新建 → 认清 up/down 动的对象 → 用桥名与租约限定归属 → 三层核对服务名、IP 与端口 → 把 IP 限定到某一次记录。**

<span id="01-docker-网络证据定位"></span>

## 01 先列网络，再看模式与端点

从 Docker 网络配置、端口发布、DNS 与宿主机连接记录建立通信关系，并核对 Compose 定义与运行状态。集群对象、Pod、CRI 及存储恢复流程统一见 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/)。

手里是容器网络和宿主机上的连接记录，还没把每张网的端点对上容器。下面先列网络，再看模式，最后还原谁在和谁通信。

操作顺序：先列出网络，再看模式和端点，对上容器 ID、IP 和发布端口。


### 01.1 列出与检查网络

手里只有 Docker 网络这个入口，还不知道每张网连着哪些容器。名单和详情要分开留。

操作顺序：先列出网络，再 inspect 每一张，对上网络 ID 和容器。

**1. 先列出网络名称。** `docker network ls` 给出名称、ID 和驱动。命令失败或名单为空时，记下报错和当时的 Docker 环境，不要改到分析机的 Docker 上重查。

```bash
docker network ls
```

**2. 再读一张网的详情。** 把「网络名」换成上一步列出的名字，看子网、网关和已连接容器。名字对不上就回到清单，不要凭常见网名猜。

```bash
docker network inspect 网络名
```

**3. 要一次留下全部网络时，按网络 ID 循环。** 循环里的 `docker network ls -q` 只输出网络 ID。某一张 inspect 失败就停下看那一张，不要把空输出写成没有容器。

```bash
for n in $(docker network ls -q); do docker network inspect "$n"; done
```

本节已核对每张网络的名称、ID，以及 inspect 里列出的容器；某一张 inspect 失败或名单为空时，写明停在哪一条命令。循环得到的网络 ID，和单张 `docker network inspect` 的输出是同一张网，一并留存网络清单，以及每张网的原始 inspect。

### 01.2 网络模式

网络已经列出来，还不知道容器是各自有地址，还是和宿主机或其他容器共用网络。先对照模式，再解释端口。

操作顺序：先看 NetworkMode，再对发布端口和监听，对上模式之后再解释 IP。

**1. 按这张表读模式。** 表里的特征对不上当前 inspect 时，记下实际 `NetworkMode`，不要改成默认 bridge。

| 模式 | 特征 | 取证重点 |
|---|---|---|
| `bridge` | 默认 NAT/虚拟网桥；容器有独立 IP | 端口发布、网桥、iptables/nftables、容器间通信 |
| 用户自定义 bridge | 有内置 DNS 和服务名解析 | 网络别名、服务拓扑、横向访问路径 |
| `host` | 容器共享宿主机网络命名空间 | `docker port` 可能无映射；宿主机监听端口就是容器进程端口 |
| `container:<id>` | 与另一个容器共享网络命名空间 | 两个容器可能使用相同 IP；常见于 sidecar 类结构 |
| `none` | 无外部网络接口 | 仍可通过挂载、IPC 或宿主机操作产生影响 |
| `macvlan` | 容器直接接入物理网段、拥有独立 MAC | 不经 docker0/NAT；核对真实网段内的 IP、ARP 与交换机侧记录 |
| `ipvlan` | 容器接入物理网段，可共用父接口 MAC（L2/L3 模式） | 同样不经 NAT；归属核对看父接口与模式 |

本节已核对这个容器的网络模式，以及它有没有独立 IP 或发布端口；`docker port` 没有映射时，还要看是不是 `host` 或 `container:<id>`，不能直接写成没有端口。inspect 里的模式和表中同一行的特征一致，一并留存模式字段，以及对应的端口或共享容器 ID。

### 01.3 还原容器通信关系

模式已经知道，还缺主机名、发布端口和当时的连接各落在哪一层。按下面的顺序对，对不上就停在缺的那一层。

操作顺序：先记网络端点，再对主机名和发布端口，对上时间线里的连接。

**1. 从每张网记下端点。** 从 `docker network inspect` 记录每个网络的子网、网关、容器 ID、IPv4/IPv6 和 MAC。某一项为空就留空，不要用另一张网的地址补。

**2. 从配置里抽出要连的主机名。** 从容器 `Env`、配置文件和日志提取数据库/缓存/API 主机名。主机名还没解析到上一步的别名或 IP 时，先记成未对应。

**3. 把已发布端口对到宿主机监听和 NAT。** 将宿主机已发布端口与进程监听、NAT 规则关联。发布项有了但 `ss` 没看到监听，继续看下一步，不要先写成应用没启动。

**4. 把外部日志放进同一条时间线。** 将 DNS、代理、负载均衡和防火墙日志加入时间线。没有这些日志时，通信关系只写到已有端点为止。

**5. 在目标会话里看监听和连接。** 下面两条分别是正在监听的套接字和已建立连接。这是该会话当时的网络命名空间，不是历史连接。

```bash
ss -lntup
ss -ntp
```

**6. 再看 Docker 网桥本身。** 接口名对不上 `docker0` 时，先保留 `ip` 和 `bridge` 的原输出，回到网络 inspect 找实际桥。

```bash
ip -d link show
ip addr show docker0
bridge link
bridge fdb show
```

**7. 最后保存 NAT 和过滤规则。** `iptables-save` 与 `nft list ruleset` 按目标上实际有的后端来跑。工具不存在就留下错误，不能写成没有规则。

```bash
iptables-save
nft list ruleset
```

**8. 地址一定要带时间。** 先保存“时间 + 完整容器 ID + 网络 ID + IP”。`bridge` 容器重建后 IP 可能变化，旧日志里的 IP 要按旧时间查。宿主机 `ss` 只看该会话的网络命名空间；没看到容器监听时，再看网络模式、发布端口、转发规则和应用日志，不直接判定应用未启动。

本节已核对同一时刻的网络端点、主机名、发布端口和宿主机监听；DNS、代理或防火墙日志没有时，不把端点写成那一次连接已经发生。时间、完整容器 ID、网络 ID 和 IP 写在同一条记录里，一并留存inspect、`ss`、网桥和 iptables/nft 的原输出。

<span id="02-docker-网络分析命令"></span>

## 02 分清只读与新建网络

要画服务之间怎么连，但创建网络会改目标。首轮只读已有网络。

操作顺序：先只读列出和检查，再确认命名空间，对上服务名或别名之后才解释地址。

**1. 先分清哪些命令只读、哪些会新建网络。** 【仅在副本/仿真/授权环境执行】下表 network create 会新建网络；首轮只读 ls/inspect，演练网络另放隔离副本。

<details>
<summary>展开网络命令副作用表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker network ls | 列出 Docker 网络 | 识别默认网络和 Compose 网络 |
| docker network inspect &lt;network&gt; | 显示连接容器、子网、网关和配置 | 绘制服务通信关系 |
| docker network create &lt;network&gt; | 创建用户定义网络 | 搭建隔离的靶场环境 |

</details>

**2. 同一张用户定义 bridge 上，先用容器名或别名。** 同一用户定义 bridge 网络中，容器通常能用容器名或网络别名解析。web 与 mysql 同网且解析正常时，用 mysql:3306。解析失败就回到网络 inspect 看别名，不要改成分析机自己的地址。

**3. 看到 127.0.0.1 时，先问它属于谁的网络命名空间。** Web 独立网络命名空间里的 127.0.0.1:3306 指向 Web 自己，不是另一个 MySQL。若采用 host、`container:<id>` 或同一 Pod 共享网络，先查共享关系，再解释 localhost。

**4. 跨服务连接用已经验证过的名字。** 先确认网络命名空间是否独立；在普通 Compose bridge 场景中，跨服务连接使用已验证的服务名或网络别名，并核对实际监听地址。名字能解析但端口没人听，就改查应用监听，不把别名当成已经连上。

**5. 可达性不只看 IP。** 网络可达性还受应用监听地址、端口、宿主机防火墙和 Docker 网络驱动影响，不能只看 IP。IP 在表里、连接仍失败时，把这四项里缺的那一项记下来。

本节已核对服务所在网络、可用的服务名或别名，以及它和 127.0.0.1 是否同一命名空间；只有 IP、没有监听、防火墙或驱动记录时，不写成网络已经可达。网络 inspect 里的别名，和应用配置里的主机名是同一个，一并留存只读 ls/inspect 输出；若在副本里创建过网络，另记那次变更。

<span id="03-docker-compose"></span>

## 03 认清 up/down 动的对象

项目能跑起来，但 up、down 和 exec 会创建或删掉对象。先认清每条命令动什么，再决定能不能在这台机器上跑。

操作顺序：先保存项目配置，再按表选命令，对上项目名和完整容器 ID。

**1. 先看命令会不会改现场。** 【仅在副本/仿真/授权环境执行】下表 up/build 会创建服务或镜像，start/stop/down 会改变运行或删除容器，exec 会新增进程。先保存项目配置和日志，再选必要的演练命令。

<details>
<summary>展开 Compose 命令副作用表</summary>

| 命令 | 作用 | 用途与操作环境 |
| --- | --- | --- |
| docker compose up | 创建并前台启动服务 | 观察实时输出和启动依赖 |
| docker compose up -d | 后台创建并启动服务 | 常规靶场启动 |
| docker compose ps | 列出本项目容器 | 确认服务状态和端口 |
| docker compose logs | 显示项目服务日志 | 整体排障 |
| docker compose logs -f | 持续跟踪全部服务日志 | 联动复现问题 |
| docker compose logs web | 只显示 web 服务日志 | 聚焦单个服务 |
| docker compose stop | 停止服务但保留容器 | 稍后继续启动 |
| docker compose start | 启动已创建且停止的服务 | 继续使用原容器 |
| docker compose down | 停止并移除项目容器和默认网络 | 拆除环境；默认不删命名 Volume |
| docker compose up -d --build | 先按需重建镜像再后台启动 | 代码或 Dockerfile 变化后更新 |
| docker compose build --no-cache | 不使用构建缓存重建服务镜像 | 排除缓存污染或验证干净构建 |
| docker compose exec web bash | 在 web 服务容器中执行 Bash | 进入常规 Linux 镜像 |
| docker compose exec web sh | 在 web 服务容器中执行 sh | 进入 Alpine 或精简镜像 |

</details>

**2. 停服务和拆项目不是同一件事。** 对照下一张表看容器、网络和 Volume 会不会被删。取证主机上要拆环境时，先回到第 1 步留下的配置和日志。

| 比较项 | docker compose stop | docker compose down |
| --- | --- | --- |
| 容器 | 停止但保留 | 停止并移除 |
| 默认网络 | 保留 | 移除 Compose 创建的默认网络 |
| Volume | 保留 | 默认保留；-v 删除声明的命名卷及所移除容器附带的匿名卷，external 卷不由 down 删除 |
| 再次启动 | docker compose start | docker compose up 重新创建 |
| 取证建议 | 仍改变运行状态，先采集 | 可能移除容器可写层，证据主机慎用 |

**3. 列表之前先确认是哪一个项目。** `docker compose ps` 默认只列所选项目的运行容器。记录工作目录、Compose 文件与项目名，另把已停止容器也列出来；用完整容器 ID 与 Docker 全局清单对应。同名服务可能来自另一项目，不能只凭服务名选容器。名单里没有已停止容器时，补一次包含停止状态的列表，不要当成容器已经不存在。

**4. 带删除的收尾只放在隔离副本。** 【仅在副本/仿真/授权环境执行】docker compose down -v 删除项目声明的命名 Volume 和被移除容器附带的匿名卷，external 卷除外；down --rmi all 删除服务镜像。先保存卷、可写层和配置，再在隔离副本确认实际删除项，别用 down 收尾取证。副本上的删除结果不能回写成目标原来就没有这些卷。

本节已核对工作目录、Compose 文件、项目名，以及完整容器 ID；`docker compose ps` 只有运行中容器时，已停止容器还要另列。项目里的服务名能对上 Docker 全局清单中的同一个完整容器 ID，一并留存项目配置、日志，以及在副本里执行过的 up/down/exec 记录。

<span id="04-容器网桥与通信归属"></span>

## 04 容器网桥与通信归属

地址落在常见私网段里，还分不清是 Docker 桥还是 LXC 桥。下面用桥名、租约和配置把归属限定住。

操作顺序：先看桥名和默认网段，再对 hosts 与租约，对上运行时再解释 IP。


### 04.1 容器网络

私网地址已经出现，桥名和租约还没对上。网段本身不能选定运行时。

操作顺序：先对桥和租约文件，再从主机名查到 IP，对上实际归属，而不是只看网段。

**1. 先按这三条对常见布局。**

- Docker：`docker0` 网桥，默认 `172.17.0.0/16`；
- **LXC**：`lxcbr0` 网桥 + **dnsmasq** 提供 DHCP/DNS（痕迹 `/var/lib/misc/dnsmasq.lxcbr0.leases`）；
- **判定技巧**：应用配置中的数据库主机名 → 查 `/etc/hosts` 得 IP → 结合网桥所属运行时配置、容器元数据和该 IP 的实际归属判断；网段只提供线索。

**2. 默认布局对不上时，把改过的桥名和 DHCP 记下来。** 这些是常见默认布局，运行时可以并存，桥名、子网和 DHCP 服务都可以修改。`10.x` 或 `172.x` 不能排除任何一种运行时；空租约文件也不能证明没有网络活动。租约为空就改查静态地址和另一条配置路径，不要停在默认网段。

本节已核对桥名、hosts 里的 IP，以及这个地址当时属于哪一种运行时；只有 `10.x` 或 `172.x`、没有桥和租约时，归属仍未确定。主机名、`/etc/hosts` 的 IP、桥配置和容器元数据指的是同一个地址，一并留存桥配置、hosts，以及 `/var/lib/misc/dnsmasq.lxcbr0.leases` 或它缺失的记录。

<span id="05-实战核对-docker-服务名ip-与发布端口"></span>

## 05 实战：三层核对服务名、IP 与端口

应用写了服务名，宿主机上又有发布端口。下面把服务名、容器 IP 和主机端口分成三层核对。

操作顺序：先固定容器和网络对象，再读 IP 与发布端口，对上应用配置里的服务名。


### 05.1 场景与材料

材料是同一时段的容器和网络记录，还没确认 web 的数据库配置指向哪个端点、服务有没有发布到主机外面。

操作顺序：先在目标会话固定对象，再把输出放进独立目录，对上采集时间。

**1. 先认材料和输出位置。** 材料为目标现场同一时段保全的 `web`、`mysql` 容器 inspect JSON、network inspect JSON，以及只读主机快照 `/mnt/evidence` 下的应用配置、Compose 文件和网络日志。目标是确认 web 的数据库配置对应哪个网络端点、服务是否对主机外部发布。输出写入 `/work/output/container-network/`；下列名称、地址、时间与结果是构造示例，不表示对实际检材已实测。

**2. 在已确认的目标会话里把当前关系一次留下来。** 容器名对不上就改用清单里的完整 ID，不要在分析机上找同名容器。

```bash
OUT=/work/output/container-network
mkdir -p "$OUT"
docker ps -a --no-trunc > "$OUT/containers.txt"
docker network ls > "$OUT/networks.txt"
docker inspect web > "$OUT/web-inspect.json"
docker inspect mysql > "$OUT/mysql-inspect.json"
docker network inspect app-net > "$OUT/app-net-inspect.json"
docker port web > "$OUT/web-ports.txt"
ss -lntup > "$OUT/listeners.txt"
ss -ntp > "$OUT/connections.txt"
iptables-save > "$OUT/iptables.txt"
nft list ruleset > "$OUT/nft-ruleset.txt"
```

**3. 命令失败和没有规则不是一回事。** iptables 与 nft 的可用性、后端和权限应按目标版本记录；任何命令失败都保留错误，不能把工具缺失当成没有过滤规则。现场连接会变化，输出必须记录采集开始/结束时间。

本节已核对这一时段的 `web`、`mysql`、网络 `app-net`，以及发布端口和宿主机监听；某条命令失败时，保留错误，不把缺的规则或连接补成空。输出目录里的 inspect 和 `ss` 带有同一次采集的起止时间，一并留存 `/work/output/container-network/` 下的清单、inspect、端口、监听和防火墙输出。

### 05.2 读取结构化关系

原始 JSON 已经在输出目录里，还没读出谁和谁同网、端口发布到哪里。

操作顺序：先抽出网络和端口字段，再按示例对地址，桥名对不上就回到驱动。

**1. 先从已保存的 JSON 抽出关系，不重新查询现场。** 文件不是单个容器记录时停下来看结构，不要改用别的字段凑 IP。

```bash
jq '.[0] | {Id,Name,NetworkMode:.HostConfig.NetworkMode,Networks:.NetworkSettings.Networks,Ports:.NetworkSettings.Ports}' "$OUT/web-inspect.json"
jq '.[0] | {Id,Name,Networks:.NetworkSettings.Networks}' "$OUT/mysql-inspect.json"
jq '.[0] | {Id,Name,Driver,IPAM,Containers}' "$OUT/app-net-inspect.json"
```

**2. 按构造示例读地址和端口。** web `10.30.0.5` 与 mysql `10.30.0.8` 都在 app-net；mysql 有别名 `mysql`，应用 `DB_HOST=mysql` 与之相符。要确认某次连接成功，还需该时刻的连接或业务日志。web 的 `127.0.0.1:8080 -> 80/tcp` 发布到宿主机回环。mysql 没有主机发布端口，但同网容器仍可能直接访问 mysql；再查其他网络连接和监听配置。只有别名、没有那一时刻的连接日志时，停在“配置指向这个别名”。

**3. 查桥、链路和 FDB 时，桥名要从驱动来。** 查询 bridge/link/fdb 时，桥名要从驱动与接口关系核对，而不是所有网络都查 docker0。`ip addr show docker0` 失败或接口不属于这张网时，改用 inspect 里的实际接口。

```bash
ip -d link show
ip addr show docker0
bridge link
bridge fdb show
```

**4. 自定义桥不要停在 docker0。** 如果 app-net 是自定义桥，实际接口常与网络 ID 有关联，仍须结合 inspect、link 及转发规则确认。FDB 是链路转发线索，不等同于完整流量日志。没有流量日志时，不把 FDB 条目写成通信已经发生。

本节已核对web 与 mysql 是否在同一张网、别名，以及 web 的发布端口；没有该时刻的连接或业务日志时，不写成数据库连接已经成功。`DB_HOST=mysql` 和网络 inspect 里的别名 `mysql` 是同一条，一并留存三段 jq 输出、桥和 FDB 输出，以及采集时间。

### 05.3 实战：宿主机与容器并存时定位数据库入口

宿主机上有 Apache，容器清单里又有 Nginx 和 MySQL，网站入口、代理后端和数据库地址还叠在一起。

操作顺序：先看宿主机监听，再读代理配置，对上容器端口和发布地址。

**1. 先把三层入口分开。** 主机有 Apache 进程，容器清单同时出现 Nginx 与 MySQL，需要区分网站入口、代理后端和数据库地址。`docker ps -a` 含已退出容器，镜像名称、进程名称或软件目录都不足以独立证明服务对外工作。

**2. 按固定顺序查，并把每一层写成同一行。** 按下面顺序查入口：先看宿主机监听和 PID，再读 Web 虚拟主机/代理配置，最后对应容器完整 ID/State、网络和发布端口。记录成 `Host:端口 → 进程或发布项 → 容器端口 → 应用`，让每一层都有配置或输出可查。中间一层对不上就停在那一层，不要跳到容器端口。

**3. 用构造出来的发布项看客户端该填哪个端口。** MySQL 的 inspect 中 `NetworkSettings.Ports` 为：

```json
{"3306/tcp":[{"HostIp":"127.0.0.1","HostPort":"33306"}]}
```

在目标宿主机上，用 `127.0.0.1:33306 → 容器 3306/tcp` 的前者连接。同网络应用可使用 `db:3306`，分析机自己的 localhost 不是目标主机；远程客户端不能直接使用目标回环地址。多个发布项都保留，逐项读 HostIp/HostPort，并区分 IPv4 与 IPv6，不只取第一项。

**4. 看到端口相关字段时，对照这张表看它能说明到哪一层。** 表的右列仍缺时，不要把左列写成服务已经对外工作。

<details>
<summary>展开端口字段判读表</summary>

| 看到什么 | 可以说明什么 | 还缺什么 |
| --- | --- | --- |
| 镜像存在 | 本地存有该镜像内容 | 容器创建/启动、应用状态与请求 |
| ExposedPorts 有 3306 | 镜像或容器声明端口 | 是否实际发布、绑定地址和监听 |
| HostConfig.PortBindings | 创建时请求的发布配置 | 当前 NetworkSettings、宿主机状态与实际网络路径 |
| 端口发布项和监听 | 当前端点具备部分连接条件 | 防火墙/NAT、认证、业务响应与历史覆盖 |
| 代理规则指向某容器 | 配置定义一条后端路线 | 目标时期请求是否真正经过该路线 |

</details>

**5. 库只在容器网络里开放时，不要为了取证去发布到公网。** 若数据库仅在容器网络内开放，不直接创建公网发布来取证；按既有隔离恢复或受控隧道路线读取实验数据。发布端口不等于任意来源都能访问，历史通信需当时的日志、规则及业务记录支持。命令和字段见 [Docker 发布端口说明](https://docs.docker.com/engine/network/port-publishing/)。

本节已核对 `Host:端口 → 进程或发布项 → 容器端口 → 应用` 这一行里的每一层；只有镜像、ExposedPorts 或代理规则时，按表的右列写下还缺的记录。`NetworkSettings.Ports` 里的 HostIp/HostPort 和宿主机监听是同一项，一并留存容器清单、发布项、虚拟主机或代理配置，以及没有改公网发布的说明。

### 05.4 Compose 定义与运行状态比较

快照里有 Compose 文件，它和当前容器是不是同一次创建还不知道。先读定义，不要为了补状态去启动项目。

操作顺序：先复制定义，再固定展开用的输入，对上 inspect 里的端口、卷和网络。

**1. 定义和当前容器分开读。** 只读快照中的 `/srv/app/compose.yaml` 与 `.env` 可以解释定义，二者不自动等于当前容器创建配置。先复制到分析目录，检查变量、服务网络、ports、volumes 与 external 声明；不执行 up/down 来补状态。

```bash
EVIDENCE_ROOT=/mnt/evidence
ls -lah "$EVIDENCE_ROOT/srv/app"
cat "$EVIDENCE_ROOT/srv/app/compose.yaml"
sha256sum "$EVIDENCE_ROOT/srv/app/compose.yaml" "$EVIDENCE_ROOT/srv/app/.env"
```

文件不在 `/mnt/evidence/srv/app` 时，记下缺失，不要到别的目录找同名文件顶上。

**2. 展开之前先把输入固定下来。** 记录工作目录、项目名、Compose 版本、按顺序使用的 `-f` 文件、`--env-file` 和参与替换的 shell 变量。这些没记就不要解释展开结果和历史配置为什么不同。

**3. 只在副本里展开，并和原 inspect 比较。** 再运行副本里的 `docker compose config`，检查展开的 ports、volumes、网络是否与原 inspect 相符。多个文件会合并，shell 同名变量可覆盖环境文件；先清点分析机变量，避免误换历史地址或镜像。输出含秘密时受控保存。发现差异就记下输入和结果，不用重建容器消掉差异。

**4. 验证时把身份和通信分开。** 验证至少包括容器完整 ID、网络 ID、端点 IP、别名、端口绑定与应用配置路径；连接日志、DNS/代理/NAT 记录才能支持某个时刻的通信。网络元数据中的地址可在重建后复用，结论必须带时间。没有那一时刻的连接日志时，地址只说明定义或当前端点。

本节已核对Compose 定义里的 ports、volumes、网络，和原 inspect 是否一致；只有定义、没有连接日志时，不写成某个时刻已经发生通信。`docker compose config` 的展开结果和 inspect 用的是同一组已记录输入，一并留存 `compose.yaml` 与 `.env` 的哈希、`-f` 和 `--env-file` 顺序，以及差异记录。

<span id="06-实战用-lxc-定义与租约限定-ip-归属"></span>

## 06 用 LXC 定义与租约限定 IP 归属（回链主线）

IP 已经从 hosts 里读到，还不能据此说它属于哪一个容器。**app-db 的 LXC 定义与租约解析主线在 [Docker 取证 01 §09.2](/knowledge/docker-evidence-01/#092-实战沿数据库配置追到-lxc-根目录)**；本节只保留本页要固定的材料、现场命令与结论。

操作顺序：先固定采集时间，再对定义、MAC 和租约，对上之后才解释那一次请求。


### 06.1 固定时间与材料路径

快照里的 hosts、LXC 配置和租约都在，但同网段说明不了这个 IP 属于谁。这里只固定材料与时间：材料为 `/mnt/evidence` 下主机快照，采集时间为 `2025-05-18T03:20:00Z`，应用配置指向 `app-db`、hosts 映射为 `10.20.3.41`、现场保全的 lxcbr0 地址为 `10.20.3.1/24`。三条材料路径（`/etc/hosts`、`/var/lib/lxc/app-db/config`、`/var/lib/misc/dnsmasq.lxcbr0.leases`）与 MAC/IP/主机名的对应、`lxc.net.0.link`/`hwaddr` 的判读、租约到期时间换算，完整步骤见 [Docker 取证 01 §09.2](/knowledge/docker-evidence-01/#092-实战沿数据库配置追到-lxc-根目录)。材料为构造例；只凭同网段无法确定归属。

快照时间与三条材料路径、`app-db` 的 MAC/IP 对应，以及租约原文与换算结果；租约为空、MAC/IP/主机名对不上或只有同网段时，归属仍未确定。
本节已核对 `app-db` 的定义、MAC `00:16:3e:20:03:41` 和租约里的 `10.20.3.41`；没有 `03:10` 当时的状态和访问记录时，不写成那次请求来自该容器。租约行里的 MAC、IP、主机名和 LXC 定义是同一条，一并留存hosts、配置、租约原文，以及两个文件的哈希和换算后的到期时间。

### 06.2 验证与限制

目标现场只保存当时状态：`lxc-ls -f`、`lxc-info -n app-db`、`ip addr` 和 bridge/邻居记录，并与定义及采集时间核对；离线材料不提供运行态，不为补状态而启动 LXC，分析机上的状态也不能写成快照里的状态。租约为空时依次查静态地址、租约清理、另一配置路径和采集遗漏，不为凑结论补一个地址。IP 可重新分配，结论要带时间，不按默认网段认定运行时。仿真侧命令见 [Docker 取证 01 §09.4](/knowledge/docker-evidence-01/#094-仿真连接与容器内命令)。

采集时间下的定义、租约，以及现场保存的 `lxc-ls -f`、`lxc-info -n app-db` 或 `ip addr`；租约为空或只有离线材料时，运行状态仍未知；IP 旁要写着它来自哪一个时间的定义、租约或日志。
本节已核对采集时间下的定义、租约，以及现场保存的 `lxc-ls -f`、`lxc-info -n app-db` 或 `ip addr`；租约为空或只有离线材料时，运行状态仍然未知。IP 旁写着它来自哪一个时间的定义、租约或日志，一并留存现场命令输出、空租约时查过的路径，以及没有启动 LXC 的记录。
