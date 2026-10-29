---
title: "CLI 命令"
doc_type: user-guide
evidence:
  - path: "src/BuiltInCommands/"
  - path: "tests/ut/BuiltInCommands/"
---

# CLI 命令

本页列出 SlimApp 注册的三个内置命令。

## 工程生成

`slimapp:project:init` 生成使用方工程；它不同于 MDF 初始化。

- `--project-root` / `-p` 指定项目根，默认当前目录。
- 根目录须已有 `composer.json`、`composer.lock` 与 `vendor/`。
- 交互收集包名、命名空间、目录、ORM/ODM 与 PHPUnit 选项。
- 写入应用类、配置模板、引导文件、Web/Console 入口和示例控制器。
- 更新 Composer autoload，并执行依赖安装相关命令。
- 已存在的生成文件会经过覆盖询问；`composer.json` 由命令直接更新。

操作步骤见[快速开始](getting-started.md)；ORM 限制见[已知偏差](../system/deviations.md)。

## 清缓存

`slimapp:cache:clear` 清除配置缓存和 HTTP Kernel 返回的缓存目录内容。

它保留目录本身；详细的部署与缓存恢复规则见[运维](../system/operations/runbook.md)。

## 验证服务

`slimapp:services:validate` 遍历可获取的服务 ID，并尝试逐个实例化。

- 成功时输出 `Done.`。
- 捕获服务的 Exception 后输出错误及 trace，再继续下一项。
- 最终返回 0；必须检查输出，不能只凭退出码判定配置正确。

自定义命令和并行命令见[自定义命令](console.md)。
