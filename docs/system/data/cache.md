---
title: "缓存数据"
doc_type: system-data
evidence:
  - path: "src/SlimApp.php"
  - path: "src/BuiltInCommands/ClearCacheCommand.php"
  - path: "tests/ut/SlimAppTest.php"
  - path: "tests/ut/Regression/BugY68QTest.php"
---

# 缓存数据

框架持有配置与容器缓存，没有内置业务数据库模型。

## 当前模型

以下文件写在 SlimApp 配置缓存目录中。

| 文件 | 内容与刷新条件 |
| --- | --- |
| config.cache | PHP 序列化配置数组；始终用 ConfigCache 检查配置资源新鲜度 |
| container.php | 编译后的 SlimAppCachedContainer；仅 debug 模式检查资源新鲜度 |
| parameterized_helper.yml | 配置展开后的 parameters 辅助视图；重新解析配置时生成 |

配置缓存位置的计算见[运行时配置](../operations/configuration.md)。

## 所有权与生命周期

配置文件及使用方 schema 是配置内容的来源；缓存只是衍生产物。

- 初始化读取新鲜且反序列化为数组的缓存；配置缺失、失效或内容非法时重新解析并写入。
- 容器文件在同进程内通过 `require_once` 加载，不支持将已加载 PHP 类原地替换为另一版本。
- 缓存目录应由应用拥有且可写；不要让不可信用户写入可执行容器文件。
- 清理操作及升级恢复顺序见[运行限制与恢复](../operations/limits-and-recovery.md)。
- Doctrine 与 DynamoDB 的业务模型属于使用方，框架不负责其数据迁移。
