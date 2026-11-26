手里是一份已经确认可分析的 Git 仓库副本，需要从提交历史中找出被修改或删除的配置与代码。原始材料保持只读，查询命令均加上禁用外部 diff 与过滤器的安全参数。

**先画全引用提交图并记下作者与时间 → 按路径查历史补丁并用 show 只读导出 → 分清三层 diff 比较范围 → 搜索历史补丁与提交树中的敏感词 → 实战找回已删除的配置版本。**

先画提交图，再围绕可疑路径和内容读取历史。提交时间、作者姓名和提交说明都可以由提交者设置；它们提供时间线线索，需要与部署日志、文件记录和仓库其他证据对应。

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

<span id="01-提交记录与全局视图"></span>

## 01 先画提交图，再记下作者与提交时间

当前分支的最后一版不一定是要找的配置。先把现存引用画成提交图，再把作者、提交者和时间分开记。

操作顺序：先从当前分支扩到全部现存引用，再记下作者、提交者和时间，对上该看哪一条历史。


### 01.1 从当前分支扩展到所有现存引用

手里是分析副本 `/work/copy/repository`，还不知道当前分支以外还有没有备份历史。先画提交图，再决定要读哪一个提交。

操作顺序：先沿当前父链读 log，再加 --all 和图形，对上 main 以外仍指向旧配置的引用。

```bash
cd /work/copy/repository
git log --no-ext-diff --no-textconv
git log --no-ext-diff --no-textconv --oneline
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate
```

**1. 先分清这三条 log 各看到哪一段。** `git log --no-ext-diff --no-textconv` 默认沿当前提交的父链读取；`--oneline` 缩为短哈希与说明；`--all` 将现存引用作为起点，`--graph --decorate` 展示分支关系及引用名称。它不是“磁盘里全部历史”，不会自动覆盖已失去引用且不在所选起点内的提交。只有当前分支、没有 `--all` 时，先不要写成仓库里只剩这一条历史。

```text
* 9f24ac7 (HEAD -> main) remove temporary configuration
| * 2b16d0e (backup) keep deployment settings
|/
* 6a03c11 add application configuration
```

**2. 按构造图把两条历史分开读。** 这组构造输出中，提交说明提示 main 可能删除了配置，backup 则指向另一条历史。提交图只给引用与父子关系，删除事实还要检查该提交的补丁和父代文件。应分别读取候选提交的内容，不应只从 main 的最后一版寻找。短哈希只用来对照这张示例图，实际操作改用自己的完整哈希。

本节已核对当前分支的父链，以及 `--all` 还能看到的现存引用，例如示例里的 main 和 backup；已经失去引用、又不在所选起点里的提交，这张图不会自动出现。`--oneline --all --graph --decorate` 里的引用名和父子关系，能对上后面要读的提交，一并留存三条 `git log` 的原始输出，以及图上每个引用的完整哈希。

### 01.2 记录作者、提交者与时间

提交图已经有了，还不能把作者时间当成事件时间。先把提交里的四类身份和时间记全，再和仓库外的日志对照。

操作顺序：先导出作者和提交者字段，再分四列时间，对上哪些字段只能当线索。

```bash
git log --no-ext-diff --no-textconv --all --format='%H %P | author=%an <%ae> %aI | committer=%cn <%ce> %cI | %s'
```

**1. 先把作者、提交者、时间和父哈希导出成一行。** `--format` 里 `%H` 是完整提交哈希，`%P` 是父哈希，`%an`、`%ae`、`%aI` 是作者姓名、邮箱和严格时间，`%cn`、`%ce`、`%cI` 是提交者姓名、邮箱和严格时间，`%s` 是说明。字段空或时间没有时区时，先标出来，不要自己补。

**2. 时间线分四列记录。** commit 时间、reflog 引用变动时间、工作树文件时间、外部日志时间。每列先保留原值和时区，再统一时间比较。对不上时先停止排序，不要只按屏幕上的时分秒排。

**3. 姓名和时间只当线索，再去对部署和认证日志。** 作者时间与提交者时间不是一回事：rebase 或补丁导入可能保留前者而改变后者。姓名、邮箱、日期也可由 Git 配置或环境变量填写，不等于 Linux 账户或 SSH 登录身份。记录完整提交哈希和父哈希，再与部署、认证日志核对。提交说明里的“remove secret”“debug backup”只帮助挑选检查对象，不直接证明泄露或入侵。

本节已核对每个提交的完整哈希、父哈希、作者、提交者和两侧时间；还没和部署日志、认证日志对照时，不把作者写成登录的人。`--format` 那一行里的 `%H`、`%P`、`%aI`、`%cI` 和说明还在，一并留存这份格式化 log，以及四列时间各自的原值和时区。

<span id="02-按文件与补丁缩小范围"></span>

## 02 按路径查历史补丁并只读导出旧文件

可疑配置的路径已经有了，还不知道它在哪一次提交里改过或删过。先看历史补丁，再对候选提交用 `show` 读内容和导出文件。

操作顺序：先按路径看补丁，再用 show 读候选提交，对上删除前的文件在哪个父提交。


### 02.1 查看历史补丁

要追 `app/config.yml` 的历史，还不知道该看当前分支还是全部引用。先出补丁，再处理改名和合并提交。

操作顺序：先看当前可达补丁，再限定路径和 --all，对上改名和合并有没有被默认补丁漏掉。

```bash
git log --no-ext-diff --no-textconv -p
git log --no-ext-diff --no-textconv -p --all
git log --no-ext-diff --no-textconv -- app/config.yml
git log --no-ext-diff --no-textconv -p -- app/config.yml
```

**1. 先看当前可达补丁，再扩到全部现存引用。** `git log --no-ext-diff --no-textconv -p` 查看当前可达补丁；`-p --all` 扩展到现存全部引用。路径前的 `--` 分开参数和文件名。`git log --no-ext-diff --no-textconv -- app/config.yml` 只列碰到这个路径的提交，加上 `-p` 才看补丁。没有补丁时，先确认路径是不是写错，或文件只存在于未加 `--all` 的另一条引用。

**2. 文件改名时先看补丁里的旧路径。** 必要时对单个路径用 `git log --no-ext-diff --no-textconv --follow -- app/config.yml`。它不保证自动处理全部复制、拆分和复杂合并。`--follow` 没有带出旧路径时，回到补丁里的 rename 行继续查。

**3. 候选是 merge 时先记下每个父哈希。** 默认 `-p` 不会逐个列出相对所有父提交的变化，应分别用两个明确提交做 show/diff 比较。补丁列表没显示，不代表合并没改文件。

本节已核对 `app/config.yml` 在现存引用里的补丁，以及改名后的旧路径；合并提交的默认 `-p` 没列出的父代差异，要另做 show/diff。路径前有 `--`，并且 `--all` 或当前分支的范围已经写明，一并留存补丁原文、旧路径，以及合并提交的父哈希。

### 02.2 对候选提交使用 `show`

补丁已经指出候选 `9f24ac7`，还不能直接切换工作树去看文件。先用 `show` 读提交和指定路径，导出成功后再算哈希。

操作顺序：先看提交和 --stat，再读提交树里的文件，核对导出状态、对象类型和内容。

```bash
git show --no-ext-diff --no-textconv 9f24ac7
git show --no-ext-diff --no-textconv --stat 9f24ac7
git show --no-ext-diff --no-textconv 9f24ac7:app/config.yml
git show --no-ext-diff --no-textconv HEAD~1:app/config.yml
```

**1. 先读提交信息和涉及的文件，不切换工作树。** `show <commit>` 输出提交信息与补丁；`--stat` 先看涉及哪些文件；`<commit>:<filename>` 读取该提交树里的文件内容，不切换工作树。若文件在该提交中已删除，读取会失败，应读取删除提交的父代。`HEAD~1` 沿第一父链走一步；合并提交要结合父哈希判断是否应使用 `^1` 或 `^2`。读失败时看标准错误，不要改用 checkout。

```bash
git show --no-ext-diff --no-textconv HEAD~1:app/config.yml > /work/output/config-before.yml
sha256sum /work/output/config-before.yml
```

**2. 导出后先检查是否成功，再算哈希。** 检查 Git 退出状态和标准错误。Shell 的 `>` 可能先创建或截断文件，然后 Git 才报对象不存在。核对对象类型、长度和导出内容，避免把空文件当成已恢复配置。记录提交哈希、仓库内路径、导出路径和 SHA-256。导出文件创建时间是本次分析时间，不是历史修改时间。文件存在、能算出 SHA-256，只能证明输出文件存在，不能证明导出成功。

本节已核对候选提交的补丁或 `--stat`，以及从父代导出的文件内容和 SHA-256；`<commit>:<filename>` 失败时，先查路径、对象和错误信息；确认该提交删除了文件后再读父代。空文件也可能是有效历史内容，须区分成功导出的空 blob 与失败重定向留下的空文件。Git 退出状态、标准错误、对象类型和长度都已核对，不只是输出文件存在，一并留存提交哈希、仓库内路径、`/work/output/config-before.yml` 和它的 SHA-256。

<span id="03-diff-比较的三个层次"></span>

## 03 分清工作区、暂存区与提交之间的 `diff`

工作树、暂存区和两个提交都可能有差异，还不知道这次 `diff` 比的是哪一层。先按命令选左右两侧，再看正负号是不是被比较方向反过来了。

操作顺序：先分清未暂存、已暂存和两个提交，再限定路径，对上补丁方向和事件时运行的版本。

```bash
git diff --no-ext-diff --no-textconv
git diff --no-ext-diff --no-textconv --cached
git diff --no-ext-diff --no-textconv 6a03c11 9f24ac7
git diff --no-ext-diff --no-textconv 6a03c11 9f24ac7 -- app/config.yml
```

<details>
<summary>展开 diff 三层比较速查表</summary>

| 命令 | 左侧与右侧 | 可回答的问题 |
| --- | --- | --- |
| `git diff --no-ext-diff --no-textconv` | 索引 → 工作树 | 哪些改动尚未暂存 |
| `git diff --no-ext-diff --no-textconv --cached` | HEAD → 索引 | 哪些改动已暂存但尚未提交 |
| `git diff --no-ext-diff --no-textconv <commit1> <commit2>` | 第一个提交树 → 第二个提交树 | 两个版本之间有什么内容变化 |
| 上一条加 `-- <filename>` | 指定路径的版本差异 | 可疑配置、代码或文件如何变化 |

</details>

**1. 先按表确认这条 diff 的左侧和右侧。** 不带提交的 `git diff --no-ext-diff --no-textconv` 是索引到工作树，回答哪些改动尚未暂存。`--cached` 是 HEAD 到索引，回答哪些改动已暂存但尚未提交。两个提交是第一个提交树到第二个提交树。后面加 `-- app/config.yml` 只看这个路径。输出为空时，先核对是不是比错了层次，不要写成文件没有变化。

**2. 再看正负号属于哪一个比较方向。** 补丁中的 `-` 与 `+` 是相对所选比较方向的删除和增加；将两个提交倒置，正负号也会倒置。比较结果不直接回答哪个版本在事件时运行，需要关联部署和镜像证据。

本节已核对这次比较的左右两侧，以及指定路径上的增删；还没关联部署和镜像时，不写成事件当时跑的就是其中一版。命令和表里的“左侧与右侧”一致，路径限制写在 `--` 后面，一并留存四条 diff 的原始补丁，以及比较用的两个提交哈希。

<span id="04-历史敏感内容搜索"></span>

## 04 在历史补丁与提交树中搜索敏感内容

补丁里可能有口令或标志一类字符串，还不知道该用关键词、`-S` 还是 `-G`。先初筛，再按字符串次数和正则分开搜，最后到可达历史树上核对。

操作顺序：先做关键词初筛，再区分 -S 和 -G，对上可达历史树里的命中、无匹配和读取错误。


### 04.1 关键词初筛

可达补丁已经能导出，还不能把 `grep` 的一行当成结论。先按关键词缩小范围，再回到提交里核对。

操作顺序：先在全部现存引用的补丁里筛词，再记下哈希和路径，对上 show 里的上下文。

```bash
git log --no-ext-diff --no-textconv -p --all | grep -i flag
git log --no-ext-diff --no-textconv -p --all | grep -i password
git log --no-ext-diff --no-textconv -p --all | grep -Ei 'flag|password|passwd|secret|token|key'
```

**1. 三条 grep 只负责缩小候选。** 前两条分别用 `-i flag` 和 `-i password`。第三条用 `-Ei`，模式是 `flag|password|passwd|secret|token|key`。没有命中时，先确认补丁范围是不是 `--all`，不要写成内容从未出现。

**2. 命中后回到提交里核对，不把一行值抄成结论。** 记录附近的提交哈希、路径和补丁上下文，再用 `git show --no-ext-diff --no-textconv` 精确核对。`key` 也可能是普通字段；删除行只能证明在该次比较中被移除，不能证明旧值有效、曾被使用或已从所有分支消失。文本筛查无法覆盖所有二进制、编码、加密内容，也不覆盖不可达对象。

本节已核对关键词附近的提交哈希、路径和补丁上下文；二进制、编码、加密内容和不可达对象，文本筛查覆盖不到。同一处再用 `git show --no-ext-diff --no-textconv` 对过，不只是 grep 的一行，一并留存grep 命中行、对应提交和随后的 show 输出。

### 04.2 `-S` 与 `-G` 的区别

关键词搜得到变量名，还分不清是出现次数变了，还是只改了值。`-S` 和 `-G` 各答一个问题，不要当成同一种搜索。

操作顺序：先用 -S 看出现次数，再用 -G 看补丁行，对上只改变量值时谁会漏。

```bash
git log --no-ext-diff --no-textconv -S'DB_PASSWORD' --all -p
git log --no-ext-diff --no-textconv -G'DB_(PASSWORD|HOST)' --all -p
```

**1. 按要回答的问题选 -S 或 -G。** `-S'<text>'` 寻找该字符串出现次数发生变化的提交；`-G'<regex>'` 寻找补丁增加/删除行匹配正则的提交。两条都加了 `--all -p`。一条有输出、另一条没有时，先看是不是次数没变，不要把没输出写成没改过。

**2. 用改值这个例子核对有没有漏。** 把 `DB_PASSWORD=old-value` 改为 `DB_PASSWORD=new-value`，变量名出现次数仍为一次，`-S'DB_PASSWORD'` 可能不命中，而 `-G'DB_PASSWORD'` 可命中修改行。应按问题选择，而不是把两者当作同一搜索。`-G'DB_(PASSWORD|HOST)'` 同时覆盖口令和主机字段。

本节已核对字符串出现次数变化的提交，或补丁行匹配正则的提交；只把 `DB_PASSWORD` 从旧值改成新值时，`-S'DB_PASSWORD'` 可能没有这条提交。选用的是 `-S` 还是 `-G`，以及示例里次数不变时 `-G` 仍能命中修改行，一并留存两条 log 的补丁，和当时要找的是次数变化还是修改行。

### 04.3 搜索可达历史树的内容

补丁搜索还没覆盖每个历史树里的文件内容。先用 `git grep` 在可达提交上找，参数太长时再逐个提交，并把读取错误单独留下。

操作顺序：先一次 grep 全部可达提交，参数太长就逐个提交，对上命中、无匹配和读取错误。

```bash
git grep -n 'DB_PASSWORD' $(git rev-list --all)
```

**1. 先看一次展开全部可达提交的 grep。** 这是 `git grep -n '<text>' $(git rev-list --all)` 的实例，每条命中包含提交、路径和行号。命令因参数太长失败时，不要把失败当成没有命中，改用下一步逐个提交。

```bash
git rev-list --all > /work/output/reachable-commits.txt
while IFS= read -r commit; do
  git grep -n -F 'DB_PASSWORD' "$commit" -- app/ || true
done < /work/output/reachable-commits.txt > /work/output/history-hits.txt
```

**2. 遍历结果分三类记录：命中、无匹配、读取错误。** 大仓库可能超过命令行参数限制，宜逐个提交执行，并保留报错。`git rev-list --all` 先写入 `/work/output/reachable-commits.txt`。循环里 `git grep -n -F 'DB_PASSWORD' "$commit" -- app/` 只在 `app/` 下做固定字符串搜索。示例中的 `|| true` 让循环继续，但也会吞掉对象缺失或参数错误，不只是“没搜到”。保存每次 Git 的原退出状态与标准错误。整个循环最后返回成功，不代表每个历史树都成功检查。

本节已核对可达提交里 `DB_PASSWORD` 的提交、路径和行号；被 `|| true` 吞掉的对象缺失或参数错误，以及不可达对象。每个提交的原退出状态和标准错误还在，不能只看循环最后一次成功，一并留存 `reachable-commits.txt`、`history-hits.txt`，以及每次失败的标准错误。

<span id="05-实战定位当前目录已删除的配置版本"></span>

## 05 实战：找回当前目录已删除的配置版本

当前目录里已经没有配置文件，还要确定是哪一次提交删的、旧内容在哪个对象里。先从补丁找到候选和父代，再用 blob 交叉确认，并记下其他引用是否还留着同一路径。

操作顺序：先从补丁定位删除提交，再导出父代并交叉确认，对上主分支删除和其他引用仍保留。


### 05.1 场景与材料

材料为 `/work/input/repository/` 的完整保全副本，当前 `app/` 中没有 `config.yml`。目标是确定它在哪次提交中删除、旧内容在哪个对象中。分析副本位于 `/work/copy/repository/`，输出位于 `/work/output/git-history/`。

操作顺序：先固定 status 和提交图，再导出父代文件和删除补丁，对上 blob 属于父提交的这个路径。

下面哈希和输出为构造示例，实际操作应从自己的结果取候选值。

```bash
mkdir -p /work/output/git-history
cd /work/copy/repository
git --no-optional-locks status --porcelain=v1 --branch > /work/output/git-history/status.txt
git log --no-ext-diff --no-textconv --oneline --all --graph --decorate > /work/output/git-history/graph.txt
git log --no-ext-diff --no-textconv --all --format='%H %P %aI %cI %s' -- app/config.yml
git log --no-ext-diff --no-textconv -p --all -- app/config.yml
```

**1. 先把现状和这个路径的历史补丁存到仓库外。** `status.txt` 是当前分支和未提交变化，`graph.txt` 是现存引用的图。后面两条只看 `app/config.yml`：一条是哈希、父哈希和两侧时间，一条是补丁。文件不存在于当前工作树时，这组 log 仍然可以有历史；没有输出时，再查是不是路径不同或只在不可达对象里。

```bash
candidate=9f24ac7
git show --no-ext-diff --no-textconv --stat "$candidate"
git show --no-ext-diff --no-textconv --format=fuller "$candidate" -- app/config.yml
git show --no-ext-diff --no-textconv "$candidate^1:app/config.yml" > /work/output/git-history/config-before.yml
git rev-parse "$candidate^1:app/config.yml" > /work/output/git-history/config-blob.txt
git diff --no-ext-diff --no-textconv "$candidate^1" "$candidate" -- app/config.yml > /work/output/git-history/deletion.patch
sha256sum /work/output/git-history/config-before.yml /work/output/git-history/deletion.patch
```

**2. 记录完整哈希后，读父代文件和删除补丁。** 示例补丁表明 `9f24ac7` 删除 `app/config.yml`，父提交为 `6a03c11`。`candidate` 先放短哈希，实际操作换成自己的完整哈希。`--stat` 和 `--format=fuller` 看这次删除涉及的文件和完整说明。`$candidate^1:app/config.yml` 读第一父提交里的文件，不切换工作树。`git rev-parse` 把该路径的 blob 哈希写入 `config-blob.txt`。diff 把父代到删除提交的补丁写入 `deletion.patch`。`sha256sum` 核对导出文件。父路径读失败时，先核对是不是合并提交该用别的父代。

**3. 示例字段只说明历史内容在父提交里，不说明当时的口令。** 示例旧配置出现 `DB_HOST=db.internal` 和 `DB_PASSWORD=training-value`，这些是演示字段，不是有效凭据。判读是“该 blob 在父提交的该路径中存在，并在选定提交中删除”，而非“已确认事件时的数据库密码”。

本节已核对删除提交、它的父提交，以及父提交里 `app/config.yml` 的 blob；还没做第二次对象读取时，导出文件还不能单独当恢复成功。`config-blob.txt`、`config-before.yml` 和 `deletion.patch` 来自同一个候选和 `^1`，一并留存 `status.txt`、`graph.txt`、父代导出、删除补丁和两份 SHA-256。

### 05.2 二次验证与限制

父代文件已经导出，还要用同一个 blob 再读一次，并看别的引用是否还留着这个路径。对不上就不要写成已经从所有历史里删除。

操作顺序：再用 cat-file 读同一 blob，和第一次导出比较，对上主分支删除和其他引用仍保留。

```bash
blob=$(cat /work/output/git-history/config-blob.txt)
git cat-file -t "$blob"
git cat-file -p "$blob" > /work/output/git-history/config-from-blob.yml
cmp /work/output/git-history/config-before.yml /work/output/git-history/config-from-blob.yml
git log --no-ext-diff --no-textconv -G'DB_PASSWORD' --all -p -- app/
```

**1. 用对象类型和第二次导出交叉确认。** `blob` 来自上一节写下的 `config-blob.txt`。`git cat-file -t` 应为 blob。`git cat-file -p` 写入 `config-from-blob.yml`。`cmp` 比较它和 `config-before.yml`。`git log --no-ext-diff --no-textconv -G'DB_PASSWORD' --all -p -- app/` 再看这个路径上的修改行。类型不是 blob、`cmp` 不一致，或补丁没有显示删除时，先不要写恢复链已经确认。

**2. 主分支删除和其他引用保留要分开写。** 若对象类型为 blob，两次导出内容一致，并且补丁明确显示该路径删除，恢复链得到交叉确认。继续检查 backup 等引用时，发现同一路径仍存在，应将“主分支删除”和“其他引用保留”分别记录。

**3. 写上这次搜索覆盖不到的部分。** 现存引用不足以覆盖全部历史；缺失对象、浅克隆、历史重写和本地未提交状态都会影响结果。没有搜索命中不等于从未存在敏感信息。后续需要时转向 reflog 与 `fsck`，保留当前搜索范围和局限。命令语义可核对 [Git 官方 log 文档](https://git-scm.com/docs/git-log)、[show 文档](https://git-scm.com/docs/git-show)与 [diff 文档](https://git-scm.com/docs/git-diff)。

本节已核对blob 类型、两份导出一致，以及补丁里的路径删除；backup 等引用仍保留同一路径、缺失对象、浅克隆、历史重写或未提交状态。`cmp` 没有差异，并且 `-G` 补丁和删除方向一致，一并留存 `config-from-blob.yml`、比较结果、搜索范围，以及还没覆盖的 reflog/`fsck` 缺口。
