---
title: "zsteg"
summary: "zsteg专注于检测PNG、BMP、ZIP、WebP等格式文件中隐藏的数据（如LSBI隐写、文件头隐藏、附加数据、密码哈希等）。"
module: "Misc"
topic: "图像与视觉"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

zsteg专注于检测PNG、BMP、ZIP、WebP等格式文件中隐藏的数据（如LSBI隐写、文件头隐藏、附加数据、密码哈希等）。

## 一、核心定位

**检测隐形数据：** 自动扫描图片是否包含隐藏的文件、字符串、密钥、密码等。

**多格式支持：** 主要针对PNG（最常用）、BMP，也支持GIF,WebP,TTF等。

**提取隐藏内容：** 配合参数，可以直接提取出隐藏在图片里的文件

## 二、应用场景

提取 RGB/Alpha 通道中藏匿的 flag、文本类明文信息

识别并导出嵌入像素数据的压缩包、文档等二进制文件

自动遍历位深度、通道组合、字节序，快速匹配特殊隐写配置

针对性检测 PNG 透明通道的隐写数据

## 三、实战命令

| 命令 | 功能说明 |
| --- | --- |
| zsteg target.png | 默认检测常见 LSB 隐写模式，直接输出识别到的隐藏内容 |
| zsteg -a target.png | 全量遍历所有通道、位深度、字节序组合，深度检测隐写 |
| zsteg -c a target.png | 仅检测 Alpha 透明通道的隐写数据 |
| zsteg --msb target.png | 按 MSB（高位优先）字节序检测，适配特殊隐写写法 |
| zsteg -e b1,rgb,lsb,xy target.png | 提取 RGB 通道 1 位 LSB 的原始隐写数据 |
| zsteg -E "payload_name" target.png > out.zip | 将识别到的隐藏文件导出并保存到本地 |
| zsteg -v target.png | 详细模式，输出完整检测过程，便于排查特殊隐写 |
