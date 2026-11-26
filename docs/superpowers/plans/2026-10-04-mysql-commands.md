# MySQL 取证实战命令补充计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在既有MySQL数据目录与表恢复知识点补齐常用取证命令，按真实赛事考点组织实用流程。
**Architecture:** 保留原11节完整前缀，追加统一命令体系及构造场景；归属Forensics / 服务器取证 / Web与数据库不变。正文在content-curation维护，生成器持久导入。
**Tech Stack:** Markdown、Astro、Python内容/保全测试；MySQL官方文档及真实竞赛一手解析；独立自建SQL样本。
**Spec:** 用户明确要求详细全面实用、结构清晰，参考实际取证比赛题。

## 约束与执行裁定

- 原材料只读；MySQL比赛检材不复跑、不编造题目或复用固定答案/真实口令。正文用来源独立的业务场景；真实赛事、URL、题意和映射在内部覆盖记录保留。
- 本轮只是用户指定现有正文的编辑，不改站点界面/行为、分类或建立新工程；直接按既有维护路径执行，不引入设计批准或Git工作树。
- 命令默认Kali/Linux；MySQL5.7/8.0/8.4/MariaDB条件明确，不把5.5本机结果当8.x实测。
- MySQL既有服务不连接/启停；若做SQL实验，仅用当前工作目录下全新datadir及独立本地通信端点，停止仅该实验进程。
- 后续授权内容修改需要刷新RegRipper保全目录中的目标主稿/生成稿两项哈希，保留前后哈希及原因，不删断言、不放宽其他文件检查。
- TDD与全量测试保持原有目录缺失失败；不伪造工具路径或忽略测试。

## 审阅重点

1. --no-defaults首选项及login-path例外、TCP/socket目标、SERVER VERSION与历史版本区分。
2. 统计的状态/NULL/时区/金额单位、COUNT与估算、JOIN倍增、确定排序与去重。
3. 导入/启动/DDL/恢复写入只针对副本；初始化不可用于既有检材datadir。
4. binlog DECODE-ROWS只读解释，不作为可执行回放；事务边界与DDL/行镜像列序核验。
5. .frm/ibd/ibd2sdi/MyISAM与force_recovery的不同能力和恢复限制；模板与实测分开。

## 任务

- [x] 保存459项源文件基线，执行91项原测试。
- [x] 写新增内容/保全/比赛覆盖/查询测试，确认失败。
- [x] 一手文档/真实赛事核验，编写命令体系及独立样本，逐项映射。
- [x] 生成持久化正文，更新两项授权保全记录，全量复验/构建/审计/重导入及专业审阅。
- [x] 浏览器正文/搜索验收；制作四项证据，独立副本回滚；生产页保持新增内容。
