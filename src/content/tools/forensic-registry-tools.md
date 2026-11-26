---
title: 注册表与事件解析工具
summary: 使用 Registry Explorer、RECmd、RegRipper 和 EvtxECmd 离线解析系统与用户痕迹。
module: Forensics
topic: 系统与用户痕迹
locationPaths: ['D:\CTF_MISC_Tools\Forensics\RegistryExplorer', 'D:\CTF_MISC_Tools\Forensics\Event Log Explorer']
sourceIds: [web-forensics-wiki-registry, web-forensics-wiki-events, web-hello-memory]
updated: 2026-10-01
---

## 1. 材料与工具选择

保留 Hive、对应 `.LOG1/.LOG2` 和用户归属；EVTX 保留通道名与归档。将材料复制到工作目录再解析。Registry Explorer 和 Event Log Explorer 的目录已定位，其余工具按用途列出，使用前另行确认是否安装与版本。

| 工具 | 适合任务 | 输出与边界 |
| --- | --- | --- |
| Registry Explorer | 查看 Hive、键值、LastWrite、书签，重放事务日志 | 重放会产生新的解析状态，保留前后副本 |
| RECmd | 单键查询、批量规则、CSV 导出 | 记录 Batch 文件及工具版本 |
| RegRipper 3 | 以对应 Hive 插件提取常见痕迹 | 不自动重放事务日志；先准备合适的 Hive 副本 |
| EvtxECmd | 批量离线 EVTX 解析 | 保留完整 XML、通道、Provider 和 RecordId |
| Timeline Explorer | CSV 筛选和时间排序 | 显示排序不改变事件真实语义 |
| Event Log Explorer / 事件查看器 | 人工查看事件详细内容 | 不只截图概览，保存记录字段 |

## 2. Registry Explorer 的检查顺序

1. 打开工作副本的 SYSTEM、SOFTWARE、SAM 或用户 Hive，确认解析状态和 Hive 类型。
2. 若存在事务日志并提示重放，保留未重放版本，再在另一副本中重放；记录工具版本与输出位置。
3. SYSTEM 先读 `Select\Current`，选对应 `ControlSet00n`；离线 Hive 没有固定的 CurrentControlSet 实体。
4. 按问题查看账户、USB、网络、UserAssist、ShellBags、启动项等。导出键值、LastWrite 和证据位置。
5. 用 EVTX、文件系统、快捷方式或浏览器记录复核。SAM 用户字段、UserAssist 计数和 ShellBags 时间各有不同含义。

## 3. RECmd 与 RegRipper

RECmd 为 Windows 命令行程序。批量规则的实际位置以所用版本为准；`--bn` 导出需要 `--csv` 指定目录。

```powershell
RECmd.exe -f .\work\SOFTWARE --kn "Microsoft\Windows NT\CurrentVersion"
RECmd.exe -d .\work\hives --bn .\BatchExamples\Kroll_Batch.reb --csv .\output
```

RegRipper 在 Kali/Linux 依赖相应 Perl 环境，先列插件，再使用匹配的插件/配置集合。下例 `samparse` 针对 SAM，`system` 是该版本可提供的插件集合；实际名称以 `-l` 与帮助为准。

```bash
perl rip.pl -l
perl rip.pl -r ./work/SAM -p samparse > ./output/sam.txt
perl rip.pl -r ./work/SYSTEM -f system > ./output/system.txt
```

报“键不存在”时核对 Hive、账户、系统版本、ControlSet 和事务状态。不同语言下组名可能变化，使用 SID/RID 关联，不仅按 Administrators 字符串检索。

## 4. EVTX 批量分析

```powershell
EvtxECmd.exe -d .\work\Logs --csv .\output --csvf events.csv
Get-WinEvent -Path .\work\Security.evtx -MaxEvents 20 |
  Select-Object TimeCreated, Id, RecordId, ProviderName
```

先查 [Windows 事件日志与登录追踪](/knowledge/forensic-windows-logs/) 的事件链，再筛选结果表。保留解析失败和覆盖缺口；日志 RecordId 间断、最后修改时间变化或空结果均不能单独证明清除。

## 5. 输出复核

对每个结果保存 `Hive/日志路径、键/记录、值名或事件字段、原始时间、转换方式、解析版本、关联证据`。完整知识路径见 [注册表取证](/knowledge/forensic-registry/)。
