---
title: "源码与元数据泄露：从单文件到还原"
summary: "先排除自定义 404，再按 .git/.svn/.hg、.DS_Store、编辑器备份、robots/证书、JS/Source Map 逐类确认；取到后做版本对齐与敏感项核对。"
module: Web
topic: "源码与环境"
tags: ["文件系统"]
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["git-history", "web-info", "web-js-reverse", "web-docker-lab"]
updated: "2026-10-29"
---

源码泄露题的关键不是“扫到某个后缀”，而是**文件真的存在、内容真能还原、还原结果与线上版本对得上**。顺序：单文件确认 → 取元数据 → 还原 → 交叉验证。

> 只对本地题目或授权目标探测；批量请求前确认范围与速率。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 排除自定义 404 | 随机路径三连 | 状态/长度/正文 |
| Git | `/.git/HEAD` | 再取 objects |
| SVN | `/.svn/wc.db`/entries | 版本分代 |
| Hg | `/.hg/requires` | 再 rip |
| 目录清单 | `/.DS_Store` | 递归 |
| 编辑器备份 | `.bak`/`~`/`.swp` | 直接 GET |
| 打包备份 | `www.zip`/`backup.tar.gz` | 看大小 |
| 前端 | JS + `.map` | 接口/密钥 |
| 站点声明 | `robots.txt`/`sitemap.xml` | 路径 |
| 证书 | SAN/crt.sh | 子域 |

## 01 原理与成立条件

```text
Web 根目录 → 误放/未删的元数据
               ├─ VCS：.git/.svn/.hg → 源码历史
               ├─ 系统：.DS_Store → 文件名
               ├─ 备份：.bak/~/.swp/zip → 源码/配置
               └─ 前端：JS/Map → 接口/密钥
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 文件可访问 | 未被 deny | 换路径/后缀 |
| 内容完整 | 对象/库可读 | 部分还原 |
| 格式可解析 | 工具支持 | 手工解析 |
| 与线上一致 | 路由/版本对得上 | 标为旧版 |

## 02 判断与分型

```text
随机路径返回什么？
 ├─ 200 且与首页相同 → 自定义 404，需对比正文
 ├─ 404 固定长度 → 正常
 └─ WAF 页 → 降速/停
目标有哪种元数据？
 ├─ /.git/HEAD 200 → Git
 ├─ /.svn/ 200 → SVN
 ├─ /.hg/requires 200 → Hg
 ├─ /.DS_Store 200 → 目录清单
 └─ JS 有 sourceMappingURL → Map
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `/.git/HEAD` 返回 `ref:` | Git 仓库 | 取 config/index |
| `.svn/wc.db` 可下 | SVN 1.7+ | SQLite |
| `.hg/requires` 200 | Hg | rip-hg |
| `.DS_Store` 头 `Bud1` | 目录清单 | 解析文件名 |
| `.swp` 头 `b0VIM` | Vim 交换 | `vim -r` |
| `.map` 可下 | Source Map | 还原源码 |
| `robots.txt` 有 `Disallow` | 隐藏路径 | 逐个确认 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 200 就认为存在 | 自定义 404 | 比正文 |
| `.git` 403 | 存在但禁读 | 换文件/换路径 |
| `.map` 404 | 未发布 | 格式化 JS |
| 源码路由对不上 | 旧版/部分 | 标版本 |

## 03 利用阶梯

### L0 建立 404 基线

**前提**：有站点访问。

**步骤**：
1. 请求 `/`、随机路径、目标文件，记状态/长度/类型。
2. 比较正文哈希与标题，排除自定义 404。
3. 确认 WAF/限速。
4. 只对授权目标继续。

**成功标志**：能区分“真文件”与“错误页”。

**失败分支**：全 200→比正文；全 403→停/换目标。

### L1 Git / SVN / Hg

**前提**：版本控制目录可读。

**步骤**：
1. Git：取 `HEAD`/`config`/`index`/`objects`；用 GitHack 或 `git clone`。
2. 丢对象：`git fsck --lost-found` 找 dangling blob。
3. SVN：1.6 看 `entries`/`text-base`；1.7+ 下 `wc.db` + `pristine`。
4. Hg：`requires` 确认后 `rip-hg.pl`。
5. 还原后与线上路由对照。

**成功标志**：还原出源码/历史 commit。

**失败分支**：objects 禁读→用 index 列名；库不全→部分还原。

### L2 备份、编辑器与目录清单

**前提**：无 VCS 或 VCS 不可读。

**步骤**：
1. 试 `index.php.bak/.old/.save/~/.swp/.swo`。
2. `.swp` 用 `vim -r` 恢复后另存。
3. 试 `www.zip`/`wwwroot.rar`/`backup.tar.gz`/`.env`。
4. `.DS_Store` 解析文件名，再逐目录取。
5. `robots.txt`/`sitemap.xml` 补路径。

**成功标志**：拿到源码/配置/文件名清单。

**失败分支**：后缀被禁→换后缀/编码；压缩包加密→找口令。

### L3 前端 JS 与 Source Map

**前提**：有前端包。

**步骤**：
1. 列页面所有 JS，找 `sourceMappingURL`。
2. 下 `.map`，用 `source-map`/浏览器 Sources 还原。
3. 搜接口、`baseURL`、`token`/`secret`/`iv`。
4. 分包：`webpackChunk` 按 chunk 找接口。
5. 格式化后搜关键字。

**成功标志**：接口/参数/硬编码凭据。

**失败分支**：无 map→格式化/动态调试；混淆→见 JS 逆向页。

### L4 验证与版本对齐

**前提**：已取到源码/配置。

**步骤**：
1. 路由/参数/依赖版本能否解释线上响应。
2. 敏感项：数据库、密钥、内网地址、测试账号。
3. 只静态阅读；要运行放隔离容器。
4. 记录 commit/文件数/哈希。

**成功标志**：源码与线上一致，敏感项有用途。

**失败分支**：版本不符→找历史 commit；文件缺失→补取。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| `.git` 目录禁列 | 直接取已知文件 | `HEAD`/`config` |
| objects 禁读 | `index` 列名 | blob 哈希 |
| 后缀黑名单 | 换后缀/大小写 | `.bak`/`.BAK` |
| 压缩包加密 | 找口令/已知明文 | 配置 |
| `.map` 404 | 格式化 JS | 搜接口 |
| WAF | 降速/换路径 | 授权 |

边界：`.git` 可读不等于能 clone；SVN 两代格式不同；`.DS_Store` 只给文件名；Source Map 可能含原始源码但版本旧；泄露源码只静态阅读。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| `robots.txt` | `Disallow` | 隐藏目录 |
| `sitemap.xml` | 全量 URL | 旧接口 |
| 证书 SAN | 子域 | crt.sh |
| 历史快照 | Wayback | 旧页面 |
| 部署文件 | `Dockerfile` | 端口/依赖 |
| 前端 map | 源码 | 密钥 |
| 备份目录 | `/backup/` | 列表 |

## 06 差异速查

| VCS | 入口 | 还原 |
|---|---|---|
| Git | `.git/HEAD` | GitHack/clone/fsck |
| SVN 1.6 | `.svn/entries` | `text-base` |
| SVN 1.7+ | `.svn/wc.db` | SQLite+`pristine` |
| Hg | `.hg/requires` | rip-hg |

| 文件 | 特征 | 工具 |
|---|---|---|
| `.DS_Store` | `Bud1` | ds_store_exp |
| `.swp` | `b0VIM` | `vim -r` |
| `.map` | JSON | source-map |
| zip | `PK` | unzip |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 基线 | `curl -o /dev/null -w` |
| Git | GitHack/git |
| SVN | dvcs-ripper/sqlite3 |
| Hg | rip-hg.pl |
| DS_Store | ds_store_exp |
| Map | source-map/DevTools |
| 记录 | 路径/哈希/commit |

验证顺序：基线 → 元数据 → 还原 → 版本对齐。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 基线 | 随机路径 | 404 特征 |
| 2 探测 | VCS/备份/DS | 候选 |
| 3 还原 | 工具 | 源码 |
| 4 前端 | JS/Map | 接口/密钥 |
| 5 验证 | 路由/版本 | 一致性 |
| 6 记录 | 路径/哈希 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 全 200 | 自定义 404 | 比正文 |
| `.git` 403 | 禁读 | 换文件 |
| clone 失败 | 对象缺失 | GitHack/fsck |
| SVN 空 | 版本/路径 | 换格式 |
| `.swp` 打不开 | 版本 | 换 vim |
| map 404 | 未发布 | 格式化 |
| 源码对不上 | 旧版 | 找 commit |

## 10 记录与复现

- [ ] 404 基线
- [ ] 元数据类型/路径
- [ ] 还原工具/文件数
- [ ] commit/版本
- [ ] 敏感项
- [ ] 验证方式

| 记录项 | 内容 |
|---|---|
| 类型 | Git/SVN/备份/Map |
| 路径 | URL |
| 还原 | 工具/文件 |
| 版本 | commit/时间 |
| 敏感 | 配置/密钥 |

相关： [Git 泄露](/knowledge/git-history/)、[敏感信息与指纹](/knowledge/web-info/)、[JS 逆向](/knowledge/web-js-reverse/)、[Docker 与虚拟网络](/knowledge/web-docker-lab/)。
