---
title: "rar爆破方法"
summary: "RAR主要分为两个大版本体系，加密结构、签名、爆破模式均不相同："
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、基础认知与格式区分

### 1.两大格式族

RAR主要分为两个大版本体系，加密结构、签名、爆破模式均不相同：

| 格式族 | 文件头签名（十六进制） | 工具通用叫法 |
| --- | --- | --- |
| RAR 3.x/4.x | 52 61 72 21 1A 07 00 | RAR3 |
| RAR 5.x | 52 61 72 21 1A 07 01 00 | RAR5 |

### 2.两种加密模式（RAR3）

RAR3存在两种加密强度，直接影响「能否看到文件名」：

普通数据加密（-p）：仅加密文件数据，文件头可见，能正常列出文件名，解压时才要求密码。这是正常的真加密行为，不是伪加密。

全加密（-hp）：同时加密文件数据与文件头，打开压缩包就需要密码，无法直接查看文件名。

对应rar2john输出标识：

$RAR3$*0*→对应-hp全加密

$RAR3$*1*→对应-p普通数据加密

### 3.伪加密认知纠正

RAR伪加密没有ZIP那样统一简单的标志位修改方案，RAR3与RAR5结构差异极大，不能照搬ZIP「改一个bit就恢复」的思路。

怀疑伪加密时，需结合版本、头结构、加密字段、头CRC、工具行为综合判断，不能仅凭「要密码但能看文件名」就定性。

### 4.分卷缺失排查

拿到文件先判断是否为分卷压缩：

**常见命名：** flag.part1.rar/part2.rar或老式flag.rar/flag.r00/flag.r01

若提示「Next volume required」「Unexpected end of archive」，优先排查是否缺少分卷，而非直接怀疑密码。

可通过binwalk检查图片、音频等其他载体尾部是否藏有分卷数据。

## 二、爆破核心原理

主流密码恢复工具不会反复调用解压程序测试密码，而是采用离线哈希爆破方案：

从RAR中提取salt、加密验证数据、密文片段，生成标准格式的哈希

在内存中高速批量验证候选密码，无需反复读写文件、启动进程

得到候选密码后，再用解压工具实际验证

**标准流程：**

RAR文件→rar2john提取哈希→John/Hashcat离线爆破→实际验证密码→解压分析

## 三、首选方案：rar2john+John the Ripper

### 1.哈希提取

基础命令

rar2john flag.rar>hash.txt

通过输出前缀可直接判断版本：

$RAR3$...→RAR3系列

$rar5$...→RAR5

支持范围

支持RAR3、RAR5、SFX自解压RAR；不支持过老的史前版本。

### 2.常用攻击模式

（1）字典攻击

john--wordlist=words.txt hash.txt

rockyou.txt是通用首轮弱密码字典，但不能假设大多数题目密码都在其中。

CTF优先使用根据题目线索生成的定制字典，命中率远高于通用字典。

（2）规则攻击

john--wordlist=words.txt--rules hash.txt

对字典中的单词自动做大小写、加数字后缀、常见变形等扩展，用较小字典覆盖更多可能性。

（3）掩码攻击

已知密码结构时使用，精准控制搜索空间。

**内置占位符：**

?l：小写字母a-z

?u：大写字母A-Z

?d：数字0-9

?s：ASCII特殊字符

?a：全部可打印ASCII

**示例：** 4位纯数字密码

john--mask='?d?d?d?d'hash.txt

**易错提醒：** ?a包含全部可打印字符，搜索空间远大于「字母+数字」，无明确依据时不要滥用。

### 3.结果与状态管理

**查看已破解密码：**

john--show hash.txt

**长任务命名会话支持断点：**

#开始任务并命名会话

john--session=rar_ctf--mask='?d?d?d?d?d?d'hash.txt

#中断后恢复

john--restore=rar_ctf

#查看状态

john--status=rar_ctf

## 四、高性能方案：Hashcat

适合GPU环境、大字典、掩码与混合攻击，是大规模密码搜索的首选。

### 1.核心模式表（必须精准记忆）

这是最高频易错点，RAR3并非统一使用12500模式：

| 模式号 | 对应加密类型 |
| --- | --- |
| 12500 | RAR3-hp（全加密，对应-hp） |
| 23700 | RAR3-p，未压缩（Store） |
| 23800 | RAR3-p，已压缩 |
| 13000 | RAR5 |

### 2.哈希格式适配

rar2john的输出带有文件名前缀与额外字段，不能直接喂给Hashcat，需先提取纯哈希：

**RAR3：**

grep-o'\$RAR3\$[^:]*'john_hash.txt>hashcat.txt

**RAR5：**

grep-o'\$rar5\$[^:]*'john_hash.txt>hashcat.txt

### 3.常用攻击模式

（1）字典攻击（-a 0）

hashcat-m 13000-a 0 hashcat.txt words.txt

（2）掩码攻击（-a 3）

**基础示例：** 6位纯数字

hashcat-m 13000-a 3 hashcat.txt'?d?d?d?d?d?d'

**自定义字符集：** 通过-1~-4定义，?1引用

#小写字母+数字的6位密码

hashcat-m 13000-a 3-1'?l?d'hashcat.txt'?1?1?1?1?1?1'

**增量掩码：** 遍历1~6位长度

hashcat-m 13000-a 3--increment--increment-min=1--increment-max=6 hashcat.txt'?d?d?d?d?d?d'

（3）混合攻击

-a 6：字典+右侧掩码，适合「关键词+数字后缀」场景

hashcat-m 13000-a 6 hashcat.txt words.txt'?d?d?d?d'

-a 7：左侧掩码+字典

### 4.结果与状态管理

**查看已破解：**

hashcat-m 13000 hashcat.txt--show

**查看未破解：**

hashcat-m 13000 hashcat.txt--left

**断点恢复：**

#命名会话

hashcat-m 13000--session=rar_ctf-a 3 hashcat.txt'?d?d?d?d?d?d'

#恢复任务

hashcat--session=rar_ctf--restore

### 5.参数认知纠正

--remove：作用是从输入哈希文件中删除已破解的条目，不是「清除密码缓存」；CTF场景不建议使用，应保留原始哈希文件。

**性能对比：** Hashcat适合GPU加速，但不存在「固定比John快10~100倍」的结论，速度受格式、模式、硬件、实现版本影响；John Jumbo也支持OpenCL加速。

## 五、rarcrack工具认知

### 1.本质定位

轻量级暴力工具，本身不解析RAR加密结构，通过调用外部unrar/7z/unzip程序验证密码，性能远低于离线哈希爆破。

### 2.认知纠正

| 错误认知 | 正确结论 |
| --- | --- |
| 纯CPU单线程 | 支持--threads设置线程数 |
| 支持--wordlist字典攻击 | 无该参数，仅支持字符集递增暴力 |
| 代码层面绝对不支持RAR5 | 兼容性依赖外部安装的unrar版本，不保证稳定，RAR5仍首选John/Hashcat |

### 3.适用场景与优先级

仅适合极短密码、极小字符集的临时验证，大空间爆破效率极低。

**实战优先级：** John/Hashcat>>rarcrack

支持断点续跑，状态保存在archive.rar.xml文件中。

## 六、分卷RAR处理

提取哈希通常针对第一个分卷，加密元数据一般从首卷读取。

不能绝对化「永远只需要第一卷」：跨卷文件的完整数据、最终解压仍需完整分卷集合。

解压验证与后续分析必须准备齐全所有分卷。

## 七、常见报错与排查

| 现象 | 优先排查方向 |
| --- | --- |
| No password hashes loaded | 哈希格式错误、工具版本不兼容、文件实际未加密 |
| Hashcat Separator unmatched | rar2john输出未清理，哈希格式不符 |
| Hashcat No hashes loaded | 模式选错、哈希格式错误 |
| Unexpected end of archive | 文件截断、缺少分卷 |
| Next volume required | 缺少分卷 |
| CRC failed | 密码错误、数据损坏 |
| Mask跑完无结果 | 密码结构假设错误、模式选错 |
