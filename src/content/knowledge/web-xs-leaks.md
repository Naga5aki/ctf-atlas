---
title: "XS-Leaks：侧信道读跨站状态"
summary: "不读响应，只观察加载/数量/时间/缓存/窗口引用：用 frame counting、onload、计时、postMessage 与 XS-Search 把页面状态变成 0/1。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-csrf", "web-xss-vectors", "web-cache-poisoning", "web-request-auth"]
updated: "2026-10-29"
---

XS-Leaks 利用浏览器暴露的**侧信道**推断跨站页面状态：资源是否存在、搜索结果是否为空、用户是否登录、页面里有没有某个 ID。它不读取响应，因此 CORS/CSP 不能完全防住；关键是找到稳定、可重复的 0/1 信号。

> 只对本地靶场或授权站点测试；侧信道会产生大量请求，先控频、先测基线。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 判断可嵌入 | `<iframe src=victim>` 看是否加载 | 看 XFO/CSP |
| 数 iframe | `window.open(url).length` | 跨站可读 `length` |
| 资源是否存在 | `<img onload/onerror>` | 先确认 MIME 行为 |
| 脚本是否存在 | `<script onload/onerror>` | HTML 会 onerror |
| 计时 | `performance.now()` + `fetch(no-cors)` | 重复取中位数 |
| 缓存 | `cache: only-if-cached` | 命中/未命中差异 |
| 窗口引用 | `window.open` 返回值 | COOP 会切断 |
| postMessage | 监听 `message` | 看是否校验 origin |
| XS-Search | 搜索页结构/计时 | 先测已知真/假 |
| 降噪 | 基线 + 10–30 次 + 多数票 | 网络抖动大 |

## 01 原理与成立条件

```text
受害者浏览器 → 跨站请求/嵌入 victim
                     ↓
        浏览器暴露：加载成功、帧数、耗时、缓存、窗口引用
                     ↓
        攻击者页面把差异变成 0/1 → 逐位推断
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 目标状态有差异 | 登录/未登录、有/无结果 | 找其他可观察状态 |
| 差异可观察 | 帧数、加载、时间、缓存 | 换信道或组合 |
| 差异稳定 | 多次测量一致 | 加基线/降噪/换时段 |
| 攻击者能发起 | iframe/资源/窗口/消息 | 换入口或转 CSRF |

XS-Leaks 不是“读响应”，而是“读浏览器的行为”；因此响应头、缓存、页面结构都会影响结果。

## 02 判断与分型

```text
目标页能 iframe？
 ├─ 是 → frame counting / onload / 结构差异
 └─ 否
    资源能跨站加载？
    ├─ 是 → img/script/link onload/onerror
    └─ 否
        能计时？
        ├─ 是 → fetch no-cors / 缓存 / 重定向
        └─ 否
            有窗口引用？
            ├─ 是 → window.length / history / name
            └─ 否 → postMessage / XS-Search 盲测
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| iframe 加载成功 | 无 XFO/frame-ancestors | frame counting |
| `w.length` 随输入变 | 页面 iframe 数不同 | 逐位猜 |
| `img onload` | 资源存在且 MIME 可渲染 | 布尔探测 |
| `script onerror` | HTML/404/语法错 | 先测基线 |
| 耗时稳定差异 | 内容大小/缓存/重定向 | 重复测量 |
| `only-if-cached` 成功 | 资源在缓存 | 缓存探测 |
| `window.open` 返回 null | 弹窗被拦/COOP | 换顶层导航 |
| `message` 收到数据 | 接收端不校验 origin | 读数据/注入 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| onerror 就认为不存在 | MIME/404/网络 | 用已知真/假样本校准 |
| 单次计时差异 | 网络抖动 | 10–30 次取中位数 |
| iframe 高度为 0 | 被 CSS/懒加载 | 看 `length` 而非高度 |
| 搜索页有广告 | 结构噪声 | 找稳定子结构/换信道 |

## 03 利用阶梯

### L0 建立基线

**前提**：有目标页的正常/异常两种状态（登录/未登录、有结果/无结果）。

**步骤**：
1. 用已知真、已知假各测 10 次，记录信号分布。
2. 确认目标页是否可 iframe、资源是否可跨站加载。
3. 记录响应头：XFO、CSP、COOP、CORP、Cache-Control。

**成功标志**：真/假两组信号有明显且稳定的差异。

**失败分支**：无差异→换信道；噪声大→加重复/换时段。

### L1 Frame / onload 布尔探测

**前提**：目标页可嵌入，或资源可跨站加载。

**步骤**：
1. `window.open(url)` 后读 `w.length`。
2. 用 `<img src=... onload=hit onerror=miss>` 判断资源。
3. 用 `<script src=...>` 判断返回是否为 JS。

**成功标志**：信号随输入/状态变化，重复 10 次一致。

**失败分支**：XFO/CSP→转计时；MIME 干扰→先用已知资源校准。

### L2 计时与缓存

**前提**：无法嵌入/加载，但请求耗时或缓存状态有差异。

**步骤**：
1. `fetch(url, {mode:"no-cors", credentials:"include"})` 计时。
2. 每个候选 10–30 次，取中位数，减去基线。
3. 试 `cache: "only-if-cached"` 判断缓存命中。
4. 看 `performance.getEntriesByName(url)` 的 `transferSize`（同源/TAO）。

**成功标志**：真/假分布可分离，命中率 > 90%。

**失败分支**：抖动大→增加样本/换网络；缓存策略一致→换 frame/消息。

### L3 postMessage / XS-Search

**前提**：页面有消息通信，或搜索/查询接口有可观察结构。

**步骤**：
1. 监听 `message`，看 `event.origin` 是否校验、`event.data` 是否含数据。
2. 用 `iframe.contentWindow.postMessage(data, "*")` 触发。
3. XS-Search：按字符集逐位猜，先测已知前缀校准。
4. 每条猜测重复多次，取多数票。

**成功标志**：拿到 Token/用户信息，或逐位还原出目标字符串。

**失败分支**：origin 严格→找同源入口；结果页无结构差异→换计时/缓存。

### L4 组合与影响

**前提**：单一信道噪声大或不稳定。

**步骤**：
1. 组合 frame + 计时 + 缓存，做多信号投票。
2. 用重定向/历史长度判断登录态。
3. 把泄漏结果接到 CSRF/账号接管链。

**成功标志**：稳定还原数据或证明业务影响。

**失败分支**：信道都被响应头切断→转 XSS/CSRF。

## 04 绕过与边界

| 限制 | 影响 | 替代 |
|---|---|---|
| `X-Frame-Options: DENY` | 不能 iframe | 顶层 `window.open` + 计时 |
| `frame-ancestors 'none'` | 同上 | 资源加载/计时 |
| `COOP: same-origin` | 切断窗口引用 | 资源/计时 |
| `CORP: same-origin` | 阻止跨站加载 | no-cors 计时 |
| `Cache-Control: no-store` | 缓存探测失效 | 计时/结构 |
| `Referrer-Policy: no-referrer` | 少 URL 泄漏 | postMessage/其他 |
| 弹窗拦截 | `window.open` 返回 null | 用户手势/顶层导航 |

边界：这些头不能阻止“计时”本身；它们切断的是 frame、资源加载与窗口引用。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| `window.name` | 跨站可写，页面当数据源 | 可能 XSS/泄漏 |
| `history.length` | 判断重定向次数 | 受浏览器限制 |
| 下载/跳转 | 观察是否触发 | 不能读内容 |
| 错误页 | 404/500 结构差异 | 先校准 |
| 登录态 | 头像/用户名/按钮 | frame/计时 |
| 搜索 | 结果数/广告位 | XS-Search |
| postMessage | Token/用户信息 | origin 校验 |

## 06 差异速查

| 项 | 行为 | 影响 |
|---|---|---|
| Chrome | 默认严格 COOP/CORP 趋势 | 信道减少 |
| Firefox | 计时噪声/缓存行为不同 | 需分浏览器测 |
| Safari | ITP/缓存策略 | 计时差异 |
| `no-cors` | 可发请求不可读响应 | 只能计时/缓存 |
| `only-if-cached` | 仅同源缓存 | 跨站常 TypeError |
| `performance` | 受 TAO 限制 | 同源才可读详细 |

## 07 工具与脚本

| 目标 | 工具/代码 |
|---|---|
| 帧计数 | `w.length` |
| 资源探测 | `new Image()` / `<script>` |
| 计时 | `performance.now()` |
| 缓存 | `fetch(url,{cache:"only-if-cached"})` |
| 消息 | `addEventListener("message")` |
| 自动化 | Playwright/Puppeteer 多轮采样 |
| 统计 | 中位数/多数票/置信区间 |

脚本骨架：

```javascript
async function probe(url, n = 15) {
  const xs = [];
  for (let i = 0; i < n; i++) {
    const t0 = performance.now();
    try { await fetch(url, {mode: "no-cors", credentials: "include"}); } catch (e) {}
    xs.push(performance.now() - t0);
  }
  xs.sort((a, b) => a - b);
  return xs[Math.floor(n / 2)];
}
```

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 目标 | 找登录态/搜索结果/资源 | 可观察状态 |
| 2 响应头 | XFO/CSP/COOP/CORP/缓存 | 可用信道 |
| 3 基线 | 真/假各 10 次 | 分布 |
| 4 探测 | frame/onload/计时/消息 | 0/1 |
| 5 降噪 | 重复/多数票/分时段 | 稳定结论 |
| 6 还原 | 逐位/逐项 | 数据 |
| 7 记录 | 脚本、样本、命中率 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| iframe 空白 | XFO/CSP | 转计时/资源 |
| `w.length` 恒 0 | 页面无 iframe/COOP | 换信号 |
| onerror 全命中 | MIME/404 | 用已知样本校准 |
| 计时无差异 | 缓存/内容相同 | 换资源/加噪声 |
| 单次结果跳变 | 网络抖动 | 增加样本 |
| postMessage 无响应 | origin 校验/无监听 | 找同源/其他消息 |
| 搜索结果看不出 | 结构稳定 | 用计时/缓存 |
| 被限流 | 请求过多 | 降频/分批 |

## 10 记录与复现

- [ ] 目标页与状态差异
- [ ] 响应头（XFO/CSP/COOP/CORP/Cache）
- [ ] 信道与脚本
- [ ] 真/假基线、样本数、命中率
- [ ] 还原结果
- [ ] 噪声与失败分支

| 记录项 | 内容 |
|---|---|
| 信道 | frame/onload/计时/缓存/消息 |
| 目标 | URL、状态、结构 |
| 基线 | 真/假分布 |
| 结论 | 数据/登录态/存在性 |
| 限制 | 响应头/噪声 |

相关： [CSRF](/knowledge/web-csrf/)、[XSS 向量](/knowledge/web-xss-vectors/)、[缓存投毒](/knowledge/web-cache-poisoning/)、[越权与访问控制](/knowledge/web-request-auth/)。
