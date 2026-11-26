**iOS 模块导航**：[原理、考点与流程](/knowledge/forensic-ios-forensics/) · [备份专项](/knowledge/forensic-ios-backup/) · [iLEAPP 与 Plist_Editor](/knowledge/forensic-ios-tools/)。本页按实际操作顺序讲解 iOS 本地备份的目录定位、加密备份口令验证、`Manifest.db` 散列文件名映射、数据库与 WAL 一致性快照，以及短信、通话和微信记录提取。

## 01 定位备份目录与四大入口文件

拿到 iOS 手机检材时，先记录设备型号、系统版本、采集时间、锁定状态和提取方式，区分**本地备份、云端备份、文件系统提取与应用导出**。常见电脑本地备份位于 Windows 用户的 `Apple\MobileSync\Backup\` 或 `Apple Computer\MobileSync\Backup\` 下，macOS 则位于 `~/Library/Application Support/MobileSync/Backup/`（具体位置随安装方式和用户设置变化）。

分析前先完整复制备份目录并计算 SHA-256 哈希，检查根目录下的四个核心入口文件：

| 入口文件 | 核心内容与取证先查项 |
| --- | --- |
| `Info.plist` | 设备名、型号、系统版本、IMEI/序列号、已安装应用与备份关联信息 |
| `Manifest.plist` | 备份格式版本、`IsEncrypted` 加密标志、应用程序包清单与 `BackupKeyBag` |
| `Status.plist` | 备份状态（`SnapshotState`）、备份起止日期与是否完整完成 |
| `Manifest.db` | `Files` 表，保存 `domain`、`relativePath`、`fileID`、`flags` 与文件元数据 `file`（bplist） |

若 `Manifest.plist` 标明备份已加密，不能直接把加密后的 `Manifest.db` 或应用数据库塞进普通 SQLite 查看器（报错并非“数据库损坏”）。已知口令线索时，可从 `Manifest.plist` 提取哈希并在副本上离线验证口令（备份口令、锁屏口令和 Apple ID 密码分属三套凭据）：

```bash
perl itunes_backup2john.pl Manifest.plist > iab.hash
hashcat -m 14800 -a 0 iab.hash wordlist.txt
```

上面用过的模式号是 `-m 14800`；执行前先用当前 `hashcat --help` 核对 `iTunes backup` 对应的模式号（旧版本模式号以本机帮助为准）。

在已解密或未加密的现代备份中，物理文件名（`fileID`）通常是 `SHA1(domain + '-' + relativePath)` 的 40 位十六进制字符串，并按前两个字符分目录存放（如 `3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28`）。切勿凭散列文件名猜测用途，也不要把 `fileID` 当作文件内容的 SHA-1 哈希：

```python
import hashlib
from pathlib import Path
domain = 'HomeDomain'
relative = 'Library/SMS/sms.db'
file_id = hashlib.sha1(f'{domain}-{relative}'.encode('utf-8')).hexdigest()
candidate = Path('work/backup') / file_id[:2] / file_id
print(file_id, candidate, candidate.exists())
```

`HomeDomain`、`AppDomain-<BundleID>`、`AppDomainGroup-<GroupID>`、`MediaDomain`、`SystemPreferencesDomain` 等域用于还原设备上的逻辑空间。备份中未出现某个文件，只说明该备份范围未收录，不能直接断定设备上从未存在。

## 02 用 Manifest.db 映射逻辑路径并连同 WAL 建立快照

在可解析的 `Manifest.db` 工作副本上，先检查完整性并抽样查看 `domain`、`relativePath` 与 `fileID` 的映射关系：

```bash
file ./work/Manifest.db
sqlite3 -readonly ./work/Manifest.db 'PRAGMA integrity_check;'
sqlite3 -readonly ./work/Manifest.db "SELECT domain, relativePath, fileID FROM Files WHERE relativePath LIKE '%.sqlite' LIMIT 20;"
```

SQLite 主库与伴随的 `-wal`、`-shm` 文件在散列备份中各有完全不同的 `fileID`（因为路径字符串不同，SHA-1 结果也不同），**绝不能在主库散列文件所在子目录里找同名 `-wal` 文件**。必须按同一 `domain` 与完整 `relativePath` 一次性查出三者的 `fileID`：

```sql
SELECT domain, relativePath, fileID
FROM Files
WHERE domain = 'HomeDomain'
  AND relativePath IN (
    'Library/SMS/sms.db',
    'Library/SMS/sms.db-wal',
    'Library/SMS/sms.db-shm'
  );
```

逐项定位 `备份目录/fileID前两字符/fileID`（兼顾旧版平铺备份目录），确认物理文件存在后，将三者导出到同一工作目录并还原为相同的逻辑基名（如 `app.sqlite`、`app.sqlite-wal`、`app.sqlite-shm`），记录映射表与导出前后内容哈希。若清单或采集范围未包含 `-wal`，应在报告中注明可能缺失尚未合并的事务，不能把“未取得 WAL”解释为“没有新消息”。

导出并拼齐三件套后，先在独立工作目录生成一致快照，再查表结构：

```bash
sqlite3 -readonly ./work/app.sqlite ".backup './work/app-snapshot.sqlite'"
sqlite3 -readonly ./work/app-snapshot.sqlite '.tables'
sqlite3 -readonly ./work/app-snapshot.sqlite '.schema'
```

`.backup` 生成的是当前已提交视图的快照，不包含所有未分配空间或过期 WAL 帧中的删除残留；原始三件套副本继续保留供深度恢复使用。

## 03 校准 Apple 纪元时间与结论边界

iOS 系统数据库大量使用 **Apple Absolute Time（以 `2001-01-01 00:00:00 UTC` 为起点，与 Unix 纪元相差 `978307200` 秒）**，且单位可能是秒或纳秒；第三方应用则常用 Unix 秒或毫秒。开始统计前，先选一条可由短信、照片或系统日志独立确认的事件校准时间单位与纪元，切勿对所有数值盲目加同一个常数。

同时核对 `Status.plist` 的备份完成时间与应用数据库最后写入时间：
- 与电脑同步的本地备份、iCloud 云端记录和设备实时痕迹可能覆盖不同时间段，同一应用也可能登录过多个账号，冲突时保留各自原始字段与采集来源。
- 区分三个证据强度层级：**“备份数据库包含该记录” → “记录字段标为已发送/已读” → “对端或服务端记录印证收到”**；定位点存在也不必然代表设备机主当时实时处于该位置。

## 04 解析短信、通话、照片与微信碎片帧

常用系统数据库可通过 `Manifest.db` 一次性检索定位：

```sql
SELECT domain, relativePath, fileID
FROM Files
WHERE relativePath LIKE '%sms.db%'
   OR relativePath LIKE '%CallHistory%'
   OR relativePath LIKE '%AddressBook%'
   OR relativePath LIKE '%Photos.sqlite%';
```

### 04.1 短信与 iMessage：同库识别服务并按外键关联号码

短信数据库的设备逻辑路径为 `/private/var/mobile/Library/SMS/sms.db`，备份中对应 `HomeDomain` 下的 `Library/SMS/sms.db`。SMS 与 iMessage 共用同一个 `sms.db`，由 `message.service` 字段区分。`message.handle_id` 是指向 `handle.ROWID` 的外键，实际号码或 Apple ID 账号需关联读取 `handle.id`（群聊参与者还需联查 `chat_message_join` / `chat_handle_join`）。

先对快照执行 `.schema message` 与 `.schema handle`；确认列存在后再执行查询（若 `text` 列为空，还需检查该版本的 `attributedBody` BLOB 及附件表）：

```sql
SELECT m.ROWID AS message_rowid,
       h.id AS handle_value,
       m.service, m.is_from_me, m.date AS date_raw,
       m.is_read, m.text
FROM message AS m
LEFT JOIN handle AS h ON m.handle_id = h.ROWID
ORDER BY m.ROWID;
```

使用 `LEFT JOIN` 可保留尚未匹配到 `handle` 的记录（缺失时保留 `NULL`，不臆测为机主本人）。当消息关联附件表（`message_attachment_join`）时，一条含多附件的消息会产生多行结果，统计消息条数时应按稳定消息主键去重（如 `COUNT(DISTINCT m.ROWID)`），不能把附件关联行数当成消息总数。通话、通讯录、照片与 Safari 的详细字段见[iOS 取证原理篇定位矩阵](/knowledge/forensic-ios-forensics/)。

### 04.2 微信备份还原与 level_0 碎片帧比对

微信备份还原后，消息库和 `session/lsm_data/level_0` 要一起看。这一份碎片用下面的帧定位一条消息：`0x42`、发送方 wxid 长度、发送方 wxid、`0x20 0x02 0x4a`、接收方 wxid 长度、接收方 wxid。双方 wxid 都是 19 字节时，两个长度字节都是 `0x13`。紧随其后的正文和时间，与消息库里同一时间的记录对照。正文不一致的条数是被改写的条数。其他应用的资产在该应用自己的库里。

## 05 旧型号恢复模式与 DFU 的证据边界

iPhone 6 及部分更早的 Home 键设备使用 Home/电源组合进入恢复或 DFU；后续机型按键组合不同。恢复模式屏幕显示连接提示，DFU 通常黑屏但可被主机 USB 识别（单纯黑屏不能证明已进入 DFU）。按键时长以具体机型与官方说明为准，不能把一个固定秒数套用到所有设备。

这两种模式只是设备引导状态，不等于自动提取或解密用户数据。进入模式、重启、升级或恢复都会改变设备状态；**执行恢复/刷机可能直接清除用户数据**。取证时优先保全并离线分析已取得的备份或镜像，切勿为了查看消息而在原始检材设备上执行恢复操作。

## 06 实战：从备份清单核对一条消息和附件

**场景与材料：** 已取得一份可解密的本地 iOS 备份，需核对某联系人的消息是否存在于备份中，并验证其图片附件是否完整。

### 06.1 按映射提取，而非猜散列文件名

1. 核对 `Info.plist`、`Manifest.plist`、`Status.plist` 中的设备标识、加密状态和备份完成时间，把“备份任务完成”与“备份包含目标应用文件”分开确认。
2. 在 `Manifest.db` 的 `Files` 表中查询 `HomeDomain` 下的 `Library/SMS/sms.db`、`Library/SMS/sms.db-wal`、`Library/SMS/sms.db-shm`，按各自的 `fileID` 从对应两字符子目录导出物理文件，在工作目录还原为同名三件套并计算各自内容 SHA-256（`fileID` 是路径 SHA-1，不能代替内容哈希）。
3. 生成 `.backup` 快照后检查 `message`、`handle`、`chat` 与 `attachment` 表的实际 schema，提取消息方向、状态、原始时间值及附件逻辑路径。
4. 用附件的 `relativePath` 回到 `Files` 表查出附件对应的 `fileID`，导出物理文件并校验文件头、字节大小与内容哈希；若仅存缩略图则如实标注缩略图，不冒充完整原图。

### 06.2 示例判读与交叉核验

若消息表存在一条发出记录，但附件清单指向的物理文件在备份目录中缺失，应表述为“备份数据库包含该条发送状态记录，对应附件实体未在本次备份中取得”；发送是否成功、对端是否收到以及备份时间点之后的新增活动，均需结合状态语义、对端检材或服务端记录另行核实。
