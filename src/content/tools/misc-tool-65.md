---
title: "oletools"
summary: "oleid 是 Office 文件的 \"总览扫描器\"，作为分析第一步使用。"
module: "Misc"
topic: "文档与取证"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、oleid

### 1. 工具定位

oleid 是 Office 文件的 "总览扫描器"，作为分析第一步使用。它检测文档里与恶意内容相关的重要特征，包括文件实际类型、VBA Macro、嵌入 OLE Object、Flash、Office 加密、可疑宏特征等。当前实现还会结合 ftguess、olevba 和 mraptor 做部分识别和宏分析。

### 2. 核心命令及参数

oleid challenge.doc

oleid challenge.docm

直接跟文件路径即可，无复杂参数。

### 3. 应用场景

拿到未知 Office 文件后第一步运行，它告诉你接下来应该用哪个工具：

VBA Macros = Yes → 用 olevba

Embedded Objects = Yes → 用 oleobj

DDE 可疑 → 用 msodde

### 4. 补充说明

oleid 本身不做深度分析，只做特征检测和分流，是整个 oletools 工具集的入口工具。它的价值在于快速判断文件风险面和后续分析方向，避免盲目逐个工具尝试。

## 二、olevba

### 1. 工具定位

olevba 是整个 oletools 里最重要的 VBA 宏分析核心工具。它负责检测 VBA、提取 VBA 源码、识别 AutoExec、识别危险 API / 关键词、提取 IOC、识别部分混淆、分析 Excel 4.0/XLM 宏。支持传统 OLE Office 和现代 OpenXML Office。

### 2. 核心命令及参数

olevba challenge.docm          # 完整分析+源码

olevba -c challenge.docm       # 只看源码（code）

olevba -a challenge.docm       # 只做分析（analysis）

olevba --decode challenge.docm # 反混淆辅助

### 3. 应用场景

分析含宏的 Office 文档（.docm/.xlsm/.pptm 等）。例如：

Private Sub Document_Open()

CreateObject("WScript.Shell").Run "powershell ..."

End Sub

**可能被标记为：**

AutoExec = Document_Open

Suspicious = CreateObject / Run / PowerShell

能识别 URL、IP、可执行文件名等潜在 IOC，以及 Base64、Hex、StrReverse 等混淆手法。CTF 中常用于从宏代码里提取 flag、密码、隐藏的 Payload。

### 4. 补充说明

olevba 是详细分析器，与 mraptor（快速筛选器）配合使用：先用 mraptor 快速判断是否可疑，再用 olevba 深入分析源码。olevba 支持的格式覆盖传统 .doc/.xls/.ppt 和现代 .docm/.xlsm/.pptm，以及 OOXML 中的 vbaProject.bin。

## 三、oleobj

### 1. 工具定位

oleobj 是恶意文档分析中非常实用的工具，专门解析并提取 Office 文件中存储的 OLE 对象。支持包括 .doc/.xls/.ppt 和 .docx/.xlsx/.pptx 等多种 Office 容器。

### 2. 核心命令及参数

oleobj challenge.doc

直接跟文件路径，自动列出并提取嵌入对象到当前目录。

### 3. 应用场景

Office 文件里可能嵌入 exe、zip、pdf、doc、xls、脚本、图片、另一个 OLE 文件。典型结构：

Word

└─ Object

└─ payload.exe

**分析流程：** 发现 Embedded Object → oleobj 提取 payload / 附件 → 用 file /strings/binwalk 继续分析。CTF 中常见题目把 flag.zip、flag.txt、另一层隐写图片嵌入 Office 文档，oleobj 是提取的关键工具。

### 4. 补充说明

oleobj 处理的是 Office OLE Object；如果文件是 RTF 格式，更推荐用专门的 rtfobj 而非 oleobj，因为 rtfobj 自带的 RTF parser 专门考虑了恶意 RTF 的混淆情况。oleobj 对现代 OOXML（.docx/.xlsx/.pptx）中的嵌入对象同样支持。

## 四、rtfobj

### 1. 工具定位

rtfobj 专门检测和提取 RTF 中的 OLE Object、OLE Package、嵌入文件。它自带的 RTF parser 专门考虑了恶意 RTF 的混淆情况，比通用 oleobj 更适合 RTF 格式。

### 2. 核心命令及参数

rtfobj challenge.rtf                    # 查看所有对象列表

rtfobj -s 2 challenge.rtf               # 提取 Object 2

rtfobj -s all challenge.rtf             # 全部提取

rtfobj -s all -d output challenge.rtf   # 指定输出目录

**参数：** -s = select（选择对象编号或 all），-d = output directory（输出目录）。

### 3. 应用场景

文件是 .rtf 时优先使用。先 rtfobj challenge.rtf 可能看到 Object 0、Object 1、Object 2... 的列表，再按需提取指定对象或全部提取。RTF 题中常把恶意 OLE 对象、Payload、隐藏文件嵌入 RTF，rtfobj 能穿透 RTF 的混淆结构准确提取。

### 4. 补充说明

**记忆口诀：** Office OLE Object → oleobj，RTF Object → rtfobj。RTF 有专门的 parser 处理混淆（如十六进制编码、特殊字符转义），不要用 oleobj 代替 rtfobj 分析 RTF，否则可能漏提取或解析错误。

## 五、msodde

### 1. 工具定位

msodde 专门用于从 Office / RTF 等文件中检测并提取 DDE（Dynamic Data Exchange）/ DDEAUTO 链接。DDE 是 Office 程序之间交换数据的老机制，历史上被利用来从 Word/Excel 触发外部命令。

### 2. 核心命令及参数

msodde suspicious.doc

直接跟文件路径即可。

### 3. 应用场景

题目不是 VBA 而是 DDE/DDEAUTO 时使用。例如文档里存在：

DDEAUTO c:\windows\system32\cmd.exe "/c calc.exe"

msodde 就是针对这种东西的，能把 DDE 链接字段从文档中提取出来。官方支持 Word、Excel、RTF、CSV 和部分 XML Office 格式。CTF 中 DDE 字段里可能藏有 flag、命令、Base64 编码的 Payload。

### 4. 补充说明

**记忆口诀：** VBA → olevba，DDE → msodde。两者检测的是 Office 中不同的代码执行机制，不要混淆。有些文档同时存在 VBA 和 DDE，需要两个工具都跑一遍。msodde 是专门针对 DDE 的轻量工具，不做宏分析。

## 六、其他工具

| 工具 | 一句话定位 | 基本命令 | 备注 |
| --- | --- | --- | --- |
| mraptor | 快速判断 VBA 宏是否有恶意倾向的筛选器，核心规则 A AND (W OR X) | mraptor challenge.doc / -m 看匹配字符串 | A=AutoExec，W=Write，X=Execute；快速筛选器，olevba 是详细分析器 |
| pyxswf | 检测 / 提取 Office/RTF 中内嵌的 SWF/Flash | pyxswf -o challenge.doc / -f RTF / -x 提取 | 偏老式恶意文档，现代 CTF 频率低 |
| ftguess | 根据内容识别真实文件类型，不依赖后缀 | ftguess challenge.bin | 理解成 file 命令 + Office/OLE 专项识别，适合后缀伪造题 |
| olebrowse | GUI 浏览 OLE 内部 Storage/Stream，可 Hex View 或 Save 提取 | olebrowse challenge.doc | 直观理解 OLE 内部结构，比 oledir 偏可视化 |
| olemeta | 提取 OLE 文档标准属性（Author、Title、Create Time 等） | olemeta challenge.doc | Metadata≠绝对真实，可修改，作为线索而非结论 |
| oletimes | 查看 OLE 内部每个 Storage/Stream 的创建 / 修改时间 | oletimes challenge.doc | 与 olemeta（文档属性）不同，看的是各流时间戳 |
| oledir | 列出 OLE 目录项，含 Free/Orphaned Entry | oledir challenge.doc | 比 olebrowse 偏底层，分析删除 / 孤立项、目录结构异常 |
| olemap | 最底层工具，显示 OLE 所有 Sector 分布映射 | olemap challenge.doc | 普通 CTF 宏题一般用不到，用于结构异常、碎片化、隐藏数据、损坏文件分析 |
