---
title: "PDF弱密码爆破"
summary: "PDF 加密题首先要分清打开密码（User Password）和权限限制（Owner Password / Permissions），两者处理方式完全不同。"
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

PDF 加密题首先要分清打开密码（User Password）和权限限制（Owner Password / Permissions），两者处理方式完全不同。

## 一、核心原理

两类密码的区别

| 密码类型 | 作用 | 表现 |
| --- | --- | --- |
| User Password | 用于打开 PDF | 双击 PDF 立即弹出密码框，不输入无法查看 |
| Owner Password | 控制打印、复制、修改等权限 | PDF 可能不输入密码也能正常打开，但不能复制 / 打印 / 编辑 |

二者最终都用于取得 PDF 的实际加密密钥。对于 "没有打开密码、只有权限限制" 的 PDF，常见情况是 User Password 实际为空字符串，所以 qpdf 可以直接取得密钥并输出无加密副本，而不是 "破解出了 Owner Password"。

处理方向判断

双击 PDF → 立即弹出密码框 → 不输入无法查看 → 优先考虑 User Password 弱密码恢复

PDF 能正常打开 → 不能复制 / 打印 / 编辑 → 优先考虑权限限制，不必先跑密码字典

不能死记 "CTF 的 PDF 密码一定弱、最多 8 位、90% 都在 rockyou"，这些没有可靠规律。正确原则是：有明确密码保护时先进行低成本字典攻击，失败后根据题目线索缩小候选空间，而不是盲目全空间暴力。

## 二、第一步：先判断是哪种保护

**检查加密信息：**

qpdf --show-encryption challenge.pdf

qpdf 支持查看 PDF 加密信息，PDF 标准加密可能使用旧式 RC4，也可能使用 AES（256-bit PDF 加密使用 AES）。

**情况一：** PDF 不需要密码就能打开

如果只是禁止复制、打印、编辑，先尝试：

qpdf --decrypt challenge.pdf output.pdf

--decrypt 的作用是创建一个不再加密的输出 PDF。如果原文件的 User Password 为空，qpdf 可以直接处理。然后用 PDF 阅读器打开 output.pdf。

**情况二：** PDF 真正需要打开密码

如果没有密码就无法打开（User Password 未知），qpdf --decrypt 并不能凭空破解密码。如果已经知道密码：

qpdf --password='123456' --decrypt challenge.pdf output.pdf

不知道密码就进入弱密码恢复。

## 三、pdfcrack：Kali 下优先尝试

pdfcrack 是专门用于 PDF 密码恢复的命令行工具，支持字典攻击、字符集暴力、指定密码长度、保存 / 恢复破解进度、User/Owner Password 选择。

### 1. 首选：rockyou 字典攻击

**开始攻击：**

pdfcrack -f challenge.pdf -w /usr/share/wordlists/rockyou.txt

-f：指定 PDF

-w：指定密码字典

**成功后通常显示：**

found user-password: '123456'

再用 qpdf 解密：

qpdf --password='123456' --decrypt challenge.pdf output.pdf

### 2. 已知字符集和长度时再暴力

例如题目提示密码为 6 位数字：

pdfcrack -f challenge.pdf -c 0123456789 -n 6 -m 6

-c：字符集

-n：最短密码长度

-m：最长密码长度

4～6 位数字：-n 4 -m 6；纯小写：-c abcdefghijklmnopqrstuvwxyz。

只有明确知道字符集和长度范围时才适合这样做。

### 3. 中断后恢复

| 原错误说法 | 正确含义 |
| --- | --- |
| -n 4 = 4 线程 | -n = 最小密码长度 |
| -c = 继续上次任务 | -c = 指定字符集 |

经典 pdfcrack 并没有多线程选项，其项目 FAQ 明确说明传统版本本身不支持 multicore/multi-CPU 并行。

运行过程中按 Ctrl + C，pdfcrack 会自动保存 savedstate.sav，恢复：

pdfcrack -f challenge.pdf -l savedstate.sav

-l = load state，这是官方定义的恢复方式。

## 四、Passware Kit：Windows GUI 方案

Passware Kit Forensic 支持 PDF 在内的数百种受密码保护文件，支持字典、组合攻击以及部分格式的 GPU / 多机加速。

大致流程

打开 Passware Kit → 添加 challenge.pdf → 软件识别加密类型

→ 进入 Password Recovery → 优先配置 Dictionary Attack

→ 导入 rockyou.txt → 开始恢复

攻击策略选择

题目明确 6 位数字 → 不要继续用大型通用字典，设置 Brute Force：Character set 0-9，Length 6

提示用户名 + 年份、比赛名 + 数字、文件名 + 数字 → 使用字典 + 规则 / 组合攻击

Passware 支持 GPU 加速，但实际加速比例取决于 PDF 加密版本、GPU 和攻击类型，不能固定认为 "必然比 pdfcrack 快 2～3 倍"。

## 五、CTF 中正确的密码攻击顺序

不要上来就 8 位大小写 + 数字 + 特殊字符全空间暴力，应按成本从低到高：

加密 PDF

↓

确认 User / Owner 保护

↓

能直接打开？

├─ 是 → qpdf --decrypt（权限限制）

└─ 否 → User Password 未知

↓

题目明显线索（常用密码/文件名/比赛名/日期/ID）

↓

rockyou.txt

↓

规则化字典

↓

已知字符集+长度才暴力

## 六、PDF 加密版本兼容性坑

不要认为 pdfcrack = 所有 RC4、AES-128、AES-256 都能稳定秒跑。PDF 加密存在多个 V/R revision，从旧式 40-bit RC4、128-bit RC4/AES 到现代 256-bit AES，算法差异很大（qpdf 文档列出 V=1~5、R=2~6 等不同标准安全处理器版本）。

遇到 pdfcrack 无法识别、解析报错、长时间没有正常状态，不一定是密码太强，也可能是 PDF 加密版本 / 结构兼容性问题。这时可以换 John the Ripper、Hashcat、Passware Kit 等工具，而不是一直卡在 pdfcrack。

## 七、实战避坑汇总

| 错误认知 | 正确结论 |
| --- | --- |
| qpdf 是 User Password 爆破工具 | qpdf 适合检查、解密已知密码 PDF 和处理空 User Password 的权限限制，不能凭空破解密码 |
| -n 4 是四线程 | -n 4 = 最短密码 4 位，pdfcrack 传统版本不支持多线程 |
| -c 是恢复任务 | -c = 指定字符集，恢复用 -l savedstate.sav |
| CTF 密码最多 8 位 | 无可靠规律，应根据题目线索判断 |
| 90% 一分钟出结果 | 无可靠规律 |
| 所有 PDF 都能用 pdfcrack 解决 | 加密版本兼容性问题时需换 John/Hashcat/Passware |
| 字典失败就直接全空间暴力 | 字典失败后先分析题目线索，明确长度和字符集后再穷举 |
| 可以上传到在线 PDF 解密网站 | 比赛和取证场景尽量使用本地工具，避免文件外泄和违反赛题要求 |
