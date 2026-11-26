---
title: "Python 应用安全：pickle、沙箱与 Flask"
summary: "三条主线：pickle 反序列化到命令执行、受限沙箱的 MRO/子类逃逸、Flask session 伪造与 debug PIN；附 SSTI 最小路径与 yaml/torch 入口。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-template-injection", "web-js-sandbox", "web-source-route", "web-python-script", "web-ssti-python"]
updated: "2026-10-29"
---

Python Web 题的三条主线：**pickle 反序列化**（对象可控）、**沙箱逃逸**（代码受限）、**Flask 配置**（session/PIN/模板）。共同点是“从可控输入走到 `os.system` 或文件读取”。

> 只对本地题目或授权环境测试；pickle 反序列化通常等价于命令执行。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 找反序列化 | `pickle.loads`/`yaml.load`/`torch.load` | 输入从哪来 |
| 构造 pickle | `__reduce__` 返回 `(callable,args)` | 本地生成 |
| 绕黑名单 | `getattr`/拼接/`sys.modules` | 看检查哪一层 |
| 沙箱逃逸 | `().__class__.__base__.__subclasses__()` | 找可用类 |
| 读文件 | `_io.FileIO`/`open` | 子类索引 |
| 命令 | `os._wrap_close`/`subprocess.Popen` | `__globals__` |
| Flask session | 解码/爆破/伪造 | `flask-unsign` |
| debug PIN | 读 machine-id/MAC | 仅 debug |
| SSTI | `{{7*7}}` | 见模板页 |

## 01 原理与成立条件

```text
可控输入 → pickle.loads / eval / render_template_string
              ├─ 反序列化 → __reduce__ → callable
              ├─ 沙箱 → 对象图 → 子类/模块
              └─ 模板 → 表达式 → globals
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 输入进入危险函数 | pickle/eval/模板 | 找其他入口 |
| 类/对象图可达 | 内建/子类/模块 | 换链 |
| 过滤只查字符串 | 运行时仍可构造 | 用拼接/编码 |
| 有输出通道 | 回显/文件/网络 | 建通道 |

## 02 判断与分型

```text
输入进入哪个函数？
 ├─ pickle.loads → __reduce__ 链
 ├─ yaml.load 非 Safe → !!python/object
 ├─ eval/exec → 直接代码
 ├─ render_template_string → SSTI
 └─ Flask Cookie → session 签名
受限在哪？
 ├─ 黑名单 → 拼接/别名
 ├─ 白名单 → 找允许的 callable
 └─ 无 builtins → 子类回溯
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 报 `UnpicklingError` | 进入 pickle | 修 opcode |
| 过滤 `os`/`system` | 字符串黑名单 | 拼接/别名 |
| `__builtins__` 被删 | 沙箱 | 子类回溯 |
| Cookie 形如 `base64.timestamp.sig` | Flask session | 解码/爆破 |
| `/console` 要 PIN | debug | 读机器信息 |
| `{{7*7}}` 变 49 | SSTI | 找 globals |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| Base64 只是 JSON | 非 pickle | 找调用点 |
| `yaml.load` 用了 SafeLoader | 安全 | 换入口 |
| 沙箱报语法错 | 表达式不合法 | 修 payload |
| session 签名失败 | 密钥错 | 爆破/找泄露 |

## 03 利用阶梯

### L0 定位入口与限制

**前提**：有源码或可观测输入。

**步骤**：
1. 搜 `pickle.loads`/`yaml.load`/`eval`/`render_template_string`/`session`。
2. 确认输入来源与编码。
3. 看黑名单/白名单/`__builtins__`。
4. 确认 Python/Flask/Werkzeug 版本。

**成功标志**：知道进入哪个函数、限制是什么。

**失败分支**：无源码→黑盒试报错；非 Python→换页。

### L1 pickle 反序列化

**前提**：输入进入 `pickle.loads`。

**步骤**：
1. 本地用 `__reduce__` 生成：`return (os.system, ("id",))`。
2. 提交并观察回显/副作用。
3. 黑名单时换 `subprocess.getoutput`/`os.popen`/`pty.spawn`。
4. 用 `pickletools.dis` 看 opcode。

**成功标志**：命令执行/文件读写。

**失败分支**：`find_class` 白名单→L2；输入被签名→找密钥。

### L2 受限 Unpickler 与沙箱

**前提**：`find_class` 只允许部分类，或代码在 `eval` 沙箱里。

**步骤**：
1. 看白名单允许的 callable：`eval`/`exec`/`getattr`/`builtins`.
2. 用 `getattr`+`__import__` 取模块。
3. 沙箱：`().__class__.__base__.__subclasses__()` 找 `_io.FileIO`/`os._wrap_close`。
4. 关键字过滤：拼接/`getattr`/十六进制/`bytes.fromhex`。

**成功标志**：在白名单/沙箱下读到文件/执行命令。

**失败分支**：白名单极窄→找已加载模块别名；对象图封闭→换入口。

### L3 Flask session 与 debug PIN

**前提**：Flask 应用，session 在 Cookie 或 debug 开启。

**步骤**：
1. `flask-unsign --decode --cookie '...'` 看结构。
2. 弱密钥：`--unsign --wordlist`。
3. 已知密钥：`--sign --cookie '{"admin":true}'`。
4. debug PIN：读 `/etc/machine-id`、`/proc/self/cgroup`、MAC，按 Werkzeug 版本计算。

**成功标志**：伪造管理员 session/进入控制台。

**失败分支**：密钥强→找源码泄露；debug 关闭→换入口。

### L4 SSTI 与其他入口

**前提**：模板字符串可控，或 `yaml.load`/`torch.load` 等。

**步骤**：
1. `{{7*7}}` 确认模板执行。
2. `{{config}}` 看密钥/配置。
3. `{{cycler.__init__.__globals__.os.popen('id').read()}}`。
4. `yaml.load`：`!!python/object/apply:os.system ["id"]`。
5. `torch.load`/`pandas.read_pickle` 按 pickle 处理。

**成功标志**：命令执行/配置泄露。

**失败分支**：沙箱模板→见模板页；`SafeLoader`→换入口。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 过滤 `os` | `posix`/`sys.modules` | 别名 |
| 过滤 `system` | `popen`/`getoutput`/`execv` | 换函数 |
| 过滤 `__` | 拼接/`getattr` | `"__cla"+"ss__"` |
| 删 `__builtins__` | 子类回溯/`warnings` | `__globals__` |
| 白名单 | 允许的 callable | `eval`/`getattr` |
| 字符集 | 十六进制/`chr` | `bytes.fromhex` |

边界：pickle 反序列化不可信数据等价于 RCE；沙箱逃逸依赖版本与已加载类，索引会随环境变化。

## 05 非典型入口

| 入口 | 说明 |
|---|---|
| `yaml.load` | 非 `SafeLoader` 可构造对象 |
| `jsonpickle` | 反序列化可执行 |
| `pandas.read_pickle` | pickle |
| `torch.load` | `weights_only=False` |
| `subprocess` 拼接 | 命令注入 |
| `eval`/`exec` | 直接代码 |
| Flask `send_file` | 路径穿越 |
| `render_template_string` | SSTI |

## 06 差异速查

| 项 | 行为 | 影响 |
|---|---|---|
| pickle 协议 0-5 | opcode 不同 | 手写用 0 |
| `find_class` | 白名单入口 | 决定可用类 |
| Python 3.11+ | 子类索引变化 | 动态查找 |
| Flask session | itsdangerous 签名 | 密钥决定 |
| Werkzeug PIN | 版本算法差异 | 逐项读文件 |
| Jinja2 | 沙箱/非沙箱 | 看环境 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 生成 pickle | 本地 `pickle.dumps` |
| 看 opcode | `pickletools.dis` |
| Flask session | `flask-unsign` |
| PIN | 按版本计算脚本 |
| SSTI | 手工/模板工具 |
| 记录 | payload、版本、结果 |

验证顺序：入口 → 限制 → 最小执行 → 稳定复现。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | pickle/eval/模板/Cookie | 可控点 |
| 2 限制 | 黑名单/白名单/版本 | 约束 |
| 3 基线 | 最小 payload | 是否执行 |
| 4 绕过 | 拼接/别名/子类 | 可用链 |
| 5 影响 | 命令/文件/session | 证据 |
| 6 记录 | 请求/脚本 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| `UnpicklingError` | opcode/长度 | 本地重生成 |
| 黑名单拦截 | 字符串检查 | 拼接/别名 |
| 白名单拒绝 | `find_class` | 找允许 callable |
| 子类索引报错 | 环境差异 | 动态查找 |
| session 签名失败 | 密钥 | 爆破/找泄露 |
| PIN 不对 | 版本/机器信息 | 逐项核对 |
| SSTI 不执行 | 沙箱/转义 | 见模板页 |

## 10 记录与复现

- [ ] 入口与函数
- [ ] 版本（Python/Flask/Werkzeug）
- [ ] 限制与绕过
- [ ] 最终 payload
- [ ] 结果（命令/文件/session）
- [ ] 复现脚本

| 记录项 | 内容 |
|---|---|
| 入口 | pickle/eval/模板/Cookie |
| 限制 | 黑名单/白名单/沙箱 |
| 链 | `__reduce__`/子类/globals |
| 结果 | 命令/文件/管理员 |
| 版本 | 决定边界 |

相关： [模板注入](/knowledge/web-template-injection/)、[JS 沙箱](/knowledge/web-js-sandbox/)、[源码路由](/knowledge/web-source-route/)、[Python 脚本](/knowledge/web-python-script/)、[SSTI](/knowledge/web-ssti-python/)。
