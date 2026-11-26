# Web 页已知缺口清单

截至 2026-11-26，整理自 `docs/maintenance/WORK-LOG.md` 里各批次记录的“没有写入”“只写……”。每行是当时留下的缺口。补全一项后删掉对应行，并在 WORK-LOG 记一笔。

| 页面 | 留下的缺口 | 出处 |
|---|---|---|
| `web-data-query` | 逐字拖库的拼接、导出整库、在操作系统上执行命令的 sqlmap 参数 | WORK-LOG 2026-10-25「SQL 注入页按类别重排」 |
| `web-data-query` | 联合查询拼接语句、报错截取语句、盲注脚本、写文件拿壳 | WORK-LOG 2026-10-25「SQL 注入页改成按现象讲解」 |
| `web-runtime-boundary` | 写文件命令、反弹命令 | WORK-LOG 2026-10-25「Web 六页补入综合靶场的复核顺序」 |
| `web-file-boundary` | 目录扫描只给了参数名；上传绕过文件名 | 同上 |
| `web-language-reading` | §02.4 Gateway（CVE-2022-22947）与 Web Flow（CVE-2017-4971）只写了成立条件，没有利用步骤；Gateway 路由正文 | 同上 |
| `web-local-lab` | §06 端口扫描、dirsearch、Burp、sqlmap、redis-cli 只写了“各回答什么”，没有完整命令 | 同上 |
| `web-info` | 扫描器报告的 `heapdump`、`env` 只写了“要打开再记”，没有命令 | 同上 |
| `web-local-lab`、`web-info`、`web-language-reading`、`web-data-query`、`web-runtime-boundary`、`web-file-boundary` | 原题相关的 flag、内网地址、木马连接、后台口令没有写入；dirsearch、Burp、sqlmap 的参数表保持原页 | 同上 |
| `web-data-query`、`web-browser-output`、`web-file-boundary`、`web-server-fetch`、`web-runtime-boundary`、`web-template-injection` | 可直接利用的语句、绕过样本和链式载荷没有写入 | WORK-LOG 2026-10-15「Web 六篇漏洞机制扩写」 |
| `web-request-auth`、`web-logic`、`web-source-route`、`web-language-reading`、`web-local-lab`、`web-parser-gap` | 票据伪造、隧道搭建、调试器 PIN 计算、请求走私报文、WAF 绕过样本没有写入 | WORK-LOG 2026-10-15「Web 剩余六篇核查扩写」 |
| `web-http-message`、`web-burp`、`web-info`、`git-history` | 攻击载荷和社工话术没有写入 | WORK-LOG 2026-10-15「Web 四篇技术手册补写」 |
| Web 模块各页 | 内网横向、WAF 替换表、具体注入语句没有写成操作步骤 | WORK-LOG 2026-10-15「Web 模块按三条题线补知识点」 |
