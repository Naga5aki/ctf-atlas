---
title: "OpenSSL AES加密"
summary: "遇到U2FsdGVkX1...这类密文，不要直接拖一个AES Decrypt然后把密码填进Key。"
module: "Misc"
topic: "文本与编码"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

遇到U2FsdGVkX1...这类密文，不要直接拖一个AES Decrypt然后把密码填进Key。OpenSSL的password模式需要先从「密码+Salt」派生真正的AES Key和IV。当前CyberChef已提供AES Decrypt、Derive EVP key、Derive PBKDF2 key，可以完整处理这类题。

## 一、快速识别

**CyberChef操作：**

Input→From Base64→To Hex

如果输出开头为53616c7465645f5f（ASCII即Salted__），通常可判断为OpenSSL-compatible salted格式。

数据结构

Salted__|8字节Salt|真正AES密文

0~7：Salted__

8~15：Salt

16~末尾：Ciphertext

## 二、解题核心三步

**假设题目给出：**

**密文：** U2FsdGVkX1/nSQN+hoHL8OwV9jlB/mSdKk5dmusulz4=

**密码：** Tokyo

**算法：** AES-256-CBC

①Base64解码并提取Salt、Ciphertext

↓

②Password+Salt派生Key、IV

↓

③AES Decrypt

**第一步：** 提取Salt和真实密文

CyberChef放入From Base64+To Hex，输出类似：

53616c7465645f5f e749037e8681cbf0 ec15f63941fe649d2a4e5d9aeb2e973e

Hex位置换算（1字节=2个十六进制字符）

| Hex字符位置 | 对应内容 |
| --- | --- |
| 前16个字符53616c7465645f5f | Salted__ |
| 接下来16个字符e749037e8681cbf0 | 8字节Salt |
| 之后全部ec15f63941fe649d... | Ciphertext |

把Salt和Ciphertext分别记下来。

**第二步：** 根据密码派生Key和IV

**情况一：** 传统OpenSSL派生（Derive EVP key）

CyberChef搜索Derive EVP key，参数填写：

| 参数 | 值 | 说明 |
| --- | --- | --- |
| Passphrase | Tokyo | 类型：UTF8 |
| Key size | 384 | AES-256-CBC需32B Key+16B IV=48B=384bit |
| Iterations | 1 | 传统EVP派生 |
| Hashing function | SHA256或MD5 | 根据题目/实现选择，老题优先试MD5 |
| Salt | 提取出的8字节Salt | 类型：Hex |

AES-256需要Key=32字节、IV=16字节，因此一次需派生32+16=48字节=384 bit。

把派生结果拆成Key和IV

假设CyberChef输出96个十六进制字符：

前64个Hex字符=AES-256 Key（32字节）

后32个Hex字符=IV（16字节）

**注意：** 一定不要把Tokyo直接填进AES Key。Tokyo是密码，真正的Key是派生后得到的32字节数据。

**第三步：** AES Decrypt

新建CyberChef Recipe，放入AES Decrypt：

| 参数 | 值 |
| --- | --- |
| Key | 派生结果前64个Hex字符，类型：Hex |
| IV | 派生结果后32个Hex字符，类型：Hex |
| Mode | CBC |
| Input | Hex |
| Output | Raw |

Input里只放Ciphertext（去掉Salted__和Salt后剩下的内容）。

CyberChef的AES Decrypt会根据Key长度自动确定AES-128/192/256（16B→128，24B→192，32B→256）；CBC/ECB默认使用PKCS#7 padding。正确的话Output直接出现明文。

## 三、老CTF题重点：MD5

如果密码、AES-256-CBC、Salt、Ciphertext都正确但还是解不开，重点修改Derive EVP key的Hashing function，尝试MD5。很多老OpenSSL/CryptoJS兼容题涉及传统EVP派生。

**Misc记忆：** Derive EVP key，Iterations=1，优先按题目参数；不清楚时重点检查SHA256/MD5。CyberChef当前支持SHA1、SHA256、SHA384、SHA512、MD5。

## 四、题目明确出现PBKDF2时

如果题目出现PBKDF2、-pbkdf2、iterations、iter=10000，不要使用Derive EVP key，改用Derive PBKDF2 key。

参数设置（AES-256-CBC为例）

| 参数 | 值 |
| --- | --- |
| Passphrase | Tokyo，UTF8 |
| Key size | 384（32B Key+16B IV） |
| Iterations | 题目给出的次数 |
| Hashing function | 题目给出的算法，如SHA256 |
| Salt | 提取出的Salt，Hex |

**输出后同样：** 前64 Hex→AES-256 Key，后32 Hex→IV，然后AES Decrypt。

## 五、不同AES-CBC模式的派生长度

| 算法 | Key | IV | 总派生长度 |
| --- | --- | --- | --- |
| AES-128-CBC | 16 B | 16 B | 32 B=256 bit |
| AES-192-CBC | 24 B | 16 B | 40 B=320 bit |
| AES-256-CBC | 32 B | 16 B | 48 B=384 bit |

拆分规则

AES-128-CBC：Key size=256，前32 Hex→Key，后32 Hex→IV

AES-256-CBC：Key size=384，前64 Hex→Key，后32 Hex→IV

## 六、易犯错误

### 1.把密码直接填进AES Key

❌错误：AES Decrypt→Key=Tokyo

✅正确：Tokyo→Derive EVP/PBKDF2 key→真正Key+IV→AES Decrypt

### 2.把整段Salted__数据拿去AES解密

❌错误：Salted__+Salt+Ciphertext整体AES Decrypt

✅正确：只取Ciphertext进行AES Decrypt（前16字节不是密文本体）

### 3.Salt填错

应该填Salted__之后的8字节，不是Salted__本身，也不是整段密文。

### 4.Hex/UTF8类型选错

例如Salt e749037e8681cbf0必须选择Hex，不是UTF8。否则CyberChef会把字符e 7 4 9 0 3...本身当成字节参与计算。

5.Key size只填写256

AES-256-CBC的AES Key确实是256 bit，但需要同时派生Key+IV，因此256+128=384 bit，Derive EVP key的Key size应设为384，不是256。
