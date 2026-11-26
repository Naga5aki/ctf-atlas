---
title: Quoted-Printable 隐藏二进制
summary: 从 =HH 字节序列还原数据，并验证解码后的文件结构。
module: Misc
topic: 文本与编码
tags: [编码, 文件格式]
status: 已整理
sourceIds: [9f28298a5e88]
challengeIds: [70afb5cd7fed]
updated: 2026-09-30
---

## 1. 识别线索

文本中密集出现 `=03`、`=00` 等 `=HH` 序列，开头还能辨出 `PK` 时，可以考虑 **Quoted-Printable** 编码的 ZIP 字节流。`=HH` 表示十六进制字节；行尾的 `=` 后接换行可能是软换行，解码时应去掉，不能把它当成数据字节。先确认取得的是连续、完整的编码文本，再判断是否存在别的前缀或编码层。

## 2. 直接从字节解码

不要先把内容转换成 Unicode 字符串再重新编码；这可能改变非 ASCII 字节和换行。将待解码内容保存为 `payload.txt`，运行：

```python
import hashlib
import quopri
import zipfile
from pathlib import Path

encoded = Path("payload.txt").read_bytes()
decoded = quopri.decodestring(encoded)
output = Path("decoded.zip")
if output.exists():
    raise FileExistsError(output)
output.write_bytes(decoded)

print("长度:", len(decoded))
print("SHA-256:", hashlib.sha256(decoded).hexdigest())
print("前 16 字节:", decoded[:16].hex(" "))
print("ZIP 结构:", zipfile.is_zipfile(output))
if zipfile.is_zipfile(output):
    with zipfile.ZipFile(output) as archive:
        for entry in archive.infolist():
            print(entry.filename, entry.file_size, entry.CRC)
```

保存为 `decode_payload.py` 后执行 `python3 decode_payload.py`。列表成功只说明中央目录可读；若需解压，还应校验解出文件的内容与 CRC，并留意是否存在口令或下一层编码。

## 3. 失败时回到输入检查

- **开头不是预期魔数**：核对是否多复制了标题、空格或引号，或编码文本前还有包裹层。
- **中央目录损坏**：核对输入是否截断、是否把可见换行误写为 `\n` 两个字符、是否丢失软换行末尾的 `=`。
- **从 PDF 或图片提取的文本**：识别过程可能插入空格、换行或改写全角字符；以题目附件中的实际字节为准，保留提取前后的长度和哈希。

不要仅因为解码后出现 `PK` 就认定 ZIP 完整；需要能解析目录并读取目标条目。
