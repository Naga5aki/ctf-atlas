## 01 建立时间来源与语义清单

时间线需要说明“哪个对象的哪个字段，在什么时钟与时区下，记录了什么事件”。某个时间显示得很精确，不代表它不可修改或接近真实行为；不同来源记录的可能是请求、提交、写入、同步或复制时刻。先保留原值，再统一显示与排序，最后讨论活动顺序和不确定范围。

### 01.1 各类来源能说明什么

| 来源 | 可能记录的事件 | 需要核对 |
| --- | --- | --- |
| 文件 mtime / btime | 内容修改、文件创建等文件系统事件 | 文件系统支持、复制/恢复行为、手工改时与缓存；btime 不总存在 |
| 系统日志 | 登录、服务启停、设备和进程活动 | 主机时钟、时区、轮转、采集范围和日志格式 |
| Web 访问日志 | 服务器记录请求的时刻 | 显式时区、代理、日志完整性、请求是否成功 |
| 数据库字段 | 应用写入的业务时间或服务器生成时间 | 单位、字段含义、会话时区、提交/更新与覆盖 |
| shell 历史 | 命令文本及可选时间记录 | 是否启用时间、是否写盘、跨会话、编辑与缺失 |
| 浏览器历史/下载 | 浏览器存储的访问、下载或状态变化 | 起算点、微秒单位、同步/导入与删除 |
| 应用专用日志 | 飞行、通信、模型加载等活动 | 版本、时钟、时区与解析完整性 |
| COW/快照元数据 | 树状态、事务或快照创建关系 | 不是每个文件活动的准确发生时刻，需关联具体版本 |

没有一种来源可以无条件标为“最可靠”。服务端日志可能拥有较好的上下文，但也能被清理或改写；文件系统精度也不代表事实准确。选择锚点时解释它为何适合当前事件，并寻找不同机制生成的记录。

### 01.2 实战：先固定一个日志时间范围

**材料：** 当前与轮转 Nginx 日志、系统时区配置、相关文件和数据库导出。读取开头、结尾及目标请求，检查格式和覆盖范围。

```bash
EVIDENCE_ROOT=/mnt/evidence
head -n 3 "$EVIDENCE_ROOT/var/log/nginx/access.log"
tail -n 3 "$EVIDENCE_ROOT/var/log/nginx/access.log"
grep -nE '/(admin|panel)\.php' "$EVIDENCE_ROOT/var/log/nginx/access.log"
readlink "$EVIDENCE_ROOT/etc/localtime"
ls -l "$EVIDENCE_ROOT/var/log/nginx/"
```

**示例判读：** 日志字段带 `+0800`，说明该条记录的显式偏移，不必由 `/etc/localtime` 推测。主机设置为 Asia/Shanghai 只能提供默认配置线索，其他应用可能独立使用 UTC。保存完整原行和行号/字节偏移，再导出事件，不把格式化截图当作唯一原始材料。

## 02 时间表示、换算与精度

### 02.1 不同表示不自动等价

| 表示 | 示例 | 读取条件 |
| --- | --- | --- |
| RFC3339 / ISO8601 带 Z | `2026-05-12T01:14:20.535713491Z` | Z 表示 UTC；小数可超过工具支持精度 |
| ISO8601 带偏移 | `2026-05-12T09:14:20+08:00` | 与 `01:14:20Z` 是同一时刻 |
| Unix 秒 | `1778548460` | 先证明单位为秒与对应字段语义 |
| 格式化日期 | `%Y/%c/%e` 对应 `2026/5/12` | 是显示格式，缺少日内时间与时区 |
| 纯数字日期 | `20260512` | 可能是计划日期或日期字符串，不能当成 Unix 秒 |

Docker `created` 等时间字段的含义与对象范围集中见[Docker 镜像结构与取证](/knowledge/docker-evidence-03/)；镜像构建时间不能直接称为容器启动时间。PE 时间与调试标识限制见[逆向工程](/knowledge/fic-case-07/)。

### 02.2 实战：同一时刻的 UTC 与本地显示

```bash
python3 - <<'PY'
from datetime import datetime, timedelta, timezone

raw = '2026-05-12T09:14:20+08:00'
event = datetime.fromisoformat(raw)
utc = event.astimezone(timezone.utc)
print('original=', raw)
print('utc=', utc.isoformat())
print('unix_seconds=', int(utc.timestamp()))
print('fixed_offset_display=', utc.astimezone(timezone(timedelta(hours=8))).isoformat())
PY
```

**预期输出中的时间：** `2026-05-12T01:14:20+00:00` 与 `2026-05-12T09:14:20+08:00`。固定 `+08:00` 只说明该偏移转换；需要历史夏令时规则时，应采用已确认的时区数据库及区域，而非给所有年份强加固定偏移。

原始毫秒/微秒/纳秒不要先转成浮点再保存；整数单位与全部小数位单独保留。Python 常用 `datetime` 精度为微秒，超过六位的小数不能无说明地截断后仍声称纳秒排序正确。空值、零值、超范围值与解析失败另列，不用当前时间替代。

### 02.3 日期统计的时区边界

数据库 `FROM_UNIXTIME` 采用会话时区，因此按天统计前先固定口径。某记录在 UTC 的前一天、在 `+08:00` 的后一天都可能正确，关键是采用哪种统计定义。

```sql
SELECT @@session.time_zone, @@system_time_zone;
SET time_zone = '+00:00';
SELECT DATE_FORMAT(FROM_UNIXTIME(user_reg_time), '%Y/%c/%e') AS reg_date,
       COUNT(*) AS cnt
FROM mac_user
WHERE user_reg_time IS NOT NULL
GROUP BY reg_date
ORDER BY cnt DESC, reg_date ASC;
```

`%c/%e` 不补零是展示规则；报告同时保存未格式化时间、单位和时区。显示成 `YYYYMMDD` 或 `YYYY/M/D` 时不改变原始证据。完整聚合、有效分母和并列日期处理见[数据库取证](/knowledge/fic-case-05/)。

## 03 合并事件与校准时钟

### 03.1 事件表的最小字段

| 字段 | 用途 |
| --- | --- |
| 对象与来源 | 主机/用户/应用/实例、文件路径、行号/记录 ID/偏移 |
| 原始时间 | 未改写的整数或字符串、字段名与单位 |
| 时间语义 | 请求、写入、创建、更新、同步、快照或计划 |
| 解释条件 | 时区、起算点、解析器、精度与已知漂移 |
| 统一时间 | UTC 值与可用的不确定区间 |
| 事件内容 | 主体、客体、行为、状态与关联键 |
| 验证等级 | 已确认字段、合理关联、残留候选或未解析 |

保留原始记录后，导出一份列为 `id,source,raw_time,event` 的 CSV。以下例子仅接受明确带偏移、至多微秒精度的 ISO 时间；纳秒记录应另用支持其精度的排序方式，不能混入后丢失精度。

```python
import csv
import re
from datetime import datetime, timezone
from pathlib import Path

rows = []
with Path('work/events.csv').open(encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f):
        raw = row['raw_time']
        frac = re.search(r'\.(\d+)', raw)
        if frac and len(frac.group(1)) > 6:
            raise ValueError('请保留更高精度并使用相应排序方法')
        parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('缺失时区不能自动补成分析机时区')
        row['utc_time'] = parsed.astimezone(timezone.utc).isoformat()
        rows.append((parsed.astimezone(timezone.utc), row))
rows.sort(key=lambda item: (item[0], item[1]['id']))
with Path('work/events-utc.csv').open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'source', 'raw_time', 'event', 'utc_time'])
    writer.writeheader()
    writer.writerows(row for _, row in rows)
```

**输出判读：** 同时保留原始时间与 UTC，稳定 ID 仅使同一时间的显示可复现，不能证明这些事件内部先后顺序。事件只有日期或秒级精度时，应按实际精度表达区间，不人为补出准确毫秒。

### 03.2 多来源的锚点与偏差

选择同一事件的稳定关联键，例如请求 ID、事务 ID、账户 ID 或文件内容摘要，再比较日志时间。固定偏差可能来自时区，缓慢变化可能来自时钟漂移，突变可能来自校时、重启或采集切换。还要排除排队、缓冲、异步写盘与复制延迟；不一致不自动等于恶意篡改。

同一数据库两次查询、同一记录两个工具展示并不形成独立时钟证据。先说明不同记录由什么机制产生，再据此限定校准可信度。

## 04 实战：后台路径变化的时间范围

### 04.1 关联文件与请求状态

**材料：** 历史提交树、现存入口、Nginx 配置及覆盖目标日期的全部日志。文件关系验证见[Web 应用取证](/knowledge/fic-case-04/)，此处只讨论时间范围。

1. 从版本树确认旧入口内容，再与现存新入口逐字节比较。
2. 从配置确认旧/新 URL 的路由和 rewrite，排除两个 URL 一直映射到同一入口。
3. 对全部轮转日志提取最后一次有效旧路径和首次有效新路径请求，保留状态、来源与上下文。
4. 核对两个观察时刻之间的日志是否完整，是否可能存在备用虚拟主机或未记录的请求。
5. 再比较文件时间、发布记录和应用日志，缩小“配置/文件发生变化”的候选区间。

**示例观察：** 旧路径最后成功请求在 `09:10`，新路径首次成功请求在 `09:18`。这说明材料中两类请求的相应观察时刻；只有日志完整、路由解释和独立修改证据支持时，才把某次切换限定在相应范围。扫描旧路径、复制入口或不同客户端选择都可能形成相似请求变化。

### 04.2 缺口与清理候选

日志中断、时间倒退、历史命令缺行和数量突然下降可作为待查异常，但也可能来自轮转、采集缺失、服务未启动、时钟调整或应用过滤。对比相邻文件、服务日志和存储时间，记录缺失范围；发现明确截断/删除指令及其时间后，仍需验证执行结果，不能只凭命令文本认定清理完成。

## 05 统计与行为结论

### 05.1 首次、末次与次数

“首次/末次”必须限定数据覆盖范围和事件类型；最新用户表字段不是完整登录史。相同时间可能有多条事件，使用事件 ID 展示排序并保留并列，不以 `LIMIT 1` 隐去事实。提问、注册、请求与交易分别有独立去重口径；重复导入或连接多表可以放大计数。

### 05.2 顺序与因果的边界

时间线能支持某时间范围内的活动集合和可观察顺序。A 在 B 前出现，并不能单独证明 A 导致 B；需要代码调用、事务关系、请求链或其他机制证据。文件快照提供历史状态，也不一定定位每一次修改的准确时刻。

最终按“事件及字段 → 原始时间和解释 → UTC/本地展示 → 独立关联 → 覆盖范围与不确定性”书写。保留未解析项、冲突项和仿真产生的新记录，让其他分析者可以按同一口径复核。
