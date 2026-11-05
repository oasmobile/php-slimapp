---
title: "已知偏差"
doc_type: system-deviations
evidence:
  - path: "src/BuiltInCommands/InitializeProjectCommand.php"
  - path: "src/BuiltInCommands/Templates/DatabaseTemplates.php"
  - path: "src/BuiltInCommands/ValidateServicesCommand.php"
  - path: "src/SlimAppCompilerPass.php"
  - path: "composer.lock"
---

# 已知偏差

本页仅记录已核实的当前限制，不把旧 spec 的遗留 checkbox 当成新任务。

## 当前偏差

本页未列出额外的 ORM 工程生成 API 偏差；迁移规则见[ORM 迁移](../user-guide/migration-orm.md)。

## 其他限制入口

以下行为按源码记录，调用方须注意其边界。

- 服务验证的退出码不表示所有服务成功，见[CLI 命令](../user-guide/cli-commands.md)。
- app 自动装配有命名空间参数前提，见[内部接口](interfaces/internal.md)。
- 缓存升级需显式清理，见[运行限制与恢复](operations/limits-and-recovery.md)。
