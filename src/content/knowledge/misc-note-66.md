---
title: "git隐藏"
summary: "Git隐藏题的核心逻辑： 当前工作区可见的文件≠Git仓库的全部内容。"
module: "Misc"
topic: "文档与取证"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心原理与基础概念

### 1.考点本质

**Git隐藏题的核心逻辑：** 当前工作区可见的文件≠Git仓库的全部内容。所有版本历史、临时保存的修改、被删除的提交、未跟踪的文件都可能保存在.git目录中。题目通常将flag放在当前工作区不可见的位置，需要通过Git版本管理机制恢复。

### 2..git目录核心结构

.git是Git仓库的核心数据库目录，默认以.开头隐藏，保存了仓库的全部状态：

**objects/：** Git对象数据库，存储所有文件内容、目录结构、提交记录

**refs/：** 存储分支、标签、stash等引用指针

**HEAD：** 记录当前工作区指向的分支/提交

**logs/：** 操作日志，对应reflog数据

**index：** 暂存区索引文件

### 3.Git三大基础对象

所有内容都以对象形式存在于objects目录中，是数据恢复的底层基础：

| 对象类型 | 作用 |
| --- | --- |
| blob（块对象） | 存储单个文件的具体内容，不保存文件名 |
| tree（树对象） | 存储目录结构，记录文件名、权限与对应blob的映射关系 |
| commit（提交对象） | 存储提交信息，包含对应tree、父提交、作者、提交说明 |

**层级关系：** commit→tree→文件名→blob→文件内容

## 二、核心考点与对应命令详解

**考点1：** 提交历史中的隐藏数据（旧commit恢复）

概念

每次git commit都会生成一个提交对象，保存当时整个工作目录的完整快照。题目通常会在旧版本中写入flag，再在后续提交中删除、覆盖文件，导致当前工作区无法直接看到。

核心命令

### 1.查看提交历史

#查看当前分支完整提交历史

git log

#精简单行显示，快速浏览提交记录

git log--oneline

#查看全部分支的提交历史，带分支拓扑图

git log--all--oneline--decorate--graph

**作用：** 梳理提交时间线，定位「添加flag、删除flag」的关键提交。

**考点：** 重点关注提交说明包含add、remove、delete、secret、flag等关键词的提交。

### 2.查看指定提交的详情

#查看提交的完整信息与代码差异

git show<提交哈希>

#仅查看提交修改的文件列表

git show--stat<提交哈希>

**示例：** git show 83ee219查看哈希为83ee219的提交修改了什么内容。

### 3.直接读取旧版本的指定文件（最常用）

git show<提交哈希>:<文件路径>

**作用：** 无需切换分支、无需回滚版本，直接读取某次提交中指定文件的完整内容，不改变当前工作区状态。

**示例：** git show 83ee219:secret.py读取旧提交里的secret.py文件。

**保存到本地：** git show 83ee219:secret.py>recovered.py

### 4.对比两个版本的差异

git diff<旧提交哈希><新提交哈希>

**作用：** 快速定位两个版本间哪些文件被修改、删除。

### 5.恢复被删除的文件到工作区

#从指定提交恢复单个文件

git restore--source=<提交哈希>--<文件名>

#旧版Git兼容写法

git checkout<提交哈希>--<文件名>

**考点2：** Git Stash临时隐藏

概念

git stash用于临时保存未提交的工作区/暂存区修改，执行后工作区会恢复到干净状态，修改内容被保存在.git中，不会出现在提交历史里，隐蔽性强，是CTF最高频的Git隐藏考点。题目通常将flag写入文件后执行stash隐藏修改，工作区文件恢复为无flag的状态。

核心命令

### 1.查看所有stash记录

git stash list

**输出格式：** stash@{0}:WIP on master:xxx

stash@{0}代表最新的临时保存，数字越大时间越早；有多个stash时需全部检查。

### 2.查看stash的具体修改内容

#仅查看修改的文件列表

git stash show stash@{n}

#查看完整的代码差异

git stash show-p stash@{n}

-p=patch，显示具体的增删行内容，无需恢复即可直接读取隐藏的flag。

**示例：** git stash show-p stash@{0}查看最新stash的全部修改。

### 3.直接读取stash中的指定文件

git show stash@{n}:<文件路径>

**作用：** 不应用stash、不修改工作区，直接读取stash里某个文件的完整内容，是取证分析的最优方式。

**示例：** git show stash@{0}:flag.txt

### 4.恢复stash到工作区

#应用stash修改，保留stash记录（推荐，不破坏原始数据）

git stash apply stash@{n}

#应用stash修改，成功后删除该stash记录

git stash pop stash@{n}

**区别：** apply只恢复不删除，可重复查看；pop恢复后删除记录。CTF取证优先用apply，避免误删原始数据。

**进阶考点：** 未跟踪文件隐藏

普通git stash不会保存从未被git跟踪过的新文件；若使用git stash-u（--include-untracked），可以将未跟踪的新文件一起隐藏。这类题目中，工作区完全看不到目标文件，提交历史里也没有记录，只能通过stash恢复。

**考点3：** Reflog找回被删除的提交

概念

reflog（引用日志）记录了HEAD指针的所有移动历史，包括提交、切换分支、reset回退、rebase等所有操作。即使通过git reset--hard删除了提交，git log中看不到该记录，只要对象未被垃圾回收，git reflog中仍能找到对应的提交哈希，是找回「被彻底删除的提交」的核心方法。

核心命令

### 1.查看完整操作日志

git reflog

**输出格式：** 哈希值HEAD@{序号}:操作:说明

可以看到所有历史操作，包括被回退掉的提交。

### 2.找回并查看被删提交

找到目标提交的哈希后，直接用git show查看内容：

git show<提交哈希>

文件恢复方法与普通提交完全一致。

**考点4：** 多分支隐藏

概念

Flag可能不保存在当前检出的分支（main/master）中，而是藏在其他未显示的分支里，比如dev、secret、flag等命名的分支。

核心命令

### 1.查看所有分支

#仅查看本地分支

git branch

#查看所有分支（本地+远程）

git branch-a

### 2.查看指定分支的提交历史

git log<分支名>--oneline

### 3.直接读取其他分支的文件

git show<分支名>:<文件路径>

**示例：** git show dev:flag.txt读取dev分支里的flag.txt

**考点5：** 悬空对象恢复（dangling object）

概念

没有被任何分支、标签、stash、提交引用的Git对象，称为悬空对象。通常是被删除的文件、被回滚的提交，只要还没被git gc垃圾回收，就仍然存在于objects目录中。这类题目没有任何引用指向目标数据，需要通过扫描对象库来发现。

核心命令

### 1.扫描仓库，查找悬空对象

#完整检查仓库，列出所有悬空对象

git fsck--full

#以丢失文件模式扫描，结果更直观

git fsck--lost-found

输出中会标注dangling blob（悬空文件内容）、dangling commit（悬空提交）、dangling tree（悬空目录）。

### 2.查看对象的类型与内容

#查看对象类型

git cat-file-t<对象哈希>

#查看对象的具体内容

git cat-file-p<对象哈希>

如果是dangling blob，直接执行git cat-file-p就能看到文件内容，可能直接得到flag。

如果是dangling commit，可以进一步查看其对应的tree与文件。

## 三、其他小众考点

**Tag标签隐藏：** flag可能写在标签的说明信息里，用git tag查看所有标签，git show<标签名>查看标签详情。

**提交信息隐藏：** flag拆分藏在多次提交的commit message中，需逐行查看提交说明拼接。

**暂存区隐藏：** 修改被加入暂存区但未提交，工作区被还原，用git diff--cached查看暂存区与HEAD的差异。

## 四、标准解题检查流程（优先级从高到低）

### 1.确认仓库状态

git status

### 2.查看所有提交历史

git log--all--oneline--decorate--graph

### 3.检查所有分支

git branch-a

### 4.检查stash临时保存

git stash list

git stash show-p stash@{0}

### 5.检查操作日志reflog

git reflog

### 6.扫描悬空对象

git fsck--full

git cat-file-p<可疑对象哈希>

## 五、高频易错点

**忽略隐藏目录：** 直接用ls看不到.git目录，误以为是普通文件夹，需用ls-la查看隐藏文件。

**stash直接pop：** 上来就用git stash pop恢复，成功后删除stash记录，破坏原始取证数据；优先使用show或apply。

**只看当前分支：** 仅检查当前分支的提交，忽略其他分支的隐藏内容。

只依赖git log：提交被reset删除后，git log看不到就放弃，忽略reflog和悬空对象。

**回滚整个仓库：** 为了看旧文件直接checkout到旧提交，改变工作区状态，容易破坏现场；优先用git show只读读取。

**扩展名陷阱：** 题目给的压缩包扩展名可能与实际格式不符，需先用file命令确认真实格式再解压
