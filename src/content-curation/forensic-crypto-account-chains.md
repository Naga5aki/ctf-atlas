## 01 调查主线：把交易、资产和身份分开

Ethereum 与其他 EVM 链采用账户状态和合约执行模型；TRON 也通过交易与合约改变账户状态，但地址表示、原生单位、资源费用和确认接口有自己的规则。调查时先确定网络和资产，再解释执行结果。

**首轮顺序：** 确定网络 → 固定交易、回执和区块 → 区分原生币、代币与授权 → 检查成功状态 → 解码事件和内部调用 → 用整数核算 → 处理分页及重复 → 复核确认状态 → 关联设备和账户证据。

| 观察层 | 保存什么 | 可以回答什么 |
| --- | --- | --- |
| 交易正文 | 网络、hash、from/to、value、input 或 contract body | 谁发起了什么请求 |
| 执行回执 | blockHash/height、status/result、fee、logs | 是否执行、用了多少资源、发出哪些事件 |
| 内部执行 | 调用类型、路径、value、error/rejected | 合约执行过程中的调用和资产移动 |
| 账户或合约状态 | 指定区块的余额、代币精度、合约代码 | 该采集高度的状态与元数据 |
| 设备和业务材料 | 钱包记录、聊天、浏览器、账户标识 | 地址与设备用户、业务事件的关联 |

本篇命令默认使用 Kali/Linux。查询需要用户自己的只读节点或已授权的 RPC 地址；网络、节点版本、数据范围和历史状态能力必须预先确认。示例写入当前分析目录的 `./output/account-chains`，不在检材目录启动钱包。没有可用接口时，从保全 JSON 离线分析。模板并不表示已在真实钱包或真实链案件上复跑；后面的数值案例均为自建练习。

## 02 EVM：先确定链，再读交易

### 02.1 同样的地址形式可以属于不同网络

`0x` 加 40 位十六进制字符是常见的 EVM 地址表示。相同地址字符串可以出现在多个 EVM 网络中；同名代币也可以由不同合约发行。先读取 `eth_chainId`，并保存 RPC 连接对象、客户端版本与区块锚点。只用币名、钱包网络下拉菜单或截图标题不足以证明网络。

资产唯一定位建议使用 `网络标识 + 代币合约地址`；交易使用 `网络标识 + transactionHash`。链 ID 是必要的网络记录，但自定义私链也可能复用链 ID，调查私链时继续保存创世块、节点配置和区块 hash。

### 02.2 交易字段描述请求，不保证资产到账

| 字段 | 含义 | 容易混淆的地方 |
| --- | --- | --- |
| `from` | 交易发起地址 | 不等于每条代币事件的 from |
| `to` | 外部交易目标，创建合约时可为 null | 调用合约时不一定是最终收款人 |
| `value` | 外部交易携带的原生币整数数量 | 不是 ERC20 金额 |
| `input` | 调用数据或部署字节码 | 只表达请求，不能单独证明执行成功 |
| `nonce` | 发起账户的序列值 | 不同交易 hash 可对应相同 from/nonce 的替换候选 |
| `gas` / gas limit | 最大允许用量 | 不是实际用量 |
| `maxFeePerGas` | 动态费用交易的单价上限 | 不是实际支付单价 |
| `blockHash` / `blockNumber` | 包含区块定位 | pending 时可能为空；应与回执核对 |

外部交易的 from、事件的 from、内部调用的 from 分别属于不同层次。路由合约、批量分发、授权代扣和合约钱包等场景下，它们可以不同。不要把一个界面中的 Sender 复制到所有资产记录。

## 03 EVM 回执、成功与 gas

### 03.1 状态判读

现代 EVM 回执的 `status=0x1` 表示交易执行成功，`status=0x0` 表示失败。`eth_getTransactionReceipt` 返回 `null` 只能说明本次查询没有找到回执；交易可能尚未入块、节点历史数据不完整、网络选错或查询对象错误。

| 材料表现 | 正确分类 |
| --- | --- |
| RPC 的 JSON `error` | 查询错误；不能当作交易失败 |
| transaction 已找到、receipt 为 null | 尚未证实执行结果，继续检查包含关系 |
| 已上链回执 status=0 | 执行失败，资产请求不按成功到账统计 |
| 已上链回执 status=1 | 外层成功；继续检查资产事件和内部调用 |
| 只看到发送/广播成功提示 | 仅证明某个客户端或节点接受了请求 |

较早的 Ethereum 历史回执可能使用状态根而没有现代 `status`。处理历史数据时明确版本范围，缺失字段不填成功。外层成功也不意味着每个内部调用都成功，更不意味着代币合约实现了正常业务逻辑。

### 03.2 用实际回执核算费用

```text
1 ETH = 10^18 wei
1 gwei = 10^9 wei
Ethereum 普通执行费 wei = gasUsed × effectiveGasPrice
```

`gasUsed` 是本交易实际用量；`cumulativeGasUsed` 是本区块执行到该交易时的累计用量。两者不能替换。动态费用交易不要用 `maxFeePerGas` 或 `maxPriorityFeePerGas` 代替回执中的实际单价。

已上链执行失败仍要支付已经消耗的计算费用；执行前校验失败而未上链的请求与此不同。失败交易保留费用记录，但不把失败 calldata 中的转账数量计为有效流入。普通执行费公式不自动包含 blob 费用或不同 L2 的附加费用，遇到这些交易要按目标网络和交易类型另列组成。

## 04 ERC20：合约、事件和精度

### 04.1 先锁定资产身份

ERC20 余额和转移由代币合约维护。名称和符号可以重复，也不能证明资产真实性。保存合约地址、网络、元数据取得时间与区块位置；同名不同合约分别统计。代理合约和可升级逻辑应考虑调查时点，不把当前代码或元数据当作所有历史时期的状态。

`decimals()`、`name()`、`symbol()` 在 ERC20 接口中是可选项。无法读取 decimals 时，保留原始整数数量并标记“精度未知”；不要默认所有 ERC20 为 18 位，也不要把原生币的 18 位套给代币。

```text
显示金额 = 原始整数 / 10^decimals
decimals=6，raw=7,500,000 → 7.5 单位
decimals=8，raw=7,500,000 → 0.075 单位
```

### 04.2 标准 Transfer 的布局

标准事件签名是 `Transfer(address,address,uint256)`。事件主题使用 Keccak-256，不能用 Python `hashlib.sha3_256` 代替。

```text
topics[0] = ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
topics[1] = from 地址，左侧补零成 32 字节
topics[2] = to 地址，左侧补零成 32 字节
data      = 原始 uint256 数量，32 字节大端整数
address   = 发出此日志的合约地址
```

EVM 日志通常为这些 hex 值添加 `0x`。解码前先检查网络、回执成功、日志合约、主题数量、主题长度与 data 长度，再取地址词的最后 20 字节。不要只搜索 `topics[0]` 就认定资产身份；其他合约也可以发出形似相同的事件。

| 事件或操作 | 统计规则 |
| --- | --- |
| `Transfer` | 根据已核对合约的语义解释转移 |
| `Approval` / approve | 授权额度变化，不能计为资产到账 |
| 零金额 Transfer | 可计为事件；正金额到账次数应另外定义 |
| from 为零地址 | 可能表示铸币，不能当作普通用户付款 |
| to 为零地址 | 可能表示销毁或合约特定行为，不能当作普通收款人 |
| 一笔交易多条 Transfer | 每条事件单列；交易数和事件数分开 |

自定义或欺骗性合约可能只发出日志而不按正常代币规则改变余额。因此事件是合约声明的执行记录；遇到合约异常、可疑假资产或题目要求证明余额时，继续结合代码、历史状态与业务材料核查。不能因为存在 Transfer 就推断某自然人发起或持有真实价值资产。

## 05 EVM 只读查询与记录保存

### 05.1 连接、输出和请求保全

需要 Bash、curl、Python 3，以及已经可访问的只读 RPC。示例使用本地 `8545`；替换为自己的地址，服务凭据不要写入公开报告。请求不需要私钥，不调用签名或发送交易接口。

```bash
RPC='http://127.0.0.1:8545'
OUT='./output/account-chains/evm'
mkdir -p "$OUT"

rpc_read() {
  printf '%s\n' "$2" > "$1.request.json"
  curl -sS -H 'Content-Type: application/json' \
    -D "$1.headers.txt" --data-binary "$2" "$RPC" -o "$1"
}

rpc_read "$OUT/chain-id.json" \
  '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
rpc_read "$OUT/client-version.json" \
  '{"jsonrpc":"2.0","id":2,"method":"web3_clientVersion","params":[]}'
rpc_read "$OUT/finalized.json" \
  '{"jsonrpc":"2.0","id":3,"method":"eth_getBlockByNumber","params":["finalized",false]}'
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$OUT/collected-at-utc.txt"
```

HTTP 成功不能替代 JSON 检查。每个响应确认不存在 `error`，`result` 的类型和值符合请求。目标链不支持 `finalized` 时记录“不支持”，并按该链的确认规则采集，不能把报错或 null 当作已最终确认。

### 05.2 同时保存交易、回执与区块

`TXHASH` 替换为带 `0x` 的 64 位交易 hash。先检查变量格式，再生成 JSON。

```bash
TXHASH='替换为0x开头的完整交易hash'
[[ "$TXHASH" =~ ^0x[[:xdigit:]]{64}$ ]] || { printf '交易hash格式错误\n' >&2; exit 1; }
REQ_TX=$(printf '{"jsonrpc":"2.0","id":4,"method":"eth_getTransactionByHash","params":["%s"]}' "$TXHASH")
REQ_RC=$(printf '{"jsonrpc":"2.0","id":5,"method":"eth_getTransactionReceipt","params":["%s"]}' "$TXHASH")
rpc_read "$OUT/transaction.json" "$REQ_TX"
rpc_read "$OUT/receipt.json" "$REQ_RC"
```

读取成功回执的 `blockHash`，替换变量后取区块。不要将截图中的高度直接与另一个网络的区块拼接。`receipt.json` 中用于核算执行状态、实际手续费与 ERC20 `Transfer` 事件的核心字段结构如下（构造示例）：

```json
{
  "result": {
    "transactionHash": "0x1111...",
    "blockHash": "0x2222...",
    "status": "0x1",
    "gasUsed": "0xc350",
    "effectiveGasPrice": "0x4a817c800",
    "logs": [{
      "address": "0xaaaa...",
      "topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", "0x0000...from", "0x0000...to"],
      "data": "0x00000000000000000000000000000000000000000000000000000000017d7840",
      "logIndex": "0x0"
    }]
  }
}
```

```bash
BLOCKHASH='替换为回执中的0x开头区块hash'
[[ "$BLOCKHASH" =~ ^0x[[:xdigit:]]{64}$ ]] || { printf '区块hash格式错误\n' >&2; exit 1; }
REQ_BLOCK=$(printf '{"jsonrpc":"2.0","id":6,"method":"eth_getBlockByHash","params":["%s",false]}' "$BLOCKHASH")
rpc_read "$OUT/block.json" "$REQ_BLOCK"
```

回执 hash、交易 hash、区块 hash 与高度必须互相一致。将回执高度与采集到的 finalized 高度比较后，还要确认该高度当前规范区块的 hash 相同；只比较高度不证明包含于同一条链。

### 05.3 在固定区块读取精度

`TOKEN` 替换为代币合约地址；`AT_BLOCK` 填调查区块的十六进制高度，例如 `0x1234`。`0x313ce567` 是 `decimals()` 的函数选择器。历史状态不可用时，保存错误，不用当前高度静默替代。

```bash
TOKEN='替换为0x开头的40位合约地址'
AT_BLOCK='替换为0x开头的调查区块高度'
[[ "$TOKEN" =~ ^0x[[:xdigit:]]{40}$ ]] || { printf '合约地址格式错误\n' >&2; exit 1; }
[[ "$AT_BLOCK" =~ ^0x[[:xdigit:]]+$ ]] || { printf '区块高度格式错误\n' >&2; exit 1; }
REQ_DEC=$(printf '{"jsonrpc":"2.0","id":7,"method":"eth_call","params":[{"to":"%s","input":"0x313ce567"},"%s"]}' "$TOKEN" "$AT_BLOCK")
rpc_read "$OUT/decimals.json" "$REQ_DEC"
```

`eth_call` 执行模拟读取，不创建链上交易。只有结果满足预期 uint8 ABI 编码且值在 `0..255` 时，才用作精度。空结果、异常、错误 ABI 与未知合约分别记录；原始整数金额继续保留。

### 05.4 只读范围事件查询

从已确认区块范围开始，使用合约地址和事件主题缩小范围。`FROM_BLOCK`、`TO_BLOCK` 使用无多余前导零的十六进制数量。

```bash
FROM_BLOCK='替换为0x开头的开始高度'
TO_BLOCK='替换为0x开头的结束高度'
TOPIC='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
[[ "$FROM_BLOCK" =~ ^0x[[:xdigit:]]+$ && "$TO_BLOCK" =~ ^0x[[:xdigit:]]+$ ]] || { printf '范围格式错误\n' >&2; exit 1; }
REQ_LOG=$(printf '{"jsonrpc":"2.0","id":8,"method":"eth_getLogs","params":[{"fromBlock":"%s","toBlock":"%s","address":"%s","topics":["%s"]}]}' "$FROM_BLOCK" "$TO_BLOCK" "$TOKEN" "$TOPIC")
rpc_read "$OUT/logs-range.json" "$REQ_LOG"
sha256sum "$OUT"/*.json > "$OUT/SHA256SUMS"
```

`eth_getLogs` 没有一个通用的分页游标。节点或服务限制范围、数量或超时时，划分固定闭区间 `[a,b]`、`[b+1,c]` 分段查询，保存每段请求和响应；不要把报错当作空结果。跨段或重试记录按事件唯一键去重，确认没有区块范围缺口。

## 06 EVM internal 与调用树

区块浏览器的 internal 页面通常展示合约执行过程中的调用记录，不是另外一笔外部签名交易。必须回到其父交易和执行回执。

| 调用字段/类型 | 解释原则 |
| --- | --- |
| `CALL` | 调用另一个账户或合约，可能携带原生币 |
| `STATICCALL` | 只读执行上下文，不能按显示行数统计付款 |
| `DELEGATECALL` | 执行另一地址的代码，to 是代码目标，不是该行付款的收款人 |
| `CREATE/CREATE2` | 创建合约的执行过程，单列创建动作 |
| `error` / `revertReason` | 失败或回滚信息，不是成功到账记录 |
| `calls[]` | 子调用树；必须保留祖先路径和执行顺序 |

一个子调用没有 error，也可能被后续失败的祖先调用整体回滚。筛选资产变化时同时检查本节点和全部祖先，外层 status=0 的调用不能当成最终生效转移。子分支失败被外层捕获时，外层 status 可以为 1；失败分支仍不计有效到账。

需要支持 Geth `debug_traceTransaction` 和 `callTracer` 的节点，且具备重放历史交易所需状态。普通托管只读 RPC 不一定开放 debug 方法；无法取得 trace 时记录可见范围，不能宣称“没有内部交易”。

```bash
REQ_TRACE=$(printf '{"jsonrpc":"2.0","id":9,"method":"debug_traceTransaction","params":["%s",{"tracer":"callTracer"}]}' "$TXHASH")
rpc_read "$OUT/trace.json" "$REQ_TRACE"
```

trace 是按客户端、版本、tracer 和选项获得的执行结果，应保存这些参数。调用树的 gasUsed 和顶层 gasUsed 不可按所有节点直接相加，因为父节点可能包含子节点用量。trace 的 `value` 也不能不分类型地相加；必要时结合状态差异解释实际原生币变化，并把 gas 费用与收款额分开。

## 07 EVM 离线事件提取

下面脚本只读取一份已保全回执，筛选一个已经确认语义的标准 ERC20 合约。保存为自己的 `decode_erc20_receipt.py`。输入参数依次为回执文件、目标合约、精度。脚本不访问网络，不验证真实包含关系或合约经济属性。

```python
import json
import re
import sys
from pathlib import Path

SIG = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ADDR = re.compile(r'^0x[0-9a-fA-F]{40}$')
WORD = re.compile(r'^0x[0-9a-fA-F]{64}$')
INDEX = re.compile(r'^0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)$')

def display(raw, decimals):
    if decimals == 0:
        return str(raw)
    whole, rest = divmod(raw, 10 ** decimals)
    fraction = str(rest).zfill(decimals).rstrip('0')
    return str(whole) + ('.' + fraction if fraction else '')

def topic_address(word):
    if not isinstance(word, str) or not WORD.fullmatch(word) or int(word[2:26], 16) != 0:
        raise ValueError('地址 topic 不符合标准 32 字节左补零布局')
    return '0x' + word[-40:].lower()

document = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if 'error' in document:
    raise SystemExit('RPC 错误，不能当作交易执行结果')
receipt = document.get('result', document)
if not isinstance(receipt, dict):
    raise SystemExit('没有可分析回执')
token = sys.argv[2]
decimals = int(sys.argv[3])
if not ADDR.fullmatch(token) or not 0 <= decimals <= 255:
    raise SystemExit('合约地址或精度无效')
if receipt.get('status') not in ('0x1', '0x0'):
    raise SystemExit('现代 status 缺失或格式未知，需单独解释')
receipt_block = receipt.get('blockHash', '')
receipt_tx = receipt.get('transactionHash', '')
if not isinstance(receipt_block, str) or not WORD.fullmatch(receipt_block):
    raise SystemExit('回执缺少有效 blockHash 定位')
if not isinstance(receipt_tx, str) or not WORD.fullmatch(receipt_tx):
    raise SystemExit('回执缺少有效 transactionHash 定位')

fee = None
if 'gasUsed' in receipt and 'effectiveGasPrice' in receipt:
    fee = int(receipt['gasUsed'], 16) * int(receipt['effectiveGasPrice'], 16)
events = []
seen = {}
if receipt['status'] == '0x1':
    for log in receipt.get('logs', []):
        if log.get('address', '').lower() != token.lower():
            continue
        topics = log.get('topics', [])
        if not topics or topics[0].lower() != SIG:
            continue
        data = log.get('data', '')
        if len(topics) != 3 or not isinstance(data, str) or not WORD.fullmatch(data):
            raise SystemExit('匹配主题但布局异常，不能按标准 ERC20 解码')
        sender = topic_address(topics[1])
        receiver = topic_address(topics[2])
        raw = int(data, 16)
        block_hash = log.get('blockHash', '')
        tx_hash = log.get('transactionHash', '')
        log_index = log.get('logIndex', '')
        if not isinstance(block_hash, str) or block_hash.lower() != receipt_block.lower():
            raise SystemExit('日志 blockHash 与回执定位不一致')
        if not isinstance(tx_hash, str) or tx_hash.lower() != receipt_tx.lower():
            raise SystemExit('日志 transactionHash 与回执定位不一致')
        if not isinstance(log_index, str) or not INDEX.fullmatch(log_index):
            raise SystemExit('日志 logIndex 缺失或不是有效十六进制数量')
        removed = log.get('removed', False)
        if not isinstance(removed, bool):
            raise SystemExit('日志 removed 不是布尔值')
        key = (block_hash.lower(), tx_hash.lower(), int(log_index, 16))
        signature = (token.lower(), sender, receiver, raw, removed)
        if key in seen:
            if seen[key] == signature:
                continue
            raise SystemExit('同一事件键字段冲突，停止输出确定统计结果')
        seen[key] = signature
        if removed:
            continue
        events.append({'block_hash': key[0], 'tx_hash': key[1],
                       'log_index': log_index, 'contract': token.lower(),
                       'from': sender, 'to': receiver,
                       'amount_raw': str(raw), 'decimals': decimals,
                       'amount_display': display(raw, decimals)})
print(json.dumps({'status': receipt['status'],
                  'execution_fee_wei': None if fee is None else str(fee),
                  'events': events}, ensure_ascii=False, indent=2))
```

```bash
TOKEN='替换为已经核对的0x开头合约地址'
DECIMALS='替换为已经核对的十进制精度'
python3 decode_erc20_receipt.py output/account-chains/evm/receipt.json "$TOKEN" "$DECIMALS"
```

金额原值输出为十进制字符串，避免后续网页或表格以浮点误读大整数。零金额事件仍然保留。日志必须与回执的区块和交易定位一致；重复事件先解码和校验，只有字段完全一致才跳过，同键地址、数量或撤销状态冲突则停止输出确定统计结果。脚本只用于标准布局；非标准代币、事件伪造、代理升级、手续费代币与余额自动调整等情形需另行分析，不能强行套用。

## 08 TRON 地址、原生币与代币

### 08.1 三种地址场景

| 场景 | 表示 | 处理 |
| --- | --- | --- |
| 普通账户/合约 Hex | `41` + 40 位地址，共 21 字节 | 保存 41 前缀并校验长度 |
| 钱包或界面 Base58Check | 通常以 T 开头的 34 字符 | 校验 checksum 后转成相同的 21 字节地址 |
| 合约 ABI 地址词 | 20 字节地址左补零成 32 字节 | 解码末尾 20 字节，再恢复 TRON 的 41 表示 |

当前 Mainnet、Shasta、Nile 地址都使用 `41` 前缀；`T` 或 `41` 不能判断网络。Base58Check 区分大小写，不能把完整 Base58 地址转小写用于比较。保留原展示，关联时使用经校验的地址字节。

以下标准库函数可放入自己的离线分析脚本，转换和校验当前 41 前缀地址；它只验证编码，不证明账户存在、激活状态或控制权。

```python
import hashlib
import hmac

ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def hex_to_base58(hex_address):
    raw = hex_address[2:] if hex_address.startswith('0x') else hex_address
    payload = bytes.fromhex(raw)
    if len(payload) != 21 or payload[0] != 0x41:
        raise ValueError('预期 21 字节且以 41 开头')
    check = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    wire = payload + check
    number = int.from_bytes(wire, 'big')
    encoded = ''
    while number:
        number, remainder = divmod(number, 58)
        encoded = ALPHABET[remainder] + encoded
    leading = len(wire) - len(wire.lstrip(b'\0'))
    return '1' * leading + encoded

def base58_to_hex(address):
    number = 0
    for char in address:
        if char not in ALPHABET:
            raise ValueError('Base58 字符错误')
        number = number * 58 + ALPHABET.index(char)
    wire = number.to_bytes((number.bit_length() + 7) // 8, 'big')
    leading = len(address) - len(address.lstrip('1'))
    wire = b'\0' * leading + wire
    if len(wire) != 25:
        raise ValueError('Base58Check 长度错误')
    payload, check = wire[:-4], wire[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if payload[0] != 0x41 or not hmac.compare_digest(check, expected):
        raise ValueError('前缀或 checksum 错误')
    return payload.hex()
```

从 ABI word 取地址之前，先检查其长度和左侧 12 字节为零，然后用 `41 + 最后40位hex` 恢复账户 Hex。不要把整个 32 字节 topic 当成账户地址。日志中的合约地址字段与普通 HTTP 请求地址可能长度不同，按字段语义转换，保留原始字段值。

### 08.2 TRX、TRC20 和内部移动分开

```text
1 TRX = 1,000,000 sun
TransferContract.amount → 原生 TRX 的 sun 数量
TriggerSmartContract   → 合约调用请求
TRC20 Transfer 日志     → 该代币的原始整数数量
internal callValue     → 按 tokenId 区分 TRX 与 TRC10
```

`TransferContract` 读取 `owner_address`、`to_address` 和 `amount`。`TriggerSmartContract` 的 `contract_address` 是被调用合约，不能直接作为最终收款人；其 `call_value` 描述调用携带的 TRX，也不是 TRC20 转移数量。TRC20 的最终转移从成功执行产生的 Transfer 日志提取。

一笔合约调用可以同时包含代币事件和内部 TRX/TRC10 移动。统计分别按资产建表，不能把所有字段金额相加后加上一个“TRX”单位。

## 09 TRON 回执、资源费与固化

### 09.1 交易正文与执行信息

`gettransactionbyid` 的正文记录请求内容、`raw_data` 和签名；`gettransactioninfobyid` 记录执行后的区块位置、费用、资源使用、日志与 internal 信息。FullNode 的已执行记录与 SolidityNode 的固化记录属于不同确认层。

原生 TRX 普通转账通过正文读取收款人和 amount，再确认包含及固化状态。智能合约调用检查固化回执的成功结果，并确认没有明确失败；`receipt.result=SUCCESS` 是成功信号。结果缺失、请求错误或空响应先保留未知，不统一填失败。不要要求普通 TRX 转账一定具有智能合约的 SUCCESS 字段。

### 09.2 资源消耗不是实际收费金额

| 项目 | 含义 | 统计方法 |
| --- | --- | --- |
| Bandwidth / net usage | 交易字节相关资源 | 保存资源用量，不直接当作 sun |
| Energy / energy usage | 合约计算资源 | 保存资源用量和各方承担情况 |
| `energy_fee` / `net_fee` | 回执提供的相关费用组成 | 读取其原始单位，不能再和总 fee 重复相加 |
| `fee` | 回执记录的实际费用金额 | 以 sun 保存，显示时除以 10^6 |
| `fee_limit` | 合约调用方的 Energy 预算限制 | 上限不等于实际支付额 |

资源不足时可以燃烧 TRX 支付，资源来源和部署方分摊会影响收费；费率与规则存在网络参数变化。历史费率不能直接用当前值重算。做费用题优先保存实际回执的 fee 及组成；缺失字段标记未知或按确定的版本语义解释，不根据当前“常见转账价”填数。

### 09.3 固化不是固定的区块数计时器

TRON 固化依据活跃 SR 的产块进度：至少 19 个不同活跃 SR 的最新成功产块高度满足对应条件。不能把它简化成“过 19 个区块就确认”，也不能把常见约一分钟的时间作为绝对保证。调查时读取 SolidityNode 的固化区块和回执，保存查询时间及块 ID。

`raw_data.timestamp` 是构造交易时的记录；链上时间使用包含区块的时间或回执 `blockTimeStamp`。`expiration` 表示交易的到期边界，不是支付发生时间，也不能假设总是等于 timestamp 加固定 60 秒。

## 10 TRON 只读接口与分页

### 10.1 查询正文、回执和固化锚点

需要自己的 TRON 节点，且 HTTP 接口提供 `/walletsolidity` 路由；示例采用本地 8090。若服务分离为不同端点，应替换正确基地址。已使用托管服务时，按服务规则使用自己的凭据；凭据不进入本篇输出和公开交付。

```bash
TRON_NODE='http://127.0.0.1:8090'
TRON_OUT='./output/account-chains/tron'
TRON_TXID='替换为64位十六进制txid，不带0x'
mkdir -p "$TRON_OUT"
[[ "$TRON_TXID" =~ ^[[:xdigit:]]{64}$ ]] || { printf 'TRON txid格式错误\n' >&2; exit 1; }
BODY=$(printf '{"value":"%s"}' "$TRON_TXID")
printf '%s\n' "$BODY" > "$TRON_OUT/request.json"
curl -sS -H 'Content-Type: application/json' --data-binary "$BODY" \
  "$TRON_NODE/walletsolidity/gettransactionbyid" -o "$TRON_OUT/transaction.json"
curl -sS -H 'Content-Type: application/json' --data-binary "$BODY" \
  "$TRON_NODE/walletsolidity/gettransactioninfobyid" -o "$TRON_OUT/receipt.json"
curl -sS -H 'Content-Type: application/json' --data-binary '{}' \
  "$TRON_NODE/walletsolidity/getnowblock" -o "$TRON_OUT/solidified-block.json"
date -u '+%Y-%m-%dT%H:%M:%SZ' > "$TRON_OUT/collected-at-utc.txt"
```

检查 JSON 是否包含 `Error`；HTTP 200 也可能是接口异常。回执 id、正文 txID 与请求应一致，blockNumber 与已保存固化锚点核对。空响应不等于金额零或交易失败，检查网络、同步、到期与历史范围后再分类。

### 10.2 从合约回执恢复实际移动

成功智能合约交易按顺序读取 `log[]` 与 `internal_transactions[]`。TRC20 Transfer 解码采用已核对代币合约的事件布局，地址按 TRON 字节表示转换，原始数量按该合约精度展示。

internal 记录先排除 `rejected=true` 的未生效移动；其余逐一读取 `callValueInfo[]`：空 tokenId 且正 callValue 表示内部 TRX；非空 tokenId 且正 callValue 表示内部 TRC10。保存 `caller_address`、`transferTo_address`、原始数量和数组位置。节点没有保存 internal 信息时，“数组缺失”只能说明不可见，不证明没有移动。

### 10.3 TronGrid 账户历史

以下路径属于 TronGrid 扩展 API，不是普通自建节点必然提供的接口。已授权服务连接可用于检索线索，最终统计仍应能够回到原始交易与回执。例子不承诺匿名服务无配额限制或永久可用。

`GRID` 填自己的服务基地址；`TRON_ADDRESS`、`TRON_TOKEN` 填经校验的 Base58Check 或 Hex 地址；时间上下限是 UNIX 毫秒整数，固定上限后开始分页。

```bash
GRID='替换为自己的TronGrid基地址'
TRON_ADDRESS='替换为目标账户地址'
TRON_TOKEN='替换为目标代币合约地址'
MIN_MS='替换为开始时间的Unix毫秒整数'
MAX_MS='替换为结束时间的Unix毫秒整数'
curl -sS --get "$GRID/v1/accounts/$TRON_ADDRESS/transactions/trc20" \
  --data-urlencode 'only_confirmed=true' \
  --data-urlencode 'limit=200' \
  --data-urlencode 'order_by=block_timestamp,asc' \
  --data-urlencode "contract_address=$TRON_TOKEN" \
  --data-urlencode "min_timestamp=$MIN_MS" \
  --data-urlencode "max_timestamp=$MAX_MS" \
  -o "$TRON_OUT/history-page-001.json"
```

从已保存响应读取 `meta.fingerprint`，下一页增加以下参数，并把输出文件改为 `history-page-002.json`。除 fingerprint 外，其余筛选参数保持不变，直到没有下一页。

```bash
FINGERPRINT='替换为上一页meta.fingerprint的完整字符串'
# 在相同的 curl 参数中增加：
# --data-urlencode "fingerprint=$FINGERPRINT"
```

该历史接口可能包含 TRC20、TRC721 的转移和授权记录。检查每条记录的类型、合约和事件语义，不能把所有行当成代币到账。每页最多 200 是页大小，不是全历史总数；第一页空、限流、超时或错误也不能统一当作没有历史。

去重优先用原始回执中的事件位置。一个 txid 可以产生多个 Transfer，不能仅用 txid 删除“重复”。服务记录无法定位日志下标时，标记唯一键不完整，回查回执；不要用 amount/from/to 拼键，把同一交易中完全相同的两条事件错误合并。

## 11 匿名竞赛式实战：聊天约定与多链到账

### 11.1 场景与问法

材料含手机镜像、聊天导出、浏览器访问记录、钱包应用数据、若干 EVM/TRON 交易和账户历史页。问法可能是：目标在某日收到多少指定代币、实际到账次数、手续费合计、最终收款地址、授权给了哪个合约、交易在哪条链、是否执行成功。

同一聊天里出现“USDT”“TRC20”“ERC20”或钱包截图，只能帮助定位网络和资产候选。继续核对真实合约地址及成功事件；问 TRC20 时不能统计其他链上同名代币，问到账时不能统计 Approval 或失败请求。

### 11.2 从材料到可复算结论

1. **设备定位：** 保存钱包网络配置、应用记录 ID、聊天消息时间、txid/hash、地址或二维码内容。区分发送请求、客户端提示和链上状态。
2. **网络与资产：** 建立候选表，每项记录网络、账户地址、代币合约、精度、获取位置。未明确网络的线索保持待核对。
3. **执行与资产：** 交易正文描述请求；回执决定执行结果；成功事件或已解释 internal 决定实际资产路径。
4. **完整性：** 固定区块/时间上限，保存所有页或所有区块段，检测错误、重复和缺口。
5. **统计口径：** 交易数、事件数、正金额到账数、流入、流出、净流量、实际费用分别计算。
6. **身份边界：** 钱包地址与设备记录建立关联，地址标签和第三方显示不替代身份材料。
7. **验证：** 随机回查合计表的每条事件定位，并核对全部非成功记录的排除原因。

题目如果问“最后一次到账”，时间相同的记录按区块内交易位置和日志位置排序；不可按金额、页面行号或采集时间排序。仅有 TRON 扩展历史且缺少块内顺序时，说明同时间记录的顺序不能可靠判定。

## 12 可手算离线案例

### 12.1 EVM 多事件、重复页与失败费

模拟网络为 `synthetic`，目标代币 K 精度 6。成功交易 t1 的两条 Transfer 给 X，原始数量分别 25,000,000 和 5,000,000；下一页重复后一条。t2 的 input 请求给 X 8,000,000，但 status=0，logs 为空。

| 项目 | 正确结果 |
| --- | --- |
| 去重后的有效 Transfer 事件数 | 2 |
| 产生到账的外部交易数 | 1 |
| X 的 K 流入 | 30 K |
| 失败请求的到账数量 | 0；保留请求记录，不能把 8 K 加入到账 |
| t1：gasUsed=50,000，实际单价=20 gwei | 执行费 0.001 ETH |
| t2：gasUsed=30,000，实际单价=20 gwei | 执行费 0.0006 ETH |
| 两笔实际执行费合计 | 0.0016 ETH |

继续加入一条零金额 Transfer 和一条 Approval：Transfer 事件数增加 1，正金额到账次数不增加，Approval 单列。改变 decimals 后重新计算展示金额；原始整数和去重键应保持相同。

### 12.2 调用树回滚

成功外层交易中，R→X 的 CALL 携带 0.2 ETH 成功，R→Y 的 CALL 携带 0.1 ETH 失败且被外层捕获，另有 DELEGATECALL 显示 value=0.3 ETH。给定完整调用树、X 分支无失败祖先且不考虑后续其他余额变化时，X 的这次有效流入为 0.2 ETH；Y 分支不计到账；DELEGATECALL 的 value 不能另加成 0.3 ETH 支付。

将外层改为失败后，前面的成功子调用也不能作为最终生效移动。这个练习考查“本节点成功”与“最终状态生效”的差别。

### 12.3 TRON 多资产与收费

固化成功原生交易向 X 支付 2,000,000 sun，fee=100,000 sun；固化成功合约交易给 X 的 K Transfer 原值为 7,500,000，精度 6，fee=300,000 sun；失败合约交易请求给 X 1,000,000，fee=50,000 sun，没有有效 Transfer。

| 项目 | 正确结果 |
| --- | --- |
| 原生 TRX 收入 | 2 TRX |
| 代币 K 收入 | 7.5 K |
| 实际费用合计 | 450,000 sun，即 0.45 TRX |
| 失败调用请求 | 不计为 1 K 到账，费用保留 |
| 合约 fee_limit | 只记录预算，不代替 fee |

费用归属必须按回执或明确材料解释；这个合计表示练习给出的交易费用总量，不自动推出全部由 X 承担。题目问 X 支出费用时，还要核对实际付款方及资源分摊。

## 13 时间、唯一键与最终性

### 13.1 事件记录不能只靠交易 hash

| 对象 | 建议唯一键 | 额外保存 |
| --- | --- | --- |
| EVM 外部交易 | 网络标识 + transactionHash | blockHash、高度、transactionIndex |
| EVM 事件 | 网络标识 + blockHash + transactionHash + logIndex | 合约、topics、data、removed |
| EVM trace | 网络标识 + tx hash + 调用树路径 | 客户端、tracer、选项、祖先错误 |
| TRON 交易 | 网络标识 + txid | 区块号、区块 ID、固化锚点 |
| TRON 日志 | 网络标识 + txid + 原始 log 数组下标 | 合约、topics、data、区块定位 |
| TRON internal | 网络标识 + txid + internal 下标或 hash | rejected、callValueInfo、地址 |
| 代币 | 网络标识 + 合约地址 | 原始数量、精度证据、元数据时点 |

EVM `logIndex` 是该日志在区块中的位置，不是仅在一笔交易中的位置。TRON 原始数组位置与服务展示序号分开记录。相同 txid 的多条事件既可能重复出现于分页，也可能是独立转移；有原始定位后再去重。

### 13.2 时间与顺序

Ethereum 区块 timestamp 使用 UNIX 秒；TRON 区块/回执时间和历史筛选使用 UNIX 毫秒。保留原始数值、字段和单位，再转 UTC；需要北京时间展示时另设列，不改写原值。

链上时间描述包含区块，不能证明用户点击、设备广播或交易所记账的精确时刻。设备时间、应用构造时间、服务器接收时间与链上包含时间分别建表。相同区块时间内的顺序采用 transactionIndex/logIndex 或确定的原始块内顺序。

### 13.3 重组、最终性与快照

EVM 新块和日志可能因重组被替换；日志的 `removed=true` 表示被撤销的记录，不计为当前有效事件。采集完成时复核锚点、边界与事件所在区块 hash，并保留变更前后的快照。Ethereum 主网的 safe/finalized 标签不能无条件代表所有 EVM 链相同的最终性。

TRON 使用固化锚点与 `/walletsolidity` 的交易回执。不同网络、节点同步范围和接口能力分别记录；查询错误、数据缺失与未固化是不同状态。历史材料不完整时，仅给出观察范围内的结论。

## 14 常见扣分点与交付

| 错误 | 应当怎样修正 |
| --- | --- |
| 把 to 合约当最终收款人 | 查看代币事件和内部资产移动 |
| 把 value 当作代币数量 | 原生币与合约代币分别解析 |
| 所有代币默认精度 18 或 6 | 保存合约特定精度证据；未知保持原值 |
| status=1 就声称转账业务成功 | 核对目标资产的事件、状态和合约语义 |
| status=0 的交易费用也删除 | 失败到账不计，实际资源费用保留 |
| gasLimit/cumulativeGasUsed 用来算本交易费 | 使用实际 gasUsed 和实际单价 |
| internal 所有 value 简单累计 | 区分调用类型、错误和失败祖先 |
| TRON 41 前缀当成主网证明 | 核对节点网络、区块锚点和接口对象 |
| fee_limit 当成实际 TRX 费用 | 读取回执 fee 和可解释组成 |
| 授权、零额、NFT 与代币转移混算 | 先分类，再声明次数与金额口径 |
| 只抓第一页就给出全历史合计 | 完成分页/分段，并审计去重与缺口 |
| 仅按 txid 去重事件 | 使用原始日志位置，回查同交易多事件 |
| 当前余额等于历史净流量 | 检查完整范围、其他资产行为与指定高度状态 |
| 地址标签当成人名 | 记录线索依据，与独立设备/账户材料关联 |

交付包含请求与响应清单、区块锚点、事件明细、费用明细、排除记录、分页覆盖表及结果表。所有金额保留原始整数和单位，所有结论能回到原始字段及文件 hash。

```text
资产事件：network / block_id / height / tx_hash / event_position /
          contract / from / to / amount_raw / decimals / display /
          success_state / confirmation_state / evidence_file

排除表：record_key / reason / original_status / evidence_file
覆盖表：query_range / page_or_segment / count / next_cursor / error / sha256
```

检索、解码、离线算术、真实接口响应、链上最终性和身份关联分别报告验证结果。没有复跑材料时不把模板写成已实测流程；不为证明地址归属而发送资金。公开结果不包含助记词、私钥、钱包解锁信息或服务密钥。

## 15 账户 nonce、替换候选与遗漏记录

### 15.1 nonce 是协议序列值，不是收付款次数

nonce 可以理解为账户使用的协议序列值。普通 EVM 外部交易带有发起账户的 nonce，节点据此检查该交易能否按账户状态执行。同一网络下，相同 `from + nonce`、不同 hash 的普通外部交易可能是替换候选；它们不是仅因 hash 不同就应累计的两次支付。

已纳入区块但执行失败的普通交易仍消耗发起账户 nonce；收取代币或接收内部调用不等于发出一笔外部交易。因此 nonce 不能直接用作收款次数或成功付款次数。在支持代码委托的网络中，账户 nonce 还可能因有效授权处理而增加，不能把当前 nonce 一律解释为“该地址历史发了这么多笔交易”。

| 要核对的对象 | 字段/只读材料 | 判读 |
| --- | --- | --- |
| 普通外部交易序列 | `from`、`nonce`、`hash`、`blockHash`、`status` | 分开成功、失败、pending 和冲突候选 |
| 指定块后的账户值 | `eth_getTransactionCount(address, block)` | 是该状态点的 nonce，不提供全部历史交易列表 |
| 当前节点待处理视图 | 同方法的 `pending` 状态 | 取决于该节点所见内存池，不能视为全网完整队列 |
| 代币 permit 序列 | 合约 `nonces(owner)` | 是合约自己的防重放计数，不是账户外部交易 nonce |
| 合约钱包操作序列 | 钱包或 EntryPoint 对应 nonce | 必须按该协议版本和字段解释，不能强行拼入外部交易序列 |

沿用第 05 节的 `rpc_read`、`OUT` 和只读节点。`ACCOUNT` 填完整地址，`AT_BLOCK` 填已保全规范区块的高度；执行后仍核对该高度的区块 hash，历史状态不可用就保留错误。

```bash
ACCOUNT='替换为0x开头的40位账户地址'
AT_BLOCK='替换为0x开头的调查区块高度'
[[ "$ACCOUNT" =~ ^0x[[:xdigit:]]{40}$ && "$AT_BLOCK" =~ ^0x[[:xdigit:]]+$ ]] || {
  printf '账户或区块高度格式错误\n' >&2; exit 1;
}
REQ_NONCE=$(printf '{"jsonrpc":"2.0","id":15,"method":"eth_getTransactionCount","params":["%s","%s"]}' "$ACCOUNT" "$AT_BLOCK")
rpc_read "$OUT/account-nonce-at-block.json" "$REQ_NONCE"
```

返回值使用十六进制数量，整数转换后单列。仅凭“某 nonce 未在浏览器页面找到”，不能证明这笔交易被删掉：列表可能只展示成功转账、只筛一种资产或漏页，也可能混入了授权引起的 nonce 变化。

### 15.2 “加速”“取消”要回到最终执行对象

普通 EVM 交易替换的实质是让同一个账户 nonce 的另一候选得到接受与包含。“加速”可能保留同一调用并改变费用参数；“取消”常表现为另一个低业务内容或自转候选，但协议没有一个通用按钮能撤销已经在规范链执行的旧交易。是否接受替换属于节点内存池策略，不能假设所有节点统一增加固定百分比费用。

保全候选 A、B 的 `chainId/from/nonce/to/value/input`、费用参数、raw transaction（若有）和采集时间；分别查回执，再核对规范链包含关系。若 A、B 属于不同网络，则相同地址与 nonce 不构成同链冲突。

**实战判读：** 设备记录先显示向某合约转币，后显示“取消”，链上最终只包含相同 from/nonce 的自转候选。此时原调用是未确认的付款意图；最终自转是否执行及其费用另记。反过来，旧调用已入规范链，设备“取消”文字不能推翻成功事件。重组时保存旧包含证据和新结果，不按最后一次页面刷新时间选择交易版本。

## 16 ABI、topics 与不同资产事件

### 16.1 ABI 是字节解释规则，topic 位置必须对应参数

ABI（合约应用二进制接口）可以理解为把原始字节解释成函数及参数的说明书。标准函数调用的 `input` 前 4 字节通常是函数签名 Keccak-256 的前 4 字节，后面才是按 ABI 排列的参数。事件日志使用另一种布局：`topics` 保存签名与 indexed 参数，`data` 保存非 indexed 参数。

Keccak-256 和 Python 标准库的 SHA3-256 并不相同，不能用 `hashlib.sha3_256` 生成函数选择器或事件签名。函数选择器只有 4 字节，也可能发生碰撞；查到一个函数名只是候选解释，应继续核对网络、合约地址、历史代码、ABI 和实际参数长度。

| 字节位置 | 标准非匿名事件中的解释 | 必需限制 |
| --- | --- | --- |
| `log.address` | 发出日志的执行账户 | 必须限定链内合约；代理执行时通常是代理地址 |
| `topics[0]` | 完整事件签名的 Keccak-256 | 事件签名不包含 indexed 关键字和参数名 |
| `topics[1..]` | indexed 参数按声明顺序排列 | 不能把“第2个topic”在所有事件中都当收款人 |
| `data` | 非 indexed 参数的 ABI 编码 | 静态参数按词解码，动态参数按偏移与长度解码 |

匿名事件不放通常的签名 topic，indexed 参数从 `topics[0]` 开始。被 indexed 的字符串、数组等复杂值一般记录特定编码的哈希，不能将 32 字节 topic 直接转 UTF-8 来“恢复全文”。地址类型的标准词左侧 12 字节应为零，右侧 20 字节才是地址；有符号数和定长 bytes 的补位规则不同，不能所有词都按无符号整数理解。

**取证顺序：** 先核对链 → 固定发出日志的合约 → 确定当时实现和 ABI → 检查 topics 数与 data 长度 → 按 indexed 声明定位 → 回到成功回执、状态或调用语义。形似 Transfer 的 topic 可以由任意合约发出，签名命中并不自动证明资产真实或控制方身份。

### 16.2 ERC20、ERC721 与 ERC1155 的布局不同

ERC20 通常是一种按整数余额计量的代币；ERC721 为每个独立 tokenId 表示一个 NFT；ERC1155 在同一合约中按 id 区分多个种类，每种 id 又可以有数量。三者分别建立资产键，不能把 NFT 标识当成可除以 decimals 的付款金额。

| 标准事件 | indexed 字段位置 | data 中的内容 | 应统计的对象 |
| --- | --- | --- | --- |
| ERC20 `Transfer(address,address,uint256)` | `[1]=from`，`[2]=to` | 一个 uint256 数量 | 合约特定原始数量，再应用精度 |
| ERC721 `Transfer(address,address,uint256)` | `[1]=from`，`[2]=to`，`[3]=tokenId` | 标准布局通常为空 | `网络 + 合约 + tokenId` 的所有权移动 |
| ERC1155 `TransferSingle(address,address,address,uint256,uint256)` | `[1]=operator`，`[2]=from`，`[3]=to` | id、value 两个 uint256 | `网络 + 合约 + id` 的数量变化 |
| ERC1155 `TransferBatch(address,address,address,uint256[],uint256[])` | `[1]=operator`，`[2]=from`，`[3]=to` | ids、values 两个动态数组 | 每对 id/value 单列，同时保留父日志位置 |

ERC20 与 ERC721 的标准 Transfer 签名类型相同，所以 `topics[0]` 相同；标准 indexed 布局却不同。第 07 节脚本严格要求 ERC20 的 3 个 topics 和一个数量词，不能用于 ERC721。ERC721 创建时允许某些初始分配不发 Transfer，因此只累计日志还未必得到完整历史所有权，应在指定状态点核对 `ownerOf(tokenId)` 与实际实现。

ERC1155 的 operator 是执行转移的账户或合约，不必是被扣减资产的 from。批量事件的 data 起始两词通常是数组偏移，不能把第一词当 id、第二词当数量。按偏移读取长度与元素，检查偏移对齐、范围、数组长度一致；同日志拆分出的记录增加 `batch_item_index`，不能覆盖原 `logIndex`。禁止把不同 id 的数量直接加成一种同质资产。

**构造练习：** 一条 ERC1155 批量事件中，ids 为 `[7,9]`，values 为 `[2,5]`。它贡献 1 条日志、2 条资产明细，分别为 id 7 的 2 单位和 id 9 的 5 单位；不能报告“收到 7 个 NFT”或“2 笔交易”。若两个数组长度不一致，保持解码异常，不能截断后继续给确定合计。

### 16.3 按收款人过滤时保留正确的 topic 空位

下面是标准 ERC20 收款事件的只读查询，沿用第 05 节的 `TOKEN/FROM_BLOCK/TO_BLOCK/rpc_read/OUT`。`address` 必须是调查网络中已经核对的代币合约，`TARGET` 是账户地址。通过 `null` 留出 from 位置，将 to 放到 topic 下标 2。

```bash
TARGET='替换为0x开头的40位收款账户地址'
[[ "$TARGET" =~ ^0x[[:xdigit:]]{40}$ ]] || { printf '账户格式错误\n' >&2; exit 1; }
TOPIC_TO="0x000000000000000000000000${TARGET#0x}"
TRANSFER_SIG='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
REQ_TO=$(printf '{"jsonrpc":"2.0","id":16,"method":"eth_getLogs","params":[{"fromBlock":"%s","toBlock":"%s","address":"%s","topics":["%s",null,"%s"]}]}' "$FROM_BLOCK" "$TO_BLOCK" "$TOKEN" "$TRANSFER_SIG" "$TOPIC_TO")
rpc_read "$OUT/erc20-target-logs.json" "$REQ_TO"
```

这只是条件命中的日志集，还要逐条核对回执、布局、removed、区块和数量；过滤到的零额事件不自动构成正金额到账。标准 ERC721 的 to 也是 `[2]`，但后续需按 NFT 解码；ERC1155 的 to 为 `[3]`，签名也不同。TRON 合约事件采用相应 ABI 时可以按参数位置解码，但外层日志对象、地址表示和事件定位必须沿用 TRON 规则，不直接套用整个 EVM JSON。

### 16.4 approve、permit 与代扣转移属于不同阶段

approve（直接授权）设置 spender 可使用某持有人资产的额度；permit（带签名的授权）允许其他账户提交持有人事先签署的授权请求。授权意味着“获得某范围的使用能力”，并不意味着资产已经转到 spender。

| 对象 | 需要保存的内容 | 资产判读 |
| --- | --- | --- |
| ERC20 `Approval` | 合约、owner、spender、value、位置 | 额度变动，不作为到账 |
| ERC721 `Approval` | tokenId、owner、approved | 单项 NFT 授权，转移时该项授权会重置 |
| `ApprovalForAll` | owner、operator、approved 布尔值及合约类型 | 合约范围操作权限；布尔值不表示币数 |
| ERC2612 permit 请求 | owner/spender/value/deadline、合约 nonce、domain | 只有请求或离线签名时，尚不能证明授权已生效 |
| 授权后的 Transfer/批量转移 | 资产事件、调用路径、状态与成功包含 | 解释真正的扣减与接收，发起方可能不同于 owner |

标准 ERC2612 permit 生效会改 allowance、增加该合约的 `nonces(owner)` 并发 Approval；外部调用者可以是任意地址，不能把支付 gas 的 from 自动写成资产 owner。domain 用于限定签名上下文，通常含链 ID 和验证合约；需按实际实现核对，不能把一个 permit 签名跨所有网络和同名代币使用。

调查授权风险时分开记录：签名请求出现 → 请求是否被链上调用使用 → 额度在何时生效 → 哪次调用实际使用权限 → 什么资产移动。当前 allowance 可能已经被消耗、撤销或改写；题目问授权发生时的额度，优先查当时成功记录与状态。同一外部交易可以先 permit 再 transferFrom，Approval 与 Transfer 分属不同含义，不是两次付款。其他 permit 变体、授权路由合约或自定义钱包权限不能无条件按 ERC2612 参数解释。

## 17 合约创建、代理版本与合约钱包

### 17.1 创建输入与部署后代码是两种字节

创建合约可以理解为执行一段初始化程序，由它返回以后驻留地址上的代码。普通外部创建交易 `to=null`，`input` 是初始化代码及其构造参数；成功回执的 `contractAddress` 才定位新合约。不能把创建 input 的全部字节当作运行时代码，也不能从 `to=null` 单独推出部署成功。

合约也可以在另一个合约执行中通过 CREATE/CREATE2 创建，外层 to 并不为空，回执的顶层 `contractAddress` 也不会列出所有内部创建地址，应检查创建 trace 和实际代码。CREATE2 的地址计算包含创建者、salt 与 init_code 的哈希；不是“看运行时代码相同就应有相同地址”，更不证明不同网络上的同地址具有相同控制方。

沿用第 05 节，在指定高度只读保存地址上的代码。`CONTRACT` 为已核对地址，`AT_BLOCK` 为保全区块高度，不使用 latest 静默替代历史：

```bash
CONTRACT='替换为0x开头的40位合约地址'
[[ "$CONTRACT" =~ ^0x[[:xdigit:]]{40}$ && "$AT_BLOCK" =~ ^0x[[:xdigit:]]+$ ]] || {
  printf '合约或区块高度格式错误\n' >&2; exit 1;
}
REQ_CODE=$(printf '{"jsonrpc":"2.0","id":17,"method":"eth_getCode","params":["%s","%s"]}' "$CONTRACT" "$AT_BLOCK")
rpc_read "$OUT/contract-code-at-block.json" "$REQ_CODE"
```

结果为 `0x` 只说明该状态点没有普通代码可返回，不能仅凭它认定是某人的普通账户；预编译等特殊对象需要按网络规则识别。当前代码、历史创建代码、浏览器展示源码和本地反编译结果分别保全，源码没有对应字节匹配依据时只是候选解释。

### 17.2 代理地址保持不变，实现代码仍可能升级

代理像一个固定入口，把调用转交给另一地址的实现代码；常见 DELEGATECALL 让实现代码在代理的状态和执行地址上下文中运行。用户资产与日志通常关联代理地址，实现地址用于解释执行代码。不能拿今天的实现 ABI 解码过去所有事件。

ERC1967 为常见代理规定了实现、beacon 和管理员存储槽，但它不是所有代理的唯一格式。沿用前面的 `CONTRACT/AT_BLOCK`，从调查高度读取标准实现槽：

```bash
IMPL_SLOT='0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
REQ_IMPL=$(printf '{"jsonrpc":"2.0","id":18,"method":"eth_getStorageAt","params":["%s","%s","%s"]}' "$CONTRACT" "$IMPL_SLOT" "$AT_BLOCK")
rpc_read "$OUT/implementation-slot-at-block.json" "$REQ_IMPL"
```

对于确实采用此槽的实现地址，结果应按 32 字节地址词解释，检查左侧补零并取最后 20 字节，再在同高度保存实现代码。全零不等于“这个合约没有代理”：beacon 代理可以把实现保存在 beacon，其他代理可能采用固定代码或自定义槽。标准 beacon 槽为 `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50`，定位 beacon 后还须在同状态点按其接口查询 implementation。

查询区块 B 的状态通常得到 B 执行完毕后的值，不一定是 B 中每一笔交易执行时的值。若同一区块先交易、后升级，或同一交易升级后继续调用，仅查 B 和 B-1 仍不足以确认目标调用采用哪一实现。此时结合块内顺序、升级日志和包含 DELEGATECALL 目标的 trace/重放结果；不能把块末槽值直接写成每条日志的解释依据。

**实战记录：** `代理地址 / 区块hash / 交易位置 / 实现地址 / 实现代码文件 / ABI依据 / 升级事件位置 / trace路径`。合约名称和代币 symbol 没有变化，不代表逻辑没变化；升级事件缺失也不自动证明未升级，必要时对照状态与执行路径。

### 17.3 合约钱包的付款人要分层描述

合约钱包把授权规则放在程序中，可能通过多签、模块或恢复机制控制资产。提交外部交易的 from、持有资产的钱包地址、批准操作的控制地址，以及代付费用的主体，可能是四个不同对象。

ERC4337 用 UserOperation 表示用户操作，由 bundler 把多个操作放入调用 EntryPoint 的外部交易。`userOpHash` 不是普通 transactionHash，不能直接放入 `eth_getTransactionReceipt` 并将 null 认定为失败；先把操作记录关联到其包含交易、EntryPoint 和钱包，再按实际版本核对操作成功与资产事件。一笔外部交易可以处理多个钱包操作，交易回执外层成功不等于每个操作的业务成功。

支持 EIP7702 的网络还允许 EOA 用授权列表设置代码委托。其代码可以是 23 字节的 `0xef0100` 加 20 字节委托地址，因此“地址有代码就一定是不可发外部交易的传统合约账户”已经不够准确。检查交易类型、授权列表、授权账户与 nonce、委托目标以及调查时点的代码；不要从钱包名称猜是否启用。

EIP7702 有效授权处理会增加授权账户 nonce，并可在外层执行失败时保留委托变更。这里应分别记录协议授权变化与被回滚的普通资产请求，不把 `status=0` 扩张成“这笔交易对账户没有任何影响”。授权发起、提交、执行与真实用户身份仍是独立证据层；本篇只做只读识别，不构造授权、签名或发送操作。

## 18 跨链与二层网络：一条资金路径有多个证明位置

### 18.1 跨链不是把同一 tx hash 搬到另一条链

跨链桥在一条链处理锁定、销毁或消息请求，再在另一条链释放、铸造或执行消息。两端通常是不同交易、不同区块，也可能由不同外部账户提交。同名资产、相同 EVM 地址或接近金额不能单独证明桥接关系。

链 ID 用于界定协议或签名上下文；交易签名的防重放保护不能替代真实网络身份核对，旧式交易和不同授权协议还可能有不同范围。每一端分别记录 chainId、创世块、包含区块和调查时的最终性。TRON 端继续使用该网络自己的身份与固化证据，不套用 EVM 的 chainId 字段。

| 证据层 | 最少保存 | 结论边界 |
| --- | --- | --- |
| 发起链资产动作 | 成功回执、资产合约、数量、实际锁定/销毁事件 | 证明发起侧行为，不能单独证明目的端到账 |
| 桥协议消息 | 已核对桥合约、messageId/nonce/hash、目的链/接收者/载荷 | 消息关联，字段位置按桥的真实 ABI 解释 |
| 目的链执行 | 目的交易与成功回执、桥消息结果、释放/铸造/转移 | 消息执行成功和目标资产移动分别核对 |
| 资产映射 | 两端合约、桥配置、精度和计量规则 | 区分原生资产、包装资产和无关同名资产 |
| 观察结果 | 两端区块锚点、等待/失败/重试/已执行状态 | 目的侧没记录时保留未证实，不直接定损失 |

建议以协议消息标识建立桥接边，并保存组成该标识的链内材料。目的侧金额可能因费用、精度、舍入和桥规则而变化，不要求两端展示小数完全相同；也不能任意调金额去“凑”一个匹配。快速流动性桥的付款可能来自流动性提供方，关联与规范桥锁定/铸造流程不同，应按其合约实际语义解释。

**构造练习：** 发起侧锁定 100 单位，目的侧只发现形似 99 单位的同名代币 Transfer。还需桥合约、消息关联、映射资产和费用规则；缺任何关键关联，就只报告两条独立事件与待验证桥接候选，不能画成确定资金边。

### 18.2 L2 回执、L1 数据与提款证明各回答一个问题

L2（二层网络）把交易执行放在另一网络，并依其协议把数据、承诺或证明交给 L1。它可以继续使用 EVM 的交易与日志对象，但确认和提款路径不是只看一份 Ethereum 主网回执就能完成。

以 OP Stack 的规则说明：节点的 `latest` 可以指已由排序器产出、尚未锚定 L1 数据的 unsafe 头；`safe` 对应从 L1 数据得到的安全头；`finalized` 进一步依赖相应 L1 的最终性。标签所证明的是该协议定义的状态，不保证所有 L2 都采用相同标签、时长或数据方式。

| 调查问题 | 查证位置 | 不能替代的材料 |
| --- | --- | --- |
| 目标 L2 调用是否执行 | L2 transaction、receipt、资产日志与区块 | L1 批次提交回执不能列出所有 L2 业务结果 |
| L2 区块是否获得 L1 数据锚定 | L2 safe/finalized 锚点、L1 批次数据及推导关联 | 单独一个“已提交”界面状态 |
| L1 入金是否在 L2 成功执行 | L1 portal/message 事件与对应 L2 deposit 执行 | L1 入金成功不保证目标合约调用一定成功 |
| L2 提款是否到达 L1 | L2 发起、L1 证明与最终执行、接收方资产变化 | L2 已烧币或消息已证明不能代替最终释放 |

OP Stack 入金可以由 L1 `TransactionDeposited` 派生 L2 deposit transaction。deposit 的 `mint` 先增加 `from` 的 L2 ETH 余额，这一步不随随后执行失败回滚；它不等于 `value` 已成功转给最终目标。因此分别核对铸入余额、`value` 转移和目标调用结果，不能把普通 EVM 调用的回滚口径套成“失败入金没有任何资产效果”。

经 CrossDomainMessenger 记录为 `failedMessages`、且尚未成功中继的跨域消息，可以按对应版本的重放条件处理；这不表示任意原始 deposit transaction 都能重跑。保存消息标识、失败/成功状态和各次调用，避免把重放当成另一笔独立入金。

提款通常分发起、证明和最终执行，必须核对协议参数、证明依赖和最终执行结果。不要把等待窗口结束、`WithdrawalFinalized` 事件出现或门户记录已处理单独等同于最终收款成功：按事件具体成功字段、目的调用和实际资产路径判读。

L1 数据可能以 calldata 或 blob 承载。只保存交易 hash 与区块头，未必保全重建所需的原始批次字节；涉及 blob 时还要确认数据是否仍可获取和归档。无法取得 L1 数据、推导映射或证明时，明确只验证到 L2 回执或桥消息层，不把整个跨层路径写成闭环。上述流程不自动适用于其他 rollup 或侧链。

## 19 TRON 原始对象、TAPOS 与账户权限

### 19.1 txID 来自 raw_data 的 protobuf 字节

TRON 的交易正文使用 protobuf 序列化；JSON 是便于查看的表示。`txID` 是原始 `raw_data` 序列化字节的一次 SHA-256，签名另放 `signature[]`。这与 Bitcoin 的 txid/wtxid 双哈希规则不同，也不是把可见 JSON 文本直接送入 SHA-256。

| 对象 | 实用字段 | 核对方法与限制 |
| --- | --- | --- |
| 交易请求 | `raw_data.contract[].type/parameter` | 先判类型，再区分 TRX、TRC10、合约调用和权限更新 |
| 原始请求字节 | `raw_data_hex` | 有原始 hex 时先重算 txID；没有时不可用 JSON 拼凑替代 |
| 授权证明 | `signature[]`、选用的 `Permission_id` | 包内签名不等于已被固化确认 |
| 有效性范围 | `ref_block_bytes/ref_block_hash`、`expiration` | 与参考区块、网络和实际包含状态核对 |
| 执行与结果 | 固化交易、transaction info、区块 ID | 重新依第 09—10 节判读，不让字节哈希检查替代执行验证 |

TAPOS 是让交易引用近期区块的一组防重放字段，`ref_block_bytes` 和 `ref_block_hash` 只是参考信息的一部分，不是完整区块 ID。它不是账户序列 nonce；两笔交易引用同一 TAPOS 不意味着互为替换。TRON 没有 EVM 式同 from/nonce 取消机制，提交另一笔交易或提高预算不会自动撤回原签名交易，原交易仍需按自身到期和包含状态跟踪。

**离线核对模板：** 将下面保存为 `check_tron_txid.py`，读取第 10 节保全的交易对象。只重算已有字节，不生成签名，也不访问节点；缺少 `raw_data_hex` 时保持不可核对。

```python
import hashlib
import json
import re
import sys
from pathlib import Path

doc = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if not isinstance(doc, dict):
    raise SystemExit('预期保存的交易JSON对象')
if 'Error' in doc or 'error' in doc:
    raise SystemExit('接口错误，不能当作交易对象')
tx = doc.get('result', doc)
if not isinstance(tx, dict):
    raise SystemExit('没有交易对象')
raw_hex = tx.get('raw_data_hex')
txid = tx.get('txID')
if not isinstance(raw_hex, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2})+', raw_hex):
    raise SystemExit('缺少有效raw_data_hex，不能用JSON文本替代原始字节')
if not isinstance(txid, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', txid):
    raise SystemExit('缺少有效txID')
computed = hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest()
if computed != txid.lower():
    raise SystemExit('txID与保存的raw_data_hex不一致，检查材料和响应对象')
print(json.dumps({'txID': computed, 'raw_byte_length': len(raw_hex) // 2,
                  'check': '保存的原始字节与标识一致'}, ensure_ascii=False))
```

```bash
python3 check_tron_txid.py output/account-chains/tron/transaction.json
```

通过只说明原始字节与 txID 自洽。还没有验证 protobuf 字段是否与展示 JSON 一致、签名和权限、资产移动或真实区块包含；这些属于另外的核对层。更改 expiration 等 raw_data 字段会改变实际签名对象，单纯增加同对象的协作签名则不会因此改变 raw_data 的 txID。

### 19.2 owner_address 与所有签名人不是同一个概念

账户权限可以让一个 TRON 账户由多把密钥按权重控制。正文 `owner_address` 标明发起动作的账户，`Permission_id` 选择其权限级别；Owner、Active 与产块专用 Witness 的职责不同，普通合约交易不能用 Witness 权限代替 Active。

实战保全字段为：`账户地址 / 操作合约类型 / Permission_id / 权限threshold / keys地址及weight / operations位图 / 权限更新交易位置 / 固化区块`。核对签名恢复地址是否在当时权限集合、有效权重是否达到阈值、操作类型是否被允许。不要把两项 signature 直接解释为“两个不同账户各付款一次”，也不要把 owner_address 当作实际所有签名人的地址。

当前账户接口显示的是当前权限，不一定是历史交易执行时权限。已有 `AccountPermissionUpdateContract` 会改变后续授权范围；调查失窃、共管或委托操作时，按固化交易和权限更新顺序恢复当时配置。只看到签名或一个新权限地址，不能单独证明设备中的自然人操作、恶意转移或完整控制权。权限分析与 TRC20 Approval 的资产使用额度也分开：两者控制不同层的能力。
