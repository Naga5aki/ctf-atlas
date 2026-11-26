---
name: ctf-atlas-verify
description: "CTF Atlas 修改后的验证流程：改前留基线、全套检查命令、浏览器与搜索验收、分层如实报告。"
whenToUse: "在 ctf-atlas 中改过任何文件之后、向用户汇报结果之前必须加载；接手时核对当前状态也用它。"
---

# CTF Atlas 验证流程

构建通过、HTTP 200 或命令退出 0，都不能单独证明内容正确。每次修改都按下述顺序留证据。

## 1. 改动前

- 列出要改的文件和章节；范围不能唯一确定时先问用户。
- 先跑一遍第 2 节的检查，记录改前状态。历史交接里的测试数字只是历史，不等于这次通过。
- 按既有做法把原文件复制到 `.work/<批次名>/` 并记下 SHA-256；不覆盖已有备份或上一批记录。
- 小批修改。不盲跑全量 `import_manuals.py`，它重读上级资料并生成多类内容，先看影响范围再决定。

## 2. 改动后的检查命令

在工程根目录执行，顺序如下。`py -V:3.12` 就是工作区任务登记的 Python 3.12（`C:/Users/TWK/AppData/Local/Programs/Python/Python312/python.exe`）。Windows 用 `npm.cmd`，可避开 PowerShell 脚本策略问题。

```powershell
py -V:3.12 -X utf8 scripts/cursor_project_check.py
py -V:3.12 -X utf8 -m unittest discover -s tests -v
npm.cmd run test:ui
npm.cmd run check
npm.cmd run build
py -V:3.12 -X utf8 scripts/audit_site.py
```

改了服务器取证相关页面时，先单跑专项再跑全套：

```powershell
py -V:3.12 -X utf8 -m unittest discover -s tests -p test_server_practical_review.py -v
```

来源文件有变动时另跑 `py -V:3.12 -X utf8 scripts/audit_forensics_web.py --cached`。纯文字组织、没动数据或配置时，不为凑流程去查无关文档。

| 检查 | 能证明 | 不能证明 |
|---|---|---|
| `cursor_project_check.py` | 工作区与规则文件齐全、Forensics 维护稿与生成页正文一致 | 语义完整性、页面视觉 |
| Python 全套测试 | 数据与内容满足机器可核对的约束 | 真实检材已复跑 |
| `npm run test:ui` | 界面脚本的单元测试 | 浏览器里的实际表现 |
| `npm run check` | Astro 文件没有类型或语法诊断 | 内容正确 |
| `npm run build` | 页面能构建，Pagefind 索引已生成 | 链接有效、页面好看 |
| `audit_site.py` | 构建产物里的本地链接没有缺失，未出现不该展示的资料名称 | 外链有效、搜索能搜到 |

## 3. 浏览器与搜索验收

- 用 `npm.cmd run preview -- --port 4329` 启动预览，只绑定 127.0.0.1。先确认端口和进程属于本项目，不随意结束别的服务。
- 实际打开受影响的页面：标题与目录、锚点跳转、代码块和表格的显示，再搜一次确认新内容能被搜到。
- 新增内容后必须重新 `npm run build`，Pagefind 才会更新；开发服务页面能打开不代表搜索索引已更新。
- 浏览器或工具被已保存的设置阻止时，如实写“待核”，不换工具绕开，也不把构建成功冒充视觉验证。

## 4. 如实报告

- 分三层报告，不混为一谈：语法检查、合成验证（只在自建材料上运行示例）、真实检材复跑。
- 改前就有的失败项照实记录，改后比较有没有新增。不写“所有测试通过”，不靠降低测试、重写历史报告或改无关哈希来掩盖。
- `docs/` 下的审查记录是基线。内容变更后保存前一版报告，再诚实更新受影响的条目。
- 向用户汇报的顺序：实际结果 → 涉及的文件和章节 → 保留和新增的考点 → 验证结果与待核项 → 下一步。用简短中文，不堆开发过程术语。

## 5. 留下可回退的版本

- 文件改动留下变更包、diff、验证记录和可回退的版本。
- 回滚先在另一个副本试验，不直接回滚正在工作的正式目录。
