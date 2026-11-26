# CTF Atlas

个人本地 CTF 知识库。网站以浅色界面呈现 **Web、Misc、Reverse、Crypto、Forensics** 五个模块，支持搜索知识点、工具、题目和 WP。Pwn / Binary Exploitation 的现有附件保留在“待归档”。一般页面不展示资料出处；XWF 指定链接整理页按用户要求在文末保留来源说明；iOS 和 Android 原理页按用户要求标注真实比赛资料与整合变更。

## 当前内容

- 177 篇知识点：Web 5、Misc 88、Reverse 4、Crypto 4、Forensics 76。Web、Reverse、Crypto 各用三组明确主题；Forensics 按计算机、内存、服务器、手机、网络、虚拟币、文件与多媒体七类题型浏览，通用方法另列。虚拟币取证保留原资金流页面作入口，六篇新正文按基础、钱包、链上交易、追踪与实战展开，并提供离线合成练习。Docker 内容集中为 5 篇连续专题；Kubernetes 集中为服务器取证下“服务器集群”的一篇完整知识点；RAID 重组取证作为独立知识点归入计算机取证的“磁盘与文件系统”。网站重构在服务器取证下独立展示，集中三要素、宝塔与PHP/Java实战流程。手机取证下新增 iOS 取证子模块，含原理流程、既有备份专项和 iLEAPP/Plist_Editor 工具实战三篇，详见 [整合与验收说明](docs/forensics-ios-review.md)。
- 79 篇工具使用指南，其中 Forensics 9 篇；工具索引登记 162 个独立程序目录、入口文件和快捷方式，本轮核对其中 161 个路径可定位，1 个外部目录缺失，保留登记并在验收记录中说明。
- 67 个 ZIP 附件的题目卡片；其中 11 个 Pwn 类附件在“待归档”。
- 3 篇依据本地 WP 整理的摘要，已连接相应题目与知识点。**这些摘要经过原文核对，尚未独立复跑题目附件。**
- 80 个原始文件的内部清单与 SHA-256 校验值。原始文件保留在上一级 `学习资源` 目录，本站不修改或复制它们。

用户指定的四个网站入口及两个 Wiki 知识目录已建立 [逐页覆盖记录](docs/forensics-web-coverage.md)，共 117 条。已整理公开可读的正文、图示、工具名称和公开附件；DigiForensics 的 58 页均提示登录阅读全文，已整理公开开头及 50 项规范索引，登录后的完整正文仍待补充。内部记录、抓取缓存和来源标识不进入网站显示。

## 本机运行

已在 Windows、Node.js 24.18.0 上构建验证。首次使用：

```powershell
cd 'D:\Desktop\学习资源\ctf-atlas'
npm ci
npm run build
npm run preview
```

在浏览器打开 `http://127.0.0.1:4321/`。预览服务只绑定 `127.0.0.1`。站点内容与搜索索引构建后可离线使用；搜索由 Pagefind 在构建阶段生成，因此**新增内容后需要重新运行 `npm run build`**，再刷新预览页面。`npm run dev` 适合排版开发，但完整搜索要在构建后的预览版检查。

## 新增内容

维护知识点时只细化、校正已有主题，不自行补入原知识库未涉及的独立知识点。需要增加主题时，先由使用者提供相应内容或明确指定范围。

知识点放入 `src/content/knowledge/`，工具指南放入 `src/content/tools/`，WP 放入 `src/content/writeups/`。可以复制 `templates/knowledge.md`、`templates/forensics.md` 或 `templates/writeup.md`，改成独立的英文文件名，再填写标题、简述、模块、主题、标签和正文。Web 使用“协议与抓包 / Web漏洞 / 源码与环境”，Reverse 使用“程序结构 / 逻辑逆推 / 验证与复现”，Crypto 使用“参数与表示 / 公钥密码 / 对称与实现”；Misc 保持七类主题。Forensics 文章必须填写 `track` 与 `topic`，从 `src/data/forensics-taxonomy.ts` 的七类题型和通用方法中选择；新增分类先更新该文件及覆盖测试。Docker 相关文章只归入服务器取证的“Docker 与容器”，避免跨分类重复。题目附件放到上一级目录的 `Misc题收集` 中，运行：

```powershell
python scripts/import_sources.py
npm run build
```

导入程序只读取原目录：记录相对路径、文件大小、哈希以及 ZIP 元数据，不解压或执行附件。`wp.txt` 中的单个 HTTPS 链接会作为比赛外部参考保留。新增题目后，查看 `src/data/inventory.json` 中生成的稳定 `id`，在相关知识点或 WP 的 `challengeIds` 中填写该值。

当知识总结、工具说明或本机工具目录发生变化时，安装 `python-docx` 后重新生成完整章节与工具索引：

```powershell
python -m pip install python-docx
python scripts/import_manuals.py
npm run build
```

生成器会将 Docker 编号章节整合为五篇专题，将综合讲义的三段容器细节搬入对应专题，并把重叠的五篇通用方法合并为两篇，同时更新其他自有编号页面与 `tool-inventory.json`。容器段落原位置保留跳转。Kubernetes 概念、kubectl、CRI、持久存储及多节点恢复统一维护在 `forensic-kubernetes-cluster.md`，服务器集群仅保留这一篇详细正文；其他入口通过链接引用。Forensics 的 76 篇完整独立正文统一维护在 `src/content-curation/<页面ID>.md`，覆盖生成与手工条目；导入在专题归并后应用维护稿，保留页面 ID、分类、标签和关联信息，避免重新带回具体题名、题号及答案式叙述。修改正文时直接更新对应维护稿，再运行导入和核对；空维护稿会使导入报错。新增授权资料的归并关系和新页面元信息在 `src/data/forensics-supplements.json` 维护；先将资料登记到内部目录，再填写对应条目，重复导入会保留正文与关联且不产生重复页面。其他模块的手工知识点和 WP 保持原有维护方式；Misc 的二维码判读和 TTL 隐写仍按原规则合并补充说明。两篇早期 Docker 短文保存在 `src/content-archive/docker/`，构建时不单独展示，其技术内容统一进入专题页。

每篇内容只能选**一个主模块**；标签从 `src/content.config.ts` 的固定词表中选择，最多三个。能用模块表达的主题就不要再重复加标签。`sourceIds` 仅供内部维护，不展示在网站中。

授权网页的归并关系使用 `forensics-supplements.json` 中可选的 `webSources`：登记稳定 `id`、页面 `url`、复核日期 `reviewedAt` 和既有文章 `articleIds`。导入只保存内部关联，不自动抓取网页；会先检查关联、模块与 URL，错误时不写入补充页面。复核日期用于更新对应知识点，重复导入不重复添加标识。本轮两篇网页的主题归属、修正项和阅读范围见 [网站与 FTP 内容覆盖记录](docs/forensics-2024-links-review.md)。

本地提供的 APP 与流量 Markdown 已按既有分类整理：APK 入口、数据链、JNI、加固和受控动态观察补入 Reverse 的 `reverse-bytecode`；扫描、身份认证、Kerberos、SMB 和 WebShell 分析补入网络取证的 `forensic-network-traffic`。两份资料的内部来源标识、哈希、缺图范围与技术校正在 [APP 与流量内容核对记录](docs/app-traffic-review.md) 和同名 JSON 中维护。Reverse 正文按手工页面维护，流量正文按 Forensics 维护稿导入；内部来源 URL 来自用户提供的导出文本，不表示在线网页及缺失图片已读取。

RAID 重组独立页面为 `forensic-raid-reconstruction`；三篇授权网页只关联这一页，计算机取证指南与镜像识别页面保留跳转。资料覆盖、技术校正和实际验收范围见 [RAID 内容核对记录](docs/forensics-raid-review.md)。

XWF 独立使用知识点为 `forensic-xways-workflow`，归入 Forensics 通用方法的“工具与路径”；内容只依据用户指定的八个链接重组，文末保留逐条来源说明、重叠与冲突处理。来源映射和验收见 [XWF 内容核对记录](docs/forensics-xways-review.md)。既有 X-Ways 工具指南保留。

U盘取证独立页面为 `forensic-usb-evidence`，归入计算机取证的“磁盘与文件系统”。正文覆盖设备、卷和用户关联，NTFS MFT 结构、SI/FN 时间、runlist，以及 XFW 和 MFTECmd 的实际用法；包含构造 FILE/USN 记录练习。阅读范围、版本差异和实际验证见 [U盘内容核对记录](docs/forensics-usb-review.md)。练习不是完整 NTFS 镜像，也不代表真实竞赛检材已复跑。

虚拟币取证是授权新增的独立题型，入口为 `fic-case-12`，原资金流完整正文与 URL 保留。六篇正文覆盖区块链结构、密码学、共识与节点、钱包、BTC、EVM/TRON、平台/跨链追踪及实践；复核公开竞赛题型后改写为独立场景。资料映射和验证边界见 [虚拟币内容核对记录](docs/forensics-crypto-review.md) 与 [区块链补充核对记录](docs/forensics-blockchain-review.md)。基础页新增八节核心概念，覆盖助记词与种子、密钥与地址、HD派生、钱包分类、智能合约、交易执行及资产/链外数据；见 [基础概念核对记录](docs/forensics-blockchain-concepts-review.md)。`public/practice/crypto-forensics/` 提供标准库脚本和练习数据：原账本、CSV、BTC交易JSON及三叶Merkle树使用构造材料，新增创世区块向量使用公开固定数据。实际链请求和真实竞赛检材未独立复跑。

内存取证独立入口为 `forensic-memory`，下设采集与识别、进程与攻击行为、对象与数据恢复、Linux/macOS、Volatility 参数与插件、综合实战六个知识点。原内存/Unix URL 保留，静态程序逆向仍在计算机取证的“程序与恶意代码”。完整参数与插件速查维护于 `forensic-memory-volatility`；两代工具按固定官方版本列内置命令、继承选项、兼容别名及依赖，第三方插件单独说明。机器目录数据位于 `src/data/volatility-catalog.json`，章节迁移、固定版本与验证记录见 [内存取证内容核对记录](docs/forensics-memory-review.md)。没有真实内存检材，本轮验证不等于取证流程已复跑。

Android 取证与 iOS 在手机取证中同级，主线分原理流程、既有目录证据、ADB/ABE/ALEAPP 工具实战三篇；原移动终端细化案例同在该分类，合计四篇。旧目录七节、移动终端十一节、跨平台应用与 iOS 正文保持完整。指定指南全部主题的逐项处理见 [覆盖记录](docs/forensics-android-coverage.json)，真实比赛来源、版本校正、合成验证与验收见 [整合说明](docs/forensics-android-review.md)。

## 维护与验证

```powershell
python -m pip install python-docx
python -m unittest discover -s tests -v
npm run test:ui
npm run check
npm run build
python scripts/audit_site.py
python scripts/audit_forensics_web.py
```

本地预览时还应实际检查首页、五个模块、题目与 WP 的关联，以及搜索关键词和筛选。来源文件若更新，重新生成清单后对照校验值，再审阅受影响的人工内容。外部 WP 链接只是参考，不能等同于本站已完成的 WP。

本轮新增的合成验证覆盖 Chromium/Firefox 查询与关联、时间换算、iOS 备份路径哈希以及 WAL 一致快照。页面和工具操作的说明不等于真实检材已独立复跑。保留私有网页缓存时，可用 `python scripts/audit_forensics_web.py --cached` 同时检查读取哈希和目录覆盖。

当前工程用于个人本地使用；没有公开部署、账号、后台服务或云端数据同步。题目 ZIP 不由网站提供下载，题目卡片给出相对于 `学习资源` 的原始路径。

## ShellBags 专项整合

计算机取证的系统与用户痕迹下新增唯一 ShellBags 正文，详解目录状态、MRU、时间语义、版本差异与 ShellBags Explorer 离线操作；注册表和 U 盘旧正文保留，仅增加跳转。GUI 菜单按官方手稿与本机2026.5.0静态资源核对，没有执行真实 Hive 解析。详见 [整合与验收说明](docs/forensics-shellbags-review.md)。


## RegRipper 专项补充

RegRipper 详解并入既有注册表取证正文的新 §10，不新建分类或重复文章。内容覆盖13项 CLI 参数、按问题选择插件、profile/多用户批处理、TLN、GUI操作、3/4差异及空结果判读；原正文完整保留。正文与插件实现逐项核对，实际运行仅使用纯自建 Hive。来源、审阅、验证与维护入口见 [整合与验收说明](docs/forensics-regripper-review.md)。

## MySQL 实战命令专项补充

既有 `forensic-database-recovery` 保留原11节，追加§12–25，覆盖连接与参数、元数据、业务聚合、时间/编码、8.x查询、导出核验、表空间/损坏恢复及binlog/PITR。6个真实赛事考点映射与23组命令见 [核对记录](docs/forensics-mysql-commands-coverage.json) 和 [整合与验收说明](docs/forensics-mysql-commands-review.md)。自建六表15组核心SQL与逻辑导出/重导入已在独立MySQL5.5.62副本运行；不把这些结果当作8.x高级查询、物理恢复或真实比赛复跑。练习入口为 `public/practice/mysql-forensics/`。
