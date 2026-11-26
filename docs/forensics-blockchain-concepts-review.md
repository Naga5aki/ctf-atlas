# 区块链核心概念补充核对记录

日期：2026-10-03。范围：Forensics → 虚拟币取证 → 基础与证据。本文为内部维护记录，不进入知识点正文。

## 内容与连续性

在 `forensic-crypto-foundations` 原有正文前加入“区块链核心概念”，共八个小节、11,338 个字符（包含 Markdown、英文与空白，不按中文字数计算）。定义后连接辨析表、构造证据场景和原有操作章节。原六个编号章节继续从01到06，原标题锚点不变；核心概念作为前置阅读段落，不重编原正文。

| 小节 | 内容 |
| --- | --- |
| 00.1 | 区块链、账本与状态：先确定对象是什么 |
| 00.2 | 私钥、公钥、数字签名、地址与keystore |
| 00.3 | 熵、助记词、种子与恢复口令 |
| 00.4 | HD钱包、派生路径与扩展密钥 |
| 00.5 | 钱包类型、账户与控制权 |
| 00.6 | 智能合约、EOA、合约账户与DApp |
| 00.7 | 交易、调用、gas与链状态 |
| 00.8 | 原生币、代币、NFT与链外数据 |

`fic-case-12` 只更新专题导航与检索简述，其01节起的完整资金流正文逐字节保留。基础页原有正文在维护稿与生成稿中分别逐字节保留。其他五篇虚拟币页面、旧核对记录、离线练习、其他模块、原始文件和内容生成器未改。

## 技术核对

- 区块链结构、账本、状态、节点和共识分开解释；哈希链自洽不等于规范网络历史。
- 公钥是椭圆曲线正向运算结果；数字签名不是私钥加密；地址、公钥、签名和秘密容器的证据作用不同。NISTIR8202部分旧表述的私钥加密类比未采用，算法核对使用BIP340。
- BIP39明确熵/校验/词数、2048次PBKDF2-HMAC-SHA512、64字节seed、NFKD与passphrase；校验通过不代表目标钱包命中。不是所有单词备份都按BIP39解释。
- BIP32/44区分节点范围、强化派生、xpub和chain code；父xpub结合已知全非强化后代私钥的风险按适用条件表述。另行导入密钥、软件发现范围与本地标签不能由seed自动覆盖。
- 钱包类型按托管、网络隔离、软件/硬件、观察/签名、多签/MPC及账户规则分维度，秘密共享恢复与阈值计算分别解释。
- 智能合约按EVM代码/状态/调用解释，EOA采用EIP7702的历史规则边界；执行失败不概括为费用、nonce和代码授权均未变化。
- 查询模拟、区块末状态、交易回执和调用过程分开；gas limit与实际结算用量分开；不采用Context7检索片段中的参数强制性作为调用语法。
- 原生币、ERC20/721/1155及资产身份分开；ERC20 decimals可选；预言机真实性、NFT状态、metadata、IPFS完整性与持续可获取分别判断。
- 五个概念名称的加粗范围经实际页面检查调整，最终未显示裸Markdown星号。

## 来源与阅读范围

共29条阅读记录，映射27个内部来源，其中14项为新登记、其余复用既有标识；来源登记关联基础页，原有关联不删除。访问日期均为2026-10-03。优先读取协议、项目文档及NIST报告，历史页面中的版本、市场采用程度和绝对保证不据此泛化。Ethereum JSONRPC页面未成功读取，模拟调用概念通过Context7与当前Geth官方页面核对。未完成的独立编辑复核不记为通过；最终协议与页面核对由主代理完成。

- [NISTIR 8202 Blockchain Technology Overview](https://nvlpubs.nist.gov/nistpubs/ir/2018/NIST.IR.8202.pdf)：00.1, 00.2；范围和采用限制详见同名 JSON。
- [BIP340 Schnorr Signatures for secp256k1](https://github.com/bitcoin/bips/blob/master/bip-0340.mediawiki)：00.2；范围和采用限制详见同名 JSON。
- [Ethereum accounts](https://ethereum.org/en/developers/docs/accounts/)：00.2；范围和采用限制详见同名 JSON。
- [Bitcoin transactions and P2PKH/P2SH conditions](https://developer.bitcoin.org/devguide/transactions.html)：00.2；范围和采用限制详见同名 JSON。
- [Web3 Secret Storage V3 definition](https://ethereum.org/en/developers/docs/data-structures-and-encoding/web3-secret-storage/)：00.2；范围和采用限制详见同名 JSON。
- [BIP39: Mnemonic code for generating deterministic keys](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)：00.3；范围和采用限制详见同名 JSON。
- [BIP32: Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)：00.4, 00.5；范围和采用限制详见同名 JSON。
- [BIP44: Multi-Account Hierarchy for Deterministic Wallets](https://raw.githubusercontent.com/bitcoin/bips/master/bip-0044.mediawiki)：00.4, 00.5；范围和采用限制详见同名 JSON。
- [SLIP39: Shamir's Secret-Sharing for Mnemonic Codes](https://github.com/satoshilabs/slips/blob/master/slip-0039.md)：00.3, 00.5；范围和采用限制详见同名 JSON。
- [Bitcoin Developer Guide: Wallets](https://developer.bitcoin.org/devguide/wallets.html)：00.5；范围和采用限制详见同名 JSON。
- [Ethereum wallets: Buy, Store and Send crypto](https://ethereum.org/wallets/)：00.5；范围和采用限制详见同名 JSON。
- [NISTIR 8214: Threshold Schemes for Cryptographic Primitives](https://nvlpubs.nist.gov/nistpubs/ir/2019/NIST.IR.8214.pdf)：00.5；范围和采用限制详见同名 JSON。
- [NIST Multi-Party Threshold Cryptography Project](https://csrc.nist.gov/projects/threshold-cryptography)：00.5；范围和采用限制详见同名 JSON。
- [What is a hardware wallet?](https://trezor.io/learn/basics/what-is-a-hardware-wallet)：00.5；范围和采用限制详见同名 JSON。
- [Ethereum: Introduction to smart contracts](https://ethereum.org/developers/docs/smart-contracts/)：00.6；范围和采用限制详见同名 JSON。
- [EIP7702: Set Code for EOAs](https://eips.ethereum.org/EIPS/eip-7702)：00.6, 00.7；范围和采用限制详见同名 JSON。
- [Ethereum: Technical introduction to dapps](https://ethereum.org/developers/docs/dapps/)：00.6；范围和采用限制详见同名 JSON。
- [ERC1967: Proxy Storage Slots](https://eips.ethereum.org/EIPS/eip-1967)：00.6；范围和采用限制详见同名 JSON。
- [Ethereum transactions](https://ethereum.org/developers/docs/transactions/)：00.7；范围和采用限制详见同名 JSON。
- [Ethereum gas and fees](https://ethereum.org/developers/docs/gas/)：00.7, 00.8；范围和采用限制详见同名 JSON。
- [Geth eth namespace: eth_call](https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-eth)：00.7；范围和采用限制详见同名 JSON。
- [ERC20: Token Standard](https://eips.ethereum.org/EIPS/eip-20)：00.8；范围和采用限制详见同名 JSON。
- [ERC721: Non-Fungible Token Standard](https://eips.ethereum.org/EIPS/eip-721)：00.8；范围和采用限制详见同名 JSON。
- [ERC1155: Multi Token Standard](https://eips.ethereum.org/EIPS/eip-1155)：00.8；范围和采用限制详见同名 JSON。
- [Ethereum oracles](https://ethereum.org/developers/docs/oracles/)：00.8；范围和采用限制详见同名 JSON。
- [IPFS: Content Identifiers](https://docs.ipfs.tech/concepts/content-addressing/)：00.8；范围和采用限制详见同名 JSON。
- [IPFS: Persistence, permanence and pinning](https://docs.ipfs.tech/concepts/persistence/)：00.8；范围和采用限制详见同名 JSON。

## 实际验收

- 基线341个文件中，仅预期六项修改；335项保持原SHA-256。新增两份核对记录单列。现有170篇知识点、69篇Forensics与71份维护稿的范围保持。
- 完整导入复跑后341项摘要和文件集合相同。导入器会重新扫描本机外部工具目录，带入与内容任务无关的变动；每次导入后均恢复任务开始时的工具清单，工具目录本身未改。
- 数据单元测试57项：56项通过、1项既有工具路径检查失败。原工具清单中的 `D:\CTF_MISC_Tools\Forensics\Inseyets PA` 在当前机器不存在；清单与基线完全一致。没有放宽或跳过该测试，不将全套测试标为通过。
- 最终内容排版调整后，再运行Forensics全部正文与维护稿一致性测试：通过。
- 5项UI测试通过；18文件Astro检查为0错误、0警告、0提示；构建329页，搜索索引320页。
- 7,368条本地链接审计0错误；既有网页覆盖缓存审计0错误。
- 实际浏览器确认八节标题、概念段目录、新旧正文衔接、加粗和专题入口。搜索“助记词”（7条）与“预言机”（1条）在Forensics/虚拟币取证/知识点筛选下均返回基础页，新段落摘要可见。页面截图记录为JPEG。

## 验证边界

完成的是概念材料核对、构造证据判读和网站验收。未进行真实助记词/钱包恢复、实际密钥派生、硬件签名、节点查询、真实交易或合约执行，未独立复跑竞赛检材。页面中的取证判断仍须在实际材料上核对。
