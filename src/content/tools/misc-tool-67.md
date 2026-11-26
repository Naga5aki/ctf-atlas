---
title: "TianTongEye"
summary: "TianTongEye"
module: "Misc"
topic: "文件结构与提取"
locationPaths: ["D:\\CTF_MISC_Tools\\图像隐写\\TianTongEye"]
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、命令速查表

| 命令 | 作用 | 使用场景 |
| --- | --- | --- |
| TianTongEYE list | 列出所有支持模块 | 查看可用隐写算法 |
| TianTongEYE image.jpg | 神通模式，自动检测并尝试提取隐写信息 | CTF首选入口，未知隐写类型 |
| TianTongEYE image.jpg -v | 显示所有模块分析结果（包括失败） | 深度排查隐藏信息 |
| TianTongEYE image.jpg -p "password" | 指定密码进行分析 | 已知密码或密码保护隐写 |
| TianTongEYE avatar image.jpg -o output.txt | 指定模块提取并保存结果 | 针对特定隐写算法 |

## 二、爆破模式

| 命令 | 作用 | 使用场景 |
| --- | --- | --- |
| TianTongEYE brute-force image.jpg -d passwords.txt | 字典爆破密码 | 常见密码、弱密码 |
| TianTongEYE brute-force image.jpg -m "?d?d?d?d" | 掩码爆破4位数字 | PIN码、数字密码 |
| TianTongEYE brute-force image.jpg -m "?l?l?l?l?l?l" | 掩码爆破6位小写字母 | 字母密码 |

掩码参数

| 参数 | 含义 | 范围 |
| --- | --- | --- |
| ?d | 数字 | 0-9 |
| ?l | 小写字母 | a-z |
| ?u | 大写字母 | A-Z |
| ?s | 特殊字符 | !@#$%^&* |
| ?a | 全字符 | 数字+字母+特殊 |

## 三、单图盲水印分析

| 命令 | 作用 | 使用场景 |
| --- | --- | --- |
| TianTongEYE blind-watermark image.png | 默认提取5种盲水印结果 | 单图盲水印首选 |
| TianTongEYE blind-watermark image.png --beta 20 -o exports | 调整增强参数并输出结果 | 水印不明显时 |
| TianTongEYE blind-watermark image.png --modes fft-multiplier,java-dct -o exports | 指定分析算法 | 针对特定水印方式 |
| TianTongEYE --format json blind-watermark image.png -o exports | JSON格式输出结果 | 自动化分析 |

支持算法

| 模式 | 作用 |
| --- | --- |
| fft-multiplier | FFT频域增强 |
| fftshift-multiplier | FFT中心化增强 |
| fft-normalization | FFT归一化 |
| fftshift-normalization | FFT中心化归一化 |
| java-dct | DCT域盲水印分析 |

## 四、PNG/BMP LSB分析（zsteg）

| 分类 | 命令 | 作用 | 使用场景 |
| --- | --- | --- | --- |
| LSB检测 | TianTongEYE zsteg image.png | 自动扫描LSB隐写 | PNG/BMP隐写检测 |
| LSB检测 | TianTongEYE zsteg image.png 2b,b,lsb,xy | 指定位、通道、顺序分析 | 精确检测 |
| LSB提取 | TianTongEYE zsteg image.png -E b3,rgb,lsb,xy -o out.bin | 提取隐藏payload | 获取隐藏文件 |
| 位平面 | TianTongEYE zsteg mask image.png -m 00000011 -o mask.png | 查看指定bit层 | 分析隐藏图像 |
| BMP分析 | TianTongEYE zsteg reflow sample.bmp -W 320 -D output | BMP像素重新排列 | BMP异常分析 |
| 输出JSON | TianTongEYE --format json zsteg image.png | JSON格式输出扫描结果 | 自动化处理 |

## 五、加密/解密与隐写算法

| 分类 | 命令 | 作用 | 使用场景 |
| --- | --- | --- | --- |
| 解密 | TianTongEYE decrypt image.jpg -M JpHide-0.51 -p "password" | 使用指定模块解密 | 已知算法+密码 |
| 差分隐写 | TianTongEYE decrypt stego.png -M ImageSteganography --reference base.png -p "password" | 基于原图差异解密 | 双图隐写 |
| 加密 | TianTongEYE encrypt image.jpg -d secret.txt -o output.jpg -M F5 | 使用F5算法嵌入文件 | 测试隐写算法 |

常用参数

| 参数 | 作用 |
| --- | --- |
| -p | 指定密码 |
| -d | 指定字典文件 |
| -m | 指定爆破掩码 |
| -M | 指定隐写模块 |
| -E | 提取指定数据 |
| -o / --output | 指定输出目录或文件 |
| --beta | 调整盲水印增强参数 |
| --modes | 指定分析模式 |
| --format json | JSON格式输出 |
