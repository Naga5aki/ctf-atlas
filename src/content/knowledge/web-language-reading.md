---
title: "PHP、Java、Python：读源码的三种规则"
summary: "从请求入口、比较规则、对象生命周期三条线读源码：PHP 弱类型/魔术方法、Java 过滤器/反序列化、Python Flask/pickle；先确认运行版本。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-source-route", "web-runtime-boundary", "web-data-query", "web-php-features", "web-java-security", "web-python-security"]
updated: "2026-10-29"
---

Web 题给源码时，先找请求怎么进来，再找比较、包含、查询和反序列化用的是哪一种规则。PHP、Java、Python 的入口不同，容易误判的点也不同。

> 版本以运行中的 `PHP_VERSION`、`java -version` 和解释器版本为准；材料与发行说明不一致时，打印语言自己的版本。

## 00 30 秒速查

| 语言 | 先找… | 容易误判 |
|---|---|---|
| PHP | `$_GET/POST`、`==`、`include`、`unserialize` | 数组/0e/魔术方法 |
| Java | `@RequestMapping`、Filter、`readObject` | 过滤器顺序/反序列化入口 |
| Python | 路由、`render_template_string`、`pickle` | session 只签名/pickle |
| 通用 | 启动命令、依赖、版本 | 运行的是否这份源码 |
| 输出 | 回显/文件/延时 | 先建通道 |

## 01 原理与成立条件

```text
请求 → 入口（超全局/路由/框架） → 过滤 → 业务 → sink
                                      ├─ 比较规则
                                      ├─ 对象生命周期
                                      └─ 文件/查询/模板/反序列化
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 源码可读 | 题目/备份/镜像 | 黑盒 |
| 入口可追 | 参数→变量 | 找路由 |
| 规则差异 | 版本/类型 | 换构造 |
| 运行一致 | 版本/配置 | 以运行态为准 |

## 02 判断与分型

```text
语言是什么？
 ├─ PHP → 看超全局/比较/include/魔术方法
 ├─ Java → 看路由/Filter/readObject/SpEL
 └─ Python → 看路由/模板/pickle/session
入口到 sink 有过滤吗？
 ├─ 无 → 直接构造
 ├─ 有 → 看类型/编码/二次
 └─ 不确定 → 本地跑
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `$_GET` 直接拼接 | PHP 入口 | 跟 sink |
| `==`/`in_array` 无严格 | 弱类型 | 0e/数组 |
| `unserialize` | 魔术方法 | 读类定义 |
| `@RequestMapping` | Java 路由 | 参数绑定 |
| `readObject` | Java 反序列化 | 链/依赖 |
| `render_template_string` | Python SSTI | 模板链 |
| `pickle.loads` | Python 反序列化 | `__reduce__` |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 看到 `==` | 两边类型固定 | 看可控性 |
| 有过滤器 | 只拦部分路径 | 看映射 |
| 有 `pickle` | 输入不可控 | 跟数据流 |
| 版本旧 | 配置已改 | 运行态确认 |

## 03 利用阶梯

### L0 确认运行环境与入口

**前提**：有源码/容器/备份。

**步骤**：
1. 看启动命令、端口、依赖锁文件。
2. 打印语言版本（`PHP_VERSION`/`java -version`/`python -V`）。
3. 列路由/超全局/模板/反序列化入口。
4. 用正常请求对照代码路径。

**成功标志**：知道运行版本与入口清单。

**失败分支**：无源码→黑盒；版本不符→以运行态为准。

### L1 PHP：比较、覆盖与生命周期

**前提**：PHP 源码。

**步骤**：
1. 比较：`==` vs `===`、`in_array` 第三参、`strcmp` 数组。
2. 哈希：`0e`、数组返回 null（PHP8 抛错）。
3. 覆盖：`extract`/`parse_str`/`$$`。
4. 生命周期：`__wakeup`/`__destruct`/`__toString`。
5. 文件：协议前缀/包含。

**成功标志**：找到可绕过的比较/覆盖/对象链。

**失败分支**：严格比较→真实碰撞；无魔术方法→换入口。

### L2 Java：路由、过滤器与反序列化

**前提**：Java/Spring 源码或 war/jar。

**步骤**：
1. 找 `@RequestMapping`/`web.xml`/Filter 链。
2. 看参数绑定来源（query/JSON/path/header）。
3. 找 `readObject`/`parseObject`/SpEL/OGNL。
4. 看依赖版本与 JDK。
5. 过滤器顺序/调度类型影响鉴权覆盖。

**成功标志**：路由→sink 的可达链。

**失败分支**：链断→换入口；依赖不明→列 lib。

### L3 Python：Flask、模板与 pickle

**前提**：Python Web 源码。

**步骤**：
1. Flask `secret_key` 是否示例/空/短。
2. `render_template` vs `render_template_string`。
3. `pickle.loads`/`yaml.load` 输入来源。
4. Flask session 只签名不加密；debug PIN 要素。
5. `str.format` 只读属性，不等于模板执行。

**成功标志**：SSTI/pickle/session 伪造路径。

**失败分支**：模板固定→换入口；pickle 不可控→找其他。

### L4 跨语言组合与运行差异

**前提**：多语言/多服务。

**步骤**：
1. 入口语言 → 中间件（Nginx/Java/Python）。
2. 解析差异：路径/编码/参数。
3. 组合：PHP 包含+日志、Java 反序列化+JNDI、Python SSTI+globals。
4. 只验证到固定回显/读文件。

**成功标志**：跨层链可复现。

**失败分支**：层间不一致→回到入口；版本已修→换链。

## 04 绕过与边界

| 语言 | 限制 | 绕过 |
|---|---|---|
| PHP | `===` | 真实碰撞/数组不适用 |
| PHP | `disable_functions` | 扩展/组合 |
| Java | 模块限制 | `--add-opens`/换链 |
| Java | autoType 关闭 | expectClass |
| Python | 沙箱 | 子类/`getattr` |
| Python | 模板沙箱 | 版本逃逸 |

边界：PHP 8 收紧字符串/数字比较；Java 8u191+ 限制 JNDI 远程加载；Flask session 完整性依赖密钥；`str.format` 不执行语句。

## 05 非典型入口

| 语言 | 入口 | 注意 |
|---|---|---|
| PHP | Header/文件名/日志 | 存储型 |
| Java | 缓存/消息/会话 | 反序列化 |
| Python | Cookie/上传/模板 | pickle/SSTI |
| 通用 | 备份/.git/配置 | 源码泄露 |

## 06 差异速查

| 表达式 | PHP 7 | PHP 8 |
|---|---|---|
| `0 == "abc"` | true | false |
| `"0e1" == "0e2"` | true | true |
| `md5([]) == 0` | true | TypeError |
| `in_array(0,["abc"])` | true | false |
| `assert(string)` | 执行 | 不执行 |

| 语言 | session/token | 注意 |
|---|---|---|
| PHP | `PHPSESSID` | 固定/预测 |
| Java | `JSESSIONID` | 固定 |
| Flask | 签名 Cookie | 密钥 |
| Django | 签名 Cookie | `SECRET_KEY` |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| PHP 版本 | `php -v`/`phpinfo` |
| Java 版本 | `java -version` |
| Python 版本 | `python -V` |
| 反编译 | jadx/CFR |
| 本地复现 | Docker/语言 REPL |
| 记录 | 文件:行号/版本 |

验证顺序：版本 → 入口 → 规则 → sink → 复现。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 环境 | 版本/依赖 | 运行态 |
| 2 入口 | 路由/超全局 | 可控点 |
| 3 规则 | 比较/生命周期 | 候选 |
| 4 sink | 查询/文件/命令 | 链 |
| 5 验证 | 本地/目标 | 证据 |
| 6 记录 | 文件/行号 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 比较绕不过 | `===` | 换碰撞 |
| 反序列化无链 | 类未加载 | 找 autoload |
| Java 路由 404 | 前缀/上下文 | 看配置 |
| Flask 签名失败 | 密钥 | 找泄露 |
| pickle 不可控 | 入口 | 换参数 |
| 模板不执行 | 数据绑定 | 找拼接 |
| 运行不一致 | 版本/配置 | 以运行态为准 |

## 10 记录与复现

- [ ] 语言/版本/依赖
- [ ] 入口与路由
- [ ] 比较/生命周期规则
- [ ] sink 与过滤
- [ ] 验证请求
- [ ] 文件:行号

| 记录项 | 内容 |
|---|---|
| 语言 | PHP/Java/Python |
| 版本 | 运行态 |
| 入口 | 参数/路由 |
| 规则 | 比较/魔术/反序列化 |
| 结果 | 绕过/执行 |

相关： [代码审计方法](/knowledge/web-source-route/)、[命令执行与反序列化](/knowledge/web-runtime-boundary/)、[SQL 注入](/knowledge/web-data-query/)、[PHP 特性](/knowledge/web-php-features/)、[Java 安全](/knowledge/web-java-security/)、[Python 安全](/knowledge/web-python-security/)。
