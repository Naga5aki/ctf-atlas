---
title: "Data URI+Base64图片"
summary: "该题型的本质是将图片/文件的原始字节做Base64编码，再通过Data URI格式嵌入文本、网页、流量中隐藏。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、核心定位

该题型的本质是将图片/文件的原始字节做Base64编码，再通过Data URI格式嵌入文本、网页、流量中隐藏。

**典型链路：**

原始文件→Base64编码→Data URI格式封装→藏入HTML/流量/JS/文本

## 二、Data URI基础结构

### 1.标准语法

**data:** [<media-type>][;base64],<data>

**结构拆分：**

**data:** ：协议前缀

media-type：MIME媒体类型，声明数据格式

;base64：可选标记，说明后续数据为Base64编码

,：分隔符，逗号后为实际数据内容

**示例：**

**data:** image/png;base64,iVBORw0KGgoAAAANSUhEUg...

### 2.常见图片类MIME类型

| MIME类型 | 对应格式 | 注意事项 |
| --- | --- | --- |
| image/png | PNG图片 | 最常见 |
| image/jpeg | JPEG图片 | 正式标准为image/jpeg，非image/jpg |
| image/gif | GIF动图 | - |
| image/webp | WebP图片 | - |
| image/svg+xml | SVG矢量图 | 解码后为XML文本 |

### 3.省略MIME的情况

**可能出现data:** ;base64,SGVsbG8=格式：

MIME类型被省略，无法从头部判断文件类型

必须Base64解码后，通过文件Magic字节判断真实格式

### 4.非Base64的Data URI

**并非所有data:** 开头的内容都是Base64编码：

无;base64标记时，数据通常为URL百分号编码（如%20代表空格）

**禁止看到data:** 就直接执行Base64解码，需先确认编码标记

## 三、应用场景

Data URI通常嵌入在以下载体中，可通过data:、base64,、data:image定位：

**HTML页面：** <img src="data:image/png;base64,...">内联图片

**HTTP流量：** 响应体中的HTML、接口返回的Base64数据，是流量题高频考点

**JavaScript代码：** 以字符串变量形式存储图片

**CSS样式：** background-image:url(data:image/png;base64,...)背景图

普通文本、日志、源码文件：直接隐藏完整Data URI串
