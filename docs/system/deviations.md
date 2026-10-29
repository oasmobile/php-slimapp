---
title: "已知偏差"
doc_type: system-deviations
evidence:
  - path: "src/BuiltInCommands/InitializeProjectCommand.php"
  - path: "src/BuiltInCommands/ValidateServicesCommand.php"
  - path: "src/SlimAppCompilerPass.php"
  - path: "composer.lock"
---

# 已知偏差

本页仅记录已核实的当前限制，不把旧 spec 的遗留 checkbox 当成新任务。

## 当前偏差

ORM 工程生成模板仍含不匹配 Doctrine ORM 3.x 的 API。

- 生成代码仍调用 `Configuration::addEntityNamespace()` 和 `EntityManager::create()`。
- `composer.lock` 锁定 ORM 3.x；安装版本不提供上述方法。
- 影响启用 ORM 的新工程；本次 MDF 迁移只记录，不修改业务实现。
- 使用方应先修正并验证生成代码，不能把生成成功视为 ORM 可运行。

## 其他限制入口

以下行为按源码记录，调用方须注意其边界。

- 服务验证的退出码不表示所有服务成功，见[CLI 命令](../user-guide/cli-commands.md)。
- app 自动装配有命名空间参数前提，见[内部接口](interfaces/internal.md)。
- 缓存升级需显式清理，见[运行限制与恢复](operations/limits-and-recovery.md)。

## 初始化状态

文档与工作流迁移已落地；是否启用由 `.mdf/manifest.yaml` 控制。
本页不保存工作清单，初始化过程见 `changes/unreleased/mdf-init/CHANGE.md`。
