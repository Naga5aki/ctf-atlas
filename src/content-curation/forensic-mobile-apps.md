## 01 建立应用身份与首轮数据库检查

手机应用取证先识别包名或 Bundle ID、安装版本、签名、数据容器（含多用户/分身空间）和当前登录账号，再区分设备实时文件、本地备份与云端导出。仅凭桌面显示名称查找容易混淆改名或双开应用。

| 数据类型 | 常见落点 | 首轮核对重点 |
| --- | --- | --- |
| 消息与联系人 | SQLite/SQLCipher 主库、WAL、附件目录、索引文件 | 消息方向、登录账号、发送/已读状态、删除标记 |
| 媒体与文档 | 缓存、缩略图、Download 及应用私有目录 | 原件与缩略图的 SHA-256 哈希及生成时间 |
| 位置与轨迹 | 坐标数据库、图片 EXIF、地图缓存与穿戴同步库 | 坐标系（WGS-84 / GCJ-02）、定位精度、来源（GPS/Wi-Fi/手填） |
| 登录与同步 | shared_prefs / Plist、MMKV、令牌元数据、服务日志 | 账号切换、设备绑定关系和云同步延迟 |

完整复制应用容器后，将数据库主文件、同目录 -wal/-shm 和附件放在工作目录，先计算哈希并检查表结构，切勿在原件上执行恢复或清理：

`ash
sha256sum ./work/app.db
file ./work/app.db
sqlite3 -readonly ./work/app.db 'PRAGMA integrity_check;'
sqlite3 -readonly ./work/app.db '.tables'
sqlite3 -readonly ./work/app.db '.schema'
`

若无 -wal 文件，不要人为创建空文件；若 integrity_check 报错，优先排查复制截断或 SQLCipher 加密。先取几条可与界面或通知互证的样本，明确发送时间、服务器接收时间与本地入库时间的差异，按 数据库路径 / 表 / 主键 / 账号ID / 原始时间 / 转换时间 / 附件哈希 记录，避免将预加载缓存或跨设备云同步记录直接写成持机人当场操作。

## 02 野火 IM 的数据库密钥链

先确认版本与包名，保全应用沙箱、`shared_prefs/config.xml`、token/ID 和消息数据库。已知实现的分析链为 `ChatManager.connect` → `IRemoteClient` 调用 → `initProto/setAuthInfo` → native 层数据库打开；类名相似不保证加密完全一致。

在部分旧版实现中，配置 token 先经 Base64 解码，再按程序中确认的 AES 参数处理；明文以 `|` 分隔，末项被用于 SQLCipher。曾见的实现常量为 `001122334455667778797a7b7c7d7e7f`，并将相同字节用于 IV。只有静态调用链和实际样本确认完全匹配时才采用该分支；记录常量来自字符串还是十六进制解码，核对长度、模式、填充与明文格式，再按实际 SQLCipher 版本验证。不要把常量当作任意版本数据库的通用口令。

SQLCipher 解密成功要能读取 schema、账号和已知记录，而非仅得到可打印文本。静态分析不充分时，在隔离实验副本中观察数据库打开和密钥传入；Frida 等动态分析要注意真实进程、native 调用与多进程初始化，不能只挂到界面进程就判定“无密钥”。保留调用链、参数和工具版本，不运行检材中的未知 APK。

## 03 运动健康与可穿戴设备

| 应用 | 常见 Android 包名线索 | 先查内容 |
| --- | --- | --- |
| Keep | `com.gotokeep.keep` | 账号、运动、轨迹、课程、截图 |
| 华为运动健康 | `com.huawei.health` | 手机/手表绑定、运动、健康与同步 |
| Zepp | `com.huami.watch.hmwatchmanager` | Amazfit 设备、运动与绑定 |
| Zepp Life | `com.xiaomi.hm.health` | 手环、步数、睡眠、运动 |
| Mi Fitness | `com.xiaomi.wearable` | 小米设备、运动与同步 |

包名随地区、版本或产品变化，先以安装记录验证。记录账号 ID、设备 ID/MAC/序列号、绑定/同步时间、workout/track ID、起止时间、duration、distance、平均速度/配速、心率、步频和数据类型；字段存在时保留实际单位与来源标识。

```bash
rg -n 'com\.gotokeep\.keep|com\.huawei\.health|com\.huami\.watch\.hmwatchmanager|com\.xiaomi\.hm\.health|com\.xiaomi\.wearable' ./work/data/system/
```

运动开始、结束、上传、同步与截图保存是不同时间。轨迹需核对坐标系、点序、间隔、定位精度与跳点；没有心率或 GPS 也可能是设备能力、室内运动、手动录入或采集缺失，不能单独认定伪造。手机缓存与手表数据可能不完整同步，设备绑定也不等于数据由该设备产生。

## 04 删除、缓存与私密空间

按当前数据库 → WAL/空闲页 → 附件/缩略图 → 系统最近删除/通知 → 备份/同步痕迹检查。每个候选保留路径、页/记录位置、账号、ID、时间、删除/恢复状态和验证方法。WAL 不是必然完整的历史记录，缩略图也不能等同完整图片。

隐藏或私密空间应先确认用户/空间标识、加密状态和采集覆盖；在普通目录没有找到，不能断言数据已删除。云端回收站与备份仅按实际取得的材料分析，本地令牌或账号配置不能自动证明云端内容。

## 05 鸿蒙与跨设备生态

先区分整机镜像、逻辑备份、文件系统、单应用导出、HAP 包、华为手机助手备份和穿戴关联数据。HAP 主要用于程序结构分析，不等同用户沙箱。不同系统版本的兼容机制和数据落点不同，不能把所有鸿蒙设备直接套成 Android 路径。

保全型号、系统版本、设备名、序列号、IMEI、手机号、华为账号、登录/同步状态和绑定设备。围绕浏览器、图库、云空间、智慧生活、运动健康及手机/手表/平板/电脑建立关联。记录属于哪个设备、哪个账户、何时同步；同一内容出现在多设备中不意味着在每台设备上都发生了相同操作。

## 06 实战：把消息、附件与运动轨迹分别核验

**场景与材料：** 一份应用沙箱与共享目录包含消息数据库、图片缓存和运动轨迹。需要判断一条消息是否带有某张图片，以及轨迹属于哪个账户和关联设备。先按应用身份和数据类型分开保全，再用稳定 ID 关联。

### 06.1 消息与附件链

1. 从 schema 和样本值确认消息主键、账户、方向、状态与附件 ID。恢复记录保留页/偏移，不与当前记录混合统计。
2. 沿附件 ID 查路径、大小与类型，再对实际文件计算哈希；文件名一致和缩略图相似都不足以证明完整内容相同。
3. 若消息来自同步，核对设备和同步字段、备份时间及另一端记录。数据库的已读状态需按实现解释，不能自动认定本机持有人阅读。

### 06.2 轨迹与设备链

以 account ID、workout/track ID 与 device ID 连接记录，保存点序、起止时间、坐标系、精度、单位和来源标识。将图片保存时间、运动开始时间、上传时间与设备同步时间分别列出。绑定某手表、缓存出现轨迹和手表实际记录该次运动是三种证据强度。

**示例判读：** 缓存存在一条轨迹但无 GPS 精度、设备来源或同期健康数据。可以描述应用保存了这条轨迹；不能据此确定使用者走过整条路线，也不能仅凭缺心率认定伪造。继续查看对应设备记录、同步日志与照片等独立证据，并保存采集缺口。

## 07 实战：把账户、安装记录与聊天附件串起来

### 07.1 微信和 NTQQ：先确认身份，再派生密钥

**材料：** 同一用户或虚拟实例的 APK、账户配置、数据库及 WAL、附件目录。保留应用版本和采集状态；下列标识只作为定位入口，具体字段与派生算法应按目标版本确认。

| 分析目标 | 读取路线 | 验证条件 |
| --- | --- | --- |
| 微信账户与绑定手机号 | 账户配置中的 uin/wxid → 对应库 → 账户或联系人记录 | 手机号可能变化；保留账户、记录时间和数据容器，不能把任意联系人电话当作绑定号 |
| 微信数据库读取 | 核对 APK 中的数据库初始化与密钥派生 → 设备/账户输入 → 对应 SQLCipher 参数 | 常见旧版本派生法不适用于所有版本；有 uin 不代表已具备全部输入 |
| NTQQ 好友备注与身份 | 核对 uid/uin 映射 → 对应账户的库 → 解密/解析字段 → 联系人或备注记录 | 显示名、好友备注、真实姓名分列；protobuf 字段语义按代码和样本确定 |
| 应用首装时间 | 包管理记录、应用市场安装日志和版本历史相互核对 | 市场下载、首次安装、升级、卸载重装与备份恢复不是同一事件 |

**操作顺序：** 确认用户空间和包名 → 复制完整容器 → 保存库版本与密钥调用链 → 按兼容参数读取 → 用账户表、联系人表和附件关联验证。若解析器只给显示名，应写“联系人显示名/备注”，不能自动提升为实名。

一批 Android 微信把 IMEI 放在 `files/KeyInfo.bin`，用字符串 `_wEcHAT_` 解密后得到这份缓存里的 IMEI；UIN 在 `files/mmkv/system_config_prefs` 及其校验文件里，保留有符号整数的写法。`MicroMsg` 下 32 位十六进制目录名若等于 `md5("mm" + UIN)`，这个 UIN 对应该目录。数据库密钥是 `md5(IMEI 的字节接上 UIN 的字节)` 的小写十六进制前 7 位。页大小、KDF 次数和 HMAC 以该版本的开库代码为准。先设置兼容参数，再设置密钥，能读出账号表并命中已知账号才算解开。不要把某一台设备上解出的 IMEI 写成所有版本的默认值。

默往这一实现从 `shared_prefs/im.xml` 读 UID，密钥是 `md5(UID)` 的小写十六进制前 6 位，先执行 `PRAGMA cipher_compatibility = 3` 再设密钥。消息表可见 `im_message`，`delStatus = 2` 表示已删除，空值表示未删。高德登录库常见于 `com.autonavi.minimap/files/girf_sync.db`，头像用已登录账号在同一 `files` 目录里的那张，排除未登录默认头像。米家一类设备的局域网地址在该应用数据目录的 MMKV 里，字符串可以直接搜。包名都以安装记录为准。

对应用市场记录，至少列出 `包名、版本、时间字段、事件类型、时区、记录位置`。例如市场日志显示一次下载，包管理记录显示随后升级，只能分别报告两个事件；缺少旧版本记录时不能从当前文件 mtime 推定首次安装。

### 07.2 SQLCipher 聊天库：沿代码找到真正的开库参数

**场景：** `databases/chat.db` 不是普通 SQLite，匹配 APK 中存在 `Application.onCreate()` 或数据库助手的开库代码。目标是读取消息并定位它引用的受保护文档。

1. 用 JADX 从 `getWritableDatabase`、`openDatabase`、数据库文件名或 SQLCipher 引用定位调用链，跟踪密码是常量、派生值还是设备绑定密钥。类名和方法名按 APK 实际结果记录。
2. 记录输入字节、编码、SQLCipher 主版本、页大小、KDF 和兼容参数；不要因一串常量可读就断定它是最终密码。
3. 在库的完整工作快照上用兼容 SQLCipher 工具开库，先读 schema 和 `sqlite_master`，再执行完整性检查、确认应用表和代表记录。错误参数可以表现为“file is not a database”，并不必然表示库损坏。
4. 按消息主键、发送方/接收方、附件路径与摘要建立关联，保留账号和时间。不要只导出聊天正文而丢失附件关系。
5. 查看消息是否提供文档口令：有分隔符的 `.`、`-` 序列可以是摩斯编码候选，先确定字母与单词边界，再解码。混合大小写、数字与末尾换行都可能影响口令。
6. 用候选口令打开附件副本，核对结构、内容和哈希，回到消息验证其确实引用该对象。解码出可读字符串还不足以证明口令正确。

**示例判读：** 一条消息引用 `report.xlsx`，同会话的编码文本解出候选口令，解密后工作簿结构可解析且表头符合消息语境。可记录“该消息提供了此附件的可用口令”，仍需独立判断发送者身份。SQLCipher/WAL 的完整参数和快照边界见[SQLite 与 WAL](/knowledge/forensic-sqlite/)。

## 08 实战：Hawk / Conceal 偏好设置的认证解密

### 08.1 材料、字段与调用链

**场景：** 应用数据内发现 `shared_prefs/Hawk2.xml` 和 `shared_prefs/crypto.KEY_256.xml`，需要解释启动 PIN、附件口令或锁定状态。应一并保存匹配 APK、两份完整 XML、版本与应用容器；只复制某个 Base64 字符串会丢失序列化和认证上下文。

| 材料 | 可能提供什么 | 不能直接假定 |
| --- | --- | --- |
| `Hawk2.xml` | 如 `MXT_PWD`、`R_PWD`、`LOCK` 的序列化记录 | 键名一定表示密码；`LOCK` 也可能是布尔值或状态 |
| `crypto.KEY_256.xml` | 部分 KeyChain 实现保存的 `cipher_key` | 所有版本均保存可导出的明文密钥 |
| APK 的 HawkSerializer | 类型信息、分隔符和密文字段位置 | 整个 XML value 都是 Base64 密文 |
| ConcealEncryption/KeyChain | 密钥来源、封装版本、nonce、认证标签和 Entity | 从头截 12 字节、从尾截 16 字节就适合所有数据 |

某些 Hawk 实现把序列化类型信息放在 `@` 之前，只把其后的内容交给加密层；Conceal 调用还可能以偏好键名创建 Entity。必须沿匹配版本的 `serialize/deserialize`、`encrypt/decrypt` 和 KeyChain 确认字节布局及认证附加数据（AAD），不能凭文件名套固定偏移。[HawkSerializer](https://github.com/orhanobut/hawk/blob/master/hawk/src/main/java/com/orhanobut/hawk/HawkSerializer.java)和[ConcealEncryption](https://github.com/orhanobut/hawk/blob/master/hawk/src/main/java/com/orhanobut/hawk/ConcealEncryption.java)可用于核对对应实现。

### 08.2 正确提取与记录参数

```bash
find ./work/app/shared_prefs -maxdepth 1 -type f
rg -n 'MXT_PWD|R_PWD|LOCK|cipher_key' ./work/app/shared_prefs
```

1. 用 XML 解析器读取完整值，处理 XML 转义，不用搜索结果中的截断文字作密文。
2. 按已确认的序列化规则取出加密字段，严格 Base64 解码并保留封装头。逐字节标注版本、nonce、密文、tag 的起点和长度。
3. 从目标 KeyChain 核对密钥是否为 Base64、长度和密钥类型；AES-256 对应 32 字节，32 个文本字符不必然是 32 字节密钥。
4. 按加密库实现构造完整 AAD。Entity 的编码、封装认证头和键名都可能参与，不能把键名字符串直接当成全部 AAD。
5. 建立一份仅用于工作区的规范化 JSON，明确记录 Base64 字段 `key、nonce、ciphertext、tag、aad` 及其提取依据。下段脚本接收的是这份已验证布局的中间记录，不直接解析任意 Hawk XML。

### 08.3 认证通过后再保存明文

把下面示例保存为 `gcm_record.py`；运行环境需有 PyCryptodome。它要求显式提供 AAD，先验证 GCM 标签，再写入新文件。

```python
import base64
import hashlib
import json
import sys
from pathlib import Path
from Crypto.Cipher import AES

def decrypt_record(record):
    fields = {
        name: base64.b64decode(record[name], validate=True)
        for name in ('key', 'nonce', 'ciphertext', 'tag', 'aad')
    }
    if len(fields['key']) != 32:
        raise ValueError('已确认的 AES-256 密钥必须为 32 字节')
    if not fields['nonce'] or len(fields['tag']) not in range(4, 17):
        raise ValueError('nonce 或 tag 长度不符合解析条件')
    cipher = AES.new(fields['key'], AES.MODE_GCM,
                     nonce=fields['nonce'], mac_len=len(fields['tag']))
    cipher.update(fields['aad'])
    return cipher.decrypt_and_verify(fields['ciphertext'], fields['tag'])

def main():
    input_path, output_path = map(Path, sys.argv[1:])
    record = json.loads(input_path.read_text(encoding='utf-8'))
    plaintext = decrypt_record(record)
    with output_path.open('xb') as stream:
        stream.write(plaintext)
    print('bytes=', len(plaintext), 'sha256=', hashlib.sha256(plaintext).hexdigest())

if __name__ == '__main__':
    main()
```

```bash
python3 gcm_record.py ./work/gcm-record.json ./work/preference-plain.bin
```

**预期行为：** 正确记录通过认证并生成明文；密钥、AAD、nonce、密文或 tag 不匹配会报错，不能输出未经认证的“看起来可读”结果。文件已存在会停止，避免覆盖既有产物。空 AAD 只适用于调用链明确不提供 AAD 的情况。[PyCryptodome GCM 文档](https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html#gcm-mode)说明认证解密接口。

### 08.4 明文语义与应用恢复验证

认证通过只证明参数与该记录对应。继续按 Hawk 类型信息解析字符串、JSON、布尔值或数字；若 PIN 是字符串，保留前导零，不能先转整数。区分“启动口令”“附件口令”“锁定状态”，将解密字段和相应操作匹配。

附件可以位于应用自定义的 `/sdcard/Android/<包名>/files/zip/`，也可以在标准共享存储目录；先核对真实访问代码和附件引用。若数据库存在实际的 `Password` 字段或口令表，先按 schema、应用读写代码与代表记录确认语义，再以附件 ID、路径或摘要关联对应口令；不同附件可以有不同口令，不把同库的任意密码互相套用。`.mxt` 等扩展名不能替代格式识别；候选口令应以成功解析内部对象、完整性检查和消息关联验证。

如需恢复应用，仅在隔离实验设备中使用副本，核对版本、签名、目录权限、SELinux 与 Keystore 依赖，并在启动前后记录变化。设备绑定密钥可能无法随 XML 迁移。成功打开界面是补充验证，仿真写入的状态不能冒充历史数据。

## 09 实战：WhatsApp 记录判读与跨设备关联入口

### 09.1 先固定手机来源和可读范围

**场景与材料：** 已取得手机中 WhatsApp 的应用数据、备份或导出，需解释一段聊天及其附件。先用设备安装/备份清单确定实际应用、版本、用户空间和数据容器，再记录手机身份、采集时刻、登录账户、库/日志/WAL与附件覆盖。不同版本、普通/商业应用、工作资料空间和恢复后的数据应分别归属，不能凭应用显示名合并。

完整保全原始对象及哈希，数据库、联系人、附件索引和实际文件一并核对。逻辑导出可能没有原库的稳定 ID、删除信息或完整附件；界面截图可能只见显示名和渲染时间，要按取得方式写明范围。若材料加密、缺密钥、缺完整备份或解析器不支持，保留其格式与报错并记录缺口；本流程不假定任何通用密钥、固定解密路径或跨版本数据库参数。

### 09.2 从账户、会话和消息字段解释记录

在已可读的工作副本上先看 schema、应用版本及解析器的字段说明，选有独立来源可确认的样本验证。表名、方向值和状态枚举以当前材料为准，不照搬其他版本；读取原则见[SQLite 与 WAL](/knowledge/forensic-sqlite/)。

| 对象 | 至少保存 | 判读边界 |
| --- | --- | --- |
| 本机账户与联系人 | 登录账户稳定 ID、实际绑定字段、联系人 ID、显示名/备注、记录时段 | 联系人电话号码不自动等于本机绑定号码；可修改名称不能替代身份 |
| 会话与消息 | 会话 ID、消息原生 ID/主键、发送方/接收方、群聊实际发送者、方向、类型 | 群会话名称不等于发送者；方向须说明相对哪个登录账户 |
| 状态与内容 | 正文完整上下文、发送/投递/已读状态、引用/转发/编辑标记、删除/恢复标记 | “待发送”“已发送”“已投递”“已读”分开；已读标志不自动证明手机持有人阅读 |
| 时间 | 原始字段、单位、字段含义、时区/偏移、换算值与依据 | 发送、服务器接收、本地入库、备份恢复与导出时间不能混用 |
| 附件 | 消息引用、附件 ID、实际路径、完整文件大小、格式与 SHA-256 | 缓存/缩略图、截图和原件分列；缺实体只能保留引用候选 |

已发送状态仍要按实际实现解释；文本包含“完成”“已上传”只能作为该条消息的内容，不代替操作日志。引用或转发的文字可能来自另一条消息或另一位发送者，保留原记录关系和会话上下文。数据库中的一条当前记录与 WAL/空闲页中的恢复候选分开报告，恢复出的可读文字需确认结构、所属账户和记录边界，不能仅凭词语命中当作完整消息。

### 09.3 先形成手机内部证据链，再连接计算机和服务器

按 `手机/用户空间 → WhatsApp 登录账户 → 会话与消息ID → 发送者/方向/状态 → 附件引用 → 实体哈希` 建立记录。一份附件在共享目录中存在但缺消息引用，只能说明手机留存该文件；消息引用了不存在的附件，也不能说明已取得附件内容。对聊天中出现的网址、账号或交易说明保留文本和上下文，继续用独立材料验证，不从文本直接推定实际访问、交易或自然人身份。

**构造判读：** 手机留存一条发送方向的消息，附件索引引用 `document.bin`；实体文件的完整 SHA-256 与服务器某个文件一致。可报告“此消息引用的附件与服务器所取得文件字节相同”。仅凭这个关系无法确认是哪一台设备上传、哪个网站账户操作，或某位自然人实施了消息中的自述；继续核对网站请求、认证会话及数据库业务行。若只有同名文件或缩略图相似，关系应保持为候选。

计算机中取得的 **Signal Desktop** 是桌面用户应用证据，应在对应计算机、系统用户/Profile、应用版本与账户下单独保全；不能把其消息时间、桌面附件或链接设备记录移填为手机 WhatsApp 的字段。不同应用的账户 ID、消息 ID 不共用命名空间，相同昵称和相近时间不能直接连接。完整的手机 WhatsApp—计算机 Signal Desktop—服务器网站/数据库流程、模拟正反例与关联表见[方法索引第 08 节](/knowledge/forensic-method-index/)，计算机归属与账户材料见[Windows 痕迹](/knowledge/forensic-windows-artifacts/)。时间字段统一见[时间证据](/knowledge/forensic-time-evidence/)。
