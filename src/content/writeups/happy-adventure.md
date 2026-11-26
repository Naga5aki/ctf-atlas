---
title: Happy Adventure
summary: 从截图尾随数据进入两层压缩包，再利用 RAR 创建时间还原字符。
module: Misc
tags: [文件格式, 压缩包, 时间线]
status: 已整理
sourceIds: [8a04441ac988]
challengeIds: [6d259f6c159f]
relatedIds: [file-carving, rar-timestamps]
updated: 2026-09-29
---

## 题目路径

这道题依次经过截图尾随数据、Base64 修复和时间戳还原三段线索。以下是可复盘的解题顺序，关键步骤尚未在当前环境重新运行。

1. `First Challenge.png` 的 `IEND` 后有尾随数据。使用 Acropalypse 截图恢复方法寻找提示，得到第一层压缩包密码 `CVE-2023-28303`。
2. `whatsthis.txt` 是被字符串 `Zss010C3` 污染、且缺少 PNG Base64 开头的数据。去除干扰串并补回开头后，图片给出 TimeKey `2144483000`。
3. 用 TimeKey 解开第二层 ZIP；直接从 RAR 元数据读取 `日志0.txt` 至 `日志20.txt` 的创建时间，换成上海时区的 Unix 时间戳后逐项减去 TimeKey，按 ASCII 还原答案主体。

## 关键验证

截图恢复、Base64 修复和时间换算应各自保留中间文件。RAR 的 `Created` 字段应从归档读取，不能用解压后文件在系统里显示的时间替代。

题目数据解出的是花括号内的内容；`flag` 前缀按常见格式补全，最终仍以比赛要求为准。
