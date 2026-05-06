# Changelog v3.1.0

本文件记录 v3.1.0 hotfix 的变更内容。

---

## 修复

### 脚手架模板适配 Doctrine ORM 3.x

- `InitializeProjectCommand` 生成的 ORM 相关代码适配 Doctrine ORM 3.x API：
  - `Setup::createAnnotationMetadataConfiguration()` → `ORMSetup::createAttributeMetadataConfiguration()`
  - `ConsoleRunner::createHelperSet()` → `SingleManagerProvider`
  - console 入口改用 `ConsoleRunner::addCommands()` 注册 ORM 命令
  - 移除已废弃的 `DefaultCacheFactory`、`RegionsConfiguration` 引用
  - `getEntityManager()` 添加返回类型声明
- `init-ut/composer.json` 中 slimapp 版本约束改为 `*` 以适配任意本地分支

### 迁移文档重构

- `docs/manual/migration-v2-to-v3.md` 全面重构：
  - 以读者操作路径为主线重新组织结构
  - 修正示例代码、补充最简迁移路径
  - 增加报错速查表（常见错误 → 解决方案）
  - 调整步骤顺序使其更符合实际操作流程

---

## 测试覆盖

- 全量测试：171 tests, 2157 assertions（全部通过）
