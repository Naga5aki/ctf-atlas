---
title: "十六进制格式应识应记"
summary: "十六进制格式应识应记"
module: "Misc"
topic: "文本与编码"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、应记

| 格式 | 十六进制特征 | ASCII/含义 | Misc实战用途 |
| --- | --- | --- | --- |
| PNG | 89 50 4E 47 0D 0A 1A 0A | PNG文件头 | 修文件头、识别伪装文件 |
| PNG | 49 48 44 52 | IHDR | 定位宽高 |
| PNG | 49 44 41 54 | IDAT | 定位图像压缩数据、IDAT隐写 |
| PNG | 49 45 4E 44 | IEND | 定位正常图像结束位置 |
| PNG | 00 00 00 00 49 45 4E 44 AE 42 60 82 | IEND Chunk | 判断PNG正常结尾 |
| JPEG | FF D8 | SOI | JPG文件开始 |
| JPEG | FF D9 | EOI | JPG文件结束 |
| JPEG | FF C0 | SOF0 | Baseline JPEG宽高 |
| JPEG | FF C2 | SOF2 | Progressive JPEG宽高 |
| JPEG | FF DA | SOS | 压缩扫描数据开始 |
| ZIP | 50 4B 03 04 | Local File Header | ZIP/Office/JAR/APK等识别 |
| ZIP | 50 4B 01 02 | Central Directory | 伪加密、目录结构分析 |
| ZIP | 50 4B 05 06 | EOCD | ZIP目录结束 |
| ZIP | 50 4B 07 08 | Data Descriptor | 某些ZIP数据描述符 |
| GIF | 47 49 46 38 37 61 | GIF87a | GIF文件头 |
| GIF | 47 49 46 38 39 61 | GIF89a | GIF文件头 |
| GIF | 3B | Trailer | GIF文件正常结束 |
| RAR4 | 52 61 72 21 1A 07 00 | Rar!... | 准确识别RAR4 |
| RAR5 | 52 61 72 21 1A 07 01 00 | Rar!.... | 准确识别RAR5 |

## 二、图片类宽高位置尤其重要

| 格式 | 定位 | 宽度 | 高度 | 字节序 |
| --- | --- | --- | --- | --- |
| PNG | 搜IHDR | IHDR后立即4字节 | 再后4字节 | 大端 |
| JPEG | SOF0/SOF2 | marker起始+7~+8 | +5~+6 | 大端 |
| GIF | 文件头后 | 偏移0x06~0x07 | 0x08~0x09 | 小端 |
| BMP | 常见BITMAPINFOHEADER | 0x12~0x15 | 0x16~0x19 | 小端 |
| TIFF | 根据IFD Tag | Tag 0x0100 | Tag 0x0101 | 由文件头决定 |

## 三、应识

| 格式 | 文件特征 | 实战重点 |
| --- | --- | --- |
| BMP | 42 4D | LSB、宽高异常、像素数据分析 |
| PDF | 25 50 44 46=%PDF | 附件、JS、对象流、隐藏内容 |
| PDF | 25 25 45 4F 46=%%EOF | 判断PDF尾部 |
| WAV | 52 49 46 46....57 41 56 45 | LSB、频谱、音频隐写 |
| WAV | 66 6D 74 20=fmt | 音频参数 |
| WAV | 64 61 74 61=data | PCM/实际声音数据 |
| ELF | 7F 45 4C 46 | Linux可执行文件 |
| PE/EXE | 4D 5A=MZ | Windows EXE/DLL |
| PE | 50 45 00 00=PE\0\0 | PE真正核心头 |
| MP3 | 49 44 33=ID3 | ID3标签隐写 |
| FLAC | 66 4C 61 43=fLaC | 音频Misc |
| OGG | 4F 67 67 53=OggS | 音频容器 |
| SQLite | 53 51 4C 69 74 65 20 66 6F 72 6D 61 74 20 33 00 | 取证、聊天记录、数据库题 |

压缩/归档格式

| 格式 | 十六进制文件头 | 识别 |
| --- | --- | --- |
| 7z | 37 7A BC AF 27 1C | 7-Zip |
| GZIP | 1F 8B 08 | gzip |
| BZ2 | 42 5A 68 | BZh |
| XZ | FD 37 7A 58 5A 00 | xz |
| ZIP | 50 4B 03 04 | zip |
| RAR4 | 52 61 72 21 1A 07 00 | rar4 |
| RAR5 | 52 61 72 21 1A 07 01 00 | rar5 |
| TAR | 偏移0x101附近出现75 73 74 61 72 | ustar |
