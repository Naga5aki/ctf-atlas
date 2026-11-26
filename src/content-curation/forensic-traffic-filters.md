实战时从右侧目录按协议跳转。过滤式写在表格里，整格复制到 Wireshark 过滤栏。命中表示这一帧里有这个字段；请求和应答再用同一个 `tcp.stream`、事务号或命令帧配成一对。

示例地址 `192.0.2.10` 表示要查的主机，`198.51.100.20` 表示外部地址，换成会话统计里的真实值。字段名按 Wireshark 4.6 的协议字段表复核。过滤栏变红时，点开包详情里的那一行，用状态栏给出的名字替换。

采集范围、对象导出和 TLS 密钥条件见 [PCAP 流量与协议证据链](/knowledge/forensic-network-traffic/)。从统计落到会话的顺序见 [网络取证：从抓包到可验证的通信过程](/knowledge/forensic-guide-network/)。

## 01 把过滤式写进对的栏

已经打开的文件用显示过滤，写在主窗口上方，也就是 `tshark -Y`。捕获过滤只在开始抓包前生效，写在捕获选项或 `-f`。`ip.addr == 192.0.2.10` 是显示过滤，`host 192.0.2.10` 是捕获过滤。

过滤栏绿色表示当前语法可以编译，红色表示写错，黄色表示旧字段仍能用。字段名区分大小写，`kerberos.CNameString` 里的大写要保留。

| 过滤式 | 读到哪里 |
| --- | --- |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0` | 纯 SYN。单独写 `tcp.flags.syn` 会留下全部 TCP，这个字段在值为 0 时也存在 |
| `ip.addr == 192.0.2.10 && ip.addr == 198.51.100.20` | 两个地址都出现的包，方向对调同样留下 |
| `!(ip.addr == 192.0.2.10)` | 去掉带这个地址的 IP 包，ARP 等非 IP 帧还在列表里 |
| `all tcp.port > 1024` | 源端口和目的端口都大于 1024。不写 `all` 时，只要其中一端是高端口就会命中 |
| `tcp.port in {80, 443, 8080, 8000..8010}` | 端口集合。区间写在 `in` 里，比较落在同一个端口上 |
| `lower(http.host) contains "example.com"` | 主机名忽略大小写。`==` 和 `contains` 区分大小写 |
| `http.host matches r"login\.example\.com"` | 正则。`r"..."` 把点号和反斜杠按字面处理；`matches` 默认忽略大小写 |

`http.response_in` 这类指向另一帧的字段，在 `tshark` 里要加 `-2` 做两遍解析。导出命令加上 `-n`，结果里的地址保持抓包中的写法。

## 02 帧

先确认这份文件盖住了要看的时间段，以及后面缺字段是不是因为抓短了。

| 过滤式 | 读到哪里 |
| --- | --- |
| `frame.time >= "2026-10-15 15:00:00" && frame.time < "2026-10-15 16:00:00"` | 限定到这一小时。不写时区时按分析机的本地时区解释 |
| `frame.cap_len < frame.len` | 捕获长度短于线上长度，这一帧被截短。证书、文件头、SQL 缺尾时先回到这里 |
| `frame.protocols contains "http"` | 协议栈里已经解出 HTTP。密文流量的协议列里是 `tls` |
| `frame contains "example.com"` | 在捕获到的原始字节里找这段 ASCII，以太网头和 IP 头也会被搜到 |
| `_ws.col.Info contains "POST"` | 用信息列做第一轮筛选，再改到 `http.request.method` 上复核 |

```bash
tshark -n -r ./evidence/capture.pcapng -q -z io,phs
tshark -n -r ./evidence/capture.pcapng -q -z conv,tcp
```

第一条按协议分层计数，用来决定先开 DNS、HTTP 还是 TLS。第二条按 TCP 会话汇总字节，先打开字节最多的几条流。

## 03 以太网与 ARP

### 以太网

| 过滤式 | 读到哪里 |
| --- | --- |
| `eth.addr == 00:11:22:33:44:55` | 这块网卡发出或收到的帧 |
| `eth.src == 00:11:22:33:44:55` | 只看它发出的方向，用来和 DHCP 里的客户端 MAC 对齐 |
| `eth.dst == ff:ff:ff:ff:ff:ff` | 以太网广播。ARP 和 DHCP Discover 集中在这里 |
| `eth.addr[0] & 0x02 == 2` | 本地管理地址。虚拟机、随机 MAC 和部分伪造帧会落在这一位 |

### ARP

| 过滤式 | 读到哪里 |
| --- | --- |
| `arp.opcode == 1 && arp.dst.proto_ipv4 == 192.0.2.10` | 谁在询问这台主机的 MAC。`1` 是请求 |
| `arp.opcode == 2 && arp.src.proto_ipv4 == 192.0.2.10` | 谁在回答这个 IP 属于自己。`2` 是应答 |
| `arp.src.hw_mac == 00:11:22:33:44:55` | 这块网卡声明过哪些 IP |

同一 IP 若对应两个以上 `arp.src.hw_mac`，按时间把应答排开，看是否为源 IP 与目的 IP 相同的无偿 ARP，再核对此后内网会话的网关 MAC 是否换成了新地址。

## 04 无线

监控模式抓包才有管理帧和 EAPOL。普通以太网镜像里看到的是解密后的业务，SSID 和握手不在那里。

| 过滤式 | 读到哪里 |
| --- | --- |
| `wlan.ssid == "example-net"` | 信标、探查或关联里的网络名 |
| `wlan.bssid == 00:11:22:33:44:55` | 固定到这一组 AP |
| `wlan.sa == 00:11:22:33:44:66` | 无线侧发送站，用来对齐后面的 EAPOL 方向 |
| `wlan.fc.type_subtype == 0x08` | 信标。读信道和 SSID |
| `wlan.fc.type_subtype == 0x00` | 关联请求。客户端在这里申报要加入的网络 |
| `wlan.fc.type_subtype == 0x0c` | 解除认证。同一 BSSID 上短时间成串出现时，记下源地址和时间，再看随后有没有新的关联 |
| `eapol.type == 3` | 802.1X 的 Key 帧 |

四次握手按 Replay Counter 配成 1 到 4，消息 3 看 Install 位。SSID 取自信标或关联请求，BSSID 要和这些 Key 帧一致。消息配对、Nonce 和 MIC 的完整读法在 [无线网络取证：握手与口令验证](/knowledge/forensic-wireless/)。

## 05 IP 与 ICMP

### IPv4 与 IPv6

| 过滤式 | 读到哪里 |
| --- | --- |
| `ip.src == 192.0.2.10 && ip.dst == 198.51.100.20` | 这台主机发出去的方向。回包把源和目的对调，或改用上一节的双向 `ip.addr` |
| `ip.addr == 192.0.2.0/24 && ip.addr == 203.0.113.5` | 内网网段和网关之间。网关外侧的源地址会变成公网地址，换地址再滤一次 |
| `ip.flags.mf == 1` | 还有后续分片。`ip.frag_offset > 0` 是非首片。等协议树出现 Reassembled，再导出重组后的载荷 |
| `ip.ttl < 10 && ip.src == 198.51.100.20` | 外部地址带着很小的 TTL。结合前后跳数看路径是否异常 |
| `ip.src#2 == 192.0.2.10` | 隧道里的内层源地址。`#1` 是外层 |
| `ipv6.addr == 2001:db8::10` | IPv6 的源或目的。双栈要和 IPv4 分开统计 |

### ICMP

普通 ping 很短。数据放进 Echo 时，帧长和 `data` 层会明显变大。

| 过滤式 | 读到哪里 |
| --- | --- |
| `icmp.type == 8 && ip.src == 192.0.2.10` | 这台主机发出的回请求。`0` 是回响应 |
| `icmp.type == 8 && data.len > 48` | 载荷长于普通 ping。逐包看 `data.text` 或 `data.data` |
| `icmp.type == 3 && icmp.code == 3` | 端口不可达。`code == 1` 是主机不可达，`code == 0` 是网络不可达 |
| `icmp.type == 11` | 超时。沿内层目的地址读每一跳 |
| `icmpv6.type == 134` | 路由通告。读前缀和网关 |
| `icmpv6.type in {135, 136}` | 邻居请求和通告，作用接近 ARP |

外带时只留固定方向的回请求，按 `frame.time_relative` 导出 `data.data`。应答若只是把同一段数据回显，保留客户端发出的那一侧再拼接。

## 06 TCP 与 UDP

### TCP

先把候选收成一条流，再看握手、载荷和复位各发生在什么位置。

| 过滤式 | 读到哪里 |
| --- | --- |
| `tcp.stream == 12` | Wireshark 编的第 12 条流。流号只在这次打开的文件里有效 |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0 && ip.src == 192.0.2.10` | 这台主机主动发出的 SYN。记下 `tcp.dstport` |
| `tcp.flags.syn == 1 && tcp.flags.ack == 1 && ip.dst == 192.0.2.10` | 对端返回的 SYN/ACK。和上一条处于同一个流号，握手第二步才出现 |
| `tcp.flags.reset == 1 && tcp.stream == 12` | 复位出现在握手之后，还是应用数据之后 |
| `tcp.len > 0 && tcp.stream == 12` | 这条流里已有应用层字节 |
| `tcp.payload contains "GET "` | 明文请求行还没被 HTTP 解析器认领时，直接搜载荷 |
| `tcp.analysis.retransmission` | 分析器标出的重传。缺口用 `tcp.analysis.lost_segment`。文件残缺时用这两处解释缺段，并对照 `frame.cap_len` |
| `tcp.window_size == 0 && ip.src == 198.51.100.20` | 对端通告零窗口，暂时不再收数据 |

扫描看起来是同一源在短时间里向大量不同 `tcp.dstport` 发纯 SYN，且这些流没有 `tcp.len > 0`。口令尝试则是同一目的端口上许多条短流，每条只有很少应用数据。

```bash
tshark -n -r ./evidence/capture.pcapng -q -z 'follow,tcp,ascii,12'
```

`12` 换成上面的流号。这份输出带端点和方向，适合先读明文。要恢复文件时改成 Raw，并且只保存传数据的那一个方向；整份报告改名后仍带说明文字。

### UDP

| 过滤式 | 读到哪里 |
| --- | --- |
| `udp.port == 53` | DNS 的常见端口。加密 DNS 不在这个端口上 |
| `udp.stream == 4` | 第 4 条 UDP 流。字段变红就改成地址加端口 |
| `udp.length > 200 && udp.port == 53` | 偏大的 DNS 承载，和后面的长查询名一起看 |
| `udp.payload contains "example"` | 端口未知时，在 UDP 载荷里找明文 |

UDP 用应用层事务号配对，例如 `dns.id`，不靠重传。

## 07 DNS

查询和应答拆开滤，再用事务号配回去。隧道的数据多在查询名的标签里，少数在 TXT 应答里。

| 过滤式 | 读到哪里 |
| --- | --- |
| `dns.flags.response == 0 && ip.src == 192.0.2.10` | 只留这台主机发出的查询 |
| `dns.flags.response == 1 && dns.id == 0x1a2b` | 用事务 ID 把应答配回查询，并核对地址是否对调 |
| `dns.qry.name contains "example.com"` | 这个父域下的全部名字 |
| `dns.qry.type == 1` | A 记录。`28` 是 AAAA，`5` 是 CNAME，`16` 是 TXT，`15` 是 MX，`33` 是 SRV |
| `dns.flags.rcode == 3` | NXDOMAIN。`0` 是 NoError，`2` 是 ServFail，`5` 是 Refused |
| `dns.flags.response == 1 && dns.flags.rcode == 0 && dns.a == 198.51.100.20` | 应答给出了这个 IPv4。再用 `ip.addr == 198.51.100.20` 看主机后来有没有连过去 |
| `dns.flags.response == 0 && len(dns.qry.name) > 40` | 偏长的查询名。隧道和一次性子域都先落在这里 |
| `dns.txt contains "v=spf1"` | 常见的 SPF。要提取的 TXT 通常更长，查询名固定而文本逐次变化 |
| `dns.cname contains "cdn.example.net"` | CNAME 的下一跳。最终地址要跟到 A 或 AAAA |

```bash
tshark -n -r ./evidence/capture.pcapng \
  -Y 'dns.flags.response == 0 && ip.src == 192.0.2.10' \
  -T fields -e frame.time_epoch -e dns.id -e dns.qry.name -e dns.qry.type
```

按时间排列查询名，去掉不变的父域名，把变化的标签按出现顺序接上，再按标签实际的十六进制、Base32 或 Base64 解码。只从查询侧取数据。应答若是一个固定 A 记录，那个地址是接收端，载荷仍在查询名里。

NoError 且 `dns.count.answers == 0` 表示没有答案。要确认主机访问过某个地址，需要 `dns.a` 以及随后的 TCP 或 UDP 会话。

`mdns` 在 5353，`llmnr` 在 5355，名字仍在 `dns.qry.name`。主机名对不上 DHCP 时把这两处补上。

## 08 DHCP 与 NetBIOS

`dhcp.type` 是 BOOTP 头：`1` 为 Boot Request，`2` 为 Boot Reply。Discover、Offer、Request、ACK 在选项 53，字段是 `dhcp.option.dhcp`。

| 取值 | 报文 |
| --- | --- |
| 1 | Discover |
| 2 | Offer |
| 3 | Request |
| 5 | ACK |
| 6 | NAK |

| 过滤式 | 读到哪里 |
| --- | --- |
| `dhcp.option.dhcp == 1 && dhcp.hw.mac_addr == 00:11:22:33:44:55` | 这块网卡开始要地址 |
| `dhcp.option.dhcp == 5 && dhcp.id == 0x1234abcd` | 同一事务号的 ACK。Offer 里的 `dhcp.ip.your` 还是候选地址 |
| `dhcp.option.hostname contains "pc-01" && dhcp.option.dhcp == 5` | 把主机名、`dhcp.ip.your`、`dhcp.hw.mac_addr` 记成一行 |
| `dhcp.option.dhcp_server_id == 192.0.2.1` | 选项里的 DHCP 服务器。`dhcp.ip.server` 是 next-server |
| `dhcp.option.domain_name_server == 192.0.2.53` | 租约下发的 DNS，用来解释后面的查询打向谁 |
| `nbns` | 名称注册和查询。把名称、后缀、应答地址和上面的租约按时间对齐 |

旧名字 `bootp.*` 可能仍能过滤，栏会标黄。现在写 `dhcp`。

## 09 HTTP

这些字段出现在明文 HTTP 里，或出现在 TLS 已经解开并解析成 `http` 之后。

### 请求、登录与脚本

| 过滤式 | 读到哪里 |
| --- | --- |
| `http.request && ip.src == 192.0.2.10 && lower(http.host) == "www.example.com"` | 这台主机向该站点发出的请求。没有 `http.request` 时先看 SNI |
| `http.request.method == "POST" && http.request.uri.path contains "login"` | 登录提交。账号在 `http.file_data` 或查询串里 |
| `http.authorization contains "Basic"` | Basic 认证头。解析后的账号口令在 `http.authbasic` |
| `http.response.code == 401` | 认证被拒绝。用 `http.request_in` 跳回那次请求，统计同一账号出现几次 |
| `http.response.code == 302 && http.set_cookie` | 响应同时下发 Cookie。把值抄到下一条 |
| `http.cookie contains "session=" && http.request` | 这个 Cookie 后来被带到了哪些路径。时间要晚于 Set-Cookie |
| `http.request.uri.query matches "(?i)union.select"` | 查询串里的联合查询。`information_schema` 用 `contains` 再滤一次；POST 改到 `http.file_data` |
| `http.request.uri contains "../"` | 明文路径穿越。百分号编码再滤 `http.request.uri matches "(?i)%2e%2e"` |
| `http.user_agent contains "sqlmap"` | 这个工具自己写的 User-Agent。nmap、nikto、masscan 同样换成对应名字 |
| `http.request.method == "POST" && http.request.uri contains ".php"` | 对 PHP 脚本的 POST。`.jsp`、`.aspx`、`.ashx` 各滤一次。同一路径反复出现、正文很短、响应像命令回显时，逐条读参数 |
| `http.x_forwarded_for` | TCP 源地址是代理时，客户端地址常常写在这里 |
| `http.response.code >= 500` | 服务器错误。堆栈和路径在 `http.file_data` |

登录要串三步：POST 或 Basic，接着 302 或 200 且带 `Set-Cookie`，再看更晚的请求是否带着这个 Cookie 打开原先返回 401 的页面。状态码 200 只说明这一次 HTTP 事务完成。

```bash
tshark -n -2 -r ./evidence/capture.pcapng \
  -Y 'http.request && ip.src == 192.0.2.10' \
  -T fields -e frame.time_epoch -e tcp.stream -e http.host \
  -e http.request.method -e http.request.uri -e http.response_in
```

`-2` 用来填上 `http.response_in`。最后一列是应答帧号。

### 文件与编码

| 过滤式 | 读到哪里 |
| --- | --- |
| `http.file_data[0:4] == "PK\x03\x04"` | ZIP 本地文件头 |
| `http.file_data[0:8] == 89:50:4e:47:0d:0a:1a:0a` | PNG |
| `http.file_data[0:5] == "%PDF-"` | PDF |
| `http.content_type contains "application/json" && http.file_data contains "username"` | JSON 正文里出现账号字段，值以该帧为准 |
| `http.content_encoding contains "gzip"` | 正文仍是压缩的。文件头对不上时先看解压是否失败 |
| `http.transfer_encoding contains "chunked"` | 分块传输。重组结果在 `http.body.reassembled.data` |

```bash
mkdir -p ./work/http-objects
tshark -n -2 -r ./evidence/capture.pcapng --export-objects http,./work/http-objects
```

目录先建空的。每个对象记下流号、URL 和哈希，再认文件头。

### HTTP/2 与 WebSocket

| 过滤式 | 读到哪里 |
| --- | --- |
| `http2.headers.method == "POST" && http2.headers.authority == "www.example.com"` | HTTP/2 的提交。路径在 `http2.headers.path`，状态在 `http2.headers.status` |
| `http2.streamid == 1` | 同一连接里的一条流。Follow 时选这个 stream |
| `http.upgrade contains "websocket" && http.response.code == 101` | 升级被接受。之后的消息在 `websocket` |

ALPN 为 `h2` 的连接解开后走这里，主机名用 `http2.headers.authority`。

## 10 TLS 与 QUIC

加密流量里稳定能读到的是服务器名、证书、套件，以及有没有应用数据。正文要等与这条会话匹配的 key log。

| 过滤式 | 读到哪里 |
| --- | --- |
| `tls.handshake.type == 1 && tls.handshake.extensions_server_name contains "example.com"` | Client Hello 里的 SNI。`1` 是 Client Hello，`2` 是 Server Hello，`11` 是证书 |
| `tls.handshake.type == 2 && ip.addr == 198.51.100.20` | 对端的 Server Hello。和 Client Hello 用同一个 `tcp.stream` |
| `tls.handshake.extensions_alpn_str == "h2"` | 下一层协议是 HTTP/2 |
| `tls.handshake.ja3` | 客户端握手指纹，3.6 起提供。相同取值只说明这组特征接近 |
| `tls.handshake.ja4` | 4.2 起的 JA4。变红就是本版没有该字段 |
| `tls.record.content_type == 23 && tcp.stream == 12` | 这条流已有应用数据记录，字节在 `tls.app_data` |
| `tls.alert_message && tcp.stream == 12` | 告警。读描述是握手失败、证书还是关闭 |
| `quic && tls.handshake.extensions_server_name contains "example.com"` | QUIC 里解出了 Client Hello。只有 `quic`、没有 SNI 时，Initial 不完整 |

记录层版本经常仍显示 `0x0303`。TLS 1.3 的版本在 supported_versions 扩展上，字段名从那一行复制。

```bash
tshark -n -2 -r ./evidence/capture.pcapng \
  -o tls.keylog_file:./evidence/tls-keys.log \
  -Y 'http.request || http2.headers.method' \
  -T fields -e frame.number -e tcp.stream -e http.host -e http.request.uri -e http2.headers.path
```

输出里出现请求行或 HTTP/2 路径，这条会话才算解开。key log 被读入只说明文件路径有效。

## 11 FTP 与邮件

### FTP

控制连接和数据连接是两条 TCP。登录看 230，拒绝看 530，传完看 226。

| 过滤式 | 读到哪里 |
| --- | --- |
| `ftp.request.command == "USER"` | 账号。口令命令是 `PASS`，参数都在 `ftp.request.arg` |
| `ftp.response.code == 230 && tcp.stream == 12` | 这条控制流里登录被接受。向前对上 USER |
| `ftp.response.code == 530` | 登录被拒绝。同一源大量 530 就是口令尝试 |
| `ftp.request.command == "STOR"` | 上传。下载是 `RETR`，文件名在 `ftp.request.arg` |
| `ftp.passive.ip && ftp.passive.port` | PASV 应答给出的数据端点。用这个地址和端口去滤第二条 TCP |
| `ftp.active.ip && ftp.active.port` | PORT 模式里客户端让服务器来连的端点 |
| `ftp.response.code == 226` | 传输完成。向前对 STOR 或 RETR |
| `ftp-data` | 数据流。`ftp-data.command` 是对应命令，`ftp-data.command-frame` 跳回控制帧 |

谁先发 SYN 由主动或被动模式决定。上传还是下载看 STOR 和 RETR。跟数据流时只保存传文件的方向，再用文件头判断类型。

### 邮件

| 过滤式 | 读到哪里 |
| --- | --- |
| `smtp.req.command == "AUTH"` | 开始认证。成功应答是 `smtp.response.code == 235`，要在同一条流里 |
| `smtp.req.command == "MAIL"` | 信封发件人。收件人在随后的 `RCPT` |
| `smtp.response.code == 354` | 允许开始 DATA。正文和附件在这之后，按 MIME 边界切开 |
| `imap.request contains "LOGIN"` | IMAP 明文登录 |
| `pop.request.command == "USER"` | POP 用户名。口令命令是 `PASS` |

命令字段变红时，从请求行复制本版名字。

## 12 SMB 与 Kerberos

横向访问要串起谁登录、打开了哪个共享、读了哪个文件。

| 过滤式 | 读到哪里 |
| --- | --- |
| `smb2.cmd == 0` | 协商 |
| `smb2.cmd == 1 && smb2.nt_status == 0` | Session Setup 成功 |
| `smb2.cmd == 1 && smb2.nt_status == 0xc000006d` | 登录失败。同一用户短时间多次出现就是口令尝试 |
| `smb2.cmd == 1 && smb2.nt_status == 0xc0000016` | 认证还要继续，看同一次会话的最后一条 |
| `smb2.cmd == 3` | Tree Connect。共享名在这一步 |
| `smb2.cmd == 5 && smb2.filename` | Create。文件或目录名 |
| `smb2.cmd in {8, 9} && smb2.filename contains "report"` | 对这个文件的读或写。`8` 是 Read，`9` 是 Write |
| `ntlmssp.auth.username` | NTLM 里的用户名。域名在同一棵 `ntlmssp` 下。口令原文不在这个字段里 |
| `kerberos.msg_type == 10` | AS-REQ。`11` 是 AS-REP |
| `kerberos.msg_type == 12` | TGS-REQ。`13` 是 TGS-REP，看申请的是哪张服务票据 |
| `kerberos.msg_type == 30` | Kerberos 错误 |
| `kerberos.CNameString` | 客户端主体。大小写必须照写 |

```bash
tshark -n -r ./evidence/capture.pcapng -Y 'smb2' \
  -T fields -e frame.time_epoch -e ip.src -e ip.dst \
  -e smb2.cmd -e smb2.filename -e smb2.nt_status
```

按时间把 Session Setup 成功、Tree Connect、Create、Read 排成一次访问。Kerberos 同一帧里主体和票据会重复，用 `-V` 展开后再读。

## 13 MySQL

明文连接可以直接读账号、库名、语句和结果行。`mysql.passwd` 是认证字节，口令原文要到语句或服务器日志里找。

| 过滤式 | 读到哪里 |
| --- | --- |
| `mysql.login_request` | 登录请求。用户名在 `mysql.user`，库名在 `mysql.schema` |
| `mysql.user == "app" && mysql.query` | 这个账号随后执行的语句 |
| `mysql.query contains "SELECT"` | 语句正文。插入、修改和读文件语句都在 `mysql.query` |
| `mysql.row.text` | 返回的文本行 |
| `mysql.load_data.filename` | LOCAL INFILE 的文件名。文件字节在 `mysql.load_data.payload` |

语句跨多帧时，读 `mysql.reassembled.in` 指向的那一帧。

## 14 远程会话

| 过滤式 | 读到哪里 |
| --- | --- |
| `ssh.protocol contains "SSH-2.0" && ip.dst == 198.51.100.20` | 连向该地址的版本字符串。版本交换之后是加密二进制，命令到主机日志里对 |
| `telnet.data && tcp.stream == 12` | 这条 Telnet 流的载荷。跟流时看客户端方向，输入是逐字符送出的 |
| `rdp` | RDP 协商。同时用 `tcp.port == 3389` 只是端口线索，先看协商走的是标准安全还是 TLS |
| `vnc` | VNC 握手和后续消息。剪贴板文本在客户端剪贴消息里，字段从该行复制 |

没有与这条 RDP 会话匹配的秘密时，记录建连时间、协商结果和对端证书名。

## 15 USB

键盘流量先分出 HID 接口，再导出中断传输里的报告。接口描述符和按键报告不在同一帧，两个条件不要写进同一个 `&&`。

| 过滤式 | 读到哪里 |
| --- | --- |
| `usb.bInterfaceClass == 3` | HID 接口。键盘和鼠标都在这一类 |
| `usb.transfer_type == 1 && usb.capdata` | 中断传输的剩余捕获数据。键盘的 Boot 报告通常是 8 字节 |
| `usb.capdata && !(usb.capdata == 00:00:00:00:00:00:00:00)` | 去掉全 0 的松开报告 |

```bash
tshark -n -r ./evidence/keyboard.pcapng \
  -Y 'usb.transfer_type == 1 && usb.capdata && !(usb.capdata == 00:00:00:00:00:00:00:00)' \
  -T fields -e frame.time_relative -e usb.src -e usb.capdata
```

8 字节报告的第 1 字节是修饰键，`0x02` 和 `0x20` 分别是左右 Shift；第 2 字节保留；后 6 字节是当前按下的键。同一键码连续出现时，对照时间间隔区分长按重复和再次按下。键码到字符的完整对照、退格和回车的两种结果，见 [USB 键盘流量还原](/knowledge/usb-keyboard/)。鼠标是另一套报告长度，和键盘分开翻译。

本版若把报告放在 `usbhid.data`，用 `tshark -G fields` 确认后替换字段名。

## 16 明文服务与捕获过滤

Redis 一类服务若没有单独的查询字段，命令就在 TCP 载荷里。

```text
tcp.port == 6379 && tcp.payload
```

跟这条流的客户端方向，按 RESP 的数组和批量字符串顺序读认证、`GET`、`SET`。端口改过时，先用载荷里的命令特征定位，再按结构 Decode As。

工控写操作先留功能码：

```text
modbus.func_code in {5, 6, 15, 16}
```

`5` 和 `15` 写线圈，`6` 和 `16` 写寄存器。读寄存器是 `3` 和 `4`。把功能码、参考地址和写值按 `tcp.stream` 与时间排开。字段变红就从 Modbus 那一行复制。

下面这些只在开始抓包时使用。写进捕获选项，或 `dumpcap -f`、`tshark -f`。没匹配上的包不会进文件。

| 过滤式 | 读到哪里 |
| --- | --- |
| `host 192.0.2.10 and not port 22` | 只留这台主机，并去掉管理用的 SSH |
| `net 192.0.2.0/24 and (tcp port 80 or tcp port 443 or udp port 53)` | 网段里的 Web 与 DNS。事后要查 SMB 时，这份文件里没有 |
| `udp port 53 or port 5353 or port 5355` | DNS、mDNS、LLMNR |
| `tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0` | 只抓纯 SYN。完整会话和文件内容不在里面 |

```bash
dumpcap -i eth0 -f 'host 192.0.2.10 and not port 22' -w ./work/host.pcapng
```

远程桌面里抓包时，把那条管理连接的端口写进 `not port`。文件已经打开之后，改回显示过滤。
