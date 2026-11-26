---
title: "CSRF：借用身份的请求"
summary: "先确认接口是否靠 Cookie 认证，再判断参数、Token、SameSite 与 Origin 校验；给出 GET/表单/JSON 三种投递、受限绕过与验证记录。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-request-auth", "web-xss-vectors", "web-xs-leaks"]
updated: "2026-10-29"
---

CSRF 不需要读响应，只需要让浏览器**带着受害者的 Cookie** 发出攻击者指定的请求。判断顺序固定：认证方式 → 参数可控性 → 一次性校验 → 浏览器限制 → 实际影响。

> 只对本地靶场或明确授权的站点验证；不要伪造真实用户的转账、改密等敏感操作。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 判断是否 Cookie 认证 | 删除 Cookie 重放，对比是否仍成功 | Bearer/自定义头通常不算 CSRF |
| 找状态变更接口 | 改密、改邮箱、绑定、下单、OAuth | 只读接口转 XS-Leaks |
| 最小 GET PoC | `<img src="http://victim/op?param=value">` | 看服务端是否执行 |
| 最小 POST PoC | 自动提交表单 | 不需要读响应 |
| 发 JSON | `enctype=text/plain` 表单 | 后端不校验 Content-Type 时有效 |
| 看 SameSite | DevTools → Application → Cookies | Lax 仍可能被顶层 GET 绕过 |
| 看 Token | 删除/置空/复用/跨用户 | 一次性且绑定会话才算有效 |
| 看 Origin/Referer | 改成攻击者域名、子域、`null` | 校验用“包含”常见可绕 |
| 看 CORS | 带 `Origin: http://evil.com` | 能读响应则升级为数据窃取 |
| 验证影响 | 用两个账号/两个浏览器 | 记录请求头与结果 |

## 01 原理与成立条件

```text
受害者已登录 → 浏览器保存 Cookie
        ↓
访问攻击者页面 → 页面自动发请求到 victim
        ↓
浏览器按 Cookie 规则自动附带身份
        ↓
服务端只认 Cookie → 执行操作
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 认证靠 Cookie/Session | 浏览器会自动携带 | Bearer/自定义头 → 转 XSS/CSRF token 窃取 |
| 参数可预测 | 不需要旧密码、验证码、随机数 | 找可预测字段或二次验证缺口 |
| 无一次性 Token | 或 Token 未绑定用户/可复用 | 转 XSS 读 Token、CORS 读接口 |
| 有状态变更 | 改密、改邮箱、转账、绑定、下单 | 只读接口转 XS-Leaks |
| 浏览器会发 | SameSite/Origin/CORS 未完全阻断 | 找顶层导航、GET、同站子域 |

只读接口不叫 CSRF；如果它能泄露信息，属于 XS-Leaks 或 CORS 配置问题。

## 02 判断与分型

```text
接口靠 Cookie 认证？
   │否 → 不是 CSRF（看 XSS/越权）
   │是
有状态变更？
   │否 → XS-Leaks / 信息泄露
   │是
有一次性 Token 且绑定会话？
   │是 → 先找 Token 泄露/复用/跨用户
   │否
SameSite 限制？
   ├─ None/未设置 → 直接表单/GET
   ├─ Lax → 试顶层 GET、方法覆盖、同站子域
   └─ Strict → 试同站 XSS、子域、OAuth 回调
Origin/Referer 校验？
   ├─ 不校验 → 直接打
   ├─ 包含匹配 → 构造 `victim.com.evil.com`
   └─ 严格等于 → 找同站入口或 `null`
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 删除 Cookie 后失败 | 依赖 Cookie 身份 | 继续 CSRF |
| 删除 Token 后仍成功 | Token 未校验 | 直接构造 PoC |
| 换用户 Token 仍成功 | 未绑定用户 | 记录跨用户复用 |
| `Content-Type: application/json` 被拒 | 有类型校验 | 试 `text/plain` 表单 |
| `SameSite=Lax` | 跨站 POST 不带 Cookie | 试顶层 GET/方法覆盖 |
| `Origin` 被检查 | 看是否包含匹配 | 试子域/`null`/重定向 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 表单提交后页面报错 | 前端校验/CSRF 中间件 | 看服务端状态码与数据 |
| 请求带 Cookie 但 302 到登录 | 会话过期 | 重新登录再做基线 |
| 浏览器拦截混合内容 | HTTPS 页面发 HTTP | 用同协议或本地环境 |
| `fetch` 被 CORS 拦 | 预检失败 | 换表单/`text/plain`/顶层导航 |

## 03 利用阶梯

### L0 建立基线

**前提**：有两个独立会话（受害者、攻击者），目标接口有状态变更。

**步骤**：
1. 受害者登录，抓一次正常请求，保存 Cookie、Token、Origin、Referer。
2. 删除 Cookie 重放，确认接口依赖 Cookie。
3. 删除/替换 Token 重放，确认 Token 是否校验。

**成功标志**：删除 Cookie 失败、保留 Cookie 成功；Token 删除后仍能成功或换用户仍成功。

**失败分支**：Bearer 认证→转 XSS/令牌窃取；接口只读→转 XS-Leaks。

### L1 GET / 表单投递

**前提**：接口接受 GET 或 `application/x-www-form-urlencoded`，无一次性 Token。

**步骤**：
1. GET：`<img src="http://victim/account/email?email=attacker@evil.com">`。
2. POST：自动提交表单，字段名照抄正常请求。
3. 把 PoC 存成本地 HTML，用受害者浏览器打开。

**成功标志**：服务端返回成功/数据已变更，且请求带受害者 Cookie。

**失败分支**：405/415→换方法或 Content-Type；302 登录→会话失效；Token 校验→L3。

### L2 JSON / 非表单

**前提**：接口收 JSON，但后端不严格校验 `Content-Type`。

**步骤**：
1. 用 `enctype="text/plain"` 表单，把 JSON 塞进字段名/值。
2. 或试 `_method=PUT`、`X-HTTP-Method-Override`。
3. 观察后端是否按 JSON 解析。

**成功标志**：响应与正常 JSON 请求一致，数据变更。

**失败分支**：严格 415→找同站 JSONP/表单接口；预检失败→转 XSS。

### L3 Token / SameSite / Origin 绕过

**前提**：存在 Token、SameSite 或 Origin 校验，但实现有缺口。

**步骤**：
1. Token：删除、置空、复用、跨用户、只校验存在性。
2. SameSite Lax：顶层 GET、`window.open` 后自动提交、方法覆盖。
3. Origin/Referer：`victim.com.evil.com`、`evil.com/victim.com`、`victim.com@evil.com`、`null`（sandbox iframe）。
4. 双提交 Cookie：子域写同名 Cookie，或同时改 Cookie 与参数。

**成功标志**：绕过校验后请求执行，响应与正常请求一致。

**失败分支**：严格同源 + 一次性 Token→转 XSS 读 Token；子域不可控→找 OAuth/登录 CSRF。

### L4 组合与影响

**前提**：已有 CSRF 或 CORS 配置缺陷，需要证明实际影响。

**步骤**：
1. 登录 CSRF：让受害者登录攻击者账号，后续绑定/支付落在攻击者账号。
2. OAuth：`state` 缺失/可预测，绑定攻击者社交账号。
3. CORS：反射 `Origin` + `credentials`，直接读响应，升级为数据窃取。
4. 业务链：改邮箱→找回密码→接管。

**成功标志**：拿到受害者数据、账号控制权或可复现的业务影响。

**失败分支**：影响链断→回到接口清单找下一个状态变更点。

## 04 绕过与边界

| 被拦 | 替代 | 示例 |
|---|---|---|
| 跨站 POST 不带 Cookie | 顶层 GET/方法覆盖 | `?_method=POST` |
| `application/json` 预检 | `text/plain` 表单 | 字段名塞 JSON |
| Token 校验 | 删除/置空/复用/跨用户 | 用 A 的 Token 给 B |
| Origin 包含匹配 | 子域/后缀/`null` | `victim.com.evil.com` |
| Referer 检查 | `Referrer-Policy: no-referrer` | 重定向后裁掉 |
| SameSite=Lax | 顶层导航 + 自动提交 | `window.open` |
| 双提交 Cookie | 子域写 Cookie | `Domain=.victim.com` |

边界：CSRF 不能读响应；能读响应说明 CORS 配错或同源 XSS。不要把它和 XSS 混为一谈。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 登录 CSRF | 强制登录攻击者账号 | 后续操作落在攻击者账号 |
| OAuth `state` | 缺失/固定/可预测 | 账号绑定劫持 |
| 方法覆盖 | `_method=PUT/DELETE` | 表单可发 |
| 同站子域 | 子域 XSS/上传 | SameSite 仍可能带 Cookie |
| `Origin: null` | sandbox iframe/`data:` | 白名单含 `null` 即失效 |
| WebSocket | 跨站握手带 Cookie | 检查 `Origin` |
| 支付/优惠券 | 金额、数量、叠加 | 业务逻辑组合 |

## 06 差异速查

| 项 | 浏览器/框架 | 影响 |
|---|---|---|
| SameSite 默认 | Chrome 等默认 Lax | 跨站 POST 不带，GET 仍可能 |
| `Origin` | 跨站表单会带 | 但 `null` 可伪造场景 |
| `Referer` | 受 `Referrer-Policy` 控制 | 可被裁掉 |
| CORS 预检 | `application/json` 触发 | 表单类型可绕过 |
| Spring Security | 默认开 CSRF | 看是否对 API 关闭 |
| Django | 默认 CSRF token | 看 `csrf_exempt` |
| Laravel | 默认 VerifyCsrfToken | 看 `except` 列表 |

## 07 工具与验证

| 目标 | 命令/操作 |
|---|---|
| 生成 PoC | Burp → Engagement tools → Generate CSRF PoC |
| 看请求头 | DevTools → Network → 复制为 cURL |
| 重放 | `curl -i -b "session=..." -H "Origin: http://evil.com" ...` |
| 看 Cookie | DevTools → Application → Cookies → SameSite |
| 本地 PoC | 存 `csrf.html`，用受害者浏览器打开 |
| 对比 | 带/不带 Token、带/不带 Cookie 各一次 |

验证时看三件事：请求是否带受害者 Cookie、服务端是否执行、响应是否与正常请求一致。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 列出改密/改邮箱/绑定/下单/OAuth | 状态变更接口清单 |
| 2 认证 | 删除 Cookie/Token 重放 | 是否依赖 Cookie |
| 3 限制 | 看 SameSite/Origin/Referer/CORS | 限制矩阵 |
| 4 投递 | GET/表单/JSON/顶层导航 | 最小 PoC |
| 5 绕过 | Token/SameSite/Origin | 可用路径 |
| 6 影响 | 账号接管/数据/业务 | 影响证据 |
| 7 记录 | 请求、头、结果 | 可复现报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 请求带 Cookie 但 302 登录 | 会话过期/跨域 | 重新登录，确认域名/协议 |
| 表单提交 415 | Content-Type 校验 | 换 `text/plain` 或找表单接口 |
| Token 删除后失败 | 服务端校验 | 试复用/跨用户/泄露 |
| SameSite 阻断 | Lax/Strict | 顶层 GET、方法覆盖、同站入口 |
| Origin 拒绝 | 严格白名单 | 找同站子域/`null`/重定向 |
| `fetch` 被 CORS 拦 | 预检 | 换表单/导航 |
| 操作成功但数据没变 | 前端假成功 | 查数据库/接口响应 |
| 只能读不能写 | 只读接口 | 转 XS-Leaks |

## 10 记录与复现

- [ ] 接口、方法、参数、Content-Type
- [ ] Cookie/SameSite/HttpOnly/Secure
- [ ] Token 位置与校验行为
- [ ] Origin/Referer/CORS 结果
- [ ] PoC 文件与浏览器
- [ ] 服务端响应与数据变化

| 记录项 | 内容 |
|---|---|
| 入口 | URL/方法/参数 |
| 认证 | Cookie/Bearer/Token |
| 限制 | SameSite/Origin/Referer/CORS |
| PoC | GET/表单/JSON/导航 |
| 结果 | 状态码/数据变化/影响 |
| 失败 | 哪一层拦住、下一步 |

相关： [越权与访问控制](/knowledge/web-request-auth/)、[XSS 向量](/knowledge/web-xss-vectors/)、[XS-Leaks](/knowledge/web-xs-leaks/)、[CORS 与同源](/knowledge/web-request-auth/)。
