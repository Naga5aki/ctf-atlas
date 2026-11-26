---
title: "SNOW隐写"
summary: "SNOW 全称为 Steganographic Nature Of Whitespace，是一种经典的文本隐写技术。"
module: "Misc"
topic: "文档与取证"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

SNOW 全称为 Steganographic Nature Of Whitespace，是一种经典的文本隐写技术。它把数据编码为行尾的空格和制表符，使文件的可见正文保持不变。主要用于 ASCII 文本，也可以处理源码、HTML、Markdown 等文本载体，前提是传输和编辑过程必须完整保留行尾空白。

## 一、核心原理

### 1. 隐藏位置

隐藏数据位于每行可见正文之后、换行符之前：

可见正文[Space/Tab 隐藏数据][CRLF 或 LF]

| 系统 | 换行字节 |
| --- | --- |
| Linux | 0A |
| Windows | 0D 0A |

真正承载数据的是换行符前面的：

空格 Space：20，可视化表现为空白

制表符 Tab：09，可视化表现为 \t、^I、箭头

### 2. SNOW 不是简单的空格转 0、Tab 转 1

标准 SNOW 使用专门的紧凑编码：

一个附加在行尾的 Tab 表示隐藏数据开始

数据按每 3 bit 一组处理

每组经过位序转换后，映射为 0～7 个空格

Tab 用于分隔这些空格组

数据可跨越多行继续存储

### 3. 标准处理流水线

**隐藏时：**

原始数据 → 可选静态 Huffman 编码 → 可选 ICE 加密 → SNOW 空白编码 → 写入行尾

**提取时：**

行尾空白 → SNOW 解码 → 可选 ICE 解密 → 可选 Huffman 解码 → 原始数据

标准 SNOW 没有可靠的文件头、密码正确标记或完整性校验。因此，工具成功运行不等于结果一定正确。

## 二、压缩机制

### 1. -C 的真实含义

-C 使用的是 SNOW 内置的固定 Huffman 编码表，主要针对英文文本优化。它不是 gzip、zlib、ZIP、DEFLATE 等通用文件压缩算法。

对于英文文本可能缩小数据

对于二进制、中文 UTF-8、压缩包、图片或高熵数据，可能没有效果，甚至使数据变大

### 2. 参数必须匹配

| 嵌入方式 | 提取方式 |
| --- | --- |
| 未使用 -C | 不加 -C |
| 使用了 -C | 必须加 -C |

错误使用 -C 有时不会直接报错，反而可能产生 "看起来像英文" 的垃圾内容。因此，不能只凭可打印率判断结果正确。

### 3. 与二次压缩区分

如果提取结果本身是 gzip 文件：

file extracted.bing

zip -dc extracted.bin > payload.bin

这属于隐藏数据的第二层处理，与 SNOW 的 -C 无关。

## 三、密码保护

SNOW 使用 ICE 算法的 1-bit CFB 模式加密。密码最长约 1170 个字符，但经典实现实际上按密码字节处理，并且只使用每个字节的低 7 位。

重要考点

SNOW 没有密码正确性校验，错误密码通常也会生成输出，只是内容错误

密码和 -C 可以同时使用

中文等非 ASCII 密码可能存在跨平台编码差异：Kali 通常传入 UTF-8 字节，而旧版 Windows snow.exe 可能使用本地代码页；同一个肉眼可见密码，在不同系统中不一定生成相同密钥

实战中优先使用 ASCII 密码；如果题目明确给出中文密码而 Windows 与 Kali 结果不同，应考虑密码字节编码差异

## 四、识别方法

### 1. 常见题目特征

出现以下情况时可优先怀疑 SNOW：

文件属于 TXT、源码、HTML、Markdown 等文本格式

可见正文完全正常

题目提示包含 snow、white、space、tab、invisible、空白、雪等词语

行尾存在大量空格和 Tab

文件大小明显大于纯正文内容

"存在行尾空白" 只能作为线索，不能单独证明一定是 SNOW。

### 2. 标准 SNOW 的较强特征

比 "存在行尾空白" 更可靠的特征：

某处行尾以 Tab 开始隐藏区

后续出现由 Tab 分隔的空格组

每个空格组通常不超过 7 个空格

结构连续分布在多行

使用 stegsnow 能够稳定提取数据

如果出现超过 7 个空格的编码组并报告 Illegal encoding，可能是数据损坏、自然行尾空白或自定义算法。

## 五、核心参数及命令

| 参数 | 作用 |
| --- | --- |
| 无 -m/-f | 进入提取模式 |
| -C | 隐藏时 Huffman 编码，提取时 Huffman 解码 |
| -p PASSWORD | 使用密码加密或解密 |
| -m MESSAGE | 隐藏命令行字符串 |
| -f FILE | 隐藏指定文件，可包含二进制数据 |
| -S | 估算载体容量 |
| -l LENGTH | 设置嵌入后的行宽限制，默认 80 |
| -Q | 静默模式，不显示统计信息 |
| -h | 显示帮助 |
| -V | 显示版本 |

### 1.提取命令：

基本提取

\# 无压缩、无密码

stegsnow carrier.txt extracted.bin

\# 使用 SNOW 内置 Huffman 编码

stegsnow -C carrier.txt extracted.bin

\# 使用密码

stegsnow -p 'password' carrier.txt extracted.bin

\# 压缩和密码同时使用

stegsnow -C -p 'password' carrier.txt extracted.bin

不要一开始使用 -Q，因为残留 bit、Huffman 异常等提示具有分析价值。

### 2.容量考点：

\# 查看估算容量

stegsnow -S carrier.txt

\# 指定行宽

stegsnow -S -l 72 carrier.txt

**容量主要受以下因素影响：** 载体行数、各行当前长度、-l 设置的行宽、Tab 所跨越的列数、是否使用 Huffman 编码。

-S 估算的是空白信道容量，其他选项基本不会参与该估算。

容量不足不一定立即失败。经典 SNOW 可能额外添加新行继续写入，只是这样更容易暴露。因此，-S 更准确的含义是估算 "在现有载体结构中、不明显增加额外行时" 的可用容量。

### 3.嵌入命令：

\# 隐藏字符串

stegsnow -m 'hidden message' cover.txt stego.txt

\# 隐藏文件

stegsnow -f payload.bin cover.txt stego.txt

\# 压缩并加密

stegsnow -C -p 'password' -f payload.txt cover.txt stego.txt

\# 限制行宽

stegsnow -l 72 -m 'hidden message' cover.txt stego.txt

\# 估算容量

stegsnow -S -l 72 cover.txt

输入文件与输出文件应使用不同名称，避免破坏载体原件。

## 六、损坏与失效原因

最容易破坏 SNOW 数据的操作包括：

编辑器自动删除行尾空白

将 Tab 自动转换为空格

对代码执行格式化

邮件客户端自动换行

Markdown、网页或聊天软件清理尾空白

复制粘贴时丢失 Tab 或行尾空格

Git 钩子或 EditorConfig 启用了 trim_trailing_whitespace

使用 expand、unexpand 等工具转换 Tab

文本重新排版、合并行或拆分行

常见异常排查

| 异常现象 | 可能原因 |
| --- | --- |
| 完全没有输出 | 文件不是 SNOW 隐写；行尾空白已被清理；没有作为起始标记的行尾 Tab；使用的是自定义空白编码 |
| 输出是乱码 | 错误添加或遗漏 -C；密码错误；中文密码编码差异；输出本来就是二进制文件；数据被部分破坏 |
| 前半正常、后半乱码 | 后半部分行尾空白被修改；文件被截断；某些 Tab 被替换为空格；邮件或编辑器在中间自动换行 |
| 错误密码也得到可打印内容 | 正常现象。SNOW 没有认证标签，错误密码或错误 -C 组合可能偶然产生可打印字符，必须结合 flag 格式、文件 magic 和结构验证 |
| Windows 与 Kali 结果不同 | 密码含中文或特殊字符时优先检查命令行编码，应尽量使用与出题工具相同的平台或准确复现其密码字节序列 |
