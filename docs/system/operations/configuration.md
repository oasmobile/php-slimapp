---
title: "运行时配置"
doc_type: system-operations
evidence:
  - path: "src/SlimApp.php"
  - path: "src/SentinelCommand/CommandConfiguration.php"
  - path: "tests/ut/ConfigParserTest.php"
---

# 运行时配置

本页说明配置文件如何进入框架；使用方取值示例见[配置访问](../../user-guide/configuration.md)。

## 应用配置装配

`SlimApp::init()` 接收配置目录、ConfigurationInterface 和可选缓存目录。

1. 从配置目录读取 `config.yml`，按使用方 schema 合并校验。
2. 保证 `dir.config` 值可用，将配置扁平化为容器参数。
3. 加载同目录 `services.yml`，运行编译 Pass 并编译容器。
4. 实例化编译容器并获取 app 服务，再安装日志 handler。

省略缓存路径时使用 `<配置目录>/cache`；缓存数据见[缓存模型](../data/cache.md)。

## 服务定义与应用属性

`services.yml` 使用 Symfony DI YAML；框架为应用装配以下属性。

| 属性 | 装配目标 |
| --- | --- |
| logging | 日志目录、级别、模式与额外 handler |
| cli | Console 名称、版本与额外命令 |
| http | MicroKernel 配置 |

`default.namespace` 控制编译 Pass 是否遍历定义，具体条件见[内部接口](../interfaces/internal.md)。

## Sentinel 配置

调度命令读取独立 YAML 文件，并使用 CommandConfiguration 校验。

| 字段 | 默认值或要求 |
| --- | --- |
| name | 必填 |
| args | 空数组，必须为数组 |
| parallel | 1 |
| once | false |
| alert | true |
| interval、frequency | 0 |
| frequency_fixed | false |

使用 ConsoleApplication 时，匹配 `%参数%` 的值整体替换为容器参数，不执行字符串插值。
调度规则和参数示例见 [Daemon Sentinel](../../user-guide/daemon-sentinel.md)。
