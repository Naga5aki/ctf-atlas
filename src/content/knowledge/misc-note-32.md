---
title: "ZIP嵌套结构已知明文攻击"
summary: "对于内层flag.zip：50 4B 03 04...flag.txt...50 4B 05 06都是普通ZIP结构。"
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

### 1.典型题目结构

flag.txt

↓压缩

flag.zip←内层ZIP，不加密

↓作为普通文件放入

outer.zip←外层ZIP：ZipCrypto+Store

### 2.核心逻辑

对于内层flag.zip：50 4B 03 04...flag.txt...50 4B 05 06都是普通ZIP结构。

对于外层outer.zip：flag.zip只是一个普通文件，其内部所有字节都会作为外层ZipCrypto的待加密明文。

虽然不知道flag.zip的完整内容，却知道它里面必然存在一些ZIP固定结构，这就产生了已知明文。

### 3.核心攻击模型

内层ZIP固定结构

↓我们可以预测

成为外层ZipCrypto明文

↓与外层密文形成明密文对

bkcrack恢复Keys

这种攻击真正利用的是文件格式的确定性，不是利用弱密码，也不是爆破密码。

## 二、最关键条件：外层必须是Store

### 1.Store模式

外层使用Store意味着flag.zip不会再次压缩：

内层flag.zip原始字节=外层ZipCrypto加密前字节

**因此可以准确判断：**

offset 0→50 4B 03 04

offset 30→内层第一个文件名

这些偏移关系不会发生变化。

### 2.Deflate模式（不可用）

flag.zip→Deflate压缩→压缩数据→ZipCrypto

此时ZipCrypto加密的已经不是50 4B 03 04...，而是一段Deflate压缩流。我们知道的ZIP头、文件名、EOCD都不能直接作为对应位置的已知明文使用。

| 外层压缩方式 | 能否使用嵌套结构已知明文攻击 |
| --- | --- |
| Store | ✅可以，偏移关系稳定 |
| Deflate | ❌不可以，压缩破坏了偏移对应关系 |

## 三、内层ZIP压缩方式不重要

假设flag.txt在内层flag.zip中使用Store或Deflate，都没关系。因为我们主要利用的是：

内层ZIP文件头

内层文件名

内层中央目录

内层EOCD

这些ZIP结构本身。

| 层级 | 压缩方式 | 影响 |
| --- | --- | --- |
| 内层ZIP | Store/Deflate均可 | 不影响攻击，利用的是ZIP结构本身 |
| 外层ZIP | 必须重点关注Store | Deflate会破坏偏移关系，攻击不可用 |

## 四、第一种攻击：内层ZIP文件头+文件名

### 1.标准ZIP第一个Local File Header结构

**固定头部长度：** 30 bytes

之后紧跟File Name

### 2.可预测内容

如果内层第一个文件叫flag.txt，则：

offset 0：50 4B 03 04（4字节）

offset 30：66 6C 61 67 2E 74 78 74=flag.txt（8字节）

### 3.为什么flag.txt只有8字节也可以攻击

bkcrack并不是简单要求必须连续12字节，而是可以组合多段已知明文：

flag.txt=8字节连续已知明文

50 4B 03 04=4字节已知明文

总计=12 bytes

**形成：**

offset 0→4 bytes

offset 30→8 bytes continuous

刚好适合攻击。

### 4.为什么文件名偏移通常是30

标准Local File Header固定部分：

| 字段 | 长度 |
| --- | --- |
| Signature | 4 |
| Version | 2 |
| Flags | 2 |
| Compression | 2 |
| Time | 2 |
| Date | 2 |
| CRC32 | 4 |
| Compressed Size | 4 |
| Uncompressed Size | 4 |
| Filename Length | 2 |
| Extra Length | 2 |
| 合计 | 30 bytes |

第一个Local Header位于offset 0时，Filename offset=30。这就是命令中-o 30的来源，不是经验值，而是ZIP结构决定的。

### 5.典型bkcrack用法

先生成明文文件（注意不要额外加入换行）：

printf"flag.txt">plain.txt

**然后执行攻击：**

bkcrack-C outer.zip-c flag.zip-p plain.txt-o 30-x 0 504b0304

| 参数 | 含义 |
| --- | --- |
| -C outer.zip | 外层加密ZIP |
| -c flag.zip | 被攻击的外层条目 |
| -p plain.txt | 已知明文文件 |
| -o 30 | flag.txt位于内层ZIP偏移30 |
| -x 0 504b0304 | 额外告诉bkcrack：offset 0=50 4B 03 04 |

攻击成功后输出三个内部Key。

6.010 Editor确认方法

打开一个正常ZIP，直接观察50 4B 03 04后的Local File Header字段：

Offset 0x00：50 4B 03 04

Offset 0x1E（=30）：66 6C 61 67 2E 74 78 74=flag.txt

比赛中遇到这类题，可以先自己制作一个类似ZIP，在010 Editor中观察一次，结构会非常直观。

## 五、第二种攻击：利用ZIP尾部EOCD

### 1.EOCD基本信息

End of Central Directory，中央目录结束记录

**Signature：** 50 4B 05 06

**标准最小EOCD长度：** 22 bytes

### 2.偏移计算

如果内层ZIP是普通单磁盘ZIP且没有ZIP Comment：

EOCD offset=内层ZIP大小-22

例如内层flag.zip大小387 bytes，则387-22=365，可推测offset 365→50 4B 05 06。

### 3.优势

甚至不需要知道内层文件名，只要确认：

里面是ZIP

知道内层ZIP总大小

结构比较标准

就可以利用。再结合offset 0的50 4B 03 04及其他已知字段，组成足够的已知明文。

### 4.EOCD方法的限制

不要死记size-22一定是EOCD，只有ZIP Comment Length=0时才成立。如果内层ZIP有Comment：

EOCD offset=file_size-22-comment_length

因此攻击前最好判断内层ZIP是否可能带Comment，CTF入门题通常没有。

## 六、真正的"长文件名"有什么作用

如果内层文件名aaaaaaaaaaaaaaaa.txt有足够长度，攻击会更简单，因为文件名本身位于offset 30且内容已知。例如连续aaaaaaaaaaaa已达到12字节，可直接利用-o 30进行已知明文攻击。

"长文件名"确实可以提升攻击便利性，但长文件名不是这个攻击成立的根本。真正根本的是：

内层ZIP结构可预测

外层Store保持原字节

外层ZipCrypto加密这些字节

## 七、最重要的层级关系：内层文件名vs外层文件名

**假设：**

outer.zip

└──flag.zip

└──flag.txt

| 名称 | 所属层级 | 能否作为外层ZipCrypto已知明文 |
| --- | --- | --- |
| flag.zip | 外层ZIP的Filename字段（外层元数据） | ❌不可以 |
| flag.txt | 内层flag.zip的Filename字段，但从外层看属于flag.zip文件内容的一部分 | ✅可以 |

flag.zip是外层ZIP元数据，不被外层ZipCrypto加密，不能当作已知明文。

flag.txt是内层ZIP的内容，会被外层ZipCrypto加密，因此可以作为外层已知明文。

## 八、与普通文件头攻击的区别

| 攻击类型 | 外层加密内容 | 利用的已知明文 |
| --- | --- | --- |
| 普通已知文件头攻击 | PNG | 89 50 4E 47... |
| ZIP嵌套结构攻击 | 一个完整ZIP | 50 4B 03 04、Filename、Central Directory、EOCD |

ZIP嵌套结构攻击可以认为是文件格式已知明文攻击的一种特殊且非常稳定的形式。

## 八、三种常见利用方式

| 方式 | 原理 | 适用场景 |
| --- | --- | --- |
| 内层文件名攻击 | offset 30→flag.txt，组合offset 0→50 4B 03 04 | 最常见，知道内层文件名 |
| 长文件名直接攻击 | 内层文件名本身足够长（如this_is_flag.txt），直接提供大段连续已知明文 | 内层文件名较长 |
| ZIP尾部结构攻击 | 利用50 4B 05 06及EOCD中可推测的字段 | 不知道内层文件名，但知道内层就是ZIP |
