---
title: "Git 基础与仓库识别"
summary: "识别仓库、工作树、裸仓库和 Git 元数据的实际位置。"
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

手里是一份可能含版本库的目录副本，或从 Web 目录里看到的 `.git`。本页回答：它是不是仓库、元数据在不在这里、能不能支撑后续历史分析。原始材料保持只读，任何会改索引、引用或工作区的命令只在副本上做。

**先确认它是不是仓库 → 保全 `.git` 元数据并判断泄露范围 → 分清哪些 Git 操作会改现场 → 实战确认站点目录能读什么、还缺什么。**

先确认仓库元数据在哪里，再记录工作树、索引与引用的状态。目录中出现 `.git` 并不一定意味着它是普通目录；它也可能是指向其他位置的文本文件。以下命令默认在 Kali/Linux 的分析副本中执行，输出写入仓库外的 `/work/output/git-identify/`。

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

<span id="01-判断目录是否属于仓库"></span>

## 01 先确认它是不是仓库

目录里出现 `.git`，还不能判断它是普通仓库、关联工作树还是裸仓库。下面先做只读检查，再从深层目录定位真正的根。

操作顺序：先做首轮只读检查，再从深层目录定位根，对上工作树和元数据目录。


### 01.1 首轮只读检查

手里是分析副本 `/work/copy/repository`，还不知道当前目录是不是仓库、工作树根在哪。先跑只读检查，再按输出决定继续打开哪一块。

操作顺序：先建输出目录并进入副本，再读 rev-parse 和 status，对上普通仓库、关联工作树或裸仓库。

```bash
mkdir -p /work/output/git-identify
cd /work/copy/repository
ls -la
git --no-optional-locks status --porcelain=v1 --branch
git rev-parse --show-toplevel
git rev-parse --absolute-git-dir
git rev-parse --is-inside-work-tree
git rev-parse --is-bare-repository
```

**1. 先读工作树根和实际元数据目录。** `--show-toplevel` 给出普通工作树根目录；`--absolute-git-dir` 给出实际元数据目录。两项分别记录。`--is-inside-work-tree` 看当前是否在工作树里，`--is-bare-repository` 看是不是裸仓库。两项对不上时，先核对有没有进错目录。

**2. 再读当前分支、暂存区和工作区。** `git status` 查看当前分支、暂存区和工作区。`--no-optional-locks` 减少可选的索引刷新，不会让可写目录变成只读介质。本页 `--porcelain=v1` 的普通已跟踪文件使用 `XY`：第一位是索引相对 HEAD 的变化，第二位是工作树相对索引的变化。`??` 是未跟踪文件；忽略文件默认不显示。遇到合并冲突时，两位表示各合并头的状态，要按冲突状态表解释，不能继续套用普通文件的两层比较。

**3. 用下表决定下一步打开哪里。** 对不上“普通仓库”时，按继续检查一列往下查。裸仓库中 `git status` 报没有工作树，不代表对象数据库不可分析。反过来，当前目录没有 `.git` 也不证明没有仓库：Git 可能向父目录寻找，或由 `GIT_DIR`、`GIT_WORK_TREE` 指定位置。

<details>
<summary>展开首轮判读表</summary>

| 观察结果 | 判读 | 继续检查 |
| --- | --- | --- |
| `.git/` 是目录，inside-work-tree 为 true | 常见普通仓库布局 | 检查 `.git/HEAD`、`config`、`objects/`、`refs/` |
| `.git` 是包含 `gitdir: ...` 的文件 | 可能是关联工作树或子模块 | 解析目标路径，确认对应元数据也在保全范围内 |
| is-bare-repository 为 true | 裸仓库，通常没有普通工作树 | 使用 `git --git-dir=/路径/仓库.git ...` 读取引用和对象 |
| status 返回 not a git repository | 当前目录及向上搜索未找到可用元数据 | 检查是否进错目录、Git 环境变量、缺失文件或损坏布局 |

</details>

本节已核对工作树根、实际 Git 目录，以及这是普通仓库、关联工作树还是裸仓库；`status` 返回 not a git repository，或环境变量指向另一份仓库时，先不要继续读历史。`--show-toplevel`、`--absolute-git-dir`、`--is-inside-work-tree`、`--is-bare-repository` 和 `git status` 写在同一次检查里，一并留存 `/work/output/git-identify/` 下的目录清单，以及这次 status 和 rev-parse 输出。

### 01.2 从深层目录定位根目录

当前目录是 `/work/copy/repository/app/config`，还不知道仓库根是不是再往上。先从这里定位根目录，再看会话有没有被环境变量指到另一份仓库。

操作顺序：在深层目录跑 rev-parse，再看 GIT_ 环境变量，对上工作树根和实际 Git 目录。

```bash
cd /work/copy/repository/app/config
git rev-parse --show-toplevel
git rev-parse --absolute-git-dir
env | grep -E '^GIT_(DIR|WORK_TREE|COMMON_DIR|OBJECT_DIRECTORY|ALTERNATE_OBJECT_DIRECTORIES)='
```

**1. 读工作树根和元数据目录。** `--show-toplevel` 和 `--absolute-git-dir` 分别给出根和实际 Git 目录。示例输出为 `/work/copy/repository` 和 `/work/copy/repository/.git` 时，后续路径限定命令均以工作树根目录为基准。对不上这两个路径时，先不要用当前目录当仓库根。

**2. 核对会话是不是指到另一份仓库。** 最后一条列出 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_COMMON_DIR`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`。若环境变量指向 `/mnt/another-repo.git`，当前输出可能属于另一份仓库，需先校正会话归属。

本节已核对从深层目录定位到的工作树根和实际 Git 目录；环境变量指向 `/mnt/another-repo.git` 或其他仓库时，这次输出不能算当前副本的历史。两条 `git rev-parse` 的路径，和 `GIT_DIR`、`GIT_WORK_TREE` 等变量写在一起，一并留存工作树根、实际 Git 目录，以及这次会话里的 Git 环境变量。

<span id="02-git-元数据与泄露判断"></span>

## 02 保全 `.git` 元数据，判断泄露范围

网页目录里能看到 `.git`，还不知道引用、对象和外置目录齐不齐。先按位置把要保全的对象列全，再在副本里核对布局。

操作顺序：先保全引用和对象，再核对指针与外置目录，对上这份副本能不能继续读历史。


### 02.1 需要保全的对象

怀疑 Web 目录暴露了 Git 元数据，还不知道一个能打开的文件够不够重建历史。先按位置保全，再判断缺了哪一块就不能继续。

操作顺序：按表留下六类位置，再看 `.git/HEAD` 以外还缺什么，对上重建要依赖的引用和对象。

<details>
<summary>展开需保全的六类位置</summary>

| 位置 | 内容 | 可以回答的问题 |
| --- | --- | --- |
| `HEAD`、`refs/`、`packed-refs` | 当前指针、分支、标签 | 现存引用指向哪些提交 |
| `objects/` 与 pack 文件 | commit、tree、blob、tag 对象 | 哪些历史内容仍存在 |
| `logs/` | 本地引用移动记录 | 是否发生过 reset、切换或重写历史 |
| `index` | 暂存区条目 | 是否存在已暂存但未提交的内容 |
| `config` | 仓库配置、远程地址 | 仓库的本地配置与关联地址 |
| `.git` 文本指针、`commondir`、`objects/info/alternates` | 外置元数据或共享对象路径 | 当前副本是否依赖其他目录 |

</details>

**1. 按表把六类位置都留下。** `HEAD`、`refs/`、`packed-refs` 回答现存引用指向哪些提交。`objects/` 与 pack 文件保存 commit、tree、blob、tag。`logs/` 看是否发生过 reset、切换或重写历史。`index` 看是否存在已暂存但未提交的内容。`config` 看仓库的本地配置与关联地址。`.git` 文本指针、`commondir`、`objects/info/alternates` 看当前副本是否依赖其他目录。表中的路径对不上时，先记缺失，不要改到别的目录名。

**2. 一个能打开的 `.git/HEAD` 只说明这个文件可读。** Web 目录暴露 Git 元数据时，历史提交可能保留已从当前页面删除的配置、源码或凭据。完整重建还依赖引用、对象、pack、索引及可能的外置对象是否齐全。删除了网页文件，也不会自动删除仍被历史提交引用的 blob。

本节已核对现存引用、对象、引用日志、索引、配置，以及有没有外置元数据；只有 `.git/HEAD`、没有对象或 pack 时，还不能完整重建。表里每一类位置都有采集状态；缺的项单独标出，一并留存 `HEAD`、`refs/`、`packed-refs`、`objects/`、`logs/`、`index`、`config`，以及 `.git` 文本指针、`commondir`、`objects/info/alternates`。

### 02.2 在副本中检查布局

当前目录是 `/work/copy/repository`，还不知道 `.git` 是目录还是指向别处的文件。先看它的类型，再按相对路径把真正的元数据目录找出来。

操作顺序：先看 `.git` 是目录还是文件，再把状态写到仓库外，对上三个相对路径的起点。

```bash
cd /work/copy/repository
ls -ld .git
file .git
# 仅在 .git 是普通文件时读取文本指针
test -f .git && sed -n '1,5p' .git
git rev-parse --absolute-git-dir > /work/output/git-identify/git-dir.txt
git rev-parse HEAD > /work/output/git-identify/head.txt
git --no-optional-locks status --porcelain=v1 --branch > /work/output/git-identify/status.txt
git remote -v > /work/output/git-identify/remotes.txt
```

**1. 先看 `.git` 是目录还是普通文件。** `ls -ld .git` 和 `file .git` 区分这两种布局。注释写明：仅在 `.git` 是普通文件时读取文本指针，用 `test -f .git && sed -n '1,5p' .git`。它是目录时不要把 `sed` 的失败当成没有仓库。

**2. 把仓库状态写到副本外。** `git rev-parse --absolute-git-dir` 写入 `/work/output/git-identify/git-dir.txt`。`git rev-parse HEAD` 写入 `head.txt`。`git --no-optional-locks status --porcelain=v1 --branch` 写入 `status.txt`。`git remote -v` 写入 `remotes.txt`。某一条失败时保留退出状态，不要用空文件代替。

**3. 按三个相对路径的起点解析指针。** `gitdir:` 相对 `.git` 指针文件所在目录。`commondir` 相对实际 `$GIT_DIR`。`objects/info/alternates` 相对对象库，不是工作树或当前终端目录。逐项保存指针原文、解析路径和采集状态。指针指向副本之外时，先保全对应目录并维持相对关系。不要在缺失材料中运行 `git init`，这只会建立一个新仓库，不能补回原对象。

本节已核对 `.git` 的类型、实际 Git 目录、HEAD、status 和远程地址；指针指向副本之外、对应目录还没保全时，先补材料，不要 `git init`。指针原文、解析路径和三个相对起点写在同一份采集状态里，一并留存 `git-dir.txt`、`head.txt`、`status.txt`、`remotes.txt`，以及指针原文。

<span id="03-常规-git-操作及其取证影响"></span>

## 03 分清哪些 Git 操作会改现场

要分清哪些命令只在练习目录里演示，哪些会改仓库或对端。先看初始化、克隆和提交留下什么，再看远程配置和同步改哪一侧。

操作顺序：先看 init、add、commit 和 clone，再看 remote、pull、push，对上哪些变化属于分析操作。


### 03.1 初始化、克隆与提交

下面要看 `init`、`add`、`commit` 会新建什么，但不能拿练习目录代替原始材料。命令只在独立目录 `/work/lab/git-basics/` 中演示，不用于识别原始材料。

操作顺序：先在练习目录初始化并提交，再看 clone 留下什么，对上新对象是分析操作。

【仅在副本/仿真/授权环境执行】先保存目录清单、HEAD、索引和引用状态。`init` 新建元数据，`add` 把文件内容写入对象库并更新索引，`commit` 创建对象并更新引用/引用日志。练习后把新对象和新时间单独记为分析操作。

```bash
mkdir -p /work/lab/git-basics
cd /work/lab/git-basics
git init
printf 'sample configuration\n' > config.txt
git add config.txt
git -c user.name='Training User' -c user.email='training@example.invalid' commit -m 'add sample configuration'
git status
```

**1. 在练习目录里看 init、add、commit 各改什么。** `git init` 新建元数据。`printf` 只写示例文件 `config.txt`。`git add config.txt` 把文件内容写入对象库并更新索引。`git -c user.name=... -c user.email=... commit -m 'add sample configuration'` 创建对象并更新引用/引用日志；姓名和邮箱是这次练习传入的，不是历史身份。`git status` 看练习结束后的分支、暂存区和工作区。任一步失败时停在这一步，不要把半成品目录当成原始现场。

**2. 练习后把新对象和新时间单独记为分析操作。** 检查新建元数据、索引、提交对象和移动后的分支。`commit -m "message"` 的说明是练习输入，不是历史证据。这些操作的状态影响已在命令前列明，不能拿练习完成后的目录继续代表原始现场。

**3. 需要分析副本时再 clone，并记下它带不走什么。** 【仅在副本/仿真/授权环境执行】`git clone <url>` 或本地路径克隆适合取得分析或复现副本。

```bash
git clone /work/input/repository /work/lab/cloned-repository
```

普通克隆主要传输可达引用与对象，通常不保留原机的 reflog、未提交工作树、索引状态和全部不可达残留。要研究删除分支或本地修改，应先保全整个目录及外置元数据，不能以一次 clone 代替采集。clone 失败或目录比预期小，先核对源路径，不要在缺对象的目录里 `git init`。

本节已核对练习目录里新建的元数据、索引、提交对象，以及 clone 实际带过来的可达引用；普通 clone 里没有的 reflog、未提交工作树、索引状态和不可达残留，要回到完整目录副本。练习前后的目录清单、HEAD、索引和引用状态；clone 目标目录单独列出，一并留存 `/work/lab/git-basics/` 的练习记录，以及 `/work/lab/cloned-repository` 与源目录的差异说明。

### 03.2 远程配置与同步

本地配置里可能有远程地址，还不能把地址当成有人访问过那台服务器。先只读地址，同步命令放到训练副本里。

操作顺序：先读 fetch/push 地址，再在训练副本里看 pull 和 push，对上哪一侧会被改掉。

```bash
git remote -v
```

**1. 先读本地配置里的地址，不要把它当成访问证明。** `git remote -v` 读取本地配置中的 fetch/push 地址。地址是关联线索，不直接证明最近访问过该服务器或操作者身份。没有输出时，先看 `config` 里有没有 remote 段，不要改成“从未配置过远程”。

**2. 训练同步前先分清三条命令各改哪一侧。** 【仅在副本/仿真/授权环境执行】以下是训练仓库的配置与同步示例；先替换实际训练远程地址。配置远程地址会写本地 `config`。`fetch` 更新远程跟踪引用和对象；`pull` 还可能改变本地分支、索引和工作树。`push` 会影响对端引用。现场识别先保存当前配置和引用，不用同步后的结果替换采集时状态。

```bash
git remote add origin https://example.invalid/training/repository.git
git pull
git push
```

**3. 看完训练结果，回到采集时的配置。** `remote add origin <url>` 修改仓库配置；`pull` 获取并整合远程变化，可能移动引用、改工作树或产生合并；`push` 修改远程引用。执行结果会引入新证据或改变旧状态，现场分析应先固定现有引用与配置，复现需要时再使用训练副本。`pull` 或 `push` 失败时保留报错，不要用后来同步成功的引用覆盖采集时状态。

本节已核对采集时 `config` 里的 fetch/push 地址，以及训练副本里 remote、pull、push 各自改了哪一侧；只有地址、没有访问日志时，不写成有人最近访问过该服务器。`git remote -v` 的原始输出，和训练前后的引用、工作树差异分开保存，一并留存采集时的 `config` 和引用；训练远程地址、命令和同步后的新状态。

<span id="04-实战确认一份站点目录是否包含完整仓库"></span>

## 04 实战：确认站点目录能读什么、还缺什么

手里是一份站点目录，还不能确定它能不能支持后续历史分析。先看 `.git` 指针指到哪，再把关联元数据补齐并验证对象可读。

操作顺序：先看场景和指针，再固定状态并验证对象，对上能分析什么、还缺什么。


### 04.1 场景与材料

材料为只读保全目录 `/work/input/site-copy/`，内含 `app/`、`public/` 和 `.git` 文件，旁边有采集清单。目标是确定这份目录能否支持后续历史分析，但还不知道元数据在不在这份目录里。

操作顺序：先复制到工作副本，再看 `.git` 是不是文本指针，对上关联元数据的真实路径。

本文示例输出用于演示判读，不表示对任何实际材料已完成复跑。先把目录复制到 `/work/copy/site-copy/`。

```bash
mkdir -p /work/copy /work/output/git-identify
cp -a /work/input/site-copy /work/copy/site-copy
cd /work/copy/site-copy
ls -la
file .git
cat .git
```

示例结果：

```text
.git: ASCII text
gitdir: ../repository-metadata/worktrees/site
```

**1. 把只读材料复制到工作副本，再看 `.git`。** `cp -a` 保留属性和相对结构。`ls -la` 看目录里有什么，`file .git` 和 `cat .git` 看它是不是文本指针。复制失败或 `.git` 不是文件时，先停下来核对采集清单，不要在站点目录里新建仓库。

**2. 按示例指针去保全关联元数据。** 示例结果是 ASCII 文本，内容为 `gitdir: ../repository-metadata/worktrees/site`。这里的元数据目标是 `/work/copy/repository-metadata/worktrees/site`，而不是 `/work/copy/site-copy/.git/`。先对照采集清单，保全 `/work/input/repository-metadata/` 中的关联工作树目录、`commondir` 指向的公共目录和对象库；复制时保持它们之间的相对结构。实际指针和示例不一致时，以这次 `cat .git` 的原文为准。

本节已核对 `.git` 是文本指针，以及它相对站点目录指向的元数据路径；`/work/input/repository-metadata/` 里的工作树目录、`commondir` 或对象库还没进采集清单时，先补材料。`file .git`、指针原文，以及解析后的绝对路径和采集清单对得上，一并留存 `/work/copy/site-copy/` 的复制记录、`.git` 原文和采集清单。

### 04.2 固定仓库状态并验证对象可读

关联元数据还在 `/work/input/repository-metadata/`，站点副本还不能直接读对象。先把元数据按原相对结构复制过来，再验证 HEAD 和对象。

操作顺序：先复制元数据，再读 HEAD、status 和 fsck，对上工作树、未提交修改和缺失对象。

```bash
cp -a /work/input/repository-metadata /work/copy/repository-metadata
cd /work/copy/site-copy
git rev-parse --show-toplevel
git rev-parse --absolute-git-dir
git rev-parse --is-bare-repository
git --no-optional-locks status --porcelain=v1 --branch
git rev-parse HEAD
git cat-file -t HEAD
git fsck --full
```

**1. 先确认这是带工作树的仓库，并且 HEAD 能读。** `cp -a` 把 `/work/input/repository-metadata` 复制到 `/work/copy/repository-metadata`，保持和站点副本的相对关系。`--show-toplevel`、`--absolute-git-dir` 记下根和实际 Git 目录。这组命令中，`--show-toplevel` 成功返回工作树根、`--is-bare-repository` 为 false，支持当前目录属于非裸仓库；inside-work-tree 字段需要执行前面介绍的对应查询后才会出现。对不上时先回到 `.git` 指针，不要在站点目录里另找一个 `.git/`。

**2. 再看未提交修改和对象缺不缺。** `git --no-optional-locks status --porcelain=v1 --branch` 看当前分支和未提交变化。`git rev-parse HEAD` 给出当前提交，`git cat-file -t HEAD` 返回 `commit` 时当前 HEAD 对象可读取。`status` 出现 ` M app/config.yml`：现存文件有未暂存修改；不能只查 HEAD 而忽略当前配置。`git fsck --full` 出现 `missing blob`：记录缺失哈希和引用它的 tree。当前材料还不能完整恢复该文件。检查失败不是“没有残留”。

本节已核对带工作树的仓库、可读的 HEAD，以及 `app/config.yml` 上的未暂存修改或缺失 blob；`missing blob` 还在时，对应文件还不能完整恢复。工作树根、is-bare-repository、`cat-file -t HEAD`、status 和 `fsck` 来自同一次检查；inside-work-tree 只在补做对应查询时记录，一并留存元数据副本路径、HEAD、status、`fsck` 里的缺失哈希和引用它的 tree。

### 04.3 输出与结论边界

对象已经能读一部分，还要把“支持哪些分析、缺哪些依赖”写清楚。先列结果清单，再算哈希，不要把连通性检查写成从未删过对象。

操作顺序：先列结果清单，再算 SHA-256，对上能分析的范围和缺的依赖。

**1. 结果清单先写全这些项。** 至少包括：工作树绝对路径、实际 Git 目录、公共对象目录、HEAD、裸仓库判断、未提交变化、远程地址、缺失对象和采集时间。缺一项就留空，不要用另一份仓库的路径填上。

**2. 再对采集清单和关键元数据算 SHA-256。** 对采集清单、`.git` 指针文件及关键元数据计算 SHA-256，并与保全记录核对。哈希对不上时，先核对复制过程，不要继续把这份副本当原始材料。

**3. 结论写成当前副本支持什么、缺少什么。** 完整引用和通过连通性检查只能说明现有对象可读取，不能证明从未删过对象；没有 reflog 可能是未采集、过期或普通克隆造成。识别结论应写成“当前副本支持哪些分析、缺少哪些依赖”，之后再进入提交历史与对象恢复。Git CLI 语义可核对 [Git 官方 rev-parse 文档](https://git-scm.com/docs/git-rev-parse)与 [Git 官方 repository layout 文档](https://git-scm.com/docs/gitrepository-layout)。

本节已核对当前副本支持哪些分析，以及 SHA-256 与保全记录一致的那些元数据；缺失对象、没有 reflog，或公共对象目录不在这份材料里。结果清单里的路径、HEAD、裸仓库判断和缺失对象，能对上前面的命令输出，一并留存工作树绝对路径、实际 Git 目录、公共对象目录、采集清单和 SHA-256。
