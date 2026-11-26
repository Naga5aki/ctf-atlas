---
title: "Libreoffice"
summary: "在 Kali 里，LibreOffice 最适合定位为 \"Office 文件的可视化查看、验证和格式转换工具\"，而不是主分析器。"
module: "Misc"
topic: "文档与取证"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

在 Kali 里，LibreOffice 最适合定位为 "Office 文件的可视化查看、验证和格式转换工具"，而不是主分析器。做 CTF / 取证时，它最实用的地方是：打开 Word/Excel/PPT、检查隐藏内容、验证解密结果、批量转换格式，以及用只读模式安全查看。Kali Rolling 当前仓库直接提供 LibreOffice。

**完整安装：** sudo apt update && sudo apt install libreoffice

**查看版本：** libreoffice --version

完整套件包括 Writer、Calc、Impress、Draw、Base、Math 等组件

对 CTF 来说，最值得掌握的四件事：

--view 安全查看原题

Calc 检查 Excel 隐藏内容

Impress/Writer 检查视觉对象

--headless --convert-to 做批量转换

这四项和 oletools + msoffcrypto-tool + John/Hashcat 配合起来，Office 类题的工作流就比较完整了。

## 二、核心命令及参数

| 用途 | 命令 | 参数说明 |
| --- | --- | --- |
| 正常启动 | libreoffice | 启动 LibreOffice 主界面 |
| 打开文件 | libreoffice challenge.docx | 直接打开指定文件 |
| 指定组件启动 | libreoffice --writer challenge.docx | --writer / --calc / --impress / --draw 等 |
| 只读查看（推荐） | libreoffice --view challenge.docx | 以 viewer /read-only 模式打开，防止误修改原题 |
| 无界面格式转换 | libreoffice --headless --convert-to pdf challenge.docx | --headless 无 GUI 运行；--convert-to 指定目标格式 |
| 指定输出目录 | libreoffice --headless --convert-to pdf --outdir output challenge.docx | --outdir 指定输出目录 |
| 批量转换 | libreoffice --headless --convert-to pdf *.docx | 支持通配符批量处理 |
| 转文本 | libreoffice --headless --convert-to txt challenge.docx | 提取纯文本，图片 / 复杂布局可能丢失 |
| 文本直接输出终端 | libreoffice --cat challenge.docx | 文本过滤器直接输出到终端，隐含 headless 模式；可配合 grep |
| 安全模式 | libreoffice --safe-mode | 临时使用新用户配置，排查启动 / 配置故障（非恶意文档沙箱） |
| 查看版本 | libreoffice --version | 显示当前安装版本 |

## 三、应用场景

### 1. CTF 最推荐：先用只读模式打开

面对来源未知的 Office 文件，推荐：

libreoffice --view challenge.docx

**两个实际好处：** 不容易误修改原题文件 + 适合只做视觉检查。

只读 ≠ 安全沙箱。它只是限制编辑，不代表未知文档里的所有主动内容都天然安全。可疑宏文档仍应先 oleid → olevba → oleobj / msodde 静态分析，再考虑 LibreOffice。LibreOffice 官方提供宏安全设置，会针对包含未受信任宏的文档显示安全警告。

### 2. Word 题（Writer）

libreoffice --view challenge.docx

**重点检查：** 正文、页眉 / 页脚、文本框、图片、超链接、批注、隐藏文字、对象、分页区域、异常字体颜色、白字白底。

**典型情况：** 肉眼正文没有 flag → Ctrl+A 全选 → 改变字体颜色 / 背景 → 发现白色文字

善用 View / 视图 → Navigator / 导航器，快速查找图片、表格、文本框、章节、书签、对象

如果文档存在宏，不要因为弹出宏提示就启用，先退出来用 oleid / olevba 分析

**宏安全级别配置：** Tools → Options → LibreOffice → Security → Macro Security（官方四档）

### 3. Excel 题（Calc，价值通常比 Writer 更大）

libreoffice --view challenge.xlsx

**重点检查：** 工作表、隐藏工作表、隐藏行、隐藏列、公式、单元格格式、字体颜色、背景颜色、批注、超链接、命名区域、图片 / 对象。

查隐藏 Sheet：底部工作表标签不完整时，查看工作表相关菜单尝试显示隐藏工作表。CTF 常见 Sheet1 正常内容，Sheet2 被隐藏 → flag

**查隐藏行列：** 行号 1 2 3 8 9 说明 4~7 行可能隐藏；列 A B C H I 说明中间列可能被隐藏

**看公式：** 最值得检查公式栏。单元格视觉显示 123，实际公式可能是 =CHAR(102)&CHAR(108)&CHAR(97)&CHAR(103)（即 flag）。Excel 题不能只看显示值，还要看公式本身

CSV 导出要谨慎：CSV 只保存当前工作表的数据，公式、格式以及其他工作表信息会丢失。不要一上来就把 XLSX 转 CSV 再分析，否则可能把真正考点丢掉

### 4. PowerPoint 题（Impress）

libreoffice --view challenge.pptx

**重点检查：** 每一页幻灯片、备注、被遮挡对象、隐藏文字、白色文字、页面外对象、背景图、图片叠层、对象排列。

CTF 常见：上层黑色矩形下面压着 flag。可以在编辑副本里选中上层对象 → 删除 / 移开，看看后面藏了什么

**建议保留原题：** cp challenge.pptx challenge_work.pptx，只编辑副本

### 5. 已知 Office 密码后验证

**标准组合流程：**

office2john / John → 得到密码 → msoffcrypto-tool → 得到正常 Office → LibreOffice → 肉眼查看

**例如：**

msoffcrypto-tool secret.xlsx decrypted.xlsx -p 123456

libreoffice --view decrypted.xlsx

LibreOffice 本身更适合做最后的验证、浏览、寻找隐藏内容，而不是负责破解密码。

### 6. 命令行格式转换（最实用能力）

\# DOCX/XLSX/PPTX → PDF

libreoffice --headless --convert-to pdf challenge.docx

\# 指定输出目录

mkdir output

libreoffice --headless --convert-to pdf --outdir output challenge.docx

\# 批量转换

libreoffice --headless --convert-to pdf --outdir pdf *.docx

\# Word → TXT（快速提取文本）

libreoffice --headless --convert-to txt challenge.docx

\# 文本直接输出到终端，配合 grep

libreoffice --cat challenge.docx | grep -i flag

--cat 会把文本类文档经过文本过滤器后直接输出到终端，隐含使用 headless 模式。只想快速看文本 → --cat；想完整视觉查看 → --view。转 TXT 只适合快速提取文本，图片、复杂布局、隐藏对象可能丢失，不能当完整取证方法。

### 7. PDF 的实战用途

LibreOffice Draw 可以打开很多 PDF 进行页面级编辑和查看：

libreoffice challenge.pdf   # 通常交给 Draw

**可辅助：** 选中文字、移动对象、查看页面、删除遮挡对象、提取图片、重新导出 PDF。

但这仍然是视觉层面的 PDF 处理。如果题目考 xref、stream、JavaScript、EmbeddedFile、增量更新、PDF Object、隐藏附件，不要用 LibreOffice 当主力，应该用 pdfid、pdf-parser、qpdf、peepdf、010 Editor。

## 四、补充说明

### 1. 故障时用 Safe Mode

如果出现 LibreOffice 打不开、启动卡死、插件配置损坏、界面异常，可以：

libreoffice --safe-mode

Safe Mode 会临时使用一个新的用户配置，并禁用部分可能导致故障的设置，用于排查启动和配置问题。

LibreOffice Safe Mode 主要是程序故障排查模式，不等于恶意文档安全沙箱。 这两个 "安全" 概念不要混淆。

### 2. 只读模式的边界

--view 只是限制编辑，不代表未知文档里的所有主动内容（宏、DDE、嵌入对象）都天然安全。面对可疑文档，仍应先做 oletools 静态分析，再决定是否用 LibreOffice 打开。

### 3. 宏安全设置

**路径：** Tools → Options → LibreOffice → Security → Macro Security，官方提供四档宏安全级别，会针对包含未受信任宏的文档显示安全警告。遇到宏提示不要随意启用。
