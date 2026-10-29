---
title: "系统边界"
doc_type: system-boundary
evidence:
  - path: "composer.json"
---

# 系统边界

SlimApp 为使用方 PHP 工程提供应用装配；业务模型、路由和部署由使用方负责。

## 切面路由

按当前任务选择一个切面，不通读全部主题。

| 切面 | 页面 |
| --- | --- |
| 组件与依赖方向 | [架构](architecture/current.md) |
| 内部协作契约 | [接口](interfaces/internal.md) |
| 框架缓存 | [数据](data/cache.md) |
| 运行与维护 | [运维](operations/runbook.md) |
| 测试 | [测试约定](testing/index.md) |
| 使用方操作 | [用户指南](../user-guide/README.md) |
| 当前偏差 | [已知偏差](deviations.md) |

## 核心模块

下表指向各行为面的唯一归属页。

| 模块 | 打开 |
| --- | --- |
| 配置 | [运行时配置](operations/configuration.md) |
| 可观测性 | [日志生命周期](operations/observability.md) |
| 错误 | [错误模型](interfaces/errors.md) |
| 鉴权 | 不适用：框架没有独立鉴权策略；HTTP security 由使用方配置 oasis/http |
| 限制与恢复 | [运行限制与恢复](operations/limits-and-recovery.md) |
