---
title: "Java 安全：反序列化与 JNDI"
summary: "先看 classpath/JDK，再选链：URLDNS 探测、CC1/CC6、ysoserial、fastjson/Jackson @type、JNDI 与 TemplatesImpl；每条链都标版本边界。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-spring-audit", "web-runtime-boundary", "web-cloud-container", "web-language-reading"]
updated: "2026-10-29"
---

Java 反序列化题的门槛不在“会不会用 ysoserial”，而在**能不能判断目标有哪些依赖、入口是哪个 readObject、JDK 版本允许什么**。先收集 classpath 与版本，再选链。

> 只对本地题目或授权环境测试；JNDI/远程类加载会出网，注意隔离。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 找入口 | `readObject`/`parseObject`/`fromXML` | 字节流从哪来 |
| 认格式 | `AC ED 00 05`/`rO0AB` | Java 序列化 |
| 探反序列化 | URLDNS + DNSLog | 依赖最少 |
| 选链 | `pom.xml`/`WEB-INF/lib` | 依赖决定 |
| fastjson | `@type`/版本 | 1.2.24-1.2.68 |
| Jackson | `enableDefaultTyping` | `@class` |
| JNDI | `lookup`/`dataSourceName` | JDK 限制 |
| 字节码 | `TemplatesImpl` | `_bytecodes` |
| 记录 | JDK/依赖/链 | 版本边界 |

## 01 原理与成立条件

```text
字节流 → ObjectInputStream.readObject → 类描述/字段 → 钩子
                                                    ├─ readObject
                                                    ├─ readResolve
                                                    └─ validateObject
JSON → @type → 反射/工厂 → JNDI/TemplatesImpl
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 输入进入反序列化 | readObject/parseObject | 找其他入口 |
| 链类在 classpath | 依赖/版本 | 换链 |
| 钩子可达 | readObject 等 | 换入口类 |
| JDK 允许 | 模块/JNDI 限制 | 换绕过 |

## 02 判断与分型

```text
输入是 Java 序列化吗？
 ├─ AC ED/rO0AB → readObject
 ├─ JSON 带 @type/@class → fastjson/Jackson
 ├─ XML → XStream
 └─ 都不是 → 找其他入口
有依赖吗？
 ├─ commons-collections → CC
 ├─ Spring → Spring 链
 ├─ 只有 JDK → URLDNS/JRMP
 └─ 未知 → 先 DNSLog 探测
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `rO0AB` | Java 序列化 | 找 readObject |
| DNSLog 收到 | 反序列化发生 | 换 RCE 链 |
| `@type` 报错 | fastjson | 查版本 |
| `InvalidClassException` | serialVersionUID | 对齐版本 |
| `JdbcRowSetImpl` | JNDI 链 | 起 LDAP |
| `TemplatesImpl` | 字节码 | 生成 translet |
| JDK 8u191+ | 远程 codebase 关 | 本地工厂 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| base64 像 `rO0AB` | 只是文本 | 解码确认 |
| DNSLog 无记录 | 出口禁 | 换入口 |
| 链类存在 | 版本不兼容 | 对齐版本 |
| JNDI 报错 | JDK 限制 | 换绕过 |

## 03 利用阶梯

### L0 指纹与依赖

**前提**：有疑似 Java 序列化/JSON 入口。

**步骤**：
1. 看 `Content-Type`/字节头/base64。
2. 收集 `pom.xml`、`WEB-INF/lib`、`MANIFEST.MF`。
3. 确认 JDK 版本（报错/镜像/配置）。
4. 列依赖版本：commons-collections、fastjson、Jackson、Spring。

**成功标志**：知道入口类型、依赖、JDK。

**失败分支**：无源码→盲探；依赖未知→URLDNS 先测。

### L1 URLDNS 探测

**前提**：有 readObject 入口，能出网。

**步骤**：
1. `ysoserial URLDNS http://<dnslog>` 生成。
2. 提交字节流（注意 base64/Content-Type）。
3. 看 DNSLog 是否收到解析。
4. 只证明反序列化发生，不证明 RCE。

**成功标志**：DNS 解析记录出现。

**失败分支**：无记录→入口/出口问题；换其他探测链。

### L2 CC / ysoserial 链

**前提**：classpath 有对应依赖。

**步骤**：
1. 按依赖选链：CC1/CC3/CC5/CC6、CB1、Groovy、Spring。
2. 用 ysoserial 生成，注意命令编码（无空格/特殊字符）。
3. 提交并看回显/外带。
4. 版本不兼容时换链/换 JDK。

**成功标志**：命令执行/外带。

**失败分支**：`InvalidClassException`→对齐版本；无依赖→L3/L4。

### L3 fastjson / Jackson

**前提**：JSON 解析未限制类型。

**步骤**：
1. 试 `{"@type":"java.lang.Class","val":"..."}`。
2. 按版本试绕过：`L`/`;`/双写/`[`/缓存。
3. JNDI：`JdbcRowSetImpl` + `dataSourceName`。
4. 字节码：`TemplatesImpl` + `_bytecodes`。
5. Jackson 看 `enableDefaultTyping`/`@class`。

**成功标志**：JNDI 出网/字节码执行。

**失败分支**：autoType 关闭→找 expectClass；版本已修→换链。

### L4 JNDI 与 TemplatesImpl

**前提**：能触发 `lookup` 或加载字节码。

**步骤**：
1. marshalsec 起 LDAP/RMI，返回 `Reference`。
2. JDK 8u191+：用本地工厂（Tomcat BeanFactory + EL）或 `javaSerializedData`。
3. `TemplatesImpl`：`_bytecodes` 继承 `AbstractTranslet`，`_name` 非空。
4. 只验证到 DNS/固定回显。

**成功标志**：远程类加载/本地工厂执行。

**失败分支**：出网禁→本地 gadget；JDK 高→换工厂。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| autoType 关闭 | expectClass/缓存 | 版本相关 |
| JDK 8u191+ | 本地工厂 | BeanFactory+EL |
| 无远程 codebase | `javaSerializedData` | 二次反序列化 |
| serialVersionUID | 对齐版本 | 改字段 |
| 命令空格 | base64/拼接 | `bash -c` |
| 模块限制 | `--add-opens` | 看启动参数 |

边界：URLDNS 只证明反序列化；CC1 依赖 JDK 8u71 前；fastjson 版本决定绕过；JNDI 高版本默认禁止远程 codebase；`TemplatesImpl` 需 translet 字节码。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Cookie | base64 序列化 | readObject |
| 文件上传 | 解析库 | XStream/Jackson |
| 缓存 | Redis 序列化值 | 二次 |
| JMX/RMI | 远程调用 | 出网 |
| XML | XStream | 类型 |
| 日志 | 反序列化 | 入口 |
| 第三方组件 | Nday | 版本 |

## 06 差异速查

| 链 | 依赖 | JDK/版本 |
|---|---|---|
| URLDNS | JDK | 通用 |
| CC1 | commons-collections 3.x | 8u71 前 |
| CC6 | commons-collections | 较高 JDK |
| CB1 | commons-beanutils | 依赖版本 |
| Spring1/2 | Spring | 版本 |
| Fastjson | fastjson | 1.2.24-1.2.68 |
| Jackson | 默认类型 | 配置 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 生成 | ysoserial |
| JNDI | marshalsec/JNDIExploit |
| fastjson | 手工/工具 |
| DNS | DNSLog |
| 依赖 | `mvn dependency:tree` |
| 记录 | 链/版本/结果 |

验证顺序：指纹 → 探测 → 选链 → 执行 → 绕过。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | 字节/JSON/XML | 类型 |
| 2 依赖 | lib/pom/JDK | 可用链 |
| 3 探测 | URLDNS | 是否反序列化 |
| 4 利用 | CC/fastjson/JNDI | 执行 |
| 5 绕过 | 版本限制 | 可用链 |
| 6 记录 | 链/版本 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| DNS 无记录 | 入口/出口 | 换入口 |
| `InvalidClassException` | 版本 | 对齐依赖 |
| 链类缺失 | classpath | 换链 |
| fastjson 报错 | autoType | 版本绕过 |
| JNDI 拒绝 | JDK | 本地工厂 |
| 命令无回显 | 通道 | 外带/延时 |
| 字节码失败 | translet | 修字节码 |

## 10 记录与复现

- [ ] 入口与格式
- [ ] JDK/依赖版本
- [ ] 链选择
- [ ] 生成命令
- [ ] 结果（DNS/命令）
- [ ] 版本边界

| 记录项 | 内容 |
|---|---|
| 入口 | readObject/JSON/XML |
| 依赖 | CC/fastjson/Spring |
| JDK | 8u 版本 |
| 链 | URLDNS/CC6/JNDI |
| 结果 | DNS/执行 |

相关： [Spring 与 Java 审计](/knowledge/web-spring-audit/)、[反序列化总览](/knowledge/web-runtime-boundary/)、[云与容器](/knowledge/web-cloud-container/)、[语言阅读](/knowledge/web-language-reading/)。
