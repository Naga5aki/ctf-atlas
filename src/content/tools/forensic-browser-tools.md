---
title: 浏览器数据库与凭据解析工具
summary: 从 History、places.sqlite、缓存与登录材料入手，按版本选择 SQLite、Hindsight、firepwd 等工具。
module: Forensics
topic: 系统与用户痕迹
locationPaths: ['D:\CTF_MISC_Tools\数据库\DB Browser for SQLite']
sourceIds: [web-forensics-wiki-browser, web-goodlunatic-761da51, web-hello-memory]
updated: 2026-10-01
---

## 1. 先保全完整用户配置

按浏览器、用户和 Profile 分目录；保全主数据库及 WAL/SHM、Local State、登录数据库、会话和缓存。不要为“导出数据”直接启动证据中的浏览器，启动可能迁移数据库、同步或刷新记录。副本快照与查询见 [浏览器取证](/knowledge/forensic-browser/) 和 [SQLite 与 WAL](/knowledge/forensic-sqlite/)。

| 工具 | 用途 | 使用边界 |
| --- | --- | --- |
| SQLite / DB Browser for SQLite | 表结构、历史、下载和应用查询 | 先查 schema，时间单位和字段不能混用 |
| Hindsight | Chromium 历史与部分用户痕迹解析 | 支持范围依浏览器版本；保存解析日志 |
| BrowsingHistoryView | 便于初筛多个浏览器的历史 | 不能代替完整数据库、会话和缓存分析 |
| ChromeCacheView / NirSoft 对应查看器 | 缓存候选项、URL、响应头和数据 | 缓存可能为预加载，未必发生主动访问 |
| firefox_decrypt | 配合 NSS 解密 Firefox 保存的登录项 | 需要配套 profile、NSS 版本和已知主密码条件 |
| firepwd | 分析 key 数据库与 logins.json | 参数和加密支持需与工具/Firefox 版本相符 |

## 2. Firefox 登录材料

保留 `logins.json` 和同一 Profile 的 `key4.db`（旧版可能为 `key3.db`），以及版本线索。安装版、便携版和多个 Profile 都要分别检查。若设置主密码，需要相应密码或独立恢复条件。

以下在工具的可信副本与已准备的 Python 依赖环境中运行，输出存放私有分析目录：

```bash
python3 firefox_decrypt.py ./work/firefox-profile --format json > ./output/firefox-logins.json
python3 firepwd.py -d ./work/firefox-profile > ./output/firepwd.txt
```

`firepwd.py logins.json` 不是通用正确调用方式。firepwd 的 `-p` 可用于已知主密码，但命令行会留下口令痕迹，应优先采用工具支持的交互/私有环境。Firefox 144 起相关 NSS 加密实现变化，旧工具可能不兼容；firefox_decrypt 需要足够新的 NSS，不能把 key4.db 都解释为同一种 3DES 结构。

## 3. Chromium 凭据

Chrome/Edge 的历史数据库可独立分析；保存口令和 Cookie 则可能涉及 DPAPI、Local State 中的包装密钥、AES-GCM，以及 Chrome 较新版的 App-Bound 加密。`v10/v11/v20` 前缀是识别线索，仍要核对平台与版本。

**能读历史不等于能解密凭据。** 仅有 Login Data 或 Cookies 往往不足；离线材料应与用户 SID、Protect MasterKey、系统材料和相应版本结合。不要把其他系统或另一用户的 Local State 混入同一解析目录。

## 4. 结果核对

历史和下载以 URL、访问/下载时间、记录 ID、路径和文件哈希关联。登录项保存说明凭据条目存在，不代表一定登录成功；Cookie 有效期也不直接证明该账号当时活跃。解密输出按需记录字段和验证结果，避免把口令、令牌放入文章或截图。
