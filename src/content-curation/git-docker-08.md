手里是一份完整的源码仓库检材，需要按标准取证流程从首轮保全一路查到现存引用、历史补丁、本地指针与底层不可达对象，并输出可复核的证据表。原始材料保持只读。

**保全仓库副本并固定未提交状态 → 清点全部现存引用并画提交图 → 搜索历史补丁与提交树 → 检查 reflog 与 stash → 扫描不可达对象并串联完整证据表。**

源码取证按“仓库确认 → 现存引用 → 历史内容 → 本地指针 → 不可达对象”推进。每一阶段先固定原始输出，再根据候选路径或对象缩小范围；恢复只在独立副本中进行。

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

<span id="01-材料目录与首轮保全"></span>

## 01 保全仓库副本并固定未提交状态

保全目录已经在手里，还不知道它是普通工作树、裸仓库，还是 `.git` 指到了别处。先约定输入输出路径，再把未提交状态固定下来。

操作顺序：先确认仓库布局，再固定未提交差异，后续命令始终操作这份副本。


### 01.1 输入与输出约定

材料为已保全目录 `/work/input/repository/`，可以是工作树加 `.git`，也可以是裸仓库及其依赖对象目录。分析副本为 `/work/copy/repository/`，输出为 `/work/output/git-investigation/`，恢复演练使用 `/work/lab/repository-recovered/`。还不知道这次 `git status` 能不能直接用。

操作顺序：先整份复制，再读顶层、Git 目录和是否裸仓库，对上外置元数据也在不在。

复制整个目录及外置元数据；普通 clone 不足以保全未提交修改、索引、reflog 和全部残留对象。

```bash
mkdir -p /work/copy /work/output/git-investigation /work/lab
cp -a /work/input/repository /work/copy/repository
cd /work/copy/repository
ls -la
git rev-parse --show-toplevel
git rev-parse --absolute-git-dir
git rev-parse --is-bare-repository
git --no-optional-locks status --porcelain=v1 --branch
git rev-parse HEAD
```

**1. 先看布局，再决定 status 能不能跑。** `cp -a` 把 `/work/input/repository` 复制到 `/work/copy/repository`。`ls -la` 看目录。`--show-toplevel`、`--absolute-git-dir`、`--is-bare-repository` 分别给出工作树根、实际 Git 目录和是否裸仓库。`git --no-optional-locks status --porcelain=v1 --branch` 是流程入口；裸仓库没有普通工作树，应改用 `git --git-dir=/work/copy/repository ...` 读取引用与对象。`git rev-parse HEAD` 留下当前提交。status 报没有工作树时，改走裸仓库读法，不要把失败写成没有对象。

**2. 指针或 alternates 指向别处时先补目录。** 若 `.git` 指向别处或存在 alternates，先确认关联目录齐全。只读挂载保全材料，在副本上运行 Git；可选锁抑制不能代替文件系统保护。

本节已核对工作树或裸仓库布局、实际 Git 目录和 HEAD；外置元数据或 alternates 还不在副本里时，先不要把普通 clone 当采集。`--is-bare-repository` 和 status 的结果一致；裸仓库改用了 `--git-dir`，一并留存 `/work/copy/repository/`、顶层路径、Git 目录和 HEAD。

### 01.2 固定未提交状态

仓库能读了，工作树和暂存区的差异还在终端里。先写到 `/work/output/git-investigation/`，再做会改状态的操作。

操作顺序：先存 status 和 HEAD，再存两份 diff，对上补丁盖不住未跟踪和忽略文件。

```bash
git --no-optional-locks status --porcelain=v1 --branch > /work/output/git-investigation/status.txt
git rev-parse HEAD > /work/output/git-investigation/head.txt
git diff --no-ext-diff --no-textconv > /work/output/git-investigation/worktree.patch
git diff --no-ext-diff --no-textconv --cached > /work/output/git-investigation/index.patch
```

**1. 两份 diff 不是完整备份。** `status.txt` 来自 `git --no-optional-locks status --porcelain=v1 --branch`。`head.txt` 是当前 HEAD。`worktree.patch` 是未暂存差异，`index.patch` 是已暂存差异。它们主要描述已跟踪内容，status 默认也不列忽略文件。补丁为空不代表站点没有变化。重定向失败时保留报错，不要用空补丁代替未跟踪文件。

**2. 未跟踪文件随目录采集，不用 add 去补齐。** 分别保存工作目录实际文件（包括被忽略的配置、上传文件）、索引和 HEAD。完成这些记录之前，不运行 reset 或清理。

本节已核对当前 HEAD、porcelain 状态，以及已跟踪内容的两份 diff；忽略文件和未跟踪文件；它们要靠目录副本，不靠 diff。四个输出文件在做 reset 或清理之前就已经写好，一并留存 `status.txt`、`head.txt`、`worktree.patch`、`index.patch`，以及工作目录里的未跟踪文件。

<span id="02-清点引用并建立提交图"></span>

## 02 清点全部现存引用并画出提交图

未提交状态已经留下，还不知道备份或发布引用在不在当前分支上。先列分支和标签，再对候选提交读 stat 和指定文件。

操作顺序：先列分支、标签和提交图，再对候选提交读 stat 和路径，对上作者字段还要和部署证据核对。

```bash
git branch -a
git tag
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
git branch -a > /work/output/git-investigation/branches.txt
git tag > /work/output/git-investigation/tags.txt
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate > /work/output/git-investigation/graph.txt
```

**1. 名字只决定检查顺序。** 优先找不在当前分支的备份、测试、发布引用。分支名或标签名只决定检查顺序，解析到完整哈希后再读对象。`--all` 覆盖现存引用可达历史，不能保证覆盖删除引用后的残留；远程跟踪引用是本地保存状态。列表写到 `branches.txt`、`tags.txt`、`graph.txt`。没有 backup 这个名字时，继续看图上的其他引用。

```bash
git show --no-ext-diff --no-textconv --stat <候选提交>
git show --no-ext-diff --no-textconv <候选提交>
git show --no-ext-diff --no-textconv <候选提交>:app/config.yml
```

**2. 大提交先看 stat，不为一个文件切换工作树。** 对大提交先用 stat 缩小路径，再查看补丁和指定文件。`<候选提交>:app/config.yml` 只读该路径。不要为了读一个旧文件切换整个工作树。作者、提交者、时间和说明需一起记录，并与实际部署证据核对。路径不存在时先看 stat 里的真实路径。

本节已核对现存分支、标签、提交图，以及候选提交里指定路径的内容；删除引用后的残留，以及还没对上的部署证据。读对象用的是完整哈希，不是只有分支名，一并留存 `branches.txt`、`tags.txt`、`graph.txt`，以及 show 的 stat 和文件内容。

<span id="03-搜索历史内容并确认上下文"></span>

## 03 搜索历史补丁与提交树并确认上下文

提交图里的说明还不能代替文件内容。先把可达补丁搜一遍，再用 `-S` 和 `-G` 分开，最后导出删除前的父代文件。

操作顺序：先导出可达补丁并筛词，再分 -S 和 -G，对上父代文件和删除补丁。

```bash
git log --no-ext-diff --no-textconv -p --all > /work/output/git-investigation/history.patch
grep -nEi 'flag|password|passwd|secret|token|key' /work/output/git-investigation/history.patch
git log --no-ext-diff --no-textconv -G'DB_(HOST|PASSWORD)' --all -p -- app/
git log --no-ext-diff --no-textconv -S'DB_PASSWORD' --all -p -- app/
```

**1. 搜索到一行后要回到提交里核对。** `git log --no-ext-diff --no-textconv -p --all` 先把可达补丁写入 `history.patch`。`grep -nEi` 的模式是 `flag|password|passwd|secret|token|key`。找到关键词后，记下提交和路径，用 `git show --no-ext-diff --no-textconv <commit>` 读完整上下文，不直接把一行值抄成结论。grep 没有命中时，继续做下面的 `-S` 和 `-G`，不要停在“没有敏感信息”。

**2. 次数不变时 -S 可能漏，-G 仍可能命中。** `-S` 查字符串出现次数变化，`-G` 查补丁行的正则匹配。只改变量值、次数不变时，`-S` 可能漏掉而 `-G` 能找到。`-G'DB_(HOST|PASSWORD)'` 和 `-S'DB_PASSWORD'` 都限定在 `app/`。

**3. 删除补丁之后导出父代，并写上覆盖限制。**

```bash
git show --no-ext-diff --no-textconv <候选提交的父代>:app/config.yml > /work/output/git-investigation/config-before.yml
git diff --no-ext-diff --no-textconv <候选提交的父代> <候选提交> -- app/config.yml
sha256sum /work/output/git-investigation/config-before.yml
```

`<候选提交的父代>:app/config.yml` 写入 `config-before.yml`，再对该路径做 diff，并算 SHA-256。删除补丁说明所选提交不再保留该路径，不代表所有分支都删除，也不证明历史配置曾在目标机器生效。文本搜索还存在二进制、编码和缺失对象的覆盖限制。父路径读失败时核对是不是该用另一个父提交。

本节已核对关键词所在的提交和路径，以及父代里的 `app/config.yml`；二进制、编码、缺失对象，以及其他分支上仍保留的同一路径。show 的上下文和 `config-before.yml` 的 SHA-256 来自同一个候选的父代，一并留存 `history.patch`、grep 行号、`-S`/`-G` 补丁和 `config-before.yml`。

<span id="04-本地引用记录与临时修改"></span>

## 04 检查 reflog 引用移动与 stash 临时修改

现存分支已经看过，reset 前的位置和未提交修改可能只在 reflog 或 stash 里。先把记录导出，再解析完整哈希。

操作顺序：先存 reflog 和 stash 列表，再把编号解析成哈希，对上没有记录不等于没有本地修改。

```bash
git reflog
git reflog --all --date=iso-strict > /work/output/git-investigation/reflog.txt
git stash list
git stash show --no-ext-diff --no-textconv -p 'stash@{0}'
```

**1. 先解析完整哈希，编号只留在原始输出里。** reflog 可能找回 reset、rebase 和切换前的位置；stash 可能保留未提交配置。`git reflog --all --date=iso-strict` 写入 `reflog.txt`。`git stash list` 和 `git stash show -p 'stash@{0}'` 看最新一条的默认补丁。先解析候选完整哈希再读对象。编号 `HEAD@{1}`、`stash@{0}` 会变动，报告不用编号替代哈希。查看 stash 的默认补丁不保证包含保存的未跟踪内容，必要时补 `git stash show --no-ext-diff --no-textconv --include-untracked -p 'stash@{0}'`。

**2. 没有记录时先写原因，候选先 show。** 不存在 reflog 或 stash 不能证明没有本地修改；普通克隆、过期和清理都可能导致记录不可见。发现候选后先 show 验证，不直接 apply 或 reset。

本节已核对reflog 或 stash 里的候选完整哈希，以及默认补丁是否包含未跟踪内容；过期、清理或普通克隆导致看不见的本地记录。报告用完整哈希；验证用的是 show，不是 apply 或 reset，一并留存 `reflog.txt`、stash 列表、补丁和解析后的哈希。

<span id="05-不可达对象与内容恢复"></span>

## 05 扫描不可达对象并恢复已删除内容

引用和 reflog 都看过之后，对象库里还可能有到不了的提交。先做两份 fsck 和一份可达清单，再按类型读对象。

操作顺序：先保存两份 fsck 和可达清单，再按类型读对象，只有 blob 时保留路径待核。

```bash
git fsck --full > /work/output/git-investigation/fsck.txt 2>&1
git fsck --full --unreachable --no-reflogs > /work/output/git-investigation/unreachable.txt 2>&1
git rev-list --objects --all > /work/output/git-investigation/reachable-objects.txt
git cat-file -t <候选对象>
git cat-file -p <候选对象>
```

**1. 两份清单各回答一个问题。** `rev-list --objects --all` 写入 `reachable-objects.txt`，列出现存引用可达对象。`fsck` 检查连通性并提供不可达候选；这次的 `fsck --full` 写入 `fsck.txt`。第二条加上 `--unreachable --no-reflogs`，写入 `unreachable.txt`。`git cat-file -t` 和 `-p` 读候选对象。默认 fsck 把 reflog 等作为起点，第二条命令忽略 reflog，所以结果不同并不矛盾。两次检查使用同一副本、同一批固定的引用/索引/日志，分别保存命令、起点选项、退出状态与错误。若中途做了 reset、stash 或同步，先登记变更，不能将后来的结果倒填为采集时状态。

**2. 按类型处理，未知二进制不要打到终端上。** commit 追根 tree 和父链，tree 记录路径与模式，blob 导出字节并识别格式。只有 blob 而没有 tree 时，路径与作者仍未确定。未知二进制对象写入输出文件后检查，不直接显示在交互终端。

```bash
git cat-file -p <已确认的blob哈希> > /work/output/git-investigation/recovered.bin
file /work/output/git-investigation/recovered.bin
sha256sum /work/output/git-investigation/recovered.bin
```

本节已核对可达对象清单、两份 fsck 的差异，以及候选对象的类型；只有 blob、没有 tree 时的路径和作者；中途改过仓库时不能倒填成采集时状态。两份 fsck 的起点选项和退出状态都在，`recovered.bin` 的 SHA-256 是文件哈希，一并留存 `fsck.txt`、`unreachable.txt`、`reachable-objects.txt` 和 `recovered.bin`。

<span id="06-实战串起删除文件与保留对象"></span>

## 06 实战：串联删除提交、悬空对象与验证记录

当前目录里的配置已经删除，backup 或其他对象里可能还留着。先从补丁找到删除提交，再检查其他入口，最后只在独立副本里恢复。

操作顺序：先从补丁定位删除提交，再查 backup、reflog、stash 和 fsck，对上恢复分支没有混进历史时间。


### 06.1 场景与初步结果

假设当前 app 目录缺少历史配置，保全材料有完整对象库和本地引用日志。还要把删除提交解析成完整哈希，并导出父代文件。本文构造输出演示一条可复核链，不表示对实际附件做过复跑。

操作顺序：先看 status、引用和这个路径的补丁，再解析候选并导出父代，对上两份读取一致。

首轮记录显示工作树干净，main 最后一个提交说明为删除临时配置，另有 backup 引用。

```bash
cd /work/copy/repository
git status
git branch -a
git tag
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
git log --no-ext-diff --no-textconv -p --all -- app/config.yml
```

**1. 先看工作树、引用和这个路径的补丁。** `git status` 看工作树是否干净。`git branch -a` 和 `git tag` 列引用。图用来看 main 和 backup。最后一条只看 `app/config.yml` 的补丁。示例补丁把候选缩到短哈希 `9f24ac7`，其父代为 `6a03c11`。实际哈希以这次输出为准。

```bash
candidate=$(git rev-parse 9f24ac7)
printf '%s\n' "$candidate" > /work/output/git-investigation/candidate.txt
git show --no-ext-diff --no-textconv --stat "$candidate"
git show --no-ext-diff --no-textconv "$candidate" -- app/config.yml
git show --no-ext-diff --no-textconv "$candidate^1:app/config.yml" > /work/output/git-investigation/config-before.yml
blob=$(git rev-parse "$candidate^1:app/config.yml")
git cat-file -t "$blob"
git cat-file -p "$blob" > /work/output/git-investigation/config-from-object.yml
cmp /work/output/git-investigation/config-before.yml /work/output/git-investigation/config-from-object.yml
sha256sum /work/output/git-investigation/config-before.yml
```

**2. 先把候选解析成完整哈希，确认路径变化并导出父代文件。** `git rev-parse 9f24ac7` 得到完整哈希并写入 `candidate.txt`。`--stat` 和路径补丁确认删除。`$candidate^1:app/config.yml` 导出父代。再取 blob，用 `cat-file -t`、`cat-file -p` 写到 `config-from-object.yml`，与 `config-before.yml` 做 `cmp`，并算 SHA-256。`cmp` 不一致或类型不是 blob 时，先不要写两条读取已经互相印证。

本节已核对删除提交的完整哈希、父代 `6a03c11` 这一示例关系，以及两份父代读取一致；backup、reflog、stash 和 fsck 还没看时，不写成只有这一条历史。`candidate.txt` 是 `rev-parse` 的完整哈希，`cmp` 没有差异，一并留存status、引用列表、补丁、`config-before.yml`、`config-from-object.yml` 和 SHA-256。

### 06.2 检查其他保留入口

父代文件已经导出，还要看 backup 是否仍保留同一份配置，以及 reflog、stash、fsck 里有没有另一条链。

操作顺序：先读 backup 的同一路径，再看 reflog、stash、fsck 和可达对象，对上悬空对象先单独验证。

```bash
git show --no-ext-diff --no-textconv backup:app/config.yml > /work/output/git-investigation/config-backup.yml
git reflog --all --date=iso-strict
git stash list
git fsck --full
git rev-list --objects --all
```

**1. backup 对得上时，恢复不必依赖 fsck。** `backup:app/config.yml` 写入 `config-backup.yml`。如果 backup 中的配置与父代导出一致，则旧内容仍由现存引用保留；恢复不必依赖 fsck。路径读失败时保留报错，再看下面几条。

**2. 悬空提交是另一条候选，不写进主线。** `git reflog --all --date=iso-strict`、`git stash list`、`git fsck --full` 和 `git rev-list --objects --all` 分别留下本地记录、未提交入口、不可达候选和可达对象。若另发现 dangling commit，它是另一条候选链，需先 cat-file 读取类型与 tree，再判断是否与本次配置相关。不要看到悬空对象就把它写成主线结论。

本节已核对backup 里的 `app/config.yml` 是否与父代导出一致；dangling commit 还没读类型和 tree 时，它还不是这次配置的主线。`config-backup.yml` 和父代导出的比较结果，以及 fsck 原文，一并留存backup 导出、reflog、stash 列表、fsck 和可达对象清单。

### 06.3 独立恢复与结果表

要在工作树里重现父代版本时，换到演练目录。分析副本的 HEAD 保持不动。

操作顺序：先复制并记下原 HEAD，再在演练目录建恢复分支，对上结果表里每一阶段的限制。

【仅在副本/仿真/授权环境执行】要重建版本，先将完整分析目录复制到 `/work/lab/repository-recovered/`，再进入该目录执行下列命令。记录复制来源及原分析目录 HEAD。恢复分支会新建引用、移动副本 HEAD，并更新索引/工作树；产生的引用和文件时间单独记为恢复实验，不混入历史事件。

```bash
candidate=$(cat /work/output/git-investigation/candidate.txt)
git switch -c recovered "$candidate^1"
git rev-parse HEAD
git status
cmp app/config.yml /work/output/git-investigation/config-before.yml
```

<details>
<summary>展开 Git 取证五阶段记录与结论边界表</summary>

| 阶段 | 最小记录 | 结论限制 |
| --- | --- | --- |
| 仓库识别 | 工作树、Git 目录、HEAD、status | 不保证外置对象已全部采集 |
| 引用检查 | 分支/Tag、完整哈希、提交图 | 只覆盖现存引用视图 |
| 内容定位 | commit、父代、路径、补丁、blob | 历史内容不直接证明运行配置 |
| 本地恢复 | reflog/stash 条目与解析哈希 | 本地记录可能过期或缺失 |
| 对象恢复 | fsck 模式、类型、tree 映射、导出哈希 | 已清理字节无法由哈希重建 |

</details>

**1. 在演练副本里切到父代，再和已导出的文件比较。** `candidate` 读 `candidate.txt`。`git switch -c recovered "$candidate^1"` 从父代建分支。`git rev-parse HEAD` 和 `git status` 核对切换结果。`cmp` 比较工作树里的 `app/config.yml` 与 `config-before.yml`。不一致时先核对 `^1` 是不是这次要的父代，不要在分析副本上重做。

**2. 用结果表写每一阶段能证明什么。** 恢复验证至少包括对象类型、历史路径、两种读取结果一致以及恢复副本 HEAD 正确。报告说明已覆盖的引用、缺失对象、未提交状态与未证实的运行关系。流程结束时保留所有输出的哈希和采集时间；不执行仓库清理来“整理”证据。完整命令语义可核对 [Git 官方用户手册](https://git-scm.com/docs/user-manual)与 [Git 官方 fsck 文档](https://git-scm.com/docs/git-fsck)。

本节已核对恢复分支 HEAD 指向父代，工作树里的配置和 `config-before.yml` 一致；表里每一阶段的结论限制：外置对象、删除后的残留、运行配置、过期的本地记录、已清理的字节。`cmp` 无差异，新引用和文件时间记在恢复实验里，没有并进历史事件，一并留存演练目录、原分析目录 HEAD、结果表，以及全部输出的哈希和采集时间。
