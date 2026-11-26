---
title: 程序格式与入口首轮判断
summary: 先按 PE、ELF、JAR、APK、WASM 等格式分流，记录入口和保护信息。
module: Reverse
topic: 程序结构
tags: [文件格式]
status: 已整理
sourceIds: []
challengeIds: [3df3f86ba521, 72e197eaaac6, 478f25269338, 1c45f7d38b2e, 4b5a4b9b0555]
updated: 2026-09-30
---

## 适用场景

拿到可执行文件、驱动、JAR、APK 或 WASM，却不知道从哪类工具开始时使用。先在**副本**上做只读识别，不依据后缀决定格式；有些题目故意去掉扩展名或改名。

## 01 固定样本并识别容器

```bash
sha256sum sample.bin
file sample.bin
xxd -l 32 sample.bin
strings -a -n 6 sample.bin | head -40
```

哈希用于确认后续分析的仍是同一份样本；`file` 和文件头用于分流；`strings` 只列可打印片段，不保证这些字符串会在运行时使用。记录架构、位数、大小端、是否带符号和明显的封装层。

| 格式 | 第一批线索 | 下一步 |
|---|---|---|
| PE/Windows 驱动 | DOS/PE 头、节、导入表、子系统 | 在 PE 解析器与反编译器中定位入口和导入函数 |
| ELF | 文件头、程序头、动态依赖、符号 | 用 `readelf` 区分加载段与节，找入口与调用链 |
| JAR | ZIP 中的 class、清单、依赖 | 先列类名，再看字节码或反编译结果 |
| APK | Manifest、DEX、资源与 native 库 | 从组件入口和交互事件追到校验函数 |
| WASM | 导入、导出、函数与线性内存 | 看导出入口及宿主环境如何调用 |

## 02 按格式深入

下面的命令**各自独立使用**，不要把 ELF 命令套到 PE 或 APK 上。

```bash
readelf -h -l -S sample.elf
unzip -l sample.jar | head -60
unzip -l sample.apk | head -60
wasm-objdump -x challenge.wasm
```

`readelf -h/-l/-S` 分别看文件头、程序头与节头；节信息被剥离时，程序头仍可说明装载布局。归档文件列表不等于安全可执行；列出内容即可，不要直接运行题目程序。WASM 的导出函数可能只是包装层，还要看 JavaScript 宿主传入什么字节。

## 03 给后续分析一个起点

输出“格式 + 架构 + 可调用入口 + 输入来源 + 第一处比较/输出”。若存在壳或混淆，先记录证据（节熵、导入异常、控制流特征），不要仅凭工具提示就断言已加壳。进入 [输入变换与比较值追踪](/knowledge/reverse-dataflow/) 或 [JAR、APK 与 WASM 的分层阅读](/knowledge/reverse-bytecode/) 后，再回到原程序确认结论。
