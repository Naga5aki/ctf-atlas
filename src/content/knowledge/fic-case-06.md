---
title: "Android 应用与 APK 逆向取证"
summary: "梳理 Android 目录、应用数据库、APK 与通信定位证据。"
module: "Forensics"
track: "手机取证"
topic: "Android"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
challengeIds: []
relatedIds: []
updated: "2026-10-15"
---

**Android 模块导航**：[原理、考点与流程](/knowledge/forensic-android-forensics/) · [数据目录与证据](/knowledge/forensic-android-storage/) · [应用与 APK 逆向实战](/knowledge/fic-case-06/) · [ADB、ABE 与 ALEAPP](/knowledge/forensic-android-tools/)。本页聚焦 Android 应用数据库提取、APK/DEX 静态反编译、Native SO 逆向与无人机飞行日志解析。

## 01 建立设备、用户与应用清单

Android 取证先确定采集范围：完整文件系统、应用导出、备份包和界面记录能看到的材料不同。再用用户 ID、包名、应用版本和数据库路径组织证据，避免把多个用户、多个安装版本或缓存副本合并成一份活动记录。以下离线场景假设文件系统已只读挂载到 `/mnt/evidence`；命令读取检材目录，结果写入 `./work/`。

### 01.1 应用沙箱目录与权限边界

Android 多用户、CE/DE 加密空间与虚拟空间的完整目录表见[Android 数据目录与存储结构](/knowledge/forensic-android-storage/)。针对单个目标应用，优先定位 `/data/user/<用户ID>/<包名>/`（用户 0 常兼容映射为 `/data/data/<包名>/`）下的 `databases/`、`files/`、`shared_prefs/`、`cache/`，以及共享存储 `/storage/emulated/<用户ID>/Android/data/<包名>/files/`（区分内部与外部专用目录见[Android 应用专用存储说明](https://developer.android.com/training/data-storage/app-specific)）：

```bash
EVIDENCE_ROOT=/mnt/evidence
ls -ld "$EVIDENCE_ROOT/data/user" "$EVIDENCE_ROOT/data/data"
find "$EVIDENCE_ROOT/data/user" -mindepth 2 -maxdepth 2 -type d -print
find "$EVIDENCE_ROOT/storage/emulated" -path '*/Android/data/*/files' -type d -print
```

**判读：** 发现 `/data/user/0/com.example.chat/` 只说明该用户目录保存应用相关材料；继续与应用安装清单、APK 包名和版本核对。读取前检查软链，绝对软链应在检材根目录内重新定位，不跟随到分析机。

### 01.2 设备身份、安装与使用时间

| 目标 | 证据落点 | 可支持的结论 |
| --- | --- | --- |
| 型号、系统版本 | 采集设备信息、系统属性、相关 `build.prop` | 系统记录的型号与构建身份；属性可能被修改 |
| 包名、版本、安装状态 | `/data/system/packages.xml`、`packages.list`、APK Manifest | 对应版本的安装管理记录与程序身份 |
| 安装或更新时间 | 包管理元数据、可信采集界面、安装日志 | 依字段区分首次安装、更新或恢复，不能混同 |
| 最后使用与活动 | `/data/system/usagestats/`、应用日志、业务记录 | 在覆盖时间范围内的使用痕迹，不保证完整 |
| 账户与同步 | `accounts.db`、用户目录下账户资料、`sync/` 等 | 账户配置与同步状态，实际位置依系统版本变化 |

```bash
grep -nE 'ro\.product\.(model|manufacturer)|ro\.build\.(version|fingerprint)' \
  "$EVIDENCE_ROOT/system/build.prop"
grep -n 'com.example.chat' "$EVIDENCE_ROOT/data/system/packages.xml"
grep -n 'com.example.chat' "$EVIDENCE_ROOT/data/system/packages.list"
```

路径不存在时，检查实际系统分区布局及采集清单，不能填入分析机或其他设备的属性。`packages.list` 并不在所有版本都保存安装时间；时间字段还需确认编码单位、所属安装阶段与系统时钟。

### 01.3 实战：核对通信应用的安装日期

**材料：** `packages.xml`、目标 APK、采集时应用管理记录、聊天数据库。记录包名和版本后，从对应 package 条目提取首次安装/更新时间候选值，按实际字段规范换算为 UTC，再按确认的设备时区显示。

**示例判读：** 首次安装字段显示某日，更新字段显示随后一日，首条聊天记录又在更晚日期。这三者描述不同事件，不能把首条消息日期当成安装日期。若设备曾迁移、备份恢复或安装记录重建，应核对安装日志和账户关系；报告同时保存原始值、解释规则、时区和来源路径。

## 02 应用数据的三条读取路径

### 02.1 数据库、偏好设置与文件

```bash
find "$EVIDENCE_ROOT/data/user/0/com.example.chat" -maxdepth 3 -type f -print
ls -l "$EVIDENCE_ROOT/data/user/0/com.example.chat/databases/"
grep -rInE 'key|token|account|server|database' \
  "$EVIDENCE_ROOT/data/user/0/com.example.chat/shared_prefs"
```

将主库、`-wal`、`-shm` 同批保存到工作目录，确认表结构后查询记录；SQLCipher 密钥与格式见[数据库取证](/knowledge/fic-case-05/)。XML 作为文本读取，出现 `key` 字段后还需追踪代码究竟用于数据库、网络认证还是其他用途。

**删除记录恢复：** 依次区分当前已提交视图、WAL 历史帧、freelist 和页内未覆写残留。残留 cell 或字符串可能不完整，须验证页、记录头、主键、字段和时间；“能搜到内容”不能等同于“当前数据库有完整有效记录”。对原件执行 VACUUM、清理缓存或启动应用，可能改变这些材料。

### 02.2 实战：便签中的计划与跨设备口令

**场景：** 便签应用的 `todo.db` 保存行程和凭据提示，另一台计算机存在加密卷。先查询 `.schema`，确定内容、记录 ID、创建/修改时间与删除标记，再检索卷名、用途或账户关键词。保留整条便签上下文，而不只截取看似口令的字符串。

记录“计划在某日出行”支持计划内容，不能证明实际到达。候选口令需要在卷副本中按真实 PIM、密钥文件等条件验证；成功解密后继续核对卷内用途、账户路径和便签关系。敏感凭据不宜在公开报告中完整展示。

### 02.3 实战：统计本地 AI 主动提问与模型

**材料：** 应用数据库、模型目录、配置及加载日志。先查看表结构，定位对话、消息、角色和会话字段。若数据库有 `messages` 表，可按实际结构使用以下模板。

```sql
SELECT role, COUNT(*) AS rows FROM messages GROUP BY role;
SELECT conversation_id, id, role, created_at, content
FROM messages
WHERE role = 'user'
ORDER BY created_at, id;
```

判读时区分主动提交、系统提示、助手输出、重试、编辑和导入副本；统计记录数不总等于实际提问次数。再检查 `files/models/local` 等路径，固定文件摘要，并读取模型元信息与配置中的加载名称。单靠文件名含某模型品牌，不能证明该模型真正运行过或模型内容一致。

## 03 APK 静态分析：从结构到数据流

### 03.1 先解剖包结构

APK 通常以 ZIP 容器保存资源和代码。先清点成员并计算摘要，不运行 APK 或其中 SO。

```bash
sha256sum ./evidence/app.apk
unzip -l ./evidence/app.apk
mkdir -p ./work/apk
unzip -q ./evidence/app.apk -d ./work/apk
jadx -d ./work/jadx ./evidence/app.apk
```

`jadx -d` 保存反编译代码与资源；[JADX 文档](https://github.com/skylot/jadx)说明反编译可能存在失败或不一致，关键分支应回到 DEX/Smali 指令复核。解压前检查成员路径是否包含目录穿越、重复项或异常大文件。

| 成员 | 关注内容 | 常见误读 |
| --- | --- | --- |
| `AndroidManifest.xml` | 包名、SDK、权限、组件、入口 | 常为二进制 XML，直接 `cat` 不可正确读取 |
| `classes*.dex` | 类、方法、字符串和调用关系 | 多 DEX 需全部检查，混淆名不代表功能 |
| `resources.arsc`、`res/` | 字符串、资源 ID 与配置 | 一条字符串未必被执行路径使用 |
| `assets/` | Web 前端、本地配置、加密数据 | 需追踪加载位置和解密逻辑 |
| `lib/<abi>/*.so` | Native 代码、常量与密文 | 不同 ABI 或版本可能内容不同 |
| `META-INF/` 等签名信息 | 部分签名材料和打包信息 | 新签名方案不一定只位于此目录 |

### 03.2 权限、资源、代码和 Native 逐层核对

已有 `aapt dump permissions app.apk` 可读取 Manifest 权限；Android SDK 的 AAPT2 对应命令如下，工具版本需记录。

```bash
aapt dump permissions ./evidence/app.apk
aapt2 dump permissions ./evidence/app.apk
rg -n 'upload|report|collect|CREATE TABLE|INSERT INTO|ContentValues' ./work/jadx
rg -n 'Base64|decode|AES|Cipher|KEY|getString|NativeLib|System\.loadLibrary' ./work/jadx
rg -n 'addJavascriptInterface|JavascriptInterface|loadUrl' ./work/jadx
```

[AAPT2 dump 文档](https://developer.android.com/tools/aapt2#dump)列出可读取的权限等信息。声明通讯录、位置、IMEI 相关权限只支持能力请求；是否获批、是否调用、是否成功上传，需要沿代码和运行痕迹验证。

**搜索顺序：** 权限定位潜在数据 → 上传/表创建逻辑定位载体 → 资源和 assets 定位参数 → Native 调用定位补充算法。对混淆程序，也可从 Android API、SQL 关键字和网络库调用反向追踪，不依赖类名含 `Uploader`。

清单里带 `MAIN` 和 `LAUNCHER` 的是启动入口。校验通过后 `startActivity` 打开的是主界面，按要找的那一个抄完整类名。加密地址在字符串资源里时，沿资源引用找到解密函数，再按 `System.loadLibrary` 实际加载的库名定位本地库。流量里另外一条明文访问，和资源解密出的地址是两条数据。邮件外发可搜 `javax.mail`、`mail.smtp.host`。密钥长度、IV 是否取密钥前半段、密文是否分段后再拼接，都按该样本的代码写。只有提交值、没有调用链的样本，保持步骤待核。

### 03.3 实战：还原上传端点与采集表

**场景：** 代码包含 Base64 常量和 `CREATE TABLE`，分析目标是确认候选上传位置和本地保存的数据字段。

1. 记录解码调用、常量来源、拼接条件和 URL 被交给哪个网络函数。
2. 离线解码为 `https://api.example.test/collect/userdata` 这样的候选地址，保留原常量和解码字节，不访问该地址。
3. 读取完整 `CREATE TABLE` 语句及后续 `ContentValues`/`INSERT`，确认表名、列和写入来源。
4. 在采集的数据库中检查实际表结构和记录，比较代码预期与现存数据。
5. 查网络日志或其他通信记录，判断调用是否实际发生、响应是否成功。

```bash
python3 - <<'PY'
import base64
encoded = b'aHR0cHM6Ly9hcGkuZXhhbXBsZS50ZXN0L2NvbGxlY3QvdXNlcmRhdGE='
print(base64.b64decode(encoded, validate=True).decode('utf-8'))
PY
```

代码中的端点和表名支持程序设计；不自动证明数据已外传。Base64 是编码，可能还包含压缩或后续加密层；先检查解码后的结构再决定下一步。

## 04 资源种子与加密配置

### 04.1 确定派生单位、模式与填充

**场景：** `assets/config.dat` 为密文，代码通过 `getString(R.string.config_seed)` 取种子，再执行 MD5 与 AES。沿资源 ID 找到种子；不要只搜到同名字符串便使用。

必须区分 `MD5(seed).digest()` 的 16 字节原始摘要，与 `MD5(seed).hexdigest()[:16].encode()` 的 16 字节 ASCII 十六进制字符。二者是不同密钥；代码若截取的是字符串，不能擅自改为原始摘要。也要核对 UTF-8 等输入编码、ECB/CBC、IV 来源和 PKCS5/PKCS7 实现。

### 04.2 离线验证配置结构

下面仅演示**已在目标代码证实**使用“十六进制摘要前 16 字符”的派生和 AES-ECB + PKCS7 时的复现。种子是演示值，密文仍需来自实际采集副本。

```python
import hashlib
import json
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

seed = 'example_config_seed'
key = hashlib.md5(seed.encode('utf-8')).hexdigest()[:16].encode('ascii')
ciphertext = Path('work/apk/assets/config.dat').read_bytes()
if len(ciphertext) % 16:
    raise ValueError('密文长度不满足已确认的分组条件')
plaintext = unpad(AES.new(key, AES.MODE_ECB).decrypt(ciphertext), 16)
obj = json.loads(plaintext.decode('utf-8'))
Path('work/config-decoded.json').write_bytes(plaintext)
print('top_level_keys=', sorted(obj))
```

**判读：** 成功解析 JSON、字段与程序读取逻辑一致，再以同样的模式、派生和填充重新加密，比较是否逐字节等于原密文。出现 `sponsors[].wallet` 等字段后，保留条目索引与完整对象上下文；地址归属和资金活动继续见[虚拟货币与资金流](/knowledge/fic-case-12/)。可读几段文字不足以证明所有参数正确，异常时回查编码、截取单位和填充。

## 05 WebView 与 JavaScript 桥

### 05.1 从加载分支找网页来源

在入口 `Activity.onCreate` 和后续逻辑中跟踪 `loadUrl`、网络判断、重定向与本地资源。`file:///android_asset/www/index.html` 对应 APK 内 `assets/www/index.html`；需要读该 HTML 的脚本引用，不能把它当作设备上普通绝对路径。

**示例判读：** 网络可用分支加载 `https://www.example.test`，其他分支加载本地首页。代码支持两种加载设计；实际加载过哪一页，还需 WebView 缓存、日志、网络记录或隔离仿真观察。主域名与上传 API 可以不同，应分别列出。

### 05.2 实战：枚举桥接对象与方法

1. 找到 `addJavascriptInterface(obj, "AppNative")`，记录对象类型、注入名称与调用位置。
2. 定位桥接类，列出所有可暴露的方法及返回类型，追踪通讯录、设备 ID、型号、IMEI、手机号、应用列表和位置等数据来源。
3. 检查 JavaScript 如何调用这些方法，返回值是否为 JSON，是否存库或交给上传函数。
4. 核对权限、SDK 与实际设备版本，再查看采集记录中是否保存对应数据。

```java
webView.addJavascriptInterface(new NativeBridge(), "AppNative");

@JavascriptInterface
public String getContactsList() {
    // 此处继续追踪联系人查询和 JSON 序列化代码
    return contactsJson;
}
```

对目标 API 17 及以上、运行于相应系统的应用，JavaScript 只可访问带 `@JavascriptInterface` 的 public 方法；更旧目标或运行系统有不同暴露行为，不能无条件概括为“仅注解方法可调用”。[WebView API 文档](https://developer.android.com/reference/android/webkit/WebView#addJavascriptInterface(java.lang.Object,%20java.lang.String))还说明对象会注入各 frame。方法数量应按实际桥接类计数，不预设固定数量；注解与方法存在仍不证明调用成功或取得完整联系人。

Native 备份端点、ARM64 常量和自定义解密链见[逆向工程](/knowledge/fic-case-07/)。

## 06 飞行日志与第三方应用文件

### 06.1 DJI Fly 的定位与解析条件

常见定位起点是 `/storage/emulated/0/Android/data/dji.go.v5/files/FlightRecord/*.txt`，也要查对应用户与应用内部 `files/`。扩展名 `.txt` 不代表纯文本；先固定日志、应用版本及目录时间，识别格式版本，再选择解析器。

```bash
find "$EVIDENCE_ROOT/storage/emulated" -path '*/dji.go.v5/*/FlightRecord/*' -type f -print
sha256sum ./evidence/flight-record.txt
xxd -l 64 ./evidence/flight-record.txt
```

部分版本结构可由“8 字节头字段、2 字节 detail 长度、1 字节版本”等起点解析，但偏移、字段和记录布局必须按该版本确认，不能将这一简图当作所有 DJI 日志的统一魔数。校验 detail 长度未越过文件、记录边界与版本匹配，再解释元数据。

可选工具包括 `dji-log-parser-js`、AirData、DJI Logbook 或厂商解析库。高版本遥测记录可能加密，解析需要相应 keychain/授权条件；[DJI 解析库说明](https://github.com/dji-sdk/FlightRecordParsingLib)列出版本与密钥要求。没有满足条件时，明确只解析到哪些未加密 detail 字段，不能以总览可读声称全部航迹已还原。

### 06.2 实战：比较两次飞行的关联

**材料：** 两份原始日志、解析器版本、JSON/表格导出和地图坐标规则。逐条保留机型、飞行器/相机/遥控器/电池 SN、起降时间、时长、距离、最大高度/速度、起降坐标、拍照数与录像时长等**实际可解析字段**。不是每种版本都完整保存或能解密这些项。

| 比较项 | 可能的观察 | 判读边界 |
| --- | --- | --- |
| 飞行器与遥控器 SN | 两日志一致 | 支持同一设备标识关系；复制日志或改写仍需排查 |
| 电池 SN | 相同或不同 | 辅助解释换电与连续活动，不决定飞行操作者 |
| 起飞坐标 | 相距数百米 | 核对坐标系、精度、有效状态，不等于手机或人员位置 |
| 起降时间与间隔 | 时间相近 | 核对日志时区、时钟与是否为同一会话 |
| 高度、距离和速度 | 低空短距离活动 | 先确认单位与基准；缺少帧时不能补出完整轨迹 |

地图反查行政区划时，记录坐标原值、WGS-84/GCJ-02 等坐标系、转换过程、地图服务和边界时间。接近行政界线或定位误差较大时，保留不确定范围，不由地图上一个点直接认定人员到达。

## 07 通信、截图与跨检材关联

### 07.1 常见载体的解释

聊天数据库可提供沟通对象、收款地址、转账约定和时间线；便签可提供行程或口令提示；浏览器历史和下载记录可关联 APK 或程序来源；截图可提供界面内容、金额和候选交易哈希。文件名可能是交易号或摘要样式，也可能由应用重命名，必须回到记录或交易验证。

**实战顺序：** 从聊天获取目标地址与约定 → 从截图提取时间、金额和候选 hash → 从配置或账本核对同一地址 → 在相关网络的交易记录中验证。保持消息 ID、发送方/接收方、截图路径和哈希、转账方向及时间基准，不以一张图片断定交易成功或账户归属。

### 07.2 输出可复核结果

每项结果保留设备/用户/包名与版本、路径、原始字段、解析参数、查询或解密过程、派生文件摘要、交叉材料和限制。静态 APK 结果与实际活动分别表述：前者说明程序具备的代码路径，后者需要业务数据、日志或通信记录支持。没有复跑对应附件时，不声称示例已在真实检材实测。

## 08 实战：版本、加固与动态调用的取舍

### 08.1 Manifest 版本与业务版本分别记录

**场景与材料：** 一份 APK、应用安装元数据及隔离复现环境；分析目标是核对包版本、运行时业务版本和动态生成字段。先固定 APK 摘要、包名、ABI、系统与工具版本。不要为了读取简单版本字段直接启动整个程序。

```bash
aapt2 dump badging ./evidence/app.apk
rg -n 'versionName|versionCode|currentTimeMillis|System\.loadLibrary|native ' ./work/jadx
```

`android:versionName` 是展示给用户的版本字符串，可为任意格式；`android:versionCode` 是安装更新使用的整数版本标识。由业务方法 `getVer()` 返回的字符串还可能来自配置、服务端、Native 或缓存，未必等于 Manifest 版本。若版本名称由资源引用给出，应读取实际解析后的资源值；离线 APK 与已安装的版本也需核对。

**示例判读：** Manifest 表示应用发布版本为 `2.4.0`，界面显示一个来自 Native 的接口版本 `api-v3`。两者都可记录，但含义不同，不能将接口版本替代包版本，也不能把安装记录里的旧版本套给新的 APK。展示值为说明字段关系的示例。

### 08.2 混淆、DEX 加密与 Native 虚拟化

| 观察到的结构 | 可做的下一步 | 不能直接得出的结论 |
| --- | --- | --- |
| 类名缩短、字符串仍可见 | 沿 Android API、网络库、资源 ID 追调用 | 类名短不独立证明加固 |
| 小型入口 DEX、动态加载、业务类缺失 | 检查加载链与运行时实际 DEX/类加载器 | 一次反编译失败不证明代码不存在 |
| Java 方法调用 `native`、SO 内虚拟解释器/调度 | 确定 JNI 入口和 Native 参数/返回值 | 普通 DEX 导出不会自动还原虚拟化逻辑 |
| qvmp 等保护线索 | 核对 SO、JNI 注册、解释器结构与实际版本 | 不凭单一字符串套用某个固定方法或调度编号 |

先静态列出可见入口、资源、DEX 和全部 ABI 的 SO，再决定需要运行时导出还是仅观察返回值。DEX 导出解决的是“运行后出现的代码”问题；Native 虚拟化逻辑即使 Java 层可见，也可能仍在 SO 中执行。保留原 APK 与派生 DEX 的独立摘要及采集时间，反编译后回到指令验证关键分支。

`lib` 或 `assets` 里的壳库可以识别加固名称，认出壳不等于已经脱壳。模拟器备份外层若是 `50 4B 03 04`，先按 ZIP 解开，再只读挂载里面的虚拟磁盘。用户安装的应用在对应 `/data/app` 的分区里，先排除预装包。勒索界面由无障碍服务盖在最上层时，在清单里找 `AccessibilityService`，再跟到创建悬浮窗和校验输入的类。

可用脱壳工具或平台辅助分析，但要核对支持的壳和版本、产物是否完整以及实际加载的代码是否相同。包含敏感数据时优先在本地隔离环境处理；未经真实材料运行验证，不声称脱壳产物等同于完整业务实现。

### 08.3 attach 与 spawn 按观察目标选择

**复现边界：** 以下动态操作仅在检材副本或专门的隔离复现设备上进行。启动、构造对象和调用业务方法可能写库、联网、改变时间或内存状态；记录触发动作，不将复现状态当作历史设备状态。

```bash
frida-ps -U
frida -U -p 1234 -l ./work/observe.js
frida -U -f com.example.app -l ./work/observe.js
```

PID `1234` 与包名 `com.example.app` 均为示例，先从实际进程列表确认；包名不总等于每个进程名，远程服务也可能运行在另一进程。正常启动并进入目标页面后 attach，适合观察已初始化对象；spawn 适合截获早期加载、密钥派生或初始化调用。加固或反调试可能影响其中一种方式，也可能两种都影响，**不能概括为所有加固程序必须 attach 或禁止 spawn**。

如果 spawn 崩溃而普通启动可正常进入页面，可先在稳定阶段 attach，并记录早期调用已错过；不能由此断言根本不存在早期调用。主机 Frida、设备端运行组件和 ABI 应匹配；先核对连接和目标 PID，再处理类未加载或桥接问题。[Frida CLI](https://frida.re/docs/frida-cli/)与当前工具帮助可核对加载方式。

## 09 实战：已有对象、重载与类加载器

### 09.1 主动调用现有实例

先用静态代码确认真实类名、方法名、参数与副作用。以下模板假定目标 Activity 已在正常启动后创建，`getVer()` 无参数且只返回状态字符串；**必须替换为目标程序实际类与方法，不原样对任意 APK 使用**。若方法依赖 UI 线程，安排到主线程，并保留对象至调用完成。

```javascript
Java.perform(function () {
  const activityClass = 'com.example.app.MainActivity';
  let matches = 0;
  Java.choose(activityClass, {
    onMatch: function (instance) {
      matches += 1;
      const saved = Java.retain(instance);
      Java.scheduleOnMainThread(function () {
        try {
          console.log('business_version=' + saved.getVer());
        } catch (e) {
          console.log('call_failed=' + e);
        } finally {
          saved.$dispose();
        }
      });
    },
    onComplete: function () {
      console.log('matching_instances=' + matches);
    }
  });
});
```

`matching_instances=0` 说明该次堆扫描未找到匹配实例；检查页面是否创建、类名与加载器，不能据此认定应用没有此方法。多个 Activity 实例的状态可能不同，分别保存调用上下文。对于工具类，只有确认构造函数和所需状态后才可用 `Java.use(...).$new()`；静态方法无需构造对象，构造成功也不证明初始化状态等同于原实例。

**结果边界：** 主动调用获取的是复现环境和该对象当时的返回值。方法若有设备绑定、缓存、网络或时间依赖，结果可能变化；历史值仍需从保存的数据库、日志或抓包核对。Frida 17 起独立构建的 agent 需显式引入 Java bridge；通过 Frida REPL 加载的脚本按当前工具集提供桥接，不把 `Java` 未定义误判成壳加固。[Java API](https://frida.re/docs/javascript-api/#java)列出对象与桥接行为。

### 09.2 按真实重载记录输入和输出

以下 `PathBuilder.build(String)` 是示例业务方法。先确认实际重载，再保存方法包装器并使用它调用原实现；避免在 hook 内反复调用自己，也不修改返回结果。

```javascript
Java.perform(function () {
  const Builder = Java.use('com.example.app.PathBuilder');
  const original = Builder.build.overload('java.lang.String');
  original.implementation = function (input) {
    const result = original.call(this, input);
    console.log(JSON.stringify({
      stage: 'build',
      input: input === null ? null : input.toString(),
      output: result === null ? null : result.toString()
    }));
    return result;
  };
});
```

`JSON.stringify` 显示 `\n` 等转义，便于发现不可见字符；继续核对返回字符串长度与实际字节编码。Native 保护不一定妨碍观察 Java 调用边界，但若调用完全发生在 Native 内部，Java hook 也可能没有命中。此时回查 JNI 注册、导出符号和实际调用关系，不能猜测一个固定 `interface11` 或数字参数就是所有版本的入口。

若确实需要核对字符串比较，可观察目标校验方法的参数/返回值；全局 hook `String.equals` 会产生大量无关调用和性能影响。仅在定位明确且加入调用栈/目标值过滤后作为补充，不用它替代网络请求构造点的证据。

### 09.3 类已存在却找不到时检查 loader

```javascript
Java.perform(function () {
  const className = 'com.example.app.PathBuilder';
  Java.enumerateClassLoaders({
    onMatch: function (loader) {
      try {
        const factory = Java.ClassFactory.get(loader);
        const Target = factory.use(className);
        console.log('loader=' + loader.toString());
        console.log('class=' + Target.$className);
      } catch (e) {
        // 该 loader 不包含目标类，继续检查其余 loader
      }
    },
    onComplete: function () { console.log('loader_scan_complete'); }
  });
});
```

记录匹配 loader 后，使用该 factory 的类包装器安装目标 hook；如果同名类出现在多个 loader，结合调用栈和目标实例确定实际使用的一份。动态 DEX 可能在进入某页面后才加载，过早扫描的缺失不代表永远不存在。

## 10 实战：动态 URL、时间与本机服务

### 10.1 还原字段来源而非手工拼一个地址

**场景：** 应用把业务路径经多层编码/加密后交给本机 HTTP 服务，查询参数来自 APK 摘要、业务版本与时间字段。分析材料为 APK、静态数据流、动态日志与复现设备上的请求记录。

1. 定位 `multiLayerEncrypt` 等实际处理方法与调用点，记录输入、算法/编码链、返回字符串和所在 loader。
2. 追踪 `apkHash` 的算法、计算对象与生命周期：可能是 APK 文件摘要，也可能是签名、代码或其他内容的摘要，不能按名称推断。
3. 区分 Manifest 版本、`getVer()` 业务值，以及 `ts` 在启动、按钮点击或每次请求时更新的条件。
4. 在真正交给网络库或服务处理器的边界记录完整 URL；将主动调用的结果与真实触发的结果比较，而不是假定相同。

### 10.2 系统毫秒、秒级参数与固定资源

`System.currentTimeMillis()` 返回从 Unix epoch 起算的系统毫秒值，受系统时钟调整影响，不能用作稳定耗时钟。包装类即使名为 `TimeFetcher` 或混淆为 `a()`，也需沿其内部调用确认；“包装方法名”和“System API 名”是不同层级。

```java
long nowMs = System.currentTimeMillis();
long nowSeconds = nowMs / 1000L;
```

约 13 位的值常见为毫秒、约 10 位常见为秒，这只是量级线索；必须核对代码中的除法、类型和网络序列化。`assets` 中保存的固定数字、缓存的启动时间和设备当前时间不同。复现时同时记录设备 UTC 时间、原值与换算结果；不要把当前运行返回值写成历史设备活动时间。

### 10.3 换行、编码层与 localhost 的边界

**示例：** 目标生成的路径段实际字节为 `status\n`。若代码把该字节作为路径数据，经 URI 编码后可出现 `status%0A`；若某网络库剔除或拒绝换行，则线上的请求不同。必须分别保存“生成字符串”和“实际 Request-URI”。不能统一删除不可见字符，也不能给所有 URL 追加 `%0A`。

```python
from urllib.parse import quote, urlencode

path_segment = 'status\n'  # 仅为演示；替换为实际生成值
params = {'hash': 'example-digest', 'ver': 'api-v3', 'ts': 1700000000}
url = 'http://127.0.0.1:8080/' + quote(path_segment, safe='')
url += '?' + urlencode(params)
print(repr(path_segment))
print(url)
```

此处只编码一个路径段；若实际函数返回完整路径或已经编码的数据，应按其层级处理，避免二次编码把 `%0A` 变成 `%250A`。查询参数中的 `+`、`/`、`=` 与 Base64 变体也需核对，不按显示效果擅自替换。

`localhost/127.0.0.1` 指向执行请求那一侧的网络命名空间。手机上的本机服务不会因分析机访问自身 localhost 而出现。若处理器如 `channelRead0` 校验对端为回环地址，需要结合实际绑定地址、端口与校验分支；不是所有本机服务都使用这种限制。

在隔离复现设备上确认安装了可用 `curl`，再以已确认的请求验证。Android 不保证自带 curl；没有时使用现有受控客户端或观察应用自身请求，不能在报告中假设命令已执行。

```bash
adb shell 'curl --path-as-is "http://127.0.0.1:8080/status%0A?hash=example-digest&ver=api-v3&ts=1700000000"'
```

URL、端口和参数均为演示值；实际验证需匹配当前复现状态。分别保存请求字节、返回状态与响应内容；404 可能来自路径、动态参数、请求时间或服务未启动，不足以单独证明“缺少换行”。

## 11 实战：Java hashCode 校验的有界复现

### 11.1 精确复现 32 位有符号值

`String.hashCode()` 是 31 倍滚动的整数哈希，不是密码学摘要。Java 的 `int` 以 32 位运算溢出；对一般 Unicode 字符串，需要按 **UTF-16 code unit** 运算，而非 Python 的 Unicode code point。8 位纯数字场景中二者值相同，但通用复现不能漏掉这一差别。[Java String API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/String.html#hashCode())定义其算术规则。

### 11.2 保留前导零并输出全部候选

下面保存为 `hashcode_candidates.py`。仅在代码已确认校验域为**恰好八个 ASCII 数字**，且目标 hash 来源明确时使用；用范围参数限定当前分析，不把任意格式都当作八位授权码。

```python
import argparse


def java_string_hash(text):
    data = text.encode('utf-16-be', errors='surrogatepass')
    h = 0
    for pos in range(0, len(data), 2):
        unit = int.from_bytes(data[pos:pos + 2], 'big')
        h = (31 * h + unit) & 0xffffffff
    return h - 0x100000000 if h >= 0x80000000 else h


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=int, required=True)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--stop', type=int, required=True,
                        help='不包含 stop；完整八位数字域为 100000000')
    args = parser.parse_args()
    if not -(2**31) <= args.target < 2**31:
        parser.error('target 必须是 Java 有符号 int')
    if not 0 <= args.start <= args.stop <= 100000000:
        parser.error('范围必须位于八位数字域内')
    checked = matches = 0
    for value in range(args.start, args.stop):
        candidate = f'{value:08d}'
        checked += 1
        if java_string_hash(candidate) == args.target:
            matches += 1
            print(candidate)
    print(f'checked={checked} candidates={matches}')


if __name__ == '__main__':
    main()
```

```bash
python3 hashcode_candidates.py --target 0 --start 0 --stop 10000
```

命令里的 `0` 仅展示参数格式，应替换为实际校验目标，范围依据已取得的约束逐段选择。完整八位数字域为 `00000000` 至 `99999999`，一共一亿个候选；Python 逐个实现可能较慢，应先估算范围和耗时，不承诺任何目标都会命中。

### 11.3 命中不等于唯一原值

哈希相同可能出现多个不同字符串；脚本不在首个匹配处停止。每个候选还需检查实际长度、允许字符、归一化/trim、附加校验、设备绑定和调用路径。小范围无结果，只能说明该范围内没有匹配；完整受限域无结果也可能说明格式、目标、字符处理或算法识别有误。

**交叉核验：** 对候选在 Java/隔离应用中重新计算 `hashCode()`，核对有符号十进制值；再在复制的校验流程中验证全部分支。若只通过 hashCode 比较，结果适合表述为“满足该整数校验的候选”，不宣称恢复唯一历史授权码。固定长度的格式校验和前导零保留必须与整数哈希同时验证。
