手里是 Web 服务器检材：可能是只读挂载的 Linux 根文件系统、Windows 导出、容器导出，或几份访问日志。本页回答五件事：网站由哪个虚拟主机提供、程序在哪个目录、连接哪一数据库、日志写在哪里、一次请求实际做过什么。原始材料保持只读；不执行检材中的 PHP 或其他代码。

**从 Web 配置对上站点 → 读 CMS 配置与数据库连接 → 用版本控制分清文件变化 → 读访问日志建时间线 → 清点暴露面并按最小证据整理结论 → Java 服务按配置、依赖与代码定位。**

<span id="01-从-web-配置建立应用范围"></span>

## 01 先把虚拟主机、程序目录、数据库和日志对到同一条站点

手里是只读挂载的 Linux 根文件系统，虚拟主机、程序目录、数据库和日志还没对上同一条站点。网站目录在，不等于 Nginx 曾把它提供给外部；配置里有域名，也不等于目标时段的 DNS 确实指向这台服务器。

操作顺序：先回答虚拟主机、程序目录、数据库和日志，再查后台入口、路由和文件变化。

**1. 先回答四个具体问题。** 网站由哪个虚拟主机提供、程序在哪个目录、连接哪一数据库、日志写到哪里。把这四项对应后，再查后台入口、路由和文件变化。后面分别用配置、文件和请求日志核对。

**2. 下面读取只读挂载到 `/mnt/evidence` 的 Linux 根文件系统。** 导出结果写入 `./work/`。PHP 文件只看文本，不执行。先运行下面的目录和软链检查。若链接目标是 `/etc/nginx/...` 这样的绝对路径，应到检材根目录中找对应文件，避免误读分析机自己的配置。目录不存在或软链跳出检材根时，先改读取位置，不把分析机文件当成站点配置。

```bash
EVIDENCE_ROOT=/mnt/evidence
mkdir -p ./work
ls -ld "$EVIDENCE_ROOT/etc/nginx" "$EVIDENCE_ROOT/var/www"
find "$EVIDENCE_ROOT/etc/nginx" -maxdepth 2 -type l -printf '%p -> %l\n'
```

检材里的 Nginx 目录、网站目录和软链目标对上了，才继续查虚拟主机；四项还没放进同一条时，不写成网站已经对外提供。`EVIDENCE_ROOT`、`./work/` 和这次目录、软链检查的输出一起保存；分析机上的 `/etc/nginx/...` 不能代替检材里的同名路径。

### 01.1 先确定部署边界与技术栈

每份材料来自物理机、云主机、虚拟机还是容器，还没登记。数据库、附件和对象存储也可能不在这份根目录里。

操作顺序：先登记材料来源，再按部署类型找下一份配置，端口和扩展名只用来继续找。

**1. 先登记每份材料来自物理机、云主机、虚拟机还是容器，再查看操作系统和采集清单。** 重点检查：数据库、附件、对象存储是否另有材料。云主机磁盘快照通常不包含独立云盘、对象存储或远程数据库。Linux 根目录也可能只是容器导出。不要因为目录都叫 `data`，就把程序、数据库和附件归到同一实例。

**2. 按部署或服务找定位起点。** 对不上远端主机、端口或独立采集材料时，先把这一项留空：

<details>
<summary>展开部署类型定位起点表</summary>

| 部署或服务 | 定位起点 | 需要核对的关系 |
| --- | --- | --- |
| 单机部署 | 服务启动定义、Web 配置、应用配置、数据库目录 | Web、运行时、数据库是否属于同一实例与时间范围 |
| 站库或文件分离 | 数据库连接地址、共享挂载、附件 URL、代理配置 | 远端主机、端口、名称解析及独立采集材料 |
| Apache / Nginx | 主配置、包含文件、虚拟主机、代理或 FastCGI 配置 | 监听 → 域名 → 程序或后端 → 日志 |
| Tomcat | 实例的 `conf/server.xml`、Context 描述、部署应用 | Connector → Host → Context → 应用与日志 |
| IIS | `applicationHost.config`、站点绑定、应用与虚拟目录 | 站点 ID → IP/端口/Host → `physicalPath` → 日志 |

</details>

**3. 平台先看系统记录，再核对程序版本和启动路径。** 平台先看 Linux 的 `/etc/os-release`、服务文件和进程记录，或 Windows 的系统与服务记录，再核对程序版本和启动路径。

**4. 不要只凭端口判定服务器类型。** 不要只凭 `80`、`443`、`8080` 判定服务器类型：Apache、Nginx 可运行于 Windows，PHP 可由不同 Web 服务处理，Java 也可能使用内嵌服务器。扩展名和端口只用于找下一份配置。端口对不上常见值时，继续读启动定义，不换一套假定的软件。

每份材料的来源登记清楚，Web、运行时、数据库是否同一实例有了判断；云盘、对象存储或远程数据库不在这份快照里的，单独记为还没采集到。定位起点和需要核对的关系来自同一份部署记录，下一份要打开的配置路径写进清单。

### 01.2 Nginx 配置体系与包含关系

主配置、站点目录和附加配置都在，还不知道哪一份真正被 `include` 进了这次解析。文件放在启用目录里，也不等于它参与了这个站点。

操作顺序：按包含顺序读到目标 server，核对同一站点的字段，要看展开结果时只测受控副本。

**1. 先认这四类位置，再按包含顺序读。**

<details>
<summary>展开 Nginx 配置位置表</summary>

| 位置 | 常见作用 | 需要确认的内容 |
| --- | --- | --- |
| `/etc/nginx/nginx.conf` | 主配置 | `include`、全局日志、HTTP 配置入口 |
| `/etc/nginx/sites-available/<site>` | Debian 系常见站点定义目录 | 文件内容是否被启用配置引用 |
| `/etc/nginx/sites-enabled/<site>` | 常见启用目录，成员常为软链 | 软链目标及主配置的包含模式 |
| `/etc/nginx/conf.d/*.conf` | 附加配置 | 独立虚拟主机、路由、rewrite 与日志覆盖 |

</details>

**2. 按包含顺序读取。** 打开主配置，找到 `include`。将文件名或通配符展开到检材里的实际文件。继续检查这些文件自己的包含项，直到找到目标 `server`。某一层文件不存在或通配符没有命中时，记下这一层，不把别的虚拟主机的行补进来。

**3. 目录惯例不等于已经启用。** `sites-enabled` 和 `sites-available` 只是目录惯例；文件只有被主配置包含才参与这次配置解析。安装前缀不同，路径也会不同。[include 指令](https://nginx.org/en/docs/ngx_core_module.html#include)允许包含关系继续向下展开。

```bash
grep -rInE '^[[:space:]]*(include|server_name|listen|root|alias|index|location|rewrite|try_files|proxy_pass|fastcgi_pass|ssl_[[:alnum:]_]+|access_log|error_log)[[:space:]]' \
  "$EVIDENCE_ROOT/etc/nginx"
```

**4. 上面的检索用于找到候选行，不是生成一份可直接使用的配置。** 对每条命中，打开完整 `server` 和 `location`，再看字段是否在下层被覆盖。域名、根目录和代理必须取自同一个站点，不能把不同虚拟主机的命中行拼在一起。若软链指向 `/etc/nginx/sites-available/site`，应读取 `$EVIDENCE_ROOT/etc/nginx/sites-available/site`，而不是分析机的 `/etc/nginx`。

**5. 每个字段接着查什么。** `server_name`、`listen`：确认请求要用的名称、地址和端口。`root/alias`、`index`：定位网站文件及默认入口。`location`、`rewrite`、`try_files`：确认 URI 被交给哪个文件或处理器。`fastcgi_pass` / `proxy_pass`：继续查后端地址、`upstream`、include，以及 PHP-FPM pool 或应用启动定义。SSL 指令：找到 TLS 设置、证书和密钥材料。`listen` 写在配置里，还不说明这个地址已经能连上。

**6. 安装前缀不同就从实际入口开始。** 宝塔等安装可能使用 `/www/server/...`。先按实际启动入口确定配置树，再搜索，不固定从发行版目录开始。

**7. 已获授权的活体采集还要保存目标 Nginx master 的启动参数。** 保存服务定义、可执行文件路径与版本，确认是否使用 `-p` 前缀或 `-c` 配置文件。使用可信的对应版本工具检查受控配置副本时，可按该实例的参数执行。改日志、证书等引用路径之前，先停在分析副本上。

【仅在副本/仿真/授权环境执行】

```bash
nginx -T -p /work/replay/nginx/ -c conf/nginx.conf \
  > ./work/nginx-config.txt 2> ./work/nginx-config-test.txt
```

**8. 看懂 `-T` 的输出范围。** `-T` 会测试并输出**这次从磁盘读到的配置**，不是向运行中的 master 查询历史配置。命令只对已准备好的受控配置副本执行，不运行 `/mnt/evidence` 中的 Nginx 程序。[命令行参数](https://nginx.org/en/docs/switches.html)

测试还可能打开日志、证书等引用文件，先把这些路径改到分析副本。保存配置输出、错误输出和退出状态；要判断目标时段是否已采用这份配置，还需查启动、reload、错误日志及采集时间。测试失败时保留退出状态，不把分析机上另一次 `nginx -T` 当成检材配置。

被主配置包含的那个 `server` 连同同一站点的名称、根目录、代理和日志一起对上；软链还指向分析机，或下层 `location` 覆盖没读完时，不把检索行拼成一份站点。命中行、完整 `server`、配置输出、错误输出和退出状态一起保存；`-T` 的输出标明是这次从副本磁盘读到的配置。

### 01.3 实战：定位网站目录与伪静态规则

主配置、站点定义、附加配置及 `/var/www/` 都在，还没说明这个虚拟主机从哪里读程序、请求怎样进 PHP、日志写到哪里。示例片段不是所有 PHP 项目的通用模板。

操作顺序：读已包含的站点定义，按检材根找程序和日志，再核对 rewrite 和 root 有没有被覆盖。

**1. 第一步：读取已确认被包含的站点定义。**

```bash
cat "$EVIDENCE_ROOT/etc/nginx/sites-available/site"
```

**2. 示例片段只摘录一份 PHP 站点。** 这里只摘录一份 PHP 站点的虚拟主机与 rewrite，不含完整 PHP 处理器配置；它不是可直接运行的通用模板，也不能据此认定所有 PHP 或 ThinkPHP 项目都使用相同规则。

```nginx
server {
    listen 80;
    server_name media.example.test;
    root /var/www/html/media-site;
    access_log /var/log/nginx/media.access.log;
    error_log /var/log/nginx/media.error.log;
    location / {
        rewrite ^/(.*)$ /index.php?s=$1 last;
    }
}
```

**3. 第二步：按检材根目录定位程序与日志。** 文件或日志不在声明路径上时，记下缺失，不改用另一个站点的目录。

```bash
ls -la "$EVIDENCE_ROOT/var/www/html/media-site"
ls -l "$EVIDENCE_ROOT/var/log/nginx/"*media*
```

**4. 按示例继续检查。** 到 `/var/www/html/media-site` 找网站程序，并核对 `index.php`。看 rewrite 后的 PHP 请求由哪个 `location` 处理，是否传给正确后端。看同级或嵌套规则有没有覆盖 `root`。到已声明的日志路径检查实际文件及目标时段。

**5. 拼接方式变了就重新定目标。** `root` 通常用于拼接请求路径；若使用 `alias`、变量或反向代理，必须按那一条规则重新确定目标，不能沿用同一个拼接公式。

**6. 配置说明打算如何提供网站。** 要说明历史上确实有请求，再找日志中的 Host 或 URI。仅凭配置修改时间，仍不能确定规则开始生效的时刻。配置里的 `listen` 也不是已经能连上的地址。

**ThinkPHP 一类后台不要按固定后缀猜。** 站点根目录从上面的 `root` 读到。数据库类型从应用的数据库配置读。后台地址把路由、库里的 URL 映射和配置里的伪静态后缀拼在一起，再和访问日志里真实出现的路径对齐。列表页和真正执行导出的方法可以差一层，以代码绑定的动作为准。口令算法读校验函数；存的是 bcrypt 时，结论写算法名。管理员的登录时间早于创建时间时，先确认两列的单位和时区，再把它列为篡改候选。删除操作的最早来源，先在菜单表查出该动作的编号，再在管理员日志里按这个编号取时间最早的一条。验证码比对位置是真正从缓存读出验证码并比较的类；只装请求字段的类分开记。

这个虚拟主机的程序目录、rewrite 和日志路径对上，目录里实际看到的文件也核对过；日志里还没有对应 Host 或 URI 时，不写成历史上确实有请求。站点定义、目录列表和已声明日志路径的文件清单一起保存。

### 01.4 对真实规则文件计算 SM3

01.3 已经定位到保存规则的站点文件，这一节对它做摘要固定；继续按服务器类型读 Apache 配置时，直接进入 01.5。规则可能散在屏幕上的几行 rewrite 里，摘要若只盖住选中行，对不上整份文件。先确定规则实际位于哪个文件，再对该文件的完整字节计算摘要。

操作顺序：先定规则所在文件，对完整字节算 SM3，两个工具的摘要要一致。

**1. 不要只对屏幕上选中的 rewrite 行计算，也不要把另一份相似配置误认成目标。** `openssl dgst -sm3` 需要 OpenSSL 1.1.1 及以上才提供 SM3；Python 的 `hashlib.new("sm3", ...)` 同样取决于它链接的加密库。先记录两个工具的版本，不支持时保留诊断，换算法后不能仍称 SM3。

```bash
openssl dgst -sm3 "$EVIDENCE_ROOT/etc/nginx/sites-available/site"
python3 - "$EVIDENCE_ROOT/etc/nginx/sites-available/site" <<'PY'
import hashlib
import pathlib
import sys
p = pathlib.Path(sys.argv[1])
data = p.read_bytes()
print(f"bytes={len(data)}")
print(hashlib.new("sm3", data).hexdigest())
PY
```

**2. 核对摘要结果。** 两个工具的十六进制摘要应一致；同时保存文件字节长度、实体路径、软链目标和读取时间。

**3. 算法或材料变了就分开记。** Python 所连接的加密库没有 SM3 时会报错，记录这个诊断，换算法不能仍称 SM3。软链路径、链接目标字符串和目标文件内容是三种不同材料；只有实际读到同一份目标字节，文件内容摘要才相同。编码或换行转换会改变摘要，应另存转换后的阅读副本。报错或两边摘要不一致时，保留诊断，不改称已经核对通过。

同一份目标文件上，两个工具算出的 SM3 十六进制摘要一致，这份规则文件才算固定下来；库不支持 SM3、软链没读到目标字节，或做了编码转换时，保留诊断，不把另一份摘要仍称为这份文件的 SM3。字节长度、实体路径、软链目标、读取时间与两条摘要命令的输出写在一起；转换后的阅读副本另行保存。

### 01.5 实战：从 Apache 配置定位站点

服务器导出包含 `/etc/apache2/`、网站目录和 Apache 日志，需要确认 `portal.example.test` 对应的应用。主配置文件名并不固定，还没沿包含关系走到这个虚拟主机。

操作顺序：从启动定义找主配置，沿 Include 读到站点文件，分开记 ServerRoot 和 DocumentRoot。

**1. 先找主配置，再读站点文件。** 先从启动定义确定主配置；其他安装可能使用 `/etc/httpd/conf/httpd.conf` 或安装前缀下的 `conf/httpd.conf`，文件名并非固定。在启动定义里确定配置入口，沿 `Include` / `IncludeOptional` 找到目标虚拟主机。下面检查软链，并读取示例站点文件的完整内容。包含文件缺失时记下断点，不换一份同名配置顶上。

**2. 需要运行实例、模块和控制命令时，转到网站重构。** 使用[PHP 篇的 Web 实例核对](/knowledge/forensic-website-reconstruction/#044-apachehttpd-与-apachectl-的实例核对与恢复)；这里专门确定离线文件的位置，不复制整套启动流程。

```bash
find "$EVIDENCE_ROOT/etc/apache2" -maxdepth 3 -type l -printf '%p -> %l\n'
cat "$EVIDENCE_ROOT/etc/apache2/sites-available/portal.conf"
```

**3. 两条根目录不要混。** 主配置的 `ServerRoot /etc/apache2` 是解析配置及相对路径的基准；虚拟主机的 `DocumentRoot /srv/portal/public` 才是网站文件候选目录。按检材根目录分别找到这两个位置。

**4. 再在同一 VirtualHost 中检查代理、重写和目录权限。** 确认哪些请求真正读取 DocumentRoot。[Apache 核心指令](https://httpd.apache.org/docs/2.4/mod/core.html#serverroot)、[URL 映射](https://httpd.apache.org/docs/2.4/urlmapping.html)

**5. 配置与目录对应后，可以说明离线部署关系。** 服务是否在目标时段运行，还需进程、启动或请求记录。要在副本测试版本、配置和模块，转到网站重构第 04.4 节。只有配置、没有这些记录时，不写成目标时段已经在提供这个站点。

`portal.example.test` 所在虚拟主机的配置入口、`ServerRoot /etc/apache2` 和 `DocumentRoot /srv/portal/public` 沿 `Include` / `IncludeOptional` 走到，两条根目录没有混用；目标时段是否运行，还缺进程、启动或请求记录。软链列表、站点文件和两个根目录在检材中的位置一起保存。

### 01.6 实战：串联 Tomcat 的端口、应用与日志

一份 Java 服务导出包含实例启动定义、`conf/`、`webapps/` 与 `logs/`，需要定位 `/support/` 应用。另一套安装的 `CATALINA_HOME` 或同名 `server.xml` 还可能混进来。

操作顺序：先确认 CATALINA_BASE，读 Connector、Host 和 Context，日志按 AccessLogValve 找。

**1. 先由启动定义确认实例基准。** 先由 `-Dcatalina.base`、环境与服务定义确认实例的 `CATALINA_BASE`，不要把另一套安装的 `CATALINA_HOME` 或同名 `server.xml` 混入。缺少启动定义时，明确记下尚未确认实例基准路径。

**2. 位置与命令：以下路径是已确认实例的示例。** 搜索目录不存在时按实际材料调整，不改去另一套安装。

```bash
TOMCAT_BASE="$EVIDENCE_ROOT/opt/tomcat-instance"
rg -n 'Connector|<Host|<Context|appBase|docBase|AccessLogValve|directory=|pattern=' \
  "$TOMCAT_BASE/conf"
find "$TOMCAT_BASE/webapps" -maxdepth 4 -type f \
  \( -name '*.war' -o -name 'web.xml' -o -name 'context.xml' \) -print
find "$TOMCAT_BASE/logs" -maxdepth 1 -type f -print
```

**3. 按命中位置逐项读取。** 打开 `server.xml` 的完整 Connector，记录协议、地址和端口。`redirectPort` 是安全约束跳转使用的端口值，不证明那里已有监听。找 Host 的 `name`、`appBase`，确认 `/support/` 属于哪个主机。找 Context 的 `docBase`，确定实际目录或 WAR。继续读 `conf/<Engine>/<Host>/*.xml`、`META-INF/context.xml` 和 `WEB-INF/web.xml`，不要只看 server.xml。

**4. webapps 只是常见起点。** `webapps` 是常见起点，目标应用也可能放在别处。[Connector](https://tomcat.apache.org/tomcat-10.1-doc/config/http.html)、[Host](https://tomcat.apache.org/tomcat-10.1-doc/config/host.html)、[Context](https://tomcat.apache.org/tomcat-10.1-doc/config/context.html)

**5. 日志从配置找，不凭名称猜。** 在 Engine、Host 或 Context 中找到 `AccessLogValve`，读取 `directory`、`prefix`、`suffix`、`pattern` 和条件记录设置。相对目录按 `CATALINA_BASE` 解析，`logs` 只是默认候选。[Access Log Valve](https://tomcat.apache.org/tomcat-10.1-doc/config/valve.html#Access_Log_Valve)

**6. 没有启用访问日志时，不要用运行日志顶替。** 没有启用访问日志的应用可能只有运行日志，两者不能互换。用部署日志、目标请求和应用内容互相核对。配置里的端口和 `redirectPort` 都还不说明已经有监听。

这个实例的 `CATALINA_BASE`、Connector 的协议地址端口、`/support/` 的 `docBase` 和访问日志的目录、字段对上；没有 `AccessLogValve` 时访问记录尚未确认，没有启动定义时实例基准路径尚未确认。`conf/` 命中行、应用描述文件和 `logs/` 里按配置找到的文件一起保存，没有混入另一套 `server.xml`。

### 01.7 实战：从 IIS 绑定定位程序与日志

Windows 系统导出包含 IIS 全局配置、网站目录和日志，需要对应 `portal.example.test`。分析机上的同名目录还不能拿来解释目标系统的路径。

操作顺序：保全 applicationHost.config，从同一个 site 读到 physicalPath，再按站点 ID 找日志。

**1. 先保全全局配置及它引用的文件。** 先保全 `%windir%\System32\inetsrv\config\applicationHost.config` 及配置引用的文件。共享配置或路径环境变量应按目标系统解释，不能使用分析机的同名目录。

**2. 在 Windows 分析副本中静态查看配置。** 示例盘符和文件名按实际采集路径替换。路径打不开时记下实际采集位置，不改读分析机的 IIS 目录。

```powershell
$IisConfigCopy = 'D:\work\windows\Windows\System32\inetsrv\config\applicationHost.config'
Select-String -LiteralPath $IisConfigCopy -Pattern '<site ', '<binding ', '<application ', '<virtualDirectory ', '<logFile ', '<siteDefaults'
Get-ChildItem -LiteralPath 'D:\work\windows\inetpub\logs\LogFiles' -Directory
```

**3. 从同一个 site 逐层读。** 先记录名称和 ID，再读 binding 的协议、IP/端口/主机头，最后读 application、virtualDirectory 的 `physicalPath`。一个站点可以有多个绑定和应用，要分别列出。

**4. 默认目录只是候选。** `C:\inetpub\wwwroot` 只是常见默认目录，实际程序位置按配置值确定。[IIS site 配置](https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/)

**5. 接着定位日志。** 将站点设置与默认值一起读，确认 `logFile` 是否启用、目录在哪里、采用什么格式和字段，再按站点 ID 找文件。`W3SVC<站点ID>` 是常见目录；集中日志、自定义目录或 ETW 另按配置找。[IIS logFile 配置](https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/logfile/)

**6. 先看字段和时间含义。** W3C 日志先看 `#Fields`；记录时间是 UTC，轮转按本地时间也不会改变这一点。配置绑定存在只说明配置关系，历史启用和访问仍查服务、请求记录。没有请求记录时，不写成这个绑定当时已经在接流量。

`portal.example.test` 所在 site 的 ID、绑定和 `physicalPath` 来自同一个 site，`logFile` 指向的目录也按站点 ID 找到；历史启用和访问还要服务、请求记录，日志目录不是 `W3SVC<站点ID>` 时按配置另找。`applicationHost.config`、站点 ID 和日志文件位置一起保存；`#Fields` 已看过，时间按 UTC 解释。

### 01.8 实战：区分宿主 Apache 与容器 Nginx

服务器导出同时出现 Apache 配置、容器内 Nginx 配置和两个网站目录。`portal.example.test` 的请求经过哪一套服务还没画出来，不能选出第一个命中的目录就停止。

操作顺序：分开读两套根目录和代理，端口和站点对上再查容器元数据，对不上就分开登记。

**1. 把容器根文件系统导出单独放在 `./work/container-root/`。** 静态定位各自的根目录、代理和日志定义；容器导出不保证包含挂载卷。卷不在导出里时记下缺口，不把宿主机目录当成容器里的网站文件。

```bash
rg -n 'ServerName|DocumentRoot|ProxyPass|CustomLog|ErrorLog' \
  "$EVIDENCE_ROOT/etc/apache2"
rg -n 'server_name|listen|root|alias|proxy_pass|fastcgi_pass|access_log' \
  ./work/container-root/etc/nginx
```

**2. 先画出请求方向。** 若 Apache 的代理目标对应容器 Nginx 的端口和站点，再查该容器的 inspect/创建元数据、端口发布、挂载、进程及两端日志。几项一致时，才将它们记为同一请求的前端和后端。

**3. 两套服务各走各的，就分开登记。** 若两套服务各自提供不同名称或端口，就分开登记。[Docker 容器与镜像证据](/knowledge/docker-evidence-03/)、[Docker 网络与 Compose](/knowledge/docker-evidence-05/)用于补查容器发布和挂载，不在本节重复整套命令。

**4. 同名不足以并成一个网站。** 同一 IP、同名网站目录或两套软件均已安装，不能证明它们服务同一网站。配置的代理目标、容器历史 IP 和当前 IP 也可能不同，结论应限定到材料覆盖的时间和实例。对不上时保持两套记录。

`portal.example.test` 的前端和后端分别落在哪一套服务、代理目标是否对得上端口和站点，几项一致才记成同一条请求路径；容器导出没有挂载卷，或历史 IP 和当前 IP 不同时，不把两套安装写成同一个网站。两套配置的命中行、`./work/container-root/` 的范围和容器元数据一起保存。

<span id="02-cms-配置与业务属性"></span>

## 02 按配置字段读出站点属性与数据库连接

业务配置和数据库连接可能不在同一个文件里，站名、模板和库地址还没按字段对上。先列出实际文件，再读被程序用到的值。

操作顺序：按配置字段找关联材料，再按应用类型核对真正被读取的连接。


### 02.1 以配置字段定位关联材料

ThinkPHP、maccms 类应用常把业务配置与数据库连接分开保存。目录布局依版本而变，键名还没对上实际文件。

操作顺序：先列出实际 php 文件，按键名读取，口令只登记位置，不执行配置。

**1. 先列出实际文件，再按键名读取。** 配置值还要和页面、缓存、日志或其他版本交叉核对：

<details>
<summary>展开配置字段线索表</summary>

| 位置或字段 | 可提取的线索 | 交叉核对 |
| --- | --- | --- |
| `application/extra/*.php` | 站点名称、域名、备案号、公告、社交链接 | 站点页面、缓存、访问日志、其他配置版本 |
| `application/database.php` | `hostname`、`database`、`username`、`password`、`hostport` | 名称解析、数据库实例与连接日志 |
| `site_url` / `site_wapurl` | 主站与移动站配置 | 不混同两个字段；核对实际请求 |
| `site_icp` | 应用填写的备案标识 | 只能先表述为配置值，不能直接证明登记有效 |
| `template_dir` | 当前配置引用的模板目录 | `template/<目录>/info.ini` 与模板文件 |
| TG/QQ 或客服链接 | 公开联系渠道、群组名称或标识 | 与聊天、访问或业务记录关联 |

</details>

```bash
find "$EVIDENCE_ROOT/var/www/html/media-site/application" -maxdepth 3 -type f -name '*.php' -print
grep -rInE 'site_url|site_wapurl|site_icp|template_dir|hostname|database|hostport|t\.me|qq' \
  "$EVIDENCE_ROOT/var/www/html/media-site/application"
```

**2. 口令只登记存在和路径。** 配置中含有口令时，报告可记录字段存在与证据路径，并限制口令展示。不要通过 `php 配置文件` 或引入 PHP 文件的方式求值；配置可能包含可执行代码。键没有命中时，记下搜过的目录，不改用执行配置来“补出”字段。

实际存在的配置文件，以及 `site_url`、模板目录、数据库字段等键的配置值对上了；配置值还没和页面、名称解析或连接日志对上时，备案号和口令都只是配置里的文字。文件清单和带行号的键名命中一起保存；字段来自文本读取，不是执行 PHP 得到的，口令只留下证据路径。

### 02.2 实战：由模板配置读取元信息

配置记录 `template_dir => 'blue_theme'`，还不知道它指向的目录在不在、元信息是什么。值也可能被环境变量、另一份配置或缓存盖掉。

操作顺序：先读完整配置确认没被覆盖，再打开模板目录和 info.ini。

**1. 先读取完整配置，确认值未被环境变量、另一份配置或缓存覆盖，再定位文件。** 目录不存在时保留差异，不换一个相似主题目录。

```bash
cat "$EVIDENCE_ROOT/var/www/html/media-site/application/extra/maccms.php"
ls -la "$EVIDENCE_ROOT/var/www/html/media-site/template/blue_theme"
cat "$EVIDENCE_ROOT/var/www/html/media-site/template/blue_theme/info.ini"
```

**2. 示例输出只说明文件里写了什么。** `name=Blue Theme`、`version=1.4`、`author=Example Studio`。这支持该目录保存了上述模板元信息；作者字段是文件声明，不能直接认定实际部署者身份。记录配置值、文件路径、字节摘要及页面或缓存中的对应样式。配置指向不存在的目录时，应保留“配置引用存在、目标文件未发现”的差异。

`template_dir => 'blue_theme'` 指向的目录和 `name=Blue Theme`、`version=1.4`、`author=Example Studio` 对上；目标目录不存在时，只保留“配置引用存在、目标文件未发现”，作者字段不写成部署者身份。配置摘录、模板目录列表、`info.ini` 和字节摘要一起保存。

### 02.3 按应用类型定位连接配置

配置文件名只是候选位置，真正使用哪个值还没沿程序读取、外部配置、环境和启动参数核对。网站目录里没有数据库文件，也不能据此认定未使用数据库。

操作顺序：先填一行连接目标，按应用类型打开候选文件，口令只登记位置，不启动应用求值。

**1. 先记录驱动或 provider、地址、端口、库名及配置来源。** 再判断数据库是在本机、容器还是远端。

**2. 每个数据库连接填一行。** `DB_HOST`、`DB_PORT`、`DB_DATABASE`、`DB_USERNAME`、`DB_PASSWORD` 分别对应地址、端口、库名、用户和受控口令位置。实际项目可能使用别的键名，按代码含义对应，不改成这五个固定字段。同一行补上驱动、TCP/socket、字符集和加载来源。端口藏在连接串时按驱动解析，不自动填 3306。随后核对实际实例、库名、表前缀和账户；服务、DDL 与权限的完整命令保留在[数据库恢复](/knowledge/forensic-database-recovery/)，这里先把连接目标找准。

**3. 按应用类型核对候选位置。** 文件不在表中的路径上时，沿这一类应用的读取链继续找，不套另一种框架的文件名：

<details>
<summary>展开应用类型候选位置表</summary>

| 应用类型 | 候选位置 | 核对要点 |
| --- | --- | --- |
| ASP.NET Framework | 站点 `web.config` 的 `connectionStrings` | `name`、`providerName`、连接地址及 `configSource` 引用；核对代码实际读取的连接名 |
| 经典 ASP | `.asp`、被 include 的配置与连接代码 | 沿 `ADODB.Connection` 等读取链定位，不能假设必有 `web.config` 连接串 |
| PHP | `config.php`、数据库配置目录、`database.php`、`.env`；WordPress 的 `wp-config.php` | 实际 require/include、环境读取、配置缓存与连接初始化；ThinkPHP 字段见第 02.1 节，WordPress 的 `DB_NAME`、`DB_USER` 分别对应库名、用户名，`DB_HOST` 的主机/端口/socket 写法依实际驱动解析，另核对 `$table_prefix`，不强加 `DB_DATABASE` / `DB_USERNAME` 键 |
| Java / Spring Boot | `application.properties`、`application.yml` / `.yaml`、`application-<profile>.*` | 打包配置、外部配置目录、活动 profile、环境变量、系统属性和启动参数 |
| Python / Django / Flask | Django 设置模块的 `DATABASES`，Flask 项目的连接初始化、配置对象与环境 | Django 的 `HOST/PORT/NAME/USER/PASSWORD` 按所选数据库别名核对；Flask 没有统一必备的数据库配置文件，沿实际驱动或扩展读取链定位 |
| Node.js / Express | 进程环境、项目配置、连接 URL 与数据库客户端初始化 | Express 不规定统一数据库字段；`DATABASE_URL` 或自定义字段按驱动解析，再核对启动脚本及进程/容器环境 |

</details>

```bash
find "$EVIDENCE_ROOT/var/www/html/portal-site" -maxdepth 4 -type f \
  \( -iname 'web.config' -o -iname '*config*.php' -o -iname '*database*.php' \
     -o -name '.env' -o -name 'application*.properties' -o -name 'application*.yml' \
     -o -name 'application*.yaml' -o -name 'settings*.py' \) -print
rg -l 'connectionStrings|configSource|ADODB\.Connection|PDO|mysqli|spring\.datasource|spring\.profiles|spring\.config' \
  "$EVIDENCE_ROOT/var/www/html/portal-site"
```

**4. 命令只列出候选文件路径。** 完整内容在受控分析视图内读取。Java 的 WAR/JAR 配置还可能在归档中，先列成员再静态提取目标文件，不能用 `java -jar` 来寻找连接信息。

**5. 外部文件和 profile 按这一版的机制核对。** ASP.NET 的 `connectionStrings` 可以通过 `configSource` 指向外部文件，见 [Microsoft 连接字符串与配置文件](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/connection-strings-and-configuration-files)。Spring Boot 会考虑 profile 配置和外部配置，具体加载顺序与覆盖规则按目标版本核对，见 [Spring Boot 外部配置](https://docs.spring.io/spring-boot/reference/features/external-config.html)。这些机制不能推广为所有 ASP 或 Java 应用的固定布局。口令或授权码只登记存在、受控证据路径、行号与摘要，不写入公开结果；连接配置存在也不证明该凭据当时有效或连接成功。数据库实例、数据与统计的验证继续见 [数据库取证](/knowledge/fic-case-05/)。

**6. 只读取配置文本。** WordPress 字段依据见 [官方配置样例](https://github.com/WordPress/WordPress/blob/master/wp-config-sample.php)，Django 字段与多数据库别名见 [DATABASES 设置](https://docs.djangoproject.com/en/5.2/ref/settings/#databases)。只读取配置文本，不通过启动 PHP、Python 或 Node 应用求值；动态覆盖继续与启动记录核对。启动记录没有时，停在“配置里有这个值”。

这一行连接的驱动、地址、端口、库名、用户和配置来源填齐；口令是否当时有效、连接是否成功，还要实例和连接日志，没有数据库文件不等于没有数据库。候选文件路径、受控视图中的字段位置、口令的证据路径和摘要一起保存；键名按代码含义对应，没有用启动应用来求值。

### 02.4 实战：验证首页字段、图片目录与 Logo

站点副本包含首页、模板、CSS 与多处图片目录，品牌标识和首页声明的业务范围还没从引用关系里定下来。不能凭 `css/`、`images/` 等目录名直接指定图片位置。

操作顺序：先确认 Web 根和首页入口，沿引用找图片，再用 root、alias 或代理规则落到文件。

**1. 先确认 Web 根目录与实际首页入口，再沿模板或静态页面的引用查找。** 下例使用已经确认的 `portal-site`；命中内容只用于定位，继续读取所属模板和样式规则。文件不在命中路径上时保留差异。

```bash
SITE_ROOT="$EVIDENCE_ROOT/var/www/html/portal-site"
rg -n -g '*.html' -g '*.php' -g '*.css' \
  '(<title|<h1|<img|background-image|url\(|logo|brand|<form|action=)' "$SITE_ROOT"
find "$SITE_ROOT" -maxdepth 4 -type f \
  \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \
     -o -iname '*.svg' -o -iname '*.webp' -o -iname '*.gif' \) -print
file -- "$SITE_ROOT/assets/brand-mark.png"
sha256sum -- "$SITE_ROOT/assets/brand-mark.png"
```

**2. 示例判读先停在模板引用。** 首页模板中的 `<img>` 指向 `/assets/brand-mark.png`，文件格式与扩展名一致，受控查看的图像显示“Example Portal”。这支持该文件是此模板引用的标识；首页标题或正文中的“信息受理”只能先记录为页面声明，不能直接证明实际经营主体或所有后台业务。

**3. 核对图片实际如何加载。** HTML 相对路径结合文档 URL、`<base>` 和模板变量解析。CSS 的 `url(...)` 结合 CSS 文件位置解析；它也可能是内嵌数据或外部地址。再套当前 Web 的 root/alias/代理规则找到文件。用已有响应或隔离副本页面确认加载结果，并检查缓存、打包文件和动态替换。

**4. 扩展名与魔数不符时保留差异。** 只有图片文件、没有页面引用或请求，仍不能认定历史上对外展示过；检材图片和业务内容不直接复制到公开页面。HTTP 200 也不能单独证明这张图曾经被展示。

首页模板引用的图片路径、文件格式和受控查看看到的标识对上；没有页面引用或请求时，不写成历史上对外展示过，页面声明不是经营主体。引用行、图片路径、`file` 和 `sha256sum` 输出一起保存，路径已按 `<base>`、`url(...)` 和当前 root/alias/代理规则解析到文件；公开页面不复制检材图片。

<span id="03-文件改名删除与版本控制"></span>

## 03 用现状、索引和提交树分清改名、复制与重写

旧文件名不见了、新文件名出现了，还不能确定是改名、复制后删除，还是另写的一份。现状、索引和某一次提交各说各的状态。

操作顺序：先分清现状、索引和提交树，再比字节和请求路径，没有客户端就解析 pack。


### 03.1 现状、索引和提交树分别说明什么

后台入口可能从 `admin.php` 改为 `panel.php`，也可能被复制、替换或重写。单看“旧文件缺失、新文件存在”只能提出候选关系，还缺版本对象和字节比较。

操作顺序：先把现状和版本对象分开，索引只说明暂存的那一状态，历史名称去读明确提交的树。

**1. 完整检查包括现状清单、版本对象、字节比较和请求变化。** 只有新旧文件名、没有字节和请求时，停在候选关系。

**2. 索引不是建仓清单。** `.git/index` 保存当前暂存路径、对象 ID 和阶段等信息，会随 `git add` 等操作改变。要找历史名称，应读一个明确提交的树；只有 index 时，结论只说明索引保存的那一状态。[Git 索引说明](https://git-scm.com/docs/git-ls-files)

现状里有哪些文件名，以及索引或某一次提交树里保存的路径和对象 ID，分开写清；只有 index、没有明确提交的树时，不把暂存路径写成历史名称，旧文件缺失、新文件存在只是候选关系。现状清单、索引记录和后来用来比较的提交一起保存。

### 03.2 实战：证明两个名称下的内容关系

`./work/site` 里有网站、`.git/` 和目标日志，还没证明现存文件和某次提交里的另一个名字是不是同一份内容。下面直接读取树和 blob，不需要 checkout。

操作顺序：先静态检查仓库，记录当前文件和索引，导出指定提交再比字节和请求。

**1. 先准备查询副本，并静态检查这个仓库。** 查询前静态检查这个仓库的配置、include、hooks 和 attributes，并在低权限隔离会话使用可信 Git。命令显式使用 `--git-dir` 时，检查也要指向那个仓库，不能只看当前终端目录中的另一套配置。“没有切换工作树”不保证所有配置都不会调用外部程序。[Git首轮识别](/knowledge/git-docker-03/) 配置会调用外部程序时，先停下，换可信 Git 和隔离会话。

**2. 第一步：记录当前文件和索引。**

```bash
find ./work/site -maxdepth 1 -type f -printf '%f\n' | sort
git --git-dir=./work/site/.git --work-tree=./work/site ls-files --stage
git --git-dir=./work/site/.git log --all --format='%H %aI %cI %s' -- admin.php panel.php
```

**3. 第二步：确认一个历史提交中保存的路径。** 将 `<commit>` 替换为上一步实际找到的提交 ID。提交不存在或路径不在那棵树里时，保留 `log` 输出，不另挑一个提交凑结果。

```bash
git --git-dir=./work/site/.git ls-tree -r '<commit>' -- admin.php panel.php
git --git-dir=./work/site/.git show '<commit>:admin.php' > ./work/admin-from-commit.php
sha256sum ./work/admin-from-commit.php ./work/site/panel.php
cmp -- ./work/admin-from-commit.php ./work/site/panel.php
```

**4. 把三项结果分开核对。** 历史提交树有 `admin.php`、没有 `panel.php`；当前根目录反过来；导出的旧文件与当前新文件在 SHA-256、逐字节比较和后台入口定义上相同。

**5. 可以报告到哪一步。** 可以报告“现存 panel.php 与该提交的 admin.php 内容一致，支持改名，或复制后删除旧文件的关系”。这还不能区分具体操作方式，也不能确定谁执行。

**6. 第三步：关联请求变化。** 若早期日志访问 `/admin.php/admin/`，后期访问 `/panel.php/admin/`，可限定切换的观察区间。请求时间是出现该路径的时间，不能直接当作文件改名的准确时刻；旧路径可能仍被扫描或被 rewrite 转发。HTTP 200 也不说明这次请求已经登录后台。

某次提交里的 `admin.php` 与现存 `panel.php` 的 SHA-256 和逐字节比较对上了；操作方式、执行人，以及改名的准确时刻仍未确定，请求路径的出现时间不能代替文件变更时间。文件名清单、`ls-files`、`log`、导出文件、`cmp` 结果和两边的请求原行一起保存；历史树、当前目录和字节比较三项分开，`--git-dir` 指向的是这份仓库。

### 03.3 无 Git 客户端时解析 packfile

没有可用的 Git 客户端，对象仍在 pack 里，路径关系还没从提交走到 blob。偏移宽度和增量对象没分开时，解出来的内容不能直接当文件。

操作顺序：固定 pack 和 idx，按扇出表定位，解开增量后再和现存文件比字节。

**1. 固定 `.git/objects/pack/` 中的 `pack-*.pack` 与 `pack-*.idx`。** 记录仓库采用 SHA-1 还是 SHA-256 对象格式。格式没确认时先不要按另一种宽度去读偏移。

**2. 根据 idx v2 的扇出表、对象 ID、CRC 和偏移表定位对象。** 大偏移还有单独的 64 位表，不能把所有偏移都当成 32 位。

**3. 解析 pack 对象头与压缩内容。** 完整对象有 `commit`、`tree`、`blob`、`tag`；`OFS_DELTA` 和 `REF_DELTA` 需要先找到基对象再应用差分。基对象找不到时，停在这个对象，不把残缺差分当成文件内容。

**4. 从提交到树再到 blob 建立路径关系。** 孤立 blob 只含内容，不保存自身文件名。重建后验证对象 ID、长度和引用关系，再与现存文件逐字节比较。

**5. 别的版本库不能套用这套对象解释。** 同样的“版本内容与现状比对”可用于 `.svn/pristine/`、`.hg/store` 和编辑器本地历史。它们的格式和时间语义不同，不能套用 Git 的对象解释。

pack 里对象的 ID、类型、路径关系，以及和现存文件的逐字节比较对上；孤立 blob 没有文件名，增量基对象缺失时内容尚未恢复，对象格式是 SHA-1 还是 SHA-256 先记下。偏移按 idx v2 读取，64 位大偏移没有被当成 32 位。`pack-*.pack`、`pack-*.idx`、对象 ID 和比较结果一起保存。

<span id="04-访问日志与活动时间线"></span>

## 04 先确认日志格式与轮转范围，再按线索筛请求

日志文件已经找到，每列是什么、轮转包没包全、某条请求能不能当成后台操作，都还没分开。先读格式，再谈时间和入口。

操作顺序：先确认字段和轮转范围，再按线索找要继续验证的材料，最后筛候选后台入口。


### 04.1 读取格式与轮转范围

还没确认每列是什么，就按默认 combined 去筛，会把状态码和路径读错列。真正字段由站点自己的格式指令决定。

操作顺序：先确认每列是什么，连轮转和压缩文件一起读，200 只说明返回了这个状态。

**1. 先确认每列是什么，再筛选请求。** 常见 combined 为 `IP - - [时间] "方法 URI 协议" 状态码 字节数 "Referer" "User-Agent"`；真正字段由 Nginx `log_format`、Apache `LogFormat` 和站点日志指令决定。找到实际日志后，一起读当前、轮转和压缩文件。error_log 的默认位置、可证事项和轮转枚举见 04.4。格式对不上时，先改匹配条件，不把没命中写成没有访问。

**2. Nginx 还要查记录被关掉或改道的情况。** Nginx 还要查 `access_log off`、条件日志和最终处理的 location。关闭记录、筛选条件和内部跳转都可能让请求写入别处或不被记录。URI、Referer、User-Agent 按配置的转义方式读；原行保留，解码/归一化内容另列。关键词没有命中，不等于这段时间没有访问。

```bash
head -n 5 "$EVIDENCE_ROOT/var/log/nginx/media.access.log"
grep -nE '/(admin|panel|manage)[^ ]*| 404 ' \
  "$EVIDENCE_ROOT/var/log/nginx/media.access.log"
zgrep -nE '/(admin|panel|manage)[^ ]*' \
  "$EVIDENCE_ROOT/var/log/nginx/media.access.log.2.gz"
```

**3. 示例行先按原行保存。** 一条记录含 `[12/May/2026:09:14:20 +0800] "GET /panel.php/admin/index HTTP/1.1" 200`。记录偏移或行号、完整原行、时区、状态码与周边请求。`200` 说明服务器返回该状态，不保证页面内容确实是后台或用户已登录；需结合响应大小、会话与业务日志。压缩文件打不开或列对不上时，保留这条诊断。

实际 `log_format` 或 `LogFormat` 确认了，当前、轮转、压缩日志里的原行按确认后的字段读；`access_log off`、条件日志或内部跳转还没排除时，关键词没命中不等于没有访问。格式指令、日志原行、行号、时区和轮转压缩文件的范围一起保存；`200` 不写成已经登录后台。

### 04.2 可关联的行为与限制

日志里已经有路径变化、大量 404 或重复 IP，这些还只是线索。源地址和 UA 也可能是代理或伪造的。

操作顺序：先按观察提出线索，再用版本、会话或其他检材验证，找不到默认日志就按配置另找。

**1. 对照观察和还要验证的材料。** 进一步验证那一列还空着时，不把线索写成已经发生的操作：

| 观察 | 可提出的线索 | 进一步验证 |
| --- | --- | --- |
| 后台路径随时间变化 | 入口或路由发生调整 | 版本内容、配置、文件时间与应用日志 |
| 大量 404、固定 UA、短时间密集请求 | 扫描或自动化访问候选 | 请求顺序、目标范围、速率与成功响应 |
| 某 IP、UA 多次出现 | 同一网络来源或客户端特征候选 | 反向代理日志、账户、会话与其他检材 |
| 日志与 mtime 不一致 | 不同事件时间或时钟、复制差异 | 时间字段含义、时区、恢复和仿真记录 |

**2. 源地址和默认文件名都有限制。** 源 IP 可能是代理、网关或共享出口；UA 可伪造。Nginx 的 [日志模块](https://nginx.org/en/docs/http/ngx_http_log_module.html)也支持动态路径或其他日志目标。未找到默认 `access.log` 不能直接认定没有请求记录。先按配置找实际路径，再决定是没有记录还是找错了文件。

某条观察对应的线索，以及已经拿来验证的版本、会话或其他检材，写在同一行；只有 IP 或 UA、没有代理日志和会话时，不写成同一个人，没有默认 `access.log` 也不写成没有请求。相关日志原行和用来验证的配置、文件时间或会话记录一起保存。

### 04.3 实战：从请求筛选候选后台入口

已确认的站点访问日志、路由或 rewrite 配置、登录处理代码和应用会话记录都在。目标是筛选后台候选并验证请求含义，而不是从 `admin`、`login` 字符串直接给出后台地址。

操作顺序：在已核对的格式上筛请求，按状态码语义读重定向，再用登录日志验证身份。

**1. 位置与命令：在本节已核对的 combined 格式上筛选请求。** 保留原行与上下文；自定义日志格式应调整匹配条件。格式不同却仍用这条正则时，先停，改条件后再筛。

```bash
rg -n -C 2 '"(GET|POST) [^ ]*(admin|login|panel|manage)[^ ]* HTTP/[^"]+" (200|301|302) ' \
  "$EVIDENCE_ROOT/var/log/nginx/media.access.log"
rg -n 'rewrite|return 30[12]|location|admin|login|panel|manage' \
  "$EVIDENCE_ROOT/etc/nginx/sites-available/site"
```

**2. 判读状态码，不把路径词当成登录成功。** 按 [HTTP 状态码语义](https://www.rfc-editor.org/rfc/rfc9110.html#name-status-codes)，`200` 表示请求按方法语义成功响应，但后台候选也可能返回登录页、通用首页或应用错误文案；`301`、`302` 是重定向，目标可能是 HTTPS、规范域名、登录页或其他入口。状态码与路径词不能证明用户登录或取得管理权限。

**3. 候选地址找到后继续做三件事。** 将原请求与实际路由、响应正文对应；重定向核对 `Location` 和后续请求。历史日志没有响应头时，记为跳转目标未确认。用应用登录日志、账户、会话和后台操作记录判断身份；副本页面测试只说明当前恢复逻辑。将扫描旧路径、rewrite 后路径及外部代理状态分开记，避免把它们当作同一次后台操作。

**4. 自定义入口可能没有这些关键词。** 自定义入口可能没有 `admin` 等关键词。继续检查 CMS 版本、入口定义和文件到 URL 的映射，[PHP后台入口追踪](/knowledge/forensic-website-reconstruction/#061-php后台入口从url映射到认证代码)保留完整认证定位，不在本节复制绕密方法。没有会话记录时，停在候选地址。

候选请求的原行、状态码，以及它和路由或 `Location` 的对应记清；没有响应头时跳转目标未确认，没有登录日志和会话时，不写成已经取得管理权限。带上下文的日志行、rewrite 命中和核对身份用的会话记录一起保存；`200`、`301`、`302` 按语义解释，扫描、rewrite 和代理状态分开记。

### 04.4 error_log 与轮转的读取位置

访问日志筛完了，服务端的启动失败、reload 拒绝和上游错误还散在 error_log 里；日志文件缺了一段，也可能是轮转而不是没人访问。先把 error_log 的实际路径和轮转配置读出来，再解释缺口。

操作顺序：先按包含关系找 error_log 的实际路径，读 logrotate 配置和状态，缺口按轮转范围解释。

**1. error_log 的路径按配置找，不猜默认值。** Nginx 的 `error_log` 可定义在 http、server、location 各级，按 01.2 的包含关系找到实际生效的那一条；Debian 系默认 `/var/log/nginx/error.log`。Apache 用 `ErrorLog` 指令，Debian 系默认 `/var/log/apache2/error.log`，虚拟主机里另有定义时以虚拟主机为准。找不到指令时记为未配置，不把默认路径当成必然存在。

```bash
rg -n 'error_log|ErrorLog' \
  "$EVIDENCE_ROOT/etc/nginx" "$EVIDENCE_ROOT/etc/apache2"
ls -l "$EVIDENCE_ROOT/var/log/nginx/"*error* \
  "$EVIDENCE_ROOT/var/log/apache2/"*error*
head -n 5 "$EVIDENCE_ROOT/var/log/nginx/error.log"
```

**2. error_log 能证明什么、不能证明什么。** Nginx 错误行形如 `2026/05/12 09:14:20 [error] 1234#5678: *90 ...`，按级别（debug…emerg）记录启动与 reload 失败、配置测试报错、上游连接失败、FastCGI 错误和客户端证书问题；它不记录正常请求，也不能单独证明某次攻击成功。目标时段没有错误行时，先查日志级别和轮转范围，不写成没有发生过错误。

**3. 轮转范围按 logrotate 配置和状态文件核。** 读全局 `/etc/logrotate.conf` 和各服务的 `/etc/logrotate.d/` 条目，确认周期、保留份数、压缩和 postrotate 重开日志的动作；`/var/lib/logrotate/status` 记录每个文件上次轮转时间。当前目录里缺中间编号时，先对状态文件和配置，不把缺口直接写成日志被清理。

```bash
cat "$EVIDENCE_ROOT/etc/logrotate.conf"
ls "$EVIDENCE_ROOT/etc/logrotate.d/"
cat "$EVIDENCE_ROOT/etc/logrotate.d/nginx"
head -n 5 "$EVIDENCE_ROOT/var/lib/logrotate/status"
```

error_log 的实际路径和级别确认后，启动、reload、上游失败各自的记录范围分开写；轮转配置和状态文件没读时，不把日志缺失写成没有发生过。error_log 原行、logrotate 配置和状态文件位置一起保存。

<span id="05-应用暴露面与结果整理"></span>

## 05 清点暴露文件，再按最小证据整理结论

程序目录里的入口、备份、表单和邮件调用都还在，还不能写成它们曾经通过 HTTP 可访问，或邮件已经送达。先清点检材里的文件，再分别追落盘和发送结果。

操作顺序：静态清点已有文件，追表单落盘和邮件调用，需要跑起来时转到网站重构。


### 05.1 静态枚举已有文件

已确认的程序根目录里，后台入口、上传目录、安装脚本和备份还没列成清单。发现文件不等于它曾通过 HTTP 可访问。

操作顺序：在程序根目录里列出入口、备份和仓库残留，再单独说明有没有请求证明它被访问过。

**1. 在已确认的程序根目录内检查这些材料。** 检查后台入口变体、上传目录、安装脚本、SQL/ZIP/BAK 备份、`.git/` 残留及 rewrite 暴露的路由。这里只清点检材中的部署材料。目录里没有这些名字时，记下搜索范围，不写成网站没有后台。

```bash
find "$EVIDENCE_ROOT/var/www/html/media-site" -maxdepth 2 -type f \
  \( -iname '*admin*' -o -iname '*manage*' -o -iname '*install*' \
     -o -iname '*.sql' -o -iname '*.zip' -o -iname '*.bak' \) -print
ls -ld "$EVIDENCE_ROOT/var/www/html/media-site/.git"
```

**2. 文件在，只说明部署材料在。** 发现文件不等于它曾通过 HTTP 可访问。要说明被访问过，回到访问日志和路由。

程序根目录里实际存在的入口变体、备份、安装脚本和 `.git/` 残留列成清单；没有对应请求时，不写成这些文件曾通过 HTTP 可访问。`find` 和 `ls` 的输出一起保存，路径来自已确认的程序根，并和 rewrite 暴露的路由分开登记。

### 05.2 实战：从 PHP 表单追到文件落盘

一个通用受理网站包含表单模板、`process-request.php`、记录目录和访问日志，需要判断输入哪些字段、是否保存过提交。文件名与字段名都是泛化示例，历史文件可能根本不在。

操作顺序：从表单字段对到脚本读取，沿变量找到写入目标，四项材料分开写。

**1. 静态读取 PHP，不执行检材代码。** 从表单的 `method`、`action`、input 的 `name` 与脚本中的输入读取逐项对应，再沿变量赋值寻找写入目标。变量对不上文件时，停在代码里的路径，不执行脚本去生成一条新记录。

```bash
SITE_ROOT="$EVIDENCE_ROOT/var/www/html/portal-site"
rg -n -g '*.html' -g '*.php' '<form|method=|action=|name=|fetch\(|FormData' "$SITE_ROOT"
rg -n -o '\$_POST|\$_SERVER|HTTP_USER_AGENT|date_default_timezone_set|chdir|__DIR__|fopen|fwrite|fclose|file_put_contents|FILE_APPEND|require|include' \
  "$SITE_ROOT/process-request.php"
find "$SITE_ROOT" -maxdepth 4 -type f -path '*/records/*' -print
```

**2. 按示例追一条提交。** 模板 POST 到 `/process-request.php`，脚本读 `ticket_ref`、`topic`、`message`，组合后写入 `records/requests.log`。继续看 `$recordPath` 如何赋值，找到实际文件。

**3. 看打开模式和返回值。** `fopen($recordPath, 'a')` 与 `fwrite` 是追加而非覆盖。接着检查返回值和错误分支，再看落地文件是否有对应记录；代码存在并不证明写入完成。[fopen 模式](https://www.php.net/manual/en/function.fopen.php)、[fwrite 返回值](https://www.php.net/manual/en/function.fwrite.php)

**4. 确定相对路径的起点。** 结合入口脚本、`chdir`、include/require、`__DIR__` 拼接和服务启动信息，查当时进程工作目录。不能直接把相对路径接到被 include 文件所在目录。[PHP 本地文件路径](https://www.php.net/manual/en/wrappers.file.php)

**5. 找到实体后分开核对。** 保存格式、大小、哈希、行号或偏移，将业务标识与请求、数据库及应用日志对应。普通访问日志通常没有 POST 请求体，POST 加 `200` 仍不能说明提交的具体值。

**6. 四项材料分开写结论。** 表单声明了什么、代码读了什么、文件保存了什么、历史请求实际提交了什么。字段可能禁用、被 JavaScript 改写、缺失或伪造，不能由读取代码推定全部值都已收集。

**7. 请求头和时区各说明各的。** `HTTP_USER_AGENT` 是可伪造的客户端请求头，不是实际操作系统或 GPS；位置要另找输入、调用和保存记录。[User-Agent 语义](https://www.rfc-editor.org/rfc/rfc9110.html#name-user-agent)

`date_default_timezone_set('Asia/Shanghai')` 只设置脚本日期函数默认时区，不证明客户端位置或服务器时钟准确。[PHP 默认时区函数](https://www.php.net/manual/en/function.date-default-timezone-set.php) 找不到历史文件时，记为落盘未确认，再查删除、采集遗漏和其他保存分支。

表单字段、脚本读取的变量、`$recordPath` 指向的文件和文件里的实际记录分开对上；找不到历史文件时记为落盘未确认，POST 加 `200` 仍没有请求体，不能写出提交的具体值。表单和脚本的命中行、落地文件的哈希和偏移一起保存；检材 PHP 没有执行。

### 05.3 实战：区分邮件配置、调用与发送结果

受理脚本引用 PHPMailer 或其他邮件组件，包含邮件配置、发送分支、应用日志和可能的 SMTP/队列记录。数据最后有没有送出，还不能从代码里的 `send()` 直接写成送达。

操作顺序：先检索调用和字段名，按表逐项对外部记录，没有结果记录就停在配置和逻辑存在。

**1. 检索只输出调用或字段名称。** 避免把硬编码口令带入共享终端记录；在受控视图中核对完整赋值、条件分支和外部配置来源。不使用检材中的账户连接真实邮件服务。

```bash
rg -l 'PHPMailer|isSMTP|SMTPAuth|SMTPSecure|addAddress|send\(' \
  "$EVIDENCE_ROOT/var/www/html/portal-site"
rg -n -o 'PHPMailer|isSMTP|Host|Port|SMTPAuth|SMTPSecure|Username|Password|setFrom|addAddress|Subject|Body|send|ErrorInfo' \
  "$EVIDENCE_ROOT/var/www/html/portal-site/process-request.php"
```

**2. 按位置或调用分别判读，再找交叉验证。** 交叉验证还没有时，这一行只说明代码或配置里有这项：

| 位置或调用 | 判读 | 交叉验证 |
| --- | --- | --- |
| `isSMTP`、`Host`、`Port`、`SMTPSecure` | 拟使用的传输、服务器与加密设置 | 外部配置、启动环境与 SMTP 连接记录 |
| `SMTPAuth`、`Username`、`Password` | 认证设置与凭据来源 | 只登记受控证据位置；口令可能是专用授权码，不能默认有效 |
| `setFrom`、`addAddress` | 发件与收件配置 | 分别记录，认证账户、From 和 To 不必相同 |
| `Subject`、`Body` | 邮件中拟包含的数据 | 沿变量追到表单、落地记录或数据库，确认是否属于发送分支 |
| `send()`、异常或 `ErrorInfo` | 调用与错误处理逻辑 | 历史应用日志、SMTP 响应、队列 ID、退信与收件副本 |

**3. 示例判读停在程序具有发送路径。** 代码把受理记录加入邮件正文并调用 `send()`，可以说明程序具有该数据发送路径。只有找到对应时段的实际执行与结果记录，才进一步描述尝试、服务器接受、排队或送达；代码里存在调用，或配置里存在口令，都不足以证明发送成功。

**4. 邮件是否送达，按结果逐层核对。** 用业务标识、时间、收件配置对应 Message-ID/队列 ID，再分别查应用返回、SMTP 接受、排队、退信和收件副本。没有后续材料时，只说明邮件配置和发送逻辑存在，不写成已经送达。

**5. 页面恢复时把出口接走。** 【仅在副本/仿真/授权环境执行】页面恢复时把邮件出口接到本地测试接收器，或关闭发送并登记差异。公开结果不展示原始口令、授权码和业务正文。

邮件调用链上的传输、认证、收件和 `send()` 逐项判读，已找到的执行或队列记录写上；没有 SMTP 响应、队列 ID、退信或收件副本时，不写成已经送达，口令存在也不证明当时有效。字段名命中和受控视图里的赋值位置一起保存，公开结果不含口令和正文。

### 05.4 隔离重构的独立入口

未修改的配置、代码和日志还在本页。需要把网站跑起来时，认证和回滚不在这里再写一套。

操作顺序：本页先保存未改材料，要跑网站时带上路径和字段去网站重构，成功提示不等于已经有会话。

**1. 本页先保存未修改的配置、代码和日志。** 需要把网站跑起来时，使用[网站重构](/knowledge/forensic-website-reconstruction/)的技术栈恢复、认证、验收和回滚步骤，并把本页查到的路径、表字段及日志带入实验。

**2. PHP 后台的改法只留在网站重构。** PHP后台定位和参数核对可读[PHP 篇的后台定位与口令重算](/knowledge/forensic-website-reconstruction/#062-旧式摘要复算函数名实际参数和字节链)；副本账号与认证分支的处理只在[PHP 篇的登录排查](/knowledge/forensic-website-reconstruction/#065-php网站后台密码绕过四种方法与副本复现)保留。这里不复制第二套正文，也不把成功提示或跳转当成已有认证会话。改配置、改口令或写数据库之前，停在那一节要求的副本上，并记下回滚办法。

本页已保存的配置、代码、日志路径和要带去重构实验的表字段记清；成功提示或跳转不能当成已有认证会话，四种改法不在本页重复。未修改配置、代码和日志的路径与哈希一起保存，仿真里的新变化单独记。

### 05.5 一条结论的最小证据

一条“入口改过、日志里出现了新路径”的结论，还缺虚拟主机、字节摘要和时间范围里的哪几项，读者就无法复查。先把最小证据凑齐再写这句话。

操作顺序：留住虚拟主机、根目录、摘要和日志原行，操作方式和执行人未核对就写明，库和容器另去对应页。

**1. 保留这些材料再写结论。** 保留虚拟主机与包含关系、程序根目录、目标文件或字段、字节摘要、提交/索引来源、日志原行和时间范围。例如：“配置引用某站点根目录；历史提交的旧入口内容与当前新入口一致；日志显示新路径从某个观察时刻起出现；现有证据支持入口内容沿用与访问路径切换，操作方式和执行人仍待核对。”

**2. 库和容器不在本页展开。** 数据库字段与统计继续见数据库取证，宿主机和容器归属统一见[Docker 与 LXC 的现场识别](/knowledge/docker-evidence-01/)。缺了摘要或原行时，不把例子里的那句话写成已经完成的结论。

虚拟主机、程序根目录、目标文件或字段、字节摘要、提交或索引来源、日志原行和时间范围凑齐，结论里的每一句都能回到其中一项；操作方式和执行人仍待核对，数据库统计和容器归属不在本页另写。包含关系、摘要、来源提交和日志原行一起保存。

<span id="06-实战java-服务配置代码位置与依赖证据"></span>

## 06 实战：定位 Java 服务的配置、依赖与代码

两份磁盘导出、Nginx、JAR 和数据库都在，哪份材料是哪台主机、哪份配置在目标时段生效，还没分开。本节只静态读取，运行和恢复转到网站重构。

操作顺序：先判两份材料的角色，不运行 JAR 定位配置，再按启动条件和依赖回到代码。


### 06.1 两份镜像先判角色，再找应用

已有两个磁盘文件系统导出、服务定义、Nginx 配置、一个 JAR、数据库和容器元数据，需要解释业务部署以及关键代码的位置。同名 `data` 目录还可能被当成第二台主机。

操作顺序：先比 UUID、主机名和连接方向，再写清代理端口，最后找被启动命令引用的 JAR。

**1. 本节只静态读取材料。** 运行与恢复统一进入网站重构。

**2. 先判断两份材料是否来自不同服务环境。** 分别记录分区和文件系统 UUID、`/etc/fstab`、主机名、`machine-id`、网卡配置、服务及采集时间，再查网站连接是否指向另一份材料中的数据库实例、卷和日志。

**3. 两个 Linux 根目录不要直接算成两台主机。** 两个 Linux 根目录可能来自两台主机，也可能是复制盘、快照或容器根目录。只有网站目录的数据盘，应按挂载关系处理；不能直接算成第二台主机，同名 `data` 也不代表盘中只有业务数据。

**4. 把代理方向写清楚。** 读取同一个 `server/location` 的 `listen` 与 `proxy_pass`。例如 `listen 18080`、`proxy_pass http://127.0.0.1:18082`，是客户端连入口 18080，再由 Nginx 转给 Java 后端 18082，不是反过来。接着找后端启动定义、进程或两端日志，确认这个地址确实对应目标 Java 服务；配置里出现端口还不说明请求已成功。HTTP 200 同样不能代替这次对应。

```bash
find "$EVIDENCE_ROOT/opt" "$EVIDENCE_ROOT/www" -type f \
  \( -name '*.jar' -o -name '*.war' -o -name 'application*.yml' \
     -o -name 'application*.yaml' -o -name 'application*.properties' \) -print
rg -n 'ExecStart|WorkingDirectory|EnvironmentFile|java|spring\.profiles|spring\.config' \
  "$EVIDENCE_ROOT/etc/systemd/system"
```

**5. 运行时目录和业务 JAR 分开记。** 不存在的搜索目录按实际材料调整。`java-1.8` 等运行时目录与业务 JAR 是不同对象；不能一概排除其中所有文件，也不能因目录名而认定应用版本。记录真正被启动命令引用的 JAR、工作目录、JVM 参数、服务用户和外部配置，再与历史命令和启动日志核对。对不上启动命令时，JAR 只记为候选文件。

两份材料的 UUID、主机名和 `machine-id` 对过分，`listen 18080` 转到 `proxy_pass http://127.0.0.1:18082` 的方向写清；配置里有端口但没有进程或两端日志时，不写成请求已经成功，同名 `data` 不单独证明第二台主机。身份字段、Nginx 的这一对指令、`find` 和单元检索输出一起保存。

### 06.2 不运行 JAR，也能定位包内配置

Spring Boot 常见可执行 JAR 的应用类与资源在 `BOOT-INF/classes/`，依赖在 `BOOT-INF/lib/`；WAR 及普通 JAR 布局可能不同。还没核对 manifest 和实有成员，就不能选定一份配置导出。

操作顺序：先枚举归档成员，只读一份大小已检查的 manifest，导出后回到原包核对哈希。

**1. 先核对 manifest 与实有成员。** 结构依据可查看[可执行包布局](https://docs.spring.io/spring-boot/specification/executable-jar/nested-jars.html)。以下只枚举归档，并读取单个已检查大小的 manifest，不解包、不执行应用。成员缺失或重复时，脚本会停，先逐个看再继续。

```bash
python3 - ./work/app.jar <<'PY'
from pathlib import PurePosixPath
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    candidates = []
    for item in archive.infolist():
        name = item.filename
        base = PurePosixPath(name).name
        if name == 'META-INF/MANIFEST.MF' or (
            base.startswith('application') and base.endswith(('.yml', '.yaml', '.properties'))
        ):
            candidates.append(item)
            print(f'{name}\tbytes={item.file_size}\tcompressed={item.compress_size}')
    manifests = [item for item in candidates if item.filename == 'META-INF/MANIFEST.MF']
    if len(manifests) != 1:
        raise SystemExit('manifest missing or duplicate: inspect archive before continuing')
    manifest = manifests[0]
    if manifest.file_size > 1024 * 1024:
        raise SystemExit('manifest too large for this inspection')
    print(archive.read(manifest).decode('utf-8', errors='replace'))
PY
```

**2. 导出前先核对归档成员。** 同名重复成员、异常大小或缺失配置，先停下自动选择，逐个确定完整成员路径。配置导出后保存归档哈希、成员路径、未压缩大小和导出文件哈希，再回到原归档核对。

**3. 入口类名不是运行证明。** `Main-Class`、`Start-Class` 和依赖名能帮助识别入口与框架，不能证明代码在目标时段运行过。只有编译包时称“部署包/字节码材料”，不称完整源码。多份同名配置分别登记，不让导出目录里的覆盖结果抹掉原包结构。

归档里的 manifest、候选配置成员和未压缩大小核对过，`BOOT-INF/classes/`、`BOOT-INF/lib/` 布局确认了；`Main-Class` 和 `Start-Class` 不能证明目标时段运行过，重复成员没逐个确定时不自动选一份。成员清单、manifest 文本、归档哈希和导出哈希一起保存，没有执行 JAR。

### 06.3 生效配置要连到启动条件

同一个字段在包内、外部文件和启动参数里可能各有一个值。找到第一份 `application.yml` 还不能当作目标时段采用的值。

操作顺序：列出全部来源，按这一版的优先级和启动日志选择，端口、库和 APP 名称分开回答。

**1. 同一个字段可能有多个值，按启动条件选生效来源。** 列出包内、外部配置和活动 profile 文件。对照环境变量、JVM 系统属性和应用参数。每个待查字段登记来源、值、适用 profile、覆盖条件和缺失材料。按包中 Spring Boot 版本的优先级和启动日志判断实际采用哪一项。[外部配置机制](https://docs.spring.io/spring-boot/reference/features/external-config.html) 缺了环境或外部文件时，先登记缺失，不把包内值称为历史生效值。

**2. 不要找到首个 `application.yml` 就结束。** 包内默认值、外部 profile 和参数不同，可能只是正常覆盖；旧版本的 YAML/profile 语法按旧实现解释。

**3. 按要回答的问题继续验证。**

| 要回答的问题 | 候选字段或位置 | 继续验证 |
| --- | --- | --- |
| 启用哪个业务配置 | `spring.profiles.active`、`application-<profile>.*`、环境和参数 | 启动日志、外部覆盖文件及配置导入；文件存在不等于活动 |
| Java服务端口是多少 | `server.port`、`server.address`、context-path | 监听/PID与Nginx上游对应；入口端口另列 |
| 连接哪一数据库 | JDBC URL、用户、数据源代码与环境 | 主机/容器、实际实例、库名、驱动、权限与连接日志 |
| 代码由谁启动 | manifest、启动脚本、systemd单元 | 程序路径、用户、工作目录和版本，不只看history |
| 参数来自哪里 | `EnvironmentFile`、`-D...`、`--...`、外部文件 | 原始输入、版本规则和查询时点；含凭据的材料限制展示 |

**4. JDBC 和口令按驱动与材料范围解释。** JDBC URL 中的参数与库名要按相应驱动规则解析，不能全字符串当数据库名。配置声明的口令也可能已失效；导出范围缺环境或外部配置时，结论应为“包内候选值”，不强称历史生效值。

**5. 查 APP 名称与配置文件名时，分开回答。** 先打开已确认生效的配置，再核对页面、业务常量和移动端接口。例如业务配置中的 `app.name` 可保存 APP 名称。APP 显示名称、包名/应用 ID、`spring.application.name` 不一定是同一个值。框架的服务注册名不能直接当作用户看到的 APP 名称。

**6. 在已经导出的配置、页面和反编译文本中定位候选。** 命中后读完整字段及其使用位置，不把搜索结果第一行直接填入结论。

```bash
rg -n -i 'spring[._-]?application|app[._-]?(name|id)|applicationName|packageName|<title|APP名称|应用名称' \
  ./work/java-config ./work/web-files ./work/decompiled
```

**7. 配置文件名要记下四件事。** 配置文件名同时记下“文件名、原 JAR 成员路径、对应 profile、加载依据”；导出时改的名字不是原配置文件名。

每个字段的来源、值、profile 登记清楚，`app.name` 和 `spring.application.name` 是不是同一个值分开了；没有启动日志或外部文件时只写“包内候选值”，文件存在不等于这个 profile 当时活动。来源清单、命中字段的上下文和原 JAR 成员路径一起保存。

### 06.4 服务发现、消息、缓存和对象存储分别查

Consul、RabbitMQ、Redis 和对象存储可能同时出现在配置里，地址、端口和密钥还没按各自的用途分开。history 里出现名称，也不证明那个组件启动成功。

操作顺序：先按依赖收集配置和数据目录，端口从应用连接读，证件照和 AccessKeyID 只处理已核对的那一行。

**1. 按依赖对照可保全的证据和边界。** 某一格的日志或数据目录还没有时，结论停在应用引用了这个地址：

| 依赖 | 可保全的证据 | 常见考点与边界 |
| --- | --- | --- |
| Consul等服务发现 | 应用引用、agent启动参数、配置、数据目录、服务注册与日志 | 工具名称/地址/节点与业务角色；history出现名称不证明启动成功 |
| RabbitMQ等消息代理 | 实例配置、环境、节点名、数据目录、队列/连接记录和日志 | 协议监听与管理端口分开；队列消息存在不等于业务处理完成 |
| Redis | 应用连接、逻辑库、键构造代码、RDB/AOF及日志 | 缓存/验证码/会话用途、过期策略；当前空键不证明历史不存在 |
| OSS/对象存储 | endpoint、bucket、对象键/URL、SDK配置、访问与对象记录 | AccessKeyID是配置标识，密钥与调用结果另证；云仓库未采集不等于无附件 |

**2. 按依赖逐个检查。** Consul：分别读 `bind_addr`、`client_addr`、`advertise_addr`，核对节点通信、客户端入口和对外声明地址，保留完整上下文。[agent配置](https://developer.hashicorp.com/consul/docs/reference/agent/configuration-file) 三个地址不一致时分别留下，不合成一个地址。

**3. 消息代理端口从应用连接配置读。** 在活动 profile 中核对 `rabbitmq.host`、`port`、`virtual-host`，再与 RabbitMQ 实例监听、容器发布端口和连接日志对应。常见 AMQP 端口为 5672、AMQPS 为 5671；管理网页常见 15672，但都能修改，不能把管理网页端口当消息连接端口。`virtual-host` 是 RabbitMQ 内部的逻辑空间，不是网页路径；配置为 `/` 也不代表连接的是网站根目录。

**4. RabbitMQ 的节点名要和数据目录一起看。** RabbitMQ：将节点名、主机名和数据目录对应。改主机名后生成的新状态，不是原消息实例已恢复。[文件与目录](https://www.rabbitmq.com/docs/relocate)

**5. Redis 按配置收集持久化文件。** Redis：按配置收集全部 RDB/AOF；多文件 AOF 连同 manifest 保全。持久化关闭或短期键过期时，记下不能恢复的范围。[持久化](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) 当前空键不证明历史不存在。

**6. 不在原证据库里写验证码。** 【仅在副本/仿真/授权环境执行】不为让网站登录，在原证据库写验证码或重写持久化文件。要写实验键时只写副本，并标明它不是历史验证码。

**7. 身份证照存到哪里，AccessKeyID 末几位怎样取。** 在已确认的配置里找 `endpoint`、`bucket`、`oss.accessKeyId` / `accessKeyId` 和对象路径；再沿上传身份证照的接口找实际使用的配置对象。其他业务的 OSS 配置不能因为同在一个文件中就合并使用。

**8. 标识和秘密值不是同一字段。** `AccessKeyID` 是访问身份标识，`accessKeySecret` / `AccessKeySecret` 是对应秘密值，两者不是同一字段。题目要求末 8 位时，先在受控记录保留完整原值、字段名和位置，再截取 ID 的末 8 个字符；不要截 Secret、不要把遮挡星号当真实字符。下面仅处理分析目录中人工核对后保存的一行 ID，不访问对象存储。脚本拒绝遮挡值或整个配置文件时，先回到原始字段，不改输入凑出 8 个字符。

```bash
python3 - ./work/access-key-id.txt <<'PY'
from pathlib import Path
import sys

rows = Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()
if len(rows) != 1 or len(rows[0]) < 8 or not rows[0].isascii():
    raise SystemExit('需核对一行完整AccessKeyID；不要输入遮挡值或整个配置文件')
if '*' in rows[0] or rows[0] != rows[0].strip():
    raise SystemExit('发现遮挡或首尾空白，先核对原始字段')
print(rows[0][-8:])
PY
```

**9. 输出只说明这个已确认 ID 的后缀。** 不证明该密钥仍有效，也不证明证件照已成功上传。上传用途由调用代码、对象键/URL 和已有日志核对；云端附件未取得时记录缺口，不用检材凭据连接真实 OSS 补材料。

每个依赖的地址、端口或数据目录，以及已确认的 `endpoint`、`bucket` 和 AccessKeyID 后缀对上；管理端口不是消息端口，`virtual-host` 为 `/` 不是网站根，云端对象没采集到就记缺口，密钥后缀不证明仍然有效或上传成功。各依赖的配置和日志位置、受控保存的完整 ID 和脚本输出一起保存，没有连接真实对象存储。

### 06.5 从题目要求回到具体代码与业务

待查的是定时任务、验证码或某笔业务在哪个类里，关键词命中还停在注释或另一个同名 class 上。反编译文本也还不是服务器上正在跑的目录。

操作顺序：从业务路由读到方法，记录包名、类名和成员路径，定时任务和验证码按调用链收束。

**1. 从待查业务找到具体方法。** 先找业务路由，再读控制器、服务方法及其数据库/外部接口调用。命中 `@Scheduled`、任务调度、验证码比较、消息生产/消费或云上传 SDK 初始化后，继续找调用者和条件，不能停在关键词。

**2. 反编译文本只是阅读表示。** 记录原包、类成员路径、类摘要、工具版本及方法名，再与字节码或源码核对。

**3. 示例判读先写成可复核的部署关系。** 包内配置指向异机数据库，启动定义引用业务 profile，容器元数据记录对应数据卷；这支持一组可复核的部署关系。若认证方法取 Redis 中的短期键，再调用远端验证码接口，说明离线登录存在这两项依赖；【仅在副本/仿真/授权环境执行】写入一个实验键只能验证副本路径，不是恢复历史验证码，更不能证明当时成功登录。

**4. 输出字段至少含这些项。** 输出字段至少含 `镜像/主机角色、Web入口和后端、包/类/成员路径、配置来源、活动条件、依赖对象、时间基准、证据位置与缺失项`。后台绑定手机、额度档位、渠道数量、完成订单、还款和服务费需要继续核对表结构、状态定义、精度与统计范围；字段名或页面标签不能替代业务 SQL 与金额复核。

**5. 找“定时任务在哪个 class”和“验证码在哪个 class”，按这条顺序做。** 保留 JAR 哈希和成员清单，用可信反编译工具在分析目录生成阅读文本，不启动业务 JAR。搜索业务词和调度/认证调用，再读命中方法的前后逻辑。记录完整包名、类名、方法名和原归档成员路径。多个目录有同名 class 时，不能只写文件名就结束。回到对应字节码或已有源码复核，保存工具版本和定位结果。

```bash
# 路径是可信工具输出的反编译文本，不是运行中的服务器目录
rg -n 'Scheduled|EnableScheduling|TimerTask|ScheduledExecutorService|scheduleAtFixedRate|TaskScheduler|定时任务' \
  ./work/decompiled
rg -n -i '验证码|captcha|verifyCode|verificationCode|ADMIN-PHONE|opsForValue|redisTemplate|equals' \
  ./work/decompiled
```

**6. 定时任务还要看谁注册了它。** 找到周期执行方法后，继续查谁注册/启动它、周期从哪里取、哪些配置条件允许执行。先核对带 `@Scheduled` 的业务类与它调用的 service 方法；任务类不一定是启动类。`@Scheduled` 是一种常见写法，不是所有 Java 任务都这样实现；Spring 还要有相应调度启用配置和实际创建的 bean。只找到 class 或注解，先写“包含任务定义”，任务是否运行由启动/调度日志与业务变化证明。

**7. 验证码从登录请求往下追。** 从登录请求读入的手机号/账号和验证码出发，依次追到 Redis 逻辑库、键构造、取值、空值/过期处理、比较和成功后的会话/删除动作。比如路由 `/admin/index/` 命中某控制器，只能先定位该入口，再读调用方法。发送验证码与比对验证码可能在不同类中；配置里有短信地址也不能代替找到比对代码。记录真正执行比较的方法及它的调用路径。对不上调用路径时，不把第一个命中的类写成验证码比较的位置。

业务方法的包名、类名、方法名、原归档成员路径和调用路径记清；只有 `@Scheduled` 或 `/admin/index/` 时，先写“包含定义”或“先定位入口”，任务是否运行、验证码是否比对成功还要日志和调用链。JAR 哈希、反编译文本位置、工具版本和输出字段清单一起保存，实验键只出现在副本路径的记录里。

