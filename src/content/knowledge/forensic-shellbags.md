---
title: "ShellBags 取证：目录浏览痕迹与 ShellBags Explorer"
summary: "定位用户目录浏览线索，分清BagMRU、MRU与时间来源，详解离线SBE操作、批量导出和多证据复核。"
module: "Forensics"
track: "计算机取证"
topic: "系统与用户痕迹"
tags: ["文件系统", "时间线"]
status: "已整理"
sourceIds: ["web-usb-usb-cases-pullega-shellbags", "web-shellbags-ms-ir-guide", "web-shellbags-ms-shell-namespace", "web-shellbags-lo-2014", "web-shellbags-libyal-winreg", "web-shellbags-libfwsi-format", "web-shellbags-carvey-2012", "web-shellbags-ms-key-lastwrite", "web-shellbags-ez-issue22", "web-shellbags-kobzar-2025", "web-shellbags-zhu-dfrws2009", "web-shellbags-eztools-home", "web-shellbags-ez-sbe-manual", "web-shellbags-ez-sbecmd-manual", "web-shellbags-powershell-import-csv"]
challengeIds: []
relatedIds: ["forensic-registry", "forensic-usb-evidence", "forensic-windows-artifacts", "forensic-guide-computer"]
updated: "2026-10-04"
---

## 01 ShellBags 是什么：先定位目录，再解释行为

**ShellBags 是 Windows Shell 为记住目录及命名空间对象的视图状态而保存的一组用户级注册表记录。** 它的本职是记住图标、排列、视图等界面状态，取证价值在于留下目录名称、层次、对象类型、部分目标元数据及相关键的更新时间。它不是逐次访问日志，也不是文件读取日志。

目录记录本身不能证明目录内某个文件被打开、阅读、复制或上传。

遇到“用户浏览过哪个目录”“移走的 U 盘上曾有什么目录”“删除目录还能找到什么痕迹”等问题，先查 ShellBags；遇到“谁打开了某文档”“复制了哪些文件”“是否上传给外部服务器”，必须增加文件级、应用级或网络级证据。

| 想回答的问题 | ShellBags 可以提供什么 | 还需要什么 |
| --- | --- | --- |
| 该用户配置曾保存哪些目录位置 | 路径、层次、Shell Item 类型和用户 Hive 归属 | SID、ProfileList、账户会话及配置迁移情况 |
| 当前不存在的目录是否有历史线索 | 保留的名称、父子关系与元数据快照 | 原卷、删除目录项、MFT/USN、回收站或历史快照 |
| 是否与可移动介质目录发生过 Shell 交互 | 盘符/卷节点和后续目录链 | 设备实例、卷标识、接入时期与用户级挂载痕迹 |
| 是否与网络位置发生过 Shell 交互 | UNC、网络节点或映射盘路径 | 映射关系、本地文件痕迹及服务端登录/访问日志 |
| 某个文档是否被打开、复制或上传 | 文档所在文件夹的背景线索 | LNK、Jump List、应用 MRU、文件操作日志、内容哈希及网络证据 |

Shell Namespace 不是单纯的磁盘目录树。工具显示的 `Desktop\My Computer\E:\Project` 包含桌面与“此电脑”等命名空间对象，不等于磁盘上有一个名为 `Desktop\My Computer` 的物理目录。控制面板、GUID 对象、MTP 设备等也可能出现在树中。

压缩包被资源管理器作为“文件夹”浏览时可留下此类记录；是否支持某归档格式取决于 Windows/扩展组件。出现归档路径不证明已解压，不证明内部文件被阅读。更改目录图标等属性交互也可能产生记录，因此“条目存在”与“进入并阅读目录内容”仍须分开。

**优先结论：目标用户 Hive 中存在某路径/对象的 Shell 状态记录。** 进一步的用户交互、时间和文件操作结论，都要列出条件和对应证据。命令行、PowerShell 或 WSL 中的目录浏览不构成同类 GUI 痕迹的必然来源。

## 02 从哪里取：Hive、用户和 Windows 版本

### 02.1 两个用户配置单元同时检查

| 检材文件 | Windows 中的常见物理位置 | 作用与提取要求 |
| --- | --- | --- |
| `NTUSER.DAT` | `C:\Users\<账户>\NTUSER.DAT` | 用户配置；保存本用户的相关 Shell 分支及其他最近活动 |
| `UsrClass.dat` | `C:\Users\<账户>\AppData\Local\Microsoft\Windows\UsrClass.dat` | 用户类注册表；现代 Windows 的重要 ShellBags 位置，不能只查 NTUSER |
| 对应日志 | 同目录的 `NTUSER.DAT.LOG1/.LOG2`、`UsrClass.dat.LOG1/.LOG2` 等实际存在文件 | 事务恢复材料；同一批次、同一用户、同一快照一并取得 |
| `SOFTWARE`、相关会话记录 | `Windows\System32\config` 及相应日志 | Windows build、ProfileList 的 SID/用户目录映射与用户归属 |

上表是**检材里的位置**，不是让分析机当前用户 Hive 代替附件。一个镜像中可能有多个账户、多个系统安装或历史快照；每份 Hive 记录 `镜像/分区、原路径、SID、采集时期、大小、SHA-256`，不同账户分别保存。

### 02.2 离线 Hive 内的查找路径

以下路径不加 `HKCU`，末尾分别查 `BagMRU` 和 `Bags`：

| 适用范围 | Hive 与首查分支 | 条件 |
| --- | --- | --- |
| Windows XP | NTUSER：`Software\Microsoft\Windows\Shell` 与 `Software\Microsoft\Windows\ShellNoRoam` | 两个分支都查；不要把 XP 的更新规律套到新系统 |
| Vista、7、8、8.1 | NTUSER：`Software\Microsoft\Windows\Shell`；UsrClass：`Local Settings\Software\Microsoft\Windows\Shell` | 记录可能分散在两个 Hive，具体对象类型和留存随版本不同 |
| 旧版 64 位候选 | UsrClass 中的 `Wow6432Node\Local Settings\Software\Microsoft\Windows\Shell` 等实际存在分支 | 用于补查，不代表所有 64 位系统都会有该位置 |
| Windows 10、11 | 优先 UsrClass：`Local Settings\Software\Microsoft\Windows\Shell`，兼查 NTUSER 的 Shell 分支 | 先确认 build，再查实际键；不能承诺每个目录、每次操作都留下记录 |

在线注册表可能表示为 `HKCU\Software\Classes\Local Settings\...` 或相应 `HKU\<SID>_Classes` 视图；离线读 UsrClass.dat 时，其根内直接从 `Local Settings` 起找。把在线根名拼进离线键路径，会造成“找不到键”的假阴性。

缺少 UsrClass.dat、键不存在、键存在但没有可解析条目、工具报错是四种不同情况。不存在记录不等于从未访问；还要考虑采集范围、日志、版本、缓存维护、注册表清理及解析器支持。

## 03 Bags、BagMRU 与目录重建原理

### 03.1 两组键的分工

| 对象 | 含义 | 容易混淆的地方 |
| --- | --- | --- |
| `BagMRU` | 保存 Shell 位置的分层结构和同级 MRU 顺序 | 不是一张带每次打开时刻的访问清单 |
| `Bags` | 保存对应视图槽的界面设置 | 视图键更新时间与目录交互推导时间分开 |
| 数字值名 `0`、`1`、`2` 等 | 该父键下对应子对象的二进制 Shell Item | 编号不是时间、访问次数或 MRU 排名 |
| 同名数字子键 | 描述相应子对象下面的进一步结构 | 父键数值 `2` 和子键 `\2` 要连接阅读 |
| `MRUListEx` | 4 字节小端编号数组，以 `FF FF FF FF` 结束 | 数组中的第一项是当前父键最近子项；MRU Position=0 不等于值名=0 |
| `NodeSlot` | 指向 `Bags\N` 的视图槽 | 不是访问次数，不是文件 ID，也不是 MRU Position |

例如父键 `BagMRU\0` 的值 `2` 描述 Project 对象，子键 `BagMRU\0\2` 中的值 `5` 描述 Reports。沿父值→同名子键→下一层值把名称串接起来，才形成目录链。孤立搜索到 Reports 字符串，不足以说明其父目录、盘符或用户。

### 03.2 Shell Item、PIDL 与长短文件名

Shell Item 是一个命名空间对象的序列化描述；PIDL 是由项目标识构成的列表表示。不同类型记录有不同结构：根 GUID、盘符/卷、网络位置、文件系统项目、委托对象、MTP 等不能用一个固定偏移模板全解。

文件系统项目可能包含短名，扩展块可补长名和其他字段。例如适用的 `0xBEEF0004` 扩展块可能包含创建/访问时间、长名及 MFT 引用信息。字段是否存在受 Shell Item 类型与扩展版本影响；未知项应保留类型、原始字节和 Hive/键位置，不能删掉 GUID 后拼出“看似完整”的路径。

某些项目含 MFT entry number 与 sequence number。二者配合卷身份才有机会与对应目录记录关联；仅凭 entry number 会遇到记录复用，同名目录也可能重建。部分记录的引用字段并不可靠，必须回查目标卷实际 MFT，不把它当无条件有效的文件定位地址。

### 03.3 手工验证 MRUListEx

下面是**自建的字节示例**，不是检材输出。它只验证数组顺序，不计算浏览时间。

```python
# MRUListEx：每项4字节小端，FFFFFFFF终止
import struct

data = bytes.fromhex(
    "02 00 00 00 00 00 00 00 05 00 00 00 FF FF FF FF"
)
if len(data) % 4:
    raise ValueError("MRUListEx length is not a multiple of 4")
order = []
for offset in range(0, len(data), 4):
    value = struct.unpack_from("<I", data, offset)[0]
    if value == 0xFFFFFFFF:
        break
    order.append(value)
else:
    raise ValueError("Missing MRUListEx terminator")
print(order)
```

输出为 `[2, 0, 5]`：值名 `2` 的 MRU Position=0，值名 `0` 的排名反而是 1。这个顺序只针对一个父键；不能跨不同父键比较后声称得到全机浏览顺序，也不能从数组长度推出目录访问次数。

## 04 时间判读：四类时间分别保存

### 04.1 日期列的来源比列名更重要

| 字段或时间 | 数据来源 | 正确解读 | 不应解释为 |
| --- | --- | --- | --- |
| Created On / CreatedOn | Shell Item/适用扩展块保存的目标创建元数据 | 对象元数据快照 | 用户第一次打开该目录 |
| Modified On / ModifiedOn | Shell Item 保存的目标修改元数据 | 记录内的目标修改状态 | 本次浏览、复制或删除时刻 |
| Accessed On / AccessedOn | Shell Item/扩展块保存的目标访问元数据 | 保存的元数据，受更新策略和缓存影响 | 每次读取目录或内部文件的记录 |
| BagMRU LastWrite | 注册表键自身的最后写入时间 | 该键/值的更新；回查是哪一级键 | 所有孩子的最后打开时间 |
| Bags 下相关 LastWrite | 视图设置键的更新时间 | 对应设置发生更新的线索 | 可以直接替代 BagMRU 的时间 |
| First Interacted / FirstInteracted | 解析器基于键时间与树结构推导 | 条件成立时保留的早期交互线索 | Hive 内原生“第一打开事件”，或一生首次访问 |
| Last Interacted / LastInteracted | 解析器结合 MRU 顺序和相关键时间推导 | 条件成立时的最近交互线索 | 每次访问都会刷新的完整事件记录 |

注册表键没有独立“最后读取时间”。键 LastWrite 按键/值的更新解释，不能直接分配给键中每一个值。Shell Item 元数据也不是目标目录的实时监控；它与当前 MFT 不一致时，可能只是采集时机、缓存状态或对象重建不同，不应立即认定改时间。

### 04.2 First/Last 的条件推导

1. **First Interacted** 常利用目标对应最底层键、没有进一步子对象时所保留的 LastWrite。后续结构变化会使条件失效；不是所有节点都能推导。
2. **Last Interacted** 常对父键中 **MRU=0** 的子对象，结合父键 LastWrite 得到候选时间。必须核查该父键，而不是把当前对象子键或 Bags 设置键的时间混用。
3. 重复进入本来就在 MRU 首位的目录时，顺序没有变化，相关键时间可能不更新。只存在一个孩子的情况尤其容易产生误读。
4. 同级其他节点不一定有可推导的 Last Interacted。空值表示当前数据与规则没有给出该列，**不是“没有访问”或“只访问过一次”**。
5. 工具版本、恢复条目与不同 Shell Item 类型可能影响字段。对关键结论保存父/子键路径、值名、MRUListEx 原值和各自 LastWrite，并回查实际解析规则。

### 04.3 编码、时区和显示精度

Registry LastWrite 使用 FILETIME；某些 Shell Item 字段也可用 FILETIME。常见 file-entry Modified 和 `0xBEEF0004` Created/Accessed 使用 FAT/DOS 编码，秒字段具有 **2 秒**粒度。格式研究将这些常见 Shell 字段标为 UTC；“FAT/DOS 编码”不能自动等同“本地时间”。其他变体另查定义，不一刀切。

先用 UTC 对齐，再按问题所需时区转换一次。工具显示毫秒、小数七位，并不会为原始 2 秒字段增加真实精度。历史夏令时按事件日期处理，不能一直套当前分析机偏移；空白、零值、缺失或明显异常日期单独标记，不把默认显示值填入活动时间线。

## 05 版本差异与常见考点

### 05.1 Windows 11 的结果不能照搬旧版口诀

Windows 10 旧实验曾观察到单击选择目录也可创建条目；这些结论必须保留实验环境。一个 Windows 11 Pro **24H2 / build 26100.3194** 的公开对照实验，在目标目录事先没有条目的条件下，观察到主动导航建/更新记录，而 mkdir、单击、复制和移动没有相同效果；从桌面双击确实进入目录时，工具仍可显示 `HasExplored=False`。

这不是所有 Windows 11 build 的统一保证，但足以说明 **HasExplored=False 不能作为未浏览的证明**。HasExplored 是解析器展示的状态标志，不应望文生义当成独立行为审计。需要判断具体触发条件时，在同版本干净环境做对照实验，而不是在检材上浏览目录来“验证”。

### 05.2 问题到证据的速查

| 常见考点 | 操作路线 | 输出与判分关键 |
| --- | --- | --- |
| 浏览过哪个目录或归档位置 | 正确用户两类 Hive→对应 BagMRU 根→重建 Shell 链 | 完整路径、Hive、SID、对象类型；不只报文件夹名 |
| 最新交互的是哪个同级目录 | 定位共同父键→读取 MRUListEx→匹配首项 | 排名与值名分开；排序不自动给出完整日期 |
| 首次/最后交互时间 | 回查推导字段、父/子键 LastWrite 和 MRU 条件 | 时间来源、UTC/当地显示及推导限制 |
| U 盘或外接盘目录 | 找到盘符/卷节点与目标目录→关联设备、卷及时期 | 盘符不是序列号，不能只报 E: 就认定某个设备 |
| 删除或已经离线的目录 | 保留 Shell 路径→查实际卷、MFT/USN/回收站/快照 | “当前未找到”与“已删除”分开，旧目录残留不恢复文件内容 |
| 网络共享或映射盘 | 找 UNC/网络节点→核对映射、用户会话与服务端日志 | 不把缓存路径当网络认证成功或传输证明 |
| 是否打开过目录内文档 | ShellBags 提供父目录背景→LNK/Jump List/应用 MRU | 文件级对象身份、路径、应用、记录时间及卷信息 |
| 是否复制/打包/外传 | 源与目标卷、MFT/USN、压缩程序/应用、网络记录组合 | ShellBags 不提供统一 COPY/UPLOAD 事件或字节数 |
| 某用户是否必然操作过 | Hive→SID→账户/会话，检查迁移与恢复情况 | 账户配置证据不直接确认实际操作者身份 |
| 为什么无记录/无时间/有未知项 | 核对范围、日志、版本、键根、恢复状态和解析错误 | 不用“从未访问”填补缺失数据 |

## 06 可重复的离线取证流程

1. **明确问题与检材层级。** 是磁盘镜像、导出的 Hive、注册表报告还是内存中的注册表片段？报告 CSV 不能替代原 Hive；只有内存片段时完整程度和恢复范围单独注明。
2. **锁定系统与账户。** 用 SOFTWARE/build、ProfileList、用户目录及会话记录建立映射，两个用户 Hive、相关日志、历史快照分别编号。
3. **保全输入。** 从镜像按文件原路径导出，不启动检材系统、不在检材目录内点开目标文件夹。保留只读原件和工作副本，先计算哈希。
4. **评估事务状态。** dirty Hive 不等于无价值；使用支持事务恢复的注册表解析器或 RLA 在副本恢复，记录日志是否采用、前后哈希与工具输出。不要给当前 Hive 拼上另一快照的 LOG1/LOG2。
5. **覆盖所有适用根。** 先查 UsrClass/NTUSER 的实际分支，再以 ShellBags Explorer 重建层次；保留 unknown/parse error/恢复条目，不只保留解析成功的名字。
6. **定位目标并回查。** 保存 Absolute Path、Bag Path、Slot、NodeSlot、MRU Position、类型、父/子键 LastWrite 及 MAC 原值。在注册表查看器核对最关键的二进制值与键关系。
7. **建立交叉证据表。** 目录、用户、卷、文件与时间分别关联。强结论要求多条证据支持，缺失环节在结果表中留空而不是猜测。
8. **输出可复核结果。** 导出完整 CSV 与筛选结果，记录筛选条件、行数、字段、分隔符、时区、版本、来源与恢复状态；保存解析日志及可追溯截图。

下面的 Windows 工作副本模板只复制明确文件，不重放事务日志，也不采集分析机注册表。Evidence 目录应已从目标镜像取得对应文件；为每次分析使用新的空工作目录，不覆盖已有分析副本。

```powershell
$src = 'C:\Case\Evidence\UserA'
$dst = 'C:\Case\Working\UserA'
New-Item -ItemType Directory -Path $dst -Force | Out-Null
$names = @('NTUSER.DAT', 'NTUSER.DAT.LOG1', 'NTUSER.DAT.LOG2',
           'UsrClass.dat', 'UsrClass.dat.LOG1', 'UsrClass.dat.LOG2')
foreach ($name in $names) {
    $source = Join-Path $src $name
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        Get-FileHash -LiteralPath $source -Algorithm SHA256
        Copy-Item -LiteralPath $source -Destination (Join-Path $dst $name)
    }
}
Get-ChildItem -LiteralPath $dst -File | Get-FileHash -Algorithm SHA256
```

若目标软件会写入或恢复工作 Hive，原件与派生件不能共用同一记录名称。历史快照用于比较状态变化：新增条目发生于两次可信快照之间，不等于能从快照差异推出唯一精确访问时刻。

## 07 ShellBags Explorer：用途、环境与加载

### 07.1 GUI 与 CLI 不同

**ShellBags Explorer（SBE）** 的图形界面适合查看层次、逐节点详情、类型图标、搜索与筛选；**SBECmd** 是同系列的独立命令行程序，适合批量解析和导出。不要给 `ShellBagsExplorer.exe` 套 `SBECmd.exe` 的参数，两者也不必同时安装才能使用。

以下 GUI 菜单按 2026.5.0 的静态文字核对，交互步骤按工具文档核验；未运行 GUI 或真实 Hive 解析。命令行部分也是文档核验的操作模板，不能把它当作真实检材实测结果。

2026.5.0 GUI 的运行配置采用 **.NET 9 Windows Desktop Runtime**；旧版手册中针对 .NET Framework 的环境要求不能直接套到这一代 GUI。仅有普通 .NET Runtime/SDK，不代表桌面组件齐全。官网的 CLI 同时提供 .NET Framework 与 .NET 9 版本，下载或使用时核对实际构建；以本机版本、runtimeconfig、Help/About 与命令行帮助为准，不混用版本截图。

工具用于已取得的离线用户 Hive，不直接把 E01/VMDK/RAW 当作 Hive 打开。先由镜像工具导出 NTUSER/UsrClass，必要时处理事务日志。能读取锁定文件不意味着 live 模式不会改变环境，也不意味着离线分析需要管理员权限；镜像、采集和解析三步分别记录。

### 07.2 打开前设置

1. 启动 `ShellBagsExplorer.exe`，核对版本。用于离线检材时不要选择分析机的 live Registry 作为目标。
2. 在 **Tools → Options** 核对 **Default time zone**，先设 UTC，再加载数据。更改时区后按程序提示重新加载 ShellBag 数据；不要只改设置就沿用旧画面截图。
3. 核对自动提交未知 GUID/Shell ID 的选项。离线工作流先关闭 **Automatically submit unknown GUIDs and Shell IDs**，避免把检材片段自动发往外部。
4. 核对 **Use CSV separator / Use comma separator (vs. tab) when exporting**。CSV 菜单名称不保证实际用逗号；以后读取导出文件必须检查表头和实际分隔符。
5. 按账户/快照组织工作目录，同一来源日志与派生 Hive 放到可识别位置；保存设置与来源记录。

### 07.3 加载正确 Hive

使用 **File → Load offline hive** 入口，选择工作副本的 `UsrClass.dat` 或 `NTUSER.DAT`。加载后核对显示的来源、识别类型、统计与错误提示，再检查树根。可在 **Tools → Show Messages window** 查看消息、在 **Show Details window** 查看详情；不同账户/不同快照分别分析，程序支持的多来源显示也不能自动替你确认 SID 与采集时期。

遇到 dirty 提示，先处理事务状态。某版程序提示按住 SHIFT 可加载 dirty Hive，这只是跳过相应 dirty 检查，不是日志 replay、损坏修复或数据完整性证明。未经恢复的结果保留“主 Hive 原始状态”标签，与恢复后结果分开比较。未知 Shell Item 或 parse error 回查原始字节，不能为了得到一张整洁表就忽略它们。

## 08 ShellBags Explorer：树、详情、筛选与导出

### 08.1 看完整层次，而不是只搜字符串

加载后通常以树视图、表格和详情区域组织数据。手册中的操作是：左键选节点，查看其详情与直接子项；对节点执行递归展开可查看下方各级数据。右键递归与左键选中可能对应不同范围，观察递归标识/表格内容后再搜索，避免把“当前只有一个节点”的结果误当全 Hive。

先辨认 Desktop/This PC、盘符/卷、网络节点、控制面板和 MTP 等类型。沿树展开 `E:`→Project→Reports，核对实际父节点；图标只是分类提示，不能替代类型与原始结构。对同名 Reports 比较来源 Hive、父路径、类型和键路径，不按名称去重。

树与表格提供查找/过滤；手册的 `Ctrl+F` Find panel 可用于快速发现名称。找到候选以后仍要查看完整路径与详情。准备深层目录检索时先选择合适的递归范围；必要时从根查看全体再过滤，否则可能漏掉当前节点之外的同名目录。

在 Absolute path 或 Value 列标题下的 filter cell 输入关键字，手册中的默认匹配为 contains；在匹配条件菜单核对是包含、相等还是其他规则。清除某列过滤与清除全部过滤分开。单击列标题排序，再单击反向；需要多列排序时按手册使用 Shift 配合第二列；按用户/类型等分组可将列标题拖到 grouping 区。单击网格记录查看 Details/Hex，右击记录可定位树节点；反复确认当前范围，不把表格操作当注册表修改。

### 08.2 关键输出字段如何读

| 信息组 | 重点字段/界面概念 | 判读动作 |
| --- | --- | --- |
| 来源与定位 | Hive/Source、Bag Path、值名或 Slot | 保存 Hive 和注册表键路径，可在另一注册表查看器复查 |
| 层次 | Absolute Path、Value/Name、Shell Type | 区分命名空间路径与磁盘路径，核对父子链 |
| 排序与视图 | MRU Position、Node Slot | 同级顺序和 Bags 视图槽分开，不当成次数 |
| 数量 | ChildBags / 子项统计 | 是当前记录结构内的子 Bag 数，不是磁盘实际文件数，也不是访问次数 |
| 时间 | Created/Modified/Accessed、First/Last Interacted、键 LastWrite | 分四类时间；回查父键与当前键，统一时区 |
| 对象关联 | 文件系统类型、适用 MFT entry/sequence 等 | 回查同一卷的目录 MFT，缺失字段留空 |
| 状态 | HasExplored、Recovered、Deleted、Unknown、Parse error 等实际显示 | 状态不是审计结论；恢复/未知项保留原始依据 |

**Recovered ShellBag / (Deleted) 指向恢复的注册表键或值时，不表示对应磁盘目录必然已经删除。** 与“目录被删除后正常 ShellBags 仍保留”也是两件不同的事。报告分别写注册表恢复状态和文件系统对象状态。

如果只有 First 没有 Last，不能答“仅打开一次”；只有 Last 没有 First，也不能答“首次就是这时”。如果时间或路径冲突，先排除不同账户、同路径重建、不同快照、父/子键误取、时区、缓存与解析差异。

### 08.3 按问题筛选

| 目标 | 建议筛选方式 | 必查的上下文 |
| --- | --- | --- |
| 某 U 盘目录 | 盘符/卷节点递归，再按 Project/Reports 等名称或路径过滤 | 卷身份、当时盘符、用户及采集时期 |
| 某 UNC 共享 | 网络节点或路径字段中的服务器/共享名称 | 映射盘、账户会话、服务端记录 |
| 异常或已不存在目录 | 名称/路径候选，结合实际文件系统查找 | 不把恢复键标志当删除目录证据 |
| 时间范围 | 分别筛 First、Last 或原始键时间 | 标明筛哪一列；空值不会因范围筛选而变成不存在 |
| 只有某类对象 | 按 Shell Type 分类/排序/分组 | 虚拟对象与物理目录不混写 |

保留未筛选的完整结果。关键词匹配是寻找线索，不是唯一身份验证；短名、GUID、别名、不同路径写法、未解析项目都可能导致名字搜索漏项。

### 08.4 导出与复核

使用 **File → Export → CSV** 对应入口保存结果。手册区分 CSV 的可用列、Excel 的网格可见列与 json 的完整数据，隐藏表格列并不自动等于删掉导出字段。导出前记下来源、当前范围、递归状态、过滤条件和行数；导出后实际数行并核对几条完整路径。不要假定 GUI 当前过滤一定限定所有导出入口的范围。

至少留两份：完整导出用于复查，按问题筛选的副本用于答题/报告。检查 UTF-8/实际编码、逗号或 TAB、引号包围字段、空日期和时区；不要直接用逗号字符串 split 去读含逗号的路径。保存 Messages 中的错误/处理信息、工具版本、CSV 哈希和关键节点截图，截图不能替代 CSV 与原 Hive。

## 09 SBECmd：批量导出与结果复查

SBECmd 是辅助批量方式，GUI 仍适合检查目录关系。以下为作者命令行使用方式的操作模板，路径代表已导出的工作副本；先执行本机帮助核对实际构建，不把模板当成已经解析了某检材。

```powershell
& 'C:\Tools\SBECmd\SBECmd.exe' --version
& 'C:\Tools\SBECmd\SBECmd.exe' --help
& 'C:\Tools\SBECmd\SBECmd.exe' -d 'C:\Case\Working\UserA' --csv 'C:\Case\Reports\UserA'
& 'C:\Tools\SBECmd\SBECmd.exe' -d 'C:\Case\Working\Users' --csv 'C:\Case\Reports\Batch'
```

| 参数 | 用途 | 使用条件 |
| --- | --- | --- |
| `-d` | 指定包含离线 Hive 的目录 | 单 Hive 解析时用仅放目标 Hive 与同批日志的独立目录；批处理控制包含的用户与历史版本，核对扫描日志与实际识别数 |
| `--csv` | CSV 输出目录 | 用独立报告目录，不覆盖证据文件 |
| `--csvf` | 自定义 CSV 文件名 | 实际命名行为按当前帮助核对；多 Hive 基线保留不同来源，不随意强制同一个输出名 |
| `--nl` | 忽略事务日志的开关，默认 false | true 是忽略日志，绝不是启用 replay；仅作明确标注的另份对照结果 |
| `--dedupe` | 生成去重视图 | 先保留各 Hive/快照基线；不能用同名路径直接判断重复 |
| `--dt` | 输出日期时间格式 | 显示格式不增加原始字段精度，也不自动改变时区 |
| `--debug` / `--trace` | 增加诊断输出 | 用于异常或未知结构复查，保留运行日志 |
| `--version` / `--help` | 核对程序构建和参数 | 实际使用前先检查，不用另一工具的参数模板替代 |

目录输入 `-d` 是此处核对的离线方式，不套用其他 Zimmerman 工具常见的单文件参数。若只解析 UsrClass.dat，把它和对应日志放到独立输入目录；不拿目录模式当文件模式。旧资料中的时区选项名称有差异，先核对当前帮助，本文不列未经本机构建确认的时区别名。历史副本、恢复项目和重复结构是取证信息；首次分析不要因为路径相同就删掉不同 Hive/快照记录。一次成功退出也不表示所有对象都解析成功，仍需检查错误、识别数和 CSV 的实际行数。

先核对导出表头，字段拼写按本次文件映射，不照抄另一版本截图。可以用 Timeline Explorer 分组/筛选 CSV，或使用 `Import-Csv` 读取明确分隔符的导出件；按列类型排序，别把日期文本和空值直接当业务顺序。

```powershell
$report = 'C:\Case\Reports\UserA\SAMPLE_usrClass.csv'
Get-Content -LiteralPath $report -TotalCount 2
$rows = Import-Csv -LiteralPath $report -Delimiter ','
$rows.Count
$rows | Select-Object -First 3 | Format-List *
Get-FileHash -LiteralPath $report -Algorithm SHA256
```

这段代码中的 SAMPLE_usrClass.csv 需替换为实际导出文件名：先看首两行，再读取逗号分隔文件。如果实际是 TAB，改为 `-Delimiter ([char]9)`；其余编码或字段差异先确认再处理。批处理报告必须保留每条记录的来源列或独立输出目录，合并后仍能回到同一 Hive/键。

## 10 实战：从目录残留到可核查结论

### 10.1 自建场景 A：E: 上的 Reports 现在找不到

**材料与目标：** 一份 Windows 镜像、某用户两类 Hive、SYSTEM/SOFTWARE、用户 LNK、相关卷的 MFT/USN。自建训练设定：解析结果有 `E:\Project\Reports`，当前镜像没有同一路径。目标分别是找历史目录、识别卷、检查文档访问；不是直接给出“用户复制并删除了文件”。

1. 确认 Hive 属于目标 SID；在 SBE 中从盘符节点递归定位目录，保存 Bag Path、Slot、NodeSlot、类型、时间与来源。
2. 在注册表查看器回查父键数字值与 MRUListEx，把目录元数据时间和交互推导时间分列。若仅有 MRU=0 和父键 LastWrite，结论保留推导条件。
3. 将 E: 与相关时期卷记录、设备实例和用户级挂载信息关联；盘符复用时不能把当前 MountedDevices 状态固定当成全部历史。
4. 有可用 MFT 引用时同时核对 entry 与 sequence，并定位同一卷。无对应记录可能是卷缺失、记录复用、对象删除、同路径重建或字段不可靠，不选一个解释来填满表格。
5. 查同一路径下文档的 LNK/Jump List、应用 MRU 和文件系统对象；若只能找到目录 ShellBags，文件打开与复制保持未证实。

| 最终证据状态 | 合适的结论 |
| --- | --- |
| 只有该用户目录 Shell 链 | 该用户 Hive 保存了对应目录位置的历史状态 |
| 增加可信设备/卷/时期映射 | 路径可在限定时期关联到具体卷，而非只凭 E: |
| 增加对象匹配的 LNK/Jump List 等 | 对指定文档存在相应应用或文件交互线索，按各记录含义描述 |
| 目标卷不在检材中 | 不能检验该卷当前对象状态；目录痕迹仍可作线索 |

ShellBags 不包含可恢复的文档正文。恢复文件内容要回到实际卷、删除记录、未分配空间或备份；目录名称残留只是定位入口。MFT 的结构与工具操作见 [U 盘取证](/knowledge/forensic-usb-evidence/)。

### 10.2 自建场景 B：UNC 路径并不等于外传

**材料与目标：** 目标用户 Hive 保存了 `\\fileserver\share\Project` 的网络位置，另有本地会话记录与部分服务器日志。先确认这是 UNC、映射盘还是命名空间对象，再按完整父链定位。

只发现缓存路径时，报告“发现该网络位置的 Shell 状态线索”。认证是否成功查服务器/客户端会话记录；文件是否被读取或写入查对象访问日志、应用记录及实际文件身份；是否外传再看协议、目的端、流量和服务端记录。ShellBags 自身不提供连接成功、传输字节数或内容哈希。

### 10.3 对照实验：验证自己所用 build 的行为

在独立干净 VM 中固定用户、Windows build、工具版本与 UTC，分别安排命令行创建目录、单击选择、双击进入、改变图标、复制/移动、反复访问 MRU 首项等动作；每轮保存两类 Hive 与日志的前后快照。记录实际动作时刻、相关键值变化和工具输出，不能只看一个时间列。

这是一套实验设计，不是已执行的系统行为实测。公开 Windows 11 24H2 结果用于提醒版本差异；它也不能替代你自己的检材 build 验证。

## 11 易错点、检查清单与总结

### 11.1 常见误判的修正

| 误判 | 修正 |
| --- | --- |
| ShellBags 是所有文件打开记录 | 主要分析目录/命名空间交互背景；文档内容访问另查证据 |
| 只提取 NTUSER 就够 | 现代系统重点看 UsrClass，并保存同批日志 |
| MRU Position=0 就是值名 0 | Position 是同父键排序，首项可能是值名 2 或其他编号 |
| NodeSlot 表示访问次数 | 它是视图槽链接，不是计数器 |
| Created On 是第一次进入时间 | 目标元数据与工具 First Interacted 分开 |
| 父键时间属于所有孩子 | 只有符合 MRU 与结构条件的对象才作限定推导 |
| Last Interacted 每次都刷新 | 重复 MRU 首项等情况可能不更新，不是完整访问日志 |
| 空日期、False、无记录证明未访问 | 先查范围、日志、版本、恢复与解析支持 |
| Recovered/Deleted 图标证明磁盘目录删除 | 可能仅是恢复的注册表键/值，磁盘状态需独立验证 |
| 盘符就能唯一确定 U 盘 | 以设备、卷、用户及时期建立关联 |
| UNC 路径证明访问成功或外传 | 缓存路径与网络会话、文件访问、传输日志分开 |
| dirty 加载或 SHIFT 等于修复 | 跳过检查不等于事务重放，派生件与原件分别保留 |
| CSV 必然逗号分隔 | 先检查实际分隔符、编码、范围、行数与时区 |
| 多快照同名目录直接去重 | 保留来源与时期；状态差异可能正是线索 |

### 11.2 一条记录的最低复核清单

`来源镜像/分区 → 用户SID → Hive原路径与哈希 → 恢复状态 → 实际BagMRU根 → 父/子键和数字值 → Shell Item类型 → 完整命名空间路径 → MRU/NodeSlot → 各时间来源/时区 → 文件系统与外部印证 → 结论限制`。

最后记住三个层次：**缓存中有对象**、**在特定条件下支持用户交互**、**有额外证据支持文件操作**。ShellBags Explorer 负责把结构和字段展示清楚；注册表、MFT、LNK/Jump List、设备与网络证据负责把推断变成可核查的证据链。Hive 基础与事务恢复见 [注册表取证](/knowledge/forensic-registry/)，用户文件级痕迹见 [Windows 常见痕迹](/knowledge/forensic-windows-artifacts/)。
