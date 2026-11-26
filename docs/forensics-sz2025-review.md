# Forensics 知识整合与复核记录

日期：2026-10-01。

## 本轮范围

依据用户指定的 `取证/2025数证杯初赛-取证知识点-模块化复习手册.md`，提取可复用知识、考点、操作方法和关联链。网站保持知识点独立，不展示资料名称、比赛、题号、固定答案及真实个人凭据。

原手册完整性记录：76,390 字节，SHA-256 `acafe9ff8cd992e0cc66d33f6fee24bf7c7e1393a22033f3201439baa2bc9821`。整理后摘要相同。

## 分类与内容归并

19 篇现有文章扩充，新增 1 篇无线取证。Forensics 从 55 篇增至 56 篇；全库知识文章从 156 篇增至 157 篇。五类题型与通用方法沿用现有分类，Docker 仍集中为服务器取证的 5 篇专题。

| 手册范围 | 知识主题与处理 | 网站条目 |
| --- | --- | --- |
| 0.1–0.4、10 | 保全、静态/动态范围、依赖关系、历史与仿真状态 | 既有流程知识保留；任务索引、易错点补依赖链与验证边界 |
| 1.1–1.2、1.3 容器身份、7.1、8.3 | Kubernetes 对象、PVC/PV/NFS、Service/端口、镜像跨节点、ConfigMap、隔离恢复、历史 ID | forensic-kubernetes-cluster（后续集中到服务器集群） |
| 1.3 删除记录、7.2 | 软删/硬删、ROW binlog、DDL/列映射、行镜像、事务、只读查询和恢复范围 | forensic-database-recovery |
| 1.3 配置与统计 | 安装/口令日志、systemd 代理、Laravel 配置/路由、版本与通知、定制派生、枚举/日期/金额与软删过滤 | forensic-server-services |
| 2.1、2.3–2.6、7.3 | 认证会话、固件页面、DNS 上下文、FTP 控制与数据、Raw 导出、反向会话与命令计数 | forensic-network-traffic |
| 2.2、7.7 无线算法 | SSID/AP/STA、握手分组/重传、PMK/PTK/MIC、协商条件、hcxtools/Hashcat 有界验证 | forensic-wireless（新增，网络取证/流量与协议） |
| 3.1–3.4、7.4、7.7 Java 算法 | Manifest/业务版本、DEX/Native、Frida 加载条件/对象/重载/类加载器、URL/时间/换行、32 位 hashCode/前导零/碰撞 | fic-case-06 |
| 4.1–4.4、5.5 调试、7.4 | RC4/AES 数据流、PE 位数/真实 ImageBase/EP、定制轮密钥/周期/CBC/尾部、系统断点模块与实验行为 | fic-case-07 |
| 5.1、5.3、5.5、8.5 | Build/修订、SAM 相对期限、bootkey/Class/ControlSet、RC4/AES 后 RID DES、外设、Xshell/Anytype、LNK/任务/Go 加载链 | forensic-windows-artifacts |
| 5.2、7.5 VHD | 虚拟磁盘逻辑末端/分配 run/簇/扇区、BitLocker 口令/恢复密钥/FVE 结构 | disk-evidence |
| 5.6、7.5 内存 | Vol2 profile/时间、RID、PID、CPU 字符串上下文、JSON、自启动插件及独立证据 | forensic-memory |
| 5.4 文档、6.2 文件尾、7.5 拼接 | 邮件/回收站/禁用账户分卷、原生多卷与 raw split、白色 run/样式、附加文档、6 位候选/Office 加密、BIN 边界 | forensic-documents |
| 5.4 媒体、6.2 图片、7.7 PNG 算法 | 完整 IHDR CRC、解码、ZIP 仅清 bit0 保留 descriptor 位、频谱/图像隐写 | fic-case-09 |
| 6.1、8.6 | 宿主/虚拟实例/账号、VMOS 数据与 importFile、内外层附件哈希 | forensic-android-storage |
| 6.1、6.3–6.5、7.6 | 微信/NTQQ 标识、安装事件、SQLCipher 参数链、Morse 与附件、Password 字段、Hawk/Conceal 封装、GCM/AAD/tag、实验恢复 | forensic-mobile-apps |
| 6.2、7.6 助记词 | 片段/位置约束、词表与 checksum、passphrase/网络/HD 路径、tokenlist/地址校验 | fic-case-08 |
| 5.3 钱包笔记、6.1 地址 | 编码层、对象/历史时间、地址格式/网络、记录与控制证据 | fic-case-12 |
| 7.1–7.7 | 工具、参数、输出口径、环境限制 | 对应实战页及 fic-case-13 索引 |
| 8.1–8.9 | Linux/Windows/Android 与应用目录，集群/虚拟实例/密钥落点 | 既有路径表完整保留；fic-case-14 补定位入口 |
| 9 高频误判、10 原则 | 握手、节点/容器、binlog、认证/GCM、地址、扇区、ZIP、内存与时间语义 | forensic-method-pitfalls 与具体专题 |
| 附录 A、B | 分析目标、证据位置与跨材料依赖全部转为通用流程；不展示题号、固定口令、私人身份/地址或答案表 | 各专题、forensic-method-index、路径索引 |

未自行增加手册明确缺少的物联网和数据分析主题。工具不强制绑定手册中的旧运行版本；按目标材料及当前官方接口核对，支持不足时说明范围。

## 重点修正

- 连续四个 EAPOL 不是有效握手的唯一判据；PTK 不使用第二次 PBKDF2。
- Docker restart 不必换 ID，overlay2 缓存目录不等于完整容器 ID，hosts 不等于 Node 清单。
- ROW 行镜像不保证所有列，阅读用伪 SQL 不直接回放；硬删也可能由备份等材料恢复。
- HTTP 200、私有 DNS 应答、静态 URL 和实验行为不单独证明历史事件。
- PNG CRC 覆盖类型码和完整 13 字节 IHDR，ZIP `0x0009` 清加密位后为 `0x0008`。
- VHD 逻辑 EOF 与最后分配扇区区分；PE 首选基址、RVA 与当次映射基址分别记录。
- SAM 域密钥/用户结构 revision 分开，新式 AES 用户哈希解开后仍有 RID 派生 DES 层。
- GCM 必须以实际封装、AAD 与 tag 认证，Hawk XML 不通用硬截。
- BIP39 checksum 不证明正确钱包；BTCRecover `--dsw` 只关闭提醒，重排由 tokenlist/顺序选项控制。
- 原生多卷与 raw split 区分，并补两种系统下显式顺序拼接的模板。

## 维护与验证

完整正文位于 `src/content-curation`，新增元信息和内部资料关联位于 `src/data/forensics-supplements.json`。导入先归并既有专题，再注册补充并应用独立正文；未登记资料、空正文和无效关联会报错。该关联不进入可见页面。

- 原有 55 篇完整正文保留；101 篇其他模块文件字节一致。
- 19 篇既有条目扩充、1 篇新增；20 篇保存本轮内部关联，既有分类/标签/ID不变。
- 重复导入后 157 篇知识文件字节一致；本轮原手册未修改。
- 24 项 Python 测试和 5 项命令显示测试通过，Astro 检查 0 错误/警告/提示。
- 构建 316 页面，Pagefind 索引 307 页面；全站 6,841 个本地链接审计 0 错误。
- 独立技术、Windows/媒体、手机三个复核组的问题均已修正；构造数据验证覆盖 GCM 参数篡改拒绝、SAM/VHD、PNG/ZIP/PE、RC4、SQL 和 URL/hashCode 等。

页面与全文检索的实际验收结果见本轮 `.work/forensics-sz2025/review-browser.json`。

**验证边界：** 构造数据验证和官方接口核对用于检查教程与实现。没有执行真实取证附件、未知程序、真实集群或大规模口令/钱包搜索，不据此宣称真实材料已经解密或归因成功。
