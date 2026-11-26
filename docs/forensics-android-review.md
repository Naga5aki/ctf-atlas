# Android 取证：整合与验收说明

验收日期：2026-10-04。网站入口：[Android 原理、考点与实战流程](http://127.0.0.1:4321/knowledge/forensic-android-forensics/)。

## 1. 分类与阅读顺序

Android 取证与 iOS 取证均为 **Forensics → 手机取证** 下的并列子模块。Android 分类保留四篇，不把旧内容删除来凑新增页数量：

| 页面 | 本次操作 | 内容 |
| --- | --- | --- |
| forensic-android-forensics | 新增 | 基本概念、提取层级、FDE/FBE、CE/DE、设备状态、权限、多用户、流程、考点、时间、真实比赛和整合说明 |
| forensic-android-storage | 补充 | 保留既有七节；新增应用、系统、网络、数据库、偏好、认证、共享存储及媒体证据位置 |
| forensic-android-tools | 新增 | ADB、ABE、ALEAPP、SQLite/XML/日志、APK 静态检查、格式与时间只读检查器 |
| fic-case-06 | 保留并互链 | 原有移动终端细化案例十一节，维护稿和生成稿字节均保持不变 |

手机取证总指南仅增加导航。原 iOS 三篇、应用通信、钱包及跨平台虚拟空间/解密内容没有覆盖；通用内容以互链消除重复。维护稿统一位于 `src/content-curation/`，完整重导入以后生产正文哈希变化为零。

## 2. 指定文章逐项覆盖

完整读取用户提供的 [Android 参考文章](https://tqandjdc.github.io/2026/06/08/Android-Forensic-Analysis-Reference-Guide/)。文章 **73 个标题**映射为 **75 个处理项**；原理页 4 项、存储页 45 项、工具页 26 项，未映射标题为零。完整定位、章节内关键词、来源抓取哈希和校正依据记录于 `docs/forensics-android-coverage.json`。

原文中的操作主题全部保留，但不能把错误机制变成实用命令：AB 改为逐行 ASCII 头与 zlib、FBE 支持年代与出厂要求分开、Telegram Android cache4 与桌面 TData 分开、Chrome 与 WebView 分开、Cookie 是容器/字段而非统一加密协议、MMS 与通话库按实际 schema 处理。权限/OEM/旧版本文件名保留为待验证候选。Firefox 通用 profile 资料不冒充 Android 全版本统一目录；缩略图不套未经验证的固定表结构。

来源作者及许可在原理正文末标注，文字经过自主组织与校正，没有照抄整篇文章。

## 3. 真实比赛与实测边界

公开案例采用主办方公告与第一人称解析，正文保留材料、证据位置、操作判读、相互验证及限制，不收录固定答案：

- Magnet Virtual Summit 2022：Pixel 3、Snapchat 发送方关联、SIM 交叉核对、空文件元数据。
- Magnet User Summit 2023：Pixel 3a XL、关机/电量、Todoist、商店及任务痕迹；与二月 MVS 的不同检材明确区分。
- Magnet Virtual Summit 2024：Pixel 3a XL、默认浏览器角色、AirTag 检测、Maps/商店搜索；手机文件系统与 Facebook/Discord 导出分别处理。
- 2024 数证杯初赛：高德头像缓存原文件查找与哈希，不能用预览截图替代原字节。

这些比赛检材 **未复跑**。实际执行的是本机 ALEAPP 2026.4.3 对纯合成 vendor/build.prop 的解析：退出 0、Build 七条记录；重开 TSV、HTML、SQLite 与 JSON 输出，逐字段核对及复制文件哈希均一致。没有执行 ADB 设备采集、实际 ABE 解包或安装比赛 APK。

只读检查器 `public/practice/android_inspect.py` 已验证 AB 未加密/加密多行头、XML 类型/实体拒绝、JWT 仅解码、时间转换和异常输入。4 MiB XML、1 MiB JWT/64 层是该检查器自身的限制，并非 Android 通用格式上限。

## 4. 最新验证结果

| 检查 | 实际结果 |
| --- | --- |
| 任务前 Python 基线 | 69 项，68 通过、1 项既有失败，退出 1 |
| 任务后全量 Python | 79 项，78 通过、同一既有失败，退出 1 |
| 新增 Android 专项 | 10 项通过，退出 0 |
| UI 单测 | 5 项通过，退出 0 |
| Astro 检查 | 18 文件，0 错误/警告/提示，退出 0 |
| 构建与搜索索引 | 335 页面、326 页面索引，退出 0 |
| 本地站点审计 | 335 页面、7604 链接、176 知识点、79 工具指南，错误 0 |
| 网络资料登记审计 | 117 登记页面、50 标准来源，错误 0 |
| 完整重导入 | 退出 0，库存原字节恢复，production_changed=[] |
| 原有内容保全 | Android 原七节逐节哈希匹配；受保护正文全部匹配 |
| 浏览器 | 实际展开 Android 四篇与 iOS 三篇同级分类，三篇主线正文可读；personalsafety_db 检索返回原理页，ABE_PASSWD 检索首条为工具页 |

既有失败是 `test_every_catalog_location_exists_and_excludes_project_metadata`：登记的 `D:\CTF_MISC_Tools\Forensics\Inseyets PA` 目录不存在。任务前即失败；没有删除登记、放宽校验或伪造工具目录。

## 5. 修改与回滚证据

完整证据位于 `.work/android-forensics-20261004/`：原始 438 文件快照与 SHA-256、`MODIFIED_FILE.md`、`DIFF_FILE.patch`、`VERIFICATION.txt`、`ROLLBACK.sh`、逐项修改清单和独立审阅报告。回滚只测试于独立副本，生产站点保留新增内容。入口默认只校验；必须显式 `--apply` 才恢复逐项记录的源文件，且先核对当前/备份哈希，避免覆盖后续修改。回滚不替换构建目录或依赖；实际回滚后需重新构建站点。

浏览器截图及文本证据：`android-module.png`、`browser-category.txt`、`browser-core.txt`、`browser-storage.txt`、`browser-tools.txt`、`browser-search.txt`、`browser-search-tools.txt`。精确命令、输入、原样输出与退出状态统一记录于 `VERIFICATION.txt`；独立内容审阅见 `final-review.md`。
