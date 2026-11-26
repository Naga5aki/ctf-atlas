**Android 模块导航**：[原理与流程](/knowledge/forensic-android-forensics/) · [数据目录与证据](/knowledge/forensic-android-storage/) · [应用与 APK 逆向实战](/knowledge/fic-case-06/) · [工具与实战](/knowledge/forensic-android-tools/)。本页按系统用户、CE/DE 加密空间、虚拟空间与常见应用沙箱梳理 Android 数据的目录结构与证据落点。

## 01 先确认用户、包名与取得方式

记录设备型号、Android 版本、补丁、解锁/加密状态、采集方式和用户 ID。区分整盘/分区镜像、完整文件系统、逻辑备份、应用导出与仅 APK。APK 用于识别程序和数据结构，不能代表用户沙箱已经取得。

从 `packages.xml`、用户包配置、应用列表和 APK 元信息确认真实包名、版本、UID 与安装路径。多用户、工作资料、多开或分身可能把同一包放到不同用户空间；不只查 `/data/data`。

## 02 数据目录速查

| 目录或材料 | 含义 | 分析重点 |
| --- | --- | --- |
| `/data/user/<userId>/<package>/` | 用户的应用凭据加密空间候选 | files、databases、shared_prefs、cache 等 |
| `/data/data/<package>/` | 常见用户 0 的兼容路径 | 确认与真实用户目录的映射，避免重复计数 |
| `/data/user_de/<userId>/<package>/` | 设备加密空间候选 | Direct Boot 阶段可用的部分数据 |
| `/data/system/`、用户系统目录 | 包、账户、系统设置与使用痕迹 | 格式和落点依版本/厂商确认 |
| `/data/misc/`、misc_ce/misc_de | 网络、蓝牙与系统组件相关材料 | 用户和 CE/DE 范围分开 |
| `/data/app/` | 应用程序与安装材料 | 包与版本，不当成用户数据库目录 |
| `/storage/emulated/<userId>/` | 模拟外部共享存储 | DCIM、Download、Documents、应用外部目录 |
| 实际可移动 SD 卡 | 独立存储介质，可能另有文件系统/加密 | 与手机内部共享存储区别处理 |

`/storage/emulated/0` 并不等于一张可移除的 SD 卡。Scoped Storage、应用权限和备份规则会限制逻辑提取的范围；看不到某个应用目录时，先查采集方式，而非认定“应用未安装”。

## 03 六种常见数据表现

| 表现 | 定位方法 | 考点 |
| --- | --- | --- |
| SharedPreferences XML | `shared_prefs/*.xml` | 账户、选项、设备标识、令牌元数据；值不一定明文 |
| 应用内部文件 | files、no_backup、cache 等 | 文本、JSON、序列化、附件；缓存不代表主动阅读 |
| 外部存储 | 公共目录与 Android/data 等 | 媒体/下载和目录权限，检查采集覆盖 |
| SQLite / SQLCipher | databases、DB/WAL/SHM、实际文件头 | 先 schema，后字段语义；加密需正确参数与密钥 |
| ContentProvider | 数据访问接口及对应系统/应用数据 | 是访问机制，不是一种独立磁盘格式 |
| Room、ORM 或网络数据 | SQLite 包装、缓存、同步状态 | Room 常建立在 SQLite 上；云端数据不能由本机缓存保证完整 |

```bash
find ./work/data -type f \( -iname '*.db' -o -iname '*.sqlite' \
  -o -iname '*-wal' -o -iname '*-shm' -o -iname '*.xml' \)
rg -n 'package|userId|version|sharedUser' ./work/data/system/packages.xml
```

目录不存在时保存覆盖缺口，不创建空材料凑齐结构。系统 XML 和数据库要按对应版本解释。

## 04 CE、DE 与重新锁屏

凭据加密（CE）空间通常在用户首次解锁后可用；设备加密（DE）空间用于支持 Direct Boot 的部分数据。首次解锁后再锁屏，不必然重新回到“首次解锁前”的密钥状态；重启会改变条件。记录 BFU/AFU 和采集时状态，而不是仅写“有锁屏”。

文件系统导出是否已经解密、是否包含全部用户、是否保存文件名和元数据，应依据采集记录和实际结构判断。缺少密钥时，不能把高熵数据直接当损坏文件。

## 05 从目录到一条可信记录

选一个应用完整保全沙箱与共享附件，记录数据库/WAL、账户、版本与时间字段。先确定表、主键、消息方向和状态，再按附件 ID/哈希关联文件，最后用系统通知、备份、流量或另一设备记录复核。

通用数据库处理见 [SQLite 与 WAL](/knowledge/forensic-sqlite/)，账号、聊天、运动与删除痕迹见 [手机应用与通信](/knowledge/forensic-mobile-apps/)。

## 06 实战：定位多用户设备中的应用数据

**场景与材料：** 已取得解密的 Android 文件系统导出，其中用户 0 和工作资料用户 10 均有同一包名。目标是确认一条消息及其附件属于哪个用户空间。以下包名为演示占位；实际分析先从安装记录确认真实包名。

### 06.1 按用户空间固定对象

```bash
package_name='com.example.chat'
find ./work/data/user ./work/data/user_de -type d -name "$package_name"
find ./work/storage/emulated -type f -iname '*.jpg'
```

只在实际存在的导出根目录运行；如果共享存储导出落在其他位置，先按采集清单调整。不要追随导出中的软链去读取分析机数据。

1. 将用户 ID、包名、应用版本、安装记录和目录路径放在同一行，区分 CE、DE 与共享附件。
2. 为每个用户分别复制数据库、WAL、配置与附件；同名数据库不能互相覆盖。按本页路径表和 SQLite 专题建立一致快照。
3. 从 schema 与已知样本确认账户 ID、消息主键、方向及附件标识，再关联该用户空间内的文件内容哈希。
4. 检查文件系统是否已解密、用户是否在采集范围内，以及采集时 BFU/AFU 状态；目录缺失与内容为空分别记录。

### 06.2 示例结果与验证

用户 0 的记录显示账号 A，用户 10 显示账号 B，附件 ID 相同但文件哈希不同。先保留两条独立记录，不能按包名或附件名合并。通过账户配置、系统用户映射、附件内容和通知时间交叉核验。最后写明“用户 10 的应用数据库包含该记录”，是否由持机人发送、是否从其他设备同步仍需独立证据。

## 07 实战：穿透 Android 虚拟空间定位应用与附件

### 07.1 场景、材料与空间映射

已经取得解密的 Android 文件系统导出，普通用户目录内找不到目标聊天库，但设备安装了虚拟空间应用。此时应区分宿主用户、虚拟实例和实例内账号：虚拟系统中的 `/data/data` 是嵌套目录，不必对应手机自身的应用沙箱。

| 对象 | 可检查的位置 | 需要记录 |
| --- | --- | --- |
| 虚拟大师类应用宿主 | `/data/data/com.yiqiang.xmaster/` | 安装包、版本、宿主用户及采集范围 |
| 虚拟实例根 | `vprom/sys/sys01/`，以及同级其他实例 | 实例编号、配置、建立与使用痕迹 |
| 实例内应用 | 实例根下的 `data/data/<包名>/` 等实际目录 | 内层包名、账户配置、库与 WAL |
| 导入或共享内容 | 实例根下的 `storage/emulated/0/importFile/` | 文件字节、原始名称和导入链 |

这些是具体产品版本的候选路径，不是所有 VMOS、多开或工作资料的共同标准。先从宿主安装记录和目录布局确认适用版本；`sys01` 不应默认代表唯一实例。

系统自带分身常把包名记成原包名加 `-1`，并重新签名。安装记录里没有这种包时，再查第三方分身应用自己的数据库，一行有效记录通常对应一款被分身的应用。见过的一种库是 `com.qh.privacysec` 下的 `fenshen.db`，目录名可能是 `database` 或 `databases`，以镜像里的实际路径为准。VMOS 一类虚拟机会在宿主包下再放客户机的 `data/data`，一种布局是 `com.vmos.pro/osimg/r/<实例名>/data/data`。实例名只代表一台客户机。宿主机和每个实例分开数应用，再按要求排除预装或指定类型。

### 07.2 从外到内建立证据清单

在工作副本中运行，路径按真实导出根目录调整：

```bash
virtual_root='./work/data/data/com.yiqiang.xmaster/vprom/sys'
find "$virtual_root" -maxdepth 2 -type d
find "$virtual_root" -type f \( -iname '*.db' -o -iname '*-wal' -o -iname '*.xml' \)
find "$virtual_root" -type d -name importFile
```

1. 保存每个虚拟实例的配置和完整应用容器，分别编号；不要把内外层同名数据库互相覆盖。
2. 根据内层安装记录、包名与配置找到微信、NTQQ 或钱包，保全数据库、WAL、偏好设置和附件。
3. 用内层账户标识关联消息与文件。宿主手机账号、虚拟系统账号和聊天账号可以不同。
4. 对 `importFile` 中的目标图片先识别格式、计算完整文件哈希，再核对是否与外层图库或下载文件相同。OCR 用于筛选，最终保留真实图片和人工确认的文字。
5. 时间字段先确认来自宿主、虚拟系统还是应用服务器；仿真时生成的新文件时间不能代替历史时间。

### 07.3 示例结果与验证边界

若内层聊天库的账户配置、好友记录和附件引用都指向账号 A，而外层应用属于账号 B，应形成两套证据记录。相同图片哈希支持内容一致；是否由账号 A 导入，还需要导入日志、应用记录或时间线。缺少某个虚拟实例只能说明本次采集未覆盖，不能证明其从未存在。

账号与加密数据库的细化流程见[手机应用与通信](/knowledge/forensic-mobile-apps/)，跨平台定位见[证据路径全景](/knowledge/fic-case-14/)。

## 08 应用数据路径与版本候选

### 08.1 先读真实沙箱结构

以下路径默认相对实际取得的应用根，不把 `/data/data`、`/data/user/0` 和归档备份域混成一种绝对路径。一般先列 `databases/`、`files/`、`shared_prefs/`、`cache/`、`code_cache/`、`no_backup/`；`app_webview/` 只在采用相关组件且保留该布局时出现。`lib/` 可能是原生库或链接，并非每个应用都包含；不要追随链接读取分析机目录。

| 子目录 | 常见内容 | 实际操作与限制 |
| --- | --- | --- |
| databases | SQLite、WAL/SHM、其他数据库或加密数据 | 先文件头、schema，再列；整个目录保全，不只复制后缀 .db |
| files / no_backup | 用户文件、协议/二进制、会话配置、密钥封装 | no_backup 通常排除常规备份；文件系统导出仍可有该目录 |
| shared_prefs | XML typed 键值、配置与认证元数据 | 解析完整 XML；文件名不是字段语义保证 |
| cache / code_cache | 网络、媒体、代码相关缓存 | 区分内容来源与缓存行为；别当作永久使用日志 |
| app_webview | Chromium/WebView profile 候选 | Cookies、History、Login Data、Web Storage、Local Storage、IndexedDB 等需实际存在才能分析 |

WebView profile 可能含普通 SQLite、JSON、LevelDB 和缓存格式；并非每个 WebView 都保存浏览器式 History、Bookmarks 或密码。`Bookmarks` 在 Chromium profile 中常是 JSON，不要因文件名就运行 SQLite。独立 Chrome 的 profile 与某应用内 WebView 要分清。

### 08.2 通信应用：先按包名和账号定位

| 应用与包名候选 | 查找内容 | 必须确认的条件 |
| --- | --- | --- |
| 微信 `com.tencent.mm` | `MicroMsg/` 下账号目录、`EnMicroMsg.db`、shared_prefs、图片/语音/附件；安装版本和登录标识 | 数据库相对层级、加密与密钥派生依版本；不固定为一个 databases 路径。细化方法见应用通信页 |
| WhatsApp `com.whatsapp` | 沙箱内 `msgstore.db`、`wa.db` 等命中数据库；共享 `WhatsApp/Databases/` 或 `Android/media/com.whatsapp/WhatsApp/Databases/` 中的备份，及 Media | `msgstore.db` 与 `.crypt12/.crypt14/.crypt15` 不是同一格式；`account.info.xml`、`com.whatsapp_preferences.xml`、WABPrefs 仅作候选，按真实版本/字段确认 |
| Telegram `org.telegram.messenger` | `files/cache4.db`，及 `files/accountN/cache4.db`、WAL/SHM、用户配置、缓存媒体 | Android 官方实现有 cache4.db 与账号子目录；消息 BLOB 需对应序列化。`TData` 是其他平台常见布局，不套成 Android 必有目录或统一 AES 库 |
| Signal `org.thoughtcrime.securesms` | `databases/signal.db`、偏好/密钥封装、附件与版本 | 官方实现使用 SQLCipher 和受保护的数据库 secret；不存在所有版本可读的通用 `files/keystore` 明文密钥流程 |
| LINE `jp.naver.line.android` | 实际 databases、账户偏好和附件；`naver_line`、ChatData 等只能作为搜索候选 | 查询 schema 后确认消息/联系人/媒体；不能预设一个文件名、固定密钥或全版本统一表结构 |

上述表用于定位而非承诺每个文件都存在。Telegram 的路径及 SQLite 打开方式可核对[官方 MessagesStorage 实现](https://raw.githubusercontent.com/DrKLO/Telegram/master/TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java)；Signal 的数据库与 secret 机制见[SignalDatabase](https://raw.githubusercontent.com/signalapp/Signal-Android/main/app/src/main/java/org/thoughtcrime/securesms/database/SignalDatabase.kt)及[DatabaseSecretProvider](https://github.com/signalapp/Signal-Android/blob/main/app/src/main/java/org/thoughtcrime/securesms/crypto/DatabaseSecretProvider.java)。网页代码的 main/master 是核查时实现，不代表历史检材同一版本。

**实战顺序：** 包/版本/用户 → 配置中的稳定账号 → 真实数据库 schema → 消息与附件 ID → 内容哈希 → 通知或独立端记录复核。微信/NTQQ 密钥链、SQLCipher 参数、WhatsApp 跨端关联和 Hawk/Conceal 的完整流程在[手机应用与通信](/knowledge/forensic-mobile-apps/)保留，不复制。

### 08.3 社交、支付、浏览器与笔记

| 应用与包名候选 | 优先查看 | 结果判读 |
| --- | --- | --- |
| Instagram `com.instagram.android` | databases、账号/会话配置、媒体/cache、实际 WebView；`local.db`、`main_database.db` 只作候选名 | 私信、浏览/媒体残留依版本，不因 Cookies 直接认定密码可得 |
| TikTok `com.zhiliaoapp.musically`；抖音 `com.ss.android.ugc.aweme` | 各自真实包目录、账号、下载、视频缓存、数据库和偏好 | 是不同产品的包名候选，不能把国际版路径代替国内版；具体渠道/版本以安装记录为准 |
| 支付宝 `com.eg.android.AlipayGphone` | 账户偏好、databases/files、日志与业务缓存；AlipayPreferences、账户 JSON 等按实际搜到内容核对 | 不规定统一大小写 `Databases/Files`；缓存记录或 token 不等于完整账本、资金控制权或当前登录有效 |
| Chrome `com.android.chrome` | `app_chrome/Default/` 下 History、Cookies、Login Data、Web Data、Top Sites、Bookmarks、Local Storage、IndexedDB、cache | `app_webview` 不是独立 Chrome 的通用主 profile；多个 profile 与 Network/Cookies 等版本迁移按真实目录核对 |
| Firefox `org.mozilla.firefox` | 实际 profile、databases、files、应用组件与版本；历史/书签、登录、会话 | 桌面/旧版的 `places.sqlite`、`key4.db`、`logins.json` 是候选，不是现代 Fenix 必有组合 |
| Google Keep `com.google.android.keep` | 实际笔记库（`KeepOfflineDB.db` 候选）、notes/list 类型记录、attachments、同步与账号配置 | 标题、正文、清单、归档/删除状态及修改时间先确认字段；附件与记录关联，不仅关键词命中 |
| 短信/联系人系统 provider | `com.android.providers.telephony`、`com.android.providers.contacts` 的 CE/DE 数据 | 不只搜索普通 user/0；下文单独解释数据库与表 |

现代 Firefox 使用的登录组件与桌面假定可能不同，见[Mozilla 登录 schema](https://mozilla.github.io/application-services/book/rust-docs/src/logins/schema.rs.html)。对于尚未核实的第三方路径，不给“固定文件—固定表—固定解密”的假规则；实际找到后保存包版本、路径、表结构和样本主键，再形成结论。

### 08.4 命名候选不能代替实际定位

一些目录/文件名字只适合作为迁移或版本核对入口。下表**不承诺其存在、大小写、数据库 schema 或内容用途在该产品全部版本相同**；找到后先识别类型，再与包、账号、代码引用或已解析记录关联：

| 应用/类别 | 补充候选 | 操作与判读 |
| --- | --- | --- |
| 微信 | `microMsg.db`、`pref_login.xml`、`app_config.xml` | microMsg.db 不代替已确认的 EnMicroMsg.db；登录/应用配置按真实键和类型解读，字段名不保证明文 |
| WhatsApp / LINE | `WABPrefs.xml`；LINE 的 `user_pref.xml` | 候选偏好设置需确认账号、注册/配置语义，不能假定是聊天数据库口令 |
| TikTok | `musically.db`、files 下 cache/preferences | 找到后先看 schema 与账号/视频引用；缺失就查版本和其他数据库，不造同名空库 |
| 支付宝 | `AlipayDB`、`db0`、Alipay/account、Alipay/secure、`AccountManager.xml`、`LoginInfo.xml` | 识别文件/目录类型，核验账户、交易或安全字段实际语义；不预设大小写、完整账本或有效 token |
| Firefox 的历史/其他 Gecko profile | `webappsFolder/firefox`、`cookies.sqlite`、`cert9.db`、`formhistory.sqlite`、`logins-backup.json` | profile 前缀不固定；分别核对会话、证书、表单历史和备份。证书不等于登录密码，自动填充不等于提交，备份不等于当前有效登录 |
| 系统消息 | `sms.db`、`mms.db` | 只作为 OEM/应用/导出命名候选，不是 AOSP 必有“备用库”；标准 mmssms 表结构见第 10 节 |
| Google Keep | `Attachments` 与实际附件文件 | 注意大小写、实例版本和笔记引用，不将所有附件归给同一条便签 |

Mozilla 的通用 profile 资料解释上述 Firefox 文件类别，但它不是 Android 全版本固定目录说明；现代 Fenix 应先看对应组件和实际数据。[Mozilla profile 文件说明](https://support.mozilla.org/en-US/kb/profiles-where-firefox-stores-user-data)

## 09 系统配置、网络与日志

### 09.1 包、账户、权限与锁屏

| 对象 | 可检索的候选 | 可以/不可以证明 |
| --- | --- | --- |
| 包与安装 | `/data/system/packages.xml`、`packages.list`、用户包状态、实际 APK/采集列表 | 包、codePath、版本、UID、安装/更新时间字段依 schema；正确名称常为 packages.list，不是通用 package.list |
| 系统账户库 | 旧 `accounts.db`，现代 `/data/system_ce/<userId>/accounts_ce.db` 与 `/data/system_de/<userId>/accounts_de.db` | accounts、authtokens、extras 等分范围；存在账号记录不等于当前会话有效或一定本人登录 |
| 默认应用/角色 | 用户配置、`roles.xml`、权限模块目录 | 角色 holder 与安装状态不同；真实比赛示例见流程页 |
| 权限状态 | packages/user runtime-permissions.xml 或版本替代/角色记录，按 API 和组件版本查找 | 安装请求权限、运行时实际授权与 AppOps 状态分开；granted_state.xml/denied_state.xml 仅作待验证名字，不是通用标准 |
| 锁屏/认证 | `locksettings.db`、相应 gatekeeper/synthetic password、厂商认证材料 | 可能有状态、口令类型或保护材料，不承诺明文口令；hardware/版本条件单列 |
| 指纹等生物认证 | 实际用户/OEM 生物认证配置和采集说明 | fingerprint.xml、locksettings.xml、pw.db 只能是待验证名字，不能称通用明文密码库或通用指纹模板 |

`packages.xml` 的属性、嵌套节点与时间编码要按文件和实现读取；`package.xml` 的单数写法不能代替包管理真实文件。签名证书节点不必直接存一个 `fingerprint` 属性，证书字节与摘要要分开。系统 XML 小节先确定包节点及字段，再解释 UID/权限；不要只 grep 一行当完整身份映射。

`<package>` 上的 `ft` 是第一次安装，`ut` 是最后一次更新。原始 XML 里这两个值常见为十六进制毫秒，换算前先认进制。两个时间接近时按属性名抄，搜不到显示名时改搜包名。ADB 授权过的计算机公钥在 `/data/misc/adb/adb_keys`，有的系统写成 `adb_temp_keys.xml`。一条公钥是一台授权过的计算机。只显示用户名和主机名的解析插件不够用来数台数，要回到原文件逐条数。最后一次开机可以看 `/data/system/dropbox/SYSTEM_BOOT@<13位毫秒>.txt`，`@` 后面是这次开机的时间戳，优先于该文件的修改时间。

账户 CE/DE 分库、旧库迁移可核对[AOSP AccountsDb](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/main/services/core/java/com/android/server/accounts/AccountsDb.java)。`accounts.xml` 示例不能套成每台设备有的全账号/全 token 文件；若实际出现，先确定它是系统、应用还是导出工具生成。锁屏文件只在副本中分析，不删除、改名或用重新启动测试历史数据可读性。

### 09.2 Wi-Fi 与热点：保存配置不是连接事实

旧版本常见 `/data/misc/wifi/wpa_supplicant.conf`；后续实现可用 `WifiConfigStore.xml`，模块化版本可能在 misc/apexdata 或 misc_ce/misc_de 用户目录；热点可有 `WifiConfigStoreSoftAp.xml`。`/data/system/wifi/` 不是跨版本唯一目录，按真实搜索结果和时间/用户映射确定。

在实际取得的 wpa_supplicant network 块中，确认 `ssid` 的引号/十六进制表示、`key_mgmt`、`psk`、`scan_ssid` 和 network 边界：

- 带引号的 WPA-PSK 值可能是口令；**64 位十六进制 psk 通常是派生的 PSK/PMK，不是明文密码**，也不能仅凭长度反推出原口令。
- `scan_ssid=1` 是扫描/探测隐藏 SSID 的配置行为，不独立证明隐藏网络何时被发现或连接。
- 配置可能迁移、已过时、被备份还原或由其他设备同步；密码也可能在导出中被隐藏。保留完整块和配置类型，再用连接事件互证。
- SSID/BSSID 是网络线索；SSID 可重复，随机 MAC、AP 迁移和扫描范围要纳入位置判断。

此处以不同年代的格式确认“不是只查一个 conf”，参考[历史 AOSP WifiConfigStore](https://android.googlesource.com/platform/frameworks/opt/net/wifi/+/refs/tags/android-q-preview-6/service/java/com/android/server/wifi/WifiConfigStore.java)。不把历史实现路径外推为所有新设备同一路径。

### 09.3 蓝牙、蜂窝、SIM 与 GPS

| 类别 | 定位方法 | 解释与限制 |
| --- | --- | --- |
| 蓝牙配置 | 搜索实际 `bt_config.conf`、`.bak`、历史 `bt_config.xml`、用户/OEM 蓝牙目录 | 地址、名称、配对材料、服务要按字段解释；排列顺序不等于首次连接时间 |
| Bluetooth HCI snoop | 在取得清单中找 btsnoop/HCI 日志，以 Wireshark 等解析 | 依设备与记录开关存在；没有启用不能补出历史日志。配对/扫描不等于传输文件或持有者身份 |
| 电话 provider | `telephony.db` 中 carriers、siminfo 等实际表 | APN/运营商/SIM配置与短信/通话库分开，不能把它当所有短信和电话记录 |
| radio / RIL / qcril | 已导出的 radio 缓冲、厂商 radio/qcril 数据 | 依芯片/OEM/调试条件；先识别数据库/文本/协议，不设全设备固定路径 |
| 定位 | 实际 location/fused/GMS/地图目录；`flp.db`、`gps.conf` 仅候选 | 配置不等于轨迹，缓存点有精度/时间/来源；GPS、Wi-Fi、基站和地图搜索分别记录 |

蓝牙历史 AOSP 将 `bt_config.conf` 与旧 XML 区别处理，见[对应版本代码](https://android.googlesource.com/platform/system/bt/+/nougat-iot-release/btif/src/btif_config.cc)。没有原始包捕获时不把配置文件解释为 HCI 流量。`[Adapter]` 下的 `Address` 是本机蓝牙地址。以 MAC 为节名的段落是配对或发现过的远端设备，里面的地址、名称和链路材料按字段抄，大小写按文件保留。

**标识词典：** ICCID 标识 SIM/UICC 卡；IMSI 标识移动订阅；MSISDN 是与订阅关联的号码概念；MCC/MNC 指网络国家/运营商；LAC 与 CID 是特定无线制式下的位置区/小区字段，其他制式有不同标识；SPN 是服务提供者名称。字段随 SIM 更换、漫游与运营商实现变化，不能将 IMSI 或 APN 直接当自然人、当前手机号或通话事实。位置点需要记录经纬度坐标系、精度、事件时间和定位源；地图搜索词或配置服务器地址不是位置点。

### 09.4 日志：按类型、时间和留存边界拆分

| 类型 | 可取得的候选 | 主要用途与限制 |
| --- | --- | --- |
| logcat | 当前缓冲或已有采集文本 | auth/login/SMS/location/Wi-Fi 等关键词初筛；环形留存有限，不是完整历史 |
| ANR | 旧 `/data/anr/traces.txt` 或新版本 `anr_*` 等 | 线程、栈、组件/进程与当时事件；不能保证含全部用户动作 |
| native crash | `/data/tombstones/` 的实际文本/Protobuf 等 | 原生进程、模块和崩溃状态；不是同一格式固定脚本 |
| kernel | 已导出 dmesg/内核日志 | 依权限、缓冲与 OEM 留存；不把 `/proc/kmsg` 当离线普通文件读取 |
| recovery / OTA | 已取得 recovery、cache 或现代 OTA/更新记录 | 恢复/更新事件；旧 cache/recovery 路径不保证新机存在 |
| radio / wifi / bluetooth / GPS 厂商日志 | 采集目录、工具报告和实际启用的日志 | 区分组件配置与事件日志，先保存完整记录再过滤 |

日志中的账号/位置关键词可能来自异常栈、缓存、服务端响应或测试内容。保存进程、标签、原始时间格式与上下文，至少由应用记录或另一痕迹复核；Android `logcat -d`、`-v long` 的实际用法在工具页，不在本页复制命令。

### 09.5 网络与日志的版本迁移候选

下表继续保留相关材料类别，未核实的文件名仅作为检索入口，不赋予一个凭名字推定的通用 schema：

| 类别 | 额外候选 | 必须区别的含义 |
| --- | --- | --- |
| Wi-Fi/热点 | `wpa_supplicant.conf.bak`、`wifi.ini`、`hostapd.conf`、`hostapd.accept` | 备份/厂商配置与当前状态分开；若实际格式确认 accept 是接入允许列表，它表达准入配置，不证明该 MAC 已实际连入 |
| 蓝牙 | `btsnoop_hci.log`、`interface.xml`、`auth_authcache`、`bt_stack.log`、`btif_dm.xml` | HCI 捕获、栈日志、配置与认证缓存不是同类材料；未开启捕获时没有历史包，私有 XML/缓存需要对应版本解析 |
| 蜂窝/SIM | `apns-conf.xml`、`imsi.txt`、`pin.conf`、`ril.log`、`qcril.db` | 静态 APN 定义与设备运行事件分开；IMSI 文本须核实来源，PIN 配置/状态不等于明文 PIN、当前解锁状态或成功拨号 |
| 定位 | `gps.db`、`gnss_config.xml`、`gnss_status.xml`，连同已提到的 flp.db/gps.conf | GNSS 是卫星定位相关机制，GPS 是其中一种系统；fused location 可以融合多种定位源。配置、状态、缓存点和连续轨迹分别解释 |
| 日志别名 | `anr_traces.txt` 与实际 traces.txt/anr_* | anr_traces 不是通用 AOSP 默认名称；OEM/导出工具可重命名，先确认内容，不因名字差别漏查 |

定位库只有在字段定义、采样时间、坐标与精度确认后才能进入时间线。融合定位与卫星状态也不能保证每个点都来自 GPS；位置源缺失时如实标明，不补造它。

## 10 SQLite与浏览器数据库

### 10.1 短信、彩信、联系人与通话

在实际 provider 的 CE/DE 路径保全 `mmssms.db` 及 WAL/SHM。常见 AOSP 短信表是 `sms`；彩信为 `pdu`、`part`、`addr`，会话还涉及 `threads`、`canonical_addresses`。不能通用套成 `messages/mms/mms_parts`。彩信 `part.mid` 关联 `pdu._id`；同一彩信可能含文本、图片等多 part，因此 part 数量不等于彩信数量。[AOSP MmsSms schema](https://android.googlesource.com/platform/packages/providers/TelephonyProvider/+/refs/heads/main/src/com/android/providers/telephony/MmsSmsDatabaseHelper.java)

先用工具页的 schema 流程确认字段，以下查询仅用于已有对应列的明文、一致工作快照：

```sql
SELECT _id, address, date, type, read, body
FROM sms
ORDER BY date, _id;
```

`sms.type` 常见 1 收件箱、2 已发送、3 草稿，还可能有 outbox/failed/queued 等类型；`read` 是该记录的阅读状态，不证明对方收到或本人阅读。实际列若有 `date_sent`、`status`，分别核查发送侧时间/状态定义，不把 date_sent 等同本地 date，status 也不是 read 的同义字段。SMS `date` 常为 Unix 毫秒，MMS pdu 的部分字段常为秒；必须逐列核对，不能整库统一除 1000。验证码提取还要核对发件号码、正文、账号业务和时间，不把接收到验证码当已成功登录。[Telephony 消息类型](https://developer.android.com/reference/android/provider/Telephony.TextBasedSmsColumns)

在匹配 schema 中，`sms/pdu.thread_id → threads._id` 可用于会话关联；`threads.recipient_ids` 如存在，先确认其 ID 列表表示，再关联 `canonical_addresses`，不能直接把它当电话号码字符串。计数按消息主键去重，多个参与者、part 或地址行都可能放大联接行数。

联系人通常查看 `contacts2.db` 的 `contacts`、`raw_contacts`、`data`、`mimetypes` 等：一个聚合联系人可对应多个来源/原始联系人、多行电话/邮箱/昵称，`data1` 的含义依 mimetype；不能把 data 表每行当一个人。按归属地统计时，先在 `mimetypes` 查出电话号码行的 `mimetype_id`，再确认号码列和归属地列。不同 ROM 的列不固定。SQLite 的 `substr` 从 1 开始计数。

小米便签若在 `com.miui.notes` 的 `note.db`，先看表结构。一种布局里 `data` 表是预览和时间，`note` 表是正文和修改时间。预览图的时间不代替正文表的修改时间。正文里的“下周五”这类说法，先把修改时间换到目标时区，得到星期几再推算。

`calls` 曾在历史联系人库，现代 AOSP 有单独 `calllog.db`，不能只查 contacts2 后宣布没有通话。[AOSP CallLog 迁移与 schema](https://android.googlesource.com/platform/packages/providers/ContactsProvider/+/master/src/com/android/providers/contacts/CallLogDatabaseHelper.java)

通话核对 `number`、`date`、`duration`、`type`、账号/SIM 等实际字段；常见 1 来电、2 去电、3 未接，其他类型依 API。去电记录不一定接通，duration 的单位及零值意义需定义与其他记录支持。联系人的缓存名称不等于当前姓名或实名身份。[Android CallLog 类型](https://developer.android.com/reference/android/provider/CallLog.Calls)

### 10.2 浏览历史、Cookies 与其他数据类型

`History` 可包含 urls、visits、downloads 等实际表，访问次数、下载路径、状态、来源和时间先读 schema；一条 URL 与多次访问不能混计。`Login Data` 是保存登录类记录，`Web Data` 可涉及自动补全/搜索引擎配置，`Top Sites` 可涉及高频/快捷入口；实际表与更新机制仍要按版本核验，不能把这些库都当完整访问日志。`Bookmarks` 的 JSON 和 Local Storage/IndexedDB 的 LevelDB 数据不要当 SQLite 查询。

Cookies 是常见 **普通 SQLite 容器**，其中 `value` 与 `encrypted_value` 可按实现保存不同形式；并非一个特殊“Google协议数据库”。读取 host、name、path、时间、secure/httponly 等存在的列，确认空 value 是否有加密值；不能套用“33 字节主密钥 + Android DPAPI”的万能流程。[Chromium Cookie 实现](https://chromium.googlesource.com/chromium/src/+/main/net/extras/sqlite/sqlite_persistent_cookie_store.cc)

Web Storage 中字符串、JSON、序列化 BLOB、LevelDB 与应用自定义文件需要相应解析器。SQLite 无法识别时，先文件头、版本、压缩/加密与损坏诊断，不反复跑随机解密参数。

### 10.3 加密数据库与备份不能按品牌硬判

| 对象 | 正确识别链 | 容易误套的规则 |
| --- | --- | --- |
| WhatsApp | 私有明文库 / 加密 crypt 备份 → 具体版本封装 → 对应密钥与认证 → 验证库 | crypt14 不能按“前 16 字节 IV + 通用 CBC”直接处理 |
| Signal | signal.db → SQLCipher 与 protected secret → 应用版本/Keystore 条件 | SQLCipher 不是自动等于有可导出的 files/keystore 明文 key |
| 微信/其他 SQLCipher 应用 | 包/版本 → 参数、key 来源、盐/页大小/HMAC 等 → schema 与记录复核 | 旧版密钥派生或仅品牌名称不保证所有版本可用 |
| Telegram | Android cache4.db 等实际 SQLite 与序列化消息、账号配置 | 普通库中 BLOB 不等于全库 AES，也不等于 Desktop TData |

原有微信、SQLCipher、Hawk/Conceal 认证解密案例统一在[应用与通信](/knowledge/forensic-mobile-apps/)。打开 schema、查询有效记录和附件对应是验证；得到“看似文本”的字节不足以证明解密成功。

## 11 SharedPreferences与认证线索

### 11.1 XML 解析、数据类型与常见候选

常见路径是应用真实根下 `shared_prefs/*.xml`，DE/多用户/备份 `sp` 域要分别映射。`<map>` 可含 `string`、`int`、`long`、`float`、`boolean`、`set`；字符串里的 XML 转义、嵌套 JSON/Base64、空值与布尔类型不要用简单 grep 截断。`long` 可能是时间也可能是计数/ID，先查调用和样本。

| 候选材料 | 检查要点 | 不应作的假设 |
| --- | --- | --- |
| 微信 `com.tencent.mm_preferences.xml`、`auth_info_key_prefs.xml` 等命中项 | 用户、uin/账号、设备/配置与版本 | 文件名不能替代 actual 字段及适用版本 |
| WhatsApp account.info/WABPrefs/preferences 类候选 | 注册账号、显示设置、号码及备份/密钥封装 | 验证或注册配置不等于会话口令或全聊天密钥 |
| 支付宝/PayPal 的偏好、账户 JSON | user/account、状态、token 类型和更新时间 | 不称每个支付 APP 都固定同一文件名；不把缓存当官方交易账本 |
| Gmail/Google 账户相关偏好 | 账户标识、同步、配置，account_pref.xml 仅候选 | Gmail、Google AccountManager 与浏览器会话是不同数据源 |
| Hawk2.xml、crypto.KEY_256.xml | 类型、key 封装、AAD/nonce/tag 和具体库调用 | 原有认证解密案例按其真实版本使用，不套一般 SharedPreferences |

PayPal 的 `auth_prefs.xml` 与 Gmail 的 `account_pref.xml` 不作所有版本固定名；按实际取得内容核对认证、账户与同步，不用名字直接推导可登录凭据。同一账号键在多用户或多个候选文件中出现时，保留路径、字段类型、值和上下文，避免只凭 value 字符串去重。工具页提供 XML 完整解析与工作副本搜索步骤；具体业务解释回到实际代码和记录。

### 11.2 密码、Cookie、JWT、OAuth 与会话

| 类型 | 需要记录 | 可以得出的有限结论 |
| --- | --- | --- |
| 保存的浏览器登录 | profile、origin_url、username_value/password_value/date_created 等实际列候选、加密状态、日期 | 列名和时间需实际 schema 核验，不泛用一个 username/password 查询；存在保存记录不保证其为明文或当前有效 |
| WebView/Chrome Cookie | host/name/path、值或加密值、时间、flags | 保存了该会话材料，不证明采集时或现在仍有效 |
| JWT | header、payload、alg、iss/aud/sub/exp 等存在字段 | Base64url 解码仅得到自述内容；未验证签名时不能信任身份/权限 |
| OAuth access/refresh token | token 类型、scope、账号/客户端、expiry | opaque token 未必可解码；有 refresh token 不保证能刷新、登录或控制账号 |
| API key / session / 注册数据 | 所在文件、调用链、接口与用途 | API key 可能只识别客户端，不是用户身份；Telegram/WhatsApp 会话材料依平台版本 |

Chrome `Login Data` 与 Firefox 登录材料必须从实际 Android profile/组件判断；桌面 `key4.db + logins.json` 不作 Android 万能解密链。Telegram Android 用户配置/账号目录与 Desktop session 不能互相套用。解码、解密、签名验证、令牌有效性和历史登录是五个不同结论；本流程只离线研究已取得材料，不用 token 访问线上账户。

## 12 共享存储、缩略图与媒体

### 12.1 公共目录、应用外部目录与多用户

`/sdcard`、旧 `/mnt/shell/emulated/0`、`/storage/emulated/<userId>`、镜像中的 `/data/media/<userId>` 可能代表不同视图/年代的模拟共享存储；先根据挂载和采集清单确认映射，避免同文件计数数次。实际可移动 SD 卡需独立记录文件系统/加密与介质身份。多用户路径中的数字是 userId，不是完整应用 UID。

| 目录候选 | 内容与考点 | 验证 |
| --- | --- | --- |
| DCIM、Pictures、Movies、Music | 拍摄/下载/处理媒体 | 文件真实格式、EXIF、内容哈希与记录引用；拍摄和下载分开 |
| Download、Documents | 浏览器/应用下载、导出、文档 | 与 History/downloads 或应用记录对应，文件名不独立证明来源 |
| `Android/data/<package>` | 应用外部专属数据、cache、files | 访问限制依系统/targetSdk；不是任意普通 APP 均可读的公共根 |
| `Android/media/<package>` | 部分应用外部媒体 | 按真实包与布局，如 WhatsApp；不是通用 Android/media/0 |
| Bluetooth 等实际收件目录 | 可能的接收文件 | 需要传输日志/内容/时间互证，不按目录名认定蓝牙来源 |
| 以点开头的目录/文件 | 隐藏、缓存、应用自建材料 | 使用完整文件清单；“隐藏”只是命名/展示属性，不等于恶意 |

Scoped Storage 的条件和取证范围在[原理页](/knowledge/forensic-android-forensics/)解释；虚拟实例中的共享目录与 importFile 实战仍见本页第 07 节，不重复展开。

### 12.2 缩略图、残留与临时文件

可能出现 `DCIM/.thumbnails/`、thumbdata、应用缩略图缓存、MediaStore 对应数据库或厂商数据库。`/.thumbnails/thumbnails.db` 和其列结构**不是跨版本通用标准**；先确认文件头、尺寸、编码和记录关联，不套固定 thumbnail 表。

缩略图可能保存已不在当前目录中的图像预览，但不等于可完整恢复原图，更不能直接代替原文件哈希。某图像可能来自浏览、分享、下载或同步；以原记录引用、EXIF 和另一文件位置交叉复核。

一并检查实际存在的 cache、`.bak`、`.db-journal`、WAL、`/data/local/tmp` 与点目录。临时目录可能含调试/采集/测试文件，不能仅凭位置认定攻击；记录创建来源、时间、内容与相关进程。删除恢复的事务与页范围详见[SQLite 与 WAL](/knowledge/forensic-sqlite/)。

**最终复核清单：** 每个候选都落到实际用户/包/版本；每个数据库结论有表与主键；每个媒体结论有真实文件哈希；每个时间保留原始值/单位；每个缺失都区分采集缺口、版本不匹配、解析失败和已证实不存在。
