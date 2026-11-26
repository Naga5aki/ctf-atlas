# hello-ctf Web → ctf-atlas Web 覆盖矩阵

口径：hello-ctf 每个 Web 页面至少映射到一个 ctf-atlas 页面；已有页面作为“基础”，新增/增强页面负责“更详细、更具体”。具体题目过程不收录，只抽取知识点、考点、工具用法与判断方法。

共 60 个 hello-ctf Web 文件（含索引），映射到 ctf-atlas 的 53 个 Web 知识点页面（17 个站内已有 + 36 个新增/增强）。

| # | hello-ctf 页面 | ctf-atlas 对应页面 | 关系 | 覆盖要点 |
|---|---|---|---|---|
| 1 | `index.md` | `/module/web/` | 入口 | 模块导航、学习顺序 |
| 2 | `web_start.md` | `/module/web/` + `/challenges/` | 入口 | 入门题单、练习顺序、WP 检索 |
| 3 | `http.md` | `web-http-message` + `web-http-smuggling` | 基础+新增 | 请求行/头/体、方法、Host/UA/Referer/XFF/Content-Type、Cookie/Session、HTTPS 抓包 |
| 4 | `php_basic.md` | `web-language-reading` + `web-php-features` | 基础+新增 | 语法、变量、数组、表单、内建函数、函数安全、精度与类型转换 |
| 5 | `php_features.md` | `web-php-features` | 新增 | 弱类型、0e、数组绕过、strcmp/in_array/switch、intval、变量覆盖、伪协议、正则绕过、自增字符 |
| 6 | `php_unser.md` | `web-php-unserialize` | 新增 | 格式、可见性、魔术方法、POP、__wakeup 绕过、字符逃逸、phar、session、原生类、C:、phpggc |
| 7 | `sql_injection.md` | `web-data-query`（原 `web-sqli-advanced` 已合并） | 增强替换 | 原理与三条件、联合/报错/布尔/时间/堆叠、HANDLER、无列名、异或、token 绕过、二阶、宽字节、非 URL 注入点、时间/外带、DBMS 差异、sqlmap、失败分支 |
| 8 | `rce.md` | `web-runtime-boundary` + `web-rce-bypass` | 基础+新增 | 执行函数、空格/关键字/字符绕过、无回显、长度限制、disable_functions 六类突破、PHP 8.1.0-dev、表达式注入 |
| 9 | `CodeExecution.md` | `web-runtime-boundary` + `web-rce-bypass` | 基础+新增 | 代码执行成因、函数、语法、Linux/Windows 差异 |
| 10 | `file_upload.md` | `web-file-boundary` + `web-upload-bypass` | 基础+新增 | 前端/MIME、扩展名矩阵、.htaccess/.user.ini、CVE-2013-4547、内容检测、竞争、路径/文件名、解析链 |
| 11 | `any_file_read.md` | `web-path-tricks` | 新增 | 编码变体、敏感文件、/proc/self、Vite CVE-2025-30208、伪协议、日志投毒 |
| 12 | `dir_traversal.md` | `web-path-tricks` | 新增 | 穿越深度、编码/双写、Zip Slip、符号链接、写文件 |
| 13 | `logical_vuln.md` | `web-logic` + `web-race-logic` | 基础+新增 | 并发兑换/下单/提现/注册、单包并发、Turbo Intruder、多线程、状态跳跃、幂等 |
| 14 | `InfoGath.md` | `web-info` + `web-leak-files` | 基础+新增 | 目录/指纹/源码/备份/Git/JS/证书/历史信息 |
| 15 | `js_reverse.md` | `web-js-reverse` | 新增 | DevTools、断点、调用栈、Hook、AES/RSA 定位、CryptoJS、webpack、AST、WASM/Worker |
| 16 | `js_sandbox.md` | `web-js-sandbox` | 新增 | vm/vm2、原型链逃逸、child_process、vm2 CVE、隔离方案 |
| 17 | `session_jwt.md` | `web-session-jwt` | 新增 | Cookie/Session、固定/预测、JWT 结构、alg:none、弱密钥、RS→HS、kid/jku/x5u、claims |
| 18 | `csrf.md` | `web-csrf` | 新增 | GET/POST/JSON、SameSite、Referer/Origin、Token 缺陷、CORS、Bot 场景 |
| 19 | `xss.md` | `web-browser-output` + `web-xss-vectors` | 基础+新增 | 反射/存储/DOM、标签/事件、属性/URL/JS 上下文、编码、框架入口、CSP、HttpOnly |
| 20 | `ssti.md` | `web-template-injection` + `web-ssti-python` | 基础+新增 | 探测、Jinja2 MRO、globals、过滤器绕过、Twig/Smarty/Freemarker、盲 SSTI、外带 |
| 21 | `xxe.md` | `web-server-fetch` + `web-server-fetch-advanced` | 基础+新增 | 文件读取、OOB、参数实体、evil.dtd、报错 XXE、SSRF 面、防御 |
| 22 | `ssrf.md` | `web-server-fetch` + `web-server-fetch-advanced` | 基础+新增 | 四问、IP/URL 变体、DNS 重绑定、gopher Redis/FastCGI、云元数据、302/短地址 |
| 23 | `cache_poisoning.md` | `web-cache-poisoning` | 新增 | Cache Key、unkeyed input、命中头、投毒头、XSS/跳转/DoS、缓存欺骗、走私组合 |
| 24 | `prototype_pollution.md` | `web-prototype-pollution` | 新增 | __proto__/constructor、merge sink、qs/lodash/jQuery、鉴权绕过、RCE、DOM gadget、ppmap |
| 25 | `java_unser.md` | `web-java-security` | 新增 | 序列化格式、反射/ClassLoader/动态代理、URLDNS、CC1/CC6、ysoserial、fastjson/Jackson、JNDI、TemplatesImpl |
| 26 | `spring.md` | `web-spring-audit` | 新增 | SpEL、Actuator（env/heapdump/refresh/gateway/jolokia）、Spring4Shell、CVE-2022-22947、war/jar、审计 |
| 27 | `java_basic.md` | `web-java-security` | 新增 | JVM、字节码、classpath、反射、ClassLoader、URLClassLoader、动态代理、Serializable/transient/readObject |
| 28 | `java_audit.md` | `web-spring-audit` | 新增 | war/jar、pom、注解路由、web.xml、过滤器、sink 追踪、grep、CodeQL |
| 29 | `php_code_audit.md` | `web-php-audit` + `web-php-unserialize` | 新增 | 超全局入口、sink 清单、grep、变量覆盖、包含、SQL、反序列化、命令执行、框架路由 |
| 30 | `code_audit.md` | `web-source-route` + `web-php-audit` | 基础+新增 | 入口→过滤→sink、审计流程、工具 |
| 31 | `cloud_container.md` | `web-cloud-container` | 新增 | 容器识别、云元数据、docker.sock、privileged、K8s SA/API、对象存储 |
| 32 | `docker_env.md` | `web-docker-lab` | 新增 | 镜像/容器、端口/卷、compose、vulhub、Dockerfile |
| 33 | `docker_install.md` | `web-docker-lab` | 新增 | 安装、镜像加速、compose 插件、SSH/VS Code Remote |
| 34 | `web_env.md` | `web-docker-lab` + `web-local-lab` | 基础+新增 | HackBar/SwitchyOmega、PHP/Python/Java/Node、虚拟机与容器 |
| 35 | `vm_lab.md` | `web-docker-lab` | 新增 | NAT/桥接/Host-only/Internal、多网卡、多网段拓扑 |
| 36 | `burp.md` | `web-burp` + `/tool/web-burp/` | 基础 | Proxy、Repeater、Intruder、Decoder、Comparer、HTTPS 证书 |
| 37 | `ad_basic.md` | `web-ad-lateral` | 新增 | 工作组/域、DC、OU/GPO、域识别、Kerberos 流程 |
| 38 | `ad_hard.md` | `web-ad-lateral` | 新增 | Kerberoasting/AS-REP、委派、BloodHound、凭据、PTH/PTT、远程执行 |
| 39 | `lateral.md` | `web-ad-lateral` | 新增 | 凭据收集、PTH、PTT、mimikatz、远程执行 |
| 40 | `pentest_flow.md` | `web-pentest-flow` | 新增 | 七阶段、信息收集、初始访问、立足、提权、维持、复盘 |
| 41 | `foothold.md` | `web-pentest-flow` | 新增 | Webshell、冰蝎/哥斯拉/蚁剑、反弹 Shell、权限维持、免杀概念 |
| 42 | `internal_recon.md` | `web-internal-recon` | 新增 | 本机枚举、网段/主机发现、端口、凭据复用 |
| 43 | `proxy_tunnel.md` | `web-internal-recon` | 新增 | frp/nps/EW/Venom/chisel、ICMP/DNS 隧道、proxychains |
| 44 | `two_layer.md` | `web-layer-practice` | 新增 | 拓扑、打点、立足、代理、打 DMZ |
| 45 | `three_layer.md` | `web-layer-practice` | 新增 | 多层代理链、逐层打点、断链排查 |
| 46 | `multi_layer.md` | `web-layer-practice` | 新增 | 代理链设计、路由表/端口转发、稳定性、工具组合 |
| 47 | `awd.md` | `web-awd-practice` | 新增 | 规则计分、开局、审计、批量打点、修复、维持、监控、分工 |
| 48 | `nday.md` | `web-nday` | 新增 | 指纹、EXP 检索、读懂/改写、常见组件、验证、防御 |
| 49 | `review.md` | `web-pentest-flow` | 新增 | 读 WP、payload 库、错题本、知识库沉淀、出题 |
| 50 | `web_pwn.md` | `web-pwn-combo` | 新增 | 内部服务、样本获取、checksec/逆向、exploit 回传、提权链 |
| 51 | `sensitive_info.md` | `web-leak-files` + `web-info` | 基础+新增 | 注释、.DS_Store、.svn、.hg、JS、.git、.bak、robots、SSL、历史信息、接口、.swp |
| 52 | `py_script.md` | `web-python-script` | 新增 | requests、Session、params/data/json/files、代理、爆破、盲注、并发、重试 |
| 53 | `py_unser.md` | `web-python-security` | 新增 | pickle opcode、__reduce__、黑名单、RestrictedUnpickler、pker |
| 54 | `py_sandbox.md` | `web-python-security` | 新增 | MRO、__subclasses__、os._wrap_close、builtins 恢复、过滤绕过、audit hook |
| 55 | `flask_sec.md` | `web-python-security` + `web-ssti-python` | 新增 | session 结构、flask-unsign、secret_key、debug PIN、render_template_string |
| 56 | `include.md` | `web-file-include` | 新增 | LFI/RFI、判断、伪协议、pearcmd/peclcmd、/proc、日志、session.upload_progress、filter chain |
| 57 | `waf_bypass.md` | `web-waf-bypass` | 新增 | 指纹、SQL/XSS/RCE/上传语法绕过、协议级绕过、代码级 WAF、方法论 |
| 58 | `http_smuggling.md` | `web-http-smuggling` | 新增 | CL.TE/TE.CL/TE.TE、判定、利用、H2 变体、防御 |
| 59 | `web_crypto.md` | `web-crypto-app` | 增强替换 | ECB/CBC、Padding Oracle、长度扩展、mt_rand、RSA 弱用法、AES 密钥泄露 |
| 60 | `digest.md` | — | 工具产物 | 下载摘要，不产生知识点 |

## 说明

- **基础+新增**：站内已有页面保留，新增页面补充进阶语法、过滤绕过、工具参数与判断表；不重复基础定义。
- **新增**：hello-ctf 有独立章节、站内没有同等粒度的页面；按“原理—入口—利用—限制—防御—记录”组织。
- **增强替换**：`web-crypto-app` 用更完整的应用密码学版本替换原页面，保留原主题与 slug。
- 索引/题单不产生独立知识点，分别落到模块页与题目库；`code_audit.md`、`ad_hard.md` 源站未取到正文，按同主题页面覆盖。
