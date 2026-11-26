---
title: 压缩包时间戳取证
summary: 按文件编号核对归档内时间字段，避免解压后时间造成误判。
module: Misc
topic: 压缩与口令
tags: [压缩包, 时间线]
status: 已整理
sourceIds: [8a04441ac988]
challengeIds: [6d259f6c159f]
updated: 2026-09-30
---

## 1. 何时查归档时间

题目提示“时间”，但解出的多个文件正文没有明显线索时，优先读取归档中保存的元数据。*Happy Adventure* 中的 RAR 包含 `日志0.txt` 至 `日志20.txt`，可先按文件编号检查 `Created` 时间是否形成序列。不要只看解压后的文件属性；解压工具和当前文件系统可能改变或丢失时间字段。

```bash
sha256sum archive.rar
7z l -slt archive.rar > archive-list.txt
```

`-slt` 将每个条目展开为 `Path`、`Created`、`Modified` 等字段。先看哪些字段实际存在，不能把某个条目的 `Created` 与另一个条目的 `Modified` 混作同一条时间线。

## 2. 按编号整理，而不是按字典序

普通字符串排序会把 `日志10.txt` 排在 `日志2.txt` 前面。下例读取列表并按文件名末尾的数字排序，同时保留两个时间字段，便于发现空值和异常跳变。

```python
from pathlib import Path
import re

text = Path("archive-list.txt").read_text(encoding="utf-8", errors="replace")
records = []
for block in re.split(r"\r?\n\s*\r?\n", text):
    fields = dict(
        line.split(" = ", 1)
        for line in block.splitlines()
        if " = " in line
    )
    name = fields.get("Path", "")
    match = re.search(r"(\d+)(?=\.[^.]+$)", name)
    if match:
        records.append((int(match.group(1)), name,
                        fields.get("Created", ""), fields.get("Modified", "")))

for number, name, created, modified in sorted(records):
    print(number, name, "Created=", created or "缺失",
          "Modified=", modified or "缺失", sep="\t")
```

保存为 `list_times.py` 后执行 `python3 list_times.py`。如果输出为空，先查看 `archive-list.txt` 的实际字段和文件名，再调整匹配规则；不要为了得到序列而直接跳过不符合预期的条目。

## 3. 解释与验证

记录**归档类型、字段名、条目名、排序方式、显示的时区信息**。若输出未给时区，只能先按显示值比较相对顺序，不能擅自当作 UTC 或本地时间进行换算。若要将秒数、日期或时间差映射为密码，先写出明确规则，再对全部条目复算；遇到缺号、重复时间或异常值时，把它们作为证据保留。
