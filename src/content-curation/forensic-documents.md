## 01 辨认文档容器层次与首轮只读检查

文档与邮件取证先固定文件 SHA-256 哈希，核对文件头魔数与容器结构，切勿仅凭扩展名或可见页面下结论：
- **现代 Office 文档（`.docx`/`.xlsx`/`.pptx`）**：本质是 ZIP 压缩包，内部包含 XML 正文、`xl/workbook.xml`（含隐藏工作表状态）、批注、`media/` 嵌入媒体、`vbaProject.bin` 宏及 `_rels/*.rels` 外部关系。
- **旧式 Office / WPS 文档（`.doc`/`.xls`/`.et`）**：属于 OLE2 复合文档（魔数 `D0 CF 11 E0`），需按存储树和流（如 `Workbook`、`WordDocument`、宏流）解析。
- **PDF 文档**：由对象、流、交叉引用表（`xref`）和增量更新组成；文件末尾可能残留修改前的旧对象或嵌入附件。
- **电子邮件（`.eml`/`.mbox`/`.pst` 与客户端存储）**：保留完整原始 MIME 头与边界，区分信封发件人、可见 `From`（易伪造）与自下而上逐跳记录的 `Received` 路由链。

首轮在工作副本上识别格式并检查归档结构完整性：

```bash
sha256sum document.bin
file document.bin
7z l document.bin
7z t document.bin
```

若 `7z` 无法按 ZIP 打开，先确认是否为 OLE 复合文档、加密容器或 PDF。文档元数据中的作者、创建时间可能继承自模板；宏存在不等于已执行，外部关系链接存在也不等于已成功外联，必须结合终端进程、文件系统与网络日志交叉印证。

## 02 PDF JavaScript、元数据与口令线索

先识别加密字典、对象、流、附件、OpenAction/AA、JavaScript 名称树和 Author/Title/Subject 等元数据。PDF 显示“需要密码”不能说明所有对象都不可读；工具是否支持相关加密方式也应记录。

```bash
pdfinfo ./work/document.pdf
exiftool -a -G1 ./work/document.pdf > ./output/pdf-metadata.txt
python3 ./tools/pdfid.py ./work/document.pdf
python3 ./tools/pdf-parser.py -s /JavaScript ./work/document.pdf
```

示例假定可信的 pdfid/pdf-parser 脚本位于 `./tools/`，命令名称、实际路径和依赖以所用版本为准。保存对象编号、过滤器链和提取流哈希。混淆脚本可能把 `this.info.author/title/subject` 拼入密钥，再通过 `app.response` 或 eval 执行；Acrobat 的 `app`、`info` 对象不是 Node 默认全局变量。

优先静态解码和重写已理解的字符串计算。需要模拟时，仅对审核后的逻辑在隔离环境定义有限对象；截获 eval 的字符串后保存输出并停止，不能为了打印代码又调用真实 eval。每层编码、元数据输入与拼接结果都保留，避免直接运行未知 PDF 或附件。

## 03 Foxmail 与邮件容器

先检查文件头和目录结构，区分 EML、MBOX、PST 与 Foxmail 账户存储。保全账户目录、配置、索引、附件和邮件体，不只拷贝几个可见邮件。

Foxmail 旧版可通过对应版本的 `FMstorage.list` 引用账户存储目录；启动客户端可能重建索引、升级或同步。确需界面验证时，用完整工作副本、匹配版本和断网实验环境，不把原存储直接接入日常邮箱客户端。

邮件按信封/头字段、Message-ID、Received 链、时间、附件哈希和发送/接收状态核对。客户端目录名像邮箱地址不等于已经证明账户归属；与系统用户、登录记录和其他通信痕迹一起关联。

## 04 实战：解释 PDF 中的脚本与元数据关系

**场景与材料：** 一个 PDF 含 JavaScript 和 Author/Title/Subject 等字段，脚本可能读取元数据拼接字符串或口令。目标是解释计算逻辑，不打开未知脚本执行。

1. 固定 PDF 哈希，读取加密字典、OpenAction/AA、名称树与对象信息；用本页命令定位 JavaScript，保存对象编号和过滤器链。
2. 导出脚本流到单独文件，记录父 PDF 哈希、对象号、导出方法和输出哈希。解压/解码前后分别保留结果，不将编码文本直接解释为最终逻辑。
3. 静态列出脚本读取了哪些元数据、采取什么拼接/转换顺序、是否引用 `app.response` 或 `eval`。将实际字段值作为输入，手工或在审核后的有限逻辑中复算。
4. 如果字符串只在 Acrobat 环境中产生，明确依赖的 `app`、`info` 等对象。不能在 Node 中忽略环境差异，也不能为了获得打印结果调用未知 `eval`。
5. 把输出先作为候选，再核对它是否满足目标结构或解密条件；成功得到字符串不等于脚本曾在用户终端执行。

**示例结论：** “对象中的脚本读取文档三个元数据字段并组合成候选字符串；字段、解码步骤和输出已记录。是否实际触发脚本，需要终端程序、打开记录或网络痕迹另行验证。”

同样的分层原则适用于邮件附件：Message-ID、Received 链、MIME 部件与附件哈希组成结构证据；发送、投递、打开和执行是不同活动，不能由附件存在一项推出全部过程。

## 05 跨目录收集分卷：先确定格式和一致集合

**场景与材料：** 一份多卷归档散落在邮件缓存、回收站和不同用户的文档目录中，部分副本同名同尺寸。目标是恢复完整归档，并读取其中的文档和程序线索，不运行成员程序。

### 05.1 记录每一份候选的来路

| 范围 | 常见位置 | 必须保存 |
| --- | --- | --- |
| 邮件正文和附件缓存 | 客户端账户目录、Foxmail 相关 `Temp-*` / `Attach` 等版本相关目录 | 账户、邮件/附件标识、原始 MIME 或存储索引关系、附件哈希 |
| 回收站 | 对应卷 `$RECYCLE.BIN\<SID>\` | `$I` 原路径/时间/大小与 `$R` 内容配对、卷和 SID |
| 用户文档 | `Users/<用户>/Documents/` 及其他实际路径 | 原路径、账户 SID、内容哈希、元数据 |
| 未登录或禁用用户 | 仍留在磁盘的用户配置与文档目录 | 当前账户状态、历史归属与采集可见范围；禁用不意味着文档为空 |

同尺寸、同文件名不能证明同一分卷；同哈希可帮助去重，但仍保留不同邮件/用户路径的关联记录。回收站中 `$I` 与 `$R` 不是两份相同文件，前者通常是元信息，后者承载内容。不要忽略禁用用户，也不要凭目录名推断所有者身份。

### 05.2 原生多卷与原始分割两类流程

1. 检查归档格式、编号规则、卷标志与相邻卷关系。**原生 RAR 多卷不是默认需要二进制拼接的碎片**，通常集齐后从第一卷交给支持的解压器读取。
2. 只有已确认是按字节直接切开的 split 文件时，才按确定顺序拼接到新文件。Windows 的 `copy /B` 和 Linux 的字节拼接都只是串接，不能修复错误卷、伪造卷或缺失字节。
3. 并非每种格式或切分方式的后续卷都具有与首卷相同魔数。头部不一致是核查入口，不能单凭“不是 RAR 起始签名”排除所有候选。
4. 原生多卷从第一卷读取；原始 split 则从合并产物读取。用支持该格式的工具列目录、测试完整结构，再检查 CRC/完整性、大小与各卷需求。解压到独立新目录，不覆盖检材或已有输出。
5. 留下所有替换组合的清单、失败信息和输出哈希。仅某一份文档可打开，不代表整个卷集合完整无错；只按文件大小筛选也不能排除等长伪造件。

**显式顺序示例：** 以下只用于已经确认按字节切分的三段文件。先核对顺序、各段哈希和输出路径；不能用通配符代替排序，也不能用于任意原生 RAR 多卷。

```bash
# Bash：拒绝覆盖已有输出，读取失败时停止后续校验
(
  set -e
  set -o noclobber
  cat ./work/part01.bin ./work/part02.bin ./work/part03.bin > ./work/archive-joined.rar
  7z t ./work/archive-joined.rar
  sha256sum ./work/archive-joined.rar
)
```

Windows 的 `copy` 是 CMD 内置命令，以下在 CMD 中运行；提前确认 `work\archive-joined.rar` 不存在，完成后检查复制退出状态并用归档工具测试合并产物。

```bat
copy /B "work\part01.bin"+"work\part02.bin"+"work\part03.bin" "work\archive-joined.rar"
```

拼接失败可能留下不完整的新文件，不能把“输出存在”当作成功。应保存失败日志，在新的输出名下修正输入重试。

**示例判读：** 两份第二卷长度一致而 SHA-256 不同，分别进入完整性测试；其中一组可读取全部成员且校验通过，另一组在跨卷成员处报错。可以记录“该候选集合在当前解析器下形成可校验归档”，不能仅凭预期正文选择看起来像正文的版本。压缩 CRC 用于差错检查，仍保留成员与归档的 SHA-256、路径和恢复过程。

## 06 Word 白色文字、样式与文件尾附加内容

### 06.1 不可见文字先做结构读取

**材料：** 经识别为 ZIP 型 DOCX 的工作副本。白色字体、隐藏属性、文本框、批注、页眉页脚、修订和未引用对象可能不在普通正文提取中出现。先用本页已有的压缩结构检查固定完整性，再读取 `word/document.xml` 及样式/关系文件；不要为了显字直接保存覆盖唯一文档。

以下脚本只读取直接设为白色或隐藏的 run，输出 XML 顺序位置和文本；**它不解析继承样式、主题色或完整页面渲染**，因此是首轮定位，不是全部不可见内容扫描器。

```bash
python3 - ./work/document.docx <<'PY'
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
attr = '{' + ns['w'] + '}val'
with zipfile.ZipFile(Path(sys.argv[1])) as z:
    info = z.getinfo('word/document.xml')
    if info.file_size > 20_000_000:
        raise ValueError('XML 超过首轮脚本上限，需用匹配规模的解析方法')
    root = ET.fromstring(z.read(info))
for index, run in enumerate(root.findall('.//w:r', ns), start=1):
    properties = run.find('w:rPr', ns)
    if properties is None:
        continue
    color = properties.find('w:color', ns)
    vanish = properties.find('w:vanish', ns)
    direct_white = color is not None and color.get(attr, '').upper() == 'FFFFFF'
    directly_hidden = vanish is not None and vanish.get(attr, 'true').lower() not in ('0', 'false', 'off')
    if direct_white or directly_hidden:
        text = ''.join(node.text or '' for node in run.findall('.//w:t', ns))
        print('run=', index, 'white=', direct_white, 'hidden=', directly_hidden, 'text=', repr(text))
PY
```

**结果判读：** 如输出一个白色 run 的候选字符串，保存该 run 所在段落、上下文与 XML 字节。白色在有色背景上可能正常显示，白色或隐藏属性存在不能单独证明人为隐写；文本还可能跨多个 run，或存在旧修订。检查 `styles.xml`、主题、背景、修订状态及其他 Word 部件，并在独立副本中使用匹配渲染器确认实际显示条件。

若候选内容像容器口令，按准确字符、空格、编码和顺序记录；再对对应工作副本做解锁及结构验证，不能因文字“像密码”或另一记录采用了某值就将其认定为可用口令。报告页面不公开真实秘密；文档结构证明与后续解锁结果分别保存。

### 06.2 文件尾、嵌入对象与后续解密链

文件名叫“备忘录”也可能是 Word、OLE、ZIP 或其他容器，先识别文件头和内部结构。对“正文没有，但文件尾有”的材料，核对格式的正常末端：DOCX 的 ZIP 中央目录、EOCD/合法注释，OLE 的流和分配结构，PDF 的增量版本与尾部结构各不相同。

用十六进制视图保存末端范围、绝对字节 offset 和候选数据哈希。合法 ZIP 注释、正常 PDF 增量内容不能自动称为恶意附加；在正常容器外发现可解析 payload 时，独立导出到新文件，核对长度、格式和与宿主对象的关联。未引用字节仍可能只是旧残留或损坏，应限定结论。

**实战链：** 分卷集合 → 完整文档 → XML 中候选口令 → 加密容器解锁 → 内层文件 → 已理解的解密程序逻辑 → 末端载荷。每一步记录输入哈希、操作、输出哈希和验证，程序成员只做静态分析或隔离实验，不能在分析机直接执行。链中任何一环未验证都保留为候选，不把最终可读内容倒推为所有历史行为已经发生。

### 06.3 数字口令范围与 Office 加密

提示明确限定 6 位纯数字时，候选空间是 `000000` 到 `999999` 共 `10^6` 个，必须保留前导零；数字范围来自材料约束，不能自行缩成六位非零首字符。先识别是归档口令、Office 文件加密还是工作表保护：加密 XLSX 可能封装在 OLE 的 `EncryptionInfo` / `EncryptedPackage` 中，不等于普通 DOCX/ZIP 的加密标志。

在隔离工作副本中用支持该加密格式的工具恢复口令，记录候选规则、工具/版本、成功验证及失败范围。取得候选后实际解密并检查全部对象/表格，而非仅接受“找到密码”的提示。表格中的银行卡前缀只能用于发行机构/卡产品的候选分类；不能由前缀推断完整账号、持卡人或交易事实，也不要在网站例子公布真实卡号。

文档加密材料统一见[加密数据与凭据](/knowledge/forensic-protected-data/)，图像/音频和 ZIP 标志修复统一见[文件结构与载荷还原](/knowledge/fic-case-09/)。
