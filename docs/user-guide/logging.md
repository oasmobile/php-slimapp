---
title: "日志配置"
doc_type: user-guide
evidence:
  - path: "src/SlimApp.php"
  - path: "src/ConsoleApplication.php"
---

# 日志配置

通过应用服务的 `logging` 属性设置日志目录、级别、文件模式和额外 handler。

## 配置示例

以下配置使用容器参数引用日志目录。

```yaml
services:
    app:
        properties:
            logging:
                path: "%app.dir.log%"
                level: "debug"
                pattern: "%date%/%script%.%type%"
                handlers: []
```

| 属性 | 输入 |
| --- | --- |
| `path` | 可写日志目录 |
| `level` | Monolog Level、其整数值或级别名称字符串 |
| `pattern` | 传给日志 handler 的文件模式 |
| `handlers` | Monolog HandlerInterface 实例数组 |

## Console 日志

Console 将输出 verbosity 映射为终端日志级别。

| verbosity | 级别 |
| --- | --- |
| quiet | Critical |
| normal | Warning |
| verbose | Notice |
| very verbose | Info |
| debug | Debug |

日志内部生命周期、默认模式与缓冲行为见[可观测性](../system/operations/observability.md)。
