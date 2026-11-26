## 01 校准抓包边界与首轮会话复核

拿到 PCAP/PCAPNG 检材时，先记录文件 SHA-256、捕获接口、起止时间、时区、捕获过滤器与丢包截断情况。镜像端口、主机网卡与网关抓包看到的方向不同；缺少某个报文不能直接证明通信未发生。首轮先用 capinfos 与 	shark 统计会话，再按五元组（源/目的 IP、端口、协议）定位异常流（完整路线见[网络取证导读](/knowledge/forensic-guide-network/)，16 类协议的显示过滤式与导出命令速查见[Wireshark 过滤](/knowledge/forensic-traffic-filters/)）：

`ash
capinfos capture.pcapng
tshark -r capture.pcapng -q -z conv,tcp
tshark -r capture.pcapng -Y 'dns.flags.response == 0' -T fields -e frame.number -e ip.src -e dns.qry.name
`

| 常见分析任务 | 核心观察点 | 独立验证方式 |
| --- | --- | --- |
| 文件传输 | HTTP/FTP/SMB 会话、分片、Content-Length 与传输编码 | 导出重组后校验文件魔数、尾部结构与 SHA-256 |
| 命令控制（C2） | 周期性心跳、固定 URI/User-Agent、加密或编码响应规律 | 关联终端进程、DNS 解析记录与服务端日志 |
| 数据外传 | 异常上行字节量、超长 DNS 查询名、ICMP/HTTP 编码片段 | 按序去重拼接载荷，核对解码结构与落地文件 |
| 扫描与口令爆破 | 短时间多端口 SYN、同一登录接口高频失败后跟随成功会话 | 对照服务端认证日志与后续受保护页面请求确认是否突破 |

对每条可疑会话建立复核表：起止帧号 / 源与目的端点 / 请求字段 / 响应状态 / 上传下载字节数 / 提取件哈希。仅有 TCP SYN 不等于完成应用交互；TLS 流量在无合法密钥（如 SSLKEYLOGFILE）时只能分析握手元数据、SNI、证书与时序，不能把域名字段写成已解密的明文请求。

## 02 攻击来源、邮件与扫描次数

出现次数最多的 IP 往往是服务器、网关或正常客户端，不能直接认定攻击者。先按会话重组，识别请求方向、载荷、失败/成功动作和后续影响，再用主机日志与代理配置定位来源。

SMTP 要区分信封 `MAIL FROM/RCPT TO`、邮件 From/To、Received 链及显示名称。保存 TCP 流、邮件头、编码和附件哈希；From 可伪造，Received 也要确认可信跳点。HTTP 的 200 只说明响应状态，需检查请求参数、响应内容、写入文件和服务日志才能确认利用结果。

ICMP 扫描按源/目标、Echo Request 类型、标识与序号、时间区间去重。把回复、重传和多分片都数成独立扫描会高估数量；“第几个地址”与“总次数”应先明确统计口径。抓包覆盖不全时只能报告可见范围。

## 03 常见 WebShell 通信特征

| 家族 | 候选模式 | 复核重点 |
| --- | --- | --- |
| 菜刀 | 可见代码片段、Base64 与特定参数结构 | 可被改名/编码，检查服务端脚本和响应 |
| 蚁剑 | 参数编码、模块化请求与分段返回 | 自定义编码器会改变表面特征 |
| 冰蝎 2/3/4 | 版本相关握手、加密载荷、会话与响应 | 不存在适用于所有版本的单一包长或固定头 |
| 哥斯拉 | 初始载荷、会话建立与后续功能调用，编码/加密响应 | 密钥、密码参数、标记与服务端实现共同确认 |

识别顺序：重组 TCP/HTTP → 解压和传输编码 → 区分首次加载与后续交互 → 对照服务器脚本中的密码/密钥与算法 → 静态验证解码结构 → 关联具体命令与落地影响。仅命中特征不能直接确定操作者；TLS 不可见时改查合法取得的解密条件和服务器记录。

## 04 CDN 与代理地址

CDN 会使 DNS、客户端抓包和访问日志出现边缘节点或代理地址。取证首先检查域名、证书、反向代理配置、可信转发头和日志记录位置。历史 DNS、关联子域名、证书和邮件头可以提供候选源站；候选 IP 还需证据印证，不将历史地址直接当当前目标。

多个地区解析不同或出现 CDN 厂商域名可提示 CDN，不能独立证明来源。未经信任配置验证的 X-Forwarded-For 可由请求者伪造；不以主动攻击、漏洞触发或批量扫描作为确认源站的必要步骤。

## 05 实战：判断扫描、认证尝试与成功行为

**场景与材料：** 抓包中一个地址短时间访问多个端口，随后出现认证请求。需要区分端口探测、认证失败和实际成功操作，而不是按出现次数最多的 IP 归因。

1. 确定采集点、目标时间段和方向，按端点、协议与会话列候选。排除服务器回包、代理流量和重传导致的重复统计。
2. 对扫描分别记录目标数、端口数与逻辑尝试数。ICMP 按 Echo Request 的源/目标、标识、序号与时间去重；TCP 探测与完整连接分开记录。
3. 对认证核对协议中的请求、响应与状态，区分失败尝试和成功认证。HTTP 200 不能替代应用的成功状态，更不能证明命令或文件写入完成。
4. 沿成功候选查询服务器认证日志、应用动作和文件/数据库变化，用会话标识及统一时间关联。对 WebShell 先核对服务端实现，再验证解码，不凭固定包长确定家族。
5. 若可见端点属于 CDN、代理或 NAT，先记录这一层归属，继续检查可信转发链；抓包中看到的 IP 不自动等于最终操作者。

**报告示例：** “可见范围内存在多端口探测和多次失败认证；另有一条候选成功响应，但尚缺主机操作日志，因此实际执行行为不能确认。”统计表附上过滤条件、去重键、帧号范围和缺失/加密范围，便于重算。

## 06 实战：还原后台访问、传文件与交互连接

### 06.1 材料与分析顺序

**场景：** 同一抓包中出现路由器管理页面、异常 DNS 回答、FTP 上传和后续 TCP 交互。分析目标是还原通信过程，分别回答“尝试了什么、是否认证成功、传了什么、是否执行了命令”。下文帧号、地址和端口均为示例，必须替换为实际抓包字段。

**材料：** 原始 PCAP/PCAPNG 的只读副本、采集点与时区说明；有条件时补充路由器配置、访问日志、终端进程及上传文件。仅有普通以太网流量不能补出不存在的无线帧；无线 SSID 与握手另见[无线网络：SSID、握手与离线验证](/knowledge/forensic-wireless/)。

```bash
mkdir -p ./work/streams ./work/objects
sha256sum ./evidence/capture.pcapng
capinfos ./evidence/capture.pcapng
tshark -r ./evidence/capture.pcapng -q -z io,phs -z conv,tcp
```

先按 `HTTP 管理会话 → DNS 查询与回答 → FTP 控制/数据会话 → 后续交互连接` 建立时间表。这是寻找候选的路线，不能预先认定所有阶段由同一人完成。每条边还需端点、会话、时间与主机证据连接；NAT、代理、共用账户都可能削弱归因。

### 06.2 HTTP 认证：失败批次与成功会话

```bash
tshark -2 -r ./evidence/capture.pcapng -Y 'http.request || http.response' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e ip.src -e ip.dst -e tcp.stream \
  -e http.request.method -e http.host -e http.request.uri \
  -e http.response.code -e http.response_in -e http.request_in
```

1. 找同一登录接口的连续 POST、重复用户名字段及相近请求间隔。`luci_password` 是 LuCI 风格表单的候选字段；应用可以修改字段名，仍应读实际表单和请求实体。
2. 在匹配的请求/响应中记录失败文案、重定向位置、Cookie、会话令牌与后续受保护页面。二次分析 `-2` 有助于读取向后关联字段；关联缺失时回到同一 TCP 流的完整顺序，不跨流拼凑。
3. “403 后跟 200”可能是失败登录后返回登录页面。只有成功状态、有效会话和受保护操作相互一致，才支持认证成功；大量失败更适合先表述为认证尝试，再判断是否构成字典尝试或自动化。
4. 若 `Authorization: Basic ...` 或明文表单包含凭据，保存字段位置并在受控工作记录中解码。解码得到用户名/口令只说明该请求提交了这些值；认证成功与操作权限仍要检查响应。

**示例判读：** 一条请求返回 302，设置新的会话 Cookie；下一条携带同一 Cookie 访问配置页，响应包含登录用户名和设置字段。相比单独的 200，这条会话链更能支持后台登录成功。不要把响应里的默认示例密码、输入框掩码或旧配置值当成已使用的认证凭据。[HTTP 字段参考](https://www.wireshark.org/docs/dfref/h/http.html)可核对关联字段与版本。

### 06.3 页面中的系统与无线配置

在 Wireshark 中追踪 HTTP 流，或使用 `文件 → 导出对象 → HTTP` 保存页面实体；对应命令如下。

```bash
tshark -r ./evidence/capture.pcapng --export-objects http,./work/objects
rg -n 'Powered by|OpenWrt|ImmortalWrt|LuCI|luci_password|ssid|password|key' ./work/objects
```

先检查 Content-Encoding、字符编码及响应是否完整。页脚中的 OpenWrt/ImmortalWrt、LuCI 标识支持该页面所呈现的固件或管理界面身份；主题可修改、反向代理可转发页面，精确版本仍以配置导出、系统信息响应或主机记录复核。

若配置页面确实以明文返回目标 SSID 的 `key`，记录 SSID、BSSID/接口、配置节名和响应时间，再与对应无线握手离线验证互证。`key` 也可能是 API 密钥、占位值或未保存表单，不能只按字段名认定是无线口令。查看提取 HTML 时优先使用文本；需要渲染时在禁用网络和脚本的隔离环境中检查，避免触发历史页面里的外部请求。

## 07 实战：DNS 异常回答的判定

### 07.1 从应答回到原查询

```bash
tshark -r ./evidence/capture.pcapng \
  -Y 'dns.flags.response == 1 && dns.flags.rcode == 0' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e ip.src -e ip.dst \
  -e dns.id -e dns.qry.name -e dns.a -e dns.aaaa -e dns.resp.ttl
```

`rcode == 0` 表示 DNS 返回 NoError，不保证存在 A/AAAA 记录，也不证明返回地址正确。把每条回答与查询 ID、查询名、类型、客户端/解析器端点对应；再检查 CNAME 链、TTL、同时出现的多个回答与后续真实连接。

### 07.2 私网地址为何只是线索

公开域名解析到 RFC1918 地址可能来自 split DNS、VPN 内部解析、广告拦截、实验环境或正常的本地服务；解析到公网地址也可能被篡改。判断 DNS 劫持应核对该时间和网络环境下的预期配置，而不是用“内网地址”替代证据。

**独立示例：** 某客户端查询 `portal.example.test`，回答为 `192.168.50.20`。此前路由器设置记录显示上游 DNS 被改为另一地址；同时间的异常解析器返回该私网地址，随后 HTTP 流访问伪造登录页面。若这些证据中的域名、客户端、时间和解析路径一致，可支持“解析配置被修改并将该域名导向异常服务”。缺少预期配置或页面证据时，结论保持为“异常解析候选”。

可用路由器配置、解析器日志、hosts 文件和采集时可信解析记录交叉验证。现在查询得到的 DNS 结果可能因 CDN、负载均衡或记录更新而变化，不能无条件替代历史正确结果；离线分析不需要向历史可疑端点发起访问。

## 08 实战：FTP 文件重组与 ZIP 核验

### 08.1 控制信道决定文件和方向

```bash
tshark -r ./evidence/capture.pcapng -Y 'ftp' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e ip.src -e ip.dst -e tcp.stream \
  -e ftp.request.command -e ftp.request.arg \
  -e ftp.response.code -e ftp.response.arg
tshark -r ./evidence/capture.pcapng -Y 'ftp-data' \
  -T fields -e frame.number -e tcp.stream -e ip.src -e ip.dst -e tcp.len
```

控制会话中的 `USER/PASS` 可暴露明文凭据；只有相应登录成功响应，才能支持服务端接受认证。`STOR` 通常是客户端上传，`RETR` 通常是下载；结合 `PORT/EPRT` 或 `PASV/EPSV` 协商及真实端点，定位数据会话。主动/被动模式影响 TCP 建连方向，不能按“谁发送 SYN”推断文件上传方。[FTP 字段参考](https://www.wireshark.org/docs/dfref/f/ftp.html)列出协商和响应字段。

### 08.2 导出原始文件字节

1. 从控制流记录文件名、传输模式 `TYPE I/TYPE A`、数据连接端点、开始与完成响应。`150` 表示准备传输，`226` 是完成线索；仍需核对实际数据完整性。
2. 在目标数据会话上选择 `追踪 → TCP 流`，核对两端点并只选择**传文件的单一方向**。
3. 将“显示数据格式”设为 **Raw/原始数据**，保存为 `./work/transfer.zip`。不把 ASCII/十六进制显示文本、双向会话或 TShark 的统计标题直接改名为 ZIP。
4. 检查 TCP 重传、乱序、缺口及抓包截断；流重组后的字节与逐包 payload 简单拼接不同。`TYPE A` 可能转换换行，二进制 ZIP 通常需要 `TYPE I`；异常转换也可能造成结构损坏。

```bash
sha256sum ./work/transfer.zip
file ./work/transfer.zip
xxd -l 32 ./work/transfer.zip
zipinfo ./work/transfer.zip
unzip -t ./work/transfer.zip
```

ZIP 的局部头魔数只是格式线索；应同时检查中央目录、成员清单、解压后的 CRC/长度及是否需要口令。不同上传会话中的同名文件分别保存与计算摘要，不能覆盖后假设为同一内容。

### 08.3 加密 ZIP 与传输闭环

确认加密标志、压缩方法及完整性后，优先找同会话的凭据、配置、聊天或其他已有线索。若需要离线候选验证，使用已有压缩包工具流程并限定字典/范围，见[凭据与加密数据](/knowledge/forensic-protected-data/)与[密码学取证](/knowledge/fic-case-08/)。不能把错误 CRC 或截断当成密码错误，也不能将某个常见数字预设为正确口令。

解压到隔离工作目录，先检查成员路径、文件类型与摘要；不执行提取出的程序。把 `控制流中的 STOR 文件名 → 数据流方向与字节 → ZIP 成员 → 主机落地文件摘要` 连起来，才能讨论文件进入了哪个环境。服务端返回完成不独立证明上传文件随后被执行。

## 09 实战：反向连接与命令统计

### 09.1 从触发载荷找到所有候选流

`http contains "/bin/sh"` 可找到未编码且可被解析的候选载荷；编码、分片重组、压缩或 TLS 会影响可见性。它只是检索入口，不足以确认反弹 shell，也不能自动给出监听端口。

```bash
tshark -r ./evidence/capture.pcapng -Y 'http contains "/bin/sh"' \
  -T fields -e frame.number -e tcp.stream -e http.request.uri
CALLBACK_PORT=4444
tshark -r ./evidence/capture.pcapng -Y "tcp.port == $CALLBACK_PORT" \
  -T fields -e tcp.stream | sort -n -u
tshark -r ./evidence/capture.pcapng -q -z 'follow,tcp,ascii,42'
```

端口 `4444` 与流号 `42` 为示例：端口需来自实际载荷/连接，流号需来自当前抓包的会话列表。使用 `tcp.port` 包含双向数据；只用 `tcp.dstport` 可能漏掉响应和反向建连。非标准端口若被误解为 HTTP，可回看原始 TCP 流，不能强行按应用协议解读。

### 09.2 命令行、包数与执行结果分别记录

反向连接可能重连；一条流没有命令不意味着其他流也没有。遍历同一目标端点与时间段的所有连接，先确定输入方向，重组后再恢复交互内容。多个命令可在一个 TCP 包内，一个命令也可跨多个包，重传和终端回显更不能重复计数。

| 流中看到的内容 | 推荐统计方式 | 限制 |
| --- | --- | --- |
| `id` 后接换行，再返回 uid 信息 | 一条输入命令，存在对应输出 | 输出可能伪造，结合进程/日志增强可信度 |
| `pwd; whoami` 后接换行 | 一条输入命令行；含两个简单命令 | 报告必须说明按命令行还是按语义统计 |
| 提示符、终端回显、同一 TCP 重传 | 不作为新的输入命令 | 区分双方方向和序列号 |
| 未结束输入、缺失回包 | 不完整输入或提交候选 | 不计为已确认执行成功 |

**示例报告：** “可见三条提交的命令行，其中一条包含两个由分号分隔的简单命令；两条有匹配输出，另一条因抓包结束无法确认结果。”附每条流、输入/输出字节范围、帧号和时间。端点连接、提交内容、结果输出与主机上的 shell/子进程分别是不同证据层级；只有裸 TCP 连接不能证明远程命令执行。

## 10 用统计找调查入口，再建立通信角色

### 10.1 按主机、会话与时间对照统计

端点包数、字节数和会话数回答的是不同问题：包数可能被小包、重传和应答放大；字节数常突出文件传输；会话数可突出扫描、短连接或正常的并发业务。先使用 `统计 → 协议分级 / 端点 / 会话 / I/O 图表`，再回到具体请求与响应。完整的采集校准和证据闭环路线见[网络取证通用流程](/knowledge/forensic-guide-network/)。

```bash
tshark -n -r ./evidence/capture.pcapng -q -z io,phs
tshark -n -r ./evidence/capture.pcapng -q -z endpoints,ip -z conv,tcp -z conv,udp
tshark -n -r ./evidence/capture.pcapng -q -z io,stat,1
```

把“最活跃的地址”标为优先检查对象，再列出它访问的服务、连接方向和各阶段时间。IPv6 用对应端点字段复核；端点统计按整个文件还是按目标时间窗口计算，要在工作表写明。`io,stat,1` 的一秒分桶只显示可见抓包中的量，不能直接换算业务请求次数或链路总负载。

### 10.2 入站利用与主动访问后的感染

| 候选过程 | 优先找的可见链条 | 需要补充的证据 |
| --- | --- | --- |
| 对服务的入站探测或利用 | 多端口探测 → 应用请求 → 对应响应 → 文件/进程变化 | 服务监听配置、访问日志、落地文件与进程 |
| 客户端主动访问后出现异常 | DNS → 页面或文件获取 → 新连接或周期性回连 | 浏览器/下载记录、文件摘要、终端进程与告警 |
| 单端点高流量或大量请求 | 时间峰值、连接完成率、协议类型、源分布 | 业务基线、接口丢包、服务负载与可用性 |

这几种过程可以混在同一文件中。某地址主要出现在 `ip.src`，只能说明它在这些报文里发送数据；下载响应、代理转发和反向连接都能改变方向。地址数量少、两端包量接近，不证明存在“一名攻击者对一台受害主机”；地址包量占比极高，也不能据此确认 DDoS、感染或网关身份。HTTP 请求方/响应方是该会话的协议角色，实际控制者还要结合采集点、NAT、代理和主机记录。

### 10.3 实战：两种异常过程不要合并归因

**场景与材料：** 一份内网镜像 PCAPNG 同时包含客户端访问网页和服务器收到探测的记录；另有同时间的访问日志与终端进程清单。目标是建立行为链，而非挑选包数最高的地址作为攻击者。

1. 在端点和会话表中分别列出客户端访问 Web 服务、服务器接受连接的候选流，并保存实际帧号范围与起止时间。
2. 追踪 HTTP 请求/响应，记录 Host、URI、方法、状态与实体。把“获取到对象”和“访问了页面”分开；对象导出方法见第 12、22 节。
3. 检查对象传输之后是否出现新的 DNS、连接或重复请求；按端点和时间关联下载文件摘要与终端进程。另一条入站探测链单独统计。
4. 对高流量时段检查正常下载、备份、重传及抓包丢失，并用服务负载日志判断是否存在可用性影响。

**判读与验证：** 若文件实体与终端保存文件摘要相同，随后确有对应进程及回连记录，才逐步支持下载、运行与通信链条。只有大流量或周期性请求时，保持“异常会话候选”。镜像口缺少另一侧、地址经过代理或主机时钟不一致时，不把两条链写成同一人的连续操作。

## 11 TCP 状态、端口扫描与计数

### 11.1 正确读取标志与序列号

| 字段 | 含义 | 取证时容易误读的地方 |
| --- | --- | --- |
| SYN | 同步序列号、发起连接协商 | 正常连接同样有 SYN；仅见 SYN 不能确认扫描 |
| ACK | 确认号字段有效 | 不是“应用响应成功”，有数据的段也常带 ACK |
| FIN | 本方向没有更多数据要发送 | 另一方向仍可能发送数据，属于半关闭 |
| RST | 复位或拒绝该连接 | 可能由端点、中间设备或异常状态产生 |
| PSH | 提示尽快把已收到的数据交付应用 | 不是“有数据”的充分或必要条件；载荷看 `tcp.len` |

常规建立过程为 `SYN → SYN/ACK → ACK`。Wireshark 默认可显示相对序列号，界面中的 0 不等于线上初始序列号真的为零。SYN 和 FIN 各占一个序列号；关闭过程可以把 FIN 与 ACK 合在一个段，也可能出现同时关闭或 RST。不要把“必须四个报文”或“握手绝对不携带数据”写成判定条件；[TCP 标准](https://www.rfc-editor.org/rfc/rfc9293.html)允许携带数据的建立过程。

### 11.2 从初始 SYN 到可见端口状态

下面地址只构造演示：假设候选发起端为 `192.0.2.10`，候选服务端为 `192.0.2.20`，请从当前抓包替换。

```bash
# 初始建连请求：列时间、双方端口与流号
tshark -n -r ./evidence/capture.pcapng \
  -Y 'ip.src == 192.0.2.10 && ip.dst == 192.0.2.20 && tcp.flags.syn == 1 && tcp.flags.ack == 0' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e ip.src -e tcp.srcport \
  -e ip.dst -e tcp.dstport -e tcp.stream -e tcp.seq_raw

# 服务端 SYN/ACK：开放候选应统计服务端源端口
tshark -n -r ./evidence/capture.pcapng \
  -Y 'ip.src == 192.0.2.20 && ip.dst == 192.0.2.10 && tcp.flags.syn == 1 && tcp.flags.ack == 1' \
  -T fields -e tcp.srcport | sort -n -u

# 服务端复位：回到同一流检查它响应的是哪个请求
tshark -n -r ./evidence/capture.pcapng \
  -Y 'ip.src == 192.0.2.20 && tcp.flags.reset == 1' \
  -T fields -e frame.number -e tcp.stream -e tcp.srcport -e tcp.dstport
```

SYN/ACK 对应的服务端**源端口**才是本次被探测服务端口；此时目标端口通常是发起端的临时端口。SYN 后收到匹配的 SYN/ACK，可表述为“该路径上端口回应连接建立”；对初始 SYN 返回 RST/ACK，通常支持连接被拒绝。只见超时不区分端口关闭、过滤、丢包和抓包盲区。代理、负载均衡或 SYN 代理回应时，还不能证明后端服务可用。

### 11.3 统计口径与工具标记

短时间探测很多目标端口、连接很短、SYN/ACK 后主动复位、缺少应用交换，可以一起支持端口探测候选。也要排除健康检查、资产巡检和获准扫描。含工具名称的 HTTP User-Agent 只说明报文携带该字符串；某些服务识别探测会有这类头，纯 TCP SYN 扫描没有 HTTP 头，标记还可以被修改。

在报告中分别记录 `目标地址数 / 目标服务端口数 / 初始 SYN 数 / 去重逻辑尝试数 / 完成连接数`。逻辑尝试可用方向明确的五元组、原始 SYN 序列号及时间分组，结合 `tcp.analysis.retransmission` 回看重传；该标记依赖解析器和捕获顺序，不能无条件删除所有标记包。ICMP 仍按第 06 节的请求、标识和序号去重。

**实战：** 对 `./evidence/probe.pcapng` 找到一批初始 SYN 后，把每个请求与同一流的 SYN/ACK、RST 或后续 ACK 关联。若很多端口均以 SYN/ACK 后复位结束且无应用数据，记录“具有半连接探测模式”；若某流继续出现 HTTP 或认证，转入应用分析。核对服务监听配置、巡检计划和防火墙日志；抓包不完整时，开放/拒绝/无可见响应三个集合只能代表该时间与路径，不能列为主机的完整端口清单。[TCP 字段参考](https://www.wireshark.org/docs/dfref/t/tcp.html)可复核所用字段。

## 12 认证、会话令牌与批量尝试

### 12.1 把频率、失败和成功分开证明

批量登录的候选特征包括同一接口高频请求、多个用户名或提交值、相似正文与大量失败结果。脚本、浏览器自动重试、共享出口和健康检查也会形成高频模式。“持续几秒”没有通用阈值；只有 POST 或某条响应更长也不能确认口令被猜中。

| 协议或方式 | 可见字段 | 结果判定与限制 |
| --- | --- | --- |
| HTTP 表单 | 请求实体、接口、Cookie、重定向及正文 | 关联有效会话和受保护动作；200 可以是失败页 |
| HTTP Basic | Authorization 值与关联响应 | Base64 是表示方式；取得提交值不证明服务端接受 |
| FTP | USER/PASS 与响应 | 用控制流的接受/拒绝结果；FTPS 加密后不能直接读取 |
| SMB/NTLM | Session Setup、用户名候选、状态 | 等待最终认证结果；中间挑战不是失败，见第 19 节 |
| SSH | 标识串、建连和密钥交换、加密流量时序 | 正常加密后的用户认证内容不可直接从普通抓包读出 |

SSH 的用户认证运行于加密传输层之上。多次短连接可以支持连接尝试异常，不能从普通密文抓包逐个数出用户名、密码或“认证失败”报文；需要 `/var/log/auth.log`、journal 导出或终端审计记录互证。[SSH 传输协议](https://www.rfc-editor.org/rfc/rfc4253.html)与[用户认证协议](https://www.rfc-editor.org/rfc/rfc4252.html)说明这两层关系。

```bash
tshark -n -2 -r ./evidence/capture.pcapng -Y 'http.request || http.response' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e tcp.stream \
  -e http.request.method -e http.request.uri -e http.response.code \
  -e http.response_in -e http.request_in
rg -n 'Failed password|Invalid user|Accepted password|Accepted publickey' \
  ./evidence/logs/auth.log*
```

HTTP 关联还要考虑同一连接多个请求、代理和截断；日志检索只适用于已有的纯文本导出。认证后还需看角色和授权范围：登录成功不等于具备管理员权限，认证接受也不证明文件或命令操作完成。

### 12.2 令牌猜测与哈希攻击的区别

同一路径反复提交变化的会话 ID、Cookie 或令牌，可以标为令牌枚举或自动化尝试候选；继续检查令牌是否能通过验证、是否访问到受保护资源，并排除正常刷新。JWT 的载荷可解码不等于签名验证通过，更不等于已经劫持会话。报告中的令牌只保存受控证据位置或摘要，避免把完整可用值散布到结论里。

哈希碰撞是两个不同输入产生相同摘要；口令猜测、猜令牌和寻找某个摘要的原像是不同问题。大量相似参数请求不能单独证明在做 MD5/SHA-1 碰撞。只有能够说明应用使用了哪个哈希、输入对是否不同、摘要是否相同以及如何绕过判定，才讨论碰撞；否则记录为参数枚举或认证尝试。

### 12.3 实战：高频失败中找候选成功会话

**材料与证据位置：** `./evidence/login.pcapng`、应用访问日志、认证日志和已有会话记录。只检查这些副本，不重放登录请求。

1. 以登录 URI、客户端方向和时间窗口列请求，把相同提交重试与变化的提交分开计数；计数单位是逻辑请求，不是 TCP 包。
2. 对失败结果记录状态、正文特征和是否产生会话。对长度突变的响应仅设为候选，检查压缩、模板变化和错误堆栈。
3. 沿候选响应中的重定向和会话关联下一次受保护请求，比较用户身份、权限与实际动作，再核对服务器接受认证日志。
4. SSH 部分以流和建连时间关联日志，不把包长拟合成密码尝试次数。

**示例判读：** 某批请求都返回登录页面，随后一条响应设置会话且同一会话访问用户设置页；认证日志对应记录接受事件。可以支持该会话认证成功，仍不能把前面的提交序列直接当成成功口令来源。日志缺失、Cookie 被重用或共享出口存在时，写清行为与人员归因的不同可信度。

## 13 用 NBNS、DHCP 与 User-Agent 关联设备

### 13.1 名称、租约与客户端声明

NBNS 是 NetBIOS 名称服务，服务于名称注册、查询及名称到地址的映射；WINS 是相关服务实现，不应把 NBNS 简化为“动态 DNS”。抓包里的名称、后缀、应答地址和查询/注册方向支持某一时间的网络名称线索，仍需与租约及主机记录核对。[NetBIOS over TCP/IP 标准](https://www.rfc-editor.org/rfc/rfc1001.html)与[NBNS 字段参考](https://www.wireshark.org/docs/dfref/n/nbns.html)可用于复核。

DHCP 重点串起事务 ID、客户端硬件地址/Client Identifier、Host Name、请求地址、服务器标识、ACK 中的地址和租约。DHCP 发包源 IP 可能为 `0.0.0.0`，广播或中继还会改变 IP/MAC 观察关系，所以不能只用 `ip.src` 识别租约拥有者。主机名可以改写，客户端 ID 与 MAC 也不能独立确定自然人。[DHCP 标准](https://www.rfc-editor.org/rfc/rfc2131.html)说明地址分配过程。

```bash
tshark -n -r ./evidence/capture.pcapng -Y 'nbns' -V
tshark -n -r ./evidence/capture.pcapng -Y 'dhcp' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e dhcp.id -e dhcp.hw.mac_addr \
  -e dhcp.option.hostname -e dhcp.option.dhcp -e dhcp.ip.your \
  -e dhcp.option.dhcp_server_id
tshark -n -r ./evidence/capture.pcapng -Y 'http.request' \
  -T fields -e frame.number -e ip.src -e http.host -e http.user_agent
```

现代 Wireshark 使用 `dhcp`；旧环境中可能出现 BOOTP 的协议或字段名，需以实际版本字段表为准。`dhcp.ip.your` 只是报文字段，Offer 不是最终完成租约；回到 ACK 和后续地址使用再确认。[DHCP 字段参考](https://www.wireshark.org/docs/dfref/d/dhcp.html)列出上述字段与支持版本。

### 13.2 User-Agent 只反映声明

User-Agent 中的系统、架构、浏览器字符串可以辅助比较同一会话，但可以被修改、兼容性伪装或减少信息。历史字符串 `Windows NT 5.1 / 6.0 / 6.1 / 6.2 / 6.3` 分别常见于 XP / Vista / 7 / 8 / 8.1；`Windows NT 10.0` 也不能区分 Windows 10 与 Windows 11。[Microsoft 的 User-Agent 说明](https://learn.microsoft.com/en-us/microsoft-edge/web-platform/user-agent-guidance)明确这类兼容性限制。`Win64; x64` 是客户端声明，不能证明物理 CPU 型号。工具名称、看似平板的主机名、过旧浏览器版本都属于候选，不当作设备身份或工具版本的确定证据。

### 13.3 实战：某个时间段的地址由哪台设备使用

**场景与材料：** 局域网 PCAPNG、DHCP 租约日志、交换机或无线关联记录、终端清单副本。怀疑一个内网地址在某时段发起了异常 HTTP 请求。

1. 从异常请求的时间与地址开始，查覆盖该时段的 DHCP 事务，配对 Request/ACK，记录实际客户端标识和分配地址。
2. 比较 NBNS 名称与 DHCP Host Name；两者不同也保留，不用一个名字覆盖另一个。
3. 关联后续 ARP/链路层地址、交换机端口或无线关联记录，再用终端清单确认设备。采集点位于路由器之后时，链路层地址可能只是下一跳。
4. 将 User-Agent 作为一致性检查；若声明明显冲突，考虑代理、地址重用、多用户或手工伪装，再看实际日志。

**判读与限制：** 名称、租约与接入记录在时间上吻合，可以支持“该租约/设备当时使用了此地址”。只能看到请求里的设备名称时，结论停留于声明。静态地址、租约过期、MAC 变化、广播盲区和共享设备都会削弱关联；网络身份、账号身份与操作者身份分别记录。

## 14 Kerberos：从票据交换到服务使用

### 14.1 三段交换与密钥层次

Kerberos 是票据认证协议；LDAP 可以提供目录查询，二者不能互换。票据不包含可直接读取的“加密密码”。按报文消息类型、Realm、客户端名、服务名、加密类型和错误码恢复过程；不同字段同叫 `enc-part`，不代表同一密钥或同一内容。

| 阶段 | 可见交换 | 应区分的密钥与取证含义 |
| --- | --- | --- |
| AS | AS-REQ / AS-REP，可能先收到要求预认证的错误 | 加密时间戳用客户端长期密钥；TGT 由 TGS 的长期密钥保护，客户端获得客户端—TGS 会话密钥 |
| TGS | TGS-REQ 携带 TGT 与认证器，TGS-REP 返回服务票据 | 认证器使用 TGT 会话密钥；返回部分使用该密钥或认证器子密钥，服务票据包含客户端—服务会话密钥 |
| AP | AP-REQ 携带服务票据和新的认证器；要求相互认证时有 AP-REP | 服务通常用自身长期密钥验证票据，再用对应服务会话密钥验证认证器；后续还可能协商子密钥 |

因此 AS 阶段与服务阶段不能统一写成“始终使用同一个 Session key”。长期密钥也不总等同于 NT 哈希：派生方式依加密类型而变。`PA-ENC-TIMESTAMP` 中是客户端时间及可选微秒值，用于预认证；随机 nonce 是另一字段。初次 `PREAUTH_REQUIRED` 可能只是正常协商，不自动归类为密码错误。上述关系见[Kerberos V5 标准](https://www.rfc-editor.org/rfc/rfc4120.html)。

### 14.2 读取报文与判断认证边界

```bash
tshark -n -r ./evidence/capture.pcapng -Y 'kerberos' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e ip.src -e ip.dst \
  -e kerberos.msg_type -e kerberos.CNameString -e kerberos.SNameString \
  -e kerberos.realm -e kerberos.etype -e kerberos.error_code
```

常用消息类型是 `10/11`（AS-REQ/REP）、`12/13`（TGS-REQ/REP）、`14/15`（AP-REQ/REP）与 `30`（错误）；字段重复出现时，先用完整树 `-V` 分清请求主体、票据和嵌套认证器。[Wireshark Kerberos 字段参考](https://www.wireshark.org/docs/dfref/k/kerberos.html)可核对大小写与版本。

AS-REP 支持 KDC 颁发了相应凭据，TGS-REP 支持服务票据颁发；这还不是服务端已经接受访问，更不能证明文件读写成功。票据可缓存或在抓包开始前取得，缺少 AS/TGS 不说明认证链不存在。LDAP 查询不能替代 AP/服务层成功证据。Windows 环境的 PAC 承载授权信息，是否存在、如何校验以及如何结合 ACL 是实现与场景相关的问题；请求不包含 PAC、获得票据或验证身份，都不等于已绕过服务授权。

### 14.3 实战：票据已经颁发，文件访问是否完成

**材料与位置：** `./evidence/domain.pcapng`、域控认证事件导出、文件服务器安全/共享审计记录。构造目标是核对一个账号候选访问共享的过程，不进行在线认证或离线口令破解。

1. 以请求时间、Realm、账号候选和服务主体列 AS/TGS 交换，记录预认证要求、实际错误或返回票据，不把挑战算成失败登录。
2. 追踪目标服务连接中的 AP/SPNEGO 及 SMB Session Setup；票据服务名与网络目的端点不一致时，检查别名、代理和服务配置。
3. 用 SMB 会话、共享路径及文件请求核对是否进入共享，按第 19 节比较认证状态、Tree Connect 与文件操作结果。
4. 关联域控票据事件和服务器文件审计，保留实际事件号、账号、服务主体、时间和请求对象。

**判读与验证：** 看见服务票据但 SMB 返回拒绝访问，应分别记录“票据已发”和“此操作被拒绝”。若最终会话接受、文件操作成功，且与服务器的审计记录相互印证，才支持具体资源访问。加密字段不能用可见主体名补成明文内容；共用账号、票据转交和时间偏差仍限制人员归因。

## 15 SMB/NTLM：身份验证、共享与文件动作

### 15.1 协商、会话和共享是不同阶段

SMB 用于文件、打印及命名管道等共享通信，看到 SMB 不等于连接打印机。分析顺序通常是传输连接 → Negotiate → Session Setup → Tree Connect → Create/Read/Write/Close 等动作，实际会话可能复用、重连或使用多个通道。

Negotiate 请求中的 dialect 列表是客户端提供的候选，响应中的 selected dialect 才是本次选中的版本。请求列出 SMB 2.1 和 SMB 3.x 不能写成“双方已使用 SMB 2.1”；要核对服务端响应，再继续分析该方言的签名、加密与认证。不要把旧 SMB1 的协商、SMB2 的命令和 SMB3 的加密外框混成一套字段。

| 阶段 | 重点字段与结果 | 不应直接推出的结论 |
| --- | --- | --- |
| Negotiate | 实际方言、签名/加密能力、服务器信息 | 不是用户认证完成；协商报文不能直接提供可用会话密钥 |
| Session Setup | SPNEGO 中的 Kerberos/NTLM、最终状态、Session ID、Guest/Null 标记 | 不能把任意 STATUS_SUCCESS 当成登录成功 |
| Tree Connect | 请求共享路径、返回 Tree ID、共享类型和状态 | 不一定是目录枚举，也不自动证明打印或文件读取 |
| 文件/管道动作 | Message ID、File ID、偏移、长度、状态及返回内容 | 请求提交不等于服务端完成，完成也不等于落地后执行 |

NTLM 连接认证常有 `NEGOTIATE → CHALLENGE → AUTHENTICATE`。Server Challenge 是 **8 字节/64 位**；应答是算法计算出的认证响应，不是抓包中直接得到的明文口令或原始 NT 哈希。NTLMv1/v2 的计算不同，不能统一简化为“哈希加挑战后加密”；工具记录中的 NetNTLMv1/NetNTLMv2 挑战响应也不能直接当作 NT 哈希使用。[Microsoft NTLM 报文规范](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nlmp/801a4681-8809-4be9-ab0d-61dcfe762786)明确挑战长度。

### 15.2 状态必须绑定具体命令与响应

```bash
tshark -n -2 -r ./evidence/capture.pcapng -Y 'smb2 || ntlmssp' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e tcp.stream \
  -e smb2.cmd -e smb2.msg_id -e smb2.sesid -e smb2.tid \
  -e smb2.nt_status -e ntlmssp.auth.domain -e ntlmssp.auth.username

# Session Setup 的成功响应候选
tshark -n -r ./evidence/capture.pcapng \
  -Y 'smb2.cmd == 1 && smb2.flags.response == 1 && smb2.nt_status == 0' -V
```

`STATUS_MORE_PROCESSING_REQUIRED` 常表示还需继续认证交换；不是最终失败。最终 Session Setup 的 `STATUS_SUCCESS` 支持会话接受，再检查 Guest/Null 及用户信息；`STATUS_LOGON_FAILURE` 是认证失败线索，不能直接推出输入了哪个错误口令。其他命令的成功状态只回答该命令结果。响应以 Message ID、Session ID、流与时间配对，复合请求还要看每个子命令。[SMB2 字段参考](https://www.wireshark.org/docs/dfref/s/smb2.html)、[NTLMSSP 字段参考](https://www.wireshark.org/docs/dfref/n/ntlmssp.html)与[微软 Session Setup 处理规范](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-smb2/e545352b-9f2b-4c5e-9350-db46e4f6755e)可复核这些状态。

### 15.3 实战：认证成功后是否上传了同一文件

**场景与材料：** 取得 PCAPNG、共享访问审计和文件系统副本，怀疑某个会话写入文档。

1. 找到最终 Session Setup 响应，保存认证机制、账号候选、Session ID 和状态。匿名/Guest 成功与实名成功分别记录。
2. 追踪同一会话的 Tree Connect，记录共享路径和 Tree ID；再用 Create 的 File ID 连接 Write、偏移、长度与 Close，不跨文件拼接。
3. 文件导出可先查询 `tshark --export-objects help` 的支持协议；若支持 SMB，用对象导出再核对实际生成件。导出失败或只得到片段时，保留相关请求、数据范围和错误，不把界面出现文件名当成完整恢复。
4. 核对服务器审计、文件长度与摘要；同名文件多版本分别保存，重传和覆盖写不重复追加。

**判读与限制：** 会话认证成功、共享连接成功、写请求成功是三个层级。完整重组件与服务器文件摘要一致，才支持同一内容写入；后续执行另查进程与日志。签名保证相关完整性，不等同于加密；SMB3 加密内容没有对应会话密钥时不可直接恢复正文，用户名或共享元数据也不能补出文件字节。

## 16 WebShell 通信的静态复核

### 16.1 一句话入口与编码不等于家族结论

服务端脚本若把 HTTP 参数交给动态执行函数，可以形成短小的远程代码入口。取证时先读参数来源、解码函数、执行点和响应构造，记录脚本路径及摘要；代码短或带错误抑制符并不自动意味着隐蔽性强。不要将提取出的正文交给 `eval`、解释器、编译器或客户端运行。

菜刀与蚁剑常见候选包括代码片段、参数编码、目录/操作系统/用户查询及响应分隔标记。旧菜刀版本之间的固定模板、蚁剑某版本的 User-Agent 或初始化代码，都可能随编码器和定制改变。静态重组后应检查完整结构，不能只命中一个字符串。具体家族候选见第 07 节。

### 16.2 按传输层次逐层拆解

推荐保存 `原抓包 → 单条请求/响应实体 → 传输解码件 → 参数值 → 解码/解密件`，每一步计算摘要并记录转换方式。HTTP 分块、压缩和字符编码先处理，再按实际 `Content-Type` 解析表单；URL 解码、Base64、ROT13、字符构造、XOR 和 AES 是不同层，不可以乱序或反复试到“像文本”为止。

| 候选表达 | 静态检查方法 | 边界 |
| --- | --- | --- |
| URL 编码的表单 | 先按表单规则拆参数，再解码该值 | `+` 在表单里可能表示空格；不要先解码整条正文再拆 `&` |
| Base64 | 检查字母表、填充、解码错误与输出结构 | 不是加密；Base64 字符串不一定是脚本 |
| ROT13 | 只对确认是这一层的字母变换 | 数字、标点和字节对象不因此恢复 |
| `chr(...)` / 十六进制字符构造 | 仅提取允许的整数并转换字符，保留拼接顺序 | 不执行外围 PHP 或混入的表达式；十进制、十六进制按实际前缀区分 |
| XOR/Base64 | 按服务端代码确定密钥字节、下标、偏移与外层编码 | 常见下标有偏移，不能只套 `i % 16` |
| AES | 核对密钥来源、字符/字节表示、模式、IV、填充和语言实现 | 密钥长度和密文块对齐只是格式检查，不能证明解密正确 |

从表单文本中取出参数并只做表示转换，可用下面的独立演示。`payload.txt` 是已分离出的单个字段，不是整条 HTTP 流；选项按实证确定，不逐项自动执行。

```bash
# URL/form 表示层：只处理已有字段，输出副本
python3 - <<'PY'
from pathlib import Path
from urllib.parse import unquote_to_bytes
text = Path('./work/payload.txt').read_text(encoding='ascii').rstrip('\r\n')
Path('./work/payload-url.bin').write_bytes(unquote_to_bytes(text.replace('+', ' ')))
PY

# 对确认有一层 Base64 的字段做严格解码
python3 - <<'PY'
import base64
from pathlib import Path
data = Path('./work/payload-url.bin').read_bytes()
Path('./work/payload-decoded.bin').write_bytes(base64.b64decode(data, validate=True))
PY
sha256sum ./work/payload*.bin
file ./work/payload-decoded.bin
xxd -l 64 ./work/payload-decoded.bin
```

先在副本中处理换行等已确认的外层格式；严格解码失败时检查截断、URL 转换或编码变体，不忽略错误后直接宣称得到完整载荷。对 CHR/CHR16，先完整核对数字记法与可允许语法，不能把相同示例误当成两种编码已经验证。

### 16.3 冰蝎的协商、静态密钥与版本限制

某些早期实现先以 GET/POST 获取一个短密钥并存入服务端 Session，之后发送加密载荷；其他实现从连接配置派生或直接嵌入密钥，不再经过相同协商。区分初次握手、载荷加载、后续功能调用与返回：一条 16 字节响应只有在脚本代码、会话与解密结果一致时，才支持它是相应密钥。

在服务端副本中核对是否使用 MD5 摘要的一部分作为字符串密钥、AES 或其他变换，以及 Session/Cookie 的关联；“前 16 个十六进制字符”是 16 字节 ASCII 表示，与“16 字节原始 MD5 摘要”不同。Java/PHP/ASP 等实现可有不同封装。`Accept`、User-Agent、Keep-Alive、`application/octet-stream`、固定长度或临时源端口都只能帮助挑候选；`application/octet-stream` 表示通用二进制实体，不限制内部只能包含一个文件或一个参数。2/3/4 的版本名称不能替代实际实现校验，端口递增也可能只是操作系统临时端口分配。

脚本里写明 16 字符密钥、AES-128-CBC、16 字节全 0 的 IV 时，请求先做 Base64，再按这些参数解密。响应若是 JSON，字段里可能还要再解一层 Base64。密钥和层数以该脚本为准。流量按阶段取字段：捕获属性、被扫描的一方、扫描工具、登录成功的那一次、向外拉取的文件、上传和上线后的回显。`capinfos` 里的“分:秒”换成秒是分乘 60 再加秒。User-Agent 里的工具名只属于出现它的那一段。同一路径上，口令不再更换且下一次变成读取受保护页面的那次提交，才是登录口令。受害机主动下载时用它的地址作源地址过滤；扩展名和正文分开看。上传端口抄服务器接收该文件的目的端口。多次上传只有一次成功时，对齐请求，找出唯一改动并且被接受的头部。服务端临时路径从成功响应正文抄。

### 16.4 哥斯拉的加载阶段和编码变体

按已取得的服务端代码识别 `PHP_XOR_BASE64 / PHP_EVAL_XOR_BASE64 / PHP_XOR_RAW` 等候选实现。BASE64 变体可能是 XOR 后 Base64，再由表单进行 URL 编码；RAW 变体直接传二进制。EVAL 变体可能把相对固定的加载代码和变化的功能参数放在不同字段；字段名与连接配置相关，不预设固定密码或密钥。

同一个变换函数可用来做 XOR 加/解，但下标偏移、输入起点、密钥字符表示和请求/响应外框必须按代码复核。区分首次把模块放入 Session、检查/建立状态、后续调用和输出；不能预设总有三个 POST。某些响应在密文两端加分隔标记，另一些直接返回原始字节；同样要按实现切片。解码出文件、数据库、截图、浏览器凭据读取、压缩或内存模块等操作名，只证明载荷表达了该功能请求，实际影响仍需文件、数据库、进程或内存证据。

样本把密文夹在两段标记之间，并写明 Base64、循环异或和压缩的顺序时，标记和密钥从该样本抄，解密按相反顺序做。压缩层是 zlib 还是原始 deflate，以解压是否成功为准，两种都试过仍失败就回到脚本核对。

### 16.5 实战：解码后仍要验证行为

**材料与位置：** `./evidence/web.pcapng`、Web 日志、服务器可疑脚本的只读副本和相关落地文件。分析目标是解释已发生的通信，不建立控制连接。

1. 按脚本 URI、HTTP 流、时间、Cookie 与服务日志定位候选请求；保存请求和对应响应，区分加载包与功能包。
2. 在脚本副本中寻找参数名、解码/解密顺序、密钥构造与返回标记，写成逐层处理表；脚本摘要与导出件分别记录。
3. 对单字段静态转换，核对输出的格式、字段结构及同会话多个包的一致性。有 AES 时，不以“填充没报错”独立判断密钥正确。
4. 若输出指向目录查询、文件读取、命令或模块加载，保存输入与对应输出位置，再关联主机文件摘要、进程/审计和数据库操作。

**判读与限制：** 有对应脚本且多条解码结果结构一致，可以支持通信机制识别；要命名家族或版本，还需对应实现特征。只有弱头部或缺少关键层时，记录“疑似加密控制流量”。HTTPS 需要先满足第 22 节的 TLS 条件；WebShell 自身加密是另一层，即便 TLS 解开也不自动得到命令。内存组件未取得时，网络请求不能独立证明其已经加载。

## 17 漏洞流量与主机证据互证

### 17.1 Shiro rememberMe：框架线索、处理错误和成功行为

历史 CVE-2016-4437 涉及 Apache Shiro 1.2.5 之前、未正确配置 rememberMe 加密密钥的场景；不能把所有版本和所有长 Cookie 都纳入相同结论。应取得该部署的依赖版本、rememberMe 管理器与密钥配置、Cookie 处理路径及请求/响应。[Apache 安全公告](https://shiro.apache.org/security-reports.html)说明历史受影响条件。

```bash
tshark -n -r ./evidence/capture.pcapng \
  -Y 'http.cookie contains "rememberMe" || http.set_cookie contains "rememberMe"' \
  -T fields -e frame.number -e tcp.stream -e http.request.uri -e http.response.code
rg -n 'rememberMe|CookieRememberMeManager|cipherKey' ./evidence/app-config
```

`rememberMe=deleteMe` 搭配过期/Max-Age 等字段可表明服务端清除 Cookie；Shiro 官方实现也使用这类清除逻辑，但字符串能够由其他程序产生。它不能“百分百确认 Shiro”，也不固定对应密码错误；登录、退出、无效 remembered identity 或配置改变都可能影响清除行为。[SimpleCookie 实现](https://shiro.apache.org/static/2.0.0/shiro-web/xref/org/apache/shiro/web/servlet/SimpleCookie.html)可复核删除动作。

长 Cookie、200、响应中的特殊符号或 Base64 字节都只是入口。逐条核对实际 Cookie、解码/解密条件、反序列化路径和异常日志；不把可疑字节送入 Java 反序列化器。认证会话、remembered identity 与应用授权分别验证，Cookie 的 Domain/Path 也决定浏览器在哪些请求发送它，不能写成“登录后所有网站都会携带”。命令执行需输出与进程/审计互证；内存马需补充运行时类、Servlet/Filter/Listener 或内存记录，不能仅凭长 Cookie 或几个返回符号确认。

**实战：** 对同一路径重复出现的 rememberMe 请求，先建立“提交值摘要—响应清除动作—日志错误”表，再以依赖版本和处理配置判断是否具有对应风险；如果只有 200 与清除 Cookie，结论是可疑处理/探测候选。若日志和终端证据确认子进程，还要解释它与哪次请求在时间、进程父子关系和输出上关联，而非用状态码替代执行证明。

### 17.2 PwnKit：网络可见操作不等于本地提权完成

CVE-2021-4034 是 polkit 的 `pkexec` 本地权限提升问题，前提涉及本地执行与受影响组件；普通网络包本身不承载一个可确认成功的“PwnKit 协议”。网络里看到扫描脚本或利用文件上传、模块名称、交互输出，只支持提交/传输/声称结果的线索。[厂商公告](https://access.redhat.com/security/vulnerabilities/RHSB-2022-001)说明本地权限提升性质。

**材料与操作：** 使用已有网络副本、上传文件、软件包版本清单、`audit.log` 与进程记录；对文件仅计算摘要并读静态结构，不上传、执行扫描脚本或运行提权模块。

```bash
sha256sum ./evidence/uploads/*
rg -n 'pkexec|polkit|euid=0|uid=0' ./evidence/logs ./evidence/package-list.txt
```

将“文件传入 → 进程启动 → 权限状态变化 → 后续操作”逐步对应。版本号要结合发行版补丁和回补，扫描器提示不是漏洞确认；命令输出里出现 root 也可能来自普通授权操作或伪造回显。UID/EUID、原始身份、父子进程、审计与文件变化吻合后，才讨论权限改变及原因。缺主机侧证据时，只报告传输或候选尝试；日志缺失也不反证未发生。

### 17.3 Dify：数据库访问、上传元数据与文件读取链

自托管应用中的 PostgreSQL、Redis 和上传服务应分别分析；管理台密码、数据库凭据、缓存凭据及模型 API 密钥是不同身份。实际版本、环境配置、容器网络和端口映射决定访问条件，不预设某一固定密码、数据库必然暴露或缓存和数据库共用凭据。[Dify 部署配置](https://github.com/langgenius/dify-docs/blob/main/en/self-host/deploy/configuration/environments.mdx)说明配置项和存储后端差异。

上传记录中的 `upload_files.key` 应结合 `storage_type`、存储根、对象存储后端及具体版本代码解释；它可能是对象键或相对存储定位值，不必然是绝对路径。只有数据库记录被改变，不足以证明文件已经被读出；应串起权限、元数据变化、加载路径和响应实体。

**独立场景与材料：** 有一份应用 PCAPNG、访问日志、数据库审计导出、配置快照、上传记录和存储目录副本。某个上传记录变化后出现工作流处理请求，需要判断是否访问了上传范围之外的内容。

1. 从既有数据库连接的认证与查询记录、应用账号和管理请求中确定可见权限；若使用 TLS，抓包只能提供元数据，需靠已有数据库/应用日志补充。
2. 对比同一上传 ID 的租户、创建者、存储类型、key、大小与时间。`rg -n 'upload_files|storage_type|STORAGE_TYPE|OPENDAL_FS_ROOT' ./evidence/app-config ./evidence/db-export` 只用于已有文本副本，不向数据库提交更新。
3. 沿上传 ID 查应用读取/预览/工作流日志及对应 HTTP 响应；静态检查该版本代码如何把 key 传给存储后端，以及目录、租户、文件权限校验在哪里发生。
4. 对已导出的响应实体计算摘要，与合法取得的目标文件副本比较。错误堆栈、文件路径字符串或 HTTP 200，均不能替代具体内容的证据。

**判读与验证：** 若元数据变化、应用读取记录、越出预期存储边界的解析路径以及响应字节相互印证，可以支持该部署的一次越界读取。缺少版本、代码或内容一致性时，仅记录异常元数据与请求候选；不泛称所有 Dify 都有同一漏洞。连接大模型或配置 API 密钥不是证明本地文件读取成功的必要环节，离线复核不需要重放请求、修改数据库或连接外部模型。

## 18 显示过滤、内容导出与解密边界

### 18.1 显示过滤速查与字段可用性

显示过滤用于已有报文，捕获过滤用于决定采集什么，两者语法不同。例如 `ip.addr == 192.0.2.10` 是显示过滤，`host 192.0.2.10` 是捕获过滤；不能把后者直接当成显示表达式。分析前记录工具版本，用字段表确认当前环境的名称，不从缺失字段推断协议未出现。

```bash
tshark --version
tshark -G fields | rg 'tcp.flags.syn|http.response_in|dhcp.option.hostname|kerberos.msg_type|smb2.nt_status'
```

| 调查目标 | Wireshark 显示过滤示例 | 读到什么与没读到什么 |
| --- | --- | --- |
| 地址与单条流 | `ip.addr == 192.0.2.10`；`tcp.stream == 42` | 示例地址/流号替换后定位双向会话；IPv6 另看 `ipv6.addr` |
| 初始建连与应答 | `tcp.flags.syn == 1 && tcp.flags.ack == 0`；`tcp.flags.syn == 1 && tcp.flags.ack == 1` | 正常建连和扫描都会命中，要配对与统计 |
| 载荷和复位 | `tcp.len > 0`；`tcp.flags.reset == 1` | 数据长度或复位，不是应用成功标志 |
| TCP 异常候选 | `tcp.analysis.retransmission || tcp.analysis.lost_segment` | 分析器推断，需检查采集点、序列号与截断 |
| HTTP 请求/响应 | `http.request`；`http.response`；`http.response.code == 401` | HTTP/1.x 解析后的字段，不能直接套在密文或其他 HTTP 版本 |
| 字符串入口 | `http contains "rememberMe"`；`http.user_agent contains "Nmap"` | 可见字节/字段命中，编码与分层可造成漏报，字符串可伪造 |
| DNS 查询/成功状态 | `dns.flags.response == 0`；`dns.flags.rcode == 0` | 查询或 NoError，不能证明地址正确、实际访问或返回了 A 记录 |
| 设备声明 | `nbns`；`dhcp`；`http.user_agent` | 名称、租约或客户端声明，需按时间互证 |
| 认证/共享 | `kerberos`；`ntlmssp`；`smb2` | 协议交换，后续授权与资源动作另判 |
| 传文件 | `ftp`；`ftp-data` | 控制与数据分别处理，方向由命令和协商决定 |
| TLS / RDP | `tls`；`rdp`；`tcp.port == 3389` | 协议候选或端口候选，端口不能独立确定协议和加密内容 |

`contains` 检查相应解析层或字段的可见字节，不等于对所有流量完成解码后的全文检索。遇到非标准端口，用 Decode As 的依据是报文结构与已知服务配置；保存变更，不强行把未知数据解成想看的协议。新版 Wireshark 使用 `tls`；旧 `ssl` 名称和旧 BOOTP 字段需要按版本调整。[TShark 手册](https://www.wireshark.org/docs/man-pages/tshark.html)说明过滤、字段输出与统计选项。

### 18.2 Follow Stream 与 Export Objects 的层次

| 输出 | 保存内容 | 适合用途与限制 |
| --- | --- | --- |
| Follow TCP / Raw / 单一方向 / Save As | 重组的该方向 TCP 应用字节 | 如 FTP 数据流；HTTP 仍可能含协议头和传输编码 |
| Follow TLS | 已成功解密的 TLS 应用数据 | 需要对应秘密与足够报文；不是证书导出 |
| Follow HTTP/HTTP2 | 对应协议解释后的交互；HTTP/2 还需选子流 | 避免把同连接中其他请求混入对象 |
| Export Objects | 解析器识别并重组的协议对象 | 不保证对象完整，也不等于在终端已保存或执行 |
| `tshark -z follow,...` | 带说明、端点和方向格式的报告 | Raw 模式也不能把整个报告直接改名作二进制文件 |

Wireshark Follow Stream 的 Raw 显示为十六进制，但在选定方向后 `Save As` 保存无额外行分隔的二进制；默认是双向会话，保存文件前务必选传数据的一方。TShark 统计输出与该 GUI 保存行为不同。[Follow Stream 文档](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvFollowStreamSection.html)和[对象导出文档](https://www.wireshark.org/docs/wsug_html_chunked/ChIOExportSection.html)说明这些区别。

```bash
tshark --export-objects help
mkdir -p ./work/http-objects
tshark -n -r ./evidence/capture.pcapng --export-objects http,./work/http-objects
tshark -n -r ./evidence/capture.pcapng -q -z 'follow,tcp,ascii,42'
sha256sum ./work/http-objects/*
```

导出目录先保持空或为每次处理建独立目录，防止自动改名后混淆对象。对每件记录协议、流/子流、方向、帧号范围、原文件名、实体长度与摘要；再做格式解析和主机侧核验。对象导出可能处理分块/重组等层次，不能拿输出长度与所有网络包长度直接等同。需恢复裸二进制时，按第 12 节单向 Raw 流程操作。

### 18.3 TLS 的证书、RSA 私钥和会话秘密

证书的公钥和签名不能直接解密流量；服务器证书使用 RSA 也不代表握手采用 RSA 密钥交换。RSA 私钥解密仅适用于匹配服务器证书、非 (EC)DHE 的旧式 RSA 密钥交换，并需相关完整握手；恢复会话及 TLS 1.3 不适用这种办法。ECDHE 的临时共享秘密不能从长期证书私钥和抓包直接推导。

对应连接的 key log 包含会话秘密，可用于 TLS 1.2 的 (EC)DHE 或 TLS 1.3 等场景，但仍需匹配会话、秘密类型和足够的握手/记录。事后设置环境变量不能补回历史连接的秘密；应用是否支持导出、握手是否缺失以及重组是否完整，都影响结果。`Export TLS Session Keys` 只导出解析器已经知道的秘密，不从密文自动破解。[Wireshark TLS 解密说明](https://wiki.wireshark.org/TLS)列出条件。

对已取得且与检材对应的 key log 可作离线验证：

```bash
tshark -n -2 -r ./evidence/capture.pcapng \
  -o tls.keylog_file:./evidence/tls-keys.log \
  -Y 'http || http2' -V
```

**结果验证：** 解密后实际出现合理的应用结构，还要核对端点、请求/响应关联和原始帧位置；成功加载 key log 文件不是解密成功证明。仍只有 TLS 记录时，检查匹配、握手、TCP 缺口与应用解析，不臆测明文。秘密文件与包含 Decryption Secrets Block 的 PCAPNG 都能暴露相应内容，工作记录只引用受控位置。

### 18.4 RDP 是加密边界检查的实例

对 RDP 候选先核对协商、安全协议和相关 TLS 会话；`3389` 是端口线索，不独立证明远程桌面登录成功。RDP 可使用标准安全机制或 TLS/CredSSP 等增强安全机制，NLA 与图形会话阶段不同；只有 TLS 证书、账号口令或服务器 RSA 证书私钥不自动满足所有解密条件。[Microsoft RDP 安全规范](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpbcgr/422e59a0-98c8-4a28-af9f-235a572b6e4d)与[RDP 字段表](https://www.wireshark.org/docs/dfref/r/rdp.html)可用于核对。

**独立场景：** 已取得远程连接 PCAPNG、对应会话秘密及 Windows 远程会话事件导出。先列 `rdp || tls || tcp.port == 3389` 候选，回到实际流检查协商协议和 TLS 解密条件；再核对认证、会话建立和主机事件。即使成功解析一层，也要确认当前工具支持相应图形、输入或虚拟通道解析。未取得可用秘密时，仅报告可见建连、协商和时序；不从密文恢复桌面截图或宣称看见用户键入的内容。
