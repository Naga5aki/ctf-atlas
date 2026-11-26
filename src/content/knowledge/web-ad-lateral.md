---
title: "域渗透与横向移动"
summary: "从一台域成员机出发：确认域/DC/用户，再做 Kerberoasting/AS-REP、委派与 ACL，最后用凭据/票据横向；每步先看权限再选工具。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-internal-recon", "web-layer-practice", "web-pentest-flow"]
updated: "2026-10-29"
---

域渗透的入口通常是“一台已控的域成员机”。先确认域、用户、DC，再决定是打 Kerberos、抓凭据，还是直接横向。不要一上来就跑 mimikatz。

> 只对授权靶场或明确授权的域环境测试；凭据与票据属于高敏数据。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 是否在域 | `whoami /all`/`systeminfo` | 域名 |
| DC | `nltest /dsgetdc`/DNS SRV | 定位 |
| 用户/组 | `net user /domain` | 权限 |
| SPN | `GetUserSPNs.py` | Kerberoast |
| 无预认证 | `GetNPUsers.py` | AS-REP |
| 委派 | `findDelegation.py` | 滥用 |
| ACL | BloodHound | 可写权限 |
| 凭据 | LSASS/SAM/GPP | 抓取 |
| 横向 | WMI/WinRM/SMB | 选协议 |

## 01 原理与成立条件

```text
域成员机 → 域认证（Kerberos/NTLM）
             ├─ TGT/TGS → 票据
             ├─ 服务账号 → SPN → 破解
             ├─ 委派/ACL → 代表用户
             └─ 本地凭据 → 横向
DC 保存用户/计算机/组/策略
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 已控域成员 | shell/凭据 | 先拿点 |
| 能查域 | DNS/LDAP | 换工具 |
| 有目标账号 | SPN/委派/ACL | 枚举 |
| 凭据可用 | 哈希/票据/口令 | 抓取 |

## 02 判断与分型

```text
whoami /all 有域名吗？
 ├─ 有 → 域环境
 │    ├─ 有 SPN → Kerberoast
 │    ├─ 无预认证 → AS-REP
 │    ├─ 委派/ACL → 滥用
 │    └─ 本地管理员 → 抓凭据/横向
 └─ 无 → 工作组，先找域凭据
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `Domain: EXAMPLE` | 域成员 | 找 DC |
| `Domain Admins` 组 | 高权 | 目标 |
| 服务账号有 SPN | Kerberoast | 请求 TGS |
| `DONT_REQ_PREAUTH` | AS-REP | 请求 |
| 委派标志 | 滥用 | 看类型 |
| ACL `GenericAll` | 可改 | BloodHound |
| 本地管理员 | 抓 SAM/LSASS | 横向 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 有域名 | 只是 DNS 后缀 | 看 `whoami` |
| SPN 账号 | 口令强 | 换目标 |
| 本地管理员 | 域内无权限 | 抓凭据 |
| ACL 可写 | 对象类型不符 | 看 BloodHound |

## 03 利用阶梯

### L0 域识别

**前提**：已控一台 Windows/Linux 域成员。

**步骤**：
1. `whoami /all`/`systeminfo` 看域/用户/组。
2. `nltest /dsgetdc:domain` 或 DNS SRV 找 DC。
3. `net user /domain`/`net group "Domain Admins" /domain`。
4. Linux：`realm list`/`sssd` 配置/`krb5.conf`。

**成功标志**：域名、DC、当前权限。

**失败分支**：无 RSAT→`net`/PowerShell；无权限→先提权。

### L1 枚举用户/主机/SPN

**前提**：有域凭据或匿名 LDAP。

**步骤**：
1. `Get-ADUser`/`Get-ADComputer` 或 `ldapsearch`。
2. `GetUserSPNs.py` 列 SPN。
3. `GetNPUsers.py` 找无预认证。
4. BloodHound 收集（`-c All`）。

**成功标志**：用户/主机/SPN/委派/ACL 清单。

**失败分支**：LDAP 受限→用已控机本地枚举；无凭据→找配置。

### L2 Kerberos 攻击

**前提**：有 SPN 或无预认证账号。

**步骤**：
1. Kerberoast：请求 TGS，`hashcat -m 13100`。
2. AS-REP：请求 AS-REP，`hashcat -m 18200`。
3. 拿到口令后验证权限，不直接打 DC。
4. 记录账号/哈希/来源。

**成功标志**：破解出服务账号口令。

**失败分支**：口令强→换账号/转委派；请求被拦→降速。

### L3 委派 / ACL

**前提**：BloodHound 显示委派或可写 ACL。

**步骤**：
1. 非约束委派：诱导 DC 连接，抓 TGT。
2. 约束委派：S4U2Self/S4U2Proxy。
3. RBCD：改目标 `msDS-AllowedToActOnBehalfOfOtherIdentity`。
4. ACL：`GenericAll`/`WriteDACL`/`ForceChangePassword` 按对象操作。
5. 只验证到目标主机权限。

**成功标志**：代表用户/获得目标权限。

**失败分支**：权限不足→换路径；对象不支持→换目标。

### L4 凭据与横向

**前提**：有本地管理员/域凭据。

**步骤**：
1. LSASS/SAM/GPP/浏览器/配置。
2. PTH：`crackmapexec`/`psexec -hashes`。
3. PTT：`KRB5CCNAME` + `-k -no-pass`。
4. 远程执行：WMI/WinRM/SMB/计划任务。
5. 记录主机/权限/数据。

**成功标志**：登录下一台/拿到目标数据。

**失败分支**：NTLM 禁用→用票据；AV→换工具/停。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| NTLM 禁用 | Kerberos/PTH 票据 | PTT |
| AV/EDR | 原生工具/内存 | 授权 |
| 无 RSAT | `net`/LDAP | 枚举 |
| 委派受限 | RBCD/ACL | 看配置 |
| 口令强 | 找配置/委派 | 换路径 |
| 日志监控 | 降速/少请求 | 停 |

边界：黄金票据需 `krbtgt` 哈希；白银票据需服务账号哈希；RBCD 需写目标权限；PTH 依赖 NTLM；域控操作影响大，只在授权靶场。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Web 应用 | 域账号登录 | 凭据 |
| 数据库 | 链接服务器 | 横向 |
| 文件共享 | SMB | 凭据 |
| 备份 | 域配置 | 离线 |
| CI/CD | 服务账号 | 权限 |

## 06 差异速查

| 攻击 | 条件 | 工具 |
|---|---|---|
| Kerberoast | SPN | GetUserSPNs |
| AS-REP | 无预认证 | GetNPUsers |
| 黄金票据 | krbtgt | mimikatz |
| 白银票据 | 服务哈希 | mimikatz |
| RBCD | 写目标 | rbcd.py |
| PTH | NTLM | crackmapexec |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 域信息 | `whoami`/`nltest` |
| 枚举 | PowerView/BloodHound |
| Kerberos | impacket |
| 凭据 | mimikatz/secretsdump |
| 横向 | wmiexec/evil-winrm |
| 记录 | 用户/哈希/主机 |

验证顺序：域 → 枚举 → Kerberos → 委派/ACL → 横向。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 域 | 域名/DC/权限 | 定位 |
| 2 枚举 | 用户/主机/SPN | 清单 |
| 3 Kerberos | roast | 口令 |
| 4 委派/ACL | 滥用 | 权限 |
| 5 凭据 | 抓取 | 哈希/票据 |
| 6 横向 | WMI/WinRM | 目标 |
| 7 记录 | 主机/权限 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 找不到 DC | DNS/网络 | 换解析 |
| LDAP 拒绝 | 权限 | 本地枚举 |
| roast 无结果 | 无 SPN/预认证 | 换账号 |
| 破解失败 | 口令强 | 换目标 |
| 委派失败 | 类型/权限 | 看 BloodHound |
| PTH 失败 | NTLM 禁用 | PTT |
| 横向被拦 | AV/防火墙 | 换协议/停 |

## 10 记录与复现

- [ ] 域名/DC/网段
- [ ] 用户/组/主机
- [ ] 攻击类型
- [ ] 凭据/票据来源
- [ ] 横向方式
- [ ] 目标权限/数据

| 记录项 | 内容 |
|---|---|
| 域 | 域名/DC |
| 账号 | 用户/组 |
| 攻击 | Kerberoast/委派 |
| 凭据 | 哈希/票据 |
| 横向 | WMI/WinRM |

相关： [内网信息收集](/knowledge/web-internal-recon/)、[多层网络实战](/knowledge/web-layer-practice/)、[渗透流程](/knowledge/web-pentest-flow/)。
