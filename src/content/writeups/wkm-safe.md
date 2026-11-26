---
title: wkm 的保险箱
summary: USB 键盘流量、BMP 尾部 RAR、零宽提示与按列像素恢复的组合题。
module: Misc
tags: [流量, 文件格式, 容器]
status: 已整理
sourceIds: [b00c1293b34b]
challengeIds: [0d13f119d880]
relatedIds: [usb-keyboard, file-carving]
updated: 2026-09-29
---

## 解题链

题目给出 `Memorandum.pcapng` 和 `Encrypted_Container.bmp`。下列流程尚未在当前环境重新运行。

1. 从 USB 键盘流量还原输入历史。密钥曾被输入又删除，所以要看逐键记录，而非只看最终文本。
2. 检查 BMP 尾部，提取附加的 RAR；其中有 `broken_data.png` 和 `hint.txt`。
3. `hint.txt` 中的零宽字符给出“左侧缺列”的提示。BMP 最右侧异常像素列与 PNG 高度相同。
4. 将 BMP 右侧一列补到 PNG 左侧，按**列优先**顺序读取像素，每个像素依 RGB 顺序写入字节，得到 VeraCrypt 容器候选文件。
5. 用键盘流量所得密钥尝试挂载，并以容器能否正确打开、内部文件是否合理作最后验证。

像素提取有宽高、通道顺序和截断长度三处易错点。复现时应以题目附件核对每一步的中间结果。
