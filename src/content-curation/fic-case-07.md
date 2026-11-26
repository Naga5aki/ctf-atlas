## 01 固定样本与选择分析入口

程序取证先说明样本从哪里导出、保存了哪些字节、属于什么格式和架构，再追踪验证、解密、挂载或清理逻辑。静态代码描述可到达的行为；是否执行成功仍需返回值、日志、文件变化或受控观察支持。不要为了取得临时输出直接运行可能改写检材的程序。

### 01.1 格式、工具与重点

| 对象 | 常用工具 | 优先检查 |
| --- | --- | --- |
| Windows PE | IDA、DIE、pe-bear、pestudio | COFF 时间字段、调试目录、架构、导入函数、入口 |
| Go ELF | IDA、符号与 Go 元数据解析工具 | `main.main` / `main_main` 等函数、字符串、运行时调用 |
| Android DEX | JADX、JEB、IDA | Manifest、类/方法、字符串池、数据流 |
| Android SO | IDA、Capstone、ELF 工具 | ABI、`.text`、`.rodata`、导出/JNI 调用与常量 |

```bash
mkdir -p ./work
sha256sum ./evidence/sample.exe
md5sum ./evidence/sample.exe
file ./evidence/sample.exe
cp --preserve=timestamps -- ./evidence/sample.exe ./work/sample.exe
cmp -- ./evidence/sample.exe ./work/sample.exe
```

**判读：** 摘要标识当前样本字节；MD5 可与既有记录对照，但不能独立承担对抗碰撞的证明。Windows 环境也可用 `certutil -hashfile sample.exe MD5`，本页操作默认在 Kali 上完成。哈希大小写只影响显示，报告保留算法、完整值和文件长度，不把前几位当作完整唯一标识。

### 01.2 Go 字符串与提示语

Go 程序可能保留函数名，帮助从 `main_main`、`main_a` 等位置进入业务逻辑，但符号可能被裁剪或工具改名。字符串地址不一定对应传统 NUL 结尾结构；需要跟踪指针与长度、调用者和字符串拼接。

**实战：** 发现“解密联系”等提示语旁有邮箱或网址。记录字符串字节、位置、引用函数和显示分支，再核对它是否被送到界面、日志或网络请求。屏幕上相邻或反编译文本中“上方两行”不是结构证据；邮箱字符串可以作为联系方式候选，不能据此确认真实控制者身份。

实际加载模块、进程映射与运行证据集中于[内存进程与攻击行为](/knowledge/forensic-memory-processes/)；从物理镜像恢复 PE 或进程页的方法见[内存对象恢复](/knowledge/forensic-memory-recovery/)。本页保留程序格式与代码逻辑的取证分析。

## 02 PE 时间字段与调试信息

### 02.1 读取 COFF 字段并保留原值

**材料：** 已固定的 PE 工作副本。DIE、pe-bear、pestudio 可展示字段，但应保留原整数与工具采用的时区。以下脚本仅读取 DOS 头指向的 PE 签名及 COFF `TimeDateStamp`，不运行样本。

```bash
python3 - ./work/sample.exe <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import struct
import sys

data = Path(sys.argv[1]).read_bytes()
if len(data) < 0x40 or data[:2] != b'MZ':
    raise ValueError('不是完整的候选 DOS/PE 头')
pe = struct.unpack_from('<I', data, 0x3c)[0]
if pe + 24 > len(data) or data[pe:pe+4] != b'PE\0\0':
    raise ValueError('PE 签名或 COFF 头越界')
raw = struct.unpack_from('<I', data, pe + 8)[0]
print(f'PE_offset=0x{pe:x}, TimeDateStamp=0x{raw:08x} ({raw})')
if raw in (0, 0xffffffff):
    print('该值不能作为常规时间解释')
else:
    print('按Unix秒解释的UTC候选值=', datetime.fromtimestamp(raw, timezone.utc).isoformat())
PY
```

**输出判读：** 得到的是“字段原值，以及按 Unix 秒解释的候选日期”。传统链接器常写入时间，但字段可修改、置零，也可能由确定性构建工具写入与时间无关的标识。先检查构建方式与调试类型，再称它为编译/链接时间线索；不能把工具显示的漂亮日期直接认定为真实编译时刻。[PE 格式说明](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)用于核对字段位置和调试目录。

### 02.2 PDB 并非天然更可信的第二时间

1. 读取调试目录的类型、时间字段、数据大小与文件偏移，验证结构未越界。
2. CodeView `RSDS` 记录通常包含 GUID、age 和 PDB 路径；GUID/age 用于匹配，**不是编译日期**。
3. 旧 `NB10` 或其他记录可能带时间字段，但仍需要按格式及构建工具解释，不能一律当成独立可信的编译时间。
4. 取得 PDB 后先核对匹配标识、摘要和来源；文件系统 mtime、PDB 内标识和 PE 字段可能来自同一构建过程，也可能被复制或重写。
5. 结合版本记录、可信构建日志、下载记录或签名相关时间，限定时间范围；冲突时保留全部原值，不只选择显示日期更合理的一项。

**示例结论：** “PE 头的时间字段按 UTC 解释为某日；调试记录为 RSDS，GUID/age 与所保存 PDB 匹配，但不能从这些标识直接获得编译时刻。”时区换算与其他文件时间继续见[时间线与行为重建](/knowledge/fic-case-11/)。

## 03 Windows GUI 验证逻辑的逆推

### 03.1 把输入、变换和比较串起来

**场景：** 程序在 GUI 中校验口令，验证通过后解密文件。先从 `WinMain`、窗口消息处理或按钮回调进入，找到读取输入、长度检查、字符检查、变换、加密比较与成功分支。

| 环节 | 必须记录 | 常见误读 |
| --- | --- | --- |
| 输入读取 | 字符串编码、缓冲区长度、是否含终止 NUL | “16 字节缓冲区”不一定等于 16 个可见字符 |
| 约束 | 实际比较长度、可打印范围 `0x20–0x7E` 等 | 反编译推断的数组大小不等于检查条件 |
| 逐字节变换 | 索引范围、截断规则、掩码来源 | 不做 `& 0xff` 会改变溢出语义 |
| AES 调用 | 密钥字节、模式、长度、IV/填充 | ECB 无 IV；不能给整块任意补填充 |
| 比较 | 明文/密文比较方向、比较字节数 | 只恢复字符串还需正向验证 |

### 03.2 实战：AES-ECB 与线性 XOR 逆推

假设静态指令已确认：输入按字节 XOR `(3*i+127)&0xff`，再作 AES-128-ECB，与一个 16 字节硬编码块比较。密钥由四个 32 位字按小端拼接，其中 `0x67452301`、`0xEFCDAB89` 等常量可能借自散列初始化值；单独出现常量不够识别完整算法。

**第一步：保存密文与密钥来源。** 从对应数据段导出恰好比较使用的字节，记录 VA/RVA、文件偏移、长度和引用指令。不要把屏幕上显示的有符号十进制数直接当作字节文本。

**第二步：按已确认条件逆推并正向回验。**

```python
import struct
from pathlib import Path
from Crypto.Cipher import AES

words = [0x67452301, 0xEFCDAB89, 0x67452301, 0xEFCDAB89]
key = struct.pack('<4I', *words)
ciphertext = Path('work/compare-block.bin').read_bytes()
if len(ciphertext) != 16:
    raise ValueError('需要已确认的16字节比较块')
transformed = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
mask = bytes((3*i + 127) & 0xff for i in range(16))
candidate = bytes(a ^ b for a, b in zip(transformed, mask))
forward = bytes(a ^ b for a, b in zip(candidate, mask))
assert AES.new(key, AES.MODE_ECB).encrypt(forward) == ciphertext
print('candidate_hex=', candidate.hex())
```

**判读：** 正向重新得到同一比较块，支持数学逆推正确；还需验证程序实际输入读取和字符约束。若尾部包含 NUL，应按读取函数语义判断它是终止符还是输入一部分，不擅自把 16 字节结论写成 16 个可见字符。若代码另有校验或环境条件，单一块通过不等于整个程序验证成功。

### 03.3 有符号常量与字节序

IDA 中负数可能表示同一 32 位比特模式。已确认是小端 32 位数组时，可以 `struct.pack('<4i', *有符号数)`；统一处理时先把每项 `& 0xffffffff`，再用 `'<4I'`。不能在超范围整数上直接使用带符号格式，也不能因为 CPU 是 x86 就把所有文件结构都当作小端。记录原显示值、归一化值和导出字节，最后与文件偏移处的真实数据比较。

## 04 Android Native 与 ARM64

### 04.1 从 JNI/调用者进入解密函数

**材料：** APK、对应 ABI 的 `libsecurity.so` 副本、DEX 调用者。先确认 ELF 的 machine、位数和端序，再定位 `System.loadLibrary`、native 方法声明、导出符号或动态注册表。JADX 的方法名与 SO 内函数可以不同，需要引用关系而不是只靠名称猜测。

```bash
file ./work/apk/lib/arm64-v8a/libsecurity.so
readelf -h ./work/apk/lib/arm64-v8a/libsecurity.so
readelf -S ./work/apk/lib/arm64-v8a/libsecurity.so
readelf -l ./work/apk/lib/arm64-v8a/libsecurity.so
```

`.text` 常为代码、`.rodata` 常放常量和密文，但实际依据 section 与 program header。`LDR`、`ADRP`/`ADD` 得到的是内存地址或相对寻址结果，**不能直接当作文件偏移**。依装载段的 `p_vaddr` 与 `p_offset` 映射，确认地址位于文件内的有效范围，再导出密钥块。

Capstone 可辅助逐条反汇编；不同版本 Python 绑定使用 `CS_ARCH_ARM64` 或 `CS_ARCH_AARCH64` 等名称，按安装版本文档选择，不混用示例。IDA 或 Capstone 输出只说明指令含义，参数追踪还要结合调用约定、寄存器和内存数据流。

### 04.2 实战：识别两阶段 XOR 与 XTEA 变体

**场景：** 上传函数在主服务器失败分支调用 `getBackupEndpoint()`，Native 返回加密保存的备用地址。分析目标是复现其解密链，而不是访问端点。

1. 确认失败条件和 native 调用确实相连，记录 ABI、函数入口和参数。
2. 找到被读取的密文块与四个 32 位密钥字，验证虚拟地址到文件偏移的映射。
3. 若 NEON 中出现 `movi v0.16b, #0xf`、`movi v1.16b, #0x55` 及索引向量，继续核对指令是否实现 `dec[i] = enc[i] ^ (i%16) ^ 0x55`；仅看常量不足以宣布掩码公式。
4. 在后续函数记录移位 `<<4` / `>>5`、加法/减法、DELTA、轮数和密钥索引。这组结构支持 TEA/XTEA 家族候选，最终靠完整运算确认变体。
5. 例如函数可能使用 DELTA `0x61C8864F`、双累加器 `0x8DDE6C40` / `0xEFA6F28F`、64 轮和 `[0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x9ABCDEF0]` 等参数。它们只是需要从实际指令读取的参数，不可替代标准模板后声称复现成功。
6. 每轮按 32 位无符号运算截断，保存阶段一输出、每块输入输出和最终字节；再按逆向推得的正向链重新加密比较。

**填充判读：** 若程序用末字节表示截断长度，应读清是否验证全部尾字节和允许范围。PKCS7 要求重复尾字节且长度在块大小内；自定义“只取末字节长度”不能直接视为标准 PKCS7。返回值成为合法域名/端口只是结构验证的一项，还要验证加密回环和实际调用关系。没有运行日志时，只能确认程序包含候选备用端点逻辑。

## 05 自清理与嵌套磁盘

### 05.1 先离线复现，再读取派生文件

程序可能在验证通过后 RC4 解密文件，调用 `OpenVirtualDisk`、`AttachVirtualDisk`，最终删除临时 VHD 或覆盖原始文件。对此先固定密文与样本，不依赖“运行得快、趁删除前拷贝”。

```bash
sha256sum ./evidence/encrypted-volume.bin
cp --preserve=timestamps -- ./evidence/encrypted-volume.bin ./work/encrypted-volume.bin
```

从函数中确认 RC4 密钥来源、编码、KSA/PRGA、是否丢弃开头密钥流、是否按块重置状态，再离线输出独立 `recovered.vhd`。RC4 密钥可能是口令本身，也可能经过派生，不能把 GUI 输入直接当作密钥。解密后核对 VHD 结构、虚拟容量与分区，使用只读解析，再固定内层账本。

### 05.2 结果与行为证据分别复核

`OpenVirtualDisk` 或删除 API 出现在导入表里，并不能证明相关行为发生；函数可能未调用、失败或被环境条件阻断。记录成功分支、返回值检查、生成文件名与删除顺序。确需观察时在隔离快照中运行，记录环境、输入和新日志，避免把仿真变化解释为原现场。

报告保持 `样本 → 校验逻辑 → 密钥/算法 → 原密文 → 解密VHD → 内层文件` 的派生链，每层保存长度与摘要。虚拟磁盘解析见[证据介质与文件系统](/knowledge/fic-case-02/)，密码参数与离线复现见[密码学取证](/knowledge/fic-case-08/)，内层流水统计见[虚拟货币与资金流](/knowledge/fic-case-12/)。

## 06 识别 RC4/AES 并复核解密出的 PE

### 06.1 从代码结构确认算法和参数

**场景与材料：** 一个 PE 读取资源或外部密文，解密后加载 DLL，DLL 再处理文件。固定样本、资源/密文、配置和路径，先用 DIE 等查看架构与壳信息，再沿读取、解密、分配、加载与调用链分析；加壳提示只是工具结论，需要实际结构支持。

| 线索 | 继续确认的结构 | 不能直接推出 |
| --- | --- | --- |
| 256 字节表、`&0xff` / 模 256 | RC4 候选的 S 初始化、KSA 的索引/交换、PRGA 的交换/输出 XOR | 任意 256 循环都等于 RC4 |
| AES S-box、逆表、T-table 常量 | 实际引用、轮函数、密钥扩展、轮数与 state 字节布局 | 仅见常量即可确认整个算法或 CBC 模式 |
| 密钥与 IV 看似相邻 | 使用参数、长度、复制顺序及数据流 | 固定“上 IV 下 key”，或必然采用小端 |
| 文件头部分可读 | 完整变换与输入边界、模式、填充、重置规则 | 一定是正确解密，或一定采用了魔改算法 |

AES 的块为 16 字节，标准 key 为 16/24/32 字节；CBC 的 IV 为 16 字节，ECB 没有 IV。模式要从分组间的 XOR 和链式状态、API 调用或完整循环中确认，不能从 key expansion 单独判断 ECB/CBC。字节串按原始顺序导出；若代码用多字节整数搬运，依据读取与装载指令确认端序，不对整个 key 盲目反转。

**具体取值：** 记录 key/IV 来源是硬编码、资源、输入或派生；每个地址同时保存 VA/RVA、文件偏移、长度和引用函数。Base64 外观的 ASCII 字节可能直接被当成 key，也可能先被解码，要跟踪真实输入；只有代码执行了 Base64 解码才将解码字节作为后续参数。

已知勒索家族的一个组件以 8 字节 `WANACRY!` 开头，接着 4 字节小端长度 `0x100`、256 字节由 RSA 加密的 AES 密钥、再 4 字节和 8 字节，其后是 AES 密文。这一家族的样本使用 CBC，IV 为 16 字节 0。内嵌压缩包的口令在解压函数的参数里。Windows `CryptExportKey` 的 PRIVATEKEYBLOB 在 magic 为 `RSA2` 时，按小端依次读取：1 字节类型、1 字节版本、2 字节保留、4 字节算法 ID、4 字节 magic、4 字节位长度、4 字节公钥指数，然后是模数和私钥分量。模数字节数是位长度除以 8。行为按 API 找：`taskkill` 的调用次数、`CreateShortcut`、`SystemParametersInfoW` 的动作值 `0x14`（设置桌面壁纸）。先看沙箱报告里的调用链，再对指定函数做静态阅读。

### 06.2 实战：已确认标准 RC4 的离线还原

假设已确认完整 KSA/PRGA、密钥字节、**不丢弃密钥流前缀、不在分块间重置状态**，可使用以下最小复现；这不是未知算法的自动识别器。密文与 key 字节分别保存在 `work/payload.enc` 和 `work/key.bin`，仅写一个新输出，不执行产物：

```bash
python3 - ./work/payload.enc ./work/key.bin ./output/recovered.dll <<'PY'
from pathlib import Path
import sys

source, key_path, output = map(Path, sys.argv[1:4])
data, key = source.read_bytes(), key_path.read_bytes()
if not 1 <= len(key) <= 256:
    raise ValueError('需要已确认的非空 RC4 密钥字节；本例最大 256 字节')
if output.resolve() in (source.resolve(), key_path.resolve()):
    raise ValueError('输出不得覆盖输入')
s, j = list(range(256)), 0
for i in range(256):
    j = (j + s[i] + key[i % len(key)]) & 0xff
    s[i], s[j] = s[j], s[i]
i = j = 0
plain = bytearray()
for value in data:
    i = (i + 1) & 0xff
    j = (j + s[i]) & 0xff
    s[i], s[j] = s[j], s[i]
    plain.append(value ^ s[(s[i] + s[j]) & 0xff])
with output.open('xb') as f:
    f.write(plain)
print('input_bytes=', len(data), 'output_bytes=', len(plain))
PY
```

确保 `output` 目录已经建立，`xb` 在文件已存在时拒绝覆盖。用同一确认参数对派生明文重新加密，与密文逐字节比较，另核对 DLL 的 DOS/PE 头、架构、节范围、数据目录、导出函数与加载器消费位置。CyberChef 的 RC4 输出同样需要保存原始字节，而不是只复制文本预览。

**判读限制：** RC4 XOR 回环对任意密钥都能成立，因此回环只验证实现/参数的一致性，**不独立证明密钥正确**；完整 PE 结构、资源来源、代码使用链及独立材料共同提高可信度。未知样本若还做了 key 派生、drop、压缩或分段重置，应先准确复现这些步骤，不能套本例后仅保留 `MZ` 开头。

### 06.3 PE 入口：RVA、首选 VA 和实际 VA

`AddressOfEntryPoint` 是 RVA；PE optional header 的 `ImageBase` 是首选加载基址，不能把所有 x64 DLL 固定为 `0x180000000`。静态首选 VA 为 `ImageBase + EntryRVA`；运行时实际 VA 为 **当次实际加载基址 + EntryRVA**，ASLR/重定位可使二者不同。某些工具直接展示 VA 或文件偏移，先读清字段再计算，避免重复加基址。

下面只读取 PE 头和节表，并给出文件映射候选，不加载 DLL：

```bash
python3 - ./output/recovered.dll <<'PY'
from pathlib import Path
import struct
import sys

data = Path(sys.argv[1]).read_bytes()
if len(data) < 0x40 or data[:2] != b'MZ':
    raise ValueError('DOS 头缺失或截断')
pe = struct.unpack_from('<I', data, 0x3c)[0]
if pe + 24 > len(data) or data[pe:pe + 4] != b'PE\0\0':
    raise ValueError('PE/COFF 头无效')
sections = struct.unpack_from('<H', data, pe + 6)[0]
optional_size = struct.unpack_from('<H', data, pe + 20)[0]
opt = pe + 24
if optional_size < 64 or opt + optional_size + sections * 40 > len(data):
    raise ValueError('optional header 或节表范围无效')
magic = struct.unpack_from('<H', data, opt)[0]
if magic == 0x10b:
    image_base = struct.unpack_from('<I', data, opt + 28)[0]
elif magic == 0x20b:
    image_base = struct.unpack_from('<Q', data, opt + 24)[0]
else:
    raise ValueError('本例仅支持 PE32/PE32+')
entry = struct.unpack_from('<I', data, opt + 16)[0]
size_image, size_headers = struct.unpack_from('<II', data, opt + 56)
print('ImageBase=', hex(image_base), 'EntryRVA=', hex(entry))
if entry == 0:
    print('入口 RVA 为零，不能在未知 DLL 中认定存在常规入口函数')
elif entry >= size_image:
    raise ValueError('入口 RVA 超过声明映像范围')
else:
    print('preferred_EntryVA=', hex(image_base + entry))
    candidates = []
    if entry < size_headers and entry < len(data):
        candidates.append(entry)
    for n in range(sections):
        s = opt + optional_size + n * 40
        virtual_size, va, raw_size, raw_start = struct.unpack_from('<4I', data, s + 8)
        if va <= entry < va + max(virtual_size, raw_size):
            delta = entry - va
            if delta < raw_size and raw_start + delta < len(data):
                candidates.append(raw_start + delta)
    print('entry_file_offset_candidates=', [hex(p) for p in candidates])
PY
```

如果示意首选基址是 `0x140000000`、EntryRVA 是 `0x2500`，首选 VA 为 `0x140002500`；当次加载基址不同则重新计算实际 VA。入口映射为空可能位于零填充区域或映像损坏/定制加载，多个候选可能说明节重叠；均需进一步检查，不能随意选择文件 offset。DLL 的实际业务导出函数也不必就是 PE 入口。

## 07 定制 AES：把轮密钥、周期和尾部规则拆开核验

### 07.1 先排除普通参数错误

**场景：** DLL 将文件加密为另一后缀，标准 AES 解密无法恢复完整格式。先核对实际 key/IV 字节、模式、padding、密文范围、头部封装、端序与状态初始化。仅“文件头像但不完全像”还可能是参数错误、损坏或其他编码，不能据此直接宣布定制 AES。

从标准 AES 结构对照实际指令，逐项检查 key expansion、轮函数、状态布局、CBC 链式 XOR、循环范围及最后写入。记录差异所在函数、输入/输出缓冲区和分支条件；标准库只提供标准 AES，不能给它一个不同 key 就认为已经复现改变扩展密钥的算法。

### 07.2 三种已识别差异分别记录

| 差异 | 需要从实现读出的信息 | 验证位置 |
| --- | --- | --- |
| 扩展结果中的 `w[0]` 与 `w[n]` 交换 | `w` 是 32 位 word、整轮 round-key 还是另一数组；`n` 起点、上限、交换发生在何时 | 每轮 key 字节与第一块完整加/解密轨迹 |
| 11 次短循环、256 块长循环 | 计数增加与重置时点、两层循环的真实索引、是否重新扩展密钥 | 第 10/11/12 次，以及第 255/256/257 块附近的输出 |
| 仅处理完整 16 字节块 | 余数是否原样复制、是否另行处理、是否保留长度 | 长度为 `16k`、`16k+1`、`16k+15` 的样例 |

这些模式必须从当前实现确认，不能作为全部定制 AES 的默认参数。`4096/16=256` 是块数换算，但不能仅凭这一等式推断 4096 字节边界重置 IV；密钥计数、CBC 前一密文块和文件读取缓冲区是不同状态。AES-128 有初始轮密钥与后续轮密钥，数组下标语义必须读清，避免把“11 轮密钥块”误写成“11 个 32 位 word”。

### 07.3 离线复现与边界实验

1. 固定代码、密文和已确认 key/IV，先实现标准参考并用公开已知测试向量检查基础 AES；仅基础参考通过还未证明定制逻辑正确。
2. 逐项加入已识别差异，将扩展密钥和计数状态逐块打印到实验记录；每个变化保留单独版本，避免同时改多处后不知道哪项使输出改变。
3. 在受控合成明文上比较已理解程序逻辑与离线实现，重点验证短周期、长周期、CBC 状态和尾部边界。使用标准 padding 去掉尾字节可能破坏原样保留的明文尾部，因此尾部处理必须依实际循环。
4. 对真实密文仅产生新文件：先检查完整头、所有块、长度和终止结构，再以相应 PNG/ZIP/PE 解析器核验全部内容；只修好前 16 字节不足以证明 4096 字节后的输出正确。
5. 重新加密比较可以检查逆过程和状态一致性，还应将独立提取的轮密钥、已知结构、受控轨迹或其他可信记录关联。摘要与预期某个短前缀相同不能替代完整字节验证。

**报告形式：** `轮密钥差异 → 下标/单位 → 短/长计数规则 → CBC状态规则 → 完整块数 → 尾部处理 → 测试范围 → 未验证条件`。没有当前样本的完整指令与受控结果时，只能保留定制链的分析方法，不虚构一份通用交换公式或声称附件已解密成功。

## 08 系统断点模块数与沙箱行为的时点

**材料：** 固定的 PE 工作副本、匹配位数的 x32dbg/x64dbg、隔离 Windows 快照。调试器初始化通常在系统断点处暂停，并可设置入口/TLS 等断点；应记录当次实际停止原因、地址和阶段。加载行为本身会改变实验状态，不能在日常分析机上直接初始化未知样本。

1. 在系统断点的明确时点保存已加载模块列表，包含模块名、完整路径、基址、大小和可核对的文件哈希；明确是否排除主 EXE、仅数 DLL、是否去重及过滤用户/系统模块。
2. 静态 import descriptor、延迟导入、运行时 `LoadLibrary`、API-set 映射和系统加载器行为不等价；因此静态导入 DLL 数不能替代该断点的实际模块数量。
3. 若先继续到程序入口或加载载荷后再截图，结果属于新时点；附加到已运行进程的 attach 断点也不同于新建进程的系统断点。OS Build、位数和运行环境可改变模块集合，不能公布固定数量作为通用答案。
4. 用模块基址加对应 RVA 计算实际地址，记录 ASLR 与重定位；静态 preferred VA 不等于当次运行地址。
5. 对后续落地文件、计划任务和域名请求，分别保存返回值、文件变化、任务 XML/事件和流量。静态字符串能说明候选；云沙箱中的外联或落地记录仅说明该实验环境的实际观察。

**独立实战判读：** 文件含一个 URL 并引用网络 API，但断网快照中请求失败；可记录程序具有该请求逻辑及当次失败，不能说历史设备已经成功下载。另一环境联网后生成程序和任务，其哈希/参数需与磁盘证据比较，并注明新增行为来自实验。云沙箱或仿真可以帮助解释代码，原设备的历史结论仍以对应时间的磁盘、内存和网络材料约束。快捷方式与 Go 图片加载链见[Windows 系统与用户痕迹](/knowledge/forensic-windows-artifacts/)。
