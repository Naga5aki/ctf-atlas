---
title: "虚拟货币与资金流"
summary: "从助记词、密钥、钱包与合约概念进入区块链原理，再串联设备、链上交易和平台资金流的证据。"
module: "Forensics"
track: "虚拟币取证"
topic: "基础与证据"
tags: []
status: "已整理"
sourceIds: ["0047c3d2f371", "cd60ad7b2b42", "web-crypto-zhihu-14425551337", "web-crypto-bitcoin-transactions", "web-crypto-ethereum-accounts", "web-crypto-erc20", "web-crypto-tron-encoding", "web-crypto-nist", "web-crypto-shuzheng-2025"]
challengeIds: []
relatedIds: ["forensic-crypto-foundations", "forensic-crypto-wallets", "forensic-crypto-bitcoin", "forensic-crypto-account-chains", "forensic-crypto-tracing", "forensic-crypto-practice"]
updated: "2026-10-03"
---

## 专题导航

虚拟币取证先理清助记词、密钥、钱包、账户与智能合约，再掌握区块、共识和账本模型，从设备线索核对钱包与网络，分析链上有效移动、平台记录和资金关系。本页保留聊天、配置、截图、本地账本与笔记历史的资金流核对流程；下列六篇按理论、操作与场景展开。

| 阅读方向 | 知识点与考点 |
| --- | --- |
| 基础与证据 | [基础概念：助记词、密钥、钱包、智能合约；区块链原理与证据流程](/knowledge/forensic-crypto-foundations/) |
| 钱包与控制权 | [本地痕迹、派生条件、助记词载体与钱包类型](/knowledge/forensic-crypto-wallets/) |
| 链上交易 | [Bitcoin：UTXO、手续费、找零与只读复核](/knowledge/forensic-crypto-bitcoin/)；[EVM/TRON：回执、代币事件、调用与分页](/knowledge/forensic-crypto-account-chains/) |
| 资金追踪与实战 | [平台账本、交易图、归因模型、跨链与归属边界](/knowledge/forensic-crypto-tracing/)；[离线账本、区块头与 Merkle 验证、场景考点与报告复核](/knowledge/forensic-crypto-practice/) |

## 01 把地址、交易与账本分开验证

资金流取证需要先确认记录的网络、资产、对象和时间范围，再讨论方向与总额。聊天里出现地址支持交流内容，截图支持当时保存的界面图像，本地账本支持应用或人员登记的流水；实际链上交易还需对应网络的交易结构与状态核对。地址存在、交易成功、地址控制权和自然人身份是不同层次的结论。

### 01.1 常见载体与提取字段

| 载体 | 可以提取 | 交叉材料 |
| --- | --- | --- |
| 聊天记录 | 地址、转账约定、金额、交易哈希、双方账号与时间 | 聊天数据库记录 ID、目标网络交易及账户关联 |
| 转账截图 | 界面显示的状态、金额、时间与候选 hash | 原图摘要、文件时间、完整交易记录；图片可被编辑 |
| 本地账本、数据库、Excel、VHD | 多条流水、姓名/账号/地址映射 | 行号/主键、导出规则、链上记录、去重与完整范围 |
| 程序配置 | 硬编码或解密后的收款地址，如 `sponsors[].wallet` | 代码读取位置、配置版本与实际业务/通信记录 |

**场景：** 聊天约定一个收款地址，程序配置保存相同地址，解密 VHD 内又有账本。先固定三类材料并建立对象关系，再逐笔验证。VHD 派生过程见[证据介质与文件系统](/knowledge/fic-case-02/)，加密配置的读取见[密码学取证](/knowledge/fic-case-08/)。

### 01.2 实战：提取目标地址与候选交易

1. 从聊天库按实际表结构读取完整消息，记录发送方、接收方、消息 ID、内容与原始时间。
2. 从配置保存条目索引和上下文，确认该字段确实被业务逻辑读取，不只保存一个孤立字符串。
3. 固定截图、账本及派生文件摘要；从截图 OCR 得到的字符逐一回看原图，排除 `0/O` 等误识。
4. 将候选地址、完整 hash、网络、资产、金额和时间列入逐笔核对表。
5. 用网络标识、交易 hash 和实际收款对象查对应记录，保存查询时点与原始结果；没有验证条件时标为本地记录或交易候选。

```bash
sha256sum ./evidence/transfer.png ./work/ledger.csv
file ./evidence/transfer.png
head -n 5 ./work/ledger.csv
```

截图名称若像交易 hash，仍需与图中、聊天中或账本中的完整值比较。文件改名、转发和重新保存都会改变名称与时间属性；名称不是交易成功证明。

## 02 地址格式、网络与资产

### 02.1 前缀只能确定候选格式

| 外观 | 候选格式 | 不能直接推出 |
| --- | --- | --- |
| `T…`，常见 34 字符 | TRON Base58Check 地址 | 使用的代币一定是 TRC20、交易已发生或控制者身份 |
| `0x` + 40 hex | Ethereum/EVM 20 字节地址 | 一定是 Ethereum 主网或 ERC20；其他 EVM 网络也使用此形式 |
| `bc1…` / `1…` / `3…` | Bitcoin 主网常见地址格式 | 所有字符串均有效、是哪笔输入/输出或地址归属 |

TRON 地址还可显示为带 `41` 前缀的 21 字节 hex；Base58Check 长度和校验需验证，见 [TRON 地址说明](https://developers.tron.network/docs/account)。EVM 地址需保存原始大小写与校验形式，明确网络/chain ID；[Ethereum 账户说明](https://ethereum.org/en/developers/docs/accounts/)介绍地址结构。地址可跨资产使用，不能把地址前缀当作代币标准。

### 02.2 实战：核对同符号资产

**材料：** 交易的网络、token 合约、资产符号、原始数量和精度来源。两个都显示为 `USDT` 的记录，可能处在不同网络或不同合约，也可能是仿冒标识。先以网络和合约确定资产，再使用可信合约元信息解释整数数量，不仅按符号相加。

精度依资产而异：BTC 常以 8 位小数展示，ETH 使用 wei 等最小单位，代币由合约/实际格式定义 decimals。不能泛说“链上都为 8 位”。[ERC-20 规范](https://eips.ethereum.org/EIPS/eip-20)定义数量与 decimals 的关系，decimals 元信息本身也需确认其可用性。若账本只给显示金额，保留它的文本与币种，不反推未保存的整数。

## 03 交易状态、方向与去重

### 03.1 按目标对象确定方向

| 目标与记录关系 | 分类示例 | 统计注意 |
| --- | --- | --- |
| `to` 是目标，`from` 是其他对象 | 转入候选 | 核对网络、资产、成功/确认状态与有效时间范围 |
| `from` 是目标，`to` 是其他对象 | 转出候选 | 金额与手续费分别记录，不能混入收款总额 |
| `from` 与 `to` 都是目标 | 自转 | 按口径单独列出，避免制造收入 |
| 两端都不是目标 | 其他或关联对象 | 不因姓名相似就并入目标地址统计 |

表格适用于已经规范化的账户式转账记录。Bitcoin 是 UTXO 结构，实际交易可有多个输入/输出和找零，不能把链上原始交易强行简化为一组 `from/to`；应按目标脚本/输出核对，见 [Bitcoin 交易结构](https://developer.bitcoin.org/reference/transactions.html)。

### 03.2 交易 hash 并非所有记录的唯一行键

同一交易可以包含多个 token Transfer 事件、多笔输出或内部调用。只按 hash 去重会漏算，按文件行号又会重复算。依据载体选择 `网络 + 完整hash + 事件索引/输出索引 + 资产标识` 等键，并验证同键内容是否一致。

前 N 位 hash 只能用于便于阅读的缩写，不适合唯一关联、去重或查询；保存完整原值后，展示需要时再截取。失败、待确认、重组或应用“已提交”状态不能不加区分地计入已完成流水。

## 04 实战：从规范化账本统计转入

### 04.1 准备可审计输入

**材料：** 已从只读内层磁盘导出的 `ledger.csv`，包含 `network,asset_id,tx_hash,event_index,from,to,status,amount`。其中 `asset_id` 是已经核对的合约/原生资产标识；`amount` 为已根据可信精度转换的十进制文本；地址已按对应网络规则验证和规范化。CSV 还应保留原始整数、精度来源、时间和原行引用，供审计使用。

下面脚本只是对这份规范化导出汇总，不查询链上状态，也不替输入完成地址校验。保存为 `sum_incoming.py`，三个参数依次为已核对的网络、资产标识和完整目标地址。

```python
import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('network')
parser.add_argument('asset_id')
parser.add_argument('target')
args = parser.parse_args()
getcontext().prec = 100
seen, accepted = {}, []
total = Decimal('0')
excluded, duplicates, self_transfers = 0, 0, 0
with Path('work/ledger.csv').open(encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    output_fields = ['line'] + (reader.fieldnames or [])
    if not reader.fieldnames:
        raise ValueError('账本缺少表头')
    for line, row in enumerate(reader, start=2):
        if row['network'] != args.network or row['asset_id'] != args.asset_id:
            excluded += 1
            continue
        if row['status'] != 'confirmed_success':
            excluded += 1
            continue
        amount = Decimal(row['amount'])
        if not amount.is_finite() or amount < 0:
            raise ValueError(f'金额异常: line={line}')
        if not row['tx_hash'] or not row['event_index']:
            raise ValueError(f'缺少完整去重字段: line={line}')
        key = (row['network'], row['asset_id'], row['tx_hash'], row['event_index'])
        signature = (row['from'], row['to'], amount)
        if key in seen:
            if seen[key] != signature:
                raise ValueError(f'同键数据冲突: line={line}')
            duplicates += 1
            continue
        seen[key] = signature
        if row['from'] == args.target and row['to'] == args.target:
            self_transfers += 1
            continue
        if row['to'] != args.target:
            excluded += 1
            continue
        total += amount
        accepted.append({'line': line, **row})
print('accepted=', len(accepted), 'duplicates=', duplicates,
      'self_transfers=', self_transfers, 'excluded=', excluded)
print('exact_total=', format(total, 'f'))
print('display_total=', total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
output_path = Path('work/incoming-selected.csv')
with output_path.open('w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=output_fields)
    writer.writeheader()
    writer.writerows(accepted)
print('generated_rows=', len(accepted), 'output=', output_path)
```

```bash
python3 sum_incoming.py '<已核对的network>' '<已核对的asset_id>' '<完整目标地址>'
sha256sum ./work/ledger.csv ./work/incoming-selected.csv
```

每次成功汇总都重写当前选中明细；零选中时保存表头和0行，并输出生成行数及路径，防止误用上次结果。只有脚本成功完成并报告本次输出后，再计算对应文件摘要。完整输入行数、被排除原因、日期条件与缺失数据另外保存；如果有时间范围，先用确定的时区和闭开区间过滤，并记录边界。

### 04.2 示例输出与判读

假设同一目标的两个成功转入记录为 `12.345` 与 `0.005`，另有一份相同事件重复导出、自转和失败转账。输出应保留两笔有效记录、识别重复和自转，精确总额为 `12.350`；按本示例“最后汇总后四舍五入到两位”的规则展示为 `12.35`。

这只是演示明确口径的预期结果，不代表真实账本总额。若先逐笔舍入再累加，会出现不同值，应按既定统计要求选择并说明。总额也不直接等于净收益、法币价值或账户余额，手续费、转出和其他资产需单独处理。

## 05 逐笔交叉与归属边界

### 05.1 由多种材料确认同一笔交易

比较网络、完整 hash、资产、事件/输出索引、目标地址、方向、数量、状态与时间。聊天约定时间、截图显示时间、区块时间和应用入账时间可能不同；先解释事件含义与时区，不因相差几分钟就认定两笔不同，也不只凭金额相同就合并。

交易所充值、钱包、银行卡或支付渠道信息可能保存在聊天和配置；平台内部账本未必直接对应一笔链上转账。会员/卡密业务与公开群组、客服链接可形成业务线索，仍需交易记录、账户映射与时间关联，不把一个群组 ID 当成收款人身份。

### 05.2 可复核的结论

报告给出材料范围、目标地址与网络、资产及精度、有效记录数、去重键、排除项、精确总额与展示舍入规则、选中明细及原始文件摘要。对缺少链上验证的部分称为“本地账本登记金额”或“截图显示金额”，不要统一称为已发生收款。

地址出现在聊天或配置里可以支持候选用途；签名能力、设备密钥、账户控制与自然人关系需要更多证据。资金流的可观察关系与身份归属分别表述，保留尚未验证的环节。

## 06 实战：从笔记历史提取地址并确认表达层

**场景：** Anytype 等笔记应用的对象库或版本历史中发现疑似地址，内容经过一层或多层编码。保全账户容器、对象库、历史记录和对应版本，再逐层记录变换，不能只保留最后显示的字符串。

1. 以对象 ID 关联标题、正文和历史版本，区分对象创建、内容首次出现、修改、导入及同步时间。文件 mtime 不能直接当作页面创建时间。
2. 对候选文本确认编码顺序，记录每层的输入/输出长度和摘要；如为 Base64、hex、URL 编码，按合法字符和实际调用方式严格解码，不把自动识别结果当作确定格式。
3. 保存最终文本的原始大小写、字节长度和校验结果。以 `3…` 开头只支持 Bitcoin P2SH 等候选方向，不能称为 TRON 地址；TRON/EVM 的核验沿本页地址表执行。
4. 从钱包配置、网络和交易记录核对同一地址。出现在笔记中说明该对象保存了这串内容，不证明设备使用者拥有私钥或控制该账户。
5. 若目标是“创建时间”，同时报告对象元数据、最早历史版本与导入/同步证据，说明各时间字段的语义和冲突。

**示例判读：** 一个历史版本首次出现某地址，而对象创建时间更早，且有外部导入记录。应分别记录“对象建立”“地址首次可见”和“导入事件”，不能任选最早时间称为钱包建立时间。应用容器和笔记数据库定位见[Windows 系统与用户痕迹](/knowledge/forensic-windows-artifacts/)。
