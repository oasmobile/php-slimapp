---
id: bug-GH7A
type: bug
status: open
severity: major
found_in: 3.2.1
---

# 生成的 PHPUnit bootstrap 传入旧整数日志级别

## 观察到的行为

静态审查发现生成模板遗漏日志级别枚举适配，审查优先级为 P1；尚未运行复现测试。

- `src/BuiltInCommands/InitializeProjectCommand.php:830` 生成 `MLogging::setMinLogLevel(Logger::CRITICAL)`。
- `Logger::CRITICAL` 为整数，当前 `MLogging::setMinLogLevel()` 参数要求 `Monolog\Level`。
- 默认参数触发该分支，PHP 会在测试 bootstrap 阶段抛出 `TypeError`。

## 期望行为

生成项目的 PHPUnit bootstrap 使用当前日志 API 支持的类型，默认测试命令能执行到测试用例。

## 复现步骤

以下步骤作为后续复现测试的设计输入，尚未执行。

1. 在隔离的临时目录生成启用 PHPUnit 支持的项目，并使用当前锁定的依赖。
2. 添加一个无业务依赖的最小通过用例，使用默认参数启动 PHPUnit，确保没有 `-v` 或 `--verbose`。
3. 断言进程成功并执行该用例，记录 bootstrap 阶段的实际输出和退出码。

## 影响

使用该模板生成的新项目无法按默认方式启动测试，失败发生在测试用例执行之前。
当前仓库自己的 `tests/bootstrap.php` 已使用枚举，不受这处模板错误影响。

## 所需回归证据

回归必须加载实际生成的 bootstrap，并隔离其它生成器问题。

- 修复前：出现指向 `setMinLogLevel()` 参数类型的 `TypeError`，最小用例未执行。
- 修复后：同一命令成功执行最小用例，bootstrap 保留预期日志级别。
- 版本依据：当前运行代码与 `v3.2.1` 一致；尚未定位最早引入此问题的提交。

## 执行约束

用户指定分阶段 TDD，由人工确认红灯并启动修复。

1. 后续仅编写能复现本 Bug 的测试，不修改生产代码，不自动运行测试。
2. 由人工运行测试，确认失败源于本 Bug，并保存命令、日志及测试报告。
3. 等待人工明确启动 Bug 修复流程后，再修改实现并运行回归验证。

复现测试已编写：`tests/ut/Regression/BugGH7ATest.php`，包含 1 个场景。
测试使用生成的 bootstrap 启动最小 PHPUnit 用例；当前尚未运行，等待人工确认红灯。
统一运行与交接见 [复现测试交接](../../changes/unreleased/v3-bug-reproduction-tests/HANDOFF.md)。
