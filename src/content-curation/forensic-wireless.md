## 01 确认无线材料与验证范围

**分析目标：** 识别目标无线网络与客户端，整理四次握手尝试，判断抓包是否包含可用于离线候选验证的认证材料。需要统计的是握手尝试、完整交换还是有效消息配对，应先明确口径。

**材料：** 已合法取得的 PCAP/PCAPNG 只读副本，其中包含 802.11 管理帧和 EAPOL-Key；目标网络与采集时间说明；有界候选字典。有条件时补充路由器配置与历史管理页面。普通以太网抓包可能只看到解密后的业务流量，不能凭空恢复 SSID、无线 MAC 或握手。

```bash
mkdir -p ./work/wireless
sha256sum ./evidence/wireless.pcapng
capinfos ./evidence/wireless.pcapng
tshark -r ./evidence/wireless.pcapng -q -z io,phs
```

确认链路类型、Radiotap/802.11 信息、捕获时间和截断情况。保留完整抓包进行转换；不要仅保存 EAPOL 后覆盖材料，因为信标、关联帧和 PCAPNG 元信息也可能用于识别 SSID 与检查消息配对。

## 02 SSID、AP 与 STA 的定位

### 02.1 用管理帧建立网络身份

| 标识 | 含义 | 复核重点 |
| --- | --- | --- |
| SSID | 网络名称的字节串 | 区分编码、大小写、隐藏 SSID 与同名网络 |
| BSSID/AP MAC | 无线接入点标识 | 同 SSID 可有多个 BSSID，漫游时不能混成一组 |
| STA MAC | 客户端无线地址 | 地址可能随机化，不直接等于设备或人员身份 |
| 信道与时间 | 采集观察条件 | 跳信道、丢包和设备断连可导致握手片段缺失 |

Wireshark 中先用 `wlan.ssid` 查看信标、Probe Response、关联请求等管理帧；再按 BSSID 和时间定位目标网络。SSID 一般不在四次握手的 EAPOL-Key 内容中；不能把 MAC 地址当 SSID，也不能从不相关的同名网络借用 SSID。

```bash
tshark -r ./evidence/wireless.pcapng -Y 'wlan.ssid' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e wlan.bssid \
  -e wlan.sa -e wlan.da -e wlan.ssid
AP_MAC=02:11:22:33:44:55
tshark -r ./evidence/wireless.pcapng \
  -Y "wlan.bssid == $AP_MAC || wlan.sa == $AP_MAC || wlan.da == $AP_MAC" \
  -T fields -e frame.number -e wlan.sa -e wlan.da -e wlan.ssid
```

上述 AP MAC 是示例，需替换为管理帧和目标网络共同确认的地址。`wlan.sa/da` 是无线帧中的源/目的地址，复杂桥接帧还有发射/接收地址；应回看 To DS/From DS 和 BSSID，不能把任意两列地址机械当 AP/STA。

### 02.2 与后台配置互证

若历史 HTTP 管理响应包含 SSID 与无线 `key`，先确认配置节、接口、BSSID 和时间是否对应目标网络。页面上的占位值、未保存表单、旧配置或其他密钥字段都不能直接当无线口令。正确候选在对应抓包的 MIC 上验证成功，能支持该候选与这组认证材料一致；不证明网络以后仍使用同一口令。

后台认证、DNS 和后续通信的分析见[流量取证](/knowledge/forensic-network-traffic/)。本文只处理无线身份与握手，不将一段管理流量自动归为同一客户端的活动。

## 03 握手分组：去重与可验证材料

### 03.1 四个消息各提供什么

| 消息 | 常见方向与关键内容 | 分析用途 |
| --- | --- | --- |
| M1 | AP → STA，ANonce、Replay Counter | 提供 AP 随机数与会话挑战 |
| M2 | STA → AP，SNonce、MIC | 提供客户端随机数与可验证 MIC |
| M3 | AP → STA，ANonce、MIC、安装/密钥数据 | 继续密钥协商，辅助会话关联 |
| M4 | STA → AP，MIC、确认信息 | 支持交换完成；Nonce 常为零，不能假定包含可用 SNonce |

```bash
tshark -r ./evidence/wireless.pcapng -Y 'eapol.type == 3' \
  -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_epoch -e wlan.bssid -e wlan.sa -e wlan.da \
  -e wlan_rsna_eapol.keydes.msgnr -e eapol.keydes.replay_counter \
  -e wlan_rsna_eapol.keydes.nonce -e wlan_rsna_eapol.keydes.mic \
  -e wlan_rsna_eapol.keydes.key_info.keydes_version
```

`eapol` 也覆盖其他 802.1X 消息；`eapol.type == 3` 缩小到 Key 消息，仍需确认 WPA/RSN Key Descriptor、成对密钥类型与消息内容。Wireshark 的消息序号是解析辅助，关键帧应核对 Key Info、方向、Nonce 和 Replay Counter；字段名与支持版本见 [RSNA EAPOL 字段](https://www.wireshark.org/docs/dfref/w/wlan_rsna_eapol.html)和 [802.1X 字段](https://www.wireshark.org/docs/dfref/e/eapol.html)。

### 03.2 不按“连续四包”机械计数

1. 以 `BSSID/AP + STA + 时间窗口` 初步分组，再结合 ANonce/SNonce、Replay Counter 和消息方向确定同一次交换。
2. 对相同消息、随机数和计数器的重传去重；同时保留重传帧号。中间夹杂其他协议、其他 AP 或其他客户端帧，不影响原组的关联。
3. 新的 ANonce、重新认证或明显分离的时间窗口提示新尝试；同一 AP/STA 不能无条件合并所有 EAPOL。
4. 分别记录“完整 M1–M4 交换数”“去重后的握手尝试数”和“转换器提取的可验证消息配对数”。三者可以不同，导出哈希行数也不等于连接次数。

**关键修正：** 常见 WPA2-PSK 场景下，匹配的 M1+M2 已可提供 ANonce、SNonce、MIC 和完整 M2 EAPOL 数据；M2+M3 也可能提供有效配对。并非必须抓到连续四个消息；也不是任意两个 EAPOL 都有效。只有 M4 且 SNonce 为零、随机数不匹配、跨会话拼接或严重截断时，可能无法进行可靠验证。

### 03.3 实战分组示例

假设同一 AP/STA 依次出现 `M1 → M1 重传 → M2 → 其他业务帧 → M3 → M4`：完整交换计为一次，M1 重传不另算握手；转换器可能保留一条优选消息配对。另一组只出现匹配 M1+M2：可记录为未完整观察到完成的尝试，但可能具备离线验证材料。

结果表保存 `AP、STA、SSID、首末帧、各消息帧号、Nonce、Replay Counter、重传与缺失项、是否形成可验证配对`。统计口径必须随表说明；不能仅根据 EAPOL 包数除以四得出握手次数。

## 04 WPA2-PSK 候选验证的原理

### 04.1 PMK 与 PTK 不是同一种派生

对传统 WPA/WPA2 的口令型 PSK，按实际 SSID 字节和口令编码计算：

```text
PMK = PBKDF2-HMAC-SHA1(passphrase_bytes, SSID_bytes, 4096, dkLen=32)
B = min(AP_MAC, STA_MAC) || max(AP_MAC, STA_MAC)
    || min(ANonce, SNonce) || max(ANonce, SNonce)
PTK = PRF-X(PMK, "Pairwise key expansion", B)
KCK = PTK 的首段；传统此类场景常为前 16 字节
```

`MAC` 为 6 字节、Nonce 为 32 字节；`min/max` 按原始字节序列进行字典序比较，不能比较带冒号的显示字符串或把十六进制文本当原始字节。传统 SHA1 PRF 使用 HMAC-SHA1，包含标签后的零字节分隔、拼接材料和单字节递增计数器；**不能把 PTK 派生替换为再次 PBKDF2**。

派生长度由实际协商的 AKM 与加密套件决定；传统 CCMP 的相关 PTK 常为 48 字节、TKIP 常为 64 字节。这里只解释传统 PSK 流程，其他 AKM 的派生不能强套同一公式。[Hostap 的成对密钥实现](https://raw.githubusercontent.com/vanhoefm/hostap-wpa3/master/src/common/wpa_common.c)和 [SHA1 PRF 实现](https://raw.githubusercontent.com/vanhoefm/hostap-wpa3/master/src/crypto/sha1-prf.c)可核对排序、长度与计数器。

### 04.2 MIC 的字节范围与版本条件

选择匹配的带 MIC 的 EAPOL-Key 帧，保存其中 MIC；复制完整 EAPOL 数据，将 **Key MIC 字段置为全零**，再计算 MIC。参与计算的是从 EAPOL 头开始的实际 EAPOL 帧，长度依据其头中声明的内容，不能把 Radiotap、802.11、LLC 头或额外尾部字节一起计算。

| Key Descriptor Version | 常见 MIC 计算 | 使用条件 |
| --- | --- | --- |
| 1 | HMAC-MD5 | 历史 WPA 相关场景，不能默认用于 WPA2 |
| 2 | HMAC-SHA1 截取前 16 字节 | 传统 WPA2-PSK 常见流程 |
| 3 | AES-128-CMAC | 需同时核对实际 AKM 和派生条件 |
| AKM 定义或其他情况 | 按协商实现确定 | 不使用通用 SHA1 小脚本硬算 |

候选与捕获 MIC 一致，是候选可验证的依据；还需检查消息配对、SSID 与协商条件。WPA3-SAE、企业级 802.1X、过渡模式中的其他认证分支不能直接套用传统 WPA2-PSK 离线字典方式。过渡模式应依据实际协商分支判断，而不是只看网络宣传名称。

## 05 实战：转换与有界字典验证

### 05.1 从抓包生成可审计材料

以下只读取已有材料，不发起无线注入、断连或新的认证尝试。记录工具版本，优先在新的工作目录中运行，避免转换结果与之前的哈希行混在一起。

```bash
hcxpcapngtool --version
hashcat --version
hcxpcapngtool -o ./work/wireless/handshakes.hc22000 \
  ./evidence/wireless.pcapng > ./work/wireless/conversion.txt 2>&1
cat ./work/wireless/conversion.txt
wc -l ./work/wireless/handshakes.hc22000
```

检查转换统计中的 SSID、EAPOL 消息配对、错误和丢失条件；没有产生输出时，回查链路类型、目标管理帧、SSID、完整 EAPOL 与配对关系。转换器提取一条材料不等于无线认证已完整成功。

Hashcat 22000 的消息配对记录使用 `WPA*02*...`；`WPA*01*...` 为 PMKID 类记录，不能把它们都计为四次握手。需要只处理已确认的目标 AP，可从派生哈希文本筛选；AP MAC 写成无冒号的 12 个十六进制字符。

```bash
AP_HEX=021122334455
awk -F '*' -v ap="$AP_HEX" \
  '$1 == "WPA" && $2 == "02" && tolower($4) == ap' \
  ./work/wireless/handshakes.hc22000 > ./work/wireless/target.hc22000
test -s ./work/wireless/target.hc22000
sha256sum ./work/wireless/target.hc22000 ./evidence/candidates.txt
```

筛选只修改派生文本，不裁掉抓包中的管理帧或元信息；实际大小写、AP/STA 和 SSID 应继续回到帧中核对。工具流程与格式见 [Hashcat WPA/WPA2 指南](https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2)。

### 05.2 执行候选字典并保存结果

```bash
hashcat -m 22000 -a 0 ./work/wireless/target.hc22000 \
  ./evidence/candidates.txt --session wireless-review \
  --potfile-path ./work/wireless/review.potfile
hashcat -m 22000 ./work/wireless/target.hc22000 --show \
  --potfile-path ./work/wireless/review.potfile
```

字典来自当前分析允许使用的候选范围，记录行数、编码与摘要。不预设固定口令，不使用无限扩展的掩码代替已有线索。对传统口令型 PSK，候选通常是 8–63 个 ASCII 字符；64 个十六进制字符表示的原始 PSK/PMK 与口令型输入的处理不同，不能混入后宣称按同一派生验证。

**结果判读：** `Recovered` 或 `--show` 的结果需对应目标哈希行；`Exhausted` 仅说明本轮候选未验证成功，不说明口令不存在或网络使用其他协议。重用 potfile 会显示历史命中，因此应保存本轮独立 potfile、输入摘要与会话日志。

### 05.3 交叉验证与结果边界

1. 用命中候选验证同一 AP/SSID 下**另一组独立的有效配对**，若材料存在；不是重复验证同一重传帧。
2. 将验证结果与采集时管理配置或页面中的目标无线密钥相对照，核对 SSID、接口和时间。
3. 有需要且材料满足条件时，使用协议解析器检查已授权的抓包解密结果是否形成合法上层协议；不能把任意可打印字节当成功解密。
4. 报告保留 AP/STA、SSID 字节、消息配对帧号、协商条件、候选范围、工具版本和验证结果。未复跑实际抓包时，只能说明示例流程与验证条件，不能称为真实材料已验证。

候选验证成功不能独立证明设备持有人、攻击者身份、口令由谁输入，或后来业务流量由该 STA 发起。此类归因仍需时间、网络地址映射、后台日志和终端记录共同支持。
