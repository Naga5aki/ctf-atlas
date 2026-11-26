---
title: 凭据与加密数据：密钥定位和只读验证
summary: 区分账户哈希、DPAPI、磁盘容器和文件加密，优先关联密钥材料，再验证解密结果。
module: Forensics
track: 综合取证
topic: 密码与资金
tags: [文件格式]
status: 已整理
sourceIds: [web-goodlunatic-761da51, web-hello-memory, web-forensics-wiki]
relatedIds: [forensic-memory, disk-evidence, forensic-browser, forensic-registry]
updated: "2026-10-15"
---
## 01 先识别保护层和材料

| 检材 | 优先寻找 | 判断边界 |
| --- | --- | --- |
| 本地 Windows 账户 | 同机 `SAM` + `SYSTEM`，必要时 SECURITY | 常见 NT 哈希不是明文，也不是简单 MD5 |
| 域账户 | `ntds.dit` + 同机 `SYSTEM`，事务日志及备份 | 输出哈希后还需按格式做口令验证 |
| LSASS 转储 | 有效 minidump、系统版本和架构 | 完整物理内存、进程 memdump、minidump 不能当作同一格式 |
| DPAPI 数据 | SID、Protect 主密钥目录、账户/机器相关凭据材料 | 搬到另一台机器并不自动可解密 |
| BitLocker | 恢复密钥、BEK、磁盘元数据、匹配内存 | 缺少可用密钥时不能称“已解密” |
| VeraCrypt / TrueCrypt | 密码、keyfile、PIM、容器/分区信息 | 同一容器可能有外层与隐藏卷 |
| EFS | 文件 DDF/DRF、证书、私钥及其保护信息 | 仅有 NTFS 文件或登录密码可能不足 |
| EncFS | 加密目录、`.encfs6.xml` 和密码 | 配置缺失会影响文件名与内容解密 |
| GPG/PGP | 私钥、口令，或对称口令 | 导入公钥不能解开仅私钥可解的数据 |

与目标数据对应的口令线索可从聊天、备忘录、文件名、配置、历史命令、截图或内存关联得到。先核对对应账户与时间，再进行有条件的离线口令搜索；候选密码命中必须用实际目标验证。

## 02 Windows 账户与进程转储

以下只处理已取得的磁盘账户材料离线副本，SAM/SYSTEM 与域数据库是不同输入范围：

```bash
impacket-secretsdump -sam SAM -system SYSTEM LOCAL
impacket-secretsdump -system SYSTEM -ntds ntds.dit -history LOCAL
```

输出中的用户名、RID、LM/NT 哈希、密码历史需分别记录。LSA 机密和缓存域凭据有不同格式，不可统一以一个模式破解。SAM 账户列表不直接给出明文密码。

有效 LSASS minidump 的格式核验、pypykatz 与匹配 Windows 环境中的离线 Mimikatz 操作集中于[内存对象与凭据恢复](/knowledge/forensic-memory-recovery/)。完整物理内存、普通进程页与 minidump 不可互换，Vol2 memdump 不会自动生成 minidump；Windows 版本、凭据保护、缺页与采集时点影响结果，不保证取得明文。

## 03 Linux 密码哈希

账户列表在 `/etc/passwd`，现代系统的口令哈希通常在 `/etc/shadow`；锁定、空值或 `!`/`*` 需区分。以哈希前缀确定算法，不按用户名或系统版本猜模式。

```bash
hashcat -m 1800 -a 0 sha512crypt.hash candidates.txt
hashcat -m 500 -a 0 md5crypt.hash candidates.txt
```

上面分别适用于 `$6$` sha512crypt 和 `$1$` md5crypt，不能用于所有 shadow 字段。带用户名时按工具要求整理输入或使用相应参数；保留 salt、rounds 与原始行。记录候选集、命中和实际登录/解密验证，避免用 `--force` 掩盖运行问题。

## 04 DPAPI 与 EFS

DPAPI 通常将敏感数据保护与用户或机器上下文绑定。用户主密钥常见于 `AppData/Roaming/Microsoft/Protect/<SID>/`；凭据管理器、Vault、浏览器、部分无线配置和证书私钥可能依赖它。

工作步骤：识别 DPAPI blob 的主密钥 GUID → 对应 Protect 文件 → 核对 SID 与密码/哈希等解密条件 → 解开主密钥 → 解目标 blob → 验证结构和用途。`DPAPImk2john.py` 等转换器的名称和参数依所用 John 版本确认；它转换可校验的材料，不是把任意加密文件自动还原明文。

EFS 是文件级加密，`cipher` 属于 Windows EFS 工具，不是独立的磁盘加密算法。保存加密文件及 NTFS 元数据、证书和私钥材料；可用 Advanced EFS Data Recovery 等匹配工具分析。仅复制普通内容流可能丢失 EFS 属性和恢复所需元数据。

工具里若同时看得到原文件和同名的 `FileSlack` 项，并且文件带系统加密属性，这是 EFS，加密绑定当前账户证书。仿真登录时使用原密码。强制改密后，DPAPI 主密钥无法用原登录密码解开，EFS 证书私钥随之失效。离线可从 `SAM` 和 `SYSTEM` 提取 NTLM，再用 hashcat `-m 1000` 撞字典。**【仅在副本/仿真/授权环境执行】**用还原出的原密码登录后，`cipher /d /s:<目录>` 递归解密，`/d` 是解密，`/s` 包含子目录。解开 EFS 后若字段仍由同目录脚本加密，密钥和 IV 从该脚本读取。

## 05 BitLocker、VeraCrypt 与 TrueCrypt

### 05.1 BitLocker

确定被保护的分区而不是只看 E01 后缀。先查恢复密钥、外部密钥文件和备份；有同时间段完整内存时，按[内存密钥候选与目标验证](/knowledge/forensic-memory-recovery/)定位；本页继续核对卷与派生镜像。

记录密钥类型、检出位置、对应卷 ID、解密工具与输出镜像哈希。Passware 的密钥扫描与密码字典搜索是不同过程。挂载成功后继续验证分区、文件系统和目标文件；不能根据软件进度条认定数据完整。

### 05.2 VeraCrypt

在工作副本选择容器、未占用盘符/挂载点及只读挂载选项，核对密码、PIM 和 keyfile。图片等任意文件可以充当 keyfile，但文件字节必须一致。失败时先查材料和卷类型，不通过改密、修复或格式化来尝试取证。聊天或文档指定的密钥文件，挂载时读的是文件字节。快捷方式就选中那个 `.lnk` 本身。比较哪个更小时用文件长度，不用按簇对齐的占用空间。外层文件头若是 `50 4B 03 04`，先按 ZIP 解开，再判断里面是不是容器。

同一容器在不同有效密码组合下可能分别进入外层卷和隐藏卷。记录每次挂载得到的卷大小、文件系统、目录与使用材料；外层看起来正常也不排除隐藏卷。

```bash
veracrypt --text --mount --mount-options=ro container.hc /mnt/volume
```

密码应交互输入，具体 PIM/keyfile 参数查看本版帮助。TrueCrypt 兼容模式并非所有新版 VeraCrypt 都提供；VeraCrypt 1.26 系列移除了旧 TrueCrypt 模式，历史 TrueCrypt 容器需明确可兼容版本。不能把“1.19 前后”一律解释成整个加密算法改变。

## 06 EncFS 与 GPG/PGP

EncFS 保全整个加密树及隐藏配置 `.encfs6.xml`，用匹配版本在副本上只读挂载。EncFS4win 可作为 Windows 对应实现，注意路径名、配置版本与输出完整性。

GPG 在独立 keyring 工作，避免把待分析密钥导入日常密钥库。

```bash
mkdir -m 700 gpg-work
gpg --homedir ./gpg-work --import private-key.asc
gpg --homedir ./gpg-work --list-secret-keys
gpg --homedir ./gpg-work --output decrypted.bin --decrypt encrypted.pgp
file decrypted.bin
sha256sum decrypted.bin
```

Kleopatra 提供相应图形界面。区分私钥口令、文件对称口令与签名验证；解密后记录完整性/MDC/认证和签名状态，不能仅凭输出文件出现就宣称来源可信。

## 07 交付与工具选择

Passware Kit Forensic 适合已支持的容器、压缩包和内存密钥分析；findaes 可辅助寻找 AES 扩展密钥候选，需实际解密验证。TrueCrypt 相关 Vol2 插件只支持部分历史版本，缺少命中不等于没有加密。

每个解密结论保留 `密文哈希 / 算法与格式 / 材料标识 / 工具版本 / 参数 / 输出哈希 / 结构验证 / 未解决项`。不要将用户敏感哈希、Token 或密码上传在线破解站。

## 08 实战：确认口令材料对应正确的加密层

**场景与材料：** 取得 Windows 磁盘中的加密容器、同机账户材料和一条可能的口令线索。目标是读取容器内文件；账户哈希、容器口令、DPAPI 主密钥与 EFS 私钥必须先分别标识。

### 08.1 从保护格式开始

1. 固定容器哈希、大小、所在路径和取得范围，用格式元信息及相邻配置确认保护层。高熵文件不必然是 VeraCrypt；也不能扫描一个明文 magic 就认定其不存在。
2. 将口令、keyfile、PIM、恢复密钥等材料与账户、卷 ID 和时间关联。keyfile 要核对完整字节，名字相同不等于密钥材料相同。
3. 在副本上按本页对应流程验证，使用只读选项和未占用挂载点。保存工具版本、错误与成功条件，不更改容器密码或初始化卷。
4. 挂载后检查卷大小、文件系统、目录结构、多个文件的实际可读性和内容哈希；外层卷与隐藏卷分别记录。

### 08.2 解密成功的判据

输出几个可打印字符不构成成功。数据库需可读 schema 与已知记录，压缩包需结构/完整性检查，磁盘需有效文件系统及一致文件内容。解密工具生成的派生镜像哈希通常与密文不同，按输入→材料→输出映射保全。

**示例判读：** 一个账户口令可用于解开某 DPAPI 主密钥，但容器仍无法挂载。可以确认相应 DPAPI 条件成立；容器可能采用其他口令、keyfile、PIM 或格式，不能把账户口令命中扩大成所有数据均已解密。缺少必要材料时保留格式和限制。

搜狗用户词库常见文件是 `sgim_gd_usrbg.bin`，词条为 UTF-16LE。一种布局在偏移 `0x40` 处用 4 字节小端整数指出词条区，其后按长度前缀存放词条。不同版本的间隔和尾部不同。先在样本上对出一条已知词，再把词条导出成字典。`pagefile.sys` 里的界面文字常是 UTF-16LE，UTF-8 和 `strings -e l` 各搜一次，`-e l` 按 16 位小端扫描。
