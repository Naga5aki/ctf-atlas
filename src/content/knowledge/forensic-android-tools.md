---
title: "Android 工具与实战：ADB、ABE 与 ALEAPP"
summary: "校正AB头和备份域，详解ADB访问条件、ALEAPP报告、数据库与XML检查、APK线索及密码格式验证。"
module: "Forensics"
track: "手机取证"
topic: "Android 工具与实战"
tags: ["文件格式", "时间线"]
status: "已整理"
sourceIds: ["web-android-6ba84fe92ff7", "web-android-2e05c4f39e9e", "web-android-c7421eab83e6", "web-android-2ed046aa17df", "web-android-1ccf76f91048", "web-android-6b1323629d6c", "web-android-bef9685c766e", "web-android-03795385e422", "web-android-ed07e8a336e2", "web-android-1d67ff31065b", "web-android-89cac5bbdc5f", "web-android-bace005e1aae", "web-android-87dab259917b", "web-android-05cae033cedc", "web-android-6b93ef6a0e98", "web-android-45b6e1ef28e8", "web-android-85731a165e63", "web-android-7bb6aaba0f31", "web-android-2d14bb12ad33", "web-android-fc6620ebb56a"]
challengeIds: []
relatedIds: ["forensic-android-forensics", "forensic-android-storage", "forensic-sqlite", "forensic-mobile-apps", "reverse-bytecode"]
updated: "2026-10-04"
---

**Android 模块导航**：[原理与流程](/knowledge/forensic-android-forensics/) · [数据目录与证据](/knowledge/forensic-android-storage/) · [应用与 APK 逆向实战](/knowledge/fic-case-06/) · [工具与实战](/knowledge/forensic-android-tools/)。命令默认 Kali/Linux；本机 Windows ALEAPP 的实际版本和合成验证另行标明。

## 01 工具分工与运行环境

| 工具 | 用途与输入 | 环境/边界 | 输出与复核 |
| --- | --- | --- | --- |
| ADB / Platform Tools | 连接已经允许调试的设备，查询状态、包与可读文件 | 对应主机平台的官方工具；USB/网络 transport、授权、UID、用户解锁与权限各自成立 | 设备清单、属性、查询结果、复制文件；不是万能私有数据提取或解密工具 |
| ABE（Android Backup Extractor） | 根据 AB 容器格式将已有 `.ab` 转为 tar；加密输入须正确的已知备份密码 | Java 运行环境与所用发布版本配套；离线处理副本 | tar、过程日志、成员清单；再检查包/域、数据库和记录 |
| ALEAPP | 解析已有 Android 文件系统、归档或支持的镜像材料 | 官方源码按该发行版 requirements 配置 Python；Windows 发布包也可使用 | HTML、TSV、日志及 LAVA 相关数据；关键记录回查输入 |
| sqlite3 / DB Browser for SQLite | 明文库、表结构、只读查询、WAL 一致快照 | 普通 SQLite 工具不自动打开所有 SQLCipher 或应用备份 | schema、行、检查结果；不能以 integrity_check=ok 证明业务真实 |
| apkanalyzer / 逆向工具 | 解析 APK Manifest、代码、资源与 native 线索 | Android SDK 命令行工具或对应静态工具；不在证据设备安装未知 APK | 包名、版本、调试标志、资源/调用链；不等于已取得使用数据 |
| 本页只读辅助脚本 | 逐行 AB 头、typed XML、JWT 解码、显式纪元时间 | Python 3 标准库，无额外库；仅本地文件或给定字符串 | JSON 与输入哈希；不是解密、签名验证或采集工具 |

操作前固定输入副本和报告目录，记录每个实际工具的版本/help 与完整错误。取得工具输出不等于获得事实结论。官方下载与接口依据：[ADB](https://developer.android.com/tools/adb)、[ABE](https://github.com/nelenkov/android-backup-extractor#usage)、[ALEAPP](https://github.com/abrignoni/ALEAPP#usage)。

## 02 ADB：从固定设备到明确权限

### 02.1 第一轮只读盘点

以下是读者使用的模板，**本次未执行设备采集**；`SERIAL`、包名与用户号由实际清单替换。查询本身会与正在运行的系统交互，仍记录采集起止和状态。

```bash
mkdir -p ./reports ./work
adb version > ./reports/adb-version.txt
adb help > ./reports/adb-help.txt
adb devices -l > ./reports/adb-devices.txt
SERIAL='SERIAL_FROM_DEVICE_LIST'
adb -s "$SERIAL" get-state
adb -s "$SERIAL" shell id
adb -s "$SERIAL" shell getprop > ./reports/android-properties.txt
adb -s "$SERIAL" shell pm list users > ./reports/android-users.txt
adb -s "$SERIAL" shell pm list packages --user 0 -f > ./reports/packages-user0.txt
adb -s "$SERIAL" shell pm path com.example.chat > ./reports/package-apks.txt
```

`device` 说明 transport 可用，`unauthorized` 表示尚未获调试认证，`offline` 表示连接/响应未就绪。多设备固定 `-s`，避免采错目标。`getprop` 的全量输出是 `[属性]: [值]`；核对 release、sdk、security_patch、build.type 等，单个空属性不证明无加密。`pm path` 可能有多条 base/split APK；包列表可见不代表沙箱可读。[ADB 状态与选项](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md)

### 02.2 复制、run-as、root 与采集范围

```bash
adb -s "$SERIAL" pull -a /sdcard/Download/example.txt ./work/example.txt
sha256sum ./work/example.txt
adb -s "$SERIAL" shell run-as com.example.chat --user 0 id
adb -s "$SERIAL" shell run-as com.example.chat --user 0 ls -la
```

`pull -a` 尝试保留时间/模式，但不提升权限；主机哈希只标识这次输出，未有两端校验时不宣称与设备端逐字节核对。私有 `shared_prefs/databases/files` 只有具备相应访问条件才可取；Permission denied、unknown package、package not debuggable 等纳入覆盖清单。

`run-as <package> [--user ID] <command>` 的包名在 `--user` 前；应用必须已安装并允许调试，设备实现还可能禁用 run-as。它切换应用身份，不是 root，也不把 `allowBackup=true` 当 `debuggable=true`。[AOSP run-as](https://android.googlesource.com/platform/system/core/+/master/run-as/run-as.cpp)

`adb root` 会请求重启 adbd；典型 userdebug/eng 与量产 user 构建条件不同，常见响应 `adbd cannot run as root in production builds` 不是“数据不存在”。`su` 仅在已有相应环境时成立；bootloader 解锁、root、CE 解密互不等价，不列为常规保全步骤。[ADB root 机制](https://android.googlesource.com/platform/packages/modules/adb/+/main/docs/dev/root.md)

已授权设备中若为问题需要，可另外记录 `adb -s "$SERIAL" shell dumpsys window` 或 `dumpsys wifi` 的当前状态；输出含义依系统服务版本。它们不是长期日志，也不证明历史窗口/连接，敏感字段可能脱敏。能否读 `/data/system/packages.xml`、`/data/data` 应以实际身份和错误为准，不用访问失败倒推应用未安装。

### 02.3 旧式 adb backup 的选项与限制

历史实现的 `-f` 指输出、`-apk/-noapk` 控制程序包、`-obb/-noobb` 控制相应 expansion 数据、`-shared/-noshared` 控制共享存储、`-all` 请求所有适用包、`-system/-nosystem` 控制系统包，尾部可选择包名。历史默认通常不包括 APK/OBB/共享存储，而 -all 默认可含系统包；显式写选项避免不同版本默认值的误解。**这些选项不是“提取完整文件系统”的保证**，也不代表每个当前 adb/设备还实现相同接口。[固定历史 AOSP 实现](https://android.googlesource.com/platform/system/core/+/e323976e747c28b78b5e1be565317f500e0f5c06/adb/commandline.cpp)

仅在已确认支持旧接口并记录操作影响的场景，历史命令模板为：

```bash
adb -s "$SERIAL" backup -f ./work/backup.ab -apk -obb -shared -all -nosystem
```

先检查实际二进制 help、设备实现、用户确认和应用规则；当前官方 man page 不列 backup/restore，不能据此给所有年代一个结论。Android 12 对 target API 31+ 的应用数据有默认排除，开发调试例外与 allowBackup、fullBackupContent、dataExtractionRules 要分别核对。[Android 12 ADB backup 限制](https://developer.android.com/about/versions/12/behavior-changes-12#adb-backup)、[应用备份属性](https://developer.android.com/guide/topics/manifest/application-element#allowbackup)

取证中已有 `.ab` 可以离线识别；不要为了扩大范围改 Manifest、重签名安装、重启或执行 `adb restore`。本页后续转换不向设备恢复备份。

## 03 AB、tar 与 pk8：先读结构，再谈解包

### 03.1 ASCII 多行头，不是固定 24 字节

AB 的基本头逐行读取，换行是结构的一部分：

```text
ANDROID BACKUP
<version>
<compressed: 0 or 1>
<encryption: none or AES-256>
```

前三个参数分别是版本文本、压缩标志、算法名；不是二进制大端版本/校验和/密钥长度，也不存在通用“第 8 字节 bit 0/bit 2”规则。常见 `ANDROID BACKUP\n5\n1\nnone\n` 正好 24 字节，**不是固定 24 字节**可以跳过后喂给任意解压工具。

| 分支 | 后续处理顺序 | 验证 |
| --- | --- | --- |
| none，压缩 0 | 当前读取位置就是未压缩 tar payload 起点 | 列 tar 成员，检查完整性与备份域 |
| none，压缩 1 | 从实际偏移读取 zlib-wrapped DEFLATE，再识别 tar | 不是 gzip，不能通用 tar -xzf |
| AES-256 | 再读盐/迭代/IV/主密钥 blob，用正确密码验证并解密，最后按标志解压 | 头解析通过不证明密码正确或认证/内容完整 |

AES-256 头另有五行：user salt、checksum salt、PBKDF2 rounds、user IV、加密 master-key blob。实际编码和旧版密码兼容由对应格式实现处理，不固定某个偏移截出“密钥”。[ABE 官方格式实现](https://github.com/nelenkov/android-backup-extractor/blob/master/src/org/nick/abe/AndroidBackup.java)

### 03.2 ABE：无加密与已知密码的操作

```bash
mkdir -p ./reports ./work
java -version
sha256sum ./work/backup.ab > ./reports/backup-ab.sha256
java -jar ./abe.jar unpack ./work/backup.ab ./work/backup.tar
tar -tf ./work/backup.tar > ./reports/backup-members.txt
```

加密备份的官方语法允许尾部已知 password，也支持 `ABE_PASSWD`。需要时使用临时环境变量，避免把值写在示例命令历史中；输出文件预先选未使用名称，不覆盖已有 tar：

```bash
read -r -s -p 'Backup password: ' ABE_PASSWD
printf '\n'
export ABE_PASSWD
java -jar ./abe.jar unpack ./work/backup.ab ./work/backup-known-password.tar
unset ABE_PASSWD
tar -tf ./work/backup-known-password.tar > ./reports/backup-known-members.txt
```

环境变量也不是永久秘密保管工具，执行完清理；已知密码条件与状态记录单列。先阅读完整退出状态/日志，再验证 tar 成员和目标数据库；写出 bytes 或文件非零不足以证明完整。实际提取先检查成员是否有绝对路径、`..`、软硬链接或特殊节点，在隔离工作目录按工具的路径防护能力提取，不向主目录或生产手机还原。

**Python/手动路线：** 可按上述 ASCII 行逐行取得真实 payload offset，none 时依据压缩 0/1 直接读 tar 或 zlib 解压，再列 tar；AES 分支不手工跳头假装明文。社区曾提及的 `libab` 并非统一的官方标准包和 CLI，离线解包优先使用已核实的 ABE，或用本页标准库脚本先做只读结构检查。不同替代工具仍需同样的成员与内容验证。

### 03.3 备份 domain 与真实目录映射

全备份常见路径为 `apps/<package>/<domain>/<relativePath>`，不是单数 `app/` 或所有应用统一 `app_` 前缀：

| token | 范围 | 映射注意 |
| --- | --- | --- |
| a | APK | 不默认是一个 apk/ 子目录；存在 APK 不证明存在用户数据 |
| f / db / sp / r | files / databases / SharedPreferences / 应用根域 | db、sp 是归档短名，不是设备根的真实目录名 |
| ef / obb | 应用外部文件 / expansion 材料 | 仍需用户与实际共享/外部目录映射 |
| d_f / d_db / d_sp / d_r | 对应 DE 范围 | 与 CE 数据分开，避免跨用户覆盖 |
| k | key/value 备份相关 | 不能直接当完整沙箱结构 |
| shared/ | 顶层共享存储前缀 | 按归档路径和用户信息确认 |
| _manifest / _meta | 包清单及相关元信息候选 | 保留真实内容，核对版本/包/备份规则 |

例如 `apps/com.example.chat/db/messages.db` 应报告为备份里的包/domain/相对路径，不能伪写为设备 `/data/data/com.example.chat/db/messages.db`。cache、code_cache、no_backup 和排除域未必进入备份；支持某个 domain 不保证此次备份含它。[AOSP FullBackup 常量](https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/app/backup/FullBackup.java)

遇到 `.pk8` 后缀文件时另行判断：Android 构建签名中的 `.pk8` 是 **PKCS#8 私钥**，常与 `x509.pem` 证书配合使用，不是 `.ab` 备份容器。应先用 `file`、字节头、导出记录和相邻文件确认真实格式，不存在所谓的独立 `.pk8` 备份解包流程。[AOSP 构建签名](https://source.android.com/docs/core/ota/sign_builds)

## 04 ALEAPP：解析、输出与一条记录的复核

### 04.1 实际版本与常用参数

本机 Windows `aleapp.exe` 的 help/version 实测为 **2026.4.3**。源码安装按所用发行版 requirements 与 Python 版本执行，不将本机发布包的依赖外推给所有版本。本机 help 确认以下选项；当前源码可另核对[参数实现](https://github.com/abrignoni/ALEAPP/blob/main/aleapp.py)。

| 参数 | 用途 | 使用条件与常见误解 |
| --- | --- | --- |
| -t fs / tar / zip / gz / raw | 选择目录、对应归档或支持的镜像输入 | fs 要保留正常路径/名称；AB 不直接选 tar；容器支持不是 FBE 万能解密 |
| -i / -o | 输入与基础输出目录 | -o 目录先存在，每次生成独立报告目录 |
| --version / -h | 固定版本与帮助 | 先保存实际输出，不从网页截图代替本机版本 |
| -p | 导出支持的 artifact 路径清单 | 独立运行，清单是插件匹配路径不是已查出的业务记录 |
| -m / -d | 加载 .alprofile / .lcasedata | 分别是解析 profile 与案件元数据 |
| -c | 生成 profile/case-data 模板 | 官方 help 要求独立使用，不与常规解析混在一条命令 |
| --custom_output_folder | 自定义输出子目录名称 | 不覆盖已有报告 |
| --html_row_limit | 超出阈值不在 HTML 展示整表，转向 TSV/LAVA | 本机默认 50000；0 才要求写所有行，网页没行不等于数据库没行 |
| --custom_artifacts_path | 增加插件目录 | 固定可信插件及版本；插件是执行代码，不加载来历不明的脚本 |
| -w | 调整输出文字换行 | 显示选项，不改变证据含义 |

raw 相关的 `--image_password_file/env`、`--image_private_key`、`--bitlocker_key` 是特定容器/卷的密码/密钥输入，不等于可解密任意 Android FBE、Signal、WhatsApp 或硬件 Keystore。具体容器格式看实际 help，不复用其他平台的密钥流程。

### 04.2 已导出文件系统的运行顺序

源码版示例，从 ALEAPP 程序目录运行；输入路径按真实导出根调整：

```bash
mkdir -p ./reports/aleapp
python3 aleapp.py --version
python3 aleapp.py --help
python3 aleapp.py -p
python3 aleapp.py -t fs -i ./work/android-fs -o ./reports/aleapp
```

归档经过确认后选择对应 `-t tar/zip/gz`，不用更改后缀欺骗解析器。查看运行日志里的匹配路径、插件异常和记录数；从报告选一行，回到其输入文件/表/主键与原始时间值核对。遇到空表先区分采集未覆盖、路径迁移、插件不支持、数据损坏和加密条件，不判断“从未使用”。

### 04.3 输出解读与实际合成验证

本轮本机实测仅对**纯合成** `vendor/build.prop` 进行 `fs` 解析，不冒充比赛检材。实际 build 插件匹配 vendor/system 路径，输出 7 条制造商、品牌、型号、device、Android Version、SDK、Version Release 记录；日志包含 `Found 7 records for Build` 与 `Report generation Completed.`，退出 0。TSV 与 SQLite 七行逐字段一致，HTML 包含全部预期值，输入与报告内复制文件哈希一致。

| 实测产物 | 查看方式 | 能验证什么 |
| --- | --- | --- |
| _HTML/Build.html | 浏览器查看，并与原文件比值 | 显示的解析标签和值是否一致 |
| _TSV Exports/Build.tsv | 文本/表格查看 | 七行 key/value 不被 HTML 行数阈值隐藏 |
| _lava_artifacts.db | SQLite 只读，实际 get_build 表 | 报告数据与输入映射，不能假设所有版本固定此 schema |
| _lava_data.lava | 本次是 JSON 元数据 | parser_info 的版本；不是因为扩展名就当 SQLite |
| data/vendor/build.prop | 原始来源副本与输入比哈希 | 解析对象与实际字节对应 |

本次本机文件名与报告结构按 2026.4.3 实际输出解释，不承诺旧版相同。真实设备采集、真实比赛镜像复现、ABE 真样本解包均未执行；只将已经验证的工具功能与格式检查标为实测。

## 05 数据库、XML 与日志的可操作检查

### 05.1 明文 SQLite：先结构，再业务

工作目录应保全一致的主库、`-wal`、`-shm`、`.db-journal`，不能用不同时刻采到的同名文件拼库。以下对已有明文工作快照执行：

```bash
file ./work/db/mmssms.db
xxd -l 32 ./work/db/mmssms.db
sqlite3 -readonly ./work/db/mmssms.db '.tables'
sqlite3 -readonly ./work/db/mmssms.db '.schema sms'
sqlite3 -readonly ./work/db/mmssms.db 'PRAGMA integrity_check;'
```

普通 SQLite 的头含 `SQLite format 3`；没有该头可能是加密、压缩、封装、截断或其他格式，不立即指定 SQLCipher。`integrity_check` 返回 ok 是结构检查，不证明时间/身份/消息真实。只读打开还要符合该版本 WAL 读取所需目录条件；原检材只保全，必要的快照工作在另一副本。

寻找 `.bak`、`.old`、journal 与 WAL，分别记录大小、哈希、时间和归属，不用“最新名字”覆盖当前库。WAL 可含尚未 checkpoint 的已提交内容，journal 可有历史页面，但都不保证全部删除可恢复。恢复、事务与一致性详见[SQLite 与 WAL](/knowledge/forensic-sqlite/)，不在原件上运行 checkpoint、压缩重写或恢复写入。[SQLite WAL 条件](https://sqlite.org/wal.html)

### 05.2 SharedPreferences：检索不代替 XML 解析

离线搜候选，路径可带空格；先定位后结构解析，避免把一条 grep 输出叫作“找回口令”：

```bash
find -P ./work/android-fs -type f -path '*/shared_prefs/*.xml' \
  > ./reports/shared-prefs-paths.txt
rg -n -i -g '*.xml' 'password|passwd|pwd|secret|token|session|auth|user|account' \
  ./work/android-fs > ./reports/auth-candidates.txt
python3 ./android_inspect.py prefs ./work/shared_prefs/sample.xml \
  > ./reports/preferences-typed.json
```

`rg` 退出 1 可以只是无匹配，其他错误另看；不静默丢弃不可读和坏 XML。脚本返回输入 SHA-256、字段原始类型与值，解析实体及 set；不把所有字符串自动当时间/密钥。真实认证值保留在案件目录，分享报告时做恰当脱敏。

### 05.3 logcat：主机命令、当前缓冲与过滤副本

已经具备设备访问条件时，先导出当前可读的 buffer 与格式，不清空日志：

```bash
adb -s "$SERIAL" logcat -b all -d -v long > ./reports/logcat-current.txt
rg -n -i -C 3 'password|passwd|pwd|secret|token|auth' \
  ./reports/logcat-current.txt > ./reports/logcat-auth-candidates.txt
rg -n -i -C 3 'location|latitude|longitude|gps|sms|mms|wifi|wpa|supplicant|connect' \
  ./reports/logcat-current.txt > ./reports/logcat-event-candidates.txt
```

`-d` 取完当前日志后退出，`-v long` 展示长格式；buffer 可含 main/system/radio/events/crash 等，具体可用性由版本/权限决定。保存读取起止、设备时区与格式；long/默认展示的日期信息不能一律视为带完整年份/时区。epoch 是时间修饰符，可在对应实现中与 long 组合成 `-v long -v epoch`；先看本机 `adb logcat --help` 与实际结果，不凭展示补历史年份。[官方 logcat 选项](https://developer.android.com/tools/logcat)

短词 lat/lon、text/message/connect 易误报；保留 PID、tag 和前后文，对账号/位置/短信业务做数据库或其他痕迹复核。当前环形缓冲不是全历史，没有命中也不能证明未发生。ANR、tombstone、kernel、recovery/OEM 日志的路径和限制见目录页。

## 06 APK 与密码格式：沿使用链验证，不套模板

### 06.1 静态 APK：二进制 Manifest、资源、DEX 与 .so

先固定 APK/split 的哈希和版本；`AndroidManifest.xml` 在 APK 内通常是编译 AXML，用能够解析编译资源/AXML 的工具，而不是对整个 ZIP 或二进制 Manifest grep 后宣称完整分析。Android SDK apkanalyzer 的 Manifest 输出可作为第一步：

```bash
apkanalyzer manifest application-id ./work/app.apk
apkanalyzer manifest print ./work/app.apk > ./reports/manifest-decoded.xml
apkanalyzer manifest debuggable ./work/app.apk
unzip -l ./work/app.apk > ./reports/apk-members.txt
```

`android:debuggable` 是程序属性，不能靠给证据设备换装修改版制造新的访问条件；Manifest 中的 allowBackup/dataExtractionRules 另查。具体代码与资源链统一见 [APK 与字节码逆向](/knowledge/reverse-bytecode/)，不在 Android 取证重复完整逆向教程。[官方 apkanalyzer](https://developer.android.com/tools/apkanalyzer)

按解码后的 `res/`、`assets/`、`resources.arsc` 与 DEX 调用检索 password/secret/api_key/apiKey/token/client_secret 等候选；`build.gradle` 通常属于源码工程，不是发布 APK 必带文件。候选可能是测试值、公开客户端标识或无引用常量，必须追踪**配置读取 → 算法初始化/接口调用 → 实际文件或记录验证**。

`lib/<ABI>/*.so` 是 ELF/native 线索，先识别 ABI、字符串引用和 JNI 调用，不把 `strings` 命中称为实际密钥。R8/ProGuard 的压缩、优化与标识符重命名不同于自动加密所有字符串；如取得匹配 `mapping.txt` 可辅助对应，其它字符串保护或加固另识别。需要运行时验证时仅在另建实验环境和副本中开展，不在证据设备执行未知 APK。[Android R8 说明](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)

### 06.2 明文、MD5、Base64、JWT 与 OAuth 速查

| 表现 | 操作 | 结论边界 |
| --- | --- | --- |
| password 字符串 | 完整 XML 解析、实体还原、引用点与业务记录 | 字段名称不证明其是当前有效密码；明文仅按实际样本报告 |
| 32 个 hex | 查代码/协议、盐、迭代、编码后再选择算法 | 长度只是 MD5 候选，也可能是别的摘要或随机 ID |
| 已核实 raw MD5 | 可对副本用 `hashcat -m 0 -a 0 ./work/hashes.txt ./work/candidates.txt` | -m 0 仅 raw MD5，字典不保证命中；命中要重算并比对原值，不把加盐/迭代强套此模式 |
| Base64 | 校验字母表与 padding，解码后识别文本/二进制结构 | 编码不是加密，也不保证结果是 user:password |
| JWT | 分 header/payload/signature；Base64url 使用 -/_ 并可能省略 =，正确补齐后解析 JSON | 解码不是签名验证；alg/iss/aud/sub/exp/iat/nbf 未经验证不得当可信声明 |
| OAuth / `ya29.` 等线索 | 确定 access/refresh、scope、expiry、issuer/客户端 | opaque token 未必是 JWT，前缀不证明有效、权限或历史成功登录 |

JWT 工具仅输出 `signature_verified: false`；不联系服务端，不接受其声明作为认证结果。exp/iat/nbf 等 NumericDate 常为 Unix 秒，仍要确认具体格式。[RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)、[Hashcat 官方模式与示例](https://hashcat.net/wiki/doku.php?id=example_hashes)

### 06.3 AES、PBKDF2、XOR 与自定义封装

AES-CBC 需正确 key、IV、填充和封装布局；AES-GCM 还需正确 nonce、AAD、tag 及认证结果，不能把“看起来像文本”作为通过。IV 不必位于密文前 16 字节，WhatsApp `.crypt14` 等更不能拿扩展名直接套一个通用 CBC 脚本。应用日志/备份与数据库的密钥也未必相同。

PBKDF2 要确定 password 编码、salt、iterations、PRF/digest 和 dkLen，不固定 SHA-1、1000 次或某个全机盐。XOR 要核对 key/周期/偏移及完整样本，不因短串可读就确认。Base64 是表示层，混淆是程序/数据转换层，认证加密则提供不同保证。原有 Hawk/Conceal 与 SQLCipher 完整解密验证在[应用与通信](/knowledge/forensic-mobile-apps/)保留；参数来自实际版本与调用链。[Android 加密实践](https://developer.android.com/privacy-and-security/cryptography)

## 07 只读辅助检查与复核练习

下载[Android 结构检查脚本](/practice/android_inspect.py)，在本地案件工作目录使用。脚本只检查结构/解码/换算，不连接设备，不解包归档、不解密备份、不验证 JWT 签名、不修改输入：

```bash
python3 ./android_inspect.py ab ./work/backup.ab
python3 ./android_inspect.py prefs ./work/shared_prefs/sample.xml
python3 ./android_inspect.py jwt --token-file ./work/session-token.txt
python3 ./android_inspect.py time 1000 --epoch unix --unit ms
python3 ./android_inspect.py time 11644473600000000 --epoch webkit --unit us
```

AB 输出 version、compressed、encryption 与实际 payload_offset，AES 只说明头与元数据，`payload_status` 明示未解密/未解压；XML 返回每个字段 type/value；JWT 只解析头和 payload；时间保留原始数字、纪元/单位与 UTC。检查器限制 XML 为 4 MiB、JWT 为 1 MiB/最多 64 层嵌套，拒绝 DTD/实体声明和不支持的字段；这是检查器边界，不是 Android 格式的通用大小上限。未知/截断/非法参数返回非零并给出错误，不自动修复原件。时间示例分别是构造的 Unix 1 秒及 WebKit 表示的 Unix 纪元，用于校验公式，不是真实比赛答案。

本页的纯合成格式和 ALEAPP 样本用于**验证工具作用与边界**，不作为虚构竞赛题。最终实战验收仍是：取得输入范围 → 保存版本/日志 → 解析一条具体记录 → 回查源数据 → 独立互证 → 写明未验证内容。
