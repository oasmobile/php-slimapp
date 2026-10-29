# Changelog v3.0

本文件记录 v3.0 release 的变更内容。

---

## 包含的 Feature

### PHP 8.5 Upgrade（PRP-001）

- PHP 最低版本要求从 >=7.0 升级至 >=8.5
- 所有 Symfony 组件升级至 ^8.0
- oasis 上游库升级至最新大版本（http ^3.0、logging ^3.0、utils ^3.0）
- PHPUnit 升级至 ^13，Doctrine ORM 升级至 ^3.6
- 源码全面采用 PHP 8.5 语法（declare(strict_types=1)、typed properties、return types、match 表达式、constructor promotion、readonly）
- HTTP Kernel 从 SilexKernel 迁移至 MicroKernel（oasis/http v3.0）
- DI 容器移除全 public 服务逻辑，改为 Symfony 标准默认 private 约定
- 移除 deprecated 的 AbstractDaemonSentinelCommand，DaemonSentinelCommand 直接继承 AbstractAlertableCommand
- 提取 ConfigParser 和 NamespaceResolver 为独立可测试类
- 引入 giorgiosironi/eris ^1.1 进行 Property-Based Testing
- ut + pbt + integration 综合覆盖率达到 90%+
- 撰写 v2 → v3 迁移指南

---

## Breaking Changes

- `getHttpKernel()` 返回类型从 `SilexKernel` 变更为 `MicroKernel`
- DI 容器服务默认 private，`getService()` 仅适用于显式声明 `public: true` 的服务
- 移除 `AbstractDaemonSentinelCommand` 类
- PHP 最低版本要求 >=8.5

---

## 工程变更

- phpunit.xml 升级至 PHPUnit 13 schema
- 新增 `tests/pbt/` 目录，包含 5 个 PBT 测试文件
- 新增 `src/ConfigParser.php`（从 SlimApp 配置解析逻辑提取）
- 新增 `src/NamespaceResolver.php`（从 SlimAppCompilerPass 命名空间解析逻辑提取）
- 删除 `src/SentinelCommand/AbstractDaemonSentinelCommand.php`
- 覆盖率合并脚本适配 PHPUnit 13 API

---

## 文档变更

- 更新 `docs/state/architecture.md`：MicroKernel、DI 可见性、Daemon Sentinel 继承关系
- 更新 `docs/state/cli-commands.md`：Command 基类体系、ValidateServicesCommand 说明
- 更新 `docs/state/configuration.md`：DI 服务可见性变更
- 更新 `PROJECT.md`：技术栈版本
- 更新 `README.md`：PHP 版本要求和依赖版本
- 新增 `docs/manual/migration-v2-to-v3.md`：迁移指南
- 新增 `docs/manual/service-container.md`：DI 容器使用指南

---

## 测试覆盖

- 单元测试: 161 tests, 259 assertions
- PBT: 10 tests, 1900 assertions（5 个 property，每个 100+ 迭代）
- 集成测试: parallel command + sentinel command 脚本通过
- 综合覆盖率: 90%+（排除 InitializeProjectCommand）
