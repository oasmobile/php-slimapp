---
title: "错误模型"
doc_type: system-interfaces
evidence:
  - path: "src/SlimApp.php"
  - path: "src/AbstractAlertableCommand.php"
  - path: "src/AbstractParallelCommand.php"
  - path: "src/SentinelCommand/"
  - path: "src/BuiltInCommands/ValidateServicesCommand.php"
---

# 错误模型

本页区分异常、命令退出码和只写输出的检查结果。

## 应用与配置异常

调用方须处理配置、容器与类型检查产生的异常。

| 条件 | 行为 |
| --- | --- |
| 配置目录无效、配置路径无法读取 | InvalidArgumentException |
| schema 不匹配 | Symfony 配置校验异常 |
| logging 不是数组或 handler 无效 | InvalidConfigurationException |
| 获取服务时类型不匹配 | Symfony DI InvalidArgumentException |
| Sentinel 参数引用取值为 null | InvalidArgumentException |
| Sentinel parallel 不是整数 | InvalidArgumentException |
| fork 或 wait 失败 | RuntimeException |

## 命令失败语义

并行命令、Sentinel 与服务检查有不同的返回规则。

- AbstractAlertableCommand 捕获 Exception，按 `--alert` 记录后重抛；不捕获全部 Throwable。
- AbstractParallelCommand 的退出码和重启规则见[自定义命令](../../user-guide/console.md)。
- Sentinel 配置文件不可读时输出错误并返回 1；正常结束返回 0。
- CommandRunner 在子进程中把命令异常映射为 255；已发送 alert 的失败可改为退出 0。
- `slimapp:services:validate` 的单服务异常只写输出；最终仍返回 0。
- 测试入口对失败与跳过的要求见[测试约定](../testing/conventions.md)。
