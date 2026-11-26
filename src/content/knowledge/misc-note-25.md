---
title: "像素点隐写"
summary: "原理： 数据依次写入R、G、B、Alpha单个通道的指定比特位，通常为最低位bit0。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、像素点隐写的基本分类

| 题型 | 隐藏位置 | 常见特征 | steg_bits对应功能 |
| --- | --- | --- | --- |
| 基础LSB | RGB/A某个位平面 | PNG/BMP、位平面有规律 | --channel、--bit |
| 多通道交错 | R0、G0、B0等交替排列 | 单通道全是乱码 | --bit-layout |
| 完整像素字节 | RGB值直接组成数据 | 像素值本身就是字节 | --channel-bytes |
| 手提像素点 | 纯色背景中的异常像素 | 单一颜色占比很高 | --sparse |
| 稀有颜色点 | 只出现少数几次的颜色 | 正常颜色多、特殊颜色极少 | --sparse-mode rare |
| 等像素点 | 满足R=G=B等条件的像素 | 正常图片中少量特殊关系 | --pixel-condition |
| 固定和/差 | RGB和、差满足固定值 | 如RGB_SUM=255 | 安全条件表达式 |
| 坐标型 | X、Y坐标保存字符 | RGB只负责标记位置 | --pixel-value X/Y |
| 等距像素点 | 每隔N个像素采样 | 宽高常为N的倍数 | --stride |
| 相邻关系 | 相邻像素XOR或差值 | 单独查看像素无明显异常 | --neighbor-operation |
| 调色板索引 | PNG palette index位 | 转成RGB后线索消失 | --channel Index |
| 两图关系 | 两张图XOR或差分 | 两图尺寸一致、肉眼接近 | --second-image |
| 黑白点阵 | 黑白像素直接表示0/1 | 水印图、二维码状点阵 | Gray阈值与扫描 |

## 二、核心题型详解

（一）基础位平面类

数据嵌入在单个或多个通道的指定位中，是最经典的像素隐写类型。

### 1.单通道LSB

**原理：** 数据依次写入R、G、B、Alpha单个通道的指定比特位，通常为最低位bit0。

**特征：** 无损格式图片，单个位平面存在规律性数据特征。

**常用命令：**

#R通道最低位提取

python3 steg_bits.py input.png--channel R--bit 0--scan row--bit-order msb--output-dir recovery

#Alpha通道最低位提取

python3 steg_bits.py input.png--channel A--bit 0--output-dir recovery_a0

**说明：** --bit 0为最低位，--bit 7为最高位。

### 2.多通道交错

**原理：** 数据按规则分散在多个通道的位平面中，单通道提取无法得到完整数据。

**两种排列模式：**

**像素交错：** 每个像素内按通道顺序读取比特（R0→G0→B0→下一个像素）

**平面交错：** 先读完整个R0平面，再依次读取G0、B0

**常用命令：**

#像素交错模式，R0-G0-B0顺序

python3 steg_bits.py input.png--bit-layout R0,G0,B0--packing pixel-interleaved--output-dir recovery

#平面交错模式

python3 steg_bits.py input.png--bit-layout R0,G0,B0--packing channel-planar--output-dir recovery

#自定义位排列

python3 steg_bits.py input.png--bit-layout B0,G0,R0--output-dir recovery

### 3.完整通道字节

**原理：** 数据不藏在单个比特，而是直接用完整通道值作为字节数据。

**常用命令：**

#RGB顺序完整字节提取

python3 steg_bits.py input.png--channel-order RGB--channel-bytes--packing pixel-interleaved--output-dir recovery

#BGR顺序

python3 steg_bits.py input.png--channel-order BGR--channel-bytes--packing pixel-interleaved--output-dir recovery

（二）稀疏异常像素类

核心逻辑是用极少数特殊像素承载数据，绝大多数像素为背景填充。

### 1.纯色背景异常像素

**原理：** 单一背景色占据绝大多数像素，少量异色像素的通道值直接保存数据。

**特征：** 主色占比极高，画面整体为纯色。

#### 操作步骤：

### 1.先统计主色比例：

python3 steg_bits.py input.png--stats--analysis-only

### 2.自动识别背景色，提取异常像素的通道值：

#自动识别背景，提取R通道值

python3 steg_bits.py input.png--sparse--background auto--pixel-value R--output-dir recovery

#指定背景色，允许色差容错

python3 steg_bits.py input.png--sparse--background 255,255,255--distance-metric max--color-distance 2--pixel-value R--output-dir recovery

### 2.稀有颜色点

**原理：** 承载数据的颜色在整张图中仅出现极少次数。

**常用命令：**

#提取出现次数≤1的颜色的R通道值

python3 steg_bits.py input.png--sparse--sparse-mode rare--rare-max-count 1--pixel-value R--output-dir recovery

#设置选中像素数量边界，避免误选过多

python3 steg_bits.py input.png--sparse--min-selected 4--max-selected 4096--pixel-value R--output-dir recovery

（三）条件像素类

通过像素通道间的数学关系标记特殊像素，未参与条件的通道或坐标承载数据。

### 1.通道相等类

**经典考法：** 相等通道负责标记特殊像素，剩余通道保存ASCII数据。

**常用条件与命令：**

#R=G=B灰度像素，提取R通道值

python3 steg_bits.py input.png--pixel-condition'R=G'--pixel-condition'G=B'--pixel-value R--output-dir recovery

#R=G，B通道存数据

python3 steg_bits.py input.png--pixel-condition'R=G'--pixel-value B--output-dir recovery

### 2.固定和/差类

**原理：** 像素通道的和、差值满足固定值，以此标记特殊像素。

**常用命令：**

#RGB三通道之和为255

python3 steg_bits.py input.png--pixel-condition'RGB_SUM=255'--pixel-value R--output-dir recovery

#R与G通道差值为1

python3 steg_bits.py input.png--pixel-condition'R-G=1'--pixel-value B--output-dir recovery

### 3.近似相等条件

三通道最大值与最小值相差不超过阈值，标记近似灰度像素：

python3 steg_bits.py input.png--pixel-condition'RGB_MAX-RGB_MIN<=1'--pixel-value R--output-dir recovery

### 4.坐标承载数据

**原理：** 特殊像素的X或Y坐标值本身承载ASCII或数值数据，RGB仅起标记作用。

**常用命令：**

#灰度像素的X坐标模256作为数据

python3 steg_bits.py input.png--pixel-condition'R=G'--pixel-condition'G=B'--pixel-value'X%256'--output-dir recovery

#Y坐标作为数据

python3 steg_bits.py input.png--pixel-condition'R=G'--pixel-condition'G=B'--pixel-value'Y%256'--output-dir recovery

### 5.像素排序规则

**默认排序：** 从上到下、从左到右（行优先）

**支持排序方式：** row、column、reverse-row、reverse-column、x、y、value、x+y

**示例命令：**

#按列优先排序

python3 steg_bits.py input.png--pixel-condition'R=G'--pixel-value B--pixel-sort column--output-dir recovery

（四）等距采样类

数据嵌入在固定空间间隔的像素中，需匹配正确的间隔与起点才能提取。

### 1.固定间隔采样

**原理：** 按固定横纵间隔选取像素，承载隐藏数据。

**常用命令：**

#横纵均为10像素间隔

python3 steg_bits.py input.png--stride 10--save-intermediate--analysis-only--output-dir analysis

#横向间隔10、纵向间隔5

python3 steg_bits.py input.png--stride 10 5--save-intermediate--analysis-only--output-dir analysis

### 2.起点偏移

**原理：** 采样不一定从(0,0)开始，存在横纵偏移量。

**约束：** 偏移值必须小于对应方向的步长

**示例命令：**

#步长10，横向偏移3，纵向偏移7

python3 steg_bits.py input.png--stride 10--offset-x 3--offset-y 7--save-intermediate--analysis-only--output-dir analysis

### 3.块聚合模式

除单点精确采样外，支持对块内像素做聚合运算：point（精确点，默认）、mean、median、min、max。

#10×10块取中位数

python3 steg_bits.py input.png--stride 10--stride-reducer median--save-intermediate--analysis-only--output-dir analysis

（五）相邻像素关系类

数据隐藏在相邻像素的运算结果中，单像素观察无异常。

### 1.相邻异或

**原理：** 相邻两个像素的通道值异或结果承载数据。

**常用命令：**

#右侧相邻像素R通道异或，结果作为完整字节

python3 steg_bits.py input.png--neighbor-operation xor--neighbor-direction right--channel-order R--channel-bytes--output-dir recovery

### 2.相邻差值

**原理：** 相邻像素的绝对差值承载数据。

**支持运算：** xor、abs-diff、next-minus-current、current-minus-next

**支持方向：** right、down、diag-right、diag-left

**示例命令：**

#下方相邻像素G通道绝对差，提取最低位

python3 steg_bits.py input.png--neighbor-operation abs-diff--neighbor-direction down--channel G--bit 0--output-dir recovery

（六）其他专项题型

### 1.调色板索引隐写

**原理：** 数据藏在PNG调色板的索引值位平面中，图片转RGB后索引信息丢失，线索消失。

**注意：** 仅真实调色板图片可用，非调色板格式会报错。

**命令：**

#提取索引最低位

python3 steg_bits.py input.png--channel Index--bit 0--output-dir recovery

### 2.双图关系隐写

**前提：** 两张图片尺寸完全一致。

**支持运算：** 异或、绝对差分、位平面异或

**常用命令：**

#灰度图异或

python3 steg_bits.py image1.png--second-image image2.png--combine xor--channel Gray--save-intermediate--output-dir analysis

#指定位平面异或

python3 steg_bits.py image1.png--second-image image2.png--plane-xor G0 G0--save-intermediate--output-dir analysis

### 3.黑白点阵隐写

**原理：** 黑白像素映射为0/1比特流，进一步还原数据。

**处理逻辑：** 灰度阈值二值化+扫描规则读取比特流。

## 三、自动模式说明

### 1.基础自动模式

**仅覆盖常规位平面检测：**

python3 steg_bits.py input.png--auto--output-dir recovery

### 2.像素隐写增强自动模式

**开启像素点类隐写检测：**

python3 steg_bits.py input.png--auto--auto-level normal--auto-pixels--output-dir recovery_pixels

### 3.自动模式覆盖范围

主色占比高的背景异常像素

R=G=B、两通道相等、近似灰度等条件像素

灰度像素的坐标取值

常见宽高公因数对应的步长

有限的相邻异或与差分检测

### 4.自动模式边界

以下场景自动模式无法覆盖，需手动配置参数：

任意自定义数学条件

任意背景色、所有稀有次数枚举

所有步长偏移组合

所有坐标排列方式

所有相邻方向与运算组合

带密钥、伪随机坐标、未知置乱的像素隐写

## 四、结果有效性判断

### 1.有效判定依据

选中像素数量、占比符合逻辑

中间掩码图存在有意义的结构

恢复结果为合法UTF-8或高比例可打印字符

Flag格式正常闭合，无控制字符

文件Magic匹配且结构验证通过

压缩格式可正常解压

参数可稳定复现结果

### 2.无效判定误区

以下现象仅为线索，不能直接证明存在隐写：

0/1比例接近50%

图片宽高能被某数值整除

存在少量满足条件的像素

数据中偶然出现flag相关字节

文件体积略大于预期
