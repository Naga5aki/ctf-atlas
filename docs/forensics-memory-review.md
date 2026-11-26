# 内存取证模块整理与验证记录

2026-10-03 完成用户授权的独立题型归并。Forensics 下增加“内存取证”，原有六类取证题型保持原有结构；页面正文独立描述材料、操作、判读和验证，不依赖原题号或固定答案。

## 归属与连续性

| 知识点 | 维护位置 | 内容职责 |
| --- | --- | --- |
| 采集与识别 | forensic-memory | 输入覆盖、采集窗口、系统识别、Profile/ISF、地址层和证据流程 |
| 进程与攻击行为 | forensic-memory-processes | 多视图进程、PID复用、命令/环境、连接、模块、注入、内核和持久化 |
| 对象与数据恢复 | forensic-memory-recovery | 文件缓存/进程页/PE差异、文本/GUI、hive/RID/SID、LSASS与密钥目标验证 |
| Linux 与 macOS | forensic-memory-unix | 同构建符号、进程/文件/连接/内核异常，旧Profile和ISF差别 |
| 工具参数与插件 | forensic-memory-volatility | 固定官方版本的全局参数、全部内置命令、有效继承参数、用途、场景和独立volshell |
| 综合实战 | forensic-memory-practice | 下载执行、恢复文件、账户、自启动、Docker/网络互证、加密容器与交付 |

扫描全部67份原有维护稿，对22篇内存关键词命中页、5篇补充上下文与3份工具指南逐段审阅。24段迁移记录与20项保留主题见同名JSON；完整before文本与哈希保存在 `.work/memory-curation/`。原内存与Unix的页面ID和URL保留。静态PE/Go/JNI/密码校验仍在计算机取证；磁盘凭据、卷解密、Docker、服务器和流量的操作仍在各自页面，混合段保留上下文和跳转。

参数全集由一个知识点维护。Volatility工具指南继续提供准备、常用任务和结果验证，跳转到全集；Oxygen/辅助工具中的采集、支持和验收上下文保留。

## 参数全集的范围

| 版本 | 内置命令 | 全局选项 | 插件参数行 | 补充范围 |
| --- | ---: | ---: | ---: | --- |
| Volatility 2.6.1 | 265 | 23 | 541 | Windows112、Linux72、macOS77、通用/格式4；继承、删除/重复配置、条件要求及renderer |
| Volatility 3 Framework 2.28.2 | 197 | 23 | 220 | 169规范命令+28兼容旧名；规范参数194行；独立volshell25选项另列 |

“全部”限定这两个官方版本公开的内置CLI入口，不包含不断变化的社区插件、任意GUI按钮或未来版本。每个插件均有中文作用、应用场景和参数说明；内部layer/kernel/symbol/组件需求单列，不伪造CLI开关。没有专属参数的插件明确说明。

固定源码：Vol2提交 `c67017651e3cc774b944203677d15411adb7c6e4`，ZIP SHA-256 `d197c2edc0ed6d133354db98701b16813214d2e2cc7282de4ce0ba95f89a73e1`；Vol3提交 `881e970121c16f0932fb9d16fbd5fb258cbcbf75`，ZIP SHA-256 `84d57eacb4a3300f440d5cb091a33782f1a2954d0a3e0b676b09516366a92158`。Context7已先解析工具名称但未返回匹配的官方库，因此使用固定官方源码、CLI帮助和官方文档。

Vol2按Python2语法恢复AST、实际构造器调用、MRO、继承选项及删除/重复语义；未解析构造器、CLI重复键和解析失败差集均为空。Vol3静态目录与160个可导入命令的需求对照无差集，因缺依赖不能导入的37命令仍从源码完整保留；独立volshell四模式帮助均已对照。456个Vol2和519个Vol3原始文件逐字节与各自ZIP一致。详见两份内部 `vol2-review.md` / `vol3-review.md` 及结构化 `src/data/volatility-catalog.json`。

## 语义校正

区分物理镜像、进程转储、崩溃类型与页覆盖；不由MEMORY.DMP名称推定含LSASS。区分hive VA、FILE_OBJECT物理/虚拟地址、DTB、RVA和派生文件偏移。SAM Names的异常值类型可能不被普通PrintKey表呈现，保留原始Type或重建hive解析路径，和Users/SID/ProfileList互证。

Vol2历史 `--cookie` 帮助文字与实际消费不同，按值说明；cache/write回调旗标不接字符串参数。Vol3参数声明与实现消费分开，特别注明部分共享YARA选项在固定实现中未被读取；导出主映像、区域页、文件缓存和minidump不互换。volshell的NullFileHandler不能当作已保存派生物。兼容旧名指向相同实现，不计作独立检测结果。

参数全集的469个折叠块在网页中实际可展开；导入器只为这一个固定页面保留无属性的details/summary标签，其余页面继续转义。两份内存工具指南归属“工具参数与插件”，工具索引保持可见。

## 实际验证

- 数据测试：退出码0；45项通过
- 界面测试：退出码0；5项通过，失败0
- 站点检查：退出码0；18个文件，错误/警告/提示均为0
- 站点构建与检索索引：退出码0；329个页面构建完成，320个页面进入搜索索引
- 本地链接审计：退出码0；329个页面、7344个链接、170篇知识与79篇工具指南，错误0
- 网络资料登记审计：退出码0；117条记录、50项规范，错误0；缓存审计不证明受限网页全文可访问
- 实战命令核对：退出码0；34个命令块、83次Volatility调用的名称/参数/语法通过；未运行检材分析
- 迁移保全与目录投影：退出码0；240份基线完整，71份维护稿正文投影匹配，6个内存专题，旧引用无丢失；21个既有未登记来源ID另列为原有问题
- 重复导入保全：退出码0；170篇知识+79篇工具指南+71份维护稿共320个文件，内容哈希无变化；本次再次复算现存文件一致
- 资料输入核对：退出码0；14份现有原资料哈希匹配；2份早期Markdown当前不可读取，既有整理页已保留，未宣称原件重新核验
- 网页实际操作核对：退出码0；6个专题可检索，RecoverFs命中全集，265/197插件名齐全，参数可展开，两份工具指南可见，无横向溢出

浏览器实际检查独立题型、六个专题的分类与标题、全集目录和折叠参数、互链及Pagefind筛选。浏览器观察数据与截图路径见同名JSON；重复导入保全及基线差异见preservation部分。

14份原始资料的现有哈希与目录登记一致。早先两份APP/流量Markdown在原路径当前不可读取，不能声称本轮重新核验其原件哈希；两篇已经整理的站点正文与本轮before完全一致，先前读取记录保留。

## 验证边界与官方入口

没有真实内存检材，未执行采集、镜像插件分析、凭据提取或解密。命令语法、目录完整性、需求对照、构建和网页可读性检查各自仅证明相应范围；不能据此承诺所有系统构建、符号、依赖或页面覆盖可用，更不能声称原比赛材料已复跑。

- [Vol2固定官方源码](https://github.com/volatilityfoundation/volatility/tree/c67017651e3cc774b944203677d15411adb7c6e4)
- [Vol2官方Usage](https://github.com/volatilityfoundation/volatility/wiki/Volatility-Usage)
- [Vol3固定发布](https://github.com/volatilityfoundation/volatility3/releases/tag/v2.28.2)
- [Vol3固定官方源码](https://github.com/volatilityfoundation/volatility3/tree/881e970121c16f0932fb9d16fbd5fb258cbcbf75)
- [Vol3官方CLI文档](https://volatility3.readthedocs.io/en/stable/vol-cli.html)，浮动文档只作辅助，目录以固定源码为准。
