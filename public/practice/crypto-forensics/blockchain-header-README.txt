区块头与 Merkle 分支离线练习

文件：blockchain_header.py、genesis-proof.json、constructed-merkle-proof.json。
运行：python3 blockchain_header.py genesis-proof.json > result/genesis-check.json
准备好 result 目录，输出路径不能覆盖输入。只用 Python 标准库，不查询网络。

genesis-proof.json 是 Bitcoin 主网创世区块的公开固定向量。
constructed-merkle-proof.json 是三个构造叶哈希的教学树，不是真实区块或付款。
后一向量的 Merkle 分支匹配，但未完成其头所声明的工作量，预期退出码1。

header_hex：80字节区块头的连续十六进制字符，不含区块体。
target_txid：32字节叶哈希，以常见显示字节序填写；本工具不解析原始交易。
transaction_count：输入声明的叶数，正整数；头本身不独立提交这个数字。
transaction_index：从0开始的叶位置，必须小于叶数，不能是布尔值。
siblings：从叶向根的兄弟哈希列表，仍用显示字节序；左右由索引决定。
奇数层末节点复制自己。分支长度须与输入声明的树宽度相容。

退出码0：所给头满足自报target，分支匹配头中的根。
退出码1：格式可计算，但上述局部条件至少一项不匹配，stdout仍有JSON。
退出码2：输入格式错误，stderr给原因，不输出成功报告。

范围：解析版本、父哈希、Merkle根、时间、nBits、nonce；计算双SHA-256。
不验证原始交易TXID、签名、脚本、witness commitment、完整区块及树结构。
不验证难度调整、网络powLimit、累计工作量、活跃链、确认数、余额或身份。
输入声明的叶数并未因此获得独立证明。边界字段保持false或null。
创世区块固定标识匹配只支持公开向量核对，不代表查询了当前节点状态。
