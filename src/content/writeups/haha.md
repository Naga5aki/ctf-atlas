---
title: haha
summary: JPG 中的 Quote-Printable 数据恢复 ZIP，之后分辨伪加密与真正的口令层。
module: Misc
tags: [编码, 压缩包]
status: 已整理
sourceIds: [9f28298a5e88]
challengeIds: [70afb5cd7fed]
relatedIds: [quoted-printable, zip-encryption-flags]
updated: 2026-09-29
---

## 解题链

依照以下顺序处理；关键偏移和口令尚未在当前环境重新验证：

1. 用十六进制编辑器检查 JPG，找到一段以 `=HH` 序列表现的 Quote-Printable 数据，其中可见 ZIP 的 `PK` 特征。
2. 从题目附件取出**准确字节**，用 `quopri.decodestring` 解码为 ZIP，确认可以读取中央目录。
3. 第一层 ZIP 表现为伪加密；核对并修正相应标志位后，再处理内部真正加密的 ZIP。
4. `hint.txt` 给出 `do_u_like_xxx`，据此设置掩码尝试口令。待验证的口令候选为 `do_u_like_ftc`。

长编码串在文本转换时可能被插入换行，不能直接将显示文本当作题目数据。具体偏移与字节以 JPG 附件为准。
