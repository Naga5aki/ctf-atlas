---
title: 文件尾附加数据定位
summary: 按容器结构确定结束偏移，提取尾随数据并验证第二层格式。
module: Misc
topic: 文件结构与提取
tags: [文件格式, 压缩包]
status: 已整理
sourceIds: [995f86da2e53, 8a04441ac988]
challengeIds: [6d259f6c159f]
updated: 2026-09-30
---

## 1. 识别值得追查的文件

图片或音频可以正常打开，但体积明显大于同尺寸文件；或者十六进制视图显示 PNG 的 `IEND`、JPEG 的 `FF D9` 之后仍有字节。此时先记录哈希、大小、候选偏移和魔数，再判断是否真的存在第二个文件。

```bash
sha256sum sample.bin
file sample.bin
binwalk sample.bin
xxd -l 64 sample.bin
```

`binwalk` 的签名命中是线索，不是完整文件证明。压缩数据或随机字节也可能恰好出现相同魔数；后续必须检查边界和内部结构。

## 2. 按 PNG 块结构确定尾部

PNG 由 8 字节签名和连续的块组成。每个块依次是 **4 字节长度、4 字节类型、数据、4 字节 CRC**。因此不能搜索到字符 `IEND` 就立即截取；需要从文件头逐块前进，读完长度为零的 `IEND` 块及其 CRC，才到 PNG 的真实结束位置。

```python
from pathlib import Path
import zlib

data = Path("image.png").read_bytes()
if not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
    raise ValueError("不是标准 PNG 签名")

offset = 8
while offset + 12 <= len(data):
    size = int.from_bytes(data[offset:offset + 4], "big")
    end = offset + 12 + size
    if end > len(data):
        raise ValueError(f"块越界：{offset}")
    kind = data[offset + 4:offset + 8]
    if kind == b"IEND":
        if size != 0:
            raise ValueError("IEND 长度异常")
        expected_crc = int.from_bytes(data[end - 4:end], "big")
        actual_crc = zlib.crc32(data[offset + 4:end - 4]) & 0xffffffff
        if actual_crc != expected_crc:
            raise ValueError("IEND CRC 不匹配，先检查图片结构")
        tail = data[end:]
        print(f"PNG 结束偏移：{end} (0x{end:x})，尾部：{len(tail)} 字节")
        if tail:
            target = Path("tail.bin")
            if target.exists():
                raise FileExistsError(target)
            target.write_bytes(tail)
        break
    offset = end
else:
    raise ValueError("未找到完整 IEND 块")
```

保存为 `extract_tail.py` 后运行 `python3 extract_tail.py`。示例仅适用于从偏移 `0` 开始的标准 PNG；若 PNG 嵌在其他文件内部，应先核对其起点。*Happy Adventure* 的截图 PNG 就可按“正常显示后继续检查 `IEND` 之后”的思路追查。

## 3. 验证提取结果

```bash
file tail.bin
xxd -l 32 tail.bin
7z l tail.bin
```

`7z l` 只在尾部像归档时使用。若出现 ZIP 魔数 `50 4b 03 04`，还要确认能列出中央目录；若文件类型不能识别，回看尾部起点、前导填充和长度，而不是直接更改扩展名。JPEG 应从实际结束标记附近核对，不能把任意一次 `FF D9` 文本命中当作边界。
