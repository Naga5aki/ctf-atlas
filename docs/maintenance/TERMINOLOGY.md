# 术语与写法统一表

本文件规定正文里的工具名、产品名和技术名词写法，供写作与 `scripts/lint_writing.py` 共同使用。规则以项目现有文章的实际用法统计为基础（2026-11-26 统计 400 篇内容文件），只收录确认出现的名称；新增术语先在这里登记，再用于文章。

## 1. 总规则

- 正文提到产品时用官方大小写；代码块和行内代码里的命令、路径、参数按原样，不强制大小写。
- 中文与英文、数字之间**不加空格**，沿用现有样例（`看到index.php，继续确认PHP版本`）。
- 中文句子用全角标点；英文条目、代码、URL 内部用半角。
- 同一篇里只用一种写法；首次出现可写全称并附缩写，之后统一用缩写。

## 2. 工具与产品

| 术语 | 正文写法 | 命令/路径写法 | 说明 |
|---|---|---|---|
| Nmap | Nmap | `nmap` | 项目名首字母大写；正文不写 `nmap` 开头句 |
| Wireshark | Wireshark | `wireshark`、`tshark` | 命令行抓包工具是 `tshark`，不混称 |
| Burp Suite | Burp Suite | — | 两个词，不写 `BurpSuite` |
| sqlmap | sqlmap | `sqlmap` | 官方全小写，正文也不写成 `SQLMap` |
| Volatility | Volatility | `vol.py`、`vol` | 版本分写 `Volatility 2`、`Volatility 3`，不写 `Volatility2` |
| Docker | Docker | `docker` | |
| Kubernetes | Kubernetes；首次后可写 k8s | `kubectl` | 不写 `K8S` 全大写 |
| Nginx | Nginx | `nginx` | |
| Apache | Apache | `apache2`、`httpd` | 宝塔的 Apache 实例与系统 Apache 分开表述 |
| MySQL | MySQL | `mysql` | 不写 `Mysql` |
| ThinkPHP | ThinkPHP | — | 不写 `thinkphp` |
| PHP | PHP | `php` | |
| Linux | Linux | — | |
| Windows | Windows | — | |
| PowerShell | PowerShell | `pwsh`、`powershell` | 不写 `Powershell` |
| Python | Python | `python`、`py` | |
| Java | Java | `java` | |
| Node.js | Node.js | `node`、`npm` | 不写 `Nodejs` |
| Git | Git | `git` | |
| Kali | Kali 或 Kali Linux | — | 首次出现写 `Kali Linux` 即可 |
| Astro | Astro | `astro` | |
| Pagefind | Pagefind | `pagefind` | |

## 3. 取证与安全概念

| 术语 | 统一写法 | 避免 |
|---|---|---|
| 电子数据取证 | 电子数据取证 | 电子取证、数字取证混用（同一篇选一个） |
| 服务器取证 | 服务器取证 | 主机取证（除非引用原文） |
| 内存取证 | 内存取证 | 内存分析（口语可用，正文统一） |
| 网站重构 | 网站重构 | 网站恢复、站点重建混用 |
| 镜像 | 镜像 | 映像（同一篇选一个） |
| 副本 | 副本 | 拷贝（正文统一用副本） |
| 哈希 | 哈希 | 散列值、Hash 混用（首次可注 SHA-256） |
| 沙箱 | 沙箱 | 沙盒 |
| 反序列化 | 反序列化 | 反串行化 |
| 越权 | 越权 | 权限绕过（不同概念，不互换） |

## 4. 站点内部名词

| 术语 | 统一写法 | 说明 |
|---|---|---|
| 知识点 | 知识点 | 不写“知识条目”“知识页” |
| 维护稿 | 维护稿 | `src/content-curation/<id>.md` |
| 生成页 | 生成页 | `src/content/knowledge/<id>.md` |
| 考点 | 考点 | 不写“知识点要素” |
| 四环 | 四环 | 探测、利用、结果、排错 |
| 保留清单 | 保留清单 | 改写前的逐节对照表 |

## 5. 维护方式

- 新增术语：先在本表加一行，写清正文写法与命令写法，再用于文章。
- 发现正文写法与表冲突：先在原处改正，并在 `WORK-LOG.md` 记一条；不要批量替换后声称全模块已改。
- 本表不追求覆盖全部名词，只固化已经出现分歧或容易写错的名称。
