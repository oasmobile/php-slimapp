# PRP-001 PHP 8.5 Upgrade

**Status**: `accepted`

---

## Background

`oasis/slimapp` 当前基于 PHP >=7.0 构建，核心依赖锁定在 Symfony ^4.0、PHPUnit ^5.7、Doctrine ORM ^2.5 等旧版本。所有 oasis 系列上游库已完成 PHP 8.5 升级并发布了新的大版本：

| 库 | 当前使用版本 | 最新大版本 | 最低 PHP 要求 |
|----|-------------|-----------|--------------|
| `oasis/http` | ^2.0 (Silex) | v3.0.1 (Symfony MicroKernel) | >=8.5 |
| `oasis/logging` | ^1.2.0 | v3.0.2 | >=8.2 |
| `oasis/utils` | ^1.6 | v3.0.2 | >=8.2 |
| `oasis/aws-wrappers` | ^2.2.1 | v3.0.3 | >=8.5 |
| `oasis/dynamodb-odm` | ^1.0 | v2.0.0 | >=8.5 |
| `oasis/doctrine-addon` | ^2.0.2 | v3.1.1 | ^8.4 |
| `symfony/*` | ^4.0 | ^8.0 | >=8.2 (oasis 库已统一到 ^8.0) |
| `doctrine/orm` | ^2.5 | ^3.6 | >=8.2 |
| `phpunit/phpunit` | ^5.7 | ^13 | >=8.3 |
| `monolog/monolog` | (via logging ^1.x) | ^3.0 | >=8.2 |

当前代码无 `declare(strict_types=1)`，无类型声明，测试用例基于 PHPUnit 5.7 API（`\PHPUnit_Framework_TestCase`、`setExpectedException()` 等），无 PBT 覆盖。

---

## Problem

1. PHP 7.0 已于 2019 年 EOL，存在安全风险
2. 无法使用 PHP 8.x 新语法特性（typed properties、union types、enums、readonly、`match` 等）
3. 上游 oasis 库的 v3.x / v2.x 大版本均要求 PHP 8.5，当前版本约束无法升级
4. `oasis/http` v3.0 从 Silex 迁移到 Symfony MicroKernel，API 发生重大变化（`SilexKernel` → `MicroKernel`）
5. PHPUnit 5.7 已不维护，缺少现代测试能力
6. 无 PBT（Property-Based Testing），测试覆盖率不足

---

## Goals

- 将 PHP 最低版本要求升级至 8.5
- 所有依赖升级至当前最高大版本
- 源码全面采用 PHP 8.5 语法（`declare(strict_types=1)`、typed properties、return types 等）
- 测试框架升级至 PHPUnit 13，所有测试用例适配并通过
- 引入 eris 1.x 进行 PBT，ut + pbt + integration 综合覆盖率达到 90%+
- 更新项目文档（`docs/state/`、`PROJECT.md`）和迁移指南

---

## Non-Goals

- 不重新设计框架架构（保持 `SlimApp` 单例模式、DI 容器、Console/HTTP 双模式）
- 不新增功能特性
- 不处理使用方项目的升级（仅提供迁移文档）
- 不新增业务功能特性

---

## Scope

### Phase 0 — Composer 依赖升级

升级 `composer.json` 中所有依赖至最新大版本：

**require**:

| 依赖 | 当前 | 目标 |
|------|------|------|
| `php` | >=7.0 | >=8.5 |
| `symfony/dependency-injection` | ^4.0 | ^8.0 |
| `symfony/config` | ^4.0 | ^8.0 |
| `symfony/console` | ^4.0 | ^8.0 |
| `symfony/finder` | ^4.0 | ^8.0 |
| `symfony/filesystem` | ^4.0 | ^8.0 |
| `oasis/logging` | ^1.2.0 | ^3.0 |
| `oasis/utils` | ^1.6 | ^3.0 |
| `oasis/http` | ^2.0 | ^3.0 |

**require-dev**:

| 依赖 | 当前 | 目标 |
|------|------|------|
| `phpunit/phpunit` | ^5.7 | ^13 |
| `doctrine/orm` | ^2.5 | ^3.6 |
| `oasis/aws-wrappers` | ^2.2.1 | ^3.0 |
| `oasis/dynamodb-odm` | ^1.0 | ^2.0 |
| `oasis/doctrine-addon` | ^2.0.2 | ^3.1 |

此阶段不要求代码能编译或测试通过，仅确保 `composer update` 成功。

### Phase 1 — 语法升级与测试适配

- 所有 `src/` 和 `tests/` 文件添加 `declare(strict_types=1)`
- 源码适配 PHP 8.5 语法：typed properties、参数/返回值类型声明、`match` 表达式等
- 适配 `oasis/http` v3.0 API 变更（`SilexKernel` → `MicroKernel`）
- 所有测试用例升级至 PHPUnit 13 API：
  - `\PHPUnit_Framework_TestCase` → `\PHPUnit\Framework\TestCase`
  - `setExpectedException()` → `expectException()` + `expectExceptionMessage()`
  - `getMockBuilder()` → `createMock()` / `createStub()`（视情况）
  - `assertInternalType()` → `assertIsArray()` / `assertIsString()` 等
  - 更新 `phpunit.xml` 配置格式（PHPUnit 13 schema）
- 全部测试通过

### Phase 2 — PBT 与覆盖率

- 引入 `giorgiosironi/eris` ^1.0 作为 dev 依赖
- 为核心组件编写 PBT 用例
- ut + pbt + integration 综合覆盖率达到 90%+
- 配置覆盖率报告（合并 ut、pbt、integration 三套 suite）

### Phase 3 — 收尾

- 清理废弃代码和 deprecated 标记
- 确认 `bin/slimapp` 入口正常工作
- 确认集成测试配置和 fixtures 适配新版本
- 全量测试通过，无 warning / deprecation notice

### Phase 4 — 文档升级

- 更新 `docs/state/architecture.md`（反映 `oasis/http` v3.0 MicroKernel 变更等）
- 更新 `docs/state/configuration.md`（如有配置变更）
- 更新 `docs/state/cli-commands.md`（如有变更）
- 更新 `PROJECT.md`（技术栈、依赖版本、PHP 版本要求）
- 撰写迁移文档 `docs/manual/php85-migration.md`，覆盖：
  - 依赖变更清单
  - `oasis/http` Silex → MicroKernel 迁移要点
  - PHP 语法变更要点
  - PHPUnit 升级要点
  - 使用方项目升级步骤

---

## References

- [oasis/http v3.0.1](https://packagist.org/packages/oasis/http) — Symfony ^8.0, MicroKernel, PHP >=8.5
- [oasis/logging v3.0.2](https://packagist.org/packages/oasis/logging) — Symfony ^8.0, monolog ^3.0, PHP >=8.2
- [oasis/utils v3.0.2](https://packagist.org/packages/oasis/utils) — PHP >=8.2
- [oasis/aws-wrappers v3.0.3](https://packagist.org/packages/oasis/aws-wrappers) — Symfony ^8.0, PHP >=8.5
- [oasis/dynamodb-odm v2.0.0](https://packagist.org/packages/oasis/dynamodb-odm) — Symfony ^8.0, PHP >=8.5
- [oasis/doctrine-addon v3.1.1](https://packagist.org/packages/oasis/doctrine-addon) — Symfony ^8.0, doctrine/orm ^3.6, PHP ^8.4
- [giorgiosironi/eris](https://packagist.org/packages/giorgiosironi/eris) — PBT for PHPUnit
- [Symfony 8.0](https://symfony.com/releases/8.0)
- [PHPUnit 13](https://phpunit.de/)

---

## Notes

- `oasis/http` v3.0 的 API 变更是本次升级最大的风险点：`SilexKernel` 被替换为 `MicroKernel`，`SlimApp` 中的 HTTP Kernel 相关代码需要重写
- 所有 oasis 上游库已统一到 Symfony ^8.0，slimapp 直接使用 ^8.0 与上游对齐；`doctrine/orm` ^3.6 也兼容 Symfony ^8.0
- 上游 oasis 库（`aws-wrappers`、`dynamodb-odm`、`doctrine-addon`）的 dev 依赖已使用 `eris` ^1.0 + `phpunit` ^13，可作为参考
