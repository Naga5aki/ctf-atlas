---
title: "zip/rar常见报错及修复方法"
summary: "zip/rar常见报错及修复方法"
module: "Misc"
topic: "压缩与口令"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、ZIP常见报错与修正

| 常见报错/现象 | 常见原因 | Misc修正思路 |
| --- | --- | --- |
| End-of-central-directory signature not found | EOCD 50 4B 05 06缺失、被改坏、文件被截断、提取长度不足 | 找CDH/EOCD；补完整ZIP；必要时zip-FF重建目录 |
| central directory corrupt/bad central directory | CDH损坏、CDH与LFH信息不一致 | 对比LFH 50 4B 03 04与CDH 50 4B 01 02，修长度、CRC、标志位 |
| 解压时突然要求密码 | 真加密或伪加密 | 比较LFH/CDH的General Purpose Bit Flag bit0 |
| bad CRC/CRC failed | 文件数据损坏、CRC字段被改、密码错误 | 先判断数据是否完整；若仅CRC被篡改可修CRC；真损坏则需恢复数据 |
| unexpected end of file/unexpected EOF | ZIP被截断、dd少提了数据、分卷缺失 | 找真实归档结束位置，重新提取；检查.z01/.z02/.zip |
| extra bytes at beginning or within zipfile | ZIP前面有图片/文本等载体，属于嵌入ZIP | 通常不是致命错误；定位真正50 4B 03 04后dd分离 |
| invalid compressed data | 压缩流损坏、压缩方法字段被改 | 检查LFH/CDH Compression Method与压缩数据 |
| unsupported compression method | 方法字段异常或确实用了工具不支持的方法 | 对比LFH/CDH的Method；被人为修改则修回 |
| 文件列表正常但某个文件不能解 | 某个Local Header/数据块损坏 | 针对该文件的LFH、数据、CRC分析 |
| cannot find zipfile directory | 中央目录缺失 | 尝试从Local Header恢复，或zip-FF |
| 解压出来文件大小异常 | Compressed/Uncompressed Size被改 | 对比LFH、CDH和实际数据 |
| 只能解部分文件 | 后半段截断、某个Header被破坏 | 沿ZIP结构逐条检查LFH |

## 二、RAR常见报错与修正

| 报错/现象 | 常见原因 | Misc修正思路 |
| --- | --- | --- |
| Cannot open as archive | 文件头损坏、RAR魔数错误 | 修RAR4/RAR5文件头 |
| Unexpected end of archive | 文件截断、分卷缺失 | 补齐数据或分卷 |
| CRC failed/Checksum error | 数据损坏、密码错误、CRC被改 | 判断是真损坏还是字段篡改 |
| File header broken | RAR4 File Header损坏、HEAD_CRC错、HEAD_TYPE被改 | 检查74、HEAD_FLAGS、HEAD_SIZE、HEAD_CRC |
| Headers Error | 块头结构或CRC错 | 找具体损坏Header修复 |
| 要求密码 | 真加密、标志异常、Header Encryption | 判断RAR4/RAR5和具体加密结构 |
| 文件明明存在却不显示 | File Header被伪装成Service Header | RAR4检查74→7A |
| Next volume is required | 分卷RAR缺失 | 补齐.part*.rar/.r00等 |
| Data error | 压缩数据损坏或缺失 | 检查数据区、分卷、大小字段 |
| 解压工具显示空压缩包 | Main/File Header被破坏或伪装 | 直接解析RAR块结构 |

## 三、常用诊断工具

ZIP工具集

| 命令 | 作用 |
| --- | --- |
| file test.zip | 识别基础格式 |
| binwalk test.zip | 扫描内部结构与嵌入文件 |
| unzip-t test.zip | 测试解压完整性与CRC |
| zipinfo-v test.zip | 查看归档详细元信息 |
| zipdetails test.zip | 输出LFH/CDH/EOCD全量字段细节 |
| 7z t test.zip | 测试归档完整性 |

RAR工具集

| 命令 | 作用 |
| --- | --- |
| file/binwalk test.rar | 格式识别与结构扫描 |
| unrar l test.rar | 列出压缩包内文件 |
| unrar t test.rar | 测试归档完整性 |
| 7z l/7z t test.rar | 列表与完整性测试 |
| rar r test.rar | 利用恢复记录修复损坏 |
