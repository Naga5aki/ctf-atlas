拿到的是面板目录、网站文件，或一份服务器文件系统导出。面板页面能打开，还不表示网站、数据库和某次上传已经对上。

**确认三个入口 → 找到面板库和虚拟主机 → 核对加密字段 → 把站点、库和上传记成一条 → 要打开网站时去网站重构 → 工具结果对回原表 → 再按现场核对上传、空列表或绑定提示。**

启停服务、改配置和改认证，只在已经做好快照、并且限制外联的副本上做。原始材料保持只读。

<span id="01-先识别面板与实际服务"></span>

## 01 确认面板、网站和数据库各自的入口

面板页面能打开，网站却打不开，或者打开的是另一套服务。

**先把三个入口分开 → 记下各自的版本和端口 → 再把面板里的站点对到正在监听的进程。**

**1. 先把三个入口分开记。**

面板用来管理，网站由 Web 服务提供，业务数据由数据库服务提供。分别写下它们的程序版本、配置路径、端口和数据目录，再把面板里的站点记录对到 vhost、程序文件和正在监听的进程。

**2. 端口只用来找到入口。**

宝塔旧版常见端口 8888，新版可能用别的端口。端口和错误页只帮助找到入口，产品类型还要看实际程序。

**3. 离线材料和活体记录分开保存。**

离线镜像先读文件和配置。活体采集另外记下操作的起止时间、终端输出，以及这次新产生的记录。

【仅在副本/仿真/授权环境执行】启停服务或开机恢复会产生新日志、缓存和时间记录。这些单独保存，不要混进目标服务器原来的历史。

面板能打开，但 vhost 或正在监听的进程对不上时，分开写，不要合成一条服务。版本、配置路径、端口，以及这次新产生的日志单独保存。

<span id="02-宝塔常见数据落点"></span>

## 02 找到面板库、站点目录和日志

面板目录在，但还不知道站点、账号和日志落在哪一个文件里。先按路径对上，再打开库。

**列出面板数据文件 → 确认是哪一份库 → 查表结构 → 再对虚拟主机。**

**1. 先按这张表对路径。** 版本不同，主库可能不在同一位置。常见主库是 `/www/server/panel/data/default.db`，新版也可能在 `data/db/default.db`、`database.db` 或 `panel.db`。网站目录多在 `/www/wwwroot/`，日志多在 `/www/wwwlogs/`，虚拟主机在 `/www/server/panel/vhost/`。这些只是候选。文件不在就记缺失，不要改成别的目录名。完整路径表在下面。

<details>
<summary>展开面板路径表</summary>

| 路径 | 内容 | 复核方法 |
| --- | --- | --- |
| `/www/server/panel/` | 面板程序、版本、配置与任务 | 与服务启动配置、进程路径核对 |
| `/www/server/panel/data/default.db` 或 `data/db/default.db` | 旧版/新版面板主库 | 先查 schema，再查站点、FTP、数据库与任务记录 |
| `/www/server/panel/data/db/database.db` | 部分新版数据库账户与连接 | 区分本机与远端数据库，记录主机字段 |
| `/www/server/panel/data/db/panel.db` | 部分新版面板配置、数据库管理信息 | 字段含义和加密格式按版本确认 |
| `/www/server/panel/data/userInfo.json` | 面板账号绑定信息 | 账号绑定不等于每次操作的操作者 |
| `/www/server/panel/data/port.pl`、`admin_path.pl` | 端口与安全入口候选配置 | 文件存在时读取；不假设跨版本固定 |
| `/www/server/panel/data/limitip.conf`、`config/basic_auth.json` | 访问限制及认证配置 | 保存状态和字段，哈希不能称为可逆加密 |
| `/www/wwwroot/` | 常见网站目录 | 以 vhost 的 root/document_root 为准 |
| `/www/wwwlogs/` | 常见网站访问/错误日志 | 与具体站点、域名、日志格式对应 |
| `/www/backup/`、`/www/backup/database/` | 备份与历史数据库 | 记录备份时间及包含范围 |
| `/www/server/panel/vhost/` | Nginx/Apache/重写配置 | 连接域名、网站目录、PHP 版本与数据库 |

</details>

**2. 在工作副本里列出库、绑定文件和虚拟主机。** 下面路径是示例，`./work` 换成这次已经复制出来的面板材料。`sqlite3 -readonly` 只读打开，不改库。

<details>
<summary>展开只读列出库、绑定文件和虚拟主机</summary>

```bash
find ./work/www/server/panel/data -maxdepth 3 -type f \
  \( -name '*.db' -o -name 'userInfo.json' -o -name 'port.pl' \)
sqlite3 -readonly ./work/default.db '.tables'
sqlite3 -readonly ./work/default.db '.schema'
rg -n 'server_name|root |DocumentRoot|access_log|error_log' ./work/www/server/panel/vhost/
```

</details>

**3. 看这三步输出，再决定查哪张表。**

1. `find` 列出深度 3 以内的库、`userInfo.json` 和 `port.pl`。同名文件按版本、目录和备份日期分开保存，不覆盖。
2. `.tables` 是表名，`.schema` 是字段。看到表名之后才选字段，不要凭文件名猜账号在哪一张表。
3. `rg` 在虚拟主机里找站点名、网站目录和日志指令。`/www/wwwroot/` 只是常见目录，仍以 vhost 里的 root 或 DocumentRoot 为准。

同时有 WAL/SHM 时，先制作一致查询副本，再查。不要删掉 WAL 来让主库“干净”。[SQLite 与 WAL](/knowledge/forensic-sqlite/)

表里有库名、但这块盘上没有数据文件时，记成缺口，不要另建空库。`.schema` 里的字段要和接下来查的站点、账号、任务是同一张表。同名库各自留哈希，查询副本不要覆盖原始库。

<span id="03-加密字段的定位与验证"></span>

## 03 核对加密字段属于哪一版实现

表里看到 `BT-0x:` 开头的字段。先留完整密文，再按这一版程序找解密条件。

**留下完整密文 → 追到实际解密函数 → 核对密钥和 IV → 把结果放回原来那一行。**

**1. 先留下完整密文。** 不只删掉 `BT-0x:` 前缀。同一前缀也可能是不同构建，不能只按名字选算法。

**2. 按这个顺序找解密条件。**

1. 确认面板版本及具体字段。
2. 追面板 Python 调用，到 `PluginLoader.so` 的 `db_decrypt` 等实际实现。
3. 找密钥材料、IV，以及 `data/div.pl` 或数据库里的 div。
4. 【仅在副本/仿真/授权环境执行】在隔离分析环境按实际实现逐层处理，保存每层输入、参数和输出。

**3. 已有版本线索仍要与代码对应。** 某些历史分支从程序常量隔位取字符，得到 AES 密钥 `3P+_lN3+jPW6Kgt#`；也见过默认 IV 为 `4HpOz4pT^4Hh-Lfl` 的分支。先确认样本采用这条实现，再使用这些值，不能当通用密钥。

div 自身还可能经过 `_aes_decrypt_module` 与 `_get_sgin_key` 的另一层处理。缺常量或 IV 时记录缺项，不猜值；每层保留输入、输出和算法参数。

**4. 怎样检查是否解对。** 将结果放回原表行，看字段应是口令、地址还是其他配置，再核对账号、连接地址和相邻记录的格式。

只得到可打印字符串还不算成功。乱码或格式不符时回查构建、密钥、IV 和处理层次；保留原密文和中间结果，不拿解出的口令去连接材料中记载的真实远程服务器。

缺常量、IV，或 div 还有另一层处理时，记缺项，不猜值。解出的内容要能放回原行，并对上账号、地址或相邻记录的格式。原密文和每一层输入留着。这些值只属于已经对上的那一版。

<span id="04-网站数据库与上传行为"></span>

## 04 把站点目录、数据库和上传对到同一条

面板里有一条站点，还要确认网站目录、数据库和上传是不是同一套。离线不执行镜像中的程序。

**读完整虚拟主机 → 读应用里的库和上传目录 → 固定这三份材料 → 再用日志把一次上传对上。**

**1. 从 vhost 确认这一条站点。** 看域名、端口、根目录、入口文件、重写规则和 PHP 或运行时版本。Nginx 从 include 找完整 server，Apache 从 Include 找完整 VirtualHost，再确认根目录、运行时和日志。

**2. 从应用配置确认数据库和上传目录。** 记下数据库类型、地址、库名、字符集、表前缀和上传目录。

**3. 固定网站目录、数据库与相关日志。** 活体数据库要采用相应一致性备份，直接复制运行中的数据目录可能不完整。

**4. 把一次上传或登录对上。** 检查后台账户、登录记录、上传目录、可疑脚本和计划任务，并用访问日志、数据库记录、文件时间与哈希关联。

**5. 扫描结果只用来缩小范围。** D_safe 等扫描结果用于缩小候选范围，继续人工检查脚本调用、文件内容和对应请求，不能以扫描标签代替行为证据。

完整诊断分别保留在[Nginx配置检查](/knowledge/fic-case-04/#012-nginx-配置体系与包含关系)、[Apache虚拟主机检查](/knowledge/fic-case-04/#015-实战从-apache-配置定位站点)。需要后台、表单或部署恢复时再进入[Web应用取证](/knowledge/fic-case-04/)、[网站重构](/knowledge/forensic-website-reconstruction/)；容器卷和导出范围按[Docker与容器证据](/knowledge/docker-evidence-01/)核对，不在这里复制命令体系。

运行中的库如果只复制了数据目录、没有一致备份，写成可能不完整。访问日志、数据库记录和文件哈希要能对上同一次上传或登录。完整 vhost、应用配置、网站目录和日志各自留哈希。

<span id="05-网站重构的独立入口"></span>

## 05 要打开网站时转到网站重构

面板里的版本、库记录、配置和日志已经保全，下一步是把网站在副本里打开。

**面板材料留在本页 → 打开网站时进入网站重构 → 副本页面和历史状态分开记。**

宝塔、网站三要素、数据盘映射、运行时与数据库匹配、仿真认证及验收回滚，集中进入[网站重构](/knowledge/forensic-website-reconstruction/)。本页不重复那一套启动和改配置的步骤。

本页留下的是面板版本、库记录、vhost 和日志范围。挂载数据盘、启动 PHP 或 Java、改后台登录，改到网站重构里做。副本上新打开的页面单独记，不写进原来的历史。

<span id="06-工具与结果表"></span>

## 06 把工具导出对回原来的表

辅助工具能导出一份表，还要把每一行对回原来的库。

**登记工具和库哈希 → 看实际 schema → 逐行对回原表 → 空结果先分原因。**

**1. 先登记工具和输入。** [PanelForensics 与综合辅助工具](/tool/forensic-assist-tools/) 可辅助读取宝塔、1Panel 和小皮面板，但支持版本有限。先登记工具版本和输入库哈希。

**2. 导出之后逐行对回原表。** 查看实际 schema，再将导出的账号、站点、任务逐行对回原表。空列表、空字段或解析报错时，检查原表是无记录、材料缺失，还是版本不支持；不要采用工具填出的默认值作为事实。

**3. 结果表至少留下这些列。** `面板/服务版本、站点域名、目录、数据库位置、账户ID、日志路径、任务定义、时间基准、恢复方式`。公网服务需要继续查反向代理和 CDN 日志；代理转发头仅在可信代理配置成立时用于确定客户端地址。

导出的每一行都要能在原表里找到同一主键。空列表先分清是无记录、材料缺失，还是这一版工具不支持。导出字段要和 `.schema` 里的列一致，不要用工具填出来的默认值。工具版本、输入库哈希和导出文件留下来。

<span id="07-实战串联站点配置上传记录与落地文件"></span>

## 07 核对上传记录有没有落到磁盘

一份服务器文件系统导出里有面板数据库、vhost、网站目录和访问日志。要核对的是某次上传有没有真正落到磁盘，不是访问日志里有没有一行成功。

**读完整 vhost → 对上站点 ID → 查上传目录和请求 → 再看文件是否在磁盘上。**

**1. 离线分析只读这些材料。** 要仿真时，换另一份隔离副本。不要在唯一导出上改站点或补文件。

站点、请求和文件哈希还没对到同一条之前，不要把访问日志里的一行成功写成文件已经落在磁盘上。仿真要另做，就换一份隔离副本。

<details>
<summary>展开确认实际站点与路径</summary>

### 07.1 确认实际站点与路径

vhost、面板库和网站目录都在，但还不知道这次上传对应哪一个站、哪一个目录。列表里的路径和磁盘上的目录可能不是同一个。

**从 vhost 抽出这一站 → 用库里的 ID 对上 → 再在上传目录里核对文件。**

**1. 从 vhost 提取这一条站点。** 看 server_name、监听、root、重写和日志位置，并记下所有 include。面板列表里的路径要和最终配置、采集到的目录对上。

**2. 用数据库 schema 确认关联。** 确认站点 ID、账户 ID、数据库地址和任务关联。本机数据库和远端数据库分开标。

**3. 从网站配置确认上传目录。** 看命名规则和关联表，再查目标期间的请求、业务返回和数据库记录。HTTP 成功状态不能单独说明应用已经把文件写进去。

**4. 在目标上传路径核对文件。** 看格式、大小、哈希和时间，再对上用户或会话、记录 ID 和访问日志。

这一站的 server_name、root、站点 ID 和上传目录是同一条配置。include 没读全，或列表路径和磁盘目录不一致时，先写明差异，不选其中一个当成事实。请求、记录 ID 和文件哈希能放在一起。只有 HTTP 成功状态还不够。保存完整 vhost、相关表的主键和字段、上传路径上的文件清单。

</details>

<details>
<summary>展开示例判读与验证</summary>

### 07.2 示例判读与验证

访问日志返回 200，数据库里登记了文件 ID，上传目录里却没有这个文件。

**先分开写三项 → 再查应用日志和备份 → 判断是没写入、后来删除，还是采集时就没有。**

**1. 三项分开写。** 先说明请求和登记都在，再查应用日志、文件系统和备份，判断是写入失败、后来被删，还是采集时就没拿到。

**2. 可疑脚本只静态看。** 追调用和请求，不要执行它来重演历史。HTTP 状态和一个文件 ID 还不能证明上传已经完成。

**3. 要打开页面时换副本。** 按网站重构记录仿真里改了什么。当前副本能显示，不能说明历史上的站点也是这个状态。

这次请求、数据库里的文件 ID，以及磁盘上有或没有的那个文件。目录里没有文件时，写明是写入失败、后来删除，还是采集范围里本来就没有。访问日志、记录 ID 和文件哈希是同一次上传。只有 HTTP 200 还不够。保存vhost、相关表行、上传路径的清单。仿真里新产生的页面单独记。

</details>

<span id="08-面板-cli-功能识别与状态保全"></span>

## 08 找到面板命令并保全主库

找到面板目录或 `bt` 命令，还不说明面板当时在运行，也不说明某次菜单被执行过。先保全入口和库，再看菜单会改什么。

**先定位入口但不运行 → 再按当前构建核对菜单 → 登录失败时把每一层认证分开。**

旧示例里 `14` 是查看默认信息，`5` 是改面板密码，`23` 是关闭 BasicAuth，`24` 是关闭动态口令。这些只作线索。菜单以副本里当前脚本的文字为准，不按编号去点。

<details>
<summary>展开找到入口不等于确认运行或历史操作</summary>

### 08.1 找到入口不等于确认运行或历史操作

磁盘上有面板目录，或者仿真控制台里能找到 `bt`。这只说明入口可能在这里，还不能说明它当时在跑，也不能说明历史操作。

**先在材料里定位目录 → 仿真里只查命令位置 → 菜单按当前文字判断，不按编号去点。**

**1. 离线先看目录、版本和启动材料。** 已授权的仿真控制台可以用 `command -v bt` 查命令在哪。没有输出，继续查 PATH、权限和采集范围。有输出，仍要看它是脚本、别名、残留，还是另一个构建。不要执行未知的镜像脚本，也不要用“bt 没报错”说明面板正常。

```bash
# 以下在分析机读取已保全的材料；先确认文件实体与软链边界
PANEL_ROOT=/mnt/evidence/www/server/panel
ls -ld "$PANEL_ROOT" "$PANEL_ROOT/data" "$PANEL_ROOT/vhost"
find "$PANEL_ROOT/data" -maxdepth 3 -type f \
  \( -name '*.db' -o -name '*Info.json' -o -name 'port.pl' \
     -o -name 'admin_path.pl' -o -name 'limitip.conf' \) -print
rg -n 'server/panel|ExecStart|Environment' /mnt/evidence/etc/systemd/system \
  /mnt/evidence/usr/lib/systemd/system

# 以下只在已授权的仿真副本控制台定位入口，不运行它
command -v bt
```

**2. 看菜单之前先保存基线。** 保存入口路径、哈希、版本、配置和快照。核对来源之后只在副本里使用。菜单功能按当前构建的文字判断，不按编号盲选。

已有官方示例里，`14` 是查看默认信息，`5` 是改面板密码，`23` 是关闭 BasicAuth，`24` 是关闭动态口令。这些只作核对线索。旧版和定制分支可能不同。具体菜单仍以副本里当前脚本为准，说明见 [宝塔面板命令行工具使用指南](https://docs.bt.cn/getting-started/bt-command-line-tool)。

| 菜单功能 | 分析时的处理 | 需要保留的状态 |
| --- | --- | --- |
| 查看访问地址、用户名、错误日志等 | 确认该分支只读后使用；敏感输出保存在受控目录 | 地址、端口、安全入口、版本、输出时间与日志范围 |
| 修改用户名、密码或数据库凭据 | 属于状态变更；先用离线解析和已知凭据，必要的仿真改动另做快照 | 认证材料、账户标识及变更前后差异 |
| 关闭 BasicAuth/动态口令、清除访问限制或入口 | 属于认证/访问策略变更，不是检查状态 | 原认证层、域名/IP/设备限制、原安全入口 |
| 重启、重载、修复、更新、清缓存/日志/垃圾 | 会改变进程、文件或时间线；不作为保全第一步 | 启动配置、运行态、日志、缓存、文件版本与哈希 |

**3. 登录失败时逐层分开查。** 面板口令、BasicAuth、动态口令、安全入口、IP 或域名限制不是同一项。找到账号或入口，并不代表其他检查也通过。默认信息也可能已经不是当前有效凭据。

面板可达时，保存响应、跳转和实际认证结果。离线只描述配置。CLI 产生的新日志单独列出。仿真里关掉认证之后的登录，不能证明历史账号具有权限。

`/www/server/panel/` 的实体、入口哈希，以及 `command -v bt` 有没有输出。菜单编号对不上这一版时，按当前脚本的文字核对，不套 `14`、`5`、`23`、`24`。没有运行证据时，不写成面板当时正常。入口是脚本、别名还是残留，已经分开。会改口令或访问策略的菜单没有被当成检查状态。保存目录列举、入口哈希、版本。仿真里的新日志单独存放。

</details>

<details>
<summary>展开用 schema 读取面板主库和绑定信息</summary>

### 08.2 用 schema 读取面板主库和绑定信息

**查询主库前先留一份不变备份。** `default.db` 是 SQLite 候选，不能用 `cat` 或字符串命中代替表查询。主库与同批 `-wal/-shm` 一起保存，再另建一致查询快照。WAL 的保全与读取条件见[SQLite 与 WAL](/knowledge/forensic-sqlite/)。

版本或日期不同的同名文件分开保存。不要删除 WAL、checkpoint 或改日志模式来修唯一材料；这些操作会改变可以解释的库状态。

下例假定已经取得 `/work/panel-query/snapshot.db`，它来自另一个查询工作副本；所有输出写到分析目录。使用可信分析机上的 SQLite 工具，不执行面板代码：

```bash
PANEL_DB=/work/panel-query/snapshot.db
PANEL_OUT=/work/output/panel
mkdir -p "$PANEL_OUT"
sha256sum "$PANEL_DB" > "$PANEL_OUT/query-database.sha256"
sqlite3 -readonly "$PANEL_DB" 'PRAGMA integrity_check;' > "$PANEL_OUT/integrity.txt"
sqlite3 -readonly "$PANEL_DB" '.tables' > "$PANEL_OUT/tables.txt"
sqlite3 -readonly "$PANEL_DB" '.schema' > "$PANEL_OUT/schema.sql"
sqlite3 -readonly -header -csv "$PANEL_DB" \
  "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;" \
  > "$PANEL_OUT/schema-index.csv"
```

**读查询结果的顺序：** 先看 `.tables` 和 `.schema`，确定实际表、字段，再查站点、账号、任务、操作及备份的主键、路径和原始时间。不同 password 字段未必都是面板登录密码。

完整性检查通过，只说明结构检查通过，不证明内容真实或操作成功。`-readonly` 限制数据库写入；WAL 还受版本和旁文件条件影响，查询工作区可能产生旁文件，原材料保持另存。[SQLite 命令行](https://www.sqlite.org/cli.html)、[WAL 只读条件](https://www.sqlite.org/wal.html#read_only_databases)

**绑定信息这样读：** 在面板目录中找全部 `userInfo.json`，核对文件实体、格式、构建和实际读取代码，再分别记录手机号、账号 ID、令牌及状态。不要固定认定它只在一个路径，也不要登录真实绑定账号验证。

文件中的手机号只能先说明保存的账号关联，不能直接确定每次操作者、绑定时间或当前有效性。继续用目标时段配置、会话和操作日志核对；展示结果时脱敏。

```bash
find "$PANEL_ROOT" -type f -name 'userInfo.json' -print
# 找到并确认实际实体后，保存哈希并作为 JSON 静态解析
sha256sum "$PANEL_ROOT/data/userInfo.json"
python3 -m json.tool "$PANEL_ROOT/data/userInfo.json" > "$PANEL_OUT/userInfo-formatted.json"
```

最后两行仅用于实际文件确认在 `data/` 的情况；路径不同按查到的实体替换，文件不存在/JSON 无效保存诊断，不制造补齐文件。格式化输出只是阅读副本，原始字节与哈希保留。

先确认入口脚本的路径和哈希、主库的表结构，以及 `userInfo.json` 里实际读到的字段。菜单编号对不上这一版，或 JSON 不在 `data/` 时，按查到的实体写，不补文件。`.schema` 之后才选的表和字段，能对上要查的站点或账号。CLI 没报错，不表示面板当时在运行。保存入口哈希、查询库哈希、schema 和格式化前的原始 JSON。

</details>

<span id="09-实战面板列表为空时追查网站与备份痕迹"></span>

## 09 列表为空时从库和备份找回站点

仿真里站点列表是空的，手头有旧面板程序、主库、少量面板日志、vhost、网站数据目录和备份目录。日志只覆盖很短一段时间。要判断这个网站是否曾经由面板管理过、有没有留下备份。界面空白不能解释成网站或源码不存在。

**先核对是不是同一份库 → 按 schema 找备份记录 → 对路径 → 只读看归档 → 恢复另建工作区。**

**1. 先保存版本和哈希。** 先保存面板和查询工具的版本、库文件和旁边 WAL/SHM 的哈希、日志文件的真实路径、首末时间，以及快照标识。检查页面连的是不是同一份库、列表字段是否符合当前程序、数据卷是否采集完整。不要靠升级或清缓存把差异消掉。

<details>
<summary>展开空列表时的库记录、路径和归档核对</summary>

**2. 按 schema 找记录。** 按一致查询快照的 schema 找站点、任务、备份和操作记录。如果看到压缩或备份命令、路径，保存表名、主键、完整字段和原始时间。不要把“命令被记录下来”写成“压缩已经成功”。

**3. 对是不是同一个路径。** 在 vhost、任务配置、shell 或面板历史、备份清单里核对是不是同一个目录或归档路径。日志里的清理命令也只是操作候选。日志少，可能是轮转、采集缺失、当时没开日志，或文件被删。要有别的证据，才能说清理真的执行了、范围有多大。

**4. 只读确认归档。** 只读确认候选归档在不在、格式、大小和哈希是否合理，清单里的路径是否对得上站点配置、需要的代码或数据。缺了什么、哪里互相矛盾，都留下来。不要执行命令记录里的脚本，也不要直接解包到原来的网站目录。

**5. 要跑起来就换工作区。** 用另一份独立快照或备份记录核对站点 ID、域名、目录和时间。要从归档恢复或把页面跑起来时，另建恢复工作区。取证结论仍看保全材料。恢复成功只说明这个副本可以拿来分析。

主库里有一条把 `/www/wwwroot/site-a` 打包的操作文本，界面上没有这个站点，备份归档里却有同路径的代码。可以说明“库里有打包线索，并且找到了内容对得上的归档”。界面为什么是空的、这份归档是不是那条命令打出来的、历史上一共有几个站点、最后一次运行是什么时候，还要另查。不能用这三项一次推定。

最后按 `面板构建 / 库与表主键 / 操作文本 / 原始时间基准 / vhost与目录 / 归档路径、格式及哈希 / 内容对应 / 日志覆盖与缺口` 逐项填写。

界面显示、库记录、文件存在、操作成功、网站是否在跑，分开写结果。日志缺了，就写已经查过哪些文件、哪段时间，只说这段里没有发现，不要扩大成全部历史都没有。

</details>

库里的打包文字、vhost 里的目录、归档里的代码，要分别对上。命令被记下来，还不等于压缩已经成功。界面为什么是空的、归档是不是那条命令打出来的、一共有几个站点，没对上之前分开写。面板版本、库主键、操作文本、原始时间、归档哈希和日志覆盖时段留下来。

## 10 宝塔绕过绑定手机号：离线仿真实战

面板程序、数据库、vhost 和网站已经备份。Linux 副本不出网，登录之后却出现宝塔账号或手机号绑定提示。要处理的是这个本地提示和相关列表报错，不是把整站恢复说成已经完成。

**先看拦截在前端、跳转还是云列表 → 只在副本上改已经对上的那一处 → 面板提示消失不等于网站后台已经恢复。**

**1. 下面只处理本地提示和相关列表报错。** 面板登录、BasicAuth、动态口令、网站验证码仍各自检查。原始绑定信息从未改过的材料里读取。构造账号不用于认定历史操作者。网站重构另处理网站怎么跑起来。不要把面板提示绕过当成整站恢复。

还没分清是弹窗、`/bind` 跳转还是软件列表报错时，先不要改文件。面板提示消失，也不写成网站业务已经恢复。历史操作者仍以未改过的材料为准。

先按现象选一条，不必把后面的方法全做一遍：

- 首页是 200，页面加载后才盖住绑定弹窗：查 `BTPanel/static/js/index.js` 里的 `bind_user` 和 `show_force_bind()`。
- 登录后仍是 302，并且 `Location` 指向 `/bind`：查 `BTPanel/__init__.py` 和 `class/public.py` 的 `is_bind()`。
- 页面能开，软件列表却是“获取插件列表失败”或 `KeyError`：查 `class/panelPlugin.py` 的 `get_cloud_list()`。
- 文件、函数或字段和下面的例子不同：按当前构建重定位，不套旧行号。

<details>
<summary>展开先辨别拦截位置，保存文件基线</summary>

### 10.1 先辨别拦截位置，保存文件基线

登录后的页面有绑定提示，但还不知道是 JS 弹窗、服务端转到 `/bind`，还是软件列表自己失败。方法选错会改到不该动的文件。

**先在浏览器里看状态码和 Location → 再按表选一节 → 改之前把七个候选文件的基线留下。**

| 实际现象 | 优先核对的代码或状态 | 选择的操作 |
| --- | --- | --- |
| 首页响应为 200，页面加载后覆盖绑定弹窗 | `BTPanel/static/js/index.js` 中的 `bind_user` 与 `show_force_bind()` | 10.2：只调整前端提示条件 |
| 已登录后仍收到 302，`Location` 指向 `/bind` | `BTPanel/__init__.py` 的路由与请求前置检查，`class/public.py` 的 `is_bind()` | 先查实际生效的文件/账号判断，再选 10.3 或 10.4 |
| 页面能打开，软件商店请求却返回“获取插件列表失败”或 `KeyError` | `class/panelPlugin.py` 的 `get_cloud_list()`、返回值与字段消费位置 | 10.5：处理已经定位的离线云列表分支 |
| 文件、函数或字段与示例不同 | 当前构建的路由、模板、打包 JS 和调用链 | 重新定位；不按旧文章行号套用 |

**1. 打开开发者工具的 Network，重新访问登录后的首页、`/files` 和软件列表。** 保存状态码、Location 和错误正文。200 的页面加载之后才弹窗，优先查 JS。302 到 `/bind`，先查服务端。列表请求单独失败，追云列表。隐藏弹窗不会改变服务端跳转。`/files` 也不是免登录入口。

**2. 备份和修改只在已经核对过的仿真副本上做。** 【仅在副本/仿真/授权环境执行】下面的备份、修改和重启，针对已经核对 `/www` 挂载和面板版本的仿真副本。分析原件时只读相应路径，不执行面板代码。先把实际文件位置和软链目标对应起来。待修改的文件和它的父目录都要留在这个副本的面板树里。

```bash
export PANEL="${PANEL:-/www/server/panel}"
export SAVE="${SAVE:-/root/panel-bind-$(date +%Y%m%d-%H%M%S)}"
umask 077
mkdir -p "$SAVE/original"
test ! -e "$SAVE/present.list" && test ! -e "$SAVE/absent.list" || exit 1
: > "$SAVE/present.list"
: > "$SAVE/absent.list"
: > "$SAVE/before.sha256"
names=(
  BTPanel/static/js/index.js BTPanel/__init__.py
  class/public.py class/panelPlugin.py
  data/bind.pl data/userInfo.json data/initBind.pl
)
for rel in "${names[@]}"; do
  test ! -L "$PANEL/$rel" || exit 1
  if test -f "$PANEL/$rel"; then
    mkdir -p "$SAVE/original/$(dirname "$rel")"
    cp -a -- "$PANEL/$rel" "$SAVE/original/$rel" || exit 1
    printf '%s\n' "$rel" >> "$SAVE/present.list"
    (cd "$PANEL" && sha256sum -- "$rel") >> "$SAVE/before.sha256" || exit 1
  elif test ! -e "$PANEL/$rel"; then
    printf '%s\n' "$rel" >> "$SAVE/absent.list"
  else
    printf 'Unexpected file type: %s\n' "$rel" >&2
    exit 1
  fi
done
printf 'Baseline saved: %s\n' "$SAVE"
```

`present.list` 记录原来存在的文件，`absent.list` 记录原来缺失的文件。恢复时两种状态都要还原。已有的 `userInfo.json` 往往包含账号和令牌线索。它的原始字节保存在受控备份目录里，不要打印到公开操作记录中。

**3. 搜索之后打开函数和调用者，不要停在命中行。**

```bash
test ! -f "$PANEL/data/version.pl" || cat "$PANEL/data/version.pl"
rg -n 'bind_user|show_force_bind' "$PANEL/BTPanel/static/js" "$PANEL/BTPanel/templates"
rg -n 'is_bind|initBind\.pl|bind\.pl|/bind|get_user_info|userInfo\.json' \
  "$PANEL/BTPanel/__init__.py" "$PANEL/class/public.py"
rg -n 'get_cloud_list|softList|PanelError' "$PANEL/class/panelPlugin.py"
```

看命中是注释还是执行代码、判断什么值、先后调用什么函数。旧分支可能读 `bind.pl`，也可能读 `get_user_info()`。另有 `initBind.pl` 分支会在第一次检查时创建文件。因此先记录存在还是缺失，避免把启动之后生成的状态当成历史。路由装饰器不能证明这是 Django。应看导入和应用对象。已经核对的实现使用 Flask。

**4. 版本只帮助定位，不代替这次读到的函数。** 7.7.0 附近常见 `bind.pl`。7.8.0 附近出现判断变化和本地账号分支。同版本也可能有补丁或定制。实际选择方法，看 `is_bind()` 和前端条件。不要把“低于或高于 7.7.0”当成所有构建的通用分界。

拦截是首页弹窗、302 到 `/bind`，还是软件列表的 `KeyError`，以及七个候选文件哪些存在。文件、函数或字段和示例不同时，按当前构建重新定位，不按旧行号套用。下一步要看到Network 里的状态码、Location 和错误正文，与 `is_bind()` 的实际调用对得上。`present.list` 和 `absent.list` 都在。保存基线目录、`before.sha256`、搜索命中和打开过的函数。

</details>

<details>
<summary>展开方法一：绕过首页弹窗，精确修改前端条件</summary>

### 10.2 方法一：绕过首页弹窗，精确修改前端条件

已经能登录，页面加载后仍被绑定弹窗盖住。先确认这是前端条件，再改那一个比较，不要改服务端。

**先打开 `/files` 看是弹窗还是跳转 → 只在恰好命中一处时改条件 → 刷新后核对实际下载的 JS。**

**1. 先测试，再选前端方法。** 已经正常登录，并且读到 `bind_user == 'True'` 会调用 `show_force_bind()`。在同一源站打开 `/files`，例如 `https://panel.local:8888/files`。协议和端口换成实际副本的值。

文件管理能显示，再定位 JS。如果也跳到 `/bind`，就去查服务端，不要反复改前端。安全入口用于登录。`/files` 是不是在源站根路由上，仍按当前构建确认。

**2. 不要照抄行号，也不要把网页里的弯引号当成代码引号。** 下面的命令只在恰好命中一个旧式条件时写入。单引号和双引号的 ASCII 引号都可以处理。零命中或多命中会在写入前结束，原文件保留。

```bash
JS="$PANEL/BTPanel/static/js/index.js"
python3 - "$JS" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
raw = path.read_bytes()
pattern = re.compile(rb"bind_user\s*==\s*(['\"])True\1")
matches = list(pattern.finditer(raw))
if len(matches) != 1:
    raise SystemExit(f"Expected one binding condition, found {len(matches)}; file unchanged")
changed = pattern.sub(b"bind_user == 'FORENSIC_OFFLINE'", raw, count=1)
path.write_bytes(changed)
print("frontend-condition=FORENSIC_OFFLINE; replacements=1")
PY
diff -u "$SAVE/original/BTPanel/static/js/index.js" "$JS"
```

**3. 修改后分两步确认。** 原值字符串 `True` 和新的比较目标不同，原来的弹窗分支应不再触发。`diff` 显示差异时，退出码 1 是正常的“文件不同”，不是补丁失败。

再按 Ctrl+F5，或开一个无痕会话。在 Network 里核对实际下载的是修改后的 JS。仍然弹窗时，查旧缓存、压缩资源，以及另一个入口加载的 JS。只改静态 JS，通常先刷新验证。这不等于官网账号已经绑定。

`bind_user == 'True'` 只有一处，并且 diff 显示它改成了别的比较目标。`/files` 仍跳到 `/bind` 时，停止改前端。仍然弹窗时，先查缓存和另一份 JS，不写成绑定已经通过。下一步要看到脚本打印 replacements=1。Network 里下载的 JS 与磁盘文件一致。保存修改前的 JS 备份和 diff。

</details>

<details>
<summary>展开方法二：保留备份后移走 `bind.pl` 标志文件</summary>

### 10.3 方法二：保留备份后移走 `bind.pl` 标志文件

服务端如果靠 `data/bind.pl` 这个标志触发强制绑定，才用这一节。只是看到同名文件，不够。

**确认代码真的读这个标志 → 移到备份位置 → 刷新后看提示和 `/bind` 是否还在。**

**1. 先确认适用条件。** 当前实际代码使用 `data/bind.pl` 触发强制绑定或首页提示。`.pl` 后缀在这里是状态标志，不是要执行的 JavaScript，也不是 DNS/BIND 的域名管理脚本。仅发现同名文件，或注释里的引用，不足以选用此方法。

```bash
FLAG="$PANEL/data/bind.pl"
test -f "$FLAG" && test ! -L "$FLAG" || exit 1
test -f "$SAVE/original/data/bind.pl" || exit 1
test ! -e "$SAVE/bind.pl.disabled" || exit 1
mv -- "$FLAG" "$SAVE/bind.pl.disabled"
test ! -e "$FLAG" && printf 'bind.pl=absent; original=preserved\n'
```

**2. 移走之后重新访问。** 原文件移到备份位置，基线里还保留另一份原件。刷新，分别看提示和 `/bind` 重定向。

只有进程在启动时才读这个标志，才在保存当前状态之后重启面板。文件被重新生成、代码检查别的标志，或继续校验账号时，回到实际调用者查原因。不要继续删除更多文件。

`bind.pl` 是当前代码读取的标志，并且已经从 `data/bind.pl` 移到备份，原件仍在基线里。刷新后仍跳转，或文件被重新生成时，不继续删文件，回到调用者。下一步要看到命令打印 `bind.pl=absent; original=preserved`。页面上的提示和 `/bind` 分别记录。保存移走前后的路径、基线里的原件。重启如果做了，记下原因。

</details>

<details>
<summary>展开方法三：为依赖本地 `userInfo.json` 的旧分支补仿真数据</summary>

### 10.4 方法三：为依赖本地 `userInfo.json` 的旧分支补仿真数据

有的旧分支只看本地有没有一份非空 JSON 或 `uid`，并不去云端校验。只有读到这个判断，才补一份原本不存在的文件。

**先读 `is_bind()` 和 `get_user_info()` → 只在文件本来不存在时创建 → 重启后按实际报错看还缺什么。**

**1. 先确认本地 JSON 真的是判断依据。** 读 `is_bind()` 和 `get_user_info()`。确认它只检查本地非空 JSON 或 `uid`，没有真实的云端校验，再选这个实验。

例子只创建原本不存在的文件。已有内容先备份和解释，另做一次副本实验，不能覆盖历史绑定。构造的 JSON 只代表实验状态。它不证明手机号、真实账号、授权或历史绑定。

```bash
python3 - "$PANEL/data/userInfo.json" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
if path.exists() or path.is_symlink():
    raise SystemExit("userInfo.json already exists; existing file preserved")
payload = dict(id=1, uid=1, state=1, username="offline-demo", secret_key="",
               access_key="", address="", addtime=1, idc_code="", area="",
               serverid="", ukey="")
with path.open('x', encoding='utf-8') as stream:
    json.dump(payload, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print("local-binding-fixture=created; uid=1")
PY
python3 -m json.tool "$PANEL/data/userInfo.json" >/dev/null
```

**2. 字段按读取代码核对，不要把构造值当成真实账号。** 示例还包含 `id/state/secret_key/addtime/idc_code/area/ukey`，用来检查会直接访问这些键的旧实现。只依赖五个常见字段的构建，仍按自己的调用者检查。

`id/uid/state/addtime` 填 `1`，其他值为空，都是构造数据。不是确认过的账号 ID、状态、创建时间或有效密钥。JSON 键齐全，只说明格式和字段在。固定长度、签名、非空和远端校验还要逐项看。

**3. 确认这个构建什么时候重新加载 JSON，再重启。** 【仅在副本/仿真/授权环境执行】确认时机和命令入口之后，执行 `bt restart`。它会停止并重启面板，改变进程和这次日志。不要用整机重启或数据库重启代替。

重新登录后保存响应、跳转和页面。如果代码还要求非空或固定长度的 `serverid`、生成服务器标识、检查签名，或调用远程账号服务，空值可能对不上。按实际错误查。不能把“JSON 格式正确”说成绑定判断已经通过。

`is_bind()` 只看本地 JSON 或 `uid`，并且新建的 `userInfo.json` 通过了 JSON 语法检查。文件本来就存在时，脚本会停、不覆盖。还要 `serverid`、签名或远程校验时，不写成绑定已通过。输出是 `local-binding-fixture=created; uid=1`。`json.tool` 没有报格式错误。保存新建文件、`bt restart` 的时间和新日志。历史绑定文件没有被覆盖。

#### 10.4.1 另一分支：精确修改 `public.is_bind()` 的本地判断

302 已经确认来自 `public.is_bind()` 返回假。改这个函数之前，还要确认它不管口令、会话和其他认证。

**先确认只有这一处本地判断 → 只替换唯一的无参 `is_bind()` → 编译通过后再重启，并准备整文件还原。**

**1. 选修改函数之前先确认三件事。** 服务端 302 确实由 `public.is_bind()` 返回假引起。读完全部调用者，确认它只处理本地绑定提示，不承担口令、会话或其他认证。已经在同一基线里保存了 `class/public.py`。这次只试这个分支，不叠加其他方法。

这个实验可以保持 `userInfo.json` 不变。改本地判断，不会产生有效的云端账号或令牌。

**2. 不要把两处修改当成固定组合。** 有些构建在绑定检查通过之后，其他函数仍会读 `userInfo.json`。先看报错堆栈。缺文件、缺键或字段类型不对，才在另一次副本实验里补所需数据。远端账号或云接口校验失败时，填本地 JSON 不会生成有效的云端账号。关闭弹窗只说明页面继续显示。还要核对网站列表、数据库列表和文件管理的实际请求是否成功。

下面的脚本不凭固定行号，也不把整个文件里的 `return False` 全部替换。它用可信的 Python 解释器解析源码，只处理唯一的、顶层的、无参数、无装饰器的 `is_bind()` 定义。语法、定义数量或签名不匹配时，写入还没有开始。

```bash
python3 - "$PANEL/class/public.py" <<'PY'
from pathlib import Path
import ast
import io
import sys
import tokenize

path = Path(sys.argv[1])
raw = path.read_bytes()
encoding = tokenize.detect_encoding(io.BytesIO(raw).readline)[0]
text = raw.decode(encoding)
tree = ast.parse(text)
nodes = [node for node in tree.body
         if isinstance(node, ast.FunctionDef) and node.name == 'is_bind']
if len(nodes) != 1:
    raise SystemExit('Expected one top-level is_bind definition; file unchanged')
node = nodes[0]
args = node.args
if node.decorator_list or args.posonlyargs or args.args or args.kwonlyargs or args.vararg or args.kwarg:
    raise SystemExit('Unexpected is_bind signature; file unchanged')
newline = '\r\n' if '\r\n' in text else '\n'
lines = text.splitlines(keepends=True)
replacement = [line + newline for line in (
    'def is_bind():',
    '    # Offline forensic copy: local binding gate only.',
    '    return True',
)]
changed = ''.join(lines[:node.lineno - 1] + replacement + lines[node.end_lineno:])
ast.parse(changed)
path.write_bytes(changed.encode(encoding))
print('is_bind-local-gate=always-True; definitions=1')
PY
diff -u "$SAVE/original/class/public.py" "$PANEL/class/public.py"
```

**3. 语法通过之后再重启。** 【仅在副本/仿真/授权环境执行】用核对过的面板解释器执行 `-m py_compile "$PANEL/class/public.py"`。保存差异。语法通过后重启面板。编译可能生成副本缓存，也记入变更。

重新请求原先返回 302 的页面。只有本地绑定导致的跳转应消失。登录和会话仍要检查。其他页面继续跳转、云列表报错，或函数还有别的职责，就沿保存的调用者查。不要把返回 True 当成全部认证成功。还原时用整个原来的 `public.py`。不要靠新增 `return False` 去猜原来的逻辑。

唯一的顶层 `is_bind()` 被改成了本地放行，`class/public.py` 的 diff 只有这一处。定义不止一个，或签名不是无参无装饰器时，文件保持原样。其他页面仍跳转时，不把返回 True 写成认证全部成功。输出是 `is_bind-local-gate=always-True; definitions=1`。`py_compile` 通过后才重启。保存`public.py` 的 diff、编译缓存说明、重启后的请求结果。还原用整份原文件，不用 `return False` 拼回去。

</details>

<details>
<summary>展开软件列表报错：只补已定位的离线返回结构</summary>

### 10.5 软件列表报错：只补已定位的离线返回结构

本地绑定已经通过，软件商店仍可能因为连不上云而报错。先看错误是超时、账号校验，还是返回里缺 `list`。

**先保存请求和堆栈 → 只有缺字段时才补这一处 → 空列表不代表本机没有 Nginx 或网站。**

**1. 列表报错单独定位。** 先保存浏览器请求和这次日志。区分连接超时、账号校验失败、返回值不是字典，或字典缺 `list`。

下面检索 `get_cloud_list()` 和错误堆栈。只在副本里读命中的函数，再按实际错误选修改位置。

```bash
rg -n 'get_cloud_list|KeyError|PanelError|获取插件列表|Traceback' "$PANEL/logs" \
  "$PANEL/class/panelPlugin.py"
```

**2. 只有确认缺字段时才替换这一块。** 在 `panelPlugin.py` 里找 `if not 'list' in softList:`，读它下面的完整报错块和后面的使用代码。

保留所属函数、同层缩进、本地插件合并和过滤。只替换已经核对的这个错误分支。不要批量注释 `PanelError`，也不要在函数开头返回空列表。错误如果出现在前面的网络或账号校验，这里改了也不会解决。

**3. 先读后面消费字段的代码，再决定补什么。** `list` 为空表示云目录没取到。`setdefault` 不覆盖字典里已有的值。`pro`、`ltd` 缺失时补 `-1`，只适用于实际代码用负值表示未开通的构建。类型或必需键不同，按它补齐。不要把下面四行当成跨版本模板。

```python
if not isinstance(softList, dict):
    raise public.PanelError('离线列表返回类型异常，请核对实际调用链')
softList.setdefault('list', [])
softList.setdefault('pro', -1)
softList.setdefault('ltd', -1)
```

`pro=0` 在部分构建里参与永久授权判断，和手机号绑定是两件事。本例不把付费状态改成永久授权，也不覆盖已有的 `pro/ltd` 值。如果报错发生在更早的账号校验或连接阶段，替换末尾的缺字段检查不会消除那个错误。按保存的堆栈定位到真正的分支。

**4. 改完先做语法检查，再重启并复测。** 下面使用已经核对的面板虚拟环境解释器。路径不同时，用服务启动脚本里的实际解释器替换。编译检查可能写入副本的 `__pycache__`，这次变更记录一并保留。

```bash
"$PANEL/pyenv/bin/python3" -m py_compile "$PANEL/class/panelPlugin.py"
```

空列表只解释云目录。它不表示 Nginx、PHP、MySQL 未安装，也不表示网站数据库是空的。继续看本地插件合并逻辑，确认已安装项目是否应显示。网站数量用面板库、vhost 和目录核对。

本节不验收离线不可用的云安装、付费插件、证书申请或账号服务。缺什么就分别记录。

报错堆栈落在缺 `list` 的分支，并且 `setdefault` 没有覆盖已有的 `pro` 和 `ltd`。错误在更早的网络或账号校验时，不改末尾分支。空的 `list` 不写成软件未安装或网站库为空。`py_compile` 通过，复测的返回结构里 `list` 是数组，或堆栈仍然指向别的分支。保存原始堆栈、改过的分支、`__pycache__` 是否出现、复测响应。

</details>

<details>
<summary>展开国际版与新版差异的处理</summary>

### 10.6 国际版与新版差异的处理

国际版或新版的绑定方式和旧的 `index.js` 可能已经不是同一套。不要把旧文件名套到当前构建上。

**先确认这是不是另一套产品 → 再沿实际加载的资源重定位 → 三个状态文件不要当成同一个开关。**

**1. aaPanel 是另一套部署选择，不是原面板的绑定补丁。** 比较账号流程时，另建空白实验环境。原材料和主仿真副本保持原版本。

当前国际版是否要求账号，仍看具体版本。不要采用“所有版本都不绑定”这种笼统结论。

**2. 新版常把资源打包，并改变路由和字段。** 旧的 `index.js` 也可能不存在。沿实际请求加载的资源、服务端跳转和本地状态函数重新定位。`bind.pl`、`initBind.pl`、`userInfo.json` 代表不同实现里的候选状态，不能混成一个开关。

当前构建实际加载的脚本、跳转，以及它读的是哪一个状态文件。`index.js` 不存在时，不按旧路径修改。国际版没有单独实验时，不写成它一定不绑定。请求加载的资源和 `is_bind` 一类函数来自这一版代码，不是旧文章里的路径。保存实际资源路径、版本，以及空白实验和主副本没有混用的说明。

#### 10.6.1 离线更新包：只在另建的版本替换实验中使用

要比较另一个面板版本时，不能在唯一材料上直接跑更新脚本。先另建一份已经做完快照的副本。

**在分析机核对离线包 → 传到实验机并核对哈希 → 读完 `update.sh` 再决定是否执行。**

**1. 确需比较版本时另开实验。** 克隆副本，保存整机或容器快照，再使用离线包。`LinuxPanel-7.7.0.zip` 和 `LinuxPanel-8.0.0.zip` 只是已有的包名例子，不保证现在还能下载，也不保证兼容。

分析机取得核对过的官方包之后，记录位置、时间、版本、SHA-256 和成员清单。仿真机不改变原来的网络隔离，通过已有的实验链路传入。

```bash
# 分析机：包名和连接参数均替换为已核对的实验值
PKG=LinuxPanel-7.7.0.zip
sha256sum "$PKG" > "$PKG.sha256"
unzip -l "$PKG" > "$PKG.contents.txt"
scp -P 2222 "$PKG" "$PKG.sha256" analyst@panel-lab:/tmp/
```

`scp -P` 里的大写 `P` 指定 SSH 端口。实验如果用默认 22，可以省略这个选项。小写 `-p` 是另一种含义。上传成功后，在实验机核对实际文件和包哈希。归档路径、软链和落点经过审查之后，再解包到独立目录。

**2. 在另建的版本替换副本里解包，不在唯一材料上执行。**

```bash
# 另建的版本替换副本：已提前保存完整快照，不在唯一材料上执行
cd /tmp
sha256sum -c LinuxPanel-7.7.0.zip.sha256
UNPACK="$(mktemp -d /tmp/panel-update.XXXXXX)"
unzip -q LinuxPanel-7.7.0.zip -d "$UNPACK"
test -f "$UNPACK/panel/update.sh" || exit 1
sha256sum "$UNPACK/panel/update.sh"
less "$UNPACK/panel/update.sh"
```

**3. 先读 `update.sh`，再决定执行。** 核对它会覆盖哪些目录、会不会做配置或数据库迁移、运行时有什么变化、会不会启停服务，以及会不会联网下载。确认所需依赖已经离线准备好之后，在该副本执行：

```bash
(
  cd "$UNPACK/panel" || exit 1
  bash update.sh > "$SAVE/version-update.log" 2>&1
)
UPDATE_STATUS=$?
printf 'update-exit=%s\n' "$UPDATE_STATUS"
```

更新结束之后检查实际变化。括号使目录切换只影响子进程。脚本仍可能启停面板或任务、覆盖目录、迁移数据库。退出码 0 或“完成升级”，不等于提示已经消失。要复查版本、文件、登录和路由，以及站点数据库。

新库、账号和日志只属于这次实验。版本替换用完整快照回滚。10.1 的七个文件只覆盖绑定相关改动，恢复不了整个更新。

先确认包的 SHA-256、成员清单，以及 `update.sh` 里会覆盖和会启停的内容。退出码是 0 时，仍要复查绑定提示是否还在。这次更新不能靠 10.1 的七个文件回滚。`scp -P` 指定已核实的 SSH 端口；实验机上 `sha256sum -c` 校验通过，说明传输前后包内容一致。脚本在 `$UNPACK/panel` 里执行，不在唯一材料上。保存包哈希、内容清单、`update.sh` 的哈希、更新日志和实验前的完整快照。

</details>

<details>
<summary>展开验证清单与完整回滚</summary>

### 10.7 验证清单与完整回滚

绑定实验做完之后，要能证明文件确实变了、页面是否还跳，以及能不能回到修改前。脚本没报错，不能代替再打开一次页面。

**按表逐项记录 → 每次只叠加一个已核对的分支 → 回滚后核对原来的哈希和缺失状态。**

| 验证项 | 记录内容与合格判据 |
| --- | --- |
| 文件确实改变 | 基线与修改后哈希、`diff`、改动字段/条件、文件存在状态；记录重启或浏览器缓存动作 |
| 面板本地页面可用 | 新会话登录后首页和 `/files` 的实际状态、是否继续 302 到 `/bind`、弹窗是否覆盖页面 |
| 软件列表错误处理 | 软件列表请求的返回结构、`list` 是否为数组、错误堆栈是否消失；空列表单独记录 |
| 证据关联保持 | 面板库记录、vhost、网站和数据库位置与静态材料一致；仿真新增数据不解释为历史操作 |
| 回滚可复现 | 在另一份副本中还原原文件及原来缺失状态，核对原哈希，并复现修改前的本地判断或提示 |

**1. 每次实验只选择一个已经核对的分支。** 先记录结果，再考虑第二种方法。出现 404、登录失败、验证码错误或连接不到数据库时，回到对应层排查，不要继续扩大绑定补丁。

**2. 回滚前确认变量仍指向同一次实验。** 【仅在副本/仿真/授权环境执行】确认 `PANEL` 和 `SAVE` 仍指向同一次实验。先暂停面板服务，再执行下面的恢复。

原来存在的文件从备份放回。原来不存在、实验新建的 `userInfo.json/initBind.pl` 等删除。脚本只处理七个候选文件，不恢复其他数据库或网站内容。整机运行状态仍用实验前的快照。

```bash
while IFS= read -r rel; do
  test ! -L "$PANEL/$rel" || exit 1
  cp -a -- "$SAVE/original/$rel" "$PANEL/$rel" || exit 1
done < "$SAVE/present.list"
while IFS= read -r rel; do
  test ! -d "$PANEL/$rel" && test ! -L "$PANEL/$rel" || exit 1
  rm -f -- "$PANEL/$rel" || exit 1
done < "$SAVE/absent.list"
(cd "$PANEL" && sha256sum -c "$SAVE/before.sha256")
```

**3. 恢复之后再访问确认。** 先核对哈希，以及文件存在或缺失的状态，再按实际服务脚本启动。启动可能重建状态文件，启动前后都记录。

完整运行态用虚拟机或容器快照回退，并复测原来的提示或请求。留下 `基线 → 单一分支修改 → 请求与页面结果 → 文件恢复 → 启动后复测`。脚本没有报错，不能代替页面确认。

本节的示例可以在构造文件和状态分支上检查字节变化、JS 条件、JSON 格式、字段默认值、备份和恢复。真实面板的账号检查、HTTP 路由和云请求结果，由当前构建的实际访问来验证，不由合成样本代替。

修改后的哈希和 diff，以及回滚后 `sha256sum -c` 是否通过。首页或 `/files` 仍 302 到 `/bind` 时，绑定提示不能写成已经消失。空的 `list` 单独记录。`PANEL` 和 `SAVE` 指向同一次实验。原来缺失的文件在回滚后再次缺失。保存验证表的五项记录、回滚命令输出、启动前后的状态文件。

</details>

<details>
<summary>展开绕过提示后，继续导出和解释面板数据库</summary>

### 10.8 绕过提示后，继续导出和解释面板数据库

面板页面能打开之后，历史账号和站点仍要以启动前保全的库为准。不要只把正在写入的主库拷走，而漏掉 WAL。

**先从未改材料保全主库 → 仿真库用一致备份再传 → 按 schema 导出，不把三张表拼成一个 CSV。**

**1. 只需要账号、网站或数据库配置时，先直接查库。** 已经取得服务器文件系统，就从未修改的材料里保全面板 SQLite 主库和同批 WAL、SHM，在分析机另建查询副本。不必先登录面板、升级版本或绕过手机号提示。确需观察面板功能时，再另建恢复副本。历史记录仍以启动前的保全材料为准。

**2. 界面可用之后仍要查原库。** 先保留启动前的数据库。旧构建常见 `/www/server/panel/data/default.db`。其他构建可能在 `data/db/`，或拆成多个库。

找到主库和同批 WAL、SHM，读 schema，再制作一致的查询快照。不要用 `scp` 只拿走正在写入的主库而漏掉 WAL。副本里的新登录记录另列，不当成历史操作。

**3. 要查询已经启动的仿真库，先做一致备份。** 【仅在副本/仿真/授权环境执行】用可信的 SQLite 工具备份到新的输出目录，再传这份快照。下面对应已经确认旧路径的实例。启动前保全的库另存，不要覆盖。

```bash
# 仿真副本：这个目录需为本次新建的输出位置
mkdir -p /work/panel-export
test ! -e /work/panel-export/snapshot.db || exit 1
sqlite3 -readonly "$PANEL/data/default.db" '.backup /work/panel-export/snapshot.db'
sqlite3 -readonly /work/panel-export/snapshot.db 'PRAGMA integrity_check;'
sha256sum /work/panel-export/snapshot.db > /work/panel-export/snapshot.db.sha256

# 分析机：单独执行传输命令，使用已核对的实验账号与端口
scp -P 2222 analyst@panel-lab:/work/panel-export/snapshot.db \
  analyst@panel-lab:/work/panel-export/snapshot.db.sha256 ./
```

**4. 收到快照后先核对哈希。** 再在 Navicat 等工具里选择打开 SQLite 的现有数据库文件，只读浏览查询副本。不是新建一个空库之后声称导入成功。

CLI 也先确认实体、读 schema，再按对应字段查询。下面的表名只是候选，不保证所有版本相同。

| 候选表 | 常见关联字段 | 判读边界 |
| --- | --- | --- |
| `users` | `id/username/password/salt/login_ip/login_time/phone/email` | 密码/盐/邮箱可能是加密或散列字段；一次登录时间不是完整操作时间线 |
| `sites` | `id/name/path/status/index/addtime/project_type/project_config` | 域名和目录与 vhost、实际挂载及网站文件核对；状态值以当前代码为准 |
| `databases` 或 `database` | `id/name/username/password/accept/db_type/conn_config/sid` | 区分面板管理账户、本地/远程连接和业务数据库；加密字段转入第 03 节 |

下面的 SQL 只对应 schema 里确有这些表和字段的查询快照。名称不同就先改 SELECT，不改证据库的结构。例子不导出 password、salt 或令牌字段。

```sql
SELECT id, username, login_ip, login_time FROM users ORDER BY id;
SELECT id, name, path, status FROM sites ORDER BY id;
SELECT id, name, username, accept, db_type FROM databases ORDER BY id;
```

**5. 把需要的记录导出成文件。** 在分析机把上面选定的一条只读 SELECT 保存为 `/work/panel-query/selected-query.sql`，按实际 schema 核对字段。每张表单独导出。不要把三组不同的列拼成一个没有说明的 CSV。

```bash
# 分析机：目录已准备好；SQL文件只含人工确认的一条SELECT
QUERY=/work/panel-query/selected-query.sql
CSV=/work/output/panel/selected-query.csv
test -s "$QUERY" && test ! -e "$CSV" || exit 1
sqlite3 -bail -readonly -header -csv /work/panel-query/snapshot.db < "$QUERY" > "$CSV"
EXPORT_STATUS=$?
printf 'csv-export-exit=%s\n' "$EXPORT_STATUS"
```

退出码不是 0 时，保留诊断。已经产生的 CSV 也不算完整导出。成功之后核对列名、主键、记录数和原始时间。记下 SQL、库和 CSV 的哈希。CSV 里的字段如果带换行，不能用文件行数当记录数，要按 CSV 解析。时间单位和时区没确认，就保留原值。

输出分别关联 `账户主键 → 登录来源与时间`、`站点主键 → 域名和目录`、`数据库主键 → 账户与连接限制`，再和未修改的库、配置及日志核对。保留库哈希、表结构、查询语句、原始时间单位和导出格式。面板列表能显示、主库能查询、真实业务能运行，是三个独立结论。

查询用的是 `snapshot.db` 的一致备份，表和字段来自这份库的 schema。WAL 没一起保全时，不把单独拷走的主库写成完整历史。仿真里的新登录不写入历史操作。下一步要看到`PRAGMA integrity_check` 和快照哈希在传输前后一致。CSV 的列名对得上那一条 SELECT。保存启动前的库和 WAL、快照哈希、schema、SQL 和 CSV 哈希。

`users` 没有 `salt` 列，或 `salt` 为空时，一批旧版面板的口令哈希是 `md5(md5(md5(明文密码) + "_bt.cn"))`。用同机出现过的口令前缀生成候选，再和 `password` 比对。绑定账号和安全入口仍按本节前面的 `userInfo.json`、`admin_path.pl` 读取。口令哈希能对上，只说明这个候选和库里的摘要一致，不代替登录记录。

</details>
