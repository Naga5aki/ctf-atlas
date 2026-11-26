---
title: "PHP 反序列化：格式、POP 链与 phar"
summary: "从序列化字节到对象方法：可见性前缀、魔术方法触发点、POP 链、__wakeup 绕过、字符逃逸、phar/session 与原生类利用。"
module: Web
topic: "Web漏洞"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-php-features", "web-upload-bypass", "web-php-audit", "web-file-include", "web-runtime-boundary"]
updated: "2026-10-29"
---

反序列化题的核心是**把“对象属性可控”变成“方法被调用”**。先找 `unserialize()` 入口，再找类里的魔术方法，最后找能执行/读写/请求的 sink。没有链时，先看原生类。

> 只对本地题目或授权环境测试；`phar`/`session` 利用会写文件，注意清理。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 找入口 | `unserialize`/Cookie/session | Base64 先解码 |
| 认格式 | `O:`/`a:`/`s:` | 长度按字节 |
| 找起点 | `__destruct`/`__wakeup` | 属性可控 |
| 找跳板 | `__toString`/`__call` | 方法调用链 |
| 找 sink | `system`/`file_put_contents`/`include` | 执行/写/读 |
| 绕 `__wakeup` | 属性个数大于真实值 | 仅老版本 |
| 字符逃逸 | 过滤改变长度 | 对齐 `s:` 长度 |
| 无显式入口 | `phar://`/session | 文件函数触发 |
| 原生类 | `SoapClient`/`SplFileObject` | 看扩展 |

## 01 原理与成立条件

```text
序列化字节 → unserialize() → 还原对象
                                ├─ __wakeup()
                                ├─ __destruct()
                                ├─ __toString()（被当字符串时）
                                └─ __call()（调用不存在方法时）
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 有反序列化入口 | 请求/Cookie/缓存/文件 | 找 phar/session |
| 类可加载 | 项目/框架/原生类 | 找 autoload |
| 魔术方法有 sink | 文件/命令/网络 | 找跳板 |
| 属性可控 | 序列化串可写 | 找字符逃逸 |

## 02 判断与分型

```text
输入是序列化串吗？
 ├─ O:/a:/s:/i: → 直接反序列化
 ├─ Base64 → 解码再看
 ├─ Cookie/session → 查处理器
 └─ 文件路径可控 → 试 phar://
有链吗？
 ├─ 项目类有 __destruct/__wakeup → 构造 POP
 ├─ 只有 __toString → 找字符串拼接点
 └─ 无业务类 → 原生类/框架链
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `unserialize(): Error at offset` | 长度/格式错 | 数字节 |
| 对象属性被过滤 | 键名/值受限 | 换属性/逃逸 |
| `__wakeup` 里 exit | 入口被拦 | 绕 wakeup/换 destruct |
| Base64 解码含 `O:` | 序列化 | 构造 |
| 文件函数报 `phar` | phar 可用 | 传 phar |
| session 文件可包含 | 反序列化 | 伪造 session |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| Base64 只是 JSON | 非序列化 | 找调用点 |
| 序列化串但不进函数 | 只是数据 | 找 `unserialize` |
| `__destruct` 存在但无 sink | 钩子空 | 找跳板 |
| phar 生成失败 | `phar.readonly=1` | 本地生成后上传 |

## 03 利用阶梯

### L0 认格式与入口

**前提**：请求/Cookie/文件中有疑似序列化字节。

**步骤**：
1. 找 `unserialize`/`session_start`/缓存读取。
2. 解码 Base64/URL 编码，确认 `O:`/`a:`。
3. 数字节：`s:长度:"内容"` 必须一致。
4. 本地 `php -r 'var_dump(unserialize(...));'` 验证。

**成功标志**：能稳定还原出对象/数组。

**失败分支**：长度错→重算；无入口→找 phar/session。

### L1 单类属性控制

**前提**：有 `unserialize`，且某个类的属性会影响行为。

**步骤**：
1. 找 `__destruct`/`__wakeup`/`__toString`。
2. 改属性值（路径/命令/URL）。
3. 构造对应可见性的键名（public/protected/private）。
4. 提交并观察副作用。

**成功标志**：属性改变导致文件/请求/输出变化。

**失败分支**：属性被过滤→L3；无 sink→L2。

### L2 POP 链

**前提**：多个类可组合，起点方法调用其他对象方法。

**步骤**：
1. 起点：`__destruct`/`__wakeup` 且属性可控。
2. 跳板：找 `$this->x->method()`、字符串拼接（`__toString`）、`call_user_func`。
3. sink：`system`/`exec`/`file_put_contents`/`include`。
4. 逐层嵌套序列化，本地验证。

**成功标志**：还原即触发 sink（命令/文件/请求）。

**失败分支**：链断→换起点/找新跳板；类被 final→换类。

### L3 `__wakeup` 绕过与字符逃逸

**前提**：`__wakeup` 拦截，或过滤函数改变字符串长度。

**步骤**：
1. 老版本：属性个数写大于真实值（CVE-2016-7124）。
2. 变长逃逸：`x`→`xx`，多出的字符挤进结构。
3. 变短逃逸：`xx`→`x`，吃掉长度声明。
4. 本地 `unserialize` 验证不报错。

**成功标志**：绕过校验/伪造出新属性。

**失败分支**：版本已修→换 `__destruct`；长度对不上→重算填充。

### L4 phar / session / 原生类

**前提**：没有显式 `unserialize`，但有文件函数/session/原生类。

**步骤**：
1. phar：本地生成带 metadata 的 phar，上传后用 `phar://` 触发。
2. session：`upload_progress` 写入可控键，LFI 包含 session 文件。
3. 原生类：`SoapClient`（SSRF/CRLF）、`SplFileObject`（读文件）、`ZipArchive`（删/覆盖）。
4. 确认 PHP 版本与扩展。

**成功标志**：文件函数/session 包含触发反序列化副作用。

**失败分支**：PHP 8 phar 不自动反序列化→换入口；扩展缺失→换类。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| `__wakeup` 校验 | 属性个数绕过/`__destruct` | 老版本 |
| 属性名过滤 | 可见性前缀/大小写 | `%00*\0` |
| 长度过滤 | 字符逃逸 | 变长/变短 |
| `phar://` 被拦 | `PHAR://`/编码 | `phar%3a//` |
| `allowed_classes=false` | 找其他入口 | session/框架 |
| PHP 8 phar | 换反序列化点 | 显式 `unserialize` |

边界：`unserialize` 不调用 `__construct`；`__sleep` 在序列化时；phar 生成需 `phar.readonly=0`，打开不需要。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Cookie | 序列化会话 | 签名/密钥 |
| session | `upload_progress` | 包含文件 |
| phar | 图片马 metadata | 文件函数 |
| 缓存 | Redis/文件缓存 | 写入点 |
| 数据库 | 存储的序列化字段 | 二次读取 |
| `C:` 格式 | `Serializable` | 自定义数据 |
| 原生类 | `SoapClient` | 扩展 |

## 06 差异速查

| 可见性 | 序列化键 | 长度 |
|---|---|---|
| public | `name` | 名字字节数 |
| protected | `\0*\0name` | +3 |
| private | `\0Class\0name` | +类名+2 |

| 版本/配置 | 行为 |
|---|---|
| PHP <5.6.25 / <7.0.10 | 属性个数绕过 `__wakeup` |
| PHP 8.0+ | phar metadata 不自动反序列化 |
| `allowed_classes=false` | 不实例化类 |
| `phar.readonly=1` | 不能创建 phar |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 本地验证 | `php -r 'var_dump(unserialize(...));'` |
| 生成 | 手写/`phpggc` |
| phar | 本地 PHP 脚本生成 |
| 改包 | Burp（URL 编码空字节） |
| 排错 | 长度→空字节→类名→wakeup→过滤 |

验证顺序：格式 → 单类 → POP → 绕过 → phar/session。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 请求/Cookie/文件 | 反序列化点 |
| 2 类 | 魔术方法/sink | 候选链 |
| 3 构造 | 属性/可见性/长度 | payload |
| 4 验证 | 本地+目标 | 副作用 |
| 5 绕过 | wakeup/过滤 | 可用链 |
| 6 记录 | 字节/类/结果 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 偏移错误 | 长度/空字节 | 重数字节 |
| 对象不还原 | 类未加载 | 找 autoload |
| 无副作用 | 钩子无 sink | 找跳板 |
| `__wakeup` 退出 | 校验 | 老版本绕过/换入口 |
| 属性被过滤 | 键名/值 | 逃逸/换属性 |
| phar 无效 | 版本/路径 | 显式入口/换协议 |
| session 不触发 | 处理器/路径 | 查配置 |

## 10 记录与复现

- [ ] 入口与编码
- [ ] 类名/属性/可见性
- [ ] 魔术方法链
- [ ] 最终序列化串
- [ ] 触发条件与副作用
- [ ] 版本/配置限制

| 记录项 | 内容 |
|---|---|
| 入口 | 请求/Cookie/phar/session |
| 类 | 起点/跳板/sink |
| 载荷 | 序列化串（含编码） |
| 结果 | 命令/文件/请求 |
| 限制 | 版本/过滤/扩展 |

相关： [PHP 特性](/knowledge/web-php-features/)、[文件上传绕过](/knowledge/web-upload-bypass/)、[PHP 代码审计](/knowledge/web-php-audit/)、[文件包含](/knowledge/web-file-include/)、[命令执行与反序列化](/knowledge/web-runtime-boundary/)。
