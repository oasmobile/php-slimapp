---
title: "日志生命周期"
doc_type: system-operations
evidence:
  - path: "src/SlimApp.php"
  - path: "src/ConsoleApplication.php"
  - path: "src/AbstractAlertableCommand.php"
  - path: "composer.lock"
---

# 日志生命周期

SlimApp 使用 oasis/logging 与 Monolog 安装全局日志 handler。

## Handler 装配

应用初始化和 Console 执行分别添加适用 handler。
SlimApp 将已解析的 Monolog Level 传给 handler 和由它创建的 Console 实例。

- SlimApp 初始化安装 LocalFileHandler 和 LocalErrorHandler。
- 错误 handler 使用错误触发的缓冲日志；不能理解成只保存逐条 error 记录。
- Console 配置 I/O 时安装终端 handler，运行命令时安装普通与错误文件 handler。
- 额外 handler 必须实现 HandlerInterface。
- `--alert` 的异常处理见[错误模型](../interfaces/errors.md)。

## 文件模式与级别

SlimApp 提供的模式会覆盖其创建的 Console 实例的默认模式。

| 来源 | 默认模式 |
| --- | --- |
| SlimApp | `%date%/%script%.%type%` |
| 独立 ConsoleApplication | `%date%/%script%.%command%.%type%` |

Console 执行命令时将 `%script%` 替换为冒号转点后的命令名，并分别替换 `%type%` 为 log/error。
它没有在此步骤替换 `%command%`；不要假定所有模式都会展开此 token。

日志目录未配置时，Console 使用系统临时目录下的 `logs`。
属性配置和终端 verbosity 映射见[日志配置](../../user-guide/logging.md)。
