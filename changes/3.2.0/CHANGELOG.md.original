# Changelog — v3.2.0

发布日期：2026-05-06

---

## 修复

### 脚手架模板适配 Doctrine ORM 3.x

- `InitializeProjectCommand` 生成的 ORM 相关代码适配 Doctrine ORM 3.x API：
  - `Setup::createAnnotationMetadataConfiguration()` → `ORMSetup::createAttributeMetadataConfiguration()`
  - `ConsoleRunner::createHelperSet()` → `SingleManagerProvider`
  - console 入口启用 ORM 时自动注册 `orm:*` 命令集
  - 移除已废弃的 `Doctrine\Common\Cache\MemcachedCache` 服务模板
  - `DataProviderInterface::STRING_TYPE` → `DataType::String` 枚举
  - `getEntityManager()` / `getItemManager()` 添加返回类型声明

### init-ut 测试环境

- `init-ut/composer.json` 中 slimapp 版本约束改为 `*`，适配任意本地分支

---

## 文档

### 迁移文档重构

- `docs/manual/migration-v2-to-v3.md` 全面重构：
  - 以读者操作路径为主线重新组织结构
  - 新增 Doctrine ORM 3.x 完整迁移指引（5 个子项）
  - 增加「常见报错速查」表（错误信息 → 解决方案）
  - 合入 oasis/http v3.4+ 恢复的便捷方法说明

---

## 测试覆盖

- 全量测试：192 tests, 2185 assertions（全部通过）
- phpstan level 8：零错误
- 覆盖率：97.87%
