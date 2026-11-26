---
title: "Passware Kit Forensic"
summary: "PKF（Passware Kit Forensic）是面向电子取证和密码恢复的综合工具，不只是 \"压缩包爆破软件\"。"
module: "Misc"
topic: "压缩与口令"
locationPaths: ["D:\\CTF_MISC_Tools\\压缩包\\Passware Kit Forensic(Eusrc)"]
sourceIds: ["0c884bd46797"]
updated: "2026-09-29"
---

## 一、工具概述

基本定位

PKF（Passware Kit Forensic）是面向电子取证和密码恢复的综合工具，不只是 "压缩包爆破软件"。它可以处理大量受密码保护的文件、加密磁盘 / 容器以及内存镜像，支持 CPU/GPU 和分布式 Agent。

应用场景

| 场景 | 用途 |
| --- | --- |
| CTF | ZIP / RAR / 7Z / PDF / Office → Recover File Password |
| 电子取证 | 加密文件、加密磁盘 / 容器（BitLocker / VeraCrypt / FileVault）、内存镜像、加密钱包、密码管理器 → 检测、密码恢复、解密、密钥提取 |

PKF 官方同时支持文件密码恢复、磁盘加密分析以及从物理内存中提取部分加密密钥。

## 二、使用方法

### 1. 最基本的文件密码恢复

打开 PKF，主界面选择 Recover File Password，然后选择文件（也可以直接把文件拖到 PKF 主界面）。之后 PKF 会识别文件格式，并给出三个主要选项：

| 模式 | 适用场景 | 特点 |
| --- | --- | --- |
| Passware Kit Wizard | 新手、已知一些密码特征 | 根据提示填写长度、字符等，PKF 自动生成合适的攻击组合 |
| Predefined Settings | 不知道密码是什么，按默认方案跑 | 适合快速试 CTF 弱密码、普通办公文档密码、常见人类密码；但会跑很多不必要的攻击，浪费时间 |
| Customize Settings | 有明显提示、需要精确控制 | 最重要的功能，进入 Attack Settings Editor 自由配置攻击 |

### 2. Customize Settings（核心功能）

**路径：** Recover File Password → 选择文件 → Customize Settings

进入后是 Attack Settings Editor，可以：

添加攻击 / 删除攻击

调整攻击顺序

设置字符集

设置长度

添加字典

组合不同攻击

把整个攻击模型保存成 .pwm，以后直接复用

### 3. 四种主要攻击方式

① Dictionary Attack（字典攻击）

怀疑是弱密码时优先使用。进入 Customize Settings → Add Attack → Dictionary，选择密码字典（如 rockyou.txt），然后 Recover。

**字典优先级：**

题目自带字典

根据题目线索自己整理的小字典

rockyou.txt 等通用字典

不要一上来就跑几千万甚至几亿组合。

② Brute-force（暴力破解）

明确知道密码字符集和长度时适合。进入 Customize Settings → Add Attack → Brute-force，设置 Length 和 Characters。

| 密码 | 搜索空间 | 可行性 |
| --- | --- | --- |
| 4 位数字 | 10⁴ = 10,000 | 非常容易 |
| 6 位数字 | 10⁶ = 1,000,000 | 比较现实 |
| 8 位大小写 + 数字 | 62⁸ | 完全另一个数量级 |

PKF 的关键不是 "点一下暴力破解"，而是尽可能缩小 Length 和 Symbol Set。

③ Mask Attack

知道密码结构时使用。例如题目提示 password = flag + 四位数字，固定 flag，只枚举最后四位数字。类似 CTF2026??????、admin??????、Nagasaki???? 都是 Mask 最适合的场景。

④ Known Password / Part（知道部分密码）

例如题目告诉你密码包含 DASCTF，但不知道前后内容，把 DASCTF 作为已知部分。比直接跑全空间暴力效率高得多。

CTF 中看到密码前缀、后缀、固定单词、部分泄露密码，应首先考虑 Mask 或 Known Password/Part，而不是 Brute-force。

### 4. 常见文件类型操作

ZIP / RAR / 7Z

直接 Recover File Password → challenge.zip，PKF 自动识别格式，然后根据题目情况选择：

| 题目情况 | 攻击方式 |
| --- | --- |
| 完全没提示 | Predefined / Dictionary |
| 弱密码 | Dictionary |
| 纯数字 | Brute-force |
| 知道格式 | Mask |
| 知道部分密码 | Known Password/Part |

具体破解速度取决于文件的加密算法 / KDF，不能简单按 "ZIP/RAR" 判断快慢。

PDF

**操作一样：** Recover File Password → challenge.pdf，然后选择攻击方式。

**普通弱密码：** Dictionary → rockyou.txt

6 位数字：Brute-force，Length=6，Characters=0-9

如果恢复的是 Owner Password，当前 Passware 还支持在恢复后创建不受原权限保护的 PDF

## 三、补充说明

### 1. GPU 加速

PKF 会利用支持的计算资源加速部分密码恢复任务。Resource Manager 可以管理本机及 Agent 的 CPU/GPU 资源，官方支持 NVIDIA、AMD、Intel Arc GPU，并支持一个主机使用多块 GPU。

**查看路径：** Tools → Resource Manager，重点检查 Built-in Agent、CPU、GPU、状态、速度。

如果有独显但 PKF 破解时 GPU 利用率始终为 0，不一定是 GPU 没识别，也可能是当前文件格式 / 攻击类型没有走 GPU 加速路径。

### 2. 分布式破解

PKF Forensic 可以让多台机器一起跑：

PKF Server

│

┌──────┼──────┐

↓      ↓      ↓

Agent1   Agent2   Agent3

CPU/GPU  CPU/GPU  CPU/GPU

当前 Forensic 版官方包含一定数量的 Agent，并可从 Resource Manager 中统一管理 Windows/Linux Agent。

CTF 单机通常没必要折腾，但电子取证中的大型密码恢复任务会很有价值。

### 3. 内存解密（取证重点）

PKF 不只是暴力密码。如果某台机器运行期间 VeraCrypt 已经挂载、BitLocker 已经解锁、某加密磁盘处于使用状态，加密密钥可能存在物理内存。

**取证流程：**

运行中的目标机器 → 获取内存镜像（memory.raw）

→ Passware Kit → 扫描内存 → 寻找加密密钥 → 解密磁盘/容器

官方明确支持利用物理内存镜像提取部分全盘加密密钥；如果目标加密卷在采集内存时已经挂载，这种方式可能比密码暴力高效得多。

**取证优先级：** 有内存镜像 → 先想密钥提取；没有内存 → 再考虑密码恢复。
