---
title: "Ceph流量分析"
summary: "Ceph 流量题的考点不在协议本身，而在于考察选手遇到陌生二进制协议时能否绕开解析、直接基于 payload 做 file carving 的通用能力。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、题型本质与协议背景

### 1. 核心本质

Ceph 流量题的考点不在协议本身，而在于考察选手遇到陌生二进制协议时能否绕开解析、直接基于 payload 做 file carving 的通用能力。掌握这一题的思路，可迁移到几十种私有协议流量题。

### 2. Ceph 是什么

Ceph 是一套统一分布式存储系统，对外提供块存储（RBD）、对象存储（RGW）和文件系统（CephFS），底层是 RADOS（可靠的自主分布式对象存储）。其内部组件（MON/MGR/OSD/MDS）与客户端之间通过自定义的 Messenger 协议通信，是典型的 "TCP 之上的私有二进制协议"。

### 3. 端口指纹（识别第一步）

| 端口 | 协议版本 | 组件 | 说明 |
| --- | --- | --- | --- |
| 6789 | msgr v1（legacy） | MON | Monitor 默认端口，已广泛使用 |
| 3300 | msgr v2（msgr2） | MON | IANA 正式注册，新版优先 |
| 6800–7300 | v1/v2 | OSD/MGR/MDS | 每个守护进程占多个端口 |
| 6800–7568 | v1/v2 | OSD（新版本） | 更新的发行版扩到 7568 |

看到 pcap 里出现 xxx → yyy:6789，或 xxx:49818 → yyy:36890（落在 6800–7568 区间），基本可直接判断是 Ceph。

### 4. msgr2 帧结构（了解即可）

新版 msgr2 连接分四个阶段：banner → auth → handshake → message，banner 是固定字符串 "ceph v2\n"。每个 frame 由 tag + payload + 副签名 / 加密字段构成，tag 是一个字节类型码，决定 payload 结构。

msgr2 提供三种传输模式：

crc / crc-mode：明文 + CRC

**secure：** 加密 + CRC

CTF 出题几乎 100% 用明文模式，否则就无解了。

## 二、Wireshark 解析与为什么必须切 File Carving

### 1. Wireshark 内置 Ceph dissector

可直接把 TCP payload 解析为 Ceph 消息：

**过滤器：** ceph、ceph.msg、ceph.connect、ceph.auth

Info 列能读到 Connect、Auth Reply、Mon Map、OSD Map、MDS Map、KEEPALIVE2 等消息类型

题目里常出现的 Malformed Packet 是正常现象——Ceph 版本众多，dissector 覆盖不全，不影响后续提取

### 2. 经典误区

很多选手看到 Wireshark"认识"Ceph，就想去 Follow TCP Stream 里翻明文 flag。实际上 Ceph 是二进制协议，Mon Map、OSD Map 这些是集群元数据，真正的对象数据（含 flag 的文件）走的是 OSD 之间的 data 帧（payload），肉眼几乎不可读。

### 3. 能藏 flag 的两类位置

| 位置 | 内容 | 是否有flag |
| --- | --- | --- |
| 元数据消息 | Mon Map / OSD Map / Auth | 通常无 flag |
| OSD 数据帧 payload | 客户端读写对象时的实际文件字节 | 重点 |

第 2 类中，文件内容原样塞在 Ceph 帧的 data 段里（明文模式下不做变换）。协议头是二进制的，但 payload 一旦是 PNG/JPEG/ZIP 这类常见格式，就一定有清晰的魔数。

**思路转向：** 与其解析 Ceph 协议头，不如在 TCP 流里直接 "搜魔数"—— 这就是 file carving。

## 三、提取工具对比

| 工具 | 工作机制 | 对Ceph适用性 | 命令示例 |
| --- | --- | --- | --- |
| tcpxtract | libpcap 抓流 + 按签名切割，自动重组 TCP 会话 | ⭐⭐⭐⭐⭐ 一条命令搞定 | tcpxtract -f x.pcap |
| NetworkMiner | GUI，自动识别协议 + carving，支持任意 TCP/UDP | ⭐⭐⭐⭐⭐ 图形化方便 | 打开 pcap → Files 标签 |
| 手工 Follow TCP Stream | Wireshark 追流 + Raw 导出 + 手工剪裁 | ⭐⭐⭐⭐ 通用兜底 | 右键 → Follow → Raw → 保存 |
| Foremost | 通用文件雕刻，但对跨 TCP 包支持弱 | ⭐⭐ 需先导出原始流 | foremost -i stream.raw |
| Binwalk | 二进制签名扫描，对 pcap 支持一般 | ⭐⭐ 适合单个导出文件 | binwalk -e stream.raw |

## 四、手工提取兜底法

操作步骤

Wireshark 全局搜魔数：编辑 → 查找分组 → 分组字节串 → 十六进制 → 89504e47，找到 PNG 起始的那条 TCP 包

右键该包 → Follow → TCP Stream，切换显示为 Raw（Show data as 选 Raw），只选一个方向（客户端→服务端）

Save as 保存为 dump.bin

用 010 Editor / HxD 打开，从 89 50 4E 47 开始，到 49 45 4E 44 AE 42 60 82 结束（含），剪掉前后 Ceph 协议头，另存为 flag.png

Python 一键切

data = open('dump.bin','rb').read()

start = data.find(b'\x89PNG')

end   = data.find(b'IEND\xaeB`\x82') + 8

open('flag.png','wb').write(data[start:end])

## 五、进阶变体

变体 1：msgr2 secure 模式

若出题人开了 msgr2 secure，data 段是 AES-128-GCM 加密的，file carving 直接失效。此时需要：

从流量中提取 auth 阶段协商的会话密钥（题目通常塞在 pcap 其他地方或附件里）

用 pyceph / Ceph 源码中的 crypto 模块解密

CTF 出这种题的概率极低，因为实现复杂度太高。

变体 2：多个文件散落在多条 TCP 流

tcpxtract 会自动枚举所有五元组并分别提取。如果漏了，可先用 tcpdump -r x.pcap 'tcp' -w split.pcap 或 Wireshark 的 tcp.stream eq N 过滤后逐条处理。

变体 3：文件本身隐写

提取出 PNG 后 flag 还要看（LSB、宽高改、zlib 追加等）—— 这就切到常规 Misc 隐写思路，和 Ceph 协议无关。

与常见 "文件传输类" 协议的通用解法对比

| 协议 | 端口 | payload是否明文 | 提取工具 |
| --- | --- | --- | --- |
| Ceph（msgr crc） | 6789/3300/6800+ | ✅ 明文 | tcpxtract / NetworkMiner |
| SMB | 445 | ✅ | NetworkMiner |
| NFS | 2049 | ✅ | tcpxtract |
| iSCSI | 860/3260 | ✅ | NetworkMiner |
| FTP-DATA | 20 | ✅ | Wireshark 自带导出 |
| TFTP | 69 | ✅ | Wireshark 导出对象 |
| Redis | 6379 | ✅（RESP 协议） | tcpxtract |
| MySQL/PG | 3306/5432 | 部分明文 | 手工 carve |
| HTTP | 80 | ✅ | Export HTTP Objects |
| msgr2 secure | 3300 | ❌ 加密 | 需密钥解密 |

**共同规律：** 只要协议是明文（或含明文 payload），不管上层是私有协议还是标准协议，基于 TCP 流重组 + 魔数签名 的 carving 都能工作。
