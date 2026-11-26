---
title: "会话与 JWT：固定、伪造与校验缺口"
summary: "先认令牌载体，再测 Session 固定/预测、JWT 声明篡改、alg:none、弱密钥、RS→HS 混淆、kid/jku/jwk 注入与 OAuth state。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-request-auth", "web-python-security", "web-crypto-app", "web-logic"]
updated: "2026-10-29"
---

会话题先问一句：**服务端凭什么认你是你**？答案可能是 Cookie 里的 SessionID、JWT、签名参数，或自定义 token。不同载体对应不同攻击面，共同点是“可伪造/可固定/可重放”。

> 只对本地题目或授权站点测试；伪造管理员令牌前确认授权范围。

## 00 30 秒速查

| 载体 | 先看… | 攻击面 |
|---|---|---|
| Session Cookie | 登录前后 ID 变不变 | 固定/预测 |
| JWT | 三段结构/alg | 篡改/弱密钥 |
| 签名参数 | `sign=md5(...)` | 密钥泄露 |
| Flask/Django Cookie | 是否签名/可解码 | 密钥伪造 |
| OAuth | `state`/`redirect_uri` | CSRF/窃码 |
| SAML | 是否验签 | 签名包装 |

| 我要… | 先试… | 备注 |
|---|---|---|
| 改身份 | 改 payload 后重签 | 无密钥则找 |
| 绕算法 | `alg:none`/大小写 | 空签名 |
| 爆破密钥 | hashcat/jwt_tool | 弱口令 |
| RS→HS | 公钥当 HMAC 密钥 | 看库 |
| kid 注入 | `../../dev/null` | 空密钥 |
| jku 注入 | 自建 JWKS | 白名单 |
| 会话固定 | 登录前后 ID | 不变即中 |

## 01 原理与成立条件

```text
Cookie/JWT → 服务端解析 → 校验签名/有效期 → 取身份 → 授权
                              ├─ 不验签 → 改声明
                              ├─ 弱密钥 → 重签
                              └─ 算法/来源可控 → 换密钥
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 令牌可控 | Cookie/头/参数 | 找其他载体 |
| 校验有缺口 | 算法/密钥/kid | 换攻击面 |
| 声明影响权限 | role/user | 改其他字段 |
| 可观察 | 接口/数据 | 用差异 |

## 02 判断与分型

```text
令牌长什么样？
 ├─ 三段 base64url → JWT
 ├─ 随机串 → SessionID
 ├─ 可解码的签名 Cookie → Flask/Django
 └─ 自定义参数 → 找前端算法
JWT 能改吗？
 ├─ 改 payload 无效 → 验签正常
 ├─ alg:none 有效 → 算法未固定
 ├─ 弱密钥 → 爆破
 └─ kid/jku 可控 → 注入
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 登录后 SessionID 不变 | 固定 | 记录 |
| `alg:none` 通过 | 未固定算法 | 伪造 |
| 字典命中密钥 | 弱密钥 | 重签 |
| `kid` 拼路径 | 注入 | `../../dev/null` |
| `jku` 可指外部 | 信任头 | 自建 JWKS |
| 删 `exp` 仍有效 | 未校验 | 记录 |
| OAuth 无 `state` | CSRF | 测绑定 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 解码出 admin | 只是 base64 | 看是否验签 |
| 改 payload 后 401 | 正常 | 找密钥/算法 |
| `none` 被拒 | 已修 | 换混淆 |
| Cookie 变了 | 正常旋转 | 看是否可预测 |

## 03 利用阶梯

### L0 识别载体与校验

**前提**：有登录/令牌。

**步骤**：
1. 看 Cookie/Authorization/参数。
2. JWT 解码 header/payload，记录 `alg`/`kid`/`exp`。
3. 改一个无权限影响的字段，看重放结果。
4. 登录前后对比 SessionID。

**成功标志**：知道载体、算法、是否验签。

**失败分支**：改字段即失效→验签正常；换算法/密钥面。

### L1 声明篡改与时间

**前提**：JWT 可被服务端接受（或校验不全）。

**步骤**：
1. 改 `role`/`is_admin`/`user`/`sub`。
2. 改/删 `exp`、`nbf`、`iat`。
3. 改 `aud`/`iss` 为期望值。
4. 每次重放并记录响应。

**成功标志**：权限/身份变化。

**失败分支**：签名失败→L2；声明不生效→换字段。

### L2 alg:none 与弱密钥

**前提**：算法未固定或密钥弱。

**步骤**：
1. `alg:none`，签名留空/保留末尾点。
2. 变体：`None`/`NONE`/`nOnE`。
3. 弱密钥：`hashcat -m 16500`/`jwt_tool -C`。
4. 用命中密钥重签管理员声明。

**成功标志**：伪造令牌被接受。

**失败分支**：none 被拒→L3；密钥强→找泄露。

### L3 算法混淆与 kid/jku

**前提**：服务端用非对称算法，或 `kid`/`jku` 可控。

**步骤**：
1. 拿公钥（`/jwks.json`、源码）。
2. RS256→HS256，用公钥字节做 HMAC 密钥。
3. `kid` 路径穿越到 `/dev/null`，用空密钥签。
4. `jku` 指向自建 JWKS，`jwk` 内嵌公钥。
5. 记录服务端接受的算法/来源。

**成功标志**：用攻击者密钥通过验签。

**失败分支**：算法固定→换 kid；jku 白名单→找子域/SSRF。

### L4 会话固定与 OAuth/SAML

**前提**：Cookie 会话或第三方登录。

**步骤**：
1. 登录前记录 SessionID，登录后看是否变化。
2. 采样多个 ID 看时间/自增/弱随机。
3. OAuth：删/固定 `state`，改 `redirect_uri` 到子域/相似域。
4. `code` 重用、PKCE 缺失。
5. SAML：先确认是否验签，再试签名包装。

**成功标志**：会话接管/授权码窃取/身份伪造。

**失败分支**：旋转正常→找预测；OAuth 严格→换入口。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 拒 `none` | 大小写/空签名 | `None` |
| 算法固定 | 算法混淆 | RS→HS |
| 密钥强 | kid 注入 | `../../dev/null` |
| jku 白名单 | 子域/开放重定向 | 自建 JWKS |
| 校验 `exp` | 改 `nbf`/`iat` | 时间边界 |
| Session 旋转 | 预测/固定窗口 | 登录前 ID |
| OAuth state | 删/固定 | CSRF |

边界：JWT 解码不是验签；`alg:none` 只在库允许时有效；RS→HS 需要公钥原文；`kid` 注入依赖拼接方式；会话固定需要攻击者能预设 ID。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 子域 Cookie | `Domain=.example.com` | 子域写同名 |
| 移动 API | 长期 token | 无旋转 |
| 记住我 | 持久 Cookie | 可预测 |
| 邀请链接 | 签名参数 | 密钥泄露 |
| OAuth | `redirect_uri` | 开放重定向 |
| SAML | XML 签名 | 包装 |
| WebSocket | 握手 token | 校验缺失 |

## 06 差异速查

| 库/框架 | 行为 | 影响 |
|---|---|---|
| PyJWT | `algorithms` 需显式 | 配错可混淆 |
| jsonwebtoken | 默认接受算法 | 看版本/配置 |
| Java jjwt | 需设密钥/算法 | 老版本 none |
| Flask | itsdangerous 签名 | 密钥决定 |
| Django | 签名 Cookie | `SECRET_KEY` |
| OAuth | `state`/PKCE | 看实现 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 解码 | `jwt_tool`/CyberChef |
| 爆破 | `hashcat -m 16500` |
| 重签 | PyJWT/`jwt_tool` |
| JWKS | 自建 JSON |
| Session | 对比登录前后 |
| 记录 | 令牌指纹/响应 |

验证顺序：载体 → 篡改 → 算法 → 密钥 → 会话/OAuth。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 载体 | Cookie/JWT/参数 | 类型 |
| 2 基线 | 原令牌重放 | 稳定 |
| 3 篡改 | 声明/时间 | 是否验签 |
| 4 伪造 | none/弱密钥/混淆 | 管理员 |
| 5 会话 | 固定/预测 | 接管 |
| 6 记录 | 令牌/响应 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 改声明 401 | 验签正常 | 找密钥 |
| none 被拒 | 已修 | 混淆/kid |
| 爆破无结果 | 密钥强 | 找泄露 |
| RS→HS 失败 | 公钥格式 | 用 PEM 原文 |
| kid 无效 | 不拼路径 | 换头 |
| Session 变了 | 正常旋转 | 预测/固定窗口 |
| OAuth 拒绝 | 白名单 | 子域/相似域 |

## 10 记录与复现

- [ ] 载体与算法
- [ ] 令牌结构/声明
- [ ] 校验缺口
- [ ] 伪造方式
- [ ] 访问到的接口
- [ ] 会话/OAuth 结果

| 记录项 | 内容 |
|---|---|
| 载体 | Cookie/JWT/自定义 |
| 缺陷 | none/弱密钥/混淆/kid |
| 工具 | hashcat/jwt_tool/PyJWT |
| 结果 | 管理员/数据 |
| 限制 | 算法/白名单 |

相关： [越权与访问控制](/knowledge/web-request-auth/)、[Python 应用安全](/knowledge/web-python-security/)、[密码学应用](/knowledge/web-crypto-app/)、[逻辑漏洞](/knowledge/web-logic/)。
