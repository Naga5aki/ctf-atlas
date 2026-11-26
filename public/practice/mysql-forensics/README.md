# MySQL 取证查询自建练习

这组材料完全由构造数据组成，不包含真实检材。`schema.sql` 建立 `forensic_lab` 的六张 InnoDB 表；`queries.sql` 只包含 `SELECT` 与连接级 `SET SESSION time_zone`。订单、提现、充值与赠送属于不同记录粒度，不能直接合并后求和。

## 下载材料

- [建表与样本数据 schema.sql](/practice/mysql-forensics/schema.sql)
- [15 组只读查询 queries.sql](/practice/mysql-forensics/queries.sql)
- [手工预先固定的期望 expected-results.json](/practice/mysql-forensics/expected-results.json)
- [练习说明 README.md](/practice/mysql-forensics/README.md)

表规模：6 个用户、9 个订单、13 条订单明细、8 条提现、8 条充值或赠送、9 条登录事件。样本包含 NULL 收入与手机号、手机号前导零、同用户多单、同额订单、多明细、多提现、同日重复登录、软删除、退款、未支付、无提现用户与无订单用户。

## Kali / Linux 操作

先把三个素材文件下载到同一目录。下面的连接参数指向自行建立的独立实验实例；将 `LAB_USER` 替换为该实例的实验账号。`-p` 始终交互输入，不把口令写入命令或材料。`schema.sql` 使用固定实验库名，不包含删库语句；首次导入应使用尚不存在的 `forensic_lab`。

```bash
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=LAB_USER

# 在独立实例建立样本库。
mysql --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p --default-character-set=utf8mb4 < schema.sql

# 保留列名、原始值、每组 case_id 与结果，方便逐组核对。
mysql --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p --default-character-set=utf8mb4 \
  --batch --raw forensic_lab < queries.sql > original.tsv

less original.tsv
less expected-results.json
```

`queries.sql` 每组先输出唯一 `case_id`，随后输出列名与结果。期望 JSON 的每个 `rows` 单元格均采用 MySQL `--batch --raw` 的文本表示；字符串 `"NULL"` 表示查询实际输出的 SQL NULL，不等于数据库内的字符串 `NULL`。查询对结果行显式排序，并固定会话 UTC；原始数据库字段没有被覆盖。

## 核对口径与反例

| 标记 | 核对内容 | 手工期望与判读 |
| --- | --- | --- |
| Q01 | `paid` 且未软删除的订单 | 5 单、4 用户、金额 `450.00`。零金额已支付单仍计入订单数。 |
| Q02 | `COUNT(*)` / `COUNT(DISTINCT user_id)` / `COUNT(paid_at)` | 全部 9 条订单、5 个下单用户、7 个非 NULL 支付时间；非 NULL 时间不是已支付状态的替代条件。 |
| Q03 | 先按用户聚合，再用 HAVING 筛组 | 用户 1：2 单、`200.00`。 |
| Q04 | 三张子表分别聚合，再 LEFT JOIN 用户 | 用户 1 支付 `200.00`、审核通过提现 `100.00`、充值 `350.00`、赠送 `20.00`；用户 5 的空子表仍保留。 |
| Q05 | 半开日期区间 `[2024-01-01, 2024-01-03)`，按日用户去重 | 第一日 3 次登录 / 2 用户；第二日 4 次登录 / 3 用户；结束边界上的登录被排除。 |
| Q06 | 用户去重活跃天数 | 用户 1 为 2 天；用户 2、3、6 各为 1 天。 |
| Q07 | `CHAR_LENGTH` 减 `REPLACE` 后字符长度 | 构造字符串 `用户甲甲` 中 `甲` 出现 2 次；单字符与多字符 token 的公式不能混用。 |
| Q08 | IP 与 UTC Unix 时间，原始字段并列保留 | `2130706433` → `127.0.0.1`；`2024-01-01 00:00:00` → `1704067200`。 |
| Q09 | 用户表自关联直属父用户 | 用户 2、3 的父用户为 1；用户 4、6 的父用户为 2；用户 1、5 保留 NULL 父关系。 |
| Q10 | HEX、字符长度、字节长度与手机号 | `用户甲甲` 是 4 字符 / 12 UTF-8 字节；`000006` 保留前导零，不能当数值转换。 |
| Q11 | 错误：订单直接 JOIN 多条明细后求和 | 9 条关联行、5 个真实订单，错误金额 `800.00`；重复的是订单记录，不是业务交易增加。 |
| Q12 | 错误：用 `SUM(DISTINCT amount)` 修复 JOIN | 正确 `450.00`，金额去重后却为 `350.00`；两笔独立 `100.00` 订单被误合并。 |
| Q13 | 错误：订单与提现同时一对多 JOIN | 用户 1 变成 4 行，支付误计 `400.00`、提现误计 `200.00`；对照 Q04。 |
| Q14 | NULL 与统计分母 | 6 用户、4 个已知收入、5 个已知手机号；已知收入合计 `1700.00`、平均 `425.00`。 |
| Q15 | 支付白名单、退款、软删除对照 | 正确 `5 / 450.00`；排除 pending 但混入退款为 `6 / 500.00`；漏掉软删除条件为 `6 / 520.00`。 |

Q04 的 `synthetic_net` 仅是本练习明确约定的算式：`COALESCE(收入,0) + 充值 + 赠送 - 未软删已支付金额 - 审核通过提现`。它不是由字段名推断出的真实账户余额，NULL 收入仍单列保留为 `income_raw`。六位用户的结果依次为 `1070.00`、`-115.00`、`455.00`、`210.00`、`0.00`、`0.00`；负值是构造关系产生的校验值。

## 逻辑导出与新库往返

```bash
mysqldump --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p --default-character-set=utf8mb4 \
  --single-transaction --skip-lock-tables --skip-add-locks \
  forensic_lab > logical.sql

mysql --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p \
  -e 'CREATE DATABASE forensic_lab_roundtrip CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'

mysql --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p --default-character-set=utf8mb4 \
  forensic_lab_roundtrip < logical.sql

mysql --no-defaults --host="$MYSQL_HOST" --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" -p --default-character-set=utf8mb4 \
  --batch --raw forensic_lab_roundtrip < queries.sql > roundtrip.tsv

diff -u original.tsv roundtrip.tsv
```

对本练习的六张 InnoDB 表，逻辑导出后的新库结果应与原库逐组相同。不同服务器版本的 dump 文本可能包含不同元信息；跨版本核验仍以表结构、行值、查询结果及导出记录为准。

## 已实测的边界

已在 MySQL `5.5.62` 的全新实验数据目录运行 15 组查询，原库和逻辑往返新库均为 `15/15` 命中。期望在服务器运行前手工固定，未从实际输出生成。此轮同版本再次导出逐字节相同。实验使用独立 named pipe、禁用 TCP，并在结束时优雅关闭实验进程；既有服务的 PID 与运行状态前后相同。

本练习覆盖 MySQL 5.5 核心 SQL、字符与时间转换、聚合口径及逻辑 dump 往返，不覆盖 MySQL 8 的递归 CTE、JSON、窗口函数，也不覆盖 binlog/PITR、redo/undo、IBD 物理恢复或真实检材重放。文章中的 MySQL 8 高级模板需在对应版本与实际字段上另行核验。
