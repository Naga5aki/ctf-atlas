---
title: "Spring 与 Java 代码审计"
summary: "从 war/jar 结构定位路由与依赖，再按 Actuator 读取、SpEL 注入、Spring4Shell、Gateway 路由逐级验证；附 heapdump 与审计 grep。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-java-security", "web-source-route", "web-cloud-container", "web-language-reading"]
updated: "2026-10-29"
---

Spring 题的入口通常只有三个：**用户输入进了 SpEL**、**Actuator 暴露了配置/内存**、**参数绑定写入了文件**。审计题则从 war/jar 的结构开始，按“路由 → 参数 → sink”走。

> 只对本地题目或授权环境测试；Actuator 的 `/refresh`、`/gateway` 会改配置，先确认可回滚。

## 00 30 秒速查

| 我要… | 先看… | 备注 |
|---|---|---|
| 找路由 | `@RequestMapping`/`web.xml` | 类+方法拼接 |
| 找参数 | `@RequestParam`/`@RequestBody` | 绑定方式 |
| Actuator | `/actuator`/`/env`/`/heapdump` | 是否暴露 |
| SpEL | `parseExpression`/`@Value` | `${}` vs `#{}` |
| Spring4Shell | JDK9+WAR+Tomcat | 参数绑定 |
| Gateway | `/actuator/gateway/routes` | SpEL |
| 看依赖 | `WEB-INF/lib`/`pom.xml` | 版本 |
| 反编译 | jadx/CFR | 路由/sink |
| 审计 | grep/CodeQL | 数据流 |

## 01 原理与成立条件

```text
请求 → DispatcherServlet → 控制器 → 参数绑定
                                ├─ SpEL 求值
                                ├─ 文件/命令 sink
                                └─ 反序列化
Actuator → 配置/内存/路由 → 改配置/读密钥
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 路由可达 | 注解/web.xml | 找隐藏路径 |
| 参数可控 | 绑定到敏感对象 | 换参数 |
| 表达式/配置可控 | SpEL/Actuator | 换入口 |
| 版本受影响 | Spring/Tomcat/JDK | 换链 |

## 02 判断与分型

```text
有 Actuator 吗？
 ├─ 有 → 读 env/heapdump/mappings
 └─ 无 → 看路由
      ├─ SpEL → 表达式注入
      ├─ 参数绑定 → Spring4Shell
      ├─ Gateway → 路由 SpEL
      └─ 反序列化 → 见 Java 页
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `/actuator` 200 | 暴露 | 列端点 |
| `/env` 有密码 | 配置泄露 | 读/改属性 |
| heapdump 可下 | 内存 | strings/MAT |
| `${7*7}` 变 49 | SpEL | 构造执行 |
| `class.module...` 生效 | Spring4Shell | 写日志 |
| Gateway 路由可加 | SpEL | 触发 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 404 | 端点未暴露 | 换路径/前缀 |
| `${}` 原样 | 占位符未解析 | 换 `#{}` |
| 参数绑定报错 | 类型不符 | 换字段 |
| heapdump 空 | 下载不完整 | 重下/看大小 |

## 03 利用阶梯

### L0 指纹与结构

**前提**：有 Spring 应用/源码/镜像。

**步骤**：
1. 看响应头/错误页/`/actuator`。
2. war/jar 解压：`WEB-INF/web.xml`、`BOOT-INF/classes`。
3. 列依赖版本（Spring/Tomcat/Jackson/fastjson）。
4. 反编译控制器，列路由。

**成功标志**：知道框架版本、路由、可用端点。

**失败分支**：无源码→黑盒探端点；版本未知→报错/依赖名。

### L1 Actuator 读取与改配置

**前提**：Actuator 暴露。

**步骤**：
1. 列 `/actuator`、`/env`、`/configprops`、`/mappings`、`/beans`。
2. 下载 `/heapdump`，`strings`/MAT 找密码/token。
3. `/env` 可写时改数据源/URL。
4. `/refresh` 触发重连（JDBC/SSRF）。

**成功标志**：拿到密钥/配置/内存数据。

**失败分支**：端点关闭→换前缀/版本；只读→用泄露凭证。

### L2 SpEL 注入

**前提**：用户输入进入 `SpelExpressionParser`/`@Value`。

**步骤**：
1. 试 `${7*7}`、`#{7*7}`。
2. `T(java.lang.Runtime).getRuntime().exec("id")`。
3. 禁 `T(`：`new java.lang.ProcessBuilder("id").start()`。
4. 禁关键字：反射/字符串拼接/`ScriptEngine`。

**成功标志**：表达式执行/命令回显。

**失败分支**：沙箱→换构造；占位符不解析→换上下文。

### L3 Spring4Shell / Gateway

**前提**：版本/部署满足条件。

**步骤**：
1. Spring4Shell：JDK9+、WAR、Tomcat、参数绑定到对象。
2. 设 `class.module.classLoader.resources.context.parent.pipeline.first.*`。
3. 多次请求写日志 JSP，再访问。
4. Gateway：POST 路由 + SpEL，`/refresh` 后访问触发。

**成功标志**：写文件/命令执行。

**失败分支**：部署方式不符→换 CVE；端点不可写→换入口。

### L4 审计与链

**前提**：有源码/大项目。

**步骤**：
1. 列路由：注解 + `web.xml`。
2. 跟参数到 sink：`Runtime.exec`/`Statement`/`readObject`/`parseObject`/`SpelExpressionParser`。
3. 看过滤器/拦截器/白名单。
4. CodeQL taint tracking 跑 `RemoteFlowSource → sink`。
5. 本地起服务验证。

**成功标志**：完整数据流/可复现请求。

**失败分支**：链断→换入口；依赖不明→先列 lib。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 禁 `T(` | `new ProcessBuilder` | 反射 |
| 禁 `Runtime` | `ScriptEngine` | 看依赖 |
| 禁 `java` | 拼接/`Class.forName` | 字符串 |
| 长度 | 分步 setValue | SpEL |
| Actuator 只读 | heapdump/env 泄露 | 凭证 |
| 端点前缀 | `/manage`/自定义 | 配置 |
| 参数绑定 | 换字段/嵌套 | Spring4Shell |

边界：Spring4Shell 需 WAR+Tomcat+JDK9+；Gateway 需 Actuator 可写；`${}` 是占位符，`#{}` 是 SpEL；heapdump 可能很大，先看大小。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 错误页 | 堆栈/版本 | 指纹 |
| 上传 | 解析库 | 反序列化 |
| 模板 | Thymeleaf | 视图名 |
| 数据源 | JDBC URL | SSRF/反序列化 |
| 日志 | 写入 JSP | 包含 |
| 定时任务 | 表达式 | SpEL |
| 第三方 | Shiro/Jackson | Nday |

## 06 差异速查

| 版本/组件 | 影响 |
|---|---|
| Spring Boot 2.x | `/env` 需 POST+开关 |
| Spring4Shell | JDK9+WAR+Tomcat |
| Gateway CVE | Actuator 可写 |
| Tomcat | AccessLogValve 字段 |
| JDK 17 | 模块限制 |
| Shiro | 默认密钥 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 解包 | `unzip -l` |
| 反编译 | jadx/CFR |
| 依赖 | `pom.xml`/`WEB-INF/lib` |
| heapdump | MAT/`strings` |
| SpEL | 手工 |
| 审计 | grep/CodeQL |
| 记录 | 路由/版本/请求 |

验证顺序：结构 → 端点 → SpEL → CVE → 审计。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 指纹 | 头/错误/Actuator | 版本 |
| 2 结构 | war/jar/依赖 | 路由 |
| 3 读取 | env/heapdump | 密钥 |
| 4 注入 | SpEL/CVE | 执行 |
| 5 审计 | 数据流 | 链 |
| 6 记录 | 请求/版本 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| Actuator 404 | 未暴露 | 换前缀 |
| `/env` 403 | 只读/关闭 | heapdump |
| SpEL 原样 | 上下文 | 换 `#{}` |
| Spring4Shell 无效 | 部署/JDK | 换 CVE |
| Gateway 失败 | 端点/权限 | 换入口 |
| heapdump 无密码 | 未加载 | 触发业务再下 |
| 路由找不到 | 混淆/前缀 | 反编译 |

## 10 记录与复现

- [ ] 框架/Tomcat/JDK 版本
- [ ] 路由与参数
- [ ] Actuator 端点
- [ ] 漏洞类型
- [ ] 依赖/链
- [ ] 验证请求

| 记录项 | 内容 |
|---|---|
| 版本 | Spring/Tomcat/JDK |
| 入口 | 路由/Actuator |
| 漏洞 | SpEL/Actuator/CVE |
| 依赖 | 链所需库 |
| 结果 | 密钥/执行 |

相关： [Java 安全与反序列化](/knowledge/web-java-security/)、[代码审计总览](/knowledge/web-source-route/)、[云与容器](/knowledge/web-cloud-container/)、[语言阅读](/knowledge/web-language-reading/)。
