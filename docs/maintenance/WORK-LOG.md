# 知识库共同维护日志

本文件为共享交接记录，不是自动锁。每一批追加记录，保留历史；同一范围仅一个代理写入。

## 2026-10-25 · SQL 注入页按类别重排

- 日期 / 执行者 / 用户任务：2026-10-25 / Cursor / 按报错、联合、布尔、时间、堆叠重写 `web-data-query.md`。后端 PHP 和数据库句子分开，每类有步骤表，SQLMap 按场景给命令，文末附语法备查。
- 修改前备份：`.work/web-sql-categories-20261025/web-data-query.md`，哈希 `ff085d4126dcace0f79a2c0612ec7423622a3214825a73e2fc885d025f9cdaff`。
- 同时把 `web-local-lab` 里指向 07.4 的句子改成「SQLMap 一节」。
- 没有写入：逐字拖库的拼接、导出整库和在操作系统上执行命令的 sqlmap 参数。
- 检验：`npm run build` 355 页，Pagefind 346 页、16348 词。浏览器打开 `http://127.0.0.1:4329/knowledge/web-data-query/#11-sqlmap-按场景选参数`，目录 01–12 和 SQLMap、语法备查都在。没有用真实靶场复跑。

## 2026-10-25 · SQL 注入页改成按现象讲解

- 日期 / 执行者 / 用户任务：2026-10-25 / Cursor / 重写 `web-data-query.md`，命令缩短，说法改成先看正常句子、再按页面现象分类。
- 修改前备份：`.work/web-sql-rewrite-20261025/baseline/web-data-query.md`，哈希 `6e21d027f6c526ddbdfbaeefb4fbb30122e49b006c4e36d73befd48d3fbd7501`。
- 保留：四种语法位置、报错与报错注入的差别、32 字符截断、宽字节三条、转义后再删字符、二次注入、`information_schema`、`secure_file_priv`、家族对照、sqlmap 参数。标题和锚点未改。
- 没有写入：联合查询拼接语句、报错截取语句、盲注脚本、写文件拿壳。
- 检验：`npm run build` 355 页，Pagefind 346 页、16326 词。页面 `http://127.0.0.1:4329/knowledge/web-data-query/` 开头已是新稿。等用户看完口气后再决定要不要推广到其他页。

## 2026-10-25 · Web 六页补入综合靶场的复核顺序

- 日期 / 执行者 / 用户任务：2026-10-25 / Cursor / 把一份多端口 Web 题解里的知识点、考点和工具用法归进现有 Web 页面。不新开页面，不写题号、flag 和可直接提交的利用语句。
- 修改前备份：`.work/web-writeup-20261025/baseline/src/content/knowledge/`。改前哈希前 16 位：`web-local-lab` `21c4d26727bae0ba`，`web-info` `4c5cbbef508876b4`，`web-language-reading` `093ba9c303ed5bcc`，`web-data-query` `66ba0e51d0af0266`，`web-runtime-boundary` `6eaeb760ccf30e86`，`web-file-boundary` `c385829ec7cc90d3`。
- 写入：
  - `web-local-lab` §06：端口扫描、dirsearch、Burp、sqlmap、redis-cli、Base64、opcode 各回答什么；`redis-cli info server` 只用来确认有没有口令。现哈希前 16 位 `c2e3938be0f8a60d`。
  - `web-info`：HTML 注释里的 opcode 文本、FineCMS 以内容模型的当前扩展名为准、扫描器报告的 `heapdump` / `env` 要打开该路径再记。`04d089b76aff2058`。
  - `web-language-reading` §01.3 读 opcode 操作数；§02.4 Gateway 的 CVE-2022-22947 与 Web Flow 的 CVE-2017-4971 只写成立条件。`fdad39d60ca68d51`。
  - `web-data-query` §02.1 区分语法错误和报错注入；§03.3 `addslashes` 之后再 `str_replace`。`6e21d027f6c526dd`。
  - `web-runtime-boundary`：地址白名单先比较参数；输出可能在新文件里，不写写文件或反弹命令。`5184403bb6194513`。
  - `web-file-boundary`：目录扫描只给出参数名；直接包含会执行但响应可以是空的；上传表增加后台字段配置。`e8624a4aeeba9b7f`。
- 没有写入：flag、内网地址、木马连接、反弹命令、上传绕过文件名、Gateway 路由正文、后台口令。dirsearch、Burp、sqlmap 的参数表保持原页。
- 检验：分类测试 1 项通过。`cursor_project_check.py` 0 错误。`npm run check` 0 错误 0 警告。`npm run test:ui` 5/5。`npm run build` 355 页，Pagefind 346 页、16325 词。`audit_site.py` 8210 条本地链接、0 错误。Python 3.12 全套 214 项，失败 9、错误 3。改前快照是失败 4、错误 1（工具目录缺失、MySQL 旧前缀哈希、docker-evidence-01 旧哈希、上级 Docker 指南不在仓库）。本批没有改那些文件。多出来的失败在宝塔绑定测试、SSH 示例解析、`test_baota_binding_content.py` 与审查记录哈希不一致，以及 docker 合并测试、SSH 配置检查两项错误；都不是这六篇 Web 正文。
- 页面：`http://127.0.0.1:4329/knowledge/web-local-lab/#06-按工具能回答的问题分类` 能打开，工具表和 `redis-cli` 命令可见。搜索 `BEGIN_SILENCE` 命中 PHP、Java与Python。构建页里有 `03.3 转义之后又删掉字符`、`01.3 给的是 opcode`、`02.4 Gateway` 和上传表的「后台字段配置」。没有用真实靶场复跑。

## 2026-10-15 · Forensics 全模块审查改进方案分批执行（已验收）

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 按已批准的 Forensics 全模块改进优化执行方案，依次执行阶段一至阶段四（语言止损、服务器取证剩余两层化与补缺、单篇结构顺畅化与 Volatility 大表折叠、跨页分工与导航闭环）。
- 修改前基线备份：`.work/forensics-full-polish-20261015/baseline/`（386 份文件，清单见 `baseline-hashes.json`，修改后哈希见 `after-hashes.json`）。
- 四阶段执行完成项（共修改 43 篇 Forensics 维护稿与生成页，全部 LF 双源同步）：
  - **阶段一（B-S1.1～1.3）**：清理 `forensic-guide-mobile`、`forensic-android-forensics`、`forensic-android-storage`、`forensic-android-tools`、`forensic-ios-backup`、`forensic-ios-tools`、`forensic-xways-workflow` 中的内部维护话术与来源对比腔；修复 `fic-case-04`、`fic-case-05`、`forensic-database-recovery`、`docker-evidence-01..05`、`git-docker-03` 中 172 处节尾分号拼接残句并平滑 274 处次级重复箭头口号；润色 `forensic-fs-*` 7 篇电报句式与做题腔。
  - **阶段二（B-S2.1～2.3）**：完成服务器取证剩余 7 篇（`git-docker-04..08`、`forensic-kubernetes-cluster`、`forensic-cloud-vm`）两层阅读改造，全部二级标题动作化并加固定旧锚点 `span`（在 `scripts/import_manuals.py` 注册白名单并在 `tests/test_server_clear_flow.py` 新增专项测试），消除全部 100 处“这次要留下的结论”四标签机械收尾；将 `git-docker-04..08` 页首重复 5 次的 `git()` 包装函数折叠并指向 `git-docker-03`；在 `forensic-kubernetes-cluster` 补齐 §08.2 Secret/RBAC 只读导出命令、§09.1 `podLogsDir`/native sidecar 版本说明、§10.2 JSON 路径说明、§12.2 `grep -Ern` 备选及 §12.3 `etcdctl snapshot save/status` 命令；在 `forensic-cloud-vm` 补齐 §04 VMware/libvirt/PVE 挂接配置字段与 §07 `ewfmount` 命令并折叠 §09 口令恢复步骤。
  - **阶段三（B-S3.1～3.4）**：消除 `forensic-memory`、`forensic-windows-artifacts`、`forensic-ios-backup`、`forensic-mobile-apps`、`forensic-network-traffic`、`forensic-file-recovery`、`forensic-documents`、`forensic-media` 单篇内部的“§01–04 简短提纲 + §05 重头再来”两段式拼接；在 `forensic-memory-volatility` 将 265 个 Vol2 插件与 197 个 Vol3 插件按 8 个操作系统分组放入 `<details>` 折叠；在 `forensic-guide-network` 与 `forensic-network-traffic` 建立到 `forensic-traffic-filters` 的双向链接；将 `fic-case-07` 标题明确为「程序样本与恶意代码取证：PE、Go、SO 与加密容器」；在 `forensic-crypto-bitcoin` 与 `forensic-crypto-account-chains` 补充 RPC 返回 JSON 短示例。
  - **阶段四（B-S4.1～4.3）**：理顺 `disk-evidence`、`fic-case-02` 与 `forensic-fs-*` 的交叉跳转；将 `fic-case-06` 标题明确为「Android 应用与 APK 逆向取证」、纳入 5 篇 Android 顶部模块导航并收缩重复基础目录表；在 `forensic-method-index` §03 建立到 `fic-case-14` 的目录字典导流并将五类任务路径表按需折叠。
- 检验结果：`cursor_project_check.py` 通过（`curation_mismatches: []`）；`test_server_practical_review.py` 10/10、`test_server_clear_flow.py` 19/19（含 7 篇新子测试）、`test_filesystem_forensics.py` 3/3、`test_memory_catalog.py` 2/2、`test_android_content.py` 10/10、`test_ios_content.py` 5/5、`test_ios_usage_supplement.py` 4/4、`test_xways_workflow.py` 3/3、`test_shellbags_content.py` 6/6、`test_kubernetes_content.py` 2/2、`test_crypto_ledger.py` 11/11、`test_blockchain_header.py` 11/11、`test_forensics_web_examples.py` 6/6、`test_traffic_filters.py` 3/3 全部通过。完整 Python 测试 214 项（新增 1 项），失败 4、错误 1 与改前基线完全一致（零新增失败）。`npm run test:ui` 5/5，`npm run check` 0 错误 0 警告，`npm run build` 355 页、Pagefind 346 页 16309 词，`audit_site.py` 355 页、8203 条本地链接、0 错误，`audit_forensics_web.py --cached` errors 为空。独立副本回滚试验 386/386 文件 SHA-256 完全一致。本会话无浏览器 MCP 工具，已对 `dist/knowledge/` 构建 HTML 逐页校验目录、旧锚点 `span`、`<details>` 折叠与新增内容；浏览器可视化交互与窄屏滚屏标记待复核。

## 2026-10-15 · 计算机取证下新增文件系统取证

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 在计算机取证下新增「文件系统取证」，按文件系统拆成独立知识点。
- 范围：只新增 7 页和分类、测试、审查记录里对应哈希。没有改 U 盘、镜像识别、RAID 和文件雕刻的原有正文。同日另一批正在写现有页，本批没有回滚那些文件。
- 分类：`src/data/forensics-taxonomy.ts` 的计算机取证增加簇「文件系统取证」，topic 为卷与引导扇区、NTFS、FAT、exFAT、ext、其他文件系统、图形工具。原「磁盘与文件系统」仍在。
- 新页（维护稿 / 生成页前 16 位）：volume `3378d7b540977e32` / `0f95f329c038db00`；ntfs `2f8733ce4eb53534` / `408fdd49d6152469`；fat `7a74a32c264a1678` / `a42ec72be212546c`；exfat `ba3cad6a7670aa47` / `064256304c258f4e`；ext `d1402d4a4c5b824b` / `781ccb4acba4b832`；other `50665d1bb8c2f5da` / `fcdca94a78b3cb8e`；gui `5648a574b90dffb0` / `2f5f8c72b61561f8`。正文 LF，维护稿与生成页正文一致。
- 保留的纠错：`0x40`/`0x44` 按有符号单字节解释；FAT 的 `fls` 号码是虚拟地址，清链后要看文件尾；`extundelete` 使用 `--output-dir`；exFAT 扇区移位在 `0x6C`、簇移位在 `0x6D`；ext 大小高 32 位在 inode `0x6C`。
- 检验：`tests/test_filesystem_forensics.py` 3 项通过。分类与正文同步测试通过。`npm run check` 0 错误。构建 355 页，Pagefind 346 页、16248 词。`audit_site.py` 8201 条本地链接、0 错误。全套 Python 213 项，失败 6、错误 1。改前基线是失败 3、错误 1（工具目录、MySQL 旧哈希、RegRipper 的 Docker01 哈希、上级 Docker 指南不在仓库）。多出的失败来自同日另一批正在改的现有页，本批没有改那些正文：Android 存储节哈希、U 盘维护稿与审查记录不一致、ShellBags 旧前缀哈希。`forensic-usb-evidence` 的维护稿和生成页当时也不一致，本批没有代为同步。
- 页面：`http://localhost:4329/module/forensics/` 计算机取证下「文件系统取证」显示 7 篇，子类含 NTFS、FAT、exFAT、ext。`/knowledge/forensic-fs-ntfs/#04-runlist-的手算和拼接` 能打开，目录 7 节都在。搜索 `1264` 命中 NTFS 这篇。没有用真实镜像复跑。

## 2026-10-15 · 两份手册的通用取证增量写入现有页

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 把已核对过的通用取证增量写入现有 Forensics 页面，不新开页面，不写题号和固定答案。
- 修改前核对：维护稿与生成页正文原先一致。审查记录原件在 `.work/forensic-increment-20261015/server-forensics-review-20261006.prev.json`。本批没有改服务器取证页的标题，所以节数仍是 556。
- 写入位置：口径与摘要在 `forensic-method-pitfalls` §06；手机系统痕迹、分身、VMOS、便签和通讯录列在 `forensic-android-storage`；文件尾与 WinZip 超长哈希在 `fic-case-09`；微信派生、默往、高德、米家在 `forensic-mobile-apps`；备份模式号和微信碎片帧在 `forensic-ios-backup`；`1074` 与登录成败计数在 `forensic-windows-logs`；网关和 `##` 共享键名在 `forensic-registry`；EFS 不改密码、容器密钥文件、词库和换页文件在 `forensic-protected-data`；回收站会话在 `forensic-remote-connections`；启动 Activity、壳和模拟器备份在 `fic-case-06`；`WANACRY!` 与 `RSA2` 字段在 `fic-case-07`；损坏引导扇区在 `forensic-usb-evidence`；流量阶段和两种脚本参数在 `forensic-network-traffic`；登录时比较 shadow 的脚本在 `forensic-server-services` §06.2；SQL Server 环境变量在 `docker-evidence-03` §01.4；空盐三层 MD5 在 `forensic-server-panel` 导出库之后；ThinkPHP 路由拼接在 `fic-case-04` §01.3；统计上界和口径在 `fic-case-05` §05。
- 维护稿前 16 位：method `06f2a4173ed24ec4`，android `bc1abc62694d1315`，files `9bf5179394a60ee1`，mobile `4ef9f7570b14c0e6`，ios `d24514de47e6bb55`，win-logs `e43f5bf38c241e7e`，registry `d37ccb79abfbdb08`，protected `da592cd7ac352d88`，remote `eae4afd57424035a`，apk `4da74e8189460031`，sample `e0f072f7a581cd6c`，usb `4a0bd852ffbaa9eb`，traffic `ebfb43c73d8c5225`，services `6e96baeaca27e40e`，docker03 `1e4c4c45a011b946`，panel `d713d37a4285f9da`，webapp `b390151dab56756d`，db `14b87222e8a645c1`。android 与 docker03 在拆段后已重新同步，以磁盘为准。
- 检验：`test_server_practical_review` 10 项通过。`test_android_content` 10 项通过。`test_shellbags_content` 6 项通过。`test_regripper_content` 仍有改前就有的 Docker01 哈希不符，1 项失败。`test_mysql_commands_content` 仍有改前就有的恢复页前缀哈希不符，1 项失败。`npm run check` 0 错误 0 警告。`npm run build` 348 页，Pagefind 339 页、16094 词。`audit_site.py` 8038 条本地链接、0 错误。浏览器打开了口径页第 06 节、应用通信页的微信派生，搜索 `KeyInfo.bin` 命中应用通信页。没有用真实检材复跑。全套 210 项没有在这一批重跑完。


## 2026-10-15 · Web 三批扩写收尾补强与哈希对齐

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 审查三批 Web 知识页扩写结果后，补齐被省略的语法/正反例代码块、Werkzeug PIN 六要素路径表、SQLMap 参数表、Google Hack 检索语法表与工具页 `src/content/tools/web-burp.md` 快捷键速查，并同步 `docs/server-forensics-review-20261006.json` 遗留哈希。
- 修改前核对与备份：基线保存在 `.work/web-polish-20261015/baseline/`（清单见 `baseline-hashes.json`）。清理了 `.work/web-manual-20261015/` 下残留的两个临时测试子仓库 `git-index-lab` 与 `git-index-src`。
- 本批写入：
  - `src/content/knowledge/web-info.md`（`4c5cbbef508876b424845172fec12e757d16978cfb0cd08fa30ce4f494ced811`）：新增 `06.1 公开搜索引擎语法（被动收集）`。
  - `src/content/knowledge/web-data-query.md`（`66ba0e51d0af0266fdc45cd7cc04210a24dd4f2230cf6b1ceb8ba0d63d6541aa`）：补齐 PDO 占位符绑定、`LIKE` 通配符转义与 `ORDER BY` 白名单映射代码块；`information_schema` 三表与 MySQL 8.0.19+ `TABLE`/`VALUES ROW` 查询代码块；新增 `07.4 SQLMap 本地复核常用参数` 表与只读命令块。
  - `src/content/knowledge/web-browser-output.md`（`8ef8a3ad8b48b4c8913e990a87e9bf5bbd755cba84c1fc7636ef9c895e4777d6`）：补齐递归 `merge` 原型链污染修复对比代码块与 `postMessage`/`textContent`/URL 协议白名单对比代码块。
  - `src/content/knowledge/web-file-boundary.md`（`c385829ec7cc90d3e2a1c61bc22fcdcfb9827b3449cca5a109e7b35cfab0452f`）：补齐 `php://filter`/`phar://`/`zip://` 流包装器路径形态对照块与 Nginx + PHP-FPM（`cgi.fix_pathinfo=0`、`security.limit_extensions=.php`）加固配置块。
  - `src/content/knowledge/web-runtime-boundary.md`（`6eaeb760ccf30e86eefff2bcfa6724cc5fc38012c4e2d2f9d34f059902fc6c39`）：补齐 PHP `public`/`protected`(`\00*\00`)/`private`(`\00类名\00`) 序列化属性字节长度对照代码块。
  - `src/content/knowledge/web-template-injection.md`（`fa42eeea3b7c26fa97a38ec88a266475fa59754d9c2aca282ab5209efc57a0c0`）：补齐 `render_template_string` 风险写法与变量绑定对比代码块，以及 `|attr()` 属性访问说明。
  - `src/content/knowledge/web-logic.md`（`8dc0138b4418dd6f1e0f01cd141092b63b7a273d54d1d022443dc42132147ca0`）：补齐 `SELECT ... FOR UPDATE` 事务行锁与条件更新 SQL 对比代码块。
  - `src/content/knowledge/web-source-route.md`（`a2258f8b8fc737077bca3f7768d2b5b994b42bb45d34d26c2e304b609532e8e6`）：补齐 Linux（`sudo -l`、`find` SUID、`cron`、`getcap`）、Windows（`whoami /all`、`wmic service`、`systeminfo`）与域环境（`nltest /dclist:`、`setspn -Q */*`）只读清点命令块。
  - `src/content/knowledge/web-language-reading.md`（`093ba9c303ed5bccf76fc0db1432a8003c44975a644b7cde85ef1b7b59a0f5cb`）：补齐 `parse_str` 双参数与 `preg_match(...) === false` 回溯超限判读代码块，以及 Werkzeug Debug PIN 六要素（`probably_public_bits` 与 `private_bits`）Linux 路径对照表。
  - `src/content/knowledge/web-parser-gap.md`（`82db920bfbc839ac7bc215c230115b6858511a1c90a3b2a7e2d30068e5f526df`）：补齐 `Content-Length` 与 `Transfer-Encoding` 同包冲突的实验室报文核对示例。
  - `src/content/tools/web-burp.md`（`56e22c6194b21cc97ca1afa7345f88ff25842cbb9d3ceb8fae88c4cb3213a65c`）：新增 `04 常用模块与快捷键速查` 并关联知识页 `/knowledge/web-burp/`。
  - `docs/server-forensics-review-20261006.json`（`588d11605c0f0c23f05d45bac8234c610eed0c29c335769a506f6645e96e9bc0`）：同步 `unaffected_hashes` 与 `approved_replacement_hashes_20261014` 中受 Web 模块分类统一及本次补强影响的哈希。
- 检验：专项测试 `test_knowledge_taxonomy.py`、`test_server_practical_review.py`、`test_website_six_stacks.py` 共 29 项全部通过（`OK`）。全套 Python 210 项恢复为基线的失败 3、错误 1（工具目录缺失、MySQL 旧前缀哈希、RegRipper 引用的 Docker01 旧哈希、上级 Docker 指南文件不在仓库）。`npm run check` 0 错误 0 警告。`npm run build` 348 页，Pagefind 339 页、16017 词。`python scripts/audit_site.py` 348 页、8037 条本地链接、0 错误。
- 页面与搜索：已在本地构建产物服务上实际查看 `/knowledge/web-data-query/#074-sqlmap-本地复核常用参数`、`/tool/web-burp/` 与 `/search/?q=probably_public_bits`，标题、目录、新增表格与代码块正常渲染。

## 2026-10-15 · Web 剩余六篇核查扩写

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 扩写越权、逻辑、代码审计、语言特性、实验环境和解析差异。本机没有 HelloCTF 目录。票据伪造、隧道搭建、调试器 PIN 计算、请求走私报文和 WAF 绕过样本没有写入。
- 修改前核对：六篇 topic 未改。`web-request-auth.md` 磁盘 `481acf1f…`、`web-source-route.md` 磁盘 `ec5234a4…` 已经和审查记录不一致。备份在 `.work/web-rest-manual-20261015/baseline/`。
- 本批写入：`web-request-auth.md`（`9e39e79f902056765f4a4b143bb530110b5023602d2836757d49068353131fb4`）、`web-logic.md`（`3f96fd5f54cf1f70782a2439cedfde5d409e4672883cc3681b9ac62d4f6a5b4c`）、`web-source-route.md`（`ab7a6300c02bd79a81ebdeeda31f2d091c65fd3f61ea068c8749ea5b1bb6880f`）、`web-language-reading.md`（`b951bd75c5e97ab681e307e3386cb00a088fca17e318859267cde7a8278d5350`）、`web-local-lab.md`（`21c4d26727bae0bae0e18d589fc35d12b50d122b9ab4dac819dd4879b2d3e909`）、`web-parser-gap.md`（`03d3d0f94814d3e4613386153e8b4ea0675facc60b4e91b209cd55469114af46`）。审查 JSON 同步了前两篇登记过的哈希，现为 `35ffbeaa52be17f7e44795d7322782e45dedda1cb8c318e69247c0f305bed3fb`。正文 LF。
- 保留：原有基线请求、状态表、CSRF 的 SameSite、对象编号、审计顺序、路由表、PHP/Java/Python 入口、容器回环映射、缓存键和“不要构造错位请求”的限制。
- 纠错：RMI 远程加载默认关闭写的是 JDK 8u121，LDAP 是 8u191；材料里的 8u113 需要用 `java -version` 核对，不能当成同一次更新。PHP 8 仍把数值形式的 `0e` 字符串按 0 比较。
- 检验：Python 3.12 全套 210 项，失败 5、错误 1。改前就有的是：工具目录缺失、MySQL 旧正文哈希、RegRipper 引用的 Docker01 旧哈希、上级 Docker 指南不在仓库。实用审查现在停在改前已不一致的 `src/content/tools/web-burp.md`；本批改过的两篇已与记录一致。六分类测试还指出 `src/pages/module/[module].astro` 和 2026-10-14 登记的 after 哈希不同，本批没有改这个文件。Astro 检查 0 错误 0 警告。构建 348 页，Pagefind 339 页、15953 词。链接审计 8035 条、0 错误。没有真实站点复跑。
- 页面：`http://localhost:4329/knowledge/web-request-auth/#06-同源策略拦的是读响应` 已打开，三种越权、同源和 CORS 可见。构建页里有 `CL.TE`、`SELECT ... FOR UPDATE` 和登录十二项。窄屏未单独测。
- 状态：六篇已可查阅。topic 未改，没有新页面 ID。

## 2026-10-15 · Web 六篇漏洞机制扩写

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 在现有 Web 分类下，按源码审计、解析机制、底层特性和版本边界扩写 SQL、XSS、上传与包含、SSRF/XXE、命令与反序列化、模板注入。本机没有找到 HelloCTF 目录，机制以这六篇现有正文和本地笔记里的函数名、配置名、版本边界为准。可直接利用的语句、绕过样本和链式载荷没有写入页面。
- 修改前核对：六篇 topic 都是 `Web漏洞`。`web-server-fetch.md`、`web-template-injection.md` 在审查记录的 `unaffected_hashes` 里，改前磁盘哈希已经和记录不一致。备份在 `.work/web-vuln-manual-20261015/baseline/`。
- 本批写入：`web-data-query.md`（`a6b8b5cbd94cfaf428ebe2e34b26a9936994e7bab811a413379db22c1c9d3e89`）、`web-browser-output.md`（`59084d3bb93cbb49a99432225980199d727a06b360eb87ad7243bebd130e75aa`）、`web-file-boundary.md`（`d3eeb434a54f7533308a0451493b98c6cbfaa98fa3cd4f83bfec3c7b081ccfd4`）、`web-server-fetch.md`（`2e0a8bfdf90643542be5e22f4c01a061f87f48de9cd81059e64530786a6b4576`）、`web-runtime-boundary.md`（`f24aca6194cb4157cd30c3664fced1e96d40a4f50ca6cf8164f52e07350fbae6`）、`web-template-injection.md`（`34df1e95aaa15a088fa9614fdb3b21cf281129e2981e045e73631f9de5fcee05`）。审查 JSON 只同步了后两篇登记过的哈希，现为 `89a6f3f6441381ab1c52595270d76e63233e46c9e1fa63b3242a73b809ab6ed1`。正文 LF。
- 保留：原有的绑定与拼接、现象分类、二次使用、提交位置、数据库家族、XSS 三类数据流、上传三份名字、包含与下载、SSRF 出网点、命令与反序列化的搜索表、模板的固定模板和拼接模板之分。XXE 的实体语法和关闭配置放在 SSRF 页，上传页只保留“有没有交给解析器”。
- 纠错：MySQL 8.0 没有删掉 `extractvalue` / `updatexml`；`.user.ini` 的 `auto_prepend_file` 不把图片变成 PHP；Apache 是否执行 PHP 看 `AddHandler` / `FilesMatch` 的锚点，不按“一律从右向左”记；`JSON.parse` 本身不会污染原型，污染发生在随后的递归赋值。
- 检验：分类测试通过。实用审查 11 项里 1 项失败，仍是改前的 `web-request-auth.md` 哈希。本批改过且登记过的两篇已与记录一致。Astro 检查 0 错误 0 警告。构建 348 页，Pagefind 339 页、15875 词。链接审计 8017 条、0 错误。没有用真实站点复跑。
- 页面：`http://localhost:4329/knowledge/web-data-query/` 与 `/knowledge/web-template-injection/#041-语法对照` 已打开，标题、目录和系统表、引擎名可见。外壳连接符 `||` 在代码块里。窄屏未单独测。
- 状态：六篇已可查阅。topic 未改，没有新页面 ID。

## 2026-10-15 · Web 四篇技术手册补写

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 对照本地笔记中的协议、抓包、指纹、DNS 与 Git/SVN 泄露材料，把现有 4 篇补成可操作的技术参考。不写攻击载荷和社工话术。Web 三个 topic 保持不变。
- 修改前核对：四篇正文都在 `src/content/knowledge/`，topic 已是 `协议与抓包` 或 `源码与环境`。`git-history.md` 在审查记录 `unaffected_hashes` 中。改前磁盘哈希 `5c32be4d…` 已经和记录里的 `3402b044…` 不一致。另外 7 个路径也已不一致，本批没有改它们：`web-request-auth.md`、`web-server-fetch.md`、`web-source-route.md`、`web-template-injection.md`、`src/content/tools/web-burp.md`、`src/pages/tools/index.astro`、`tests/test_knowledge_taxonomy.py`。
- 备份：`.work/web-manual-20261015/baseline/`，含四篇正文和当时的审查 JSON。四篇当时都是 LF。
- 本批写入：`web-http-message.md`（`a306c73413fd69b29af8c1ff3582934e0d77a4b702a773e53b76abd3b6658869`）、`web-burp.md`（`19143d0d77b3ceef9e403f21065fc2c9fb198565edef7e4750b6b29ea925d1a7`）、`web-info.md`（`713278e30b8d079658f4976d7731799abe9f75263c465d63f709b02cc97d6067`）、`git-history.md`（`00d36069691062d4bd9bdd8815eb301515f7241e8347ca3071f9dcb1ad312615`）。审查 JSON 只把 `git-history.md` 的哈希改成现稿，现为 `6baf9ad3ae17efce7cf6f0ed2efd1523151562a05478de636a2d68d02103008f`。正文均为 LF。
- 保留：HTTP 四段、原 curl、状态码表、头字段表、Cookie 属性、Burp 的历史/Repeater/Comparer/Decoder 顺序、Intruder 不清空位置的警告、敏感文件名单、Git 的 status/log/show 与“旧提交对当前响应”的写法。对象恢复仍指向 `git-docker-08`。
- 纠错：303/307/308 不按 302 记；POST 没有协议级无限长度；单机一次 ping 不能证明没有 CDN；泛解析要先分 A 和 CNAME；Grep-Extract 只填结果表，下一请求要用 Recursive grep 或宏；Firefox 使用自己的证书库；空的 `.git` 目录不能直接 `ls-files`。
- 检验：`test_knowledge_taxonomy.py` 通过。`test_server_practical_review.py` 11 项里 1 项失败，第一处就是改前已存在的 `web-request-auth.md` 哈希；本批的 `git-history.md` 已与记录一致，没有新增失配。Astro 检查 0 错误 0 警告。构建 348 页，Pagefind 339 页、15756 词。`audit_site.py`：348 页、8015 条本地链接、0 错误。没有用真实站点复跑命令。
- 页面：`http://localhost:4329/`。四篇标题、目录和 topic 正确；HTTP 与源站锚点可打开；页面无横向溢出。搜索索引能把 `Battering` 指到 Burp、把 `wc.db` 指到 Git泄露。Web 模块页仍是协议与抓包、Web漏洞、源码与环境三组。`127.0.0.1:4329` 连接被拒绝，同一服务用 `localhost` 可打开。窄屏未单独测。
- 状态：四篇已可查阅。没有新增知识点 ID。

## 2026-10-15 · 流量过滤手册新页

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 把 Wireshark 过滤按协议收成 Forensics 流量取证下的一个知识点。
- 修改前核对：现有 `forensic-network-traffic` 第 22 节只有短表；`forensic-guide-network`、`forensic-wireless`、`usb-keyboard` 已有各自完整正文。本批不改这三页，避免动审查哈希。字段名对照过 Wireshark 4.6 的 HTTP、DNS、TLS、DHCP、FTP、MySQL、USB 字段表；没有对真实 pcap 复跑。
- 本批写入：`src/content/knowledge/forensic-traffic-filters.md`（`db7394e52aa7e9574976184d58f0c35bb0ce06bcf028b130dd13ed0a7dd363a8`）与 `src/content-curation/forensic-traffic-filters.md`（`4a50e815438f0f02f3115fec818e8c39cc684d6a35168d74370e112ff1d143fe`），正文一致。分类是网络取证 / 流量与协议。`tests/test_traffic_filters.py` 锁住分类和关键过滤式。`tests/test_import_manuals.py` 的取证篇数由 55 改为 56；`docs/server-forensics-review-20261006.json` 里该测试的旧哈希 `1423ed27…` 换成 `7e5cb5fb4359cd92922455d96591396bd205a8b84d444f9c9c20b6a7c2b756c4`。
- 保留与边界：采集范围、对象导出、TLS 密钥仍在流量证据链页；无线握手配对仍在无线页；键码对照仍在 USB 键盘页。新页只放过滤和读字段的下一步。
- 检验：Python 3.12 共 210 项，失败 3、错误 1，与改前相同：工具目录缺失、MySQL 旧正文哈希、RegRipper 引用的 Docker01 旧哈希、上级 Docker 指南文件不在本仓库。专项 3/3。UI 5/5。Astro 检查 0 错误 0 警告。构建 337 页，Pagefind 328 页。链接审计 7742 个本地链接、0 错误。缓存来源审计 errors 为空。
- 页面：`http://localhost:4329/knowledge/forensic-traffic-filters/`。标题、16 个目录锚点、23 张表无溢出。`#07-dns` 能打开。搜索 `ftp.passive.port` 第一条是本页。Forensics 模块页含本篇标题。
- 状态：本篇已可查阅。2026-10-15 同日把显示名改为「Wireshark 过滤」，页面 ID 仍是 `forensic-traffic-filters`。未做真实检材复跑。

## 2026-10-15 · Web 模块按三条题线补知识点

- 日期 / 执行者 / 用户任务：2026-10-15 / Cursor / 从 HelloCTF Web 目录提炼考点，写入本站 Web 模块，不写具体题目和可直接利用的载荷。
- 对照：原有 Web 页只有请求与权限、服务端请求、模板、路由、Git 泄露。HelloCTF 目录覆盖 HTTP、Burp、会话、注入、文件、XSS、反序列化、语言源码、本地环境和解析差异。
- 新增：`web-http-message`、`web-burp`、`web-data-query`、`web-file-boundary`、`web-browser-output`、`web-runtime-boundary`、`web-language-reading`、`web-local-lab`、`web-parser-gap`。分类只用既有的请求与身份、输入与执行、源码与部署。
- 补写：`web-request-auth` 增加跨站请求和对象编号；`web-server-fetch` 增加协议与重定向；`web-template-injection` 增加引擎对照；`web-source-route` 增加后续阅读表和源码包里的配置文件。
- 边界：内网横向、WAF 替换表和具体注入语句没有写成操作步骤。页面要求在本地题目或授权环境里对照代码、请求和响应。
- 依据：MDN 的 Cookie / SameSite / CSRF 说明，OWASP 的参数化查询和按上下文编码说明。没有对真实站点复现。


## 2026-10-11 · fic-case-03 两层阅读（Trae 校准批次）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 接管服务器取证审查维护；先全面评价（`.work/trae-server-eval-20261011/REVIEW.md`，21 篇问题清单、覆盖映射、B1–B18 分批计划与 D1–D4 决策点），评价与计划落盘后执行校准批次 B1 = `fic-case-03` 两层阅读。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-fic03-twolayer-20261011/baseline/`。维护稿 `cf878573e44e6fbfe94d9e8d9f12d4eefd20e32f03f9744787ff45cfd786ded2`，生成页 `6c6728d4…7fd5`，导入器 `f50477da…9b53`，审查 JSON `47412f29…815c`，clear_flow 测试 `1b841717…62e9`。本批没有新取网页全文。分类仍是服务器取证 / 主机与服务。
- 本批唯一写入文件与章节：两份 `fic-case-03` 正文；`scripts/import_manuals.py` 增加本篇无属性折叠与 6 个固定旧锚点；`tests/test_server_clear_flow.py` 增加本篇专项；`tests/test_import_manuals.py` 第 72 行重导入模拟补 `article_id="fic-case-03"`（生产路径 import_manuals.py:803 本就传 article_id，断言未削弱）；`docs/server-forensics-review-20261006.json` 更新本篇 18 节标题/行号、10 条本批改动、正文哈希及上述测试文件的 unaffected 哈希。其他 20 篇未改。
- 语义查重结论 / 保留知识点与考点：三环境区分、os-release/主机名/时区、UUID 对盘、安装-初始化-运行四层、离线包记录、数据库服务识别、家目录证据位置、历史命令追搭建、ngrok 启动方式、SSH 远程取证、隔离仿真与结果表均在。映射在 `.work/trae-fic03-twolayer-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；6 个二级标题改成动作句并各加固定空 span；02.1 字段判读表与 03.1 四层判断表改为按需展开（判断核心表留主线）；15 处四标签收尾改成各节自己的判据句。12 个代码块、全部表格与行内技术词逐字节核对未改（`check_diff.py`）。05.1 标题因有入站锚点保持原文。
- 基线与修改后命令、结果、退出码和旧失败差异：本机 Python 均无 python-docx，测试经 uv 临时环境执行（命令见 CURRENT-STATE 环境备注）。改前 196 项、3 项历史失败；改后 197 项（+1 fic03 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 8/8。UI 5/5，退出码 0。Astro 检查 0 错误 0 警告。构建 336 页。链接审计 7685 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `babdbcd67cb08577d5635d3404b48e7755607b402d91005ee663a8c8a2b8f74d`，生成页 `842afc332e75f1cae9fe8264769a51c45442fe2dd2e9fa15f9560deaeca24c6f`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/fic-case-03/` 页首主线可见；2 个折叠默认关闭、可开可关；旧锚点 `#03-服务清单与状态判定` 落到 03 新标题；构建 HTML 的「本页目录」6 链接齐全（浏览器代理 DOM 查询误报无目录，以构建产物为准）；本页折叠只包参考表、无折叠内锚点场景，`#021-实战识别发行版与版本` 为折叠外锚点；搜索 `ngrok` 命中本页、摘要来自 04.3 节。390px 窄屏未实测（浏览器工具超时），以 CSS 规则与同构页既有验收为据，标记待核。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-fic03-twolayer-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：校准批次 fic-case-03 完成。下一步按计划 B2 = `forensic-guide-server`（两层阅读 + 导航修复）。其余 17 篇未开始。D1–D4 决策点等用户确认。
- 状态：本篇已验收（窄屏项待复核）。20 篇整体还没完成。

## 2026-10-11 · forensic-guide-server 两层阅读与导航修复（Trae B2）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B2 = `forensic-guide-server` 两层阅读 + P1-14 导航修复（§05 收缩 + §07 补链 + §01 日志路由 + §02 非 systemd 分支）。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b2-guideserver-20261011/baseline/`。维护稿 `99eaf1c9…`，生成页 `1c378a95…`，导入器 `bf0c8e8c…`，clear_flow 测试 `6a1cab8a…`，审查 JSON `96a64a10…`。本批没有新取网页全文。§05 收缩前已逐点核实 `forensic-cloud-vm` §01/§02/§04 完整覆盖被收缩内容；§01 路由目标（fic-case-04 §04、server-services §06/07）与 §07 补链目标（forensic-database-recovery、forensic-cloud-vm）均实际存在。本篇 8 个二级标题无入站锚点，可安全动作化。
- 本批唯一写入文件与章节：两份 `forensic-guide-server` 正文；`scripts/import_manuals.py` 的 disclosure_ids 与 legacy_anchors 增加本篇 2 折叠与 8 个固定旧锚点；`tests/test_server_clear_flow.py` 增加本篇专项（现 9 个测试）；`docs/server-forensics-review-20261006.json` 更新本篇 8 节标题/行号、15 条本批改动、表格哈希（§07 表计划内变化）与正文哈希。其他 19 篇未改。
- 语义查重结论 / 保留知识点与考点：服务链路（入口→反代→Web→库）、活机最小现状清单、登录/请求/执行/数据四步、容器证据链转接、云识别与资源 ID 接回、事件顺序与缺口写法、七类架构识别、Web 请求追库实战均在。映射在 `.work/trae-b2-guideserver-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；8 个二级标题改成动作句并各加固定空 span；五层证据定位表与七类架构识别对照表改为按需展开；8 处四标签收尾改成各节自己的判据句；§01 补日志路由句；§02 补非 systemd 分支；§05 收缩为识别提示 + 资源 ID 字段串 + cloud-vm 转接；§07 表内补 3 条子页链接。代码块 1 个、行内资源字段串逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：改前 197 项、3 项历史失败；改后 198 项（+1 guide 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 9/9。UI 5/5。Astro 检查 0 错误。构建 336 页、Pagefind 327 页。链接审计 7690 个本地链接（+5，新增补链）、0 错误。缓存来源审计 errors 为空。维护稿现为 `f2944561df128fe9…`，生成页 `eaa652323f5c5681…`，导入器 `0c7a7daa…`，测试 `e8bbd855…`，审查 JSON `7cd97a3a…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/forensic-guide-server/` 页首主线可见；2 个折叠默认关闭、可展开；旧锚点 `#05-云与虚拟化再补控制面`、`#07-不同服务架构如何归入同一条主线` 均落位；构建 HTML 的「本页目录」8 链接齐全（浏览器代理 DOM 查询误报无目录，以构建产物为准，同 B1 现象）；搜索「服务链路」第一条命中本页。390px 窄屏未实测，沿用 CSS 规则与同构页验收为据，标记待复核。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b2-guideserver-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B2 forensic-guide-server 完成。下一批按计划 B3 = `fic-case-04`。其余 16 篇未开始。D1–D4 决策点等用户确认。
- 状态：本篇已验收（窄屏项待复核）。19 篇整体还没完成。

## 2026-10-11 · fic-case-04 两层阅读（Trae B3）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B3 = `fic-case-04`（Web 应用取证）两层阅读 + P1-6/7/8 修复。用户指令"继续任务"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b3-fic04-20261011/baseline/`。维护稿 `f9c38024…`（82025B），生成页 `2fef1907…`（82853B），导入器 `0c7a7daa…`，clear_flow 测试 `e8bbd855…`，审查 JSON `7cd97a3a…`。本批没有新取网页全文。入站锚点核实：4 个（`#04-访问日志与活动时间线`←server-services/website-reconstruction、`#012-nginx-配置体系与包含关系`、`#015-实战从-apache-配置定位站点`、`#043-实战从请求筛选候选后台入口`），据此二级标题可改名但三级节不重编号。
- 本批唯一写入文件与章节：两份 `fic-case-04` 正文；`scripts/import_manuals.py` 的 disclosure_ids 与 legacy_anchors 增加本篇 4 折叠与 6 个固定旧锚点；`tests/test_server_clear_flow.py` 增加本篇专项（现 10 个测试）；`tests/test_server_practical_review.py` 第 58 行节数断言 533→534（本篇新增 04.4，断言未削弱、仅反映现状）；`docs/server-forensics-review-20261006.json` 更新本篇 35 节（新增 04.4 记 added）标题/行号、19 条本批改动、代码/表格/正文哈希，并同步顶层 `unaffected_hashes` 中 `tests/test_server_practical_review.py` 的新哈希。其他 20 篇未改。
- 语义查重结论 / 保留知识点与考点：虚拟主机/程序目录/数据库/日志四者对站点、部署类型起点（单机/站库分离/IIS/Tomcat）、Nginx 包含关系与 -T、SM3 摘要固定、CMS 配置字段线索、maccms 版本与前台/后台、改名-删除-复制与 Git 提交树、访问日志格式与 combined、筛选可疑请求、静态枚举暴露文件、PHP 表单追落盘、PHPMailer 调用链、隔离重构入口、最小证据清单、Java 双盘角色与 Nginx proxy_pass、JAR 包内配置定位、生效配置与启动条件、Consul/RabbitMQ/Redis/OSS、定时任务与验证码反编译追码均在。映射在 `.work/trae-b3-fic04-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；6 个二级标题改成动作句并各加固定空 span；01.1/01.2/02.1/02.3 四张参考表改为按需展开（判断核心表留主线）；29 处四标签收尾改成各节自己的判据句；P1-6 在 01.4 开头补过渡句接回 01.3→01.5 主线（三级节有入站锚点，不移动不重编号）；P2 补 OpenSSL≥1.1.1 / hashlib 的 SM3 版本前提；P1-7 04.1 孤句"Apache日志定位。"改为指向 04.4 的路由句；P1-8 新增 `### 04.4 error_log 与轮转的读取位置`（含 2 个新代码块，追加为 04.4 避免重编号）；纠错 01.3/01.5/02.2 三处 `sed -n '1,220p'`（行数 220 无依据）改为 `cat`。其余 24 个代码块、8 张表、258 个行内 token 逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：本机 Python 均无 python-docx，测试经 uv 临时环境执行（命令见 CURRENT-STATE 环境备注）。改前 198 项、3 项历史失败；改后 199 项（+1 fic04 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 10/10。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15543 词。链接审计 7690 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `aa49d2941feac444…`，生成页 `8e994aa20b3d3059…`（LF），导入器 `e4a82c83…`，测试 `b02d8f75…`，审查 JSON `bcd6a490…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/fic-case-04/` 页首材料说明与箭头主线可见；4 个折叠默认关闭、可开可关；`### 04.4` 存在；构建 HTML 的「本页目录」6 链接齐全；旧锚点 `#04-访问日志与活动时间线` 因自动化环境 fragment 卡死无法直接观测滚动，但 DOM 旁证完整（空 span 在 04 新标题上方约 27px，标题 scroll-margin-top 88px > sticky 头 58px），标记待复核；无横向滚动。`/search/` 搜 `logrotate.conf` 第一条命中本页。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b3-fic04-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B3 fic-case-04 完成。下一批按计划 B4 = `fic-case-05`（数据库取证，P0-1 SQLCipher PRAGMA 顺序修复 + P1-9/10/11）。其余 15 篇未开始。D1–D4 决策点等用户确认。
- 状态：本篇已验收（旧锚点滚动项待复核）。18 篇整体还没完成。

## 2026-10-11 · fic-case-05 两层阅读（Trae B4）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B4 = `fic-case-05`（数据库取证）两层阅读 + P0-1 修复 + P1-9/10/11。用户指令"继续"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b4-fic05-20261011/baseline/`。维护稿 `743a8fff…`，生成页 `a110b562…`，导入器 `e4a82c83…`，clear_flow 测试 `b02d8f75…`，审查 JSON `bcd6a490…`。本批没有新取网页全文，P0-1 的顺序依据取自 SQLCipher 官方 API 文档（key 与选项必须在首次操作前设置）。入站锚点核实：`fic-case-05/#*` 无入站引用，可自由改标题与移节。
- 本批唯一写入文件与章节：两份 `fic-case-05` 正文；`scripts/import_manuals.py` 的 disclosure_ids 与 legacy_anchors 增加本篇 4 折叠与 6 个固定旧锚点；`tests/test_server_clear_flow.py` 增加本篇专项（现 11 个测试）；`docs/server-forensics-review-20261006.json` 更新本篇 23 节标题/行号（新增 §01.3 记 moved）、22 条本批改动、代码/表格/正文哈希。其他 20 篇未改。节数净 0（+§01.3 −§06.1）。
- 语义查重结论 / 保留知识点与考点：实例类型与定位起点（MySQL/TiDB/PostgreSQL/SQLite/SQLCipher/Redis）、SQLite 主库与 WAL/SHM 固定、SQLCipher 头部与密钥派生、便签与本地 AI 应用、未知业务库候选人员、订单状态与付款事件、借贷业务统计、原始页读取与字节序、聚合口径与分母、主备库图片记录比对均在。映射在 `.work/trae-b4-fic05-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；6 个二级标题改成动作句并各加固定空 span；01.1/03.1/03.4/04.1 四张速查表改为按需展开；17 处四标签收尾改成判据句；P0-1 §02.2 代码块顺序改为 `cipher_compatibility`→`key`→读表（正文不动）；P1-9 §06.1 移为 §01.3（§06.2 重编号为 §06.1）；P1-10 §01.1 补 PostgreSQL 范围并指向恢复页；P1-11 §04.1 加恢复路由句；P2 补 `sqlite3 -readonly` 的 WAL 局限、收窄 §03.4 rg 模式、类型表补 Redis 行。其余代码块、表格逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：本机 Python 均无 python-docx，测试经 uv 临时环境执行。改前 199 项、3 项历史失败；改后 200 项（+1 fic05 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 11/11。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15543 词。链接审计 7693 个本地链接（+3，新增恢复页/Redis 链接）、0 错误。缓存来源审计 errors 为空。维护稿现为 `cac3104c7cbfaca0…`，生成页 `fac2ac8839cb117f…`，导入器 `63de6702…`，测试 `f16e9f47…`，审查 JSON `15cfad0a…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/fic-case-05/` 页首材料说明与箭头主线可见；4 个折叠默认关闭；01 节下 01.1/01.2/01.3 顺序正确；**§02.2 代码块已确认 `cipher_compatibility` 在 `PRAGMA key` 之前**；「本页目录」6 链接齐全；6 个旧锚点 span 存在；无横向滚动。搜索能命中本页（`安装、服务与实例身份` 第 3 条、`lab_loan` 第 4 条；首条为共享该词的其他页）。折叠开合点击因本次受控标签渲染节流（页面不可滚动、scrollHeight==clientHeight）未实测，以 HTML open=false、站点无 details 显隐覆盖、同族页既有验收为据，标记待复核；搜索首条排序同样受相关性影响，仅记"可命中本页"。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b4-fic05-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B4 fic-case-05 完成。下一批按计划 B5 = `forensic-database-recovery`（含 P0-3/4 账户与变量修复；§17-21 收缩待 D2）。其余 14 篇未开始。D1–D4 决策点等用户确认。
- 状态：本篇已验收（折叠交互与搜索首条待复核）。17 篇整体还没完成。

## 2026-10-11 · forensic-database-recovery 两层阅读（Trae B5）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B5 = `forensic-database-recovery`（MySQL 数据目录与表恢复）两层阅读 + P0-3（账户）+ P0-4（输出目录）+ P2 两条。用户指令"继续 B5"。§17-21 统计 SQL 收缩待 D2，本批未做。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b5-dbrecovery-20261011/baseline/`。维护稿 `588d349d…`，生成页 `d4c3e702…`，导入器 `63de6702…`，clear_flow 测试 `f16e9f47…`，审查 JSON `15cfad0a…`。本批没有新取网页全文。入站锚点核实：`#19-时间ip字符串二进制与json字段` 被 forensic-website-reconstruction 引用，§19 改名时保留该 id。
- 本批唯一写入文件与章节：两份 `forensic-database-recovery` 正文；`scripts/import_manuals.py` 增本篇 2 折叠与 25 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 12 个测试）；`docs/server-forensics-review-20261006.json` 更新本篇 70 节标题/行号、34 条本批改动、代码/表格/正文哈希，并同步顶层 `unaffected_hashes` 中 `docs/forensics-mysql-commands-coverage.json` 的哈希；`docs/forensics-mysql-commands-coverage.json` 同步 §13/20/23/24 的 target_heading。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：材料识别（逻辑备份/数据目录/单表/MyISAM/XtraBackup/binlog）、`.frm`+`.ibd` 单表恢复、XtraBackup 增量链、软删/硬删/日志覆盖、ROW binlog 行镜像、SSH 隧道与连接目标、逻辑导入前检查、离线授权副本、命令与对象约定、数据目录与版本、mysql 客户端参数、实例/账户/变量/只读会话、库表与未知对象定位、SELECT 与聚合口径、时间/IP/JSON 字段、MySQL 8 窗口与递归、mysqldump/OUTFILE、物理目录与 force_recovery、binlog 状态与回放、实战组合、排错清单均在。映射在 `.work/trae-b5-dbrecovery-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；20 个二级标题动作化、另 5 个原名即动作句仅加 span（共 25 个固定旧锚点）；§01 材料识别表与 §10 导入前检查表改为按需展开；53 处四标签收尾改为各节判据句（按统一模板保留四标签全部内容）；P0-3 §22.5 补 `lab_admin`/`lab_replay` 建户与用途；P0-4 §06.2/§10 输出目录统一到 §12.2 的 `$CASE/output`；P2 §12.1 速查表加「动作」列、§24.2 命名管道平台说明。其余 46 个代码块、13 张表逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 200 项、3 项历史失败；改后 201 项（+1 dbrecovery 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 12/12。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15542 词。链接审计 7693 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `7f6c848d…`，生成页 `dcf2f91a…`（LF），导入器 `3e652bd3…`，测试 `4f6c6ddc…`，审查 JSON `967a1526…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/forensic-database-recovery/` 页首材料说明与箭头主线可见；2 个折叠默认关闭；25 个二级标题与「本页目录」25 链接齐全；**旧锚点 `#19-时间ip字符串二进制与json字段` 空 span 存在**；§12.1 表已含「动作」列；§22.5 代码块含 `lab_admin`/`lab_replay` 建户；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b5-dbrecovery-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。`docs/forensics-mysql-commands-coverage.json` 的 4 处 target_heading 改动可手工还原（13/20/23/24）。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B5 forensic-database-recovery 完成（§17-21 收缩待 D2）。下一批按计划 B6 = `docker-evidence-01`。其余 13 篇未开始。D1–D4 决策点等用户确认。
- 状态：本篇已验收。16 篇整体还没完成。

## 2026-10-11 · D2 收缩：recovery §17-§19.2 统计/字段 SQL 归并（Trae B5 追加）

- 依据 / 决策：用户确认执行 D2（方案甲）。比对确认与 fic-case-05 §03/§05 重复的 6 类：SELECT 抽样、JOIN 倍增、NOT IN/NULL、SUM(DISTINCT)、FROM_UNIXTIME、INET_NTOA；fic-case-05 未覆盖而须保留的是 JSON（§19.3）、MySQL 8 窗口/递归（§20）、备份导入导出核验（§21）。
- 本批唯一写入：`src/content-curation/forensic-database-recovery.md` 与对应生成页的 §17、§18、§19.1、§19.2；`docs/server-forensics-review-20261006.json`（新增 6 条 D2 改动、6 节标记 decision=shrink、更新正文/代码哈希）。未改导入器、二级标题或节数（仍 70）。
- 实际改动：删除重复统计/字段 SQL 模板（8 个代码块），改为"恢复实例上的只读核验要点 + 回链 fic-case-05"（§03 字段语义、§05 统计口径）。§19.3 JSON、§20 窗口/递归、§21 备份导入导出全文保留。
- 知识点保全：删除会带走 `= NULL`、`IS NULL`、`BETWEEN`、半开区间、`%/_` 五个判据 token（fic-case-05 未完整覆盖），已在 §17.1 以一句话要点保留，审查记录复核 dropped=0。curation 1884→1688 行（-196）。
- 检验：Python 201 项、失败仍是同 3 项历史失败；UI 5/5；Astro 检查 0 错误 0 警告；构建 336 页、Pagefind 327 页 15518 词；链接审计 0 错误；缓存来源审计 errors 为空；回滚试验五份基线 OK。维护稿现为 `fec77163…`，生成页 `f75c20a2…`（LF），审查 JSON `1145271a…`。
- 页面：预览确认 §17/§18/§19.1/19.2 已无 SQL 模板、各含 1 个 fic-case-05 回链；§19.3/§20/§21 保留；回链可跳转；目录 25 链接；无横向滚动。
- 状态：D2 完成并验收。B5 全流程（两层化 + P0-3/4 + P2 + D2）结束。下一步 B6 = `docker-evidence-01`。

## 2026-10-11 · docker-evidence-01 两层阅读（Trae B6，含 D1/D3）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B6 = `docker-evidence-01`（Docker 取证 01｜环境、服务与配置）两层阅读 + P1-2/P1-3 + 决策 D1/D3。用户确认 D1 = §07 Git 内容收缩为原则 + 链接 git-docker-03；D3 = LXC 租约主线留本页 §09.2。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b6-docker01-20261011/baseline/`。维护稿 `0019e0f4…`，生成页 `09738d08…`，导入器 `3e652bd3…`，clear_flow 测试 `4f6c6ddc…`，审查 JSON `1145271a…`。本批没有新取网页全文。入站锚点核实：`docker-evidence-01/#*` 无入站引用。
- 本批唯一写入文件与章节：两份 `docker-evidence-01` 正文；`scripts/import_manuals.py` 增本篇 3 折叠与 10 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 13 个）；`tests/test_import_manuals.py` 第 269 行内容契约的 heading 期望随 §09 改名同步（断言未削弱）；`docs/server-forensics-review-20261006.json` 更新本篇 37 节、19 条本批改动、代码/表格/正文哈希，并同步顶层 `unaffected_hashes` 中 `tests/test_import_manuals.py` 的哈希。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：三环境区分与保全、Docker 组件与调用链、RPM/YUM/DNF + dpkg/apt 安装定位、systemd 单元与 ExecStart/Environment、daemon.json 字段与冲突、参考规范、按问题选第一条查询、Dockerfile/Image/Container/Volume/Network/Compose、CLI 与 Compose 版本、Docker 与 LXC 元数据识别、镜像创建字段、离线复核安装与服务均在。映射在 `.work/trae-b6-docker01-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；10 个二级标题动作化并各加固定空 span；02.1/04.3/05.2 三张速查表改为按需展开；29 处四标签收尾改为判据句；P1-2 §03.1 补 dpkg/--admindir 与 dpkg/apt 日志；P1-3 §02.3 补 kubelet/containerd/crio 服务、数据根与 crictl 核对；D1 §07 的 Git 读取链删除并收缩为"两类对象命令分开跑"+ 回链 git-docker-03；D3 §09.2 标注为唯一完整主线。其余 46 个代码块、19 张表逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 201 项、3 项历史失败；改后 202 项（+1 docker01 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 13/13。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15521 词。链接审计 0 错误。缓存来源审计 errors 为空。维护稿现为 `11e01dfd…`，生成页 `e0116423…`（LF），导入器 `324c28be…`，测试 `11ae9458…`，审查 JSON `87e92d1e…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/docker-evidence-01/` 页首材料说明与箭头主线可见；3 个折叠默认关闭；10 个二级标题与「本页目录」10 链接齐全；§07 已无 `git log -p --all`/`reflog`/`fsck --full`、含 4 处 git-docker-03 回链；§02.3 含 crictl；§03.1 含 dpkg/--admindir；§09.2 含唯一主线句；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b6-docker01-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B6 docker-evidence-01 完成。下一批按计划 B7 = `docker-evidence-02`（含 P1-1 的 §10 LXC 片段按 D3 折叠回链本页、P2 表格转义）。其余 12 篇未开始。D1/D3 已定；D2 已执行；D4（Git/Docker 增补建议）仍待确认。
- 状态：本篇已验收。15 篇整体还没完成。

## 2026-10-11 · docker-evidence-02 两层阅读（Trae B7，含 D3/D1 续）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B7 = `docker-evidence-02`（Docker 取证 02｜现场流程与操作边界）两层阅读 + D1 续（§08.1/§09.1 Git 收缩）+ D3（§10 LXC 收缩回链）+ P2 两条。用户指令"继续 B7"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b7-docker02-20261011/baseline/`。维护稿 `ce334737…`，生成页 `6f8484f3…`，导入器 `324c28be…`，clear_flow 测试 `11ae9458…`，审查 JSON `87e92d1e…`。本批没有新取网页全文。入站锚点核实：`docker-evidence-02/#*` 无入站引用。
- 本批唯一写入文件与章节：两份 `docker-evidence-02` 正文；`scripts/import_manuals.py` 增本篇 3 折叠与 11 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 14 个）；`tests/test_import_manuals.py` 第 271 行内容契约随 §10 改名与 LXC 细节回链同步；`docs/server-forensics-review-20261006.json` 更新本篇 32 节、21 条本批改动、代码/表格/正文哈希，并同步 `unaffected_hashes` 中 `tests/test_import_manuals.py`。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：首轮定位与整体流程、快速定位表、现场检查清单、核心思想入口、清理与风险命令、完整流程阶段产物、Docker 易混命令、只读命令与记录字段、容器地址归属、把首轮输出变成可复核清单均在。映射在 `.work/trae-b7-docker02-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线（原页首两段移入 §01 内）；11 个二级标题动作化并各加固定空 span；§03 定位表、§06 清理表、§08.2 Docker 易混表三处折叠；26 处四标签收尾改为判据句；D1 §08.1/§09.1 Git 内容收缩为原则 + 5 处回链 git-docker-03（§09.3 删 3 行 Git、§09.4 去 Git 动词）；D3 §10 的 LXC 定义/租约/`lxc-attach` 详解收缩为清点命令 + 结论 + 回链 docker-evidence-01 §09.2/§09.4；P2 §03 表拆分为「问题\|查看位置」两列表 + 可复制命令块、§05.1 标题改为「把清单落到文件」。其余代码块、表格逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 202 项、3 项历史失败；改后 203 项（+1 docker02 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 14/14。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15518 词。链接审计 7711 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `b8171f1d…`，生成页 `9654b648…`（LF），导入器 `7eb8e635…`，测试 `cfd8afec…`，审查 JSON `a48f1806…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/docker-evidence-02/` 页首材料说明与箭头主线可见；3 个折叠默认关闭；11 个二级标题与「本页目录」11 链接齐全；§03 已无字面 `<pre>`/`<code>`/`&#124;`、有可复制命令块；§05.1 标题为「把清单落到文件」；§08.1/§09.1 无 Git 命令残留、含 5 处 git-docker-03 回链；§10 引言含 docker-evidence-01 回链；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b7-docker02-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 经验教训：inline_tokens 校验按次数（Counter 交集）而非仅存在性；本页首次暴露"存在性判断导致 min 次数不足"的新失败，已改用 `Counter(old) & Counter(now)`。改名/收缩后须同步：内容契约测试的 heading/detail、审查记录 `unaffected_hashes`。
- 已完成 / 尚未完成 / 下一页及下一节：B7 docker-evidence-02 完成。下一批按计划 B8 = `docker-evidence-03`（容器与镜像，含 P0-7 `-p` 参数、P2 输出文件名占位符与危险 capability）。其余 11 篇未开始。D1/D3 已定、D2 已执行；D4 待确认。
- 状态：本篇已验收。14 篇整体还没完成。

## 2026-10-11 · docker-evidence-03 两层阅读（Trae B8）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B8 = `docker-evidence-03`（Docker 取证 03｜容器与镜像）两层阅读 + P0-7 + P2 两条。用户指令"继续 B8"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b8-docker03-20261011/baseline/`。维护稿 `36074d59…`，生成页 `902e64c7…`，导入器 `7eb8e635…`，clear_flow 测试 `cfd8afec…`，审查 JSON `a48f1806…`。本批没有新取网页全文。入站锚点核实：`docker-evidence-03/#*` 无入站引用。
- 本批唯一写入文件与章节：两份 `docker-evidence-03` 正文；`scripts/import_manuals.py` 增本篇 3 折叠与 9 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 15 个）；`docs/server-forensics-review-20261006.json` 更新本篇 32 节、17 条本批改动、代码/表格/正文哈希。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：容器清单与 inspect、时间状态进程、Env/Mounts/NetworkSettings、权限与逃逸面、镜像身份与构建历史、镜像命令副作用、容器管理命令对象、exec 与容器内检查、Dockerfile 分层残留、save/export/load/import/commit、分开保全状态与层、数据库容器配置对应业务数据均在。映射在 `.work/trae-b8-docker03-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；8 个二级标题动作化、§09 原名即动作句仅加 span（共 9 个固定旧锚点）；§03 镜像命令表、§05.1 exec 表、§07 save/export 表三处折叠；27 处四标签收尾改为判据句；P0-7 §04.2 端口示意改为合法的 `-p 127.0.0.1:8080:80`；P2 §01.2 输出文件名统一到 `$CID`、§01.7 补危险 capability 名单。其余 38 个代码块、13 张表逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 203 项、3 项历史失败；改后 204 项（+1 docker03 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 15/15。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15519 词。链接审计 7711 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `23e45f4f…`，生成页 `4b5c773b…`（LF），导入器 `72a58460…`，测试 `394f19d2…`，审查 JSON `e1974d02…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/docker-evidence-03/` 页首材料说明与箭头主线可见；3 个折叠默认关闭；9 个二级标题与「本页目录」9 链接齐全；§04.2 已是完整 `-p 127.0.0.1:8080:80` 且无缺段映射行；§01.2 用 `container-$CID-inspect.json`；§01.7 列出危险 capability 名单；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b8-docker03-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B8 docker-evidence-03 完成。下一批按计划 B9 = `docker-evidence-04`（日志、文件与持久化，含 P0-8 `docker events` 256 条无依据、P1-4 local 日志驱动路径）。其余 10 篇未开始。D1/D3 已定、D2 已执行；D4 待确认。
- 状态：本篇已验收。13 篇整体还没完成。

## 2026-10-11 · docker-evidence-04 两层阅读（Trae B9）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B9 = `docker-evidence-04`（Docker 取证 04｜日志、文件与持久化）两层阅读 + P0-8 + P1-4。用户指令"继续 B9"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b9-docker04-20261011/baseline/`。维护稿 `739d00a5…`，生成页 `12b46909…`，导入器 `72a58460…`，clear_flow 测试 `394f19d2…`，审查 JSON `e1974d02…`。本批没有新取网页全文。入站锚点核实：`docker-evidence-04/#*` 无入站引用。
- 本批唯一写入文件与章节：两份 `docker-evidence-04` 正文；`scripts/import_manuals.py` 增本篇 3 折叠与 8 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 16 个）；`docs/server-forensics-review-20261006.json` 更新本篇 28 节、15 条本批改动、代码/表格/正文哈希。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：日志真实路径与驱动、CLI 日志与时间窗、默认目录与驱动表、访问/异常/攻击痕迹分析、数据根与子目录、containers/overlay2/volumes、containerd image store、logs/inspect/events 取舍、文件提取方向、Volume 与挂载类型、环境变量排查、可疑请求对到日志文件与卷均在。映射在 `.work/trae-b9-docker04-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；8 个二级标题动作化并各加固定空 span；§03.1 子目录表、§04.3 命令表、§05 cp 方向表三处折叠；23 处四标签收尾改为判据句；P0-8 §04.3 删除无依据的『256 条』改为 daemon 缓冲有限；P1-4 §02.2 补 local 驱动落盘路径 `containers/<ID>/local-logs/`。36 个代码块逐字节未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 204 项、3 项历史失败；改后 205 项（+1 docker04 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 16/16。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15520 词。链接审计 7711 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `2c2f73da…`，生成页 `645f42b7…`（LF），导入器 `308b4f33…`，测试 `e7d8a5ae…`，审查 JSON `a8754731…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/docker-evidence-04/` 页首材料说明与箭头主线可见；3 个折叠默认关闭；8 个二级标题与「本页目录」8 链接齐全；§04.3 已无「256」、含「缓冲」表述；§02.2 local 行含 `local-logs/` 路径；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b9-docker04-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B9 docker-evidence-04 完成。下一批按计划 B10 = `docker-evidence-05`（网络与 Compose，含 P1-5 网络模式表补 macvlan/ipvlan、D3 的 app-db LXC 片段折叠回链 docker-evidence-01 §09.2）。其余 9 篇未开始。D1/D3 已定、D2 已执行；D4 待确认。
- 状态：本篇已验收。12 篇整体还没完成。

## 2026-10-11 · docker-evidence-05 两层阅读（Trae B10，D3 收口）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B10 = `docker-evidence-05`（Docker 取证 05｜网络与 Compose）两层阅读 + P1-5 + D3（§06 LXC 片段折叠回链，D3 的最后一段）。用户指令"继续 B10"。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/trae-b10-docker05-20261011/baseline/`。维护稿 `91ffd338…`，生成页 `ecc8d8b2…`，导入器 `308b4f33…`，clear_flow 测试 `e7d8a5ae…`，审查 JSON `a8754731…`。入站锚点核实：`docker-evidence-05/#*` 无入站引用。内容契约核实：`tests/test_import_manuals.py` 第 270 行引用本篇 heading「容器网桥与通信归属」与 detail「桥名、子网和 DHCP 服务都可以修改」，故 §04 标题与 §04.1 该句原文保留。
- 本批唯一写入文件与章节：两份 `docker-evidence-05` 正文；`scripts/import_manuals.py` 增本篇 3 折叠与 6 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 17 个）；`docs/server-forensics-review-20261006.json` 更新本篇 16 节、13 条本批改动、代码/表格/正文哈希。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：网络清单与 inspect、网络模式、端点与主机名、网络命令副作用、Compose 命令对象与 stop/down 差异、桥名与租约归属、三层入口核对、Compose 定义与运行状态比较、IP 归属限定均在。映射在 `.work/trae-b10-docker05-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一行箭头主线；5 个二级标题动作化、§04 标题因内容契约保留（共 6 个固定空 span）；§02 网络命令表、§03 Compose 命令表、§05.3 端口字段表三处折叠；12 处四标签收尾改为判据句；P1-5 §01.2 模式表补 `macvlan`/`ipvlan` 两行；D3 §06 的 app-db LXC 定义/租约/到期换算详解收缩为材料、现场命令与结论并回链 docker-evidence-01 §09.2/§09.4（删 3 个代码块）。其余代码块、表格逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 205 项、3 项历史失败；改后 206 项（+1 docker05 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 17/17。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15522 词。链接审计 7714 个本地链接（+3，新增回链）、0 错误。缓存来源审计 errors 为空。维护稿现为 `d0952137…`，生成页 `168c0066…`（LF），导入器 `0034ea8a…`，测试 `84aa1f52…`，审查 JSON `1f1598f0…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/docker-evidence-05/` 页首材料说明与箭头主线可见；3 个折叠默认关闭；6 个二级标题与「本页目录」6 链接齐全；§04 标题原文保留；§01.2 含 macvlan/ipvlan 两行；§06 含 3 处 docker-evidence-01 回链（§09.2 ×2、§09.4 ×1）且节内 0 个代码块；无横向滚动。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b10-docker05-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B10 docker-evidence-05 完成，**D1/D2/D3 三个决策点至此全部收口**（D1 见 B6/B7/B8、D2 见 B5+、D3 见 B6→B7→B10）。下一批按计划 B11 = `git-docker-03`（Git 取证，D1 的 Git 唯一正文落点；D4 增补建议待确认）。其余 8 篇未开始。
- 状态：本篇已验收。11 篇整体还没完成。

## 2026-10-11 · git-docker-03 两层阅读（Trae B11）+ D1 回链纠错（B6b/B7b）

- 日期 / 执行者 / 用户任务：2026-10-11 / Trae（Nexus）/ 按 B1–B18 分批计划执行 B11 = `git-docker-03`（Git 取证：识别仓库与 `.git` 元数据）两层阅读。用户指令"直接开始 B11"。
- 开场发现并先修正的缺陷（B6b/B7b）：复核 D1 收缩落点时发现，REVIEW.md L154 的 D1 原文是"完整命令已在 **git-docker-03..08** 存在"（整个系列），而 B6/B7 把 `docker-evidence-01`/`docker-evidence-02` 的 Git 回链一律写成了单页 `git-docker-03`，但该页只讲"识别仓库/`.git` 泄露"，不含 log/reflog、reset 模式、show/diff、对象类型。已按内容归属改写回链：识别仓库与元数据=03、提交与差异(show/diff)=04、log 与 reflog/reset 模式/checkout/restore=05、对象模型(commit/tree/blob/tag)=06、stash 与引用=07；静态检查陌生 `.git` 的方法仍指向 03（原本正确）。改动限于 `docker-evidence-01`（4 处）与 `docker-evidence-02`（5 处）的链接句，两页已重同步；审查记录中对应两条 edit 的 new、两篇 `modified_text_sha256`/代码/表格/token 哈希已一并刷新。构建产物核对：01 页→03/04/05/06、02 页→03/04/05/06 各归其位（浏览器 8 项复核通过）。
- 修改前核对的文件、哈希和来源阅读状态：B11 基线 `.work/trae-b11-git03-20261011/baseline/`（在 D1 纠错前保存）。维护稿 `8475cd04…`，生成页 `fd3eaea2…`，导入器 `0034ea8a…`，clear_flow 测试 `84aa1f52…`，审查 JSON `1f1598f0…`。入站锚点核实：`git-docker-03/#*` 无入站引用；4 个二级 slug 已从构建产物核实（`02-git-元数据与泄露判断` 等）。
- 本批唯一写入文件与章节：两份 `git-docker-03` 正文；`scripts/import_manuals.py` 增本篇 2 折叠与 4 个固定旧锚点；`tests/test_server_clear_flow.py` 增本篇专项（现 18 个）；`docs/server-forensics-review-20261006.json` 更新本篇 13 节、8 条本批改动、代码/表格/正文哈希，并刷新上述两页条目。其他 19 篇未改。节数净 0。
- 语义查重结论 / 保留知识点与考点：`.git` 目录/文本指针判别、rev-parse 四判据、status --porcelain、gitdir/commondir/alternates 三个相对起点、六类保全位置、init/add/commit/clone 的影响、remote/pull/push 改哪一侧、站点目录完整性实战（HEAD/fsck/缺失 blob）均在；顶部 `git()` 安全函数与三条前置检查、四条读取注意全部保留。映射在 `.work/trae-b11-git03-20261011/knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：页首加材料说明与一声箭头主线；4 个二级标题动作化并各加固定空 span；首轮判读表与六类位置表两处折叠；9 处四标签收尾改为判据句。11 个代码块、2 张表逐字节核对未改（`check_diff.py`）。
- 基线与修改后命令、结果、退出码和旧失败差异：测试经 uv 临时环境执行。改前 206 项、3 项历史失败；改后 207 项（+1 git03 专项），失败仍是同 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。专项 18/18。UI 5/5。Astro 检查 0 错误 0 警告。构建 336 页、Pagefind 327 页 15522 词。链接审计 7724 个本地链接（D1 纠错使跨页链接 +10）、0 错误。缓存来源审计 errors 为空。维护稿现为 `056df032…`，生成页 `4cfaf868…`（LF），导入器 `9fc30b90…`，测试 `832cd510…`，审查 JSON `0e20cb08…`；D1 纠错后 `docker-evidence-01` 维护稿 `06fca292…`/生成页 `84fb92d5…`，`docker-evidence-02` 维护稿 `5a5b5f1f…`/生成页 `6504da1f…`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/git-docker-03/` 页首材料说明与箭头主线可见；2 个折叠默认关闭；4 个二级标题与「本页目录」4 链接齐全；无四标签残留；无横向滚动。另复核 `docker-evidence-02`：08.1 指向 04/05、09.1 指向 03/04/05/06（不再误指 03）。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/trae-b11-git03-20261011/rollback-trial/` 五份基线哈希与清单一致；基线导入器转义现稿 details/span，现行导入器保留。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：B11 git-docker-03 完成（含 B6b/B7b 纠错）。下一批按计划 B12 = `git-docker-04`（提交记录与全局视图、show/diff 三层、敏感内容搜索、已删除配置定位）。其余 7 篇未开始。D1/D2/D3 已收口；D4 待确认。
- 状态：本篇已验收。10 篇整体还没完成。

## 2026-10-09 · Cursor本地工作区接入

- 用户选择：本地专用工作区，直接管理ctf-atlas，不创建云端Project或上传远程仓库。
- 本次执行者：Codex负责项目配置与交接；Cursor仅做只读理解核对，未获本次开始下一批文章改写的指令。
- 配置范围：工作区、.cursor/rules、索引排除、docs/maintenance、只读项目检查脚本。
- 网站正文、历史报告、AGENTS.md、分类和既有测试不因本次接入而改动。
- 原服务器风格批次：3篇36节已核对；剩余18篇497节；下一批网站重构01。确切状态看CURRENT-STATE与原STATE。
- 本次验收记录：`.work/cursor-project-setup-20261009/VERIFICATION.txt`；运行与UI结果以该文件为准，未完成项不得在这里提前宣布完成。
- Cursor界面已打开本地“CTF-Atlas-知识库管理”，路径为本工程；Customize → Rules显示三份新增项目规则和既有AGENTS。没有初始化Git、建立云端Project或切换模型。
- Cursor会话“CTF Atlas knowledge review”已实际读文件并复述八项要求。首轮短样例漏写“已确认PHP”的前提，经补充规则第16条、重新读取和二次回答后已纠正。原始回答及修订回答保存于验收目录，不把初次遗漏隐藏成一次通过。
- 本轮原有488个文件哈希未变；修改前后六组检查相同：完整Python测试仍为原3个失败，其余UI/检查/构建/链接/缓存来源审计通过。正文配对76/76、服务器保全10/10。浏览器视觉和交互搜索仍未在本轮复核。
- 当前状态：本地接入与理解核对完成，Cursor等待用户具体修改任务；没有开始网站重构01，也没有把剩余18篇497节标为完成。后续每一小批仍需逐点覆盖和实际验收。

## 2026-10-09 · 网站重构第01节风格改写

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 从 forensic-website-reconstruction 第01节开始做服务器取证风格改写。
- 修改前核对的文件、哈希和来源阅读状态：维护稿字节 SHA-256 `1fc36eb02729c4a0291387fe75dc43952bb3fcc4d6e0617c7e92c1f5a0150e47`，生成页字节 SHA-256 `5c8bd0188b2c3d8167f0bf08fc3a806c6de67668c4ca2811ff6bca1bb270f313`，正文 SHA-256 `f29e456e33b0e61df8d1f83fb855d9b12fcd9ae225285cf8ee224fc6dc0755cf`。两份正文当时一致。审查记录里的来源仍是既有阅读状态，本批没有新取网页全文。
- 本批唯一写入文件与章节：`src/content-curation/forensic-website-reconstruction.md`、`src/content/knowledge/forensic-website-reconstruction.md` 的 `## 01`；`docs/server-forensics-review-20261006.json` 只更新了这一节的说明和受影响哈希。06.5及第02节以后的正文未改。
- 语义查重结论 / 保留知识点与考点：第01节仍是“先固定站点材料，再在副本上恢复”。没有并入总览里的服务链路表，也没有提前写PHP后台四方法。Host-only写成“模式名不能代替路由检查”，避免和服务器服务页里“通常不从外部直接访问”互相打架。
- 实际改动 / 未改内容 / 冲突处理：保留恢复目标、完整流程句、四阶段表、外联限制、原复制命令和代码目录外的数据缺口。原复制命令不单独记录权限，所以在只读挂载上追加 `site-metadata.txt`，并用数字UID/GID，不用分析机账户名。
- 基线与修改后命令、结果、退出码和旧失败差异：改写后维护稿 `ba4b9d3afd980cff733e31d13adb55bbc1f53c997e4896aa2768636ca4deb34e`，生成页 `a2269498c8576756e40cc6f75eafd7c30ccee42b88281a37efcd71844110da20`。最后一句措辞修正后重跑完整Python测试：189项、失败3项，与历史相同，分别是外部目录缺失、MySQL旧哈希、Docker01旧哈希。同一次修正后构建336页、Pagefind 327页、链接审计0错误。保全专项10/10包含在这次完整测试里。UI 5/5和Astro检查0错误是修正前一次运行，检查的是页面组件，不读取这句正文。
- 页面与搜索实际检查 / 待核：预览页能看到第01节标题、阶段表、两段bash和01–08目录。搜索框已聚焦，提交查询被工具拦截，结果列表待核。GNU find临时目录只看到普通文件和目录，软链接类型`l`未在本机复现。
- 回滚副本检查 / 变更包：`.work/server-style-batch02-20261009/baseline/` 保存改写前文件。独立副本恢复到改写前哈希，正式正文保持新稿。
- 已完成 / 尚未完成 / 下一页及下一节：第01节完成。下一节是同一篇的 `## 02 网站重构三要素：三条匹配链`。
- 状态：等待用户继续。

## 2026-10-09 · 网站重构第02–08节与面板第01、07、09节

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 用户要求继续改进服务器取证剩余内容，并明确本段不用核对、直接改正文。
- 修改前哈希：网站重构维护稿 `ba4b9d3afd980cff733e31d13adb55bbc1f53c997e4896aa2768636ca4deb34e`，生成页 `a2269498c8576756e40cc6f75eafd7c30ccee42b88281a37efcd71844110da20`。面板改写前另存于 `.work/server-style-batch04-20261009/baseline/`。
- 本批写入：`forensic-website-reconstruction` 的第02、03、04、04.1、04.2、05、06开头、07.1、07.2、08开头；`forensic-server-panel` 的第01、07、09节。两份维护稿都已同步到对应生成页正文。审查 JSON 更新了这两篇的正文哈希和上述章节说明。
- 保留：命令块、表格、行内技术字段、06.5 四方法、网站重构 07.3 和面板第10节的既有修订段落。07.2 只改备份这条路线，没有把认可样例再抄成第二套完整流程。
- 未改：网站重构 04.3、04.4、06.1–06.4、06.6、06.7；面板第02–06、08、10节。这些段落原来已经按操作顺序写。
- 验证：本段没有跑 Python 测试、Astro 检查、构建、链接审计和浏览器。代码块哈希、表格哈希和必须保留的修订段落各出现一次，已与审查记录对过。
- 修改后正文哈希：网站重构 `1645087d76a9a547ac47544d97ec66cf6679c9a7e22942a410e1832534ce7cc7`，其生成页字节 `d85dbdc9c49c99103bbd2f905263b765b393835b7ee9ce356df248300d92127b`。面板正文 `9cef2237dc0092b2cbd4ffe00d3916a5b2127bfc57a8223a7cc4e900fa7db4f4`，其生成页字节 `1eb3d9c1432e53d77b089c50480df650eaa5bc57fa55f1a1dd43b9f6ce2568ed`。
- 下一节：`forensic-server-services`。不要重写网站重构第01节、06.5、07.3，也不要重写面板第10节。
- 状态：等待用户继续。正文已改，整站测试未跑。

## 2026-10-09 · 网站重构 07.2 按认可样例重写（等待风格验收）

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 用户要求暂停全模块推广，只把 forensic-website-reconstruction 的 07.2 改成可跟着做的完整恢复过程，并等待风格验收。
- 修改前基线：`.work/server-style-batch05-20261009/baseline/`。维护稿字节 `1645087d76a9a547ac47544d97ec66cf6679c9a7e22942a410e1832534ce7cc7`，生成页字节 `d85dbdc9c49c99103bbd2f905263b765b393835b7ee9ce356df248300d92127b`。两份正文当时一致。本批没有新取网页全文。Context7 不可用，MySQL 报错含义沿用项目内已认可样例，没有另查当前版本文档。
- 本批唯一写入章节：两份网站重构正文里的 `### 07.2`。审查 JSON 更新了这一节说明，以及因新增命令、表格而变化的代码块、表格和正文哈希。06.5、07.3 和其他章节未改。
- 语义查重 / 保留：原查找命令字节未改。操作记录不等于压缩成功、salt 不同先查输入字节、备份版本和日志时段、角色与分页、新账号不计入历史，都留在本节。登录主线写成方式 A、方式 B；方法二、方法三仍只在 06.5，本节点明何时去用，没有另写一套矛盾步骤。
- 修改后哈希：维护稿 `16c7f9658a7c09759de7e51b078ed88d31180f7d46faddeb0a449aacedeae6f0`，生成页 `7a2d3daec3a91009d15f7a6090160e88a095cc5fe23ce923849e2cdbf23961d1`。
- 验证：Python 189 项，失败仍是原来 3 项（工具目录缺失、MySQL 旧哈希、Docker01 旧哈希）。UI 5/5。Astro 检查 0 错误。构建 336 页，Pagefind 327 页。链接审计 7680 个本地链接、0 错误。缓存来源审计 errors 为空。独立副本回滚到改写前哈希，正式目录仍是新稿。
- 页面：已有预览 `http://127.0.0.1:4329/knowledge/forensic-website-reconstruction/#072-面板列表为空从备份与操作记录找回-php-站点` 能看到新标题、文件菜单、三个目录分支和路径块。右侧目录仍是 01–08。搜索词 `php-cgi-74` 只返回这一页；结果摘要停在较早的 PHP 段落，没有单独摘出 07.2 那一句。
- 状态：等待用户风格验收。未确认前不推广。

## 2026-10-09 · 网站重构 07.2 定点精修（等待用户验收）

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 保留已改好的 07.2，只做定点精修并检查实际页面，不推广到整个服务器取证模块。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/server-style-batch06-20261009/baseline/`。维护稿字节 `16c7f9658a7c09759de7e51b078ed88d31180f7d46faddeb0a449aacedeae6f0`，生成页字节 `7a2d3daec3a91009d15f7a6090160e88a095cc5fe23ce923849e2cdbf23961d1`，审查 JSON `4fff230982271f844df334086061a1693733a6e90306306aed8ed759d7960823`。本批没有新取比赛原文。Context7 不可用。`tar -tv`、`sqlite3 .backup`、`systemctl list-units`、`ss -lntp/-lxnp`、`zipinfo` 分别按 GNU tar 手册、SQLite 命令行文档、systemd 手册、iproute2 手册和 Info-ZIP zipinfo 手册核对。
- 本批唯一写入文件与章节：两份网站重构正文里的 `### 07.2`；`docs/server-forensics-review-20261006.json` 只更新这一节说明和因此变化的代码块、表格、正文与文件哈希。06.5、07.3 和其他章节未改。
- 语义查重结论 / 保留知识点与考点：七步主线、宝塔菜单、配置搜索、Navicat 两页、报错到认证代码、PHP-FPM/进程池/socket、方式 A/B、salt、回滚和证据保全都保留。方法二、方法三仍只在 06.5，本节改为可点击链接。
- 实际改动 / 未改内容 / 冲突处理：修正监听与访问端口、欢迎页四种可能、hosts 条件、socket 排查、socket 自身权限、空库三种情形、`$PANEL_DB` 定义、SQLite 冻结提取与运行中备份、归档详细清单。查找命令分别放回找备份、找配置和定位认证代码，文末不再重复整组。重复的空列表、四套账号和结尾提醒已收短。
- 基线与修改后命令、结果、退出码和旧失败差异：精修后维护稿 `9918c70dcaffa76606a6a13004fee977d9a25c2877378bea823de6933cbe2fa8`，生成页 `a5785993e8f8c471ba89bf2e7ef0a04ff3f2b6483b62d0ce6d4b927bc84d6b77`。服务器保全 10/10。完整 Python 189 项，失败仍是原来 3 项：工具登记外部目录缺失；MySQL 旧正文哈希 `b9bd9436…` 对 `7a9ca835…`；RegRipper 里 Docker01 哈希 `0264e09e…` 对 `527afd4f…`。没有新增失败，也没有改测试预期。UI 5/5。Astro 检查 0 错误。构建 336 页，Pagefind 327 页、15355 词。链接审计 7682 个本地链接、0 错误。缓存来源审计 errors 为空。
- 页面与搜索实际检查 / 待核：预览页能看到 07.2 标题、编号步骤、目录分支列表、路径代码块、配置表和报错表。方法二链接落到原 h4。锚点仍是 `#072-面板列表为空从备份与操作记录找回-php-站点`。右侧目录仍是 01–08。`php-cgi-74` 只返回本页，摘要停在 04.2。`default-backup` 因连字符拆词，本页是 10 条里的第 6 条。搜索框手动提交这轮没有再做。
- 回滚副本检查 / 变更包：正式目录保持精修稿。回滚试验只在 `.work/server-style-batch06-20261009/rollback-trial/` 对照基线哈希，不覆盖正式正文。
- 已完成 / 尚未完成 / 下一页及下一节：07.2 精修和本轮检查完成。没有继续改其他章节。
- 状态：等待用户验收。

## 2026-10-09 · 网站重构 07.1 按已认可的 07.2 风格改写

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 用户认可 07.2 的内容、格式和讲解风格，要求按此改进服务器取证剩余内容，包括此前已改但未按这一风格写的章节。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/server-style-batch07-20261009/baseline/`。维护稿字节 `9918c70dcaffa76606a6a13004fee977d9a25c2877378bea823de6933cbe2fa8`，生成页字节 `a5785993e8f8c471ba89bf2e7ef0a04ff3f2b6483b62d0ce6d4b927bc84d6b77`，审查 JSON `a4b3cd07be2ae20846c709851e99e4679873b7da71bf211cedeb4d8b07d29c2f`。本批没有新取比赛原文。挂载参数、`systemctl` 和 `curl --resolve` 沿用本文已有命令，没有另造一套工具。
- 本批唯一写入文件与章节：两份网站重构正文里的 `### 07.1`；`docs/server-forensics-review-20261006.json` 更新这一节说明，以及因此变化的代码块、正文和文件哈希。07.2、06.5、07.3 和其他章节未改。
- 语义查重结论 / 保留知识点与考点：系统盘网站目录为空、数据盘上的面板/网站/日志/备份/数据库目录、商城路径 `/www/wwwroot/shop/public`、两个后台、订单编号/金额/币种/商户/状态、验证码、空列表、404、socket 权限和仿真记录，都留在本节。第 03 节的 ext4 `ro,noload` 和第 05 节的 `--resolve` 在本节按这次商城重写了一遍，方便这一节单独做完。
- 实际改动 / 未改内容 / 冲突处理：原来的四步清单和“先按第 03 节”改成八步：对盘、只读查看、映射 `/www`、对虚拟主机和面板库、对 `datadir`、按单元启动、打开前台并分开两个后台、核对一笔订单。补上 `$PANEL_DB`、`.backup`、`datadir` 所在配置，以及先列单元再启动。IP 和端口已经打开正确站点时，不强制 hosts。
- 基线与修改后命令、结果、退出码和旧失败差异：修改后维护稿 `81c0143956d90f5c32b763fa148e872f28e7e80b01dd566d3e277e3ff11928a9`，生成页 `64571127f677615e8530766feb416317aa153b379f832df210a714c8de53ecfb`，审查 JSON `627d4cb860efc06e3f5804f4fbe2eead43385018c08060fe5d94520f411bb620`。代码块 86，表 18。服务器保全 10/10。完整 Python 189 项，失败仍是原来 3 项：工具登记外部目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。没有新增失败，也没有改测试预期。UI 5/5。Astro 检查 0 错误。构建 336 页，Pagefind 327 页、15359 词。链接审计 7682 个本地链接、0 错误。缓存来源审计 errors 为空。
- 页面与搜索实际检查 / 待核：预览 `http://127.0.0.1:4329/knowledge/forensic-website-reconstruction/?v=071b#071-宝塔数据盘从-www-映射恢复-php-业务` 能看到 07.1 标题、八个编号步骤和 `lsblk` 代码块。页面正文里已经没有“先按第 03 节”。右侧目录仍是 01–08。搜索 `shop.example.test` 只返回本页，摘要是这次的 curl 命令。没有用真实检材重放这些命令。搜索框手动提交这轮没有再做。
- 回滚副本检查 / 变更包：`.work/server-style-batch07-20261009/rollback-trial/` 与基线哈希一致。正式目录仍是新稿。
- 已完成 / 尚未完成 / 下一页及下一节：07.1 完成。同一篇的 01–06、08、07.3，以及面板和其他服务器取证文章都还没按这一风格改完。下一节是同一篇的 `## 02`。
- 状态：正在按已认可风格继续。这一批先停在 07.1，等下一轮从第 02 节接着改。

## 2026-10-09 · 网站重构第 02、03 节按已认可风格改写

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 用户要求按已认可的 07.2 格式和讲解风格，继续改服务器取证剩余内容，包括此前已改但未按这一风格写的章节。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/server-style-batch08-20261009/baseline/`。维护稿 `81c0143956d90f5c32b763fa148e872f28e7e80b01dd566d3e277e3ff11928a9`，生成页 `64571127f677615e8530766feb416317aa153b379f832df210a714c8de53ecfb`，审查 JSON `627d4cb860efc06e3f5804f4fbe2eead43385018c08060fe5d94520f411bb620`。本批没有新取比赛原文。挂载参数和查找命令沿用本节原有写法。
- 本批唯一写入文件与章节：两份网站重构正文里的 `## 02` 和 `## 03`；审查 JSON 更新这两节说明，以及因此变化的代码块、表格、正文和文件哈希。01、04 以后、06.5、07.1、07.2、07.3 未改。
- 语义查重结论 / 保留知识点与考点：三要素表、八类技术栈、一行对照、localhost 不一定是同一台机器、fastcgi 与 proxy 的协议区别、Laravel 配置缓存、`php artisan config:clear` 会引导框架、Java 不运行 JAR、IIS 三种连接写法、ext4 `ro` 与 `ro,noload`、四目录候选、映射前四步和不要初始化空库，都留在原节。
- 实际改动 / 未改内容 / 冲突处理：第 02 节改成六步，技术栈表的第三列写成打开文件后接着核对什么，并补上虚拟主机查找和 JAR 成员名单。第 03 节改成四步，原两段挂载命令未改。网站目录为空时，在本节写明先对 UUID 和 `wwwroot`，不再只写“先做下一节”。
- 基线与修改后命令、结果、退出码和旧失败差异：修改后维护稿 `f5e0051ae428f6c6ac8f0522b0c5be022d25ca28471294b40c22d602893abf9c`，生成页 `79784ccd67b17bc28407848a294e9cbd37495d2a5393823f115d86b193f362af`，审查 JSON `8bae196c4a1e434c55dcd3a3994b4eb11e96abfaed80d8421b85c3f968437a42`。代码块 88，表 18。完整 Python 189 项，失败仍是原来 3 项：工具登记外部目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。没有新增失败，也没有改测试预期。UI 5/5。Astro 检查 0 错误。构建 336 页，Pagefind 327 页、15360 词。链接审计 7682 个本地链接、0 错误。缓存来源审计 errors 为空。
- 页面与搜索实际检查 / 待核：预览 `http://127.0.0.1:4329/knowledge/forensic-website-reconstruction/?v=0203b#02-网站重构三要素三条匹配链` 能看到第 02 节标题、六步和三要素表。第 03 节四步也在同一页。页面里已经没有“先做下一节把数据盘对上”。右侧目录仍是 01–08。搜索 `DB_NAME` 前几条不是本页。搜索框没有手动提交。没有用真实检材重放。
- 回滚副本检查 / 变更包：`.work/server-style-batch08-20261009/rollback-trial/` 与基线哈希一致。正式目录仍是新稿。
- 已完成 / 尚未完成 / 下一页及下一节：第 02、03 节完成。同一篇还剩 01、04–06、08、07.3，以及面板和其他服务器取证文章。下一节是 `## 04`。
- 状态：正在按已认可风格继续。这一批先停在第 02、03 节。

## 2026-10-09 · 网站重构第 04–06 节开头按已认可风格改写

- 日期 / 执行者 / 用户任务：2026-10-09 / Cursor / 用户要求继续按已认可风格改正文，并明确之后不用核对，直接修改文字。
- 修改前基线：`.work/server-style-batch09-20261009/baseline/`。维护稿 `f5e0051ae428f6c6ac8f0522b0c5be022d25ca28471294b40c22d602893abf9c`，生成页 `79784ccd67b17bc28407848a294e9cbd37495d2a5393823f115d86b193f362af`。
- 本批写入：两份网站重构正文的 `## 04`、`### 04.1`、`### 04.2`、`## 05`、`## 06` 到 `### 06.1` 之前。审查 JSON 更新了这几节说明和正文哈希。04.3、04.4、06.1–06.7、07、08 未改。
- 保留：原启动命令、面板库查询、PHP-FPM 与 socket 例子、ThinkPHP/WordPress/Laravel 分流、Docker inspect、SSH 隧道、curl、后台查找命令、验证码表和 `state=0`。运行中的面板库改为 `.backup`，冻结快照仍留主库和 `-wal`、`-shm`。
- 修改后：维护稿 `8dd5884fe99f5f80fa5b6c9420a7d8f1444cb9050e6edb5ffa1bc1e1a6d81d7a`，生成页 `46854d7e1631d0590fbaaa59d7ef9dcd9f8a1e67b467998b6b5990c8fa4f7f58`。代码块 88，表 18。用户要求本批不跑测试、构建和浏览器。
- 下一节：同一篇的 `## 08`。04.3、04.4、06.1–06.7 先读，已经是分步操作的不重写。
- 状态：按用户要求只改正文，继续下一节。

## 2026-10-10 · 网站重构 01/07.3/08、面板 01–09、服务页 01–05 与 08

- 日期 / 执行者 / 用户任务：2026-10-10 / Cursor / 用户要求按已认可的分步写法继续改剩余正文，并明确不用核对、直接改文字。
- 网站重构：改了 `## 01`、`### 07.3`、`## 08`。01 保留阶段表和两条 find；08 保留症状表、两条 SQL、变更表和四步还原；07.3 保留七步、Redis 命令和现象回查。审查记录里 07.3 的原段落已换成现稿。06.5 未改。04.3、04.4、06.1–06.4、06.6、06.7 仍是原来的分步正文。
- 网站重构基线：`.work/server-style-batch10-20261009/baseline/`。改完后维护稿 `74239b87920455b7257f21cb9012164565663594a00b368291a4801d79b9445e`，生成页 `54ce9294d67ea11c791bc04037b9eead2122f0a69743dac22cdc59c4db9a2b46`。代码块 88，表 18。
- 面板：改了第 01–09 节，补上操作顺序和收束。原路径表、查找命令、AES 示例值、CLI 和 schema 命令保留。第 10 节两段锁定文字未改。改前正文从当时尚未同步的生成页收回，文本哈希与旧正文哈希 `9cef2237dc0092b2cbd4ffe00d3916a5b2127bfc57a8223a7cc4e900fa7db4f4` 一致，放在 `.work/server-style-batch11-20261009/baseline/`。生成页原文件哈希 `1eb3d9c1432e53d77b089c50480df650eaa5bc57fa55f1a1dd43b9f6ce2568ed` 也在该目录。
- 面板改完：维护稿 `7b4841c3f88332f58b4e0f92e231d07407bb6916fd7ff481630bf29f33b03f79`，生成页 `f3dddcd5a8a2a993c615b41f8b246c48109a2b0e2448350c1513e4b436562b84`。代码块 20，表 5。
- 服务页：改了 `forensic-server-services` 的第 01–05 节和第 08 节。活机示例命令、cron 的五步判断和“脚本缺失不能写成已经执行”都留在原节。基线 `.work/server-style-batch12-20261010/baseline/`。改完后维护稿 `19913a55c6300f7d732ae303680b7a7cd80b9f506b04af78f65c0779a94cd42d`，生成页 `8f84d320af5a22650e4d9561672a6b83bb5bc9fb4e4c1c704a514f0603ca0fc5`。代码块 38，表 15。14.3、14.7、15.2 未改。
- 验证：按用户要求没有跑测试、构建、链接审计和浏览器。两份正文已按 strip 对齐。
- 下一节：`forensic-server-services` 的 `## 06`。不要重写本批已经改过的节，也不要改锁定段落。
- 状态：按用户要求只改正文，继续下一节。

## 2026-10-10 · Docker 取证 01、02 按分步写法改完

- 改了 `docker-evidence-01`、`docker-evidence-02` 全部现有标题。标题文字、代码块和表格未改。行内技术词没有少。
- 维护稿分别是 `3b0aa2c8216efcd4a7ac2bcf635adadb456c9288998561fbf07b1a04c838b820`、`e61c57bc755a9554907172dc5d97a47ac37431d8def06b94bf7b07eafc80150d`。生成页已与维护稿对齐。审查记录里被改写的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。其余服务器取证文章还在改。
- 状态：这两篇已对齐。整模块还没改完。

## 2026-10-10 · Docker 取证 03–05 按分步写法改完

- 改了 `docker-evidence-03` 32 节、`docker-evidence-04` 28 节、`docker-evidence-05` 16 节。标题、代码块和表格未改，行内技术词没有少。父级标题只保留引导，步骤写在子节。
- 维护稿 `22ed1d6d8a65b4fda10e605d404bf2251e1138dcab81077fdc82477086fe607c`、`5f8687045108fb43948cbd87ebda1eee3ad7515de9443543c45ab4f59f8619db`、`c3b8cc01a740779c7f79b56b0f893e5edb84ba796d2b29ba552dde59e2b4238c`。生成页已对齐。审查记录里被改写的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。
- 状态：这三篇已对齐。其余服务器取证文章还在改。

## 2026-10-10 · Kubernetes 与三篇案例按分步写法改完

- 改了 `forensic-kubernetes-cluster` 55 节，`fic-case-03` 18 节，`fic-case-04` 34 节，`fic-case-05` 23 节。标题、代码块和表格未改，行内技术词没有少。
- 维护稿 `aed2e60f13feca1da87c24c5a5e41f9694e744823741ea58767516f0d11b5da0`、`74aa0687281088300ffccf50948ac8b92876efaf6d6a4f6dd683da349ceee62f`、`f9dcb4a43261316c0a1023bb0f0a6776a93fcdb9f95a5d6333d9232cfa16b718`、`c73a3585ad408aeb82225d47ff5c202c24ae4d4cef9c05e939936a4156e1df4f`。生成页已对齐。审查记录里被改写的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。
- 状态：这四篇已对齐。MySQL 表恢复、Git、云虚拟机、服务页和面板剩余节还在改。

## 2026-10-10 · MySQL 表恢复按分步写法改完

- 改了 `forensic-database-recovery` 全部 70 节。标题、49 个代码块和 14 张表未改，行内技术词没有少。
- 维护稿 `3bab3bf1bb02735a076a8a70308fd9e45fbd67d72c2c693ba856055afb0e8308`。生成页已对齐。审查记录里 30 处被改写的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。
- 状态：这一篇已对齐。Git、云虚拟机、服务页和面板剩余节还在改。

## 2026-10-10 · 服务页、面板和网站重构剩余节改完

- 服务页改了还没有收束的 38 节，面板改了 15 节，网站重构改了 8 节。已经有收束的节没有重写。网站重构 06.5 到 06.6 之前的字节未变。
- 标题、命令块和表格未改，行内技术词没有少。面板 10.4.1、10.8 和服务页 14.3、14.7、15.2 的审查原段落已换成现稿。
- 维护稿：服务页 `158431e226b945246c2442f3497425ca72c9a1201038a4c00ebdfa03c1ca7839`，面板 `3692090da9054b5c11aa334059b6252ed0435a4753917d675a3f2c892a97a5a6`，网站重构 `5a890ce10e45c1f2b1b3b53cbd5306d512d0674afa016c7856edd9b31d9ae2de`。生成页已对齐。
- 按用户要求没有跑测试和浏览器。
- 状态：这三篇已对齐。Git、云虚拟机和服务器总览还在改。

## 2026-10-10 · Git、云虚拟机和服务器总览改完

- 改了 `git-docker-03` 到 `git-docker-08`、`forensic-cloud-vm`、`forensic-guide-server`。标题、代码块和表格未改。
- 改写时漏掉三个行内技术词，已补回：服务器总览的 `ss` 与 `-tulpn`，Git 的 `show <tag>` 和 `fsck`。
- 生成页已对齐。审查记录里被改写的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。服务器取证 21 篇的这轮分步改写到这里对齐完成。
- 状态：这一批已对齐。没有重跑测试，不能把历史测试结果写成这次已通过。

## 2026-10-10 · 补齐父级标题和 06.5 的收束

- 服务器取证里还有 98 个只有引导、没有收束的父级标题，以及网站重构 06.5 的引言和四种方法。这次都补上了「对上了什么 / 还缺什么 / 用什么结果证明 / 留下哪些材料」。
- 没有新增标题，没有改命令块和表格。06.5 的四个方法标题、锚点和原有命令还在。四种方法的字节哈希已换成现稿 `bcba8c4be2642a29b1cd1fcd32d4a98389a39971132a0a02ffb1412c92e129a5`。
- 生成页已与 21 篇维护稿对齐。审查记录里因此对不上的原段落已换成现稿。
- 按用户要求没有跑测试和浏览器。
- 状态：服务器取证 533 节都有这套收束。没有重跑测试，不能把历史测试结果写成这次已通过。

## 新一批记录模板

每次复制下列字段并填写事实，不覆盖上面的历史：

- 日期 / 执行者 / 用户任务：
- 修改前核对的文件、哈希和来源阅读状态：
- 本批唯一写入文件与章节：
- 语义查重结论 / 保留知识点与考点：
- 实际改动 / 未改内容 / 冲突处理：
- 基线与修改后命令、结果、退出码和旧失败差异：
- 页面与搜索实际检查 / 待核：
- 回滚副本检查 / 变更包：
- 已完成 / 尚未完成 / 下一页及下一节：
- 状态：正在修改 / 等待用户 / 已验收（据实填写）：

## 2026-10-11 · Codex 复查与微调（当前结论）

- 范围：既有服务器取证21篇、533节；本轮在10月10日保存基线，10月11日收尾。此前“不跑测试”的记录属于历史批次，不是本轮验收状态。
- 内容：定点修正 findmnt 与 fstab 的证明范围、Apache 九步顺序、SSH 四类认证与失败判读、Git 变更统计与提交树、Kubernetes 对象归属/端口/存储/日志定位、Docker 日志文件名以及数据库深度统计的边界。网站重构06.5仅校正文案中的验收条件与过强结论，四方法、代码及命令不变。
- 风格与格式：删除98处重复父级收尾；保留子节中的具体操作、判据和证据材料。统一标题后的空行，保留07.2认可样章的讲解内容，不再复制第二套完整流程。
- 保全：21篇维护稿与生成页对应一致；533个标题、520个代码块、184张表及原有技术字段保留。结构全覆盖不代表533节都已在真实检材上执行。
- 验证：Python基线189项/17项失败，修订后189项/3项失败；UI5/5；Astro检查0错误0警告；构建336页，链接审计7685个本地链接、0错误；缓存来源审计errors为空。未改测试或放宽断言。
- 剩余3项：本机工具目录路径缺失、MySQL旧正文前缀哈希、RegRipper测试引用的Docker01旧保全哈希。均在修改前失败，未通过改写历史报告掩盖。
- 页面：浏览器抽查网站重构04.4/07.2与Kubernetes05.2的内容、列表、表格和代码；服务器分类6+1+5+1+7篇，加导读共21篇；搜索targetPort得到1条并成功打开Kubernetes页。不是21篇逐屏检查。
- 证据：`.work/server-final-review-20261010/`保留基线、修改记录、逐命令原始日志、差异、修订包和回滚工具；以`VERIFICATION.txt`及`transaction-manifest.json`核对最终字节和独立回滚结果。正式目录保持修订稿，不覆盖相邻历史报告。
- 后续：内容复查本批已落稿；若处理上述3项工程历史检查，应另查工具目录及旧保全基线，不为了“全绿”降低检查要求。

## 2026-10-11 · 网站重构简明主线（最新单页调整）

- 用户要求：参考《利用宝塔重构网站》的简洁讲解和操作顺序，实际调整网站重构知识点后供检验。参考正文已在浏览器读取；只借鉴结构，不照搬其中不充分的成功判据。
- 结构：8个短步骤为默认阅读主线，10处原详解按需展开；先登录宝塔、找文件和核对环境，再打开前台、排查数据库、找后台并核对业务数据。默认Markdown约2500字符（含锚点与标记），不是全文缩成2500字。
- 保留：原88个代码块逐字节、18张表、全部三级四级标题和技术字段；8个旧二级锚点另设固定别名。删除24处重复模板收尾，07.2实操主体保留；其他20篇服务器文章不变。
- 同步：维护稿、生成页与当前审查记录一致；导入器仅为本页放行无属性details/summary及9个固定空span，其他HTML转义规则不变。没有新增知识点或改动页面模板。
- 检验：完整Python基线与修改后均189项、相同3项历史失败；新增折叠与重导入专项6/6，UI5/5，Astro检查0错误0警告，构建336页，7685本地链接0错误，缓存来源审计errors为空。没有修改现有测试或降低断言。
- 浏览器：8步与10个默认关闭的详解显示正确；打开并关闭运行环境详解、点击06目录；旧04.2子节链接自动展开且落在标题；搜索php-cgi-74找到1条并打开本文。其他旧主锚点以构建HTML及保全检查核对。
- 交付与恢复：本轮基线、精确命令、原始日志和独立副本回滚记录保存在`.work/website-clear-flow-20261011/`；最终状态以VERIFICATION.txt为准。网站内容验证不等于对真实服务器检材重放。

## 2026-10-11 · 服务器面板改为两层阅读

- 日期 / 执行者 / 用户任务：2026-10-11 / Cursor / 以当前网站重构页面为模板，精修服务器取证其余 20 篇。本段只完成 forensic-server-panel，并做重导入、测试、浏览器和副本回滚。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/server-two-layer-20261011/baseline/`。维护稿 `b1fa23467ee395b9b7b4b521517e51baf0a6f8cf9935235757200bfe936236e6`，生成页 `d46072343186b0e966037cf6a9f7664849d086e0da3cd3984f81479ecab8a6d5`，导入器 `93d1b7818515a084ff1e5d523fe3a8fd71e91ec1ef4eaac5c29a98a0543dda81`，审查 JSON `2f45ad91eccda08758b29158555309d1be082adccff90322778d1452d0ce4d6c`。本批没有新取网页全文。分类仍是服务器取证 / Web 与数据库。
- 本批唯一写入文件与章节：两份 `forensic-server-panel` 正文；`scripts/import_manuals.py` 只为本篇放行无属性 details/summary 和 9 个固定旧锚点；`tests/test_server_clear_flow.py` 新增专项；`docs/server-forensics-review-20261006.json` 只更新本篇标题、两处修订段落和正文哈希。网站重构和其他 19 篇未改。
- 语义查重结论 / 保留知识点与考点：10 节范围未并入网站重构。路径表、只读 sqlite、加密字段、上传对盘、空列表、CLI 菜单号和绑定四条路线都还在。映射在 `.work/server-two-layer-20261011/panel-knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：二级标题改成动作，第 10 节标题保持测试要求的原文。24 个标题、20 个代码块、5 张表字节未改。四个收尾标签改成各步自己的判据。没有改命令字节。
- 基线与修改后命令、结果、退出码和旧失败差异：改前 Python 189 项、失败 3。改后 195 项、失败仍是这 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。UI 5/5，退出码 0。Astro 检查 0 错误 0 警告。构建 336 页，Pagefind 327 页、15531 词。链接审计 7685 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `28c6a67eb51e46776a1ed7c6563696ed9ff94d1a5c3595c03c7e45e46c3879e4`，生成页 `c2dd6107249340d95d7b1fa0a52ee0fb183d137511a396ebe13394451c54984a`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/forensic-server-panel/` 默认看到箭头主线和 10 个新目录，15 个详解关闭。路径表可展开再收起。目录第 08 节落到标题。旧 `#02-宝塔常见数据落点` 落到 span。折叠内方法一锚点会展开并停在标题附近。搜索 `local-binding-fixture` 找到本页并打开，摘要来自折叠代码。390px 宽页面不横向撑破；路径在单元格里换行。没有编辑过程或来源标识。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/server-two-layer-20261011/rollback-trial/` 中的四份基线文件哈希与 baseline-manifest 一致。用基线导入器处理本篇时，details 和旧 span 会被转义；现行导入器保留无属性折叠和指定 span，脚本、带属性标签和其他文章的 details 仍转义。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：面板一篇完成。下一篇是 `forensic-server-services`，从开头和二级标题做同一结构；同批再做 `fic-case-03`。其余 18 篇未开始。
- 状态：首篇已验收。20 篇整体还没完成。

## 2026-10-11 · 服务页改为两层阅读

- 日期 / 执行者 / 用户任务：2026-10-11 / Cursor / 面板一篇通过后，继续把 forensic-server-services 改成简明主线和按需展开。
- 修改前核对的文件、哈希和来源阅读状态：基线 `.work/server-two-layer-20261011/baseline/`。维护稿 `b9ae1f107b01ea050bfbe5bd56f5cc73e8b593ce56350f34d5b2575b067311d6`，生成页 `d41665f4597afcb3fe49ea43135164fbe80da3f61ee61fad9f78a06e7813d3d8`。分类仍是服务器取证 / 主机与服务。本批没有新取网页全文。
- 本批唯一写入文件与章节：两份 `forensic-server-services` 正文；`scripts/import_manuals.py` 增加本篇的无属性折叠和 14 个固定旧锚点；`tests/test_server_clear_flow.py` 增加本篇稳定性检查；`docs/server-forensics-review-20261006.json` 更新本篇标题、行号和因此变化的修订段落。网站重构、面板正文和其他 18 篇未改。
- 语义查重结论 / 保留知识点与考点：服务清单、离线账户、journal、定时任务、Laravel、口令派生、业务统计、vsftpd 和 SSH 十一节都还在。第 14 节不并入 fic-case-03。映射在 `.work/server-two-layer-20261011/services-knowledge-map.md`。
- 实际改动 / 未改内容 / 冲突处理：01–13 和 15 的二级标题改成动作。第 14 节和 14.1–14.11 标题保持测试要求的原文。44 个标题、38 个代码块、15 张表字节未改。四个收尾标签改成各步自己的判断。没有改命令字节。
- 基线与修改后命令、结果、退出码和旧失败差异：Python 196 项，失败仍是原来 3 项：工具目录缺失；MySQL 旧正文哈希；RegRipper 里 Docker01 旧哈希。UI 5/5，退出码 0。Astro 检查 0 错误 0 警告。构建 336 页，Pagefind 327 页、15531 词。链接审计 7685 个本地链接、0 错误。缓存来源审计 errors 为空。维护稿现为 `5c21a4d6bd21777f4108e3e1910a97c77a4fe0144e417eb7c4a1198a6ab89623`，生成页 `b3c363defe63a0d9996fae747e0191384fa5b50662bcc00d93ae883fef73c77a`。
- 页面与搜索实际检查 / 待核：`http://127.0.0.1:4329/knowledge/forensic-server-services/` 默认看到箭头主线和 15 个目录，22 个详解关闭。账户口径详解可展开再收起。目录第 14 节落到标题。旧 `#08-实战验证一项可疑定时任务` 落到 span。折叠内 `#141-sshopenssh基础` 会展开并停在标题附近。搜索 `ListenStream` 只返回本页，摘要来自折叠内容。390px 宽页面不横向撑破。没有编辑过程或来源标识。没有用真实检材重放命令。
- 回滚副本检查 / 变更包：`.work/server-two-layer-20261011/rollback-trial-services/` 中的四份基线文件哈希与 baseline-manifest 一致。基线导入器会转义本篇 details 和旧 span；现行导入器保留无属性折叠和指定 span。正式目录保持修订稿。
- 已完成 / 尚未完成 / 下一页及下一节：面板和服务页完成。下一篇是 `fic-case-03`，从开头和二级标题做同一结构。其余 18 篇未开始。
- 状态：这两篇已验收。20 篇整体还没完成。



## 2026-10-14 · 网站重构六分类（当前批次）

- 用户确认以 PHP、Java、Python、Node.js、IIS、静态站六篇独立操作稿替换混合八步正文。每篇独立三要素表、逐步回填、失败分支、账号处理与旧记录验收。
- 保留既有页面ID与“服务器取证 → 网站重构”分类；只调整重构正文和邻页对应导航标签。旧入站锚点映射到新正文。
- 基线已保存，完整基线测试207项，3项失败、1项错误；不是历史记录中的只有3项。构建336页，链接审计0错误。
- 当前正在同步正文、更新导入与新内容契约、浏览器和副本回滚检查。最终结果另追加，不把此段当完成记录。


### 2026-10-14 · 网站重构六分类验收

- 正文：六类各自从材料定位、入口/程序/库确认做到旧编号金额和状态验收；36个步骤逐步回填三格。纯静态明确无数据库，含接口的前端分别验证后端。
- 分类：保留原专题ID，网站重构分类显示6类流程，六个入口直达对应章；未增加重复知识点，其余分类原样保留。只更正Web应用取证页中3处旧路由标签。
- 耐久：维护稿和生成页同步，导入两次保持正文和新标题；旧入站锚点保留。旧八步/四绕过正文测试契约按用户新要求替换，原独立认证构造实验及负例测试仍保留；本批旧全文与旧测试完整存档。
- 检验：基线207项，3项失败1项错误；修改后207项，同样4个既有问题，无新增失败。UI5/5；检查0错误0警告；构建336页、Pagefind327页；7705本地链接0错误，缓存来源审计errors为空。
- 浏览器：六类入口展开、六张三要素表、六项目录链接、IIS实际滚动落点、PHP旧后台锚点、搜索“网站重构”第一条新版正文；修正33处结果标签的加粗显示，无页面横向溢出。
- 回滚：独立副本恢复16份原文件并移除2个本批新增文件，489份受保护文件哈希全部回到基线；同一只读材料输入下原207项测试恢复相同3失败1错误。原材料不改，正式目录仍是六分类新稿；473份非本批文件无变化。
- 证据：C:\Users\23037\Documents\Codex\2026-10-14\php-java-python-node-js-iis\outputs\VERIFICATION.txt；包含原哈希、修改哈希、精确命令、结果、退出码与回滚状态。仅验证内容与站点显示，不把此结果当实际服务器检材重放。

## 2026-10-29 · Web 模块 SQL 注入页合并落库

- 日期 / 执行者 / 用户任务：2026-10-29 / Codex / 将审阅通过的 SQL 注入改进稿写入站点，替换原基础页并合并进阶页。
- 修改前核对：`web-data-query.md` 与 `web-sqli-advanced.md` 已备份到 `.work/backup-sql-20261029/`；备份哈希分别为 `59eb8722…`、`dd568715…`；新页哈希 `2e2b0209…`，WAF 链接页哈希 `8e010864…`。审阅稿为 `web-sql-injection.md`，正文已删结构解释句、13 防御、14 训练与记录。
- 本批写入文件与章节：`src/content/knowledge/web-data-query.md` 全文替换为 SQL 注入合并稿，frontmatter 改为 `topic: Web漏洞`、`tags: []`、`status: 已整理`、`updated: 2026-10-29`；删除 `web-sqli-advanced.md`；`web-waf-bypass.md` 的进阶链接改指 `web-data-query`；新增 `public/knowledge/web-sqli-advanced/index.html` 做 meta refresh 跳转；`astro.config.mjs` 不保留 redirects 配置。
- 语义查重 / 保留考点：合并稿覆盖原理三条件、参数化边界、联合、报错、布尔、时间、OOB、堆叠、文件、命令、token 绕过、非 URL 入口、DBMS 差异、sqlmap、实战流程与失败分支；原基础页的搜索型/参数化边界保留为表项，进阶页的 HANDLER、无列名、异或、二阶、宽字节、元数据入口均已并入。
- 实际改动 / 未改内容：只改 SQL 相关页与一条 WAF 链接；其他模块和 Web 其他页未动。旧页正文完整留在备份目录，未删除备份。
- 基线与修改后命令：`sh /app/data/build/ctf-build.sh`，退出码 0；构建 391 页，审计 392 页、9250 条本地链接、232 篇知识文章、79 篇工具，`Errors: 0`，`CTF_ATLAS_BUILD_OK`。Pagefind 无重定向页警告。
- 页面与链接检查：`/knowledge/web-data-query/` 浏览器显示 12 个二级标题、24 张表；`/knowledge/web-sqli-advanced/` 正常跳转；`/module/web/` 只列出一篇 SQL 注入。
- 回滚：恢复 `.work/backup-sql-20261029/` 两份原文件并移除新增跳转页即可回到修改前；备份哈希见上。
- 状态：已落库并通过构建审计。

## 2026-10-29 · Web 模块全量按模板改造

- 日期 / 执行者 / 用户任务：2026-10-29 / Codex / 按《Web 模块知识点模板》改造 SQL 之外的 Web 全部页面。
- 范围：Web 模块共 52 页（51 个 `web-*.md` + `git-history.md`）。本批完成环境工具 4 页（`web-local-lab`、`web-docker-lab`、`web-python-script`、`web-race-logic`）与 2026-10-29 补齐的 `git-history`；其余 47 页在此前批次完成。
- 统一结构：`00 速查 → 01 原理与成立条件 → 02 判断与分型 → 03 利用阶梯 L0–L4（每级前提/步骤/成功标志/失败分支）→ 04 绕过与边界 → 05 非典型入口 → 06 差异速查 → 07 工具与验证 → 08 实战流程 → 09 失败分支 → 10 记录与复现 → 相关`。删除“防御/修复/训练与记录”和结构解释句。
- 文档同步：`docs/web-module-upgrade/web-module-composition.md` 的 52 个标题按 frontmatter 回填，写作规范改为模板结构；`coverage-matrix.md` 映射不变。
- 结构自检：除 SQL 样板 `web-data-query.md` 外，51 页均含 00–10 与 L0–L4；全模块无 `防御/修复/训练与记录/13/14` 标题，无“这页把…”类元叙述。
- 构建审计：`sh /app/data/build/ctf-build.sh` 退出码 0；Astro check 0 errors / 0 warnings；构建 391 页；审计 392 页、9414 条本地链接、232 篇知识文章、79 篇工具，`Errors: 0`，输出 `CTF_ATLAS_BUILD_OK`。
- 浏览器抽查（Edge，`http://127.0.0.1:4329/`）：`/module/web/` 列出 52 条知识页链接且包含 `web-race-logic`、`git-history`；`web-python-script` 显示 00–10 共 11 个二级标题、L0–L4 共 5 个三级标题、13 张表；`git-history` 11 个二级标题、L0–L4、12 张表；`web-race-logic`、`web-docker-lab` 均为 L0–L4、13 张表；抽查页面正文均无“防御/修复/训练”章节。截图：`web-home.png`、`web-module.png`、`web-python-script.png`。
- 状态：已落库，构建审计与浏览器抽查均通过。

## 2026-11-26 · DSH 写作/查证/验证能力工程化（开工登记）

- 日期 / 执行者 / 用户任务：2026-11-26 / DSH / 按用户“依次全部执行，确保优化效果”落实能力改造：写作 lint、反例与术语固化、查证索引、验证与交接闭环。
- 修改前备份：`.work/2026-11-26-dsh-writing-improve/`，含 4 个 SKILL.md、CURRENT-STATE.md、WORK-LOG.md、START-HERE.md 与 profile 的 cordis.patch.yml；哈希随备份文件保存。
- 打算新增：`scripts/lint_writing.py`、`docs/maintenance/REJECTED-PATTERNS.md`、`docs/maintenance/TERMINOLOGY.md`、`.dsh/skills/ctf-atlas-research/references/local-tools.md`、`tests/writing-regression/`。
- 打算修改：4 个 SKILL.md、CURRENT-STATE.md 头部、profile 的 cordis.patch.yml（子代理模型授权与 persona 补一条）。
- 不改：现有正文、frontmatter、页面 ID、分类与测试契约；不动原始材料。
- 状态：开工，基线另记。
### 2026-11-26 · 能力工程化验收

- 实际写入：
  - 新增 `scripts/lint_writing.py`：高置信规则（正文占位词、代码块占位、元叙述、术语错拼、正文一级标题）加宽规则（空转表达、代码块后缺说明、中英标点混用、标题跳级）；默认报告模式退出码 0，`--strict` 才失败。
  - 新增 `tests/test_lint_writing.py`：12 项规则级自测，覆盖代码块与行内代码不误报、宽规则默认关闭、frontmatter 跳过。
  - 新增 `docs/maintenance/TERMINOLOGY.md`（依据 400 篇内容的真实写法统计）与 `REJECTED-PATTERNS.md`（7 条，全部取自现有规范或历史 WORK-LOG）。
  - 新增 `.dsh/skills/ctf-atlas-research/references/local-tools.md`：`D:\CTF_MISC_Tools` 19 类目录索引，只列目录名，不猜版本。
  - 新增 `tests/writing-regression/`：README 加 2 个案例（空泛闭环句、sqlmap 四环），粗稿与参考定稿均取自现有规范，未虚构。
  - 修改 4 个 DSH 技能（写作加句级规则与 lint 自检，验证加 lint 命令，查证加本机索引与来源三件套，交接加三项能力指标）；修改 START-HERE 与 CURRENT-STATE。
- 内容修正：`forensic-memory-volatility` 首段“本页把……”改为直接陈述，维护稿与生成页同步；`docs/forensics-shellbags-preservation.json` 两个哈希更新为新值。
- 保留：其余正文、frontmatter、页面 ID、分类与测试契约未动；未改动原始材料。
- 检验：
  - `python -X utf8 scripts/lint_writing.py --strict`：400 篇，0 命中，退出码 0。
  - `python -X utf8 -m unittest tests.test_lint_writing`：12 项 OK。
  - 全套 226 项：10 失败、9 错误，与改前 214 项的 10 失败、9 错误逐项相同；新增 12 项全过，零新增。
  - `cursor_project_check` 0 错误；`npm run check` 0 错误 0 警告；构建 391 页；Pagefind 382 页、16948 词；`audit_site.py` 9414 条链接、0 错误。
- profile 配置：`cordis.patch.yml` 新增子代理模型授权（`deepseek-account/deepseek-v4-pro`），persona 增加一条“动笔前读术语表与反例集”；改后 SHA-256 `435CDB6D…F25C1`，用 DSH 自带 YAML 方言校验通过。MCP 参数未变，热重载后 context7 与 playwright 实例继续运行，未重建。
- 回滚：`.work/2026-11-26-dsh-writing-improve/` 内含 4 个技能、3 份维护文档与改前 profile 补丁；恢复后重跑上述命令。
- 未做：没有复跑真实检材；没有在浏览器里逐页检查（仅一段正文改动，构建与链接审计通过）；子代理授权与 persona 需新建会话观察。
- 状态：已验收（构建与测试），浏览器与 DSH 新会话待用户确认。