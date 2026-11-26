---
title: "键鼠流量判断"
summary: "3.若bInterfaceProtocol=0x00，应查看HID Report Descriptor："
module: "Misc"
topic: "流量与网络"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、先确认HID设备

### 1.查看USB接口描述符：

bInterfaceClass=0x03

表示HID设备。

### 2.常用过滤：

usb.bInterfaceClass==0x03

## 二、通过接口协议区分设备

| 字段 | 键盘 | 鼠标 |
| --- | --- | --- |
| bInterfaceClass | 0x03 | 0x03 |
| bInterfaceSubClass | 0x01 | 0x01 |
| bInterfaceProtocol | 0x01 | 0x02 |

### 1.键盘接口：

usb.bInterfaceClass==0x03&&

usb.bInterfaceProtocol==0x01

### 2.鼠标接口：

usb.bInterfaceClass==0x03&&

usb.bInterfaceProtocol==0x02

3.若bInterfaceProtocol=0x00，应查看HID Report Descriptor：

Usage Page=Generic Desktop

Usage=Keyboard→键盘

Usage Page=Generic Desktop

Usage=Mouse→鼠标

## 三、锁定设备接口和端点

### 1.确定设备类型后，记录：

usb.device_address

usb.interface_number

usb.endpoint_address

键盘和鼠标的有效数据通常通过：

Interrupt IN

设备→主机

2.同一个USB接收器可能同时包含键盘和鼠标，应按不同的接口号或端点地址区分，不能只看设备地址。

**示例：**

usb.device_address==3&&

usb.endpoint_address==0x81

## 四、过滤HID数据字段

### 1.常见数据字段：

usbhid.data：已被HID解析器识别的数据

usb.capdata：USBPcap捕获的原始数据

### 2.过滤包含任一数据字段的报文：

usbhid.data||usb.capdata

### 3.只看设备发往主机的数据：

usb.endpoint_address.direction==1&&

(usbhid.data||usb.capdata)

### 4.按内容精确过滤：

usbhid.data==00:00:04:00:00:00:00:00

usb.capdata==00:00:04:00:00:00:00:00

### 5.按部分字节过滤：

usbhid.data contains 00:00:04

usb.capdata contains 00:00:04

## 五、通过数据长度辅助判断

| 数据长度 | 常见设备 |
| --- | --- |
| 8字节 | 标准Boot Keyboard |
| 3或4字节 | 标准Boot Mouse |

### 1.键盘候选：

(usbhid.data&&len(usbhid.data)==8)||

(usb.capdata&&len(usb.capdata)==8)

### 2.鼠标候选：

(usbhid.data&&

(len(usbhid.data)==3||len(usbhid.data)==4))

||

(usb.capdata&&

(len(usb.capdata)==3||len(usb.capdata)==4))

### 3.也可使用USB数据长度字段：

usb.data_len==8

usb.data_len==3||usb.data_len==4

## 六、最终判断顺序

### 1.bInterfaceClass=0x03

→确认HID

### 2.bInterfaceProtocol

0x01→键盘

0x02→鼠标

### 3.Protocol无法判断

→查看Usage：Keyboard或Mouse

### 4.记录设备地址、接口号和端点地址

### 5.过滤usbhid.data或usb.capdata

### 6.根据数据长度辅助验证

8字节→键盘候选

3/4字节→鼠标候选

数据长度只能辅助判断。NKRO键盘、游戏鼠标、带Report ID或厂商自定义HID的报告长度可能不同，最终应以接口协议、Usage、接口号和端点地址为准。
