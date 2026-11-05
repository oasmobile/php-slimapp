# Spec Goal: PHP 8.5 Upgrade (Release 3.0)

## 来源

- 分支: `release/3.0`
- 需求文档: `docs/proposals/PRP-001-php85-upgrade.md`

## 背景摘要

`oasis/slimapp` 是一个基于 Symfony 组件的 PHP 全栈微框架，支持 CLI 和 HTTP 双模式。当前基于 PHP >=7.0，核心依赖锁定在 Symfony ^4.0、PHPUnit ^5.7 等旧版本。

所有 oasis 上游库（`http`、`logging`、`utils`、`aws-wrappers`、`dynamodb-odm`、`doctrine-addon`）已完成 PHP 8.5 升级并统一到 Symfony ^8.0。其中 `oasis/http` v3.0 从 Silex 迁移到了 Symfony MicroKernel，API 发生重大变化。

当前代码无 `declare(strict_types=1)`，无类型声明，测试基于 PHPUnit 5.7 API，无 PBT 覆盖。本次升级是一个大版本（3.0），允许 breaking changes。

## 目标

- PHP 最低版本要求升级至 >=8.5
- 所有依赖升级至当前最高大版本（Symfony ^8.0、PHPUnit ^13、Doctrine ORM ^3.6 等）
- 源码全面采用 PHP 8.5 语法（`declare(strict_types=1)`、typed properties、return types 等）
- 适配 `oasis/http` v3.0 API（`SilexKernel` → `MicroKernel`），`getHttpKernel()` 返回类型直接改为 `MicroKernel`
- 移除 `SlimAppCompilerPass` 中的全 public 服务逻辑，改为 Symfony 标准 DI 方式（默认 private）
- 移除 deprecated 的 `AbstractDaemonSentinelCommand`，只保留 `DaemonSentinelCommand`
- 测试框架升级至 PHPUnit 13，所有测试用例适配并通过
- 引入 `giorgiosironi/eris` ^1.1 进行 PBT，ut + pbt + integration 综合覆盖率达到 90%+（`InitializeProjectCommand` 继续排除）
- 更新项目文档和撰写迁移指南

## 不做的事情（Non-Goals）

- 不重新设计框架架构（保持 `SlimApp` 单例模式、DI 容器、Console/HTTP 双模式）
- 不新增业务功能特性
- 不处理使用方项目的升级（仅提供迁移文档）
- 不为 `InitializeProjectCommand` 编写自动化测试

## Clarification 记录

### Q1: `oasis/http` v3.0 MicroKernel 替换 SilexKernel 后，`getHttpKernel()` 如何处理？

- 选项: A) 直接替换返回类型为 `MicroKernel`，使用方自行适配 / B) 引入适配层 / C) 移除 HTTP Kernel 相关代码 / D) 补充说明
- 回答: A — 直接替换，使用方自行适配

### Q2: `SlimAppCompilerPass` 全 public 服务逻辑在 Symfony 8.0 下如何处理？

- 选项: A) 继续保持全 public / B) 移除全 public，改为标准 DI / C) 提供配置项 / D) 补充说明
- 回答: B — 移除全 public，走标准 DI

### Q3: deprecated 的 `AbstractDaemonSentinelCommand` 是否移除？

- 选项: A) 直接移除 / B) 保留并标记 `#[\Deprecated]` / C) 不做变更 / D) 补充说明
- 回答: A — 直接移除

### Q4: `InitializeProjectCommand` 是否纳入覆盖率统计？

- 选项: A) 继续排除 / B) 纳入并 mock 测试 / C) 先纳入，不达标再排除 / D) 补充说明
- 回答: A — 继续排除

## 约束与决策

- **Breaking changes 允许**：这是大版本升级（3.0），`getHttpKernel()` 返回类型变更、全 public 服务移除、deprecated 类删除均为预期的 breaking changes
- **Symfony 版本对齐**：与 oasis 上游库统一使用 ^8.0
- **DI 模式变更**：`getService()` 仅用于显式声明为 public 的服务，使用方需改为构造函数注入；这是迁移文档的重点内容
- **覆盖率计算基准**：排除 `InitializeProjectCommand` 和 `src/tests/` 目录后，ut + pbt + integration 综合 90%+
- **PBT 框架**：使用 `giorgiosironi/eris` ^1.1，与上游 oasis 库保持一致
