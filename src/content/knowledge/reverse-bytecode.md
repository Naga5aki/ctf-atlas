---
title: JAR、APK 与 WASM 的分层阅读
summary: 从 JAR、APK 与 WASM 的入口追到字节码、资源和原生库，结合 Android 数据落点、受控动态观察与离线复现验证行为。
module: Reverse
topic: 程序结构
tags: [程序校验]
status: 已整理
sourceIds: ["local-app-reverse-5eac65ccf155"]
challengeIds: [478f25269338, 1c45f7d38b2e, e39fd964440f, 4b5a4b9b0555]
updated: 2026-10-02
---

## 01 先看谁调用谁

这三类文件都可能是“外层交互 + 内层校验”。JAR 先看入口类和静态初始化；APK 先看 Manifest 的组件、按钮回调以及 JNI 调用；WASM 先看导入/导出函数和宿主 JavaScript。只分析最显眼的 `check()`，容易漏掉进入它之前的编码、重排或解密。

## 02 JAR 与 Java 字节码

```bash
unzip -l sample.jar | head -80
unzip -p sample.jar META-INF/MANIFEST.MF
javap -classpath sample.jar -c -p com.example.Main
```

把最后一行的类名换成列表中真实存在的类。`javap -c` 查看字节码，适合核对反编译器还原不准的分支、类型转换和数组访问。留意运行时版本、资源条目、依赖包以及静态字段初始化；加密常量不一定直接出现在主方法。

`-p` 包括私有成员，`-classpath` 指向待分析的类路径；工具参数见 [OpenJDK javap 文档](https://github.com/openjdk/jdk/blob/master/src/jdk.jdeps/share/man/javap.md)。

## 03 APK 与 Android 入口

### 3.1 先区分 APK、备份与运行环境

APK 提供某个版本的代码和资源；手机镜像、应用备份提供采集时能够取得的配置、数据库与缓存。两者需要用**包名、版本、签名、用户空间和采集时间**关联，不能拿任意版本 APK 解释旧数据库。模拟器备份、虚拟磁盘、厂商备份、原始镜像和 E01 的封装不同，先确定容器格式、加密和提取范围，再分析其中的 Android 文件系统；备份不必然含私有目录、WAL 或全部 APK 分包。

第一轮先离线检查工作副本，不以安装应用作为默认起点。以下 `sample.apk` 已是工作副本，输出目录必须是新的分析目录：

```bash
sha256sum sample.apk
file sample.apk
unzip -l sample.apk | head -80
apksigner verify --verbose --print-certs sample.apk
jadx -d jadx-out sample.apk
apktool d sample.apk -o apktool-out
```

保留完整文件列表、解码日志和工具版本；`head` 仅用于快速预览。JADX 侧重 Java/Kotlin 近似源码，Apktool 可解码 Manifest、资源并生成 smali，两者互相核对。反编译报错、类型转换、异常分支和关键算术应回看 DEX/smali 或 native 汇编。签名验证失败需要检查原件状态、文件截断、结构修复和工具兼容性，不能直接归因为篡改；通过也不能证明应用可信或签名对应某个自然人。参数见 [JADX](https://github.com/skylot/jadx#usage)、[Apktool](https://apktool.org/docs/cli-parameters) 与 [apksigner](https://developer.android.com/tools/apksigner) 官方文档。

### 3.2 APK 结构怎样对应程序行为

| 位置 | 先查内容 | 如何追到使用处 |
|---|---|---|
| `AndroidManifest.xml` | 包名、组件、权限、SDK 要求、进程、启动入口 | 解析后的 Manifest → 对应类；APK 内常为二进制 XML |
| `classes.dex`、`classes2.dex` 等 | 类、方法、字符串、分支与调用 | 搜索全部 DEX；漏掉分包或多 DEX 会漏代码 |
| `assets/` | 任意原始资源、网页、脚本、配置、加密数据或动态载荷 | `getAssets().open("文件名")`、WebView 加载、解密与类加载路径 |
| `res/` | 布局、图片、语言与界面资源 | `setContentView`、资源 ID、控件事件和资源引用 |
| `resources.arsc` | 编译后的资源表 | 把 `R.string`、`R.layout` 等 ID 还原到资源内容 |
| `lib/<abi>/*.so` | 对应 CPU ABI 的原生库，常见为 ELF | `System.loadLibrary`、`System.load`、native 方法与 JNI 注册 |
| `META-INF/` 等签名相关结构 | JAR/v1 签名条目及元数据 | 同时用签名工具核对；v2/v3 等签名不能仅靠此目录判断 |

这是一张常见结构表，不能用“必须恰好七项”判断完整性。`assets` 不等于第三方接口目录，`.so` 可以来自 C/C++ 等原生代码或保护组件，单独出现不能证明加固。资源表名称是 `resources.arsc`；解码后的 `res/values/strings.xml` 是工具还原结果，不保证原 APK 中存在同名明文文件。[AssetManager 的 `open` 接口](https://developer.android.com/reference/android/content/res/AssetManager#open(java.lang.String)) 返回资源流，`getAssets()` 本身不接收文件名。

### 3.3 ZIP 结构异常与“伪加密”

APK 基于 ZIP 容器。遇到解压器要求密码时，先核对目录、条目头、压缩方式、加密标志、数据长度与 CRC；真实加密、结构损坏和工具兼容性也可能产生相似报错。

| 结构 | 文件中的字节签名 | 判读重点 |
|---|---|---|
| 本地文件头 | `50 4B 03 04` | 这是头部，文件数据位于文件名与扩展字段之后 |
| 中央目录文件头 | `50 4B 01 02` | 与本地头关联，检查条目偏移和长度 |
| 中央目录结束记录 | `50 4B 05 06` | 检查中央目录位置、条目数和注释长度 |

按 [PKWARE ZIP 格式规范](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)，常规本地头的通用标志在头起点 `+6`，中央目录文件头的对应标志在 `+8`，均为两字节小端字段；bit 0 表示该条目加密。只有证实标志与实际数据结构不一致时，才在单独修复副本中调整相应条目。不要全文件搜索替换某个字节；额外字段、数据描述符、ZIP64 和签名块都需要按结构解析。保存原始偏移、修改前后字节和哈希，复核条目能否完整读取、CRC 与资源/DEX 是否可解析；修复后的文件也可能无法通过原签名验证。

### 3.4 手机副本中的数据落点

| 常见位置 | 优先检查 | 容易误判的地方 |
|---|---|---|
| `/data/app/.../base.apk` 与同目录分包 | 安装包、版本、签名和 ABI | 中间目录可能带随机标识，不能按包名拼固定路径 |
| `/data/user/<userId>/<package>/` | 凭据加密的应用私有数据 | `/data/data/<package>/` 常用于用户 0；多用户或私密空间须分别检查 |
| `/data/user_de/<userId>/<package>/` | 设备加密存储的数据 | 与上一路径的可用时机和内容不同 |
| `shared_prefs/` | 配置、账号 ID、状态、令牌元数据 | 正确拼写是 `shared_prefs`；相同 key 在不同账号或文件中含义可变 |
| `databases/` | 主库、`-wal`、`-shm`、journal 和版本迁移 | 只复制主库可能丢失未合并记录 |
| `files/`、`cache/`、`code_cache/`、`no_backup/` | 文件、媒体缓存、代码缓存与不参与常规备份的文件 | 缓存可能被清理或预加载，代码缓存不自动等于脱壳 DEX |
| `/storage/emulated/<userId>/Android/data/<package>/` 等 | 应用外部文件与缓存 | 自定义共享目录也可能存在；访问受系统版本和存储模型限制 |

应用中 `getFilesDir()`、`getCacheDir()`、`getExternalFilesDir()`、`getDatabasePath()` 和实际文件打开路径比硬编码目录更可靠。`.so` 不一定先释放到应用私有 `lib/` 才加载。依据 [Android 存储文档](https://developer.android.com/training/data-storage) 记录当前 Android 版本、用户空间、解锁状态、备份方式及访问缺口，再用 [手机应用、通信与定位证据](/knowledge/forensic-mobile-apps/) 的记录关联方法解释数据。

### 3.5 应用形态与功能问题如何转成证据

先区分原生 Android 界面、WebView/网页封装、混合实现；框架名称或一个 `.so` 不足以确定全部业务运行在哪层。“原生界面”与“JNI 原生机器码”是两个不同概念。网页封装重点追 `loadUrl`、本地 HTML/JavaScript、跳转地址和 JavaScript 桥；混合应用还要追网页消息如何进入 Java/Kotlin 或 native 方法。

业务类型用于明确取证目标，不能代替行为证据：

| 要确认的功能 | 代码与资源入口 | 本地或关联证据 | 结论限制 |
|---|---|---|---|
| 直播、交易、提现与订单 | API 构造、账单界面、存储字段 | 账号、交易 ID、账单库、缓存及响应副本 | 页面数字可能是缓存或演示数据，须区分本地余额与服务端确认 |
| 聊天、联系人、音视频 | 消息模型、附件下载、媒体/通讯录 API | 消息库、附件、缓存、授权与时间记录 | 缓存不证明观看；读取联系人代码不证明已上传 |
| 定位、Wi-Fi 与设备信息 | 权限检查、定位/网络 API、请求字段 | 原始坐标、精度、时间、设备 ID 与上传记录 | 权限声明不等于授予，授予不等于实际调用 |
| 推广、客服、支付或其他跳转 | Intent、WebView、URL 路由 | 完整跳转链、第三方标识和离线响应 | CDN、共享 IP 或支付通道不能直接归属某个操作者 |
| 文件增删改与数据库更新 | 文件 API、SQL、事务和清理任务 | 路径、哈希、表/主键、前后状态与操作时间 | 提取缺失、缓存淘汰和业务删除需要分别解释 |

功能鉴定在隔离实验副本中设计单个动作，例如“授予定位后点击查询”，比较操作前后文件、数据库、日志和网络请求。记录系统/ABI、应用版本、账号、权限、网络状态与时钟；模拟器和实验真机出现差异时，先检查依赖、硬件能力与环境检测，不直接认定为隐藏功能。真实域名失效时仍可分析资源和离线代码，但不能据此确认已停止运营或恢复曾经的服务端行为。

### 3.6 从 Manifest 找到真正的入口链

先找同一个 `intent-filter` 中的 `android.intent.action.MAIN` 与 `android.intent.category.LAUNCHER`。入口可能声明在 `activity-alias` 上，此时沿 `targetActivity` 找实际 Activity；不要只全文搜到两个词就认定它们属于同一入口。[Activity 别名文档](https://developer.android.com/guide/topics/manifest/activity-alias-element)说明别名可以独立具有启动过滤器。

下例是构造的实验应用结构，用于说明调用关系：

```xml
<application android:name="com.example.lab.LabApplication">
    <activity android:name="com.example.lab.EntryActivity"
              android:exported="false" />
    <activity-alias android:name="com.example.lab.Launcher"
                    android:targetActivity="com.example.lab.EntryActivity"
                    android:exported="true">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity-alias>
</application>
```

再检查 `application android:name` 的初始化、Provider 初始化、静态初始化、组件的 `android:process`、深链和广播/服务入口。`onCreate()` 是重要起点，业务也可能在 `onResume()`、事件回调或另一个进程中执行。`uses-permission`、`android:exported`、`allowBackup`、`usesCleartextTraffic` 需要结合系统版本、目标 SDK、运行时授权及网络安全配置解释，Manifest 不能独自证明实际访问或可备份范围。

找不到入口类时，依次检查类名展开、别名、所有 DEX、已缺失的分包、反编译错误、动态加载和保护层；“Manifest 中有类但 JADX 没找到”不能单独证明加固。

### 3.7 组件、生命周期和事件回调

| 组件 | 关键回调/接口 | 逆向时追什么 |
|---|---|---|
| Activity | `onCreate`、`onStart`、`onResume`、`onPause`、`onStop`、`onRestart`、`onDestroy` | 页面初始化、恢复、事件注册与前后台切换 |
| Service | `onCreate`、`onStartCommand`、`onBind`、`onUnbind`、`onDestroy` | 谁启动或绑定、处理数据的线程/进程、停止条件 |
| BroadcastReceiver | `onReceive(Context, Intent)` | 广播来源、action、extras、后续工作和动态注册 |
| ContentProvider | `onCreate`、`query`、`insert`、`update`、`delete`、`openFile` 等 | 初始化、authority、URI、权限、数据库/文件映射和调用者 |

这些是回调线索，执行顺序由状态和触发条件决定；`onDestroy()` 也不保证每次进程结束都会执行。Service 是应用组件，不等于恶意程序，也不自动提供独立线程；默认仍在所属进程的主线程处理回调。Provider 不一定以 SQLite 为后端，也不能把访问短信简单等同于所有 Provider 的作用。参见 [Activity 生命周期](https://developer.android.com/guide/components/activities/activity-lifecycle)、[Service](https://developer.android.com/develop/background-work/services)、[广播](https://developer.android.com/develop/background-work/background-tasks/broadcasts)与[应用组件](https://developer.android.com/guide/components/fundamentals)。

从页面追业务时，按 `setContentView/资源 ID → findViewById/绑定代码 → setOnClickListener/onClick → 输入处理 → 条件/调用 → 结果或存储` 阅读。Kotlin lambda、Compose、反射、WebView 桥或异步任务可能没有经典的 `findViewById` 形式。Intent 需要追目标组件、action、URI 和 extras；Toast/Dialog/日志适合反查调用点，但提示内容不能代替真实执行结果。线程任务追 `Runnable.run()`、`Thread.start()` 或执行器提交点；Handler 要核对它绑定的 Looper，不能一概当作新线程。

Toast 常见链为 `Toast.makeText(context, text, Toast.LENGTH_SHORT).show()`，短显示常量是 `LENGTH_SHORT`；`context` 是否可用取决于调用对象和生命周期，不能在任意 Fragment/后台路径中机械替换为 `getActivity()`。接口见 [Toast 官方参考](https://developer.android.com/reference/android/widget/Toast)。

### 3.8 全文检索与交叉引用

```bash
rg -n -i 'https?://|wss?://|loadUrl|baseUrl|endpoint|mailto:|tel:' jadx-out apktool-out
rg -n 'getSharedPreferences|putString|getString|SQLiteOpenHelper|execSQL|insert|update|delete|openFileOutput' jadx-out
rg -n 'loadLibrary|native |DexClassLoader|InMemoryDexClassLoader|Class\.forName|getDeclaredField|RegisterNatives' jadx-out apktool-out
```

对地址、邮箱、号码保留完整上下文、资源/类/方法和引用者，区分接口、日志、第三方 SDK、示例和未使用常量。分段拼接、Base64、运行时配置或 native 生成的地址可能搜不到；对原生库另做字符串与引用分析。URL 只是候选线索，必须追到请求构造和触发条件，再与已有流量或受控实验观察核对。

JADX 的跳转声明与查找用例用于建立读写和调用关系，但“用例”同时可能是读取、写入、传参或方法调用，不全部等于赋值。界面快捷键随工具版本变化，以当前界面菜单为准；保存类/方法名、签名和 DEX 位置，避免只保存改名后的显示文本。

### 3.9 混淆、反射与条件推演

短类名、多层包装和字符串加密会降低可读性。先用**参数类型、返回类型、调用者、资源 ID、常量、副作用**定义角色，再为方法起分析别名。例如两个同名重载分别接收 `String` 和 `byte[]` 时，要核对转换发生在哪一层；同一个短变量名也可能属于不同作用域。

反射链通常是 `类名来源 → Class.forName → 字段/方法定位 → 对象或静态成员 → 调用/取值`：

| API 线索 | 正确含义 | 需要补充的证据 |
|---|---|---|
| `getDeclaredField(s)` | 返回本类声明的 Field 描述，可包含非 public 字段 | 字段名、类型与实际读写者；不等于已取得字段值 |
| `getField(s)` | 查找 public 字段，包含继承的可访问成员 | 声明类与继承链 |
| `Field.get(obj)` / `Field.set(obj, value)` | 从对象取值/向对象写值 | static 字段的对象参数可为 `null`；实例字段需要对象 |
| `setAccessible(true)` | 尝试放宽反射访问检查 | 系统/API 限制和异常；不保证任意成员都能访问 |

接口细节见 [Class](https://developer.android.com/reference/java/lang/Class) 与 [Field](https://developer.android.com/reference/java/lang/reflect/Field) 官方参考。分析时优先观察参数与返回值；直接反射改字段会改变条件和状态，不能用改值后的成功证明原来的功能链成立。

对 `if/else`、`try/catch/finally`、循环和异常路径逐一记录可达条件、状态变化与退出位置。异常分支可能选用备用地址，循环体可能逐字节变换，`finally` 可能写文件；不能只看 `if`、`try` 或循环判断。全局字段需同时追定义、初始化、最近写入、异步写入与读取点。

### 3.10 JNI 与 SO：跨过 Java 层的空方法

看到 `System.loadLibrary("logic")` 时检查对应 ABI 的 `liblogic.so`；看到 `System.load(path)` 时追完整路径的构造和文件来源。先确认 ELF 架构、导出符号、字符串和依赖，再在 IDA/Ghidra 等工具中读 native 调用链。

```bash
file apktool-out/lib/arm64-v8a/liblogic.so
readelf -h -Ws apktool-out/lib/arm64-v8a/liblogic.so
strings -a apktool-out/lib/arm64-v8a/liblogic.so | rg 'Java_|JNI_OnLoad|https?://|sqlcipher'
```

文件名和 ABI 均为示例，应替换为样本实际条目。JNI 有两条常见连接方式：按 `Java_包名_类名_方法名` 等规则查找导出符号，或用 `RegisterNatives` 映射“类、方法名、JNI 签名、函数地址”。后者常见于 `JNI_OnLoad`，但注册也可能在其他路径执行；符号被隐藏时不能据“没有 Java_ 导出”断言没有 native 方法。

`JNI_OnLoad` 常规签名为 `jint JNI_OnLoad(JavaVM* vm, void* reserved)`。普通 JNI 方法首参是 `JNIEnv*`，第二参随实例方法/静态方法分别为 `jobject`/`jclass`。例如 Java 方法 `byte[] decode(byte[] input)` 对应 JNI 签名 `([B)[B`；先恢复数组长度、返回类型和编码，再解释伪 C 参数。按 [Android JNI 指南](https://developer.android.com/ndk/guides/jni-tips)记录注册表到真实函数的关联，交叉核对整数截断、符号扩展、字节序和 JNI 字符串转换；`JNIEnv*` 属于线程，不能直接跨线程复用。

### 3.11 加固与动态加载的判别

| 观察到的结构 | 下一步证据位置 | 验证缺口 |
|---|---|---|
| 外层加载器把代码写到文件再加载 | `files`、`code_cache` 或实际写入路径；加载器参数 | 文件必须由本次路径产生且能解析为 DEX/载荷，不能只凭扩展名 |
| 从内存加载解密载荷 | 解密出口、缓冲区、类加载器与加载时机 | 有字节转储不代表已恢复全部类、方法或入口 |
| 方法按需释放/替换，或解释执行保护逻辑 | 特定业务触发、方法入口、解释器或 native 路径 | 单次转储可能缺少未触发路径，内存不足也不是唯一困难 |

这些是分析模型，不按某厂商名称固定归代，也不假设“全部执行一遍”即可脱壳。先完成容器和加载链静态检查；需要运行时观察时仅使用受控样本副本和隔离实验环境。记录每次触发动作、时刻、进程、ABI、类加载器、输出字节及哈希；解密的 DEX/方法还需结构检查和行为对照。未触发、无法运行或保护层无法还原时，应保留明确缺口。

### 3.12 ADB 的查询、复制与状态改变

已有手机镜像优先离线读取。下例仅用于已准备好的受控模拟器，不操作原始取证手机；包名是实验占位名：

```bash
LAB_SERIAL='emulator-5554'
adb devices -l
adb -s "$LAB_SERIAL" shell pm list packages
adb -s "$LAB_SERIAL" shell pm path com.example.lab
adb -s "$LAB_SERIAL" shell dumpsys package com.example.lab
```

`LAB_SERIAL` 必须与受控模拟器的实际序列号一致，连接状态为 `device` 也不保证系统已启动完整。`pm path` 可能返回多条 APK 路径，每条 `package:` 后的路径分别记录；只拿 `base.apk` 可能漏掉分包。

| 命令形式 | 用途 | 使用边界 |
|---|---|---|
| `adb -s SERIAL pull DEVICE_PATH NEW_LOCAL_PATH` | 将可访问文件复制到新的本地工作位置 | 不会自动取得私有数据访问权；保留采集日志和哈希 |
| `adb -s SERIAL shell`、`exit` | 进入/退出设备 shell | shell 能执行写操作，不能把进入 shell 当成取证只读保障 |
| `adb -s SERIAL forward tcp:LOCAL tcp:REMOTE` | 将主机本地端口转发到设备端口 | 这是主机 CLI 命令，不是 Python API；映射不证明远端服务存在 |
| `adb connect HOST:PORT`、`adb -s SERIAL usb` | 改变连接方式 | 仅面向已配置的实验环境，不是通用桥接或授权手段 |
| `install`、`uninstall`、`push` | 安装、卸载、向设备写入 | 改变程序、数据或文件状态，仅在可恢复的实验副本中使用 |
| `adb -s SERIAL shell am start -D -n PACKAGE/ACTIVITY` | 启动并等待调试器 | 改变运行状态；`-D` 不会自动使任意发布版具备调试权限 |
| `adb kill-server` | 停止主机端 ADB server | 会影响同一主机的其他 ADB 会话，不能作为首选排错动作 |

主机端 ADB server 默认监听 5037；Linux 上可先用 `ss -ltnp 'sport = :5037'` 查看监听者与权限允许显示的进程信息，再核对 ADB 版本、路径、设备状态。监听是 ADB 的正常情况之一，不是看到 5037 就结束进程。`dumpsys window` 的字段随系统变化，当前焦点 Activity 也不能代表全部后台进程。命令语法见 [ADB 官方文档](https://developer.android.com/tools/adb)。

### 3.13 动态调试、Objection 与 Frida 的受控观察

先确认样本副本在对应 Android 版本和 ABI 上可执行，再选择 Java/JDWP、native 调试或运行时插桩。保存操作前的文件/数据库基线，限定一个触发动作，记录目标进程、类加载器、调用参数、返回值和副作用；没有命中钩子也可能是重载、进程、加载时机或路径不匹配。

Objection 的免 root 方案依赖可用的 Frida Gadget 等接入条件，通常涉及重新打包和签名；它会改变样本，可能触发签名校验、更新或登录差异。把原件、实验改包与其哈希/签名分别保存，不把改包行为写成原始行为。准备条件见 [Objection APK patching](https://github.com/sensepost/objection/wiki/Patching-Android-Applications)。

下面的 `com.example.lab` 是自建训练应用，`Decoder.decode(byte[])` 为已确认的实例方法。脚本只记录测试字节并返回原方法结果：

```javascript
// observe.js：仅用于受控训练样本
Java.perform(() => {
  const Decoder = Java.use('com.example.lab.Decoder');
  const decode = Decoder.decode.overload('[B');
  const hex = a => a === null ? null :
    Array.from(a, v => (v & 0xff).toString(16).padStart(2, '0')).join('');
  decode.implementation = function (input) {
    console.log('decode input:', hex(input));
    const output = decode.call(this, input);
    console.log('decode output:', hex(output));
    return output;
  };
});
```

在已经配置好 Frida 接入的隔离模拟器中，用 `frida-ls-devices` 确认实验 ID；示例中的 ID 必须对应受控模拟器：

```bash
LAB_DEVICE_ID='emulator-5554'
frida-ps -D "$LAB_DEVICE_ID"
frida -D "$LAB_DEVICE_ID" -f com.example.lab -l observe.js
```

Spawn 适合观察启动阶段；Attach 使用 `-p PID` 附加已确认的实验进程，可能错过初始化调用。`-F` 指当前前台应用，不能保证就是目标进程。当前 CLI 默认在加载后恢复新进程，需要暂停时使用版本支持的 `--pause`；不要照搬旧教程的 `--no-pause`。核对客户端、server/Gadget、ABI 与 Java bridge 接入方式；单独通过 SDK 创建脚本时，桥接依赖和加载方式可能与 CLI 不同。语法见 [Frida Android 示例](https://frida.re/docs/examples/android/)、[进程选择参数](https://github.com/frida/frida-tools/blob/main/frida_tools/application.py)和[当前 CLI 暂停参数](https://github.com/frida/frida-tools/blob/main/frida_tools/repl.py)。这里的代码是训练模板，不能作为某个原始 APK 已被观察到的证据。

### 3.14 抓不到请求时怎样定位缺口

| 已有现象 | 先核对 | 目前不能下的结论 |
|---|---|---|
| 无 DNS 查询 | IP 字面量、缓存、DoH/DoT、抓取接口、请求是否触发 | 无 DNS 不等于 URL 必然直接使用 IP |
| 无代理 `CONNECT` | 是否使用 HTTP 代理、明文 HTTP、直连、UDP/QUIC | `CONNECT` 属于代理隧道流程，不是所有 GET/POST 的必经步骤 |
| TLS 建连失败或只见加密数据 | TLS 版本、证书信任/固定、网络安全配置、实验时钟 | 失败不等于应用没有业务请求，也不等于确认存在某种证书固定 |
| 域名解析为异常地址 | 原始响应、hosts、环境映射、缓存与拦截 | 某次返回 `0.0.0.0` 不能代表原服务的真实地址 |
| 点击后无包 | 缓存、权限/登录条件、异步任务、崩溃、后台进程和其他接口 | 单次无包不能证明不存在上传功能 |

把 `触发事件 → 请求构造 → DNS/连接 → TLS/应用数据 → 响应处理 → 本地写入` 与代码逐段对照，先确认最早缺失的阶段。TCP、UDP、代理和域名解析是不同层次；详细过滤和流重组见 [网络流量取证](/knowledge/forensic-network-traffic/)。

### 3.15 配置与数据库：从读写点解释文件

对 SharedPreferences，先找文件名和 key，再追 `getString/getInt/getLong` 的默认值以及 `edit/putString/remove/clear/apply/commit` 的写入链。构造的实验代码如下，只用于识别 API 到文件字段的关系：

```java
SharedPreferences prefs = getSharedPreferences("session", Context.MODE_PRIVATE);
String accountId = prefs.getString("account_id", "");
prefs.edit().putString("account_id", "lab-user").apply();
```

传统实现通常对应 `shared_prefs/session.xml`。`apply()` 异步写盘，`commit()` 同步写入并返回结果；内存状态、文件快照与操作时间可能不同。`MODE_PRIVATE` 是访问模式，不能据此认定每次编辑都覆盖全部 key；`MODE_APPEND` 用于文件写入，不是 SharedPreferences 的追加模式。`MODE_WORLD_READABLE/WRITEABLE` 已于 API 17 弃用，现代系统还可能拒绝使用，不能当成推荐的跨应用共享方法。详见 [SharedPreferences](https://developer.android.com/training/data-storage/shared-preferences)、[Editor](https://developer.android.com/reference/android/content/SharedPreferences.Editor) 和 [Context 模式定义](https://developer.android.com/reference/android/content/Context)。

数据库先辨认实际 import、实现版本和打开函数：

| 实现线索 | 判读 | 要追的调用链 |
|---|---|---|
| `android.database.sqlite.*` | Android 普通 SQLite API | `SQLiteOpenHelper` 构造中的数据库 name、升级逻辑、打开与 SQL |
| `net.sqlcipher.database.*`、`SQLiteDatabase.loadLibs(context)` | 旧 SQLCipher Android 实现 | 库加载 → 口令来源/派生 → 对应的带口令打开函数 |
| `net.zetetic.database.sqlcipher.*`、`System.loadLibrary("sqlcipher")` | 新 SQLCipher Android 实现 | 按该实现的接口核对；不能套用旧包名和 `loadLibs` 示例 |

普通 `SQLiteOpenHelper.getWritableDatabase()` 无口令参数；出现 `execSQL` 或继承 Helper 也不能证明数据库加密。旧式带口令 API 须核对具体 SQLCipher 版本。构造参数的数据库 name 只是文件名线索，实际路径还需追应用存储和调用者。参见 [Android SQLiteOpenHelper](https://developer.android.com/reference/android/database/sqlite/SQLiteOpenHelper)、[旧 SQLCipher](https://github.com/sqlcipher/android-database-sqlcipher)和[新 SQLCipher Android](https://github.com/sqlcipher/sqlcipher-android)。

### 3.16 两个可迁移的实战场景

**场景 A：只有离线 APK 与应用备份，要解释聊天数据库为何打不开。** 材料包含一份 APK、沙箱内 `databases/message.db`、可能存在的 WAL/SHM、配置 XML 和附件目录；这些是场景约定，不代表实际已经取得。

1. 记录包名、版本、签名、数据用户与备份时间，确认 APK 与数据是否对应；将数据库和已有伴随文件一起复制到工作目录并计算哈希。
2. 在全部 DEX/native 调用链中找数据库文件名、Helper、SQLCipher import 和打开函数；找到配置 key 只说明候选来源，继续追编码、拼接、设备/账号绑定与派生。
3. 若能确认加密参数，在另一工作副本中用匹配版本的解析工具验证；打开失败依次检查口令字节表示、SQLCipher 兼容参数、完整性与采集缺口，不反复修改原数据库。
4. 成功标准是可读 schema、账号及能与附件/其他记录对应的样本记录。记录账号、表、主键、时间、状态与附件哈希；能读库不保证已覆盖删除记录、其他账号或所有消息。

**场景 B：网页封装应用启动失败，要定位候选回传与交易接口。** 先从 Manifest 追启动 Activity、WebView、`assets` 网页和 JavaScript 桥；将本地主地址、配置下载地址、客服/支付跳转与第三方 SDK 地址分别记录到调用链。沿查询/提交事件确认请求字段、账号、交易 ID 和响应缓存的位置，再与已有流量和账单库交叉验证。没有运行成功时，可以报告“代码在某条件下构造某接口请求”，不能写成“已回传”或用界面余额当作已确认资金。真实服务、支付账户与漏洞扫描不属于离线分析步骤。

### 3.17 加解密与代码复现的核对表

从真正的调用处记录 `输入来源 → 字符编码/解码 → 重排/派生 → 加解密或哈希 → 比较/请求/落库`，不要从类名猜算法。至少保存以下参数：

| 节点 | 必须核对 |
|---|---|
| 编码与字符串 | UTF-8/UTF-16、Base64 变体与填充、十六进制解码、大小写、换行/NUL |
| 对称加密 | 算法、模式、密钥实际字节及长度、IV/nonce、填充、认证标签与 AAD |
| 哈希/派生 | 输入拼接顺序、盐、迭代、摘要/派生长度；不可把哈希当作可逆加密 |
| 数组/native 运算 | 有符号字节、32/64 位截断、端序、长度与边界 |
| 校验/存储 | 比较范围、成功条件、数据库格式与版本、事务和异步写入 |

在离线小脚本中先用自造的 ASCII、非 ASCII、边界长度输入逐层记录十六进制字节和长度，运行方式默认 `python3 reproduce.py`。再与相同版本的受控样本中间值对照，定位第一处差异；只有自测通过时，应写“复现脚本内部一致”，不能写“原程序已验证”。详细逆推方法见 [输入变换与比较值追踪](/knowledge/reverse-dataflow/) 与 [GUI 程序校验逻辑逆推](/knowledge/reverse-validation/)。

## 04 WASM 与宿主接口

```bash
wasm-objdump -x challenge.wasm
wasm2wat challenge.wasm -o challenge.wat
```

先记录导入函数、导出函数、内存段和数据段；再查宿主程序向内存写入的字节、调用时传入的指针/长度以及读取结果的方式。WAT 有助于看分支与整数操作，但变量名通常不可恢复。32 位整数运算会截断，线性内存的字节顺序也要与宿主端保持一致。

命令属于 [WABT 工具集](https://github.com/WebAssembly/wabt)；`wasm-objdump -x` 查看 section 细节，`wasm2wat -o` 输出文本表示。

## 05 验证边界

把“入口 → 参数编码 → 校验函数 → 输出”画成四段。每段保存输入/输出的实际字节，明确哪些来自反编译推断，哪些已由原程序或本地测试确认。不要把工具成功打开文件等同于题目已解出。

对 Android 功能分析，还要保存 `样本哈希/版本/签名 → 触发动作 → 进程与调用位置 → 参数/返回字节 → 文件/数据库/网络证据 → 验证结果与缺口`。用“代码声明”“静态推断”“受控实验观察”“检材记录”区分证据层次；截图缺失时只按可核对的文字和代码解释机制，不填入未观察到的地址、数值、进程或成功结果。
