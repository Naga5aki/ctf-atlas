---
title: 远程控制与连接客户端痕迹
summary: 统一检查远控、数据库和 SSH 客户端的配置、会话、日志与凭据版本。
module: Forensics
track: 计算机取证
topic: 系统与用户痕迹
tags: [日志, 时间线]
status: 已整理
sourceIds: [web-forensics-wiki-remote]
updated: "2026-10-15"
---
## 01 配置、连接与操作分开判断

先确认程序版本、安装版/便携版、用户 SID、配置根目录和时区。**保存过某个连接**只说明配置存在；会话日志才能说明连接发生过；要认定远程执行或传输，还需操作、文件、进程和网络证据。

保全程序目录、用户配置目录、相关注册表及日志轮转文件。路径可被用户修改，下表用于定位候选位置，最终以实际文件结构、程序配置和版本说明为准。不要启动工作副本中的未知程序来“自动读取密码”。

## 02 六类远程控制工具

| 工具 | 候选位置与文件 | 重点提取 |
| --- | --- | --- |
| 向日葵 Sunlogin | `Program Files\Oray\SunLogin\SunloginClient\`、`AppData\Roaming\Oray\`；配置及 log 目录 | 本机设备标识、控制/被控角色、对端、起止时间、传输与操作日志 |
| ToDesk | 安装目录及 `AppData\Local\ToDesk\`；`config.ini`、Logs、设备列表 | 设备码、账户绑定、对端、会话与传输时间 |
| UU 远程 | 安装目录及用户 `AppData` 中的 UU 相关目录 | 设备/账户标识、连接列表、会话日志 |
| AnyDesk | `ProgramData\AnyDesk\`、`AppData\Roaming\AnyDesk\`；配置、trace 与 connection 日志 | 地址/别名、入站出站连接、授权和传输记录 |
| RustDesk | 安装版用户 `AppData\Roaming\RustDesk\`，便携版亦检查邻近目录；`config` 中的 TOML | ID/中继服务器、对端、会话与连接日志 |
| TeamViewer | 安装目录中的 `TeamViewer*_Logfile.log`、Connections 相关文本，用户配置 | 连接双方标识、方向、时间、文件传输 |

同一产品不同版本的文件名不同；不要把 `history.log`、`devlist.json` 或某个 ID 长度当成全版本固定规则。配置中的保存口令可能加密或仅是令牌，不能看到一个字段就认定为明文密码。

## 03 数据库客户端

| 工具 | 优先检查 | 可回答的问题 |
| --- | --- | --- |
| Navicat Premium | 用户配置、Documents 下 Navicat 目录、注册表、导出的 `.ncx` | 连接名、数据库类型、主机、端口、用户、SSH 隧道与查询记录 |
| DBeaver | 用户工作区 `.metadata`、项目 `.dbeaver`；`data-sources.json`、`credentials-config.json` | 数据源标识、JDBC 参数、凭据存储方式、SQL 工作区 |
| DataGrip | 用户 JetBrains 配置、项目 `.idea/dataSources.xml`、查询控制台 | 数据源、驱动、SSH 代理、查询与项目路径 |
| SQLyog | 用户配置及安装/便携目录中的 INI、连接配置与历史 | MySQL 连接、端口、SSH 隧道、保存的查询 |

账号密码可能依赖操作系统安全存储、主密码、产品版本和导出选项。Navicat 并非所有版本都采用同一 AES 参数；DBeaver 也不能统一套一条固定 OpenSSL 命令。提取时同时保留数据源配置与凭据文件，并记录解密前提。

## 04 SSH 与服务器客户端

| 工具 | 候选数据 | 分析步骤 |
| --- | --- | --- |
| FinalShell | 安装/便携根目录或用户配置中的 `conn`、`*_connect_config.json` | 解析主机、端口、用户、代理与会话；Base64 外观不代表口令只做 Base64 |
| Xshell | Documents 下 NetSarang/Xshell 的 Sessions，`*.xsh`；配置指定的日志目录 | 会话文件常为 INI 式键值，并非统一 XML；日志需事先启用 |
| MobaXterm | `MobaXterm.ini`、导出会话、`HKCU\Software\Mobatek`，安装/便携两类位置 | 会话、跳板、保存的 SSH 密钥与凭据；检查主密码与版本 |
| SecureCRT | 配置根目录中的 `Sessions\*.ini`、`Global.ini`、日志路径 | 主机、认证方式、日志选项；口令解码依赖对应版本格式 |
| WindTerm | 程序/用户指定的 `.wind`，`profiles` 下用户会话配置与终端日志 | 配置根目录、会话、代理、历史；不能固定假设每会话一个 `.session` 文件 |

找到配置后先以文本或 JSON/INI 解析器读取，再检查引用的日志和密钥路径。便携程序未写入系统安装记录很常见；缺少卸载项不代表未使用。

```bash
find ./work -type f \( -iname '*.xsh' -o -iname 'MobaXterm.ini' \
  -o -iname '*connect_config.json' -o -iname 'data-sources.json' \
  -o -iname 'credentials-config.json' -o -iname 'dataSources.xml' \)
rg -n -i 'hostname|host=|port|username|session|proxy|logfile' ./work/client-config/
```

只在已定位的配置副本中检索。日志如果含认证字段，输出到私有分析目录，结论使用账户标识和哈希，避免把秘密作为展示内容。

Xshell、Xftp 除了用户文档里的会话目录，还要看回收站里该用户 SID 下的会话文件。`$I` 记录原名和删除时间，`$R` 是内容。主机和端口分两列抄。5.1 这一代的会话口令可以不填写用户名就解密；更高版本再按该版本要求补用户名或主密码。书签里的名称可以和会话用户名核对，用户名有时是名称拼音。

## 05 建立会话证据表

记录 `程序/版本、配置路径、连接名、对端地址/设备ID、端口、角色、账户、开始/结束时间、日志记录位置、文件传输方向与哈希`。连接标识相同不代表自然人相同；时间漂移、重连和轮转都要标明。再与 [Windows 事件日志](/knowledge/forensic-windows-logs/)、[浏览器活动](/knowledge/forensic-browser/) 和流量记录核对。

## 06 实战：从保存会话核对远程文件传输

**场景与材料：** 用户目录中发现一个 SSH/远控客户端的连接配置、轮转日志和下载目录。目标是确认有没有连接与文件传输。先确定程序版本及便携/安装配置根目录，再静态读取材料。

1. 从配置提取会话 ID、主机/设备 ID、端口、用户、代理与日志路径，保存原始字段；凭据以材料标识引用，不在展示记录中贴明文。
2. 沿日志查连接开始、认证、传输与结束，按同一会话/连接 ID 串联。只有配置时结论停在保存连接信息。
3. 对传输记录提取方向、远端/本地路径、大小、状态与时间，核对落地文件哈希和文件系统操作记录。
4. 有跳板、中继或代理时分别记录各端点；中继地址和保存主机名不能自动当作操作人的地址。

| 示例材料 | 可以确认 | 进一步验证 |
| --- | --- | --- |
| 会话配置指向某服务器 | 存在保存配置 | 查会话日志、服务端认证与网络 |
| 认证成功，无传输条目 | 存在认证记录 | 核对会话建立、操作日志覆盖范围 |
| 日志标为传输完成且文件相符 | 相应传输较充分 | 对端哈希、会话归属和时间漂移 |

轮转缺口、日志未启用或配置被复制时，保留这些条件。不要启动未知客户端或访问配置中的真实服务器来补造历史记录。关联登录者需进一步看系统 SID、登录会话和服务端账户证据。
