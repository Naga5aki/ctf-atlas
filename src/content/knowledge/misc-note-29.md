---
title: "MS-Office文件本质与隐写"
summary: "Office文件按底层结构可分为四大类，分析思路差异极大，是解题第一判断点。"
module: "Misc"
topic: "文档与取证"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、文件格式分类与本质区分

Office文件按底层结构可分为四大类，分析思路差异极大，是解题第一判断点。

| 类型 | 常见扩展名 | 底层本质 | Misc处理思路 |
| --- | --- | --- | --- |
| OOXML普通格式 | .docx.xlsx.pptx | ZIP/OPC标准包 | 优先解包分析XML与各类Part |
| OOXML宏格式 | .docm.xlsm.pptm | ZIP/OPC+宏二进制Part | 解包+VBA/嵌入对象专项分析 |
| 旧版二进制格式 | .doc.xls.ppt | OLE/CFB复合文件 | 不能当ZIP处理，分析OLE数据流 |
| Excel二进制工作簿 | .xlsb | ZIP/OPC包，工作簿主体为二进制记录 | 可解包，但不能将所有内容当纯XML分析 |

关键认知纠正

.xlsb不属于旧版OLE格式，仍为ZIP/OPC容器，仅部分内容采用二进制存储。

后缀为.docx/.xlsx的文件不一定是ZIP结构，加密后的OOXML可封装为OLE复合文件形态。

格式判断永远遵循Magic优先于扩展名的原则。

## 二、新版OOXML核心架构

OOXML的物理载体是ZIP压缩包，逻辑上遵循OPC（Open Packaging Conventions）规范，由三部分组成。

### 1.核心概念

**Part：** 包内的每一个独立资输入文件，如XML文档、图片、嵌入对象，是数据的实际载体。

Relationship（关系文件）：后缀为.rels，定义Part之间的关联关系，是Office定位内容的核心依据，而非依靠文件夹路径。

Content Types：[Content_Types].xml，描述每个Part的内容类型。

### 2.典型目录结构

以DOCX为例，解包后核心目录与文件：

| 第一层（根目录） | 第二层 | 第三层 | 功能说明 |
| --- | --- | --- | --- |
| [Content_Types].xml | — | — | 包内所有Part的内容类型声明，定义各文件对应的格式类型 |
| _rels/ | .rels | — | 顶层关系文件，定义主文档、文档属性、缩略图等核心资源的位置与关联关系 |
| docProps/ | core.xml | — | 核心元数据，保存作者、标题、创建时间、修改时间等基础文档属性 |
| docProps/ | app.xml | — | 应用级元数据，保存软件版本、编辑时长、模板等应用相关属性 |
| word/（Excel对应xl/，PPT对应ppt/） | document.xml | — | Word正文主文档，保存文档正文的文本、格式、段落等核心内容 |
| word/ | styles.xml | — | 文档样式定义文件，保存各类样式的格式规则 |
| word/ | settings.xml | — | 文档设置文件，保存兼容性、编辑限制等全局配置 |
| word/ | media/ | — | 媒体资源目录，存放文档内嵌的图片、音视频等素材文件 |
| word/ | embeddings/ | — | 嵌入对象目录，存放OLE嵌入对象、内嵌文档等二进制资源 |
| word/ | _rels/ | document.xml.rels | 主文档关系文件，定义正文引用的图片、链接、嵌入对象等关联关系 |

## 三、基础操作：格式验证与解包

### 1.格式验证

拿到文件第一步先确认真实格式，禁止仅凭后缀判断：

**正常未加密OOXML：** 文件头为50 4B 03 04（ZIP特征）

旧版二进制/加密OOXML：文件头为D0 CF 11 E0 A1 B1 1A E1（OLE特征）

### 2.解包方法

无需修改后缀，ZIP工具可直接访问OOXML包：

#不解压列出所有成员

unzip-l challenge.docx

#解压到指定目录

unzip challenge.docx-d office_out

#7z解压

7z x challenge.docx-ooffice_out

## 四、各组件高频隐写点

### 1.Word（DOCX/DOCM）

**核心主文档：** word/document.xml

重点检查位置

word/comments.xml：文档批注

word/footnotes.xml/word/endnotes.xml：脚注、尾注

word/header*.xml/word/footer*.xml：页眉、页脚

**word/media/：** 内嵌图片

word/embeddings/：嵌入对象

word/_rels/document.xml.rels：主文档关联关系

经典隐写手法

**隐藏文字：** 通过<w:vanish/>属性标记文本，普通显示状态下不可见，但XML中完整保留，是Word最典型的隐写方式。

白色字体、极小字号、页面外文本框等视觉隐藏，均会在XML中保留原始内容。

批注、脚注、尾注中直接写入flag、密码等线索。

### 2.Excel（XLSX/XLSM）

**核心工作簿：** xl/workbook.xml

重点检查位置

xl/worksheets/sheet*.xml：各工作表内容

xl/sharedStrings.xml：共享字符串表，大量文本通过索引引用，不直接写在工作表XML中

xl/comments*.xml：单元格批注

xl/externalLinks/：外部链接

xl/embeddings/：嵌入对象

经典隐写手法

**隐藏工作表：** 分为三级Visible/Hidden/VeryHidden；其中VeryHidden无法通过普通取消隐藏界面恢复，只能通过修改xl/workbook.xml中sheet的state属性查看。

隐藏行、隐藏列、隐藏单元格，内容仍保留在XML中。

单元格公式、批注、定义名称中隐藏信息。

共享字符串表中存在未被引用的隐藏字符串。

### 3.PowerPoint（PPTX/PPTM）

**核心演示文稿：** ppt/presentation.xml

重点检查位置

ppt/slides/slide*.xml：各幻灯片正文

ppt/notesSlides/：演讲者备注页，与幻灯片正文为独立Part

ppt/comments/：幻灯片批注

ppt/media/、ppt/embeddings/：媒体与嵌入对象

经典隐写手法

**演讲者备注：** 放映时默认不显示，是PPT隐写最高频的位置，界面无内容不代表备注无信息。

幻灯片批注、隐藏幻灯片。

## 五、通用隐写手法

### 1.包内无关联额外文件

出题人直接将flag.txt、secret.zip、图片等文件塞进ZIP包，但不添加对应的Content Type与Relationship；Office界面完全不显示，解压后可直接看到。

**排查方法：** unzip-l列出全部成员，关注根目录、异常路径下的陌生文件。

### 2.媒体资源嵌套隐写

media/目录下的图片、音视频文件，本身可能承载第二层隐写：

图片LSB隐写、文件尾追加数据、PNG异常Chunk、EXIF元数据

图片内嵌套压缩包、二维码

**排查方法：** 解包后对所有媒体文件执行file、binwalk、strings检查。

### 3.OLE/嵌入对象

embeddings/目录下的.bin文件，本质是嵌入的OLE对象，可能是Excel表格、Word文档、PDF、ZIP、其他二进制文件，不能因扩展名忽略。

**排查方法：** file识别真实类型，提取后单独分析。

### 4.宏文件隐写

.docm/.xlsm/.pptm格式包含vbaProject.bin宏文件，可能藏有硬编码字符串、Shell命令、密码、flag等。

**排查方法：** 提取VBA工程，用olevba等工具分析宏代码。

### 5.文档元数据

docProps/core.xml、docProps/app.xml中保存的作者、修改者、标题、主题、公司、创建时间等字段，均可被用来隐藏线索。旧版OLE文件对应SummaryInformation、DocumentSummaryInformation信息流。

### 6.Relationship隐写

.rels文件中的<Relationship>可指向内部Part，也可通过TargetMode="External"指向外部URI。

异常的外部链接、特殊相对路径、隐藏对象引用

**排查方法：** 全局搜索Target=，检查所有关系目标是否异常。

### 7.Custom XML与自定义UI

customXml/目录、customUI/目录中可存放自定义XML数据，界面不展示，可直接写入隐藏信息。

### 8.ZIP容器层隐写

OOXML基于ZIP，因此所有ZIP类隐写均适用：

ZIP归档注释（unzip-z查看）

文件尾追加数据（trailing data）

异常Extra Field、孤立Local File Header

## 六、旧版二进制Office（OLE/CFB）

### 1.格式标识

**文件头魔数：** D0 CF 11 E0 A1 B1 1A E1，俗称「复合文件二进制格式」，内部类似小型文件系统，由Storage（存储目录）和Stream（数据流）组成。

**核心禁忌：** 不能用unzip解压旧版.doc/.xls/.ppt。

### 2.分析重点

各类信息流的原始内容

SummaryInformation/DocumentSummaryInformation元数据

VBA宏工程流

嵌入OLE对象

未使用空间、隐藏数据流

### 3.常用工具

oletools套件（olevba、oledir、oleobj）、strings、十六进制编辑器。
