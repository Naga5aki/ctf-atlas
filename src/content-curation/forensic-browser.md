## 01 先确定用户和配置目录

**第一轮目标：哪个配置目录、什么浏览器版本、哪段时间、访问或下载了什么。** 对每个配置目录单独编号，保留数据库、同目录的 `-wal` / `-shm` 文件、JSON 配置与缓存。不要在检材目录启动浏览器，它可能更新数据库、清理会话或触发同步。

| 浏览器 | Windows 常见目录 | 需要一起保全 |
| --- | --- | --- |
| Chrome | `C:\Users\<用户>\AppData\Local\Google\Chrome\User Data\` | 根目录 `Local State`，以及 `Default`、`Profile 1` 等每个配置目录 |
| Edge | `C:\Users\<用户>\AppData\Local\Microsoft\Edge\User Data\` | 与 Chrome 类似，但版本、策略、扩展和加密实现须分别核对 |
| Firefox | `C:\Users\<用户>\AppData\Roaming\Mozilla\Firefox\` | `profiles.ini`、`installs.ini`、`Profiles` 下的完整配置目录 |

`Default` 不等于唯一用户，`Profile 1` 也不能直接对应 Windows 第二个账户。通过配置名称、登录标识、目录所有者与系统 SID 建立关系。记录浏览器构建版本；同为 Chromium，不能假定所有字段、缓存格式和解密方式一致。

## 02 Chromium 文件与考点

| 文件或目录 | 重点字段 / 内容 | 可以回答的问题 |
| --- | --- | --- |
| `History` | `urls`、`visits`、`downloads`、`downloads_url_chains`、`keyword_search_terms` | 访问时间、URL、下载目标、重定向链和搜索词 |
| `Network/Cookies`，旧版 `Cookies` | host、name、时间、加密值 | 哪些域留下会话状态；不等于确认登录成功 |
| `Login Data` | `origin_url`、`username_value`、`password_value` | 保存了哪些站点账户，密码是否可离线解密 |
| `Web Data` | 自动填充、地址等版本相关表 | 输入或保存过哪些表单信息 |
| `Bookmarks` | JSON URL 与目录关系 | 收藏内容；收藏不等于访问 |
| `Preferences` / `Secure Preferences` | 设置、扩展、权限 | 扩展安装和配置变化 |
| `Top Sites`、`Shortcuts`、`Favicons` | 常用站点、地址栏匹配、图标 | 补充访问和搜索上下文 |
| `Cache` / `Cache_Data`、`Code Cache`、`GPUCache` | HTTP 缓存、编译代码、渲染缓存 | 是否保留页面资源；三者不能按同一格式解析 |

缓存文件名不应直接当成内容哈希。通过缓存解析器恢复请求 URL、响应头和主体，再对导出主体单独计算哈希。现代缓存布局可能嵌套在 `Cache/Cache_Data`。

### 02.1 查询前先检查表结构

以下命令只读取工作副本；若存在 WAL，先在隔离的副本目录完成一致性恢复，再保存查询用快照。不要用 `immutable=1` 忽略仍需重放的 WAL。

```bash
sqlite3 -readonly History '.tables'
sqlite3 -readonly History 'PRAGMA table_info(visits);'
sqlite3 -readonly History 'PRAGMA table_info(downloads);'
```

**访问记录：** 一次 URL 可对应多条 visits，不能把 `urls.last_visit_time` 当作全部访问历史。保留整数时间，再额外换算为 UTC。

```sql
SELECT v.id AS visit_id, u.url, u.title, u.visit_count,
       v.visit_time AS time_raw,
       datetime(v.visit_time / 1000000.0 - 11644473600, 'unixepoch') AS time_utc,
       v.from_visit, v.transition
FROM visits AS v
JOIN urls AS u ON u.id = v.url
ORDER BY v.visit_time, v.id;
```

**下载记录：** 先查任务，再按 `chain_index` 重建跳转顺序。某些版本没有 `tab_url` 或使用旧字段名，应按实际 schema 调整，不能把 SQL 报错当成没有下载。

```sql
SELECT id, target_path, tab_url, start_time, end_time,
       received_bytes, total_bytes, state
FROM downloads ORDER BY start_time;

SELECT id, chain_index, url
FROM downloads_url_chains ORDER BY id, chain_index;

SELECT k.term, u.url, u.title
FROM keyword_search_terms AS k
JOIN urls AS u ON u.id = k.url_id
WHERE k.term LIKE '%目标词%';
```

完成下载需综合状态、接收字节数和落地文件。HTTP 200、存在下载任务或保存路径，都不能单独证明文件下载完成、被打开或被执行。

## 03 Firefox 文件与查询

| 文件 | 内容与边界 |
| --- | --- |
| `places.sqlite` | 历史、书签，以及版本相关的下载注释 |
| `cookies.sqlite` | Cookie 字段；不能套用 Chromium 的 AES-GCM 格式 |
| `logins.json` + `key4.db` | 配套的登录记录与密钥材料；旧版本可见 `key3.db` / `signons.sqlite` |
| `formhistory.sqlite` | 表单输入历史 |
| `permissions.sqlite` | 站点权限 |
| `favicons.sqlite` | 图标数据与关联 |
| `downloads.sqlite` | 历史版本使用，现代版本不保证存在 |

```sql
SELECT h.id AS visit_id, p.url, p.title,
       h.visit_date AS time_raw,
       datetime(h.visit_date / 1000000.0, 'unixepoch') AS time_utc,
       h.from_visit, h.visit_type
FROM moz_historyvisits AS h
JOIN moz_places AS p ON p.id = h.place_id
ORDER BY h.visit_date, h.id;

SELECT b.id, b.parent, b.title, p.url
FROM moz_bookmarks AS b
LEFT JOIN moz_places AS p ON p.id = b.fk
ORDER BY b.parent, b.position;
```

下载注释存在时，先检查 `moz_annos` 与 `moz_anno_attributes`，按 place ID 关联 `moz_places`；只在有这些表的数据库执行查询。Firefox 微秒时间以 1970 年 UTC 为起点，Chromium 常见时间以 1601 年 UTC 为起点。

```python
from datetime import datetime, timedelta, timezone

def chromium_time(value):
    return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(value))

def firefox_time(value):
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(value))

print(chromium_time(13348540800000000))  # 2024-01-01 00:00:00+00:00
print(firefox_time(1704067200000000))    # 同一时刻
```

保留微秒整数，避免浮点舍入影响精确排序。SQL 的 `datetime` 展示到秒；空值、零值、异常未来时间应单独标记。

## 04 Cookie 和密码的版本边界

### 04.1 Windows Chromium

1. 保存 `Local State`、目标配置目录、账户 SID 和相关 DPAPI 材料。
2. 确认密文前缀及浏览器版本。旧 Windows 记录可能直接使用 DPAPI；部分版本的 `v10` 记录采用 AES-256-GCM，主密钥由 DPAPI 保护。
3. 对传统 GCM 记录，识别前缀、nonce、密文和认证标签；必须验证 tag，不能把未经认证的输出当作成功解密。
4. Chrome 127 起引入应用绑定加密，`v20` 等记录不能套用“去掉 DPAPI 前缀后在任意电脑调用解密”的旧流程。系统、账户和应用保护条件不满足时，明确记录未解密。
5. Cookie 数据库版本还可能要求核对 host 绑定摘要；成功解密不等于能直接把全部字节作为 Cookie 值使用。

单独把 `Local State` 和 `Login Data` 搬到另一台机器，通常不足以恢复密码。DPAPI 的作用域、主密钥与凭据条件见 [加密数据取证](/knowledge/forensic-protected-data/)。

### 04.2 Firefox

`firefox_decrypt` 接受配置目录，依赖匹配的 NSS 库；若设置主密码，需已知主密码。它并不自动破解未知主密码。`Firepwd` 使用 Python 解析密钥结构，版本支持要与样本相符，不能把所有 Firefox 都概括为 3DES。

```bash
python3 firefox_decrypt.py --help
python3 firefox_decrypt.py ./profile-copy/
python3 firepwd.py -h
python3 firepwd.py -d ./profile-copy/
```

Firefox 144 及之后的密码保护有变化；使用支持该格式的版本和 NSS，遇到未知算法先记录算法标识与工具错误。不要误用不存在的 `--export-logins logins.json --key4 key4.db` 参数组合。

## 05 隐私模式与证据强度

- 隐私会话关闭后，Chrome 不保留常规浏览历史及下载历史；**已下载的文件和保留的书签仍可能存在**。二者必须区分。
- 内存、DNS、代理、服务端日志、文件系统仍可能留下相关线索，但缓存寿命、加密和采集时点会影响可见性。
- 缓存命中可能由预加载、同步或后台请求产生；历史时间不必然代表用户正在观看页面。
- BV 号、邮箱、QQ 号是候选标识。将命中位置、进程、URL、账户目录和时间连起来，不能只凭一个字符串认定本人操作。

## 06 工具与交付

DB Browser for SQLite 用于查看 schema 和执行查询；ChromeHistoryView、ChromeCookiesView、ChromePass 面向相应记录；ChromeCacheView 解析缓存；Hindsight 汇总 Chromium 行为；Plaso/log2timeline 关联多类时间线。具体操作见 [浏览器工具指南](/tool/forensic-browser-tools/)。

交付表至少包括：`配置目录 / 浏览器版本 / 数据库和表 / 行 ID / 时间原值 / UTC / URL或路径 / 行为判断 / 交叉证据`。历史、下载、登录凭据分别输出，避免将“保存密码”写成“发生登录”。

## 07 实战：核对下载任务与落地文件

**场景与材料：** 某 Chromium 配置目录中的 History 包含目标 URL。已保全同批次数据库/WAL、浏览器版本、用户目录与下载目录。目标是区分访问、下载完成和程序执行；下面是示例记录，不是对任何实际检材的预设结论。

### 07.1 建立可复查的关联

1. 按前面的 schema 检查与快照流程建立查询副本，以 visits 主键列出目标 URL 的访问；记录重定向和 from_visit。
2. 在 downloads 中定位候选任务，以下载 ID 连接 downloads_url_chains，保留完整跳转次序、目标路径、原始时间、状态与字节数。
3. 导出目标文件并计算内容哈希、识别格式。路径中的文件可能已经被替换，当前同名文件不能自动对应历史下载。
4. 将文件哈希或路径与进程创建、Prefetch、UserAssist、文件系统记录交叉检查。没有执行证据时，结论停在已确认的下载层级。

### 07.2 三类示例判读

| 数据组合 | 解释 | 验证动作 |
| --- | --- | --- |
| 只有 visits | 数据库记录了访问候选 | 查下载任务、缓存和服务端记录 |
| 下载任务有路径，但 received_bytes 少于 total_bytes | 可能是中断或尚未完成 | 核对状态枚举、错误和实际文件完整性 |
| 任务状态、大小及落地文件一致 | 下载完成证据较充分 | 再独立核对打开或执行痕迹 |

状态数字必须依据实际浏览器版本解释；缺失 total_bytes、恢复记录或旧缓存会降低判断强度。多个 Profile 或云同步中的相同 URL 分开记录，避免重复计为同一用户操作。
