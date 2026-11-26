---
title: "CVE-2023-28303截图工具漏洞"
summary: "CVE-2023-28303（Acropalypse）是一类 PNG 截图裁剪后残留数据泄露漏洞，最早影响 Microsoft 截图工具，后来也发现类似问题影响部分…"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

CVE-2023-28303（Acropalypse）是一类 PNG 截图裁剪后残留数据泄露漏洞，最早影响 Microsoft 截图工具，后来也发现类似问题影响部分 Android 截图工具。漏洞本质：截图工具裁剪图片时，只修改了图片显示范围（IHDR 宽高），没有正确清除原始 PNG 数据（IDAT），导致被裁剪区域仍然保存在文件内部。

## 一、漏洞原理

正常 PNG 结构

PNG 文件

├─ IHDR（图片宽高）

├─ IDAT（实际像素数据）

└─ IEND

裁剪后（存在漏洞）

PNG 文件

├─ IHDR（新的小图片尺寸）

├─ IDAT（仍可能包含原始完整图片像素）

└─ IEND

图片查看器根据 IHDR 的宽高显示裁剪后的区域，但 IDAT 中可能仍保存裁剪前完整图片数据，需要专用工具重新解析 IDAT 恢复隐藏区域。

## 二、两类主要泄露方式

### 1. IDAT 像素残留恢复

截图工具裁剪图片后更新了 IHDR 宽高，但没有重新生成干净的 IDAT，原始像素数据仍存在。因此显示尺寸 ≠ 实际保存像素数据。

例如原图 1920×1080，裁剪为 500×500，文件中 IHDR 是 500×500，但 IDAT 可能仍包含 1920×1080 数据。恢复工具通过分析 PNG 结构、IDAT 压缩数据、原始扫描行，重新生成完整图片。

**典型场景：** 图片表面正常、flag 被裁剪掉、zsteg/binwalk/strings 无结果、图片大小明显异常 → 直接使用 Acropalypse 恢复工具。

### 2. 文件尾空闲空间泄露（较早期）

部分截图工具保存文件时先申请固定大小空间，写入 PNG 数据后未清理剩余空间，导致 PNG 正常内容 + 文件尾残留数据（可能来自删除文件碎片、缓存数据、之前文件内容）。

**检查方式：** 010 Editor 打开 PNG → 跳到文件末尾 → 查看 IEND 之后内容；或 strings image.png 寻找 flag{、CTF{。

目前主流更偏向第一种 IDAT 恢复。

## 三、识别特征

图片特征

PNG 格式

看起来像普通截图

图片内容明显被裁剪

图片尺寸较小但文件体积异常大

flag 可能位于图片边缘区域

分析特征

常规方法 binwalk、strings、zsteg、StegSolve、LSB 分析均无有效结果。

题目提示

**常出现：** Acropalypse、CVE-2023-28303、截图漏洞、Snipping Tool、裁剪恢复。

## 四、工具使用方法

### 1. Acropalypse 恢复工具（核心）

**常用工具：** Acropalypse-Multi-Tool，目录结构通常包含 acropalypse.py、gui.py、requirements.txt。

**核心恢复命令：**

python acropalypse.py --restore --input challenge.png --output restored.png --preset windows_snipping_tool

| 参数 | 含义 |
| --- | --- |
| --restore | 恢复模式 |
| --input | 输入漏洞图片 |
| --output | 输出恢复图片 |
| --preset | 截图工具类型 |

常用 preset：

Windows 截图工具：--preset windows_snipping_tool

Google Pixel：--preset pixel_7

恢复成功后 restored.png 就是尝试恢复出的完整图片。

### 2. 恢复失败排查

① 检查截图工具类型（最常见失败原因）

preset 错误会导致恢复失败，例如 Windows 截图误用 --preset pixel_7，应改为 --preset windows_snipping_tool。

② 不要修改原始 PNG

**以下操作都会破坏漏洞数据：**

重新保存图片

Photoshop 打开后保存

微信发送后下载

转换格式

压缩图片

**原因：** 这些操作会重新生成 IHDR、IDAT、CRC，原始残留数据消失。

③ 不要手动解压 IDAT

很多人会想到提取 IDAT → zlib 解压 → 查看像素，但 PNG 像素恢复需要正确宽高、Filter 算法、行扫描方式、色彩模式，直接解压得到的通常只是原始像素流，无法直接显示。应优先使用专用恢复工具。

## 五、常见误区

| 错误认知 | 正确结论 |
| --- | --- |
| 所有 PNG 都能恢复 | 必须满足使用受影响截图工具、裁剪保存过程存在漏洞、原始像素数据未被覆盖，普通 PNG 不存在该漏洞 |
| 文件大就一定存在漏洞 | 大文件只是提示可能残留大量 IDAT 数据，最终仍需工具验证 |
| 恢复出来有乱码或噪点就是失败 | 由于 PNG 过滤方式、部分数据缺失、宽高推测不完全，恢复图可能存在花屏 / 噪点 / 部分区域损坏，重点观察 flag 所在区域 |
| 可以手动解压 IDAT 恢复 | 需要正确宽高、Filter 算法、行扫描方式、色彩模式，直接解压只是原始像素流，应优先专用工具 |
| 图片可以先重新保存再处理 | 重新保存会重新生成 IHDR/IDAT/CRC，原始残留数据消失 |
