# ShellBags 取证知识点整合验收

日期：2026-10-04。

## 归属与修改边界

- 新增唯一知识点 `forensic-shellbags`，标题为“ShellBags 取证：目录浏览痕迹与 ShellBags Explorer”。
- 沿用 **Forensics → 计算机取证 → 系统行为与程序 → 系统与用户痕迹**，不改分类树。
- 维护稿：`src/content-curation/forensic-shellbags.md`；生成稿：`src/content/knowledge/forensic-shellbags.md`。正文一致，补充登记仅有一个同 ID 条目。
- 注册表、U 盘取证维护稿的旧字节全文保留，仅追加指向独立详解的互链；对应生成稿保留原正文及元数据。
- Android/iOS 相关 25 项文件及已有 Volatility 知识点保持原哈希。新专项测试通过 `forensics-shellbags-preservation.json` 自动保护 16 个核心源文件及两处旧正文前缀，不依赖临时 `.work` 文件；Android/iOS 全部 25 项关联文件另外通过 448 项全基线比对核验，两个检查范围分开记录。
- 本轮源文件由 448 项基线增加至 454 项；全站知识页从 176 增至 177，Forensics 从 75 增至 76。

## 内容组织与专业核验

| 章节 | 新增内容与判读边界 |
|---|---|
| 01 概念 | 用户级目录/命名空间状态缓存；不是逐次访问、文档读取、复制或外传日志。 |
| 02 位置 | NTUSER、UsrClass、日志文件、用户归属与离线路径；XP、旧版 Wow6432Node 和现代 Windows 分开。 |
| 03 结构 | Bags/BagMRU、数字值/同名子键、MRUListEx、NodeSlot、PIDL、长短名、MFT 引用条件。 |
| 04 时间 | Shell Item MAC、键 LastWrite、视图配置时间、First/Last 条件推导；UTC、FAT 编码、精度、空值和重复交互。 |
| 05 考点 | 10 类问题映射证据；Windows 11 原始实验限定版本与前置状态；HasExplored=False 不等于从未浏览。 |
| 06 流程 | 8 步离线流程；导出、日志、哈希、工作副本、历史快照、交叉证据与报告。 |
| 07 工具准备 | SBE 与 SBECmd 分工、.NET 9 Desktop、版本核对、UTC/重载、关闭未知项目自动提交、离线加载与错误判读。 |
| 08 GUI 操作 | 树与递归范围、详情/Hex、分组/排序/过滤、输出字段、Recovered 与磁盘删除区别、CSV/TAB 导出复核。 |
| 09 CLI | 官方 `-d` 离线目录模板；`--nl true` 忽略日志，不是开启回放；参数以本机 help 为准。 |
| 10 实战 | 明确标记自建的 U 盘历史目录、UNC 目录线索案例；干净虚拟机对照实验设计，未冒充比赛或真实检材重放。 |
| 11 总结 | 易错点对照、最低证据字段、两种独立证据交叉验证与结论模板。 |

补充登记关联 15 条一手资料：Microsoft 文档、作者官方工具页面/手稿/解释、libyal 格式文档、研究论文及原始行为实验。旧资料与当前 GUI 版本要求分开，Windows build 实验结果不推广为普遍定律。

独立审阅未发现待修复的内容问题。审阅报告：`.work/shellbags-20261004/final-review.md`。原始实验、工具文档、本机静态资源和本轮实际测试四类证据分开记录。

## 工具验证实际范围

- 本机 `D:\CTF_MISC_Tools\Forensics\ShellBagsExplorer\ShellBagsExplorer.exe` 为 2026.5.0.0，签名为 Valid / ZimTech LLC；runtimeconfig 为 net9 / Windows Desktop。
- 程序 DLL 只读提取的 107 项界面文字经独立逐偏移字节核对匹配。此举只证明文字资源，不证明实际点击效果；固定 grid 列名没有冒称当前 CSV 表头。
- **本轮未启动 SBE GUI、未读取本机用户 Hive、未解析真实检材、未执行 SBECmd，未执行 Windows 11 对照实验。** GUI 菜单/操作及 CLI 命令属于资料核验后的使用模板。
- 文中 MRUListEx 自建 Python 示例实际执行，输出 `[2, 0, 5]`，终止项为 `FFFFFFFF`。

## 自动与可见验收

- 新增 6 项 ShellBags 专项测试：唯一分类/生成一致、结构与时间边界、GUI/CLI 实用覆盖、旧内容及跨平台保全、一手来源登记、自建 MRU 示例运行。
- 全量 Python：85 项，84 通过，1 项任务前已有失败；基线为 79 项、78 通过、同一失败。唯一失败为外部登记目录 `D:\CTF_MISC_Tools\Forensics\Inseyets PA` 缺失，没有创建虚假目录、删除登记或修改断言。
- UI 测试 5 项通过；Astro 检查 18 文件，0 error/warning/hint；构建 336 页，搜索索引 327 页。
- 全站审计：336 页、7637 个本地链接、177 知识页、79 工具指南，0 错误；Forensics Web 审计 117 页、50 条标准，0 错误。
- 重导入审计：扫描 166，原工具目录清单保持不变，生产文件变化 `[]`。
- 浏览器实际展开分类，看见新文章在“系统与用户痕迹”；正文的 11 个主节及未实测说明已读取；搜索 ShellBags 得到 8 条结果，新文章为第一条；页面截图保存在 `.work/shellbags-20261004/browser-shellbags.png`。

## 交付、回滚与复现

四项证据位于 `.work/shellbags-20261004/`：

- `MODIFIED_FILE.md`：与最终维护稿字节一致。
- `DIFF_FILE.patch`：相对本轮 448 项基线的统一差异。
- `VERIFICATION.txt`：准确命令、输入、输出、退出码、哈希、工具验证范围及浏览器结果。
- `ROLLBACK.sh`：经语法/可执行核验，默认只做哈希预检；`--apply` 恢复已记录的本轮源文件变化。先完成全部叶路径/哈希检查，再逐文件恢复或删除新增项。

独立副本回滚验收恢复 448 项原哈希、176 知识点 / 75 Forensics，Android/iOS 新结构仍保留；重跑原 79 项测试，仅存在同一外部目录缺失失败。生产文件前后哈希不变，仍保留新增文章。回滚范围为源文件，不冒称同时回退运行中页面、构建目录或其他任务变化。

完整观察结果、精确数量和 literal 输出以 `VERIFICATION.txt`、`change-manifest.json`、`rollback-verification.json` 为准。
