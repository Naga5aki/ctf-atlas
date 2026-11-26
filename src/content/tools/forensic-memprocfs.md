---
title: MemProcFS 与 LovelyMem：内存文件视图
summary: 挂载内存副本，检查系统、进程、NTFS、注册表、时间线和异常候选结果。
module: Forensics
topic: 工具参数与插件
locationPaths: ['D:\CTF_MISC_Tools\Forensics\MemProcFS_files_and_binaries-win_x64-latest', 'D:\CTF_MISC_Tools\Forensics\Lovelymem']
sourceIds: [web-hello-memory, web-forensics-wiki-lovelymem]
updated: 2026-10-03
---

## 1. 挂载与取证模式

MemProcFS 将可解析内存呈现为虚拟文件系统。Windows 挂载依赖对应文件系统驱动；在分析机准备依赖，不在目标镜像中安装。输入为工作副本，输出和挂载盘另选独立位置。

```powershell
MemProcFS.exe -device .\work\memory.raw -mount M -forensic 1
```

先确认 M 盘未被占用。`-device` 指输入，取证模式适用于稳定副本；实时采集对象会变化，不应照搬同一结果解释。常用模式：**1 内存数据库，2 临时数据库并退出后删除，3 临时数据库并保留，4 固定数据库**。保存模式、启动参数、工具版本、符号状态和完成情况，优先启动时启用取证分析。

## 2. 按问题选择目录

| 问题 | 优先查看 | 判读 |
| --- | --- | --- |
| 系统名与构建 | `sys` 系统信息、注册表 SOFTWARE/SYSTEM | 版本、系统名、启动时间需相互核对 |
| 进程行为 | `pid` / `name` 下的进程目录 | 进程、模块、命令行、虚拟内存、线程 |
| 文件候选 | `forensic\files` 下 NTFS/文件视图 | 内存重建可能缺页；保留导出和目录映射 |
| 浏览、账号或远控 | 相应用户目录、应用缓存、注册表和进程 | QQ 标识、BV 号、IP 都是线索，继续关联 |
| 时间与文件活动 | `forensic\timeline`、NTFS、注册表派生结果 | 确认每类时间含义和输入覆盖 |
| 可疑可执行内存 | `forensic\findevil` 与 YARA 结果 | 属于候选，需要进一步人工检查 |

目录与 CSV 文件名依版本变化，先读根目录说明和实际生成的列表。`files\ROOT` 可帮助定位用户桌面、下载和 ToDesk 记录等，但不能假设每份镜像都能重建完整磁盘。

## 3. 时间线与搜索

时间线常按进程、注册表、NTFS 等分表；保留类型、原始时间、PID、路径与内存位置。先等待取证扫描完成，再复制需要的结果，以免把正在增长的 CSV 当作完整数据。

```powershell
Get-ChildItem -LiteralPath 'M:\forensic\timeline' -File
Get-ChildItem -LiteralPath 'M:\forensic\files' -Recurse -File |
  Where-Object { $_.Name -match 'history|consolehost|todesk|stikynot' }
```

大量递归会耗时，先按进程或用户目录缩小范围。检索账号、视频编号和字符串时保存完整上下文；某个账号出现在缓存中不等于本机登录过该账号。

## 4. FindEvil 的边界

FindEvil 主要帮助分析支持范围内的 Windows x64 用户进程。可见类型包括注入 PE、未链接 PE、补丁、可执行私有内存和 YARA 命中等。合法 JIT、杀毒和浏览器也会触发异常候选；它不等于通用内核 rootkit 扫描器。

记录命中类型、PID、区域、保护属性、对应模块与字节，再用 Volatility、文件签名、网络和日志复核。处理过程不必运行导出的可疑文件。

## 5. LovelyMem 的工作方式

LovelyMem 提供图形入口，组织 MemProcFS、Volatility 2/3 和字符串/导出任务。先配置各引擎和 Python 路径，查看实际执行的参数和输出目录，再按系统、进程、文件、网络、注册表顺序操作。

框架兼容性和插件依赖不能靠“一键分析”自动保证。保存工具生成的原始文本/CSV、失败信息和版本；第三方插件先核对用途与代码，不盲目执行。版本差异与命令参考见 [Volatility 指南](/tool/forensic-volatility/)。
