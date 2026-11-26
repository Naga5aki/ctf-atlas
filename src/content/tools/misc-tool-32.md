---
title: "zip2john/rar2john"
summary: "zip2john 与 rar2john 是 John the Ripper Jumbo 密码破解套件的配套工具，分别适配 ZIP、RAR 格式的加密压缩包。"
module: "Misc"
topic: "压缩与口令"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

zip2john 与 rar2john 是 John the Ripper Jumbo 密码破解套件的配套工具，分别适配 ZIP、RAR 格式的加密压缩包。二者本身不具备密码爆破能力，核心作用是从加密压缩包的文件头中提取密码校验哈希，输出为 John the Ripper 可识别的标准格式，将压缩包在线密码破解转化为离线哈希爆破任务。

## 二、核心命令

| 工具名称 | 基础命令 | 功能说明 |
| --- | --- | --- |
| zip2john | zip2john target.zip > zip_hash.txt | 读取目标 ZIP 加密压缩包，提取其密码校验哈希，将结果保存到指定的哈希文件中 |
| rar2john | rar2john target.rar > rar_hash.txt | 读取目标 RAR 加密压缩包，提取其密码校验哈希，将结果保存到指定的哈希文件中 |

哈希提取完成后，可通过john hash.txt执行默认弱口令爆破，或通过john --wordlist=dict.txt hash.txt加载自定义字典定向爆破。

## 三、应用场景

### 1.真加密压缩包离线爆破

针对标准真加密的 ZIP/RAR 压缩包，先通过工具提取哈希，再搭配 John the Ripper 完成离线哈希爆破，相比 fcrackzip 等在线爆破工具效率更高，是弱口令加密压缩包的主流解法。

### 2.配合自定义字典定向爆破

当题目给出密码的字符范围、长度规则等线索时，可先用 crunch 生成符合规则的定制字典，再通过 John 加载字典对提取出的哈希执行定向爆破，缩小破解范围、提升破解成功率。

### 3.批量筛查加密压缩包

针对包含多个压缩包的复杂题型，可批量对目录下的 ZIP/RAR 文件执行哈希提取，快速筛选出带有有效加密哈希的文件，单独开展后续破解，提升排查效率。

## 四、补充点

### 1.格式适配限制

仅支持传统标准加密的 ZIP、RAR 格式，其中 rar2john 可适配 RAR3、RAR5 两个版本的加密格式，新式高强度非标准压缩加密无法提取有效哈希。

两个工具格式严格对应，不可混用，rar2john 无法处理 ZIP 文件，zip2john 也无法解析 RAR 文件。

### 2.工具边界说明

仅负责哈希提取，本身无密码破解能力，必须配合 John the Ripper 或 hashcat 等爆破工具使用。

导出的哈希文件不可手动修改内容、调整格式，否则会导致爆破工具无法正常识别解析。

伪加密压缩包无法生成有效哈希，这是快速识别伪加密的核心特征。
