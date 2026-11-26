---
title: "ZIP Raw Deflate 数据流手工提取与解压"
summary: "那么可以绕过 ZIP 文件结构，直接提取该文件对应的 Deflate 压缩数据进行解压。"
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、考点本质

ZIP 中某个文件如果满足以下条件：

没有加密

压缩方法为 Deflate

ZIP 文件结构本身可能损坏，导致常规解压失败

那么可以绕过 ZIP 文件结构，直接提取该文件对应的 Deflate 压缩数据进行解压。

核心流程

ZIP → 定位文件数据 frData → 提取原始 Deflate 数据 → 补适当的 Zlib 包装 → Inflate → 恢复原文件

## 二、识别方法

### 1. 确认压缩方式为 Deflate

使用 010 Editor 的 ZIP 模板分析时，可以看到：

COMPTYPE = COMP_DEFLATE (8)

其中 Compression Method = 8 代表 Deflate。

| 压缩方式编号 | 含义 |
| --- | --- |
| 0 | Store，不压缩 |
| 8 | Deflate |

看到 Compression Method: 8 就是本题最重要的信号之一。

### 2. 找到真正的文件压缩数据

在 010 Editor ZIP 模板中，Local File Header 后通常可以看到：

frFileName[8] = flag.txt

frData[21]

| 字段 | 含义 |
| --- | --- |
| frFileName | ZIP 内部文件名 |
| frData | 该文件实际保存的压缩后数据 |

真正需要提取的是 frData，而不是：

PK 03 04 文件头

文件名

Central Directory

整个 ZIP 文件

## 三、核心原理：Raw Deflate vs Zlib

为什么不能直接 Zlib Inflate？

这是这个考点最容易混淆的地方。

ZIP 中的 Deflate 数据通常保存的是 Raw DEFLATE 数据流

很多工具的 Zlib Inflate 期待的是 Zlib 格式封装的 Deflate 数据

**二者关系：**

Raw DEFLATE

↓

加 Zlib 包装

↓

Zlib 数据流

Deflate 是压缩算法；Zlib 是对 Deflate 数据的一种封装格式。

## 四、为什么补 78 9C

常见 Zlib 数据头

| Header | 说明 |
| --- | --- |
| 78 01 | 无压缩 / 最快 |
| 78 5E | 默认压缩 |
| 78 9C | 默认压缩（CTF 最常见） |
| 78 DA | 最佳压缩 |

操作方法

原始 ZIP frData：

4B CB 49 4C AF 2E 49 2D ...

前面补 78 9C：

78 9C 4B CB 49 4C AF 2E 49 2D ...

**然后交给：**

CyberChef → From Hex → Zlib Inflate

重要纠正

78 9C 本身不是 "Deflate 文件头"，更准确地说它是常见的 Zlib Header

不要记成 "Deflate 文件头一定是 78 9C"

**正确理解：** ZIP 内部通常是 Raw Deflate；某些工具只接受 Zlib 流，因此可尝试在 Raw Deflate 前补常见 Zlib Header 78 9C 后解压

关于 Adler-32 校验

严格的 Zlib 数据格式还包含尾部 Adler-32 校验值：

有些工具较宽松，仅补头也能成功

如果工具严格校验，则可能还需要完整构造 Zlib 包装（补头 + 补尾部 Adler-32）

## 五、CTF 触发场景

**尤其看到以下情况时要敏感：**

| 场景 | 说明 |
| --- | --- |
| ZIP 无密码，但正常解压失败 | 结构损坏导致常规工具无法处理 |
| ZIP 尾部结构被破坏 | EOCD 等尾部字段丢失或错误 |
| Central Directory 损坏或缺失 | 无法通过目录索引定位文件 |
| CRC、文件大小等字段被修改 | 校验不通过导致解压失败 |
| ZIP 文件被故意截断 | 数据不完整但 Local File Header 仍在 |
| 能看到完整的 PK 03 04 Local File Header | 单个文件记录结构完整 |
| 010 Editor 能正常定位 frData | 压缩数据本身完好 |
| Compression Method 为 8 / Deflate | 符合 Raw Deflate 提取条件 |

这时不要一直修整个 ZIP，完全可以尝试绕过 ZIP 结构，直接抢救内部压缩流。
