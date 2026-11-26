# CTF Atlas 维护约定

- 只修改 `ctf-atlas` 内的网站和整理内容。上一级 `学习资源` 中的原始 DOCX、PDF、Markdown、TXT 与 ZIP 保持只读。
- 站点维持浅色界面；展示知识点、工具、题目和 WP。任何用户可见的页面文案都不提及源文件、文档出处或原文。
- 主模块限定 Web、Misc、Reverse、Crypto、Forensics。Pwn / Binary Exploitation 进入待归档，不硬塞进五大模块。
- Forensics 知识点按 `src/data/forensics-taxonomy.ts` 的七类题型与通用方法归类，文章填写 `track` 和 `topic`；不使用“专项笔记”兜底分类。虚拟币取证是用户授权的独立题型，按基础、钱包、链上交易、资金追踪与实战归类；`fic-case-12` 保留完整资金流正文及 URL 作为专题入口。Docker 只归入服务器取证的“Docker 与容器”，其五篇合并专题由 `scripts/import_manuals.py` 生成，修改后同步核对正文保全与分类覆盖测试。
- 内存取证是用户授权的独立题型，按采集与识别、进程与攻击行为、对象与数据恢复、Linux 与 macOS、工具参数与插件、综合实战归类。保留 `forensic-memory` 和 `forensic-memory-unix` 的 ID；静态程序逆向仍归计算机取证的“程序与恶意代码”。Volatility 2/3 全局参数和内置插件清单按明确的官方版本维护于 `forensic-memory-volatility`，区分插件参数、内部依赖、兼容别名与第三方扩展，保留机器可核对的目录数据和版本证据。
- 标签只用 `src/content.config.ts` 中的固定词表，每篇最多三个。先选择主模块，再加确实有助于跨模块检索的标签。
- Kubernetes 详细概念、命令、节点关联、存储与多节点恢复统一维护在 `forensic-kubernetes-cluster`，只归入服务器取证的“服务器集群”。Docker 专题和通用索引保留必要的识别提示与跳转，不重新复制 K8s 详解或 kubectl 命令块。
- 非 Forensics 知识点必须填写 `topic`；Web 限“协议与抓包 / Web漏洞 / 源码与环境”，Reverse 限“程序结构 / 逻辑逆推 / 验证与复现”，Crypto 限“参数与表示 / 公钥密码 / 对称与实现”，Misc 保持现有七类。新增文章优先补既有类别，不设“其他”兜底。
- 整理内容时填写内部 `sourceIds` 以便维护；这个字段不展示在网站。没有复跑附件，就不要声称解题过程已实测验证。
- iOS 取证是用户授权的手机取证子模块，原理与流程、既有备份专项、工具与实战各有唯一正文。按本次明确要求，在 `forensic-ios-forensics` 的真实比赛段落标明可核查的赛事和公开解析，不编造题目或固定答案；其余条目沿用独立实用的写法。Plist_Editor 按本机实际 Plist Editor Pro 产品及官方手册维护，不混同其他同名工具。
- Android 取证是用户授权的手机取证子模块，与 iOS 同级，入口/目录证据/工具实战各有唯一正文。旧 forensic-android-storage 的 ID、topic 和七节正文保留，跨平台加密聊天与虚拟空间详细步骤不重复。forensic-android-forensics 按本次明确要求标明真实赛事与可核查解析，不编造题目、不复用固定答案；合成工具验证不得冒充比赛重放。
- 知识点只整理、细化和校正已有知识库中的主题；不得自行新增原知识库没有的独立知识点。需要延伸说明时，放在对应原有条目内并注明验证边界。
- Forensics 正文保持独立实用，不出现具体题号、题名、比赛简称和答案式叙述；实战示例写清场景、材料、证据位置、操作命令、结果判读、验证和限制。完整正文维护于 `src/content-curation/<页面ID>.md`，生成器在专题归并后统一应用；不得直接编辑生成正文后遗漏对应维护稿。
- 网站重构是用户授权的服务器取证独立知识点，完整流程统一维护在 `forensic-website-reconstruction`，包括三要素、宝塔、PHP备份和Java站库分离实战、仿真认证与外部依赖、验收及回滚。其他条目保留配置/日志/数据库取证内容与跳转，不重复重构操作。
- 题目附件只记录元数据、哈希和路径；导入过程中不执行 ZIP 内程序。新增外部 WP 仅标为参考，不自动认定所有题目已有 WP。
- CTF 操作命令默认使用 Kali/Linux 语法。涉及文件修改的步骤说明副本、目标偏移和修改后的实际验证。
- 修改后运行单元测试、`npm run check`、`npm run build`、`python scripts/audit_site.py`，并在浏览器中检查实际页面和搜索。检查链接、WP 关系及目录计数，不只看构建退出码。
