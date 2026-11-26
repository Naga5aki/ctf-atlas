---
title: "原型链污染：从 __proto__ 到 RCE"
summary: "先找递归 merge/解析入口，再试 __proto__ 与 constructor.prototype；按认证字段、child_process 选项、模板引擎、DOM gadget 逐级验证影响。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-xss-vectors", "web-js-sandbox", "web-source-route", "web-rce-bypass"]
updated: "2026-10-29"
---

JavaScript 每个对象都继承 `Object.prototype`。当应用把用户输入递归合并进对象、又不拒绝 `__proto__`/`constructor.prototype` 时，攻击者就能给**所有对象**加属性，包括权限判断用的 `isAdmin`、传给 `child_process` 的 `shell`。

> 只对本地题目或授权环境测试；服务端原型链污染可能导致 RCE，先在容器里验证。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 找 merge 入口 | JSON body、表单、查询串 | 看是否递归合并 |
| 最小探测 | `{"__proto__":{"x":"p"}}` | 看页面/响应是否出现 `p` |
| 换键 | `constructor.prototype`、`prototype` | WAF 可能只拦一个 |
| 权限绕过 | 污染 `isAdmin`/`role`/`verified` | 再访问管理接口 |
| RCE | 污染 `shell`、`NODE_OPTIONS`、`execArgv` | 看 `execFile`/`fork`/`spawn` |
| 模板 | `outputFunctionName`/`escapeFunction` | EJS/Pug/Handlebars 版本 |
| 客户端 | `?__proto__[srcdoc]=...` | 看 DOM gadget |
| 依赖 | `npm ls lodash qs deepmerge` | 对照 CVE |
| 验证 | 带/不带污染键对比 | 记录差异 |

## 01 原理与成立条件

```javascript
const user = {};
user.__proto__.isAdmin = true;   // 污染 Object.prototype
console.log({}.isAdmin);         // true
```

两条路径等价：

- `obj.__proto__`：直接指向构造函数的 `prototype`。
- `obj.constructor.prototype`：通过构造函数拿原型。

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 有递归合并/赋值 | merge/deepcopy/qs 解析 | 找其他 sink |
| 键名未过滤 | `__proto__`/`constructor` 可达 | 换编码/换入口 |
| 属性会被读取 | 权限、配置、模板选项 | 找 gadget |
| 影响可观察 | 响应/权限/命令/弹窗 | 换影响点 |

`Object.create(null)` 创建的对象没有原型，不会被污染；`Map`/`Set` 也不走原型链。

## 02 判断与分型

```text
输入进入递归 merge/深拷贝？
 ├─ 否 → 找 qs/JSON/模板/客户端 merge
 └─ 是
    能否写 __proto__/constructor.prototype？
    ├─ 否 → 换键/编码/其他库
    └─ 是
        影响在哪？
        ├─ 权限字段 → 认证绕过
        ├─ child_process 选项 → RCE
        ├─ 模板选项 → 模板 RCE
        └─ DOM gadget → XSS
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 污染 `x` 后页面出现 `p` | merge 可达原型 | 试权限字段 |
| `isAdmin` 改变 | 权限判断读原型 | 访问管理接口 |
| 命令回显/外连 | `shell`/`NODE_OPTIONS` 生效 | 记录 RCE |
| 模板报错变化 | 选项被污染 | 查引擎版本 |
| DOM 出现属性 | 客户端 gadget | 试 `srcdoc`/`href` |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 响应出现 `p` | 只是回显输入 | 用不带键的请求对比 |
| `isAdmin` 没变 | 用 `hasOwnProperty` | 换字段/换 sink |
| 污染后进程崩溃 | 破坏原型 | 换键/降影响 |
| JSON 解析安全 | 合并才危险 | 找业务 merge |

## 03 利用阶梯

### L0 找 merge / 解析入口

**前提**：应用接收 JSON、表单、查询串，并可能递归合并。

**步骤**：
1. 发 `{"__proto__":{"x":"p"}}`，看响应/页面是否出现 `p`。
2. 换 `constructor.prototype`、`prototype`。
3. 用 `?__proto__[x]=p`、`a[__proto__][x]=p` 试 qs。
4. 记录依赖：`npm ls lodash qs deepmerge hoek`。

**成功标志**：污染键影响后续对象/页面，且不带键时无该效果。

**失败分支**：键被过滤→换编码/换键；无 merge→找客户端/模板 sink。

### L1 认证 / 权限绕过

**前提**：权限判断直接读 `user.isAdmin`/`user.role`。

**步骤**：
1. 注册普通用户，发 `{"__proto__":{"isAdmin":true}}`。
2. 访问管理接口/查看角色字段。
3. 试 `role`、`verified`、`balance`、`status`。

**成功标志**：普通用户获得管理权限/字段变化。

**失败分支**：`hasOwnProperty`/`Map`→换字段/换 sink；会话不共享原型→换入口。

### L2 child_process / RCE

**前提**：服务端有 `execFile`/`fork`/`spawn`，选项来自对象。

**步骤**：
1. 污染 `shell: "/bin/sh"`，看 `execFile` 是否走 shell。
2. 污染 `NODE_OPTIONS: "--require /tmp/x.js"`。
3. 污染 `execArgv`/`argv0`（`fork`/`spawn`）。
4. 用回连/写文件验证。

**成功标志**：命令执行/文件写入/外连。

**失败分支**：选项被显式覆盖→换选项；无子进程→转模板/DOM。

### L3 模板引擎 / DOM XSS

**前提**：模板引擎或前端库把配置对象合并进编译/ DOM。

**步骤**：
1. EJS：污染 `outputFunctionName`（老版本）。
2. Pug：污染 `compileDebug`/`self`。
3. Handlebars：污染 `escapeFunction`。
4. 客户端：`?__proto__[srcdoc]=<script>alert(1)</script>`，看是否进 DOM。

**成功标志**：模板编译执行代码/弹窗。

**失败分支**：版本已修→换库/换 gadget；DOM 无 sink→找 jQuery/路由。

### L4 组合与影响

**前提**：已有污染点，需要扩大影响。

**步骤**：
1. 污染配置让 WAF/鉴权中间件失效。
2. 污染日志/序列化选项，写入文件。
3. 与服务端模板/客户端 XSS 组合，升级为账号接管。

**成功标志**：稳定 RCE/账号接管/数据泄露。

**失败分支**：影响链断→回到 L1 换字段。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 拦 `__proto__` | `constructor.prototype` | `{"constructor":{"prototype":{"x":1}}}` |
| 拦字符串键 | 编码/大小写 | `%5f%5fproto%5f%5f` |
| `Object.create(null)` | 换 sink | 模板/子进程选项 |
| `Map`/`Set` | 换入口 | qs/客户端 |
| 只查一层 | 嵌套/数组 | `a[__proto__][x]` |
| 读取用 `hasOwnProperty` | 换字段 | `role`/`verified` |

边界：污染是全局副作用，可能让进程崩溃；验证用最小键，验证后重启/清环境。

## 05 非典型入口

| 入口 | 载荷 | 注意 |
|---|---|---|
| JSON body | `{"__proto__":{"x":1}}` | 业务 merge |
| qs/查询串 | `?__proto__[x]=1` | 版本/`allowPrototypes` |
| `lodash.merge`/`set` | 旧版本 | 查 CVE |
| `jQuery.extend(true)` | 深拷贝 | 客户端 |
| `hoek`/`deepmerge` | 旧版本 | Node |
| 模板配置 | `outputFunctionName` | EJS/Pug |
| 前端路由 | hash/query 合并 | DOM XSS |
| `postMessage` | 数据进 merge | 客户端 |

## 06 差异速查

| 项 | 行为 | 影响 |
|---|---|---|
| Node `qs` 新版本 | 默认丢弃 `__proto__` | 老版本/配置才可 |
| lodash 4.17.21+ | 修复 merge 污染 | 查版本 |
| `Object.assign` | 浅拷贝 | 通常不污染 |
| `JSON.parse` | 不污染 | 后续 merge 才危险 |
| EJS 3.1.7+ | 修复 `outputFunctionName` | 查版本 |
| 浏览器 | 原型共享同源 | 客户端 gadget |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 依赖 | `npm ls lodash qs deepmerge hoek` |
| 扫描 | `ppmap`、Burp 插件 |
| 手工 | JSON/qs 变体 |
| 回显 | 污染 `x` 看页面 |
| 权限 | 污染 `isAdmin` 看接口 |
| RCE | 污染 `shell`/`NODE_OPTIONS` |
| 客户端 | DevTools 看 DOM/属性 |

验证顺序：污染探测 → 键变体 → 影响点 → 带/不带对比。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | JSON/表单/查询/客户端 | merge 候选 |
| 2 探测 | `__proto__`/constructor | 是否可达 |
| 3 影响 | 权限/子进程/模板/DOM | 影响类型 |
| 4 利用 | RCE/XSS/绕过 | PoC |
| 5 验证 | 带/不带键 | 稳定结果 |
| 6 记录 | 请求/依赖/影响 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 污染键无效果 | 被过滤/不递归 | 换键/换入口 |
| 页面出现 `p` 但权限没变 | 只是回显 | 用对比请求 |
| `isAdmin` 无效 | `hasOwnProperty` | 换字段/sink |
| 命令不执行 | 选项被覆盖 | 换 `execArgv`/模板 |
| 模板报错 | 版本已修 | 换引擎/gadget |
| DOM 不触发 | 无 gadget | 找 jQuery/路由 |
| 进程崩溃 | 原型被破坏 | 换最小键/重启 |

## 10 记录与复现

- [ ] 入口与 merge 函数
- [ ] 污染键与载荷
- [ ] 依赖/版本
- [ ] 影响（权限/RCE/XSS）
- [ ] 带/不带污染对比
- [ ] 环境清理/重启

| 记录项 | 内容 |
|---|---|
| 入口 | JSON/qs/表单/DOM |
| 载荷 | `__proto__`/constructor |
| 影响 | 权限/命令/模板/DOM |
| 依赖 | 库名/版本 |
| 验证 | 响应/回显/弹窗 |

相关： [XSS 向量](/knowledge/web-xss-vectors/)、[JS 沙箱](/knowledge/web-js-sandbox/)、[源码路由](/knowledge/web-source-route/)、[RCE 绕过](/knowledge/web-rce-bypass/)。
