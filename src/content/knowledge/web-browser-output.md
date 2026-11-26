---
title: "XSS 基础：类型、输出与影响验证"
summary: "先分清反射、存储、DOM 三种数据路径，再判断输出上下文与编码是否成立；用执行证据而非弹窗判断影响，并划清 HttpOnly/SameSite/CSP 的边界。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-xss-vectors", "web-csrf", "web-xs-leaks"]
updated: "2026-10-29"
---

页面出现你输入的文字，只说明数据被显示。它是否变成脚本，取决于**输出时的上下文**和**数据路径**。这一页解决“是不是 XSS、是哪一种、影响多大”；具体闭合符与 payload 选择见 [XSS 向量](/knowledge/web-xss-vectors/)。

> 只在本地题目或授权环境验证；用不会破坏数据的标记与 `console.log` 证明执行。

## 00 30 秒速查

| 我要… | 先做… | 备注 |
|---|---|---|
| 判断反射型 | 请求带唯一串，看同一响应 | 刷新后参数消失则标记消失 |
| 判断存储型 | 写入后换页面/换会话读 | 写入包和读出页都要留 |
| 判断 DOM 型 | 看服务端响应是否含 payload | 不含也可能在浏览器执行 |
| 看上下文 | Elements 面板 + 原始响应 | 两边不一致 = 前端改过 DOM |
| 确认执行 | Console 报错/断点/回连 | 弹窗只是最浅证据 |
| 判断影响 | 能否读令牌/发请求/读页面 | 看令牌存哪 |
| 看限制 | `HttpOnly`/`SameSite`/CSP | 三者管的事不同 |
| 记录 | 请求、响应、DOM、截图 | 换会话复现 |

## 01 原理与成立条件

```text
数据源 → 服务端模板/前端 API → 浏览器解析
                                   ├─ 文本节点：只显示
                                   ├─ HTML/属性：可能成元素
                                   └─ 脚本/URL：可能执行
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 输入可达输出 | 参数/存储/消息进入页面 | 换入口/找二次渲染 |
| 编码不匹配上下文 | 该转义的地方没转义 | 找双重解码/前端 sink |
| 浏览器会解释 | 落在 HTML/JS/URL 上下文 | 换上下文 |
| 有触发条件 | 加载/事件/点击 | 换自动触发 |

| 类型 | 数据从哪来 | 何时执行 | 必须留的证据 |
|---|---|---|---|
| 反射 | 本次请求参数/头 | 同一响应解析时 | 该请求 + 该响应 |
| 存储 | 数据库/文件/评论 | 后来访问页面时 | 写入请求 + 读出页面 |
| DOM | URL/hash/storage/postMessage | 前端写入 DOM 时 | 浏览器内 source→sink 链 |

存储型只留读出页，看不出谁写入；DOM 型只看服务端模板会漏掉，因为响应可以是完全静态的。

## 02 判断与分型

```text
提交唯一串后，服务端响应里有它吗？
 ├─ 有 → 反射或存储
 │    ├─ 只在本次响应 → 反射型
 │    └─ 换会话/换页面仍有 → 存储型
 └─ 无 → 可能 DOM 型
      └─ Elements 面板有节点/脚本读到输入 → DOM 型
再看输出位置：
 ├─ 标签之间 → HTML 上下文
 ├─ 属性值内 → 属性上下文
 ├─ href/src → URL 上下文
 ├─ <script> 内 → JS 上下文
 └─ CSS/JSON → 对应解析器
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 原始响应原样含 `<` | 未编码 | 按上下文选向量 |
| `<` 变 `&lt;` | HTML 实体编码 | 试属性/URL/JS |
| 引号被转义 | 属性受保护 | 找无引号属性/模板串 |
| 响应干净但页面有节点 | DOM 型 | Hook sink |
| 刷新后标记消失 | 反射型 | 换存储点 |
| 换用户仍触发 | 存储型 | 记录写入点 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 源码出现 payload | 只是回显/被编码 | 看 Elements 是否成节点 |
| 自己浏览器弹窗 | 只验证了本地 | 换受害者会话/存储型 |
| `alert` 不弹但 Console 报错 | 语法/上下文错 | 修闭合符 |
| `<script>` 不执行 | 经 `innerHTML` 插入 | 用事件属性/SVG |
| CSP 报错但脚本已跑 | 只拦了后续加载 | 看 Console 时序 |

## 03 利用阶梯

### L0 确认数据路径

**前提**：有一个会回显的参数、存储点或前端 source。

**步骤**：
1. 提交唯一串 `xss<canary>123`。
2. 看原始响应是否含它、是否被编码。
3. 刷新/换页面/换会话再读。
4. 响应不含时，在 Elements 面板搜 canary，查 `location.hash`/`postMessage`。

**成功标志**：能判定反射/存储/DOM，并指出输出位置。

**失败分支**：完全无回显→盲 XSS/带外；全编码→找二次解码或其他入口。

### L1 证明脚本执行

**前提**：已定位上下文，且该上下文允许脚本。

**步骤**：
1. 用最小向量（见向量页）触发 `console.log(document.domain)`。
2. 在 Console 看执行结果与报错。
3. 在 Sources 打断点，确认进入预期函数。
4. 记录原始响应、最终 DOM、Console。

**成功标志**：页面上下文里稳定执行，刷新/重放仍可复现。

**失败分支**：语法错误→修闭合；被过滤→L4；CSP→看指令。

### L2 证明跨用户/持久化

**前提**：存储型或 DOM 型，需要证明他人会中招。

**步骤**：
1. 存储型：用户 A 写入，用户 B（另一会话）读取。
2. DOM 型：构造带 payload 的链接，另一会话打开。
3. 确认触发不需要攻击者本地状态。
4. 记录两个会话的请求与页面。

**成功标志**：受害者会话中执行，且不依赖攻击者浏览器。

**失败分支**：仅自己触发→找列表页/详情页/触发条件；需要点击→换自动触发。

### L3 影响验证

**前提**：脚本已能在受害者上下文执行。

**步骤**：
1. 看会话令牌位置：Cookie（`HttpOnly`？）/localStorage/页面变量。
2. `HttpOnly` 时验证能否以受害者身份发请求（CSRF 式）。
3. 读页面敏感数据：`document.body.innerText`、接口返回。
4. 记录影响：账号操作、数据泄露、钓鱼/键盘记录。

**成功标志**：有具体数据/操作证据，而不只是弹窗。

**失败分支**：令牌读不到→转请求伪造/CSRF；权限不足→找高权页面。

### L4 限制下的边界

**前提**：有 CSP、`HttpOnly`、`SameSite` 或框架沙箱。

**步骤**：
1. 读 CSP 原文，确认 `script-src`/`nonce`/`strict-dynamic`。
2. 找同源 JSONP、上传 JS、`<base>`、DOM clobbering。
3. 确认 `HttpOnly` 只挡读 Cookie，不挡发请求。
4. 确认 `SameSite` 只影响跨站自动带 Cookie，不影响同站脚本。

**成功标志**：明确“能做什么/不能做什么”，不把缓解当根治。

**失败分支**：CSP 严格且无同源→转 CSRF/XS-Leaks/点击劫持。

## 04 输出编码与边界

| 上下文 | 数据位置 | 正确做法 | 只做 HTML 正文编码时 |
|---|---|---|---|
| HTML 正文 | 标签之间 | `&` `<` `>` 字符引用 | 正确 |
| 普通属性 | 引号内 `value`/`title` | 再编码包住属性的引号 | 引号可提前闭合 |
| URL 属性 | `href`/`src`/`action` | 先限协议，再编码参数 | `javascript:` 可能残留 |
| 脚本内联 | `<script>` 字符串 | JS 字符串编码/JSON 嵌入 | 脚本语法不认 HTML 实体 |
| 事件属性 | `onclick` 等 | 固定处理函数 + `textContent` | HTML 编码挡不住脚本 |
| CSS | `style`/样式表 | 白名单值，禁止 `expression`/`url(javascript:)` | 解析规则不同 |

| 限制 | 实际作用 | 不能做什么 |
|---|---|---|
| `HttpOnly` | 脚本读不到该 Cookie | 不阻止脚本发请求 |
| `SameSite` | 跨站请求是否自动带 Cookie | 不阻止同站脚本 |
| CSP `script-src` | 限制脚本来源/内联 | 不修复输出编码缺陷 |
| `frame-ancestors` | 限制被嵌入 | 不限制本页脚本 |
| `Report-Only` | 只报告不拦截 | 不能当作已防护 |

编码要发生在写入的那个上下文；入库时做一次总替换，遇到二次解码/另一上下文就失效。富文本需要单独清洗并记录允许标签，清洗前编码、清洗后再解码等于没编码。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Header 回显 | `User-Agent`/`Referer` 进页面 | 存储型 |
| 文件名 | 上传名回显到列表 | 需闭合上下文 |
| Markdown/富文本 | 允许原始 HTML | 渲染器配置 |
| SVG 上传 | `<svg onload>` | `image/svg+xml` |
| `postMessage` | `event.data` 进 `innerHTML` | 查 `event.origin` |
| `window.name` | 跨页保留 | 前端读取 |
| JSONP | `callback` 拼接 | 同源脚本 |
| 错误页 | 参数回显到 404/500 | 反射型 |

## 06 差异速查

| 项 | 行为 | 影响 |
|---|---|---|
| `innerHTML` | 解析 HTML，不执行 `<script>` | 用事件属性/SVG |
| `textContent` | 按文本写入 | 安全 sink |
| `document.write` | 可执行脚本 | 会覆盖页面 |
| `location.hash` | 不发往服务端 | 日志看不到 |
| `HttpOnly` | 阻止 `document.cookie` 读取 | 仍可发请求 |
| `SameSite=Lax` | 顶层 GET 导航可带 | 跨站 POST 不带 |
| CSP nonce | 只允许带 nonce 的脚本 | nonce 可预测即失效 |
| 框架插值 | Vue/React 默认转义 | `v-html`/`dangerouslySetInnerHTML` 例外 |

## 07 工具与验证

| 目标 | 工具/操作 |
|---|---|
| 看原始响应 | DevTools Network → Response |
| 看最终 DOM | Elements → 搜 canary |
| 看执行 | Console、Sources 断点、`debugger` |
| Hook sink | 重写 `innerHTML`/`eval`/`document.write` |
| DOM 型 | DOM Invader、Sources |
| CSP | Console 报错、CSP Evaluator |
| 盲 XSS | 自建回连/XSS Hunter |
| 记录 | 请求、响应、DOM、截图 |

验证顺序：数据路径 → 上下文 → 最小执行 → 跨会话 → 影响。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 参数、表单、Header、文件名 | 可控点清单 |
| 2 分型 | 反射/存储/DOM | 类型结论 |
| 3 上下文 | 原始响应 + Elements | 编码缺口 |
| 4 执行 | 最小向量 + Console | 执行证据 |
| 5 影响 | 令牌/接口/页面 | 影响证据 |
| 6 边界 | CSP/HttpOnly/SameSite | 限制说明 |
| 7 记录 | 双会话/双包 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 输入完全消失 | 被过滤/未回显 | 换参数/存储型/Header |
| 响应有 payload 但不执行 | 上下文/编码 | 看 Elements 与 Console |
| 刷新后不触发 | 反射型 | 找存储点 |
| 换用户不触发 | 输出位置/权限 | 找列表页/详情页 |
| `<script>` 不执行 | `innerHTML` | 换事件属性/SVG |
| `alert` 被拦 | 关键字过滤 | 用 `console.log`/拼接 |
| 只有 CSP 报错 | 来源受限 | 找同源/上传/nonce |
| 读不到 Cookie | `HttpOnly` | 转请求伪造/读页面 |

## 10 记录与复现

- [ ] 数据路径与入口
- [ ] 输出上下文与编码形态
- [ ] 最小执行证据
- [ ] 跨会话/持久化
- [ ] 影响（令牌/接口/数据）
- [ ] 限制（CSP/HttpOnly/SameSite）

| 记录项 | 内容 |
|---|---|
| 类型 | 反射/存储/DOM |
| 入口 | 参数/Header/存储点/source |
| 上下文 | HTML/属性/URL/JS |
| 证据 | 响应、DOM、Console、截图 |
| 影响 | 数据/操作/会话 |
| 限制 | CSP/HttpOnly/SameSite |

相关： [XSS 向量](/knowledge/web-xss-vectors/)、[CSRF](/knowledge/web-csrf/)、[XS-Leaks](/knowledge/web-xs-leaks/)。
