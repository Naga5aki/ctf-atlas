手里是数据库检材：MySQL/MariaDB、TiDB、PostgreSQL、SQLite 或 SQLCipher 的数据文件，以及它们的配置和日志。本页回答：实例在哪、怎么打开、字段怎么读、服务起不来怎么读原始页、统计口径怎么固定、主备数据是否一致。原始材料保持只读，只在隔离副本上查询。

**先定位实例 → 按代码核对 SQLCipher 密钥与参数 → 按字段语义取值 → 服务起不来时读原始页 → 统计前固定口径 → 枚举端点并核对主备差异。**

<span id="01-先定位实例再查询数据"></span>

## 01 先把每个数据库实例定位成独立条目

应用配置里的地址、端口、库名和文件路径还没列成独立实例。端口、扩展名或一次打开失败，都还不能决定这是哪种数据库。

**先从配置列出地址和文件 → 固定数据和日志 → 用包、监听和文件名核对实例身份 → 再在隔离副本里查询。**

**1. 先读应用配置，列出数据库地址、端口、库名和文件路径。** 固定数据与日志后，再在隔离恢复副本中查询。

**2. 每份结果注明实例、表、版本和时间范围，并保留它与原检材的派生关系。** 端口、扩展名和一次打开失败都只提供线索，不能单独决定数据库类型。对不上类型时，先补程序身份和文件头，不换一种客户端硬打开。

每个实例的地址、端口、库名或文件路径，以及它和原检材的派生关系对上；只有端口、扩展名或一次打开失败时，数据库类型还不能单独决定。结果写明了实例、表、版本和时间范围，配置中的连接项、固定下来的数据和日志位置一起保存。

### 01.1 数据库类型与定位起点

连接配置、端口和数据目录都还只是线索，MySQL、TiDB、PostgreSQL、SQLite 和 SQLCipher 的读法不能互套。先按类型选定起点，再核对版本和配套文件。

操作顺序：按线索对上类型，用匹配的客户端读已确认的实例，主库和备份库分开登记。

**1. 先看类型、常见线索和读取限制。** 端口能改，文件头不合法时不要换一条限制硬读：

<details>
<summary>展开数据库类型与读取限制表</summary>

| 类型 | 常见线索 | 读取方式与限制 |
| --- | --- | --- |
| MySQL / MariaDB | 连接配置、3306、服务端程序、数据目录 | 使用匹配版本的恢复实例和 MySQL 客户端；端口可修改 |
| TiDB | MySQL 协议端点、常见 4000、TiDB/PD/TiKV 配置与日志 | MySQL 客户端能查询协议兼容端点；端口本身不能区分 MySQL 与 TiDB |
| PostgreSQL | 5432、`/var/lib/postgresql/<ver>/`、`postgresql.conf`、`pg_hba.conf` | `psql` 连接已确认的恢复实例，核对版本及认证配置 |
| SQLite | 应用目录内 `.db/.sqlite`，合法 SQLite 文件头和结构 | `sqlite3` 或 DB Browser for SQLite 读取副本，并带齐 WAL 等配套文件 |
| SQLCipher | 应用代码引用 SQLCipher、加密参数、随机外观文件头 | SQLCipher 兼容工具或 DB Browser for SQLCipher；同时确认密钥与参数 |
| Redis 等键值库 | 端口 6379、`redis.conf`、RDB/AOF 持久化文件 | 内存库；用持久化快照恢复，键过期或未持久化部分不可回收。容器与实例归属见[Docker 与 LXC 的现场识别](/knowledge/docker-evidence-01/) |

</details>

**2. PostgreSQL 的最小操作范围。** 类型表已给出 `psql` 连接、版本与 `pg_hba.conf` 认证的核对方向；数据目录、认证与实例恢复的完整主线见[MySQL 数据目录与表恢复](/knowledge/forensic-database-recovery/)，本页不展开 PostgreSQL 的额外交互步骤。

**3. 场景里的两个端点分成两个实例。** 网站配置指向 `db-main:3306/site_main`，备份配置指向 `db-backup:4000/site_backup`。建立两个独立实例条目，分别记录名称解析、程序身份、数据目录、版本、导出时间和恢复步骤。不要把一端查询不到的记录直接解释为删除，也不要把备份库名称直接当作复制关系证据。

**4. 宿主机和容器分开确认。** 宿主机与容器中的部署应分别确认，集中方法见[Docker 与 LXC 的现场识别](/knowledge/docker-evidence-01/)和[Docker 网络与 Compose](/knowledge/docker-evidence-05/)。服务清单还可参照[Linux 系统与服务取证](/knowledge/fic-case-03/)。一端打不开时，先核对该实例自己的认证和数据目录。

每个端点的类型线索、程序身份、数据目录和版本登记成两条独立实例记录（`db-main:3306/site_main` 与 `db-backup:4000/site_backup`）；查询不到的记录还不能写成删除，备份库名称也还不是复制关系。名称解析、导出时间、恢复步骤和宿主机或容器的归属一起保存。

### 01.2 固定 SQLite 主库、WAL 与 SHM

已只读挂载的应用目录是 `/mnt/evidence/data/user/0/com.example.chat/databases/`。主库名是演示材料，配套的 WAL 和 SHM 还没确认是否一起固定。只拷主库会漏掉尚未 checkpoint 的更新。

操作顺序：先列出整组文件，只复制已经确认存在的配套文件，在副本上只读打开。

**1. 材料路径按实际存在的文件替换。** 下面的主库名是演示材料，实际使用时替换为存在的文件。配套文件不存在时，跳过对应复制并单列记录，不删除已有的 WAL。

```bash
mkdir -p ./work/chat-db
ls -l /mnt/evidence/data/user/0/com.example.chat/databases/chat.db*
cp --preserve=timestamps -- /mnt/evidence/data/user/0/com.example.chat/databases/chat.db ./work/chat-db/
# 仅在已经确认存在这些配套文件时执行对应复制
cp --preserve=timestamps -- /mnt/evidence/data/user/0/com.example.chat/databases/chat.db-wal ./work/chat-db/
cp --preserve=timestamps -- /mnt/evidence/data/user/0/com.example.chat/databases/chat.db-shm ./work/chat-db/
sha256sum ./work/chat-db/chat.db*
sqlite3 -readonly ./work/chat-db/chat.db '.tables'
sqlite3 -readonly ./work/chat-db/chat.db '.schema'
```

**2. 先保全一组文件，再打开副本。** `.db` 是主库；WAL 可能保存已提交但尚未 checkpoint 到主库的更新，单拷主库会漏掉这些内容。SHM 是 WAL 索引辅助文件，不是业务行的主要存储，也应随组保全；缺失时单列记录。

**3. 原件不打开、不 checkpoint、不 VACUUM。** 【仅在副本/仿真/授权环境执行】工具需要辅助文件时，只让它在可写的副本目录生成。只读打开报错，先保存错误，再查三份文件是否一致采集及目录权限；不要删除 WAL 后声称数据完整。事务背景见 [SQLite WAL 说明](https://www.sqlite.org/wal.html)。

**4. 活体还在写入时，先后复制三份文件并不保证同一时点。** 下面的复制命令用于已固定的离线材料。活体应用还在写入时，应先取得一致快照，记录采集方式。

**5. 复制后仍要核对哈希，并注意只读方式的局限。** `cp --preserve=timestamps` 只保留文件时间，复制后仍要核对哈希与一致性。`sqlite3 -readonly` 限制数据库连接，但副本目录可写时仍可能生成辅助文件；面对带 WAL 的库，只读打开不会 checkpoint，若 WAL 未一并保全，读到的可能不是最新已提交状态。打开前留一套未打开副本，打开后对比目录，把新增或变化的辅助文件单独记录。

主库、已确认的 WAL 和 SHM 都在副本里，只读打开能看到表和结构；配套文件缺失、只读报错或活体复制不是同一时点时，不声称数据完整。打开前后的目录对比和哈希保存，新增辅助文件单独列出，原件没有被 checkpoint 或 VACUUM；未打开的那一套副本、`sha256sum` 输出和 `.tables`、`.schema` 一起留存。

<span id="02-sqlcipher-的识别与密钥验证"></span>

### 01.3 安装、服务与实例身份

§01.1 从配置列出的实例，还要用包、监听和文件名核对身份。下面的命令若在分析机上跑，会把分析机的包和端口填进目标结果；离线检材要改读它自己的包数据库和文件根。

操作顺序：确认是目标会话或仿真副本，看包、监听和文件名，写“未发现”前再核对搜过的根。

**1. 以下命令只用于已确认的目标运行会话或隔离仿真副本。** 离线检材应指定其软件包数据库、配置和文件根目录，不能查询分析机后填入目标结果。

```bash
dpkg -l | grep -iE 'mysql|mariadb|postgres|tidb'
ss -tlnp
find / -name '*guessdb*' 2>/dev/null
```

**2. 容器内的包清点不在这里复制。** 容器内原有 `lxc-attach -n <容器> -- dpkg -l` 及实例清点操作统一见[Docker 与 LXC 命令速查](/knowledge/docker-evidence-02/)。常见端口包括 MySQL/MariaDB `3306`、TiDB `4000`、PostgreSQL `5432`、TiDB 状态端口 `10080`、PD `2379/2380`、TiKV `20160`。它们只辅助定位：状态端口不是业务查询端口，客户端包不等于服务端已部署，文件搜索未命中也不能排除手工改名或容器内部安装。

**3. 最后的 `find /` 只扫描当前会话可访问的文件树。** `2>/dev/null` 隐藏标准错误，并不证明搜索完整。

**4. 准备写“未发现”前再核对范围。** 首轮可用它快速定位文件。准备写“未发现”前，再核对实际搜索根、不可读目录、未挂载卷，以及未进入的容器根目录或挂载命名空间。需要完整审计时，把错误另存分析目录，不继续忽略。分析机上的 `dpkg` 和 `ss` 不是镜像里的历史安装和监听。

目标会话里的相关包、监听端口和文件名命中路径对上；`2>/dev/null` 藏掉的错误、未挂载卷和未进入的容器仍是缺口，状态端口 `10080` 不是业务查询端口。命令运行的是目标会话或仿真副本而非分析机，客户端包没有写成服务端已部署；三条命令的输出保存，完整审计时另存错误。

## 02 按代码核对 SQLCipher 的密钥与参数

文件头已经不像明文 SQLite，但随机字节还不能直接定成 SQLCipher。先看失败信息，再按代码核对口令和参数。

操作顺序：看文件头和报错，按派生步骤核对候选口令，其他来源逐条回到调用链。


### 02.1 文件头和失败信息的含义

普通 SQLite 的头部应是明文签名，这份文件开头却像随机字节。还没区分加密、损坏、压缩和参数不匹配，就不能选定密钥。

操作顺序：先保存文件头和完整错误，再在 APK 里找实际打开流程，然后才选密钥和参数。

**1. 先按默认加密库的头部来认，不用明文签名那套说法。** 普通 SQLite 的头部是 `SQLite format 3\0`。SQLCipher 默认加密数据库头部，**开头 16 字节保存随机盐，不保留明文 SQLite 签名**；使用明文头部配置时会不同。因此，不能用“SQLite 签名仍在、页大小被盐覆盖”作为默认识别方法。[SQLCipher 设计说明](https://www.zetetic.net/sqlcipher/design/)解释了盐、逐页加密与完整性机制。

```bash
file ./work/chat-db/chat.db
xxd -l 64 ./work/chat-db/chat.db
```

**2. 先保存文件头和完整错误。** 随机字节或 `file is not a database` 只说明当前工具和参数读不出普通 SQLite，不能直接定为 SQLCipher。损坏、压缩、其他加密格式、截断及参数不匹配都可能产生相近现象。

**3. 再查 APK 代码。** 定位 `PRAGMA key`、`openOrCreateDatabase`、`SQLiteDatabase.openDatabase`，核对 SQLCipher 库引用及版本。找到实际打开流程后，再选择密钥和兼容参数。代码里没有这些调用时，停在“当前工具读不出普通 SQLite”。

文件头的前 64 字节、完整错误，以及 APK 里实际的打开调用和库版本对上；只有 `file is not a database` 时还不能定为 SQLCipher，明文头部配置也会不同。识别没有依赖“签名仍在、页大小被盐覆盖”，密钥和参数来自已找到的打开流程；`file`、`xxd` 输出与 `PRAGMA key`、`openOrCreateDatabase`、`SQLiteDatabase.openDatabase` 的代码位置一起保存。

### 02.2 实战：从文件名关系核对候选密钥

应用保存名为 `wk_<账户标识>.db` 的数据库，反编译代码显示它从账户标识派生口令。文件名还只是候选来源，不能直接宣布“文件名就是密钥”。

操作顺序：固定 APK 和数据库，在代码里核对派生步骤，在副本上用对应参数验证可读。

**1. 按这条顺序核对，不跳过派生步骤。**

1. 固定 APK、数据库、WAL、偏好设置和相关账户记录。
2. 在代码中查明是否去掉 `wk_`、是否去掉扩展名、是否拼接设备参数、是否经过 MD5/PBKDF 等派生。保留调用链与编码方式。MD5 在这里若出现，只是派生步骤的名称，不是解密。
3. 在 DB Browser for SQLCipher 等兼容工具中，对副本设置实际候选口令及对应的 SQLCipher 版本、页大小、KDF 和 HMAC 参数。
4. 使用 `SELECT count(*) FROM sqlite_master;` 和表结构验证可读性；再运行数据库与加密页完整性检查，保留完整输出。
5. 比较账户 ID、记录数量及目标业务内容，确认读到的是预期实例，不只看工具是否弹出表名。

**2. 需要 SQL 形式记录参数时，保留操作清单。** 候选口令来自已证明的派生步骤，不在正文固定展示真实秘密。参数还没从代码确认时，不要先设兼容级别。

```sql
-- 先按目标实现确定兼容级别（仅在证据表明采用旧版本默认格式时设置）
PRAGMA cipher_compatibility = 3;
PRAGMA key = '<已核对的候选口令>';
SELECT name, type FROM sqlite_master ORDER BY name;
PRAGMA integrity_check;
PRAGMA cipher_integrity_check;
```

**3. 先定参数，再设口令，然后才读表。** 先按目标实现确定兼容参数，再设置 `PRAGMA key`，之后才读表。顺序不能颠倒。设置后若仍报错，保存完整错误，不改口令去试到能开为止。

**4. 原件不做改密钥和迁移。** 【仅在副本/仿真/授权环境执行】原件不执行 `rekey`、`cipher_migrate`，也不导出覆盖。副本中表结构可读、检查无报错，支持密钥和参数正确；这不证明采集完整，也不证明未显示的历史记录从未存在。

**5. 设置语句没报错，还不等于口令正确。** 设置 `PRAGMA key` 后继续读取 schema 或表页；这一步成功，才实际检验到解密，不能仅凭设置语句未报错认定口令正确。

**6. 两种完整性检查分开保存。** 分别保存 `PRAGMA integrity_check` 的结构检查结果和 `PRAGMA cipher_integrity_check` 的加密页认证结果。运行前记下工具版本，确认它包含 SQLCipher 且支持对应 PRAGMA。普通 SQLite 对未知 PRAGMA 返回空输出，不算通过检查。

代码里的派生步骤、副本上的候选口令参数以及 schema 和完整性检查的输出对上；只弹出表名或 `PRAGMA key` 未报错都不能认定口令正确，普通 SQLite 的空 PRAGMA 输出不算通过。账户 ID、记录数量和业务内容对得上预期实例，原件没有执行 `rekey` 或 `cipher_migrate`；调用链、工具版本和两条 PRAGMA 的完整输出保存，真实秘密不写进正文。

### 02.3 其他密钥来源及边界

文件名这条线已经核过，固定字符串、包名和系统密钥库还可能是别的来源。拿到 XML 或 APK，也不保证能离线导出密钥。

操作顺序：每条候选回到代码，核对编码、截取和版本，系统密钥库依赖设备时单独记下。

**1. 候选来源还包括固定字符串、包名、`shared_prefs` XML、设备参数拼接和 `AndroidKeyStore`。** 每条候选都回到代码验证使用位置、字符编码、截取单位及版本。代码没有使用这个来源时，把它留在候选外。

**2. 系统密钥库可能依赖设备状态或硬件。** 获得 XML 或 APK 不保证能离线导出密钥。不要把“直接试文件名”当作所有移动应用的通用设计。导不出密钥时，写明缺的是设备状态或硬件，不改成文件名尝试。

每条候选密钥在代码里的使用位置、编码、截取单位和版本登记清楚，候选经过调用链核对，不是把文件名当成所有应用的通用口令；`AndroidKeyStore` 依赖设备或硬件时，XML 和 APK 仍不能离线导出密钥。`shared_prefs` 的路径、代码位置和未能导出时的原因一起保存。

<span id="03-表结构字段语义和检索条件"></span>

## 03 按表结构和字段语义取值

库已经能打开，字段是整数时间、数值 IP 还是文本名称还没确认。条件写宽了，会把别的账户一起带出来。

操作顺序：先看版本、表结构和时区，再按已确认的类型转换，模糊检索留下全部候选。


### 03.1 先确认字段再取值

已恢复并确认身份的 MySQL 协议实例里，版本、库、表结构和时区还没看。下面的 SQL 是查询模板，表名要替换成实际存在的对象。

操作顺序：先查版本、库和时间区，看创建语句里的类型，再决定能不能转换。

**1. 在已确认身份的实例上查看版本、库、表结构和时区。** 表不存在时更换为实际对象，不沿用模板里的名字硬查。

```sql
SELECT VERSION(), DATABASE(), @@session.time_zone, @@system_time_zone;
SHOW TABLES;
SHOW CREATE TABLE mac_user;
SHOW CREATE TABLE mac_vod;
```

**2. 先查类型，再查写入代码。** 本例 `user_last_login_ip` 是 `INT UNSIGNED`，`user_reg_time` 是整数，`user_name` 是 UTF-8 文本。

**3. 整数时间和 IP 都要确认单位和编码。** 整数时间按应用写入逻辑确认秒、毫秒或自定义单位。IP 字段同样要确认：它可能保存 `INET_ATON` 结果，也可能保存文本、二进制 IPv6 或自定义编码。字段名只能提示含义，不能决定转换方式。类型对不上时，先不要套表里的函数。

<details>
<summary>展开字段转换前提表</summary>

| 字段 | 可采用的转换 | 前提与常见误读 |
| --- | --- | --- |
| IPv4 数值 | `INET_NTOA(col)`，反向用 `INET_ATON('10.0.5.9')` | 已确认使用相同数字编码；大地址宜为无符号整数 |
| Unix 秒 | `FROM_UNIXTIME(col)` | 会话时区影响显示；不能直接用于毫秒值 |
| 日期显示 | `DATE_FORMAT(t, '%Y/%c/%e')` | `%c/%e` 不补零，只影响显示格式 |
| 用户名称 | 中文、拼音、别名、大小写等组合检索 | 由实际账户记录支持关联，不假设中文名普遍以拼音存储 |
| 金额 | `DECIMAL` 或应用约定的整数最小单位 | 核对小数位、资产与舍入规则，避免二进制浮点累加 |

</details>

**4. 显示转换和页内字节不是一层。** [MySQL IP 函数](https://dev.mysql.com/doc/refman/8.0/en/miscellaneous-functions.html)用于数字与地址的转换；数值的显示语义与数据页内的字节布局是两个层次。

实例版本、当前库、会话时区和系统时区，以及字段的实际类型对上；写入代码还没确认秒或毫秒、数值或文本时，不按字段名直接转换。`user_last_login_ip`、`user_reg_time`、`user_name` 的类型来自 `SHOW CREATE TABLE` 而非字段名；版本查询、建表语句和后来使用的转换及前提一起保存。

### 03.2 实战：关联姓名、末次登录和 IP

业务表结构、账户映射和登录记录都在。只有姓名时，同名的人还没分开；用户表里的“最后登录”也不一定是完整事件。

操作顺序：先用账户 ID 或多种姓名写法定位，保留原值和转换值，时段内的最后一次改查登录日志。

**1. 先用已知账户 ID 定位。** 只有姓名时，分别检索中文、拼音和别名，并记录所有同名候选。

```sql
SELECT user_id, user_name, user_last_login_ip,
       INET_NTOA(user_last_login_ip) AS login_ip,
       user_last_login_time,
       FROM_UNIXTIME(user_last_login_time) AS login_time
FROM mac_user
WHERE user_name IN ('林晓明', 'Lin Xiao Ming');
```

**2. 示例输出要保留原整数。** 账户 `2048` 的名称为 `Lin Xiao Ming`，IP 数值 `167773449` 显示为 `10.0.5.9`。保留原整数与转换值，并以 `SELECT INET_ATON('10.0.5.9');` 反向核对。相同拼音可能对应多人，应结合账户 ID、手机或聊天账号建立映射。反向结果不一致时，停在原整数，不改显示值。

**3. 最后登录字段通常只是最新汇总。** 用户表中的“最后登录”字段往往只是最新汇总状态，不是完整事件表。如果目标是某时间段的最后一次行为，应读取实际登录日志，按时间和稳定主键排序；一条字段值不能恢复它曾经被覆盖的所有旧值。

账户 `2048` 的名称、IP 原值 `167773449` 和显示值 `10.0.5.9`，以及反向核对的结果对上；相同拼音的其他候选和被覆盖过的旧登录值仍是缺口，汇总字段不能代替时段内的登录日志。原整数与 `SELECT INET_ATON('10.0.5.9');` 的结果一致，映射还用了账户 ID 或手机；查询、原值、转换值和登录日志中的排序键一起保存。

### 03.3 便签与本地 AI 应用

手机里的便签库和本地模型目录还没按角色分开。记录里有一个日期，也不等于人已经按这个计划出行。

操作顺序：按表结构读便签，对话只统计用户主动提交的消息，模型身份用文件摘要和加载日志核对。

**1. 便签库常位于 `/data/user/0/com.miui.notes/databases/todo.db`。** 可按表结构读取行程、口令或提醒内容；记录文本含某日期，首先说明用户保存了该计划，不能据此确认实际出行。库不在这条路径时，按实际应用目录找，不把别的库当成便签。

**2. 本地 AI 应用可能把对话放在数据库，把模型放在 `files/models/local` 等目录。** 核对角色字段，只统计用户主动提交的消息；排除系统提示、助手消息、重新生成、重复导入和删除残留。模型文件名、配置名称和实际模型身份也可能不一致，应保留文件摘要、元信息及加载日志。手机路径与 APK 验证见[Android 取证](/knowledge/fic-case-06/)。

便签或对话所在的库、角色字段以及模型文件的摘要和加载日志对上；文本里的日期不能确认实际出行，文件名和配置名称不一致时模型身份还没定。统计排除了系统提示、助手消息、重新生成、重复导入和删除残留；数据库路径、角色字段、文件摘要和加载日志一起保存。

### 03.4 实战：从未知业务库找到候选人员记录

隔离副本里的业务库、网站连接配置、实例版本和表结构都已保全，姓名片段还没对应到稳定主键。库名不能凭网页标题来猜。

操作顺序：先确认实例和字段，模糊检索留下全部候选，再用已确认主键读日期原值。

**1. 下列库、表和字段名为构造示例。** 先检查实际 schema，不能凭网页标题猜数据库名称。Navicat 中分别记录连接类型、主机、端口、用户名及 SSH 页签是否启用。连接成功只证明当前端点和认证可用；宿主机发布端口、容器服务端口与 SSH 端口分别核对。也可在已确认的实验实例查询。连不上或看不到库时，先记权限和端口，不改口令去验证。

```sql
SELECT VERSION(), @@hostname, @@port, DATABASE();
SHOW DATABASES;
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'lab_site'
ORDER BY TABLE_NAME;
SELECT COLUMN_NAME, COLUMN_TYPE, COLLATION_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'lab_site' AND TABLE_NAME = 'customers'
ORDER BY ORDINAL_POSITION;
SHOW CREATE TABLE lab_site.customers;
```

**2. 先把网站配置中的端点与实际实例、表结构、持久目录对应起来。** 配置是连接线索，不是连接成功证明；当前账号看不到某个库，也可能只是权限不足。

**3. 使用 SSH 隧道时，分开记录两个入口。** 使用 SSH 隧道时，分开记录 SSH 入口和数据库入口，具体连接层见[数据库连接与 SSH 隧道](/knowledge/forensic-database-recovery/)。容器实例另外记录宿主机发布地址、发布端口和容器内端口，确认配置实际指向哪一个入口。

**4. 第二步：保留模糊命中的全部候选。** 示例已确认 `customer_id` 是稳定主键，`display_name` 是名称，`birth_date` 是 DATE 字段。按片段检索后，用独立身份材料核对主键。字段名不同就先改对照，不套这三列。

```sql
SELECT customer_id, display_name, birth_date
FROM lab_site.customers
WHERE display_name LIKE '%Lee%'
ORDER BY customer_id;

-- 仅在独立账号材料支持 customer_id=1002 后精确读取
SELECT customer_id, display_name, birth_date
FROM lab_site.customers
WHERE customer_id = 1002;

-- 搜索名称中的字面下划线，明确指定转义符
SELECT customer_id, display_name
FROM lab_site.customers
WHERE display_name LIKE '%!_%' ESCAPE '!'
ORDER BY customer_id;
```

**5. 条件的含义按这张表读，不把一种 LIKE 换成另一种。**

<details>
<summary>展开 LIKE 与条件含义表</summary>

| 条件 | 含义 | 判读边界 |
| --- | --- | --- |
| `LIKE '%Lee'` | 以 Lee 结束 | 不等于任何位置包含 Lee |
| `LIKE '%Lee%'` | 任意位置包含 Lee | 可命中多账号，不能只取首行 |
| `%` / `_` | 任意长度字符串 / 单个字符 | 字面字符需转义；不是正则表达式 |
| `=` 或主键 | 按明确值定位 | 字符串比较仍受类型、排序规则影响；主键与人员身份需另证 |
| 大小写、重音、拼音、别名 | 根据列/表达式排序规则和实际存储 | 不假设名称都存拼音或比较默认区分大小写 |

</details>

**6. 构造判读要留下排除依据。** 模糊结果为 `1001 / Alex Lee` 和 `1002 / Morgan Lee`，独立账号材料对应 `1002`。保留两条候选及排除依据，再引用已确认主键的日期原值。缺少可靠对应关系时交付候选集合，不能凭姓名片段确定人员身份。

**7. 第三步：保留原值，再解释日期。** DATE 通常是日历日期；字符串、整数时间戳、仅年份的字段，各自按表结构和写入代码解释。NULL、零日期和格式错误分列，不补猜生日。展示格式另列一栏，不覆盖原值。不要为展示将名称、口令或数据库值整体转大写；表中有日期，也不证明它就是现实中真实的身份信息。

**8. 在实验副本中使用受限账号，只查询必需字段。** 结果旁记下实例、SQL、主键、行数、原值、类型、排序规则和采集时间，再查 GUI 预览或导出是否限制行数。

**9. 只读事务不等于没有服务日志，也不代替一致性快照。** 【仅在副本/仿真/授权环境执行】不用建表、更新、自动迁移或重置口令去验证历史记录。字符串匹配还要核对排序规则，参见 [MySQL 字符串比较](https://dev.mysql.com/doc/refman/8.4/en/string-comparison-functions.html)。

**10. 后台登录账号表与绑定手机号：先从登录代码找表，再按账号查人。** 在 Java 项目中，沿登录控制器、用户实体、Mapper/XML 或 DAO 读取真实查询；例如看到候选表 `sys_user`，继续核对 `id`、`name`、`phone`、`type`、`state` 是否确为本版本的列。表名相似不证明它就是后台认证使用的表，`state` 数字也不能跨项目套用。

```bash
rg -n -i 'sys_user|@TableName\(|@Table\(|login|verify|password|phone|mobile' ./work/decompiled
```

**11. 看清 SQL 再回数据库核对 DDL。** 看清 SQL 的表名、连接关系、租户/角色和软删条件，再回数据库核对 DDL。手机号字段需要区分绑定手机号、联系方式与登录名；保存原值与记录主键，报告展示时脱敏。

**12. 构造练习表不是目标网站的真实表名。** 下面的 `lab_loan.users` 是构造练习表，不是目标网站的真实表名。本例先按账号精确匹配，保留全部候选，不用 `LIMIT 1` 隐藏同名记录。

```sql
SELECT user_id, login_name, phone, tenant_id, deleted_at
FROM lab_loan.users
WHERE login_name = 'LAB-ADMIN-001'
ORDER BY tenant_id, user_id;
```

**13. 同名多行时按登录 SQL 的规则定位。** 若同名账号有多行，按登录 SQL 实际使用的租户、角色与软删规则定位，再用已确认主键查询。关联到手机号只支持“该记录保存了这一号码”，不直接证明当时持有人或每次登录者。

实例、表结构，以及独立材料已经对应上的主键和日期原值对上；只有姓名片段时交付候选集合，手机号只说明记录里保存了这个号码，`state` 不能跨项目套用。模糊结果保留了 `1001 / Alex Lee` 和 `1002 / Morgan Lee`，精确读取用的是已确认主键，没有用 `LIMIT 1` 藏掉同名行；连接类型和端口、SQL、主键、行数、原值、排序规则保存，口令重置和建表不拿来验证历史。

<span id="04-服务不可用时读取原始页"></span>

## 04 服务起不来时，从原始页读候选记录

服务起不来，记录还在页、键值或文件系统块里。还没认出存储格式和字节序，字符串命中不能当成当前行。

操作顺序：先认出存储格式和编码，再在副本里按偏移读上下文，结构明确后才做数值转换。


### 04.1 先识别存储格式

服务已经起不来时，先把实例恢复出来。带上数据目录、配置和版本去[数据库恢复](/knowledge/forensic-database-recovery/)按实例恢复主线尝试，能拿到可读实例就回到 §03；只有恢复仍不可行时，才用本节从原始页读候选记录。

手里是 `.ibd`、TiKV、SQLite 或 ZFS 里的数据文件，页大小、压缩和编码都还没确认。直接搜索字符串，可能错过压缩或加密的记录。

操作顺序：先对上存储对象要解析的结构，再按已验证的编码选择字节序。

**1. 按存储对象选择要解析的结构。** 限制那一列还没排除时，不把文件当成可以直接读出行的表：

<details>
<summary>展开存储对象解析表</summary>

| 存储对象 | 需要解析的结构 | 限制 |
| --- | --- | --- |
| InnoDB `.ibd` 或系统表空间 | 页头、记录格式、索引、字段定义及溢出页 | 常见页大小为 16 KiB，也有其他配置；压缩、加密、版本会影响解析 |
| TiDB/TiKV | TiKV/RocksDB 的键值编码、SST、日志、区域与时间版本 | JSON 集群元数据不是业务行格式；原始字符串可来自旧版本或日志 |
| SQLite | 文件头、B-tree 页、cell、serial type、varint 与溢出页 | WAL、freelist 和未分配空间属于不同事务或恢复层次 |
| ZFS 内的数据文件 | vdev/数据集/块映射与实际数据库文件 | 压缩、块重用和多设备映射会阻止直接字符串搜索 |

</details>

**2. 字节序纠正。** 数据库整数并非一律小端。SQLite 页头及许多固定宽度字段使用大端，行记录还使用 varint；InnoDB 有自身编码；TiKV 键编码也依字段与协议而定。只有验证“某字段在某种记录内以何种编码保存”后，才可选择 `'<I'` 或 `'>I'`。格式细节以 [SQLite 文件格式](https://www.sqlite.org/fileformat.html)等对应规范核对。编码还没验证时，先不要解整数。

这份材料的存储对象、页或键的结构，以及某个字段已经验证的编码对上；压缩、加密、版本或 ZFS 映射还没排除时，字符串搜不到也不等于没有记录。`'<I'` 或 `'>I'` 的选择对应已经验证的那种记录编码而非默认小端；文件类型、页大小或编码说明和用来核对的规范位置一起保存。

### 04.2 实战：在数据副本中定位候选记录

数据库服务无法启动，但已有存储池或数据文件副本。已知账户别名和集群版本键还只是搜索词，命中偏移不是当前行。

操作顺序：先按字符串定位偏移，换成实际偏移读上下文，记录布局明确后才转换 IP。

**1. 先搜索已知账户别名与集群版本键，再验证记录结构。** 不把搜索命中直接当成当前行。没有命中时，接着查压缩、加密或不同编码，不写成库里没有这个人。

```bash
LC_ALL=C grep -aob 'Lin Xiao Ming' ./work/data-file.bin
LC_ALL=C grep -aob '"status_port"' ./work/data-file.bin
# 使用实际命中偏移读取上下文；这里的 4096 只是示例
xxd -s 4096 -l 256 ./work/data-file.bin
```

**2. 示例 JSON 只提供候选版本与地址。** 示例 JSON 含 `version`、`git_hash`、`ip` 和 `status_port`，可提供集群组件候选版本与地址。需要结合程序、配置和日志判定它属于哪个实例、哪次部署；重复副本或旧配置不能直接代表采集时版本。

**3. 先运行定位命令，再查看命中附近的字节。** `grep -aob` 的 `-a` 把二进制输入按文本处理，`-o` 只显示命中片段，`-b` 给出字节偏移；`LC_ALL=C` 固定字节级匹配环境。

**4. 拿到偏移后替换示例起点。** 把 `xxd -s 4096 -l 256` 的示例起点换成实际命中附近位置，读取 256 字节并保留前后上下文。偏移只属于本次输入文件，不是整盘或分区全局偏移。这两步只找位置，尚未解析数据页或事务。

**5. 只有布局明确才做下面的转换。** 针对用户记录，依次确认所属文件/页、表结构、记录头、字段边界、主键、删除标记与版本信息。只有记录布局明确说明四字节是小端 IPv4 数值时，才可进行如下转换；这里的字节演示来自自定义导出格式，不作为 InnoDB/TiKV 通用格式。

```python
import ipaddress
import struct
raw = bytes.fromhex("09 05 00 0A")
value = struct.unpack("<I", raw)[0]
print(value)
print(ipaddress.IPv4Address(value))
```

**6. 示例输出再和恢复实例核对。** **示例输出：** `167773449` 和 `10.0.5.9`。再与恢复实例的 `INET_NTOA`、账户 ID 和登录日志核对。无法确认页归属或时间版本时，应写“发现候选残留记录”，而不是“当前数据库中的最后登录地址”。没有字符串命中也不能排除压缩、加密或编码不同的记录。

本次输入文件中的命中偏移、附近字节，以及布局明确时得到的 `167773449` 和 `10.0.5.9` 对上；页归属或时间版本未确认时只写“发现候选残留记录”，偏移不是整盘全局偏移。转换前提是四字节小端 IPv4，并与 `INET_NTOA`、账户 ID、登录日志核对过，这组字节不是 InnoDB/TiKV 的通用格式；`grep -aob` 的偏移、`xxd` 上下文和转换所用的原始字节一起保存。

<span id="05-聚合统计与多表关联"></span>

## 05 统计前先固定口径和分母

要报的是某一天的注册数、最近一条，或已付款金额，口径和分母还没固定。关联一多，行数和金额都会被放大。

操作顺序：先固定时区和分母，再看关联是否一对多，订单和借贷各自用已确认的状态统计。

时间列带时分秒时，上界写成下一天，避免字符串日期把当天白天的记录丢掉。操作次数在存在次数字段时对该字段求和，行数是另一列。流水规模先对金额取绝对值。登录人数对用户去重。先取投注最多的若干类型、再数开奖次数时，类型来自投注表，次数来自开奖表。关系表用手机号、证件号或工号建图；直接下线是子节点数，全部下游是向下遍历且不重复的节点数。工具导出的表和 SQL 不一致时，以库为准。启用数和包含停用项的总数分开报。

```sql
WHERE create_time >= '2020-01-01 00:00:00'
  AND create_time < '2020-07-01 00:00:00'
```

分组查询报错时，把查询改成完整分组。不在仿真库上关闭 `ONLY_FULL_GROUP_BY` 来让页面出数。副本里重建业务账户时，只授予该业务库；认证插件只在驱动握手报不兼容时再看。这些改动【仅在副本/仿真/授权环境执行】，临时口令和手写验证码不写进历史结论。


### 05.1 按日期统计并保留分母

要比较注册数量最多的日期。时区、空值和异常值还没单列，首行最大也不代表没有并列。

操作顺序：先记时区、空值和总数，再按日期分组，并列的最大值全部留下。

**1. 先记录时区、有效时间范围、空值和异常值，再统计。** 以下示例使用 UTC；若目标口径为其他时区，明确设置并记录对应条件。会话时区没固定时，先不要比较跨日结果。

```sql
SET time_zone = '+00:00';
SELECT COUNT(*) AS total_rows,
       SUM(user_reg_time IS NULL) AS null_times
FROM mac_user;

SELECT DATE_FORMAT(FROM_UNIXTIME(user_reg_time), '%Y/%c/%e') AS reg_date,
       COUNT(*) AS cnt
FROM mac_user
WHERE user_reg_time IS NOT NULL
GROUP BY reg_date
ORDER BY cnt DESC, reg_date ASC;
```

**2. 判读时保留并列和异常。** 首行计数最大不代表没有并列；保留完整排序或所有同最大值的日期，不只用 `LIMIT 1` 隐去并列。日期转换失败、零值或不合理未来时间应另列，不能悄悄算入某一天。[FROM_UNIXTIME](https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html)采用会话时区，因此跨日统计必须固定同一基准。

同一时区下的总行数、空时间行数，以及每个日期的计数和并列的最大值对上；转换失败、零值和未来时间还没另列时不能算进某一天。没有用 `LIMIT 1` 藏掉并列，`FROM_UNIXTIME` 使用的会话时区已经记下；时区设置、两段查询的完整结果和另列的异常值一起保存。

### 05.2 最近记录、关联表与分类层次

要拿最近一条登录，或把视频和分类联起来。同一时间可能有多条，关联后行数也可能变多。

操作顺序：先确认标识属于哪一层，关联前后分别数行，LIMIT 1 只用于确定的一条展示。

**1. 先跑这三类查询，字段名按实际表结构替换。** 表或列不存在时停在结构，不改名硬连。

```sql
-- 最近记录：同一时间可能多条，稳定主键用于展示排序
SELECT * FROM login_events
WHERE user_id = 2048
ORDER BY event_time DESC, event_id DESC
LIMIT 1;

-- 将业务实体与其分类分别展示
SELECT v.vod_id, v.type_id, v.type_id_1, v.vod_name, v.vod_en,
       t.type_name, t.type_en
FROM mac_vod AS v
LEFT JOIN mac_type AS t ON v.type_id = t.type_id
WHERE v.type_id = 3 OR v.type_id_1 = 3;

-- 保留左表记录：实际字段与关联基数需先查表结构
SELECT a.id, a.x, b.y FROM a LEFT JOIN b ON a.id = b.aid WHERE a.id = 2048;
```

**2. 先确认标识层次。** `vod_en` 属于视频，`type_en` 属于分类，不能因两者都像拼音而互换。`type_id` 与 `type_id_1` 的层级由应用逻辑核对。

**3. 执行关联查询前后，分别统计行数和主键去重数。** 数量增加时先查一对多关系。LEFT JOIN 会保留无匹配的左表行，但 WHERE 若要求右表字段等于某值，仍会过滤这些 NULL 行。[MySQL JOIN 语义](https://dev.mysql.com/doc/refman/8.4/en/join.html)说明这一行为。

**4. 问号不是可以直接执行的字面值。** `?` 是准备语句接口的参数占位符，普通客户端中不要把它当 SQL 字面值直接执行。

**5. “最近记录”的 LIMIT 只打破展示并列。** “最近记录”示例的 `LIMIT 1` 用于按时间、再按稳定主键选出一条确定展示行；若要回答“同一最新时间的全部记录”，先取最大时间，再保留该时间下全部主键。主键只打破展示并列，不证明同一时间戳的真实先后；时间精度不足或来源日志另有顺序时，把这些限制随结果交付。

视频和分类各自的标识、关联前后的行数，以及按时间加稳定主键选出的那一条对上；要同一最新时间的全部记录时，还缺这个时间下的全部主键，`type_id` 和 `type_id_1` 的层级还要应用逻辑。行数增加时已经查过一对多，WHERE 没有把 LEFT JOIN 的 NULL 行悄悄滤掉却仍称为外连接结果；关联前后的行数、主键去重数和时间精度不足时的说明一起保存。

### 05.3 实战：核对订单状态、付款事件与通道映射

已有某业务库的一致快照、应用订单/付款代码、表结构和事件日志，需要统计已付款订单并辨认通道。状态数字还没有跨网站的通用含义，关联后金额也容易被乘开。

操作顺序：先列状态分布，在原表上算金额基线，查映射基数后再对付款事件。

**1. 证据位置和构造示例先分开。** 证据位置包括业务库 `orders`、`merchants`、`customers`、`payment_events`、`payment_mapping`，以及应用枚举、付款回调和退款处理。以下库、表、字段和值均为构造示例，先按实际 DDL 和写入代码建立对照；仅在代码证明 `orders.status='paid'` 代表目标状态时使用相应过滤。代码没有证明时，不用这个过滤。

**2. 先列状态，再汇总金额。** 从应用逻辑确认创建、付款完成、交付、取消、退款、软删和超时分别对应什么值；数字状态没有跨网站通用含义。

**3. 保存各表快照和两类差异。** 保存各表快照、状态分布、关联键、时间单位、币种和金额类型。订单表可能只有最后状态，付款回调表可能一笔交易多条事件；当前 paid 不等于指定历史时点仍未退款。先解决这两类差异，再统计。

**4. 历史状态和应用显示分开核对。** 需要核对历史状态时，用保全备份或 binlog 对照变更；需要核对应用显示时，对照页面字段与原记录。统计口径不能只按当前页面结果倒推。

```sql
-- 本例已确认 amount 是 DECIMAL(18,2)，created_epoch 是 Unix 秒
-- SET 仅固定本会话显示，不改表内原值
SET time_zone = '+00:00';
SELECT status, currency, COUNT(*) AS order_rows,
       COUNT(amount) AS known_amount_rows,
       COUNT(*) - COUNT(amount) AS null_amount_rows,
       SUM(amount) AS order_amount
FROM lab_site.orders
GROUP BY status, currency
ORDER BY status, currency;

-- 在订单原表上计算基线，避免关联后放大金额
SELECT currency, COUNT(*) AS paid_order_rows,
       COUNT(*) - COUNT(amount) AS null_amount_rows,
       SUM(amount) AS paid_order_amount
FROM lab_site.orders
WHERE status = 'paid'
GROUP BY currency;
```

**5. 先看金额类型与空值，再运行 `SUM`。** 它忽略 NULL，没有匹配行时返回 NULL；不要预先把未知金额全部改为 0。结果中分开记录空集合、金额未知和实际零金额。

**6. 整数和 DECIMAL 保持精确值。** 整数和 DECIMAL 求和保持精确值，FLOAT/DOUBLE 仍是近似值，事后转成 DECIMAL 也找不回已丢精度。若字段保存最小货币单位整数，先保留整数合计，再按已确认比例展示；不同币种分别统计。类型与空值规则见 [MySQL 聚合函数](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html)。

**7. 再检查关联基数。** 确认商户和用户关联列是否有唯一约束；不能因字段名像 ID 就认定一对一。通道映射尤其可能缺失或一对多，先查每笔订单匹配了几条：

```sql
SELECT o.order_id, o.payment_code, COUNT(pm.map_id) AS mapping_rows
FROM lab_site.orders AS o
LEFT JOIN lab_site.payment_mapping AS pm
       ON pm.input_code = o.payment_code
WHERE o.status = 'paid'
GROUP BY o.order_id, o.payment_code
HAVING COUNT(pm.map_id) <> 1;

SELECT o.order_id, o.status, o.amount, o.currency,
       o.created_epoch, FROM_UNIXTIME(o.created_epoch) AS created_utc,
       m.merchant_name, u.display_name, o.payment_code, pm.channel_name
FROM lab_site.orders AS o
LEFT JOIN lab_site.merchants AS m ON m.merchant_id = o.merchant_id
LEFT JOIN lab_site.customers AS u ON u.customer_id = o.customer_id
LEFT JOIN lab_site.payment_mapping AS pm ON pm.input_code = o.payment_code
WHERE o.status = 'paid'
ORDER BY o.order_id, pm.map_id;

-- 查未匹配通道的订单，保留 NULL 代码作为待解释项
SELECT o.order_id, o.payment_code
FROM lab_site.orders AS o
WHERE o.status = 'paid'
  AND NOT EXISTS (
    SELECT 1 FROM lab_site.payment_mapping AS pm
    WHERE pm.input_code = o.payment_code
  )
ORDER BY o.order_id;
```

**8. 先读映射计数。** 本例 `map_id` 是已确认的非 NULL 主键，0 表示未命中，超过 1 表示一单对应多个映射。

**9. 不要在展开结果上直接 SUM 金额。** LEFT JOIN 仍保留缺商户、用户或通道的订单，但下面第二段明细可能展开为多行。先比较原表订单数、明细行数、去重订单 ID 数，**不要在展开结果上直接 SUM 金额**。

**10. 多映射和缺失映射分开处理。** 遇到多映射，查版本、启用区间和应用选择逻辑。随便取 MIN、首行或 DISTINCT 金额只会掩盖问题。

查缺失映射时，先检查子查询是否含 NULL。`NOT IN (子查询)` 遇到 NULL 可能得到 UNKNOWN，把本该保留的候选过滤掉。

本例用相关 `NOT EXISTS` 查“没有相等匹配”的记录。代码为 NULL 只说明缺少关联依据，不直接等于无效付款。若把子查询当标量值使用，先确认它只返回一行。语义见 [MySQL 子查询与 NULL](https://dev.mysql.com/doc/refman/8.0/en/subquery-optimization-with-exists.html)。

**11. 最后核对付款事件。** 按实际支付流水号、事件主键、回调状态、币种、金额、事件类型及时间区分付款、重复通知、失败与退款。订单金额汇总与付款事件金额汇总分开交付；一笔订单多次尝试付款或多条回调时，不能将每条事件都算成一次成功收款。去重需由唯一流水及应用处理规则支持，不能按“金额相同”去重。若分析净额，明确退款、手续费与部分退款是否属于口径；缺字段时保留不确定范围。

**12. 构造判读与验证。** 假定原表有三笔目标状态订单；一笔没有商户映射，一笔通道代码对应两条记录。INNER JOIN 会丢掉缺商户订单，展开后的 LEFT JOIN 又可能多出一行，均不能直接充当订单计数或金额总额。保存三笔订单的主键及原值、缺失/多重映射清单、付款事件对照与 SQL，再用原表基线核对。时间展示固定 UTC，同时保留整数；毫秒、DATE/DATETIME、本地时区字段与事件日志分别解释，FROM_UNIXTIME 不会自动修正单位或历史时区。

**13. 使用受限读取账户查询快照。** 【仅在副本/仿真/授权环境执行】不为报表删除“异常”行、补齐关联对象或修改状态。表内快照只支持该采集时点的状态，历史支付是否已提交仍需事件、日志或备份互证。HTTP 200 或页面上的已付款也不能代替这张快照。

原表上按状态和币种的订单数、金额基线，以及每笔订单的映射行数对上；映射不是恰好一条或付款事件有重复回调时，不把展开行或每条事件当成成功收款，当前 paid 也不等于历史时点仍未退款。金额 `SUM` 在原表基线上，空值、未知金额和零金额分开，缺失映射用的是 `NOT EXISTS` 而不是被 `NOT IN (子查询)` 里的 NULL 滤掉；状态分布、三笔示例的主键和原值、映射清单、付款事件对照和 SQL 一起保存。

### 05.4 借贷业务：人数、放款、还款与服务费分别统计

已有借贷类应用代码、订单/客户/放款/还款表、费用配置和回调日志，需要解释成功业务数量和相关金额。申请成功、审核通过、放款成功和还款结清还没按代码分开，上一节的已付款条件也不能套过来。

操作顺序：先沿代码确定每种成功，在各基表分别汇总，再按一单复核后才做全量。

**1. 先沿状态枚举、处理函数与流水确定含义。** 先沿状态枚举、处理函数与流水确定“申请成功、审核通过、放款成功、还款结清”的含义；不能把订单创建或接口返回成功直接解释为资金已到账，也不将上一节的 `paid` 条件直接套到另一业务。接口返回成功仍只是返回，不是到账。

**2. 要统计的对象、依据和易混范围先列开。**

| 要统计的对象 | 计数与金额依据 | 易混淆的范围 |
| --- | --- | --- |
| 借款人和申请单 | 经核对的客户标识、申请主键及目标时段 | 同一客户多笔申请；合并身份的规则须有证据，不能把订单数称为人数 |
| 成功放款 | 放款流水、成功状态、币种、实际金额、到账或渠道回执 | 审核通过、待放款、尝试失败与重复回调不属于同一状态 |
| 已还和未还 | 还款流水、冲正/退款、分期、订单与期次关系 | 一单多次或部分还款；当前未结清不自动说明某个历史时点逾期 |
| 利息与服务费 | 原费用字段、计费配置、计算代码、实际收取/退回记录 | 应收与实收、固定费用与比例、计费天数、舍入和最小货币单位分别核对 |

**3. 先分别统计，再关联。** 在各基表确认主键、状态、币种和金额。放款流水与还款流水各自按已确认关联键汇总，汇总结果再与订单一对一连接。

**4. 不要把多条放款和多条还款乘在一起再求和。** 不要同时连接一单的多条放款和多条还款后求和：它们会产生乘积行。重复事件按流水号、渠道和处理逻辑判断，保留原记录及去重清单。

**5. 费用配置只说明拟采用的规则。** 实际收费还要找资金记录，不能把“费率 × 本金”直接写成已收金额。

**6. 先复核一单，再核对全量。** 选已有订单，依次对照申请、放款、还款、费用和页面字段。单笔口径对应后，用相同时段及角色范围核对全部数量。

**7. 金额同时保留原值和复算值。** 金额同时保留原值、复算值、币种、单位、精度、舍入点与差异。缺渠道回执、历史状态或费用字段时，分别列出缺口。

**8. 首次额度、逾期费率：先找规则，不从当前余额猜。** 先在配置表、应用配置和计算代码中搜索“初始额度、首次借款、逾期、费率”。配置表可能叫 `global_config`；核对 `config_id`、`config_key`、`content`、`title`、`type` 和更新时间后，读命中项的完整内容，再找代码实际读取的 key。

- 首次借款额度：确认规则适用于新用户、首笔成功借款还是首次审核；默认授信上限、可选档位、当前可用余额与首笔实际借款金额分开列。
- 逾期费率：保存原始数值和单位，再核对按日/按月、百分数/小数/万分数、本金或未还金额、宽限期、封顶与生效版本。例如构造值 `0.001/日` 是每天 0.1%，不是每天 0.001%。
- 当前配置只能先说明查询时规则。历史订单使用什么费率，还要对照订单保存的费率、当时配置或计算代码，不能把今天的规则套回全部旧订单。

**9. 额度种类与渠道数量：列全再数，停用项不能悄悄漏掉。** 完整导出配置行及主键，核对页面是否分页、筛选或只显示启用项。“禁用”可能是下一步按钮动作，不一定说明这一行目前已禁用；“启用”同理。当前状态以字段定义、界面逻辑和实际值共同核对。

额度至少分别给出配置条目数、不同额度值数、启用条目数；同额但不同期限/产品可能是不同档位。渠道至少分别给出配置总数、启用数和历史订单引用的渠道 ID 数。软删、租户、产品和重复名称按任务范围说明，不把页面当前页行数当总数。订单保存渠道 ID 只证明引用关系；是否实际调用渠道，还看流水与回执。

**10. 构造 SQL：把要数的对象和要加的金额写出来。** 下列 `lab_loan` 是自建练习库，不表示目标网站字段已确认；使用前按真实 DDL 和业务代码建立字段对照。本例 `status='completed'` 表示已确认的目标完成状态；`principal_cents`、`service_fee_cents`、`amount_cents` 是整数“分”，`service_fee_cents` 已核对为实际收取服务费。真实字段是应收或浮点数时，不直接套用。

```sql
-- 1. 先看状态分布，保存全部枚举，不能默认数字状态的含义
SELECT status, currency, COUNT(*) AS order_rows
FROM lab_loan.orders
GROUP BY status, currency
ORDER BY status, currency;

-- 2. 已确认user_id=1002后，核对这个用户完成了几笔
-- 完成订单次数不是回调条数；若任务问借款/结款，先确认对应状态
SELECT currency, COUNT(*) AS completed_orders,
       COUNT(principal_cents) AS known_amount_rows,
       SUM(principal_cents) AS completed_amount_cents
FROM lab_loan.orders
WHERE user_id = 1002 AND status = 'completed'
GROUP BY currency;

-- 3. 全部完成订单：人数、订单数与金额同时列出
SELECT currency, COUNT(*) AS completed_orders,
       COUNT(DISTINCT user_id) AS completed_users,
       COUNT(*) - COUNT(principal_cents) AS unknown_amount_rows,
       SUM(principal_cents) AS completed_amount_cents
FROM lab_loan.orders
WHERE status = 'completed'
GROUP BY currency;

-- 4. 还款从还款流水基表求和；本例已确认流水不含重复通知
SELECT currency, COUNT(*) AS successful_repayment_events,
       COUNT(*) - COUNT(amount_cents) AS unknown_amount_rows,
       SUM(amount_cents) AS repaid_amount_cents
FROM lab_loan.repayments
WHERE state = 'succeeded' AND event_type = 'repayment'
GROUP BY currency;

-- 5. 额度：配置行、不重复数值、启用行三个不同结果
SELECT COUNT(*) AS configured_levels,
       COUNT(DISTINCT amount_cents) AS distinct_amount_values,
       COUNT(CASE WHEN enabled = 1 THEN 1 END) AS enabled_levels,
       COUNT(*) - COUNT(amount_cents) AS unknown_amount_rows
FROM lab_loan.credit_levels;

-- 6. 渠道：定义数量、启用数量与历史引用数量分开
SELECT COUNT(*) AS configured_channels,
       COUNT(CASE WHEN enabled = 1 THEN 1 END) AS enabled_channels
FROM lab_loan.channels;
SELECT COUNT(DISTINCT channel_id) AS historically_referenced_channel_ids
FROM lab_loan.orders;

-- 7. 完成订单的实际服务费：保留分的精确合计，再换算/取整展示
-- 本例规则是求和后四舍五入到元；不是逐笔取整后求和
SELECT currency, COUNT(*) AS completed_orders,
       COUNT(*) - COUNT(service_fee_cents) AS unknown_fee_rows,
       SUM(service_fee_cents) AS service_fee_cents,
       ROUND(SUM(service_fee_cents) / 100.0, 0) AS service_fee_whole_units
FROM lab_loan.orders
WHERE status = 'completed'
GROUP BY currency;
```

**11. 这组展示表达式按 MySQL 的整数或 DECIMAL 使用。** 这组金额展示表达式按 MySQL 的整数/DECIMAL 字段使用：`100.0` 是精确数值字面量，不是指数形式的浮点数；仍以原始“分”的 SUM 为核验依据。其他数据库的除法、数值类型和 ROUND 行为可能不同，先验证工具与类型，不将 SQLite 小额构造查询通过当作 MySQL 精度已经实测。[MySQL精确数值运算](https://dev.mysql.com/doc/refman/8.0/en/precision-math-expressions.html)

**12. 这样核对结果。**

1. “总金额”先确认是申请金额、本金、实际放款还是实收还款；单位为分时，精确合计后除以 100 展示元。币种不同分别求和。
2. 同一笔还款有多条回调时，用实际流水号、事件主键及业务去重规则核对，不用 `SUM(DISTINCT amount)` 消除重复金额。
3. 退款、冲正与部分还款另列；累计还款、净还款和已结清订单本金不是同一个结果。
4. `SUM` 忽略 NULL；空集合和全为 NULL 可能返回 NULL，不能直接写 0。`unknown_amount_rows` / `unknown_fee_rows` 非 0 时说明合计未覆盖未知金额。
5. 题目要求整数，保留原始精确合计及舍入规则；若代码规定逐笔取整，就逐笔复算。金额类型为 FLOAT/DOUBLE 时先记录精度风险，不靠最后一层 CAST 假装原值精确。
6. 在明细中保留目标主键、状态、金额原值和范围，独立复算后再比对后台仪表盘。仪表盘数字本身不能说明是否过滤了停用项、软删、租户或只取当前页。

**13. 仿真数据不计入历史统计。** 仿真新增的登录、验证码和测试订单不计入历史统计。需要验收页面重构时，按[网站重构](/knowledge/forensic-website-reconstruction/)核对已有记录的展示，不把实验数据混入结论。【仅在副本/仿真/授权环境执行】为验收改页面或写测试订单时，只改副本并单独登记。

人数、订单数、放款、还款和服务费各自的基表、状态、币种和整数合计对上；渠道回执、历史费率或费用字段缺失时分别列缺口，`0.001/日` 这类当前配置不能套回全部旧订单，页面当前页不是总数。没有把 `paid` 套到借贷业务，也没有用 `SUM(DISTINCT amount)` 去掉重复金额，`unknown_amount_rows` 和 `unknown_fee_rows` 已经看过；配置键、DDL 对照、各段 SQL 的原始“分”合计和与仪表盘比对时的过滤说明一起保存。

<span id="06-枚举所有端点与核对部署状态"></span>

## 06 枚举连接端点并核对主备数据差异

端点清单已经列过，主库和备份库的图片记录还没用同一套条件比较。

操作顺序：先列出全部连接端点，再用相同字段和条件比较主库和备份库的图片记录。




### 06.1 实战：比较主库与备份库的图片记录

主库和备份库都能打开，图片路径和文件还没用同一业务 ID、同一条件比过。32 位十六进制的文件名也不等于这份文件的 MD5。

操作顺序：列出全部端点，分别恢复主库和备份库，用相同字段比较路径、时间和摘要。

**1. 从现存和历史配置列出全部连接端点，核对名称解析、监听及进程身份。** 端点对不上进程时，先不要把两次查询当成同一个实例。

**2. 分别恢复主、备实例，记录库名、版本和适用时间。**

**3. 以相同业务 ID 和查询条件读取图片路径、文件名、修改时间和记录状态。**

**4. 固定图片文件并计算摘要，检验路径指向的对象，而不是把 32 位十六进制文件名直接称为 MD5。** 摘要算法以实际计算为准。MD5 这个词若出现在文件名长度上，不是解密，也不是已经算出的摘要。

**5. 比较快照时间、复制延迟、删除状态与查询范围，解释差异能支持什么。**

**6. 输出差异时带上两端的查询。** 输出“主库未命中、备份库保存一条相关记录”时，同时给出两端 SQL、条件、行数和时间范围。只有备份中的旧版本和主库变化过程相互印证，才进一步讨论记录删除或替换；单一差异仍有其他解释。

**7. 两次连接没有共同事务快照。** 先固定主库和备份库各自的可读状态，再用相同字段、条件、排序逐项比较。两次连接、两个实例没有共同事务快照，因此要各自记录采集时点。

**8. 路径和文件哈希分开核对。** 数据库中的图片路径与实体文件哈希分开核对：先确认路径解析基准和所在卷，再记录大小、哈希及读取错误。一端缺卷或只有旧备份时，只说明已读两份材料有差异，不据此认定实时主备不同步。

两端用同一业务 ID、同一条件和排序读到的路径、文件名、时间和记录状态，以及文件摘要对上；只有一端有记录时，还要快照时间、复制延迟和删除状态，缺卷时不写成实时主备不同步。两端 SQL、条件、行数、时间范围和采集时点都在，十六进制文件名没有被叫做 MD5；端点清单、两份查询、文件大小、哈希和读取错误一起保存。
