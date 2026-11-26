# iOS 取证模块：整合与验收说明

日期：2026-10-04。归属：**Forensics → 手机取证 → iOS 取证**。

## 1. 模块与内容

| 状态 | 页面 | 内容分工 |
| --- | --- | --- |
| 新增 | [iOS 原理、考点与流程](../src/content-curation/forensic-ios-forensics.md) | 概念、安全机制、应用身份、Plist/SQLite/时间、流程、痕迹矩阵、真实比赛、易错点与总结，共14节 |
| 保留并修订导航 | [iOS 备份专项](../src/content-curation/forensic-ios-backup.md) | 完整保留原10节正文与URL，Manifest/SMS/附件/WAL导出继续在此维护 |
| 新增 | [iOS 工具与实战](../src/content-curation/forensic-ios-tools.md) | iLEAPP与实际VOWSoft Plist Editor Pro：用途、环境、步骤/参数、输出、场景、注意，共9节 |

新增文章不是用新稿覆盖旧稿。手机总览和备份页只在正文前增加导航，原正文在统一CRLF/LF后逐字符保留，原sourceIds不变。路径索引、跨平台应用与通信、钱包专题未修改，原理页提供交叉入口。合并指学习路线整合；去重指新稿不重新复制旧备份操作，不删除原有知识。

## 2. 真实比赛依据与验证边界

共4届比赛、7份官方公告/本人解析。正文不保留题号、固定答案、实际账号、地址或凭据。所有比赛段落均未复跑原检材；字段和题意来自公开文字。

| 比赛/来源 | 提炼考点 | 读取限制 |
| --- | --- | --- |
| [Magnet Virtual Summit 2021 CTF - iPhone](https://www.stark4n6.com/2021/05/mvs2021-ctf-iphone.html) | healthdb.sqlite：cloud_sync_stores.last_sync；作者手工查表并转换Apple时间；Apple News等应用的Library/SplashBoard/Snapshots下KTX快照补足OCR与邮件搜索未命中的屏幕内容；DCIM中的Live Photo包含可播放音频；通话/聊天姓名可辅助消歧，不能只读HEIC静态画面 | 作者对Snapchat arroyo.db消息格式明确保留疑问，不能宣传所有内容已经通用解密；keychain plist为比赛额外材料，不代表原始keychain数据库可直接读取；未读取附件和截图原图；未独立证明Health时间单位或KTX渲染流程 |
| [Update on Magnet Summit 2022 Capture the Flag Contests](https://www.magnetforensics.com/blog/update-on-magnet-summit-2022-capture-the-flag-contests/) | 官方获奖名单列出Kevin Pagano，与其2022 iPhone一手解析交叉对应 | 没有下载镜像；公告不用于证明具体数据库字段或完整iOS题目列表 |
| [Magnet User Summit 2022 CTF - iPhone](https://www.stark4n6.com/2022/06/magnet-user-summit-2022-ctf-iphone.html) | private/var/mobile/Library/CoreDuet/Knowledge/knowledgeC.db：ZOBJECT；筛ZSTREAMNAME=/app/inFocus，按ZVALUESTRING分组，SUM(ZENDDATE-ZSTARTDATE)；Safari/History.db的访问时间不等于首次搜索；另检查保留的Google URL中ei解析时间并区分UTC与本地时间；Gmail sqlitedb的label_counts及label_server_perm_id；作者报告主库与加入-wal后的未读统计存在差异 | 只证实该检材和作者处理结果；比赛接受值不能覆盖WAL差异或取代状态解释；未复跑SQL或Unfurl；没有保留具体答案、账号及搜索URL |
| [Magnet 2022 CTF – iOS15](https://bakerstreetforensics.com/2022/07/28/magnet-2022-ctf-ios15/) | Library/Caches/com.apple.routined/Cache.sqlite：ZRTCLLOCATIONMO；先验证ZTIMESTAMP日期意义再排序，读取ZLATITUDE、ZLONGITUDE；单条Screen Time最长不代表累计最长；作者导出并按应用汇总；Live Photo方向需播放运动片段并结合场景定位；朝向和倒退时的运动方向不同 | 同一2022比赛的第二份解析，不重复计为新比赛；不得把网页中截图或在线街景当作本轮已经重放的检材；作者首次搜索时间解释需与时区证据核对，不能照搬机器本地时区 |
| [Announcing the MVS 2023 CTF Winners and a NEW CTF Challenge!](https://www.magnetforensics.com/blog/announcing-the-mvs-2023-ctf-winners-and-a-new-ctf-challenge/) | 官方实际题目包括账户去重、地点、Live Photo移动方向、Apple距离与地点关联等；官方Solutions链接直接指向Kevin Pagano及Emma Sousa本人文章 | 原始检材未下载；公开哈希未经本轮重算；官方题干与WP标题个别用词不同，以题意及证据路线核对而非机械匹配题名 |
| [Magnet Virtual Summit 2023 CTF - iOS 16 iPhone](https://www.stark4n6.com/2023/03/magnet-virtual-summit-2023-ctf-ios-16.html) | Library/Health/healthdb_secure.sqlite的距离记录，按时间段关联Library/Caches/com.apple.routined/Cache.sqlite定位；作者通过Biome User Activity及Google Search报告获取浏览语义；不能因knowledgeC缺失就认定不存在活动；应用Documents/plus-ad-video缓存可提供广告播放内容；文件存在与用户确实观看次数需区分 | 本文未提供Biome原始流精确路径、表字段或健康距离SQL，不能凭报告标签编造查询；仅正文阅读，未解析ZIP、视频、Biome或Health数据库；不得据此笼统声称Biome在全部版本完全替代knowledgeC |
| [数证杯个人 / 2024数证杯决赛个人赛wp](https://www.cnblogs.com/zzpu213/p/18692389) | 参赛者定位记账App数据库，依据类别UUID及支付方式ID筛选账目并合计；文章文本表名写为TBL OUTGOCATEGORYINFO；作者赛后更正金额单位，应核验分与元而非照搬原始整数SUM；商业工具未解析的便签内容仍需回查应用数据库；家庭地址需区分删除记录与当前记录 | TBL OUTGOCATEGORYINFO拼写仅来自正文；数据库文件名及精确列名未核实，不能擅自改为带下划线表名；图像原图读取失败；没有复跑检材和原作者SQL；GPS照片只能支持照片摄制位置，单独不足以证明机主本人到访 |

2022两个作者解析属于同届比赛。国内题的提取层级、数据库文件名和完整列名没有确认，不补造SQL。候选西电页404/不可访问未计入；国内解析截图原图未取得。官方比赛镜像公开哈希不作为本轮重算结果。

## 3. 文档与工具版本核验

Context7已尝试定位两款工具，但只返回同名云凭据工具或Plist编程库；没有用这些不相关文档证明GUI/CLI参数。改为原作者iLEAPP项目、固定发布提交、实际帮助，以及VOWSoft官方产品页/手册。

- 本机 iLEAPP `--version` 退出0，字面输出 `iLEAPP 2026.4.4`；`--help`退出0。对应标签v2026.4.4、提交7b0594a03c50d9b27ab49fa586e720e788b6236b。
- `fs/zip/tar/file`四种模式均退出0；构造SystemVersion.plist解析出版本17.0/构建21A000，并输出TSV、HTML及LAVA目录。输入SHA256前后相同。该样本不是比赛题，也不证明其他插件、加密备份或raw/gz都已测试。
- 本机3份选定模块代码与对应发布代码只在统一换行后相同；原始字节哈希不同。没有据此声称整个exe已认证。
- 本机Plist Editor Pro版本2,1,0,1、VOWSoft、签名Valid；官网2.5.0不等于本机版本。GUI未运行，操作步骤依据官方手册；没有捏造命令行接口。
- 只读脚本保留bool/int/Data/Date/UID类型，不解密或自动解档；纪元、单位由调用者显式选择。错误值返回退出2。

## 4. 所有参考链接的落点

| 参考链接 | 页面与章节 |
| --- | --- |
| [web-ios-reference-888171a6e1](https://support.apple.com/en-us/108353) | forensic-ios-forensics: ## 01 先辨别检材和采集层级 |
| [web-ios-reference-9d458e869c](https://support.apple.com/guide/security/data-protection-overview-secf6276da8a/web) | forensic-ios-forensics: ## 02 iOS 安全机制如何影响取证 |
| [web-ios-reference-de0656fc72](https://support.apple.com/guide/security/data-protection-classes-secb010e978a/web) | forensic-ios-forensics: ## 02 iOS 安全机制如何影响取证 |
| [web-ios-reference-c1df50aa91](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web) | forensic-ios-forensics: ## 02 iOS 安全机制如何影响取证 |
| [web-ios-reference-4eb80a97c7](https://support.apple.com/guide/security/role-of-apple-file-system-seca6147599e/web) | forensic-ios-forensics: ## 02 iOS 安全机制如何影响取证 |
| [web-ios-reference-8fdef7fc68](https://support.apple.com/en-euro/guide/security/sec1a976c067/web) | forensic-ios-forensics: ## 03 应用沙盒、身份与目录 |
| [web-ios-reference-50aa28ec61](https://github.com/apple-oss-distributions/CF/blob/main/PropertyList.dtd) | forensic-ios-forensics: ## 04 Plist、SQLite 和序列化对象；forensic-ios-tools: ## 07 Plist 键、Data 和日期的输出解读 |
| [web-ios-reference-83bb3ee720](https://docs.python.org/3/library/plistlib.html) | forensic-ios-forensics: ## 04 Plist、SQLite 和序列化对象；forensic-ios-tools: ## 07 Plist 键、Data 和日期的输出解读 |
| [web-ios-reference-f9612325f4](https://developer.apple.com/documentation/foundation/date/timeintervalsincereferencedate-swift.property) | forensic-ios-forensics: ## 05 时间：纪元、单位与事件语义 |
| [web-ios-reference-624a3d6efc](https://www.stark4n6.com/2021/05/mvs2021-ctf-iphone.html) | forensic-ios-forensics: ## 08 真实比赛：健康同步、应用快照与 Live Photo |
| [web-ios-reference-aa8086607d](https://www.magnetforensics.com/blog/update-on-magnet-summit-2022-capture-the-flag-contests/) | forensic-ios-forensics: ## 09 真实比赛：累计时长与 WAL 差异 |
| [web-ios-reference-c28539d8f8](https://www.stark4n6.com/2022/06/magnet-user-summit-2022-ctf-iphone.html) | forensic-ios-forensics: ## 09 真实比赛：累计时长与 WAL 差异, ## 10 真实比赛：最后位置与首次搜索 |
| [web-ios-reference-879ebb9a57](https://bakerstreetforensics.com/2022/07/28/magnet-2022-ctf-ios15/) | forensic-ios-forensics: ## 10 真实比赛：最后位置与首次搜索 |
| [web-ios-reference-b277096430](https://www.magnetforensics.com/blog/announcing-the-mvs-2023-ctf-winners-and-a-new-ctf-challenge/) | forensic-ios-forensics: ## 11 真实比赛：健康距离、位置与新版本活动 |
| [web-ios-reference-2749c43720](https://www.stark4n6.com/2023/03/magnet-virtual-summit-2023-ctf-ios-16.html) | forensic-ios-forensics: ## 11 真实比赛：健康距离、位置与新版本活动 |
| [web-ios-reference-457f3cdaa3](https://www.cnblogs.com/zzpu213/p/18692389) | forensic-ios-forensics: ## 12 真实比赛：账本金额、便签和地址状态 |
| [web-ios-reference-d4a1c20c09](https://github.com/abrignoni/iLEAPP) | forensic-ios-tools: ## 01 版本、用途与运行环境, ## 04 常用与扩展参数表, ## 05 输出解读与验证 |
| [web-ios-reference-787e2defd7](https://github.com/abrignoni/iLEAPP/releases/tag/v2026.4.4) | forensic-ios-tools: ## 01 版本、用途与运行环境 |
| [web-ios-reference-1338e9c36c](https://www.icopybot.com/plist-editor.htm) | forensic-ios-tools: ## 01 版本、用途与运行环境 |
| [web-ios-reference-57f0129efc](https://github.com/abrignoni/iLEAPP/blob/7b0594a03c50d9b27ab49fa586e720e788b6236b/ileapp.py) | forensic-ios-tools: ## 04 常用与扩展参数表 |
| [web-ios-reference-241c451a58](https://www.icopybot.com/plist-editor-manual.htm) | forensic-ios-tools: ## 06 Plist_Editor 的只读操作 |

## 5. 已观察的验收结果

| 检查 | 结果 |
| --- | --- | --- |
| python-tests | exit 1；详细日志：`.work\ios-forensics-20261004\python-tests.txt` |
| ui-tests | exit 0；详细日志：`.work\ios-forensics-20261004\ui-tests.txt` |
| check | exit 0；详细日志：`.work\ios-forensics-20261004\check.txt` |
| build | exit 0；详细日志：`.work\ios-forensics-20261004\build.txt` |
| site-audit | exit 0；详细日志：`.work\ios-forensics-20261004\site-audit.txt` |
| web-audit | exit 0；详细日志：`.work\ios-forensics-20261004\web-audit.txt` |

Python共65项测试，64项通过、1项既有失败。既有失败是外部目录 `D:\CTF_MISC_Tools\Forensics\Inseyets PA` 缺失，修改前已经存在；未创建空目录、删除登记或修改测试掩盖。新增5项iOS检查全部通过。UI测试5项通过；静态检查0错误、0警告；构建333页、搜索索引324页；页面与链接审计0错误。

完整重导入退出0，保留工具清单原字节后，所有src及public/practice文件变化为0。重扫描会得到166条工具记录，当前保留162条既有登记，因为本任务没有请求工具清单扩容。

实际浏览器已看到手机取证下“iOS 取证 3篇”，三页路径正确；检索iOS并筛选Forensics/手机取证/知识点得到4条结果（3篇iOS页和手机总览）。搜索可进入原备份页，备份页导航可进入新工具页；新正文14/9节渲染完整，浏览器无已捕获的控制台错误。

## 6. 维护边界与保全

生成正文与src/content-curation维护稿一致，分类和内部来源关联可再次导入。用户明确要求真实比赛依据，audit_site仅对原理页放行“数证杯”这个赛事名称；其他禁词、其他页面、缺失链接及外部工具路径检查保持有效，新增测试锁定该单页例外。

本任务开始前412个站点文件的哈希与副本保存在 `D:\winoptimizeDir\Desktop\Misc学习\ctf-atlas\.work\ios-forensics-20261004\before` 与 `D:\winoptimizeDir\Desktop\Misc学习\ctf-atlas\.work\ios-forensics-20261004\baseline-hashes.json`。任务改动清单保存在同目录change-manifest.json。完整结构化证据见 [forensics-ios-review.json](forensics-ios-review.json)。

两名研究者分别只读复核比赛字段/归属及工具参数/四模式输出，未发现有依据的对应错误。最终页面及三个文章URL、脚本URL均返回HTTP 200；脚本响应字节与磁盘文件相同。
