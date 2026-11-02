---
title: "测试约定"
doc_type: system-testing
evidence:
  - path: "src/BuiltInCommands/Templates/UnitTestTemplates.php"
  - path: "tests/bootstrap.php"
  - path: "tests/integration/bootstrap.php"
  - path: "tests/integration/config/config.yml"
  - path: "tests/integration/config/routes.yml"
  - path: "tests/integration/config/sentinel.yml"
  - path: "tests/integration/config/services.yml"
  - path: "tests/integration/console.php"
  - path: "tests/integration/fixtures/DummyCommand.php"
  - path: "tests/integration/fixtures/TestAppConfig.php"
  - path: "tests/integration/fixtures/TestController.php"
  - path: "tests/integration/fixtures/TestSentinelCommand.php"
  - path: "tests/integration/http.php"
  - path: "tests/pbt/CommandConfigurationPbtTest.php"
  - path: "tests/pbt/CommandRunnerSchedulingPbtTest.php"
  - path: "tests/pbt/ConfigParserPbtTest.php"
  - path: "tests/pbt/NamespaceResolverPbtTest.php"
  - path: "tests/pbt/VerbosityMappingPbtTest.php"
  - path: "tests/run_all_coverage.sh"
  - path: "tests/scripts/merge_coverage.php"
  - path: "tests/scripts/parallel_command_test.php"
  - path: "tests/scripts/sentinel_command_test.php"
  - path: "tests/ut/AbstractAlertableCommandTest.php"
  - path: "tests/ut/AbstractParallelCommandPcntlTest.php"
  - path: "tests/ut/AbstractParallelCommandTest.php"
  - path: "tests/ut/BuiltInCommands/ClearCacheCommandTest.php"
  - path: "tests/ut/BuiltInCommands/InitializeProjectCommandTest.php"
  - path: "tests/ut/BuiltInCommands/ValidateServicesCommandTest.php"
  - path: "tests/ut/CommandConfigurationTest.php"
  - path: "tests/ut/CommandRunnerPcntlTest.php"
  - path: "tests/ut/CommandRunnerTest.php"
  - path: "tests/ut/ConfigParserTest.php"
  - path: "tests/ut/ConsoleApplicationTest.php"
  - path: "tests/ut/Fixtures/ConcreteParallelCommand.php"
  - path: "tests/ut/ForkProcessTest.php"
  - path: "tests/ut/Regression/Bug2AN6Test.php"
  - path: "tests/ut/Regression/BugGH7ATest.php"
  - path: "tests/ut/Regression/BugY68QTest.php"
  - path: "tests/ut/Regression/BugP4KUTest.php"
  - path: "tests/ut/Regression/Bug1MW9Test.php"
  - path: "tests/ut/NamespaceResolverTest.php"
  - path: "tests/ut/SentinelCommand/DaemonSentinelCommandPcntlTest.php"
  - path: "tests/ut/SentinelCommand/DaemonSentinelCommandTest.php"
  - path: "tests/ut/SlimAppCompilerPassTest.php"
  - path: "tests/ut/SlimAppTest.php"
  - path: "phpunit.xml"
  - path: "composer.json"
  - path: ".mdf/modules.yaml"
---

# 测试约定

本页定义本项目的自动测试成员、运行前提和失败语义。

凭据 fixture 只核对加载关系；配置值不进入事实正文与审阅范围。

## 测试分类

自动测试由 PHPUnit 13 运行，PT 使用 Eris。

| 类别 | 目录与作用 |
| --- | --- |
| UT | tests/ut；含内存测试、文件系统测试及 pcntl 子进程测试 |
| PT | tests/pbt；配置、解析、调度和 verbosity 的性质测试 |
| 人工集成材料 | tests/integration；HTTP/Console 入口与 fixture，不自动纳入套件 |
| 辅助脚本 | tests/scripts 与 run_all_coverage.sh；子进程覆盖率采集与合并 |

V3 升级 Bug 的复现测试位于 `tests/ut/Regression/`，随 ut 纳入 smoke/release，不进入 quick。
其 fixture 使用隔离临时目录，子进程输出和命令保存在 `.mdf/reports/v3-bug-repro-*`。

## 失败语义与依赖

运行器错误和报告均属于验收依据，不能只看终端摘要。

- `failOnAllIssues`、`failOnEmptyTestSuite`、`failOnSkipped`、`failOnIncomplete` 均启用。
- 缺少 pcntl 时，独立 PcntlTest 类的 setUp 失败，不运行时跳过。
- pcntl 方法从原类移入独立类；原断言、子进程等待和文件清理保留。
- 三个 PcntlTest 共包含 14 个原测试方法，消除 13 处 runtime skip。
- 第三方 warning/notice/deprecation 没有额外豁免。
- `tests/run_all_coverage.sh` 保留非预期子命令失败状态与错误输出；它没有 JUnit，仍为辅助覆盖率入口。
- ForkProcessTest 普通运行不启用子进程覆盖率；`COVERAGE_FILE` 的值按 PHP 布尔规则为真时才请求采集。
- 预期业务退出 255 仍须排除 `Fatal error` 和 `Uncaught`，不能只检查退出码。
- 无覆盖率驱动回归使用专属空目录隔离 INI 扫描，避免重复加载扩展污染子进程输出。

## Quick

quick 只运行七个纯内存测试类，预算 30 秒。

```bash
vendor/bin/phpunit --testsuite quick --log-junit "$MDF_REPORT_DIR/junit.xml"
```

- UT：ConfigParserTest、NamespaceResolverTest、CommandConfigurationTest、SlimAppCompilerPassTest。
- PT：ConfigParserPbtTest、NamespaceResolverPbtTest、CommandConfigurationPbtTest。
- 精确文件列表同时写在 phpunit.xml 与 `.mdf/modules.yaml`。

## Smoke

smoke 包含 quick 和全部原 ut/pbt 成员，预算 300 秒，需要 pcntl 与临时目录写权限。

```bash
vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"
```

## Release

release 目前与 smoke 成员相同，不设置总耗时上限。

```bash
vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"
```

目前没有额外的自动发布级套件；不得将人工集成入口声称为已自动验证。

## 定点运行与报告

测试类对应 JUnit testcase 的 classname；单测名称保留在 name 字段。

```bash
vendor/bin/phpunit --filter 'ConfigParserTest::test方法名' --log-junit "$MDF_REPORT_DIR/junit.xml"
```

独立运行先设置并创建 `MDF_REPORT_DIR`；MDF verify 自动完成这些准备。

## 工程生成器人工验证

`init-ut/` 使用独立 Composer 配置，经 path/symlink 引用当前框架。

1. 在 init-ut 安装该工程自己的依赖。
2. 交互运行 `php vendor/bin/slimapp slimapp:project:init --project-root=.`。
3. 检查生成的配置模板、入口、PHPUnit schema 和 PHP 语法。
4. 启用数据库支持时，另按[ORM 迁移](../../user-guide/migration-orm.md)核对数据库适配。

生成的 `ut/bootstrap.php` 安装 ConsoleHandler；未传 `-v` 或 `--verbose` 时，以 `Level::Critical` 设置最低日志级别。
该流程会生成工程文件，不由初始化验证自动运行；清理前确认只涉及本次生成物。
