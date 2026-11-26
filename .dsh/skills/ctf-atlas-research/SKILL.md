---
name: ctf-atlas-research
description: "CTF Atlas 的信息搜集与事实核对。核对命令语法、工具版本、库或框架的当前用法，补全被省略的技术细节，或用户要求补充资料、查证事实时使用：先查项目内和本机资料，再查技术文档与一手来源，记录来源与待核项。"
whenToUse: "在 ctf-atlas 中需要核对命令语法、工具版本、库或框架的当前用法，需要补全被省略的技术细节，或用户要求补充资料、查证事实时加载。"
---

# CTF Atlas 信息搜集与事实核对

## 1. 先在项目内找

按顺序查，命中就不必外查：

1. 原始材料：工程上一级目录（只读）。
2. 内部数据（`src/data/`）：`inventory.json`（原始文件清单与哈希）、`forensics-supplements.json`（授权资料的归并关系）、`external-links.json`、`tool-inventory.json`、`volatility-catalog.json`。
3. 已有正文、相邻章节和认可样例，避免重复或前后矛盾。
4. `docs/` 下的核对记录：来源映射、版本差异、已知的验证边界。

## 2. 本机资料

都在这台机器上，只读参考：

- **工具自带的文档和源码**：`D:\CTF_MISC_Tools\` 按类别分目录，如 `Web`、`pcap`、`reverse`、`crypto`、`图像隐写`、`文档隐写`、`音频隐写`、`压缩包`、`数据库`。`D:\CTF_MISC_Tools\Web\` 下有 sqlmap、nuclei、Nmap、dirsearch-master、BurpSuite 等的目录，参数拿不准时读其中的 README 或源码。
- **取证技能包**：`D:\Desktop\学习资源\弘连_skills\` 下 8 个 `.hexp.zip`，覆盖服务器、内存、流量、EXE 逆向、APK 分析、GoldenEyes、账单分析和取证文书起草。解压到临时目录后按需读 `EXPERT.md`、`references/` 和 `skills/*/SKILL.md`，适合核对取证流程、术语和结论写法。
- **课程笔记**：`D:\Desktop\学习资源\Cyber-Security-Course-Notes-master\`，含渗透基础、协议与抓包、Web 漏洞、扫描工具、WAF 与免杀、内网渗透、应急响应、安全开发。

## 3. 再查技术文档与外部来源

- 常用来源按类别列在 `references/sources.md`，都核对过可访问。
- 库、框架、SDK、API、CLI 的当前语法与配置：已配置 Context7 时先 resolve-library-id，再按单一主题 query-docs；版本明确就核对该版本。没有该工具就如实说明“待配置”，不虚构调用。
- 用 `webSearch` / `webFetch` 找一手来源：官方文档、官方仓库、工具自带手册。先官方后教程，看清版本号和日期，不把旧版本的语法写成当前写法。
- 渗透技巧和工具参数，以工具官方文档和可核实的权威资料为准，再与靶场里的实际行为对照。
- 纯文字组织和一般脚本逻辑，不为凑流程去查无关文档。

## 4. 查到的资料怎样用

- 核对性查询（确认语法、版本、输出格式、参数含义）可以直接做，用来校正和补全已有条目。
- 把外部资料作为新的独立知识点或新来源写入，需要用户授权。授权后把来源登记到对应内部数据，例如 `forensics-supplements.json` 的 `webSources`（`id`、`url`、`reviewedAt`、`articleIds`）。
- 来源信息只进内部数据和 `docs/` 记录。页面文案不提来源名或文件出处；根 `AGENTS.md` 里用户授权的例外继续保留。

## 5. 质量与诚实

- 优先一手来源，记下 URL、版本和访问日期。
- 不编造 URL、版本号、参数或输出。查不到就标“待核”，并写明查过哪些渠道和关键词。
- 来源之间冲突时，保留可核实细节并纠正错误；案例操作与官方行为冲突时，不为了像来源而恢复错误结论。

## 6. 汇报

逐条说明关键事实的来源和版本；区分哪些来自一手来源、哪些是推断、哪些仍待核。
