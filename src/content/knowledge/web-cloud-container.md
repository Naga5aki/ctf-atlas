---
title: "云与容器：从元数据到宿主边界"
summary: "先判断在容器/云主机/哪家云，再按元数据、环境变量、docker.sock、privileged、K8s SA token、对象存储逐级验证；每级只做只读确认。"
module: Web
topic: "Web漏洞"
tags: ["容器"]
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-server-fetch-advanced", "web-internal-recon", "web-docker-lab", "web-pentest-flow"]
updated: "2026-10-29"
---

云上题目的典型链路是 **Web 漏洞 → SSRF → 元数据 → 临时凭证 → 对象存储/API**；容器题则是 **Web RCE → 容器内信息 → socket/privileged/K8s → 宿主机**。先判断“在哪”，再决定“往哪走”。

> 只对本地题目或授权云环境测试；元数据凭证属于敏感信息，不要用于范围外的资源。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 是否容器 | `/.dockerenv`/cgroup | 见下 |
| 哪家云 | 元数据地址/环境变量 | 逐家试 |
| 云凭证 | `security-credentials`/env | 只读验证 |
| 容器权限 | `capsh --print` | CapEff |
| docker.sock | `/var/run/docker.sock` | 可写=高危 |
| K8s | `KUBERNETES_SERVICE_HOST` | SA token |
| 宿主挂载 | `mount`/`/proc/1/root` | 只读 |
| 对象存储 | `*.oss-*`/`*.s3*` | 公开读/列 |
| 内核 | `uname -r` | 版本边界 |

## 01 原理与成立条件

```text
Web/SSRF → 元数据/环境变量 → 临时凭证
容器 RCE → 能力/挂载/socket → 宿主
K8s Pod → SA token → API → Secret/Pod
对象存储 → 公开/预签名 → 数据
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 能发请求/执行 | SSRF/RCE | 找入口 |
| 云/容器标识可达 | 元数据/socket | 换路径 |
| 权限足够 | 凭证/能力 | 换原语 |
| 范围允许 | 授权 | 停 |

## 02 判断与分型

```text
/.dockerenv 存在或 cgroup 含 docker/kubepods？
 ├─ 是 → 容器
 │    ├─ docker.sock 可写 → 宿主
 │    ├─ privileged/CAP_SYS_ADMIN → 挂载/逃逸
 │    ├─ K8s SA → API
 │    └─ 普通 → 环境变量/元数据
 └─ 否 → 云主机/VM
      ├─ 元数据可达 → 凭证
      └─ 不可达 → 内网/对象存储
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `/.dockerenv` | Docker | 查挂载/能力 |
| cgroup `kubepods` | K8s | SA token |
| `CapEff` 大 | 特权 | 挂载/逃逸 |
| `docker.sock` 可写 | Docker API | 起容器 |
| `KUBERNETES_SERVICE_HOST` | K8s | 调 API |
| 元数据 200 | 云 | 取凭证 |
| 页面引用 OSS/S3 | 对象存储 | 列桶 |
| 主机名随机 | 编排 | 看环境 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 元数据超时 | 网络策略 | 换地址/停 |
| 有 `docker` 命令 | 未必有 socket | 看权限 |
| 能读 `/proc` | 不等于宿主 | 看命名空间 |
| OSS 域名 | 可能只是 CDN | 看凭证/权限 |

## 03 利用阶梯

### L0 判断环境

**前提**：已有命令执行/文件读取。

**步骤**：
1. 看 `/.dockerenv`、`/proc/1/cgroup`、`hostname`。
2. `mount`/`/proc/self/mountinfo` 找宿主挂载。
3. `capsh --print`/`cat /proc/self/status` 看能力。
4. 看环境变量里的云/K8s 标识。

**成功标志**：确定容器/云厂商/K8s。

**失败分支**：无命令执行→SSRF/文件读取；信息少→换路径。

### L1 云元数据与凭证

**前提**：能发 HTTP/SSRF。

**步骤**：
1. 按厂商试地址：AWS `169.254.169.254`、阿里 `100.100.100.200`、腾讯 `169.254.0.23`、GCP/Azure 需特定头。
2. AWS IMDSv2：先 `PUT /latest/api/token` 取 token，再带 `X-aws-ec2-metadata-token`。
3. 读 `iam/security-credentials/` 角色与临时凭证。
4. 只读验证身份（STS `GetCallerIdentity`）。

**成功标志**：拿到临时凭证/实例信息。

**失败分支**：需头→找可自定义头的入口；IMDSv2→先取 token；超时→停。

### L2 容器内信息

**前提**：容器内命令执行。

**步骤**：
1. `env`/`/proc/self/environ` 找 DB/密钥。
2. 看 `docker.sock`、`/run/secrets`、宿主目录挂载。
3. 看 `/proc/1/root` 是否宿主根。
4. 记录用户/能力/内核。

**成功标志**：找到可用的逃逸原语/凭证。

**失败分支**：普通容器→元数据/网络；无挂载→换原语。

### L3 socket / privileged / K8s

**前提**：有 socket/特权/SA token。

**步骤**：
1. `curl --unix-socket`/`docker -H` 看版本；能起容器则只读挂载宿主验证。
2. privileged：看是否能 `mount` 宿主磁盘；只读挂载。
3. K8s：读 SA token/CA，`kubectl auth can-i --list`，只读 `get pods/secrets`。
4. 有 `create pods` 才考虑挂载宿主；否则停在读。

**成功标志**：读到宿主文件/其他 Pod/Secret。

**失败分支**：socket 只读→换原语；RBAC 严格→停。

### L4 对象存储与横向

**前提**：拿到云凭证或发现 Bucket。

**步骤**：
1. 看页面引用域名（OSS/S3/COS）。
2. 试公开读/列目录（`aws s3 ls --no-sign-request`）。
3. 预签名 URL：改路径/过期时间，观察签名错误。
4. 用临时凭证列桶/读对象，只读题目范围。
5. 记录权限边界。

**成功标志**：读到对象/列出桶。

**失败分支**：私有→找凭证；预签名严格→停。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 元数据需头 | 找可加头入口 | GCP/Azure |
| IMDSv2 | 先取 token | AWS |
| socket 只读 | 换能力/内核 | 停 |
| 无 `docker` 客户端 | curl API | Unix socket |
| RBAC 严格 | 只读端点 | 停 |
| 对象私有 | 预签名/凭证 | 看权限 |

边界：容器内 root ≠ 宿主 root；`CAP_SYS_ADMIN` 才可能挂载；内核漏洞依 `uname -r`；云凭证有范围与时效；元数据访问可能被网络策略阻断。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| SSRF | 元数据 | 需头 |
| 环境变量 | DB/密钥 | 只读 |
| 挂载 | `/host`/`/proc/1/root` | 权限 |
| 日志 | 云凭证 | 泄露 |
| 镜像 | 层里的密钥 | 本地分析 |
| CI/CD | 变量 | 授权 |
| 对象存储 | 公开桶 | 范围 |

## 06 差异速查

| 云 | 元数据 | 头/方法 |
|---|---|---|
| AWS | `169.254.169.254` | IMDSv2 token |
| 阿里云 | `100.100.100.200` | 无 |
| 腾讯云 | `169.254.0.23` | 无 |
| GCP | `metadata.google.internal` | `Metadata-Flavor: Google` |
| Azure | `169.254.169.254` | `Metadata: true` |
| 华为云 | `169.254.169.254/openstack` | 无 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 容器判断 | `cat /.dockerenv`/cgroup |
| 能力 | `capsh --print` |
| Docker API | `curl --unix-socket` |
| K8s | `kubectl`/curl |
| 对象存储 | `aws s3`/`ossutil` |
| 记录 | 环境/凭证/结果 |

验证顺序：环境 → 元数据 → 容器 → 原语 → 对象存储。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 环境 | 容器/云/K8s | 定位 |
| 2 元数据 | 地址/头 | 凭证 |
| 3 容器 | 能力/挂载/socket | 原语 |
| 4 宿主 | 只读验证 | 文件 |
| 5 存储 | 桶/对象 | 数据 |
| 6 记录 | 凭证/范围 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 元数据超时 | 网络策略 | 停/换入口 |
| 401 | 需 token/头 | IMDSv2/头 |
| socket 403 | 权限 | 换原语 |
| 挂载失败 | 能力 | 停 |
| K8s 403 | RBAC | 只读端点 |
| 桶私有 | 凭证/签名 | 找泄露 |
| 预签名错 | 路径/过期 | 逐项改 |

## 10 记录与复现

- [ ] 环境/云厂商
- [ ] 元数据地址/头
- [ ] 凭证来源/权限
- [ ] 容器原语
- [ ] 宿主/其他 Pod
- [ ] 对象存储范围

| 记录项 | 内容 |
|---|---|
| 环境 | 容器/VM/K8s |
| 云 | AWS/阿里/腾讯 |
| 凭证 | 临时/角色 |
| 原语 | socket/privileged |
| 结果 | 文件/对象 |

相关： [SSRF 与 XXE 进阶](/knowledge/web-server-fetch-advanced/)、[内网信息收集](/knowledge/web-internal-recon/)、[Docker 与虚拟网络](/knowledge/web-docker-lab/)、[渗透流程](/knowledge/web-pentest-flow/)。
