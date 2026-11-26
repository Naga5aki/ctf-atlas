---
title: "Cobalt Strike流量分析"
summary: "Cobalt Strike 的核心是 Beacon（信标）与 TeamServer（C2 服务器）之间的加密通信。"
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理

Cobalt Strike 的核心是 Beacon（信标）与 TeamServer（C2 服务器）之间的加密通信。

Beacon 与 TeamServer 通信时，使用 AES 加密任务数据，同时通过 HMAC 校验完整性

会话密钥来源于 Beacon 生成并传递给 C2 的元数据

**密钥体系：**

Beacon 生成随机 Raw Key

↓

SHA256 派生

↓

┌───────────┬───────────┐

│  AES_KEY  │ HMAC_KEY   │

│ 数据加密  │ 完整性校验 │

└───────────┴───────────┘

Beacon 会用 TeamServer 公钥加密元数据，而 TeamServer 保存对应私钥，因此拥有 RSA 私钥即可解密元数据、还原 Raw Key、进而派生会话密钥。

## 二、题目特征识别

拿到 .pcap / .pcapng 流量包后，首先判断是否存在 Cobalt Strike。

### 1. 周期性 Beacon 通信

内网主机

|

|  定时访问

|

公网 IP / C2 服务器

**特点：**

固定时间间隔

固定数据长度

HTTP / HTTPS / DNS 通信

### 2. HTTP 特征

**常见路径：**

GET /xxx

POST /submit.php

典型 Wireshark 过滤：

http.request.uri.path == "/submit.php"

这是 Cobalt Strike HTTP Beacon 常见过滤方向。

### 3. 请求内容异常

POST 请求中 Cookie: xxxxxx

Body 为一串随机字符

类似 /submit.php?id=xxxx

没有正常网页行为

数据高度随机

周期访问

## 三、CTF-NETA 一把梭流程

PCAP

↓

CTF-NETA

↓

识别 Cobalt Strike

↓

提取 Key

↓

解密 Beacon 通信

↓

获得命令 / 回显 / flag

对于比赛而言，不需要优先手算 AES 或分析协议细节。CTF-NETA 一把梭的核心就是：导入流量 → 自动识别 CS → 提取 Key → 自动解密 → 搜 flag。手工分析主要用于工具无法识别时。

## 四、Wireshark 手工辅助过滤器

Wireshark 辅助分析。

| 目的 | 过滤表达式 |
| --- | --- |
| 找 HTTP Beacon | http |
| 找 POST 请求 | http.request.method=="POST" |
| 找指定路径 | http.request.uri.path=="/submit.php" |
| 查看完整交互 | 右键 → Follow → TCP Stream |

Follow TCP Stream 后重点观察：

Cookie

POST 数据

返回内容

## 五、常见解密对象

Cobalt Strike 流量中主要分析三类内容：

| 对象 | 包含内容 |
| --- | --- |
| Metadata | Beacon ID、主机名、用户名、系统信息 |
| Task（任务） | 攻击者发送的执行命令，例如 cmd.exe /c whoami |
| Output（回显） | 目标返回的命令结果，例如 root、Administrator、flag |
