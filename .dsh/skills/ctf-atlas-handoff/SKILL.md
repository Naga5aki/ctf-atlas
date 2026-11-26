---
name: ctf-atlas-handoff
description: "CTF Atlas 的接手与交接。在 ctf-atlas 中开始一批修改之前，以及一批修改验收后收尾时使用；用户说“继续”时也用它找续接点：开工前读什么、在 WORK-LOG 登记什么、收尾留什么、怎样与其他代理和 git 协作。"
whenToUse: "在 ctf-atlas 中开始一批修改之前，以及一批修改验收后收尾时必须加载；用户说“继续”时也用它找续接点。"
---

# CTF Atlas 接手与交接

## 1. 接手时按顺序实际读取

1. 根目录 `AGENTS.md`：全部约定和明确例外。
2. `docs/maintenance/START-HERE.md`：从哪里改、每次先看什么。
3. `docs/maintenance/CURRENT-STATE.md` 和 `WORK-LOG.md` 的最新条目：当前状态、谁在写哪些文件、确切的续接点。
4. `docs/maintenance/WRITING-STANDARD.md` 和认可样例 `examples/website-reconstruction-approved.md`。
5. 目标维护稿、对应生成页、相邻章节、来源记录和专项测试。
6. `docs/maintenance/TERMINOLOGY.md` 与 `REJECTED-PATTERNS.md`：术语写法和已退回的写法。

必须实际读取，不能只说“已加载”。别一次把上百份历史报告塞进上下文，按索引读对应材料。首次接手只做 `docs/maintenance/CURSOR-START-PROMPT.md` 里的只读理解核对，然后等用户的具体修改命令。

## 2. 用户说“继续”

先看最近日志和文件差异，接上最后一个未完成的章节。不重做已验收的批次，不擅自启动其他待办。

## 3. 开工前登记

在 `WORK-LOG.md` 追加一条，保留历史，不改旧条目：日期 / 执行者（写 `DSH`）/ 用户任务 / 修改前备份位置与哈希 / 打算改的文件和章节。同一范围同一时间只有一个代理写入。

## 4. 与其他代理协作

- 默认一个代理负责一个明确的小批，另一个只读审查。同一文件同一时刻只由一个代理修改。
- 发现他人写入就重读差异，不覆盖，不自动清理。
- 最新的用户明确要求优先于旧交接摘要。
- 接近上下文或 token 上限时，完成当前小批的核对，记录修改路径、哈希、测试、待办和下一节，停下等用户继续，不自动新开任务。

## 5. 收尾时写回

- 补全 `WORK-LOG.md` 本批条目：修改前备份与哈希、改了什么、保留了哪些考点、没有做什么、检验命令与真实结果（构建页数、索引、链接数、测试失败项）、真实 UI 状态、下一步。
- 记三个能力指标：本批退回次数、verify 失败项数、`py -V:3.12 -X utf8 scripts/lint_writing.py --strict` 命中数。指标上升时，先把原因写进 `REJECTED-PATTERNS.md` 或术语表，再改技能。
- `CURRENT-STATE.md` 随最新验收更新；历史 `.work` 产物不覆盖。

## 6. git

本工程用 git 管理版本，远端见 `git remote -v`。

- 一批验收通过的修改对应一次提交。提交前确认 `git status` 里只有本批文件。
- 未经用户要求不 push，不 force push。`.work/`、`dist/`、`.astro/`、`node_modules/` 不进版本（已在 `.gitignore`）。
- 需要 diff 或历史时用 `git diff`、`git log`。回退仍按验证技能第 6 节先在副本试验。
