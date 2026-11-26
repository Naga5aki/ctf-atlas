---
title: SQLite 与 WAL：当前记录和删除残留
summary: 保全数据库三件套，区分有效事务、历史页面和雕刻残留，再按表、主键和页偏移复核。
module: Forensics
track: 文件与多媒体取证
topic: 文件恢复与格式
tags: [文件格式, 时间线]
status: 已整理
sourceIds: [web-forensics-wiki, web-digiforensics-mobile]
relatedIds: [forensic-browser, forensic-mobile-apps, forensic-ios-backup]
updated: "2026-10-01"
---

## 01 三个文件各自负责什么

| 文件 | 作用 | 分析要求 |
| --- | --- | --- |
| `app.db` | SQLite 主数据库，含页、B-tree、schema 和记录 | 保留原始大小、哈希、页大小和编码 |
| `app.db-wal` | Write-Ahead Log，按 frame 保存数据库页版本 | 同一主库、同一代 WAL 一起保全 |
| `app.db-shm` | WAL 索引和协调状态，可重建 | 有则保全，不为缺失情况制造空文件 |

WAL 是数据库修改日志，不是“每条消息一行”的文本记录。主库中的最新逻辑状态可能需要 WAL 才能还原；文件名相同也不能证明属于同一次采集。

## 02 结构和事务边界

主库文件头以 `SQLite format 3` 标识，页大小通常在头部字段中。B-tree 页存表或索引，记录由 serial type、varint 和字段内容编码；溢出页、空闲列表、freeblock 与未分配区可能残留旧数据。

WAL 由文件头和多个 frame 组成，每帧含页号、数据库大小字段、salt 和校验值，以及完整页数据。需验证文件头、frame salt、checksum 和 commit 边界。最新且有效的提交状态不等于文件中出现的最后一个字符串；过期 frame 也不能直接视为当前消息。

## 03 在副本上建立一致快照

复制完整同批次文件到隔离目录，保留证据副本后才让 SQLite 读取。启动数据库连接可能建立 SHM 或处理日志，所以工作目录和不可变副本分开。

```bash
sha256sum work/app.db work/app.db-wal
sqlite3 work/app.db '.backup work/snapshot.db'
sqlite3 -readonly work/snapshot.db 'PRAGMA integrity_check;'
sqlite3 -readonly work/snapshot.db '.tables'
sqlite3 -readonly work/snapshot.db '.schema'
```

没有 WAL 时只对实际存在的主库计算哈希。若库无法打开，先确认是否 SQLCipher、复制不完整、页大小不符或 WAL 不匹配。不要在检材上用 `PRAGMA wal_checkpoint`，它会把 WAL 状态写回主库。

## 04 记录恢复的三个层次

1. **当前有效记录：** 从一致快照按 schema 查询，记录表、主键和原始时间。
2. **历史页版本：** 从有效 WAL frame、旧备份或快照恢复，记录 frame 编号、页号、提交阶段和对应主库。
3. **残留雕刻：** 在 freeblock、freelist、未分配区或不完整页中发现数据，记录字节偏移、解析依据与缺失字段。

```bash
sqlite3 -readonly work/snapshot.db '.dump' > work/current.sql
sqlite3 work/app.db '.recover' > work/recovered.sql
```

`.recover` 用于尽可能恢复数据库结构和记录，不保证找回所有删除记录，也不专门替代 WAL 历史解析。恢复 SQL 应导入新库验证，不能导回检材。SQLCipher 应先确定版本、密钥、页大小、KDF 与兼容参数，在工作副本导出明文新库后再查完整性。

## 05 常见取证问题

| 现象 | 检查方向 |
| --- | --- |
| 工具能看到消息，普通 SQL 看不到 | 工具是否合并 WAL、读取删除残留或其他数据库 |
| 复制后最新消息消失 | 是否漏带 WAL、采集是否跨时间点 |
| 同一 ID 有不同内容 | 不同 frame、编辑记录、同步、账号与版本 |
| 只搜到消息片段 | 编码、字段边界、页结构和归属表；不能当成完整记录 |
| 数据库空但缓存有图片 | 缓存、附件、通知、索引和备份的独立留存 |

最终输出 `数据库哈希 / 表与主键 / 记录状态 / 页或frame / 字节偏移 / 原始值 / 时间基准 / 关联附件`。明确当前记录、删除残留和缓存的区别，避免把旧页面中的内容认定为当前可见消息。

## 06 实战：区分当前消息、WAL 历史与删除片段

**场景与材料：** 同批次取得 app.db、存在时的 WAL/SHM 和附件目录，综合工具显示一条普通查询未找到的消息。目标是解释差异并确定记录状态。

### 06.1 建立一致查询对象

1. 对同批次文件分别记录大小、哈希与采集时间，保留不可变副本，再在独立工作目录沿本页 `.backup` 建立快照。
2. 保存 snapshot 的 schema 与完整性检查；按表、主键、账号和原始时间查询当前记录。不要用 VACUUM、checkpoint 或删除 WAL 来试图“修复”唯一材料。
3. 对综合工具命中记录查看其来源类型：主库有效行、有效 WAL frame、空闲页、未分配片段或其他文件，保存页号、frame、偏移及字段缺口。
4. 将记录 ID、账户、时间、正文与附件关联；相同 ID 的不同版本并列，不凭一句字符串确定最后有效状态。

### 06.2 恢复 SQL 的验证

仅当结构损坏需要恢复时，对新的恢复工作副本输出 recovered.sql，先静态检查 SQL 内容与工具诊断，再导入**不存在的新实验库**。恢复脚本可能包含错误结构、异常值或无关内容，不能导回证据数据库。

```bash
sqlite3 work/recovered-new.db < work/recovered.sql
sqlite3 -readonly work/recovered-new.db 'PRAGMA integrity_check;'
sqlite3 -readonly work/recovered-new.db '.schema'
```

新库路径须独立，记录输入输出哈希、恢复诊断和验证样本。完整性检查通过只说明结构符合检查范围，不保证所有行均真实、字段归属正确或删除记录完整恢复。

### 06.3 示例结论

快照中无消息，WAL 旧页有同一 ID 的候选文本，附件仍存在。可报告“在历史页版本中发现候选记录，并关联到附件”；是否当前可见、何时删除、是否阅读仍需提交边界、应用状态及其他记录验证。只有雕刻片段时进一步降为残留线索，不能按当前有效行统计。
