---
title: "convert"
summary: "convert是ImageMagick套件里的核心命令，专门处理图像格式转换、像素编辑、隐写分析等操作"
module: "Misc"
topic: "图像与视觉"
locationPaths: []
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

convert是ImageMagick套件里的核心命令，专门处理图像格式转换、像素编辑、隐写分析等操作

## 一、核心功能

### 1）格式互转（解决后缀欺骗）

很多Misc题会把图片改后缀伪装成其他文件，convert可以直接识别并转换真实格式：

#把伪装成.txt的PNG转成正常PNG

convert  fake.txt  real.png

#常见格式互转：PNG↔JPG↔GIF↔BMP↔WebP

convert  input.jpg  output.png

**适用场景：** 文件后缀被篡改、图片无法正常打开、需要提取隐藏在格式里的信息。

### 2）调整尺寸/方向/颜色

**旋转/翻转：** 处理被旋转的二维码、倒置的图片

convert  input.png  -rotate  90 output.png

#顺时针旋转90°

convert  input.png  -flip  output.png

#垂直翻转

convert  input.png  -flop  output.png

#水平翻转

**缩放/裁剪：** 提取局部关键信息（如二维码角落、flag片段）

convert  input.png  -resize  50%output.png

#缩放到50%

convert  input.png  -crop  100x100+50+50  output.png

#裁剪(宽x高+偏移x+偏移y)

**颜色调整：** 修复对比度/亮度，提取隐藏的浅色文字

convert input.png -contrast -brightness -contrast 20x30 output.png

## 二、核心作用

### 1）处理LSB隐写

LSB隐写是把信息藏在图片像素的最低位，convert可以通过调整位平面来暴露：

#提取R通道第0位（最低位），生成可视化图片

convert input.png -channel R -evaluate and 1-negate  lsb_R.png

#提取G/B通道最低位

convert input.png -channel G -evaluate and 1-negate  lsb_G.png

convert input.png -channel B -evaluate and 1-negate  lsb_B.png

生成的黑白图里，黑色/白色区域就是隐藏的二进制信息，可进一步转成文本或二维码。

### 2）分离颜色通道

有些题会把信息拆分到R/G/B/Alpha通道里，单独提取后才能看到flag：

#分别提取R/G/B通道

convert input.png -channel R -separate channel_R.png

convert input.png -channel G -separate channel_G.png

convert input.png -channel B -separate channel_B.png

#提取Alpha通道（透明通道）

convert input.png -alpha extract alpha.png

**适用场景：** 信息被分散在不同颜色通道、透明通道藏有数据。

### 3）合并/拼接图片

**拼接多段碎片：** flag被切成多张图，需要按顺序拼接

#水平拼接

convert +append  part1.png  part2.png  full_horizontal.png

#垂直拼接

convert -append  top.png  bottom.png  full_vertical.png

**合并多通道：** 把分离的通道重新组合，或用不同通道生成新图

convert R.png G.png B.png -combine -set colorspace sRGB combined.png

### 4）处理GIF/多帧图片

**提取GIF每一帧：** 有些题把信息藏在GIF的某一帧里

convert animation.gif  frame_%d.png

#导出所有帧为frame_0.png,frame_1.png...

**调整帧延迟/循环：** 修复无法正常播放的GIF，或提取关键帧

convert input.gif -delay 100  output.gif

#每帧延迟100ms

## 三、高级分析

### 1）提取元数据与注释

虽然主要用exiftool，但convert也能查看/导出图片注释：

convert input.png -verbose info

#查看详细元数据

convert input.png -comment "flag{xxx}" output.png

#写入/修改注释

### 2）修复损坏图片

部分题目会故意损坏图片头/数据，导致无法打开，convert可以尝试修复：

#修复后缀异常 / 头部轻微损坏的文件

convert input.corrupted  output.png

#自动清理图片尾部追加数据

convert input.png output.png

### 3）生成差异图（对比两张图片）

如果题目给了两张几乎一样的图，flag藏在差异处：

convert  a.png b.png -compose difference  -composite  diff.png

-compose difference：设置图片合成模式为「像素差值计算」

-composite：正式执行两张图片的合成操作

差异区域会高亮显示，方便定位隐藏信息。

## 四、常用参数速查表

| 参数组合 | 核心功能 | 正确命令示例 |
| --- | --- | --- |
| -format | 指定输出文件格式 | convert  input.jpg  -format png output.png |
| -rotate 角度 | 按指定角度旋转图片 | convert  input.png  -rotate 180 output.png |
| -flip / -flop | 图片翻转 | 垂直翻转：convert input.png  -flip output.png<br>水平翻转：convert input.png  -flop output.png |
| -crop | 按指定区域裁剪图片 | convert input.png -crop 200x200+50+50 output.png |
| -channel + -separate | 提取指定颜色通道 | convert input.png -channel R <br>-separate r.png |
| -channel + -evaluate and 1 | 提取指定通道的最低位（LSB） | convert input.png -channel R -evaluate and 1 lsb.png |
| -negate | 图片颜色反色（负片效果） | convert lsb.png -negate output.png |
| +append / -append | 多张图片拼接 | 水平拼接：convert a.png b.png +append full.png<br>垂直拼接：convert a.png b.png -append full.png |
| -combine | 合并单通道图为彩色图 | convert r.png g.png b.png -combine out.png |
| -compose difference -composite | 生成两张图的差异对比图 | convert a.png b.png -compose difference -composite diff.png |
