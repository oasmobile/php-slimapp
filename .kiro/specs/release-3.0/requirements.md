# Requirements Document

## Introduction

`oasis/slimapp` 是一个基于 Symfony 组件的 PHP 全栈微框架，支持 CLI 和 HTTP 双模式运行。Release 3.0 是一次大版本升级，核心目标包括：将 PHP 最低版本要求升级至 >=8.5、所有依赖升级至最新大版本（Symfony ^8.0、PHPUnit ^13 等）、源码全面采用 PHP 8.5 现代语法、适配 `oasis/http` v3.0 API（SilexKernel → MicroKernel）、移除全 public 服务逻辑和 deprecated 类、测试框架升级并引入 PBT 达到 90%+ 综合覆盖率、更新文档和撰写迁移指南。

本次升级允许 breaking changes。

**不涉及的内容（Non-scope）**：不重新设计框架架构（保持 SlimApp 单例模式、DI 容器、Console/HTTP 双模式）；不新增业务功能特性；不处理下游使用方项目的实际升级（仅提供迁移文档）；不为 `InitializeProjectCommand` 编写自动化测试。

---

## Glossary

- **SlimApp**: `Oasis\SlimApp\SlimApp` 类，框架核心单例，管理配置、DI 容器、日志、HTTP Kernel 和 Console Application
- **ConsoleApplication**: `Oasis\SlimApp\ConsoleApplication` 类，继承 Symfony Console Application，提供日志集成
- **SlimAppCompilerPass**: `Oasis\SlimApp\SlimAppCompilerPass` 类，DI 编译器 Pass，负责默认命名空间解析、`app` 服务注册和服务可见性控制
- **DaemonSentinelCommand**: `Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand` 类，读取 YAML 配置并通过 pcntl_fork 调度多个守护进程命令
- **AbstractDaemonSentinelCommand**: `Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand` 类，DaemonSentinelCommand 的 deprecated 父类，本次升级将被移除
- **CommandConfiguration**: `Oasis\SlimApp\SentinelCommand\CommandConfiguration` 类，Sentinel YAML 配置的 Symfony ConfigurationInterface 实现
- **CommandRunner**: `Oasis\SlimApp\SentinelCommand\CommandRunner` 类，负责 fork 子进程并管理调度（间隔、频率、重启等）
- **AbstractAlertableCommand**: `Oasis\SlimApp\AbstractAlertableCommand` 类，提供 `--alert` 选项的 Command 基类
- **AbstractParallelCommand**: `Oasis\SlimApp\AbstractParallelCommand` 类，支持 pcntl_fork 并行执行的 Command 基类
- **MicroKernel**: `Oasis\Mlib\Http\MicroKernel` 类，`oasis/http` v3.0 中替代 SilexKernel 的 HTTP Kernel 实现
- **SilexKernel**: `Oasis\Mlib\Http\SilexKernel` 类，`oasis/http` v2.x 中基于 Silex 的 HTTP Kernel 实现，v3.0 中已被 MicroKernel 替代
- **Eris**: `giorgiosironi/eris` ^1.1，PHP 的 Property-Based Testing 库，集成于 PHPUnit
- **Composer_Config**: `composer.json` 文件，定义项目依赖、自动加载和元数据
- **PHPUnit_Config**: `phpunit.xml` 文件，定义测试套件、覆盖率过滤和报告配置
- **Coverage_Baseline**: 排除 `InitializeProjectCommand` 和 `src/tests/` 目录后，ut + pbt + integration 综合覆盖率 90%+ 的目标基准
- **Migration_Guide**: `docs/manual/migration-v2-to-v3.md` 文件，面向下游项目维护者的 2.x → 3.0 迁移指南
- **ClearCacheCommand**: `Oasis\SlimApp\BuiltInCommands\ClearCacheCommand` 类，清除框架缓存目录的内置命令

---

## Requirements

### Requirement 1: PHP 版本与 Composer 依赖升级

**User Story:** 作为框架维护者，我希望将 PHP 最低版本和所有依赖升级至最新大版本，以便框架能够使用现代语言特性和受维护的上游库。

#### Acceptance Criteria

1. THE Composer_Config SHALL declare `php` requirement as `>=8.5`
2. THE Composer_Config SHALL declare `symfony/dependency-injection` as `^8.0`
3. THE Composer_Config SHALL declare `symfony/config` as `^8.0`
4. THE Composer_Config SHALL declare `symfony/console` as `^8.0`
5. THE Composer_Config SHALL declare `symfony/finder` as `^8.0`
6. THE Composer_Config SHALL declare `symfony/filesystem` as `^8.0`
7. THE Composer_Config SHALL declare `oasis/logging` as `^3.0`
8. THE Composer_Config SHALL declare `oasis/utils` as `^3.0`
9. THE Composer_Config SHALL declare `oasis/http` as `^3.0`
10. THE Composer_Config SHALL declare `phpunit/phpunit` as `^13` in require-dev
11. THE Composer_Config SHALL declare `doctrine/orm` as `^3.6` in require-dev
12. THE Composer_Config SHALL declare `oasis/aws-wrappers` as `^3.0` in require-dev
13. THE Composer_Config SHALL declare `oasis/dynamodb-odm` as `^2.0` in require-dev
14. THE Composer_Config SHALL declare `oasis/doctrine-addon` as `^3.1` in require-dev
15. THE Composer_Config SHALL declare `giorgiosironi/eris` as `^1.1` in require-dev
16. WHEN `composer update` is executed, THE Composer_Config SHALL resolve all dependencies without conflict

### Requirement 2: PHP 8.5 语法现代化

**User Story:** 作为框架维护者，我希望所有源码和测试文件采用 PHP 8.5 语法，以便代码库保持一致、类型安全并充分利用现代语言特性。

#### Acceptance Criteria

1. THE SlimApp SHALL include `declare(strict_types=1)` in every `.php` file under `src/` and `tests/`
2. THE SlimApp SHALL declare typed properties (with explicit types) for all class properties in `src/`
3. THE SlimApp SHALL declare parameter types and return types for all methods in `src/`
4. THE SlimApp SHALL use `match` expressions where appropriate to replace `switch` statements with simple value mappings
5. THE SlimApp SHALL use constructor promotion where it simplifies constructor-only property assignment
6. THE SlimApp SHALL use `readonly` modifier for properties that are assigned once and never mutated
7. WHEN PHP 8.5 is the runtime, THE SlimApp SHALL produce zero deprecation notices from PHP engine

### Requirement 3: HTTP Kernel 适配（SilexKernel → MicroKernel）

**User Story:** 作为框架维护者，我希望将 SilexKernel 替换为 `oasis/http` v3.0 的 MicroKernel，以便 HTTP 子系统使用当前的上游 API。

#### Acceptance Criteria

1. THE SlimApp SHALL use MicroKernel as the HTTP Kernel implementation (replacing SilexKernel)
2. THE SlimApp SHALL store and expose the HTTP Kernel instance as MicroKernel type
3. THE SlimApp `getHttpKernel()` method SHALL return MicroKernel as its declared return type
4. WHEN `getHttpKernel()` is called, THE SlimApp SHALL instantiate MicroKernel with the HTTP config and debug mode
5. WHEN `getHttpKernel()` is called, THE SlimApp SHALL inject the SlimApp instance and container parameters into MicroKernel using MicroKernel's API
6. THE SlimApp SHALL remove all references to `SilexKernel` from the codebase
7. THE ClearCacheCommand SHALL clear MicroKernel's cache directories: preferring `getCacheDirectories()` if available, otherwise using MicroKernel's alternative cache path API (e.g. `getCacheDir()`)

### Requirement 4: DI 容器 — 移除全 Public 服务逻辑

**User Story:** 作为框架维护者，我希望移除 SlimAppCompilerPass 中的全 public 服务行为，以便 DI 容器遵循 Symfony 标准的默认 private 约定。

#### Acceptance Criteria

1. THE SlimAppCompilerPass SHALL retain the `default.namespace` class resolution logic
2. THE SlimAppCompilerPass SHALL retain the `app` service auto-registration logic (setting class and factory)
3. THE SlimAppCompilerPass SHALL remove the `$definition->setPublic(true)` call that forces all services to public
4. WHEN the DI container is compiled, THE SlimAppCompilerPass SHALL leave service visibility at its declared value (defaulting to private per Symfony convention)
5. THE SlimAppCompilerPass SHALL keep the `app` service as public (it is the framework's core entry point and consumers may retrieve it via the container)
6. THE SlimApp `getService()` method SHALL only retrieve services that are explicitly declared as public in `services.yml`
7. IF `getService()` is called with a non-public service ID, THEN THE SlimApp SHALL throw a `ServiceNotFoundException` (standard Symfony behavior)

### Requirement 5: 移除 AbstractDaemonSentinelCommand

**User Story:** 作为框架维护者，我希望移除已废弃的 AbstractDaemonSentinelCommand，以便代码库只保留单一、清晰的 Sentinel 命令实现。

#### Acceptance Criteria

1. THE SlimApp SHALL delete the file `src/SentinelCommand/AbstractDaemonSentinelCommand.php`
2. THE DaemonSentinelCommand SHALL directly extend AbstractAlertableCommand (instead of extending AbstractDaemonSentinelCommand)
3. THE DaemonSentinelCommand SHALL contain the complete sentinel execution logic: reading YAML config, dispatching child processes via CommandRunner, and waiting for background processes to complete
4. THE DaemonSentinelCommand SHALL retain the sentinel command configuration behavior (setting description and the `file` argument)
5. THE DaemonSentinelCommand SHALL retain the execution behavior of config parsing, CommandRunner instance creation, and process lifecycle management
6. THE DaemonSentinelCommand SHALL retain the background process waiting behavior, including process exit handling and early-runner logic
7. THE SlimApp SHALL remove all test files referencing AbstractDaemonSentinelCommand

### Requirement 6: PHPUnit 13 测试框架升级

**User Story:** 作为框架维护者，我希望将所有测试升级至 PHPUnit 13 API，以便测试套件在当前 PHPUnit 版本上运行且无弃用警告。

#### Acceptance Criteria

1. THE PHPUnit_Config SHALL use PHPUnit 13 XML schema (`https://schema.phpunit.de/13.0/phpunit.xsd` or equivalent)
2. THE PHPUnit_Config SHALL use `source` element with `include`/`exclude` for coverage filtering (replacing the deprecated `filter`/`whitelist` elements)
3. WHEN test classes extend a base class, THE SlimApp SHALL use `\PHPUnit\Framework\TestCase` (replacing `\PHPUnit_Framework_TestCase`)
4. THE SlimApp SHALL replace all `setExpectedException()` calls with `expectException()` and `expectExceptionMessage()`
5. THE SlimApp SHALL replace all `assertInternalType('array', ...)` calls with `assertIsArray(...)` (and analogous replacements for other internal types)
6. THE SlimApp SHALL replace `getMockBuilder(...)->getMock()` with `createMock(...)` or `createStub(...)` where appropriate
7. WHEN the full test suite is executed, THE SlimApp SHALL produce zero PHPUnit deprecation warnings
8. THE SlimApp SHALL update `tests/bootstrap.php` and `tests/integration/bootstrap.php` to be compatible with PHPUnit 13

### Requirement 7: Property-Based Testing 引入

**User Story:** 作为框架维护者，我希望使用 Eris 引入 Property-Based Testing，以便核心组件能够通过大量生成的输入来发现边界情况。

#### Acceptance Criteria

1. THE SlimApp SHALL create PBT test files under `tests/pbt/` directory
2. THE PHPUnit_Config SHALL include a `pbt` test suite pointing to `tests/pbt/`
3. THE SlimApp SHALL write PBT tests for CommandConfiguration that verify: FOR ALL valid command config arrays, processing then re-processing the configuration SHALL produce an equivalent result (idempotence property)
4. THE SlimApp SHALL write PBT tests for CommandRunner scheduling logic that verify: FOR ALL combinations of `once`, `interval`, `frequency`, and `frequency_fixed` values, `onProcessExit()` SHALL produce a `nextRun` value consistent with the scheduling rules (nextRun >= lastRun + frequency when frequency > 0; nextRun >= time() + interval when interval > 0)
5. THE SlimApp SHALL extract configuration parsing logic into an independently testable unit and write PBT tests that verify: FOR ALL valid configuration trees (generated with constrained random values), parsing followed by retrieval SHALL return the corresponding value from the input tree (round-trip property)
6. THE SlimApp SHALL write PBT tests for SlimAppCompilerPass namespace resolution that verify: FOR ALL class names and namespace combinations, the resolution logic SHALL produce a fully-qualified class name that either exists or equals the original input (metamorphic property)
7. THE SlimApp SHALL write PBT tests for ConsoleApplication verbosity-to-log-level mapping that verify: FOR ALL valid Symfony verbosity constants, `configureIO()` SHALL map to a valid Monolog log level (total function property)

### Requirement 8: 覆盖率目标

**User Story:** 作为框架维护者，我希望综合测试覆盖率达到 90%+，以便代码库具备强有力的回归保护。

#### Acceptance Criteria

1. THE PHPUnit_Config SHALL exclude `src/BuiltInCommands/InitializeProjectCommand.php` from coverage measurement
2. THE PHPUnit_Config SHALL exclude the `src/tests/` directory from coverage measurement
3. WHEN ut, pbt, and integration test suites are executed together, THE Coverage_Baseline SHALL reach 90% or higher line coverage
4. THE SlimApp SHALL provide a coverage merge script (`tests/run_all_coverage.sh` or equivalent) that combines coverage from ut, pbt, and integration suites into a single report
5. THE SlimApp SHALL configure PHPUnit to output coverage reports in at least text format for CI verification

### Requirement 9: 集成测试适配

**User Story:** 作为框架维护者，我希望集成测试和 fixtures 能够在升级后的依赖下正常工作，以便端到端行为得到验证。

#### Acceptance Criteria

1. THE SlimApp SHALL update `tests/integration/fixtures/TestAppConfig.php` to use the Symfony 8.0 TreeBuilder API (replacing deprecated `TreeBuilder()` constructor and `->root()` call)
2. THE SlimApp SHALL update `tests/integration/config/services.yml` to declare services that need to be fetched via `getService()` as `public: true`
3. THE SlimApp SHALL update integration test fixtures (`DummyCommand.php`, `TestSentinelCommand.php`, `TestController.php`) to use PHP 8.5 syntax and PHPUnit 13 API
4. THE SlimApp SHALL update integration test scripts (`tests/scripts/parallel_command_test.php`, `tests/scripts/sentinel_command_test.php`) to be compatible with the upgraded framework
5. WHEN integration tests are executed, THE SlimApp SHALL produce zero errors and zero failures

### Requirement 10: 文档更新

**User Story:** 作为框架维护者，我希望项目文档反映 3.0 的变更，以便维护者和使用方拥有准确的参考资料。

#### Acceptance Criteria

1. THE SlimApp SHALL update `docs/state/architecture.md` to reflect MicroKernel replacing SilexKernel, removal of all-public services, and removal of AbstractDaemonSentinelCommand
2. THE SlimApp SHALL update `docs/state/cli-commands.md` to reflect any command changes (removal of AbstractDaemonSentinelCommand, updated DaemonSentinelCommand)
3. THE SlimApp SHALL update `docs/state/configuration.md` to document the DI visibility change (services default to private)
4. THE SlimApp SHALL update `PROJECT.md` to reflect PHP >=8.5, Symfony ^8.0, PHPUnit ^13, and other dependency version changes
5. THE SlimApp SHALL update `README.md` to reflect the new PHP version requirement and major dependency versions

### Requirement 11: 迁移指南

**User Story:** 作为下游项目维护者，我希望有一份从 slimapp 2.x 升级到 3.0 的迁移指南，以便我能够有清晰的指引来规划和执行升级。

#### Acceptance Criteria

1. THE SlimApp SHALL create `docs/manual/migration-v2-to-v3.md` as the migration guide
2. THE Migration_Guide SHALL list all dependency version changes (from → to) in a table format
3. THE Migration_Guide SHALL document the `getHttpKernel()` return type change from SilexKernel to MicroKernel, including required consumer code changes
4. THE Migration_Guide SHALL document the DI visibility change: services default to private, `getService()` only works for explicitly public services, consumers must use constructor injection
5. THE Migration_Guide SHALL document the removal of AbstractDaemonSentinelCommand and the migration path (extend DaemonSentinelCommand or use it directly)
6. THE Migration_Guide SHALL document PHPUnit upgrade steps for consumer test suites (base class, assertion methods, mock API changes)
7. THE Migration_Guide SHALL recommend consumers migrate from `getService('app')` to constructor injection for the `app` service
8. THE Migration_Guide SHALL provide a step-by-step upgrade checklist for downstream projects

---

## Socratic Review

### 每条 requirement 是否都在描述外部可观察行为？

Req 1–4、6、8–11 聚焦于外部可观察行为和配置约束，符合 requirements 定位。Req 5（移除 AbstractDaemonSentinelCommand）在修正前包含了过多实现细节（具体方法名、pcntl_waitpid loop），已修正为聚焦行为层面的描述。Req 7（PBT）的 AC 描述了测试应验证的属性（idempotence、round-trip、total function 等），这些是可观察的质量属性而非实现细节，可以接受。

### 是否有遗漏的场景？

- **错误路径**：Req 4 AC6 覆盖了 `getService()` 调用非 public 服务的异常行为。Req 5 的 sentinel 执行逻辑中进程异常退出的处理属于现有行为保持，不需要额外 AC。
- **边界条件**：Req 2 的 PHP 8.5 语法现代化未明确 `tests/` 下的类型声明严格程度（测试代码是否也要求完整类型声明）。AC1 已覆盖 `declare(strict_types=1)` 对 tests/ 的要求，AC2-3 限定为 `src/`，这是合理的——测试代码的类型声明要求可以宽松一些。
- **并发/幂等**：不涉及新的并发场景，现有 sentinel 的 fork 行为属于保持不变。

### 各 requirement 之间是否存在矛盾或重叠？

- Req 1 AC15（Eris 依赖声明）与原 Req 7 AC1 存在重复，已修正（移除 Req 7 中的重复项）。
- Req 2（语法现代化）与 Req 9（集成测试适配）在 PHP 8.5 语法方面有交叉，但 Req 2 聚焦 `src/`，Req 9 聚焦 `tests/integration/`，分工合理。
- Req 6（PHPUnit 升级）与 Req 9（集成测试适配）在测试框架方面有交叉，但 Req 6 聚焦 API 迁移规则，Req 9 聚焦集成测试特有的 fixtures 和配置，分工合理。

### 是否有隐含的前置假设没有显式列出？

- 假设 `oasis/http` v3.0 的 MicroKernel 提供了与 SilexKernel 等价的 `getCacheDirectories()` 或类似 API（Req 3 AC7 依赖此假设）。如果 API 不存在，ClearCacheCommand 的适配方式需要在 design 阶段确认。
- 假设 Eris ^1.1 兼容 PHPUnit 13。如果不兼容，PBT 方案需要调整。
- 假设 Symfony ^8.0 的 TreeBuilder API 变更方式与 Symfony 4→5→6 的演进一致（Req 9 AC1）。

### 与 proposal 的 scope / non-goals 是否一致？

Requirements 覆盖了 proposal 中 Phase 0–4 的所有内容。Non-goals 与 proposal 一致（不重新设计架构、不新增功能、不处理使用方升级）。Requirements 未越界也未缩水。

### scope 边界是否清晰？

- Req 3（HTTP Kernel 适配）的边界清晰：只替换 SlimApp 内部的 SilexKernel 引用，不涉及下游使用方的适配。
- Req 4（DI 可见性变更）的边界清晰：只移除 CompilerPass 中的 `setPublic(true)`，不改变 DI 容器的其他行为。
- Req 11（迁移指南）的边界清晰：只提供文档，不执行下游项目的实际迁移。

---

## Gatekeep Log

**校验时间**: 2025-01-20
**校验结果**: ⚠️ 已修正后通过

### 修正项
- [结构] Introduction 补充了 Non-scope 段落，明确列出不涉及的内容
- [结构] 各 section 之间补充了 `---` 分隔符
- [结构] 补充了缺失的 Socratic Review section
- [术语] Glossary 补充了 `Migration_Guide` 和 `ClearCacheCommand` 术语定义（AC 中使用但未定义）
- [语体] 11 条 User Story 从英文改为中文（`作为 <角色>，我希望 <能力>，以便 <价值>`）
- [内容] Req 3 AC1-2 从具体 import 语句改为聚焦行为层面的描述
- [内容] Req 5 AC3-6 移除了过度的实现细节（具体方法名、pcntl_waitpid loop、early-runner cloning logic），改为聚焦行为
- [内容] Req 7 移除了与 Req 1 AC15 重复的 Eris 依赖声明 AC，并重新编号

### 合规检查
- [x] 无 TBD / TODO / 待定 / 占位符
- [x] 无空 section 或不完整的列表
- [x] 内部引用一致（术语表术语在 AC 中使用，AC 编号连续）
- [x] 无 markdown 格式错误
- [x] 一级标题存在且正确
- [x] Introduction 存在，描述了 feature 范围
- [x] Introduction 明确了不涉及的内容（Non-scope）
- [x] Glossary 存在且非空，术语格式正确
- [x] Requirements section 存在且包含 11 条 requirement
- [x] 各 section 之间使用 `---` 分隔
- [x] Glossary 中的术语在正文 AC 中被实际使用
- [x] AC 中使用的领域概念在 Glossary 中有定义
- [x] User Story 使用中文行文
- [x] AC 使用 `THE <Subject> SHALL` / `WHEN ... THEN` / `IF ... THEN` 语体
- [x] AC 编号连续无跳号
- [x] AC 聚焦外部可观察行为，无不当的实现细节
- [x] Goal CR 决策已体现在 requirements 中
- [x] 文档整体目标清晰，scope 边界明确
- [x] AC 构成充分的验收条件
- [x] 具备足够信息进入 design 阶段

### Clarification Round

**状态**: 已回答

**Q1:** Req 3 AC7 要求 ClearCacheCommand 调用 MicroKernel 的缓存目录 API。当前代码调用的是 `SilexKernel::getCacheDirectories()`。如果 MicroKernel 的缓存目录 API 签名或行为与 SilexKernel 不同，ClearCacheCommand 应如何适配？
- A) 假设 MicroKernel 提供等价的 `getCacheDirectories()` 方法，直接调用
- B) 如果 MicroKernel 无此方法，ClearCacheCommand 改为只清除 SlimApp 自身的 configCachePath，不再清除 HTTP Kernel 缓存
- C) 如果 MicroKernel 无此方法，通过 MicroKernel 的其他 API（如 `getCacheDir()`）获取缓存路径
- D) 其他（请说明）

**A:** A/C — 优先调用等价的 `getCacheDirectories()`；如果 MicroKernel 无此方法，则通过其他 API（如 `getCacheDir()`）获取缓存路径。无论如何必须解决 HTTP Kernel 的缓存清理问题

**Q2:** Req 4 移除全 public 服务后，现有集成测试中通过 `getService()` 获取的服务需要在 `services.yml` 中显式声明为 `public: true`。对于框架自身注册的内部服务（如 `app` 服务），是否也应改为 private，还是保持 public？
- A) `app` 服务保持 public（它是框架的核心入口，使用方可能需要通过容器获取）
- B) `app` 服务也改为 private，使用方通过构造函数注入获取
- C) `app` 服务保持 public，但在迁移指南中建议使用方改为构造函数注入
- D) 其他（请说明）

**A:** C — `app` 服务保持 public，但在迁移指南中建议使用方改为构造函数注入

**Q3:** Req 2 要求源码全面采用 PHP 8.5 语法，包括 `readonly` 修饰符。SlimApp 是单例模式，其属性在 `init()` 中赋值后不再变更。是否应将 SlimApp 的这些属性标记为 `readonly`？这会影响 `resetService()` 等方法的可行性。
- A) 仅对确定不会被重新赋值的属性使用 `readonly`，`resetService()` 涉及的属性除外
- B) 不对 SlimApp 类使用 `readonly`，仅对其他类（如 CommandConfiguration、CommandRunner）使用
- C) 积极使用 `readonly`，如果与 `resetService()` 冲突则重新设计 reset 机制
- D) 其他（请说明）

**A:** A — 仅对确定不会被重新赋值的属性使用 `readonly`，`resetService()` 涉及的属性除外

**Q4:** Req 7 要求为 SlimApp 配置解析编写 PBT（round-trip property）。SlimApp 的 `init()` 方法依赖文件系统（读取 YAML 配置文件）和 DI 容器编译，这使得纯粹的 property-based testing 较为困难。PBT 应在什么层面进行？
- A) 对 `init()` 进行端到端 PBT，使用临时文件系统生成随机配置文件
- B) 提取配置解析逻辑为独立的可测试单元，对提取后的单元进行 PBT
- C) 降低 PBT 范围，仅测试 `getMandatoryConfig()` / `getOptionalConfig()` 在容器已初始化后的行为
- D) 其他（请说明）

**A:** B — 提取配置解析逻辑为独立的可测试单元，对提取后的单元进行 PBT
