# Cursor 首次理解核对提示词

首次打开工作区时，可把下面整段发送给Cursor。该步骤只读，不启动新的内容改写批次。

```text
这是CTF Atlas知识库的本地专用工作区。请先实际读取根AGENTS.md、.cursor/rules下三份规则、docs/maintenance/START-HERE.md、WRITING-STANDARD.md、CURRENT-STATE.md、WORK-LOG.md，以及examples/website-reconstruction-approved.md的前四步；再读取src/content.config.ts、src/data/forensics-taxonomy.ts和forensic-guide-server的维护稿/生成页，确认资料确实对应当前项目。

这次只做理解核对，不修改任何文件，不运行终端、Shell、测试、服务或其他程序，不访问外部网址，不安装插件，不开始下一批改写。只使用文件读取工具；缺少读取工具时直接说明，不改用执行命令。

用中文回答：
1. 网站结构、唯一工程位置和五个主模块是什么？
2. Forensics正文改哪里，怎样避免重导入丢失和维护稿/生成稿不一致？
3. 用户认可的讲解顺序是什么？给一段不超过150字的小样，不能空谈“边界/闭环”。
4. 如何语义查重并保留所有有效知识点、考点、命令、参数和失败分支？
5. 网站重构和SSH分别归哪里？怎样处理PHP与非PHP网站？
6. 当前服务器取证实际完成和剩余是多少？下一步从哪一页哪一节继续？
7. 哪些测试问题和浏览器验证仍是待核/历史状态？不能说本次已运行。
8. 怎样防止与另一代理互相覆盖，以及上下文快满时怎样保存续接点？

最后列出这次实际读过的文件；区分“理解核对完成”与“功能、全模块改写、测试已完成”。回答后停下等我的下一条具体命令。
```
