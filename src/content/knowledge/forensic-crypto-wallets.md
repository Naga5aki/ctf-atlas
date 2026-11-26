---
title: "钱包取证：本地痕迹、派生与控制权"
summary: "定位本地钱包、keystore与HD派生材料，区分观察、硬件、多签及合约钱包的控制条件，判读DApp签名与代币授权。"
module: "Forensics"
track: "虚拟币取证"
topic: "钱包与本地痕迹"
tags: ["文件系统", "编码"]
status: "已整理"
sourceIds: ["web-crypto-zhihu-14425551337", "web-crypto-ethereum-accounts", "web-crypto-core-files", "web-crypto-wallet-rpc", "web-crypto-web3-storage", "web-crypto-metamask-passworder", "web-crypto-metamask-recovery", "web-crypto-metamask-accounts", "web-crypto-bips", "web-crypto-sqlite-wal", "web-crypto-leveldb", "web-crypto-mobile-wallet-research", "web-crypto-shuzheng-2025", "web-crypto-fic-final-2025", "web-crypto-meiya-individual-2024", "web-crypto-research-c613834a37ca", "web-crypto-research-ef670f5fab3d", "web-crypto-research-f085cce41a61", "web-crypto-research-0778b6b5eb0a", "web-crypto-research-9c6865410dbe", "web-crypto-research-e925009bccf3", "web-crypto-research-2d0c755b29bf", "web-crypto-research-65470fa353a6", "web-crypto-research-bd56c2d50d15", "web-crypto-research-c78d0f0c60a4", "web-crypto-research-1f53bb744ddd", "web-crypto-research-814581643761", "web-crypto-research-d6fd00db521f"]
challengeIds: []
relatedIds: ["fic-case-12", "forensic-crypto-foundations", "forensic-crypto-bitcoin", "forensic-crypto-account-chains", "forensic-crypto-tracing", "forensic-crypto-practice"]
updated: "2026-10-03"
---

## 01 先区分钱包、账户与控制权

虚拟币钱包通常管理密钥、地址、交易记录和连接配置。资产状态保存在对应区块链或服务账本上，并不是一批“硬币文件”藏在电脑中。钱包取证先回答三个问题：设备保存过哪些账户或地址、留下了哪些操作痕迹、现有材料是否足以证明具备某种签名能力。三者需要不同证据。

| 对象 | 用途 | 取证结论的边界 |
| --- | --- | --- |
| 地址 | 标识收款目标或链上账户；格式随链与脚本类型变化 | 地址可被复制、导入、收藏或监看，不独立证明控制权 |
| 公钥 / 扩展公钥 | 验证签名；扩展公钥可派生范围内的非强化子公钥 | 能列出地址不等于能签名；扩展公钥仍有隐私风险 |
| 私钥 / 扩展私钥 | 为相应密钥或派生子树提供签名能力 | 需确认链、路径、用途与保护状态；不得在报告或网页展示真实值 |
| 助记词与 seed | 按特定标准生成密钥树的备份材料 | 还需确认 passphrase、派生路径、网络和索引；不同产品未必使用同一标准 |
| 加密 keystore / vault | 保存受口令保护的秘密或 keyring 数据 | 文件存在不代表已解密；字段识别不证明口令正确 |
| 仅观察钱包 | 跟踪公开地址、脚本或扩展公钥 | 可显示余额与交易，但通常不具备相应私钥 |
| 硬件钱包账户 | 由外部设备保存秘密并完成签名 | 电脑侧可能只有公有账户、派生路径和连接信息 |
| 标签、备注、账户名 | 用户或软件给记录赋予的本地名称 | 可修改、同步或导入；不是链上实名，也不证明操作者身份 |

交易所应用的登录账户还可能只对应托管服务账户。发现登录记录、充值地址或资产页面，不应直接解释成设备存有链上私钥。智能合约账户、多签和外部签名器也不能简化为“一个地址对应一份本地私钥”。

## 02 找到正确的钱包实例和版本

### 02.1 Bitcoin Core

先固定程序版本、操作系统账户、运行配置、网络和数据目录。Linux 常见数据目录为 `~/.bitcoin/`；Windows 较新版本常见 `%LOCALAPPDATA%\Bitcoin\`，历史版本还可能使用 `%APPDATA%\Bitcoin\`；macOS 常见 `~/Library/Application Support/Bitcoin/`。自定义数据目录、钱包目录、启动参数和配置会改变位置。

命名钱包常见于 `<datadir>/wallets/<钱包名>/wallet.dat`；默认钱包可在 `wallets/`，旧布局也可能直接放在数据目录中。测试网络、signet 和 regtest 使用各自子目录。`wallet.dat` 只是常见文件名，不能凭后缀确认数据库类型。

| 线索 | 优先保全 | 判读 |
| --- | --- | --- |
| 现代 descriptor 钱包 | 钱包目录、`wallet.dat` 及存在的 SQLite 日志 | descriptor 描述脚本及派生规则，可使用公钥或私钥材料 |
| 历史 legacy 钱包 | `wallet.dat`、`database/`、`db.log`、相关锁文件与版本信息 | 常见 Berkeley DB；不要直接当 SQLite 读取 |
| 多钱包或迁移 | 所有对应钱包目录及备份，原配置和迁移时间 | 迁移可能分出 watch-only 或 solvable 钱包，名称不能代替内容检查 |
| 节点数据 | `blocks/`、`chainstate/`、索引及日志 | 区块与 UTXO 数据不等同本机钱包私钥，也不证明本机发起交易 |

较新 Bitcoin Core 版本以 SQLite descriptor 钱包为主，历史 legacy 钱包的支持范围已经变化。不要把旧钱包交给最新版程序直接加载、迁移或重扫；这些操作会改变工作状态，且可能根本不支持该格式。确有版本复现实验时，在隔离环境使用额外实验副本。

已经获准运行的实验实例可用 `getwalletinfo` 查看 `format`、`descriptors`、`private_keys_enabled`、`external_signer` 和处理到的区块。`private_keys_enabled=false` 表示该钱包禁用私钥；`descriptors=true` 只说明脚本管理方式；`external_signer=true` 表示配置了外部签名器。不要仅凭一个字段推断所有历史钱包的密钥内容。

```bash
# 只用于已隔离、已加载实验副本的本地实例；不是首轮采集步骤
bitcoin-cli -rpcwallet='lab-wallet' getwalletinfo
bitcoin-cli -rpcwallet='lab-wallet' listlabels
bitcoin-cli -rpcwallet='lab-wallet' getaddressesbylabel 'example-label'
```

标签与地址的映射支持“该实例记录过这个名称和地址”的结论。标签可以对应收款或发送目的地址，不能单凭标签认定地址属于本机、钱包所有者或某个实名主体。锁定钱包仍可能公开地址和交易信息；加密保护的重点与元数据可见性需要分别核对。

### 02.2 Ethereum Web3 keystore

识别 JSON 内容而不是只搜扩展名。Web3 Secret Storage V3 的路径约定与具体客户端数据目录不同；例如 Geth 的 Linux 常见路径为 `~/.ethereum/keystore/`，Windows 较新版本为 `%LOCALAPPDATA%\Ethereum\keystore\`，历史配置可能不同。`UTC--时间--地址` 样式名称是线索，不证明创建时间、当前余额或操作者。

V3 keystore 通常保护一个私钥，不应自动当作 HD 钱包全部账户的备份。记录 `version`、`id`、存在时的 `address`、加密字段与 KDF 参数。`address` 在部分实现中存在，但不是所有 V3 文件必须具备的字段；它即使存在也不能替代密码学验证。

### 02.3 MetaMask 浏览器扩展

先确认浏览器、配置目录、扩展 ID、扩展版本和安装渠道。Chromium 系浏览器常见线索为：

```text
<浏览器用户目录>/<Profile>/Extensions/<扩展ID>/<版本>/manifest.json
<浏览器用户目录>/<Profile>/Local Extension Settings/<扩展ID>/
<浏览器用户目录>/<Profile>/Preferences
<浏览器用户目录>/<Profile>/Secure Preferences
```

Chrome 常见 MetaMask 扩展 ID 为 `nkbihfbeogaeaoehlefnkodbefgpgknn`。Linux Chrome 用户目录常见 `~/.config/google-chrome/`，Windows 常见 `%LOCALAPPDATA%\Google\Chrome\User Data\`；`Default`、`Profile 1` 等分别是不同实例。其他浏览器、商店和开发构建的 ID 与路径可能不同，必须结合 manifest 和浏览器配置确认。Firefox 的扩展 UUID、存储后端和编码方式也不同，不套用 Chromium 的固定目录。

关注扩展本地存储、历史记录、下载记录、已连接站点、网络配置、账户列表、交易元数据和备份。`KeyringController`、`vault` 是定位候选结构的关键词。发现多个 vault 或同一账户的旧状态时，保留各自文件、偏移和版本；不能将字符串搜索的最后一个命中视为当前有效数据。

## 03 首轮只读保全：取得整批材料再解析

以下以已采集、已只读挂载且状态稳定的目录为输入。不要将未知钱包导入日常联网钱包软件；需要加载的验证只在隔离环境使用额外实验副本。原设备仍在运行时，先记录进程和状态，并按采集方案处理易失数据；之后再关闭浏览器或钱包写入者，或取得一致的文件系统快照。关闭程序可能提交、checkpoint 或清理日志，必须记录影响。对运行中的目录逐个复制，即使每个文件都有哈希，也不能证明它们来自同一个数据库状态。

```bash
umask 077
case_dir="$PWD/wallet-case"
src='/mnt/evidence/home/user/.config/google-chrome/Profile 1'
test ! -e "$case_dir" || { echo '目标目录已存在，请使用新的采集目录'; exit 1; }
mkdir -p "$case_dir"/{preserved,work,notes}
date -u +%FT%TZ > "$case_dir/notes/acquired-at.txt"

# src 必须是稳定只读材料；整个配置目录包含扩展、历史与配置关联
find "$src" -xdev -type f -printf '%P\t%s\t%T@\n' \
  | LC_ALL=C sort > "$case_dir/notes/source-files.tsv"
(cd "$src" && find . -type f -print0 | LC_ALL=C sort -z \
  | xargs -0 -r sha256sum) > "$case_dir/notes/source.sha256"
cp -a -- "$src" "$case_dir/preserved/browser-profile"
(cd "$case_dir/preserved/browser-profile" && find . -type f -print0 \
  | LC_ALL=C sort -z | xargs -0 -r sha256sum) \
  > "$case_dir/notes/copy.sha256"
diff -u "$case_dir/notes/source.sha256" "$case_dir/notes/copy.sha256"
cp -a -- "$case_dir/preserved/browser-profile" "$case_dir/work/browser-profile"
```

`diff` 无差异支持这些常规文件的字节副本一致，不能独立证明采集时间一致、原设备内容完整或历史行为真实。镜像、采集报告、目录元数据和缺失项仍需保全。路径中的符号链接、容器映射、挂载点或另一个配置目录要单独审查，不能默认都被普通文件清单覆盖。

### 03.1 SQLite 主库、WAL 与 SHM

同批次保留主库和存在的 `-wal`、`-shm`、回滚日志。WAL 可能包含尚未 checkpoint 到主库的已提交状态；主库单独复制会丢失这些内容。SHM 是协调与索引文件，可重建，但有则保全；不要制造空 SHM 或拿另一次采集的同名日志补上。

`mode=ro` 或 `-readonly` 限制数据库写入，不等于分析目录内绝无辅助文件变化。SQLite 在一定条件下会创建或使用 SHM。`immutable=1` 会跳过锁与变更检测，只适用于确实不会变化的稳定材料；用它强行读取活动库可能得到错误结果。

```bash
# app.db 与同批次存在的 app.db-wal / app.db-shm 已放入 work/sqlite/
# 本连接只在可写的实验目录运行，输出为新快照；preserved 中的文件不打开
sqlite3 work/sqlite/app.db '.backup work/sqlite/snapshot.db'
sqlite3 -readonly work/sqlite/snapshot.db 'PRAGMA integrity_check;'
sqlite3 -readonly work/sqlite/snapshot.db \
  "SELECT type,name FROM sqlite_schema WHERE type IN ('table','index');"
```

建立快照会得到派生查询对象，不能代替原始 WAL 历史。不要在唯一检材上执行 `VACUUM`、`PRAGMA wal_checkpoint`、修复或删除日志。Bitcoin Core SQLite 钱包常见回滚日志，不应预设每份 wallet.dat 都使用 WAL。数据库结构和历史页判读见[SQLite 与 WAL](/knowledge/forensic-sqlite/)。

### 03.2 LevelDB 必须保全整目录

LevelDB 数据由目录内多种文件共同表示：`CURRENT` 指向 MANIFEST；MANIFEST 记录表集合及版本；编号 `.log` 保存写入日志；`.ldb` 或 `.sst` 保存排序表；`LOCK`、`LOG`、`LOG.old` 等提供状态与诊断线索。只拿一个 `.log`、`.ldb` 或含 vault 字样的文件，可能缺少有效状态和关联记录。

复制时保留整目录和所有实际存在的文件，确保写入者已停止或输入是一致快照。不要对 preserved 目录用普通 LevelDB 库直接打开：恢复过程可能创建新日志、重建表、清理旧文件或删除过期文件。解析器需要明确支持所用 Chromium/LevelDB 变体；缺少 Snappy、键值编码或版本支持时，记录失败条件。

```bash
# 只列候选文件名，不把 vault 或其他秘密内容打印到终端
rg -a -l -- 'KeyringController|"vault"|"ciphertext"' \
  'work/browser-profile/Local Extension Settings'
```

上述搜索不解析 LevelDB 的序列号、删除标记和有效版本，只用于分诊。压缩块、分片记录和转义 JSON 可造成漏检；命中也可能属于旧记录或缓存。后续解析应保留表文件、记录偏移、序列号、状态以及结构完整性。

## 04 只读识别 keystore 与 vault

### 04.1 Web3 Secret Storage V3 字段

| 字段 | 作用 | 检查 |
| --- | --- | --- |
| `version`、`id` | 格式版本和文件标识 | V3 的 version 为数值；UUID 不是密码或私钥 |
| `crypto.cipher` | 对称算法声明 | AES-128-CTR 是 V3 最低支持要求，不凭后缀固定算法 |
| `cipherparams.iv` | 初始向量 | 校验编码与字节长度；IV 不等于口令 |
| `ciphertext` | 加密的秘密字节 | 先校验编码与完整长度，不输出内容 |
| `kdf`、`kdfparams` | 口令到密钥的派生参数 | PBKDF2 常见 `c/prf/dklen/salt`；scrypt 常见 `n/r/p/dklen/salt` |
| `mac` | 校验派生密钥与密文的对应关系 | V3 使用 Keccak-256，不能替换成 NIST SHA3-256 |

V3 的 MAC 关系为 `Keccak-256(DK[16:32] || ciphertext)`，AES-128-CTR 常用 `DK[0:16]` 作加密密钥。这里只描述验证关系；不得在联网网页提交真实 keystore、候选口令或解出的密钥。MAC 不覆盖所有外层备注字段，也不是用户身份签名。

下面只读结构，输出字段名与编码长度，不解密、不打印密文或密钥。输入可用合成教学 JSON；真实材料应保留于本地受控目录。

```python
import json
from pathlib import Path

obj = json.loads(Path('work/keyfile.json').read_text(encoding='utf-8'))
crypto = obj.get('crypto', obj.get('Crypto'))
if obj.get('version') != 3 or not isinstance(crypto, dict):
    raise ValueError('未确认是本例支持的V3对象')
print('version=', obj['version'], 'has_address=', 'address' in obj)
print('cipher=', crypto.get('cipher'), 'kdf=', crypto.get('kdf'))
print('kdf_parameter_names=', sorted(crypto.get('kdfparams', {})))
for label, value in (
    ('iv', crypto.get('cipherparams', {}).get('iv')),
    ('ciphertext', crypto.get('ciphertext')),
    ('mac', crypto.get('mac')),
):
    if not isinstance(value, str) or len(value) % 2:
        raise ValueError(f'{label}不是完整的偶数长度hex字段')
    print(label + '_bytes=', len(bytes.fromhex(value)))
```

大小写兼容仅便于识别部分实现，不能自动证明格式合规。结构检查通过不说明文件来自指定用户、口令命中或 MAC 正确。若字段属于验证者 keystore 等其他版本，重新识别对应格式，不套 V3。

### 04.2 MetaMask vault 的平台与版本差异

浏览器扩展的常见加密封装含 Base64 `data`、`iv`、`salt`，较新封装还可能含 `keyMetadata`。上游浏览器加密实现使用 PBKDF2 与 AES-GCM，并存在旧参数兼容分支。取证记录应保存 payload 中的算法与迭代元数据、扩展版本和相关实现，不能把某个历史迭代数当作所有 vault 的常量。

手机 vault 可能采用 `cipher`、`iv`、`salt`、`lib`、`keyMetadata` 等另一套封装。不要把手机的 `cipher` 字段改名为浏览器 `data` 后就视为同一算法，也不要通过删掉未知元数据“兼容”工具。外层 JSON 中的 vault 还可能是一段经过转义的 JSON 字符串：应逐层正常解析，而不是全局删除反斜线。

vault 可以包含软件 HD 账户与导入账户的秘密，硬件账户的地址和连接记录则不证明相应私钥存于该电脑。应从 keyring 类型、账户来源和版本确认范围；“看见地址”“识别加密封装”“能够离线验证秘密材料”分别记录。

## 05 助记词、派生路径与校验的不同层次

### 05.1 从词到地址

```text
产品备份格式 / BIP39单词与顺序
    → entropy与checksum检查
    → mnemonic + passphrase生成seed
    → BIP32密钥树
    → 已确认purpose / coin_type / account / change / index
    → 对应链与脚本类型的地址
```

BIP39 的常见合法词数为 12、15、18、21、24。单词属于词表不等于组合有效；checksum 通过只说明词序符合校验条件，不证明命中目标钱包。BIP39 passphrase 参与 seed 生成，换一个 passphrase 仍会得到有效 seed，不能靠 checksum 检出“passphrase 错误”。它与钱包解锁口令、手机 PIN、备份密码不是同一种参数。

BIP32 区分扩展私钥和扩展公钥；公钥派生仅支持相应非强化分支。路径中 `'` 或软件使用的 `h` 常表示强化派生。扩展公钥可以暴露派生地址关系，仍应避免公开真实 xpub；它不直接具有签名能力。不能从“只保存公钥”推断完全没有敏感信息。

### 05.2 常见 Bitcoin 路径结构

| 约定 | 典型主网首账户首外部地址路径 | 常见脚本类型 |
| --- | --- | --- |
| BIP44 | `m/44'/0'/0'/0/0` | P2PKH |
| BIP49 | `m/49'/0'/0'/0/0` | P2WPKH 嵌套在 P2SH |
| BIP84 | `m/84'/0'/0'/0/0` | 原生 P2WPKH |

通用层级为 `m/purpose'/coin_type'/account'/change/address_index`。上述三条只展示约定，不能强套到未知钱包。测试网络 coin_type、其他币种、硬件产品、账户索引、自定义路径、Taproot 或 multisig 都可能不同。地址前缀不能独立证明完整路径；descriptor 中的脚本表达式、密钥来源与路径信息更有助于确认范围。

BIP44 的 change 常用 `0` 表外部收款、`1` 表内部找零，发现算法还涉及账户与地址 gap。恢复界面没显示某个账户，不证明它不存在；余额为零也不等于没有历史交易。记录实际软件采用的发现范围，不把一种钱包的自动恢复行为当作所有钱包标准。

助记词片段排序、checksum 和有界候选验证继续见[密码学取证的助记词验证流程](/knowledge/fic-case-08/)。本专题只补充钱包实例、账户来源、派生范围和证据归属，不重复口令搜索命令。

### 05.3 核对密钥树的范围

分层确定性（HD）钱包，是从一份种子按固定规则生成整棵密钥树的钱包。某账户的 xpub 只是树中一个节点；它的深度、后续分支和脚本类型共同决定能观察哪些地址，不能自动覆盖其他账户。

从备份、账户来源和 descriptor 中整理 `网络 / 根来源 / 路径 / 分支 / 索引范围 / 脚本类型`，再离线比对已知公有地址。BIP39 的 NFKD 是统一等价 Unicode 字符表示的规则；保留原始字符，勿擅自删空格、改大小写或翻译词表。passphrase 只记录“为空、已知或未知”等条件。匹配一个地址仅验证该路径的对应关系；小范围没有命中不证明整个钱包不存在。短密钥指纹只适合快速关联，可能碰撞，不能替代完整公钥和路径核对。

## 06 手机钱包：本地数据、缓存与备份分别核对

优先保存应用标识、版本、Android 用户/工作资料/虚拟实例、iOS 容器映射、备份采集时间和实际取得范围。Android 常见候选包括应用私有 `files/`、`databases/`、`shared_prefs/`、WebView 存储和缓存；iOS 包括应用容器的 `Documents/`、`Library/` 及备份映射。包名相同不代表属于同一用户、同一钱包或同一安装时期。

部分 MetaMask 手机版本或备份可在 `Documents/persistStore/persist-root` 找到持久状态及 `KeyringController` 线索。此路径只能作为定位候选，不能承诺所有 Android/iOS 版本均采用它。缓存、WebView LevelDB、请求记录和交易元数据可补充地址、网络、交易哈希和 dApp 访问线索，但它们可能过期或由服务端同步而来。

| 材料 | 可以支持 | 不能直接推出 |
| --- | --- | --- |
| 账户列表、地址与名称 | 应用实例保存或显示过相关账户 | 本机保存私钥、账户真实归属、已发生转账 |
| 网络、RPC、代币配置 | 该实例采用过的连接与显示条件 | 余额实时、已成功广播或交易最终确认 |
| 交易状态与哈希缓存 | 可关联本地请求和链上候选交易 | pending/failed 状态对应最终链上结果 |
| 截图、二维码、通知 | 地址或付款线索与时间候选 | 二维码必为私钥；通知必是本人操作 |
| 系统备份、云同步和导出文件 | 某时间点留下的独立副本 | 当前设备全部材料都在备份内、硬件绑定密钥可迁移 |

备份有自己的时间和加密条件。iOS 备份口令、系统钥匙串条件、手机解锁条件和钱包口令分别记录；Android 应用备份策略或设备绑定密钥可能限制可恢复范围。拿到应用 JSON 不等于拿到系统保护密钥，拿到缓存也不等于拿到钱包秘密。

传统 SRP 恢复、导入私钥/JSON、硬件账户、其他 SRP，以及较新登录创建方式和 Backup and sync 功能可能使用不同的恢复逻辑。不要固定写成“恢复助记词会恢复所有账户”或“只会恢复第一个账户”。检查账户来源、版本与功能状态，并将自动恢复缺失和密钥材料缺失分开。

## 07 实战：四个需要分别验证的场景

### 07.1 显示余额的仅观察钱包

**材料与目标：** 离线取得 Bitcoin 钱包目录、版本配置和某地址的余额截图，目标是确定设备保存的内容与具备的能力。

1. 保全所有钱包目录，按文件头、版本和配置区分 SQLite descriptor 与历史 BDB 钱包。
2. 从解析得到的 descriptor、密钥类型与标志确认是否只有公开材料。实验副本若使用本地 RPC，分别记录 `private_keys_enabled`、`descriptors`、`external_signer`。
3. 将截图地址与 descriptor 派生范围、本地交易记录和网络关联；标签单独保存，不把名称变成实名。
4. 记录已知缺口，例如没有私钥、签名设备未取得、没有当前链状态或缺失日志。

**示例判读：** 钱包禁用私钥，descriptor 使用公开材料，保存了地址和交易记录。可以报告该实例追踪过相关脚本或地址；截图余额不证明本机可签名，也不证明截图中的资产在采集时仍存在。

### 07.2 扩展 LevelDB 中出现多个 vault

**材料与目标：** 同批次取得 Chromium 配置目录，多个文件出现 vault 候选，目标是确定当前与历史状态，关联账户和应用行为。

1. 用 manifest、Preferences 和目录确认扩展实例、版本与配置账户，不只按固定 ID 搜索。
2. 在完整 LevelDB 工作副本上解析，记录候选所在文件、偏移、序列号、删除状态和封装完整性。字符串搜索仅标记候选文件。
3. 逐层解析外层状态与内层 JSON，记录加密字段、keyMetadata 和 keyring 类型；不在输出中展示 vault 全文。
4. 与账户列表、网络配置、历史及备份关联。密码条件未成立时停在结构和上下文，不宣称解出助记词。

**示例判读：** 一个候选来自已删除的旧记录，另一候选属于解析器还原的当前状态。两者分列为历史候选与当前封装；“旧 vault 存在”不等于“旧钱包仍在使用”，也不等于“能够恢复其中秘密”。

### 07.3 手机备份中的地址与待处理交易

**材料与目标：** 取得一个手机应用备份、请求缓存与交易状态，目标是核对地址来源和交易是否完成。

1. 用容器映射和备份时间确认实例，区分主库、WAL、缓存及旧备份；将账户来源与恢复方式分列。
2. 保存原始 chain/network 信息、交易哈希、地址、数额原始单位、nonce、状态和原始时间值。
3. 用同链的区块、receipt 或其他已取得的链上材料验证交易归属及执行结果。链上查询如获准使用公开服务，只提交公有标识，不发送 keystore、vault、助记词或密钥。
4. 区分请求构建、请求发送、签名、广播、pending、失败和最终确认；余额缓存与成功交易分别核对。

**示例判读：** 备份缓存记录交易为 pending，取得的同链 receipt 表明执行失败。可以报告本地曾保存该交易候选与对应链上失败结果，不能统计为成功付款。若只有请求或截图，则保留未能验证的状态。

### 07.4 分散的备份片段与对象地址线索

**材料与目标：** 图库图片、分身或虚拟 Android 实例、备忘录以及 Anytype 等对象笔记中出现钱包相关线索，目标是确认备份片段之间的关系，并与已有公有地址关联。

1. PNG 无法显示时，先核对完整 PNG 结构、IHDR 的宽高及 CRC。修复只写入副本，记录准确偏移、前后值和哈希，再验证整图可解码；宽高恢复成功不证明图片中的词来自目标钱包。
2. 从宿主用户、分身包名、虚拟实例映射进入第二套 Android 存储，分别保存图库、应用数据、导入文件和备份目录。不能用外层账户或第一套实例的数据代替内层目标。
3. 备忘录名称与内容不符时，检查文件头、尾部和真实文档结构，再解析隐藏或附加的完整内容。`.doc` 名称不保证内容是传统 Word 二进制，也不能只从最后几个可打印单词断定词序。
4. 对三段词先记录每段位置、段内顺序和 OCR 置信度，再用已证实约束检查 BIP39 checksum。多个排列都通过校验时，需要目标钱包的网络、passphrase、派生路径与已知地址继续验证；具体离线流程见[助记词片段与地址验证](/knowledge/fic-case-08/)。
5. 对象笔记中的地址若经过多层编码，逐层记录输入、编码类型、输出字节与判断依据，不凭“可读了”就停止。关联对象 ID、当前值、历史版本和原始时间字段，区分地址被粘贴、页面创建、页面更新与钱包首次使用。

**示例判读：** 某词序通过 checksum，且在确认路径下派生出已知地址，可以报告备份候选与该地址的派生关系匹配。笔记对象早于某次更新保存了同一地址，只能支持地址曾在相应对象中出现；地址页创建时间不等于钱包建立时间，页面拥有者也不自动等于地址控制者。缺少 passphrase 或路径时保留验证缺口，不把 checksum 通过写成钱包已恢复。

## 08 离线练习与结论记录

练习一：用合成 V3 JSON 调整字段、hex 长度、KDF 参数和 version，运行本页只读结构脚本。观察“可解析 JSON”“符合候选结构”和“密码学验证成功”的区别。全部零值只适合教具，不是可用钱包。

练习二：使用公开 BIP39 测试向量，在离线环境比较无 passphrase 与指定 passphrase 的 seed；记录 NFKD、词数与 checksum。仅打印匹配布尔值，避免把真实助记词或派生秘密复制到命令行、日志、截图或在线工具。公开向量用于验证算法实现，不能接收实际资产。

练习三：在全新实验目录创建教学 SQLite 数据库，使记录只存在于已提交 WAL 状态，再比较主库单独副本与同批次主库加日志副本。练习完成后保留各对象哈希和观察结果；不要对真实钱包制造 checkpoint 来验证现象。LevelDB 练习先比较整目录清单与故意缺少文件的副本，不用不完整结果作历史结论。

本页公开 BIP39 测试向量的 PBKDF2 结果、零熵 checksum 和 passphrase 差异做过离线核对；钱包附件、扩展数据库、手机备份和上述采集命令未据真实检材复跑。格式识别、数据库完整性检查和测试向量匹配，都不能代替真实钱包与账户关系的验证。

结论至少记录：`采集对象与范围 / 实例与版本 / 原始路径 / 文件哈希 / 数据库批次与状态 / 记录偏移或主键 / 公有地址与网络 / 账户来源 / 已确认派生范围 / 操作与链上结果 / 缺失材料与限制`。涉及秘密的值只存于受控证据材料，公开正文使用材料标识。分别写明“发现过地址”“记录过交易”“材料通过离线验证”“具备何种签名条件”，不要将其中任一项扩大成身份、资产归属或已经发生的支付行为。

## 09 硬件、多签与合约钱包的控制条件

硬件钱包说明密钥在哪里使用，多签说明需要哪些授权，链上账户类型说明如何执行操作；三者可以组合。外部账户（EOA）由私钥签名驱动；智能合约钱包按链上程序设定的授权规则执行，并不存在一把直接对应合约地址的普通私钥。

| 类型 | 材料位置与核对 | 可支持的判断 |
| --- | --- | --- |
| 普通 EOA | 本地账户来源、公钥、既有签名 | 公钥与地址、原消息与签名匹配；不能据此确定实际操作者 |
| 硬件账户 | 密钥管理器类型、设备连接记录、派生路径 | 电脑侧可保留公开材料；连接过设备不证明本机存有私钥或已完成签名 |
| Bitcoin 阈值多签 | descriptor、花费规则脚本、参与公钥 | 例如三把公钥需两份有效签名；一份密钥只对应其中一个签名条件，须核对完整脚本 |
| Safe 合约钱包 | 指定历史区块的合约、授权者名单与所需确认数量 | 还需检查额外执行入口（module）与执行检查（guard）；名单中出现一个账户不等于可独立转出 |

观察钱包也可能构建交易、接收外部签名再广播，界面有“转账”按钮并不改变密钥所在位置。验证时只分析已取得的材料和只读历史状态，不调用真钱包签名或转币。

合约可按 ERC-1271 接口判断既有签名是否被接受；结果可能依赖区块时刻的状态，不能用当前验证替代历史验证。支持 EIP-7702 的网络允许 EOA 委托代码执行，因此“地址有代码”不足以断定它是普通合约账户；同时核对网络、区块与委托目标。

## 10 DApp 连接与签名不等于付款

DApp 是与区块链交互的应用。先在扩展权限、访问记录和请求缓存中关联站点、账户、网络与时间，再区分请求种类：

| 痕迹 | 判读与验证 |
| --- | --- |
| `eth_requestAccounts` | 请求账户访问权限；结合成功响应核对获准账户，不代表转账授权 |
| `personal_sign` | 对消息加特定前缀后签名；保留原始字节，按对应规则验证既有签名 |
| `eth_signTypedData_v4` | 对带类型结构的数据签名；保留字段类型 types、主类型 primaryType、适用域 domain 与内容 message，不把 JSON 文本直接当作签名消息 |

签名请求、签名返回、链上使用分别记录；返回签名也可能来自外部设备。结构化消息的域用于限定适用环境，核对其中实际存在的链编号 chainId 和验证合约地址，不能自行补入缺失字段。Permit 是以签名设置代币使用额度的授权，需核对使用方、额度、授权序号与到期条件；第三方可提交既有授权，故“消息签名无需本机支付手续费”不等于没有资产影响。最终是否授权或付款，仍按对应合约的执行结果核对，不能只凭弹窗或签名缓存判断。
