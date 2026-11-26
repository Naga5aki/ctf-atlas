---
title: "pngcheck"
summary: "出题套路： 篡改 PNG 头部 IHDR 区块的宽 / 高数值且不更新 CRC，导致图片显示不全、黑屏，flag 藏在未渲染区域"
module: "Misc"
topic: "图像与视觉"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、核心实战参数

| 参数命令 | 功能说明 |
| --- | --- |
| pngcheck <文件> | 基础检测，校验 PNG 文件 CRC 校验值、整体结构完整性，输出结构报错信息 |
| pngcheck -v <文件> | 详细输出模式，罗列所有 Chunk 区块信息，可识别尾部冗余数据、自定义异常区块 |
| pngcheck -7 <文件> | 读取 PNG 内置 tEXt、zTXt 等文本区块，直接提取其中隐藏的明文字符串 |
| pngcheck -f <文件> | 强制解析模式，跳过轻微格式错误，支持破损、残缺 PNG 文件的检测 |

## 二、六大核心应用场景

场景 1：IHDR 宽高篡改

**出题套路：** 篡改 PNG 头部 IHDR 区块的宽 / 高数值且不更新 CRC，导致图片显示不全、黑屏，flag 藏在未渲染区域

**检测命令：** pngcheck target.png

**关键特征：** 返回 CRC error in chunk IHDR

场景 2：文本块隐藏信息

**出题套路：** 在 tEXt、zTXt 等标准文本区块写入 flag、解密密钥、提示信息，常规看图软件无法读取

**检测命令：** pngcheck -7 target.png

**关键特征：** 直接输出区块内的明文内容

场景 3：尾部文件捆绑

**出题套路：** 在 PNG 标准结束块 IEND 之后，拼接压缩包、文本、其他文件等隐藏附件

**检测命令：** pngcheck -v target.png

**关键特征：** 返回 extra data after IEND

场景 4：残缺 PNG 修复

**出题套路：** 人为删除 IEND 结束块、截断 IDAT 图像数据，导致图片损坏无法打开

**检测命令：** pngcheck target.png / pngcheck -f target.png

**关键特征：** 提示 missing IEND chunk 或 IDAT truncated

场景 5：自定义异常区块

**出题套路：** 插入非标准私有 Chunk 区块，藏匿密文、编码数据，常规工具无法识别

**检测命令：** pngcheck -v target.png

**关键特征：** 出现非 PNG 官方标准的陌生区块名称

场景 6：IDAT 数据篡改

**出题套路：** 修改 IDAT 核心像素数据并破坏 CRC，用于埋藏 LSB 隐写、加密载荷

**检测命令：** pngcheck target.png

**关键特征：** 返回 CRC error in chunk IDAT

## 三、关键注意事项

仅支持 PNG 格式，不适用于 JPG、GIF 等其他图片格式

所有 CRC 报错均为题目刻意设计的突破口，并非随机文件损坏

无法打开的损坏 PNG，优先加-f参数强制解析

是 PNG 结构题的首选筛查工具，优先级高于所有隐写分析软件
