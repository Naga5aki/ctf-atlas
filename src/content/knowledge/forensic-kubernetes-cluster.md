---
title: "Kubernetes 集群取证：概念、命令与实战"
summary: "梳理集群、节点、工作负载与容器层级，用 kubectl 追踪网络和持久存储，并在多节点实战中关联日志、恢复业务与复核历史。"
module: "Forensics"
track: "服务器取证"
topic: "服务器集群"
tags: ["容器", "日志"]
status: "已整理"
sourceIds: ["0047c3d2f371", "2530fdc7be10", "c7613f4a6214", "cd60ad7b2b42"]
challengeIds: []
relatedIds: ["forensic-guide-server", "docker-evidence-01", "docker-evidence-03", "docker-evidence-04", "forensic-database-recovery", "forensic-server-services"]
updated: "2026-10-01"
---

手里是多节点容器集群检材：可能包含控制平面对象导出、节点容器运行时（containerd/CRI 或 Docker）、kubelet 目录与后端 NFS/PV 存储快照。本页回答：声明写在哪、容器跑在哪台节点、端口怎么转发、持久数据落在哪个目录、历史容器与仿真容器怎么分开。原始材料保持只读。

**先定集群取证路线 → 分清控制平面、节点与运行时 → 从控制器、API 对象、网络与存储追到后端目录 → 用 kubectl 与 CRI 受控采集 → 在隔离副本恢复多节点应用并核对历史时间线。**

<span id="01-阅读路线与取证主线"></span>

## 01 先定集群取证路线与材料边界

手里是多台主机上的容器化应用，还分不清声明写在哪、容器实际跑在哪、持久数据又落在哪。先固定主机身份和集群对象，再决定往下读哪一节。

操作顺序：确认主机身份与时间，保存集群对象和节点状态，沿 Pod、容器、卷和网络追到磁盘与日志。

**1. 先按这个顺序做首轮。** Kubernetes（简称 K8s）负责在多台主机上调度、维护容器化应用。同时记下**应用的声明、实际运行的位置，以及持久数据的存放位置**。顺序是：确认各主机身份与时间，保存集群对象及节点状态，找到目标工作负载，沿 Pod、容器、卷和网络追踪，核对磁盘与日志，必要时在隔离副本中恢复业务。

**2. 不知道先读哪一节时，对这张表。**

| 要解决的问题 | 阅读位置 | 核心输出 |
| --- | --- | --- |
| 不熟悉术语和层级 | 02—04 架构、工作负载、API 对象 | 一张对象关系图 |
| 入口端口、配置、数据在哪里 | 05—07 网络、存储、配置与身份 | Service → Pod；Pod → PVC → PV → 后端路径 |
| 如何查询和固定状态 | 08—09 kubectl 与节点证据 | 对象 JSON、完整 ID、日志、配置和采集时间 |
| 多机环境无法正常启动 | 10—11 存储定位与恢复实战 | 每个故障的事件、依赖、调整与复核结果 |
| 如何区分历史与仿真结果 | 12—14 历史身份、业务关联与交付 | 历史对象、采集对象、实验对象分别记录 |

**3. 命令放在对得上的环境里。** 本篇命令默认采用 Kali/Linux shell。`/mnt/evidence` 表示只读材料挂载点，`/work/output` 表示分析输出目录。需要访问集群或节点的命令，放在已核对身份的采集会话或隔离实验环境执行。没有运行接口时，从保全的对象 JSON、YAML、节点目录与存储快照开始。

本节已核对各主机身份、采集时间，以及声明、运行位置和持久数据分别落在哪一类材料里；没有运行接口时，缺的是集群查询，改从已保全的对象 JSON、YAML、节点目录与存储快照继续。首轮输出能对上上面这张表里的某一行，一并留存主机身份与时间、集群对象、节点状态、目标工作负载，以及磁盘和日志的核对记录。

<span id="02-架构控制平面节点与运行时"></span>

## 02 分清控制平面、工作节点与容器运行时

手里是多台主机和一份集群对象，还分不清控制平面、工作节点和外部依赖各管什么。先把物理部署和逻辑对象分开，再往下对组件职责和运行时。

操作顺序：先分物理部署和逻辑对象，再对每个组件读什么，对上节点实际用的运行时。


### 02.1 先区分物理部署与逻辑对象

集群图画在一起时，容易把命名空间当成一台主机。先看物理部署，再看逻辑对象，对上 Pod 实际落在哪台 Node。

操作顺序：先读物理部署，再读逻辑对象，对上 Namespace、Node 和 Pod 的对应关系。

**1. 按这张图把两层分开。**

```text
物理部署
集群 Cluster
├─ 控制平面 Control Plane（可一台，也可多台）
│  ├─ kube-apiserver       接收 Kubernetes API 请求
│  ├─ etcd                保存集群对象与配置状态
│  ├─ kube-scheduler      为未分配节点的 Pod 选择节点
│  └─ controller-manager  持续协调对象的期望状态与实际状态
├─ 工作节点 Node
│  ├─ kubelet → CRI → containerd / CRI-O / 其他兼容运行时
│  ├─ 网络插件 CNI、服务转发实现
│  └─ Pod → 一个或多个 Container
└─ 外部依赖：NFS、数据库、镜像仓库、负载均衡等
   外部依赖服务器不一定注册为 Kubernetes Node

逻辑对象
Namespace apps
├─ Deployment → ReplicaSet → Pod → Container
├─ Service → selector / EndpointSlice → 后端 Pod
├─ ConfigMap / Secret → 环境变量或挂载文件 → Container
└─ PVC → 集群级 PV → NFS / CSI / 本地存储
```

**2. 两张图各记各的。** Namespace 是资源的逻辑范围，不是一台主机。一个命名空间的 Pod 可以分布在多台 Node 上，一台 Node 也可以运行多个命名空间的 Pod。控制平面节点在条件允许时同样能运行应用 Pod。角色用组件和节点对象核对，主机名只作名称线索。

本节已核对控制平面、工作节点、外部依赖，以及 Namespace 里的 Deployment、Service、配置和 PVC 各属于哪一层；主机名对不上角色，或外部依赖服务器没有注册为 Kubernetes Node 时，分别写明。同一张图上能指出 Pod 所在的 Node，以及它属于哪个 Namespace，一并留存这张物理部署与逻辑对象对照，以及用来核对角色的节点对象。

### 02.2 每个组件承担什么职责

组件名字已经对上，还不知道调查时该读哪一项。按表逐个组件记下职责和要读的材料。

操作顺序：对组件名，读它负责的状态，对上调查时要打开的配置、事件或日志。

**1. 按这张表读每个组件。**

<details>
<summary>展开 Kubernetes 核心组件职责与取证读取表</summary>

| 组件 | 职责 | 调查时重点读取 |
| --- | --- | --- |
| kube-apiserver | 集群 API 的统一入口，处理认证、授权与准入 | 地址、证书、启动参数、审计策略与审计记录 |
| etcd | 保存 API 对象的持久状态 | 实际数据目录、快照、成员配置、采集一致性；它不保存所有业务卷内容 |
| kube-scheduler | 根据资源与调度约束为 Pod 选择 Node | `spec.nodeName`、FailedScheduling、资源不足与约束 |
| kube-controller-manager | 运行多类控制器，协调副本、节点与对象生命周期 | ownerReferences、对象创建删除、状态变化 |
| cloud-controller-manager | 在采用云集成时连接云厂商能力 | 云节点、负载均衡、路由及云端记录；本地集群可以没有它 |
| kubelet | 在节点上维护 Pod，调用运行时、挂载卷、执行探针 | 服务参数、节点配置、Pod UID 目录、挂载事件与日志 |
| 容器运行时 | 管理镜像、sandbox、容器和执行任务 | CRI 端点、完整容器 ID、镜像摘要、日志路径、snapshotter |
| CNI 插件 | 为 Pod 提供网络连接 | 插件配置、Pod 网段、网络命名空间、节点路由 |
| kube-proxy 或替代实现 | 实现 Service 到后端的流量转发 | Service、EndpointSlice、转发规则；部分 CNI 可承担该能力 |
| CoreDNS | 提供集群服务名解析 | DNS Service、配置、Pod 状态与查询结果 |

</details>

**2. 控制平面清单先找本机实际路径。** 常见 kubeadm 环境以静态 Pod 部署控制平面，清单位于 `/etc/kubernetes/manifests/`。这不是所有发行版的统一布局。托管集群也可能无法取得控制平面磁盘，应记录可见范围。组件关系见 [Kubernetes 组件说明](https://kubernetes.io/docs/concepts/overview/components/)。

本节已核对每个可见组件的职责，以及这次能读到的地址、数据目录、事件或日志；发行版布局不同，或托管集群拿不到控制平面磁盘时，写明可见范围。组件名和表中的“调查时重点读取”能对上同一份材料，一并留存静态 Pod 清单路径、各组件启动参数，以及看不到控制平面磁盘时的范围说明。

### 02.3 Docker、containerd、CRI 与 Kubernetes 的关系

节点上有容器，但 `docker ps` 是空的，或者根本没有 `docker`。先确认这台 Node 实际用的运行时，再决定查哪一个接口。

操作顺序：先看 containerRuntimeVersion，再对 kubelet 端点和 socket，对上 CRI 或 Docker 的那一个实例。

**1. 先分清 Docker Engine 和 CRI。** **Docker Engine** 可以独立运行容器，使用 Docker API 管理对象；它通常也使用 containerd 等组件。**CRI** 是 kubelet 与容器运行时之间的接口。现代 Kubernetes 可以通过 CRI 直接使用 containerd 或 CRI-O，不要求安装 Docker Engine。

**2. 核对这一版是否还带着 dockershim。** 较老环境可能使用内置 dockershim；Kubernetes 从 v1.24 移除了内置 dockershim。继续使用 Docker Engine 的集群需要兼容适配层，例如 cri-dockerd，或采用发行版提供的对应实现。

**3. 再看 Pod sandbox 和调用链。** **Pod sandbox** 提供 Pod 运行的基础环境；一个 Pod 可含多个业务容器。使用 runc 的 containerd 路径常见为 `containerd → containerd-shim → runc`，其他运行时实现可能不同。

**4. 用节点字段选定后面要查的接口。** 查看 Node 的 `containerRuntimeVersion`，再比对 kubelet 端点参数、节点服务和实际 socket。没有 `docker` 或 `docker ps` 为空时，继续查 CRI。Docker 管理的 containerd 与独立 containerd 可能同时存在，后续查询使用刚确认的接口和数据根，不混查另一个实例。

本节已核对这台 Node 的 `containerRuntimeVersion`、kubelet 端点和实际 socket；`docker` 不存在或 `docker ps` 为空时，CRI 端点还没对上，就继续查运行时，不在这里结束。后面的查询使用的是刚确认的那一个接口和数据根，一并留存运行时版本、端点参数、服务名和 socket 路径。

<span id="03-工作负载层级与-pod-生命周期"></span>

## 03 从控制器追到 Pod 容器层级与状态

手里是一堆工作负载名字，还分不清谁在管理 Pod、Pod 里面有几层、状态为什么停在这里。先看控制器，再看 Pod 内部，最后对状态、探针和调度约束。

操作顺序：先看谁在管理 Pod，再看 Pod 里面的容器层级，对上状态、探针和调度约束。


### 03.1 工作负载控制器如何管理 Pod

对象列表里同时有 Deployment、Service 和 PVC，还分不清谁拥有 Pod。按表看每个对象管什么，再单独核对所有权。

操作顺序：先认对象类型，再看它管的是副本、身份、任务还是节点覆盖，对上 owner 和选择器。

**1. 按这张表认对象。**

| 对象 | 层级与用途 | 调查重点 |
| --- | --- | --- |
| Pod | 最小调度单位，包含一个或多个容器 | namespace、UID、Node、IP、容器状态、卷与配置引用 |
| ReplicaSet | 按标签选择器维持指定数量的 Pod | 由哪个 Deployment 管理，创建了哪些 Pod |
| Deployment | 维护 ReplicaSet，实现声明式更新与副本管理 | Pod 模板、镜像版本、replicas、更新策略、旧 ReplicaSet |
| StatefulSet | 管理具有稳定身份及持久存储需求的 Pod | Pod 序号、稳定名称、volumeClaimTemplates 与各实例 PVC |
| DaemonSet | 在符合条件的节点上运行 Pod | 节点覆盖、日志/网络代理、宿主机挂载和权限 |
| Job | 管理需要完成的任务 | 完成/失败次数、启动参数、输出和创建的 Pod |
| CronJob | 按计划创建 Job | schedule、timeZone、并发规则、最近执行与历史保留 |
| HPA | 根据指标调整工作负载副本数 | 指标来源、min/maxReplicas、扩缩容事件；不是业务执行容器 |
| PDB | 约束某些主动中断造成的不可用副本数 | 可用性与驱逐限制；不保证抵御所有故障 |
| CRD / Operator | 扩展资源类型，由控制器管理应用 | 实际安装的自定义类型与生成对象；`get all` 不会完整枚举它们 |

**2. 网站这条链单独画出来。** 典型网站采用 **Deployment → ReplicaSet → Pod → Container**。Service 提供访问入口，但不是 Pod 的上级控制器；PVC 提供存储引用，同样不属于这条所有权链。StatefulSet、DaemonSet、Job 有各自的管理路径，不能全部套用 Deployment 模型。[工作负载管理说明](https://kubernetes.io/docs/concepts/workloads/controllers/)

本节已核对目标 Pod 的控制器类型、所有者，以及 Service、PVC 是否只是引用而不是所有者；`get all` 没有列出的自定义类型，要按实际安装的 CRD 和 Operator 再查。沿 Pod 的 ownerReferences 核对所有者的 kind、name 和 UID；选择器只用于筛选关联候选，不单独证明控制关系，一并留存工作负载对象、它创建的 Pod，以及各自的 UID。

### 03.2 一个 Pod 内部还有哪些层级

Pod 已经找到，应用却停在初始化，或者某个文件只在其中一个容器里。先分清这个 Pod 里有哪几类容器，再看它们是否共享目录。

操作顺序：先认业务容器、init、sidecar 和临时容器，再对 volumeMounts，对上文件在哪个容器里可见。

**1. 先认业务容器。** **业务容器（containers）** 执行应用。同一 Pod 的容器通常共享网络命名空间和 Pod IP，可以通过 localhost 通信。挂载哪些卷仍按每个容器配置判断。

**2. 再看初始化是否已经走完。** **初始化容器（initContainers）** 里，普通 init 容器按顺序完成后才启动业务容器。下载或初始化失败时，应用可能卡在 Init 状态。

**3. 伴生容器按实际字段读。** **伴生容器（sidecar）** 与主应用协作，例如代理或日志收集。它可以作为普通并行容器部署；较新版本还支持具有重启策略的原生 sidecar，读取实际字段与版本。

**4. 临时容器单独记成一次调试。** **临时容器（ephemeralContainers）** 用于调试既有 Pod。存在它可能说明进行过调试。创建它会修改 Pod，不能作为无影响的历史采集方式。

**5. 文件是否可见，看每个容器的挂载。** Pod 中的多个容器不必拥有相同文件系统。共享目录来自明确的 volumeMounts。只凭相同 Pod 名，不能认定任意文件对所有容器都可见。

本节已核对这个 Pod 里的业务容器、initContainers、sidecar、ephemeralContainers，以及每个容器的 volumeMounts；应用停在 Init，或文件只在其中一个容器里时，写明停在哪一个容器、哪一个挂载。容器名、状态和 volumeMounts 来自同一份 Pod 对象，一并留存Pod 对象里的容器列表、初始化状态和挂载配置。

### 03.3 状态、探针与调度约束

Pod 列表上的状态已经看到，还不知道该读探针、资源还是调度约束。先把字段含义对上，再决定下一步读哪里。

操作顺序：先读 phase 和 STATUS，再对探针、资源与调度约束，重启后用 UID 和 lastState 分开旧实例。

**1. 按这张表决定下一步读什么。**

| 字段/状态 | 实际含义 | 下一步 |
| --- | --- | --- |
| Pod phase：Pending / Running / Succeeded / Failed / Unknown | Pod 生命周期的粗粒度状态 | 再查 conditions、容器状态与事件 |
| `STATUS` 列的 ContainerCreating、CrashLoopBackOff 等 | CLI 展示的原因或等待状态，不都属于 Pod phase | 读取 Waiting/Terminated reason、message、exitCode |
| `READY 0/1` | 尚未满足容器就绪条件 | 看 readiness、初始化、依赖与应用日志 |
| readinessProbe | 影响容器是否就绪及常规 Service 后端选择 | Running 仍可能未就绪；同时检查 publishNotReadyAddresses |
| livenessProbe | 检测失败达到阈值可触发容器重启 | 核对探针配置与重启前日志 |
| startupProbe | 为较慢启动提供独立启动判断 | 成功前其他探针受到抑制；失败也可能导致重启 |
| requests / limits | 调度需求与运行资源约束 | FailedScheduling、OOMKilled、CPU 限制与节点压力 |
| nodeSelector / affinity | 限定或偏好调度位置 | 本地镜像所在节点是否满足约束 |
| taints / tolerations | 节点排斥规则与容忍关系 | 容忍污点不等于一定调度到该节点 |

**2. 重启之后先比较 UID。** 容器重启时 Pod UID 可能不变；Pod 删除后重建，即使名字相似也会换 UID。保存当前容器 ID，再分别读重启计数和 `lastState`。旧实例日志按旧 ID 和时间查。

本节已核对当前 Pod phase、STATUS 列、探针结果，以及调度约束是否把 Pod 留在 Pending；容器重启或 Pod 重建后，旧实例的 `lastState` 和旧日志还没按旧 ID 对上时，写明缺口。UID、容器 ID、重启计数和 `lastState` 写在同一条记录里，一并留存Pod 状态、事件、探针配置，以及当前容器 ID。

<span id="04-api-对象命名空间与-yaml"></span>

## 04 拆读 API 对象四层结构与关联字段

手里是一份对象 JSON 或 YAML，还分不清名字、期望状态和节点上报的状态。先按四层读对象，再分命名空间和集群级，最后拆一份 Deployment。

操作顺序：先看对象四层，再分命名空间和集群级，对上一份 Deployment 里的应用、配置和数据。


### 04.1 读对象时先看这四层

打开一份对象后，字段很多，还不知道哪一段是身份、哪一段只是上报状态。先按四层读，再核对标签和所有者。

操作顺序：先看类型和身份，再分开 spec 与 status，对上标签、注解和 ownerReferences。

**1. 按这四层读。**

| 层级 | 关键字段 | 判读 |
| --- | --- | --- |
| 类型 | `apiVersion`、`kind` | 对象所属 API 组及类型，兼容性随版本变化 |
| 身份 | `metadata.name`、namespace、UID、creationTimestamp | 名称可复用；UID 标识这次对象实例，创建时间不是应用首次使用时间 |
| 期望状态 | `spec` | 声明期望的镜像、副本、挂载、网络和调度条件 |
| 观察状态 | `status` | 控制器或节点上报的实际状态，应与采集时间对应 |

**2. 关联时核对类型、名称和 UID。** `labels` 用于分类与选择器匹配；`annotations` 保存额外说明或组件约定；`ownerReferences` 指向所有者实例。名称或标签相似不等于存在所有权关系。

**3. 这几个字段按原样留下。** `resourceVersion` 保存原字符串，用于版本和并发控制，不换算时间。`generation` 用来看期望状态是否变更。`managedFields` 用来看字段由哪个管理器处理；要查谁改了什么，继续找 API 审计和运维记录。`finalizers` 表示对象可能正在等待删除处理。先保存状态和日志。移除 finalizer 会改变删除处理，取证时不靠它清掉卡住的对象。

[API 对象说明](https://kubernetes.io/docs/concepts/overview/working-with-objects/)

本节已核对对象的 apiVersion、kind、名称、namespace、UID，以及 spec 和 status 各自对应的采集时间；只有 `managedFields`、还没有 API 审计时，谁改过字段仍然未确认。所有权用类型、名称和 UID 对上，而不是只靠相似的名称或标签，一并留存原对象，以及原样保留的 `resourceVersion`、`generation`、`managedFields` 和 `finalizers`。

### 04.2 命名空间与集群级对象

查询时有的对象要加命名空间，有的加了反而对不上。先分清这个对象是命名空间级还是集群级。

操作顺序：先看对象范围，命名空间级加上 -n 或 -A，集群级对象不再加 -n。

**1. 按这张表决定要不要写命名空间。**

| 范围 | 常见对象 | 查询规则 |
| --- | --- | --- |
| 命名空间级 | Pod、Deployment、Service、PVC、ConfigMap、Secret、ServiceAccount、Role、RoleBinding | 用 `-n apps` 指定；`-A` 枚举全部可见命名空间 |
| 集群级 | Node、Namespace、PV、StorageClass、ClusterRole、ClusterRoleBinding、CRD | 不属于某个 namespace，无需 `-n` |

**2. 同名对象先把命名空间写全。** `default` 是未指定命名空间时常用的默认范围，`kube-system` 常用于系统组件。实际应用可以部署在任何命名空间。同名 Service、PVC、Secret 在不同命名空间中是不同对象。Namespace 本身不是完整的网络或安全隔离机制，仍需 RBAC、NetworkPolicy 与运行权限配合。

本节已核对对象是命名空间级还是集群级，以及它的 namespace 或集群范围；同名对象出现在多个命名空间时，还没写全 namespace 的那几个要补上。查询命令和对象范围一致：命名空间级用了 `-n` 或 `-A`，集群级没有误加 `-n`，一并留存对象名、namespace 或集群级标记，以及这次的查询范围。

### 04.3 实际拆读一份 Deployment

一份 Deployment YAML 已经打开，还要分别找到镜像、网站文件和密码从哪来。下面是构造示例，只用于阅读字段。

操作顺序：先认 Deployment 和标签，再对镜像、卷和配置引用，对上容器端口和实际入口不是同一层。

**1. 先声明这是构造示例。** 对应的 PVC、ConfigMap、Secret 与镜像必须另行核对，不能直接当作完整恢复方案提交。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portal
  namespace: apps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: portal
  template:
    metadata:
      labels:
        app: portal
    spec:
      containers:
        - name: web
          image: lab/web-runtime:7.4
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
          envFrom:
            - configMapRef:
                name: portal-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: database-auth
                  key: password
          volumeMounts:
            - name: site
              mountPath: /app
      volumes:
        - name: site
          persistentVolumeClaim:
            claimName: site-data
```

**2. 按这份 YAML 逐项往下找。** `apps/portal` 是 Deployment，`template` 是待创建的 Pod 模板；`app: portal` 用于匹配。容器镜像为 `lab/web-runtime:7.4`，先记名称，再核对实际镜像摘要。`site` 卷引用 `apps/site-data`，挂到 `/app`；查网站文件沿这个 PVC 继续找后端。普通配置读 `apps/portal-config`，密码读 `apps/database-auth` 的 `password` 键。`containerPort: 80` 只是容器端口声明；要查宿主机入口，再看 Service 或其他实际发布配置。

**3. 磁盘上的 YAML 先当成候选定义。** 它是否提交过、提交到哪个集群、是否被后续修改，应结合 API 对象、审计、运维记录与时间核对。文件存在时，部署是否成功要另外用 API 对象和记录证明。

本节已核对Deployment 名称、Pod 模板标签、镜像名、卷引用、配置引用和容器端口声明；镜像摘要、PVC 后端、ConfigMap、Secret，以及宿主机入口还没分别核对时，写明缺哪一项。字段来自这份 YAML，并且和另行保存的 API 对象或卷数据对得上，一并留存这份声明，以及随后核对的镜像摘要、PVC 和配置对象。

<span id="05-网络podserviceingress-与-dns"></span>

## 05 对齐 Pod、Service、Ingress 与 DNS 端口链路

请求已经到达某个地址，还分不清它停在节点、Service、Ingress 还是 Pod。先分四种地址，再读端口，最后对 DNS 和网络策略。

操作顺序：先分清四种地址，再读 Service 类型和端口，对上 DNS、Ingress 与网络策略。


### 05.1 先分清四种地址

日志里有一个 IP，还不知道它是节点、Pod、Service 还是外部入口。先把四种地址分开，再沿请求路径往下对。

操作顺序：先认地址属于谁，再沿入口追到 Pod，对上这一时刻的后端。

**1. 按这张表认地址。**

| 地址 | 谁拥有 | 取证含义 |
| --- | --- | --- |
| Node IP | 主机/节点 | 节点通信与部分对外入口 |
| Pod IP | Pod 网络接口 | 某时刻的应用实例；删除重建后可能变化或被复用 |
| ClusterIP | Service | 集群内部稳定入口，映射到选中的后端 |
| 外部域名/地址 | Ingress、Gateway 或负载均衡 | 外部流量入口，不等于后端 Pod 身份 |

**2. 沿这条路径逐跳核对。** 常见请求路径是 `客户端 → 节点/负载均衡 → Service → EndpointSlice → Pod → 容器进程`。采用 Ingress 时，还需加入实际 Ingress Controller 与路由规则。NAT、代理和地址复用会影响归属。日志中的一个 IP 要和同一时刻的后端、连接记录一起看，才能谈到操作者。

本节已核对这个地址是 Node IP、Pod IP、ClusterIP，还是外部域名或负载均衡地址；只有一个 IP、没有同一时刻的 EndpointSlice 或连接记录时，操作者身份仍然未确认。地址、Service、EndpointSlice 和 Pod 能放进同一次采集，一并留存四种地址的取值、采集时间，以及 Ingress 或负载均衡规则（如果这次有）。

### 05.2 Service 类型与端口层级

Service 已经找到，还分不清 80、容器端口和 nodePort 各是哪一层。先认类型，再把三个端口对到后端。

操作顺序：先认 Service 类型，再对 port、targetPort 和 nodePort，对上 EndpointSlice 和转发规则。

**1. 按这张表认类型。**

| 类型 | 用途 | 核验重点 |
| --- | --- | --- |
| ClusterIP | 集群内部访问 | clusterIP、selector、EndpointSlice |
| NodePort | 在配置允许的节点地址上发布端口 | nodePort、节点地址范围、过滤规则、转发实现 |
| LoadBalancer | 请求外部负载均衡能力 | 实际控制器/云实现与 external 地址，不保证本地环境自动可用 |
| ExternalName | 返回 DNS CNAME 指向外部名称 | externalName；不按普通 Service 转发理解 |
| Headless（`clusterIP: None`） | 不分配通常的虚拟 ClusterIP，便于发现实例地址 | 常配合 StatefulSet；不是第五个 `type` 值 |

**2. 用这份构造示例把端口读开。**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: portal
  namespace: apps
spec:
  type: NodePort
  selector:
    app: portal
  ports:
    - name: http
      port: 80
      targetPort: http
      nodePort: 31080
```

**3. 按这份 Service 往下核对。** `port: 80` 是 Service 端口。`targetPort: http` 找到所选 Pod 中命名为 http 的容器端口。`nodePort: 31080` 是示例节点入口；默认分配范围常为 30000—32767，实际范围和节点地址可能已改。再查后端健康、流量策略和防火墙。普通 `ss` 没有监听进程时仍要查转发规则，Service 可能由规则转发。

[Service 与端口说明](https://kubernetes.io/docs/concepts/services-networking/service/)

本节已核对Service 类型、selector，以及 port、targetPort、nodePort 各自指向的那一层；`ss` 看不到监听进程时，转发规则、节点地址范围和防火墙还要另查。本例的命名 targetPort 对应 Pod 中同名的容器端口，并与 EndpointSlice 的后端端口核对；若 targetPort 是数字，按数字端口核对，不要求另有同名声明，一并留存Service 对象、EndpointSlice、实际 nodePort 范围和节点地址。

### 05.3 DNS、Ingress 与网络策略

Service 已经存在，短名称却可能解析到别的命名空间，或者 Ingress 文件在但外面打不开。沿 DNS、入口和策略逐层看。

操作顺序：先对服务名和 namespace，再看 Ingress 或 Gateway 是否有控制器，对上 NetworkPolicy 和实际监听。

**1. 先把 DNS 名称写全。** 常见完整服务名形如 `database.apps.svc.cluster.local`，集群域不一定是 cluster.local。应用配置的 DB_HOST 应与 namespace、Service 和 Pod 的 resolv.conf 对照。跨命名空间仅使用短名称可能解析到错误对象。

**2. 再看 Ingress 有没有控制器在处理。** Ingress 声明 HTTP/HTTPS 的域名与路径规则；需要实际的 Ingress Controller 才能处理流量。核对 ingressClass、TLS Secret、后端 Service 端口以及控制器配置。一份 Ingress YAML 只说明声明在，网站是否对外开放要看控制器和后端。

**3. Gateway API 只在安装了对应类型时查询。** 它通过 GatewayClass、Gateway、HTTPRoute 等对象拆分入口与路由职责。仅在实际安装相应 API 与控制器的环境查询。缺少这些类型时，记下未安装，不把缺少类型写成集群损坏。

**4. NetworkPolicy 和别的过滤分开记。** NetworkPolicy 约束选中 Pod 的入站或出站流量，依赖支持该策略的网络实现。它与主机防火墙、Service 流量策略、应用认证分别核对。

**5. 访问异常时按这条链定位。** 沿 `DNS → Service → EndpointSlice → Pod Ready → 容器实际监听 → 过滤与应用依赖` 逐层定位。就绪后端存在，说明的是采集时的配置和状态。历史请求是否到达，要看访问日志。

本节已核对完整服务名、Ingress 或 Gateway 的控制器，以及 NetworkPolicy 选中的 Pod；只有 Ingress YAML、没有控制器，或只有就绪后端、没有访问日志时，分别写明。DB_HOST、namespace、Service 和 resolv.conf 是同一条；入口规则能对上实际控制器，一并留存DNS 配置、Ingress 或 Gateway 对象、NetworkPolicy，以及后端就绪状态。

<span id="06-存储卷pvcpvstorageclass-与-nfs"></span>

## 06 从容器挂载经 PVC、PV 追到后端存储

容器里看到一个路径，还不知道文件在节点本地、PVC 还是 NFS 上。先从挂载走到后端，再按卷类型和删除规则核对。

操作顺序：从容器路径走到 PVC、PV 和后端，再按卷类型看痕迹，对上访问模式和删除边界。


### 06.1 从容器路径逐层走到数据后端

容器里有 `/app` 这样一类路径，还不知道对应哪一块存储。从 volumeMounts 开始，一层层走到后端。

操作顺序：从容器挂载找到卷名，再从 PVC 找到 PV，对上 NFS 或 CSI 后端。

**1. 按这条链往下走。**

```text
容器 /app/.env
  ↓ 找该容器 volumeMounts 的 mountPath、name 与 subPath
Pod volumes[name=site]
  ↓ persistentVolumeClaim.claimName = site-data
PVC apps/site-data
  ↓ spec.volumeName = pv-site-data
PV pv-site-data（集群级）
  ↓ spec.nfs.server + spec.nfs.path，或 CSI volumeHandle
存储服务器/卷的实际数据
```

**2. 每一层只回答它自己的问题。** PVC（PersistentVolumeClaim）记录应用需要的存储；PV（PersistentVolume）记录已提供的存储；StorageClass 记录类别和动态制备规则；provisioner/CSI driver 执行后端创建或连接。

**3. Bound 之后继续看挂载和文件。** 看到 PVC 为 Bound 后，继续查 Pod 挂载事件和后端目录。绑定已经完成时，业务文件是否存在、当前能否挂载，要看事件和目录。

**4. 制备方式和等待绑定分开记。** 静态制备先提供 PV 再匹配 PVC；动态制备按 StorageClass 请求创建后端。有 `WaitForFirstConsumer` 绑定模式时，PVC 等待调度决定再绑定可能是正常阶段，需要同时查看 Pod 事件。CSI 的 `volumeHandle` 通常是后端标识，不是可以直接拼接的 Linux 路径。

本节已核对容器路径、volumeMounts、PVC、PV，以及 NFS 路径或 CSI `volumeHandle`；PVC 仍是 Pending，或 Bound 之后后端目录还没打开时，写明停在哪一层。claimName、volumeName 和后端标识来自同一串对象，一并留存Pod 挂载、PVC、PV、StorageClass，以及后端目录或 volumeHandle。

### 06.2 各类卷留下的痕迹不同

路径已经挂进容器，还不知道它会随 Pod 消失，还是留在节点或 NFS 上。先认卷的类型，再换算后端路径。

操作顺序：先认卷的生命周期，再按 subPath 换算路径，到后端确认文件还在。

**1. 按这张表决定去哪找痕迹。**

| 卷/来源 | 生命周期与特性 | 取证动作 |
| --- | --- | --- |
| 容器可写层 | 绑定该容器实例 | 查实际运行时的层、快照与元数据 |
| emptyDir | 随 Pod 创建，Pod 从节点移除时通常删除；同一 Pod 内容器重启可保留 | 查 Pod UID 对应节点目录；介质设为 Memory 时不能预设磁盘有完整内容 |
| hostPath | 挂载 Node 本地路径 | 查实际运行节点的路径，其他节点同名路径可能不同 |
| PVC/PV | 可独立于容器和 Pod 生命周期 | 查绑定关系、后端数据及回收规则 |
| NFS | 使用服务端导出的共享目录 | 查 PV server/path、`/etc/exports`、客户端挂载、权限及网络 |
| ConfigMap / Secret / projected | 将配置或令牌投射到容器 | 查对象版本、键名、挂载及更新时间，不能默认全部持久落盘 |

**2. 把容器路径换成后端路径。** `subPath` 是卷内子目录。PV 根为 `/srv/nfs/lab/site-data`、`subPath: portal`、`mountPath: /app` 时，容器的 .env 候选位置为 `/srv/nfs/lab/site-data/portal/.env`。如果用 `subPathExpr`，先按这个 Pod 的环境和 Downward API 展开 `$(POD_NAME)` 等变量；表达式本身不是目录名。`subPath` 和 `subPathExpr` 不能同时设置。

**3. 算出路径后到后端看文件。** 核对软链、NFS 导出映射和文件内容。计算出路径后仍要确认文件实际存在。

本节已核对卷类型、mountPath、subPath 或展开后的 subPathExpr，以及后端上的候选文件；emptyDir 使用 Memory、hostPath 不在这块节点盘上，或算出的路径在后端不存在时，写明。容器路径和后端文件的相对位置与 subPath 一致，并且文件哈希已经记下，一并留存卷定义、换算后的路径、软链和文件是否存在的记录。

### 06.3 访问模式与删除边界

卷已经绑定，还要判断它能不能被多个节点写，以及删掉 Deployment 会不会删掉数据。先读访问模式，再看回收策略。

操作顺序：先读访问模式，再看回收策略和 finalizers，对上后端文件是否还在。

**1. 按这张表读访问模式。**

| 模式 | 含义 | 易错点 |
| --- | --- | --- |
| ReadWriteOnce（RWO） | 允许单个节点以读写方式挂载 | 不等于仅一个 Pod 可用；同节点可能有多个 Pod |
| ReadOnlyMany（ROX） | 允许多个节点以只读方式挂载 | 声明本身不是取证写保护，要核对实际挂载/后端权限 |
| ReadWriteMany（RWX） | 允许多个节点以读写方式挂载 | 多实例/多主机均可能改写同一业务目录 |
| ReadWriteOncePod（RWOP） | 限制单个 Pod 使用，需相应 CSI 支持 | 与 RWO 的约束粒度不同 |

**2. 删除对象之前先看回收规则和文件。** 回收策略 **Retain** 通常保留后端供人工处理；**Delete** 可能由驱动删除关联后端；旧环境还可能出现已弃用的 Recycle。删除 Deployment、Pod、PVC、PV 对存储的影响不同，需结合回收策略、provisioner 规则、finalizers 与真实文件状态。取证时不通过删除 PVC 测试数据是否还在。[持久卷与访问模式](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

本节已核对访问模式、回收策略，以及后端文件现在是否还在；对象已经删除、回收策略或 provisioner 规则还没读到时，数据是否残留仍然未确认。访问模式、回收策略和后端标识属于同一份 PV；文件系统卷核对目录与文件，块卷核对设备或快照，远端后端注明实际取得的范围，一并留存PV 的访问模式、回收策略、finalizers 和后端文件状态。

<span id="07-配置身份与权限"></span>

## 07 核对 ConfigMap、Secret、ServiceAccount 与 RBAC

应用配置和集群身份混在一起，还分不清容器读到的是哪一份、当前身份能看哪些对象。先看配置怎么进容器，再对 RBAC，最后分清凭据和 Dashboard。

操作顺序：先看 ConfigMap 和 Secret 怎么进应用，再对 kubeconfig、ServiceAccount 和 RBAC，对上凭据读取和 Dashboard 的边界。


### 07.1 ConfigMap 与 Secret 如何进入应用

配置对象已经找到，应用里的值却和当前对象不一致。先看它是以环境变量还是文件进入容器，再分开保存三份值。

操作顺序：先认引用方式，再对启动时的值和当前对象，对上应用实际读到的那一份。

**1. 按这张表核对引用。**

| 对象/引用 | 用途 | 实际核验 |
| --- | --- | --- |
| ConfigMap | 普通配置、环境值或配置文件 | name、namespace、data/binaryData、挂载键、envFrom 与 env 引用 |
| Secret | 密码、令牌、证书、私有仓库凭据等 | type、键名、引用对象及有效期；内容单独受控保存 |
| env / envFrom | 将值或引用注入容器环境 | 启动时的环境与当前对象值可能不同 |
| volumes / volumeMounts | 将对象键投射为文件 | items、mountPath、subPath、readOnly 与实际读取路径 |
| imagePullSecrets | 让运行时获取私有镜像 | 引用的 Secret 与 registry、节点拉取事件 |

**2. 先分清编码和加密。** Secret 的 `data` 是 Base64 编码，**不是加密**。是否在 etcd 加密保存，要看实际配置。

**3. 变更之后按这三种情况看应用读到什么。** 普通文件挂载更新可能有延迟，还要查应用是否缓存。环境变量不会随 ConfigMap 自动更新；记录容器启动时取的值。subPath 挂载不会接收这种自动更新。

**4. 三份值分开保存。** 把当前配置、启动值和应用实际读取值分别保存。[ConfigMap 更新](https://kubernetes.io/docs/concepts/configuration/configmap/)、[Secret 说明](https://kubernetes.io/docs/concepts/configuration/secret/)

本节已核对ConfigMap 或 Secret 的名字、键、引用方式，以及当前对象值和启动时的值；应用有缓存，或 subPath、环境变量不会自动更新时，实际读取值还要另取。对象键、容器引用和读到的值能放在同一条记录里。Secret 内容单独受控保存，一并留存对象版本、键名、挂载或环境引用，以及当前值、启动值和实际读取值。

### 07.2 kubeconfig、ServiceAccount 与 RBAC

能列出一部分对象，另一部分是 Forbidden 或看不见。先分清 kubeconfig、ServiceAccount 和绑定各自决定什么。

操作顺序：先看 kubeconfig 的 context，再看 ServiceAccount 和绑定，对上这次请求实际被允许的动作。

**1. 先读 kubeconfig 里的 context。** **kubeconfig** 保存集群地址、用户认证方式及 context。context 将 cluster、user 与可选 namespace 组合起来；常见位置是 `~/.kube/config`，kubeadm 环境还可能有 `/etc/kubernetes/admin.conf`。

**2. 再看 Pod 用的是哪个 ServiceAccount。** **ServiceAccount** 为 Pod 或应用提供访问 API 的身份。Pod 的 `serviceAccountName` 指定使用哪个账号。账号本身不自动获得管理员权限。

**3. 权限看 Role 和绑定，不看账号名字。** **Role / ClusterRole** 定义允许的资源、子资源与操作。Role 在命名空间内生效，ClusterRole 可定义集群级及可复用规则。**RoleBinding / ClusterRoleBinding** 将权限关联到用户、组或 ServiceAccount。RoleBinding 可以引用 ClusterRole，但授权仍限绑定所在命名空间；ClusterRoleBinding 可以扩大到集群范围。

**4. 每个动作和子资源分开试。** `get`、`list`、`watch` 与 `create`、`update`、`patch`、`delete` 是不同权限；`pods/log`、`pods/exec` 等子资源也单独授权。`-A` 只扩大请求范围，**不会绕过 RBAC**。不可见、Forbidden 与对象确实不存在必须分别记录。[RBAC 实践](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)

本节已核对context、ServiceAccount，以及这次被允许的动词和子资源；不可见、Forbidden 和对象不存在要分开写；还没区分开的，不能合成一个“没有这个对象”。同一条记录里有身份、资源、动词和返回结果，一并留存kubeconfig 的 context 说明、绑定对象，以及 can-i 或实际请求的结果。凭据本身不放进普通报告。

### 07.3 凭据读取与 Dashboard 的边界

需要读对象，但 kubeconfig 里有 `exec` 插件，或者有人准备先登录 Dashboard。先静态看配置，再决定要不要签发短期凭据。

操作顺序：先静态审阅 kubeconfig，只把隔离目标用于恢复会话，读数据时先走 API 和文件。

**1. 查询之前先看认证会不会跑到外部。** 先静态审阅工作副本 kubeconfig 的地址、证书路径、认证方式和 `exec` 插件，避免未经核对的外部认证程序被查询操作触发。只将指向隔离目标的配置用于恢复会话。输出目录采用受限权限。token、私钥或密码不放入普通报告。

**2. 业务数据先按 API、节点文件和卷检查。** Dashboard 可浏览应用对象。镜像或 PVC 缺失时，管理员 token 不会把镜像和卷补回来。它的 namespace、Service 和端口从实际部署查。

**3. 登录只在需要页面时做。** 【仅在副本/仿真/授权环境执行】确需登录 Dashboard 时，先确认已有 ServiceAccount 及权限绑定，再签发短期凭据。只为读取数据不必先修 Dashboard。

本节已核对kubeconfig 的地址、证书路径、认证方式，以及 Dashboard 的实际 namespace、Service 和端口；镜像或 PVC 缺失时，页面登录不能代替这两项材料。读取来自 API、节点文件或业务数据；短期凭据只出现在有记录的恢复会话里，一并留存审阅过的 context 说明、权限绑定，以及受控保存的凭据使用记录。

<span id="08-kubectl-使用与状态采集"></span>

## 08 用 kubectl 受控采集集群状态与日志

准备查询集群，还没固定 context、输出目录和这次能看的权限。先看命令结构，再保存对象，然后按目标读日志，最后把读取和恢复分开。

操作顺序：先固定 context 和输出，保存集群与工作负载，按目标读字段、事件和日志，把读取和恢复分开记。


### 08.1 命令结构、范围和输出

终端里已经能敲 kubectl，还没确认它连的是哪一个 context。先看命令结构，再把工作配置和输出目录固定下来。

操作顺序：先看命令结构，固定 KUBECONFIG 和 context，记下时间、错误和权限。

**1. 先按这个结构读每一条命令。**

```text
kubectl [全局选项] <操作> <资源类型> [对象名] [选项]
例：kubectl --context lab-forensics get pod portal-demo -n apps -o yaml
```

**2. 参数和操作按这张表选用。**

| 参数/操作 | 含义 | 使用要点 |
| --- | --- | --- |
| `--kubeconfig` | 指定连接配置 | 可避免使用分析机默认集群 |
| `--context` | 指定配置中的上下文 | 每次采集对应同一个经核对的目标 |
| `-n` / `--namespace` | 指定命名空间 | namespaced 对象使用，PV/Node 等不需要 |
| `-A` / `--all-namespaces` | 查询全部可见命名空间 | 不证明权限与历史范围完整 |
| `get` | 获取对象或列表 | `-o wide` 便于阅读；JSON/YAML 用于字段与关联保全 |
| `describe` | 展示状态、依赖与关联事件 | 便于排障，不能替代完整对象 JSON |
| `-o json` / `-o yaml` | 结构化输出 | 记录对象 UID、版本与采集时间 |
| `-o jsonpath=...` | 提取指定字段 | 列表与单对象结构不同，需检查空值 |
| `-l` | 按 label selector 筛选 | 标签可变化或复用，仍需 UID 核对 |
| `--field-selector` | 按支持的对象字段筛选 | 不支持任意 JSON 字段 |
| `logs -c` | 选择一个容器读取日志 | 多容器 Pod 要明确目标，init/sidecar 也可能有关键日志 |
| `logs --previous` | 读取该 Pod 中该容器前一个实例的可用日志 | 不是全部历史 Pod 的日志档案 |

**3. 在已审阅的工作配置里固定 context。** 以下示例统一使用已审阅的工作配置。`CTX` 要改成 `get-contexts` 中确认的隔离目标；同一终端中设置一次后，后续各节继续使用它。

```bash
KCFG=/work/input/lab-kubeconfig.yaml
export KUBECONFIG="$KCFG"
CTX='lab-forensics'
umask 077
OUT=/work/output/k8s
mkdir -p "$OUT"

kubectl config get-contexts
kubectl --context "$CTX" config view --minify
kubectl --context "$CTX" version --client -o yaml
kubectl --context "$CTX" auth can-i list pods --all-namespaces
kubectl --context "$CTX" auth can-i get pods --subresource=log -n apps
date -u +'%Y-%m-%dT%H:%M:%SZ' > "$OUT/collection-start.txt"
```

**4. 查询后把这些一起保存。** 保存请求时间、标准错误、退出状态和所用权限。多次查询之间应用状态可能已经变化。`config view` 默认遮蔽部分敏感值，不用 `--raw` 批量公开凭据。列表查询通常不改 spec，但仍可能留下 API 审计记录。

本节已核对这次使用的 kubeconfig、`CTX`、客户端版本，以及对 Pod 和日志的 can-i 结果；can-i 被拒绝，或 context 还没从 `get-contexts` 里确认时，先停下，不改用分析机默认集群。命令、请求时间、标准错误和退出状态留在一起，一并留存 `collection-start.txt`、context 输出，以及受控保存的配置视图。

### 08.2 保存集群、工作负载与依赖

context 已经固定，还没有一份可复核的对象导出。把节点、工作负载、网络和存储先保存下来，再处理缺类型和空输出。

操作顺序：先保存节点、工作负载、网络和存储，再按 api-resources 补缺的类型，空输出和 Forbidden 分开记。

**1. 先把这批对象保存到输出目录。**

```bash
kubectl --context "$CTX" version -o yaml > "$OUT/version.yaml"
kubectl --context "$CTX" get nodes -o json > "$OUT/nodes.json"
kubectl --context "$CTX" get nodes -o wide > "$OUT/nodes.txt"
kubectl --context "$CTX" get namespaces -o json > "$OUT/namespaces.json"
kubectl --context "$CTX" get pods -A -o json > "$OUT/pods.json"
kubectl --context "$CTX" get pods -A -o wide > "$OUT/pods.txt"
kubectl --context "$CTX" get deployments,replicasets,statefulsets,daemonsets,jobs,cronjobs -A -o json > "$OUT/workloads.json"
kubectl --context "$CTX" get services,endpointslices,ingresses,networkpolicies -A -o json > "$OUT/network.json"
kubectl --context "$CTX" get pvc -A -o json > "$OUT/pvc.json"
kubectl --context "$CTX" get pv -o json > "$OUT/pv.json"
kubectl --context "$CTX" get storageclasses -o json > "$OUT/storageclasses.json"
kubectl --context "$CTX" get configmaps -A -o json > "$OUT/configmaps.json"
kubectl --context "$CTX" get events -A --sort-by=.metadata.creationTimestamp > "$OUT/events.txt"
```

**2. 列表缺内容时分开查。** ConfigMap 也可能含密码，输出受控保存；Secret、权限绑定和自定义资源另按需要受控采集（例如 `kubectl --context "$CTX" get clusterroles,clusterrolebindings,roles,rolebindings -A -o json > "$OUT/rbac.json"` 与 `kubectl --context "$CTX" get secrets -A -o json > "$OUT/secrets.json"`，导出文件严格限制访问权限，不在公开报告贴明文）。`get all -A` 没有包含全部资源，先用 `kubectl --context "$CTX" api-resources` 看实际可查询类型。类型不存在或请求 Forbidden 时，保存报错，再按单个类型查询。空输出先保存原样，再和报错、权限一起判断有没有这个资源。

本节已核对这次导出的节点、命名空间、工作负载、网络、PVC、PV、StorageClass、ConfigMap 和事件；Secret、权限绑定、自定义资源，以及 Forbidden 或类型不存在的报错，要单独列出。每个文件都能对上命令、context 和采集时间。空文件旁有退出状态或标准错误，一并留存上面这些 JSON、文本和事件输出。含密码的 ConfigMap 受控保存。

### 08.3 按目标读取字段、事件与日志

工作负载列表里已经有目标，还要把 UID、节点、容器状态和日志固定到同一份输出。名称用列表里核对过的值。

操作顺序：先保存目标 Pod 的 JSON 和 describe，再读状态字段和日志，事件和更早的日志分开找。

**1. 按目标保存对象、事件和当前日志。**

```bash
# portal-demo 为构造名，实际名称从 pods 列表核对
POD='portal-demo'
NS='apps'
kubectl --context "$CTX" get pod "$POD" -n "$NS" -o json > "$OUT/target-pod.json"
kubectl --context "$CTX" describe pod "$POD" -n "$NS" > "$OUT/target-pod-describe.txt"
kubectl --context "$CTX" get pods -n "$NS" -l app=portal -o wide
kubectl --context "$CTX" get pods -A --field-selector spec.nodeName=node-a -o wide
kubectl --context "$CTX" get pod "$POD" -n "$NS" -o jsonpath='{.metadata.uid}{"\n"}{.spec.nodeName}{"\n"}'
kubectl --context "$CTX" logs "$POD" -n "$NS" -c web --timestamps > "$OUT/web-current.log"
kubectl --context "$CTX" logs "$POD" -n "$NS" -c web --previous --timestamps > "$OUT/web-previous.log" 2> "$OUT/web-previous.stderr"
```

**2. 把容器状态字段一起留下。** 同时保存 `containerStatuses`、`initContainerStatuses`、`ephemeralContainerStatuses`，核对 image/imageID、containerID、restartCount、state 与 lastState。Pod 名与容器名不是容器 ID，`containerd://` 等前缀说明运行时类型。

**3. 事件和日志分开读。** Events 可能过期或聚合。排序后再看 first/lastTimestamp、eventTime、series，不能只按 creationTimestamp 认定每次发生顺序。`kubectl logs` 只返回最近日志文件中可用内容；`--previous` 取同一 Pod、同名容器的前一个实例，不是全部重启历史。保存 Pod UID、容器名、当前/前一实例、采集时间和报错。查更早日志时，到节点轮转文件或集中日志中找；删除、驱逐和权限不足分别记明。

[kubectl 速查](https://kubernetes.io/docs/reference/kubectl/quick-reference/)、[日志架构](https://kubernetes.io/docs/concepts/cluster-administration/logging/)

本节已核对目标 Pod 的 UID、节点、容器 ID、重启计数，以及当前或 previous 日志；`--previous` 报错、事件过期，或更早日志只在节点轮转文件里时，写明还缺哪一段。JSON、describe、日志和标准错误使用同一个 Pod 名、命名空间和采集时间，一并留存target-pod.json、describe、当前日志、previous 日志和它的 stderr。

### 08.4 读取操作与恢复操作分开记录

对象已经导出，后面有的命令会改集群或新开进程。先把读取和写入分开，恢复实验另留基线。

操作顺序：先保存查询输出，再标明哪条命令会写对象或新开进程，恢复只放在隔离副本。

**1. 写操作先留在隔离环境。** 【仅在副本/仿真/授权环境执行】下表中的 exec、apply、patch、edit、delete 和恢复操作会修改集群或新增进程；查询输出先保存，恢复实验另留基线。

**2. 按这张表决定这条命令能不能出现在首轮。**

<details>
<summary>展开 kubectl 读写操作取证影响对照表</summary>

| 操作 | 影响 | 用途 |
| --- | --- | --- |
| `get`、`describe`、`logs`、`auth can-i` | 读取/检查目标，可能留下 API 请求痕迹 | 首轮采集与核验 |
| `apply -f`、`edit`、`patch`、`scale` | 写入对象期望状态，可引发控制器动作 | 仅用于隔离副本的明确恢复目标 |
| `delete pod`、`rollout restart` | 删除或重新创建运行实例，可能更改 UID、ID 和日志 | 已保全后验证依赖修复；不能替代故障诊断 |
| `exec`、`cp`、`debug` | 在运行环境执行程序或改变调试状态 | 用于受控实验，记录额外访问与写入 |
| `create token` | 签发凭据，不是读取历史 token | 实验登录或既有身份的短期访问 |
| `port-forward` | 建立本地到资源的访问通道 | 实验环境访问；限制到本地地址 |

</details>

本节已核对哪些输出来自 get、describe、logs、auth can-i，哪些命令会写对象或新开进程；还没另存基线时，不开始 apply、delete、exec 或 port-forward。每条写命令旁边有执行前后的对象身份和输出，一并留存查询输出、恢复基线，以及每次写操作的命令和时间。

<span id="09-节点证据apicri-与磁盘的关联"></span>

## 09 将 API 对象关联到节点 CRI 与磁盘目录

API 里的对象、节点上的运行时、磁盘快照，三份材料的时间和范围可能不一样。先标明这次读的是哪一个视角，再选工具。

操作顺序：标明 API、CRI 还是磁盘快照，按表选工具，空列表只记这个视角这次没列出对象。

**1. 先标明这次读的视角。** API 是控制面的对象视图；CRI 是指定 Node 上的运行时视图；节点快照是磁盘保全时的状态。三者的时间和范围可能不同。一个视角返回空列表，只说明这个视角这次没有列出对象。

**2. 按这张表选工具。**

| 工具 | 读取内容 | 选择依据 |
| --- | --- | --- |
| kubectl --context "$CTX" | 集群对象、工作负载、卷引用与事件 | 已核对的 context 与权限 |
| crictl | sandbox、全部容器、镜像、inspect 与日志 | 实际 CRI socket；`ps -a` 包含停止实例 |
| ctr | containerd namespace、containers、tasks、插件与镜像 | 实际 containerd socket 与 namespace；`k8s.io` 是常见值 |
| journalctl / 静态日志 | kubelet、运行时和服务记录 | 对应 Node 与时间范围 |

本节已核对这次读取用的是 API、CRI 还是节点快照，以及对应的 context、socket 或日志目录；另一个视角还没读，或某个视角是空列表时，分别写明。工具、读取内容和选择依据写在同一行，一并留存context 或 socket、查询输出，以及这份材料的采集时间。

### 09.1 配置、日志与数据位置

节点目录已经挂上，默认路径却是空的。先读这台 kubelet 和 containerd 的实际参数，再打开对应目录。

操作顺序：先读 kubelet 的 root-dir 和 podLogsDir，再读 Kubernetes 与 containerd 配置，对上 dump 和当前进程。

**1. 先确认路径再读目录。** 查看该节点 kubelet 服务参数和配置。`--root-dir` 决定 kubelet 管理卷与 Pod 文件的根，KubeletConfiguration 中的 `podLogsDir`（随对应版本支持）决定 Pod 日志根；K8s v1.28+ 引入、v1.29 默认启用的原生 sidecar（`initContainers` 中设置 `restartPolicy: Always`）同样在该日志根下按容器名落盘。记下原值并映射到检材挂载点。默认目录为空时，先转查这两项配置的路径。

```text
/etc/kubernetes/
```

**2. 重点看这些子项。**

| 路径 | 用途 | 取证价值 |
|---|---|---|
| `/etc/kubernetes/manifests/` | 控制平面静态 Pod 清单 | API Server、scheduler、controller-manager、etcd 参数 |
| `/etc/kubernetes/admin.conf` | 常见管理员 kubeconfig | 高敏感凭据，必须严格保护 |
| `/etc/kubernetes/kubelet.conf` | kubelet 访问集群的配置 | 节点身份、API Server 地址 |
| `/var/lib/kubelet/config.yaml` | kubelet 配置 | 运行时、认证、DNS、cgroup 等线索 |
| `/var/lib/kubelet/pods/` | 按 Pod UID 保存本地卷和挂载 | 已删除对象的残留、Secret/ConfigMap/emptyDir 线索 |
| `/var/log/pods/` | Pod 日志目录 | 按命名空间、Pod、UID 关联日志 |
| `/var/log/containers/` | 常见容器日志符号链接 | 便于按 Pod/容器名检索 |

**3. 再读这台 containerd 的配置。** 默认配置文件是：

```text
/etc/containerd/config.toml
```

查看磁盘配置与当前实例的插件列表：

```bash
cat /etc/containerd/config.toml
containerd config dump
ctr --address /run/containerd/containerd.sock plugins ls
```

**4. 配置项按这张表解释。**

| containerd 配置项 | 取证意义 |
|---|---|
| `root` | 持久化元数据根目录，常见默认值为 `/var/lib/containerd` |
| `state` | 运行时状态目录，常见默认值为 `/run/containerd` |
| CRI 插件配置 | sandbox 镜像、运行时类型、cgroup、registry 配置 |
| registry `config_path` | 定位私有仓库证书、镜像源和 `hosts.toml` |
| snapshotter | 决定快照数据的组织与恢复路径 |

**5. 先记下版本和启动，再读 dump。** 先记录 `containerd --version`、实际 `--config` 路径、启动命令、配置哈希和启动时间。`containerd config dump` 用本次磁盘配置、imports 和该二进制默认值生成结果；插件配置节名称可能随版本不同。再比对当前插件、进程和日志。磁盘文件可能在启动后被改过，dump 是这次配置解释出来的结果，不是历史加载记录。离线解析用目标自己的配置和二进制默认值，不用分析机默认值代替目标运行值。

本节已核对kubelet 的 `--root-dir`、`podLogsDir`，以及 containerd 的 root、state、snapshotter 和实际 config 路径；默认目录为空，或 dump 和当前进程参数不一致时，写明差在哪一项。目录映射来自这台节点的参数，dump 旁边有版本、配置哈希和启动时间，一并留存kubelet 配置、containerd 配置、插件列表和路径映射。

### 09.2 材料与 API 视图

要把它一个应用 Pod 的容器 ID 对到本机日志和挂载，材料里不一定有 Docker。先从 API 取出 UID、节点和 containerID，再交给对应节点。

操作顺序：先列 Pod 和 Service，保存目标 JSON 和事件，对上 UID、节点和容器 ID。

**1. 先列清这次有哪些材料。** 材料包括保全的集群对象 JSON、已确认节点会话，以及节点快照中的 `/var/log/pods/`、`/var/log/containers/`、`/var/lib/kubelet/pods/` 和实际 containerd 根目录。目标是将一个应用 Pod 的容器 ID 对应到本地日志与挂载。示例 Pod 为命名空间 `apps` 下的 `portal-demo`。

```bash
kubectl --context "$CTX" get pods -A -o wide
kubectl --context "$CTX" get services -A
kubectl --context "$CTX" get pod portal-demo -n apps -o json > "$OUT/pod.json"
kubectl --context "$CTX" get events -A --sort-by=.metadata.creationTimestamp > "$OUT/events.txt"
jq '{uid:.metadata.uid,node:.spec.nodeName,podIP:.status.podIP,containers:.status.containerStatuses}' "$OUT/pod.json"
```

**2. 用构造结果选定节点和运行时。** 构造结果为 Node `node-a`、Pod IP `10.40.2.17`，containerID 以 `containerd://` 开头。这为节点查询提供运行时与候选 ID。API 当前视图受对象删除、RBAC 和事件保留影响；保存失败与不可见范围。

本节已核对目标 Pod 的 UID、Node、Pod IP 和 containerID 前缀；API 返回 NotFound、Forbidden，或事件已经过期时，写明不可见范围。jq 取出的 uid、node、podIP、containers 来自刚保存的 pod.json，一并留存pods 宽表、Service 列表、pod.json 和 events.txt。

### 09.3 在正确节点、正确端点读取

API 已经指向 node-a，还要在这台节点上用核对过的 socket 读 sandbox 和容器。输出不要和别的节点混放。

操作顺序：先确认本机端点，列出 sandbox 和容器，用完整 ID 读 inspect 和日志。

**1. 输出目录按节点分开。** 节点输出单独保存在本机 `/work/output/k8s-node-a`，不要与其他节点的同名输出混放。先在 node-a 会话确认 `/etc/crictl.yaml`、kubelet/containerd 启动参数与服务身份，再显式指定已经核对的端点。下面 socket 是示例值，不可直接套到所有主机。

```bash
OUT=/work/output/k8s-node-a
mkdir -p "$OUT"
cat /etc/crictl.yaml
systemctl status containerd
systemctl show containerd -p ExecStart -p MainPID
CRI=unix:///run/containerd/containerd.sock
IMAGE_ENDPOINT="$CRI"
crictl --runtime-endpoint "$CRI" info > "$OUT/cri-info.json"
crictl --runtime-endpoint "$CRI" pods -o json > "$OUT/sandboxes.json"
crictl --runtime-endpoint "$CRI" ps -a -o json > "$OUT/cri-containers.json"
crictl --runtime-endpoint "$CRI" --image-endpoint "$IMAGE_ENDPOINT" images > "$OUT/cri-images.txt"
```

**2. 镜像端点和运行时端点按实际配置填。** 这里的运行时接口和镜像接口使用同一 socket。实际配置若分开，分别填写 `CRI` 与 `IMAGE_ENDPOINT`，不要让镜像查询回落到分析机的默认端点。

**3. 用完整 ID 读 sandbox 和容器。** 从 Pod UID、名称、命名空间与标签寻找 sandbox，再从同一 sandbox 关联容器。不要只按一个短名称选任意同名对象。把实际完整 sandbox ID 与容器 ID 填入变量，读取对象：

```bash
SID='替换为确认后的完整PodSandboxID'
KCID='替换为确认后的完整容器ID'
crictl --runtime-endpoint "$CRI" inspectp "$SID" > "$OUT/sandbox-inspect.json"
crictl --runtime-endpoint "$CRI" inspect "$KCID" > "$OUT/cri-container-inspect.json"
crictl --runtime-endpoint "$CRI" logs "$KCID" > "$OUT/cri-container.log" 2> "$OUT/cri-logs.stderr"
jq . "$OUT/cri-container-inspect.json"
```

**4. 用完整 JSON 找节点文件。** 核对日志路径、挂载、镜像、Pod 标签和运行 PID；字段位置随 CRI/containerd 版本可能不同。stderr 有应用错误或工具报错时，结合退出状态逐条分辨。容器已删导致查询失败，就继续找节点快照和 kubelet 日志。查询失败时保留报错，不新建容器去补原来的结果。

本节已核对node-a 的 CRI socket、sandbox ID、完整容器 ID，以及 inspect 里的日志和挂载路径；容器已删除或端点连不上时，改查节点快照和 kubelet 日志，并留下 stderr。inspect 里的 Pod UID、命名空间和名称与 API 里的目标是同一个，一并留存cri-info、sandboxes、容器列表、inspect、日志和 stderr。

### 09.4 静态日志与快照关联

节点已经做成只读挂载，要在检材根里找日志和 kubelet 目录，不能读到分析机自己的 `/var/log`。先映射软链，再按 UID 对上 inspect。

操作顺序：先映射日志软链，默认目录为空就查 podLogsDir，再用 ctr 对上 container 和 task。

**1. 在检材根里列出日志和 kubelet 目录。**

```bash
EVIDENCE_ROOT=/mnt/evidence
ls -lah "$EVIDENCE_ROOT/var/log/containers"
find "$EVIDENCE_ROOT/var/log/pods" -type f -name '*.log*' -print
find "$EVIDENCE_ROOT/var/lib/kubelet/pods" -maxdepth 2 -type d -print
cat "$EVIDENCE_ROOT/etc/containerd/config.toml"
```

**2. 离线日志按这三步找。** 保存 `/var/log/containers` 的软链本身，把绝对目标映射回 `$EVIDENCE_ROOT`，不读分析机的 `/var/log/pods`。默认目录为空，查 `podLogsDir`、kubelet `--root-dir` 和 CRI inspect 的实际日志路径，分别记录自定义目录或已清理文件。将日志目录或软链中的 Pod UID、容器名和重启序号，与同一节点、同一时间的 inspect 对应；缺文件时列出未取得项。

**3. 需要 ctr 时先确认 socket 和 namespace。** Kubernetes 对象常位于 `k8s.io`。默认 namespace 的空列表只说明这个 namespace 没有列出容器。查询例为：

```bash
ctr --address /run/containerd/containerd.sock namespaces list
ctr --address /run/containerd/containerd.sock --namespace k8s.io containers list
ctr --address /run/containerd/containerd.sock --namespace k8s.io tasks list
```

**4. container 和 task 分开看。** container 是运行时定义，task 是正在执行的实例；退出后可能还有 container，却没有 task。快照目录和 snapshotter 从该实例配置与 inspect 查，不按目录新旧选。`containerd config dump` 只解释本次磁盘配置，另保存插件列表和进程参数；实现可核对 [containerd config 命令源码](https://github.com/containerd/containerd/blob/main/cmd/containerd/command/config.go)。

**5. 结果至少留下这些字段。** 命名空间、Pod 名/UID、Node、sandbox ID、完整容器 ID、镜像摘要、日志/挂载路径和采集时间。API、CRI 与静态文件不一致时保留差异，按删除、重启、权限与采集时间逐项复核。

本节已核对检材根里的日志路径、Pod UID、容器名，以及 `k8s.io` 里的 container 或 task；软链目标不在 `$EVIDENCE_ROOT`、日志已清理，或只有 container 没有 task 时，分别写明。日志路径或软链解析出的 Pod UID、容器名和重启序号，与同一节点的 inspect 及采集时间相符；不要求每行日志正文都有 UID，一并留存软链、日志文件清单、containerd 配置、ctr 列表和差异说明。

<span id="10-实战一从业务容器追到-nfs-数据目录"></span>

## 10 实战一：从业务容器追到 NFS 持久化目录

网站 Pod 已经不在列表里，节点磁盘、运维 YAML 和 NFS 目录还在。先画依赖和材料，再逐层核对对象，最后在只读挂载上找落点。

操作顺序：先画依赖和材料，保存对象并逐层核对，在只读挂载上对上静态落点。


### 10.1 场景、材料与依赖图

多台 Linux 主机都在，网站代码和数据库实际落在哪一台还没定。先给每台主机一个角色，再沿卷把应用追到目录。以下对象名、地址与路径为构造示例。

操作顺序：先给每台主机标角色，再沿 Deployment、PVC、PV 画到 NFS，对上代码和数据库各走自己的卷。

**1. 先写下场景和主机。** 多台 Linux 主机构成一个集群，网站 Pod 已消失，但节点磁盘、运维 YAML、NFS 数据目录及备份仍在，需要确定网站代码和数据库的实际落点。

| 实验主机 | 示例地址 | 角色 | 首轮材料 |
| --- | --- | --- | --- |
| control-a | 10.50.0.10 | 控制节点 | kubeconfig、控制面清单、对象导出、部署 YAML |
| node-a | 10.50.0.11 | 工作节点 | kubelet、运行时数据、Pod 日志、镜像 |
| node-b | 10.50.0.12 | 工作节点 | 同上，可能缺少某个应用镜像 |
| storage-a | 10.50.0.20 | 外部 NFS 主机 | exports、业务卷目录、网站归档、数据库文件 |

**2. 按依赖顺序看，外部服务可以后补。** 目标依赖是：存储与网络，然后数据库或缓存，然后网站配置与代码，然后网站 Pod 与 Service。机器人可以另外依赖数据库、挂载配置和外部 API。静态分析它的配置与数据时，不要求先恢复外部通信。

**3. 主机数量和 Node 数量分开数。** 先为控制节点、工作节点和存储服务器分别建立材料清单。`/etc/hosts` 仅是名称映射，可能有过期条目；是否为 Kubernetes Node 需结合保全的 API 对象、kubelet 配置和节点日志。单独提供 NFS 的主机可以没有注册为 Node。

**4. 每个对象只回答表里的那一个问题。**

| 对象 | 读取什么 | 解决的问题 |
| --- | --- | --- |
| Deployment / Pod | 镜像、Node、`volumeMounts`、`volumes`、环境引用 | 哪个容器在何处运行、哪个卷映射到容器内路径 |
| Service | `type`、`port`、`targetPort`、`nodePort`、selector | 集群服务端口、后端端口与对外入口各是什么 |
| PVC | namespace、UID、`volumeName`、StorageClass、注解 | 业务声明绑定了哪个实际卷 |
| PV | claimRef、NFS server/path、回收策略 | 后端位置及删除对象可能产生的影响 |
| StorageClass / provisioner | provisioner 名、路径模板、NFS 根 | 动态制备目录规则是否真的使用某条注解 |
| ConfigMap / Secret 引用 | 对象名、挂载键或环境变量名 | 应用依赖是否齐全；秘密内容单独保护 |

**5. 把关系画成一条链。** 建议把关系画成 `应用 → Pod 挂载 → PVC → PV → NFS 主机/目录`。数据库、缓存和机器人配置各沿自己的卷追踪。持久数据可能在 NFS、其他 PV 或绑定挂载中。

本节已核对每台实验主机的角色，以及应用挂载到 PVC、PV 和 NFS 目录的那条链；主机还没对上 Node 对象，或数据库和网站不在同一存储上时，分别写明。主机地址、Node 身份和卷后端来自同一批材料，`/etc/hosts` 只作为名称线索，一并留存主机清单、对象读取表，以及画好的依赖链。

### 10.2 保存对象并逐层核对

Pod 可能已经删了，也可能接口还在。两条路都先留下现有材料，再从 PVC 的 volumeName 找到 PV，最后换算 .env 的位置。

操作顺序：离线材料先记挂载和旧 UID，接口还在就导出对象，用 volumeName 对上 PV 和 NFS 路径。

**1. 只拿到离线材料时，先从残留往下找。** 从控制节点导出、部署 YAML 和节点残留，记下 Pod 镜像、挂载、配置引用。从已保存的 PVC/PV JSON 找数据后端。Pod 已删时，API 的 NotFound 只表示当前查不到；继续找旧部署定义、日志 UID 和存储文件。没有历史导出就明记缺少，不用新建结果补填。

**2. 对象还在时，用这条接口路线保存。** 以下命令用于对象仍存在的已确认采集会话，或完成第 11 节隔离恢复后的查询。`portal-demo` 是示意名，恢复后从实际 Pod 列表取名；新对象只解释恢复结果。`OUT` 是分析输出目录。分析机自己的集群不拿来当目标。

```bash
OUT=/work/output/k8s-storage
mkdir -p "$OUT"
kubectl --context "$CTX" get nodes -o wide > "$OUT/nodes.txt"
kubectl --context "$CTX" get pods -A -o wide > "$OUT/pods.txt"
kubectl --context "$CTX" get services -A -o yaml > "$OUT/services.yaml"
kubectl --context "$CTX" get deployments -A -o yaml > "$OUT/deployments.yaml"
kubectl --context "$CTX" get pvc -A -o yaml > "$OUT/pvc-all.yaml"
kubectl --context "$CTX" get pv -o yaml > "$OUT/pv-all.yaml"
kubectl --context "$CTX" get storageclass -o yaml > "$OUT/storageclasses.yaml"
kubectl --context "$CTX" describe pod portal-demo -n apps > "$OUT/web-pod.txt"
kubectl --context "$CTX" describe pvc site-data -n apps > "$OUT/site-pvc.txt"
kubectl --context "$CTX" get configmap portal-config -n apps -o yaml > "$OUT/portal-config.yaml"
```

记录执行时间、上下文、namespace、对象 UID 和权限限制。PV、StorageClass 是集群级对象，PVC、ConfigMap 是命名空间级对象。`get pods -A` 的多行并不全是故障，先看 STATUS/READY、describe 的具体事件和依赖。

**3. 从 PVC 取实际 PV 名，再查这个 PV。** 不能凭名称相似选择另一个卷。

```bash
PV_NAME=$(kubectl --context "$CTX" get pvc site-data -n apps -o jsonpath='{.spec.volumeName}')
printf '%s\n' "$PV_NAME"
# PVC 为 Bound 且 PV_NAME 非空时再查；Pending 状态先读 describe 事件
if [ -n "$PV_NAME" ]; then
  kubectl --context "$CTX" get pv "$PV_NAME" -o yaml > "$OUT/site-pv.yaml"
fi
```

**4. 按构造结果换算 .env 位置。** `apps/site-data` 为 Bound，PV 的 `claimRef` 对应同一 PVC UID。`spec.nfs.server` 是 `10.50.0.20`，`spec.nfs.path` 是 `/data/k8s_data/apps/site-data`。Pod 挂到 `/app` 时，`/app/.env` 对应该 NFS 目录的 `.env`。有 `subPath`、软链或其他 mountPath 时，再换算相对路径；最后在存储快照读取文件并核对哈希。

**5. 在分析机上把第 08.2 节已导出的 `/work/output/k8s/{pv,pvc}.json` 收成绑定关系（若仅执行了本节第 2 步 YAML 导出，先补充导出对应 JSON 或将路径指向实际 JSON 目录）。** 空值和 unmatched 都保留。

```bash
# 对应 08 节输出；空值及 unmatched 都保留，不能补猜
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/work/output/k8s')
pv_by_name = {p['metadata']['name']: p for p in json.loads((root/'pv.json').read_text())['items']}
for claim in json.loads((root/'pvc.json').read_text())['items']:
    meta = claim['metadata']
    volume = claim.get('spec', {}).get('volumeName', '')
    pv = pv_by_name.get(volume, {})
    spec = pv.get('spec', {})
    ref = spec.get('claimRef', {})
    matched = bool(pv) and all(ref.get(k) == meta.get(k) for k in ('namespace', 'name', 'uid'))
    backend = spec.get('nfs', spec.get('csi', {}))
    print(json.dumps({'pvc': f"{meta.get('namespace')}/{meta['name']}",
                      'uid': meta['uid'], 'phase': claim.get('status', {}).get('phase'),
                      'pv': volume, 'binding_matches': matched, 'backend': backend}, ensure_ascii=False))
PY
```

这段脚本只整理已保存的对象，不访问集群，也不读取 Secret 内容。`binding_matches: true` 仅说明这两份导出中的 namespace/name/UID 一致，仍要核对采集时间、PVC 状态、Pod 挂载和后端文件。

**6. NFS 目录先看已绑定 PV。** 从 PV 取实际 server/path，再查 provisioner 的 NFS 根和存储主机 `/etc/exports`。`nfs.io/storage-path` 是部分外部 provisioner 的注解，只有 StorageClass 的 `pathPattern` 或实现确实用它时才参与目录计算，不是通用公式。材料不足就保留候选路径，不猜目录。[NFS subdir provisioner 配置](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner)

本节已核对PVC 的 `spec.volumeName`、PV 的 `claimRef`，以及 NFS server/path 或换算后的 `.env` 路径；PV_NAME 为空、Pending，或 `binding_matches` 不是 true 时，先读 describe 事件，不补猜目录。绑定关系来自已保存的 JSON；后端文件在存储快照里有哈希，一并留存对象导出、site-pv.yaml、绑定关系输出和 `/etc/exports`。

### 10.3 静态落点与保全清单

控制节点和存储主机都已只读挂上，要在各自的挂载根里找声明、exports 和站点目录。找到的 YAML 先当候选，再和 API 对象、卷数据对时间。

操作顺序：分开映射两台主机，找声明、exports 和 .env，对上卷数据是否还在。

**1. 在两个只读根里列出声明和数据。**

```bash
CONTROL_ROOT=/mnt/evidence/control-a
STORAGE_ROOT=/mnt/evidence/storage-a
find "$CONTROL_ROOT/root" -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.tar' \) -print
cat "$STORAGE_ROOT/etc/exports"
ls -lah "$STORAGE_ROOT/data/k8s_data/apps/site-data"
find "$STORAGE_ROOT/data/k8s_data/apps/site-data" -maxdepth 2 -type f -name '.env' -print
```

**2. 把候选定义和实际卷对上时间。** 这里分别映射控制节点与存储主机的只读挂载根。控制节点 `/root` 中可能有 Deployment、Service、PVC、ConfigMap 声明以及网站归档；若备份或声明实际保存在其他主机，使用那台主机的挂载根并记录归属。它们是候选部署定义，需与已保存的 API 对象、卷数据和备份时间对应。部署对象被删除不等于卷数据已删除，但 PV 回收策略、provisioner 的删除规则、人为清理及实际文件状态会影响残留。不要通过删除 PVC 来验证数据是否还在。

本节已核对控制节点上的候选声明、storage-a 的 exports，以及 site-data 目录里的文件；声明实际在别的主机，或目录里没有 `.env` 时，写明归属和未找到的路径。文件位于这次映射的只读根下，并和已保存的 PV 路径、备份时间对过，一并留存YAML 和归档清单、exports、目录列表和文件哈希。

<span id="11-实战二恢复多节点应用并解释每个故障"></span>

## 11 实战二：在隔离副本恢复多节点应用并排查故障

多节点应用起不来，历史状态还没固定。先保存旧状态，再用事件区分故障，然后分发镜像并提交声明，最后复核入口和数据库。

操作顺序：先固定历史状态，用事件区分故障层级，分发镜像并提交声明，需要重建时记下变化，复核入口、数据库和配置。


### 11.1 先固定历史状态，再建立恢复条件

要在隔离环境里读应用内容。材料还没分清哪些是旧状态、哪些会在启动后新产生。先保存哈希和启动前状态，再按依赖把实验环境搭起来。

操作顺序：先留旧状态的哈希，只连隔离网络，按依赖启动存储、控制和网站配置。

**1. 恢复只在隔离副本里做，新产生的对象单独记。** 【仅在副本/仿真/授权环境执行】材料包括控制/工作节点快照、NFS 快照、业务备份、已审阅声明和本地镜像包。恢复目的是读取应用内容；先保存旧状态，再按下面顺序建立实验环境。新 Pod、容器 ID、日志和数据库改动全部记为本次仿真。

**2. 按这个顺序建立实验环境。** 保留每台镜像和关键目录的完整哈希，保存启动前的网络、日志与容器元数据。仅连接隔离网络，按目标配置恢复节点地址、名称解析和存储连接；不要将重复地址接入真实网络。按依赖启动存储、控制服务和工作节点，保证分析所需主机同时可用；没有适用于所有集群的固定主机启动顺序。先读取 PVC/PV、NFS 和数据库，再恢复网站及其 ConfigMap。机器人依赖外部 API 时可继续静态读取配置与库，不必恢复外部通信。

**3. 四台主机先逐台核对。** 保存 `ip -br addr`、`ip route`、`hostnamectl`、`date -u`、`/etc/hosts`。

**4. API 连不上时先查控制面入口。** 先查 control-a 服务、6443 入口、证书时间和 kubeconfig 地址，再查 Node Ready、kubelet、运行时。control-a、node-a、node-b 若都注册，是三个 Node；两台工作节点与四台实验主机另记。历史数量到当时 Node 清单和日志查。

本节已核对每台主机启动前的哈希、地址、时间和 `/etc/hosts`，以及 API 入口是否已通；6443、证书或 kubelet 还没对上时，先停在这一层，不重建集群。新 Pod、新容器 ID 和新日志都标成这次仿真，和启动前材料分开，一并留存镜像和目录哈希、启动前网络与日志、四台主机的核对输出。

### 11.2 用事件区分故障层级

Pod 或卷起不来，事件里已经有 Pending、FailedMount 或 ImagePullBackOff。先用事件决定查调度、存储、镜像还是应用，再从真正挂载的那台节点测 NFS。

操作顺序：先用事件选故障层，从工作节点看 NFS，调整过滤只记成这次实验。

**1. 按这张表选下一步，避免跳层下结论。**

<details>
<summary>展开 Pod 与卷常见故障事件排查表</summary>

| 现象/事件 | 下一步 | 不应直接推断 |
| --- | --- | --- |
| Pod Pending / FailedScheduling | Node Ready、requests、污点、亲和性、PVC 绑定及调度事件 | 不等于容器已运行后崩溃 |
| PVC Pending、制备失败 | StorageClass、provisioner 事件、NFS 根与连通性 | 不等于 NFS 数据已消失 |
| FailedMount、mount timeout / access denied | PV server/path、exports、权限与防火墙 | 服务正在运行不代表挂载可达 |
| ConfigMap not found / missing key | namespace、对象名、挂载键、对应声明 | 不等于镜像损坏 |
| ImagePullBackOff / ErrImageNeverPull | 节点运行时、本地镜像、准确标签/摘要、pull policy | 控制节点有镜像不代表工作节点有 |
| CrashLoopBackOff | 该容器 previous 日志、退出原因、探针与业务配置 | 这是反复失败后的等待，不是唯一根因 |
| Pod Running 但业务失败 | 数据库、缓存、应用日志及配置 | Running 不保证业务数据或请求正确 |

</details>

**2. NFS 探测从实际工作节点发起。** `nmap -Pn -p 2049 10.50.0.20` 可观察 NFS 服务端口，但 `filtered` 只能说明探测受过滤或无响应，不能唯一归因某一防火墙。NFS 版本可能还涉及其他服务与端口。成功的端口探测只说明端口有响应，卷是否挂载成功要看挂载结果。

**3. 关闭防火墙只作为临时实验。** **【仅在副本/仿真/授权环境执行】** `systemctl stop firewalld` 改变整台主机过滤状态，先保存规则和预期通信。只有确需临时关闭测试时才执行，记录测试范围、结果并恢复规则。原现场记录保持不变；调整后能连接，写为这次实验结果。

**4. 在存储端和工作节点分别读。** 在 storage-a 核对 `/etc/exports`、实际导出目录、服务状态与防火墙区域；在发生 FailedMount 的 node-a 核对节点路由、PV 地址、NFS 版本和挂载报错。以下为实验会话读取命令，NFS unit 名随发行版变化：

```bash
# storage-a：服务、导出、监听与已有规则
systemctl status nfs-server --no-pager
cat /etc/exports
exportfs -v
ss -lntup
firewall-cmd --get-active-zones
firewall-cmd --list-all

# node-a：从真正发起挂载的工作节点检查
ip route get 10.50.0.20
nmap -Pn -p 2049 10.50.0.20
journalctl -u kubelet --no-pager -o short-iso
```

**5. 把版本、权限和挂载结果分开。** NFSv4 常用 2049，NFSv3 还可能需要 rpcbind/mountd 等实际协商端口；目录权限、exports 的客户端范围、版本选项和网络都要匹配。`showmount` 结果也不能覆盖所有纯 NFSv4 服务。调整仅限实验主机的必要通信规则，复测后保存“调整前/后”的事件和状态。端口从 filtered 变成 open，只说明探测结果变了；业务卷是否挂载成功，看挂载事件和目录。

本节已核对事件属于调度、制备、挂载、配置、镜像还是应用，以及 storage-a 的 exports 和 node-a 的路由；端口仍是 `filtered`，或 showmount 看不到纯 NFSv4 导出时，写明还缺挂载结果。调整前和调整后的事件、规则分开保存，原现场记录没有被改写，一并留存事件表、exports、防火墙规则、nmap 和 kubelet 日志。

### 11.3 跨节点镜像分发与声明恢复

工作节点缺镜像，或者声明还没提交到隔离集群。先确认每个节点的运行时，再选 Docker 或 containerd 一条路线，最后才 apply。

操作顺序：先确认运行时，导出并核对哈希，导入后用 CRI 检查，审阅声明后再提交。

**1. 导入和提交都会改实验环境。** 【仅在副本/仿真/授权环境执行】先确认每个节点实际运行时，再从下面两条镜像分发路线选一条。导入会写接收端镜像存储，apply 会修改集群。从已审阅 Deployment 取镜像名称，并核对摘要、架构和目标节点。同名标签先核对摘要，再开始导入。

**2. Docker 路线只用于已经确认 Kubernetes 使用该 Docker 镜像存储的实验节点。**

```bash
# 有镜像的实验节点：导出归档并记录哈希
docker images --no-trunc
docker save -o /work/output/web-image.tar lab/web-runtime:7.4
sha256sum /work/output/web-image.tar

# 复制归档到缺镜像的实验工作节点，接收端再次核对哈希
scp /work/output/web-image.tar analyst@10.50.0.12:/work/input/web-image.tar

# 接收实验节点：导入本地 Docker 存储，保留 load 输出
docker load -i /work/input/web-image.tar
docker images --no-trunc
```

`docker load` 通常恢复归档内已有的镜像和标签，**不是导入后必然丢失标签**。只有确认镜像内容匹配、归档中缺少部署所需标签时，才用 `docker tag 完整镜像ID lab/web-runtime:7.4` 在实验环境补标签。四位短 ID 可能对应多个对象，补标签时用完整镜像 ID。命令行为见 [Docker load](https://docs.docker.com/reference/cli/docker/image/load/)。

**3. containerd 路线要进 CRI 能看见的存储。** Docker 中导入的镜像不会自动进入节点的 CRI 镜像存储。先在每个节点确认实际 socket、CRI 镜像端点和 containerd namespace；以下示例使用 `k8s.io`，镜像完整名称从导出端列表取值。

```bash
# 有镜像的实验节点：只导出已核对的镜像
SOCKET=/run/containerd/containerd.sock
IMAGE='docker.io/lab/web-runtime:7.4'
ctr --address "$SOCKET" --namespace k8s.io images list
ctr --address "$SOCKET" --namespace k8s.io images export /work/output/web-image.tar "$IMAGE"
sha256sum /work/output/web-image.tar
scp /work/output/web-image.tar analyst@10.50.0.12:/work/input/web-image.tar

# 接收实验节点：重新确认本机端点，导入后检查 CRI 能否看见
SOCKET=/run/containerd/containerd.sock
CRI=unix:///run/containerd/containerd.sock
IMAGE_ENDPOINT="$CRI"
sha256sum /work/input/web-image.tar
ctr --address "$SOCKET" --namespace k8s.io images import /work/input/web-image.tar
ctr --address "$SOCKET" --namespace k8s.io images list
crictl --runtime-endpoint "$CRI" --image-endpoint "$IMAGE_ENDPOINT" images
```

**4. 导入后按这几项查。** 比较两端归档哈希、镜像名、摘要和 CPU 平台；包只有一个平台时，不用于另一个平台。查 socket、namespace 和 CRI 插件是否指向同一实例，Deployment 引用是否匹配。`ctr images list` 有镜像后，再查 `crictl images` 和 Pod 事件，确认 kubelet 能使用。每个实际可调度节点都查一次，它们的镜像存储独立。

[containerd 导入说明](https://github.com/containerd/containerd/blob/main/docs/cri/crictl.md)及本机 `ctr images import --help`、`ctr images export --help` 用于核对版本参数。

**5. 离线时先读 pull policy，再决定要不要改实验声明。** `Never` 要求调度节点已有该镜像，`IfNotPresent` 也不能解决本地缺失且仓库不可达的问题。改变 Deployment 的策略会创建新的实验状态，不能用它推断历史策略。先确认本地镜像摘要、平台和调度节点，再修改实验声明。

```bash
# 仅限实验恢复目录：先检查归档条目、绝对路径和软链，不运行包内程序
tar -tvf /work/input/site-backup.tar
mkdir -p /work/restore/site
tar -xvf /work/input/site-backup.tar -C /work/restore/site

# 在审阅过的实验声明中指定隔离的 PV、地址、镜像与配置后，再提交
kubectl --context "$CTX" apply -f /work/restore/manifests/database-pvc.yaml
kubectl --context "$CTX" apply -f /work/restore/manifests/database-config.yaml
kubectl --context "$CTX" apply -f /work/restore/manifests/database-deployment.yaml
kubectl --context "$CTX" apply -f /work/restore/manifests/database-service.yaml
kubectl --context "$CTX" apply -f /work/restore/manifests/portal-config.yaml
kubectl --context "$CTX" apply -f /work/restore/manifests/site-deployment.yaml
kubectl --context "$CTX" get pods,pvc,services -n apps
kubectl --context "$CTX" describe pod portal-demo -n apps
```

**6. 恢复归档和提交声明时各查这些。** 用空工作目录解包，先查路径逃逸、软链、权限和成员，再把代码放入实验卷；不覆盖唯一保全目录。启动数据库前另留未启动副本，启动会写数据目录。`portal-config.yaml` 的 `metadata.name` 是 `portal-config`，核对 Deployment 引用；文件名不决定对象名。`portal-demo` 只是示意名，实际 Pod 名从列表读取；不删除已有 PVC/PV 来试修复。

**7. Dashboard 不是读业务的必经步骤。** 先用 API 和文件读取业务；需要它时，从实际 Service 和部署配置查入口，不套固定端口。

【仅在副本/仿真/授权环境执行】版本支持且 ServiceAccount/权限已审阅后，才运行 `kubectl --context "$CTX" create token dashboard-reader --namespace kube-system --duration=15m`。命令签发新凭据，`15m` 只是请求时长，实际到期时间按服务端返回核对。限制权限与网络，token 不公开。登录后继续比较卷文件、SQL 结果和应用日志，不能只看面板页面。

本节已核对两端归档哈希、镜像摘要、目标节点的运行时，以及实验声明里的镜像、PV 和配置名；`crictl images` 看不见、平台不一致，或 `metadata.name` 和 Deployment 引用不一致时，先停下。load 或 import 的输出、CRI 镜像列表和 apply 之后的 Pod 事件是同一轮实验，一并留存归档哈希、导入输出、审阅过的声明、Pod 和 PVC 列表。新 token 受控保存。

### 11.4 需要重建 Pod 时，知道会改变什么

依赖已经修好，旧日志也保存了，但新的配置还没进到正在跑的进程。先看配置怎样进入应用，再从下面的写操作里选需要的那一条。

操作顺序：先看配置进环境变量还是文件，再选 edit、rollout 或 delete 中的一条，记下新的 UID 和 ID。

**1. 先看配置怎样进入应用。** 修改 Pod 模板通常触发 Deployment 更新；只更新 ConfigMap 不一定新建 Pod。环境变量要新实例才能读取新值，文件挂载还需检查更新方式和应用缓存。

**2. 只在隔离 context 里选择需要的动作。** 【仅在副本/仿真/授权环境执行】先修好依赖、保存旧日志，再从下面命令选择需要的恢复动作：

```bash
# 编辑仅限隔离 context；在打开的模板中核对镜像和 imagePullPolicy
kubectl --context "$CTX" edit deployment portal -n apps

# 已审阅配置需要新实例生效时，选择一次受控滚动重启
kubectl --context "$CTX" rollout restart deployment/portal -n apps
kubectl --context "$CTX" rollout status deployment/portal -n apps --timeout=120s

# 已记录目标 UID 的某个 Pod 确需移除时，才单独执行；不是首轮步骤
kubectl --context "$CTX" delete pod portal-demo -n apps
```

**3. 三条命令按需要选一条。** 这三种写操作按需要选择，**不要顺次全部执行来尝试碰运气**。受 Deployment 管理的 Pod 被删除后，控制器通常会补建，前提是依赖和权限允许；没有控制器的独立 Pod 不会凭空自动恢复。镜像策略取 Never 只适合所选节点已经有准确镜像的离线恢复，不能作为统一修复值。

本节已核对配置进入应用的方式，以及这次实际执行的那一条写命令；旧日志还没保存，或所选节点还没有准确镜像时，不把 imagePullPolicy 改成 Never。执行前后的 Pod UID、容器 ID 和 rollout status 都留着，一并留存旧日志、改过的声明，以及新 Pod 的 UID。

### 11.5 复核入口、数据库与应用配置

实验里的 Pod 已经起来，还要核对 Service 后端、数据库端口和应用实际读到的配置。页面能开之后，继续沿卷看 `.env` 和数据库。

操作顺序：先对 Deployment、Pod、Service 和 EndpointSlice，再分清 3306 和 NodePort，沿卷核对配置和数据。

**1. 先把入口和后端对象保存下来。**

```bash
kubectl --context "$CTX" get deployment portal -n apps -o yaml
kubectl --context "$CTX" get pods -n apps -l app=portal -o wide
kubectl --context "$CTX" get service portal -n apps -o yaml
kubectl --context "$CTX" get endpointslices -n apps -l kubernetes.io/service-name=portal -o yaml
kubectl --context "$CTX" get service database -n apps -o yaml
kubectl --context "$CTX" get configmap portal-config -n apps -o yaml
```

**2. 按示例把端口读开。** 网站 Pod 在 node-a 且 Ready；Service selector 为 `app: portal`，EndpointSlice 指向同一 Pod，端口为实际 HTTP 端口；数据库 Service 有就绪后端。若数据库的 Service port 为 3306、NodePort 为 31306，则集群应用通过内部服务名和 3306 访问，实验客户端经所允许 Node 地址的 31306 访问。这两个端口各写各的用途。

**3. 实验客户端需要本地转发时再开通道。** 【仅在副本/仿真/授权环境执行】实验客户端可用 `kubectl --context "$CTX" port-forward -n apps service/database 13306:3306 --address 127.0.0.1` 建立本地转发，再让数据库客户端连接 `127.0.0.1:13306`。记录转发建立和结束时间。

**4. SSH 隧道连通之后还要看数据库认证。** Navicat 的 SSH 隧道是另一条路线，分别填写 SSH 主机、数据库地址和身份。隧道连通后，还要检查数据库认证、版本及数据。SSH 成功只说明隧道通了。

**5. 页面有响应后继续核对配置和数据。** 网站显示正常后，还要沿卷读取 `.env`、应用日志、数据库与缓存配置：DB_HOST 是否对应实际 Service，缓存驱动是否对应已恢复的缓存服务，后台路径与配置挂载是否一致。机器人无法连外部 API 时，可先读取其挂载配置与数据库，核对代理地址及业务记录。查看已经在卷里的数据时，不需要为这一步恢复对外通信。

**6. 用这些条件判断这一轮恢复写到哪。** PVC/PV 绑定关系与实际卷对应；镜像在被调度节点的实际运行时可用；依赖对象及配置键完整；Pod Ready、Service 后端与访问结果一致；数据库记录、卷文件和页面展示能互证。Running 或 rollout 成功都要和这些结果放在一起看，单独一条不能说明业务完整。

本节已核对selector `app: portal`、EndpointSlice 里的 Pod、数据库端口，以及卷里的 `.env` 和数据库记录；后端未就绪、DB_HOST 对不上 Service，或对象存储一类依赖缺失时，写明缺什么。页面、卷文件和数据库记录能对上同一条业务数据。HTTP 响应只说明这一次请求有返回，一并留存对象 YAML、转发起止时间、`.env`、应用日志和数据库核对结果。

<span id="12-历史容器身份把当前-id-与镜像中的旧记录分开"></span>

## 12 区分当前容器 ID 与节点镜像中的历史记录

仿真里看到一个容器 ID，镜像目录里还有另一套旧记录。先定 ID 什么时候会变，再在静态文件里交叉核对，最后看已删除对象还能从哪补。

操作顺序：先定 ID 变化的边界，在镜像数据根里静态查找，已删除对象改从审计、日志和卷核对。


### 12.1 ID 变化的正确边界

手里同时有当前容器 ID 和磁盘上的旧目录，还不知道两者是不是同一个对象。先看这次 ID 是重启保留的，还是重建出来的。

操作顺序：先看是 restart 还是重建，再把 overlay 目录和容器 ID 分开，到数据根里找旧元数据。

**1. 先分清重启和重建。** `docker restart` 重新启动同一个容器对象，通常保留其 ID。删除后重建、Deployment 创建新 Pod 或运行时重建容器才可能产生新 ID。仿真得到的当前 ID 既不能自动代表历史 ID，也不能因为不同就认定历史元数据错误。

**2. 层目录和容器 ID 分开记。** Docker 的 `/var/lib/docker/overlay2/<目录名>/` 是存储层标识，**目录名不等于容器 ID**。一个容器可引用多个镜像层。历史对象优先从实际 Docker 数据根的 `containers/<完整ID>/config.v2.json`、`hostconfig.json`、容器日志、kubelet/运行时记录中关联。数据根、存储驱动和日志驱动都需先确认。默认路径先和这台主机的实际数据根核对，再打开文件。

本节已核对当前 ID 来自重启还是重建，以及数据根里的 config.v2.json 和 hostconfig.json；数据根、存储驱动或日志驱动还没确认时，不把默认路径写成这台主机的路径。完整容器 ID 出现在容器元数据里，overlay 目录只作为层标识，一并留存完整 ID、config.v2.json、hostconfig.json，以及数据根和日志驱动的确认记录。

### 12.2 静态查找与交叉核验

镜像里能搜到业务名称，还要把它收成容器元数据、Pod UID 和日志。先找 JSON 和日志文件，再读完整 ID。

操作顺序：先找 config 和日志，读完整 ID 和标签，历史、采集和仿真分三行记。

**1. 在实际数据根里找容器元数据和日志。**

```bash
EVIDENCE_ROOT=/mnt/evidence
DOCKER_ROOT="$EVIDENCE_ROOT/var/lib/docker"
find "$DOCKER_ROOT/containers" -mindepth 2 -maxdepth 2 -type f \
  \( -name 'config.v2.json' -o -name 'hostconfig.json' -o -name '*-json.log' \) -print
rg -n 'chat-bot|lab/chat-bot' "$DOCKER_ROOT/containers" \
  --glob 'config.v2.json' --glob 'hostconfig.json' --glob '*-json.log'
```

**2. 命中目录后先读 JSON（环境无 `rg` 时可改用 `grep -Ern 'chat-bot|lab/chat-bot' "$DOCKER_ROOT/containers"`）。** 保存完整 `ID`、Name、Config.Image、创建/启动信息和 Kubernetes 标签。再按同一时段的 Pod UID、节点、镜像摘要和容器日志找对应记录。

**3. 只在层里看到名称时，先停在层。** 只在层里搜到业务名称时，先记“该层含应用文件”，再找容器元数据和层关系。展示短 ID 前留完整值并检查前缀冲突。

**4. 交付时分成三行。** 将“快照中历史对象”“采集时运行对象”“仿真新对象”分三行记录各自完整 ID、时间、节点、应用名称和支持材料。名称、标签或 IP 可以复用。多个独立记录在同一时间范围互相印证，才支持历史归属。旧元数据或日志缺失时报告缺口。新对象的 ID 只记在仿真那一行。

本节已核对完整 `ID`、镜像、Kubernetes 标签，以及同一时段的 Pod UID 和节点；只有层里的业务名称，或短 ID 有前缀冲突时，历史归属还没完成。三行记录各自有完整 ID、时间和支持材料，一并留存config.v2.json、hostconfig.json、容器日志，以及三行对照。

### 12.3 已删除对象还能从哪里核对

API 列表里已经没有旧 Pod，业务目录或日志可能还在。按材料能回答的问题去补，并记下每一种材料的限制。

操作顺序：先看审计、kubelet 和日志，再看 etcd 快照和 YAML，对上 PV 里是否还有业务数据。

**1. 按这张表选还能回答问题的材料。**

| 材料 | 可回答的问题 | 限制 |
| --- | --- | --- |
| API 审计 | 谁以什么身份请求了哪些资源操作 | 需启用及保留；记录深度受策略影响，身份可能是共享账号或服务账号 |
| kubelet / 运行时日志 | 哪个节点创建、停止或删除过什么实例 | 时间校准、轮转和清理可能造成缺口 |
| `/var/log/pods` 与容器日志 | 实例运行期间的 stdout/stderr 和重启线索 | Pod 删除后目录不一定保留 |
| etcd 保全快照 | 快照时仍保存的资源状态 | 不是完整 API 操作历史；压缩、删除与加密配置影响解析 |
| YAML、备份、运维记录 | 候选部署配置和恢复材料 | 不能单独证明已经部署或一直生效 |
| PV/NFS 业务数据 | 部署对象消失后仍可能保留的业务内容 | 需验证回收/删除规则、真实路径和文件状态 |

**2. etcd 要按启动配置找一致副本。** etcd 的位置从 `/etc/kubernetes/manifests/etcd.yaml` 或对应服务参数中的 `--data-dir` 确定，常见 kubeadm 默认目录为 `/var/lib/etcd`，证书常见于 `/etc/kubernetes/pki/etcd/`。活动目录的任意散文件复制不等于一致快照；在已获授权的控制面现场可配合证书执行 `ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key snapshot save /work/output/etcd-snapshot.db` 并用 `ETCDCTL_API=3 etcdctl snapshot status /work/output/etcd-snapshot.db -w table` 校验修订号与键总数，离线镜像则保全完整停机副本。离线解析及必要恢复放在专门实验副本，不覆盖正在运行的集群。

已删除对象在审计、节点日志、Pod 日志、etcd 快照或 PV 数据里还能对上的那一项；审计没启用、日志已轮转，或 etcd 只是活动目录的散文件时，写明不能回答的部分。每条结论旁边标明材料种类和它的时间范围，一并留存审计范围、日志范围、一致的 etcd 快照或停机副本，以及 PV 上的业务文件。

<span id="13-实战三把集群关系接到业务证据与时间线"></span>

## 13 实战三：将集群关系接入业务数据与统一时间线

网站可以打开，但一条历史业务记录已经不在。先把同一个应用的访问、存储和操作串起来，再把多台主机放到同一时间尺度。

操作顺序：先接访问、存储和操作三条链，再把主机、对象、容器和仿真动作放到同一时间尺度。


### 13.1 同一个应用的三条证据链

要定位数据库材料，并分开历史删除和恢复时的写入。先确定三条链分别停在哪个对象，再读数据目录。

操作顺序：先写三条链，沿 Service 找到数据库卷，用兼容版本在副本里读，并把新写入分开。

**1. 先把三条链写下来。**

```text
访问链：Node/Ingress 入口 → Service → EndpointSlice → Pod UID → 容器与应用日志
存储链：Pod mountPath → volume → PVC UID → PV → NFS/CSI → 业务文件或数据库
操作链：API 身份/审计 → 工作负载变更 → ReplicaSet/Pod → 节点运行时与新旧 ID
```

**2. 按这个场景往下找数据。** 网站可以恢复访问，但某条历史业务记录已不存在，需要定位相应数据库材料，并区分历史删除与恢复时的写入。

**3. 从网站配置追到数据目录。** 从网站的保全配置取得数据库 Service 名与库名引用；沿 Service selector、EndpointSlice 和数据库 Pod 找到目标实例。从数据库容器的 volumeMounts 追到 PVC/PV，再对应 storage-a 上的真实数据目录，保全数据文件、配置、binlog 及必要的密钥材料。使用与该数据目录兼容的数据库版本在副本分析。真实版本由服务、文件与日志核对，不从镜像标签或某次网页截图直接定值。

**4. 把恢复前的数据和实验启动后的新记录分开。** 对比恢复前数据、日志中的操作及实验启动后新产生的记录。涉及行事件、删除恢复和金额统计，转入[数据库恢复与日志分析](/knowledge/forensic-database-recovery/)。应用后台配置、邮件发送人、缓存类型、机器人代理等，优先从配置和业务表取得，并与页面及日志复核。哈希或盐值计算按实际代码处理，见[服务器服务与应用分析](/knowledge/forensic-server-services/)。盐和哈希不是明文口令。

**5. 先落实三个位置再分析内容。** 本节先落实三个位置：数据库实例、存放数据的卷、应用的通信入口。找到后分别保存数据库文件、日志和应用配置，再分析记录内容。网站页面、面板和外网可以后补，这三个位置先固定下来。

本节已核对数据库实例、数据卷的真实目录，以及应用的通信入口；版本还没由文件和日志核对，或 binlog 没覆盖目标记录时，历史删除和仿真写入还不能分开。Service、EndpointSlice、PVC/PV 和 storage-a 上的目录是同一条链，一并留存数据库文件、配置、binlog、应用配置，以及恢复前后的对照。

### 13.2 将多台主机的记录放到同一时间尺度

三条链上的时间来自不同主机，显示值还不能直接拼接。先记下每台机器的时区和偏差，再把对象、容器、日志和仿真动作放进同一张表。

操作顺序：先记每台主机的时间基准，再把对象、容器、日志和存储放进表，仿真动作单独标出。

**1. 按这张表保留时间和对它的动作。**

| 时间/对象 | 保留内容 | 核对动作 |
| --- | --- | --- |
| 主机时间 | UTC、本地时区、校时来源、已知偏差 | 每台 Node、存储主机分别记录，不直接按显示值拼接 |
| API 对象 | UID、creationTimestamp、版本、采集时刻 | 明确是对象创建、观察状态还是 API 操作 |
| 容器实例 | 完整 ID、startedAt、finishedAt、restartCount、Node | 同 Pod 的旧/新实例分开 |
| 日志 | 时间戳、时区、文件轮转、记录范围 | Pod 日志、节点 journal、应用日志与 API 审计交叉对齐 |
| 存储与业务 | PVC/PV 身份、实际路径、哈希、数据库记录/事件 | 文件时间不直接等于业务发生时间 |
| 仿真动作 | 操作前后快照、命令、时间及结果 | apply、启动、重启、导入等改变分别标明 |

**2. 构造结论要带着 UID、节点和缺口。** 可以写成：“采集时 `apps/portal-demo` 的 UID 为记录中的值，运行在 node-a；其 site 卷绑定同 UID 的 `apps/site-data`，后端为 storage-a 的指定目录；节点日志与运行时标签关联到同一实例。镜像和卷支持恢复当前应用内容。更早的 Pod 已不在 API 列表，历史归属需以保留的审计、节点日志和旧元数据进一步证明。”

**3. 恢复结果和更早实例分开写。** 示例结论保留 Pod UID、节点、卷目录和对应日志。恢复成功只写本次副本结果。更早实例仍按旧日志和旧元数据说明，缺什么就列什么。

本节已核对采集时的 Pod UID、节点、同 UID 的 PVC，以及对应的日志和卷目录；更早的 Pod 不在 API 列表，且审计或旧元数据还没补上时，历史归属保持未完成。同一条结论里的 UID、节点、卷和日志来自同一时间尺度，仿真动作单独列出，一并留存各主机时间基准、对象时间、容器时间、日志范围和仿真动作记录。

<span id="14-高频误区与交付清单"></span>

## 14 逐项核对高频误区与交付清单

材料已经收过一轮，判断还容易把主机数当成 Node 数，交付时也不知道哪些必须留下。先修正容易混的判断，再按清单收材料。

操作顺序：先修正易混判断，再按清单留下集群、对象、网络、数据和恢复记录。


### 14.1 先修正判断，再选择操作

准备下结论或做下一步操作时，先看这张表里有没有把两件不同的事合成一件。对上之后，再选要读的对象或要在副本里做的调整。

操作顺序：先找到容易混的那一句，按右边的复核再读一遍材料，对上了再选操作。

**1. 先逐行修正判断。**

| 易混判断 | 正确复核 |
| --- | --- |
| 主机总数就是 Node 数 | 外部 NFS、管理机不一定注册；控制节点和工作节点分别计数 |
| `get all -A` 包含全部证据 | 显式查询卷、配置、身份、网络和实际自定义类型 |
| Deployment 就是一个容器 | 按 Deployment → ReplicaSet → Pod → Container 查关系 |
| Service 是 Pod 的所有者 | 查 selector/EndpointSlice，所有权查 ownerReferences |
| PVC 名能直接推算后端目录 | 查 Bound PV、claimRef UID、真实后端与 provisioner 规则 |
| Pod 删除等于持久数据删除 | 查 PVC/PV、回收规则与实际后端文件 |
| Node 上导入 Docker 镜像就能被 CRI 使用 | 确认调度节点、真实运行时、镜像摘要与存储 |
| Running、READY 或 Dashboard 能登录就恢复完整 | 逐层验证网络、配置、挂载和业务记录 |
| 当前 token、IP、名称或 ID 代表全部历史 | 凭据有效期、对象 UID、时间范围与旧记录分别核对 |
| 重新 apply 同名 YAML 就是原对象 | 重建产生新实例和时间，按实验结果记录 |
| 关防火墙、删 Pod 是通用排障 | 先查事件和依赖，在副本做有明确目的的最小调整 |

**2. 复核过的那一行，才用来选下一步。** 主机、对象、卷、镜像和当前 ID 各自留在自己的证据上。需要改过滤规则、删除 Pod 或重新提交声明时，回到前面的实验步骤，在副本里做有明确目的的最小调整。

本节已核对这次结论避开了表里左边的混法，并且右边的复核已经有材料；某一行还只有左边的判断、没有右边的材料时，这条结论先空着。每条结论能指到 Node 清单、PV、运行时镜像或旧 UID 中的具体一项，一并留存复核时打开的对象、事件和文件。

### 14.2 最终应留下的材料

分析做完了，还要把能复核的材料收成一份清单。逐项看有没有，没有的写明缺口。

操作顺序：按清单逐项核对，敏感内容分开保存，Docker 细节转到对应的容器材料。

**1. 最终留下这些材料。**

- [ ] **集群范围：** 节点清单、主机角色、可见 namespace、版本与权限缺口。
- [ ] **对象身份：** 工作负载、Pod UID、Node、sandbox ID、完整容器 ID、镜像摘要与采集时间。
- [ ] **配置关系：** context、ConfigMap/Secret 引用、身份绑定与调度条件；敏感内容分开保存。
- [ ] **网络关系：** 入口、Service 三层端口、selector、EndpointSlice、DNS 与网络策略。
- [ ] **数据关系：** mountPath/subPath、PVC UID、PV claimRef、NFS server/path 或 CSI 标识、真实目录与哈希。
- [ ] **历史材料：** API 审计、节点/运行时/Pod/业务日志、轮转范围、保全快照与无法恢复的缺口。
- [ ] **恢复记录：** 隔离网络、启动前副本、每次写操作、导入镜像和新的对象/实例身份。
- [ ] **业务验证：** 卷文件、应用配置、数据库及页面结果的一致性；明确哪些是构造示例，哪些已经在目标验证。

**2. 容器运行时的细节继续看对应材料。** Docker 的安装、数据根、镜像层与独立容器操作可继续阅读[环境与配置](/knowledge/docker-evidence-01/)、[容器与镜像](/knowledge/docker-evidence-03/)及[日志、卷与文件提取](/knowledge/docker-evidence-04/)。

本节已核对清单里已经有文件或输出支撑的那些项；没勾上的项写明缺的是权限、日志范围、卷文件还是恢复记录。每一项都能指回前面各节留下的对象、路径或哈希，一并留存这张清单，以及敏感内容的单独保管记录。
