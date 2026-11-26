# iOS 取证使用知识补充核对记录

日期：2026-10-04。落点：**Forensics → 手机取证 → iOS 取证**。

## 阅读与处理

已阅读用户指定的 [iOS 越狱设备电子取证指南](https://tqandjdc.github.io/2026/05/29/ios%E7%9F%A5%E8%AF%86%E7%82%B9/) 正文。仅选择文件树、证据定位、数据解析与结果验证相关主题，使用工具作者固定代码及系统/工具说明核对；没有搬入完整目录百科、星级排名或系统类比。

| 主题 | 处理 | 唯一维护位置 | 理由 |
| --- | --- | --- | --- |
| 提取层级、加密、Keychain、时间、Plist与哈希 | 合并/去重 | 现有原理02/04/05、备份05/07与工具01–07 | 原有条目已覆盖，不复制安装目录或通用转换示例 |
| 目录别名、Library层级和真实根前缀 | 新增 | 原理3.1 | 核对真实链接，逻辑路径去重，不跟随导出绝对链接读取分析机 |
| 应用容器身份 | 修订/补充 | 原理3.2、工具9.1 | 使用MCMMetadataIdentifier、compatibilityInfo；备份清单不是通用UUID索引，Documents拼写校正 |
| SMS/iMessage与消息计数 | 合并/修订 | 原理07、备份8.1 | 同库按service辨别，handle外键关联、群聊参与者和附件去重分别处理 |
| 通话、联系人、日历、Safari、Notes、Photos、Wi-Fi | 修订/补充 | 原理07 | 候选路径和实际schema核对，数据库和格式校正，不保证所有采集都有 |
| 日志与既有越狱/SSH/Shell材料 | 新增/修订 | 原理07/7.1 | 版本条件、rootful/rootless、状态与行为分开；配置或known_hosts不证明成功登录 |
| SQLite只读检查与恢复 | 合并/新增 | 原理4.2跳转、工具9.2/9.3 | 重复检查命令归并；恢复使用新派生目录和失败即停，结果不等于完整已删除数据 |
| 目录星级、百分比、Windows类比与无条件工具目录 | 不收录 | 不加入正文 | 不提供可核对的iOS使用结果或与目标操作无关 |
| 越狱后全可读、块复制自动解密和恢复保证 | 不收录错误结论 | 现有原理02与工具9.3明确边界 | 与Apple保护机制和SQLite恢复说明相矛盾 |

## 结构与保全

- 不新增页面、不改变手机取证分类；更新原理、备份、工具三篇既有维护稿及其生成页面。
- 原理篇第08–12节真实比赛内容逐节与本次基线比较，全部保持一致；原有来源ID继续保留。
- 时间/Plist/采集/备份/WAL既有方法沿用；SQLite基础检查命令统一归到工具篇，原理篇保留解释及跳转。
- 新位置按作者固定代码 `cc17f322d9e510931b7f2688bc823ee3b2328c1d` 核查，不以此宣称本机旧发行版所有模块已实际运行。

## 验证

- 修改前：65项数据测试，64通过；1项既有目录定位测试失败。
- 修改后：69项数据测试，68通过；同一项失败。新增4项增量检查在修改前快照上全部失败、在更新内容上全部通过；iOS相关9项全部通过。
- 合成SQLite测试实际执行正文消息SQL：保留未匹配handle的消息；三条附件连接行对应两条消息；只读连接拒绝DELETE；文件哈希保持不变。它是查询验证，不是编造比赛题。
- UI测试5项通过；静态检查18文件零错误/警告；构建333页、索引324页；7524本地链接审计零错误。
- 全量重新导入退出0，保留既有工具清单字节后，src/public/README哈希差异为0；导入扫描166项，不把它冒充既有162项清单已全部验证。
- 浏览器核对三篇正文及新增字段、命令，手机取证分类搜索 `known_hosts` 命中原理篇；控制台未见错误。
- 恢复命令仅经官方文档核对，未实际执行损坏库恢复；正文明确这一边界。恢复新目录拒绝复用，导出/导入非零即停止。

既有失败项的缺失路径：`D:\CTF_MISC_Tools\Forensics\Inseyets PA`。本任务未改工具清单，也未用空目录遮蔽失败。

## 文件与证据

- 维护稿：`src/content-curation/forensic-ios-forensics.md`、`forensic-ios-backup.md`、`forensic-ios-tools.md`。
- 生成正文：同ID的 `src/content/knowledge` 页面。
- 内部关联：`src/data/forensics-supplements.json`；新增检查：`tests/test_ios_usage_supplement.py`。
- 完整基线与逐文件哈希：`.work/ios-usage-supplement-20261004/before/`、`baseline-hashes.json`。
- 命令、退出码与原始日志：同目录 `verification-results.json` 和对应txt；差异：`changes.diff`、`change-manifest.json`。
- 浏览器记录：`browser-core/tools/backup/search.json`；截图：`ios-usage-core.png`。
- 本记录的机器可核查配套：`docs/forensics-ios-usage-supplement-review.json`，包含逐来源URL、代码哈希、合并决定及验证结果。
