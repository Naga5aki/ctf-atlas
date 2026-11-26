---
title: "PHP 代码审计：从入口追到 sink"
summary: "先列超全局入口与危险函数，再沿数据流看过滤；覆盖变量覆盖、包含、SQL、反序列化、命令执行与 Laravel/ThinkPHP 路由差异。"
module: Web
topic: "源码与环境"
tags: []
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-source-route", "web-php-features", "web-php-unserialize", "web-language-reading"]
updated: "2026-10-29"
---

PHP 审计的目标不是“读完所有代码”，而是**从可控输入出发，沿数据流找到危险操作**。先列入口（超全局变量、路由参数、文件），再列 sink（执行/包含/查询/文件/反序列化），最后看中间有没有过滤。

> 只对本地题目或授权源码审计；不要对未授权站点做扫描。

## 00 30 秒速查

| 我要… | 先做… | 备注 |
|---|---|---|
| 找入口 | `$_GET/POST/REQUEST/COOKIE/SERVER` | 也包括路由参数 |
| 找执行 | `system/exec/eval/include` | 先 grep |
| 找 SQL | 字符串拼接/`query` | 看预处理 |
| 找反序列化 | `unserialize/phar://` | 魔术方法 |
| 找覆盖 | `extract/parse_str/$$` | 同名变量 |
| 找上传 | `$_FILES`/`move_uploaded_file` | 后缀/路径 |
| 看过滤 | `intval/addslashes/escapeshellarg` | 是否覆盖所有入口 |
| 框架入口 | 路由文件/控制器 | 版本/中间件 |
| 验证 | 本地起环境 | 文件:行号 |

## 01 原理与成立条件

```text
请求 → 路由/超全局 → 过滤 → sink → 结果
                        ├─ 无过滤 → 直接利用
                        ├─ 过滤不全 → 绕过
                        └─ 二次使用 → 存储型
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 入口可控 | 参数/头/文件 | 找其他路由 |
| 数据到 sink | 变量传递 | 跟踪赋值 |
| 过滤可绕/缺失 | 类型/函数 | 找二次入口 |
| 结果可观察 | 回显/文件/状态 | 盲打 |

## 02 判断与分型

```text
源码里先找什么？
 ├─ 入口：$_*、路由、上传
 ├─ sink：执行/包含/SQL/文件/反序列化
 └─ 过滤：类型/转义/白名单
入口到 sink 有过滤吗？
 ├─ 无 → 直接构造
 ├─ 有但可绕 → 编码/类型/二次
 └─ 有且严 → 换入口/换 sink
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| `$_GET` 直接进 `include` | LFI | 读源码/包含 |
| `system("ping ".$ip)` | 命令注入 | 分隔符 |
| `"SELECT ... $id"` | SQLi | 联合/盲注 |
| `unserialize($_COOKIE)` | 反序列化 | POP 链 |
| `extract($_GET)` | 变量覆盖 | 同名参数 |
| `move_uploaded_file` | 上传 | 后缀/路径 |
| `preg_match` 过滤 | 正则 | 换行/数组 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 看到危险函数 | 参数不可控 | 跟数据流 |
| 有 `intval` | 只覆盖部分 | 找其他入口 |
| 用了 PDO | 仍可能拼接 | 看 `query` |
| 前端校验 | 服务端未校验 | 直接请求 |

## 03 利用阶梯

### L0 列入口与 sink

**前提**：有源码/备份。

**步骤**：
1. 解压/确认版本与依赖。
2. grep 入口：`\$_(GET|POST|REQUEST|COOKIE|SERVER|FILES)`。
3. grep sink：命令/代码/包含/SQL/文件/反序列化。
4. 标出“入口 → 变量 → sink”的候选。

**成功标志**：有一张候选数据流表。

**失败分支**：源码混淆→解密/找入口；无源码→黑盒。

### L1 单文件数据流

**前提**：入口与 sink 在同一文件/函数。

**步骤**：
1. 跟变量赋值/拼接。
2. 看过滤函数与类型转换。
3. 构造最小请求验证。
4. 记录文件:行号与参数。

**成功标志**：请求触发 sink。

**失败分支**：中间有过滤→L2；变量被覆盖→L3。

### L2 过滤与二次使用

**前提**：有过滤/转义，但可能不全。

**步骤**：
1. 看过滤是否覆盖所有入口（Header/JSON/数组）。
2. 类型绕过：数组/对象/数字字符串。
3. 二次使用：入库转义、出库拼接；存储型 XSS/SQL。
4. 编码/大小写/双写。

**成功标志**：过滤条件下仍到 sink。

**失败分支**：白名单严格→换入口；预处理完整→找其他 sink。

### L3 变量覆盖与文件链

**前提**：`extract`/`parse_str`/`$$` 或文件操作。

**步骤**：
1. 找 `extract($_GET)` 与 `EXTR_SKIP`。
2. 覆盖 `$file`/`$is_admin`/`$sql`。
3. 包含上传/日志/session/phar。
4. 上传+包含、phar+文件函数组合。

**成功标志**：改变逻辑/执行代码。

**失败分支**：覆盖顺序不符→换键；文件不可包含→换协议。

### L4 框架与链

**前提**：Laravel/ThinkPHP/WordPress 等。

**步骤**：
1. 找路由文件/控制器/中间件。
2. 看版本与已知漏洞（入口是否可达）。
3. 追 model/helper 的拼接与反序列化。
4. 组合：反序列化 POP + 文件/命令。

**成功标志**：从路由到 sink 的完整链。

**失败分支**：版本已修→换组件；入口需鉴权→找越权。

## 04 绕过与边界

| 过滤 | 绕过 | 示例 |
|---|---|---|
| `intval` | 其他入口/数组 | Header/JSON |
| `addslashes` | 二次注入/宽字节 | GBK |
| `escapeshellarg` | 参数分隔/环境 | 看 shell |
| `preg_match` | 换行/数组 | `%0a` |
| 后缀白名单 | 包含/phar | 上传链 |
| `disable_functions` | 扩展/组合 | 见 RCE 页 |
| 前端校验 | 直接请求 | 改包 |

边界：`PDO::query` 拼接仍可注入；`htmlspecialchars` 不防 SQL/命令；`open_basedir` 限制文件路径；框架版本决定 Nday 可达性。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| Header | UA/Referer/XFF | 存储型/命令 |
| 文件名 | 上传/导出 | 路径/命令 |
| 路由参数 | `/user/{id}` | 控制器 |
| JSON/XML | `php://input` | 解析 |
| 缓存 | 序列化值 | 反序列化 |
| 日志 | 包含 | 投毒 |
| 插件 | WordPress | 第三方 |

## 06 差异速查

| 框架 | 入口 | 注意 |
|---|---|---|
| Laravel | `routes/web.php` | 中间件/模型绑定 |
| ThinkPHP | `app/controller` | `?s=` 兼容 |
| CodeIgniter | `application/controllers` | 老版本 |
| Symfony | `config/routes.yaml` | 注解 |
| WordPress | `wp-content/plugins` | `admin-ajax.php` |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| grep | `rg -n` 入口/sink |
| 依赖 | `composer.lock` |
| 污点 | Semgrep/CodeQL |
| 本地 | Docker/php -S |
| 请求 | Burp/curl |
| 记录 | 文件:行号/参数 |

验证顺序：入口 → sink → 过滤 → 请求 → 复现。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 准备 | 解压/版本 | 环境 |
| 2 入口 | 路由/超全局 | 可控点 |
| 3 sink | grep 危险函数 | 候选 |
| 4 数据流 | 赋值/过滤 | 链 |
| 5 验证 | 本地请求 | 证据 |
| 6 记录 | 文件/行号 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 参数不可控 | 路由/覆盖 | 跟赋值 |
| 过滤挡住 | 类型/白名单 | 换入口 |
| 包含无输出 | 无回显 | base64 |
| SQL 无回显 | 盲注 | 布尔/时间 |
| 反序列化无类 | 未加载 | 找 autoload |
| 框架入口不可达 | 鉴权/版本 | 找越权/组件 |

## 10 记录与复现

- [ ] 版本/依赖
- [ ] 入口文件:行号
- [ ] sink 文件:行号
- [ ] 过滤与绕过
- [ ] 验证请求/响应
- [ ] 影响

| 记录项 | 内容 |
|---|---|
| 版本 | PHP/框架 |
| 入口 | 参数/文件 |
| 过滤 | 函数/类型 |
| sink | 函数/上下文 |
| 验证 | 请求/结果 |

相关： [代码审计方法](/knowledge/web-source-route/)、[PHP 特性](/knowledge/web-php-features/)、[PHP 反序列化](/knowledge/web-php-unserialize/)、[语言阅读](/knowledge/web-language-reading/)。
