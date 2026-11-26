**Android 模块导航**：[原理、考点与流程](/knowledge/forensic-android-forensics/) · [数据目录与证据](/knowledge/forensic-android-storage/) · [应用与 APK 逆向实战](/knowledge/fic-case-06/) · [ADB、ABE 与 ALEAPP](/knowledge/forensic-android-tools/)。Android 与 [iOS 取证](/knowledge/forensic-ios-forensics/) 并列；跨平台聊天、密钥链与健康数据继续在[手机应用与通信](/knowledge/forensic-mobile-apps/)维护。

## 01 先识别检材：拿到的是什么，缺少的是什么

Android 取证的目标不是“打开所有文件”，而是把**设备、用户空间、应用账号、具体记录及时间**联系起来。一个包名、一张缓存图或一条系统账户记录，都不足以独立证明某个人完成了某次操作。

| 基本概念 | 专业解释 | 分析时的具体用途 |
| --- | --- | --- |
| Android / AOSP / OEM | Android 是操作系统平台，AOSP 是开源实现基础；OEM 可调整目录、组件和日志 | 路径先作为候选，按系统版本、厂商与实际文件确认 |
| APK、split APK、包名 | APK 是程序包；一个应用可有 base 和多个拆分包；包名是程序身份线索 | 保存全部取得的组成部分，核对版本、签名和安装用户，不能把 APK 当用户数据 |
| UID 与 Android userId | UID 是进程/应用的权限身份；userId 是系统用户或工作资料空间的标识 | 同包在用户 0 与 10 中可能有不同账号；userId 不等于完整 UID |
| 应用沙箱 | 基于 UID、文件权限、SELinux 等隔离的应用运行与存储环境 | 普通 shell 可列包，不代表可读取每个包的 databases |
| ContentProvider | 通过 URI、权限与实现向其他组件暴露数据的访问接口 | 它不是独立磁盘文件格式；接口结果与底层数据库要区别记录 |
| SharedPreferences / Room | 前者常用 XML 保存键值；后者是数据库访问抽象，常基于 SQLite | 先看字段类型和实际 schema，不能把 Room 文件当另一种通用加密容器 |
| 逻辑 / 文件系统 / 物理提取 | 分别偏向接口导出、目录与文件、分区或存储层获取；工具名不能替代方法说明 | 每种方法的删除空间、元数据、密钥和用户覆盖独立核对 |

先记录检材哈希、采集工具版本、提取方法、设备型号/系统/API/补丁、用户与账号、提取起止时间、设备时区、BFU/AFU 状态和采集清单。型号与系统可结合 `build.prop`、采集报告、包记录核验；不能仅凭归档名称推断。

### 01.1 提取层级决定能够回答的问题

| 已取得材料 | 可以开始做什么 | 仍需核对的缺口 |
| --- | --- | --- |
| 仅 APK | Manifest、代码、资源、库、数据模型分析 | 未取得使用者的聊天、账号和附件 |
| DCIM/Download 等共享目录 | 媒体元数据、下载内容、文件关联 | 不等于应用私有目录已采集 |
| `.ab` 或应用备份 | 检查容器、备份域、规则、实际成员，再分析可读数据 | 被排除应用、cache/no_backup、时间及加密条件 |
| 解密文件系统导出 | 分用户查看应用、系统与共享数据，关联 WAL 和附件 | 不保证全盘未分配空间、全部历史记录或硬件密钥 |
| 原始分区/镜像 | 文件系统、元数据和有条件的删除恢复 | FDE/FBE、文件系统支持、密钥可用性 |
| 云/平台导出 | 账户活动、登录、服务端记录、跨设备同步 | 不一定在该手机生成，不是本机实际操作的完整日志 |

Android 12 对 target API 31+ 应用的 ADB 备份有额外限制；应用备份规则与 `debuggable` 条件要分别核查。非零备份文件不证明“全量”；格式处理详见[工具页](/knowledge/forensic-android-tools/)。[Android 12 备份行为](https://developer.android.com/about/versions/12/behavior-changes-12#adb-backup)

## 02 安全原理：加密、权限和设备状态不是一回事

### 02.1 FDE、FBE 与 CE/DE

FDE 是整块用户数据分区层面的加密；FBE 是基于文件的加密，并支持不同用户、存储类别使用不同保护条件。**FBE 从 Android 7.0 开始支持，出厂搭载 Android 10 及以上的设备要求使用 FBE**；不能把所有旧版系统归为 FBE，也不能写成每台设备都同时启用 FDE 与 FBE。系统版本、出厂要求、升级路径与 OEM 实现要分开。[AOSP 文件加密说明](https://source.android.com/docs/security/features/encryption/file-based)

CE（Credential Encrypted）数据通常在对应用户首次解锁后可用；DE（Device Encrypted）数据可支持 Direct Boot 阶段。BFU 是本次开机尚未首次解锁，AFU 是已经首次解锁；**用户 0 已解锁不代表工作资料也已解锁**。AFU 后再锁屏与重启不同。目录、状态判读与多用户完整实战见[数据目录与存储结构](/knowledge/forensic-android-storage/)，此处不复制既有七节。

### 02.2 Keystore、TEE 与 StrongBox

Android Keystore 提供应用使用密钥的接口，密钥可设置用途、认证和有效期等限制。部分密钥由 TEE 或 StrongBox 等硬件支持，但不是每个设备、每种算法和每个密钥都使用 StrongBox。**能够调用密钥进行操作，不等于能导出密钥字节**；拿到应用文件或 root 身份，也不保证得到可离线使用的硬件绑定密钥。相反，应用自身保存的配置密钥、未加密缓存仍需实际检查，不能用“支持 Keystore”概括所有文件。[Android Keystore](https://developer.android.com/privacy-and-security/keystore)

### 02.3 Scoped Storage、调试授权与 root

Scoped Storage 管理应用访问共享存储的范围，与设备/文件加密不是同一概念。Android 10 开始采用相关模型，Android 11 对相应 targetSdk 应用进一步强制；应用私有外部目录、媒体权限与文档选择接口不能混用。具体可读范围还受系统/API、应用 targetSdk、角色与采集身份影响。[共享存储规则](https://developer.android.com/training/data-storage#scoped-storage)

ADB 的 `device` 状态仅说明调试连接可用，不证明 CE 解锁或 root。`run-as` 仅在应用及设备满足调试条件时切换到应用身份，不是全机提权。`adb root` 请求重启 adbd，零售构建常不支持；已有 `su` 与 bootloader 解锁也不是同一种能力。**解锁 bootloader 通常要求清理用户数据**，不能列为保全原数据的例行前置步骤。这里解释状态，不在活设备执行改变状态的演示。[沙箱原理](https://source.android.com/docs/security/app-sandbox)、[Bootloader 状态转换](https://source.android.com/docs/core/architecture/bootloader/locking_unlocking)

### 02.4 多用户、工作资料和虚拟空间

一个物理设备可以包含系统用户、次用户、工作资料和应用自建虚拟实例。用户号要从实际用户记录确认；`99` 不是固定“访客编号”，`0` 也不能无条件理解为持机人日常账号。宿主与虚拟实例内的 `/data/data` 可能形成两层路径；按**宿主 userId → 实例 → 内层包 → 账号**建立映射，保留原有虚拟空间实战，不以同名数据库合并。[AOSP 多用户机制](https://source.android.com/docs/devices/admin/multi-user)

## 03 可重复的取证流程

| 顺序 | 操作 | 产物与复核点 |
| --- | --- | --- |
| 1 保全 | 固定输入、哈希、采集清单、时间和设备状态；工作目录与报告目录分开 | 材料清单、提取范围、未取得/未知类别 |
| 2 识别 | 区分 tar/zip/AB/原始镜像；检查头、成员、用户、程序版本 | 实际格式、用户映射、包名与版本表 |
| 3 初筛 | ALEAPP 等工具解析，保留日志；同时按目录索引手工搜索 | 候选记录与失败项，不能把解析空表当不存在 |
| 4 深查 | 完整保留主库、WAL、SHM、journal 和相邻配置；核对 schema/字段 | 路径、表、主键、状态、原始时间和值 |
| 5 关联 | 稳定账号 ID → 会话 → 消息 → 附件；系统角色/使用痕迹与应用互证 | 去重规则、附件内容哈希、来源区分 |
| 6 校时 | 确定每个字段的纪元、单位、时区和事件含义 | 原始值、转换公式、UTC 与需提交的当地时间 |
| 7 复核 | 回查至少一条解析记录、一个附件和一处系统痕迹 | 工具报告与底层记录对应，另列矛盾和缺口 |
| 8 输出 | 分开事实、推断、缺失及版本条件 | 证据位置、步骤、结果、限制，可由另一人重做 |

离线初筛在工作副本进行，不追随导出中的软链去读分析机其他目录：

```bash
mkdir -p ./reports
find -P ./work/android-fs -type f -print0 | sort -z \
  | xargs -0 -r sha256sum > ./reports/input-sha256.txt
find -P ./work/android-fs -type f \( -iname '*.db' -o -iname '*-wal' \
  -o -iname '*-shm' -o -iname '*.xml' -o -iname 'build.prop' \) \
  > ./reports/candidate-paths.txt
```

该清单只是文件候选，既不自动判断它们为明文数据库，也不证明提取完整。用户、CE/DE、`.ab` domain 与文件系统目录必须先统一表示；不能把归档的 `db/` domain 直接写成设备路径。

## 04 常见考点：问题、证据与答题口径

| 考点 | 优先检查 | 需要避免的错误 |
| --- | --- | --- |
| 设备、系统与用户身份 | 采集记录、属性、系统用户、packages、账户库 | 设备名、手机号、SIM、账号混为一人 |
| 应用安装/更新、默认应用 | 包与版本、用户包配置、roles.xml | 安装了 Chrome 不等于默认浏览器；文件副本时间不是安装时间 |
| 短信/彩信、验证码、通话 | mmssms、contacts/calllog、对应表/状态 | MMS 附件数当消息数；草稿当已发；通话尝试当接通 |
| 聊天最多联系人/发送方 | 消息方向与稳定 ID，好友/会话库 | 双向总数当本人发送数；附件 join 后重复计数 |
| 账号、密码、令牌 | typed XML、数据库、代码中的调用链 | Base64 当加密；JWT 解码当签名通过；硬编码 key 当所有版本通用 |
| 浏览/下载/搜索 | History、downloads、Cookies、Web Storage | 搜索当到访；下载风险状态当实际感染；Cookies 当明文密码库 |
| Wi-Fi/蓝牙/热点/SIM | 系统网络配置、日志、telephony siminfo、Checkin | 已保存网络当连接轨迹；配对当文件传输；SIM 标识当实名身份 |
| 位置/运动/追踪设备检测 | 图像 GPS、地图库、Google Play services、健康应用 | 基站/Wi-Fi/搜索/检测点混为连续 GPS 轨迹 |
| 开机、关机、电量与时区 | bootstat、shutdown-checkpoints、电池库、系统时间配置 | 文件名当全部事件时间；电量/时区变化当定位 |
| 删除/残留/隐藏/分身 | WAL、journal、缓存、回收范围、虚拟实例 | 逻辑导出保证恢复全部删除；缩略图当原图 |

### 04.1 时间换算必须由字段定义决定

Android 数据常见 Unix 秒或毫秒，Chromium 的部分时间字段使用 1601-01-01 UTC 起算的微秒。**不是所有 Chrome/Android 字段都采用同一单位**；调用时间、消息时间、同步时间、缓存创建时间也不是同一事件。

Unix 毫秒先除以 1000；WebKit/Chromium 微秒转换为 Unix 秒时，常用 `value / 1000000 - 11644473600`，前提是已核实该字段定义。不要看到 13 位数便自动认定单位。工具页提供显式纪元/单位转换器。

记录 IANA 时区或精确偏移，并按事件日期处理夏令时。历史美国东部时间不能全年固定减四小时。系统当前时区、照片时区、应用服务器 UTC 和导出展示时区分别记录；多个字段相差整小时不应立即认定设备时钟被篡改。[Chromium time 定义](https://chromium.googlesource.com/chromium/src/+/main/base/time/time.h)

## 05 真实比赛实战：从公开题目提炼可复用方法

以下赛事与数据位置来自主办方公告和参赛者公开解析；**未复跑比赛检材**。流程是对已公开解题证据的归纳，不把自行写的命令称为原比赛命令，不展示固定答案。构造练习与真实题目分开标记。

### 05.1 Magnet Virtual Summit 2022：发送方、SIM 与空文件元数据

**真实材料：** Google Pixel 3 的 `Pixel.tar`，另有 Google Takeout。主办方有 Android 题目及公开解析入口。[主办方公告](https://www.magnetforensics.com/blog/update-on-magnet-summit-2022-capture-the-flag-contests/)、[Kevin Pagano 的 Android 解析](https://www.stark4n6.com/2022/05/magnet-virtual-summit-2022-ctf-android.html)

- **发送方考点：** `data/data/com.snapchat.android/databases/arroyo.db` 的 `conversation_message.sender_id`，关联 `main.db` 的 `Friend.userId`，再读 `Friend.username`。先核对 schema 和方向，再按稳定发送方 ID 统计；不要直接按显示名分组，也不要因联接重复计数。
- **SIM 考点：** `com.google.android.gms/shared_prefs/Checkin.xml` 的 `CheckinService_lastSim` 与 `data/user_de/0/com.android.providers.telephony/databases/telephony.db` 的 `siminfo.icc_id` 互证。ICCID 与 IMSI 分别说明不同标识，不能混用。
- **恢复出厂考点：** `data/misc/bootstat/factory_reset` 可为空标记；此时检查采集保存的文件系统元数据，而不是认为零字节没有意义。解压后分析机的新时间不替代历史时间。
- **验证：** 报告记录回到源库主键，SIM 两位置按同一设备和时间范围核对。作者当时工具尚未覆盖较新的 Snapchat 数据库，转用 AXIOM 与人工查库；这个事实说明“工具未解析”不等于“没有材料”，不外推为今天仍不支持。

### 05.2 Magnet User Summit 2023：关机原因、电量与冷门应用

**真实材料：** Google Pixel 3a XL Android 数据；属于 MUS 四月现场赛及五月线上复赛，不是二月 MVS 的 iOS/Windows/VMDK 题。[主办方赛事说明](https://www.magnetforensics.com/blog/announcing-the-mvs-2023-ctf-winners-and-a-new-ctf-challenge/)、[Kevin 的 Part 1](https://www.stark4n6.com/2023/05/magnet-user-summit-2023-ctf-android.html)、[Part 2](https://www.stark4n6.com/2023/05/magnet-user-summit-2023-ctf-android_5.html)

- **开关机：** `data/misc/bootstat/last_boot_time_utc` 与 `data/system/shutdown-checkpoints/` 的检查点文件；先看具体事件和关机原因，不能只取文件名的数值当该文件所有事件时间。
- **电量与时区：** `com.google.android.settings.intelligence/databases/battery-usage-db-v4` 用于电量问题；`com.google.android.apps.turbo/databases/turbo.db` 提供相关时间/时区线索。不同库分别确认事件，再比较首次/末次记录。公开解析没有完整 schema，实际查询要先 `.schema`，不编造固定 SQL。
- **未被自动识别的小众应用：** `com.todoist/databases/database.db` 的 `items`，`com.android.vending/databases/suggestions.db`，以及 `data/system_ce/0/recent_tasks`。从安装包列表进入应用目录，任务、搜索和截图形成补充证据，不能单凭最近截图证明完整执行历史。
- **复核与限制：** 原解析的部分 Wi-Fi 判断明确是猜中，且有 EST/UTC 偏移问题；不把猜测或固定换算当标准解法。不同日期应按真实时区规则换算，热点配置值不证明当时有客户端连接。

### 05.3 Magnet Virtual Summit 2024：默认浏览器、AirTag 检测和搜索

**真实材料：** `Google Pixel 3a XL Logical Image - Data.tar`，主办方确认 Android 12；另有 Facebook、Discord 导出包。[主办方公告与题目](https://www.magnetforensics.com/blog/2024-magnet-virtual-summit-ctf-winners-and-another-chance-to-play/)、[Madi Brumbelow 的解析](https://m-brumbelow.github.io/posts/MVS2024CTF/)、[Kevin 的 Android 解析](https://www.stark4n6.com/2024/03/magnet-virtual-summit-2024-ctf-android.html)

- **默认浏览器：** 在该检材检查 `data/misc_de/0/apexdata/com.android.permission/roles.xml`，以 `android.app.role.BROWSER` 的 holder 判断分配结果，不以“Chrome 已安装”代替。两篇解析存在一层目录重复的路径差异，此处采用 Madi 公开位置，实际仍须按检材查找。
- **AirTag 检测：** `data/user/0/com.google.android.gms/databases/personalsafety_db`；公开解析及 ALEAPP 报告用于追踪设备检测位置问题。未公布完整表字段，不能构造假 schema。检测坐标是一次检测记录，不等于标签持有人身份或连续跟踪轨迹。
- **搜索：** Maps 的 `gmm_storage.db` 与 Google Play 的 `suggestions.db` 分属不同应用。地图搜索证明查询意图，商店搜索不等于安装或运行。
- **来源分离：** Facebook 导出的 `security_and_login_information/ip_address_activity.html` 与 Android 相机文件属于不同采集来源；保留各自的时区与格式，校准后再关联。逻辑 `Data.tar` 不等于全盘删除空间已获取。

### 05.4 2024 数证杯初赛：地图头像缓存的原文件哈希

公开第一人称解析涉及高德应用资料、短信及开机等问题；其中头像方向给出 `/media/0/Android/data/com.autonavi.minimap/files/autonavi/httpcache/imageajx/` 候选。这里的根前缀取决于导出方式，不能照抄成所有手机固定路径。[参赛者公开记录](https://tn1k6.github.io/2024/11/18/2024%E6%95%B0%E8%AF%81%E6%9D%AF-%E5%88%9D%E8%B5%9BWP%5B%E8%AE%A1%E7%AE%97%E6%9C%BA%E3%80%81U%E7%9B%98%E3%80%81%E6%89%8B%E6%9C%BA%5D/)

**操作链：** 根据真实包名和用户定位 → 在多个头像/媒体缓存中识别格式 → 用账号配置、记录引用或图像内容核对候选 → 对取得的原始文件字节计算题目要求的哈希 → 保存路径、算法及复核记录。工具预览截图、缩略图和原文件可能不同，不能替代计算。公开记录未给型号、完整镜像名或多数 schema，因此仅采用已公布路径和方法，不追加未公开字段或固定答案。

## 06 易错点与问题驱动的提取优先级

不要按“十个路径一定齐全”去补空文件，按问题选择以下十类材料：**短信彩信、联系人通话、账户偏好、应用数据库、Wi-Fi/热点、浏览器历史与下载、蓝牙、定位/地图、照片媒体、系统包/用户/角色**。每类标注已取得、未取得或未知；同一文件多个别名只算一次。

1. 文件名含 `.db` 不证明 SQLite；明文 SQLite 头存在也不证明每个字段未加密。先识别字节与 schema。
2. 不因 `-wal`、`.db-journal` 或 `.bak` 存在就认定包含全部删除记录；页归属、事务状态、恢复范围及工具版本要复核。
3. 缓存、缩略图、通知预览支持残留内容，不自动证明本人主动查看、发送或保存。
4. `read=1`、送达状态、通话 duration 与业务动作需要按应用/系统定义解释；一端数据库不是双方通信的全部证据。
5. Wi-Fi 配置、蓝牙配对和基站/APN 不是统一“位置日志”；保存网络与真实连接时间要另外举证。
6. 账户 token、Cookie、JWT、数据库口令、锁屏凭据是不同对象；字段名 `password` 也需要确认编码、散列和使用位置。
7. `R8/ProGuard` 的标识符混淆不保证所有字符串都被隐藏；APK 静态信息也不能代表某次历史使用。
8. “物理/root/完整提取”不是全量明文承诺；缺失条件要写清，不能用工具生成成功替代证据验证。

## 07 既有知识整合与去重

| 情况 | 本次处理 | 保留入口 |
| --- | --- | --- |
| 新增 | Android 独立子模块、原理流程、工具实战和四组真实比赛研究 | 本页与工具页 |
| 修订 | AB 头、FBE 年代、短信表、Chrome/Telegram/系统路径和密码万能规则 | 对应目录页与工具页，条件随主题说明 |
| 合并 | 用户/目录/CE-DE/多用户/虚拟空间原七节继续保留，补入应用、系统、通信和日志证据 | [既有目录页](/knowledge/forensic-android-storage/)原 ID 与 URL 不变 |
| 去重 | 微信/NTQQ、SQLCipher、Hawk/Conceal、WhatsApp 的既有完整步骤不重复搬运 | [应用与通信](/knowledge/forensic-mobile-apps/) |
| 保留 | iOS、钱包、Reverse APK/JNI 的完整正文与分类 | Android 只提供必要跳转，不覆盖原稿 |
| 保留与互链 | [移动终端（Android）取证](/knowledge/fic-case-06/)的原十一节、URL 与既有分类继续保留在 Android 子模块 | DJI 飞行日志、WebView/JNI、动态调用与有界校验等既有细化案例不重新复制 |

本模块三篇主线说明通用原理、证据落点与工具操作；加上保留的移动终端细化案例，分类中共四篇。通用流程与旧案例在目标不同的层级互链，不删除旧页以凑数量。

**总结：** 先确认范围和身份，再读结构和原始值；自动报告用于定位，关键结论回到数据库、配置、日志与真实文件。提交答案前至少能回答“哪个用户的哪个应用、哪条记录、什么时候、由什么独立证据复核、还缺什么”。

指定参考文章已按章节与命名应用逐项处理，并对版本相关或错误项作条件化校正：[Android Forensic Analysis Reference Guide](https://tqandjdc.github.io/2026/06/08/Android-Forensic-Analysis-Reference-Guide/)（作者 1t5@l0^e，CC BY-NC-SA 4.0）。这里以独立说明和官方实现核验组织内容，不直接复制整篇文字；覆盖与修订明细保留在维护记录。
