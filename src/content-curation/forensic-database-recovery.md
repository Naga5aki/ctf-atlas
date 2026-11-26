手里是一批数据库文件，可能是逻辑备份、整份数据目录、单表、MyISAM、XtraBackup 或 binlog，以及它们的配置与日志。本页回答：材料属于哪类、能不能单独恢复、怎么在隔离副本里打开、删除与时间点怎么核、结果与实验怎么分开交付。原始材料保持只读；启动、导入、回放、改账户只在副本上做。

**先认材料 → 在隔离副本恢复实例 → 读原始页与日志 → 核到可信记录 → 逻辑导入与导出 → 时间点回放 → 按最终证据清单交付。**

<span id="01-先辨认拿到的材料"></span>

## 01 先认出手里的数据库材料属于哪一类

手里是一批数据库文件，还分不清它是逻辑备份、整份数据目录、单表、MyISAM、XtraBackup，还是 binlog。文件名对了，也还不能决定能不能单独恢复。

操作顺序：先对扩展名和目录里的文件，再查页大小、加密、压缩、版本、外键和损坏范围，类型对上再往下走。

**1. 先按这张表认出材料。** 单表数据文件是 **`.ibd`**。若材料来自 MySQL 8，先查对应版本的数据字典，不直接套用旧版 `.frm` 恢复步骤。

<details>
<summary>展开数据库材料识别表</summary>

| 类型 | 识别线索 | 处理方式 |
| --- | --- | --- |
| 逻辑备份 | SQL、表定义、INSERT、字符集 | 用对应版本导入新建实验库 |
| 完整数据目录 | `ibdata1`、表空间、redo/undo、系统库 | 确认版本与一致性，整体恢复副本 |
| 单表材料 | MySQL 5.7 等旧版 `.frm` + `.ibd` | 恢复精确 DDL，再尝试表空间导入 |
| MyISAM | `.MYD` 数据 + `.MYI` 索引 + 表定义 | 仅在对应引擎的工作副本恢复 |
| XtraBackup | `xtrabackup_*` 元信息、`.qp`、xbstream | 解包/解压 → prepare → 独立实例恢复 |
| binlog、应用备份 | 变更事件、历史 SQL/配置 | 与主库状态和目标时间关联 |

</details>


**2. 文件名正确，只是材料识别的第一步。** 决定能否独立恢复前，再查页大小、加密、压缩、版本、外键和损坏范围。对不上就停在缺口上，不按错误类型继续恢复。

本节已核对这批文件属于逻辑备份、完整数据目录、旧版单表、MyISAM、XtraBackup，还是 binlog 或应用备份；页大小、加密、压缩、版本、外键或损坏范围还没核对时，不写成已经可以独立恢复。扩展名、`ibdata1`、`.frm`、`.ibd`、`.MYD`、`.MYI`、`xtrabackup_*` 或 `.qp` 和表里的处理方式是同一条，一并留存文件清单，以及页大小、加密、压缩、版本和损坏范围的核对记录。

<span id="02-frm-与-ibd-的旧版恢复路径"></span>

## 02 按旧版 `.frm` 与 `.ibd` 走单表恢复

手里是旧版 `.frm` 和 `.ibd`，实验空表还没建。`DISCARD TABLESPACE` 会改动实验表，不能用于证据库或生产库。

操作顺序：先留原文件哈希，提取候选 DDL，只在新建空库里 discard 和 import，报错就按结构、版本、页大小、密钥和完整性回查。

**1. 先保存原文件，不改原名。** 保存原文件哈希、文件名、相邻配置和版本信息。文件名带 MySQL 编码字符时，另列物理名与逻辑名对照，不改原名。以下流程限支持独立 InnoDB 表空间导入的匹配实验环境，必须在**专门新建的空库**执行。

**2. 提取候选建表语句，再核对字段。** 用匹配时代的 `mysqlfrm --diagnostic` 或其他解析器提取候选建表语句。mysqlfrm 是旧版工具，输出后逐项核对字段顺序、索引、行格式、字符集和引擎。

先创建示例的 `./output` 目录，再运行下面的命令。`>` 会写分析机上的输出文件；同名文件已存在时会被截断，所以每轮换新输出名，同时保存 stderr 和退出状态。

```bash
mysqlfrm --diagnostic ./work/table.frm > ./output/table-ddl.sql
```


得到文件后，先确认不是空文件，再检查候选 DDL 的字段、索引和版本。重定向创建了文件，不代表解析成功。

**3. 只在匹配版本的实验空表上导入。** 【仅在副本/仿真/授权环境执行】在匹配版本的独立实例创建结构相同的实验空表。对实验空表 discard，再按该版本要求复制 `.ibd` 及可用的 `.cfg/.cfp`，设置实验实例读写权限，然后 import。这些操作改变实验表和接收目录，不针对原文件。

```sql
-- 仅在已经按精确 DDL 建好的实验空表中执行
ALTER TABLE lab_database.sample_table DISCARD TABLESPACE;
-- 在此步骤之间按对应版本要求安放表空间副本
ALTER TABLE lab_database.sample_table IMPORT TABLESPACE;
SELECT COUNT(*) FROM lab_database.sample_table;
```


创建表才会生成相应结构；discard 并不是“生成 frm 的方法”。缺少一致性导出元信息时有些版本仍可尝试导入，但结果不保证完整。所有复制、权限改动和实例启动都保留记录。

**4. 保存导入日志，报错就逐项回查。** 保存导入日志，核对行数、字段和已知样本。报错时按结构、版本、页大小、加密密钥、文件完整性逐项回查，不忽略错误。

本节已核对候选 DDL 的字段顺序、索引、行格式、字符集和引擎，以及导入后的行数和已知样本；结构、版本、页大小、加密密钥或文件完整性对不上时，只留下报错，不把空实验表当成检材里没有记录。`mysqlfrm --diagnostic` 的输出不是空文件，导入日志和 `SELECT COUNT(*)` 来自同一张实验空表，一并留存原文件哈希、物理名与逻辑名对照、候选 DDL、stderr、退出状态和导入日志。

<span id="03-压缩物理备份与增量链"></span>

## 03 顺着压缩物理备份的增量链还原

手里是 XtraBackup 的元信息、压缩文件和增量目录，解包、解压和 prepare 还叠在一起。`--copy-back` 会写数据库目录，现在还不能做。

操作顺序：先在新目录解包再解压，确认工具版本后按 LSN prepare，接收路径确认之后才考虑写回。

**1. 保留元信息，把解包和解压分开。** 保留 XtraBackup 元信息、压缩文件和增量目录。先在新目录解包，再解压；解压与 prepare 是两个步骤。压缩备份可能需要 qpress，工具与备份版本应匹配。

```bash
mkdir -p ./work/unpacked ./output
xbstream -x -C ./work/unpacked < ./evidence/backup.xbstream
xtrabackup --decompress --target-dir=./work/unpacked
xtrabackup --prepare --target-dir=./work/unpacked
```


**2. 先确认数据库版本和备份工具是否匹配。** 上面的命令是适用的 XtraBackup 2.4 流程，MySQL 8 需要支持对应版本的工具。对不上就换工具，不拿这组命令处理另一版备份。

**3. prepare 只改工作备份目录。** 【仅在副本/仿真/授权环境执行】prepare 会改写工作备份目录，先留未修改副本，再按 LSN 顺序应用增量。加密表还要准备相关 keyring/密钥材料。

**4. 最后才考虑写回新实例。** 准备和核对完成后，最后才考虑 `--copy-back`。它会写数据库目录，执行前单独确认新实例的接收路径。

本节已核对解包目录、解压结果，以及按 LSN 准备过的工作备份；工具版本对不上、增量 LSN 不连续或加密表缺少 keyring 时，不写成已经可以 copy-back。未修改副本还在，prepare 的错误和退出状态与所用 XtraBackup 版本写在一起，一并留存元信息、压缩文件、增量目录、未修改副本，以及新实例接收路径的确认记录。

<span id="04-从恢复成功到可信记录"></span>

## 04 把“恢复成功”核到可信记录

恢复命令已经结束，但 `COUNT(*)` 一样还不等于每一行都相同。库里的最新状态，也不能直接写成事件发生时的状态。

操作顺序：先留下恢复前后的哈希和日志，用稳定主键核对业务字段，时间点再拿备份基线和日志覆盖对。

**1. 先记下恢复过程。** 记录恢复前后哈希、工具/数据库版本、DDL、备份时间和执行日志。

**2. 用稳定主键核对，不要只看行数。** 用稳定主键与业务字段核对账户、登录、交易或消息。`COUNT(*)` 一致仅说明数量相同，不证明每一条记录相同；还要抽样比对关键字段、索引、关联表和编码。

**3. 库文件和 binlog 各证明一个时间点。** binlog 反映操作序列，库文件反映某一状态。若要恢复目标时间点，先确认备份基线、日志覆盖和时间基准，【仅在副本/仿真/授权环境执行】再在副本重放；不要把最新状态误写为事件时刻状态。移动端与浏览器 SQLite 统一见 [SQLite 数据库与 WAL 残留](/knowledge/forensic-sqlite/)。

本节已核对稳定主键上的账户、登录、交易或消息，以及备份基线、日志覆盖和时间基准；只有行数相同、没有关键字段和关联表样本时，不写成每一条记录都已恢复。抽样字段、索引、关联表和编码与恢复日志是同一次恢复，一并留存恢复前后哈希、工具和数据库版本、DDL、备份时间、执行日志。

<span id="05-实战恢复一张旧版-innodb-表并验证记录"></span>

## 05 实战：恢复一张旧版 InnoDB 表并验证记录

手里是匹配旧版 MySQL 的 `.frm`、`.ibd`、邻近配置和备份记录，业务表还读不出来。先确认版本和引擎；本流程不适用于把任意 MySQL 8 表空间直接交给旧版 mysqlfrm。

操作顺序：先确认版本和引擎，再按下面两节建实验表并核对记录，MySQL 8 的表空间不要套这套旧步骤。


### 05.1 建立实验恢复清单

输入文件的哈希和未修改副本还没留，候选 DDL 也还没和同版本材料对过。

操作顺序：先列文件和哈希，核对候选 DDL，只在实验空表导入，再按主键看文字、金额和时间。

**1. 列出输入，留一套未修改副本。** 列出输入文件大小、哈希、物理名和目标逻辑表名，留一套未修改副本。

**2. 从 `.frm` 提取候选 DDL，并和相邻材料核对。** 拿配置、同版本程序和相邻备份核对字段顺序、索引、行格式、页大小、字符集及加密要求。

**3. 结构匹配后再导入。** 【仅在副本/仿真/授权环境执行】用精确 DDL 建实验空表，再 discard、复制、import；完整保留错误日志。结构不匹配就回查 DDL，不删列、改值凑成功。

**4. 导入后先数行，再查主键样本。** 导入后先统计行数，再选稳定主键检查文字、金额及单位、时间和关联表。备份或 binlog 可用时，对照同一记录的状态和操作顺序。

本节已核对输入文件的物理名、逻辑表名，以及字段顺序、索引、行格式、页大小、字符集和加密要求；结构不匹配或错误日志没留全时，不删列、不改值继续导入。行数、稳定主键上的文字、金额、时间和关联表来自同一次导入，一并留存未修改副本、哈希、候选 DDL 和完整错误日志。

### 05.2 示例判读与失败处理

表已经能查，但文字乱码、行数相同或缺少密钥时，还不能写成恢复正确。实验文件的新时间，也不是历史访问时间。

操作顺序：先分清编码、主键和材料缺口，再交付映射和日志，实验产生的时间单独记。

**1. 文字乱码先查编码和原始字节。** 如果表可查询但部分文字乱码，先检查字段编码、客户端显示和原始字节；不要在证据表上运行批量 UPDATE。

**2. 总数相同还要看主键和金额。** 若条目总数相同但主键/金额不同，数量一致不能说明恢复正确。

**3. 缺密钥或表空间损坏时只报告实际范围。** 若缺少密钥或表空间损坏，只报告实际恢复范围及错误，不据实验空表推断检材中没有业务记录。

**4. 交付样本，实验时间不写成历史时间。** 交付输入映射、DDL、版本、恢复日志、查询 SQL 和主键样本。实验启动与导入产生的文件时间属于本次恢复过程，不能当作历史数据库创建或最后访问时间。

本节已核对主键样本上的文字、金额和单位，以及实际恢复到的范围；乱码原因、密钥或损坏页还没查清时，不把实验空表当成检材没有业务记录。编码、原始字节、主键和金额已经对照；数量相同本身不算恢复正确，一并留存输入映射、DDL、版本、恢复日志、查询 SQL 和主键样本。

<span id="06-删除记录分析先分清软删硬删和日志覆盖"></span>

## 06 先分清软删、硬删和日志覆盖

订单还在不在、是怎么消失的，现在还分不清。下面先判断删除的实际含义，再固定日志链和事件当时的表结构。

操作顺序：先看行还在不在、字段有没有变，再固定日志顺序和版本，缺覆盖就不把“没找到”写成从未存在。


### 06.1 判断删除的实际含义

手里有网站业务库、MySQL 数据目录、`my.cnf`、应用代码、逻辑备份和若干 binlog，要确定一笔订单是否曾存在、何时被移除，以及能恢复哪些字段。启动、导入和回放还不能在原件上做。

操作顺序：先读保全材料，按表判断软删、硬删、未显示或范围不足，binlog 没有命中也不单独下结论。

**1. 优先读已经保全的材料。** **场景与材料：** 获得网站业务库、MySQL 数据目录、`my.cnf`、应用代码、逻辑备份及若干 binlog。数据库启动、导入和回放仅在隔离的新实例或工作目录进行。【仅在副本/仿真/授权环境执行】需要启动、导入或回放时换隔离副本。

**2. 先判断现在看到的是哪一种状态。**

| 状态 | 常见表现 | 需要核验 |
| --- | --- | --- |
| 软删 | 行仍在，`deleted_at` 或状态字段已变化；应用默认查询隐藏 | 删除方法、模型作用域、字段值与操作日志 |
| 硬删 | DELETE 后当前表中已没有该行 | binlog 删除事件、旧备份、相邻业务/审计记录及物理残留 |
| 未显示但未删除 | 分页、权限、筛选、归档表、不同库/实例 | 查询条件、连接对象、表结构与应用实际读取路径 |
| 恢复范围不足 | 缺日志、备份晚于删除、表空间被覆盖 | 覆盖时间、缺失文件、解析错误与方法限制 |


**3. 软删约定和硬删证据分开核。** `deleted_at IS NULL` 只有在该应用确实采用这种软删约定时才代表“未软删”。硬删也不是只能靠 binlog：历史备份、保留的物理页或其他记录可能提供证据，能否恢复受覆盖、清理、加密和数据一致性影响；已有表空间方法仍适用对应材料。不要因 binlog 未找到目标记录就断言它从未存在。

本节已核对这一行是软删、硬删、查询没显示，还是恢复材料本身不够；没有删除方法、旧备份或覆盖时间时，不把 binlog 未命中写成记录从未存在。`deleted_at` 或状态字段、应用查询条件和日志覆盖写在同一条判断里，一并留存业务库、`my.cnf`、应用代码、逻辑备份、binlog 范围，以及启动或回放所在的隔离副本记录。

### 06.2 固定日志链、表结构与版本

binlog 的真实路径和基名还没从配置、index 和卷映射里定下来。只打开搜到的一个文件，可能漏掉前后事务。

操作顺序：先定位文件并留下哈希，按 index、Rotate、位置和 GTID 排完整链，再用兼容的 `mysqlbinlog` 核对版本。

**1. 替换示例路径，找不到就单列错误。** 先从配置、binlog index 和卷映射确定真实路径与日志基名，替换下面的示例。找不到的目录或文件单列范围和错误。

```bash
EVIDENCE_ROOT=/mnt/evidence
DB_DIR="$EVIDENCE_ROOT/data/k8s_data/apps/mysql-data"
CASE=/work/mysql-case; OUT="$CASE/output/binlog"   # 与 §12.2 的对象约定一致
mkdir -p "$OUT"
find "$DB_DIR" -maxdepth 2 -type f \
  \( -name 'binlog.*' -o -name '*-bin.*' -o -name '*.index' \) -print
rg -n 'log[-_]bin|binlog[-_]format|binlog[-_]row[-_]image|datadir' \
  "$EVIDENCE_ROOT/etc/my.cnf" "$EVIDENCE_ROOT/etc/mysql"
sha256sum "$DB_DIR/binlog.000001" "$DB_DIR/binlog.000002" > "$OUT/input.sha256"
mysqlbinlog --no-defaults --version > "$OUT/parser-version.txt"
```


**2. 读完整链，再查截断和缺文件。** 按 index、Rotate 事件、文件位置及 GTID 排出日志顺序，保留各文件开头的格式描述事件。读完整链后，再查截断、校验失败和缺文件；只读一个搜到的文件，可能漏掉前后事务。

**3. 版本用多处材料互证。** 版本从部署镜像、启动日志、软件包记录、备份元信息和 binlog 头核对。在已恢复的隔离实例可用 `SELECT VERSION();` 辅助；它返回的是本次运行的服务器版本，不能单独证明历史版本。优先采用与生产者兼容、必要时同版本的 `mysqlbinlog`，记录工具全版本和解析错误；“补丁号必须完全相同，否则一概失败”过于绝对。MySQL 与 MariaDB 的版本、事件扩展和加密支持也不能简单互换。

本节已核对真实日志路径、基名、文件顺序，以及和生产者兼容的解析器版本；目录不存在、文件截断、校验失败或 MySQL 与 MariaDB 混用时，分别写明，不把本次 `SELECT VERSION();` 当成历史版本。index、Rotate、文件位置、GTID 和格式描述事件能串成同一条链，一并留存输入哈希、解析器版本、缺失文件清单和解析错误。

<span id="07-实战阅读-row-binlog-中一笔删除前的订单"></span>

## 07 实战：读 ROW binlog 里一笔删除前的订单

删除前的订单还在解码文本里，行镜像全不全、事务提交了没有，都还没分开。下面三节按这个顺序读。

操作顺序：先把日志解码成阅读文本，再看这一事件实际有哪些列，最后核验历史存在、删除动作和事务结果。


### 07.1 解码用于分析的文本

保全日志还没解码，分析机的默认配置也可能影响 `mysqlbinlog`。解码文本是用来读的，不是回放脚本。

操作顺序：先加 `--no-defaults` 和 `-vv` 解码，用 `rg` 定位后再读完整事件，列序号对上当时的 DDL。

**1. 只读保全日志，输出写到分析目录。** 先把 `--no-defaults` 放在选项首位，避免分析机默认配置影响解析。用 `-vv` 查看列类型等细节；`DECODE-ROWS` 把行事件显示成带注释的伪 SQL，便于读内容，不是回放脚本。下面只读取保全日志；解码文本和错误写入分析输出目录：

```bash
TZ=UTC mysqlbinlog --no-defaults -vv --base64-output=DECODE-ROWS \
  "$DB_DIR/binlog.000001" "$DB_DIR/binlog.000002" \
  > "$OUT/row-events.txt" 2> "$OUT/parser.stderr"
rg -n 'Table_map:|Delete_rows:|Update_rows:|### DELETE FROM|### UPDATE|orders|COMMIT|Xid' \
  "$OUT/row-events.txt"
```


`TZ=UTC` 固定本次解析的显示时区，不能改变应用字段原本的时区语义。保存退出状态和标准错误；出现格式错误、加密或损坏时先核对版本、密钥材料与日志完整性，不跳过失败记录后声称完整恢复。`rg` 是候选定位，必须阅读其前后的 Table_map、完整行事件和事务边界，不能只抄单条命中。

**2. 先确认两个输入属于同一条已排序日志链。** 把完整解码结果作为主记录。后续关键词筛选只用于导航：删除和更新的列值可能没有业务关键词，事务结束也可能落在轮转后的文件中；无命中时继续检查已经读取的范围和事件类型，不直接判定没有删除。分析文本、错误和输入哈希分别保留，避免反复执行时覆盖上一轮失败证据。

**3. 用构造片段练习删除前镜像。** **构造输出片段：** 假定当时的 DDL 依次为 `id`、`order_no`、`actual_price`、`status`、`updated_at`、`deleted_at`。位置、时间、编号与金额均为讲解数据，不是实际检材结果：

```text
# at 780
#260815 09:20:00 server id 1 end_log_pos 930 Delete_rows: table id 42 flags: STMT_END_F
### DELETE FROM `shop`.`orders`
### WHERE
###   @1=1201
###   @2='LAB-ORDER-001'
###   @3=49.90
###   @4=4
###   @5='2026-08-15 09:19:30'
###   @6=NULL
# at 930
# Xid = 57
COMMIT/*!*/;
```


先读删除事件的 WHERE：它表示**删除前行镜像**，不是当前表仍存在的行，也不一定是用户输入的 DELETE 原语句。

再把 `@1`、`@2` 等列序号对应到事件发生时的表结构。遇到 ALTER TABLE 要切换相应 DDL，不能一直套最新结构。字段名没有可靠依据时保留“第 N 列”，不猜业务含义。

本节已核对同一日志链上的删除前行镜像，以及 `@1`、`@2` 对应的当时列；格式错误、加密、损坏，或字段名没有依据时，保留第 N 列和解析错误，不补业务含义。Table_map、完整行事件和事务边界已经连着读过；`rg` 的单行命中不算完整事件，一并留存解码文本、stderr、退出状态、输入哈希，以及这一轮之前的失败输出。

### 07.2 行镜像的完整性决定能恢复什么

事件已经解码，但还不知道当时记的是全部列、只有主键，还是语句和行事件混在一起。

操作顺序：先看这一事件里实际有哪些列，对照行镜像范围，当前变量不能代替历史事件。

**1. 按实际事件读这张表。** 采集时 `SHOW VARIABLES` 或当前 `my.cnf` 只是当前设置，最终以该历史事件实际包含哪些列为准。

| `binlog_row_image` 或实际事件 | 可见范围 | 取证结论 |
| --- | --- | --- |
| FULL | 通常记录全部相关列；DELETE 仅有 before image | 可以逐列核对删除前值，但仍查日志/事务完整性 |
| MINIMAL | DELETE 可能只记录定位行所需主键或唯一键 | 可定位被删主键，未记录列不能凭空恢复 |
| NOBLOB | 部分不必要的 BLOB/TEXT 可能省略 | 正文或附件字段可能需要其他材料补充 |
| STATEMENT / MIXED | 可能看到原始语句，部分操作仍是行事件 | 依据每个实际事件分析，不把全文件都当 ROW |


**2. 分清插入、删除和更新各自的镜像。** 删除仅有 before image，插入仅有 after image，更新才有前后两类信息；不能说“每个 ROW 事件都有完整前后行”。有关行镜像范围见 [MySQL binlog_row_image](https://dev.mysql.com/doc/refman/8.0/en/replication-options-binary-log.html#sysvar_binlog_row_image)。

本节已核对这一历史事件实际包含的列，以及它是 FULL、MINIMAL、NOBLOB 还是语句/行事件混合；未记录的列、被省略的 BLOB/TEXT，或当前 `binlog_row_image` 和历史事件不一致时，分别写明。结论来自该事件里的列，不来自采集时的 `SHOW VARIABLES` 或当前 `my.cnf`，一并留存事件类型、可见列清单，以及和当前配置不一致的说明。

### 07.3 核验历史存在、删除动作与事务结果

行镜像已经有了，但“曾经存在”“发生了删除”“事务已提交”还是三件不同的事。

操作顺序：先留位置、表映射和当时的 DDL，对照旧备份和当前库，没有事务结束信息就不写成已提交。

**1. 保存位置和事务边界。** 保存日志文件哈希、事件开始/结束位置、server ID、表映射、可用 GTID、事务边界和显示时区。

**2. 按事件时刻的 DDL 逐列记录。** 核对事件时刻 DDL，逐列记录值、类型、NULL、编码与金额单位；包含个人或凭据字段的导出单独保存。

**3. 三项结论分开对照。** 以主键或订单号对照旧备份、订单关联表、应用访问/操作日志和当前库；区分“历史曾存在”“发生删除事件”“当前已不存在”三项结论。

**4. 看事务有没有结束。** 对事务型表检查后续 Xid/COMMIT 及完整日志链。只有截断片段而缺结束信息时，不把候选删除直接写成确认提交；非事务型表还需结合引擎行为。

**5. 只有主键时，缺列不要默认成 NULL。** 若行镜像只保留主键，报告能确认的字段范围，再通过前面的写入/更新事件、旧备份和关联记录补足，不把缺失字段默认为 NULL。

**6. 三份证据对上，再写删除结论。** **先列三份证据，再写结论。** 完整日志链中有主键 1201 的删除前镜像及对应提交；旧备份中有同一订单号；保全的当前快照中已无该主键。三者对应，才支持“记录曾存在，并在该日志位置被删除”。

时间另行解释：`updated_at` 可能是最后业务更新，事件头时间也不应单独当作用户点击删除的客户端时间。

本节已核对同一主键上的删除前镜像、旧备份里的订单号，以及当前快照里已经没有该主键；只有截断片段、没有 Xid/COMMIT，或行镜像只剩主键时，不把缺字段写成 NULL，也不把候选删除写成已提交。事件位置、当时 DDL、事务边界和旧备份是同一条记录。`updated_at` 和事件头时间各自保留含义，一并留存日志哈希、起止位置、server ID、表映射、GTID、显示时区，以及含凭据字段的单独导出。

<span id="08-阅读结果与实验恢复分开交付"></span>

## 08 阅读结果与实验恢复分开交付

解码文本已经能读，但还不能把它当成可以导入的恢复脚本。下面先分清阅读和回放，再按检查表交付。

操作顺序：先确认带注释的行只用于阅读，要看删除前状态就换备份基线和可执行日志，最后按检查表留下依据。


### 08.1 不直接执行带 `###` 的伪 SQL

`row-events.txt` 里有 `###` 开头的行。这些行是注释，删掉井号也不能变成正确的恢复 SQL。

操作顺序：先把解码文本当阅读结果，要恢复就从删除前备份回放到目标事务之前，列不够就只交付候选字段。

**1. 不要执行这些伪 SQL。** `-vv --base64-output=DECODE-ROWS` 的文本用于阅读，行事件的可执行 BINLOG 内容被抑制，`###` 行也只是注释。不能把 `row-events.txt` 当作完整恢复 SQL 直接导入，更不能靠删除 `###`、把所有 DELETE 替换成 INSERT 就保证恢复正确。它无法自动补齐字段名、未记录列、顺序、约束和事务语义。选项边界见 [MySQL 行事件显示](https://dev.mysql.com/doc/refman/8.0/en/mysqlbinlog-row-events.html)。

**2. 要看删除前状态，从备份基线回放。** 若目标是查看删除前状态，优先把**删除前的备份基线**恢复到新建的隔离实例，再按对应版本的方法回放完整、可执行的日志链到目标事务之前。【仅在副本/仿真/授权环境执行】回放包含写操作，执行前明确目标库、数据目录、备份位置和终止边界；停止位置要落在正确事务边界，不能切断事务。恢复后的记录与原日志/备份对照，实验产生的新 binlog 和文件时间不属于历史证据。

**3. 只能提炼一行时，写进单独的分析表。** 若只能从完整 before image 提炼一行，在单独的分析表中记录“根据事件重建的记录”、输入位置、DDL 与不确定字段。对照主键冲突、字符集、NULL、枚举、金额精度、关联表及应用显示；没有足够列时只交付候选字段，不制造完整订单。

本节已核对阅读文本和可执行回放已经分开；回放停在目标事务边界之前；字段名、未记录列、约束或事务语义补不齐时，只留下候选字段，不制造完整订单。恢复后的记录能对上原日志和备份；实验新产生的 binlog 和文件时间另外存放，一并留存目标库、数据目录、备份位置、终止边界，以及分析表里的输入位置和不确定字段。

### 08.2 最终检查表

库表、日志覆盖、被删值、恢复可靠性和统计口径，还没有各自的依据。网页能不能打开，也不能代替这些依据。

操作顺序：按表逐项对依据，缺一项就写缺口，查库和启动网站分开交付。

**1. 按这张表留下依据。**

| 检查项 | 应交付的依据 |
| --- | --- |
| 找的是哪个库/表 | 数据目录与实例对应、事件表映射、事件时刻 DDL |
| 日志是否覆盖目标期间 | index/Rotate/位置、事务边界、缺失和解析错误 |
| 被删值是否完整 | 实际行镜像列集合、类型、编码、缺字段说明 |
| 恢复是否可靠 | 备份基线、实验版本、回放范围、主键与业务字段核验 |
| 统计口径是否一致 | 状态定义、软删过滤、日期范围、时区、金额单位 |


**2. 查记录和启动网站是两条途径。** 业务状态与统计 SQL 的独立实战见 [数据库实例、业务字段与 SQL 关联](/knowledge/fic-case-05/)。查数据库记录与启动网站是两条途径：网页无法运行时，仍可沿表结构、代码和日志核对数据；网页能运行也不替代数据库和历史日志验证。网站程序、虚拟主机与资源重构集中见 [网站重构与业务验证](/knowledge/forensic-website-reconstruction/)。

本节已核对库和表、日志覆盖、被删列、恢复范围，以及统计用的状态、时间和金额口径；表里任一项没有依据时，写明缺口；网页能打开不代替数据库和历史日志。每一项检查都能指回数据目录、事件、备份或查询口径，一并留存这张检查表的依据，以及和网站重构分开存放的数据库核对记录。

<span id="09-实战区分-ssh-隧道和数据库连接目标"></span>

## 09 实战：分清 SSH 隧道与数据库连接目标

已有隔离仿真副本、网站连接配置、数据库启动日志和容器 inspect，要用 Navicat 读业务表。配置里的端点和口令还只是候选，不能代替连接后的身份核验。

证据先看应用 `.env`、`application.yml`、`web.config`，数据库 `my.cnf` 及其包含目录，容器 `Mounts`、`NetworkSettings.Ports`，以及数据库错误日志。

操作顺序：先把 SSH 和数据库分成两层，连上后用只读查询对实例和账户，对不上就记下报错和可见范围。


### 09.1 把两个连接层分别记录

SSH 页和数据库常规页还写在一起。常规页里的主机，是从 SSH 端点看出去的地址，不是分析机自己的回环地址。

操作顺序：先填 SSH 入口再填数据库入口，端口和账户分层记录，容器变量不等于卷里的当前口令。

**1. 两层分开填。**

| 连接层 | Navicat 中填写什么 | 核对什么 |
| --- | --- | --- |
| 分析机 → SSH 端点 | SSH 页的主机、SSH 端口、系统账户、密钥或口令 | SSH 主机身份、认证方式、转发限制与隔离范围 |
| SSH 端点 → 数据库 | 常规页的数据库主机、数据库端口、数据库账户及口令 | 从 SSH 端点看是否可达、实际匹配的数据库账户、目标实例 |


先填 SSH 入口，再填数据库入口。Navicat 常规页的主机是**从 SSH 服务器看出去的数据库地址**，只有数据库确实在它可达的回环地址上，才填 `127.0.0.1`。

例如宿主机 `127.0.0.1:13306` 发布到容器 `3306`，常规页按这条实际路径填写；SSH 端口、宿主机发布端口、容器端口分别记录。

隧道只改变网络入口，数据库仍要验证 MySQL 账户，Host 匹配以数据库实际看到的来源为准。SSH 系统账户和 MySQL 账户不是一个身份。[Navicat SSH 设置](https://www.navicat.com/manual/pdf_manual/en/navicat_17/mac_manual/navicat_mac_en.pdf)区分了这两层。

**2. 应用配置里的口令先当候选。** 先读应用配置里的 `DB_USERNAME` 与 `DB_PASSWORD`，记为应用账户候选；它可能只对一个业务库有权限，不直接称为 root 凭据。

**3. 镜像初始化变量不等于当前口令。** 容器中的 `MYSQL_ROOT_PASSWORD` 是 Docker 官方 MySQL 镜像的初始化变量。已有数据目录保留已有账户状态，变量不一定等于当前卷内口令。依次核对镜像身份、持久卷映射、初始化时间和后续账户变更，不删除卷或建空库验证口令。[官方镜像的已有数据库说明](https://hub.docker.com/_/mysql)说明了这种情况。

**4. 端点按容器或集群材料核对。** 容器端点按 [Docker 网络与 Compose](/knowledge/docker-evidence-05/)核对；集群端点按 [Kubernetes 集群取证](/knowledge/forensic-kubernetes-cluster/)核对。

本节已核对SSH 主机、端口、系统账户，以及从 SSH 端点看出去的数据库主机、端口和账户；只看到 `MYSQL_ROOT_PASSWORD` 或应用配置口令、还没核对卷内账户时，不把它写成当前 root 口令。宿主机发布端口、容器端口和 SSH 端口各记一层；`127.0.0.1` 只在数据库确实落在 SSH 端点可达的回环地址上才填写，一并留存两层连接参数、`DB_USERNAME`、`DB_PASSWORD` 的候选范围，以及镜像、卷映射和初始化时间。

### 09.2 用只读查询确认实例与账户

已经连上，但主机名、端口或库名相同，还不能确认就是目标实例。旧的 `mysql.user.password` 读法也不能套到现在的版本上。

操作顺序：先查版本、端口和匹配账户，再看授权和认证插件，连接被拒绝时按原因逐项分。

**1. 连接后先记录这些只读查询。** 再核对 schema、DDL、持久目录与一条已知主键记录。查询受权限限制时保留报错和可见范围；主机名、端口或库名相同都不能单独确认对象。

```sql
SELECT VERSION() AS server_version, @@hostname AS server_host,
       @@port AS server_port, DATABASE() AS current_schema,
       USER() AS supplied_identity, CURRENT_USER() AS matched_account;
SHOW GRANTS FOR CURRENT_USER;
SHOW CREATE USER CURRENT_USER;
```


**2. 按顺序读身份和端口。** 对比 `USER()` 和 `CURRENT_USER()`：前者是提交的用户名及连接来源，后者是服务器实际匹配的账户。记录 `@@port`，这是服务端监听端口；经发布或转发后，它可以不同于客户端填写的端口。把当前版本与部署记录、备份和历史日志比较。实验恢复时升级出的版本，不是历史版本。用 `SHOW GRANTS` 看权限，用 `SHOW CREATE USER` 看认证插件、锁定等属性。角色还要核对授予与本会话激活状态，并按目标版本解释。

输出可能带敏感认证材料，受限保存。[账户属性](https://dev.mysql.com/doc/refman/8.4/en/show-create-user.html)和 [授权显示](https://dev.mysql.com/doc/refman/8.4/en/show-grants.html)分别说明查询范围。

**3. 旧做法按版本纠正。**

| 常见旧做法 | 版本与取证纠正 |
| --- | --- |
| 固定读取 `mysql.user.password` | 系统表字段随版本与产品变化；现代 MySQL 的认证字符串也不是明文口令。优先按账户读取属性与授权，不把“列不存在”判成无密码 |
| MySQL 8 执行 `PASSWORD()` 或 `GRANT ... IDENTIFIED BY` | MySQL 8 移除了旧函数和通过 GRANT 管理认证的旧用法；账户创建、认证修改与授权应按版本分别使用账户管理语句 |
| 直接把 root 的 Host 更新为 `%` | 会改动账户范围且可能冲突；连接调查先核对当前匹配账户，不用全网 root 授权修复取证连接 |


相关移除项见 [MySQL 8 账户管理变化](https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html)。

**4. 连接拒绝时分开查原因。** 连接拒绝时依次区分端点不可达、端口未监听、账号/Host 不匹配、口令错误、插件/TLS 不兼容及库权限不足。旧客户端不支持认证插件时，先选择兼容客户端；`mysql_native_password` 在 MySQL 8.4 默认禁用，MySQL 9.0 起移除，不能把强制切换旧插件写成通用修复。[认证插件版本边界](https://dev.mysql.com/doc/refman/8.4/en/native-pluggable-authentication.html)给出适用条件。

**5. 两层都对上，才说明读到了哪一个实例。** **验证与判读：** SSH 使用主机 A，发布端口为 13306，数据库返回内部端口 3306、实例 B 和受限业务账户，DDL、已知主键与卷映射一致，支持“这次查询沿已记录路径读取了实例 B”。仅 SSH 成功或界面显示“连接成功”不够。保存两层参数、查询时间、输出、表样本与失败信息；不为连接测试关闭整机防火墙、开放远程 root 或写入原数据。

本节已核对 `USER()` 与 `CURRENT_USER()` 的差别、服务端 `@@port`，以及 DDL、已知主键和卷映射；只有 SSH 成功或界面显示连接成功、查询报错还没留下时，不写成已经读到目标实例。版本能对上部署记录；权限和认证插件来自 `SHOW GRANTS` 与 `SHOW CREATE USER`。实验升级出的版本单独标明，一并留存两层参数、查询时间、输出、表样本、失败信息，以及受限保存的认证材料。
<span id="10-逻辑导入先检查版本编码与写入对象"></span>

## 10 逻辑导入前先查版本、编码和写入对象

逻辑备份一导入就会执行 SQL，里面可能有 `CREATE DATABASE`、`USE`、DROP、账户、触发器、事件、DEFINER 或 GTID。命令末尾写了 `lab_site`，也约束不住文件里的全部语句。

操作顺序：先保存未改备份并检查版本、编码和权限，确认无切库语句再导入，失败就留错误，换干净副本重试。

**1. 先看备份会执行什么。** 逻辑备份导入会执行 SQL。先保存未改备份，在专用实例检查内容与所需权限；不能认为命令末尾指定 `lab_site` 就能约束文件内全部语句。备份含 CREATE DATABASE / USE 与不含这些语句时的导入方式不同，见 [MySQL SQL 备份加载](https://dev.mysql.com/doc/refman/8.4/en/reloading-sql-format-dumps.html)。

**2. 按这张表检查，再决定能不能导入。**

<details>
<summary>展开逻辑导入前检查表</summary>

| 检查项 | 处理与实际验证 |
| --- | --- |
| 生产者与恢复版本 | 固定 dump 头、程序、启动日志、镜像摘要；新排序规则、DDL、系统表与跨 MySQL/MariaDB 差异不能靠随意删掉报错项解决 |
| 字符集与排序规则 | 查备份字节、SET NAMES、字段 DDL 和客户端设置；UTF-8、utf8mb3 与 utf8mb4 不混称，乱码先检查字节和解码链 |
| 导入账户权限 | 读库权限不等于建表、触发器或 DEFINER 所需权限；给专用导入账户所需权限，导入结束改用受限读取账户 |
| 认证与传输 | 分开处理客户端插件、账户锁定、TLS 与口令；导入 SQL 还未执行的认证失败，不解释为备份损坏 |
| 数据完整性 | 保存退出状态及错误；比较表/视图/触发器清单、主键、行数、NULL、文字、金额和关联记录，不以“能打开网站”代替 |

</details>


**3. 只导入已经审查过的单库副本。** 以下仅适用于已审查为 **utf8mb4、单库、无切库语句** 的工作副本，且 `lab_site` 已在专用实例新建。127.0.0.1 与 13306 要替换为确认过的实验端点，使用交互口令提示；导入输出写到分析目录。

【仅在副本/仿真/授权环境执行】下面的导入会执行备份中的 SQL，并写入专用实例。

```bash
CASE=/work/mysql-case; OUT="$CASE/output"   # 与 §12.2 的对象约定一致
mkdir -p "$OUT"
mysql --no-defaults --protocol=TCP --host=127.0.0.1 --port=13306 \
  --user=lab_importer --password --default-character-set=utf8mb4 lab_site \
  < ./work/site.sql > "$OUT/import.stdout" 2> "$OUT/import.stderr"
import_rc=$?
printf '%s\n' "$import_rc" > "$OUT/import.exit-code"
```


**4. 看连接方式和退出状态。** 先明确连接方式。本例显式选择 TCP，避免 Unix 下 `localhost` 走 socket，导致端口选项没有作用于预期入口；见 [MySQL 连接方式](https://dev.mysql.com/doc/refman/8.0/en/connecting.html)。

再按备份的实际编码设置字符集，utf8mb4 不是任意乱码修复开关。导入失败时保留错误日志和失败副本，重试换干净副本；不要用忽略错误模式制造成功。

本节已核对生产者版本、字符集、导入账户权限，以及这份备份有没有切库语句；认证失败、字符集不一致或退出状态非零时，不把“文件能打开”写成导入完成。stdout、stderr 和退出码与表、视图、触发器清单及主键样本是同一次导入，一并留存未改备份、导入日志、失败副本，以及确认过的实验端点。

<span id="11-离线授权副本恢复访问区分产品与版本"></span>

## 11 离线授权副本：按产品与版本恢复访问

匹配版本的隔离副本因为现有认证不能查询。产品和版本还没分开，重置后的口令也不能当成历史凭据。

操作顺序：先固定账户、权限、启动参数和数据目录，按产品版本选改法，临时跳过授权只在可丢弃副本上做，做完撤掉参数。

**1. 先固定材料，优先用已有账户。** **场景与边界：** 已合法取得数据库完整材料，匹配版本的隔离副本因现有认证不能查询。先固定账户配置、权限材料、启动参数、数据目录与日志；优先使用已有受限账户或该副本本来支持的本地认证。恢复访问会改变实验账户状态，不能在唯一证据或真实业务主机执行，也不能将重置后的口令当作历史凭据。

**2. 按产品和版本选择，不要套另一家的旧脚本。**

| 产品/版本 | 应采用的判断 |
| --- | --- |
| MySQL 5.7 正式版本 | 使用对应版本支持的 ALTER USER；不要推广更早版本直接改系统表的旧脚本；可对照 [5.7 安全部署手册](https://downloads.mysql.com/docs/mysql-secure-deployment-guide-5.7-en.a4.pdf) |
| MySQL 8.0 / 8.4 | PASSWORD() 旧流程不适用；账户插件及策略决定合法修改方式，按完整版本选择流程 |
| MariaDB 10.4 起 | 账户可有多个认证插件；许多默认安装可通过 unix_socket 本地认证，mysql.user 是视图，不按 MySQL 旧脚本更新它 |


MariaDB 的本地系统身份认证不是“数据库无密码、谁都能登录”；系统账户、socket 路径和已配置插件均须匹配。保留原有多插件语义，不随意改成单一口令认证。[MariaDB 10.4 起的认证说明](https://mariadb.com/docs/server/security/user-account-management/authentication-from-mariadb-10-4)还说明 `mysql.global_priv` 与授权恢复的顺序差异。

**3. 确需跳过授权时，只动另一份可丢弃副本。** 【仅在副本/仿真/授权环境执行】若确需临时跳过授权检查，按以下程序记录操作；其中所有目录、进程、账户和配置都属于 **另一份可丢弃的实验副本**。断开副本外网及共享业务网络，确认数据库不会参与复制、集群或向外部发送事件；备份实验配置和账户状态，记录独立 datadir、socket、PID、日志路径与服务系统用户。

**4. 只停止该实验实例，再临时进入授权恢复模式。** 只停止该实验实例，由正确数据库系统用户按匹配版本临时启动授权恢复模式；采用本地 socket，并确认网络监听关闭。MySQL 8 启用 `--skip-grant-tables` 会同时禁用网络；其他版本与 MariaDB 仍需按其实际配置核验，不能假定所有端口都会自动关闭。

**5. 确认目标 socket 后，再改最小访问。** 在确认目标 socket 后，按官方顺序恢复最小访问。下列 SQL 仅是 MySQL 8.0 / 8.4 的示例，须先核对目标账户确为 `'root'@'localhost'`、插件与密码策略；不是读取分析的普通步骤。

```sql
-- 只在已确认无网络的实验授权恢复会话中执行
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY '<实验临时口令>';
```


先分产品和版本，再执行账户恢复。MySQL 先 FLUSH，之后才能重新使用账户管理语句。MariaDB 10.4 起也先 FLUSH，再按该账户的插件使用对应版本的 SET PASSWORD 等语句。

不要照旧教程改系统表，也不要把 MySQL 的系统表更新脚本套给 MariaDB。MySQL 的顺序可对照 [官方 root 访问恢复流程](https://dev.mysql.com/doc/refman/8.4/en/resetting-permissions.html)。

**6. 撤掉临时参数，用正常授权重启实验副本。** 停止临时实例，移除临时授权绕过参数及初始化脚本，以正常授权模式重启 **实验副本**；继续保持取证隔离和受限监听。核验正常登录需认证、授权范围正确、恢复参数已撤除，再用受限账户查看目标表。

**7. 失败就回到未修改副本。** 保存启动与修改日志、前后配置、账户变化和查询结果；失败时停止实验并回到未修改副本。通过这种程序读到业务记录，只证明相应恢复副本可读，不能据此声称历史口令有效或原服务可正常运行。

本节已核对产品、版本、目标账户 `'root'@'localhost'` 的插件和密码策略，以及恢复参数已经撤除；网络监听没确认关闭、MariaDB 多插件被改成单一口令，或失败后没有回到未修改副本时，停止实验。正常登录需要认证，授权范围正确，业务记录只说明这份恢复副本可读，一并留存前后配置、启动和修改日志、账户变化、查询结果，以及独立 datadir、socket、PID。

<span id="12-mysql-实战命令先选任务再选命令"></span>

## 12 先选定任务，再选 MySQL 命令

先按任务找命令：连接实例、清点表、抽样查询、业务统计、恢复、日志分析、导出或排错，每组都要说明输入材料、命令、关键字段和下一步核验，不是把全部 SQL 或管理参数堆在一起。

拿到单表文件时先核对 DDL 和表空间；拿到物理备份时先核对版本和备份链；调查删除记录时先固定日志链和事件时刻的表结构，材料分清后，再选下面的命令。

操作顺序：先选定这次要回答的问题，再从下表选一条命令，写操作单独记录改动对象。


### 12.1 命令速查与动作区别

任务已经选定，但这张表里有的命令只读，有的会写副本。普通 EXPLAIN 和 `EXPLAIN ANALYZE` 也还没分开。

操作顺序：先按问题选命令，核对结果栏里的字段，会写副本的动作单独留下对象。

**1. 按这张表选命令。**

| 需要回答的问题 | 首选命令或表达式 | 动作 | 结果应核对什么 |
| --- | --- | --- | --- |
| 材料是什么、目录在哪里 | `find`、`file`、`rg`、`sha256sum` | 读 | 完整目录、备份时间、配置引用、哈希及缺失文件 |
| 连到哪一个实例 | `mysql`、`status`、`SELECT VERSION(), @@datadir` | 读 | socket/TCP、运行版本、库、卷、账户身份 |
| 有哪些库、表、字段 | `SHOW DATABASES`、`SHOW FULL TABLES`、`DESCRIBE`、`SHOW CREATE TABLE` | 读 | 可见权限、精确DDL、引擎、字段顺序 |
| 未知字段在哪里 | `INFORMATION_SCHEMA.COLUMNS` | 读 | 限定业务库、返回所有候选表与列 |
| 指定记录/最新记录 | `SELECT`、`WHERE`、`ORDER BY`、`LIMIT` | 读 | 稳定主键、并列、NULL、当前状态和历史状态 |
| 人数、订单数、金额 | `COUNT`、`COUNT(DISTINCT ...)`、`SUM`、`AVG` | 读 | 分母、状态、时间、软删、金额单位 |
| 分用户/分日统计 | `GROUP BY`、`HAVING`、`CASE` | 读 | 分组键、过滤阶段、时区和并列排名 |
| 跨表身份/资金链 | `JOIN`、`LEFT JOIN`、`EXISTS` | 读 | 关联键、孤立行、一对多倍增 |
| 层级和并列排名 | `WITH RECURSIVE`、`ROW_NUMBER`、`DENSE_RANK` | 读 | MySQL 8、根层、环路、不同排名定义 |
| 时间、地址、编码 | `FROM_UNIXTIME`、`CONVERT_TZ`、`INET_NTOA`、`HEX` | 读 | 原值、单位、时区、字符集及应用写入逻辑 |
| 逻辑备份/结果导出 | `mysqldump`、`mysql --batch`、`SELECT ... INTO OUTFILE` | 读+写 | 一致性、输出位置、编码、错误、DDL与样本 |
| 完整目录无法启动 | `mysqld`、错误日志、`innodb_force_recovery` | 写 | 匹配版本、全新副本、恢复等级与实际可读范围 |
| 单表/旧引擎材料 | `mysqlfrm`、`ibd2sdi`、`DISCARD/IMPORT TABLESPACE`、`myisamchk` | 写 | 工具年代、DDL、引擎、密钥及表空间条件 |
| 删除记录/时间点状态 | `mysqlbinlog`、位置/事务筛选、备份+完整日志回放 | 读+写 | 显示与执行分开，事务边界、列序、日志缺口 |
| 长查询和锁等待 | `EXPLAIN`、`SHOW FULL PROCESSLIST`、`SHOW ENGINE INNODB STATUS` | 读 | 本次恢复实例状态，不当作历史活动日志 |
| 查询身份/授权 | `USER()`、`CURRENT_USER()`、`SHOW GRANTS`、`SHOW CREATE USER` | 读 | 提供身份与匹配身份、角色和访问范围 |


**2. 执行前先分清读和写。** **执行前先分动作。** `SELECT/SHOW` 读取恢复实例；`SET SESSION` 只改当前会话。启动数据库、导入、DDL、账户修改及 prepare/repair/replay 会写副本，需要单独记录改动对象。【仅在副本/仿真/授权环境执行】启动、导入、改账户、prepare、repair 和 replay 只在副本上做。

只读 SQL 不保证数据库进程不写缓存、日志或元数据，原目录仍须保全。普通 EXPLAIN 用于查看计划；`EXPLAIN ANALYZE` 会实际执行查询，两者分开使用。

本节已核对这次要回答的问题，以及表里对应的命令和应核对的字段；命令会写副本，或 `EXPLAIN ANALYZE` 会真正执行查询时，先记下改动对象，不把计划当成历史活动。`SELECT/SHOW` 的结果和 `SET SESSION` 的会话改动已经分开，一并留存输入材料、命令、关键字段，以及写操作的对象记录。原目录另行保全。

### 12.2 后续命令中的对象约定

后面的命令还没约定哪一份是只读材料、哪一份是实验库。工具版本输出来自分析机，还是来自历史服务器，也还没分开。

操作顺序：先定目录、实验库和读取账户，记下三个客户端的版本，每次重要操作分别留 stdout、stderr 和 exit。

**1. 先按约定准备目录。** 默认 Bash/Kali。`/mnt/evidence`为只读材料，`/work/mysql-case`为分析目录；`lab_site`为**另建的实验业务库**，`case_reader`为实验读取账户。表名和状态值是讲解模板，先通过DDL和代码确认实际对象，再替换。练习材料使用独立库`forensic_lab`，见§24。

```bash
CASE=/work/mysql-case
EVIDENCE=/mnt/evidence
OUT="$CASE/output"
SOCKET="$CASE/run/mysql.sock"
mkdir -p "$OUT" "$CASE/run" "$CASE/tmp"
mysql --version
mysqldump --version
mysqlbinlog --version
```


**2. 版本输出要和历史版本分开。** 版本输出表示分析工具/正在运行的恢复服务器，历史版本另从原程序、镜像、错误日志、备份头和配置互证。命令中的`$?`只对应紧邻的上一命令；每次重要操作都分别记录stdout、stderr和exit。

本节已核对只读材料目录、分析目录、实验库 `lab_site` 和读取账户 `case_reader`；表名还是讲解模板、历史版本还没从原程序或备份头互证时，不把工具版本写成历史版本。每次重要操作都有自己的 stdout、stderr 和 exit；`$?` 只解释紧邻的上一条命令，一并留存目录约定、三个客户端的版本输出。练习库 `forensic_lab` 留到 §24。

<span id="13-数据目录配置版本与日志位置"></span>

## 13 定位数据目录、配置、版本与日志

配置、数据目录和日志位置还没对上。离线文件和已经启动的恢复副本，也不能记成同一次采集。

操作顺序：先离线找出配置和数据文件，再在已有恢复副本上看进程和端口，容器映射单独记一层。


### 13.1 离线清点

配置文件和 `ibdata1` 还散在材料里。版本不能靠文件名、目录名或文件大小猜。

操作顺序：先按名字找出配置和数据文件，再做哈希和目录清单，网站连接按启动时的 profile 解释。

**1. 按实际已经定位的目录列文件。** 配置路径不存在就记缺失，不假设它一定在示例位置。

```bash
find "$EVIDENCE" -type f \( -name 'my.cnf' -o -name 'my.ini' \
  -o -name 'ibdata1' -o -name 'mysql.ibd' -o -name '*.ibd' \
  -o -name '*.frm' -o -name '*.MYD' -o -name '*.MYI' \
  -o -name 'xtrabackup_info' -o -name 'xtrabackup_checkpoints' \) -print
rg -n 'datadir|socket|port|bind[-_]address|log[-_]error|log[-_]bin|binlog|innodb|keyring|!include' \
  "$EVIDENCE/etc/my.cnf" "$EVIDENCE/etc/mysql"
# 按实际已定位目录替换，不假设配置路径必定存在
DBDIR="$EVIDENCE/path/to/mysql-data"
find "$DBDIR" -type f -print0 | sort -z | xargs -0 -r sha256sum > "$OUT/input-files.sha256"
file "$DBDIR/ibdata1"
find "$DBDIR" -maxdepth 2 -type f -printf '%P\t%s\t%TY-%Tm-%TdT%TH:%TM:%TS\n' \
  > "$OUT/file-inventory.tsv"
```


**2. 先有完整目录，再判断版本。** 不要用文件名、目录名或 `ibdata1` 大小推断版本号。

MySQL 8 的 `mysql.ibd` 属于事务数据字典，不按普通业务单表处理。redo 布局也随 8.x 版本变化，保留整目录，不只拷 `.ibd`。

**3. 文件时间先标分析环境的时区。** 记录时间时注明分析环境时区：GNU `find -printf` 的显示受它影响，文件时间还可能来自复制或备份，不能直接当数据库事件时间。

**4. 网站连接材料按实际启动环境解释。** 网站连接材料可在`.env`、PHP配置、`application.yml`及活动profile、JDBC URL、宝塔站点配置中查找。先确定启动时激活的profile/环境，再解释库名、端口和账户；输出若含口令，单独受限保存，不作为公开报告附件。

本节已核对实际 datadir、配置里的路径，以及 MySQL 8 数据字典所在的整目录；配置路径不存在、profile 还没确定，或文件时间只来自复制时，分别写明。哈希清单和 `file` 结果来自同一 `DBDIR`；版本不是由 `ibdata1` 大小推出来的，一并留存输入哈希、文件清单、时区说明，以及含口令输出的受限副本。

### 13.2 已启动的恢复副本：进程与容器映射

恢复副本已经在跑，但进程、socket 和发布端口还没分开。这些命令看的是这次仿真，不是原主机。

操作顺序：先看 mysqld 进程和监听，服务名按实际部署选一个，容器再查挂载和端口。

**1. 只清点已经建立的仿真或恢复环境。** 以下只在已经建立的仿真/恢复环境清点，不对原主机启动服务。

【仅在副本/仿真/授权环境执行】下面查询当前恢复环境。服务名可能是 mysqld 或 mariadb，依据实际部署选一个，不批量启停。

```bash
ps -eo pid,user,args | grep '[m]ysqld'
ss -lntp
ss -lxnp
systemctl status mysql --no-pager
systemctl cat mysql
# 服务名可能是mysqld或mariadb，依据实际部署选一个，不批量启停
```


**2. 材料来自 Docker 时先查映射。** 如果材料来自Docker，先查映射而非猜端口：

```bash
docker ps -a --no-trunc
docker inspect DB_CONTAINER --format '{{json .Mounts}}'
docker inspect DB_CONTAINER --format '{{json .NetworkSettings.Ports}}'
```


`DB_CONTAINER`须替换为已识别的恢复容器。宿主机13306发布到容器3306时，两者各代表一层；配置中的localhost也相对于执行应用的主机/容器解释。完整容器操作集中见[Docker网络与Compose](/knowledge/docker-evidence-05/)。

本节已核对这次恢复进程的用户、参数、监听，以及容器挂载和端口发布；服务名不确定或 `DB_CONTAINER` 还没替换成已识别容器时，不猜端口，也不对原主机启停。宿主机发布端口和容器端口各是一层；localhost 相对于执行应用的那一台来解释，一并留存进程、`ss`、单元输出，以及 Mounts 和 Ports 的 inspect。

<span id="14-mysql-客户端连接参数与交互操作"></span>

## 14 连接 mysql 客户端并区分参数与交互命令

客户端还没决定走 TCP 还是 socket。参数和交互命令也还没和服务器上的 SQL 分开。

操作顺序：先写明端点，再查参数会不会改传输或导出，交互记录不写成目标服务器的历史。


### 14.1 明确TCP或socket

要连的是实验实例，但 Unix 下 `localhost` 通常走 socket，只加 `-P` 改不了这一点。客户端还可能去读 `.mylogin.cnf`。

操作顺序：先显式选择 TCP 或 socket，再看会不会读登录配置，TLS 按端点证书设置。

**1. 两条连接分别写明协议。**

```bash
# 本地实验TCP端点；-P是端口，-p是交互口令
mysql --no-defaults --protocol=TCP -h 127.0.0.1 -P 13306 \
  -u case_reader -p --default-character-set=utf8mb4 lab_site

# 独立实验socket，避免连到默认系统实例
mysql --no-defaults --protocol=SOCKET --socket="$SOCKET" \
  -u case_reader -p --default-character-set=utf8mb4 lab_site
```


要走 TCP，就显式选 TCP；Unix 下 `localhost` 通常走 socket，仅加 `-P` 不足以改变这一点。

**2. 先看帮助，再决定读不读登录路径。** 先看客户端帮助，再安排配置读取选项。`--no-defaults` 放在前面的选项文件控制位置，但 MySQL 客户端仍可能读取 `.mylogin.cnf`。支持 `--no-login-paths` 的版本可再禁止 login-path 读取。MariaDB 和旧 MySQL 支持项不同，不整套照搬。

```bash
# 已核对支持该选项的现代MySQL客户端
mysql --no-defaults --no-login-paths --protocol=TCP -h 127.0.0.1 -P 13306 \
  -u case_reader -p --execute='SELECT VERSION(), DATABASE(), USER(), CURRENT_USER();'
```


**3. TLS 和排错默认项分开。** TLS选项按恢复端点证书与客户端能力设置；远程需验证证书时使用相应CA和`--ssl-mode=VERIFY_IDENTITY`，别把关闭TLS、开放root或更换认证插件当连接排错默认项。SSH转发的两层身份和主机解释见本页§09。

本节已核对这次走的是 TCP 还是 socket，以及客户端有没有读取 `.mylogin.cnf`；选项在 MariaDB 或旧 MySQL 上不存在时，不整套照搬；证书没验证时不把关闭 TLS 当成默认排错。`--protocol`、主机和端口或 `--socket` 与 `SELECT VERSION(), DATABASE(), USER(), CURRENT_USER()` 是同一次连接，一并留存实际端点、客户端帮助里确认过的选项，以及 TLS 所用的 CA。

### 14.2 高频客户端参数

参数很多，`-P` 和 `-p` 的大小写还没对上，导出格式也容易被看错。限制都在表的右侧。

操作顺序：先查参数对应哪一种端点或输出，再看判读与限制，对不上就停，不靠加大超时或 `--force` 往下走。

**1. 按这张表选参数。**

| 参数 | 用途 | 判读与限制 |
| --- | --- | --- |
| `-h/--host`、`-P/--port`、`--protocol`、`-S/--socket` | 指定端点与传输 | -P/-p区分大小写；先确认实际实例 |
| `-u/--user`、`-p/--password` | 提供账户，省略口令值则提示输入 | `-p SECRET`不等于传入口令；示例不内嵌真实口令 |
| `--default-character-set` | 客户端连接字符集 | 按材料选择；utf8mb4不修复任意乱码 |
| `-e/--execute` | 执行给定SQL后退出 | 多语句用`;`，保留SQL原件；Shell引号需正确 |
| `-B/--batch` | 制表符分列、逐行输出 | 默认转义特殊字符，不是CSV |
| `-N/--skip-column-names` | 去掉列标题 | 正式导出通常保留标题；纯ID列表才按需去掉 |
| `-r/--raw` | 禁用非表格输出的特殊字符转义 | 字段内TAB/换行会破坏直接按行/列切分 |
| `-q/--quick` | 逐行读取结果而非先缓存全部 | 适合大结果集，长查询仍要看错误与完整性 |
| `-t/--table`、`--vertical` | 横向表格/纵向展示 | 展示格式，不改变数据库字段类型 |
| `--binary-as-hex` | 将二进制值显示为十六进制 | 版本支持先检查；SQL的HEX更便于保存明确字段 |
| `--show-warnings` | 每个语句后显示警告 | 截断、隐式转换、排序规则错误不可忽略 |
| `--connect-timeout`、`--max-allowed-packet` | 连接超时/大字段传输 | 客户端和服务端限制分别核对，不靠增大值跳过坏数据 |
| `--skip-reconnect` | 连接丢失后不自动重连 | 避免事务快照和会话参数悄然丢失；重新连接须重建上下文 |
| `--local-infile=0` | 不启用客户端LOCAL文件上传 | 普通读取和SQL导入通常无需LOCAL能力 |
| `--force` | SQL报错后继续 | 取证导入默认不使用；零散结果不作为完整导入证明 |


**2. 限制对不上时回到右侧一列。** `-p SECRET` 不等于传入口令，`--batch` 不是 CSV，`--force` 不是取证导入的默认项。客户端和服务端的 `--max-allowed-packet` 分开核对，不靠增大值跳过坏数据。

本节已核对端点、账户、字符集和输出格式各自用了哪个参数；参数大小写、转义或版本不支持 `--binary-as-hex` 时，按表里的限制停住。正式导出仍保留列标题；特殊字符没有被 `-r/--raw` 切坏，一并留存实际使用的客户端参数，以及警告和连接丢失后的重连记录。

### 14.3 交互命令不是服务器SQL

交互会话里的 `status`、`tee` 和 `source` 还没和发到服务器的 SQL 分开。分析机上的 `.mysql_history` 也不是目标服务器的历史。

操作顺序：先分清缓冲、执行和记录，`source` 之前审查文件，重构后新增的历史与原件分开。

**1. 下面这些是客户端交互。**

```text
status
use lab_site
tee /work/mysql-case/output/session-001.txt
SHOW CREATE TABLE orders\G
pager less -S
nopager
SHOW WARNINGS;
SELECT id, order_no FROM orders ORDER BY id LIMIT 20;
print
clear
source /work/mysql-case/work/reviewed-query.sql
notee
quit
```


**2. 分清执行和清空缓冲。** `\G`执行并纵向展示；`;`正常执行，`\c`/`clear`清空未执行缓冲，`\p`/`print`显示缓冲。已执行的语句不会被clear撤销。

**3. 会话记录追加到新文件。** `tee`/`\T`记录交互语句与屏幕结果且**追加**；每轮使用新文件名，`notee`结束。批处理另用stdout/stderr重定向。

**4. 执行文件前先审查。** `pager`在Unix交互模式可用，Windows不作为同样步骤；`source`/`\.`执行文件内语句，须先审查文件，不是只读打开。【仅在副本/仿真/授权环境执行】`source` 会执行文件里的语句，只对已审查的实验对象使用。

**5. 分隔符只改变客户端分句。** `delimiter //`常用于定义含分号的例程，结束后恢复`delimiter ;`；它改变客户端分句，不改变SQL语法或权限。

**6. 客户端历史不是服务器历史。** 会话记录与分析机`.mysql_history`不代表目标服务器历史，尤其重构后新增历史应与原件区分。

本节已核对哪些输出是客户端缓冲或 `tee` 记录，哪些语句已经发给服务器；`source` 的文件还没审查，或 Windows 上没有同等 `pager` 步骤时，分别写明。每轮 `tee` 使用新文件名；已执行语句没有被 `clear` 撤销，一并留存新的会话记录文件。分析机 `.mysql_history` 与目标服务器历史分开存放。

<span id="15-实例账户变量状态与只读会话"></span>

## 15 核对实例、账户、变量、状态与只读会话

连接已经建立，但版本、匹配账户、变量和这次进程的 Uptime 还混在一起。多表读取也还没有同一份快照。

操作顺序：先查身份、变量和本次状态，再在同一连接上开只读快照，断开就重新建快照，不把两次结果并成一份。

**1. 先跑状态查询，报错也留下。**

```sql
SELECT VERSION() AS server_version, @@version_comment AS product,
       @@hostname AS host, @@port AS port, @@datadir AS datadir,
       DATABASE() AS current_db, USER() AS supplied_identity,
       CURRENT_USER() AS matched_account, CONNECTION_ID() AS session_id;
SHOW GRANTS FOR CURRENT_USER;
SHOW CREATE USER CURRENT_USER;
-- MySQL8角色，5.7不套用
SELECT CURRENT_ROLE();
SHOW VARIABLES WHERE Variable_name IN
 ('sql_mode','time_zone','system_time_zone','character_set_server',
  'collation_server','lower_case_table_names','innodb_page_size',
  'innodb_file_per_table','binlog_format','binlog_row_image',
  'gtid_mode','read_only','super_read_only','event_scheduler',
  'secure_file_priv','local_infile','log_error','general_log',
  'general_log_file','slow_query_log','slow_query_log_file');
SHOW GLOBAL STATUS LIKE 'Uptime';
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW FULL PROCESSLIST;
SHOW ENGINE INNODB STATUS\G
```


`SHOW CREATE USER`含认证材料、角色和部分SHOW命令受权限/版本限制；报错须记录，未看到不代表没有对象。Uptime、PROCESSLIST、InnoDB状态反映本次恢复进程及当前时刻；重启之后的值不用于证明历史开机、连接或攻击行为。`SHOW GLOBAL STATUS`与`SHOW SESSION STATUS`范围不同。

**2. 多表读取时建立同一份只读快照。** 在支持只读事务的MySQL 5.7/8.x，读取InnoDB多表时可建立同一快照：

【仅在副本/仿真/授权环境执行】下面的 `SET SESSION` 和只读事务只作用于当前实验连接。

```sql
SET SESSION time_zone = '+00:00';
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
SELECT COUNT(*) FROM lab_site.orders;
SELECT COUNT(*) FROM lab_site.users;
COMMIT;
```


**3. 保持同一连接。** 保持同一连接，在适用的事务引擎上读取同一快照。连接断开就重新建立快照，并给新一轮输出记新的时点，不能把跨会话结果并成一份。

**4. 快照盖不住的对象另标时点。** MyISAM、DDL、其他实例及文件日志不在这个快照范围内。READ ONLY 也不表示整个服务器绝不写盘。本机 5.5 样本没有验证这里的现代 READ ONLY 语法。

在同一连接、同一事务中完成相互比较的表查询，并保留开始和结束位置；客户端自动重连、手动换连接或事务外的导出不自动继承该快照。先用 DDL 确认涉及表的引擎，其他引擎的结果另标采集时点。`COMMIT` 在这里结束只读事务，不表示服务端从未产生日志或缓存写入。

本节已核对本次服务器版本、匹配账户、datadir，以及同一只读快照里的多表计数；权限报错、MyISAM 或自动重连导致快照中断时，不把未看到写成没有对象，也不把 Uptime 写成历史开机时间。`SHOW GLOBAL STATUS` 和 `SHOW SESSION STATUS` 的范围已经分开；比较查询留有开始和结束位置，一并留存身份查询、变量清单、报错，以及新一轮快照的时点。本机 5.5 未验证的语法单独注明。

<span id="16-库表ddl字段索引与未知对象定位"></span>

## 16 从目录查到库表、DDL、字段与未知对象

库和表还停在目录名上，未知字段也不该对每张表盲目 LIKE。下面先取精确结构，再查元数据。

操作顺序：先列出库、表和 DDL，再在元数据里找候选列，没有外键定义就改查索引、代码和稳定 ID。


### 16.1 从目录到精确结构

还不知道有哪些库、表、视图和例程。`SHOW TABLE STATUS` 里的行数对 InnoDB 通常只是估算。

操作顺序：先列出对象，再取 DDL、列和索引，名称确认后再取例程定义。

**1. 按这个顺序从目录走到定义。**

```sql
SHOW DATABASES;
USE lab_site;
SHOW FULL TABLES;
SHOW TABLE STATUS LIKE 'orders'\G
DESCRIBE orders;
SHOW FULL COLUMNS FROM orders;
SHOW CREATE TABLE orders\G
SHOW INDEX FROM orders;
SHOW CREATE VIEW view_name\G
SHOW TRIGGERS FROM lab_site;
SHOW EVENTS FROM lab_site;
SHOW PROCEDURE STATUS WHERE Db = 'lab_site';
SHOW FUNCTION STATUS WHERE Db = 'lab_site';
-- 上一步确认名称和类型后，再取定义
SHOW CREATE PROCEDURE procedure_name\G
SHOW CREATE FUNCTION function_name\G
SHOW CREATE TRIGGER trigger_name\G
SHOW CREATE EVENT event_name\G
```


**2. 占位名称换成实际对象后再解释。** 视图/触发器/事件/例程名称是占位符，逐个替换为实际对象。清点这些对象可发现软删逻辑、费用计算或异步写入；`DEFINER`是定义上下文，不自动等于某次执行者。`SHOW TABLE STATUS.Rows`或`TABLE_ROWS`对InnoDB通常为估算；求精确数量用COUNT，且说明快照与范围。

本节已核对实际库、表、视图、触发器、事件和例程的名称与 DDL；名称还是占位符，或 Rows 只是估算时，不把 `DEFINER` 写成某次执行者，不用估算值当精确行数。`SHOW CREATE` 的字段顺序和索引来自同一对象；精确数量另有 COUNT 和快照范围，一并留存对象清单、DDL、索引，以及软删、费用或异步写入相关的定义。

### 16.2 查元数据，不对每张表盲目LIKE

字段可能在很多表里，还不该逐表 LIKE。元数据查询也没有一份放在数据目录里的 INFORMATION_SCHEMA 库文件。

操作顺序：先限定 `lab_site` 查表和列，再用列名模式找候选，外键没有时改查代码和稳定 ID。

**1. 先查表、列和引用。**

```sql
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE, ENGINE, TABLE_ROWS,
       DATA_LENGTH, INDEX_LENGTH, TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'lab_site'
ORDER BY TABLE_NAME;

SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, COLUMN_TYPE,
       IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, COLLATION_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'lab_site'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'lab_site'
  AND (COLUMN_NAME LIKE '%phone%' OR COLUMN_NAME LIKE '%order%'
       OR COLUMN_NAME LIKE '%deleted%' OR COLUMN_NAME LIKE '%income%')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'lab_site' AND REFERENCED_TABLE_NAME IS NOT NULL;
```


**2. 看权限和跨版本的视图名。** 数据库可见范围受权限控制；元数据没有物理目录对应的INFORMATION_SCHEMA库文件。没有外键定义不代表没有业务关系，需结合索引、代码JOIN和稳定ID。跨版本表空间元数据名称不同：5.7常用`INNODB_SYS_TABLES`，8.x常用`INNODB_TABLES`；先查实际视图列，不直接移植旧查询。

本节已核对 `lab_site` 里的表、列顺序、候选字段名，以及已经定义的外键；权限看不到的库，或 5.7 与 8.x 的表空间视图名不同时，先查实际列，不移植旧查询。候选列来自 `INFORMATION_SCHEMA.COLUMNS`，业务关系还有索引、代码 JOIN 或稳定 ID，一并留存表清单、列清单、引用关系和权限报错。

<span id="17-select实战条件排序去重与异常记录"></span>

## 17 用 SELECT 抽样、排序、去重并标出异常

条件、排序和去重还没定，大表也不该先做全量计算。孤立行要不要留下，放到下一节。

操作顺序：先抽样再写条件，看执行计划和警告，空值、日期边界和通配符按字段语义解释。


### 17.1 先抽样，再做全量计算

在恢复实例上核对时，先抽少量真实行确认字段与排序，再用稳定主键分段，而不是不断加大 `OFFSET`。要看访问路径时先跑普通 `EXPLAIN` 并读 `SHOW WARNINGS`；`type/key/rows/filtered/Extra` 里的 `rows/filtered` 是优化器估算，不是命中数量，实际数量仍用 COUNT 核对。不要为提速给恢复业务库建索引；`EXPLAIN ANALYZE` 会实际执行查询，与普通 `EXPLAIN` 分开使用。判读边界按原语义留：`= NULL` 不用于判断空值，`IS NULL` 与空字符串、数字 0、字符串 '0' 分开；`BETWEEN` 两端包含，日期优先半开区间 `>=开始 AND <次日/下一边界` 以覆盖小数秒；LIKE 的 `%/_` 按 sql_mode/ESCAPE 转义，字面符号不要当通配符；排序规则可能忽略大小写/重音，需要区分原始字节时比较 HEX。详见[字段语义与检索条件](/knowledge/fic-case-05/#03-表结构字段语义和检索条件)。

抽样行、筛选条件、稳定排序，以及执行计划里的索引和 Extra；`rows/filtered` 只是估算，实际数量用 COUNT 核对过；“最后一行”或“第二高”还没定义口径时不做全量结论；查询 SQL、`SHOW WARNINGS` 和半开时间边界。

### 17.2 EXISTS与孤立关联

孤立行（关联表对不上的订单或用户）要先分原因：历史删除、其他租户、同步缺口或恢复不完整都可能造成，不能仅凭 JOIN 失败认定伪造。有"至少一笔符合口径"的用户用 `EXISTS`，不会被多笔订单重复放大；没有匹配账户的订单用 `LEFT JOIN` 留下，而不是丢掉。使用 `NOT IN` 前先查子查询是否含 NULL，缺失关联常用 `NOT EXISTS` 表达。查询写法与 NULL 陷阱见[统计口径](/knowledge/fic-case-05/#05-聚合统计与多表关联)。

至少有一笔符合口径订单的用户，以及账户表对不上的订单主键；子查询含 NULL，或孤立行还没区分删除、租户、同步和恢复缺口时，不下伪造结论；两条 SQL 和孤立订单的主键清单。

<span id="18-聚合排名与多表资金统计"></span>

## 18 聚合、排名与多表资金统计先各自汇总

人数、金额和跨表资金还没定口径。一张明细直接 JOIN 另一张明细，金额会被乘重复。

操作顺序：先说清 COUNT、SUM、AVG 在数什么，再各自聚合后关联，去重用业务键，不靠金额相同来消掉倍增。


### 18.1 COUNT/SUM/AVG：明确数量和分母

数量与分母的核验要点：`COUNT(*)` 数行，`COUNT(列)` 忽略 NULL，`COUNT(DISTINCT 用户ID)` 是该口径下的去重账户、不等于自然人数；`SUM/AVG` 通常忽略 NULL，空集合 SUM 为 NULL，AVG 分母是非 NULL 数量。业务明确允许"没有记录即 0"时才用 `COALESCE`，不把未知收入默认为 0。金额优先按原 `DECIMAL` 或已确认的最小货币单位分币种合计，`ROUND` 只用于写明口径的展示。`WHERE` 筛行、`HAVING` 筛聚合组；遇 `ONLY_FULL_GROUP_BY` 报错先改 SQL，不关模式任意取一行。地区用稳定编码，不用 `SUBSTRING(address,1,2)` 猜省份。完整统计口径与示例见[统计口径](/knowledge/fic-case-05/#05-聚合统计与多表关联)。

行数、非空数量、去重账户、金额合计，以及 WHERE 和 HAVING 各自筛的对象；币种、NULL 是否计入分母，或地区码还没规范化时，不把未知收入写成 0；聚合 SQL、状态条件、时间范围和金额单位。

### 18.2 JOIN倍增：先各自聚合，再关联

一条明细直接 JOIN 另一条明细会把两侧金额乘重复（例如 2 笔充值 × 3 笔提现 = 6 行）。正确做法是先按用户各自聚合，再 `LEFT JOIN` 回主表；比率用 `NULLIF` 让零分母成为 NULL，保留"无充值"类别，不硬填 0。单笔订单有多条明细时先回到订单主键粒度。**不要用 `SUM(DISTINCT amount)` 消除倍增**——两笔不同订单金额相同会被合并；去重应基于订单 ID/业务唯一键，并比较关联前后的 COUNT 与主键集合。示例与陷阱见[统计口径](/knowledge/fic-case-05/#05-聚合统计与多表关联)。

按用户汇总后的充值和提现，以及按订单主键汇总的金额；赠送、手续费、退款、冻结或状态还没核对时，不把充值减提现写成平台利润或当前余额；关联前后的 COUNT 和主键集合已经比较，零分母是 NULL 不是 0。
<span id="19-时间ip字符串二进制与json字段"></span>

## 19 判读时间、IP、字符串、二进制与 JSON 字段

时间、地址、号码和 JSON 还是原始列。单位、时区和类型没确认之前，不能直接转换。

操作顺序：先留时间原值和会话时区，再处理地址与号码的原始字节，JSON 只在确认类型和版本后展开。


### 19.1 时间原值、会话时区和单位

先记下 `@@session.time_zone`、`@@global.time_zone`、`@@system_time_zone` 三个字段，再判断单位：按列类型、应用写入代码和数量级确认秒、毫秒还是微秒，不只按位数判断。`FROM_UNIXTIME`/`UNIX_TIMESTAMP` 受会话时区影响，`TIMESTAMP` 存取会做会话时区转换、`DATETIME` 自身不带时区；`SET SESSION time_zone='+00:00'` 不改写已存进去的本地 DATETIME。`CONVERT_TZ` 返回 NULL 时先查参数和命名时区表是否已加载，MySQL 5.7 与 8.x 的时间范围、精度分别核对。按日分组的半开区间与转换示例见[统计口径](/knowledge/fic-case-05/#05-聚合统计与多表关联)。

时间原值、列类型、会话时区，以及秒/毫秒/微秒中的哪一种；`CONVERT_TZ` 为 NULL 或 5.7 与 8.x 的时间范围还没分开时，不把位数当成单位；三个时区字段、半开区间，以及原值与换算 SQL。

### 19.2 IPv4、号码和原始字节

按列类型转换：IPv4 数值用 `INET_NTOA` 显示、`INET_ATON` 反向核对；受支持版本上的 IPv6 用 `INET6_NTOA`/`INET6_ATON`，不拿任意 BLOB 当地址。号码按字符串保留前导零、国际前缀和原格式，不额外加规则改变样本范围；`LENGTH` 数字节、`CHAR_LENGTH` 数字符，中文列两者不同。二进制列先留 `HEX`/`OCTET_LENGTH` 原值再转换，隐式数值转换会把异常文字误作 0 并产生警告。字段判读与转换前提见[字段语义](/knowledge/fic-case-05/#03-表结构字段语义和检索条件)。

IPv4 或受支持版本上的 IPv6 文本、号码原串，以及字节长度和字符数；列不是地址、版本不支持 INET6，或隐式转换出现警告时，保留原值和 HEX，不把异常文字当成 0；原值、`HEX` 结果和警告。

### 19.3 JSON：仅在确认类型及版本后展开

列看起来像 JSON，但类型和版本还没确认。日志里的一段字符串，也不一定是 JSON 列。

操作顺序：先确认 5.7 或 8.x，用构造常量看函数结果，再替换成实际列。

**1. 版本确认后再展开。** MySQL 5.7支持JSON类型及相关函数；8.x增加更多展开能力。以下构造常量可验证操作语义，业务数据替换为实际列：

```sql
SELECT JSON_VALID('{"action":"login","device":{"id":"LAB-1"}}') AS valid_json;
SELECT JSON_UNQUOTE(JSON_EXTRACT(
  '{"action":"login","device":{"id":"LAB-1"}}','$.device.id')) AS device_id;
SELECT JSON_KEYS('{"a":1,"b":2}'), JSON_LENGTH('[1,2,3]');
-- MySQL8：把数组展开为关系行
SELECT j.item_id FROM JSON_TABLE('[{"id":1},{"id":2}]','$[*]'
  COLUMNS(item_id INT PATH '$.id')) AS j;
```


**2. 把几种空和引号分开。** 区分SQL NULL、JSON null、缺路径、空字符串和非法JSON；日志中的字符串也不一定是JSON列。`JSON_EXTRACT`可能保留JSON引号，`JSON_UNQUOTE`用来取得标量文本；不直接用REPLACE去掉所有引号。JSON数据改变函数不是读取步骤。

本节已核对版本支持的 JSON 函数，以及路径上取出的标量文本；SQL NULL、JSON null、缺路径、空字符串和非法 JSON 还没分开时，不把日志字符串当成 JSON 列。`JSON_VALID` 的结果和 `JSON_UNQUOTE(JSON_EXTRACT(...))` 来自已确认的类型；没有用 REPLACE 去掉引号，一并留存版本、路径、构造常量与实际列的对应关系。

<span id="20-mysql-8窗口排名最新一条与会员层级"></span>

## 20 MySQL 8 的窗口排名、最新一条与会员层级

这些模板要求支持窗口函数/CTE的MySQL8环境；MySQL 5.7 不支持，改用聚合、关联或导出后脚本，并保留同样口径。

本节没有把 MariaDB 的功能起始版本等同 MySQL。

操作顺序：先确认服务器是 MySQL 8，再套排名或递归模板，5.7 就换聚合、关联或导出后的脚本。


### 20.1 “第N名”与“第N个不同值”

要的是第二条记录，还是第二个不同的累计值，现在还没分开。只要 `MAX(event_at)` 也拿不回那一行的 IP。

操作顺序：先给排序一个确定次序，ROW_NUMBER 取第几条，DENSE_RANK 取第几个不同值，最新一条按分区取整行。

**1. 第二条记录和第二个不同值分开取。**

```sql
WITH totals AS (
  SELECT user_id, SUM(amount) AS total
  FROM lab_site.orders WHERE status='paid' AND deleted_at IS NULL GROUP BY user_id
), ranked AS (
  SELECT user_id,total,
         ROW_NUMBER() OVER(ORDER BY total DESC,user_id) AS ordinal,
         DENSE_RANK() OVER(ORDER BY total DESC) AS value_rank
  FROM totals
)
SELECT * FROM ranked WHERE ordinal=2 OR value_rank=2 ORDER BY total DESC,user_id;
```


要第二条记录，用 ROW_NUMBER，并给排序一个确定次序。要第二个不同累计值的所有并列用户，用 DENSE_RANK。

DENSE_RANK 的 ORDER BY 不要额外加入唯一 ID，否则原本金额相同的用户会被拆开。RANK 还会跳号，它与 DENSE_RANK 不是同一口径。

**2. 每个用户的最新一条要整行。**

```sql
WITH latest AS (
  SELECT id,user_id,event_at,ip_num,
         ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY event_at DESC,id DESC) AS rn
  FROM lab_site.login_events
)
SELECT id,user_id,event_at,INET_NTOA(ip_num) AS ip FROM latest WHERE rn=1 ORDER BY user_id;
```


MAX(event_at)只有时间值，不直接返回那一行的IP；5.7可先求MAX时间再关联并处理并列，或按相同排序导出核验，不随意选非分组列。

本节已核对确定次序下的第 N 条记录，或第 N 个不同累计值上的全部并列用户；MySQL 5.7 没有窗口函数时，改用聚合或导出后脚本，不随意选非分组列当 IP。DENSE_RANK 的排序没有混入唯一 ID；RANK 的跳号没有当成同一口径，一并留存排序键、并列规则，以及 5.7 替代查询的输出。

### 20.2 下线层级：根为第1层，记录环路限制

根用户的下线还没展开。根是第 1 层，环和递归上限也还没记。根 ID 是构造示例，不是题目答案。

操作顺序：从指定根向下递归，路径里挡住已经出现的 ID，达到上限就先查环、重复和孤立节点。

**1. 根为第 1 层，并记录路径。**

```sql
WITH RECURSIVE tree AS (
  SELECT id,parent_id,1 AS depth,CAST(CONCAT('/',id,'/') AS CHAR(4096)) AS path
  FROM lab_site.users WHERE id=1
  UNION ALL
  SELECT u.id,u.parent_id,t.depth+1,CONCAT(t.path,u.id,'/')
  FROM lab_site.users AS u JOIN tree AS t ON u.parent_id=t.id
  WHERE t.depth<100 AND LOCATE(CONCAT('/',u.id,'/'),t.path)=0
)
SELECT id,parent_id,depth,path FROM tree ORDER BY depth,id;
```


**2. 达到上限时先查为什么停。** 根ID是构造示例，不是题目答案。100是实验上限，不代表历史树最多100层；达到上限或受`cte_max_recursion_depth`限制时记录截断，先核对环、重复ID、孤立节点、路径宽度和ID范围。路径的锚定类型应容纳递归追加，CHAR长度与字符集限制须按真实深度调整。找最大层级可以在同一CTE的最终查询使用MAX(depth)；统计后代时明确是否排除根，避免人工添加根节点造成层数偏移。

本节已核对根为第 1 层的路径和深度，以及有没有在上限处截断；出现环、重复 ID、孤立节点或路径宽度不够时，先记下截断，不把 100 写成历史最大层数。同一 CTE 的 MAX(depth) 给出本次可达结果的最大深度；根是否纳入统计由查询条件说明，不能从最大值倒推。`cte_max_recursion_depth`、实验深度上限及截断检查分别记录，一并留存根 ID、路径、深度和截断原因。

<span id="21-逻辑备份导入结果文件与重导入核验"></span>

## 21 逻辑备份、导入、结果文件与重导入核验

逻辑导出、导入、客户端结果文件和服务端 OUTFILE 还堆在一起。文件在磁盘上，还不等于内容完整。

操作顺序：先按结构、整库和条件分别导出，再导入另一个空库，客户端文件和服务端文件分开核验。


### 21.1 mysqldump：结构、全库和条件数据分别导出

还没决定这次导出的是结构、整库，还是带条件的一张表。别的版本上的参数也不能直接拿来用。

操作顺序：先核对客户端版本、引擎和权限，三条导出分开命名，失败逐项记，不用 --force 装成完整备份。

**1. 三条导出各自留下退出状态。**

```bash
# 单业务库结构；5.7/8.x版本和权限已核对的恢复实例
mysqldump --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --default-character-set=utf8mb4 --no-tablespaces --set-gtid-purged=OFF \
  --no-data --skip-lock-tables --routines --events --triggers lab_site \
  > "$OUT/schema.sql" 2> "$OUT/schema.stderr"
printf '%s\n' "$?" > "$OUT/schema.exit"

# 单库完整逻辑备份；不是--databases，因此不主动添加CREATE DATABASE/USE
mysqldump --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --single-transaction --quick --hex-blob --routines --events --triggers \
  --no-tablespaces --set-gtid-purged=OFF --default-character-set=utf8mb4 \
  lab_site > "$OUT/lab-site.sql" 2> "$OUT/dump.stderr"
printf '%s\n' "$?" > "$OUT/dump.exit"

# 单表/指定条件，保留结构；条件中的状态先核对
mysqldump --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --single-transaction --quick --hex-blob --no-tablespaces --set-gtid-purged=OFF \
  --where="status='paid' AND deleted_at IS NULL" lab_site orders \
  > "$OUT/paid-orders.sql" 2> "$OUT/paid-orders.stderr"
```


**2. 先看锁，以及只导出结构还是只导出数据。** 结构导出显式--skip-lock-tables适用于已隔离静止副本，避免默认锁表及额外LOCK TABLES权限；其本身不保证并发DDL一致。

`--no-data`只定义，`--no-create-info`只数据；`--databases db1 db2`会增加CREATE DATABASE/USE，`--all-databases`可能包含系统库，取证导入不默认采用。`--ignore-table=lab_site.table_name`必须用完整库表名且会改变覆盖范围。`--skip-extended-insert`便于逐行检查但会扩大文件、降低导入效率；不改变是否完整。

**3. 再按引擎组合一致性参数。** 先确认客户端版本、目标表引擎和所需权限，再组合参数：

- `--single-transaction` 用于 InnoDB 一致快照，不覆盖 MyISAM 或并发 DDL；`--quick` 只改变读取方式。
- `--hex-blob` 保留二进制值表示；`--no-tablespaces` 去掉表空间管理语句，不跳过业务数据。
- `--set-gtid-purged=OFF` 控制 dump 中的 GTID 语句，不改原历史 GTID。
- MySQL 8 客户端导出旧服务器，遇到特定兼容问题时可核对 `--column-statistics=0`。先查客户端是否支持，旧客户端不一定有此选项。

**4. 版本或权限对不上就停。** MySQL 5.5、MariaDB 和不同客户端的选项不能照搬。例程、事件、触发器及 DEFINER 可能需要额外权限，失败逐项记录，不用 --force 将不完整导出包装成完整备份。

**5. 条件子集不要当成整库备份。** 三种导出分别命名并保存各自 stdout、stderr 和退出状态；第三个条件导出也须记录状态。先列出被导出表的引擎，再决定能否用单事务快照；导出过程中有并发建表、改表、删表、重命名或 TRUNCATE 时，记录失败或一致性缺口，不把非事务表结果包装为同一时点。后续重导入核验使用对应导出文件，不把条件子集当整库备份。

本节已核对结构文件、整库文件和条件文件各自的范围、引擎和退出状态；并发 DDL、权限失败或 MyISAM 不在单事务快照里时，记下缺口，不用 --force 补成完整备份。`--set-gtid-purged=OFF` 没有改原历史 GTID；条件导出没有被拿去当整库，一并留存三份命名文件，以及各自的 stdout、stderr 和 exit。

### 21.2 在另一个空实验库导入

空的实验库还没建。dump 里如果有 USE 或 ALTER DATABASE，命令行上的 `lab_restored` 挡不住文件内部切库。

操作顺序：先建库并预查切库语句，确认只写预期单库再导入，失败就留副本，重试另建干净库。

**1. 新建实验库，排序规则按实际 DDL。** 【仅在副本/仿真/授权环境执行】下面会创建数据库并导入 SQL。

```sql
-- 新实验库，字符集/排序规则按实际DDL；不用新规则替换不匹配的原规则
CREATE DATABASE lab_restored CHARACTER SET utf8mb4;
```


**2. 预查之后再导入。**

```bash
rg -n 'CREATE DATABASE|ALTER DATABASE|^USE |DROP |DEFINER|GTID_PURGED|CREATE.*(TRIGGER|EVENT|USER)|`lab_site`\.' "$OUT/lab-site.sql"
# rg是预检查，不是SQL安全解析器；按§10完整审查后再执行
mysql --no-defaults --protocol=SOCKET --socket="$SOCKET" -u lab_importer -p \
  --default-character-set=utf8mb4 lab_restored < "$OUT/lab-site.sql" \
  > "$OUT/reimport.stdout" 2> "$OUT/reimport.stderr"
printf '%s\n' "$?" > "$OUT/reimport.exit"
sha256sum "$OUT/schema.sql" "$OUT/lab-site.sql" > "$OUT/dumps.sha256"
```


带例程的dump还可能有ALTER DATABASE；例程/视图/触发器定义中显式原库限定引用也须逐项核验，不用--databases不等于跨库引用全部消失。

**3. 确认文件内部不切库。** 先读 dump 中的 USE 和 DDL，确认它只写预期单库。命令行给出 `lab_restored`，并不能限制文件内部切库；本模板只用于已确认不切库的 dump。

**4. 失败按报错行回查。** 【仅在副本/仿真/授权环境执行】先建新实验库，再导入。失败时按报错行检查字符集、版本、DEFINER 和权限，保留失败副本。重试另建干净副本，不用 DROPs 覆盖旧失败状态。

本节已核对dump 只写入预期的 `lab_restored`，例程和触发器里的原库限定引用已经逐项看过；文件内有 USE、ALTER DATABASE 或跨库引用时，不因为命令行写了库名就认为没有切库。预查命中和导入的 stdout、stderr、exit 是同一份 dump，一并留存新库的字符集、失败副本，以及 dump 文件的哈希。

### 21.3 客户端TSV与服务端OUTFILE

结果要落到文件，但还没分清写在分析机上，还是写在数据库进程那边。批处理里的文字 NULL，也可能和真的字符串 `'NULL'` 撞在一起。

操作顺序：先做客户端批量导出，再核对转义和 NULL，服务端 OUTFILE 另记路径，权限错误不当成没有结果。

**1. 先确认输出在客户端。**

```bash
mysql --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --batch --quick --default-character-set=utf8mb4 lab_site \
  --execute='SELECT id,user_id,order_no,status,amount,paid_at FROM orders ORDER BY id' \
  > "$OUT/orders.tsv" 2> "$OUT/orders-query.stderr"
printf '%s\n' "$?" > "$OUT/orders-query.exit"
```


先确认输出在客户端。`--batch` 默认转义 TAB、换行、NUL 和反斜线；加 --raw 后，任意文本不再保证一行一条。把 TAB 换成逗号也不是正式 CSV。

**2. 可空字段同时留下是否为 NULL。** 再核对 NULL：mysql 批处理显示的文字 NULL 可能与真实字符串 'NULL' 碰撞。重要可空字段同时导出 `字段 IS NULL AS 字段_null` 和 `HEX(字段)`，或使用保留原类型及 NULL 的导出程序。

正式 CSV 由理解原列、NULL 和转义的程序生成。金额保留十进制文本，ID/号码保留字符串，同时记录表头和编码。

**3. 服务端文件按 OUTFILE 的规则写。** 【仅在副本/仿真/授权环境执行】`INTO OUTFILE` 会在数据库服务端创建文件，即使语句主体是 SELECT 也属于新增输出。

```sql
-- 服务端副本文件路径，满足FILE权限和secure_file_priv；不是分析机OUT路径
SELECT id,order_no,amount FROM lab_site.orders ORDER BY id
INTO OUTFILE '/work/mysql-case/server-export/orders.tsv'
CHARACTER SET utf8mb4
FIELDS TERMINATED BY '\t' ESCAPED BY '\\' LINES TERMINATED BY '\n';
SELECT @@secure_file_priv;
```


OUTFILE由服务端进程写，既有文件不会覆盖，需要FILE权限并受secure_file_priv限制。以上OUTFILE转义规则下SQL NULL通常写作`\N`，读回时按同样ESCAPED BY约定解释，别与文字NULL/含反斜线字符串混淆；服务端目录须事先按实验用户建立。`LOAD DATA [LOCAL] INFILE`是写入表的另一操作，默认不为查询开启LOCAL；若必须加载构造分析表，明确编码、分隔、转义、列顺序、NULL和LOCAL传输对象，不把任意日志原样导入证据表。

**4. 两条路径分开交付。** 【仅在副本/仿真/授权环境执行】执行前确认服务端实际文件系统、目标目录、权限与剩余空间；记录服务器路径和文件摘要，再与客户端导出的分析机路径分别交付。错误若属于 FILE 权限、secure_file_priv 或同名文件已存在，不解释为业务查询没有结果。

本节已核对客户端 TSV 的编码和表头，以及服务端 OUTFILE 的实际路径；FILE 权限、`secure_file_priv` 或同名文件已存在时，不写成查询没有结果。可空字段有 `字段 IS NULL AS 字段_null` 或 `HEX(字段)`；服务端 NULL 按 `\N` 和同样的 ESCAPED BY 读回，一并留存两份文件的路径、摘要、退出状态，以及 LOCAL 是否启用的说明。

### 21.4 核验内容，而非只核对文件存在

重导入的文件已经在了，但还没比内容。某一个 COUNT 或 SUM 相同，也不证明每一行相同。

操作顺序：对对象清单、DDL、主键和样本，排序、编码和时间语义一致才做文件哈希，校验和不能跨版本当逐字段证明。

**1. 比较两边的对象和字段。** 比较原恢复库与重导入库的表/视图/例程清单、DDL、主键集合、COUNT、NULL数、金额合计、时间范围、HEX样本及孤立关联。

**2. 哈希和校验和都要看前提。** 稳定主键排序后导出可做文件哈希对照，前提是字段、排序、显示、编码与时间语义完全相同。CHECKSUM TABLE受引擎/格式/版本影响，不能跨版本当通用逐字段证明；COUNT或某一个SUM相同也不证明每行相同。

本节已核对两边的对象清单、主键集合、NULL 数、金额合计、时间范围和 HEX 样本；排序、编码或时间语义不一致时，不做文件哈希对照；不把单个 SUM 写成每行相同。稳定主键排序后的导出，字段和显示格式已经相同，一并留存清单差异、哈希前提，以及 CHECKSUM TABLE 的引擎和版本限制。

### 21.5 派生分析表、CRUD与事务验证

要练习改一行的状态，但还不能改恢复业务库。建表用的 DDL 会隐式提交，ROLLBACK 撤不回它。

操作顺序：先在新分析库复制表，事务里更新和删除构造行，回滚后按同一主键看原值是否回来。

**1. 派生表放在新分析库。** 需要重建候选记录/练习改值时，在**新分析库**操作，不改恢复业务库；先用SHOW CREATE TABLE确认分析表是InnoDB。CREATE/ALTER/TRUNCATE/DROP等许多DDL隐式提交，建表在事务之前，ROLLBACK不是任意文件/DDL的回滚机制。

【仅在副本/仿真/授权环境执行】下面会建库、插入，并在事务里 UPDATE 和 DELETE。只在新分析库执行。

```sql
CREATE DATABASE lab_analysis CHARACTER SET utf8mb4;
CREATE TABLE lab_analysis.orders_copy LIKE lab_site.orders;
INSERT INTO lab_analysis.orders_copy SELECT * FROM lab_site.orders;
SHOW CREATE TABLE lab_analysis.orders_copy;
START TRANSACTION;
SELECT id,status FROM lab_analysis.orders_copy WHERE id=1001;
UPDATE lab_analysis.orders_copy SET status='analysis_candidate' WHERE id=1001;
DELETE FROM lab_analysis.orders_copy WHERE id=1002;
SELECT ROW_COUNT() AS last_statement_affected_rows;
ROLLBACK;
SELECT id,status FROM lab_analysis.orders_copy WHERE id IN (1001,1002) ORDER BY id;
```


**2. 列顺序没核对，就不要整行插入。** `INSERT ... SELECT *`只适用于已核对列顺序且可按该顺序写入的表；涉及生成列、不可见列等情况时，应依据DDL明确列出可写列和对应SELECT列，生成列不直接写普通值。

**3. 占位值和影响行数分开看。** ID和状态是构造占位。ROW_COUNT只对应最近语句，不表示此前每一步的影响；需要逐步记录时在每个DML后立即查询。LIKE不完整复制触发器/外键等关联对象，派生表不作为原库结构完全保全；MyISAM的非事务写入不由ROLLBACK撤销。重建历史记录应另带输入文件哈希、事件位置、当时DDL及未知字段列，而非把推导值写成原始事实。

**4. 回滚后重新查询同一主键。** 执行练习前确认两个主键存在、状态列能保存构造值，并记录原值。状态若为 ENUM、长度不足或有检查约束，先按已审阅的分析表 DDL 选择可存的实验值，不为套示例改原业务库。ROLLBACK 后重新查询同一主键，将行是否恢复及字段是否回到原值分别核对；仅看到 ROLLBACK 没报错不等于所有变化已撤销。

本节已核对分析表是 InnoDB，两个构造主键的原值，以及回滚后查到的值；状态列是 ENUM、长度不够或有检查约束时，先改实验值，不改原业务库。每个 DML 后的 ROW_COUNT 只解释那一条语句；ROLLBACK 没报错之后又按主键重查过，一并留存分析表 DDL、原值、回滚后的查询。历史重建另附输入哈希、事件位置和未知字段。

<span id="22-物理目录表空间与损坏副本的操作入口"></span>

## 22 物理目录、表空间与损坏副本的操作入口

完整数据目录、损坏副本、单表和增量备份还堆在同一个入口。启动会写数据，`--initialize` 也不是用来读历史 datadir 的。

操作顺序：完整目录先写独立配置，损坏时只在救援副本导出，单表、MyISAM 和 XtraBackup 按材料分支走。


### 22.1 完整数据目录：启动前写独立配置

原配置的 include、密钥和外部路径还没查。datadir 一启动就会做恢复并写数据，未启动的那一份副本还没留出来。

操作顺序：先查配置链和外部路径，写只属于实验根的配置，ping 通之后再对实际 datadir。

**1. 复制到工作目录，留下未启动副本。** 先检查原配置的include链、插件/密钥、页大小、日志、复制/集群和外部路径。完整目录仅复制到工作目录；启动会进行恢复并写数据，保留一份未启动副本。**`mysqld --initialize`只用于全新空实验实例，不用于已取出的datadir恢复；初始化与读取历史数据是两回事。**

**2. 按匹配版本写独立配置。** 以下是经匹配版本确认后、已具备完整副本的Linux独立实例配置示意；选项名称按具体版本调整：

```ini
[mysqld]
# 所有写路径属于同一实验根，原材料不作为datadir
basedir=/opt/mysql-matched
datadir=/work/mysql-case/work/datadir
socket=/work/mysql-case/run/mysql.sock
pid-file=/work/mysql-case/run/mysql.pid
log-error=/work/mysql-case/output/mysqld-error.log
tmpdir=/work/mysql-case/tmp
skip-networking
skip-log-bin
event-scheduler=OFF
# 复制启动参数在此按所用版本设置，见下面的版本分支
```


【仅在副本/仿真/授权环境执行】下面会启动这份实验实例，并在核验后只停止这个端点。

```bash
# 配置保存为独立lab.cnf；defaults-file是首个选项
/opt/mysql-matched/bin/mysqld --defaults-file="$CASE/lab.cnf" --user=mysql
# 在另一个终端确认socket/PID/log，再连接核验@@datadir
mysqladmin --no-defaults --protocol=SOCKET --socket="$SOCKET" -u lab_admin -p ping
mysql --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --execute='SELECT VERSION(),@@datadir,@@socket,@@event_scheduler;'
# 只停止该已确认实验端点，不使用systemctl stop mysql停全局服务
mysqladmin --no-defaults --protocol=SOCKET --socket="$SOCKET" -u lab_admin -p shutdown
```


**3. 版本分支逐项填，不整段套用。**

- MySQL 8.0.26 起使用 `skip-replica-start`，更早版本使用 `skip-slave-start`。SQL 的 STOP REPLICA 从 8.0.22 起支持，这是另一个边界。
- 8.x 用 `mysqlx=OFF` 关闭 X Plugin 独立监听，用 `persisted-globals-load=OFF` 阻止 datadir 内 mysqld-auto.cnf 的持久变量生效。原文件仍保留核对。
- MySQL 8.0.16 起可用 `--upgrade=NONE` 拒绝启动需要升级的数据目录。报错就回到匹配版本，不靠升级改掉历史状态。

**4. 确认写路径没有指回原件。** 仅 --defaults-file 和 skip-networking 不能完成全部网络及配置隔离。上述 8.x 选项不直接用于 MySQL 5.7 或 MariaDB，先查对应版本插件和支持项。

创建目录、复制、属主/权限调整仅针对核验过的实验根。复制常用`cp -a`/`rsync -a`，应记录符号链接和外部路径，确保恢复配置没有把写入重定向到原件。socket/PID不复用原服务；数据库系统用户须能访问其专用目录。MySQL8.0自动升级数据目录及跨产品不兼容尤其需控制，绝不让“较新版启动成功”替代原版本恢复说明。错误日志缺redo/undo/表空间/密钥时补齐对应材料，别直接删除文件尝试启动。

**5. 启动前对路径，响应之后再对身份。** 启动前逐项核对配置中的 basedir、datadir、socket、PID、日志和临时目录是否实际属于这个副本，软链及外置表空间也要检查最终实体。`mysqladmin ping` 只探测服务响应，不替代成功认证或目标身份查询；随后查询实际 datadir/socket，并与进程、日志对应，再开始业务读取。停止时只使用已经核实的实验端点。

本节已核对实验配置里的 basedir、datadir、socket、PID、日志和临时目录都属于这份副本；redo、undo、表空间或密钥缺失时，补材料，不删文件硬启动；8.x 选项不套到 5.7 或 MariaDB。`mysqladmin ping` 之后又查了实际 `@@datadir` 和 `@@socket`，并与进程、日志对应，一并留存未启动副本、独立 `lab.cnf`、错误日志，以及符号链接和外部路径清单。

### 22.2 innodb_force_recovery：救援导出，不是修复

正常的匹配副本启动失败，并且已经有 InnoDB 损坏的证据。force recovery 用来把能读的数据导出，不是把损坏文件修好。

操作顺序：另建救援副本，从等级 1 开始，能读就按主键分段导出，不在这个状态上做 DML。

**1. 只在救援副本上逐级增加。** 正常匹配副本启动失败且有InnoDB损坏证据时，另建救援副本，先从`innodb_force_recovery=1`尝试，只有必要时逐级增加并记录效果；启动参数/配置仅用于该副本。等级越高跳过的恢复处理越多，4—6有严重数据风险，6可能保留未应用redo的旧页，结果不能宣称事务完整。

【仅在副本/仿真/授权环境执行】下面的参数只追加到另建救援副本，不覆盖正常实验配置。

```ini
# 仅追加到另建救援副本的配置，不覆盖正常实验配置
innodb_force_recovery=1
```


**2. 按等级看会跳过什么。**

| 等级 | 跳过的处理与取证影响 |
| --- | --- |
| 1 | 尝试越过部分损坏页/记录，可能遗漏行 |
| 2 | 停止部分后台/purge工作，未修复物理页 |
| 3 | 不做崩溃后事务回滚，可能影响事务一致性 |
| 4 | 不合并insert buffer及部分统计，可能永久损坏，二级索引不可信 |
| 5 | 不扫描undo，未完成事务可能被当作已提交 |
| 6 | 不进行redo前滚，页状态可能过时 |


**3. 能读之后只导出。**

```bash
# 针对已能读取的救援副本，按该版本支持项组合；不承诺坏页/高等级快照完整
mysqldump --no-defaults --protocol=SOCKET --socket="$SOCKET" -u case_reader -p \
  --quick --skip-lock-tables --no-tablespaces --set-gtid-purged=OFF \
  lab_site orders > "$OUT/rescued-orders.sql" 2> "$OUT/rescued-orders.stderr"
printf '%s\n' "$?" > "$OUT/rescued-orders.exit"
```


取得可读状态后用受限SELECT/mysqldump导出能读的表/主键范围，不进行DML或把这个状态投入正常服务。按稳定主键分段可定位坏页影响；每段保存错误和边界，缺段不填0。去掉该参数并不能把已损坏文件自动修好，应以新建正常实例重导入已核验的逻辑数据；原副本与失败日志保留。MySQL和MariaDB在各等级的写限制可能不同，按所用版本官方说明确定，默认仅救援读取。

本节已核对救援副本实际使用的等级，以及能读出来的表和主键范围；某一段主键报错时留下边界，缺段不填 0；等级 4 到 6 的结果不写成事务完整。导出的 stderr 和 exit 与该等级写在一起；去掉参数没有被当成修复，一并留存救援配置、分段错误、逻辑导出，以及原来的损坏副本和失败日志。

### 22.3 单表、MyISAM、XtraBackup：按材料分支

材料可能是旧 `.frm`、MySQL 8 的 `.ibd`、MyISAM，或一份 XtraBackup。条件不满足时，不能串到别的分支上。

操作顺序：先按材料选命令入口，核对页大小、引擎和密钥，写操作只在副本上做。

**1. 按这张表选入口。**

| 材料 | 命令入口 | 必须满足的条件 |
| --- | --- | --- |
| 旧MySQL`.frm` | `mysqlfrm --diagnostic ./work/table.frm` | 旧工具，只提候选DDL；字段/索引/行格式与同版核验 |
| MySQL8未加密可解析`.ibd` | `ibd2sdi ./work/table.ibd > ./output/table-sdi.json` | SDI元数据，不是行数据恢复；加密及不同格式受工具支持限制 |
| 可导入独立InnoDB表空间 | 精确建空表→`DISCARD TABLESPACE`→安放副本→`IMPORT TABLESPACE` | 页大小、DDL、版本、行格式、外键、加密/密钥、完整性及元信息匹配，详见§02 |
| MyISAM副本 | `myisamchk --no-defaults --check --read-only ./work/sample.MYI` | 服务器不同时打开该表；工具离线操作，引擎需明确 |
| 损坏MyISAM索引 | `myisamchk --no-defaults --recover ./work/sample.MYI` | 写入新的恢复副本；读完整输出，复核数据与索引 |
| 已隔离实例的MyISAM表 | `CHECK TABLE lab_site.sample_table;`、`REPAIR TABLE lab_site.sample_table;` | CHECK/REPAIR有锁及引擎操作，不是无影响只读；REPAIR不修InnoDB |
| 可用XtraBackup物理链 | `xbstream`、`xtrabackup --decompress/--prepare` | 产品/版本兼容、完整LSN链、prepare写副本，见§03 |


MyISAM的`--read-only`表示检查后不改“已检查”标记，不抵消--recover修改语义；--force可能自动修复，不用于纯检查。恢复算法失败时可在另一修复副本考虑`--safe-recover`，仍核对丢行与索引。

**2. 空表只用来演示导入顺序。** 【仅在副本/仿真/授权环境执行】discard 和 import 会改实验表。真实 DDL 另从材料恢复。新建匹配**空表**的常用 SQL：

```sql
-- 这只是结构示意，不用于套任何未知表空间
CREATE DATABASE lab_tablespace CHARACTER SET utf8mb4;
CREATE TABLE lab_tablespace.sample_table(id BIGINT PRIMARY KEY, note VARCHAR(100)) ENGINE=InnoDB;
ALTER TABLE lab_tablespace.sample_table DISCARD TABLESPACE;
-- 按匹配版本导入条件放入 .ibd 及可用 .cfg/.cfp 工作副本
ALTER TABLE lab_tablespace.sample_table IMPORT TABLESPACE;
SHOW WARNINGS;
SHOW CREATE TABLE lab_tablespace.sample_table;
SELECT COUNT(*) FROM lab_tablespace.sample_table;
```


**3. 先判断是不是独立表空间。** 先判断表空间类型：这里的独立表空间 IMPORT 不用于共享系统或通用表空间。分区表需要对应分区文件及 `DISCARD/IMPORT PARTITION ... TABLESPACE`，不是“一个 ibd 就是一张普通表”。

再查结构与密钥。`.cfg` 可帮助核对结构；有的版本允许缺 cfg 尝试导入，但不能忽略完整性。涉及 INSTANT 添加或删除列且缺 cfg 时存在未定义行为，不把无 cfg 当成通用可恢复条件。加密表还需相应密钥传输材料或兼容机制。

**4. 外键表要处在同一逻辑时点。** 实验会话临时关闭 foreign_key_checks 后，IMPORT 和重新开启都不追查已有行，导入后仍用关联查询核验。

【仅在副本/仿真/授权环境执行】源副本可运行时，用 `FLUSH TABLES ... FOR EXPORT` 在同一会话持锁；另开终端复制 ibd/cfg/cfp，完成后再 `UNLOCK TABLES`。解锁或关闭会话会清理 cfg。已有离线镜像不写成执行过一致导出。

**5. 重建表的语句会改实验表。** `ALTER TABLE ... ENGINE=InnoDB` 会重建实验表，不是无损恢复。`OPTIMIZE/ANALYZE/REPAIR/TRUNCATE/DROP` 也不对原件执行。

本节已核对材料分支、候选 DDL 或 SDI、页大小、行格式和密钥条件；缺 `.cfg`、缺分区文件或加密密钥时，不把“一个 ibd”写成一张普通表已经恢复。IMPORT 之后用关联查询核对外键；MyISAM 的检查和 `--recover` 已经分开，一并留存命令输出、警告、丢行和索引复核。离线镜像不记成做过 `FLUSH TABLES ... FOR EXPORT`。

### 22.4 XtraBackup增量链的命令组合

基础备份和增量的 LSN 还没接上。最终 prepare 如果做得太早，后面的增量就加不进去。

操作顺序：先读每份 checkpoints，用 apply-log-only 按顺序合并，链完整后再做最终准备。

**1. 只对匹配版本的未准备副本做。** 以下限匹配产品/版本的未准备基础和按LSN连续的增量**副本**，已有压缩材料先按§03解包/解压；不是任意MySQL目录都能prepare。

【仅在副本/仿真/授权环境执行】prepare 会改写工作备份目录。

```bash
xtrabackup --prepare --apply-log-only --target-dir="$CASE/work/base"
xtrabackup --prepare --apply-log-only --target-dir="$CASE/work/base" \
  --incremental-dir="$CASE/work/inc-01"
xtrabackup --prepare --apply-log-only --target-dir="$CASE/work/base" \
  --incremental-dir="$CASE/work/inc-02"
# 增量链已全部合并，再执行最终准备；逐步保存错误和exit
xtrabackup --prepare --target-dir="$CASE/work/base"
```


**2. 先看 LSN 是否连续。** 先逐份读取 xtrabackup_checkpoints，检查 from_lsn/to_lsn 是否连续，再核对备份时间。保留继续合并能力时用 --apply-log-only，不先做最终回滚后再追加任意增量；同一增量目录也不反复供多个目标使用。

**3. 写回之前先确认接收目录。** 【仅在副本/仿真/授权环境执行】--copy-back/--move-back 会写接收 datadir，先确认实例停止、目标为新建空目录。--move-back 还会消耗工作备份，所以本页默认保留副本，不给省略目标检查的搬回命令。

本节已核对from_lsn 与 to_lsn 连续的基础备份和每一份增量；LSN 不连续，或增量目录已经被另一个目标用过时，不继续合并，也不先做最终回滚再追加。每一步的错误和 exit 都在；最终 prepare 发生在增量全部合并之后，一并留存checkpoints、工作副本。接收 datadir 只有在实例已停止且目录是新建空目录时才记录写回。

### 22.5 实验账户与权限命令

已有读取身份时，不必新建账户。要建实验账户，也不能默认做成 `root@%` 或 `GRANT ALL`。

操作顺序：优先用已有读取身份，只在正常授权的实验实例上建最小权限账户，账户改动不是历史口令。

**1. 新账户只给这次实验需要的权限。** 正常访问优先使用已取得的副本读取身份；授权恢复顺序详见§11。新分析账户仅在正常授权的实验实例建立：

【仅在副本/仿真/授权环境执行】下面会创建账户、授予 SELECT 和 SHOW VIEW，并在后续管理会话里撤销。

```sql
CREATE USER 'case_reader'@'localhost' IDENTIFIED BY '<实验专用口令>';
GRANT SELECT, SHOW VIEW ON lab_site.* TO 'case_reader'@'localhost';
-- 管理与回放账户：仅在隔离实验实例建立，权限按本次用途单独限定
CREATE USER 'lab_admin'@'localhost' IDENTIFIED BY '<实验专用口令>';
GRANT SHUTDOWN, PROCESS ON *.* TO 'lab_admin'@'localhost';
CREATE USER 'lab_replay'@'localhost' IDENTIFIED BY '<实验专用口令>';
GRANT SELECT, INSERT, UPDATE, DELETE ON pitr_target.* TO 'lab_replay'@'localhost';
SHOW GRANTS FOR 'case_reader'@'localhost';
SHOW GRANTS FOR 'lab_admin'@'localhost';
SHOW GRANTS FOR 'lab_replay'@'localhost';
-- 后续正常实验管理会话撤销这些临时权限，不触及原账户
REVOKE SELECT, SHOW VIEW ON lab_site.* FROM 'case_reader'@'localhost';
REVOKE SHUTDOWN, PROCESS ON *.* FROM 'lab_admin'@'localhost';
REVOKE SELECT, INSERT, UPDATE, DELETE ON pitr_target.* FROM 'lab_replay'@'localhost';
```

账户用途：`lab_admin` 用于 §22.1 的 `mysqladmin ping/shutdown`（需 SHUTDOWN、PROCESS）；`lab_replay` 用于 §23.3 的时间点回放（写回放目标库 `pitr_target`，库名按实际回放目标替换）。二者都只在隔离实验实例建立，正常访问优先用已取得的副本读取身份。


**2. Host 按实验连接来源配置。** 专用账户的Host按实际实验连接来源配置，不默认授予root@%或GRANT ALL。需要例程定义/FILE/PROCESS/恢复管理权限时单独说明用途与版本，不把所有读取命令默认为此SELECT账户都能执行。MySQL先`FLUSH PRIVILEGES`再`ALTER USER`的`--skip-grant-tables`恢复分支是另一模式；正常CREATE/GRANT之后通常无需额外FLUSH。账户状态改动不是历史凭据证据。

本节已核对实验账户的 Host、认证方式和 `SHOW GRANTS` 里的 SELECT、SHOW VIEW；还需要 FILE、PROCESS 或例程定义权限时，单独说明用途和版本，不并进这条只读授权。正常 CREATE/GRANT 之后没有把 `--skip-grant-tables` 的 FLUSH 流程混进来，一并留存账户语句和授权输出。这些状态改动不作为历史凭据。

<span id="23-binlog其他日志与时间点回放命令"></span>

## 23 binlog、其他日志与时间点回放

历史 binlog 文件、恢复副本上的当前变量，以及真正能回放的日志，还没分开。其他错误日志和慢查询也不能当成 binlog。

操作顺序：先清点当前状态，完整读过再按时间或位置缩小，回放要有可执行日志和正确基线。


### 23.1 状态清点：区分历史文件与当前变量

恢复副本上现在看得到 binlog 变量，但这不能证明历史上一直开着日志。5.7 和 8.4 的状态命令名称也不一样。

操作顺序：只跑这一版支持的一条状态命令，留下不支持或权限错误，历史文件改看离线 index 和事件头。

**1. 先看当前实例的日志状态。**

```sql
SHOW BINARY LOGS;
SHOW VARIABLES LIKE 'log_bin%';
SHOW VARIABLES LIKE 'binlog%';
SHOW VARIABLES LIKE 'gtid%';
-- MySQL 5.7/较早8.0状态命令；8.4按新名称
SHOW MASTER STATUS;
-- MySQL8.4使用
SHOW BINARY LOG STATUS;
```


**2. 当前清单和历史文件分开写。** 只运行该版本支持的一条状态命令，保留不支持/权限错误。恢复副本当前binlog变量和文件清单不证明历史一直开启日志；离线index、Rotate、格式描述、server_id及时间范围另核验。GTID事务身份不是墙上时钟；不要把PURGE BINARY LOGS或RESET类指令加入取证清点。

本节已核对这一版实际支持的状态命令，以及当前实例上的 binlog 变量和文件清单；命令不支持或没有权限时留下报错；历史是否开启要另看离线 index、Rotate 和格式描述。GTID 没有被当成墙上时钟；清点命令里没有 PURGE 或 RESET，一并留存状态输出、权限错误，以及离线日志的 server_id 和时间范围。

### 23.2 只读显示、时间筛选、位置筛选

完整日志链还没读，就用一秒的时间窗口去筛，可能把一个事务切成两半。窗口里没有输出，也不等于没有这件删除。

操作顺序：先解码完整文件，再按已核对的时间或位置缩小，`###` 只当阅读注释。

**1. 完整读取、时间窗口和位置窗口分开存。**

```bash
TZ=UTC mysqlbinlog --no-defaults --base64-output=DECODE-ROWS -vv \
  --verify-binlog-checksum ./work/binlog.000001 > "$OUT/binlog-read.txt" 2> "$OUT/binlog-read.stderr"
printf '%s\n' "$?" > "$OUT/binlog-read.exit"

TZ=UTC mysqlbinlog --no-defaults --base64-output=DECODE-ROWS -vv \
  --start-datetime='2024-01-01 00:00:00' --stop-datetime='2024-01-02 00:00:00' \
  ./work/binlog.000001 > "$OUT/binlog-window.txt" 2> "$OUT/binlog-window.stderr"

# 已用完整日志核对位置/事务后定位，数值只是构造占位
TZ=UTC mysqlbinlog --no-defaults --base64-output=DECODE-ROWS -vv \
  --start-position=120 --stop-position=930 ./work/binlog.000001 \
  > "$OUT/binlog-position.txt" 2> "$OUT/binlog-position.stderr"
rg -n 'Table_map:|Write_rows:|Update_rows:|Delete_rows:|Xid|COMMIT|GTID|Rotate' "$OUT/binlog-read.txt"
```


**2. 看筛选作用在文件的哪一端。** 先读完整日志链，再按时间或位置缩小范围。datetime 按工具运行环境时区解释；同一秒内的多个事务不能只靠秒级筛选排序，回放要用核验过的事务边界位置或 GTID。

多文件输入时，start/stop-position 分别作用于首文件和末文件，位置号不是跨文件唯一地址。`--database` 对 statement、row 事件及跨库语句的筛选含义不同；先完整读取再过滤，保留审计依据。

**3. 时间窗口不按事务整组截取。** `--start-datetime` 从首个时间戳达到起点的事件开始，`--stop-datetime` 在首个时间戳达到终点的事件前停止；这种窗口不自动按事务整组截取。先在完整输出中找 BEGIN/GTID、行事件及 Xid/COMMIT，再确定目标边界。筛选不到目标也要核对输入文件的实际起止范围、工具时区和解析错误，不能把“窗口无输出”当作完整阴性结论。

**4. 伪 SQL 和损坏都不要补成完整恢复。** 看到 DECODE-ROWS 的 `###`，把它当阅读用的注释伪 SQL，不当可执行回放文件。缺完整 before image 或事件时刻 DDL，就保留第 N 列和未知字段，不补猜。

加密、损坏、截断或版本不兼容报错时，记录材料缺口，不强制忽略后声称完整。`mysqlbinlog --read-from-remote-server/--raw` 是在线采集分支，本页读离线材料不需要它，也不能用它恢复已清除的日志。

本节已核对完整解码里的事务边界，以及缩小后的时间或位置窗口；窗口没有输出时，还要核对文件实际起止、工具时区和解析错误，不能写成阴性结论。目标边界落在 BEGIN/GTID 和 Xid/COMMIT 上；`###` 没有被当成回放文件，一并留存三份解码输出、stderr、exit，以及校验失败的记录。

### 23.3 回放需要可执行日志和正确基线

要回到删除前的某个位置，但全新隔离实例上还没有放好已核验的备份。示例里的位置 120 和 930 不是检材坐标。

操作顺序：先导入删除前备份，生成不含 DECODE-ROWS 的可执行文件，同一个连接按顺序执行，失败就从新基线重来。

**1. 基线和文件内容核验之后再执行。** 先把已核验的删除前备份导入**另一个全新隔离实例**，确认原备份坐标，再生成不加DECODE-ROWS的可执行文件。以下只示意单文件区间，位置120/930不是实际检材坐标：

【仅在副本/仿真/授权环境执行】回放会写入隔离实例。生成退出状态不是 0，或事务边界还没核验时，不要执行。

```bash
mysqlbinlog --no-defaults --start-position=120 --stop-position=930 \
  ./work/binlog.000001 > "$OUT/replay.sql" 2> "$OUT/replay.stderr"
replay_rc=$?
printf '%s\n' "$replay_rc" > "$OUT/replay.exit"
# 仅在生成exit为0、文件内容/事务边界/跨库语句已核验后执行
mysql --no-defaults --protocol=SOCKET --socket="$CASE/pitr-run/mysql.sock" \
  -u lab_replay -p --binary-mode < "$OUT/replay.sql" \
  > "$OUT/replay-import.stdout" 2> "$OUT/replay-import.stderr"
printf '%s\n' "$?" > "$OUT/replay-import.exit"
```


**2. 回放仍然会写。** `--binary-mode`用于兼容包含特殊字节的回放输入，不把原SQL变为只读或去掉写操作。重放目标须隔离复制、事件调度和外部依赖，禁止把未知跨库操作送往既有实例。GTID模式、已执行GTID与重复事务须另核对；默认保留可执行日志的GTID语义，不随意加`--skip-gtids`“解决”报错。回放期间新产生的日志属于实验记录。恢复后按目标主键、状态、金额和历史镜像复核；不是“运行命令没有错误就完整还原”。

**3. 多文件交给同一个连接。** 【仅在副本/仿真/授权环境执行】多文件回放按已核对的顺序生成同一份可执行输入，并由同一个 mysql 连接执行，避免跨文件语句依赖的临时表随中间断开而丢失。生成失败时保留部分输出但不执行；执行失败时保留目标副本和已到达的位置，下一轮从新的同一基线开始，不能在部分完成的目标上盲目重复回放。

本节已核对删除前备份的坐标、可执行文件的事务边界，以及回放后的主键、状态和金额；生成失败或执行停在半路时，保留已到达位置，下一轮从新的同一基线开始。没有用 `--skip-gtids` 压掉报错；实验期间新产生的日志单独存放，一并留存 `replay.sql`、两份退出状态、目标副本。位置 120/930 只作为构造占位。

### 23.4 错误、慢查询、general与审计日志

错误日志、慢查询和 general log 还没和 binlog 分开。现在把 general_log 打开，也只能记后面的请求，补不回过去。

操作顺序：先看变量指向哪份文件或表，已有日志按保全副本读，启用或清空会改副本，不作为默认动作。

**1. 先看日志变量；确有表日志再查表。**

```sql
SHOW VARIABLES WHERE Variable_name IN
 ('log_error','general_log','general_log_file','log_output',
  'slow_query_log','slow_query_log_file','long_query_time');
-- 仅当原材料/恢复副本确有TABLE日志且权限允许
SELECT event_time,user_host,thread_id,command_type,argument
FROM mysql.general_log
WHERE event_time>='2024-01-01 00:00:00' AND event_time<'2024-01-02 00:00:00'
ORDER BY event_time,thread_id;
```


**2. 按每种日志能证明的范围来读。** FILE日志读取已保全副本，例如`rg -n 'Access denied|ready for connections|Shutdown|ERROR|Query_time' ./work/logs/`。general_log可记录发送给服务器的语句，不保证语句成功提交；slow log有阈值/过滤，不是全活动。binlog通常记录适用的更改事件，不提供所有SELECT历史。没有日志既可能未启用，也可能轮转、遗漏或覆盖；现在开启general_log只记录后续请求，不能追溯过去。【仅在副本/仿真/授权环境执行】启用/清空日志、FLUSH LOGS均会改变副本状态，非本页默认历史读取动作。

本节已核对 `log_error`、general log 和 slow log 的实际路径或表，以及已保全文件里的相关行；日志不存在时，写明可能是未启用、轮转、遗漏或覆盖，不把“现在打开”当成补上了历史。general_log 里的语句没有被写成已经提交；慢日志没有被写成全部活动，一并留存变量输出、FILE 日志摘录。启用或 FLUSH 如果做过，单独记在副本变更里。

<span id="24-实战组合与自建sql练习"></span>

## 24 实战组合与自建 SQL 练习

要算的是会员、金额、提现还是被删订单，口径还没从材料里定下来。自建的六张练习表也不是检材。

操作顺序：先按场景拿到依据，再选命令链，练习材料只导入全新实验库。


### 24.1 从题意确定查询口径

还没分清这次是让副本变得可读、查当前记录，还是读过去的变更。三件事有关联，但不能互相代替。

操作顺序：先对上场景和已经拿到的依据，再按命令链交付，页面结果不自动证明历史状态。

**1. 按这张表确定依据和交付。** 以下是常见实题考点的独立操作场景，不沿用固定答案或未公开DDL：

| 场景 | 先拿到的依据 | 命令链与交付 |
| --- | --- | --- |
| 网站无法运行，需要查会员资料 | 活动配置、卷映射、业务库DDL | 清点→连接身份→元数据字段搜索→已知ID定位→原值/HEX导出 |
| 求成功业务的总数/人数/服务费 | 状态代码、费用字段、时间定义 | 条件抽样→COUNT与COUNT DISTINCT分开→SUM→状态分组对照→边界核验 |
| 求每用户累计提现最多者 | 提现审核状态、用户稳定ID | 先WHERE状态→GROUP BY用户→SUM→稳定排序/并列→关联姓名 |
| 求充值扣提现且排除赠送 | 类型和审核字典、币种、时间范围 | 两表分别聚合→LEFT JOIN→COALESCE/NULLIF→异常/无记录用户保留 |
| 求某天登录人数最多 | 事件表、一人多次登录、时间基准 | 半开范围→DATE分组→COUNT DISTINCT用户→排名与并列 |
| 电话中指定字符出现次数 | 字符串原值和筛选范围 | NULL分类→CHAR_LENGTH/REPLACE→逐条与总数复核，不加未要求格式过滤 |
| 求第二高地区平均收入 | 规范地区映射、收入类型/NULL | GROUP BY→AVG并保留有效分母→ROW_NUMBER或DENSE_RANK口径 |
| 求根用户下线最大层级 | id/parent映射、根层定义 | 自关联抽样→递归/脚本→环路、孤立、截断检测→MAX层级 |
| 查被删除订单的原值 | 时间前备份、完整binlog、事件时刻DDL | 当前状态与软删区分→解码事件→列序/事务核验→必要时新实例回放 |
| 历史聊天在另一份SQL备份 | 原备份、编码、导入前审查 | 新实验库导入→身份/时间字段查询→和当前库差异对照 |


**2. 三件事分开做。** 先分清正在做哪件事：恢复目录是让副本可读取，查询当前记录是读当前状态，读取历史日志是查过去的变更。三者有关联，但不能互相代替。

**3. 业务口径和页面分开验证。** 计算业务数据前确认字段写入逻辑、状态、金额单位和时间口径；验证网站时再把页面字段与同一实例的记录对应。当前页面结果不自动证明历史状态。

本节已核对这次场景需要的状态、字段、时间或日志依据，以及对应的命令链；依据还是未公开的 DDL，或页面字段还没对上同一实例时，不沿用固定答案。恢复目录、当前查询和历史日志的结果各有自己的材料，一并留存场景依据、查询 SQL，以及和页面对照过的那几条记录。

### 24.2 下载构造材料，练习“看似正确”的错误统计

要练习那些看起来对、其实口径错了的统计。材料是完全自建的六张表，不能把预期数字填进真实检材。

操作顺序：先审查建表 SQL 和目标端点，只导入全新实验 schema，用独立算好的预期对照输出。

**1. 先拿到这四份自建材料。** 提供完全**自建**的六表材料：users、orders、order_items、withdrawals、login_events、funds，包含重复金额、多明细、多提现、软删、退款/未支付、NULL、无记录用户、前导零号码及重复登录。

- [建表与数据SQL](/practice/mysql-forensics/schema.sql)
- [查询SQL](/practice/mysql-forensics/queries.sql)
- [预期结果](/practice/mysql-forensics/expected-results.json)
- [运行与核验说明](/practice/mysql-forensics/README.md)

**2. 只导入全新的实验库。** 【仅在副本/仿真/授权环境执行】素材只导入全新的实验schema，不是比赛检材；先审查建表SQL与目标端点，再按README运行。核验订单数与账户数、关联倍增前后的主键粒度、SUM(DISTINCT金额)漏计、无充值用户与收入NULL分母、号码NULL、日去重人数和时间/IP反向转换。预期值来自构造数据的独立计算，与实际输出对照，不用执行结果反填期望。

**3. 已有记录只说明那次构造实验。** **既有构造材料的验证记录：** 此处记录的是已完成的构造实验，不是本轮对检材运行数据库。在全新 datadir 和独立本地连接上使用 MySQL 5.5.62（该次实验在 Windows 上以命名管道连接；Linux 下的等价物是本地 socket，站点其余命令默认按 Linux/Kali 书写），15 组查询逐项命中预先手写期望；逻辑 dump 导入另一新 schema 后，15 组再次一致，二次 dump 字节一致。

预期基线是 5 笔未软删 paid 订单、4 个账户、金额 450.00。明细 JOIN 会膨胀为 9 行/800.00；SUM(DISTINCT amount) 则误计 350.00。实验进程正常结束，没有连接或启停既有数据库服务。

**4. 没在那次实验里跑过的模板，不要写成实测。** 这些结果只验证构造数据的核心 SQL 和逻辑往返。NULLIF 比率、READ ONLY、JSON/窗口/递归模板、8.x 物理恢复、表空间导入、强制恢复及 binlog 回放没有据此声称实测，也不等于真实比赛附件重放。

本节已核对构造库上的订单数、账户数、金额口径，以及 JOIN 前后的行数差异；NULLIF、窗口、递归、物理恢复、表空间导入和 binlog 回放没有这次构造实验的实测记录。15 组查询对上预先手写的期望；二次 dump 字节一致。预期值不是用执行结果反填的，一并留存建表 SQL、查询 SQL、预期结果、README 运行记录。这不是比赛检材的重放。

<span id="25-排错易错命令与最终证据清单"></span>

## 25 排错、易错命令与最终证据清单

连接失败、权限不足或行数看起来一样时，还不能推出库已经损坏、记录从未存在，或备份已经完整。

操作顺序：先按现象回到表里的处理，不写右侧禁止推出的结论，再按最小交付把哈希、口径和缺口留齐。

**1. 按这张表排错。**

| 现象/命令 | 正确处理 | 不应推出的结论 |
| --- | --- | --- |
| 2002/2003连接失败 | 实验进程、socket/TCP、路径/监听、发布端口与隧道分层 | 库文件损坏或口令必错 |
| 1045 Access denied | 账户Host、认证插件、TLS、锁定/口令候选 | 改root@%即可解决全部问题 |
| 1044/1142权限不足 | 记录可见范围，按操作申请实验权限 | 没有数据库/表 |
| 1049/1146未知库/表 | 核对实例、大小写、schema、导入错误及视图/历史名称 | 历史记录从未存在 |
| 1054列不存在 | 检查DDL、列顺序和事件时刻版本 | 随意改列名拼出答案 |
| 1055分组错误 | ONLY_FULL_GROUP_BY下明确分组/聚合/排名 | 关闭模式后任意一行可信 |
| 乱码或1265/1366转换问题 | 原始字节、DDL字符集、客户端字符集、警告及严格模式 | 批量UPDATE转码一定修好 |
| 表可见但查询失败/1812等表空间错误 | 错误日志、DDL、dictionary/ibd匹配、页大小、密钥与完整性 | 只复制ibd或删ibdata1可通用修复 |
| mysqldump输出文件有内容但报错 | exit、stderr、对象清单/权限和内容核验 | 文件存在即备份完整 |
| 刚启动文件时间变化 | 实验恢复/日志/升级写入记录 | 历史最后访问时间 |
| TRUNCATE/DROP/ALTER/REPAIR | 仅新实验对象按条件执行，保留回滚副本 | ROLLBACK能撤销任意DDL；MySQL许多DDL隐式提交 |
| UPDATE/DELETE调试 | 构造表或新分析副本才做，验证条件/影响行数 | 加LIMIT或safe-updates就能保护原证据 |
| general_log/日志回放 | 已有日志先保全，回放写入另一个实验实例 | 现在开日志能补历史；伪SQL可直接回放 |


**2. 最小交付留下这些。** **最小交付：** 输入目录/备份/日志哈希，历史与实验版本，实际datadir/socket/端口与账户，DDL及状态/类型字典，查询SQL原件，时区与时间单位，金额单位/NULL/软删/去重/并列口径，stdout/stderr/exit，结果文件编码与哈希，主键/样本核验，恢复/回放写入范围与缺口。

**3. 首轮按这个顺序做。** **首轮依次做。** 清点材料和版本，确认恢复副本身份；取得精确 DDL 后先抽样，再做分组、关联和转换；最后用历史日志互证，导出并重导入核验。

**4. 三件表面结果各只证明一件事。** SQL 能执行、行数相同、界面能打开，各自只证明一件事。把样本内容、历史状态和往返结果核对完，再写恢复结论。

本节已核对现象对应的处理、最小交付里的版本和口径，以及样本、历史状态和往返结果；表里右侧那一列的结论还没有别的证据时，不写出去。stdout、stderr、exit 和主键样本在同一份交付里；SQL 能执行、行数相同、界面能打开各算一条，一并留存哈希、datadir、socket、端口、账户、DDL、查询原件、时区、金额单位和恢复缺口。
