---
title: "“冷门”二维码识别"
summary: "按定位图形与模块形态区分常见矩阵码，并验证解码结果。"
module: "Misc"
topic: "图像与视觉"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-30"
---

## 1. 先辨认符号结构

遇到陌生二维码，先看**定位图形、模块形状、整体长宽比**，再选解码器。只凭外观给出格式名称容易误判，尤其是图片被旋转、裁边、反色或缩放后。以下线索用于缩小范围，最终仍需由相应格式的解码结果确认。

| 候选格式 | 优先观察的特征 | 下一步 |
| --- | --- | --- |
| Aztec Code | 中央有同心方形定位图案 | 保留中心和外圈，尝试旋转后识别 |
| Data Matrix | 两条相邻实线边组成 L 形定位边 | 核对另外两边的交替模块 |
| MaxiCode | 中央靶心与六角形模块 | 避免按普通方格二维码处理 |
| PDF417 | 多行堆叠的一维条纹，通常较宽 | 保留完整行与左右边界 |
| DotCode | 信息单元呈分离的圆点 | 避免二值化时把相邻点粘连 |
| GridMatrix、汉信码 | 先对照下方图例确定候选 | 使用明确支持该格式的解码器复核 |

## 2. 实战解码顺序

1. **保留未处理图片**：记录分辨率和哈希；裁切工作副本时不要切掉定位图形或边缘留白。如果一张图里有多个码，逐个裁切。
2. **先试原图**：确认所用工具支持候选码制。一个工具返回“未识别”只说明这次识别失败，不说明图中没有数据。
3. **再做有限变换**：按 `0° / 90° / 180° / 270°` 旋转，分别尝试原色、灰度和反色；每次只改变一个条件，记录哪张图得到什么结果。
4. **检查输出类型**：保存解码后的原始字节与十六进制值，再判断它是文本、URL、文件头还是下一层编码。乱码可能是二进制数据，也可能是识别错误。

在 Kali/Linux 可先制作对照图；放大只改善显示，不会凭空恢复已经丢失的模块细节：

```bash
sha256sum input.png
file input.png
magick input.png -colorspace Gray -auto-level -filter point -resize 400% enlarged.png
magick input.png -negate inverted.png
```

若图像倾斜或透视变形，应先校正几何，再比较不同处理版本的解码结果。最终答案需能由稳定、完整的符号区域重复读出；仅凭一张经过强处理的图得到一次字符串，不足以排除误识别。

## 3. 格式图例

### 1. Aztec code

![示意图 7](/doc-media/misc-note-71-007.png)

### 2. DataMatrix

![示意图 8](/doc-media/misc-note-71-008.png)

### 3. GridMatrix

![示意图 9](/doc-media/misc-note-71-009.png)

### 4. MaxiCode

![示意图 10](/doc-media/misc-note-71-010.png)

### 5. DotCode

![示意图 11](/doc-media/misc-note-71-011.png)

### 6. 汉信码

![示意图 12](/doc-media/misc-note-71-012.png)

### 7. PDF417 Code

![示意图 13](/doc-media/misc-note-71-013.png)
