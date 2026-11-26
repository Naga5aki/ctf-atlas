---
title: "Git 深度取证与对象恢复"
summary: "解析 Git 对象、悬空提交和残留数据，寻找未引用线索。"
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

手里是一份常规分支与 `reflog` 都已找不到目标提交的 Git 仓库副本，需要从底层对象库（`.git/objects` 与 packfile）中寻回悬空提交、树或文件块。原始材料保持只读。

**顺着 commit、tree、blob 读懂对象模型 → 用 fsck 找出不可达与悬空对象 → 用 cat-file 按类型只读解析 → 枚举松散与打包对象并还原路径 → 按只读顺序从悬空提交恢复历史配置。**

当提交不再被分支引用时，内容未必立即消失。先检查对象库的连通性和有效性，再按 commit → tree → blob 关系恢复；不要把一条悬空 blob 的内容直接当成已确定路径、作者或时间的文件。

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

<span id="01-git-对象模型"></span>

## 01 顺着 commit、tree、blob 读懂对象模型

对象库里已经有哈希，还分不清它是提交、目录还是文件字节。先按类型读这张表，再把对象 ID 和导出文件的 SHA-256 分开。

操作顺序：先认 commit、tree、blob、tag，再区分两种哈希，对上 blob 没有文件名。

<details>
<summary>展开四类 Git 对象结构表</summary>

| 类型 | 保存内容 | 取证意义 |
| --- | --- | --- |
| commit | 根 tree、父提交、作者、提交者、说明 | 重建父链与提交上下文 |
| tree | 文件名、模式、子 tree/blob 哈希 | 将内容关联到目录和路径 |
| blob | 文件字节，不保存文件名或普通文件时间 | 导出残留内容，识别格式 |
| tag | 带注释标签的目标、标签者、说明 | 验证发布点与标签上下文 |

</details>

**1. 按表把四类对象分开读。** commit 保存根 tree、父提交、作者、提交者和说明，用来重建父链。tree 保存文件名、模式和子 tree/blob 哈希，用来把内容关联到路径。blob 只有文件字节，不保存文件名或普通文件时间。tag 保存带注释标签的目标、标签者和说明。类型对不上时，先用 `cat-file -t` 看实际类型，不要按哈希长度猜。

**2. 对象 ID 和导出文件的 SHA-256 不是同一件事。** Git 对象按内容寻址，仓库可以采用 SHA-1 或 SHA-256 格式。对象 ID 用于库内定位，导出文件的 SHA-256 用于保全核对，这两个哈希不是同一语义。blob 的对象 ID 计算包含 Git 对象头，不能直接拿文件 `sha256sum` 与一个 blob ID 判定是否一致。

本节已核对候选哈希的类型，以及它能回答路径、父链还是只有字节；只有 blob、没有 tree 时，文件名和普通文件时间仍然没有。类型和表中“保存内容”一列一致；文件 `sha256sum` 没有被拿去和 blob ID 直接比较，一并留存对象类型、对象 ID，以及另行计算的导出文件 SHA-256。

<span id="02-使用-fsck-检查对象"></span>

## 02 用 `fsck` 找出不可达与悬空对象

分支列表里已经没有旧提交，对象却可能还在。先做连通性检查，再分清不可达和悬空，最后才考虑会写目录的 `--lost-found`。

操作顺序：先保存 fsck 输出，再区分不可达和悬空，对上 --lost-found 写进去的是工具输出。


### 02.1 基本命令与输出

当前副本是 `/work/copy/repository`，还不知道引用之外还有没有对象，以及有没有损坏。先保存默认检查，再按需要扩大范围。

操作顺序：先跑 fsck 和 --full，再单独保存忽略 reflog 的结果，对上 missing 或 corrupt 影响哪条链。

```bash
cd /work/copy/repository
git fsck
git fsck --full
```

**1. 先保存默认检查，再按需要扩大范围。** `git fsck` 通常以引用、索引和 reflog 等记录为起点。`--full` 检查 pack 及可能的替代对象池；当前版本通常默认 full，显式写出便于记录。没有 dangling 输出，不代表分支之外没有提交：旧对象可能仍被 reflog 保留。要找这类对象，继续保存下面忽略 reflog 的检查结果。

**2. 需要区别引用图和本地指针记录时，在同一副本中另保存第二份检查。**

```bash
git fsck --full --unreachable --no-reflogs > /work/output/fsck-without-reflogs.txt 2>&1
```

`--no-reflogs` 不把 reflog 当作可达性起点；`--unreachable` 报告从选定起点到不了的对象。命令不会删除对象。出现 missing/corrupt 时，先记录缺失或损坏哈希，再追到引用它的 commit、tree 或索引，标清受影响的文件或祖先。每次保存 Git 版本、完整命令、退出状态、标准输出和标准错误。检查失败不是“没有残留”。单个候选能读取，只说明这条对象链已验证，不能抵消同次检查的其他 missing/corrupt。

本节已核对默认 `fsck`、`--full`，以及忽略 reflog 后的不可达对象或 missing/corrupt；没有 dangling 行时，仍要看 reflog 是不是还指着旧提交。两份检查的命令、退出状态、标准输出和标准错误都在；一条能读的候选没有拿来抵消其他损坏，一并留存Git 版本、`/work/output/fsck-without-reflogs.txt`，以及缺失或损坏哈希和引用它们的对象。

### 02.2 不可达与悬空术语

检查输出里同时有 unreachable 和 dangling，还不能把所有不可达对象都叫悬空。先按表用词，再决定下一步读类型、父链还是导出。

操作顺序：先按表区分四个术语，再决定读类型、父链或导出，对上悬空只是不可达集合的端点。

<details>
<summary>展开 fsck 常见输出判读表</summary>

| 术语 | 含义 | 下一步 |
| --- | --- | --- |
| unreachable object | 从选定起点无法到达的对象 | 用 `cat-file -t` 确认类型，再读内容 |
| dangling commit | 没有其他对象引用的不可达提交边界 | 检查提交、父链和根 tree |
| dangling blob | 未被其他对象引用的不可达内容对象 | 导出识别，但路径未必能确定 |
| dangling tree | 未被其他对象引用的不可达目录对象 | 检查模式、文件名与子对象 |

</details>

**1. 按表选择下一步，不要把四个词当成同一件事。** unreachable object 是从选定起点到不了的对象，下一步用 `cat-file -t` 确认类型。dangling commit 是没有其他对象引用的不可达提交边界，要检查提交、父链和根 tree。dangling blob 导出后路径未必能确定。dangling tree 要检查模式、文件名与子对象。输出里的词和表对不上时，先保留原文，不要改写成另一个术语。

**2. 悬空只是端点，残留也不直接等于恶意行为。** dangling 是不可达集合中没有被其他对象引用的端点，不等于“所有不可达对象”。一个悬空 commit 的父提交、tree 和 blob 可能都不可达，却不是单独的 dangling 项。普通暂存、合并或中断操作也会留下对象；残留不直接等于恶意行为。

本节已核对这条输出是 unreachable、dangling commit、dangling blob 还是 dangling tree；悬空 commit 下面那些不是单独 dangling 项的父提交、tree 和 blob，还要继续读。用词和表中“含义”一列一致，下一步已经按表执行或标明还没做，一并留存fsck 原文、类型，以及还没确定路径的 blob。

### 02.3 `--lost-found` 的影响

只读检查已经有候选，还想把悬空对象落到目录里。这个命令会在 Git 目录里新建文件，只能在可写的恢复副本中使用。

操作顺序：先确认是可写副本，再看新建的 lost-found 路径，对上这些文件是工具输出。

【仅在副本/仿真/授权环境执行】`--lost-found` 会写实际 Git 目录。分析用的只读副本不要跑。

```bash
# 仅在可写的恢复副本中使用
git fsck --lost-found
```

**1. 看它在 Git 目录里新建了什么。** 【仅在副本/仿真/授权环境执行】`--lost-found` 会在实际 Git 目录创建 `lost-found/commit/` 或 `lost-found/other/`，保存部分悬空对象；blob 可能写成内容文件。注释写明仅在可写的恢复副本中使用。命令失败时保留报错，不要到只读检材上重试。

**2. 新建文件标成工具输出，路径仍要靠 tree。** 它不会自动恢复原文件名、全部目录或工作树，也不会自动移动 HEAD。执行前后记录新增路径和哈希，把这些文件标为工具输出，而不是仓库原有遗留物。正式恢复仍要记录对象哈希、类型和 tree 中的路径映射。

本节已核对 `lost-found/commit/` 或 `lost-found/other/` 里新增文件的路径和哈希；原文件名、完整目录和工作树；这些不会自动恢复。执行前后的目录差异只出现在恢复副本，HEAD 没有被这条命令移动，一并留存新增路径、哈希，以及仍待做的对象类型和 tree 路径映射。

<span id="03-cat-file-按类型读取"></span>

## 03 用 `cat-file` 按对象类型只读解析内容

哈希已经有了，还不知道该打印成提交文本、目录条目还是文件字节。先看类型，再按类型读，并把模式和普通文件区分开。

操作顺序：先看 -t，再按类型用 -p，对上模式是普通文件、符号链接还是子模块。

```bash
git cat-file -t <对象哈希>
git cat-file -p <对象哈希>
```

**1. 先看类型，再决定 -p 怎么读。** `-t` 返回类型；`-p` 按类型打印。commit 输出中的 `tree` 是根目录对象，`parent` 是父提交；tree 条目包含模式、子对象类型、哈希与名称；blob 输出是文件字节。对未知二进制 blob 先重定向到分析输出，避免终端控制字符干扰记录。类型不是预期的那一种时，停下来，不要把 blob 字节当成提交说明。

```bash
git cat-file -t "$candidate"
git cat-file -p "$candidate" > /work/output/object-commit.txt
git cat-file -p "$blob" > /work/output/recovered.bin
file /work/output/recovered.bin
sha256sum /work/output/recovered.bin
```

**2. 把候选提交和 blob 分别导出后再识别。** `git cat-file -t "$candidate"` 看候选类型。提交文本写入 `/work/output/object-commit.txt`。blob 写入 `/work/output/recovered.bin`。`file` 识别格式，`sha256sum` 算导出文件的哈希，这个哈希不是 blob 对象 ID。

**3. 模式决定下一步能不能把它当普通文件。** `100644` 通常为普通文件，`100755` 为可执行普通文件，`120000` 为符号链接 blob，`160000` 是子模块提交链接。不能将符号链接文本或子模块提交 ID 当成普通程序内容。模式也有意义，不能把符号链接文本或子模块提交 ID 当成普通程序内容。

本节已核对对象类型，以及 commit 的 `tree`/`parent`、tree 条目或导出的 blob 字节；模式是 `120000` 或 `160000` 时，还没有普通文件内容。`-t` 的类型和 `-p` 的输出一致，二进制已经落到 `recovered.bin` 而不是终端，一并留存 `object-commit.txt` 或 `recovered.bin`、`file` 结果和 SHA-256。

<span id="04-枚举对象与路径"></span>

## 04 枚举松散与打包对象并还原历史路径

要在可达历史里找路径，还是从一条悬空提交把目录树展开，这是两件不同的事。先列可达对象，再沿 commit 和 tree 重建路径。

操作顺序：先列可达对象，再沿 tree 找到路径和模式，只有 blob 时保留路径待核。


### 04.1 可达对象清单

`fsck` 的不可达对象先放着。这一步只回答现存引用还能到达哪些对象、路径能不能跟在哈希后面。

操作顺序：先列出可达对象，再用关键词缩小路径，对上同一 blob 可能出现在多条路径。

```bash
git rev-list --objects --all
git rev-list --objects --all | grep -Ei 'flag|config|backup|secret|password|passwd|token|key'
```

**1. 清单只覆盖现存引用能到达的对象。** `git rev-list --objects --all` 枚举这些对象，能关联的对象后面会显示路径。第二条用 `grep -Ei`，模式是 `flag|config|backup|secret|password|passwd|token|key`。没有路径的行先保留哈希。关键词没有命中，不代表不可达内容里也没有。

**2. 关键词只缩小候选。** 它不代表扫描了全部不可达内容；同一 blob 可在多个提交或不同路径使用，清单也不一定列出全部路径关系。要确定某一条路径，继续用下一节的 tree。

本节已核对现存引用可达的对象，以及能跟在哈希后面的路径；不可达对象，以及清单没有列出的其他路径。命令范围是 `--all` 的可达对象，关键词只标成初筛，一并留存完整对象清单和 grep 命中行。

### 04.2 沿 commit 与 tree 重建

候选已经是一个 commit，或者只剩一个 blob。有提交时先展开树；只有 blob 时把“路径未确定”写进结果。

操作顺序：先读提交，再展开 tree，对上路径、模式和内容来自同一棵树。

```bash
git cat-file -p "$candidate"
git ls-tree "$candidate"
git ls-tree -r "$candidate"
git show --no-ext-diff --no-textconv "$candidate:app/config.yml" > /work/output/config-recovered.yml
```

**1. 有 commit 时先确定路径。** `git cat-file -p "$candidate"` 读提交。`git ls-tree` 看根树，`git ls-tree -r` 展开候选提交树，记录路径、模式及 blob 哈希。`git show --no-ext-diff --no-textconv "$candidate:app/config.yml"` 把该路径导出到 `/work/output/config-recovered.yml`。路径不存在时命令会失败，先回到 tree，不要改工作树。

**2. 按模式区分普通文件、符号链接和 gitlink。** 符号链接 blob 存的是链接目标；gitlink 指向子模块提交，不是普通文件内容。静态分析不跟随链接，也不启动子模块。确需复现链接或子模块的文件系统形态时，另在独立副本验证。

**3. 只有 blob 时写明路径未确定。** 找不到引用 blob 的 tree 时，写明“内容已恢复，原路径未确定”，不要凭内容中的文件名猜原位置。

本节已核对候选提交的路径、模式和 blob，或仅有内容、路径未确定；没有 tree 时的原路径；符号链接和 gitlink 的普通文件内容。`ls-tree -r` 的模式和导出文件来自同一个 `$candidate`，一并留存tree 清单、`config-recovered.yml`，以及“路径未确定”的那些 blob。

<span id="05-深度恢复的顺序"></span>

## 05 按只读枚举到独立副本的顺序做深度恢复

单次命令已经会用，还要把顺序固定下来，避免先清理对象库。按下面五步做，清理命令不进入这个顺序。

操作顺序：先固定仓库和引用，再读类型并恢复路径，对上复现只发生在独立副本。

**1. 先保存仓库位置和整份目录。** 保存仓库路径、实际 Git 目录、HEAD、status、现存分支与采集清单，保全整个目录和外置对象池。外置对象池不在这份副本里时，先补采集，不要在缺对象的目录里继续。

**2. 再读 reflog，并留下两份 fsck。** 阅读 `git reflog`；再分别保留普通 `fsck --full` 与忽略 reflog 的检查结果。两份结果不同并不矛盾，因为起点不同。

**3. 候选先读类型，再按 commit、tree、blob 分开。** 不把全部哈希直接输出为文本。未知二进制先写入文件。

**4. 能找到 commit 或 tree 时记录原路径。** 只能找到 blob 时保留内容与类型限制。

**5. 需要版本复现时换独立副本。** 【仅在副本/仿真/授权环境执行】在独立副本执行 `git switch -c recovered <hash>`，核对 HEAD 和文件哈希。检查中不要运行 gc、prune、repack 清理或修补原始对象库。对象丢失会削弱恢复能力；共享对象池、浅仓库和采集不全也会造成边界，需随结论记录。

本节已核对仓库路径、HEAD、两份 fsck，以及候选的类型和能确定的路径；共享对象池、浅仓库或采集不全造成的缺失对象。复现用的是独立副本里的 `git switch -c recovered <hash>`，原始对象库没有被 gc、prune 或 repack，一并留存采集清单、reflog、两份 fsck、对象类型和导出哈希。

<span id="06-实战从悬空提交恢复历史配置"></span>

## 06 实战：从悬空提交逐层恢复历史配置

分支列表里没有早期部署分支，工作树里也没有旧配置。先从 fsck 取出悬空提交，再映射路径并导出，最后写上这条链的局限。

操作顺序：先固定 HEAD、reflog 和 fsck，再按 tree 导出配置，对上路径来自 tree，不来自 blob 自己。


### 06.1 场景与材料

材料为 `/work/input/repository/` 的完整目录副本，分支列表中没有早期部署分支，工作树也不含旧配置。分析副本位于 `/work/copy/repository/`，输出位于 `/work/output/git-objects/`。

操作顺序：先保存 HEAD、reflog 和两份 fsck，再把完整哈希读成提交和 tree，对上候选来自自己的检查结果。

示例哈希为构造输出，实际操作从自己的 fsck 结果复制完整哈希，不使用示例短哈希猜对象。

```bash
mkdir -p /work/output/git-objects
cd /work/copy/repository
git rev-parse HEAD > /work/output/git-objects/head-before.txt
git reflog --all --date=iso-strict > /work/output/git-objects/reflog.txt
git fsck --full > /work/output/git-objects/fsck.txt 2>&1
git fsck --full --unreachable --no-reflogs > /work/output/git-objects/unreachable.txt 2>&1
```

构造输出中出现：

```text
dangling commit 9f24ac7...（此处省略完整哈希）
```

**1. 两份 fsck 分开存，省略号不能拿去当哈希。** `head-before.txt` 是当前 HEAD。`reflog.txt` 用 `--all --date=iso-strict`。`fsck.txt` 是 `--full`。`unreachable.txt` 再加上 `--unreachable --no-reflogs`。构造输出中出现 `dangling commit 9f24ac7...（此处省略完整哈希）`。省略符只是展示，不能粘贴给 Git。没有 dangling commit 时，先看 reflog 和另一份 fsck，不要用示例短哈希猜对象。

```bash
candidate='替换为检查结果中的完整提交哈希'
git cat-file -t "$candidate"
git cat-file -p "$candidate" > /work/output/git-objects/candidate-commit.txt
git show --no-ext-diff --no-textconv --stat "$candidate"
git ls-tree -r "$candidate" > /work/output/git-objects/candidate-tree.txt
```

**2. 把实际完整哈希放进候选变量再读类型和树。** `candidate` 换成检查结果中的完整提交哈希。`git cat-file -t` 看类型，`-p` 写入 `candidate-commit.txt`。`--stat` 看涉及的文件。`git ls-tree -r` 写入 `candidate-tree.txt`。类型不是 commit 时，按 blob 或 tree 回到上一节，不要对这个变量执行路径导出。

本节已核对自己的 fsck 里那条 dangling commit，以及它的类型和 tree 清单；示例里的省略哈希；它不能代替检查结果中的完整哈希。`candidate` 来自 `fsck.txt` 或 `unreachable.txt` 的原文，`cat-file -t` 为 commit，一并留存 `head-before.txt`、`reflog.txt`、两份 fsck、`candidate-commit.txt` 和 `candidate-tree.txt`。

### 06.2 路径映射与内容导出

tree 清单里已经有一条路径，还要证明内容来自这个路径对应的 blob，而不是 blob 自己带了文件名。

操作顺序：从候选树取出路径和 blob，用两种方式导出并比较，对上字节属于 app/config.yml。

示例 tree 中出现 `100644 blob ... app/config.yml`，据此得到路径和 blob，不是由 blob 自己提供文件名。导出并二次读取同一对象：

```bash
blob=$(git rev-parse "$candidate:app/config.yml")
printf '%s\n' "$blob" > /work/output/git-objects/config-blob.txt
git cat-file -t "$blob"
git cat-file -p "$blob" > /work/output/git-objects/config-from-blob.yml
git show --no-ext-diff --no-textconv "$candidate:app/config.yml" > /work/output/git-objects/config-from-tree.yml
cmp /work/output/git-objects/config-from-blob.yml /work/output/git-objects/config-from-tree.yml
sha256sum /work/output/git-objects/config-from-blob.yml
```

**1. 路径来自 tree 里的模式和名称。** 示例 tree 中出现 `100644 blob ... app/config.yml`，据此得到路径和 blob，不是由 blob 自己提供文件名。`git rev-parse "$candidate:app/config.yml"` 得到 blob，写入 `config-blob.txt`。`cat-file -t` 应为 blob。`-p` 写入 `config-from-blob.yml`。show 再按提交路径写入 `config-from-tree.yml`。`cmp` 比较两份，`sha256sum` 算 blob 导出的哈希。路径不在 tree 里时 show 会失败，先改清单里的真实路径。

**2. 两次一致才记录恢复了该路径的字节。** 类型为 blob、两次内容一致且路径存在于候选树时，可记录“恢复了候选提交中 app/config.yml 的字节内容”。读取 commit 父链及完整时间字段，再判断它与当前分支的关系；作者字段与提交说明都不足以单独归因。

本节已核对候选树中的 `100644`、路径 `app/config.yml`，以及两份导出一致的字节；作者和提交说明还不能单独说明是谁做的这次提交。`cmp` 无差异，blob 类型和 tree 里的路径是同一条，一并留存 `config-blob.txt`、两份 yml、SHA-256，以及 commit 的父链和时间字段。

### 06.3 恢复结果及局限

字节已经导出一份，还要把检查错误和没恢复出来的祖先写进同一张结果表。不要把一个读到的候选写成整段历史都齐全。

操作顺序：先填结果表，再标缺失 blob 和祖先，对上对象还在库里才有恢复基础。

**1. 结果表先写这些字段。** fsck 模式、候选 commit、根 tree、blob、路径、模式、导出文件 SHA-256、检查错误与当前引用关系。缺的格子留空。单个候选读取得到，不保证其全部祖先齐全；若 missing blob 阻断读取，应保留已找到的树与缺失哈希，明确内容无法验证。

**2. 写清 lost-found 和已经清理的字节分别能到哪一步。** 【仅在副本/仿真/授权环境执行】`--lost-found` 可以在恢复副本中辅助归档，但没有自动还原全部文件与提交链的承诺。对象仍在库中才有恢复基础；已经清理的字节需要其他保全副本或备份，不能只凭遗留哈希重建。可核对 [Git 官方 fsck 文档](https://git-scm.com/docs/git-fsck)、[cat-file 文档](https://git-scm.com/docs/git-cat-file)与 [ls-tree 文档](https://git-scm.com/docs/git-ls-tree)。

本节已核对结果表里已经填上的 commit、tree、blob、路径和导出 SHA-256；missing blob、不齐全的祖先，以及已经被清理、只剩下哈希的字节。内容无法验证的项旁边有缺失哈希；`--lost-found` 的文件标成恢复副本里的工具输出，一并留存结果表、检查错误、当前引用关系，以及还需要的其他保全副本或备份。
