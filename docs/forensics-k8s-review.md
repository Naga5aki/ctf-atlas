# Kubernetes 集群取证合并与验收

完成日期：2026-10-02。

## 1. 唯一归属与覆盖

`Forensics → 服务器取证 → 服务器集群` 仅收录 `forensic-kubernetes-cluster`。正文共 14 个一级知识章节，集中讲解：

- 控制平面、节点、运行时及物理/逻辑层级；Deployment、ReplicaSet、Pod、Container 与其他主要控制器。
- API 对象、命名空间、UID、标签、所有权、spec/status、YAML 判读。
- Service 端口、EndpointSlice、DNS、Ingress/Gateway、CNI 与网络策略。
- 卷、PVC、PV、StorageClass、NFS/CSI、访问模式与回收策略。
- ConfigMap、Secret、kubeconfig、RBAC、子资源权限与 Dashboard 凭据边界。
- kubectl 查询、状态采集、日志、previous、事件；节点 CRI/containerd 与磁盘残留关联。
- 三个独立实战：业务挂载追到 NFS；多机依赖恢复、故障与镜像分发；业务数据与多机时间线关联。
- 历史 Pod/容器身份、实验状态、结论复核与交付清单。

不展示题目、比赛名称、题号、固定答案或文件出处。构造名称/地址明示为示例。Docker 与 containerd 镜像分发按实际运行时分支，控制节点和存储节点的只读路径分开。

## 2. 原有内容保全

旧 Docker 05 的第 01、03、04、05、06、08 节继续保留，编号调整为 01—06，Docker/Compose/LXC 技术正文完整。旧第 02、07、09、10、11 节及其他页面的 K8s 详解，迁移关系记录于 `.work/forensics-k8s/migration.json`。

Docker 保持五篇，最后一篇更名“Docker 取证 05｜网络与 Compose”。旧知识点 ID 可继续访问，相关目录和速查入口改为指向新正文。内部补充注册表和维护约定同步更新，详细内容由 `src/content-curation` 持久维护。

157 篇既有知识点无删除；11 篇更新正文或导航，146 篇哈希不变；新增一篇后合计 158 篇（Forensics 57 篇）。连续两次导入全部 158 篇内容哈希一致。学习手册输入哈希不变。保全结果见 `.work/forensics-k8s/retention-review.json`。

## 3. 参考核对

| 参考 | 读取范围 | 使用方式 |
| --- | --- | --- |
| https://www.cnblogs.com/WXjzc/p/19190900 | 公开服务器取证部分 | 多机依赖、NFS、镜像、业务恢复与历史身份方法归纳 |
| https://mei-you-qian.github.io/2025/11/05/2025%E6%95%B0%E8%AF%81%E6%9D%AF%E5%88%9D%E8%B5%9B/ | 浏览器公开服务器部分 | PVC/挂载故障、配置、镜像与业务证据相互核对 |
| https://mp.weixin.qq.com/s/APyP-mcd40kGCn2U1RKrZA | 未读取；浏览器访问策略阻止 | 保留待核对，未使用替代通道绕过访问策略 |
| Kubernetes 官方文档（Context7 及官网） | 架构、对象、工作负载、存储、配置、权限、日志及 CLI | 核对主要概念与命令语义 |
| containerd 官方文档和 CLI 实现 | CRI、ctr images import/export | 区分运行时端点、镜像端点、namespace 和归档行为 |

已修正容易混淆的结论：重启不等于重新创建 Pod；load 不一定丢失标签；动态 NFS 注解不是通用路径公式；四台主机不等于四个 Node；容器启动或端口探测成功不能单独证明业务恢复。

## 4. 验收证据

| 验收项 | 实际结果 |
| --- | --- |
| 全部 Python 数据/分类/保全测试 | 26 项通过 |
| 命令显示界面测试 | 5 项通过 |
| Astro 检查 | 18 文件，0 错误、0 警告、0 提示 |
| 构建与检索索引 | 317 页构建；308 页检索索引 |
| 本地链接审计 | 6882 个链接，0 错误 |
| 既有外部公开资料维护审计 | 117 页记录、50 项规范，缓存核对通过 |
| 文内命令示例 | 20 个 Bash 块语法检查；未执行集群操作 |
| YAML 示例 | Deployment、Service 两个对象解析成功 |
| PVC/PV 示例脚本 | 正常 NFS 绑定、错误 UID、Pending 缺卷、CSI 后端四组构造数据判读符合预期 |
| 内容独立性与合并复核 | 两次独立只读复核，已修正对象名、静态/接口流程与多主机路径 |
| 浏览器分类 | 服务器集群 1 篇；点击进入新正文；14 项目录正常 |
| 浏览器排版 | 浅色；标题层级、表格、等宽命令块清晰；页面无整体横向溢出，代码块支持自身横向滚动 |
| 实际搜索 | kubectl + Forensics 返回正文及通用索引两项；再选择服务器取证，仅返回新正文一项 |

命令与内容复核不等于真实多机检材的重放；本次未启动或改写取证对象，也未实际运行 kubectl、Docker、ctr 或 crictl 操作。测试输出、示例判读与哈希记录位于 `.work/forensics-k8s`。
