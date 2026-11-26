# RegRipper 注册表取证补充与核对记录

## 归属与完整性

- 用户要求：详细实用讲解 RegRipper 参数、插件的具体使用，并入注册表取证。
- 唯一正文：`src/content-curation/forensic-registry.md`，生成页面：`src/content/knowledge/forensic-registry.md`。
- 原 ID、URL、Forensics / 计算机取证 / 系统与用户痕迹不变；没有新增文章或分类。新 §10 包含12个子节，解释13项CLI参数、29组插件入口、第一响应、批处理、TLN、GUI、版本差异和实测判读。
- 此前注册表正文及ShellBags链接的完整字节前缀保留；ShellBags、U盘、Android、iOS等既有内容不覆盖。前缀与受保护源文件哈希见 `forensics-regripper-preservation.json`；新增测试据此核验，不依赖临时工作目录。
- 来源仅在内部 supplements 登记，生成器导入；正文不渲染内部来源编号。9条新增一手来源关联，原有3条关联保留。

## 来源与版本核对

- 使用作者RegRipper3.0/4.0仓库README、驱动器rip.pl、GUI rr.pl和插件源码，以及Kali官方工具文档。
- Context7已分别解析两代文档，但其返回摘要中关于TLN/参数的错误解释未采纳；参数与字段以作者实际代码核对。
- 本机3.0 rip.exe哈希与作者仓库提供的编译文件一致。此一致性不代表已编译驱动器的每一实现细节等同最新rip.pl；帮助与无Hive命令另行实测。
- 对本机257份.pl静态建立元数据/源行/哈希目录，见 `forensics-regripper-plugins.json`：9个profiles、60个TLN插件。数量只对应该快照；没有为插件增加并不存在的getDate方法。
- 默认profiles逐项与实际插件目录对照，说明ntuser中的adoberdr/link_click等缺失项；-uP生成清单不是联网更新，且排除tln、All单列和平台写出路径必须检查。
- 独立审阅纠正两处输出范围：networkcards实际输出网卡描述与子键LastWrite，GUID/ServiceName回原键补查；uninstall不承诺直接输出安装路径/卸载命令，这些字段回原键补查。

## 命令、输出与实际运行边界

- 列全13项短参数，区别-r/-f/-p与-a/-aT；模式不是严格互斥。-c仅与-l形成插件清单，不是注册表数据CSV。-s/-u分别修改TLN第三/四字段，不能当证据身份或套到普通文本。
- 实际无Hive帮助/别名/缺参数矩阵保存stdout、stderr、退出状态；--help可能有Unknown option却exit0，空结果亦不意味着无痕迹。
- 两个8192字节regf Hive完全自建，包含/缺少TypedPaths；只对这些材料实际运行本机3.0 CLI。普通typedpaths返回两个值；typedpaths_tln只取url1；缺键仍exit0；-d返回not dirty；有效最小Hive的-g只返回换行。输入前后哈希一致。
- GUI的Hive File / Report File / Rip!标签、自动选插件、.txt与同基名.log追加语义由源码核对，未运行GUI。
- 4.0的run不含3.0的StartupApproved部分、usbstor属性标签及run_yara外部程序/规则调用由源码核对；未执行4.0或Yara。
- 未获取真实用户Hive，未进行比赛检材复跑或用户行为实验。模板命令、静态源码审阅、自建解析结果分别标注，不互相替代。

## 验收入口与基线异常

- 新增6项测试覆盖正文持久化、原文与其他主题保全、参数边界、实际插件名、TLN和实用流程；先失败后通过。
- 基线85项测试中84通过、1项旧失败：登记的外部工具目录`D:\CTF_MISC_Tools\Forensics\Inseyets PA`缺失。目录清单与测试断言原样保留，未伪造路径或忽略测试。
- 补充后全量91项测试；唯一失败仍是相同旧失败。UI测试、Astro检查、构建与站点/来源审计分别运行；具体命令、字面输出、退出状态保留在工作证据。
- 全量重复导入检查正文/元信息哈希，原工具清单字节保持；正文与关联可持续重导入。
- 浏览器检查新§10、参数表、插件字段、12个子节与RegRipper搜索结果，保存页面截图及可访问树。

## 变更与回滚证据

证据包：`.work/regripper-20261004/`。任务前源文件快照与哈希、统一差异、修改稿副本、`VERIFICATION.txt`、可执行`ROLLBACK.sh`分别保存。回滚程序先校验每个目标绝对路径与前后哈希，默认仅检查；独立命名副本的回滚验证不会回滚生产站点。恢复的是源文件状态，不宣称恢复dist、浏览器或服务状态。最终执行命令与结果以`VERIFICATION.txt`、`rollback-verification.json`、`final-review.md`为准。

## 本轮已观察结果

- 6项新增测试与独立终审通过；全量91项中90项通过、1项原有缺失目录失败。5项UI通过，Astro18文件0 errors/warnings/hints。
- 构建336页面、检索索引327页面；站点审计7639条本地链接、177知识点、79工具指南、0错误；网页来源审计117条、50项标准、errors为空。
- 浏览器新§10与12子节、修正后的networkcards/uninstall字段及GUI标签可见；RegRipper检索5条，注册表正文第一，页面定位与截图已保存。
- 独立副本执行回滚：恢复4个旧文件、移除5个本轮新增文件；454个任务前文件哈希全部恢复。原85项测试84通过、同一旧失败1，Android/iOS与ShellBags保留；生产源文件未回滚，§10继续存在。
