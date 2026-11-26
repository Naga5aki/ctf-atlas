---
title: "Web 与 Pwn 组合题"
summary: "Web 打点只是入场券：从 Web 层拿立足点、发现内网二进制服务、下载样本、checksec/逆向、写 exploit 回传执行，打通到 flag。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-pentest-flow", "web-internal-recon", "web-cloud-container", "web-layer-practice"]
updated: "2026-10-29"
---

组合题的结构是“Web 入口 → 内部服务/二进制 → flag”。Web 部分只负责拿到执行点与信息，真正的考点在后端程序；别在 Web 层死磕，先确认 flag 不在当前权限可读的位置。

> 只对本地题目或授权环境测试；二进制 exploit 可能崩溃服务，先快照。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| flag 权限 | `ls -l /flag` | 读不了才需提权 |
| 本机服务 | `ss -lntup` | 只看 127.0.0.1 |
| 自定义程序 | `/opt`/`/srv`/`/app` | 文件名/权限 |
| SUID/cap | `find -perm -4000`/`getcap` | 提权 |
| 样本 | `file`/`checksec` | 架构/保护 |
| 偏移 | `cyclic`/pattern | 崩溃点 |
| 回传 | base64/上传/curl | 目标无工具 |
| 执行 | 本地脚本/远程 | 交互 |

## 01 原理与成立条件

```text
Web 漏洞 → 执行点 → 本机侦察
                      ├─ 内部服务（127.0.0.1）
                      ├─ 自定义二进制
                      └─ 提权路径
样本 → 本地分析 → exploit → 回传执行 → flag
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| Web 执行点 | RCE/上传/SSRF | 回 Web 专题 |
| 内部服务可达 | 本机/端口 | 隧道 |
| 样本可取 | 下载/base64 | 盲打/逆向流量 |
| 可回传执行 | 上传/写文件 | 正向/隧道 |

## 02 判断与分型

```text
flag 能读吗？
 ├─ 能 → 直接拿
 └─ 不能
     ├─ 本机有 127.0.0.1 服务 → Pwn
     ├─ 有 SUID/内核 → 提权
     ├─ 有自定义程序 → 逆向/溢出
     └─ 容器 → 逃逸/元数据
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `127.0.0.1:9999` | 内部服务 | 取样本/打 |
| `/opt/bin` 可执行 | 自定义程序 | `file`/checksec |
| SUID root | 提权 | 看程序逻辑 |
| `getcap` 有 cap | 能力 | 滥用 |
| flag 600 root | 需高权 | 提权/Pwn |
| 目标无 python | 回传受限 | 静态/管道 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 端口开放 | 服务假死 | 看 banner |
| SUID | 无利用点 | 看版本/参数 |
| 样本下载 | 截断 | 校验大小/hash |
| exploit 本地通 | 远程环境不同 | 对齐 libc |

## 03 利用阶梯

### L0 Web 立足点

**前提**：Web 漏洞可执行/上传。

**步骤**：
1. 确认命令执行或 webshell 稳定。
2. 记录用户/目录/权限。
3. `ls -l /flag`/`find / -name 'flag*'` 看是否可直接读。
4. 不直接打内核 exp。

**成功标志**：稳定执行 + flag 权限结论。

**失败分支**：无执行→回 Web；命令受限→换解释器。

### L1 发现内部服务/程序

**前提**：有 shell。

**步骤**：
1. `ss -lntup`/`netstat` 看本机监听。
2. `ps aux`/`/proc/1/cmdline` 看进程。
3. `ls -la /opt /srv /app /home`。
4. `find / -perm -4000`/`getcap -r /`。
5. 标“外网不可达、本机可达”的服务。

**成功标志**：内部服务/自定义程序清单。

**失败分支**：无服务→提权/容器；权限不足→换目录。

### L2 样本获取与分析

**前提**：有二进制/服务。

**步骤**：
1. `curl 127.0.0.1:9999/bin -o /tmp/bin` 或 base64 回传。
2. `file`/`checksec`/`strings`/`readelf`。
3. Ghidra/IDA 看输入/崩溃点。
4. 本地 `pwndbg`/`cyclic` 找偏移。
5. 记录架构/保护/libc。

**成功标志**：知道漏洞类型与偏移。

**失败分支**：样本取不到→盲测/流量；静态链接→看 gadget。

### L3 编写与本地验证

**前提**：有样本/崩溃点。

**步骤**：
1. 按类型写：ret2text/ret2libc/格式化/堆。
2. 本地 `process` 跑通，再 `remote`。
3. 对齐远程 libc（泄露地址/版本）。
4. 记录 payload 与交互。

**成功标志**：本地/远程稳定 getshell 或读 flag。

**失败分支**：远程崩→对齐 libc/偏移；无交互→换 gadget。

### L4 回传执行与提权

**前提**：目标无 Python/不出网。

**步骤**：
1. 上传静态 exploit/脚本到可写目录。
2. 用 `perl`/`ruby`/`socat`/管道执行。
3. 不出网：写文件后本地执行/正向端口。
4. 需要提权：SUID/cron/内核/配置凭据。
5. 只验证到读 flag。

**成功标志**：exploit 在目标执行并拿到 flag。

**失败分支**：上传被杀→编码/分段；提权失败→换路径。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 目标无 python | 静态/管道 | socat |
| 不出网 | 写文件/正向 | 上传 |
| 样本截断 | base64/分块 | 校验 |
| 远程 libc 不同 | 泄露/对齐 | 版本 |
| NX/PIE | ROP/泄露 | gadget |
| 容器 | 逃逸/元数据 | 见云页 |

边界：exploit 可能崩服务；远程偏移需重新确认；SUID 程序要看版本/参数；flag 权限决定是否需要提权。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 内部 HTTP | 管理口 | 样本 |
| 数据库 | 扩展/命令 | 提权 |
| 定时任务 | 脚本 | 可写 |
| 容器 | 宿主挂载 | 逃逸 |
| CI | runner | 内网 |

## 06 差异速查

| 保护 | 影响 | 绕过 |
|---|---|---|
| NX | 栈不可执行 | ROP |
| PIE | 基址随机 | 泄露 |
| Canary | 栈保护 | 泄露/绕过 |
| RELRO | GOT | 看 full/partial |
| Fortify | 格式化 | 限制 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 侦察 | `ss`/`ps`/`find` |
| 样本 | `file`/`checksec`/`strings` |
| 反编译 | Ghidra/IDA |
| 调试 | pwndbg/gef |
| 偏移 | `cyclic` |
| 回传 | base64/curl |
| 记录 | 样本/偏移/payload |

验证顺序：立足 → 服务 → 样本 → 本地 → 远程 → flag。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 立足 | Web 执行 | shell |
| 2 侦察 | 端口/程序/权限 | 目标 |
| 3 样本 | 下载/分析 | 漏洞 |
| 4 本地 | exploit | 通 |
| 5 远程 | 回传/执行 | flag |
| 6 记录 | 样本/payload | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| flag 读不了 | 权限 | 提权/Pwn |
| 无内部服务 | 单层 | 提权/容器 |
| 样本取不到 | 路径/权限 | base64/流量 |
| 本地通远程崩 | libc/偏移 | 对齐 |
| 上传被杀 | AV | 编码/分段 |
| 无交互 | 管道 | socat/正向 |

## 10 记录与复现

- [ ] Web 入口/执行点
- [ ] 内部服务/程序
- [ ] 样本/架构/保护
- [ ] 偏移/libc
- [ ] exploit/回传
- [ ] flag/权限

| 记录项 | 内容 |
|---|---|
| 入口 | Web 漏洞 |
| 侦察 | 端口/程序 |
| 样本 | 路径/架构 |
| 偏移 | 偏移/地址 |
| exploit | 脚本/结果 |

相关： [渗透流程](/knowledge/web-pentest-flow/)、[内网信息收集](/knowledge/web-internal-recon/)、[云与容器](/knowledge/web-cloud-container/)、[多层网络实战](/knowledge/web-layer-practice/)。
