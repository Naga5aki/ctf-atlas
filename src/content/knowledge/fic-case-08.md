---
title: "密码学取证"
summary: "辨认加密算法、密钥材料与哈希用途，复现受保护数据的解析过程。"
module: "Forensics"
track: "综合取证"
topic: "密码与资金"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42"]
challengeIds: []
relatedIds: []
updated: "2026-10-01"
---

## 01 从保护层到可验证的明文

密码学取证的任务是从程序、配置和介质中确认算法与参数，离线读取受保护内容，再验证结果的结构和上下文。高熵、固定长度和几个常量只能提供候选方向，不能替代数据流分析。先固定原密文及相关程序，输出到独立工作文件，避免程序自清理或覆盖导致材料丢失。

### 01.1 算法线索与确认条件

| 观察 | 候选 | 需要继续确认 |
| --- | --- | --- |
| 256 项置换表、双索引交换、输出密钥流 | RC4 | KSA、PRGA、密钥来源、状态初始化和丢弃字节数 |
| `<<4` / `>>5`、DELTA、固定轮数与密钥选择 | TEA/XTEA 家族 | 完整运算、轮数、索引、字节序及自定义变化 |
| `0x9E3779B9` | TEA/XTEA 常见 DELTA | 常量也会被其他算法使用，不能单独定型 |
| 16 字节分组，独立块映射、无 IV | AES-ECB 候选 | 实际 AES 调用或轮结构、密钥长度与填充 |
| `0x67452301`、`0xEFCDAB89` 等 | 借用散列常量的密钥或散列初始化 | 常量使用位置；不能因此认定完整算法 |
| Base64 字符集、可能含尾部 `=` | Base64 编码候选 | 严格解码、字节结构和调用链；也有无填充/URL-safe 形式 |
| 32/64 个十六进制字符 | MD5、SHA-256、SM3 等摘要样式 | 算法声明或重新计算；长度不能区分 SHA-256 与 SM3 |
| 输入输出等长、逐字节变化 | XOR、流密码或计数模式候选 | 掩码/密钥流、状态与是否还包含校验头 |

**实战顺序：** 找到读取密文的位置 → 跟踪密钥参数 → 确认变换和封装层 → 导出准确字节 → 离线复现 → 检查格式及重新加密回环。可读文本只是一项信号，不能当作唯一验收条件。

## 02 对称加密与模式参数

### 02.1 AES、RC4、TEA/XTEA 和 XOR

| 算法 | 结构 | 取证要点 |
| --- | --- | --- |
| AES | 128 位分组；密钥可为 128/192/256 位 | ECB 无 IV，CBC 需 IV；CTR 需 nonce/计数器布局，不能仅凭长度猜模式 |
| RC4 | 流密码，密钥初始化置换表后产生密钥流 | 密钥可直接来自口令或经过派生；状态重置和 drop 条件影响输出 |
| TEA/XTEA | 64 位分组、通常 128 位密钥 | 按 32 位字运算，核对轮数、sum、DELTA 和密钥调度 |
| XOR | 固定、位置相关或循环密钥掩码 | 记录是否使用 `i%16`、是否从某头部后开始、是否多层变换 |

这些算法在此用于解析既有材料，不能因为某种模式简单就先尝试它并把偶然可读输出当作结论。RC4 重用同一密钥流会暴露两个明文的 XOR 关系，但恢复单个明文还需要已知内容或其他约束。

### 02.2 实战：资源种子派生 AES 密钥

**材料：** APK 的资源、解密代码与 `assets/config.dat` 副本。假设已经确认代码以 UTF-8 编码种子，计算 MD5，取十六进制字符串前 16 个字符作 AES-128 密钥，采用 ECB 和 PKCS7。

```python
import hashlib
import json
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

seed = 'example_config_seed'
key = hashlib.md5(seed.encode('utf-8')).hexdigest()[:16].encode('ascii')
source = Path('work/config.dat')
ciphertext = source.read_bytes()
if not ciphertext or len(ciphertext) % 16:
    raise ValueError('密文不符合已确认的AES分组条件')
plaintext = unpad(AES.new(key, AES.MODE_ECB).decrypt(ciphertext), 16)
obj = json.loads(plaintext.decode('utf-8'))
assert AES.new(key, AES.MODE_ECB).encrypt(pad(plaintext, 16)) == ciphertext
Path('work/config-decoded.json').write_bytes(plaintext)
print('bytes=', len(plaintext), 'keys=', sorted(obj))
```

**示例判读：** 输出 `keys=['server', 'sponsors']`，JSON 结构符合代码读取字段，重新加密逐字节一致。这支持当前派生和模式与该密文对应，仍需确认字段属于目标版本和实例。原始 MD5 摘要的 `digest()[:16]` 与 `hexdigest()[:16].encode()` 不相同，截取“16 字节”或“16 字符”必须忠实于代码。[PyCryptodome AES API](https://pycryptodome.readthedocs.io/en/latest/src/cipher/aes.html)用于核对模式与密钥要求。

### 02.3 实战：离线 RC4 解出嵌套文件

**场景：** 程序代码显示以某个派生后的字节串初始化 RC4，连续解密一个文件，不丢弃初始密钥流。工作副本名为 `encrypted-volume.bin`，从已证明的派生结果读取 `rc4-key.bin`。

```python
from pathlib import Path
from Crypto.Cipher import ARC4

key = Path('work/rc4-key.bin').read_bytes()
ciphertext = Path('work/encrypted-volume.bin').read_bytes()
plaintext = ARC4.new(key, drop=0).decrypt(ciphertext)
assert len(plaintext) == len(ciphertext)
assert ARC4.new(key, drop=0).encrypt(plaintext) == ciphertext
Path('work/recovered.vhd').write_bytes(plaintext)
print('recovered_bytes=', len(plaintext))
```

```bash
file ./work/recovered.vhd
sha256sum ./work/encrypted-volume.bin ./work/recovered.vhd
```

`drop=0` 是复现已确认行为，不是设计新协议的安全建议。若原程序丢弃初始字节、逐块重新初始化或多线程交错，需要按真实实现调整；直接使用库默认值可能偏离目标。[ARC4 API](https://pycryptodome.readthedocs.io/en/latest/src/cipher/arc4.html)说明状态和 drop 参数。

重新加密回环对任意密钥都可能成立，因此它不能独立证明密钥正确；必须进一步验证 VHD 页脚/头部、虚拟容量、分区和内层文件结构。磁盘只读解析与派生链见[证据介质与文件系统](/knowledge/fic-case-02/)。

### 02.4 自定义 XTEA 与位置 XOR

位置 XOR 可能为 `output[i] = input[i] ^ (i%16) ^ 0x55`，或形状坐标使用 XOR `85`。先确认起始索引、处理长度与是否跳过头部。XOR 自反可快速回验，但输出有语义才是进一步证据。

TEA/XTEA 变体可能修改 DELTA、轮数、sum 初值，甚至采用双 sum 和变化的密钥索引。移位和加法支持算法家族判断，不能直接套标准解密函数。逐轮保留 32 位截断、大小端拆块、sum 更新顺序和最后填充处理；Native 参数追踪见[逆向工程](/knowledge/fic-case-07/)。

## 03 RSA 参数与可行恢复路径

### 03.1 先看条件，再选方法

| 条件 | 可以研究的路径 | 必须满足的限制 |
| --- | --- | --- |
| `n` 可分解 | 求因子、私钥指数，再解密 | 通常需有可行因子结构；大位数常规模数不能因“小工具能输入”就认为可分解 |
| 低加密指数，如 `e=3` | 无模约减的小消息根攻击或其他低指数条件 | 仅 e 小不够；填充和 `m^e < n` 等条件决定适用性 |
| 同一模数、不同互素指数、同一明文 | 共模攻击 | 必须证明同一明文和对应密文，负指数步骤还需可逆性 |
| 私钥指数过小 | Wiener 等路径 | 有具体数学范围，不是所有小 d 都必然符合 |
| 泄露部分因子高位 | Coppersmith/部分密钥恢复 | 已知位数、未知范围与方程须满足适用条件 |

优先找私钥文件、内存残留、配置、口令和派生逻辑。它们可能比尝试分解大 `n` 更直接；没有条件时应记录不可恢复的范围，不承诺硬算成功。

### 03.2 实战：可分解的教具参数

下面使用公开的小参数验证计算过程，展示从 `n/e/c` 到原始字节的关系，不代表真实检材的固定值。采用两个不同素数和无填充的教具 RSA。

```python
from sympy import factorint, mod_inverse

n, e, c = 3233, 17, 2790
factors = factorint(n)
if len(factors) != 2 or any(exp != 1 for exp in factors.values()):
    raise ValueError('本示例公式仅适用两个不同素数的模数')
p, q = sorted(map(int, factors))
assert p * q == n
phi = (p - 1) * (q - 1)
d = int(mod_inverse(e, phi))
m = pow(c, d, n)
assert pow(m, e, n) == c
raw = m.to_bytes(max(1, (m.bit_length() + 7) // 8), 'big')
print('factors=', p, q, 'd=', d)
print('plaintext_integer=', m, 'bytes=', raw)
```

**预期输出：** 因子 `53, 61`，`d=2753`，明文整数 `65` 和 `b'A'`。`factorint` 返回因子与重数，不能把字典键无条件解包成两个因子；`mod_inverse` 失败表示逆元条件不满足，不能继续计算。[SymPy 数论文档](https://docs.sympy.org/latest/modules/ntheory.html)用于核对接口。

真实文件若按多个 RSA 块保存，要确认每块宽度、字节序、长度字段和填充（如 OAEP/PKCS#1）；单纯 `pow` 与最短字节输出不保留前导零，也不完成填充验证。图片恢复后应检查完整格式，再读取二维码或其他载荷，见[文件格式与隐写](/knowledge/fic-case-09/)。

## 04 哈希、完整性与资源关联

### 04.1 算法用途与字节范围

| 算法 | 输出长度 | 取证用途与限制 |
| --- | --- | --- |
| MD5 | 128 位、32 hex | 对照旧标识、资源命名或弱派生线索；存在碰撞风险 |
| SM3 | 256 位、64 hex | 按明确要求或实现验证内容摘要 |
| SHA-256 | 256 位、64 hex | 文件与派生结果完整性记录；仍需采集关系证明 |

```bash
md5sum ./evidence/config.bin
sha256sum ./evidence/config.bin
openssl dgst -sm3 ./evidence/config.bin
```

```python
import hashlib
from pathlib import Path
data = Path('evidence/config.bin').read_bytes()
print('bytes=', len(data))
print('sm3=', hashlib.new('sm3', data).hexdigest())
```

对完整文件按原始字节计算；末尾换行、CRLF、编码、BOM 和补零都改变摘要。Python SM3 支持依所用加密库而定，报错时记录工具能力，不能用 SHA-256 替代后仍称 SM3。与 [OpenSSL dgst](https://docs.openssl.org/3.0/man1/openssl-dgst/)核对命令输出的算法和文件名。

### 04.2 实战：核对十六进制图片名称

**场景：** 数据库保存 `012345...abcd.jpg` 样式名称，想与备份图片关联。先将文件名视为候选标识，再固定真实图片，计算 MD5 与 SHA-256，检查文件名是否等于某种算法的完整摘要。名称相同并不保证字节相同，32 hex 也不证明算法就是 MD5。

若配置显示应用按内容 MD5 命名，且重新计算与名称一致，可用它关联主库、备份库和缓存路径；仍保留 SHA-256 及字节比较，防止同名覆盖、碰撞或应用任意命名。关联结论应包含真实对象而不是只比较名称。

## 05 密钥派生的证据链

### 05.1 常见来源与验证方法

| 来源 | 需要确认的细节 | 读取边界 |
| --- | --- | --- |
| 直接口令 | 输入编码、NUL、截断、是否额外变换 | 人可读口令不必然等于传给算法的字节 |
| 文件名/账户标识 | 前后缀、扩展名、大小写、派生步骤 | 只是候选关系，需代码或成功结构验证 |
| MD5 种子 | 原始摘要还是 hex、截取长度/单位 | 无盐快速派生属弱设计线索，但强弱不替代正确性验证 |
| 设备参数拼接 | `Build.*`、IMEI、包名的顺序、分隔符和缺失值 | 仿真设备的值不能代替原设备的历史值 |
| `AndroidKeyStore` | alias、算法、设备/硬件绑定、解锁条件 | APK/XML 可提供配置，但未必提供可导出的密钥 |

**实战记录：** `资源或设备字段 → 原始输入字节 → 派生函数/参数 → 实际密钥字节长度 → 模式和 IV → 明文结构`。公开报告可记录过程和证据位置，敏感密钥存入受控材料；不要在所有截图和命令历史中重复泄露。

### 05.2 失败时按可验证的条件回查

填充失败先回查模式、密钥字节、IV、密文偏移与长度；JSON 失败回查明文编码和是否还有压缩层；输出长度不同回查封装头与截断。不要把“先试 ECB，再试 CBC”写成唯一流程，已有程序逻辑应优先决定条件。每次试验保存参数和输出摘要，避免只保留看起来像明文的一次。

## 06 离线复现与验收

### 06.1 最小材料清单

保留原密文、程序和资源摘要，导出偏移/长度，密钥来源与派生参数，字节序、有符号处理、状态初始化、填充，脚本版本及中间结果。处理整数时使用 `struct` 与明确宽度；处理摘要用 `hashlib`；算法库调用使用已经核对的模式与参数。

### 06.2 输出判读和限制

1. 校验输入未在处理过程中变化，输出为新文件。
2. 核对明文长度、文件头、内部结构与校验字段，而不只看熵下降。
3. 对确定性加密过程重新加密比较，但说明回环不能单独证明密钥语义正确。
4. 对图片、数据库、VHD 等使用对应格式解析器进一步检查，保留可读文件或字段的上下文。
5. 将解密结果与账户、路径、时间或业务记录交叉；解密成功只证明材料与参数对应，不直接证明操作者身份或历史行为。

自定义填充若只用最后一字节表示长度，也要验证允许值和截断边界；不经检查就 `data[:-data[-1]]` 会在长度为 0 或异常值时产生错误。程序自清理、Native 数据块和验证约束继续见[逆向工程](/knowledge/fic-case-07/)。

## 07 实战：从分散片段恢复助记词顺序

### 07.1 场景与材料保全

**材料：** 钱包应用保存的已知地址、三份包含助记词片段的图片或文档、对应应用版本与钱包配置。先记录每个单词来自哪个对象、在对象中的位置和识别置信度；恢复的是词序，不把不确定的 OCR 字符直接当作正确单词。

| 片段形式 | 读取方法 | 验证条件 |
| --- | --- | --- |
| 不能打开的 PNG | 检查 IHDR、完整 CRC 和解码结果 | CRC 匹配还需完整图片可解码；保留修复前后哈希 |
| 虚拟空间中的图片 | 宿主 → 虚拟实例 → 导入/图库目录 | 区分内外层账号，保存实例映射和真实图片 |
| 名称与内容不符的备忘录 | `file`、文件头/尾、文档结构识别 | 附加 OOXML 或其他文档必须完整提取并能解析，不能只看扩展名 |
| OCR 提取的单词 | 与对应语言的 BIP39 词表比对，再人工复核 | `l/i`、近形字、断词与顺序错误分别列候选 |

格式修复见[文件格式与隐写](/knowledge/fic-case-09/)，虚拟实例定位见[Android 文件系统](/knowledge/forensic-android-storage/)。不要在完成保全前用修复结果覆盖图片。

### 07.2 先缩小搜索条件，再验证钱包

1. 确认钱包使用 BIP39，而不是产品自定义备份格式；固定词表语言、词数和重复单词。
2. 将可靠的位置作为约束：若三段各四词且段内顺序有证据，只需研究段的排列；若段内顺序也未知，不能沿用这一较小搜索空间。
3. 校验词表与 BIP39 checksum，排除结构无效候选。12 个不同单词任意重排有 `12! = 479001600` 种排列；重复单词和位置约束会改变数量。校验通过仍可能有多个候选。
4. 从钱包设置确认 passphrase、网络、派生路径、账户和地址索引，用已知地址验证候选。空 passphrase 也是一个明确假设；它与设备解锁 PIN 不等价。
5. 保留搜索范围、工具版本、候选数、派生路径与地址匹配结果。未找到匹配先回查词序约束和地址生成范围，不直接认定单词错误。

**校验关系：** BIP39 将熵和校验位映射到单词；生成种子时，对助记词与 passphrase 使用 NFKD 规范化，以 `mnemonic` 加 passphrase 作 salt，执行 PBKDF2-HMAC-SHA512、2048 次迭代。种子还要经过钱包的 HD 派生路径才能得到地址；checksum 正确与地址匹配是不同验证层。[BIP39 规范](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)定义这些条件。

### 07.3 BTCRecover 的有界验证流程

**场景假设：** 已确认目标为 Ethereum 钱包，十二词是英文 BIP39，匹配地址位于已确认路径的首个地址。使用工具文档的 tokenlist 语法表达可变位置和候选词，先在公开演示钱包上检验约束是否覆盖预期词序，再处理本地工作材料。

**词表示例：** `seed-tokens.txt` 可以把十二个候选词各写一行。以下仅展示公开演示词表的格式，必须将全部单词和已证实的位置约束按实际材料配置；不要把演示词当作自己的助记词。

```text
boy
hidden
kidney
famous
spring
convince
rich
season
gloom
ocean
husband
attitude
```

```bash
python3 seedrecover.py --help
python3 seedrecover.py \
  --mnemonic-length 12 --language EN \
  --wallet-type ethereum \
  --bip32-path "m/44'/60'/0'/0" \
  --addr-limit 1 \
  --addrs '替换为已核对的Ethereum地址' \
  --tokenlist ./work/seed-tokens.txt
```

**参数判读：** `--tokenlist` 读取候选约束，未指定 `--keep-tokens-order` 时可重排 token；`--addr-limit` 限定每个候选检查的地址数。`--dsw` 是关闭安全提示的选项，与重排算法无关，本例不使用。示例中的路径和范围必须由钱包证据支持；其他网络、产品、账户或地址索引应按匹配版本的工具选项调整。不要把首地址限制作为所有钱包的默认结论，也不要用面向 Bitcoin 的地址校验替代 Ethereum。[词序恢复文档](https://btcrecover.readthedocs.io/en/latest/BIP39_descrambling_seedlists/)与[Ethereum 示例](https://github.com/3rditeration/btcrecover/blob/master/docs/Usage_Examples/2020-05-02_Descrambling_a_12_word_seed/Example_Descrambling_a_12_word_seed.md)用于核对支持条件。

**示例结果：** 两个排列都通过 BIP39 checksum，只有一个在确认路径下导出已知地址。可以记录“该候选与此地址的派生关系匹配”；是否控制资产、发生过交易或由谁保存片段，需要钱包数据和交易证据另行判断。不要承诺“几秒完成”，先测候选速度与真实搜索规模；私密助记词和派生私钥只保留在本地受控工作区。
