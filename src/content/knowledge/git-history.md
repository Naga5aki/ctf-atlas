---
title: "Git/SVN 泄露：从元数据到历史"
summary: "目录 403 不等于没有泄露：先逐文件确认 HEAD/config/index，再在本地副本里查提交、reflog、stash 与 SVN pristine，最后回到当前服务核对。"
module: Web
topic: "源码与环境"
tags: [Git]
status: 已整理
sourceIds: [c7613f4a6214]
challengeIds: []
relatedIds: ["web-leak-files", "web-info", "web-source-route"]
updated: "2026-10-29"
---

站点目录出现 `.git`/`.svn` 线索时，先记录**可访问路径、响应码、正文长度、取回时间**。目录名或 403 不能证明仓库可下载；只有单文件正文符合格式才算证据。

> 只在题目副本或书面授权环境执行；不要在运行中的网站目录里 `git checkout` 或恢复文件。

## 00 30 秒速查

| 我要… | 请求/命令 | 成功标志 |
|---|---|---|
| 确认 Git | `/.git/HEAD` | `ref: refs/heads/main` 或 40 位哈希 |
| 看配置 | `/.git/config` | `[core]`/`repositoryformatversion` |
| 看索引 | `/.git/index` | 前 4 字节 `DIRC` |
| 判 SVN 代 | `/.svn/entries`、`wc.db` | 文本清单 vs `SQLite format 3` |
| 查历史 | `git log --all --stat` | 提交/文件 |
| 看某次文件 | `git show COMMIT:path` | 正文 |
| 找消失配置 | `git log -S 'KEY' --all` | 增删提交 |
| 找悬空提交 | `git reflog` | 旧 HEAD |
| 看暂存 | `git stash list/show -p` | 补丁 |
| 回当前验证 | 历史文件 vs 现响应 | `cmp` 退出码 |

## 01 原理与成立条件

```text
Web 根目录误放 .git/.svn
 ├─ 单文件可读 → 元数据泄露
 ├─ objects/pack 可读 → 可还原仓库
 └─ 仅 HEAD → 只能确认，不能取历史
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 单文件可读 | 非目录列表 | 逐文件请求 |
| 正文格式对 | 不是自定义 404 | 与随机路径对比 |
| 对象齐全 | `objects`/pack | 只记元数据 |
| 本地副本 | 分析不污染站点 | 先复制 |
| 授权 | 题目/书面 | 停 |

| 路径 | 正文 | 不能说明 |
|---|---|---|
| `/.git/HEAD` | `ref: refs/heads/master` 或 40 位十六进制 | 对象是否存在 |
| `/.git/config` | `[core]`、`repositoryformatversion` | 远程账号可用 |
| `/.git/index` | `DIRC` + 大端版本 2/3/4 | 能否读出内容 |
| `/.git/logs/HEAD` | reflog | 是否完整 |
| `/.svn/entries` | 1.6 文本清单 | 新版本路径 |
| `/.svn/wc.db` | `SQLite format 3` | pristine 是否存在 |

## 02 判断与分型

```text
/.git/HEAD 返回 200 且格式对吗？
 ├─ 是 → Git
 │    ├─ index/config 也可读 → 继续
 │    └─ objects 可读 → 尝试还原
 └─ 否
     ├─ /.svn/entries 有文本清单 → SVN 1.6
     ├─ /.svn/wc.db 是 SQLite → SVN 1.7+
     └─ 都是 HTML → 自定义 404/无泄露
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 目录 403、文件 200 | autoindex off | 逐文件 |
| `HEAD` 200 | 可能是 Git | 看正文 |
| `index` 前 8 字节 `44 49 52 43` | Git 索引 | 单独分析 |
| `entries` 很短 | 可能是 1.7 | 看 `wc.db` |
| `wc.db` 头 `SQLite` | 新式工作副本 | 查 NODES |
| 正文 `<!DOCTYPE` | 错误页 | 按 404 处理 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 目录 403 当泄露 | 只拒列表 | 请求单文件 |
| 200 HTML 当文件 | 自定义 404 | 比长度/哈希 |
| `entries` 一行数字 | SVN 1.7 格式号 | 查 `wc.db` |
| `index` 有列表 | 无对象库 | 只记索引 |
| 历史有口令 | 可能已失效 | 不抄值，回服务验证 |

## 03 利用阶梯

### L0 单文件确认

**前提**：发现 `.git` 线索。

**步骤**：
1. 不加 `-L`、用 `--path-as-is` 请求 `HEAD`/`config`/`index`。
2. 分别保存响应头与正文。
3. `index` 用 `od -An -tx1 -N 8` 核对 `44 49 52 43`。
4. 与随机路径比长度/正文，排除自定义 404。

```bash
curl -sS -D - -o head.txt --path-as-is 'http://127.0.0.1:8000/.git/HEAD'
curl -sS -D - -o config.txt --path-as-is 'http://127.0.0.1:8000/.git/config'
curl -sS -D - -o index.bin --path-as-is 'http://127.0.0.1:8000/.git/index'
od -An -tx1 -N 8 index.bin
```

**成功标志**：至少一个文件正文符合格式。

**失败分支**：403→规则拦截；404→未暴露；HTML→错误页。

### L1 SVN 分代

**前提**：目录出现 `.svn` 线索。

**步骤**：
1. 同时请求 `entries` 与 `wc.db`。
2. `entries` 为文本清单→1.6 及更早。
3. `wc.db` 前 16 字节 `SQLite format 3`→1.7+。
4. `PRAGMA table_info(NODES)` 核对列名，再查 `local_relpath/checksum`。
5. `$sha1$` 校验和映射到 `pristine/<前两位>/<40位>.svn-base`。

```bash
sqlite3 wc.db "PRAGMA table_info(NODES);"
sqlite3 wc.db "SELECT local_relpath, presence, kind, checksum FROM NODES WHERE op_depth = 0;"
```

**成功标志**：拿到路径清单，pristine 命中并 SHA-1 一致。

**失败分支**：只有 `wc.db`→有路径无字节；校验和非 `$sha1$`→不套路径；查询列名不符→按实际列。

### L2 副本查提交

**前提**：已拿到仓库副本或对象。

**步骤**：
1. 复制到分析目录，不在站点目录操作。
2. `git status --short` 看工作树。
3. `git log --all --oneline --decorate --graph` 看分支/标签。
4. `--stat`/`--name-status` 定位文件出现、改名、删除。
5. `git show COMMIT:path` 取正文。

```bash
git --no-optional-locks log --all --stat
git --no-optional-locks log --all --name-status -- path/to/file
git --no-optional-locks show COMMIT:path/to/file
```

**成功标志**：目标配置/路由/密钥所在提交与时间明确。

**失败分支**：提交时间不可信→对服务日志；文件找不到→L3；对象缺失→只记元数据。

### L3 reflog、stash 与索引

**前提**：可达历史没有目标。

**步骤**：
1. `git reflog` 找旧 HEAD；先看 `.git/logs` 是否存在。
2. `git stash list`，再 `stash show -p 'stash@{0}'`。
3. `git log -S 'KEY' --all -- path` 按内容变化找提交。
4. 只有 `index.bin`：`git init` 后替换索引，`ls-files --stage`。

```bash
git --no-optional-locks reflog
git --no-optional-locks stash list
git --no-optional-locks log -S 'NEEDLE' --all -- path/to/file
git init /tmp/git-index-lab
cp index.bin /tmp/git-index-lab/.git/index
git --no-optional-locks -C /tmp/git-index-lab ls-files --stage
```

**成功标志**：找到悬空提交/暂存补丁/路径与 blob 哈希。

**失败分支**：reflog 空→无本地历史；stash 空→看未跟踪；无对象→`git show` 报缺失，只能记索引。

### L4 回当前服务验证

**前提**：历史里有配置/路由/凭据线索。

**步骤**：
1. 把历史文件与当前响应各存一份。
2. 静态文件用 `cmp -s`；动态页面改比配置键/路由/版本。
3. 核对环境变量是否仍被加载，而不是拿旧值直接试。
4. 记录“旧提交显示 X；当前证据 Y”。

```bash
git --no-optional-locks show COMMIT:path/to/file > historical.txt
curl -sS 'http://127.0.0.1:8000/path' -o live.txt
cmp -s historical.txt live.txt; echo $?
```

**成功标志**：能说明旧配置是否仍生效。

**失败分支**：动态内容→比结构；凭据疑似有效→只在授权内验证并记录时间。

## 04 绕过与边界

| 场景 | 边界 | 处理 |
|---|---|---|
| 目录 403 | 仅禁列表 | 逐文件请求 |
| `-L` 跟随 | 跳到错误页 | 不加 |
| 点路径改写 | 客户端规范化 | `--path-as-is` |
| 对象缺失 | 只有 HEAD/index | 不宣称还原 |
| 动态页面 | 每次不同 | 比键/路由 |
| 凭据 | 可能失效 | 不抄值 |
| 站点目录 | 不能改 | 只在副本 |

边界：`HEAD` 只证明单文件；`index` 无对象库读不出正文；`docker save` 不含卷（类比：元数据不等于数据）；`reflog` 默认约 90 天；旧提交不等于线上运行版本。

## 05 非典型入口

| 入口 | 线索 | 注意 |
|---|---|---|
| `.git/logs/HEAD` | reflog | 悬空提交 |
| `.git/packed-refs` | 分支/标签 | 对象仍缺 |
| `.git/objects/pack` | pack | 可还原 |
| `.svn/pristine` | 原始字节 | 按 SHA-1 |
| 备份文件 | `.git.bak`/`.zip` | 同法确认 |
| 部署目录 | `.env`/CI | 只读 |

## 06 差异速查

| 版本/对象 | 判断 | 取法 |
|---|---|---|
| Git HEAD | `ref:`/40 位 | 直接读 |
| Git index | `DIRC` | `ls-files --stage` |
| SVN ≤1.6 | `entries` 文本 | 读清单 |
| SVN ≥1.7 | `wc.db` SQLite | `NODES`+pristine |
| 仅有 HEAD | 无对象 | 只记确认 |
| 仅有 index | 有路径 | `--stage` |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 取文件 | curl（无 `-L`） |
| 看头 | `od`/`xxd` |
| Git 分析 | git（副本） |
| SVN 分析 | sqlite3/sha1sum |
| 对比 | `cmp` |
| 扫描 | 目录探测（授权、限速） |

验证顺序：单文件 → 副本 → 历史 → 回服务。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 线索 | `/.git`/`/.svn` | 路径表 |
| 2 确认 | HEAD/config/index | 泄露结论 |
| 3 还原 | 对象/pristine | 文件/路径 |
| 4 查史 | log/reflog/stash | 旧配置 |
| 5 回验 | 历史 vs 现响应 | 是否生效 |
| 6 记录 | 路径/哈希/时间 | 证据 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 目录 403 | 仅禁列表 | 请求单文件 |
| 200 HTML | 自定义 404 | 比随机路径 |
| index 无对象 | 对象缺失 | 只记索引 |
| SVN 路径空 | 版本误判 | 查 `wc.db` |
| 校验和不匹配 | 非 `$sha1$` | 不套路径 |
| 历史无文件 | reflog/stash | L3 |
| 旧配置不生效 | 已部署新版 | 记差异 |

## 10 记录与复现

- [ ] 可访问路径/响应码/长度
- [ ] 文件格式证据（`DIRC`/`SQLite`/40 位）
- [ ] 副本来源与哈希
- [ ] 提交/分支/reflog/stash
- [ ] 历史文件与当前响应差异
- [ ] 时间与授权范围
- [ ] 清理副本

| 项 | 记录 |
|---|---|
| 入口 | `/.git/HEAD` 等 |
| 版本 | Git/SVN 代 |
| 证据 | 正文片段/哈希 |
| 历史 | 提交号/文件 |
| 回验 | `cmp`/键值 |
| 清理 | 副本删除 |

相关： [源码与元数据泄露](/knowledge/web-leak-files/)、[敏感信息与指纹](/knowledge/web-info/)、[代码审计](/knowledge/web-source-route/)。
