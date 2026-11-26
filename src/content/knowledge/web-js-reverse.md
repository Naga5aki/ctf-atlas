---
title: "JS 逆向：从请求反推签名"
summary: "从一条成功请求出发，用 Initiator/断点/调用栈定位参数改写点，Hook 关键函数，识别 CryptoJS/RSA/国密，扣 webpack 模块或用 AST 解混淆，最后交付可重复的签名脚本。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-leak-files", "web-python-script", "web-crypto-app", "web-js-sandbox"]
updated: "2026-10-29"
---

JS 逆向通常只服务一个目标：**让脚本能重复构造出服务端接受的参数**。不要从“读完整份代码”开始，而是从一条真实请求出发，定位参数在哪个函数被改写、密钥从哪里来、有没有时间/随机数参与。

> 只分析本地题目或授权站点的前端代码；不绕过第三方付费/风控接口。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 哪个文件发的请求 | Network → Initiator | 调用栈入口 |
| 参数何时被改 | XHR/fetch 断点 | 停在发送前 |
| 密钥在哪 | Scope/Closure | `key`/`iv`/`secret` |
| 调了哪些函数 | Hook `stringify`/`fetch`/`encrypt` | 先注入 |
| 什么算法 | CryptoJS/RSA/国密特征 | 看库名 |
| webpack 模块 | `__webpack_require__` | 模块缓存 |
| 混淆 | 字符串数组/平坦化 | AST |
| 浏览器/Node 差异 | `window`/`navigator`/时间 | 补环境 |
| 签名覆盖 | 排序/拼接/编码 | 固定字段测 |
| 复现 | 脚本 + 样例 | 输入输出对齐 |

## 01 原理与成立条件

```text
表单/按钮 → JS 读取字段 → 加密/哈希/拼接 → 发送
                                ├─ 密钥硬编码
                                ├─ 接口下发
                                └─ 时间/随机数参与
服务端 → 验签/解密 → 业务
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 能抓成功请求 | 参数形态 | 先登录 |
| 能定位改写点 | 断点/栈 | Hook/搜索 |
| 能复现算法 | 库/常量 | 扣代码 |
| 服务端接受 | 时间/一次性 | 固定变量 |

## 02 判断与分型

```text
参数像什么？
 ├─ 定长 hex/base64 → 哈希/加密
 ├─ 很长且分段 → RSA/国密
 ├─ 有 sign/nonce/timestamp → 签名
 └─ 明文 → 可能只编码
算法在哪？
 ├─ CryptoJS → AES/DES
 ├─ JSEncrypt → RSA
 ├─ sm2/sm4 → 国密
 └─ 自定义循环 → 异或/流式
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| Initiator 指向 `login.js` | 发送点 | 下断 |
| `CryptoJS.AES.encrypt` | AES | 找 key/iv |
| `setPublicKey` | RSA | 取公钥/填充 |
| `sm4`/`gmssl` | 国密 | 模式/填充 |
| 大数组+索引函数 | 混淆 | AST |
| `__webpack_require__` | 分包 | 模块 id |
| `debugger` 循环 | 反调试 | 绕过/替换 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| base64 像加密 | 只是编码 | 解码 |
| 改了参数仍过 | 未参与签名 | 逐字段测 |
| 本地跑结果不同 | 环境/编码 | 补环境 |
| 断点不进 | 代码已缓存 | 清缓存/Overrides |

## 03 利用阶梯

### L0 请求与参数表

**前提**：有一条成功请求。

**步骤**：
1. 记 URL、方法、`Content-Type`、参数名/长度。
2. 标 `sign`/`nonce`/`timestamp`/`token`。
3. 看 Initiator 调用栈。
4. 失败响应是否提示“签名错/过期”。

**成功标志**：知道哪些参数需要复现。

**失败分支**：找不到 Initiator→全局搜 URL/字段。

### L1 断点与调用栈

**前提**：能复现请求。

**步骤**：
1. XHR/fetch 断点：URL 含 `login`/`api`。
2. 事件断点：`click`/`submit`。
3. 源码断点：搜函数名。
4. 看 Call Stack/Scope/Watch，找参数刚被赋值的那层。

**成功标志**：停在加密/签名函数，能看到入参与密钥。

**失败分支**：栈太深→L2 Hook；代码压缩→格式化。

### L2 Hook 与算法识别

**前提**：调用栈深/混淆。

**步骤**：
1. 页面加载前注入 Hook：`JSON.stringify`、`fetch`、`XHR.send`、`btoa/atob`、`CryptoJS.AES.encrypt`、`crypto.subtle.encrypt`、`JSEncrypt.encrypt`。
2. 打印实参/返回值/`this`。
3. 按特征识别算法与模式。
4. 找 key/iv/公钥来源（硬编码/接口/登录返回）。

**成功标志**：拿到算法、密钥、输入输出样例。

**失败分支**：Hook 太晚→Overrides；库被改→看实现。

### L3 webpack 与解混淆

**前提**：代码分包/混淆。

**步骤**：
1. 搜 `__webpack_require__`/`webpackChunk`，找模块注册表。
2. 在 `__webpack_require__.c` 找已加载模块/导出名。
3. 搜 `login`/`encrypt`/`sign` 回溯模块 id。
4. 扣最短路径到 Node，补 `window`/`document`/`navigator`。
5. 混淆：`js-beautify` → 字符串数组还原 → Babel AST 去 `debugger`/常量折叠。

**成功标志**：纯函数可在 Node 跑出同样结果。

**失败分支**：依赖太多→Playwright 直接调用；平坦化→先还原关键函数。

### L4 WASM / 环境 / 签名重放

**前提**：算法在 WASM/Worker，或签名含时间/随机数。

**步骤**：
1. `.wasm` → `wasm2wat`，找导出函数/内存。
2. Worker/Service Worker 切上下文下断。
3. 固定 `Date.now`/`Math.random`/UA/时区，逐项排除。
4. 签名覆盖：排序/空值/编码（`+` vs `%20`）。
5. 重放：`nonce` 是否一次性、时间窗口多大。

**成功标志**：脚本稳定通过服务端校验。

**失败分支**：WASM 复杂→浏览器调用；时间窗→同步时钟。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 代码压缩 | 格式化/`{}` | Sources |
| 混淆 | AST/字符串还原 | Babel |
| 反调试 | 替换 `debugger`/条件断点 | Overrides |
| 环境检测 | 补 `window`/UA | jsdom |
| 时间签名 | 固定/同步 | `Date.now` |
| 一次性 nonce | 每次现取 | 先请求 |
| WASM | 浏览器调用 | `page.evaluate` |

边界：前端没有真正的秘密；公钥可公开、私钥不会在前端；补环境只需最短路径；签名脚本要固定随机源。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Worker | 加密线程 | 切上下文 |
| Service Worker | 拦截请求 | Application |
| WASM | 导出函数 | `wasm2wat` |
| WebSocket | 帧签名 | 另一套 |
| 小程序 | 包/运行时 | 工具 |
| Electron | 本地 JS | 解包 |

## 06 差异速查

| 特征 | 算法 | 找什么 |
|---|---|---|
| `CryptoJS.AES` | AES | key/iv/mode |
| `JSEncrypt` | RSA | 公钥/填充 |
| `sm2/sm3/sm4` | 国密 | 模式/填充 |
| `md5/sha` | 摘要 | salt/顺序 |
| `^` 循环 | 异或 | 密钥/长度 |
| `btoa` | Base64 | 非加密 |

| 环境 | 差异 | 处理 |
|---|---|---|
| 浏览器/Node | `window`/`crypto` | 补/jsdom |
| 时区 | `Date` | 固定 |
| 随机 | `Math.random` | 固定序列 |
| 编码 | UTF-8/GBK | `TextEncoder` |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 断点 | DevTools Sources |
| Hook | Snippets/Overrides |
| 格式化 | js-beautify |
| AST | Babel/AST Explorer |
| 反混淆 | webcrack/de4js |
| WASM | wabt/Ghidra |
| 浏览器 | Playwright `page.evaluate` |
| 记录 | 脚本/样例 |

验证顺序：请求 → 断点 → Hook → 算法 → 扣代码 → 重放。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 请求 | 参数/Initiator | 目标字段 |
| 2 断点 | 发送前 | 调用栈 |
| 3 Hook | 入参/密钥 | 算法 |
| 4 复现 | Node/浏览器 | 同结果 |
| 5 重放 | 服务端 | 通过 |
| 6 记录 | 脚本/样例 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 断点不进 | 缓存/压缩 | 清缓存/格式化 |
| 栈太深 | 封装 | Hook |
| 结果不同 | 环境/编码 | 补环境 |
| 签名错 | 覆盖/排序 | 逐字段测 |
| 过期 | 时间 | 同步 |
| nonce 重用 | 一次性 | 现取 |
| WASM 难读 | 指令 | 浏览器调用 |

## 10 记录与复现

- [ ] 请求与字段
- [ ] 算法/模式
- [ ] key/iv/公钥来源
- [ ] 编码顺序
- [ ] 时间/随机
- [ ] 脚本与样例
- [ ] 失败差异

| 记录项 | 内容 |
|---|---|
| 入口 | URL/方法 |
| 算法 | AES/RSA/国密 |
| 密钥 | 值/来源 |
| 编码 | base64/hex/URL |
| 复现 | 脚本/命令 |

相关： [源码与元数据泄露](/knowledge/web-leak-files/)、[Python 脚本](/knowledge/web-python-script/)、[密码学应用](/knowledge/web-crypto-app/)、[JS 沙箱](/knowledge/web-js-sandbox/)。
