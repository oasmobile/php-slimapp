# Implementation Plan: Release 3.0

## Overview

将 `oasis/slimapp` 从 PHP 7.0 / Symfony 4.0 / PHPUnit 5.7 技术栈升级至 PHP 8.5 / Symfony 8.0 / PHPUnit 13。按 Proposal Phase 顺序执行：先完成 Composer 依赖升级，再按模块拆分语法升级与测试适配，最后完成集成测试、PBT、覆盖率、文档和迁移指南。

## Tasks

- [x] 1. Composer 依赖升级（Phase 0）
  - [x] 1.1 更新 `composer.json` 中所有依赖版本
    - 将 `php` 要求改为 `>=8.5`
    - 将 `symfony/dependency-injection`、`symfony/config`、`symfony/console`、`symfony/finder`、`symfony/filesystem` 改为 `^8.0`
    - 将 `oasis/logging` 改为 `^3.0`，`oasis/utils` 改为 `^3.0`，`oasis/http` 改为 `^3.0`
    - 将 `phpunit/phpunit` 改为 `^13`，`doctrine/orm` 改为 `^3.6`
    - 将 `oasis/aws-wrappers` 改为 `^3.0`，`oasis/dynamodb-odm` 改为 `^2.0`，`oasis/doctrine-addon` 改为 `^3.1`
    - 新增 `giorgiosironi/eris` `^1.1` 到 require-dev
    - Ref: Req 1, AC 1–15
  - [x] 1.2 执行 `composer update` 并验证依赖解析无冲突
    - 确保 lock 文件正确生成
    - 此阶段不要求代码编译通过
    - Ref: Req 1, AC 16
  - [x] 1.3 Checkpoint: 确认 `composer.json` 和 `composer.lock` 正确更新，所有依赖版本符合 Req 1 的 AC。如有问题请向用户确认。Commit。

- [x] 2. SlimApp 核心语法升级 + ConfigParser 提取 + HTTP Kernel 适配
  - [x] 2.1 升级 `src/SlimApp.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 所有属性添加类型声明（`bool`、`array`、`?ArrayDataProvider`、`?Container`、`?string`、`int`、`?ConsoleApplication`、`?MicroKernel`、`?array`、`string` 等）
    - 所有方法添加参数类型和返回类型
    - 对确定不会被重新赋值的属性使用 `readonly`（`resetService()` 涉及的属性除外）
    - Ref: Req 2, AC 1–3, 6
  - [x] 2.2 将 `SilexKernel` 替换为 `MicroKernel`
    - `$silexKernel` 属性重命名为 `$microKernel`，类型改为 `?MicroKernel`
    - `getHttpKernel()` 返回类型声明为 `MicroKernel`
    - `getHttpKernel()` 内部实例化改为 `new MicroKernel($this->httpConfig, $this->isDebugMode)`
    - 调用 `addControllerInjectedArg()` 和 `addExtraParameters()` 注入参数
    - `setHttpProperty()` 中 `$this->silexKernel = null` 改为 `$this->microKernel = null`
    - 移除所有 `SilexKernel` 的 import 和引用
    - Ref: Req 3, AC 1–6
  - [x] 2.3 提取 `ConfigParser` 类（`src/ConfigParser.php`）
    - 创建 `Oasis\SlimApp\ConfigParser` 类，包含 `parse()`、`flatten()`、`retrieve()` 三个静态方法
    - `parse()`: 使用 Symfony Processor 处理配置数组
    - `flatten()`: 将配置树扁平化为 `key => value` 参数映射
    - `retrieve()`: 从扁平化参数中按 key 检索值
    - 在 `SlimApp::init()` 中使用 `ConfigParser` 替代内联的配置解析和扁平化逻辑
    - Ref: Req 7, AC 5
  - [x] 2.4 更新 `SlimAppTest.php` 适配 PHPUnit 13 和 MicroKernel
    - 基类从 `\PHPUnit_Framework_TestCase` 改为 `\PHPUnit\Framework\TestCase`
    - `setExpectedException()` 改为 `expectException()` + `expectExceptionMessage()`
    - `assertInternalType('array', ...)` 改为 `assertIsArray(...)`
    - `getMockBuilder(...)->getMock()` 改为 `createMock(...)` 或 `createStub(...)`
    - `setUp()` 添加 `: void` 返回类型
    - `testGetHttpKernel` 中 `SilexKernel` 断言改为 `MicroKernel`
    - `testMagicSetHttpResetsKernel` 中反射属性名从 `silexKernel` 改为 `microKernel`
    - Ref: Req 3, AC 1–2; Req 6, AC 3–6
  - [x] 2.5 为 `ConfigParser` 编写单元测试（`tests/ut/ConfigParserTest.php`）
    - 测试 `parse()` 基本行为
    - 测试 `flatten()` 扁平化逻辑
    - 测试 `retrieve()` 检索行为
    - 测试 round-trip 基本示例
    - Ref: Req 7, AC 5
  - [x] 2.6 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'SlimAppTest|ConfigParserTest'`，确认 SlimApp 和 ConfigParser 相关测试通过。Commit。

- [x] 3. SlimAppCompilerPass 语法升级 + NamespaceResolver 提取 + 移除全 Public
  - [x] 3.1 升级 `src/SlimAppCompilerPass.php` 为 PHP 8.5 语法并移除全 public 逻辑
    - 添加 `declare(strict_types=1)`
    - `$classname` 属性改为 constructor promotion：`protected readonly string $classname`
    - `process()` 方法添加返回类型 `: void`
    - 移除循环中的 `$definition->setPublic(true)` 调用
    - 在 `app` 服务处理分支中显式添加 `$definition->setPublic(true)`
    - `==` 比较改为 `===`
    - Ref: Req 2, AC 1–3, 5; Req 4, AC 1–5
  - [x] 3.2 提取 `NamespaceResolver` 类（`src/NamespaceResolver.php`）
    - 创建 `Oasis\SlimApp\NamespaceResolver` 类，包含 `resolve(string $className, array $namespaces): string` 静态方法
    - 将 `SlimAppCompilerPass::process()` 中的类名解析和工厂类名解析逻辑委托给 `NamespaceResolver::resolve()`
    - Ref: Req 7, AC 6
  - [x] 3.3 更新 `SlimAppCompilerPassTest.php` 适配 PHPUnit 13 和新行为
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - `testProcessSetsAllServicesPublic` 测试改为验证非 `app` 服务保持其声明的可见性（不再被强制 public）
    - `testProcessSetsAppServiceClassAndFactory` 验证 `app` 服务仍为 public
    - `testConstructorStoresClassname` 适配 constructor promotion（反射方式可能需调整）
    - Ref: Req 4, AC 3–5; Req 6, AC 3
  - [x] 3.4 为 `NamespaceResolver` 编写单元测试（`tests/ut/NamespaceResolverTest.php`）
    - 测试已存在的完全限定类名直接返回
    - 测试短类名在命名空间下解析成功
    - 测试不存在的类名返回原始输入
    - 测试多命名空间优先级
    - Ref: Req 7, AC 6
  - [x] 3.5 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'SlimAppCompilerPassTest|NamespaceResolverTest'`，确认 CompilerPass 和 NamespaceResolver 相关测试通过。Commit。

- [x] 4. AbstractAlertableCommand + AbstractParallelCommand 语法升级
  - [x] 4.1 升级 `src/AbstractAlertableCommand.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 方法添加参数类型和返回类型
    - `const` 常量保持不变（PHP 8.5 中 class constants 已有类型推断）
    - Ref: Req 2, AC 1, 3
  - [x] 4.2 升级 `src/AbstractParallelCommand.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 所有属性添加类型声明
    - 所有方法添加参数类型和返回类型
    - Ref: Req 2, AC 1–3
  - [x] 4.3 更新 `AbstractAlertableCommandTest.php` 和 `AbstractParallelCommandTest.php` 适配 PHPUnit 13
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - `setExpectedException()` 改为 `expectException()`
    - `setUp()` 添加 `: void` 返回类型
    - Ref: Req 6, AC 3–4
  - [x] 4.4 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'AbstractAlertableCommandTest|AbstractParallelCommandTest'`，确认测试通过。Commit。

- [x] 5. DaemonSentinelCommand 重构 — 移除 AbstractDaemonSentinelCommand
  - [x] 5.1 重构 `src/SentinelCommand/DaemonSentinelCommand.php`
    - 将继承关系从 `extends AbstractDaemonSentinelCommand` 改为 `extends AbstractAlertableCommand`
    - 从 `AbstractDaemonSentinelCommand` 内联所有逻辑到 `DaemonSentinelCommand`：
      - `$runningProcesses` 属性（typed: `array`）
      - `configure()` 方法（设置 description 和 `file` argument）
      - `execute()` 方法（读取 YAML 配置、创建 CommandRunner、fork 子进程）
      - `waitForBackgroundProcesses()` 方法（pcntl_waitpid 循环、early-runner 逻辑、进程退出处理）
    - 添加 `declare(strict_types=1)` 和类型声明
    - Ref: Req 2, AC 1–3; Req 5, AC 1–6
  - [x] 5.2 删除 `src/SentinelCommand/AbstractDaemonSentinelCommand.php`
    - Ref: Req 5, AC 1
  - [x] 5.3 更新 Sentinel 相关测试
    - 删除 `tests/ut/SentinelCommand/AbstractDaemonSentinelCommandTest.php`
    - 重写 `tests/ut/SentinelCommand/DaemonSentinelCommandTest.php`：
      - 基类改为 `\PHPUnit\Framework\TestCase`
      - 验证 `DaemonSentinelCommand` 直接继承 `AbstractAlertableCommand`（不再经过 Abstract）
      - 验证 command 定义（name、description、file argument）
      - 验证空配置文件执行返回 0
    - Ref: Req 5, AC 7; Req 6, AC 3
  - [x] 5.4 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'DaemonSentinelCommandTest'`，确认测试通过。Commit。

- [x] 6. ConsoleApplication 语法升级
  - [x] 6.1 升级 `src/ConsoleApplication.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 所有属性添加类型声明
    - 所有方法添加参数类型和返回类型
    - `configureIO()` 中的 `switch` 改为 `match` 表达式
    - Ref: Req 2, AC 1–4
  - [x] 6.2 更新 `ConsoleApplicationTest.php` 适配 PHPUnit 13
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - `setUp()` 添加 `: void` 返回类型
    - `getMockBuilder(...)->getMock()` 改为 `createMock(...)`
    - Ref: Req 6, AC 3, 6
  - [x] 6.3 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'ConsoleApplicationTest'`，确认测试通过。Commit。

- [x] 7. ClearCacheCommand 语法升级 + MicroKernel 适配
  - [x] 7.1 升级 `src/BuiltInCommands/ClearCacheCommand.php` 为 PHP 8.5 语法并适配 MicroKernel
    - 添加 `declare(strict_types=1)`
    - 方法添加参数类型和返回类型（`configure(): void`、`execute(...): int`）
    - `execute()` 中使用 `assert($console instanceof ConsoleApplication)` 替代 `@var` 注释
    - HTTP 缓存目录获取改为防御性策略：优先 `getCacheDirectories()`，回退 `getCacheDir()`，都不存在则跳过
    - `execute()` 返回 `int`（添加 `return 0`）
    - Ref: Req 2, AC 1, 3; Req 3, AC 7
  - [x] 7.2 更新 `ClearCacheCommandTest.php` 适配 PHPUnit 13 和 MicroKernel
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - Mock 对象从 `SilexKernel` 改为 `MicroKernel`
    - `assertContains` 改为 `assertStringContainsString`（PHPUnit 13 对字符串断言的要求）
    - `assertFileNotExists` 改为 `assertFileDoesNotExist`
    - Ref: Req 3, AC 7; Req 6, AC 3, 6
  - [x] 7.3 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'ClearCacheCommandTest'`，确认测试通过。Commit。

- [x] 8. CommandConfiguration 语法升级 + TreeBuilder API 升级
  - [x] 8.1 升级 `src/SentinelCommand/CommandConfiguration.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - `$application` 属性改为 constructor promotion：`private readonly Application $application`
    - `getConfigTreeBuilder()` 返回类型声明为 `TreeBuilder`
    - TreeBuilder API 升级：`new TreeBuilder()` + `$builder->root('daemon-monitor')` 改为 `new TreeBuilder('daemon-monitor')` + `$builder->getRootNode()`
    - `replaceParameterInValue()` 添加参数类型和返回类型
    - Ref: Req 2, AC 1–3, 5
  - [x] 8.2 更新 `CommandConfigurationTest.php` 适配 PHPUnit 13
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - `setExpectedException()` 改为 `expectException()`
    - `getMockBuilder(...)->getMock()` 改为 `createMock(...)`
    - Ref: Req 6, AC 3–4, 6
  - [x] 8.3 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'CommandConfigurationTest'`，确认测试通过。Commit。

- [x] 9. CommandRunner 语法升级
  - [x] 9.1 升级 `src/SentinelCommand/CommandRunner.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 所有属性添加类型声明
    - 所有方法添加参数类型和返回类型
    - 构造函数参数添加类型声明
    - 匿名函数中的 `$PARALLEL_INDEX` 替换逻辑保持不变
    - Ref: Req 2, AC 1–3
  - [x] 9.2 更新 `CommandRunnerTest.php` 适配 PHPUnit 13
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - Ref: Req 6, AC 3
  - [x] 9.3 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'CommandRunnerTest'`，确认测试通过。Commit。

- [-] 10. ValidateServicesCommand 语法升级
  - [x] 10.1 升级 `src/BuiltInCommands/ValidateServicesCommand.php` 为 PHP 8.5 语法
    - 添加 `declare(strict_types=1)`
    - 方法添加参数类型和返回类型（`configure(): void`、`execute(...): int`）
    - `execute()` 中使用 `assert($console instanceof ConsoleApplication)` 替代 `@var` 注释
    - `execute()` 返回 `int`（添加 `return 0`）
    - 修正 `execption` 拼写为 `exception`
    - Ref: Req 2, AC 1, 3; Req 4, AC 6
  - [x] 10.2 更新 `ValidateServicesCommandTest.php` 适配 PHPUnit 13
    - 基类改为 `\PHPUnit\Framework\TestCase`
    - `getMockBuilder(...)->getMock()` 改为 `createMock(...)`
    - `assertContains` 改为 `assertStringContainsString`
    - Ref: Req 6, AC 3, 6
  - [-] 10.3 Checkpoint: 运行 `./vendor/bin/phpunit --filter 'ValidateServicesCommandTest'`，确认测试通过。Commit。

- [~] 11. PHPUnit 配置 + 测试 bootstrap 升级
  - [ ] 11.1 升级 `phpunit.xml` 为 PHPUnit 13 格式
    - Schema 改为 `https://schema.phpunit.de/13.0/phpunit.xsd`
    - `<filter><whitelist>` 改为 `<source><include>/<exclude>`
    - `<logging><log type="coverage-text">` 改为 `<coverage><report><text>`
    - 移除 deprecated 属性（`backupStaticAttributes`、`verbose`）
    - 添加 `pbt` 测试套件指向 `tests/pbt/`
    - 排除 `src/BuiltInCommands/InitializeProjectCommand.php` 和 `src/tests/`
    - Ref: Req 6, AC 1–2; Req 8, AC 1–2, 5
  - [ ] 11.2 升级 `tests/bootstrap.php` 兼容 PHPUnit 13
    - 移除 PHPUnit 5.7 的 `ReflectionType::__toString()` deprecation 抑制逻辑
    - 保持 oasis/logging 静默配置
    - Ref: Req 6, AC 8
  - [ ] 11.3 更新剩余测试文件适配 PHPUnit 13
    - `tests/ut/ForkProcessTest.php`：基类改为 `\PHPUnit\Framework\TestCase`，`setUpBeforeClass()` 添加 `: void`
    - `tests/ut/BuiltInCommands/InitializeProjectCommandTest.php`（如存在）：基类改为 `\PHPUnit\Framework\TestCase`
    - Ref: Req 6, AC 3, 7
  - [ ] 11.4 Checkpoint: 运行 `./vendor/bin/phpunit --testsuite ut`，确保所有单元测试通过且无 PHPUnit deprecation 警告。Commit。

- [~] 12. 集成测试适配
  - [ ] 12.1 升级 `tests/integration/fixtures/TestAppConfig.php`
    - 添加 `declare(strict_types=1)`
    - TreeBuilder API 升级：`new TreeBuilder()` + `$treeBuilder->root('app')` 改为 `new TreeBuilder('app')` + `$treeBuilder->getRootNode()`
    - 方法添加返回类型
    - Ref: Req 9, AC 1
  - [ ] 12.2 更新 `tests/integration/config/services.yml`
    - 需要通过 `getService()` 获取的服务添加 `public: true`（如 `app`、`cli.command.dummy`、`cli.command.sentinel` 等）
    - Ref: Req 9, AC 2
  - [ ] 12.3 升级集成测试 fixtures 为 PHP 8.5 语法
    - `DummyCommand.php`：添加 `declare(strict_types=1)`，方法添加类型声明
    - `TestSentinelCommand.php`：添加 `declare(strict_types=1)`，方法添加类型声明
    - `TestController.php`：添加 `declare(strict_types=1)`，方法添加类型声明
    - Ref: Req 9, AC 3
  - [ ] 12.4 升级集成测试脚本兼容升级后的框架
    - `tests/scripts/parallel_command_test.php`：适配 PHPUnit 13 覆盖率 API（`Filter` 和 `CodeCoverage` 构造函数签名可能变化）
    - `tests/scripts/sentinel_command_test.php`：同上
    - `tests/scripts/merge_coverage.php`：适配 PHPUnit 13 覆盖率 API，更新文件列表（移除 `AbstractDaemonSentinelCommand.php`，添加 `ConfigParser.php` 和 `NamespaceResolver.php`）
    - Ref: Req 9, AC 4
  - [ ] 12.5 升级 `tests/integration/bootstrap.php` 兼容 PHPUnit 13
    - Ref: Req 6, AC 8; Req 9, AC 5
  - [ ] 12.6 Checkpoint: 运行集成测试和 fork 测试脚本，确保所有集成测试通过且无错误。Commit。

- [~] 13. Property-Based Testing 引入
  - [ ] 13.1 创建 `tests/pbt/` 目录和 PBT 基础设施
    - 创建 `tests/pbt/` 目录
    - 确认 `phpunit.xml` 中 `pbt` 测试套件已配置（Task 11.1 已完成）
    - Ref: Req 7, AC 1–2
  - [ ] 13.2 编写 CommandConfiguration 幂等性 PBT（`tests/pbt/CommandConfigurationPbtTest.php`）
    - **Property 1: CommandConfiguration 处理幂等性**
    - 生成随机 command config 数组（name: string, args: array, parallel: int 1-10, once/alert/frequency_fixed: bool, interval/frequency: int 0-300）
    - 验证：处理一次得到 R1，将 R1 作为输入再处理得到 R2，R1 === R2
    - 最小迭代次数 100 次
    - Ref: Req 7, AC 3
  - [ ] 13.3 编写 CommandRunner 调度约束 PBT（`tests/pbt/CommandRunnerSchedulingPbtTest.php`）
    - **Property 2: CommandRunner 调度约束**
    - 生成随机 once (bool)、interval (int 0-300)、frequency (int 0-300)、frequency_fixed (bool)、lastRun (int time()-600..time())、exitStatus (int 0-255)
    - 验证：非 once 时，`nextRun >= lastRun + frequency`（当 frequency > 0）；`nextRun >= now + interval`（当 interval > 0）；frequency=0 且 interval=0 时 `nextRun ≈ now`
    - 最小迭代次数 100 次
    - Ref: Req 7, AC 4
  - [ ] 13.4 编写 ConfigParser Round-Trip PBT（`tests/pbt/ConfigParserPbtTest.php`）
    - **Property 3: 配置解析 Round-Trip**
    - 生成随机配置树（叶子值为 string/int/bool，嵌套深度 1-3 层，key 为合法 YAML key）
    - 验证：对于配置树中每个叶子节点路径 `path`，`ConfigParser::retrieve(ConfigParser::flatten($config), 'app.' + path)` 等于原始值
    - 最小迭代次数 100 次
    - Ref: Req 7, AC 5
  - [ ] 13.5 编写 NamespaceResolver Metamorphic PBT（`tests/pbt/NamespaceResolverPbtTest.php`）
    - **Property 4: 命名空间解析 Metamorphic 属性**
    - 生成随机短类名 (string) 和命名空间数组 (string[])，混合存在/不存在的类名
    - 验证：结果要么是存在的 FQCN（`class_exists(result) === true`），要么等于原始输入
    - 最小迭代次数 100 次
    - Ref: Req 4, AC 1; Req 7, AC 6
  - [ ] 13.6 编写 Verbosity-to-LogLevel 全函数 PBT（`tests/pbt/VerbosityMappingPbtTest.php`）
    - **Property 5: Verbosity-to-LogLevel 全函数属性**
    - 从 5 个有效 Symfony verbosity 常量中随机选择
    - 验证：映射结果属于有效的 Monolog Logger 级别常量集合
    - 最小迭代次数 100 次
    - Ref: Req 7, AC 7
  - [ ] 13.7 Checkpoint: 运行 `./vendor/bin/phpunit --testsuite pbt`，确保所有 PBT 通过。Commit。

- [~] 14. 覆盖率目标验证
  - [ ] 14.1 更新 `tests/run_all_coverage.sh` 覆盖率合并脚本
    - 适配 PHPUnit 13 覆盖率 API
    - 添加 `pbt` 测试套件到覆盖率收集流程
    - 更新 PHP 二进制路径（从 `php74` 改为当前 PHP 8.5 路径）
    - Ref: Req 8, AC 4
  - [ ] 14.2 验证综合覆盖率达到 90%+
    - 运行全量覆盖率脚本
    - 确认排除 `InitializeProjectCommand` 和 `src/tests/` 后，ut + pbt + integration 综合覆盖率 ≥ 90%
    - 如未达标，补充测试用例
    - Ref: Req 8, AC 1–3, 5
  - [ ] 14.3 Checkpoint: 运行全量测试套件（ut + pbt + integration），确保全部通过。确认覆盖率达标。Commit。

- [ ] 15. 文档更新
  - [ ] 15.1 更新 `docs/state/architecture.md`
    - HTTP Kernel 段落：SilexKernel → MicroKernel
    - DI 容器段落：移除"所有服务设为 public"，改为"默认 private，`app` 服务保持 public"
    - Daemon Sentinel 段落：移除 AbstractDaemonSentinelCommand 引用，DaemonSentinelCommand 直接继承 AbstractAlertableCommand
    - Ref: Req 10, AC 1
  - [ ] 15.2 更新 `docs/state/cli-commands.md`
    - Command 基类体系图：移除 AbstractDaemonSentinelCommand 层级
    - ValidateServicesCommand 说明更新为"验证所有 public 服务"
    - Ref: Req 10, AC 2
  - [ ] 15.3 更新 `docs/state/configuration.md`
    - DI 可见性变更说明：服务默认 private，需要通过 `getService()` 获取的服务须在 `services.yml` 中声明 `public: true`
    - Ref: Req 10, AC 3
  - [ ] 15.4 更新 `PROJECT.md`
    - 技术栈更新：PHP >=8.5、Symfony ^8.0、PHPUnit ^13、oasis 上游库版本
    - 开发依赖更新：Doctrine ORM ^3.6、Eris ^1.1
    - 目录结构：移除 AbstractDaemonSentinelCommand，添加 ConfigParser、NamespaceResolver、tests/pbt/
    - Ref: Req 10, AC 4
  - [ ] 15.5 更新 `README.md`
    - PHP 版本要求更新
    - 主要依赖版本更新
    - Ref: Req 10, AC 5
  - [ ] 15.6 Checkpoint: Review 所有文档变更，确认内容准确。Commit。

- [ ] 16. 迁移指南
  - [ ] 16.1 创建 `docs/manual/migration-v2-to-v3.md`
    - 依赖变更清单（表格：依赖名 | 2.x 版本 | 3.0 版本）
    - Breaking Change 1: PHP 版本要求（>=7.0 → >=8.5）
    - Breaking Change 2: HTTP Kernel 变更（`getHttpKernel()` 返回类型从 `SilexKernel` 改为 `MicroKernel`，使用方代码中的类型提示需更新）
    - Breaking Change 3: DI 容器可见性变更（服务默认 private，`getService()` 仅适用于 public 服务，推荐构造函数注入）
    - Breaking Change 4: AbstractDaemonSentinelCommand 移除（迁移路径：直接使用或继承 DaemonSentinelCommand）
    - Breaking Change 5: PHPUnit 升级（基类、断言方法、Mock API 变更清单）
    - `app` 服务保持 public，但建议迁移到构造函数注入
    - 升级步骤清单（有序列表）
    - Ref: Req 11, AC 1–8
  - [ ] 16.2 Checkpoint: Review 迁移指南内容完整性和准确性。Commit。

- [ ] 17. 手工测试
  - [ ] 17.1 Increment alpha tag
  - [ ] 17.2 验证 CLI 模式基本功能
    - [ ] 执行 `slimapp:cache:clear`，确认缓存目录被正确清除
    - [ ] 执行 `slimapp:services:validate`，确认仅验证 public 服务且输出正确
  - [ ] 17.3 验证 HTTP Kernel 初始化
    - [ ] 调用 `getHttpKernel()` 确认返回 MicroKernel 实例
    - [ ] 确认 MicroKernel 缓存目录获取的容错逻辑正常工作
  - [ ] 17.4 验证 DI 容器可见性变更
    - [ ] 确认 `getService('app')` 正常返回 SlimApp 实例
    - [ ] 确认 `getService()` 调用非 public 服务抛出 `ServiceNotFoundException`
  - [ ] 17.5 验证 Daemon Sentinel 基本功能
    - [ ] 使用测试配置文件执行 DaemonSentinelCommand，确认进程 fork 和调度正常
  - [ ] 17.6 Checkpoint: 汇总手工测试结果，确认所有场景通过。Commit。

- [ ] 18. Code Review
  - 委托给 code-reviewer sub-agent 执行。

## Issues

（stabilize 阶段新发现的 issue 记录于此，初始为空）

## Notes

- 按 spec-execution 规范执行，commit 随 checkpoint 一起执行
- Task 排序遵循 Proposal Phase 顺序：依赖升级 → 按模块语法升级 → 集成测试 → PBT → 覆盖率 → 文档 → 手工测试 → Code Review
- AbstractAlertableCommand（Task 4）必须在 DaemonSentinelCommand 重构（Task 5）之前完成，因为 DaemonSentinelCommand 将改为直接继承 AbstractAlertableCommand，父类方法签名需先适配 Symfony 8.0
- 每个 task 引用了具体的 Requirements 条款，执行时可参照 requirements.md 和 design.md 中对应的 section
- PBT 使用 `giorgiosironi/eris` ^1.1，每个 property test 最小迭代 100 次
- 覆盖率计算排除 `InitializeProjectCommand` 和 `src/tests/`，目标 90%+
- 此为 release spec，手工测试 task（Task 17）遵循 release stabilize 流程，首个 sub-task 为 increment alpha tag

## Socratic Review

### tasks 是否完整覆盖了 design 中的所有实现项？

是。Design 中的 11 个组件（SlimApp、SlimAppCompilerPass、DaemonSentinelCommand、ConsoleApplication、ClearCacheCommand、CommandConfiguration、CommandRunner、AbstractAlertableCommand、AbstractParallelCommand、ValidateServicesCommand、PHPUnit 配置）均有对应 task。新增的 ConfigParser 和 NamespaceResolver 分别合并在 SlimApp（Task 2）和 SlimAppCompilerPass（Task 3）的 task 中，符合 design CR Q1 的决策。集成测试（Task 12）、PBT（Task 13）、覆盖率（Task 14）、文档（Task 15-16）均有对应 task。

### task 之间的依赖顺序是否正确？

是。Task 1（Composer 依赖升级）为所有后续 task 的前置条件。Task 4（AbstractAlertableCommand 升级）排在 Task 5（DaemonSentinelCommand 重构）之前，因为 DaemonSentinelCommand 将改为直接继承 AbstractAlertableCommand，父类需先完成 PHP 8.5 语法适配。Task 2-10 的模块间无强依赖（各模块独立升级），但 Task 11（PHPUnit 配置）放在所有模块升级之后、全量测试之前。Task 12（集成测试）依赖所有源码升级完成。Task 13（PBT）依赖 ConfigParser 和 NamespaceResolver 已提取（Task 2-3）。Task 14（覆盖率）依赖所有测试就绪。Task 15-16（文档）放在代码变更之后，符合 design CR Q4 的决策。

### 每个 task 的粒度是否合适？

是。每个 sub-task 聚焦单个文件或紧密相关的一组文件，可在独立 session 中执行。无过粗的 task（每个 sub-task 只做一件事），也无过细的 task（如单独一个 sub-task 只改一行 import）。

### checkpoint 的设置是否覆盖了关键阶段？

是。每个 top-level task 的最后一个 sub-task 为 checkpoint，包含具体的验证命令和 commit 动作。关键里程碑：Task 1（依赖升级）、Task 11（单元测试全量通过）、Task 12（集成测试通过）、Task 14（覆盖率达标）均有 checkpoint。

### 手工测试是否覆盖了 requirements 中的关键用户场景？

是。手工测试覆盖了 CLI 命令执行（Req 3, 4）、HTTP Kernel 初始化（Req 3）、DI 容器可见性变更（Req 4）、Daemon Sentinel 基本功能（Req 5）等关键场景。

## Gatekeep Log

**校验时间**: 2025-07-14
**校验结果**: ⚠️ 已修正后通过

### 修正项
- [结构] Checkpoint 从独立 top-level task（原 Task 2, 13, 15, 18, 21）改为各 top-level task 的最后一个 sub-task，每个 checkpoint 包含具体验证命令和 commit 动作
- [结构] 补充了缺失的手工测试 top-level task（Task 17），覆盖 CLI 命令、HTTP Kernel、DI 可见性、Daemon Sentinel 等关键场景；首个 sub-task 为 "Increment alpha tag"（release spec 要求）
- [结构] 补充了缺失的 Code Review top-level task（Task 18），作为最后一个 top-level task
- [结构] 补充了缺失的 `## Issues` section（release spec 要求）
- [结构] 补充了缺失的 `## Socratic Review` section
- [依赖] 将 AbstractAlertableCommand + AbstractParallelCommand 语法升级（原 Task 10）提前至 Task 4，排在 DaemonSentinelCommand 重构（Task 5）之前——因为 DaemonSentinelCommand 将改为直接继承 AbstractAlertableCommand，父类方法签名需先适配 Symfony 8.0（graphify 确认 AbstractAlertableCommand → DaemonSentinelCommand 继承关系）
- [格式] Requirement 引用格式从 `_Requirements: X.Y, ..._` 统一为 `Ref: Req X, AC Y` 格式
- [格式] 移除所有 `*` optional 标记（Task 3.5→2.5, 4.4→3.4, 16.2-16.6→13.2-13.6），所有 task 均为 mandatory
- [内容] Notes section 补充了 spec-execution 规范引用、commit 时机说明、AbstractAlertableCommand 依赖说明等执行要点
- [内容] 全文重新编号（原 21 个 top-level task 整合为 18 个）

### 合规检查
- [x] 无 TBD / TODO / 待定 / 占位符
- [x] 无空 section 或不完整的列表
- [x] 内部引用一致（requirement 编号、design 中的模块名）
- [x] checkbox 语法正确（`- [ ]`）
- [x] 无 markdown 格式错误
- [x] `## Tasks` section 存在
- [x] Release spec 手工测试 top-level task 的第一个 sub-task 是 "Increment alpha tag"
- [x] 最后一个 top-level task 是 Code Review（Task 18）
- [x] 倒数第二个 top-level task 是手工测试（Task 17）
- [x] 自动化实现 task 排在手工测试和 Code Review 之前
- [x] 所有 task 使用 `- [ ]` checkbox 语法
- [x] top-level task 有序号，sub-task 有层级序号，序号连续无跳号
- [x] 每个实现类 sub-task 引用了具体的 requirements 条款（`Ref: Req X, AC Y` 格式）
- [x] requirements.md 中的每条 requirement 至少被一个 task 引用（11/11 全覆盖）
- [x] 引用的 requirement 编号和 AC 编号在 requirements.md 中确实存在
- [x] top-level task 按依赖关系排序（AbstractAlertableCommand 在 DaemonSentinelCommand 之前）
- [x] 无循环依赖
- [x] 已对核心模块执行 graphify 依赖查询（AbstractAlertableCommand、SlimAppCompilerPass、ConsoleApplication、SlimApp、AbstractDaemonSentinelCommand）
- [x] task 排序与 graphify 揭示的模块依赖一致
- [x] checkpoint 作为每个 top-level task 的最后一个 sub-task
- [x] checkpoint 描述中包含具体的验证命令和 commit 动作
- [x] 每个 sub-task 足够具体，可在独立 session 中执行
- [x] 无过粗或过细的 task
- [x] 所有 task 均为 mandatory（无 optional task）
- [x] 手工测试 top-level task 存在，覆盖关键用户场景
- [x] Code Review 是最后一个 top-level task，描述为委托给 code-reviewer sub-agent
- [x] `## Notes` section 存在，引用了 spec-execution 规范，说明了 commit 时机
- [x] `## Socratic Review` section 存在且覆盖充分
- [x] Design CR 决策已在 tasks 编排中体现（Q1 提取类合并到对应模块 task、Q2 Phase 顺序、Q3 集成测试独立 task、Q4 文档作为收尾 task）
- [x] Design 全覆盖（所有模块、接口、实现项均有对应 task）
- [x] 每个 sub-task 可独立执行
- [x] checkpoint + 手工测试 + code review 构成完整验收闭环
- [x] 执行路径无歧义
