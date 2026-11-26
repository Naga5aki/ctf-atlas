---
title: ZIP 加密标志与伪加密
summary: 对照本地文件头与中央目录的加密位，区分伪加密和真实口令。
module: Misc
topic: 压缩与口令
tags: [压缩包, 文件格式]
status: 已整理
sourceIds: [995f86da2e53, 9f28298a5e88]
challengeIds: [70afb5cd7fed]
updated: 2026-09-30
---

## 1. 先判断是哪一层 ZIP

图片后附加 ZIP、ZIP 内再包含 ZIP 时，先把每一层分开编号，记录各自的哈希和能否列目录。*haha* 需要先从 JPG 中恢复外层 ZIP，处理其加密标志后，内层仍可能真正需要口令。不要因为归档工具弹出密码框，就立即判断压缩数据已加密。

```bash
sha256sum archive.zip
file archive.zip
7z l -slt archive.zip
```

## 2. 核对每个条目的两个标志位

ZIP 的**通用用途标志**中，最低位 `0x0001` 表示该条目被标记为加密。本地文件头从签名 `50 4b 03 04` 开始，标志位位于该头起点后 **6–7 字节**；中央目录条目从 `50 4b 01 02` 开始，标志位位于该头起点后 **8–9 字节**。两个位置都要按小端序读取，且一个归档中可能有多个条目。

下例只读取，不改归档。`ZipInfo.flag_bits` 来自中央目录；`header_offset` 指向对应的本地文件头。

```python
from pathlib import Path
from zipfile import ZipFile

path = Path("archive.zip")
with ZipFile(path) as archive, path.open("rb") as stream:
    for entry in archive.infolist():
        offset = entry.header_offset
        stream.seek(offset)
        header = stream.read(8)
        if header[:4] != b"PK\x03\x04":
            raise ValueError(f"本地文件头签名异常：{entry.filename}")
        local = int.from_bytes(header[6:8], "little")
        central = entry.flag_bits
        print(entry.filename, f"local=0x{local:04x}",
              f"central=0x{central:04x}",
              f"encrypted={bool(central & 1)}")
```

保存为 `inspect_zip_flags.py` 后运行 `python3 inspect_zip_flags.py`。若目录本身损坏、脚本不能打开归档，先检查尾部中央目录与截取边界，不能把报错直接归为伪加密。

## 3. 修改与验证的边界

当证据显示“只有标志位错误、压缩数据本身未加密”时，才在**副本**上逐条记录偏移、原值和目标值，修改对应标志位。不要清空其他位；数据描述符、UTF-8 文件名等也使用同一字段。修改后重新读取本地头和中央目录的标志，并对工作副本执行 `7z t archive.work.zip`；还应解出目标文件核对内容和 CRC。

如果清除加密位后仍然出现解压错误、CRC 不匹配或乱码，就不能称为修复成功。此时回看数据是否真正加密、是否存在多层归档、中央目录是否与本地头不一致。
