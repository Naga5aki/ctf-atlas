# XWF 独立知识点核对记录

## 落点与维护

- 页面：`forensic-xways-workflow`，Forensics → 通用方法 → 工具与路径。
- 完整维护稿：`src/content-curation/forensic-xways-workflow.md`；生成页：`src/content/knowledge/forensic-xways-workflow.md`。正文两者一致。
- 内部登记与八个网页关联保存在 `src/data/forensics-supplements.json`。
- 保留既有 X-Ways 工具指南，增加知识点跳转；将“只能用独立案件并行”的笼统表述改为指定 Wiki 的同案、独立身份及模式边界。
- 用户本次明确要求来源说明，因此此页保留逐条地址、重叠与冲突说明。没有使用其他手册、工具文档或既有页面事实扩写正文。

## 逐条阅读与章节映射

8 个地址均已取得可见正文，无整篇完全重复来源。提取清单共 410 项，逐项章节映射保存在同名 JSON；其中 390 项操作/学习要点归并或带限定保留，20 项非关键背景、作者评价、示例计数或截图辅助配置另注明上下文理由。未映射与剩余关键遗漏为 0。这个统计不是软件插件或功能数量。

| 地址 | 提取项 | 正文章节 |
| --- | --- | --- |
| [X-Ways Forensics 入门指南（一）](https://www.forensics-wiki.com/node/0197f5eb-59ea-7d5d-a88f-d997aac44bdc) | 86 | 01, 02, 04, 05, 06, 07, 08, 09, 13, 18 |
| [使用 X-Ways Forensics Excire 照片分析模块进行照片分析](https://www.forensics-wiki.com/node/0197f603-6725-7f16-9edb-87c885033916) | 98 | 05, 09, 10, 12 |
| [X-Ways Forensics 入门指南（二）——使用技巧](https://www.forensics-wiki.com/node/0197f606-44de-70fa-840c-6ed2c0462d5c) | 38 | 03, 04, 05, 11, 14, 15 |
| [XWF 高效取证思路——多开提效](https://www.forensics-wiki.com/node/0197f612-4279-7699-a18b-3ca961f7b7bb) | 28 | 02, 03, 04, 06, 15 |
| [XWaysForensics功能介绍事件列表功能](https://www.forensics-wiki.com/node/0197fd30-0ac9-7077-b4a6-bb8badd8accf) | 27 | 05, 07, 11, 13, 18 |
| [XWaysForensics包含报告表标签的使用](https://www.forensics-wiki.com/node/0197fd4e-1ec0-7f00-a3a9-aa54a0705086) | 36 | 04, 05, 07, 09, 12, 13, 16 |
| [【X-ways Forensics全面攻略】：从入门到精通，数字取证的10大实用技巧](https://wenku.csdn.net/column/45z64793a5) | 53 | 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 13, 17, 18 |
| [掌握 X-Ways Forensics 的基本操作和高级功能；深入了解 X-Ways Forensics 的高级功能和技术，掌握 X-Ways Forensics 的深层次功能和技术，深入的技术和方法；基础到高级的 X-Ways Forensics 使用技术和方法，](https://www.cnblogs.com/suv789/p/18304375) | 44 | 01, 02, 03, 04, 05, 06, 08, 09, 10, 11, 12, 13, 14, 17, 18 |

前三篇 Wiki 的正文全部读取；入门页核对图 3、9、10、11、13、14、46、47，其他 110 图没有逐图读取，不补写其附加字段。后三篇 Wiki 的图 13+23+36=72 张全部读取。总计视觉核对 80 图。CSDN 文库直接读取返回错误，但浏览器取得其概览及六章可见主文章；作者自称第四章部分内容，不推断未展示文章。专栏推荐的其他文章、付费附件和外链均不计为已读。

## 冲突和限定

| 项目 | 采用的处理 |
| --- | --- |
| 快照与镜像 | 精炼快照是解析视图；不采用文库“完整磁盘图像”的等同解释 |
| 成像入口 | Wiki 文件→创建磁盘镜像 Alt+C 优先；文库 Image a drive / Ctrl+I、工具→物理镜像仅作来源主张 |
| 事件列表 | 保留快照解析、递归范围和具体类别；不等同当前文件浏览器时间轴或文库 Tools→Timeline |
| SQLite | 采用 Wiki 外部 DB Browser for SQLite/SQLCipher；不把博客园内置数据库概括写成已确认步骤 |
| 名称、版本与时间 | 标签20.7/报告表旧称、Excire拼写差异、回忆性首发年份、图示20.0 SR-7和作者测试均保留限定 |
| 协作 | 同案多实例与证据容器分发分开；分布式协同与保护案件只读分开；导入消费标签文件的语义保留 |
| 补充来源独有主张 | 实时RAM、网络/云、脚本/API、通用解密/修复、快照变化检测及平台版本等归入17，不编造接口或步骤，不承诺能力 |

所有菜单、键名、标签和示例来自指定页面；读取和内容校核不表示当前安装版本已经验证，更不表示真实检材或 XWF GUI 已复跑。

## 验收证据

| 检查 | 命令或输入 | 观察结果 | 退出 |
| --- | --- | --- | --- |
| 基线全量测试 | `python -X utf8 -m unittest discover -s tests -v` | 57项，56通过，1失败 | 1 |
| 修改后全量测试 | 同上 | 60项，59通过，1个相同失败；新增XWF3项均通过 | 1 |
| UI测试 | `npm run test:ui` | 5通过、0失败 | 0 |
| 结构诊断 | `npm run check` | 18文件、0 errors / 0 warnings / 0 hints | 0 |
| 构建与搜索索引 | `npm run build` | 331页面，322页面被索引 | 0 |
| 链接审计 | `python -X utf8 scripts/audit_site.py` | Audited 331 pages, 7447 local links, 172 knowledge articles, 79 tool guides
Errors: 0 | 0 |
| 既有网页覆盖审计 | `python -X utf8 scripts/audit_forensics_web.py` | 117记录，errors=[] | 0 |
| 重导入 | `scripts/import_manuals.py`，恢复原工具清单字节后比较全量生产文件哈希 | 412文件、changed=[]、inventory_preserved=true | 0 |
| 浏览器 | 模块展开工具与路径；Forensics/通用方法/知识点筛选，输入XWF | 独立入口可见，找到1条结果；正文18节、来源说明8链接 | 页面实查 |

相同失败是 `test_every_catalog_location_exists_and_excludes_project_metadata`，外部目录 `D:\CTF_MISC_Tools\Forensics\Inseyets PA` 缺失；不删除清单条目或创建空目录来掩盖。工具清单162项中161个路径存在。本次保留全部清单字节。

## 内容保全

修改前407个生产文件留存于私有工作快照。仅 README、补充登记、既有XWF指南3个文件有预期修改，其余404个原有文件字节未变；新加独立维护稿/生成页、3项测试与本核对记录。既有USB、内存、虚拟币等正文及分类保留。

正文 SHA-256：`2bca5e6e95480235ecde2c9ee5284e01ccaaa53fba1a73681dd76251578a5e6c`。

截图和日志位于 `.work/xwf-knowledge-20261004/`。机器映射、读取范围、哈希及当前浏览器验收见 `docs/forensics-xways-review.json`。
