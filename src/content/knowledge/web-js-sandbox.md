---
title: "JS 沙箱逃逸：vm、vm2 与宿主对象"
summary: "Node 的 vm/vm2 不是安全边界：从 constructor.constructor 到 process.mainModule/getBuiltinModule，再到异常/Proxy/import() 与 vm2 CVE；先认版本再选链。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-python-security", "web-prototype-pollution", "web-rce-bypass", "web-js-reverse"]
updated: "2026-10-29"
---

“把用户代码放进 `vm` 里跑”是常见 CTF 形态，也是常见误用。`vm` 文档明确说它**不是安全机制**；`vm2` 曾试图补上，但多次被绕过。先确认用的是哪一种、版本是多少。

> 只对本地题目或授权环境测试；逃逸后通常直接命令执行，注意容器隔离。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 哪种沙箱 | `vm`/`vm2`/`isolated-vm` | 版本 |
| 能否拿宿主 Function | `this.constructor.constructor` | 经典 |
| 有无 `process` | `typeof process` | 未必直接给 |
| 无 require | `process.mainModule.require` | 老 Node |
| Node 22+ | `process.getBuiltinModule` | 新接口 |
| 动态导入 | `import('node:child_process')` | 绕过 require |
| 异常/Proxy | `Error.prepareStackTrace` | vm2 |
| 限制 | 长度/字符/超时 | 先列 |
| 结果 | 命令/文件 | 只读优先 |

## 01 原理与成立条件

```javascript
const vm = require("vm");
vm.runInNewContext(code, {});   // 新上下文
vm.runInThisContext(code);      // 当前上下文（更危险）
new vm.Script(code).runInNewContext(sandbox);
```

`runInNewContext` 只隔离全局对象，不隔离**原型链与宿主对象**；`this.constructor.constructor` 仍能拿到宿主 `Function`。

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 用户代码被执行 | eval/vm/vm2 | 无逃逸面 |
| 宿主对象可达 | 原型/构造器 | 换链 |
| 有 require/process | 或可动态导入 | 换接口 |
| 限制可绕 | 字符/长度 | 编码/拼接 |

## 02 判断与分型

```text
代码在哪跑？
 ├─ vm.runInNewContext → 原型链
 ├─ vm2.VM → 版本/CVE
 ├─ isolated-vm → 基本不可逃
 └─ eval/Function → 直接宿主
有 process 吗？
 ├─ 有 → require/child_process
 ├─ 无 → constructor/globalThis
 └─ 无 require → mainModule/import()
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `typeof process` 为 object | 直接可用 | 取 require |
| `this.constructor.constructor` | 宿主 Function | 执行 |
| 报 `process is not defined` | 全局被删 | `globalThis`/构造器 |
| `require is not defined` | 被拦 | `mainModule`/`import()` |
| `vm2` 版本旧 | CVE | 对照公告 |
| `isolated-vm` | 隔离 | 放弃/找配置 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 能算表达式 | 只证明执行 | 找宿主对象 |
| `process` 是假的 | 沙箱伪造 | 看 `versions`/`mainModule` |
| 一次逃逸失败 | 版本已修 | 换链/换 CVE |

## 03 利用阶梯

### L0 识别沙箱与限制

**前提**：有执行用户代码的入口。

**步骤**：
1. 搜 `vm.`/`vm2`/`isolated-vm`/`eval`。
2. 看 `package.json` 版本与 Node 版本。
3. 列可用全局：`process`/`require`/`Buffer`/`console`。
4. 试长度/字符/超时限制。

**成功标志**：知道沙箱类型、版本、限制。

**失败分支**：无源码→报错/行为推断；强隔离→停。

### L1 constructor 链

**前提**：`vm` 上下文，宿主对象可达。

**步骤**：
1. `this.constructor.constructor("return process")()`。
2. `[].constructor.constructor("return process")()`。
3. `this.constructor.constructor("return this")()` 拿宿主 global。
4. 取 `process` 后读 `version`/`mainModule`。

**成功标志**：拿到宿主 `process`。

**失败分支**：`constructor` 被代理→换 `Error`/Proxy；无宿主→L3。

### L2 取 require / 命令

**前提**：已有 `process` 或宿主函数。

**步骤**：
1. `process.mainModule.require("child_process")`。
2. `module.constructor._load("child_process")`。
3. Node 22+：`process.getBuiltinModule("child_process")`。
4. `import("node:child_process")`（异步）。
5. 只读命令/读文件验证。

**成功标志**：命令执行/文件读取。

**失败分支**：`require` 拦截→`import()`/`binding`；无 `process`→L4。

### L3 vm2 与 CVE

**前提**：使用 vm2 且版本旧。

**步骤**：
1. 读 `package.json` 的 vm2 版本。
2. 对照 CVE：Promise 回调、异常处理、Proxy、`Error.prepareStackTrace`。
3. 用对应 PoC 取 `process`。
4. 不要盲打；版本不符换链。

**成功标志**：在 vm2 内拿到宿主对象。

**失败分支**：版本已修→换 CVE/换入口；vm2 移除→isolated-vm。

### L4 无 process / 强限制

**前提**：全局被删、字符/长度受限。

**步骤**：
1. `globalThis`/`arguments.callee.caller`/`Error` 栈找宿主函数。
2. 拼接/`String.fromCharCode`/模板串绕关键字。
3. `Proxy`/`getPrototypeOf` 触发宿主陷阱。
4. 动态 `import()` 异步外带。
5. 只验证到读文件/固定回显。

**成功标志**：限制下仍取到宿主能力。

**失败分支**：isolated-vm→找配置漏洞；无宿主→转其他漏洞。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 删 `process` | `globalThis`/构造器 | `this.constructor...` |
| 拦 `require` | `mainModule`/`import()` | 动态导入 |
| 拦关键字 | 拼接/`fromCharCode` | 字符串 |
| 长度 | 分步/变量 | 短 payload |
| `constructor` 代理 | `Error`/Proxy | vm2 |
| 超时 | 异步/分步 | 注意题目 |

边界：`vm` 的 `timeout` 只防死循环，不防逃逸；`vm2` 已停止维护；`isolated-vm` 是独立 isolate；前端 JS 沙箱（iframe）与 Node 沙箱不是一回事。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 模板表达式 | 用户公式 | 沙箱 |
| 规则引擎 | 自定义脚本 | vm |
| 插件系统 | 用户 JS | vm2 |
| 在线运行 | 代码执行 | 容器 |
| 前端 iframe | `sandbox` | 浏览器边界 |
| Serverless | 函数 | 隔离 |

## 06 差异速查

| 沙箱 | 隔离 | 逃逸面 |
|---|---|---|
| `vm` | 全局 | 原型/构造器 |
| `vm2` | Proxy | CVE |
| `isolated-vm` | isolate | 基本无 |
| iframe | 同源策略 | 浏览器 |
| 子进程 | 进程 | 权限/容器 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 版本 | `package.json`/`process.version` |
| 探测 | `typeof process` |
| 构造器 | `this.constructor.constructor` |
| 导入 | `import()` |
| 记录 | 沙箱/版本/payload |

验证顺序：沙箱 → 版本 → 宿主对象 → require → 命令。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | vm/eval | 可控代码 |
| 2 沙箱 | 类型/版本 | 限制 |
| 3 基线 | 表达式 | 执行 |
| 4 逃逸 | 构造器/CVE | process |
| 5 影响 | 命令/文件 | 证据 |
| 6 记录 | payload/版本 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 无 process | 全局删除 | globalThis/构造器 |
| 无 require | 拦截 | mainModule/import |
| 语法被拦 | 字符过滤 | 拼接/编码 |
| 超时 | 限制 | 分步/异步 |
| vm2 无效 | 版本 | 换 CVE |
| isolated-vm | 强隔离 | 找配置/停 |

## 10 记录与复现

- [ ] 沙箱类型/版本
- [ ] Node 版本
- [ ] 可用全局
- [ ] 逃逸链
- [ ] 结果
- [ ] 限制

| 记录项 | 内容 |
|---|---|
| 沙箱 | vm/vm2/isolated |
| 版本 | Node/vm2 |
| 链 | 构造器/CVE |
| 结果 | 命令/文件 |
| 限制 | 字符/长度/超时 |

相关： [Python 沙箱](/knowledge/web-python-security/)、[原型链污染](/knowledge/web-prototype-pollution/)、[RCE 绕过](/knowledge/web-rce-bypass/)、[JS 逆向](/knowledge/web-js-reverse/)。
