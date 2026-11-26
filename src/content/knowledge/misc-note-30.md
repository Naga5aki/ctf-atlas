---
title: "Python反编译"
summary: "最常见的Python反编译对象，本质保存Python字节码，可通过反编译工具尽量恢复为.py源码。拿到.pyc第一反应：确定版本→反编译→分析源码。"
module: "Misc"
topic: "文件结构与提取"
tags: []
status: "已整理"
sourceIds: ["995f86da2e53"]
challengeIds: []
relatedIds: []
updated: "2026-09-29"
---

一、常见出题形式

| 出题形式 | 核心任务 |
| --- | --- |
| 直接给.pyc文件 | 判断版本→反编译→从源码找flag或逆向算法 |
| PyInstaller打包的.exe | 解包→找主程序.pyc→必要时修复→反编译 |
| .pyc文件损坏 | magic number被改/文件头缺失/截断拼接→先修复再反编译 |
| 反编译工具无法直接还原 | 字节码被改/版本不兼容/混淆保护→转向字节码反汇编和动态分析 |

## 二、重点文件类型

### 1..pyc

最常见的Python反编译对象，本质保存Python字节码，可通过反编译工具尽量恢复为.py源码。拿到.pyc第一反应：确定版本→反编译→分析源码。

### 2..pyo

旧版本Python的优化字节码，处理方法与.pyc基本相同，无需单独学习一套方法。

### 3.PyInstaller.exe

CTF中非常常见（chall.exe、flag.exe、main.exe）。若确认由Python打包而成，解题路线：exe→PyInstaller解包→pyc→Python源码。

## 三、核心工具

### 1.pyinstxtractor

**用途：** 从PyInstaller打包程序中提取Python文件和资源。

**命令：** python pyinstxtractor.py chall.exe

**输出：** chall.exe_extracted/目录，内含main.pyc、struct.pyc、PYZ-00.pyz、PYZ-00.pyz_extracted/及各种依赖模块。

**重点：** 寻找主程序.pyc，通常名称与exe相近，但不能只依赖文件名，应结合文件大小、字符串和代码内容综合判断。

2.pycdc

**用途：** 将.pyc尽可能还原成Python源代码，是首选反编译工具。

**命令：**

pycdc chall.pyc

pycdc chall.pyc>chall.py

### 3.uncompyle6/decompyle3

**定位：** 备用反编译工具，pycdc失败时尝试。

**命令：** uncompyle6 chall.pyc或decompyle3 chall.pyc

**注意：** 不同工具对不同Python字节码版本支持不同，一个工具失败不代表无法反编译；版本支持范围随工具更新变化，不要死记固定版本区间。

4.dis

**用途：** 自动反编译失败后的字节码分析手段，输出Python虚拟机指令。

**前提：** 需能正确加载.pyc中的code object，且加载环境Python版本与目标字节码兼容。

**命令：**

import dis

dis.dis(code)

## 四、第一步：确定Python版本

Python字节码与版本高度相关，3.8/3.9/3.10/3.11的字节码结构可能存在明显差异。反编译失败时首先考虑版本是否匹配。

判断方法

| 方法 | 操作 | 说明 |
| --- | --- | --- |
| file | file chall.pyc | 有时直接输出Byte-compiled Python module for CPython 3.x |
| 查看文件头 | xxd chall.pyc\|head | 重点看前4字节magic number，辅助判断版本 |

## 五、直接拿到.pyc的标准流程

①file判断类型

↓

②xxd查看文件头

↓

③判断Python版本

↓

④pycdc反编译

↓

⑤其他反编译工具交叉尝试

↓

⑥阅读源码

↓

⑦写脚本逆向算法

↓

⑧得到flag

## 六、PyInstaller.exe解题流程

**第一步：** 判断是否为Python/PyInstaller

strings chall.exe|grep-i pyinstaller

binwalk chall.exe

结合Detect It Easy、PE-bear、strings综合判断

出现PyInstaller、PYZ、python3x.dll即高度怀疑

**第二步：** pyinstxtractor解包

python pyinstxtractor.py chall.exe

cd chall.exe_extracted

ls

**第三步：** 寻找主.pyc

重点观察chall.pyc、main.pyc、__main__.pyc及体积较大的.pyc

find.-name"*.pyc"列出所有

**第四步：** 检查并反编译

file main.pyc

pycdc main.pyc

**重要纠正：** 不要把「PyInstaller提取出的所有.pyc都必须手动补16字节头」当成固定规则。不同PyInstaller、Python版本、pyinstxtractor版本处理方式不同，很多情况下已生成可直接反编译的.pyc。

**正确做法：** 先file/pycdc测试，能识别就直接反编译，不能识别再检查文件头。

## 七、.pyc文件头损坏修复

### 1.常见表现

Unknown magic number、Unsupported Python version、Bad magic、Invalid pyc。

### 2.修复方法

找同版本正常.pyc对比头部：

xxd bad.pyc|head

xxd normal.pyc|head

用十六进制编辑器（010 Editor、hexedit、vim）修复magic number和文件头。

## 八、反编译后重点看什么

不要逐句阅读整个程序，优先搜索关键内容。

### 1.直接搜索flag

grep-ni"flag"chall.py

**还可搜索：** ctf、key、password、secret、correct、success、wrong、input。

### 2.重点寻找输入校验逻辑

**更常见的是：**

flag=input()

if check(flag):

print("correct")

此时真正需要分析的是check()函数，而非整个程序。例如MD5校验、逐字符XOR比较等，直接逆运算即可。

## 九、常见Python加密/编码逻辑

Python反编译常只是外壳，真正考点是编码、加密或数学运算。

**重点关注以下模块和函数：**

| 类型 | 关键字 | 逆向方法 |
| --- | --- | --- |
| XOR | ^、xor | flag[i]=data[i]^key[i]（XOR自逆） |
| 字符转换 | ord()、chr() | ord('A')=65、chr(65)='A' |
| 数组运算 | 整数列表 | ''.join(map(chr,result)) |
| Base64 | base64.b64encode() | base64.b64decode() |
| 十六进制 | bytes.hex() | bytes.fromhex() |
| 哈希 | hashlib.md5/sha1/sha256 | 通常需爆破或已知明文 |
| 对称加密 | Crypto、AES、DES | 找key和IV后解密 |
| 压缩 | zlib | zlib.decompress() |
| 序列化 | marshal、pickle | 按对应格式分析 |

这种情况下Python反编译只是找到算法的手段，真正解flag属于普通Misc逆向逻辑。

## 十、反编译不完整怎么办

pycdc输出Unsupported opcode、Failed to decompile或只能恢复部分源码时，不要认为题目做不了，按以下顺序处理：

换反编译器

↓

查看字节码（dis）

↓

结合字符串和常量

↓

手动恢复关键函数

## 十一、dis字节码分析

### 1.重点认识的指令

LOAD_CONST：加载常量

LOAD_FAST/STORE_FAST：加载/存储局部变量

LOAD_GLOBAL：加载全局对象

**CALL：** 函数调用

COMPARE_OP：比较运算

BINARY_OP：二元运算（含XOR等，对应目标Python版本）

**跳转指令：** POP_JUMP_FORWARD_IF_FALSE等

RETURN_VALUE：返回

### 2.分析目的

dis的核心不是完整恢复源码，而是看懂关键函数进行了什么运算。例如：

LOAD_FAST flag

LOAD_CONST 10

BINARY_OP^

大致可还原为flag^10。

## 十二、Python混淆与保护

### 1.普通混淆

反编译后出现无意义变量名（a、b、O0O0OO0O、_0x123），不要纠结变量名，重点跟踪：

输入在哪里→经过什么运算→与什么数据比较→成功条件是什么

可自行重命名变量（如a→flag、b→key）方便分析。

### 2.PyArmor等保护

可能出现pycdc无法恢复、源码只有启动壳、核心代码被保护。这已属于Python反逆向方向，Misc中只需掌握基本思路：

无法静态恢复→程序运行时必须解密→考虑动态提取（运行时寻找解密后的代码、变量、key、flag）

不必在普通Misc阶段深入研究PyArmor内部实现。

## 十三、动态分析

若程序可以运行且最终会计算关键数据，可直接运行、调试、修改代码、插入print、Hook函数。例如恢复出：

key=func1()

data=func2(key)

result=decrypt(data)

与其完整分析func1→func2→decrypt，有时直接修改插入print(key)、print(data)、print(result)效率更高。
