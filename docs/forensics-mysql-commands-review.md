# MySQL 数据目录与表恢复：常用取证命令补充与核对

## 归属、整合与保全

- 用户要求：在已有“MySQL 数据目录与表恢复”知识点补齐常用实战命令，依据真实取证比赛题，详细、实用且结构清晰。
- 唯一正文为 `src/content-curation/forensic-database-recovery.md`；导入生成 `src/content/knowledge/forensic-database-recovery.md`。ID、URL、Forensics / 服务器取证 / Web 与数据库保持原样，没有新增文章或分类。
- 原11节26419字节完整前缀保留，SHA256为`77a63794767a7884ba220d5ba802b4ecb27697e0b079bfce617132d352866e54`。追加§12–25共14节，结构为：任务速查 → 文件与配置 → 连接参数 → 身份和会话 → 元数据 → 条件查询 → 业务聚合 → 时间和编码 → 8.x查询 → 导出与派生分析 → 物理恢复 → 日志 → 实战 → 排错核验。
- 385项其他src/public文件哈希不变；此前Android/iOS、ShellBags、注册表等知识点保留。新增6项专项测试读取正式保全记录，检查旧正文、其他主题、生成持久性、分类、命令和实践边界。
- RegRipper保全记录只刷新本次明确授权的MySQL主稿/生成稿两个哈希；保留原哈希、修改后哈希及原因，不删断言、不放宽其他文件检查。
- 内部覆盖记录为`forensics-mysql-commands-coverage.json`，记录23组命令、6个真实竞赛来源和26个一手文档。supplements新增29条网页记录，既有3条增加目标关联，新增32个目标关联；既有共享来源复核日期保留，避免更新无关文章。

## 真实比赛依据

真实题意逐项映射到正文，保留可见范围和“补充命令并非原WP使用”的边界。正文改写为独立业务场景，不复用固定答案、真实库名/口令或题号。

| 真实赛事与公开解析 | 读取到的考点 | 对应章节 |
| --- | --- | --- |
| [2022美亚杯个人赛](https://www.cnblogs.com/zzpu213/p/18652791) | Docker数据库端口、访问线索、业务库识别 | §13、§14、§16、§24 |
| [2024数证杯服务器](https://damodev.csdn.net/682416faa5baf817cf4b99f2.html) | 活动Java配置、镜像/账户恢复、业务状态与服务费合计 | §13、§15、§18、§22、§24 |
| [2025数证杯服务器](https://www.blog.st4rr.top/posts/f294c61f/index.html) | 成功订单统计、已删除记录与binlog、排除删除项的业务金额 | §17、§18、§23、§24 |
| [2024数证杯团体赛](https://www.cnblogs.com/WXjzc/p/18595176) | 累计提现、电话字符长度、消费/提现比率、层级关系 | §18–20、§24 |
| [2024数证杯个人赛](https://www.cnblogs.com/zzpu213/p/18692389) | 用户状态、地区聚合、均值及第二高判读 | §17–20、§24 |
| [2022第六届蓝帽杯半决赛官方解析](https://mdr.skyeye.qianxin.com/forum/share/1807) | 累计充值/赠送、净额口径、日登录去重、历史备份与聊天记录 | §18、§19、§21、§23、§24 |

没有把未公开的截图DDL补猜为真实字段；比赛提供的物理检材未复跑。`.frm/.ibd`恢复使用官方条件与模板，没有杜撰竞赛成功案例。

## 文档、版本与专业审阅

- Context7查MySQL官方手册，命令语义再与对应官方页面/固定5.7.44源码核对；部分旧手册URL重定向到新版本，未把重定向内容冒充旧版行为。
- 默认Kali/Linux，区分MySQL5.7/8.0/8.4与MariaDB。连接TCP/socket、首选项`--no-defaults`及login-path例外、大小写/排序/时区与只读一致性均单列。
- 明确COUNT精确计数和InnoDB TABLE_ROWS估算、COUNT与NULL、金额单位、JOIN倍增、SUM(DISTINCT)错误去重、AVG缺失值、半开日期区间、秒/毫秒和业务时区。
- 导出注明mysqldump默认锁、DDL/非事务表与single-transaction边界、跨库限定引用和ALTER DATABASE检查、TSV的NULL碰撞/转义、OUTFILE服务器路径与FILE/secure_file_priv。
- 物理恢复分完整匹配目录、InnoDB force_recovery、SDI/旧frm、transportable tablespace、MyISAM与XtraBackup增量；不把启动/prepare/import/repair当无写入读取。
- binlog只读DECODE-ROWS解释和可执行AUTO回放分开，注明备份前提、事务/位置/列序、GTID及目标日志控制，不把general_log当可补回未启用的历史日志。
- 主稿由独立审阅者复核；全部15组预期值另用Decimal、集合、关联及UTC/IP换算独立计算，不用实际输出反向修改预期。

## 自建SQL实践及确实执行范围

`public/practice/mysql-forensics/`提供schema.sql、queries.sql、expected-results.json和README.md，六张表全部构造：6用户、9订单、13明细、8提现、8资金事件、9登录。15个只读练习涵盖金额与人数、JOIN倍增、NULL、时间/编码、异常关联和分组。

- 本机实际执行工具为MySQL5.5.62；使用全新工作目录datadir、唯一命名管道和skip_networking，不连接既有数据库服务。
- 原练习15/15正确，mysqldump→另建空库→导入→再次查询15/15正确，两次逻辑导出字节一致。
- 典型字面结果：有效成功订单5条、用户4个、合计450.00；错误明细JOIN产生9条/800.00，错误SUM(DISTINCT)为350.00。
- 独立实验进程正常结束exit0；执行前后既有mysql服务保持RUNNING、PID5404，练习输入前后哈希一致。
- 5.5只证明这些核心SQL与逻辑往返；MySQL8的CTE/窗口/JSON、READ ONLY一致快照、OUTFILE、binlog/PITR、物理损坏恢复和IMPORT均为文档核对模板，不计入实测。练习不是真实比赛附件。
- 原始每条命令、输入、字面stdout/stderr、退出状态保存在工作证据的synthetic-command-records.json；顶层运行字面结果与实验状态分别在synthetic-run-record.json和synthetic-verification.json。

## 验收与回滚入口

基线91项测试90通过，1项既有失败：登记的外部工具目录`D:\CTF_MISC_Tools\Forensics\Inseyets PA`缺失。原目录断言及工具清单保持，没有伪造工具路径。TDD新增6项先失败后通过。全量重复导入exit0，src/public/README无变化，工具库存字节保留。

最终验收在`.work/mysql-commands-20261004/`：全量测试、UI、类型检查、构建、站点/网页来源审计、浏览器正文/搜索、独立审阅及独立副本回滚分别记录。四项证据为MODIFIED_FILE.md、DIFF_FILE.patch、VERIFICATION.txt、可执行ROLLBACK.sh。默认回滚仅预检；实际验证只在指定独立副本执行。恢复源文件而非dist、浏览器或服务状态，生产页保持本轮新增正文。

## 本轮已观察结果

- 修改后全量97项测试96通过、1项原目录缺失失败，新增6项全绿；UI5项通过，Astro18文件0 errors/warnings/hints。
- 构建336页面、搜索索引327页面；站点审计7660条本地链接、177知识点、79工具指南、Errors: 0；网页来源审计117条、50项标准、errors为空。知识点数量不变，Forensics仍76篇。
- 全量导入两次目标最终稳定，最后一次production_changed=[]，扫描166项工具但保留原tool-inventory字节。
- 初次全量检验发现两处文字触发旧审计规则：“源文件”及“误计350”被旧题号正则命中。仅改为“输入文件”“误计 350”，旧断言未变，新增测试补防回归；首次失败输出保留在validation-attempt01。
- 浏览器显示原11节与新14节共25节；命令速查/15组客户端参数/实践下载入口可见；SUM(DISTINCT检索4条，MySQL原页面第一，返回§12并保存JPEG截图。
- 临时证据中的所有最终结果以VERIFICATION.txt为准；回滚恢复源文件且原91项测试保留同一旧失败，不声称恢复构建产物或服务。

- 独立终审通过：旧正文前缀、385保护文件、生成正文一致、6专项测试、15条命令输入/输出哈希与15组独立预期计算均复核。主稿81333字节，SHA256 `4da563ba374bfe016ddb40436dd74198a9a9a67fa0a6206718d93ae75340a0c3`。
- 独立命名副本回滚exit0：恢复5个旧文件、移除9个新增文件，459项基线哈希全部恢复；原91项90通过、同一旧失败1项。MySQL恢复为原11节，Android/iOS/注册表/ShellBags保留；生产页新14节继续存在。完成记录回填后再次生成差异并在另一份全新命名副本重复该回滚核验。
