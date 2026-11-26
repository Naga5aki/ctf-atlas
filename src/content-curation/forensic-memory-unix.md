## 01 识别系统和失败原因

**先看 banner，再找同构建的调试内核。** 文件扩展名不能判断系统，`uname -r` 显示的是分析机内核，也不能代替镜像中的版本。

```bash
sha256sum memory.raw
python3 vol.py -f memory.raw banners
strings -a memory.raw | rg 'Linux version|Darwin Kernel Version'
```

记录内核 release、发行版修订号、架构、编译器和完整 banner。多个命中可能是同一字符串的缓存，也可能来自内存中的虚拟机或文件；结合进程和地址层确认目标。Windows 可自动取得部分 PDB，Linux/macOS 一般需要匹配的 ISF。

## 02 Volatility 3 的 Linux ISF

### 02.1 必须准备的材料

| 材料 | 作用 | 常见错误 |
| --- | --- | --- |
| 含 DWARF 的 `vmlinux` | 内核类型与字段布局 | 用压缩启动文件 `vmlinuz` 代替调试 ELF |
| 同构建 `System.map` | 补充或校正符号地址 | 同名 release 但发行版修订不同 |
| `dwarf2json` | 生成 ISF JSON | 内存不足导致进程被杀，或空输出未发现 |
| 完整 banner | 核对样本和符号 | 只比较 `5.4`，忽略补丁号、架构和构建 |

Ubuntu 通常找 `linux-image-...-dbgsym` 的 `.ddeb`；Debian 找 `linux-image-...-dbg`；CentOS/RHEL 找匹配的 `kernel-debuginfo` 和 `kernel-debuginfo-common`。软件包可解包到独立目录，无需把目标旧内核安装进分析机。

```bash
mkdir -p kernel-files symbols/linux
dpkg-deb -x kernel-debug.ddeb kernel-files/
find kernel-files -type f -name '*vmlinux*'
file kernel-files/usr/lib/debug/boot/vmlinux-target
readelf -S kernel-files/usr/lib/debug/boot/vmlinux-target | rg '\.debug_info'

./dwarf2json linux \
  --elf kernel-files/usr/lib/debug/boot/vmlinux-target \
  --system-map kernel-files/boot/System.map-target > symbols/linux/target.json
python3 -m json.tool symbols/linux/target.json > /dev/null
python3 vol.py -s ./symbols isfinfo.IsfInfo
python3 vol.py -s ./symbols -f memory.raw linux.pslist
```

替换实际路径；若调试包不带 `System.map`，可先只传 `--elf`，不要填一个不匹配的文件。`-s ./symbols` 指向包含 `linux/` 的符号根目录。JSON 能解析仅说明语法完整，还需通过 ISF 中的 banner、目标进程和多个插件验证匹配。

### 02.2 不同发行版的内核匹配示例

下面用不同发行版说明版本匹配差异。release 与软件包修订必须来自目标 banner 和实际调试材料，不能直接套用表中值。

| 发行版环境 | release / 软件包修订 | 要点 |
| --- | --- | --- |
| Ubuntu 20.04 | `5.4.0-100-generic` / `5.4.0-100.113` | generic headers、公共 headers 与调试内核配套 |
| Ubuntu 18.04 HWE | `5.4.0-84-generic` / `5.4.0-84.94~18.04.1` | HWE 内核有发行版后缀，核对完整 banner |
| Ubuntu 16.04 HWE | `4.13.0-36-generic` / `4.13.0-36.40~16.04.1` | `System.map` 可能位于 image 包 |
| Ubuntu 22.04 | `5.15.0-43-generic` / `5.15.0-43.46` | 历史包需查版本存档；旧 Vol2 的 DWARF 支持有局限 |
| Debian 10 | `4.19.0-21-amd64` / `4.19.249-2` | common/amd64 headers 与 dbg 包对应 |
| Debian 11 | `5.10.0-21-amd64` / `5.10.162-1` | 普通 image 中的 map 可能不完整，应检查实际符号 |
| CentOS 7 环境 | `3.10.0-1160.el7.x86_64` 等实际完整 release | `1160` 与 `1160.108.1` 不能当成同一构建 |

旧仓库下线、包被替换、第三方符号压缩包名称错误都会导致失败。记录包名、版本、下载位置与 SHA-256；名称相近不是匹配证据。

## 03 Volatility 2 的 Linux Profile

Vol2 的 Profile ZIP 通常包含 `module.dwarf` 与 `System.map`，使用 Deflate 压缩。它与 Vol3 JSON 是两种格式，不能互换。

1. 在隔离的旧环境中准备匹配内核头文件、编译器、构建工具和 Vol2 `tools/linux`。
2. 修改构建目标，明确使用检材内核头文件；不要让 Makefile 默认使用分析机的 `uname -r`。
3. 编译生成 `module.dwarf`，检查文件非空，再取得同构建 `System.map`。
4. 打包到 Vol2 的 `volatility/plugins/overlays/linux/`，使用 `--info` 查实际 Profile 名。

```bash
zip -9 LinuxTarget.zip module.dwarf System.map-target
unzip -l LinuxTarget.zip
python2 vol.py --info | rg 'Linux'
python2 vol.py -f memory.raw --profile=实际Profile名 linux_banner
```

构建环境可用虚拟机或容器；Ubuntu、Debian、CentOS 所需包不同。Debian 常需匹配 `linux-kbuild` 和编译器包，CentOS 用 `kernel-devel`；某些模块编译需 GPL license 声明。新版本 dwarfdump 与旧 Vol2 解析器可能不兼容，先核对版本和已知补丁，优先考虑 Vol3。

符号构建只是分析环境准备，容器证据的专题统一放在 [服务器取证](/module/forensics/#server)。

### 03.1 可复查的构建步骤

以下操作在独立的匹配构建环境进行，不在检材系统安装内核。以 `5.4.0-100-generic` 为例，替换包文件名、release 和实际 Vol2 目录。

```bash
sudo apt-get install build-essential dwarfdump kmod linux-base
sudo dpkg -i ./linux-headers-5.4.0-100_5.4.0-100.113_all.deb
sudo dpkg -i ./linux-headers-5.4.0-100-generic_5.4.0-100.113_amd64.deb
cd ./volatility/tools/linux
make KVER=5.4.0-100-generic
test -s module.dwarf
cp module.dwarf ../../../symbols-work/module.dwarf
```

先创建 `symbols-work` 目录。此 Makefile 的 `KVER` 可从命令行覆盖；也有历史副本将 release 写在 Makefile 中，需先核对实际构建规则。编译会生成模块和 DWARF，但无需将模块加载到内核；不要执行 `insmod` 来制作离线 Profile。

Debian 10/11 的匹配头文件通常分 `common` 与架构包，先装前者，并准备相应 `linux-kbuild-4.19` / `linux-kbuild-5.10` 和 GCC 工具链。CentOS 7 使用匹配的 `kernel-devel`，`System.map` 可从 kernel RPM 解包获得；构建机的默认内核不应替代目标 release。

```bash
mkdir -p rpm-files
cd rpm-files
rpm2cpio ../kernel-target.x86_64.rpm | cpio -idmv
find ./boot -name 'System.map*' -type f
```

解包会写当前目录，因此目标必须是空的工作目录，先检查包的文件清单。构建失败时保留错误、编译器版本、包哈希和规则；对于 Ubuntu 22.04 等旧 Vol2 不兼容的 DWARF，不能用“文件已生成”代替 Profile 可被正确解析的验证。

## 04 Linux 行为分析顺序

| 目标 | Vol2 常用插件 | Vol3 常用插件 / 检查方向 |
| --- | --- | --- |
| 进程和父子链 | `linux_pslist`、`linux_psaux` | `linux.pslist`、`linux.psscan`、`linux.pstree`、`linux.psaux` |
| 历史与环境 | `linux_bash` | `linux.bash`、环境变量插件；名称以本版帮助为准 |
| 文件和映射 | `linux_lsof`、`linux_find_file` | `linux.lsof`、`linux.proc.Maps`、`linux.elfs` |
| 网络连接 | `linux_netstat` | `linux.sockstat`；关联 PID、端点与时间 |
| 挂载和命名空间 | `linux_mount` | `linux.mountinfo`；容器中挂载视图可能不同 |
| 模块与可疑代码 | `linux_lsmod`、`linux_hidden_modules`、`linux_malfind` | `linux.lsmod`、`linux.check_modules`、可疑内存插件 |
| 内核检查 | syscall/IDT/AFINFO 等插件 | `linux.check_syscall`、`linux.check_idt`、`linux.check_afinfo`、`linux.check_creds` |
| 其他运行态 | 内核日志、TTY、内存空间 | `linux.kmsg`、`linux.tty_check`、`linux.keyboard_notifiers`、`linux.capabilities`、`linux.iomem` |

```bash
python3 vol.py -s ./symbols -f memory.raw linux.pslist
python3 vol.py -s ./symbols -f memory.raw linux.pstree
python3 vol.py -s ./symbols -f memory.raw linux.bash
python3 vol.py -s ./symbols -f memory.raw linux.lsof
python3 vol.py -s ./symbols -f memory.raw linux.sockstat
```

先记录 PID、UID、开始时间与执行路径，再筛选异常。Bash 记录可能含未执行输入或残留；隐藏模块与 hook 命中要排除解析错误、合法补丁和安全软件。

### 04.1 从缓存恢复文件

Vol2 可通过 inode 查文件，也可恢复缓存中仍存在的文件系统片段。

```bash
mkdir -p recovered
python2 vol.py -f memory.raw --profile=实际Profile名 linux_find_file -L
python2 vol.py -f memory.raw --profile=实际Profile名 \
  linux_find_file -i 0xffff000000000000 -O recovered/target.bin
python2 vol.py -f memory.raw --profile=实际Profile名 \
  linux_recover_filesystem -D recovered/
sha256sum recovered/target.bin
```

地址只作占位，必须取自本次输出；`-O` 后需给文件名。恢复结果可能缺页、补零或只含部分缓存，用格式校验、大小和磁盘版本核对。查看 Desktop、home、脚本、配置和临时目录可以缩小文件与行为的调查范围。

### 04.2 volshell

交互式 volshell 用于切换进程上下文、检查地址空间和结构。`hh()` 查帮助，`ps()` 列进程，`cc(pid=...)` 切上下文，`db()` 查看字节，`dt()` 看结构。虚拟地址、物理地址与导出件偏移应各自标注，不能直接互换。

## 05 macOS 内存

先提取 `Darwin Kernel Version`，核对系统构建与架构；再准备对应 kernel 与调试信息。Vol3 用 `dwarf2json mac`，通用 Mach-O 需明确架构。符号根目录中的子目录为 `mac/`。

```bash
mkdir -p symbols/mac
./dwarf2json mac --macho kernel.dSYM/Contents/Resources/DWARF/kernel \
  --macho-symbols kernel > symbols/mac/target.json
python3 vol.py -s ./symbols -f memory.raw mac.pslist.PsList
```

按进程、打开文件、网络、命令行和模块逐层检查，插件是否支持取决于版本与符号。旧 Vol2 的 Mac Profile 和 x86 示例不能直接用于 Apple Silicon；没有匹配环境时保留 banner、字符串偏移与限制，不自行编造进程结果。

## 06 排错与交付

层错误先查是否完整物理内存、压缩封装或进程转储；符号错误查 banner、包版本、架构与缓存；某插件无结果查功能支持、页缺失和采集时点。记录 `镜像哈希 → 符号哈希 → 工具版本 → 插件 → 对象地址 → 派生结果哈希`，并与磁盘、主机日志交叉核验。

## 07 实战：从内核 banner 到进程与连接

**场景与材料：** 一份 Linux 物理内存镜像及若干候选调试包，需要核对可疑脚本的执行和外连。分析机内核版本不参与目标匹配；所有版本值从镜像 banner 与候选包分别记录。

### 07.1 先验证符号，再解释对象

1. 保存镜像哈希和 banners 输出；核对完整 release、修订、架构与构建信息，不只选名称接近的调试包。
2. 按本页 ISF 工作流生成符号，校验 JSON、banner 及多个插件的对象合理性。能输出一行进程名不等于字段布局完全匹配。
3. 从 pslist、pstree、psaux 建立 PID/UID、启动时间、父子链和参数。PID 与地址都记录，退出对象和活动对象分别处理。
4. 沿 lsof、映射与 sockstat 核对脚本路径、打开文件和端点，再与磁盘脚本内容、主机日志或同时间段流量交叉检查。

### 07.2 示例输出的解释边界

进程参数包含某脚本，Bash 缓冲区有相似命令，套接字指向一个外部地址：三项可以形成调查线索。脚本内容、对应进程时间与实际请求日志一致时，才能进一步描述已确认的执行/通信。仅有缓存命令不能证明成功执行，仅有旧套接字不能证明采集时连接仍活动。

没有匹配符号时，保留字符串偏移、banner、缺页与错误，不编造进程和网络结果。后续取得调试包时，用同一镜像重跑并比较对象地址与字段。
