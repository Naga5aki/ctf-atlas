---
title: "Git 分支 Tag Stash 分析"
summary: "区分分支、标签与 stash 的证据含义及修改风险。"
module: "Forensics"
track: "服务器取证"
topic: "版本与源码"
tags: []
status: "已整理"
sourceIds: ["c7613f4a6214"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

手里是一份包含多分支、发布标签或临时 `stash` 的 Git 仓库副本，需要排查主分支之外残留的备份代码、版本标记与未提交改动。原始材料保持只读，不执行 `fetch`/`pull` 等联网更新命令。

**清点本地分支与远程跟踪引用 → 分清轻量标签与附注标签 → 检查 stash 父链与未跟踪文件补丁 → 用 blame 从可疑行反查引入提交 → 实战对比备份分支、标签与 stash。**

分支、标签和 stash 提供不同的历史入口。先列出并解析它们指向的对象，保存完整哈希，再读取内容；切换分支和应用 stash 都放在独立恢复副本中。

运行前先在隔离会话加载 [Git 基础页的只读安全包装函数 `git()`](/knowledge/git-docker-03/)；也可直接展开下方代码块复制定义：

<details>
<summary>展开 Git 只读安全包装函数与前置检查</summary>

**运行命令前先检查 `.git` 的这几处：**

1. 用可信文本工具查看 `config` 及 `include/includeIf` 指向的配置，再看 `hooks`、`.gitattributes` 和 `info/attributes`。这些文件也要保存原始字节。
2. 在低权限、隔离的分析会话中，使用分析机安装的可信、受支持 Git，不运行检材目录里带来的 Git 程序。
3. `--no-optional-locks` 只能减少索引刷新等可选写入。它不等于只读挂载，也不能阻止配置调用其他程序。

**下面函数怎样用：** 每次打开新的 Bash 分析会话，先完整粘贴并定义它，再执行本页的 Git 命令。示例程序路径是 Kali 的 `/usr/bin/git`；路径不同时，先核对分析机的软件清单，再替换。

函数只对本次命令加参数，不改仓库原配置。它禁用系统/用户配置、仓库 fsmonitor、hooks 与 pager，并读取 filter 名称，将对应的 clean/smudge/process 清空，避免 status 或恢复文件时执行这些转换器。

```bash
git() {
  local key
  local -a overrides=(-c core.fsmonitor=false -c core.hooksPath=/dev/null -c core.attributesFile=/dev/null)
  while IFS= read -r -d '' key; do
    overrides+=(-c "$key=" -c "${key%.*}.required=false")
  done < <(env -u GIT_PAGER -u GIT_EXTERNAL_DIFF GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
    /usr/bin/git --no-pager config --null --name-only --get-regexp '^filter\..*\.(clean|smudge|process)$')
  env -u GIT_PAGER -u GIT_EXTERNAL_DIFF GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 \
    /usr/bin/git --no-pager "${overrides[@]}" "$@"
}
```

**读取和恢复时分别注意：**

- 日志、show、diff 与 stash 补丁命令加 `--no-ext-diff --no-textconv`，防止外部比较程序或文本转换器介入。确需查看转换效果时，另用可丢弃副本。
- 读取二进制对象用 `git cat-file -p`，不要加 `--filters` 或 `--textconv`。先导出到文件，再识别格式。
- 恢复会改动副本。禁用过滤器后取得的是对象字节，可能不同于正常 checkout 转换后的工作树文件。
- 上述设置不是“陌生仓库绝不会执行程序”的保证。外置目录、异常配置和版本差异仍要先检查。依据为 [Git SECURITY 说明](https://git-scm.com/docs/git#_security)与 [gitattributes 转换器说明](https://git-scm.com/docs/gitattributes)。

</details>

<span id="01-分支与远程跟踪引用"></span>

## 01 清点本地分支与远程跟踪引用

当前分支的工作树里没有要找的配置，其他分支、远程跟踪引用可能还有。先把引用清点完，再读它们指向的对象；切换放到独立副本里。

操作顺序：先清点本地和远程跟踪引用，再按完整哈希读内容，确需切换时再进入恢复副本。


### 01.1 清点引用

分析副本在 `/work/copy/repository`，还不知道 backup 一类名字是不是本地分支、远程跟踪引用，或只是标签。先列引用，再读对象，最后才考虑切换。

操作顺序：先列分支和提交图，再按表判读范围，对上完整引用名和对象 ID。

```bash
cd /work/copy/repository
git branch
git branch -a
git branch -r
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
```

<details>
<summary>展开分支查询命令对照表</summary>

| 命令 | 范围 | 判读 |
| --- | --- | --- |
| `git branch` | 本地分支 | 找 dev、test、backup、old 等历史入口 |
| `git branch -a` | 本地与远程跟踪分支 | 检查当前分支以外的引用 |
| `git branch -r` | 本地保存的远程跟踪引用 | 找未曾在本地切换的远程历史 |

</details>

**1. 先按表看这三条 branch 各覆盖哪里。** `git log --oneline --all --graph --decorate` 把现存引用画出来。远程跟踪引用是本地保存的远程状态快照，不代表远端此刻仍有该分支。取证首轮不运行 fetch/pull 来刷新它，否则会改变引用与对象状态。名称如 backup 只是线索，内容必须由对象确认；没有这个名字也不代表没有备份历史。

```bash
git show --no-ext-diff --no-textconv --stat backup
git rev-parse refs/heads/backup
git show --no-ext-diff --no-textconv backup:app/config.yml
```

**2. 直接读 backup 的对象，先不切换。** `git show --stat backup` 看涉及的文件，`git rev-parse refs/heads/backup` 留下完整对象 ID，`git show backup:app/config.yml` 读该路径。读失败时核对引用名是 `refs/heads/backup` 还是别的同名标签。直接读文件无需切换。

```bash
git switch backup
git checkout backup
```

**3. 要看完整工作树时，只在恢复副本里切换。** 【仅在副本/仿真/授权环境执行】上面两条可分别使用，不是必须接连执行。只读旧文件不需要切换；上面的 show 已能读取。需要观察完整工作树时，`switch <branch>` 用于切换分支，`checkout <branch>` 是还兼有路径恢复功能的旧式命令。二者可能改索引和工作树；先保存 HEAD、索引与未提交修改，出现冲突不要强制覆盖。清点时记录 `refs/heads/backup` 这类完整引用名及对象 ID，以免分支与标签同名。切换后核对实际对象 ID，不能只凭提示里的短分支名认定恢复成功。

本节已核对本地分支、远程跟踪引用，以及 `refs/heads/backup` 的对象 ID 和路径内容；还没 fetch 的远端现状；首轮不要用 fetch/pull 去刷新。引用名是完整的 `refs/heads/...`，切换后的对象 ID 和 show 读到的是同一个，一并留存分支列表、提交图、backup 的对象 ID，以及切换前的 HEAD 和未提交修改。

<span id="02-tag-的对象含义"></span>

## 02 分清轻量标签与附注标签并核对指向对象

分支清点之后，发布点可能在标签上，而标签不一定是提交。先列出标签，再看它是轻量引用还是带注释的 tag 对象。

操作顺序：先列出标签，再看类型和剥离后的目标，对上标签说明只是线索。

```bash
git tag
git show --no-ext-diff --no-textconv release-demo
git cat-file -t refs/tags/release-demo
git rev-parse 'refs/tags/release-demo^{}'
```

**1. 先分清轻量标签和带注释标签。** `git tag` 列出名字。`git show --no-ext-diff --no-textconv release-demo` 的表现依目标类型而变，占位形式 `show <tag>` 也一样，不能把所有 Tag 都当成一个普通分支。`git cat-file -t refs/tags/release-demo` 看引用本身的类型。`git rev-parse 'refs/tags/release-demo^{}'` 里的 `^{}` 用于剥离标签到目标对象；其结果可能是 commit，也可能是其他对象，应检查类型。轻量标签是指向对象的引用；带注释标签拥有 tag 对象，含目标、标签者与说明。名字不存在时先看 `git tag` 的原文，不要改用同名分支。

**2. 按表决定保存标签文本、提交树，还是只当作发布线索。** 标签者、作者、时间和说明都可由创建者填写，不独立证明发布成功或身份。标签名可重用或移动，记录完整对象哈希比只记名称更可靠。

<details>
<summary>展开 tag 类型判读表</summary>

| 观察 | 含义 | 后续 |
| --- | --- | --- |
| `cat-file -t` 为 tag | 存在带注释标签对象 | 保存标签文本及目标对象 |
| 类型为 commit | 常见轻量标签指向提交 | 读取提交树与父链 |
| 标签说明含部署或备份信息 | 可能是发布线索 | 与部署日志及对应源码比较 |

</details>

标签者、作者、时间和说明都可由创建者填写，不独立证明发布成功或身份。标签名可重用或移动，记录完整对象哈希比只记名称更可靠。

本节已核对标签是 tag 对象还是直接指向 commit，以及剥离后的目标哈希；标签说明里的部署信息还没和部署日志、源码比较时，不写成已经发布成功。`cat-file -t` 和 `^{}` 的类型写在一起，完整对象哈希不只是标签名，一并留存标签列表、show 输出、目标对象哈希。

<span id="03-stash-中的未提交状态"></span>

## 03 检查 Stash 父链与未跟踪文件补丁

未提交的修改可能在 stash 里，而不在任何分支上。先列出并读补丁，应用放到可写的恢复副本。

操作顺序：先列出 stash 并读补丁，再确认父提交保存了什么，确需应用时再进入副本。


### 03.1 先列出，再查看补丁

编号 `stash@{0}` 会变，还不知道这条记录里有没有未跟踪文件。先列出，再读补丁和 stash commit 的父对象。

操作顺序：先列出并解析完整哈希，再看未跟踪文件是否已存入，对上三个父提交各自是什么。

```bash
git stash list
git stash show --no-ext-diff --no-textconv -p
git stash show --no-ext-diff --no-textconv -p 'stash@{0}'
git rev-parse 'stash@{0}'
```

**1. 编号会变，先留下完整 stash commit 哈希。** `stash list` 查看 stash 的本地引用日志；`stash show -p` 默认读取最新记录的补丁，指定 `stash@{0}` 可明确候选。`git rev-parse 'stash@{0}'` 解析对象。编号会随着新增、删除或移动变化，应保存完整 stash commit 哈希。默认显示方式不保证包含所有未跟踪内容；只有创建 stash 时纳入了未跟踪文件，才有相应对象可读。列表为空时，先写明可能未创建、已清理或这份材料是普通克隆。

```bash
git stash show --no-ext-diff --no-textconv --include-untracked -p 'stash@{0}'
git cat-file -p 'stash@{0}'
```

**2. 先确认 stash 当时保存了哪些内容。** `--include-untracked` 只能显示已存入 stash 的未跟踪文件，不能找回从未保存的文件。忽略文件是否包含，还取决于创建 stash 时的选项。`git cat-file -p 'stash@{0}'` 读这条 stash commit。

**3. 用父哈希把暂存和工作树分开。** 读取 stash commit 的原始父哈希后分别比较：第一父通常是当时 HEAD，第二父保存索引树，stash 自身树保存工作树。这样可区分已暂存和未暂存修改。有额外未跟踪父树时再读它，不固定假设每条记录都有三个父提交。

本节已核对stash 的完整哈希、补丁，以及第一父、第二父分别对应的 HEAD 和索引树；创建时没纳入的未跟踪文件或忽略文件，`--include-untracked` 也读不回来。报告里是完整哈希，不是会变动的 `stash@{0}`；父提交个数按这次对象实际读取，一并留存 `stash list`、两份补丁和 `cat-file -p` 的父哈希。

### 03.2 应用 stash 的改变

补丁已经够用时不必应用。确需把修改放进工作树时，只在 `/work/lab/stash-recovery` 的可写副本里做。

操作顺序：先确认只是找线索就用 show，要应用再进副本，对上冲突和索引是否恢复。

【仅在副本/仿真/授权环境执行】`apply` 会改工作树。分析原目录不运行。

```bash
# 在 /work/lab/stash-recovery 的可写副本中
git stash apply 'stash@{0}'
git status
git diff --no-ext-diff --no-textconv
```

**1. 应用前先处理合并驱动，并保存前后状态。** 【仅在副本/仿真/授权环境执行】`apply` 把修改应用到工作树，并保留 stash 记录；可能产生冲突。只是找线索时，用 show 即可，不需要 apply。注释写明在 `/work/lab/stash-recovery` 的可写副本中。检查 attributes 和 `merge.<驱动>.driver`，在独立副本取消不可信自定义合并驱动。禁用 textconv 不能代替这一步。保存应用前后的 status、diff、退出状态及未合并条目。分析原目录不运行 stash drop/pop/clear。

**2. 需要恢复暂存状态时再加 --index。** 要同时恢复暂存状态时，可尝试 `apply --index`，但冲突可能使索引恢复失败。stash 仍存在，不代表原现场已完整还原。`git status` 和 `git diff --no-ext-diff --no-textconv` 看应用后的差异。有冲突时先记录未合并条目，不要 drop。

本节已核对应用前后的 status、diff，以及 stash 记录是否仍在；冲突导致 `apply --index` 失败时，索引还没有恢复成当时的暂存状态。命令发生在 `/work/lab/stash-recovery`，分析原目录没有 drop/pop/clear，一并留存应用前后的 status、diff、退出状态和未合并条目。

<span id="04-从可疑行反查-blame"></span>

## 04 从可疑代码行用 `blame` 反查引入提交

配置文件里有一行可疑内容，还不知道是哪次提交最后改的它。blame 只回答所选版本里这一行最近的修改，不回答是谁最初引入行为。

操作顺序：先对整文件或行号做 blame，再用 show 看完整补丁，作者字段不直接当作身份结论。

```bash
git blame app/config.yml
git blame -L 5,12 -- app/config.yml
git show --no-ext-diff --no-textconv <对应提交哈希> -- app/config.yml
```

**1. 先标出这一行最近的提交。** `blame <filename>` 为每行标注所选版本中最近修改它的提交、作者与时间。`git blame -L 5,12 -- app/config.yml` 只看这几行，路径前的 `--` 分开参数和文件名。没有行号时先打开文件确认行范围，不要把别的文件的行号套过来。

**2. 再用 show 看完整补丁。** `git show --no-ext-diff --no-textconv <对应提交哈希> -- app/config.yml` 读那次提交里的这个路径。它适合从一行配置或可疑函数反查历史。代码移动、重命名、格式化和历史重写影响结果；“最后触碰这一行”不等于“最初引入行为”，也不直接证明某个人实际操作。

本节已核对所选版本里这一行对应的提交、作者标注和时间；移动、重命名或重写历史之后，这一行不能单独证明最初引入行为或实际操作者。blame 的提交哈希和随后的 show 补丁是同一个，一并留存blame 输出、行号范围和对应提交的补丁。

<span id="05-实战比较备份分支发布标签和临时修改"></span>

## 05 实战：对比备份分支、发布标签与临时修改

当前 main 里的数据库配置可能已经删除，备份分支、发布标签和 stash 里还可能各有一版。先把三个入口的哈希列出来，再比较内容，最后才在副本里应用 stash。

操作顺序：先解析分支、标签和 stash，再比较三份配置，对上哪一份生效还要部署证据。


### 05.1 场景与材料

材料为 `/work/input/repository/` 的完整保全目录，含本地分支、标签和 stash reflog。目标是判断一个数据库配置是否只在当前 main 删除，而仍存在于其他历史入口。分析副本为 `/work/copy/repository/`，输出为 `/work/output/git-refs/`。

操作顺序：先把分支、标签和 stash 列表存下来，再解析完整哈希，对上示例名字来自这次清单。

下列引用名和输出是构造示例；实际操作应先列出现有记录再取值。

```bash
mkdir -p /work/output/git-refs
cd /work/copy/repository
git branch -a > /work/output/git-refs/branches.txt
git branch -r > /work/output/git-refs/remote-tracking.txt
git tag > /work/output/git-refs/tags.txt
git stash list > /work/output/git-refs/stashes.txt
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate > /work/output/git-refs/graph.txt
```

**1. 五份清单先落盘。** `branches.txt` 是 `git branch -a`，`remote-tracking.txt` 是 `git branch -r`，`tags.txt`、`stashes.txt` 和 `graph.txt` 分别是标签、stash 列表和现存引用图。某一份为空时保留空文件和命令，不要改成“没有这类历史”。

```bash
git rev-parse refs/heads/backup > /work/output/git-refs/backup-commit.txt
git cat-file -t refs/tags/release-demo
git show --no-ext-diff --no-textconv release-demo > /work/output/git-refs/tag-show.txt
git rev-parse 'refs/tags/release-demo^{}' > /work/output/git-refs/tag-target.txt
git rev-parse 'stash@{0}' > /work/output/git-refs/stash-commit.txt
git stash show --no-ext-diff --no-textconv -p 'stash@{0}' > /work/output/git-refs/stash.patch
git stash show --no-ext-diff --no-textconv --include-untracked -p 'stash@{0}' > /work/output/git-refs/stash-with-untracked.patch
```

**2. 示例名字要先在清单里出现，再解析。** 示例清单出现 `backup`、`release-demo` 和一条 `stash@{0}`。逐项解析，并记录查到的完整哈希。`refs/heads/backup` 写入 `backup-commit.txt`。`git cat-file -t refs/tags/release-demo` 看标签类型，show 写入 `tag-show.txt`，`^{}` 的目标写入 `tag-target.txt`。`stash@{0}` 的完整哈希写入 `stash-commit.txt`，两份补丁分别是默认补丁和 `--include-untracked`。实际清单里没有这些名字时，改用清单里的名字，不要套示例。

本节已核对backup 的提交、release-demo 的类型和目标、stash 的完整哈希；清单里没有的名字；不要用构造示例填到真实材料上。五个列表文件和随后的解析输出使用同一批引用名，一并留存 `/work/output/git-refs/` 里的列表、`backup-commit.txt`、`tag-target.txt`、`stash-commit.txt` 和两份补丁。

### 05.2 内容与归属复核

三个入口的哈希已经有了，还要看 `app/config.yml` 在备份分支和标签目标里各是什么，以及 blame 标的是哪一次修改。

操作顺序：先导出两份配置，再 diff 和 blame，对上三份状态还不能决定当时哪一份生效。

```bash
git show --no-ext-diff --no-textconv refs/heads/backup:app/config.yml > /work/output/git-refs/config-backup.yml
git show --no-ext-diff --no-textconv 'refs/tags/release-demo^{}:app/config.yml' > /work/output/git-refs/config-release.yml
git diff --no-ext-diff --no-textconv refs/heads/backup 'refs/tags/release-demo^{}' -- app/config.yml
git blame refs/heads/backup -- app/config.yml
sha256sum /work/output/git-refs/config-backup.yml /work/output/git-refs/config-release.yml
```

**1. 三份状态分开记，名称不能代替内容。** 示例 backup 配置含 `DB_HOST=db.internal`，发布标签对应版本改为 `DB_HOST=db.service`，stash 补丁另增加调试开关。应记录为三个不同状态：备份分支快照、标签目标快照、未提交修改快照。`refs/heads/backup:app/config.yml` 写入 `config-backup.yml`。`refs/tags/release-demo^{}:app/config.yml` 写入 `config-release.yml`。diff 比较这两个引用的该路径。`git blame refs/heads/backup -- app/config.yml` 只解释 backup 这一版里各行最近的提交。`sha256sum` 核对两份导出。路径不存在时保留报错，不要改用 main 的当前文件充数。

**2. 哪一份当时生效，还要部署和容器配置。** 哪一份在事件时生效仍需部署与容器配置证据，不因引用名称自动认定。

本节已核对备份分支、标签目标和 stash 补丁里的三份不同配置状态；部署记录和容器配置；没有这些时不指定哪一份当时生效。两份导出的 SHA-256、diff 和 blame 都限定在 `app/config.yml`，一并留存 `config-backup.yml`、`config-release.yml`、diff、blame 和 SHA-256。

### 05.3 恢复演练与限制

需要把 stash 放进工作树时，不能在分析副本上做。先复制到演练目录，再和应用前导出的补丁比较。

操作顺序：先复制并保存 HEAD，再应用已确认的候选，核对实际差异，不只看退出状态。

【仅在副本/仿真/授权环境执行】应用会改演练副本的工作树。分析副本只保留前面的导出。

**1. 在演练目录里应用，并和已导出的补丁比较。** 需要重建 stash 时，把完整分析目录复制到 `/work/lab/stash-recovery/`，保存应用前 HEAD 和 status，再应用已确认的候选。应用后比较 `git diff --no-ext-diff --no-textconv` 与之前导出的 stash 补丁，记录冲突；成功退出但有差异时继续核对基线提交与路径，不声称已完整重现。

**2. 最终清单写上覆盖不到的情况。** 最终清单保留引用名、引用类型、解析对象哈希、路径、导出哈希和局限。没有 stash 可能是未创建、已清理、采集不全或普通克隆导致；远程跟踪分支不说明实时远端状态；blame 不作为身份定论。可核对 [Git 官方 stash 文档](https://git-scm.com/docs/git-stash)、[tag 文档](https://git-scm.com/docs/git-tag)与 [blame 文档](https://git-scm.com/docs/git-blame)。

本节已核对演练副本里应用后的 diff，和先前导出的 stash 补丁是否一致；冲突、基线提交不一致，或材料里本来就没有 stash、只有远程跟踪名。应用前 HEAD、status 还在，成功退出后的差异已经和补丁对过，一并留存引用名、类型、对象哈希、路径、导出哈希，以及演练目录里的冲突记录。
