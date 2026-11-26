手里是一份发生过回退、切换或删除的 Git 仓库副本，需要找回被 `reset` 移走的提交或被删改的文件。原始材料保持只读，先只读导出到外部目录，确需修改工作区时只在独立演练副本中进行。

**对照 log 与 reflog 找回历史引用 → 分清 reset 三种模式的影响范围 → 先只读导出对象再在独立副本恢复 → 实战从 reflog 找回 reset 前的配置提交。**

恢复时先读对象、再导出文件，最后才在独立副本里切换或建立分支。`log` 解释现存提交图，`reflog` 解释本地引用曾指向哪里；两种记录的保留范围不同。

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

<span id="01-log-与-reflog"></span>

## 01 对照 `log` 与 `reflog`，找回本地移动过的引用

分支比预期少了一个提交，还不知道该看现存提交图，还是本地引用曾经指向哪里。先分清两种记录，再在恢复前把当前 HEAD 和差异固定下来。

操作顺序：先分清 log 和 reflog，再固定恢复前状态，对上旧位置还在不在。


### 01.1 两种记录的含义

手里有仓库副本，reset 之后当前 `git log` 已经看不到旧提交。先用表分清两种记录各自留下什么，再从 reflog 里抽出候选哈希。

操作顺序：先对照表，再读 log 和 reflog，对上旧提交的完整哈希，而不是编号。

<details>
<summary>展开 log 与 reflog 对照表</summary>

| 项目 | `git log --no-ext-diff --no-textconv` | `git reflog` |
| --- | --- | --- |
| 记录对象 | 提交及其父子关系 | 本地 HEAD、分支等引用的移动记录 |
| 默认范围 | 当前提交可达历史 | 当前 HEAD 的本地移动记录 |
| reset 后 | 被移出所选分支的提交可能不再显示 | 未过期时可能仍保留旧位置 |
| 传输范围 | 可达提交可随克隆、获取或推送传输 | 通常是本地记录，不随普通 push/clone 传输 |
| 恢复用途 | 找历史版本和删除补丁 | 找 reset、rebase、切换前的候选提交 |

</details>

**1. 先按表决定这次该读 log 还是 reflog。** 表的左列是提交图，右列是本地引用移动。reset 后 log 可能不再显示旧提交，reflog 未过期时仍可能留着旧位置。不要用其中一种记录代替另一种。

```bash
cd /work/copy/repository
git log --no-ext-diff --no-textconv
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
git reflog
git reflog --all --date=iso-strict
```

构造示例：

```text
6a03c11 HEAD@{0}: reset: moving to HEAD~1
9f24ac7 HEAD@{1}: commit: add deployment configuration
```

**2. 示例先给出候选，不直接证明恢复成功。** HEAD 曾从 `9f24ac7` 移到 `6a03c11`，旧提交可能仍在对象库。`git reflog` 看当前 HEAD；`git reflog --all --date=iso-strict` 扩大到全部引用并保留严格时间。没有这行时，先查 reflog 是否过期或这份材料是普通克隆。

**3. 把编号解析成完整哈希，再读对象。** 先保留原始 reflog 文件，摘录引用名、旧/新哈希、时间及操作说明。同一对象可能在多次移动中出现。将 `HEAD@{1}` 解析为完整对象哈希。后续操作会改变编号，报告不能只记这个编号。用 cat-file 检查该对象。reflog 日期表示引用变动，不代替 commit 的作者/提交者时间。只保存编号解析后的哈希，会丢掉“为什么选中这个提交”的本地记录。

本节已核对reflog 里的旧位置 `9f24ac7`，以及它对应的完整对象哈希；还没用 cat-file 读到对象时，这行记录还不是已恢复的文件。引用名、旧/新哈希、时间和操作说明还在，报告不只写 `HEAD@{1}`，一并留存原始 reflog、两条 log 输出，以及解析后的完整哈希。

### 01.2 恢复前固定当前状态

准备动副本之前，当前 HEAD、未提交差异和 reflog 还没存到仓库外。先把这五份输出写好，再做任何 reset 或切换。

操作顺序：先写下 HEAD 和两份 diff，再存 reflog，对上补丁盖不住的未跟踪文件。

```bash
mkdir -p /work/output/git-recovery
git rev-parse HEAD > /work/output/git-recovery/head-before.txt
git --no-optional-locks status --porcelain=v1 --branch > /work/output/git-recovery/status-before.txt
git diff --no-ext-diff --no-textconv > /work/output/git-recovery/worktree-before.patch
git diff --no-ext-diff --no-textconv --cached > /work/output/git-recovery/index-before.patch
git reflog --all --date=iso-strict > /work/output/git-recovery/reflog.txt
```

**1. 五份输出分开保存，补丁空也不要跳过目录副本。** `head-before.txt` 是当前 HEAD。`status-before.txt` 是分支和 porcelain 状态。`worktree-before.patch` 是索引到工作树的差异，`index-before.patch` 是 HEAD 到索引的差异。`reflog.txt` 用 `--all --date=iso-strict`。补丁不能保全所有未跟踪文件、二进制属性或外置对象，完整目录副本仍是前提。某一条重定向失败时保留报错，不要用后一次命令覆盖前面的空文件而不检查。

**2. 看不到旧位置时，先写明记录为什么不在。** reflog 可能被禁用、过期或清理；普通克隆缺少它也很常见。“未看到旧位置”不能证明从未重写历史。

本节已核对恢复前的 HEAD、status、工作树差异、索引差异和 reflog；未跟踪文件、二进制属性和外置对象，补丁里没有的要靠完整目录副本。五个输出路径都有内容或明确的失败记录，时间还是采集时的原值，一并留存 `/work/output/git-recovery/` 里的 `head-before.txt`、两份 patch 和 `reflog.txt`。

<span id="02-reset-三种模式"></span>

## 02 分清 `reset` 三种模式对 HEAD、索引和工作区的改动

旧提交可能还在，但不能靠 reset 来“找回文件”。先分清 soft、mixed、hard 各改 HEAD、索引还是工作树，再只在三个独立练习目录里各看一种。

操作顺序：先分清三种模式改什么，再在各自的练习副本里观察，只读导出旧文件时不必先 reset。


### 02.1 提交指针、索引与工作树的区别

命令表已经能区分三种 reset，还容易把带路径的 reset 当成也会移动 HEAD。先读表，再把 `-- <path>` 和 `--hard` 的失败分支分开。

操作顺序：先按表看 HEAD、索引和工作树，再核对有没有路径参数，对上 hard 会改到哪些未提交内容。

<details>
<summary>展开 reset 三种模式影响表</summary>

| 命令 | HEAD/当前分支 | 索引 | 工作树 | 常见结果 |
| --- | --- | --- | --- | --- |
| `git reset --soft HEAD~1` | 移到父提交 | 保留 | 保留 | 被撤回提交的变化仍保持暂存 |
| `git reset --mixed HEAD~1` | 移到父提交 | 重置为目标树 | 保留 | 变化通常成为未暂存修改 |
| `git reset HEAD~1` | 移到父提交 | 重置为目标树 | 保留 | 默认与 mixed 相同 |
| `git reset --hard HEAD~1` | 移到父提交 | 重置为目标树 | 重置为目标树 | 丢弃冲突的工作状态并改写文件 |

</details>

**1. 这四行都是带提交参数、没有路径限定的 reset。** `--soft` 只把 HEAD/当前分支移到父提交，索引和工作树保留，被撤回提交的变化仍保持暂存。`--mixed` 和默认的 `git reset HEAD~1` 还会把索引重置为目标树，变化通常成为未暂存修改。`--hard` 再把工作树重置为目标树。和表不一致时，先看命令里有没有路径。

**2. 带路径的 reset 不要套用“移动 HEAD”。** `git reset -- <path>` 则主要修改索引，不应套用“移动 HEAD”这个结论。`--hard` 会覆盖已跟踪文件的未提交内容，并可能删除或覆盖妨碍目标文件写入的未跟踪路径，不能简化成“绝不影响未跟踪文件”。

本节已核对所选模式会改 HEAD、索引、工作树中的哪些层；命令带了路径，或工作树里有未跟踪文件时，不能直接套表里“移动 HEAD”的那一行。实际命令和表中的四列一致，路径形式单独记录，一并留存选用的 reset 形式，以及执行前已经保存的 HEAD、索引和工作树。

### 02.2 只在练习副本中观察模式

要比较三种模式，还不能在同一个目录里连着做三次。每次都会再退一格，比较就没有共同起点。

操作顺序：从同一起点复制三个目录，各做一种 reset，对上取证恢复旧文件不必先 reset。

【仅在副本/仿真/授权环境执行】下列三条命令是不同模式的语法示例，不是连续步骤。依次执行会反复后退，比较结果也就失去共同起点。要比较模式，从同一初始仓库复制三个独立目录，分别执行一种 reset。三种提交形式都可能移动 HEAD/分支并留下 reflog；`--mixed` 还改索引，`--hard` 还改工作树。分别保存前后的 HEAD、索引差异、工作树差异和 reflog。

```bash
# /work/lab/recovery-soft 中
git reset --soft HEAD~1
git status

# /work/lab/recovery-mixed 中
git reset --mixed HEAD~1
git status

# /work/lab/recovery-hard 中
git reset --hard HEAD~1
git status
```

**1. 三个目录各执行一种，做完分别看 status。** `/work/lab/recovery-soft` 只跑 `--soft`，`/work/lab/recovery-mixed` 只跑 `--mixed`，`/work/lab/recovery-hard` 只跑 `--hard`。注释已经写明目录。`git status` 看这一次之后的暂存和工作树。如果三个命令出现在同一目录的历史里，这次比较作废，回到复制前的起点重做。

**2. 取证恢复旧文件时先导出，不先 reset。** 先用 `git show --no-ext-diff --no-textconv` 导出目标内容可以避免移动分支和覆盖工作树；若为了复现使用 hard，必须保全未提交和未跟踪材料，并明确记录副本路径及变化。

本节已核对三种模式各自的 HEAD、索引差异、工作树差异和 reflog；三个目录不是从同一次复制开始时，status 不能互相比较。每个目录只执行了一种 reset，前后记录都在，一并留存三个练习目录的路径，以及各自前后的 HEAD、diff 和 reflog。

<span id="03-恢复整个版本与单个文件"></span>

## 03 先只读导出对象，再在独立副本恢复文件

目标可能是一个旧文件，也可能是整个提交。先只读导出，再决定要不要在工作副本里切换或恢复路径。

操作顺序：先用 show 导出单个文件，再按表选择切换或恢复，对上改动的是引用、索引还是工作树。


### 03.1 只读导出优先

已经有提交 `9f24ac7` 和路径 `app/config.yml`，还不需要切换仓库。先把该提交树里的文件导出，并核对冒号右侧的路径确实存在。

操作顺序：导出指定提交里的路径，再算 SHA-256，对上提交可读不等于每个 blob 都在。

```bash
git show --no-ext-diff --no-textconv 9f24ac7:app/config.yml > /work/output/git-recovery/config-recovered.yml
sha256sum /work/output/git-recovery/config-recovered.yml
```

**1. 冒号右侧必须是所选提交树里的路径。** `git show --no-ext-diff --no-textconv 9f24ac7:app/config.yml` 把该路径写到 `/work/output/git-recovery/config-recovered.yml`，`sha256sum` 再算导出文件。Shell 的 `>` 可能先创建空文件；Git 报对象不存在时，不要把空文件当成恢复结果。

**2. 提交能读，不等于里面每个文件都能导出。** 提交恢复和文件恢复是不同目标：一个 commit 可以读取到，并不表示其所有父代和 blob 都齐全，继续检查对象有效性及目录内容。

本节已核对提交 `9f24ac7` 的树里存在 `app/config.yml`，并且导出文件有 SHA-256；父代或别的 blob 缺失时，这次导出不能代表整个提交都齐全。Git 退出状态正常，导出内容的长度和哈希已经核对，一并留存 `config-recovered.yml` 和它的 SHA-256。

### 03.2 工作副本中的切换与恢复命令

只读导出还不够，需要在副本里看到工作树或新建分支。先按表选一条命令，四条不要接连执行。

操作顺序：先看表里改的是 HEAD、索引还是工作树，再在副本里只做一种，对上这次究竟动了哪一层。

<details>
<summary>展开切换与恢复命令副作用表</summary>

| 命令 | 改变对象 | 含义 |
| --- | --- | --- |
| `git checkout <commit>` | HEAD 与工作树，通常还有索引 | 切换到提交，进入 detached HEAD |
| `git checkout <commit> -- <filename>` | 指定路径的索引与工作树 | 以旧版本替换该文件，不移动分支 |
| `git restore --source=<commit> <filename>` | 默认仅工作树 | 从指定提交恢复路径，默认不更新索引 |
| `git switch -c recovered <commit>` | 新分支、HEAD、工作树 | 从旧提交建立恢复分支并切换 |

</details>

```bash
# 在 /work/lab/repository-recovered 副本中，选择所需的一种操作
git checkout 9f24ac7
git checkout 9f24ac7 -- app/config.yml
git restore --source=9f24ac7 -- app/config.yml
git switch -c recovered 9f24ac7
```

**1. 先决定要恢复什么，再选表里的一条命令。** 只提取旧文件：用上一节 show 导出对象，不切换整个仓库。切换版本或分支：按表选择 checkout/switch，并保存 HEAD、索引及工作树状态。只恢复某个路径：按表选择 restore/checkout 的路径形式。注释写明在 `/work/lab/repository-recovered` 副本中选择所需的一种操作。四条都跑过时，后一条会盖住前一条的状态，这次记录作废。

**2. 有冲突时先保存状态，不随手加 force。** 【仅在副本/仿真/授权环境执行】工作树有冲突时先保存状态，不随手加 force。detached HEAD 表示直接指向提交；在该状态创建新提交后，应建立引用，否则切走后可能失去分支入口。记录本次究竟改了哪个引用、索引和文件。`git checkout <commit>` 会动 HEAD 与工作树，通常还有索引。`git checkout <commit> -- <filename>` 只替换该路径的索引与工作树，不移动分支。`git restore --source=<commit> <filename>` 默认仅工作树，默认不更新索引。`git switch -c recovered <commit>` 从旧提交建立恢复分支并切换。

本节已核对这次实际执行的那一条命令，以及它改过的引用、索引或文件；detached HEAD 上的新提交还没有引用时，切走后可能失去分支入口。命令和表中“改变对象”一列一致，冲突和 force 没有混在同一次未记录的操作里，一并留存副本路径、执行前的 HEAD/索引/工作树，以及这次新建或移动的引用。

<span id="04-实战找回-reset-前的配置提交"></span>

## 04 实战：从 reflog 找回 reset 前的配置提交

现有分支比本地引用记录少一个配置提交。先从 reflog 取出候选，再验证并导出，最后只在独立副本里建恢复分支。

操作顺序：先从 reflog 取出候选，再验证并导出配置，对上恢复分支和原分析副本没有互相改写。


### 04.1 场景与材料

材料是包含 `.git/logs/` 与 `objects/` 的完整仓库保全目录 `/work/input/repository/`。现有分支比本地引用记录少一个配置提交，目标是恢复该配置并记录出处。分析副本为 `/work/copy/repository/`，恢复演练目录为 `/work/lab/repository-recovered/`。

操作顺序：先读 log、reflog 和 HEAD@{1}，再核对这条是不是 reset 前的位置，对上候选哈希。

下列输出为构造示例，不表示实际检材已跑通。

```bash
mkdir -p /work/output/git-recovery /work/lab
cd /work/copy/repository
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
git reflog --all --date=iso-strict
git rev-parse 'HEAD@{1}'
```

**1. 先读图和全部引用记录，再解析编号。** `git log --oneline --all --graph --decorate` 看现存引用。`git reflog --all --date=iso-strict` 看本地移动和时间。`git rev-parse 'HEAD@{1}'` 把当前编号解析成对象。编号随后会变，输出里要留下完整哈希。

**2. 确认这条是要查的 reset 前位置。** 根据示例，`HEAD@{1}` 指向候选 `9f24ac7`。实际应用时先比较引用记录，确认该条是要查的 reset 前位置，而不是仅按索引数字选最新条目。对不上操作说明时，换一条 reflog，不要用示例短哈希硬查。

本节已核对reflog 中 reset 前的那条记录，以及解析出的候选哈希；只凭 `HEAD@{1}` 这个编号、还没核对操作说明时，候选还不能用。引用记录里的操作说明和 `git rev-parse` 的完整哈希是同一条，一并留存log 图、reflog 原文和解析结果。

### 04.2 按候选哈希验证与导出

候选编号已经解析，还要确认它是 commit，并且 `app/config.yml` 能导出。先把完整哈希写入文件，再读类型和内容。

操作顺序：先保存候选并看类型，再导出配置和 blob，对上内容是历史配置，不是可用口令。

```bash
candidate=$(git rev-parse 'HEAD@{1}')
printf '%s\n' "$candidate" > /work/output/git-recovery/candidate.txt
git cat-file -t "$candidate"
git show --no-ext-diff --no-textconv --stat "$candidate"
git show --no-ext-diff --no-textconv --format=fuller "$candidate" -- app/config.yml
git rev-parse "$candidate:app/config.yml" > /work/output/git-recovery/blob.txt
git show --no-ext-diff --no-textconv "$candidate:app/config.yml" > /work/output/git-recovery/config-recovered.yml
sha256sum /work/output/git-recovery/config-recovered.yml
```

**1. 先确认提交类型，再读取提交树中的目标路径。** `candidate` 来自 `git rev-parse 'HEAD@{1}'`，写入 `candidate.txt`。`git cat-file -t` 看类型。`--stat` 和 `--format=fuller` 看这个提交改了哪些文件。`git rev-parse "$candidate:app/config.yml"` 把路径对应的 blob 写入 `blob.txt`。show 把文件内容写入 `config-recovered.yml`，再算 SHA-256。类型不是 commit、树中路径不存在或导出失败时，停下检查错误。stat 没有该路径只可能说明该提交未改动它，不代表文件不在提交树中。

**2. 导出成功只表示历史内容可读。** 若 `cat-file -t` 为 commit，提交树中 `app/config.yml` 可解析为 blob，且内容导出成功，则该候选可以用于读取这个历史文件。示例文件为三行训练配置，包括 `DB_HOST=db.internal`；这里只恢复历史内容，不使用其中的账号或网络地址。

本节已核对候选是 commit，提交树包含 `app/config.yml` 对应的 blob，成功导出的内容可算 SHA-256；还没在独立副本里建分支时，分析副本的 HEAD 应仍停在原处。`candidate.txt`、`blob.txt` 和 `config-recovered.yml` 来自同一次 `HEAD@{1}` 解析，一并留存候选哈希、blob 哈希、导出文件和 SHA-256。示例里的 `DB_HOST` 只留在导出文件中，不当成可用地址。

### 04.3 在独立副本建立恢复分支

配置已经导出，还要在另一份目录里重现该提交，同时证明原来的分析副本没有被移动。

操作顺序：先复制到演练目录，再建立 recovered 分支，对上两份配置一致且原 HEAD 没动。

【仅在副本/仿真/授权环境执行】`git switch -c` 会新建引用并移动这份演练副本的 HEAD、索引和工作树。不要在 `/work/copy/repository` 里执行。

```bash
cp -a /work/copy/repository /work/lab/repository-recovered
cd /work/lab/repository-recovered
candidate=$(cat /work/output/git-recovery/candidate.txt)
git switch -c recovered "$candidate"
git rev-parse HEAD
git --no-optional-locks status --porcelain=v1 --branch
sha256sum app/config.yml /work/output/git-recovery/config-recovered.yml
cmp app/config.yml /work/output/git-recovery/config-recovered.yml
```

**1. 在演练副本里建分支，再比较两份文件。** `cp -a` 把分析副本复制到 `/work/lab/repository-recovered`。`candidate` 读的是上一节的 `candidate.txt`。`git switch -c recovered` 从该提交建分支并切换。`git rev-parse HEAD` 应等于候选完整哈希。`status` 看切换后的工作树。`sha256sum` 和 `cmp` 比较工作树里的 `app/config.yml` 与先前导出的文件。`cmp` 有差异或 HEAD 不一致时，先核对候选文件，不要在分析副本上重做 switch。

**2. 回到分析副本，确认原 HEAD 没被演练移动。** HEAD 与候选完整哈希一致、路径存在、两份内容一致时，可记录“恢复分支重现了该提交中的配置”。再回到分析副本读取原 HEAD，与 `head-before.txt` 对比，确认原分析链未因恢复演练而移动。

**3. 按材料还在哪一层，选择下一种找法。** 若对象已经清理，reflog 留有哈希也无法凭空恢复内容；若没有 reflog，但候选仍被其他分支引用，可从 log 找到；若已不可达但仍在对象库，则进入 `fsck` 对象恢复。结论应区分“找到记录”“对象可读”“文件恢复并验证”三个阶段。命令边界可核对 [Git 官方 reflog 文档](https://git-scm.com/docs/git-reflog)、[reset 文档](https://git-scm.com/docs/git-reset)与 [restore 文档](https://git-scm.com/docs/git-restore)。

本节已核对恢复分支的 HEAD 等于候选，两份 `app/config.yml` 内容一致，分析副本的 HEAD 仍是 `head-before.txt`；对象已清理、没有 reflog，或提交已不可达时，分别改走 log 或 `fsck`，不要从哈希凭空恢复字节。`cmp` 无差异，并且演练前后的分析副本 HEAD 对比还在，一并留存演练目录、`recovered` 分支的 HEAD、两份文件的 SHA-256，以及三个阶段里已经完成的那一阶段。
