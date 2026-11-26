---
title: "elf文件"
summary: "重点看： 32-bit / 64-bit、x86 /x86-64 / ARM、dynamically linked /statically linked、strip…"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

## 一、基础识别

**拿到文件先执行：**

file challenge

**重点看：** 32-bit / 64-bit、x86 /x86-64 / ARM、dynamically linked /statically linked、stripped /not stripped。

再检查文件头和 ELF Header：

xxd challenge | head

readelf -h challenge

readelf -h 重点关注：Class（ELF32/ELF64）、Data（大端 / 小端）、Type（EXEC/DYN/REL）、Machine（架构）、Entry point（程序入口）。

## 二、核心概念：Section 与 Segment

| 概念 | 含义 | 查看命令 | Misc用途 |
| --- | --- | --- | --- |
| Section | ELF 文件内部的数据分区 | readelf -S -W | 找隐藏数据的重点 |
| Segment | 程序运行时真正映射到内存的区域 | readelf -l | 分析运行加载 |

常见 Section：

.text（代码）、.rodata（只读数据 / 字符串）、.data（已初始化变量）、.bss（未初始化变量）、.symtab（符号表）、.strtab（字符串表）、.dynsym（动态符号表）、.dynstr（动态字符串表）。

**简单记：**

Section → 文件内部怎么组织；

Segment → 程序运行时怎么加载。找隐藏数据优先看 Section。

## 三、高频考点汇总

考点 1：字符串泄露

**最先做的检查：**

strings -a challenge

strings -a challenge | grep -Ei 'flag|ctf|key|pass|secret|password'

可能直接找到 flag、密码、密钥、文件名、URL、Base64 密文、提示信息、函数名。重点关注 .rodata、.data、.strtab、.dynstr、自定义 Section、文件尾。

查看 .rodata：

readelf -x .rodata challenge

objdump -s -j .rodata challenge

**条件反射：** 拿到 ELF 先做 file + strings -a。

考点 2：Section 隐藏数据

先查看所有 Section：

readelf -S -W challenge

**重点寻找异常名称：** .secret、.flag、.hidden、.payload、.key、.data1；也要注意正常 Section 是否大小异常（如 .comment、.note、.rodata、.data）。

查看可疑 Section：

readelf -x .secret challenge

objdump -s -j .secret challenge

提取 Section（推荐）：

objcopy --dump-section .secret=secret.bin challenge

file secret.bin && strings secret.bin && xxd secret.bin | head && binwalk secret.bin

考点 3：内嵌文件 / 尾部附加数据

ELF 中可能嵌入 ZIP、PNG、JPEG、PDF、文本、另一层 ELF、压缩数据等。

binwalk challenge

**注意：** 不要单纯通过 "最后一个 Section 结束位置" 判断 Overlay，ELF 后面还可能存在合法的 Section Header Table、对齐数据等。

考点 4：符号表泄露

not stripped：符号信息通常完整，nm challenge 或 readelf -s challenge 可能直接出现 decrypt_flag、check_password、print_flag、get_secret、xor_decode 等。

**stripped：** 也不要认为完全没有信息，继续 nm -D challenge、objdump -T challenge、readelf -s challenge，动态链接程序可能仍保留 .dynsym、.dynstr。

stripped ≠ 完全没有符号信息。

考点 5：通过导入函数判断逻辑

objdump -T challenge

| 函数 | 可能含义 |
| --- | --- |
| strcmp / memcmp | 比较输入和正确答案 |
| strlen | 检查字符串长度 |
| fopen / fread | 打开 / 读取文件 |
| write / puts / printf | 输出数据 / 提示 |
| system | 执行系统命令 |
| malloc | 动态申请内存 |

考点 6：动态追踪

**直接运行：** chmod +x challenge && ./challenge，观察输入要求、输出、生成文件、报错。

strace（追踪系统调用）：strace ./challenge，重点看 openat、read、write、access、execve、connect。例如 openat(..., "flag.txt", ...) 说明程序尝试读取 flag.txt。

ltrace（追踪动态库函数）：ltrace ./challenge，简单题可能直接看到 strcmp("AAAA", "correct_password")。特别适合 strcmp、memcmp、strlen、printf、puts 相关题；但静态链接或自行实现函数时可能无效。

考点 7：轻量逆向

objdump -d -M intel challenge

重点关注 main、strcmp、memcmp、循环、xor、add、sub、字符比较、固定数组。复杂时再进 Ghidra、IDA、Cutter。

考点 8：UPX 加壳

**先检查：** strings challenge | grep -i UPX。明显是 UPX 则：

upx -d challenge

脱壳后重新 file、strings -a、readelf -S -W、binwalk，按普通 ELF 重新分析。

考点 9：ELF 文件头损坏

有些题修改 7F 45 4C 46 导致 file 只显示 data。先 xxd challenge | head 检查前几个字节，标准开头 7f 45 4c 46，被修改则用十六进制编辑器修复。

**注意：** ELF Header 损坏不一定只改魔数，还可能破坏位数、字节序、架构、入口点、Program Header Offset、Section Header Offset。修复后继续 readelf -h 检查是否合理。

考点 10：Section Header 缺失

可能出现 readelf -S 异常或没有 Section，但程序仍可正常运行 —— 这是正常现象，因为 ELF 运行主要依赖 Program Header，而非必须依赖 Section Header。

没有 Section Header ≠ 不是 ELF ≠ 不能运行

## 四、elf执行方法

### 1. 标准执行

chmod +x challenge

./challenge

当前目录不在 PATH 中，必须加 ./ 前缀。

### 2. 带输入执行

echo "input" | ./challenge

./challenge < input.txt

./challenge arg1 arg2

### 3. 常见报错速查

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| Permission denied | 无执行权限 | chmod +x challenge |
| No such file or directory（文件存在） | 32 位库缺失或解释器缺失 | 安装 libc6:i386，或 ldd challenge 查依赖 |
| error while loading shared libraries | 缺动态库 | ldd challenge 找缺失库，LD_LIBRARY_PATH=./libs ./challenge 指定路径 |
| cannot execute binary file | 架构不兼容（如 ARM 在 x86 上） | 用对应架构环境或 qemu-arm ./challenge |

### 4. 查看依赖与解释器

ldd challenge                    # 查看依赖库

readelf -l challenge | grep interpreter   # 查看解释器路径
