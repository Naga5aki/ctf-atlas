## 01 先确定要恢复的对象

内存中的文件缓存、进程页、可执行映像、注册表 hive、桌面缓冲区和凭据容器属于不同对象。先完成[内存采集与镜像识别](/knowledge/forensic-memory/)中的格式和符号核验，再选择相应方法；不要将一份输出改成 `.dmp` 扩展名后交给任意转储解析器。

| 输出类型 | 实际材料 | 适合的验证 | 不能直接推出 |
| --- | --- | --- | --- |
| 文件缓存导出 | 文件映射或缓存中仍可读的页 | 实际字节数、格式解析、页面/块完整性、与磁盘版本比较 | 曾打开的全部文件均可完整恢复 |
| 进程内存页 | 某进程可寻址且镜像中可读的页面 | 虚拟地址映射、缺页、字符串/缓冲区归属 | 等同完整物理内存或 LSASS minidump |
| 重建可执行映像 | 工具从内存重建的 PE 等映像 | 节表、重定位、导入、重建范围及字节比较 | 与磁盘文件哈希必须一致 |
| minidump | 具有头、转储目录与相应数据流的专用容器 | 容器结构、进程/模块、架构、页覆盖、解析器兼容性 | 文件扩展名为 dmp 就支持凭据解析 |
| 内存 hive/对象 | 取得时仍可读的配置或对象状态 | 键路径、对象地址、原始值、磁盘 hive 与时间比较 | 必然等于后来磁盘上的完整状态 |
| 原始像素缓冲区 | 尚存的画布或图形数据 | 偏移、尺寸、跨度、颜色通道、方向及上下文 | 随机出现的轮廓等于真实完整截图 |

`dumpfiles`、Volatility 2 `memdump`、`procdump` 以及 Volatility 3 `memmap --dump` 是提取或重建，不是口令“爆破”。每份输出保存 `镜像哈希 → 对象地址/进程实例 → 提取参数 → 地址映射 → 输出大小/哈希 → 完整性与验证 → 限制`。对不完整材料，明确区分已恢复内容与候选片段。

## 02 按文件对象导出缓存

先建立文件对象清单，保存完整输出，再按路径筛选。以下以已识别的 Windows 镜像为例；地址必须来自当前镜像，示意地址不可照抄。

```bash
mkdir -p output/files output/process output/text
python3 vol.py -f work/memory.raw windows.filescan.FileScan \
  > output/filescan.txt
rg -i 'Desktop|Downloads|Documents|Videos|\.txt|\.png|\.zip|\.pdf' \
  output/filescan.txt
python3 vol.py -f work/memory.raw windows.dumpfiles.DumpFiles --help
```

确认文件对象地址属于虚拟还是物理地址。选取当前对象实际地址后，使用相应参数，不能把文件名、进程 VA、缓存页地址或磁盘偏移误作 FILE_OBJECT 地址：

```bash
# 仅当结果确认这是 FILE_OBJECT 的虚拟地址时使用。
python3 vol.py -f work/memory.raw -o output/files \
  windows.dumpfiles.DumpFiles --virtaddr 0xffff800012345678

# 仅当结果确认这是 FILE_OBJECT 的物理地址时使用，另建输出目录。
mkdir -p output/files-physical
python3 vol.py -f work/memory.raw -o output/files-physical \
  windows.dumpfiles.DumpFiles --physaddr 0x12345678
```

Volatility 2 的 `dumpfiles -Q` 接收 FILE_OBJECT 的物理地址，不等同于 Volatility 3 的 `--virtaddr`。Vol2 的 profile 和插件帮助必须先核验；具体参数差异见[Volatility 2/3 完整速查](/knowledge/forensic-memory-volatility/)。

同一文件对象可能通过不同缓存/映射结构生成多份输出。保留输出名称、对应结构、取得页面和空洞信息，不凭路径相同就合并。缓存可能只有前几页、旧版本、零填充区域或重用对象残留；导出成功也只说明取得了这些字节。

```bash
file output/files/*
sha256sum output/files/* > output/files-hashes.txt
```

继续用对应格式解析器检查页、索引、块和校验。导出的 PDF 可解析前几页时，报告部分页内容；ZIP 有文件名但数据缺失时，报告目录线索；数据库有页但无法恢复完整 schema 时，不称为完整数据库。缓存与磁盘文件哈希不同，先定位截断、缺页、页面版本和实际变化，不能直接判断篡改。

## 03 提取进程页和有归属的文本

按[进程与攻击行为](/knowledge/forensic-memory-processes/)选定进程实例，保存 PID、对象地址、创建时间和映像路径。导出页面时同时保存内存映射；PID `1234` 必须换成本镜像的候选实例。

```bash
python3 vol.py -f work/memory.raw windows.memmap.Memmap --pid 1234 \
  > output/process/pid-1234-map.txt
python3 vol.py -f work/memory.raw -o output/process \
  windows.memmap.Memmap --pid 1234 --dump
strings -a -t d work/memory.raw > output/text/strings-ascii.txt
strings -a -e l -t d work/memory.raw > output/text/strings-utf16le.txt
rg -i 'password|token|https?://|\.hc|\.zip|\.pdf' \
  output/text/strings-ascii.txt output/text/strings-utf16le.txt
```

系统 `strings` 给出的偏移是其输入文件中的字节偏移；扫物理镜像、导出进程文件和单个缓存文件，偏移各不相同。Volatility 2 的 `strings` 插件可按物理字符串偏移关联进程地址，它与系统 `strings` 不是同一命令。保留完整命中、编码、邻近字节、输入哈希与归属，不将导出文件偏移直接拿去读镜像物理地址。

字符串可能是文档、缓存、旧值、模板、安装包或不同会话的残留。出现 URL 不能直接证明访问，出现密钥文本不能直接证明使用，出现删除命令也不能直接证明删除成功。将候选串关联到进程、文件对象或有结构的数据，再与浏览器记录、日志和实际目标核验。多处相同文本若来自同一缓存或共享页，不构成多条独立证据。

命令相关材料分别解释：`cmdline` 是进程参数；Vol2 `cmdscan/consoles` 是支持环境中的控制台结构；PSReadLine 是历史文件；4104 是已启用相应日志条件下的脚本块记录。各自可读范围与时点不同，不能用一份材料填补另一份材料缺失的执行结果。

## 04 编辑器、便签、浏览器与图像缓冲区

| 对象 | 内存定位与磁盘互证 | 边界 |
| --- | --- | --- |
| 旧便签 StikyNot.exe | 进程文本、`AppData/Roaming/Microsoft/Sticky Notes/*.snt` | 新版可能使用应用包内 `plum.sqlite`，不能全部按 snt 解析 |
| 画图 mspaint.exe 与绘图程序 | 进程页、画布缓存、窗口尺寸、已保存图像 | 未保存内容可能部分留存，不能保证画布完整 |
| 旧通讯录 wab.exe | 对应进程对象与 `.contact` 文件 | 只适用于实际存在的系统和程序 |
| 旧 IE | 历史插件、缓存对象与磁盘记录 | 旧 `iehistory` 不覆盖所有现代浏览器 |
| 剪贴板、窗口、编辑控件 | 支持系统的旧 GUI 插件与进程缓冲区 | 可读结构有限，空表不证明未使用 |
| 私密浏览会话 | 浏览器进程页、DNS、代理/服务端记录、文件残留 | 内存时点和缓存寿命限制恢复范围 |

浏览器私密模式可能减少本地历史，但不保证 DNS、内存、代理、服务端和文件系统完全无痕。缓存也可能由预加载、同步或后台访问形成；找到缓存不能单独证明用户手工访问。磁盘浏览器结构与业务解释仍见[浏览器取证](/knowledge/forensic-browser/)。

恢复未保存画布时，先保存进程页映射和窗口/画布尺寸线索，在独立候选副本中提取像素区间。用 GIMP 的 Raw Image Data 导入时，逐项记录起始偏移、宽、高、RGB/BGR/RGBA、每行跨度及上下方向。这里不提供猜定的宽高；每次调整都应保留参数与候选图，而不是只留下最像图像的一张。

核验像素字节是否足以覆盖每行与全部高度，是否存在行填充、边界截断、重复行或缺页。将候选画面与实际窗口、画布大小、部分保存文件或其他独立材料比较。能够显示轮廓只说明该解释可行，不能凭模糊轮廓猜出文字并写成确定结论。Vol2 的旧 `screenshot` 插件输出窗口布局信息，不等于保证恢复完整桌面位图。

## 05 从内存注册表核验账户与 RID

内存 hive 可用来核验账户和配置状态；它与磁盘 SAM/SYSTEM 的密码材料处理是不同流程。先列出 hive，保存 SAM 对象地址和路径，确认插件期望的地址类型。Volatility 3 的示例使用 hive offset：

```bash
python3 vol.py -f work/memory.raw windows.registry.hivelist.HiveList \
  > output/hivelist.txt
python3 vol.py -f work/memory.raw windows.registry.printkey.PrintKey --help
# 替换为当前 hivelist 中确认的 SAM hive 虚拟 offset。
sam_va=0xfffff80001234000
python3 vol.py -f work/memory.raw windows.registry.printkey.PrintKey \
  --offset "$sam_va" --key 'SAM\Domains\Account\Users\Names' \
  > output/sam-users-names.txt
python3 vol.py -f work/memory.raw windows.registry.printkey.PrintKey \
  --offset "$sam_va" --key 'SAM\Domains\Account\Users' \
  > output/sam-users-rid.txt
```

Volatility 2 的对应模板仅用于已核验 profile；`-o` 取该 SAM 的虚拟 hive 地址，`-K` 取该 hive 内的键路径：

```bash
profile='REPLACE_WITH_VERIFIED_PROFILE'
volatility -f work/memory.raw --profile="$profile" hivelist \
  > output/vol2-hivelist.txt
volatility -f work/memory.raw --profile="$profile" printkey \
  -o "$sam_va" -K 'SAM\Domains\Account\Users\Names' \
  > output/vol2-sam-users-names.txt
volatility -f work/memory.raw --profile="$profile" printkey \
  -o "$sam_va" -K 'SAM\Domains\Account\Users' \
  > output/vol2-sam-users-rid.txt
```

用户名到 RID 的映射可能使用非常规类型字段编码；保存解析器原值及原始对象，不能因默认值显示为空就认定账户没有标识。示意 RID 的十六进制 `0x000003F1` 转换为十进制 `1009`，对应账户 SID 的末段是十进制 `1009`；它不是由用户名推定的常量。

Vol3 `PrintKey` 会检查注册表值类型是否属于标准 `RegValueTypes`；Names 映射中的非标准 RID 类型可能被显示为不可读值，普通结果表未必直接给出原始 RID。按匹配符号复核原始 `_CM_KEY_VALUE.Type` 整数字段，或在保留缺页记录的重建 hive 上用离线解析器检查；保存字节、类型与用户项对应关系，再同 Users 子键、磁盘 SAM 和完整 SID 互证。不可读提示不能代替原始类型字段的判读。

将 Names 映射、Users 对应项、磁盘 SAM、ProfileList 的完整 SID 与进程/登录会话逐项对照。账户记录存在不证明当前已登录；会话存在也不保证账户 hive 完整。缓存或缺页造成差异时，记录内存与磁盘各自时点，不强行合并。SAM 修订版、RID、bootkey 和磁盘账户哈希结构仍见[Windows 系统痕迹](/knowledge/forensic-windows-artifacts/)及[加密数据与凭据](/knowledge/forensic-protected-data/)。

## 06 区分 LSASS minidump 与其他转储

先判断输入容器，不仅检查后缀。完整物理内存、Vol2 `memdump` 的进程页、`procdump` 重建映像和 Windows minidump 不可互换；内核崩溃转储也不保证包含 LSASS 用户态页。保存转储头、目录、流、目标进程、模块、架构与可读范围，确认解析器支持该材料。

已取得有效且具有所需页覆盖的 LSASS minidump 时，可在隔离 Linux 分析环境使用 pypykatz。先保存帮助，输出可能包含敏感材料，只在受控目录保全：

```bash
mkdir -m 700 -p output/credentials
pypykatz lsa minidump --help > output/credentials/pypykatz-help.txt
pypykatz lsa minidump work/lsass.dmp \
  > output/credentials/lsass-analysis.txt
```

官方 minidump 功能的输入要求与各版解析支持需同时核验；报错、没有条目、部分包解析失败分别保留。不能因为缺页、凭据保护或不兼容而输出为空，就写成“用户没有登录”或“没有密码”。LSASS 中是否存有明文受系统版本、配置、凭据保护、采集时点及实际认证包影响，不保证总能提取明文。

Mimikatz 的以下操作属于明确的 Windows 离线分析分支，需要匹配的程序架构及支持的系统版本；只指向已有 minidump，不对真实主机注入或采集：

```text
sekurlsa::minidump C:\Case\Working\lsass.dmp
sekurlsa::logonpasswords
```

用户名、域、会话、RID、LM/NT 哈希、密码历史、票据及其他认证包输出应分别标记；哈希不是明文，LSA 机密与缓存域凭据也不能统一按一种格式破解。只在必要范围保留秘密的证据标识、归属、取得位置与验证结果，公开页面不展示真实口令、Token 或可用凭据。磁盘 SAM/SYSTEM 与域数据库的离线提取保留在[加密数据与凭据](/knowledge/forensic-protected-data/)，不因同属账户材料就搬成内存操作。

## 07 密钥候选必须回到实际目标验证

先识别被保护对象：BitLocker 卷、VeraCrypt/TrueCrypt 容器、DPAPI blob、EFS 文件、GPG 私钥或脚本中的加密数据。聊天、便签、历史命令、配置、截图、进程页与密钥文件均可提供候选，但要记录归属账户、目标、时间和字节范围。高熵不自动证明某种容器；单个可打印字符串也不证明密钥有效。

内存密钥扫描、AES 扩展密钥查找与密码字典搜索是不同工作。Passware 的支持格式和版本应按实际工具确认；findaes 等工具给出候选时，要回到对应算法与目标数据验证。Vol2 的 TrueCrypt 相关插件只覆盖部分历史实现，插件缺失或无命中不能排除加密。这里不把不受支持的新版本套入旧插件，也不编造统一的提取参数。

| 候选材料 | 需匹配的对象 | 有效验证 |
| --- | --- | --- |
| BitLocker 恢复/内存密钥 | 对应卷 ID、元数据和密文范围 | 派生镜像中的分区、文件系统与多个目标文件一致可读 |
| 容器密码、PIM、keyfile | 实际容器/分区、外层或隐藏卷 | 只读打开后核对卷大小、文件系统、目录及文件内容 |
| DPAPI 主密钥线索 | 主密钥 GUID、SID、Protect 文件与账户/机器条件 | 主密钥与目标 blob 的结构、用途一致 |
| EFS 证书/私钥 | 对应文件的 DDF/DRF、证书与私钥保护信息 | 实际文件可解且保留必要 NTFS 元数据 |
| AES/RC4 等脚本密钥 | 算法、字节处理顺序、IV/nonce、填充与输入范围 | 结构、校验/认证与目标内容验证 |
| RSA/ECC 等私钥片段 | 参数、编码、对应公钥/密文及完整性 | 数学与格式条件成立后，再做实际目标验证 |

内存中找到一个账户口令，可能只够解开某 DPAPI 主密钥；它不自动成为容器密码、EFS 私钥或所有账户凭据。keyfile 的文件名相同也不代表字节一致。对称密钥、口令、盐、IV、nonce、PIM 和恢复密钥各有角色，不能仅按长度命名。算法与参数校验详见[密码材料分析](/knowledge/fic-case-08/)，完整磁盘/容器只读处理仍见[加密数据与凭据](/knowledge/forensic-protected-data/)。

“成功”需要结构和内容：压缩包可完整测试，数据库有合理 schema 与已知记录，磁盘有一致文件系统与可读文件，带认证格式通过对应校验。仅有输出文件、若干可打印字符或软件进度条不足以确认解密。每次保存密文哈希、材料标识、算法/格式、工具版本与参数、输出哈希、验证及未解决项；不将秘密上传在线破解服务。

## 08 实战：文本、脚本、文件缓存和未保存画布

**场景与材料：** 训练场景中给定一份 Windows 内存镜像，其中浏览器有下载目录线索，便签存在容器提示，绘图进程可能保留未保存内容，脚本文本包含对某文件的逐字节处理。另有同机磁盘副本，目标是恢复可验证内容并区分完整文件、片段和解释性重建。这里提供分析模板，不表示已实际生成或复跑这些材料。

### 08.1 定位和独立导出

1. 固定镜像、磁盘和输出目录的对应关系。按进程实例定位浏览器、便签和绘图程序；保存版本、PID、创建时间、映射和文件对象。
2. 按第二节保存 filescan 全表并按实际地址类型导出候选文件；按第三节独立导出进程页。可执行映像若需分析，另行重建并单列记录，不能混成同一种导出。
3. 扫 ASCII 与 UTF-16LE，保存提示、路径和脚本文本的偏移、上下文及归属；浏览器下载记录与缓存只能按各自可确认范围描述。
4. 画布恢复记录偏移、宽高、跨度、颜色通道、方向和缺页；每份候选图保留参数，不凭可辨轮廓推定未读出的文字。
5. 逐次使用文件结构、真实 magic、字节数和格式解析器验证。扩展名可能伪装，每次转换后重新识别输入/输出格式。

### 08.2 安全重写已确认的字节算法

只有脚本证据足以确认算法和密钥字节时，才在分析副本中重写相同字节变换，不执行未知附件。以下仅说明重复密钥 XOR：

```python
from pathlib import Path

data = Path('work/cipher.bin').read_bytes()
key = b'known-key'  # 替换为证据中确认的完整密钥字节
if not key:
    raise ValueError('key must not be empty')
plain = bytes(value ^ key[index % len(key)]
              for index, value in enumerate(data))
Path('output/plain.bin').write_bytes(plain)
```

保存脚本文本、密钥标识、处理顺序、输入范围与派生输出。若实际逻辑还含编码、偏移、分块或其他变换，不能只因开头像文件就跳过其余步骤。候选解密后用格式和已知结构检验，不把猜定密钥写成证据已确认密钥。

GIF 的逻辑屏幕宽位于偏移 6–7、高位于 8–9，均为小端 16 位；各帧还具有自己的图像描述和范围。确需修正候选尺寸时，只改独立副本，保存前后哈希、改动偏移与旧/新字节，核对所有帧及帧边界。某一帧显示正常不代表全文件修复，也不能把解释性修复结果冒充取得时的原始字节。

### 08.3 判读与验证

缓存 PDF 只有前几页，而进程页中有同名路径：可以确认取得部分 PDF 与路径线索，不能将字符串拼成缺页文件。缓存哈希不同于磁盘版本：先检查空洞、截断和差异区间，再决定是否有内容变更证据。未保存画布可辨认但存在缺页：报告可恢复范围和参数，不报告完整截图。

若容器最终可只读打开，核对卷、文件系统和多个目标文件；如果只是 XOR 输出有图片头或 GIF 一帧可见，继续结构验证。所有派生物保留输入、对象、变换和输出映射，综合编排见[内存取证综合实战](/knowledge/forensic-memory-practice/)。

## 09 恢复结果的交付与复核

| 复核项 | 必须可回答的问题 |
| --- | --- |
| 对象范围 | 是全镜像、某进程页、文件缓存、注册表对象、minidump 还是像素候选？ |
| 地址范围 | 地址属于物理、进程虚拟、hive offset、模块 RVA/VA 还是导出文件偏移？ |
| 完整性 | 哪些页可读、哪些缺失、哪些被填零或工具重建？ |
| 归属与时间 | 对应哪个进程实例/账户/文件，材料处于哪个采集时段？ |
| 实际验证 | 格式、校验、结构、多个目标内容和独立材料核验到哪一步？ |
| 秘密保护 | 公开结果是否只给必要标识，原始敏感输出是否单独受控？ |
| 失败解释 | 插件/依赖、符号、格式、架构、缺页与无匹配对象是否已区分？ |

恢复失败不证明对象从未存在。无命中可能来自缓存回收、采集较晚、覆盖、保护机制或工具不支持；结论应给出本次方法能观察的范围。两种工具读同一对象可复核解析，却不能替代磁盘、日志、网络与采集记录的独立互证。
