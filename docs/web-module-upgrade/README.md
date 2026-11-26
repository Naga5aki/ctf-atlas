# ctf-atlas Web 模块全方位升级 · 交付说明

## 1. 本次交付内容

```
web-module-upgrade/
├── content/knowledge/          # 37 个可入库的 markdown 页面（36 新增 + 1 增强替换）
├── reports/
│   ├── coverage-matrix.md      # hello-ctf 60 个 Web 页面 → atlas 页面覆盖矩阵
│   ├── web-module-composition.md # 升级后 53 页的 8 分类组成方案与模块页结构
│   └── staged-index.json       # 37 个页面的 frontmatter/字数/表格数清单
├── validate.py                 # frontmatter 校验脚本
└── README.md                   # 本文件
```

- **新增 36 页**：覆盖 hello-ctf 中站内没有独立页面的主题（SQL 进阶、NoSQL、RCE 绕过、上传绕过、路径读取、文件包含、PHP 特性/反序列化、Python 安全、SSRF/XXE 进阶、XSS 向量、CSRF、XS-Leaks、缓存投毒、原型链、JWT、Java/Spring、JS 沙箱、走私、WAF、密码学应用、云容器、流程、内网、多层、域、Pwn 组合、Nday、AWD、PHP 审计等）。
- **增强替换 1 页**：`web-crypto-app`，保留原 slug 与主题，补充 ECB/CBC、Padding Oracle、长度扩展、mt_rand、RSA 弱用法。
- **站内原有 17 页保持不变**，作为基础层；新增页只做增量，不重复基础定义。

最终 Web 模块 **53 页 / 8 分类**：

| 分类 | 页数 |
|---|---:|
| 协议、环境与工具 | 5 |
| 信息收集与源码 | 5 |
| 注入与执行 | 16 |
| 客户端与浏览器 | 6 |
| 认证、会话与逻辑 | 4 |
| 语言与框架 | 5 |
| 协议层与高级 | 4 |
| 云、内网与实战 | 8 |

## 2. 页面格式

每个文件均为 Astro content collection 可用的 markdown：

```yaml
---
title: "页面标题"
summary: "一句话摘要"
module: "Web"
type: "知识点"
category: "8 分类之一"
tags: ["Web漏洞", "..."]
order: 4-40
---
```

正文结构统一：

1. 一段“这页解决什么问题”的定位 + 授权边界提示。
2. `## 01 …` 编号小节：判断表、命令、payload、版本差异。
3. 末尾“记录”表：入口、限制、利用、结果、复现命令。
4. 相关页面用 `/knowledge/<slug>/` 交叉链接。

## 3. 落库方式

1. 把 `content/knowledge/*.md` 复制到 Astro 项目的 `src/content/knowledge/`（或项目实际 content 目录）。
2. 确认 `web-crypto-app.md` 覆盖原文件（同 slug）。
3. 按 `reports/web-module-composition.md` 第三节更新 `/module/web/` 的分类与顺序；页面本身按 `order` 排序。
4. 如需工具索引，按 `reports/web-module-composition.md` 第五节更新 `/tools/?module=Web`（只改 Web 过滤结果，不动其他模块）。
5. 重新构建后，Pagefind 会自动索引新页面；`module=Web`、`type=知识点` 过滤可用。

## 4. 校验

运行：

```bash
python3 validate.py
```

本次结果：

- 37 个文件，frontmatter 全部完整；
- module 全部为 `Web`，type 全部为 `知识点`；
- category 均在 8 个分类内；
- order 4–40 连续、无重复；
- 正文合计约 14.1 万字符，平均 3.8 千字符/页（不含站内原有 17 页）。

## 5. 覆盖与“更详细”的保证

- `reports/coverage-matrix.md` 对 hello-ctf 的 60 个 Web 文件逐条给出映射，确保没有主题缺口。
- 对 hello-ctf 有长章节的主题（SQL、RCE、PHP 反序列化、SSTI、XSS、上传、SSRF/XXE、文件包含），采用“站内基础页 + 新增进阶页”双层结构：基础定义在原有页，新增页只写进阶语法、过滤绕过、工具参数、版本差异与记录表。
- 具体题目的完整 walkthrough 未收录；只抽取知识点、考点、工具用法与判断方法，符合“不往知识库加具体事例”的要求。
- 所有命令/payload 均标注“仅本地题目或授权环境”；未验证的版本差异标注“需本地验证”。

## 6. 未改动范围

- 只新增/替换 `content/knowledge/` 下的 Web 页面。
- 未修改 Misc、Reverse、Crypto、Forensics 模块内容。
- 未修改题目库、WP 库、工具库条目；工具索引建议仅作为维护参考。
- 未写入站点构建产物或全局配置。

## 7. 已知限制

- 源站 `code_audit.md`、`ad_hard.md` 未取到正文，分别由 `web-source-route`/`web-php-audit` 与 `web-ad-lateral` 覆盖。
- 容器内未找到 Astro 源码工程，因此本次以“可入库 markdown + 组成方案”交付，未直接改站点构建。
- 页面中的版本号/CVE 需在目标环境复核；利用前先在本地快照验证。
