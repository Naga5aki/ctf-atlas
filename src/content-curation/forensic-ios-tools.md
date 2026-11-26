本篇集中维护 iOS 材料解析与人工复核的操作。**iLEAPP** 用于批量解析支持的 iOS 痕迹；**Plist_Editor** 用于查看和核对 Plist 键、类型与嵌套数据。二者都不等于设备采集工具，也不自动替代数据库、媒体及账号关系的人工分析。

先阅读 [iOS 原理、考点与流程](/knowledge/forensic-ios-forensics/)；若材料是哈希式本地备份，清单映射及数据库/WAL 导出按 [既有备份专项](/knowledge/forensic-ios-backup/) 操作。以下命令默认 Kali/Linux；Windows 专用程序另给 PowerShell 示例。

## 01 版本、用途与运行环境

| 工具 | 定位 | 本次核验与运行条件 |
| --- | --- | --- |
| iLEAPP：iOS Logs, Events, And Plists Parser | 搜索输入材料中的支持路径，调用相应解析模块，生成可追溯的痕迹报告 | 本地 `ileapp.exe --version` 返回 `iLEAPP 2026.4.4`；本篇参数按该版本实际 `--help` 及对应发布代码核对 |
| Plist_Editor | 本地文件夹实际程序是 VOWSoft 的 **plist Editor Pro**，不是同名 Python Plist-Parser | 本机程序文件属性版本为 `2, 1, 0, 1`（签名 Valid），官方产品页展示为 `v2.5.0`；记录时以本机实际运行的二进制版本为准 |

iLEAPP 提供预编译 Windows、macOS 和 Linux 构建；选择与操作系统、架构一致的发行包。预编译程序不需要为了运行它额外安装 Python。Windows 目录含 `_internal` 依赖时应整体保留，不只复制单个 exe。源码方式需要 Python 与对应版本 `requirements.txt` 中的依赖，先使用虚拟环境；本篇不把任意 Python 版本宣称为已验证兼容。[iLEAPP 官方项目及使用说明](https://github.com/abrignoni/iLEAPP)、[本篇对应发布版本](https://github.com/abrignoni/iLEAPP/releases/tag/v2026.4.4)

Plist Editor Pro 是 Windows 图形工具，支持 XML/binary plist。官方页面列出 Windows XP/Vista/7/8/10；此清单不是本轮对所有系统的实际兼容性测试。使用自己的可运行版本核对菜单和类型显示，不因安装路径写着 Plist_Editor 就认定是某一个同名产品。[官方产品说明](https://www.icopybot.com/plist-editor.htm)

**本地定位**：`D:\CTF_MISC_Tools\Forensics\iLEAPP\ileapp.exe`；`D:\CTF_MISC_Tools\Forensics\Plist_Editor\plist Editor Pro\plistEditor.exe`。这些是本机路径，迁移到另一机器时应改成实际安装路径。

## 02 iLEAPP 开始前的准备

1. 固定检材哈希，明确输入是文件树、原始备份、压缩包、单文件还是磁盘镜像。不要靠 `.zip` 扩展名判断它里面是普通路径还是备份哈希路径。
2. 单独创建输出目录；本版要求 `-o` 的基础输出目录已经存在。输出不要放进输入文件树，以免后续扫描混入报告。
3. 保存 `--version`、`--help` 和运行日志；使用与材料版本匹配的模块，不把历史 WP 中的旧版参数照搬到当前版。
4. 区分“解析器匹配路径”“成功读结构”“得到业务记录”三个状态；选错输入模式会使数据大量未命中。

```bash
# 在已取得对应发行版本或源码的目录运行。
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 ileapp.py --version
python3 ileapp.py --help
mkdir -p ./output/fs
python3 ileapp.py -t fs -i ./work/extracted -o ./output/fs -tz Asia/Shanghai
```

此源码命令是官方运行方式，依赖安装应使用同一版本代码与依赖清单；本轮实际解析验证使用的是 Windows 预编译程序，不宣称已经安装并运行了每种平台的源码环境。

```powershell
$Ileapp = 'D:\CTF_MISC_Tools\Forensics\iLEAPP\ileapp.exe'
& $Ileapp --version
& $Ileapp --help
New-Item -ItemType Directory -Path '.\output\fs' -Force | Out-Null
& $Ileapp -t fs -i '.\work\extracted' -o '.\output\fs' -tz Asia/Shanghai
```

图形方式可无参数启动程序，选择材料及输入类型、输出目录和解析模块，再运行并检查报告/日志。模块筛选用于缩小分析范围，不意味着未选模块对应的证据不存在。若本地界面与教程不同，先核对版本和本版帮助。

## 03 输入模式：不同材料不要混用

| `-t` 值 | 输入与用途 | 关键注意 |
| --- | --- | --- |
| `fs` | 已提取且保留正常逻辑路径/文件名的目录 | 应指向真实根目录，保留模块所需路径结构 |
| `zip` / `tar` / `gz` | 含正常路径和文件名的压缩包 | 格式与内容都需匹配；外层是压缩包不代表内层就是普通文件树 |
| `itunes` | 含清单及哈希式路径的原始 iTunes/Finder/Apple Devices 备份目录 | 使用备份映射；加密备份提供匹配密码，不能当普通 fs 猜散列文件名 |
| `file` | 单个目标文件 | 仅适用于支持的模块；文件名、路径和结构仍可能影响匹配，不代表任意文件均会自动识别 |
| `raw` | 本版支持的磁盘映像/采集容器，直接搜索所支持文件系统 | 本版帮助列出该模式；镜像/文件系统支持不等于能破解 iPhone 加密或读取任何 NAND 明文 |

```bash
mkdir -p ./output/zip ./output/tar ./output/backup ./output/file
python3 ileapp.py -t zip -i ./work/phone.zip -o ./output/zip -tz UTC
python3 ileapp.py -t tar -i ./work/phone.tar -o ./output/tar -tz UTC
python3 ileapp.py -t itunes -i ./work/backup -o ./output/backup -tz Asia/Shanghai
python3 ileapp.py -t file -i ./work/System/Library/CoreServices/SystemVersion.plist -o ./output/file
```

**加密备份**：保持 `-t itunes`，另加 `--itunes_password "BACKUP_PASSWORD"`，将占位值换成实际备份密码。参数中的密码可能留在命令历史或进程参数中；分析记录不应保存真实密码。官方 README 的某处输入模式示例有笔误，本篇以本版帮助和解析代码为准，不沿用错误类型。

**另有 keychain 导出**：`--keychain ./work/keychain.plist` 接收已有采集文件，某些应用的数据库密钥可能存于其中；是否能解析取决于文件内容、应用版本及模块支持。它不会主动从锁定设备采集 keychain。

## 04 常用与扩展参数表

以下是本机 `v2026.4.4 --help` 的参数用途，不是承诺每项都在真实检材上验证。版本更新后先重新读取帮助。[发布版本主程序与参数定义](https://github.com/abrignoni/iLEAPP/blob/7b0594a03c50d9b27ab49fa586e720e788b6236b/ileapp.py)

| 参数 | 作用与典型场景 | 使用注意 |
| --- | --- | --- |
| `-h` / `--help`；`--version` | 显示帮助、版本，核对当前运行文件 | 与分析日志一起保留 |
| `-i` / `--input_path` | 输入文件或目录 | 与所选 `-t` 匹配 |
| `-o` / `--output_path` | 基础输出目录 | 必须先创建；不是覆盖检材的路径 |
| `-tz` / `--timezone` | IANA 时区名，如 `Asia/Shanghai`、`America/New_York` | 报告展示时区不改写原始业务字段；国外题目需考虑夏令时 |
| `-w` / `--wrap_text` | 本版关闭数据文件文本折行 | 选项名易误读，不要解释成开启折行 |
| `-m` / `--load_profile` | 加载 `.ilprofile` 配置 | 适合固定解析模块集合；不要手写猜测配置字段 |
| `-d` / `--load_case_data` | 加载 `.lcasedata` 案件资料 | 描述性案件信息不是额外证据 |
| `-c` / `--create_profile_casedata` | 在指定位置生成配置/案件资料 | 官方帮助要求单独使用，不与解析命令混写 |
| `-p` / `--artifact_paths` | 在当前工作目录生成痕迹路径列表 `path_list.txt` | 单独使用，方便检查模块期望的路径；不是所有版本的固定路径全集 |
| `--custom_output_folder` | 自定义本轮报告子目录名 | 可分开版本/批次，避免误读上次报告 |
| `--html_row_limit` | 默认 50000 行；大于阈值的痕迹表不写入 HTML，页面引导查看 LAVA/TSV | 0 表示写出所有表；HTML 无表不等于零记录，大数据量注意报告大小 |
| `--custom_artifacts_path` | 载入额外模块目录 | 扩展模块会执行代码，记录版本与哈希；与内置支持分开说明 |
| `--itunes_password` | 提供加密本地备份密码 | 与 `-t itunes` 配合，不是设备锁屏口令参数 |
| `--keychain` | 指向已有 keychain 材料 | 不是通用解密保证，具体应用依模块支持 |
| `--image_password_file` | 从文件首行读支持的加密镜像/卷密码或恢复凭据 | 属于 `-t raw` 相关功能，不是备份密码文件接口 |
| `--image_password_env` | 从指定环境变量读取支持的镜像/卷凭据 | 传的是变量名，不是直接密码值 |
| `--image_private_key` | 支持的证书封装镜像所需未加密 RSA 私钥文件（PEM/DER） | 不表示可替代任意 iOS 密钥层级 |
| `--bitlocker_key` | 支持镜像中 BitLocker 卷的 `.BEK` 启动密钥，可重复 | 磁盘容器功能，不要当成 iOS 解锁方案 |

```bash
# 两条是独立的配置/目录辅助操作，不与 -i/-t 组合。
python3 ileapp.py -p
python3 ileapp.py -c ./output

# 同样的材料使用不同输出子目录，便于比较展示而非改写输入。
python3 ileapp.py -t fs -i ./work/extracted -o ./output/fs \
  --custom_output_folder review-utc -tz UTC --html_row_limit 0
```

## 05 输出解读与验证

官方项目说明包括 HTML、TSV、时间线、KML 和 LAVA 等输出能力；某次实际运行生成什么文件取决于命中模块和记录内容，不能要求没有定位记录时也一定生成 KML。[官方输出说明](https://github.com/abrignoni/iLEAPP)

本轮构造样本运行中，实际报告包含 `index.html`、`_HTML`、`_TSV Exports`、`_Timeline`、`_lava_artifacts.db`、`_lava_data.lava` 等。输出检查的顺序：

1. 从报告首页核对本轮材料、生成时间、系统版本和输出位置，避免打开旧批次。
2. 在目标痕迹表找原始逻辑路径/Source File、列名和关键记录，而不只用全文搜索命中标题。
3. 读取 TSV 或 LAVA 查看完整行，特别是 HTML 行数阈值导致不显示大表时。
4. 回查对应 Plist 键或数据库表/主键；报告中的标准化字段仍需核对时间和类型。
5. 检查模块日志。`No file found`、读入错误、零条业务记录与模块未选择，是四种不同情况。

**本轮实测边界**：使用保留 `System/Library/CoreServices/SystemVersion.plist` 结构的构造样本，分别运行 `fs`、`zip`、`tar`、`file` 四种模式，均退出 0，并产生 `System Version plist.tsv`。表头为 `Property / Property Value / Source File`，能够回查到 `ProductVersion=17.0` 与 `ProductBuildVersion=21A000`；这些是明确标记的构造值，不是真实手机、比赛答案或受检设备状态。输入文件 SHA256 在运行前后保持一致。

该测试证明本机程序和这一个模块对这些输入可工作，不证明其他所有应用、加密备份、`gz/raw` 或全部插件已实测。本机三份选定模块代码与相应发布代码在统一换行后相同，字节哈希因 CRLF/LF 不同而不同；这也不是整个 exe 来源的认证。

## 06 Plist_Editor 的只读操作

本节按 VOWSoft 的 Plist Editor Pro 官方手册给操作路径；本轮核对了本机产品属性和签名，**未执行图形界面开文件/保存操作**，不把手册步骤表述为本轮 GUI 实测。[官方手册](https://www.icopybot.com/plist-editor-manual.htm)

1. 将目标 Plist 导出到工作目录，记下逻辑路径、导出哈希和对应检材；保留不变的原件。
2. 在程序中用 `Ctrl+O` 打开副本，进入 **View → Read only**。这是编辑器的只读模式，不能替代检材存储层面的只读保全。
3. 用 **XML View / List View** 或 `Ctrl+Tab` 切换。XML 便于核对键与原始标签，列表便于看层级和类型；显示形式不同不表示两个不同证据。
4. 用 `Ctrl+F` 查目标键，展开字典/数组，记录完整键路径、值和类型。区分空字符串、NULL 类表现、布尔与整数，不只截一行值。
5. 对 Data 项可双击查看嵌套内容，工具会按内容打开内置文本/十六进制/图像/数据库/Plist 查看器。是否能识别取决于数据格式，不能保证每个 Data 都是可直接解码业务对象。
6. 十六进制视图核对偏移、字节及大小端预览；涉及修改的按钮只用于另行分析副本，不对检材保存。
7. 记录结果和截图。确需输出另一个文件时用 **File → Save As** 指向独立派生目录，再计算哈希并重新解析；平时避免误按 `Ctrl+S` 覆盖当前副本。

手册介绍的是查看/编辑工具，未确认批量命令行接口。因此不为 `plistEditor.exe` 编造 `--decode`、`--export-json` 等参数。需要可复现批量读取时，使用下节的只读脚本，而不是把不存在的 GUI 参数写入工作流程。

## 07 Plist 键、Data 和日期的输出解读

| 观察对象 | 如何阅读 | 适用场景和注意事项 |
| --- | --- | --- |
| 系统版本键 | 同时记录 `ProductVersion`、`ProductBuildVersion` 和文件路径 | 识别系统版本与构建号，注意归档日志中的历史副本 |
| Bundle ID/账号配置 | 记录键路径、应用版本及稳定账号标识 | 配置存在只能证明保存了配置，不单独证明在指定时刻登录或操作 |
| 数组与字典 | 保留数组次序、每个值的数据类型和完整层级 | 不将多个历史值误当同一条当前状态 |
| Date | XML 常以带 `Z` 的 UTC 日期表示；保留解码后的时区语义 | 不再对已解析的日期字符串加 Apple 纪元偏移，也不默认按本机时区解释 |
| Data | Base64 展示对应字节内容；可进一步识别嵌套格式 | Base64 是编码不是加密；打开失败可能是压缩、截断、未知对象或真正加密，需验证 |
| NSKeyedArchiver/UID | 检查对象表、入口和引用关系 | UID 是对象引用；看到结构不代表应用自定义对象已经完整还原 |

Binary plist 与 XML 之间转换可能改变字节、类型表现或工具可读性；另存后哈希变化是正常的派生物变化，但必须验证所需字段语义是否保持。含 UID 的归档不适合无条件转成普通 XML/扁平 JSON。[Apple Plist 类型定义](https://github.com/apple-oss-distributions/CF/blob/main/PropertyList.dtd)、[Python plistlib 的格式和 UID 支持](https://docs.python.org/3/library/plistlib.html)

可下载 [ios_inspect.py](/practice/ios_inspect.py) 交叉读取 XML/binary plist：

```bash
mkdir -p ./output/plist
sha256sum ./work/Info.plist
python3 ios_inspect.py plist ./work/Info.plist > ./output/plist/info-typed.json
sha256sum ./work/Info.plist
```

脚本只读取文件，输出原文件 SHA256、格式和保留类型的 JSON：Data 以长度与 Base64 表示，Date 以 UTC 表示，UID 保留引用数值而不假装完成解档。它不是提取工具、解密工具或完整 NSKeyedArchiver 业务解析器。错误退出时回查格式与完整性，不把空输出当成证据不存在。

## 08 实战：两款工具在真实考点中的分工

| 真实问题方向 | iLEAPP 负责什么 | Plist_Editor / 原始数据复核负责什么 |
| --- | --- | --- |
| 2021 健康库同步 | 初筛健康/系统相关报告，记录命中路径 | Plist 核对系统与材料身份；同步答案回到 SQLite `cloud_sync_stores.last_sync`，不是从配置时间猜 |
| 2022 应用累计时长 | 输出支持的活动记录，提供快速定位 | 用实际 knowledgeC 结构复查、分组与累计，Plist 辅助关联 Bundle ID，不把最长单行当总时长 |
| 2022 未读统计差异 | 报告初筛与解析日志 | 主库/WAL 状态和数据库字段人工核验；Plist 编辑器不替代 SQLite 查询 |
| 2023 健康距离与地点 | 按支持版本找健康、RoutineD、Biome 入口 | 核对样本时间窗、位置时间和来源；未知字段不补造 SQL |
| 2024 类别与支付渠道金额 | 支持时先筛对应应用及账号 | Plist 确认应用/配置，SQLite 联合筛选类别与渠道，验证分/元和状态后汇总 |

以上均对应 [原理篇中的真实比赛资料与方法](/knowledge/forensic-ios-forensics/)，不是本轮用工具复跑后的成绩或答案。工具不支持某 App 时，继续按格式和数据库结构分析；不要为了让报告显示一个值而修改检材。

## 09 离线实战：从目录命中到可复查记录

**材料与目标**：一份已经取得的 iOS 文件系统导出，需定位应用归属、查询通信记录，并判断数据库报错究竟来自格式、伴随文件还是损坏。以下步骤在工作副本上进行，输出目录与输入分开；备份哈希布局先按备份篇映射，不当普通文件树搜索。

### 9.1 搜索真实路径，再读类型

```bash
mkdir -p ./output/triage
# -P 在搜索起点前；不跟随导出中的符号链接到分析机或其他目录。
find -P ./work/extracted -type f -name '.com.apple.mobile_container_manager.metadata.plist' -print > ./output/triage/container-metadata-paths.txt
find -P ./work/extracted -type f \( -name 'sms.db*' -o -name 'CallHistory*.storedata*' -o -name 'NoteStore.sqlite*' -o -name 'Photos.sqlite*' \) -print > ./output/triage/database-paths.txt
```

输出是候选路径清单，不是业务记录。`-P` 不自动展开别名；若导出只保留链接，要依据采集清单定位真实目录，不随意改用 `-L` 扫描。路径前缀、大小写、容器 UUID 和同名库不同，都可能导致工具没有命中。[GNU find 符号链接处理](https://www.gnu.org/software/findutils/manual/html_node/find_html/Symbolic-Links.html)

从清单选择一个真实元信息文件，复制到单独检查目录，再复用现有 `ios_inspect.py` 或 Plist_Editor 的只读查看步骤，记录 `MCMMetadataIdentifier`、类型和父目录；不要因报告中 Bundle ID 的列标题就把共享组值当作主应用身份。系统数据库与共享库的定位、版本和字段解释统一见 [原理篇第 03、07 节](/knowledge/forensic-ios-forensics/)，本节不另列第二套路径表。

### 9.2 数据库先保全组合，再做只读查询

1. 按实际逻辑路径登记主库及同名 WAL/SHM，导出组合后保存哈希；保持同一 basename，查询前按备份篇保存独立快照。
2. 对快照确认格式、表结构和实际列；不要先点 GUI 的修复、清理或写入功能。只读打开控制数据库连接，不代替工作副本隔离与文件哈希核验。
3. 保存 SQL、主键、原始时间和原值；消息/附件连接可能一对多，统计时明确对象并去重。

```bash
# app-snapshot.sqlite 是已生成的独立工作快照，不是原始检材。
file ./work/app-snapshot.sqlite
sqlite3 -readonly ./work/app-snapshot.sqlite '.tables' > ./output/triage/tables.txt
sqlite3 -readonly ./work/app-snapshot.sqlite '.schema' > ./output/triage/schema.sql
sqlite3 -readonly ./work/app-snapshot.sqlite 'PRAGMA quick_check;' > ./output/triage/quick-check.txt
```

`quick_check` 返回 `ok` 只支持本次结构检查通过，不证明全部记录或旁文件齐全；报错先核对文件格式、是否加密、完整性与工具版本。SQLite GUI 可用于人工查看，但 SQLite 数据库不交给 Plist 编辑器解释。[SQLite 官方 CLI](https://sqlite.org/cli.html)

### 9.3 损坏库的派生恢复与限制

`.recover` 用于尝试抢救损坏 SQLite 中仍可读的数据，不是“完整恢复已删除记录”的保证，也不解密数据库。先保全输入组合，只对另一个派生副本尝试；输出使用本次新目录：

```bash
mkdir -p ./output
# 在独立脚本/会话中执行；目录已存在就停止，换新的运行编号。
mkdir ./output/recovery-run-01 || exit 1
# 先用 sqlite3 --help、.help 核对本机构建提供 .recover。
sqlite3 -readonly ./work/damaged-copy.sqlite '.recover' > ./output/recovery-run-01/recovered.sql 2> ./output/recovery-run-01/recover.log || exit 1
# 上一步成功且 SQL 已检查后，再建立新数据库；不回写输入。
sqlite3 -bail ./output/recovery-run-01/recovered.sqlite < ./output/recovery-run-01/recovered.sql 2> ./output/recovery-run-01/import.log || exit 1
sqlite3 -readonly ./output/recovery-run-01/recovered.sqlite 'PRAGMA integrity_check;'
```

保存两步退出状态、日志和派生哈希，回查 SQL、表与原始记录。恢复可能带回旧删除内容、改变值/类型、丢失关系或把内容放入 `lost_and_found`；结构检查通过也不保证业务真实性。`--ignore-freelist` 会跳过空闲页，不能不说明选项就把两种结果混为一份。把恢复线索与现存记录分开，并与媒体、通信对端或其他库验证。本轮未执行损坏库 `.recover`，不宣称恢复效果。[SQLite 恢复及限制](https://sqlite.org/recovery.html)

## 10 故障排查和交付清单

| 表现 | 优先检查 |
| --- | --- |
| iLEAPP 找不到输入或输出 | 路径引号、工作目录、`-o` 是否存在，输入是否误指向输出 |
| 大量 `No file found` | 输入类型、目录前缀、文件名、配置中选择的模块；与 `-p` 的本版路径需求对照 |
| 单文件没有报告 | 模块是否支持单文件、期望的文件名和结构是否保留，不把任意 `.plist` 等同 SystemVersion |
| 备份打不开 | `-t itunes`、清单文件完整性、是否加密及密码是否匹配；不要把镜像密码参数当备份参数 |
| SQLite 数据缺失或报告与查询不同 | 同名 WAL/SHM、读取快照、字段转换、版本和账号范围 |
| HTML 缺表但日志有记录 | `--html_row_limit` 与 TSV/LAVA；不是简单重装工具 |
| Plist 打开失败 | 真实文件头、XML/binary 格式、文件是否截断、是否压缩/加密或其他序列化格式 |
| Data 看起来“乱码” | 保留原字节，验证 Base64、嵌套结构与大小端；不可按肉眼猜成密码 |
| GUI/命令显示不同日期 | 日期对象与数值时间区别、纪元/单位、展示时区，原始值是否相同 |

**交付时同时保留**：输入哈希和逻辑路径、工具版本和命令/GUI步骤、运行日志、报告目录、目标 TSV/记录定位、人工复查查询、原值与转换值、结论与限制。iLEAPP 报告用于提高检索效率，Plist_Editor 用于看清类型与结构，最终证据仍回到真实记录及其上下文。
