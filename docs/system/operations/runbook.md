---
title: "框架运行与维护"
doc_type: system-operations
evidence:
  - path: "bin/slimapp"
  - path: "config/app.php"
  - path: "init-ut/composer.json"
  - path: "tests/integration/console.php"
  - path: "tests/integration/http.php"
---

# 框架运行与维护

SlimApp 作为 Composer 库分发；生产业务入口由使用方项目生成并维护。

## 入口与责任

框架 CLI、业务入口和测试入口有不同用途。

| 路径 | 用途 |
| --- | --- |
| bin/slimapp | 探测使用方 bootstrap 或 Composer autoload，取得应用后运行 Console |
| config/app.php | 保留的单例返回入口；bin 不直接加载此文件 |
| 使用方 bootstrap.php | 初始化应用单例 |
| 使用方 web/front.php | 运行 MicroKernel |
| 使用方 bin/项目.php | 运行应用 Console |
| tests/integration/console.php、http.php | 仓库人工集成入口，不属于自动 smoke/release |
| init-ut/ | 独立工程生成器测试环境，通过 Composer path 引用框架 |

## 按故障定位

按故障所属主题读取一份页面。

- 配置与应用属性：[运行时配置](configuration.md)。
- 日志与 handler：[日志生命周期](observability.md)。
- 缓存与进程恢复：[运行限制与恢复](limits-and-recovery.md)。
- 静态已知问题：[已知偏差](../deviations.md)。
- 开发验证与环境：[PROJECT.md](../../../PROJECT.md)。
