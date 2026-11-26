## 01 先确定日志范围

默认日志目录为 `C:\Windows\System32\winevt\Logs\`。保全 Security、System、Application 以及对应的 Operational 日志和归档，记录通道、Provider、最早/最晚事件、记录数量、时区与哈希。事件 ID 必须与 Provider 和通道一起解释。

| 问题 | 日志与重点字段 | 不能直接推断的结论 |
| --- | --- | --- |
| 谁登录 | Security：账户、SID、LogonId、LogonType、源地址 | 账户名不能直接确定自然人 |
| 运行了什么 | Security 4688、Sysmon 1：路径、父进程、参数、哈希 | 没有开启审计时，空表不能证明未执行 |
| 远程桌面 | Security + TerminalServices 两类 Operational | 一次认证成功不代表交互桌面建立 |
| 安装服务 | System 7045、Security 4697 | 合法安装也会留下服务事件 |
| PowerShell | PowerShell/Operational、Windows PowerShell | 历史文件与事件日志不是同一类证据 |

## 02 登录事件速查

| ID | 含义 | 关联方法 |
| --- | --- | --- |
| 4624 / 4625 | 成功登录 / 登录失败 | 检查目标账户、登录类型、地址、失败状态码 |
| 4634 / 4647 | 会话结束 / 用户发起注销 | 用 LogonId 关联，不能只按用户名连接 |
| 4648 | 显式凭据认证尝试 | 关联进程和目标服务器；不保证远端成功 |
| 4672 | 新登录被授予特殊权限 | 与对应 4624 的 LogonId 配对 |
| 4778 / 4779 | 会话重连 / 断开 | 检查会话名、客户端与相关登录事件 |
| 1074 | 系统日志中由进程或用户发起的关机或重启 | 在 `System.evtx`；用来回答关机，不拿来回答注销 |
| 1102 | Security 审计日志被清除 | 结合账户、时间和归档确认清除行为 |

常见登录类型：**2 交互、3 网络、4 批处理、5 服务、7 解锁、10 远程交互、11 缓存交互**。类型 3 可能来自文件共享、管理接口等，不应全部标为 RDP。来源为空、回环地址或代理地址时，应继续查远程工具和网络记录。

RDP 常见链为：RemoteConnectionManager 1149 → LocalSessionManager 21/22 → Security 4624 类型 10。23 表示会话注销，24/25 对应断开/重连。版本和审计配置会影响记录，使用账户、会话 ID、地址与时间共同关联。

要求“不论成败”的登录次数时，把该账户的 `4624` 和 `4625` 相加，注销事件不计入。同一钟点、日期差一天时，用事件 XML 里的 UTC `SystemTime` 按东八区换算，不靠心算改日期。

## 03 离线查询与导出

以下是 Windows 环境对**工作副本**的读取命令。保留完整 XML，再生成便于排序的摘要。

```powershell
$logPath = '.\work\Security.evtx'
$events = Get-WinEvent -FilterHashtable @{
  Path = $logPath
  Id = 4624,4625,4648,4672,1102
}
$events | ForEach-Object { $_.ToXml() } |
  Set-Content -LiteralPath '.\output\security-events.xml' -Encoding UTF8
$events | Select-Object TimeCreated, Id, RecordId, ProviderName, Message |
  Export-Csv -LiteralPath '.\output\security-summary.csv' -NoTypeInformation -Encoding UTF8
```

先创建 `output` 目录。事件 XML 中的 `TimeCreated/SystemTime` 为 UTC；`TimeCreated` 的界面显示取决于分析机时区。解析账户或地址时按 XML `Data/@Name` 取字段，避免用 `Properties[5]` 等固定序号跨版本套用。

```powershell
wevtutil qe .\work\Security.evtx /lf:true /f:xml /q:"*[System[(EventID=4624 or EventID=4625)]]"
EvtxECmd.exe -d .\work\Logs --csv .\output --csvf events.csv
```

`wevtutil /lf:true` 指定离线日志。EvtxECmd 批量解析后的筛选在结果表中完成；不要假设它存在任意 `--eid` 参数。字段详解和工具操作见 [注册表与事件解析工具](/tool/forensic-registry-tools/)。

## 04 PowerShell 与 Sysmon

PowerShell 4103 是模块日志，4104 是脚本块日志；长脚本可能分多条消息，要按 ScriptBlockId 和 MessageNumber/MessageTotal 重组。转录、PSReadLine 历史、进程参数可互证，但不是所有命令都被完整记录。

| Sysmon ID | 线索 | 核验重点 |
| --- | --- | --- |
| 1 / 5 | 进程创建 / 结束 | ProcessGuid 优先于可能复用的 PID |
| 3 | 网络连接 | 是否开启该事件采集；与进程关联 |
| 7 / 8 / 10 | 镜像加载 / 远程线程 / 进程访问 | 合法软件也可能触发，检查调用链 |
| 11 | 文件创建 | 路径、进程、后续删除或替换 |
| 12 / 13 / 14 | 注册表对象、值设置、重命名 | 目标键与持久化位置是否一致 |
| 22 | DNS 查询 | 查询不代表连接或数据传输成功 |
| 23 / 26 | 文件删除相关 | 配置和版本决定是否有归档文件 |

分析已有日志时记录 Sysmon 版本与配置；在检材上新安装 Sysmon 不能补回历史事件。

## 05 缺口、清除与结果表达

记录号跳变可能由筛选、轮转、归档或缺失造成，不能单独认定有人清日志。结合 Security 1102、Eventlog 服务事件、日志元数据、审计策略与外部日志判断。成功登录与随后执行的程序也需要会话或进程关联。

一条结论应包含：**日志路径 → Provider/事件 ID/RecordId → 原始 XML 字段 → UTC 时间 → 关联账户/进程 → 第二类证据**。无法证明会话后的行为时，停在“认证成功”或“会话建立”这一层。

## 06 实战：核对远程交互会话及后续程序

**场景与材料：** Security、System 与 TerminalServices Operational 日志覆盖目标时段，需分析一次远程访问和后续程序。先保全全部通道、归档、Provider 与采集范围，不能只导出筛选后的几行。

### 06.1 按关联标识建立事件链

1. 在 Security 中筛出候选 4624/4625，记录账户 SID、LogonId、登录类型、来源与 XML UTC 时间，网络类型 3 与远程交互类型 10 分开。
2. 核对 RemoteConnectionManager 的认证记录和 LocalSessionManager 的会话建立/断开/重连，以账户、地址、会话及时间共同连接。1149 单项不代替完整交互会话证据。
3. 有 4688/Sysmon 1 时，核对用户/会话、进程标识、父子关系与完整参数。PID 可能复用，Sysmon 有 ProcessGuid 时保留该标识。
4. 沿 PowerShell ScriptBlockId 重组片段，核对实际参数和文件/网络行为，再与其他主机或流量记录交叉印证。

### 06.2 示例判读

认证成功后只有断开事件，没有可用的会话建立和程序日志：先报告认证与断开记录，明确审计范围，不猜测执行了哪些程序。若 4624 类型 10 与会话事件、进程记录一致，可描述对应会话中的程序启动；是否由某自然人操作仍需额外身份材料。

日志有 1102 时记录清除账户与时间，并核对归档、系统日志和外部记录。记录号间断本身可能由过滤或轮转造成，不能作为清除的唯一依据。
