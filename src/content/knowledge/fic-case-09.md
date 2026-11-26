---
title: "文件格式与隐写"
summary: "从媒体容器、文档结构、熵值与二维码中识别隐藏和损坏线索。"
module: "Forensics"
track: "文件与多媒体取证"
topic: "文件恢复与格式"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
challengeIds: []
relatedIds: []
updated: "2026-10-15"
---
## 01 先识别容器，再判断损坏或隐藏

文件格式取证先区分外层容器与内部载荷。扩展名、随机外观或播放器报错只能提供线索；需要解析成员、长度、偏移、校验和引用关系。修复或解密只写入副本，保留原始摘要、修改位置和派生链，最后使用结构解析与实际内容共同验证。

### 01.1 常见容器与关注字段

| 格式 | 结构 | 检查重点 |
| --- | --- | --- |
| MP4 / ISO-BMFF | `ftyp`、`moov`、`mvhd`、`stco/co64`、`stsz`、`stts`、`mdat` 等 box | box 长度、chunk 偏移、样本大小、时间表与轨道对应 |
| OLE `.doc/.xls/.et` | 复合文档流，如 `Workbook`、`WordDocument` | OLE 流目录、BIFF、`MSODRAWING(0x00EC)`、`OBJ(0x005D)` |
| OOXML `.docx/.xlsx/.pptx` | ZIP + XML + 媒体成员 | 隐藏表、批注、自定义属性、`media/`、关系文件 |
| PDF | 对象、交叉引用、流 | 嵌入文件、JS、注释与增量更新关系 |
| ZIP/APK | 本地头、成员、中央目录 | 重复成员、注释、路径、加密位与真实加密结构 |

```bash
sha256sum ./evidence/input.bin
file ./evidence/input.bin
xxd -l 64 ./evidence/input.bin
```

ZIP 的加密标志可能被改写，但取消标志不是通用解密方法；PDF 或文档中的脚本作为静态材料查看，不为读内容而运行。格式解析失败时，记录失败位置和剩余可解析范围，不立刻认定它是隐写。

## 02 MP4 chunk 偏移的定位与修复

### 02.1 区分症状与已证实原因

花屏、无法 seek、关键帧错误可能来自样本数据损坏、编码器问题、缺失 `moov`、时间表或偏移损坏。`stco` 保存 32 位大端 chunk 偏移，`co64` 保存 64 位值；它们在非分片文件的样本表内引用媒体数据。不能仅因花屏就认定“全部偏移被统一修改”。

**材料：** 视频原件、修改它的程序或已确认的损坏规律、播放器/解析日志。先查看容器与轨道，再分析程序中是否确实对所有目标偏移减去常量。

```bash
mkdir -p ./work
ffprobe -v error -show_format -show_streams -of json ./evidence/input.mp4 > ./work/input-probe.json
MP4Box -info ./evidence/input.mp4
```

检查 `ftyp`、box 边界、轨道数量、时间和样本表。`mvhd` 的 timescale/duration 需要一起解释，`stts` 决定解码时间映射，`stsz` 与 `stsc` 决定样本大小及 chunk 内布局，不能只看某个时长数值。若是含 `moof/traf/trun` 的分片 MP4，数据定位体系不同，下面脚本不适用。

### 02.2 实战：已证实统一偏移的非分片文件

**场景：** 静态分析已证明程序对普通、单文件、内部媒体数据的 MP4 chunk 偏移统一减去 `1337`，但没有改动 `mdat` 内容和表结构。修复方向应为**加回 1337**。如果实际程序加了该值，就传入负的修复增量。不存在统一规律时，停止套用此方法。

保存下面脚本为 `repair_mp4_offsets.py`。它沿已知 box 容器结构解析真实 `stco/co64`，校验边界和计数，只把修复后值允许落入顶层 `mdat` 数据区的表写入新文件；不搜索任意字节串、不取模绕过溢出，也不覆盖输入。

```python
import argparse
import struct
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('output')
parser.add_argument('--delta', required=True, type=int,
                    help='加到每个已确认chunk偏移的修复增量')
args = parser.parse_args()
src, dst = Path(args.input), Path(args.output)
if src.resolve() == dst.resolve() or dst.exists():
    raise ValueError('输出必须是不存在的新文件')
data = bytearray(src.read_bytes())
containers = {b'moov', b'trak', b'mdia', b'minf', b'stbl'}
tables, mdats, top_types = [], [], []

def walk(start, end, path=()):
    pos = start
    while pos < end:
        if end - pos < 8:
            raise ValueError(f'box头截断: {pos}')
        size, kind = struct.unpack_from('>I4s', data, pos)
        header = 8
        if size == 1:
            if end - pos < 16:
                raise ValueError('扩展box头截断')
            size = struct.unpack_from('>Q', data, pos + 8)[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            raise ValueError(f'box长度越界: {pos} {kind!r}')
        body, stop = pos + header, pos + size
        here = path + (kind,)
        if not path:
            top_types.append(kind)
            if kind == b'mdat':
                mdats.append((body, stop))
        if kind in (b'stco', b'co64') and path and path[-1] == b'stbl':
            unit = 4 if kind == b'stco' else 8
            if stop - body < 8 or data[body:body+4] != b'\0\0\0\0':
                raise ValueError('样本偏移表版本/flags异常')
            count = struct.unpack_from('>I', data, body + 4)[0]
            if stop - body != 8 + count * unit:
                raise ValueError('偏移表长度与count不一致')
            tables.append((here, body + 8, count, unit))
        if kind in containers:
            walk(body, stop, here)
        pos = stop

walk(0, len(data))
if b'moof' in top_types or not mdats or not tables:
    raise ValueError('需要含mdat和样本偏移表的非分片文件')
changed = 0
for path, entries, count, unit in tables:
    fmt = '>I' if unit == 4 else '>Q'
    for i in range(count):
        at = entries + i * unit
        old = struct.unpack_from(fmt, data, at)[0]
        new = old + args.delta
        if not 0 <= new < (1 << (8 * unit)):
            raise ValueError('修复值下溢或溢出')
        if not any(lo <= new < hi for lo, hi in mdats):
            raise ValueError(f'修复值不在mdat数据范围: {old}->{new}')
        struct.pack_into(fmt, data, at, new)
        changed += 1
    print('/'.join(k.decode('ascii') for k in path), 'entries=', count)
if not changed:
    raise ValueError('没有可修改的偏移条目')
dst.write_bytes(data)
print('modified_entries=', changed, 'output=', dst)
```

```bash
mkdir -p ./work
python3 repair_mp4_offsets.py ./evidence/input.mp4 ./work/repaired.mp4 --delta 1337
sha256sum ./evidence/input.mp4 ./work/repaired.mp4
ffprobe -v error -show_format -show_streams -of json ./work/repaired.mp4 > ./work/repaired-probe.json
ffmpeg -v error -i ./work/repaired.mp4 -f null - 2> ./work/decode-errors.log
```

**输出判读：** 脚本列出实际表路径与条目数；例如 `moov/trak/mdia/minf/stbl/stco entries=120`。这证明哪些表被修改，不证明视频已经正确恢复。若 `ffmpeg` 报 invalid NAL、解码失败或缺帧，继续核对样本内容和相关表，不重复调整常量凑出可播放效果。[FFmpeg 文档](https://ffmpeg.org/ffmpeg.html)中的解码检查可补充结构解析。

### 02.3 修复边界与最终复核

脚本仅适用于已证实统一增量、box 结构完整、样本表有效、媒体数据内置的非分片文件。它没有检查每个 chunk 的全部样本是否都在合法范围，也没有重建缺失 `moov`、修复编码数据或外部数据引用。`mdat` 起点内命中只是必要条件，完整修复仍需 `stsc/stsz`、轨道与样本一致性检查。

最后检查解码日志，实际播放多个时间点、seek 和关键画面，必要时比对已知画面或修改前的独立副本。报告保留依据、增量方向、条目数、偏移修改清单、原/新摘要及未恢复的部分。仅“播放器能打开”不能替代这些验证。

## 03 OLE / BIFF：从绘图记录到坐标

### 03.1 读取 Workbook 与 BIFF 记录链

**场景：** 一个 WPS `.et` 或旧式 `.xls` 是 OLE 复合文档，表格内容很少但包含大量绘图对象。先确认存在 `Workbook` 或 `Book` 流，再解析 BIFF 的 `type(2B) + length(2B) + data`，两字段为小端。

```python
import struct
from pathlib import Path
import olefile

out = Path('work/drawing-records')
out.mkdir(parents=True, exist_ok=True)
with olefile.OleFileIO('evidence/input.et') as ole:
    print('streams=', ole.listdir())
    name = 'Workbook' if ole.exists('Workbook') else 'Book'
    if not ole.exists(name):
        raise ValueError('没有候选BIFF工作簿流')
    stream = ole.openstream(name).read()
pos, serial = 0, 0
while pos < len(stream):
    if len(stream) - pos < 4:
        raise ValueError('BIFF记录头截断')
    kind, size = struct.unpack_from('<HH', stream, pos)
    stop = pos + 4 + size
    if stop > len(stream):
        raise ValueError('BIFF记录长度越界')
    if kind in (0x00EC, 0x005D):
        serial += 1
        (out / f'{serial:04d}-{kind:04x}.bin').write_bytes(stream[pos+4:stop])
        print(f'offset={pos}, type=0x{kind:04x}, bytes={size}')
    pos = stop
```

此脚本导出定位用记录，没有完整解析 OfficeArt/Escher。绘图可能跨 `CONTINUE` 记录，工作簿存在多张表与不同记录范围；后续需按实际 BIFF 与 OfficeArt 结构关联，不能把每一段 `MSODRAWING` 都直接当作独立形状。[olefile 读取 API](https://olefile.readthedocs.io/en/latest/Howto.html)用于核对复合文档流读取。

### 03.2 实战：数字标识编码坐标

假设程序或有效对象字段已证明数字标识采用 `encoded = x_part * 1000 + y_part`，且 `0 <= y_part < 1000`。真实坐标由 `x=(x_part^85)-100`、`y=(y_part^85)-100` 恢复。先验证编码边界，再按公式解码；没有这些证据时不能对所有数字套用。

```python
def decode_label(label, xor_key=85, bias=100):
    if not label.isdecimal():
        raise ValueError('不是已确认的数字标识')
    value = int(label)
    x_part, y_part = divmod(value, 1000)
    return (x_part ^ xor_key) - bias, (y_part ^ xor_key) - bias

print(decode_label('221220'))
```

**预期输出：** `(36, 37)`。检索时分别尝试 UTF-16LE 与实际 ANSI 编码；每个候选都验证它确实属于形状名称/目标属性、编码长度及坐标范围。两个解码方法都输出数字，不是“投票”确认正确的充分依据，结构位置更重要。

### 03.3 点阵字符与识别评分

1. 按 `char_idx = x // spacing` 分到字符位置，再用 `((x%spacing)//cell, y//cell)` 建立局部网格。
2. 记录 `spacing`、`cell`、原点、坐标方向、缩放和去重方式；负坐标或边界点要单独核对。
3. 把每个字符点集可视化，与实际使用的内置点阵字模比较。
4. 用 F1 等相似度保留最优与次优字符及分差，不把低分结果硬拼成唯一字符串。
5. 将识别出的字符重新映射为点集，核对与真实形状的一致性及未匹配点。

```python
def f1(observed, template):
    observed, template = set(observed), set(template)
    if not observed and not template:
        return 1.0
    return 2 * len(observed & template) / (len(observed) + len(template))
```

相似度高支持点阵对应，仍需结构与编码来源。形状 Z 序、线宽、颜色通道、批注、隐藏行列、自定义属性、`veryHidden` 表等都可作为已有文档的检查位置；只有发现规律与有效载荷后才称为隐写，正常格式信息不能自动归为隐藏数据。

## 04 熵值与加密配置

### 04.1 计算指定范围的 Shannon 熵

**场景：** 飞行日志或配置文件前部可读，正文看起来随机。先保留完整文件，再按已确认的头部长度计算正文熵；`100` 字节不是所有格式通用的头长。

```python
import math
from collections import Counter
from pathlib import Path

data = Path('evidence/input.bin').read_bytes()
start = 100  # 仅在已确认格式采用此正文起点时使用
body = data[start:]
if not body:
    raise ValueError('选定范围为空')
entropy = -sum((count/len(body)) * math.log2(count/len(body))
               for count in Counter(body).values())
print('range=', start, len(data), 'bytes=', len(body), 'bits_per_byte=', entropy)
```

接近 `8 bits/byte` 可以提示压缩、加密或随机数据；不能单独判定 AES，也不能证明整个文件都加密。小样本、压缩图片和正常媒体块也有相近表现。结合格式版本、代码调用、文件头和解密参数再判断。

### 04.2 实战：加密配置解为 JSON

从 `assets/config.dat` 的读取位置追踪种子或密钥，核对 `resources.arsc/strings.xml`、派生单位、AES 模式、IV 与填充，再离线读取。`MD5(seed)[:16]` 必须说明指原始摘要还是 hex 字符；不要盲试模式后只保留可读片段。

输出 JSON 后解析完整对象、核对代码消费字段并重新加密比较。密钥派生和工程步骤见[密码学取证](/knowledge/fic-case-08/)，资源与 APK 调用链见[Android 取证](/knowledge/fic-case-06/)。若得到钱包字段，继续核对链与资金活动，不能只凭字符串称为收款事实。

## 05 图片、二维码与其他载荷

### 05.1 还原图片后再读取内容

图片可能被 RSA、AES 或 XOR 保护。先恢复完整格式、检查尺寸和像素内容，再读取二维码。二维码可能包含下载链接、钱包地址或通信端点；记录原始文本，不自动打开其中链接。

```bash
file ./work/recovered.png
sha256sum ./work/recovered.png
zbarimg --raw ./work/recovered.png
```

**判读：** 解码器返回 `https://download.example.test/app.apk`，说明该图片对应二维码可解出此文本。还需核对静区、纠错、图像是否重绘、多个二维码顺序及真实下载记录；二维码有地址不等于文件已经下载或程序执行。扫码失败时可在副本中改善缩放/对比度，但保留原图与所有处理步骤。

### 05.2 文件名与多种隐藏位置

图片名称可能含交易 hash、内容摘要或随机 ID。先验证名称与实际交易/摘要的关系，再将它用于跨文件关联。EXIF 自定义字段、LSB、拼接载荷及尾随数据也需先识别结构。

```bash
binwalk ./evidence/input.png
```

`binwalk` 的签名命中只给出嵌套内容候选和偏移，压缩数据中也可能误命中。先读取候选范围、验证长度和格式，再导出到新文件；不要未经核对就自动提取并运行成员。最后记录“原图 → 修改/解密副本 → 可解析载荷 → 内容关联”的链路，注明识别成功与未验证的历史行为。

## 06 PNG 宽高修复：完整 IHDR 与可信 CRC

### 06.1 确认哪个字段损坏

**场景与材料：** 一张 PNG 的画面截断或解码报错，其他块仍可读取，怀疑只有 IHDR 的宽/高被改变。先固定图片哈希，验证签名和块链，保存原 IHDR 数据和 CRC。画面异常也可能来自 IDAT 损坏、颜色类型、行滤波或拼接载荷，不能默认都由宽高导致。

普通 PNG 的首块 IHDR 长度为 `13`：宽 4 字节、高 4 字节，以及位深、颜色类型、压缩、滤波、隔行 5 个单字节字段。它们都按 PNG 规定解释；**IHDR CRC32 覆盖 `b'IHDR' + 全部13字节数据`，不含长度字段**。只计算 `IHDR+宽高8字节` 会漏掉 5 个字段，得到错误结果。

| 标准首块位置 | 内容 | 单位 |
| --- | --- | --- |
| `0x00–0x07` | 8 字节 PNG 签名 | 原始字节 |
| `0x08–0x0B` | IHDR 数据长度 | 大端 32 位，标准值 13 |
| `0x0C–0x0F` | `IHDR` 类型 | 4 字节 |
| `0x10–0x13` / `0x14–0x17` | 宽 / 高 | 大端 32 位 |
| `0x18–0x1C` | 其余 5 个字段 | 按格式定义逐项读取 |
| `0x1D–0x20` | 首块 CRC32 | 大端 32 位 |

这些偏移适用于签名和首块完整的标准布局；文件前面有额外封装、块缺失或长度错位时，先解决层次问题，不直接写固定 offset。

### 06.2 实战：已知高度时有限枚举宽度

假设高度已由另一可信记录或完整扫描线结构确认，IHDR 除宽度外的字节及原存 CRC 也可信，才可按限定宽度搜索。以下脚本只输出候选，不自动修改图片；`1080` 是示例已知高度，要替换为实际核对值。扫描其余块发现 CRC 不一致时停止，避免把多处损坏归结成单字段问题。

```bash
python3 - ./work/input.png 1080 <<'PY'
from pathlib import Path
import struct
import sys
import zlib

data = Path(sys.argv[1]).read_bytes()
known_height = int(sys.argv[2])
if data[:8] != b'\x89PNG\r\n\x1a\n' or len(data) < 33:
    raise ValueError('PNG 签名/首块不完整')
if struct.unpack_from('>I', data, 8)[0] != 13 or data[12:16] != b'IHDR':
    raise ValueError('不是标准 13 字节 IHDR 首块')
if not 1 <= known_height <= 0x7fffffff:
    raise ValueError('已知高度不合法')
offset, seen_iend = 8, False
while offset + 12 <= len(data):
    length = struct.unpack_from('>I', data, offset)[0]
    end = offset + 12 + length
    if end > len(data):
        raise ValueError('块长度越界')
    kind = data[offset + 4:offset + 8]
    stored = struct.unpack_from('>I', data, offset + 8 + length)[0]
    actual = zlib.crc32(data[offset + 4:offset + 8 + length]) & 0xffffffff
    if offset != 8 and stored != actual:
        raise ValueError('IHDR 之外的块 CRC 不一致：' + repr(kind))
    if kind == b'IEND':
        if length != 0:
            raise ValueError('IEND 长度错误')
        seen_iend = True
        print('IEND_end=', end, 'trailing_bytes=', len(data) - end)
        break
    offset = end
if not seen_iend:
    raise ValueError('没有完整 IEND')
target_crc = struct.unpack_from('>I', data, 29)[0]
other_fields = data[24:29]
matches = []
for width in range(1, 5001):  # 根据材料限定范围，不能无限扩大后择一
    candidate = struct.pack('>II', width, known_height) + other_fields
    if zlib.crc32(b'IHDR' + candidate) & 0xffffffff == target_crc:
        matches.append((width, known_height))
print('dimension_candidates=', matches)
PY
```

脚本保留原颜色类型等 5 字节。没有匹配可能是范围不足、高度错误、其他字段或 CRC 已改变；多个匹配应全部保留。若宽高都不确定，要根据已知尺寸、扫描线结构等限定二维候选范围，逐一计算完整 IHDR，不把未知高度当作固定值，也不能使用参数却未把它写入 CRC 输入。

### 06.3 修改副本与解码验证

1. 每个有依据的候选只修改工作副本的宽高字段，保留原 CRC 和其他字节，记录改动前后、offset、长度与 SHA-256。以原 CRC 约束出的候选，不应先重写 CRC 再宣称“CRC 已验证原尺寸”。
2. 独立核对候选 IHDR CRC、合法位深/颜色组合、IDAT 解压结果与行长度、滤波和隔行方式；本节候选脚本不代替完整解码器。
3. 用完整 PNG 解码器实际加载所有像素，记录解码错误和画面边界，再与截图、尺寸线索及内容结构交叉核验。CRC32 是差错校验，可碰撞，也不能证明尺寸曾经如此或图片未被蓄意重写。
4. 原 CRC 不可信时，可尝试有证据支持的结构修复，但应明确“新构造了可解码候选”；不能称为从原 CRC 反推出原始宽高。

若画面含文本或助记词，保存像素坐标和完整顺序；文字识别结果要回图逐个核对，不能将首词、第三词和分段顺序混用，也不在页面公布真实秘密。

### 06.4 结束标记之后，以及损坏的文件头

图片能正常打开时，仍要看结束标记后面还有没有字节。PNG 的结束标记是 `49 45 4E 44 AE 42 60 82`。紧跟着 `D0 CF 11 E0 A1 B1 1A E1` 时，从这里把尾部切出，按 Office 97–2003 复合文档打开。JPEG 结束符 `FF D9` 后面可以再接 PNG 头 `89 50 4E 47 0D 0A 1A 0A`；PNG 的 `IEND` 后面还可以再接 RAR 头 `52 61 72 21 1A 07`。按偏移逐层切开，每一层单独认格式。

文件头被写成 0、但偏移 `0x06` 一带仍有 `JFIF` 或 `Exif`、末尾仍是 `FF D9` 时，这是 JPEG 的头被盖住。**【仅在副本/仿真/授权环境执行】**在偏移 0 覆盖 `FF D8 FF E0`，后面的图像字节保持原位。在文件前面插入一段头会把图像整体后移。两个分区各放一半损坏图片和半段摘要时，补头、拼合内容和两段文本之后再截取摘要。

## 07 ZIP 伪加密：只清加密位，不清数据描述位

### 07.1 标志位和真正加密的区别

**场景：** ZIP 提示输入密码，但条目可能只是 general purpose flag 的加密位被错误设置。先保存归档哈希、EOCD、中央目录、本地头、压缩方法与数据范围，再判断有没有真实加密封装；不因“密码打不开”就认定伪加密。

WinZip AES 的 hashcat 模式是 `-m 13600`。包内数据很大时，提取出的哈希会因为过长被拒绝，实际上限以当前版帮助为准。这时改用支持该格式的恢复工具，或按压缩包注释里给出的短字符集做有限尝试。解开后若仍是编码过的图片，先还原图片再读画面。

| 位/字段 | 意义 | 修复边界 |
| --- | --- | --- |
| general purpose flag 的 bit 0 | 该条目加密标志 | 只有确认载荷为未加密压缩数据时才考虑清除此位 |
| bit 3 | CRC/长度可由后置 data descriptor 给出 | 与加密位独立，必须保留并读取描述记录 |
| bit 6 / 特定 extra / 方法 99 等 | 强加密或 AES 等加密扩展线索 | 不能仅靠清 bit 0 解开真实加密数据 |
| local header / central directory | 同一条目的两份结构记录 | 用成员名、offset、方法、长度对应，核对标志和数据一致性 |

比如小端字节 `09 00` 表示 `0x0009`，bit 0 和 bit 3 都置位。仅清加密位应变成 `08 00`，**不是 `00 00`**；后者丢掉 descriptor 语义，可能导致 CRC/长度为零、截断或错位。也不要全文替换 `09 00`，这两个字节可能出现在正常压缩数据中。

### 07.2 精确修改与结构对应

普通本地头签名为 `50 4B 03 04`，flags 位于该头起点 `+6`；中央目录条目签名为 `50 4B 01 02`，flags 在条目起点 `+8`，都是 2 字节小端。按已解析的头位置确认后，对工作副本计算：

```python
import struct

def clear_encryption_bit(buf, confirmed_flag_offset):
    if confirmed_flag_offset < 0 or confirmed_flag_offset + 2 > len(buf):
        raise ValueError('已确认字段位置越界')
    old = struct.unpack_from('<H', buf, confirmed_flag_offset)[0]
    if old & ((1 << 6) | (1 << 13)):
        raise ValueError('存在强加密/遮蔽标志，不能使用本步骤')
    new = old & ~1
    struct.pack_into('<H', buf, confirmed_flag_offset, new)
    return old, new
```

这是**字段级修改函数**，不负责发现头、证明伪加密或处理 Zip64/AES。调用者必须先按中央目录指向的本地头建立同一条目关系，排除真实加密结构，再只对这两份已确认的 flags 修改；有的候选仅一处错置，需说明不一致原因和各自原值。不可从压缩数据中扫描到签名后就调用函数。

### 07.3 测试结构和完整成员

确认 bit 3 时，按实际格式检查 compressed data 后的 data descriptor；它可能有或没有 `50 4B 07 08` 签名，Zip64 长度字段另有规则。对照中央目录的 CRC、压缩/原始长度及真实数据范围，不能依本地头中的零长度跳到下一头。

修复候选以新文件保存，重新列目录并测试**全部成员**的解压、长度和 CRC；只看到成员名或一份文档可打开不足以通过。下面在已修复候选上做受限首轮解压校验，不向文件系统提取成员，不运行任何内容：

```bash
python3 - ./work/repaired.zip <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    members = z.infolist()
    if len(members) > 10000 or sum(i.file_size for i in members) > 50_000_000:
        raise ValueError('超过首轮成员数量/总解压大小上限，需另行规划')
    for item in members:
        if item.flag_bits & 1:
            raise ValueError('候选仍含标为加密的条目')
        count = 0
        with z.open(item) as stream:
            while True:
                block = stream.read(1 << 20)
                if not block:
                    break
                count += len(block)
                if count > item.file_size or count > 50_000_000:
                    raise ValueError('解压结果越过声明长度或读取上限')
        if count != item.file_size:
            raise ValueError('解压长度与中央目录不符')
        print(repr(item.filename), 'bytes=', count, 'crc=', hex(item.CRC))
PY
```

该读取依赖 Python 支持的压缩方法并检查成员 CRC，**不替代全部 ZIP 元数据、data descriptor 和尾部结构审计**；运行时间与压缩比异常时停止并使用资源受限环境。保留修复前后只发生预期 flags 差异的记录；如果所谓修复工具“要运行两次”，应逐次比较实际改动及剩余错误，而非把两次点击当成通用步骤。

## 08 音频频谱与图片附件隐写的证据链

### 08.1 音频中从声波切换到频谱

**材料：** 短 WAV 工作副本、音频头与采样参数、对应邮件/下载记录。没有明显语音只能提示需要进一步检查，不能直接判为隐写。Audacity 或 Adobe Audition 可切换频谱视图，调整窗口大小、时间尺度、频率范围、线性/对数显示及动态范围；保存每次参数，不只截一张“能读出字”的画面。

1. 先检查格式、时长、采样率、声道和截断情况，再在副本中打开；原始波形与各声道分别保留。
2. 频谱中如见文字/图形，记录所在时间段、频率范围、声道、窗口参数与完整截图。不同窗口长度会改变时间/频率分辨率，模糊时逐项调整并比较。
3. 对结果回到原始片段核对，区分信号中稳定图形、谐波/噪声及主观联想；必要时导出对应片段并固定哈希。
4. 系统装有音频编辑工具只是背景线索，不证明谁制作了隐藏内容。应用痕迹、文件来源、附件哈希与处理记录共同限定行为范围。

### 08.2 邮件图片与本地隐写工具关联

邮箱附件图片与下载目录的隐写工具应先分别固定。检查图片格式、元数据、尾部、像素/通道和工具版本，**不能为了尝试而运行未经审核的陌生工具或载荷**；使用可信解析器或经理解的算法在隔离副本上还原。

**独立实战：** 已确认工具采用某种像素位提取规则，从对应邮件附件提取出一串候选口令。保存图片哈希、附件/Message-ID 关联、位平面/通道顺序、输出长度与哈希，再对目标加密工作副本验证是否可解锁以及结构是否完整。工具名字和图中隐藏文本都不能单独证明目标卷密码已设置或曾被使用；验证结果需绑定具体卷/保护器。

解码后的内容若是 URL、程序或文档，不自动联网或执行，先识别真实格式并延续派生链。图像、音频、文档和密码材料使用同一 `输入 → 提取 → 输出 → 结构验证 → 行为佐证` 记录方式，便于独立复查。
