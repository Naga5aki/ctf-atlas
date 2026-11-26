## 01 区分网络配置与历史通信

网络与通信取证先列出接口、地址、路由、名称解析、代理和隧道，再追踪它们与应用、服务和日志的关系。配置说明使用意图，运行现场说明采集时状态，日志说明对应时间范围内的活动。三个层次应分别记录，不把分析机自己的接口和连接当作目标证据。

### 01.1 运行现场与离线材料

| 目标 | 运行现场命令/位置 | 离线可寻找的材料 |
| --- | --- | --- |
| IP 与网段 | `ip addr`、`ifconfig` | 采集输出、接口配置、DHCP/NetworkManager 日志 |
| 路由与网关 | `ip route` | 路由配置、已保存输出及服务日志 |
| DNS | `/etc/resolv.conf` | 解析配置与服务/应用缓存，先检查软链 |
| 静态映射 | `/etc/hosts` | 当前文件、快照、历史版本与可验证残留 |
| 网桥 | `ip link`、`brctl show` | 网桥配置和容器网络元数据 |
| ARP/邻居 | `arp -a`、`/proc/net/arp` | 采集输出与网络记录；缓存不等于完整连接历史 |
| TCP 连接 | `ss -tanp`、`/proc/net/tcp` | 已采集的会话输出、日志或其他通信记录 |

`/proc` 是运行时接口，常规离线根文件系统镜像通常不保存采集时的完整 `/proc`。目录不存在不等于目标从未有连接；在分析机读 `/proc/net/tcp` 也不会得到目标历史。

### 01.2 实战：建立一个现场状态表

下列命令只在已确认身份的目标会话或隔离仿真中执行。执行前记录主机、账户、UTC 时间及环境性质，再保存输出。

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
hostname
ip addr
ip route
ip link
ss -tanp
cat /proc/net/arp
cat /proc/net/tcp
# 较旧工具存在时，保存对应结果作为辅助核对
ifconfig
brctl show
arp -a
```

**示例判读：** 接口 `eth0` 保存地址 `192.0.2.20/24`，默认路由指向 `192.0.2.1`，一条 TCP 连接由某进程关联到远端。记录接口、源/目标地址、端口、状态与进程信息；权限不足可能使进程栏为空。公网出口、NAT、代理和共享网络会改变外部看到的地址，不能直接由一个 IP 确认自然人身份。

仿真启动后分配的地址和新连接是仿真状态，不能代替原现场。容器网桥、端口发布与编排关系集中见[Docker 网络与 Compose](/knowledge/docker-evidence-05/)。

## 02 代理、VPN 与系统设置

### 02.1 配置落点与检查字段

| 客户端/机制 | 常见位置 | 关注字段 |
| --- | --- | --- |
| Clash | `~/.config/clash/config.yaml` | HTTP/SOCKS/mixed 端口、监听地址、代理节点、规则与选择记录 |
| mihomo | `~/.config/mihomo/` | 配置版本、实际加载文件、代理组与规则 |
| v2ray / xray | `/etc/v2ray/config.json` 及实际服务参数引用的路径 | inbound/outbound、监听、目标节点与日志设置 |
| 系统代理 | GNOME gsettings、`/etc/environment`、`/etc/profile.d/` | 代理模式、地址、端口与环境变量 |

默认目录未命中时，从服务单元、启动参数和用户家目录找真实位置。GUI 中存在应用图标只能定位候选程序，不能直接证明启用状态。系统代理也不保证所有应用遵循；应用可能有独立代理、直连规则或 DNS 策略。

```bash
EVIDENCE_ROOT=/mnt/evidence
grep -nE 'port:|socks-port:|mixed-port:|allow-lan:|bind-address:|mode:|server:' \
  "$EVIDENCE_ROOT/home/analyst/.config/clash/config.yaml"
grep -rInE 'https?_proxy|all_proxy|no_proxy' \
  "$EVIDENCE_ROOT/etc/environment" "$EVIDENCE_ROOT/etc/profile.d"
```

命令用于定位文本，仍需读完整 YAML/JSON 上下文；某个 `port` 可能属于远端节点而不是本地监听。配置或订阅可能包含认证凭据，报告限制展示，保留摘要和受控原件。

### 02.2 实战：核对本地代理端口

**材料：** 用户配置、启动日志、已采集监听输出。示例配置包含 `mixed-port: 7890` 和 `allow-lan: false`。

1. 从启动参数或日志确认加载的是这份配置，防止读到订阅缓存或旧副本。
2. 找到运行现场 `ss` 中的对应进程、监听地址和端口，核对本地还是对局域网开放。
3. 从系统/应用代理设置核对客户端是否指向该端口，再检查流量或访问记录。
4. 配置与运行输出不一致时，检查覆盖参数、端口冲突、配置更新时间和采集时间。

**结论边界：** 代理节点地址可以帮助识别出口或中继，不能推出使用者的真实地理位置或身份。节点名称中的国家缩写也可能是自定义标签。要关联用户活动，需结合账户、目标设备、选择日志、实际连接和时间；不能将 IP 地理定位结果直接当作人员所在地。

## 03 主机名解析与损坏映射恢复

### 03.1 从应用名称追到候选地址

**场景：** 应用 `database.php` 记录 `hostname='db-internal'`，需要确认它在目标环境中的地址。先读应用配置，再核对 hosts、DNS 配置、容器/网桥元数据和实际连接。

```bash
grep -nE 'hostname|hostport|database' \
  "$EVIDENCE_ROOT/var/www/html/site/application/database.php"
grep -nE '(^|[[:space:]])db-internal([[:space:]]|$)' "$EVIDENCE_ROOT/etc/hosts"
ls -ld "$EVIDENCE_ROOT/etc/resolv.conf"
readlink "$EVIDENCE_ROOT/etc/resolv.conf"
```

示例 hosts 保存 `10.0.3.120 db-internal`，可表述为“检材的静态映射关联该名称与该地址”。它不自动证明所有时期都使用此解析；DNS、容器内配置或应用缓存可能不同。同网段只能辅助定位，实例归属还需明确配置与数据目录。

### 03.2 实战：hosts 被补零后的候选恢复

**材料：** 损坏文件、文件系统镜像、快照/版本与目标名称。先记录当前长度和补零范围，优先读已验证的快照或备份；没有完整副本时再在原始介质查候选。

```bash
ls -l "$EVIDENCE_ROOT/etc/hosts"
xxd "$EVIDENCE_ROOT/etc/hosts"
LC_ALL=C grep -aob '127.0.0.1' ./work/partition.dd
LC_ALL=C grep -aob 'db-internal' ./work/partition.dd
# 用实际命中偏移读取前后文，4096仅为演示偏移
xxd -s 4096 -l 512 ./work/partition.dd
```

**候选片段示例：**

```text
127.0.0.1 localhost
127.0.1.1 app-server
10.0.3.120 db-internal
```

继续验证字节范围、换行、文件长度、所属块/extent、目录与 inode 或快照关联、事务和时间。相邻块命中不是天然的同一文件；日志、安装包、备份、旧版本和其他账户材料也可能保存相同文本。文件较小并不保证仍有完整副本，更不保证当前有效。

**结论写法：** “在分区副本的某偏移发现一段候选 hosts 内容，包含目标映射；已/未建立其与某个文件版本的结构关联。”未能证明版本时，保留它作为历史解析候选，不直接覆盖损坏原件或填为采集时地址。文件系统旧树与残留验证见[证据介质与文件系统](/knowledge/fic-case-02/)。

## 04 ngrok、frp 与 Cloudflare Tunnel

### 04.1 配置、启动与历史端点

| 工具 | 常见材料 | 继续追踪 |
| --- | --- | --- |
| ngrok | `~/.config/ngrok/ngrok.yml`、旧 `~/.ngrok2/`、实际日志路径 | agent 版本、启动命令、config 覆盖、公网端点与本地 upstream |
| frp | `frpc.ini` / `frpc.toml`、服务单元和日志 | 服务端地址、代理类型、本地/远端端口、域名 |
| Cloudflare Tunnel | `~/.cloudflared/`、`config.yml`、服务/应用日志 | tunnel 标识、ingress、后端服务与历史域名关系 |

ngrok 的当前默认 Linux 配置路径见[配置说明](https://ngrok.com/docs/agent/config)；历史版本和自定义 `--config` 可使用其他位置。端点也可能是账户固定域名或动态产生的地址，不能一律假设每次改变，也不能假设重启仍能恢复历史值。

### 04.2 实战：配置为空时追踪启动链

**场景：** 默认 ngrok 配置没有端点信息，需要确认目标时期是否使用隧道及历史公网地址。先静态检查自启动与命令记录，不启动隧道。

```bash
grep -rInE 'ngrok|frpc|cloudflared' \
  "$EVIDENCE_ROOT/etc/crontab" \
  "$EVIDENCE_ROOT/etc/cron.d" \
  "$EVIDENCE_ROOT/etc/systemd/system" \
  "$EVIDENCE_ROOT/etc/rc.local"
grep -nE 'ngrok|frpc|cloudflared' "$EVIDENCE_ROOT/root/.bash_history"
```

在明确的目标运行现场，还可采集 `crontab -l`、`systemctl list-unit-files`、进程参数及与隧道有关的环境；这些当前结果不能替代历史日志。离线读取用户 cron spool 前先确认用户与路径，读取软链单元需在检材根内定位目标。

**示例历史文本：** `ngrok http 80` 说明启动意图是将本地 80 端口作为上游；不证明命令成功，也不包含历史公网域名。继续找到实际日志目的地，提取带时间的 endpoint/upstream 字段，与服务日志、访问日志和采集的进程记录核对。

```bash
grep -nE 'url=|endpoint|upstream|started tunnel|error' \
  "$EVIDENCE_ROOT/var/log/ngrok.log"
```

日志格式随版本而变；`url=https://service.example.test` 与 `addr=http://localhost:80` 等字段需要读整条记录，区分公网 URL 和本地 upstream。没有日志时，结论应限定为“发现启动配置或命令线索，历史公网地址尚不能确认”。

### 04.3 禁止用新运行结果补历史结论

重新启动 ngrok 可能生成新端点、复用账户端点并产生新通信，任何一种结果都不能单独证明过去的地址。需要历史 agent 日志、服务日志、可信采集、控制面记录或同时期请求证据。配置空、日志缺失、程序未成功启动分别有不同含义，不应合并成“没有使用”。

隧道公网地址可作为历史对外暴露面的候选；再关联 Nginx 请求、后端服务与时间范围。请求源可能显示隧道中继，不能直接当作访问者 IP；是否保存原始客户端头还需按可信代理和日志格式确认。

## 05 通信路径与结论复核

### 05.1 按链路逐层记录

`应用目标名称 → hosts/DNS解析 → 本地代理或容器网络 → 隧道/远端节点 → 后端服务 → 带时间的请求记录`。各层可能不存在，或配置与运行记录不一致；保留差异，不强行拼成一条已证实路径。

### 05.2 最小结果字段

每条结果记录对象和环境、采集时刻、原始配置/日志路径、接口及地址、端口、进程/服务身份、解析方式、历史端点、关联时间和限制。配置存在、进程运行、连接建立、请求成功与用户身份是逐步增加的结论，分别提供相应证据。容器网络专题继续使用[Docker 网络与 Compose](/knowledge/docker-evidence-05/)，不在此重复部署操作。
