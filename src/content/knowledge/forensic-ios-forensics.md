---
title: "iOS 取证：原理、考点与实战流程"
summary: "辨别提取层级、安全机制和应用身份，解析Plist、数据库、时间与系统痕迹，结合真实比赛建立可复核的证据链。"
module: "Forensics"
track: "手机取证"
topic: "iOS 原理与流程"
tags: ["文件系统", "时间线"]
status: "已整理"
sourceIds: ["web-ios-reference-888171a6e1", "web-ios-reference-9d458e869c", "web-ios-reference-de0656fc72", "web-ios-reference-c1df50aa91", "web-ios-reference-4eb80a97c7", "web-ios-reference-8fdef7fc68", "web-ios-reference-50aa28ec61", "web-ios-reference-83bb3ee720", "web-ios-reference-f9612325f4", "web-ios-reference-624a3d6efc", "web-ios-reference-aa8086607d", "web-ios-reference-c28539d8f8", "web-ios-reference-879ebb9a57", "web-ios-reference-b277096430", "web-ios-reference-2749c43720", "web-ios-reference-457f3cdaa3", "web-ios-usage-7ada2ca0c7", "web-ios-usage-b0bb1c805a", "web-ios-usage-09ef9b1cbf", "web-ios-usage-016f8c816d", "web-ios-usage-3f3259a6ed", "web-ios-usage-67ccde0137", "web-ios-usage-8dec4223d1", "web-ios-usage-899cad5fb8", "web-ios-usage-01949cb94c", "web-ios-usage-d0bf7cdb96", "web-ios-usage-9880b65abc", "web-ios-usage-6c7b8f2355", "web-ios-usage-c6e748a3d6", "web-ios-usage-262208cbbd", "web-ios-usage-50614f659b", "web-ios-usage-44f73ffcb4", "web-ios-usage-d2a1afda89", "web-ios-usage-3445cee28c", "web-ios-usage-92da6b019b"]
challengeIds: []
relatedIds: ["forensic-ios-backup", "forensic-ios-tools", "forensic-guide-mobile", "forensic-mobile-apps"]
updated: "2026-10-04"
---

iOS 取证的核心不是“把手机导入工具后找答案”，而是确认提取覆盖范围，识别系统和应用对象，解释原始字段，再用独立证据核验结论。本模块位于 **Forensics → 手机取证 → iOS 取证**，按以下路线学习：

1. 本篇：基本概念、安全原理、证据位置、常见考点与真实比赛方法。
2. [iOS 备份与系统痕迹分析](/knowledge/forensic-ios-backup/)：已有专项内容，完整保留 Manifest 映射、数据库伴随文件、消息关联和备份导出方法。
3. [iOS 工具与实战：iLEAPP 与 Plist_Editor](/knowledge/forensic-ios-tools/)：解析、人工复核、命令参数、输出及故障排查。

## 01 先辨别检材和采集层级

| 材料或方式 | 实际含义与适用问题 | 最容易误判之处 |
| --- | --- | --- |
| 应用导出、逻辑提取 | 取得特定接口允许导出的记录、附件或报告，适合有明确目标的核对 | 报告不是完整文件系统；无记录可能是未导出 |
| 本地备份 | Finder、Apple Devices 或 iTunes 创建的备份；以清单域和逻辑路径组织文件 | 备份不等于整机镜像，哈希式文件名不等于内容 SHA256 |
| 加密本地备份 | 需要该备份密码；相对未加密备份，可能包含更多密码、Wi-Fi、网站历史、健康和通话信息 | 不包含 Face ID、Touch ID 或设备解锁口令数据；“加密”不表示所有项目齐全 |
| 文件系统提取 | 取得可访问的系统与应用文件树，比赛中经常以 ZIP/TAR 交付 | Full File System 仍不保证所有文件已解密、所有数据库完整或有未分配空间 |
| 物理或磁盘映像 | 面向存储结构、分区和文件系统；能力取决于设备、版本、加密及实际采集方式 | 读取闪存或 APFS 容器不自动获得可读的全部用户数据 |
| 云端材料 | 同步、云备份或服务端导出，覆盖范围依服务和采集时间而异 | 云账户记录、设备本地记录、备份记录不能直接合并为“本机操作” |

本地加密备份与设备文件加密是两个层次，备份密码、屏幕解锁口令、Apple 账户密码也不是同一种凭据。Apple 的备份说明明确区分加密与未加密备份的内容范围；本篇不把比赛额外提供的 keychain 导出视为普通备份的必备文件。[Apple 本地备份加密说明](https://support.apple.com/en-us/108353)

**开题记录表**：材料名称与容器格式、取得方式、采集时间及其时区、设备型号和系统版本、当前锁定状态、目录/压缩包哈希、已知缺失项、是否加密、使用工具版本。处理每个子文件时保留逻辑路径、物理存放路径、导出哈希三者。

## 02 iOS 安全机制如何影响取证

### 2.1 Secure Enclave、文件保护与密钥

Secure Enclave 是 Apple 芯片中的安全子系统，参与受保护密钥及认证操作；它不是一个供取证人员直接读取全部明文的文件夹。Data Protection 通过密钥层级和文件保护类别控制数据可访问性，因此“拿到存储字节”“拿到文件”“拿到已解密内容”应分别描述。具体密码算法会随硬件变化，分析时先确认型号与系统，不靠一个旧设备教程推断所有机型。[Apple Data Protection 原理](https://support.apple.com/guide/security/data-protection-overview-secf6276da8a/web)

| 文件保护类别 | 原理概要 | 分析时应问什么 |
| --- | --- | --- |
| A / Complete Protection | 文件的可读性与解锁状态关联，重新锁定后相应密钥会被清除 | 材料在什么状态、什么时间采集？是否只是解析层面未命中？ |
| B / Protected Unless Open | 支持锁定时对已打开文件继续操作等场景，关闭后的访问规则不同 | 文件在后台写入和重新打开的状态是否一致？ |
| C / Until First User Authentication | 本次开机首次认证后，相应类别密钥不会因普通锁屏立即清除 | 当前锁屏与“从未在本次开机解锁”不能混为一谈 |
| D / No Protection | 不依赖用户口令提供同等级访问保护，但设备上的文件仍受底层加密保护 | “No Protection”不是“闪存上必为明文” |

**BFU**（Before First Unlock）指本次开机首次解锁前；**AFU**（After First Unlock）指已发生首次解锁后的状态。AFU 的手机此刻仍可能锁屏，且不意味着所有保护类别均可访问。这里用 BFU/AFU 解释首次认证的影响，不将其作为保证采集成功的结论。类别规则以 Apple 的定义为准。[Apple 文件保护类别](https://support.apple.com/guide/security/data-protection-classes-secb010e978a/web)

### 2.2 Keychain 与数据库密码

Keychain 用于保存密码、密钥、令牌等小型敏感对象。其数据库的元数据与秘密值有不同保护方式，应用访问还受访问组和授权约束。因此找到一个 keychain SQLite 文件，不等于其中所有密码已被解密。文件系统中的应用数据库也可能另有应用层加密。[Apple Keychain 保护机制](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web)

遇到“应用数据库打不开”时，分开核对：文件是否真正的 SQLite、是否截断、伴随文件是否齐全、是否为 SQLCipher 或其他格式、是否有匹配的已解密 keychain 导出、解析器是否支持该应用版本。iLEAPP 的 `--keychain` 是接收已有 keychain 材料，不是获取设备密钥或通用解锁命令。

### 2.3 APFS 与已删除内容

APFS 是文件系统，具有加密、写时复制、克隆、快照等机制；iOS 存储至少区分系统卷与数据卷。一个普通文件树提取不能自动包含所有快照或未分配空间，也不能据此保证恢复全部已删除文件。不要把 macOS 卷布局或恢复步骤机械套用到 iPhone。[Apple APFS 说明](https://support.apple.com/guide/security/role-of-apple-file-system-seca6147599e/web)

## 03 应用沙盒、身份与目录

应用沙盒限制应用访问自身范围以外的数据，授权的 App Group 允许相关应用共享特定容器。**Bundle ID** 是应用身份标识，**容器 UUID** 是具体目录标识；两者不是同一对象。显示名称可能重复、改名或本地化，不宜作为数据库归属的唯一依据。[Apple 应用保护与共享组](https://support.apple.com/en-euro/guide/security/sec1a976c067/web)

在文件系统材料中，用下面的识别框架，而不是把 UUID 猜成软件名称：

| 对象 | 常见逻辑位置或标志 | 操作与解释 |
| --- | --- | --- |
| 应用程序包 | `Bundle/Application/<UUID>/<App>.app`，内部 `Info.plist` | 查看 `CFBundleIdentifier`、版本和显示名；程序包不等于用户数据库 |
| 应用数据容器 | `Data/Application/<UUID>/` | 结合容器元信息、配置和数据库确认归属，再检查 `Documents`、`Library`、`tmp` |
| 共享容器 | `Shared/AppGroup/<UUID>/` | 用 App Group 标识关联，不因其不在应用数据 UUID 下而漏查 |
| 用户系统痕迹 | `private/var/mobile/Library/` | 消息、健康、浏览器、活动等常见入口，具体路径和格式随版本改变 |
| 应用快照与缓存 | 应用 `Library/SplashBoard/Snapshots`、缓存、媒体目录 | 可补充屏幕内容或广告线索，但文件存在不等于观看次数或当前页面 |

上述 `Bundle`、`Data`、`Shared` 常位于 `/private/var/containers/` 或 `/private/var/mobile/Containers/` 等根路径下，提取工具也可能改写前缀；先对实际目录搜索，再记录完整路径。不要只搜索唯一硬编码根目录。`Documents`、`Library`、`tmp` 的作用是分类提示，不能保证某应用把目标记录放在固定子目录。

应用清点应建立“Bundle ID → 应用版本 → 数据容器 → 共享组 → 账号 → 数据库/附件”映射。重装后容器标识可能变化；同一应用的多个账号和同步设备也应分开，计数前先明确统计对象。

### 3.1 先辨别目录层级与别名

在已取得的文件树中，分别登记系统级 `/Library`、用户 `/private/var/mobile/Library` 和应用容器内的 `Library`；同名目录不代表同一数据范围。Apple 的基础构建使用 `/var → private/var`、`/etc → private/etc` 链接，导出工具则可能保留链接、展开链接或省略根前缀。先看实际链接和采集清单，再统一逻辑路径；不能把两个别名计为两份独立证据，也不要跟随导出中的绝对链接去读分析机的 `/private/var`。[Apple 基础目录与链接构建](https://github.com/apple-oss-distributions/files/blob/main/Makefile)

目录搜索以工作副本为起点；路径缺失时先记录“未取得/未命中”，再核查采集范围与版本。目录名、文件所有者和权限位可以辅助识别对象，但不会解除文件保护类别或应用层加密。

### 3.2 容器归属：元信息和应用状态，而非猜 UUID

- 对取得的 `.com.apple.mobile_container_manager.metadata.plist` 保留父目录 UUID、完整路径及 `MCMMetadataIdentifier`。共享容器记录的值可能是 **App Group 标识**，不能因为报告列名叫 Bundle ID 就当成主应用 Bundle ID；插件容器也须分开登记。该元信息是归属线索，不是指定时间的使用记录。[iLEAPP 容器元信息解析代码](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/appGrouplisting.py)
- 若取得 `mobile/Library/FrontBoard/applicationState.db`，先检查 schema，再解析支持版本的 `compatibilityInfo` BLOB；其中的 `bundleIdentifier`、`bundlePath`、`sandboxPath` 可用于交叉关联。缺失或未成功解档时回查容器及程序包 `Info.plist`，不能由缺少一条映射认定应用从未安装。[iLEAPP 应用状态解析代码](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/applicationStateDB.py)
- 本地备份的 `Manifest.db` 用 `domain / relativePath / fileID` 映射备份文件，**不是文件系统材料中通用的容器 UUID 索引**；按备份篇操作，不在 `Containers` 下假定有同名索引。应用文档目录用 `Documents`，不把误拼的 `Document` 写成通用路径。

## 04 Plist、SQLite 和序列化对象

### 4.1 Plist 不只是文字配置

Property List 是有类型的序列化结构，可为 XML 或 binary plist。常用类型有字典、数组、字符串、整数、实数、布尔、日期和二进制数据；字典的键和值、数组顺序、`true` 与整数 `1` 都有不同语义。XML 中的 `<data>` 通常表示 Base64 编码的字节，不是明文密码标签。[Apple Plist 格式定义](https://github.com/apple-oss-distributions/CF/blob/main/PropertyList.dtd)

典型考点：设备和备份属性、应用配置与账号、数据库密钥线索、数组中的历史值、嵌套 Data。先保留键路径、类型、原始值，再解释。`ProductVersion` 是系统版本，`ProductBuildVersion` 是构建版本，不能相互替代；配置时间也不能直接当成对应行为的发生时间。

看到 `$archiver`、`$objects`、`$top` 和 UID 引用时，应考虑 **NSKeyedArchiver** 对象归档。UID 通常是对象表引用，不是用户身份证号，也不应直接输出为最终业务值。普通 Plist 查看器可显示结构，但不保证已经完成对象关系还原；循环引用、嵌套对象和应用自定义类需要相应解析器或人工核验。[Python plistlib 对 binary plist 与 UID 的支持](https://docs.python.org/3/library/plistlib.html)

### 4.2 SQLite：先看结构，再查字段

SQLite 保存结构化记录，常见于通信、浏览器、定位、健康和第三方应用。数据库主文件、同名 `-wal` 与 `-shm` 应整体保全；主库视图与应用关闭前的已提交状态可能不同。已有备份页提供按清单分别定位这些文件、重命名到同一逻辑基名和只读导出快照的完整方法，本篇不重复导出脚本。

对已保全的工作副本识别格式，用只读连接查看 `.tables`、`.schema` 并执行 `PRAGMA quick_check;`；命令和留痕输出统一见 [工具篇的离线数据库检查](/knowledge/forensic-ios-tools/)，本篇只维护结构与结果判读。

`.schema` 只说明结构，`quick_check` 只检查结构一致性，两者都不能证明采集完整或字段已正确解释。Core Data 数据库中的 `Z` 前缀和外键要按实际模式关联，不猜列名。查询返回零行时，检查版本、库和时间范围、WAL 是否存在、记录是否在 BLOB/其他库中，之后再描述“本材料未检出”。

## 05 时间：纪元、单位与事件语义

Apple Foundation 的参考时间起点是 **2001-01-01 00:00:00 UTC**；Unix 起点是 **1970-01-01 00:00:00 UTC**，两者相差 `978307200` 秒。iOS 材料中两者均可能出现，且单位可能是秒、毫秒、微秒或纳秒。不能因为文件来自 iPhone 就统一加这一偏移，也不能仅靠数字位数断言类型。[Apple Date 参考纪元](https://developer.apple.com/documentation/foundation/date/timeintervalsincereferencedate-swift.property)

| 步骤 | 操作 | 为什么必要 |
| --- | --- | --- |
| 保存原值 | 记录数据库、表、主键、列名、原始数值、NULL/零值 | 转换后仍可回查，不把缺失值转换成真实日期 |
| 确认纪元与单位 | 查该版本解析器、相邻记录和可验证事件 | 对同一字段先确定编码，之后批量处理 |
| 得到 UTC | Apple 秒值加偏移；毫秒/纳秒先换算单位 | 时区偏移与纪元偏移不是同一件事 |
| 展示当地时间 | 用事件地点所需的 IANA 时区，例如 `Asia/Shanghai` | 国外比赛不能默认 UTC+8；有夏令时的地区不能全年固定偏移 |
| 判断语义 | 创建、修改、访问、同步、采集、报告展示分别命名 | “最后同步”不是“最后一次健康活动” |

下载 [只读 Plist 与时间检查脚本](/practice/ios_inspect.py)，在 Kali/Linux 下运行：

```bash
# 以下零值用于验证纪元，属于格式检查，不是比赛记录或答案。
python3 ios_inspect.py time --epoch apple --unit s --value 0 --zone UTC
python3 ios_inspect.py time --epoch apple --unit ns --value 1000000000 --zone Asia/Shanghai
python3 ios_inspect.py plist ./work/Info.plist > ./output/info-typed.json
```

第一条应显示 UTC `2001-01-01T00:00:00+00:00`；第二条 Apple 纳秒值表示参考纪元后 1 秒。脚本要求显式选择单位，不猜业务字段；其时间显示精度为微秒，原始数值仍保留。Windows 若缺 IANA 时区数据，先用 UTC 核验，再配置时区数据，不把本机默认时间强加给证据。

## 06 开题到结论的取证流程

1. **材料保全**：哈希压缩包或镜像；工作副本与输出目录分离。登记采集类型、时间、系统版本、是否加密及已有报告，不先还原到真机改变状态。
2. **识别结构**：备份查 `Info.plist`、`Manifest.plist`、`Status.plist`、`Manifest.db`；文件系统查实际根路径、系统版本和应用容器；单文件先识别格式。
3. **建立目录与账号索引**：按 Bundle ID、共享组、数据库、附件组织材料；区分安装记录、登录配置和真正业务活动。
4. **批量初筛**：以 iLEAPP 解析支持的痕迹，检查日志、版本、命中路径及失败模块。报告空白与材料不存在是不同结论。
5. **人工核对**：Plist_Editor 查看键与数据类型；SQLite 检查模式、主键、关联、WAL 与删除/同步状态。回到原始记录，不只抄报告搜索结果。
6. **统一时间与统计口径**：先确定纪元、单位、时区、范围，再筛选和聚合；合计金额先核验币种及最小单位，应用时长先定义累计还是单次。
7. **交叉取证**：聊天+附件、照片+视频、健康时间段+定位、配置账户+业务数据库，优先关联同一用户和同一事件窗口。
8. **提交与复核**：结论注明材料路径、表/键/主键、原值、转换方法、工具版本、反例和覆盖限制。比赛要求的输出格式与真实取证解释分别保留，不以“提交通过”代替证据判断。

建议证据表字段：`问题类型 / 设备与账号 / 文件逻辑路径 / 记录定位 / 原始值 / 转换值 / 时间语义 / 支持证据 / 限制 / 导出哈希`。同一结论的来源彼此依赖时，不把两个解析器对同一记录的输出当成两条独立证据。

## 07 常见考点与定位矩阵

下表是开题索引，不是所有 iOS 版本通用的固定表结构；每一项都需对当前检材确认路径和 schema。

| 考点 | 检查入口 | 答题方法 | 限制与复核 |
| --- | --- | --- | --- |
| 系统、备份和应用身份 | 系统 `SystemVersion.plist`、备份元信息、应用 `Info.plist` | 对照系统版本、构建号、应用 Bundle ID、备份时间 | sysdiagnose 中可有旧版本副本，不等于当前系统 |
| SMS 与 iMessage | 候选 `mobile/Library/SMS/sms.db` 与附件，备份按 Manifest 映射 | 同库先查 `service`；`message.handle_id` 关联 `handle.ROWID`，群聊参与者另查会话关联表 | `handle_id` 不是电话号码本身；方向、状态和多账号要复核，具体查询见备份专项；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/sms.py) |
| 通话与服务来源 | 候选 `mobile/Library/CallHistoryDB/CallHistory.storedata`，另查 `CallHistoryTemp.storedata` | 确认 `ZCALLRECORD` 的 `ZDATE / ZDURATION / ZADDRESS / ZORIGINATED / ZANSWERED / ZSERVICE_PROVIDER` | 旧 `call_history.db` 属另一结构；FaceTime/第三方服务按实际提供者识别，保留类型/断开原因原值；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/callHistory.py) |
| 通讯录身份与号码 | 候选 `mobile/Library/AddressBook/AddressBook.sqlitedb`；头像另查 `AddressBookImages.sqlitedb` | 确认 `ABPerson.ROWID → ABMultiValue.record_id`，核对标签、属性编号和值 | 同名不等于同人；联系人存在不是通信证明；属性编号映射以当前 schema/解析器为准；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/addressBook.py) |
| 日历事项与地点 | 候选 `mobile/Library/Calendar/Calendar.sqlitedb`，以实际命中路径为准 | 查 `CalendarItem` 的摘要、起止时间、时区及日历/地点关联 | 日程不证明实际出席；浮动时间和缺失时区不强行当 UTC；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/calendarAll.py) |
| Safari 搜索、浏览与书签 | `Library/Safari/History.db` 与保留 URL；书签候选 `Bookmarks.db` | URL、查询词、访问时间与时间戳参数交叉验证；书签另查 `bookmarks` 的 `title / url / hidden` | 书签不是访问历史；访问、搜索发起、会话时间可能不同；[书签解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/safariBookmarks.py) |
| 应用累计使用时长 | 支持版本的 `knowledgeC.db`；新版本另检查 Biome 支持情况 | 过滤活动类型、按应用分组求时段长度，核对重复和重叠 | 单次最长不等于累计最长；后台痕迹不等于前台交互 |
| 最晚记录位置 | `com.apple.routined/Cache.sqlite` 等定位缓存 | 校验时间单位后排序，核对经纬度及其他位置线索 | 缓存位置不等于设备当前的位置，照片 GPS 也不是机主到访的单独证明 |
| 健康活动与同步 | `Library/Health/healthdb.sqlite`、`healthdb_secure.sqlite` | 区分同步元数据、距离/运动样本、来源设备及时间段 | 同步时间不是活动时间；来源可能是关联设备 |
| 照片、Live Photo 与截图 | 候选 `mobile/Media/PhotoData/Photos.sqlite`、DCIM、关联 HEIC/JPEG 与 MOV、应用快照 | 对照资产记录、创建/加入/删除时间、媒体关联和 GPS；播放动态片段/音轨 | 先确认版本与 `ZGENERICASSET / ZASSET`；元数据存在不保证原图在本机，文件名近似不等于配对，相机朝向不等于运动方向；[资产解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/Ph001BasicAssetData.py) |
| 应用账本与订单 | 对应应用数据库、类别/渠道维表、状态列 | 定义交易范围，联合筛选，核对金额单位、退款/删除状态 | 应用标签、类别 UUID、渠道 ID 要实际关联，不能凭名字 SUM 全库 |
| 备忘录、便签与已删除线索 | 搜索实际 `NoteStore.sqlite`，包括共享容器；另查应用库、BLOB、WAL、缓存和快照 | 支持结构中核对 `ZICNOTEDATA.ZNOTE → ZICCLOUDSYNCINGOBJECT.Z_PK`；正文 `ZDATA` 需对应解码，标题/摘要不代替正文 | 口令保护正文可能未解码；多附件可造成重复行；现存、删除、同步分别统计，残片需上下文支持；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/notes.py) |
| 账号数量与身份归属 | 配置、系统账户、应用用户表、共享容器 | 以稳定标识和平台区分账号，记录去重规则 | 同一账号在多个应用出现，不应重复算多个自然人 |
| Wi-Fi 已知网络与配置 | 按文件名搜索 `com.apple.wifi.plist`、`com.apple.wifi-networks.plist.backup`、`com.apple.wifi.known-networks.plist`，记录实际全路径 | 区分版本结构，核对 SSID/BSSID；保留 `JoinedBySystemAt / JoinedByUserAt / UpdatedAt / LastDiscoveredAt` 等实际键 | 键名不保证存在；按原字段描述时间，不由配置推出密码、成功联网或精确移动轨迹；[解析依据](https://github.com/abrignoni/iLEAPP/blob/cc17f322d9e510931b7f2688bc823ee3b2328c1d/scripts/artifacts/appleWifiPlist.py) |
| 崩溃与诊断上下文 | 取得的 CrashReporter/诊断目录、`.ips` 报告；文本 syslog 仅作候选 | 崩溃报告先看类型、进程、版本、时间及加载镜像，再与业务痕迹关联 | iOS 10 起采用统一日志，不能假设完整文本 syslog；崩溃证明故障上下文，不等于用户成功操作 |

Biome 是较新 iOS 中需要关注的活动痕迹体系，不能凭一个版本的知识点声称它在所有设备上完全替代 knowledgeC。若公开解析只展示报告标签而没有原始流路径和字段，本篇只给定位思路，不编造查询语句。


该核查照片模块对 iOS 11–13 的资产表使用 `ZGENERICASSET`，iOS 14–26 分支使用 `ZASSET`，仍应先查看当前 schema；不要把另一个 `Syndication.photoslibrary/database/Photos.sqlite` 同名库混入主照片库统计。Wi-Fi 文件以实际文件名、键与清单为准，不要求它一定在某一个偏好设置目录。普通备份是否包含这些对象，需重新按采集清单确认。

日志解析也要先识别格式。Apple 说明 iOS 15 起的 `.ips` 崩溃格式由首行元信息 JSON 和后续报告 JSON 两个对象组成，先核对 `bug_type`；`309` 对应崩溃报告，不能把每个 `.ips` 都套入同一崩溃 schema。统一日志需要对应格式的解析流程，不能仅用文本搜索代表完整分析。[Apple 统一日志](https://developer.apple.com/documentation/os/logging/)、[Apple IPS 崩溃格式](https://developer.apple.com/documentation/xcode/interpreting-the-json-format-of-a-crash-report)

### 7.1 已存在的越狱、Shell 与 SSH 痕迹怎么判读

本节分析**已经取得的文件树和记录**，不要求为找文件而改变原设备状态。root 权限不等于所有受保护对象已解密，采集边界仍按第 02 节确认。

| 候选材料 | 具体检查 | 结论边界 |
| --- | --- | --- |
| 包与注入配置 | 传统布局下核查 `/Library/MobileSubstrate/DynamicLibraries` 的库/配置及包管理元数据；rootless 布局检查实际 jbroot | Theos 的 rootless 布局使用 `/var/jb` 前缀，也支持重定位；只在旧路径未命中不能排除其他布局；文件存在仅支持安装/配置或残留线索，不单独证明已加载；[布局依据](https://theos.dev/docs/rootless) |
| root 家目录与命令历史 | 在取得的 `private/var/root`、实际用户 HOME 中查 Shell 历史，保存原文件、行号和时间关联 | Apple 基础目录本就包含 root 家目录，不是单独越狱证明；Bash 历史受 HISTFILE、保存和过滤影响，缺失不等于未操作，条目也不证明成功执行；[目录依据](https://github.com/apple-oss-distributions/files/blob/main/hierarchy.not_sim)、[Bash 历史机制](https://www.gnu.org/software/bash/manual/html_node/Bash-History-Facilities.html) |
| SSH 服务配置和授权 | 查取得的 `sshd_config`、Include/Match、启动记录、进程/监听及日志；另登记 `authorized_keys` | 配置和允许认证不等于服务正在运行或已登录；有效配置还可能受命令行影响；[OpenSSH 配置语义](https://man.openbsd.org/sshd_config) |
| SSH 主机密钥记录 | 查看实际 `.ssh/known_hosts` 的主机键及文件上下文；与服务端认证和会话日志关联 | 此文件可在用户认证前写入或预置，不作为成功登录记录；私钥文件也不证明对应账号被使用；[OpenSSH 主机验证实现](https://github.com/openssh/openssh-portable/blob/master/sshconnect.c) |

判断“历史安装”“当前启用”“成功执行”时分别写证据，不把标记文件、目录、配置和进程状态混为同一结论。读取配置、历史和日志的副本即可，不为了验证线索启动目标服务或加载插件。

## 08 真实比赛：健康同步、应用快照与 Live Photo

**比赛依据**：Magnet Virtual Summit 2021 CTF 的 iPhone 解析记录。材料为文件系统 ZIP，并另有 keychain plist；它不是“普通本地备份”的示例。实际问题涉及健康库最后同步时刻，解析者从 `healthdb.sqlite` 的 `cloud_sync_stores.last_sync` 读取并转换时间；同篇还使用应用快照和 Live Photo 音轨辅助查找内容。[参赛者本人解析](https://www.stark4n6.com/2021/05/mvs2021-ctf-iphone.html)

**提炼考点**：业务记录与同步元数据区分；路径搜索与数据库复查；静态图片以外的动态及声音证据。工具 OCR 没命中时，检查应用快照格式是否被支持，而不是断言画面不存在。读取同步字段后记录其纪元、单位和时区，不能把同步值改写为运动发生时刻。

这份解析对部分 Snapchat 数据格式仍有疑问，因此不以它证明该应用所有消息都可通用解密。本轮只阅读公开解析，未复跑比赛检材。

## 09 真实比赛：累计时长与 WAL 差异

**比赛依据**：Magnet User Summit 2022 的 iOS 15 全文件系统题；主办方公告确认该材料和赛事，第一人称解析涉及“哪个应用的屏幕使用时间最多”。[主办方公告](https://www.magnetforensics.com/blog/update-on-magnet-summit-2022-capture-the-flag-contests/)、[参赛者的 iPhone 解析](https://www.stark4n6.com/2022/06/magnet-user-summit-2022-ctf-iphone.html)

实际证据为 `private/var/mobile/Library/CoreDuet/Knowledge/knowledgeC.db` 的 `ZOBJECT`：活动类型由 `ZSTREAMNAME` 确认，应用标识在 `ZVALUESTRING`，区间来自 `ZSTARTDATE` 与 `ZENDDATE`。在该结构确认存在时，可使用以下方法查询工作快照：

```sql
PRAGMA table_info(ZOBJECT);
SELECT ZVALUESTRING AS bundle_id,
       COUNT(*) AS interval_count,
       SUM(ZENDDATE-ZSTARTDATE) AS interval_seconds
FROM ZOBJECT
WHERE ZSTREAMNAME='/app/inFocus'
  AND ZVALUESTRING IS NOT NULL
  AND ZSTARTDATE IS NOT NULL AND ZENDDATE>=ZSTARTDATE
GROUP BY ZVALUESTRING
ORDER BY interval_seconds DESC;
```

**输出解读**：先输出各应用的记录数与累计秒数，再关联 Bundle ID 显示名称。若有重复导入、重叠区间或多个设备数据，先界定是否需要去重/区间合并；简单 SUM 只代表所选记录的区间合计，不自动等于人实际操作的唯一时长。查询应加上实际要求的起止范围，并说明跨边界区间如何裁剪。

同份解析还记录 Gmail `sqlitedb` 中 `label_counts`、`label_server_perm_id` 的未读统计在包含 WAL 后出现差异。考点是**保留主库与 WAL 两种状态证据、解释统计时点**，不是把某个被比赛接受的数字当成任何状态下都正确。本轮未复跑这些库，代码是有真实结构依据的方法，不是已执行的比赛结果。

## 10 真实比赛：最后位置与首次搜索

同一 2022 比赛的独立解析把“手机最后位置”落到 `Library/Caches/com.apple.routined/Cache.sqlite` 的 `ZRTCLLOCATIONMO`，读取 `ZTIMESTAMP`、`ZLATITUDE`、`ZLONGITUDE`。这与累计时长是同届比赛的不同考点，不重复算成新赛事。[解题者本人位置与媒体解析](https://bakerstreetforensics.com/2022/07/28/magnet-2022-ctf-ios15/)

```sql
PRAGMA table_info(ZRTCLLOCATIONMO);
SELECT ZTIMESTAMP, ZLATITUDE, ZLONGITUDE
FROM ZRTCLLOCATIONMO
WHERE ZTIMESTAMP IS NOT NULL
ORDER BY ZTIMESTAMP DESC
LIMIT 10;
```

**正确判读顺序**：先确认字段时基与单位，筛除非有效记录，转换为 UTC 和题目要求时区，再输出最后若干条位置作连贯性检查。“最新缓存定位记录”才是直接观测结果；说成“当前手机所在地点”还需要采集时刻和新鲜度等支持。

首次搜索问题不能简单取 Safari 最大/最小访问时间。2022 解析区分 `History.db` 历史时间与保留 Google URL 的 `ei` 参数所含时间，提醒搜索/会话与访问语义的区别。本篇不把 URL 参数解码泛化为任意搜索的准确点击时刻：应保留原 URL、字段解释和对照时间线。[搜索时间与 WAL 解析依据](https://www.stark4n6.com/2022/06/magnet-user-summit-2022-ctf-iphone.html)

## 11 真实比赛：健康距离、位置与新版本活动

Magnet Virtual Summit 2023 官方公布 iOS 16 Full File System 材料及实际问题，包含按 Apple 记录判断移动距离最多的地点、浏览场所、账号去重和 Live Photo 运动方向；官方直接链接参赛者解析。[主办方题目与解题入口](https://www.magnetforensics.com/blog/announcing-the-mvs-2023-ctf-winners-and-a-new-ctf-challenge/)

解析方法将 `Library/Health/healthdb_secure.sqlite` 中的距离活动时间段与 `Library/Caches/com.apple.routined/Cache.sqlite` 的位置进行关联。它不是“选出最大距离数字后把任意最近位置贴上去”：必须确认样本来源、时间窗、单位与位置覆盖。公开正文没有给出完整 Health 距离 SQL，本篇不补造表名和列名。[参赛者 iOS 16 解析](https://www.stark4n6.com/2023/03/magnet-virtual-summit-2023-ctf-ios-16.html)

同篇使用 Biome User Activity 报告提供浏览语义。这说明较新系统需要调整痕迹入口；它不证明所有 Biome 流均被解析，也不证明没有 knowledgeC 就没有活动。Live Photo 问题还要求区分镜头朝向与行进方向，结合 MOV 运动片段、场景和时空记录判断，不能只看 HEIC 静态画面。本轮没有下载或复跑官方镜像。

## 12 真实比赛：账本金额、便签和地址状态

2024 **数证杯决赛个人赛** 的参赛者本人解析含苹果手机题，涉及按指定支付渠道和用途类别合计记账金额，查找未被工具直接解析的便签，以及区分历史删除地址和当前地址。正文未明确手机提取类型，不能擅自归成 iTunes 备份或完整文件系统。[本人赛中与赛后解析](https://www.cnblogs.com/zzpu213/p/18692389)

**可迁移步骤**：

1. 根据应用配置、Bundle ID 和数据库内容确认目标记账应用，不根据界面中文标签猜库。
2. 检查实际 schema，找到类别 UUID 与支付方式 ID 的维表关系，分别验证“用途”和“渠道”，再联合筛选账目。
3. 记录金额列原值、单位、符号、交易状态与范围。作者在赛后更正分与元的换算，提示要先核对最小货币单位再合计，不照搬原始整数。
4. 用明细导出复核汇总：总额必须能追溯到具体记录；删除、退款、转账或多个账号是否计入，以实际题意与字段为依据。
5. 便签报告未命中时回查应用数据库/BLOB；家庭地址记录需要区分有效状态、删除记录、同步或旧缓存。

公开文字中的表名拼写和截图细节不足以确认完整 SQL，因而本篇不捏造可执行查询，也不保留题目的具体金额、地址或账号答案。照片 GPS 支持的是照片记录的位置，单独不足以确定机主本人到访。本轮未复跑该比赛材料。

## 13 易错点与结论检查

| 易错结论 | 更严谨的做法 |
| --- | --- |
| “这台设备的 ZIP 能直接代表普通备份范围” | 写明提取层级；比赛另给 keychain、日志或应用导出时分别登记 |
| “AFU 就是当前已解锁、所有数据可读” | 同时记录首次认证状态和当前锁屏状态，区分保护类别 |
| “工具没有显示所以没有记录” | 对照原路径、支持模块、版本、错误日志和业务结构 |
| “哈希文件名就是内容哈希” | Manifest fileID 是路径标识，另计算导出内容哈希 |
| “所有 iOS 整数时间都是 Apple 秒值” | 每一字段确认纪元与单位，保留原始值 |
| “最长一条使用记录就是使用最多的应用” | 定义单次/累计统计，处理时间窗、重复和重叠 |
| “Health 最大距离对应最新定位点” | 按同一活动时间窗与来源设备关联，检验位置空窗 |
| “数据库主文件是唯一真实状态” | 保全伴随文件、解释已提交事务和快照；残片与现存记录分开 |
| “UID 就是最终对象内容” | 解析对象表引用，保留键路径与序列化层级 |
| “缓存、删除地址或照片能证明当前居住地” | 区分现存/删除/同步状态和时间，再找独立证据 |
| “比赛答案通过就能消除证据冲突” | 同时保留所需提交格式、原始结果、差异与解释，不改变证据迎合答案 |

## 14 既有内容整合与总结

| 类型 | 处理情况 |
| --- | --- |
| **新增** | 本篇建立 iOS 原理、考点、流程与真实比赛索引；工具篇独立维护 iLEAPP/Plist_Editor 的操作和版本 |
| **修订** | 手机取证总览和已有 iOS 备份篇增加新模块导航；原 URL、原知识正文和原内部资料关联保留 |
| **合并** | 把安全机制、应用容器、系统痕迹、时间与比赛方法组织为同一学习路线；应用与通信通用篇继续作为跨平台内容，不搬走或覆盖 |
| **去重** | Manifest 映射、SMS/附件与 WAL 导出细节只在备份专项维护；本篇给考点和入口，工具命令只在工具篇集中维护，避免复制多套易漂移步骤 |

已有备份篇的流程示例属于通用操作示例，不标成真实比赛题。新增的真实比赛部分逐段给出官方公告或第一人称解析；2022 的两个解题页面属于同届比赛，2021/2023 的文件系统材料不能替代备份教程的采集假设。

既有 [系统目录与应用位置索引](/knowledge/fic-case-14/) 的 iOS 备份入口保持有效；[虚拟币钱包取证](/knowledge/forensic-crypto-wallets/) 中的 iOS 容器、备份与钱包口令区分继续在钱包专题维护，本模块提供其系统基础，不复制钱包实操。[应用与通信](/knowledge/forensic-mobile-apps/) 的跨平台账号、消息和定位关联方法也保持原归属，分析具体 iOS 应用时与本模块配合阅读。

**复习总纲**：先认材料，再认身份；先看结构，再看记录；先定时间/单位，再统计；先回查原始值，再写结论。实用的 iOS 取证结果应能从报告回到路径、表/键和记录，并说明覆盖边界，而不是停留在工具截图。

**本次使用知识补充（2026-10-04）**：目录/容器身份并入第 03 节；通信、媒体、备忘录、网络和日志位置扩充第 07 节；Shell/SSH 与越狱痕迹按条件判读。已有提取层级、安全机制、时间、Plist、工具安装与比赛段落继续保留，不另建重复知识点。指定阅读材料的操作主题经与工具作者代码及系统说明交叉核对后整理；未将目录星级、跨系统类比、通用解密或恢复保证作为操作结论。[补充阅读：iOS 文件树取证检查主题](https://tqandjdc.github.io/2026/05/29/ios%E7%9F%A5%E8%AF%86%E7%82%B9/)
