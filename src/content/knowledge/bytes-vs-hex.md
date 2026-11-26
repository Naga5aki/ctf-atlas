---
title: 原始字节与十六进制文本
summary: 确认偏移和实际字节，再修复文件头并验证文件结构。
module: Misc
topic: 文件结构与提取
tags: [文件格式, 编码]
status: 已整理
sourceIds: [995f86da2e53]
updated: 2026-09-30
---

## 1. 先区分“值”和“文字”

`89 50 4E 47` 是描述字节的十六进制**文本**；PNG 文件开头的实际字节是 `89 50 4e 47 0d 0a 1a 0a`。把文本直接粘贴到十六进制编辑器的字符区，写进去的可能是字符 `8`、`9`、空格，而不是字节 `0x89`。完整的 PNG 签名有 8 字节，只有前四字节相同不足以证明文件有效。

```bash
xxd -l 32 sample.bin
printf '%s' '89504e470d0a1a0a' | xxd -r -p | xxd
```

第二条命令仅演示“文本转字节”，不会修改文件。对照输出时同时看左侧偏移和右侧字节，避免把屏幕上的十六进制字符当作文件内容。

## 2. 在工作副本上修复指定偏移

先用 `file sample.bin` 和 `xxd` 判断格式与目标偏移。若证据表明偏移 `0` 应当是 PNG 签名，可在 Kali/Linux 使用下例。脚本拒绝覆盖已有工作副本，并在写入后从同一偏移重新读取。

```python
from pathlib import Path
from shutil import copy2

src = Path("sample.bin")
dst = Path("sample.work.bin")
offset = 0
expected = bytes.fromhex("89504e470d0a1a0a")

if dst.exists():
    raise FileExistsError(dst)
copy2(src, dst)
with dst.open("r+b") as stream:
    stream.seek(offset)
    before = stream.read(len(expected))
    if len(before) != len(expected):
        raise ValueError("目标偏移超出文件范围")
    print("before:", before.hex(" "))
    stream.seek(offset)
    stream.write(expected)
    stream.seek(offset)
    assert stream.read(len(expected)) == expected
print("after: ", expected.hex(" "))
```

把代码保存为 `repair_header.py` 后运行 `python3 repair_header.py`，再执行 `xxd -l 16 sample.work.bin` 与 `file sample.work.bin`。`file` 的识别只是第一层检查；还要尝试用对应格式工具解析完整结构。

在 010 Editor 中执行相同步骤时，先定位偏移、记录现有字节，再用 **Paste from Hex Text** 写入十六进制文本；从文件内部搬运字节块则用二进制复制与粘贴。以重读到的字节和结构解析结果判断修复，不以“脚本执行成功”代替验证。
