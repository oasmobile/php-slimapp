---
id: bug-GH7A
type: bug
status: closed
severity: major
found_in: 3.2.1
fixed_in: 3.2.2
---

# 生成的 PHPUnit bootstrap 传入旧整数日志级别

## 观察到的行为

静态审查发现生成模板遗漏日志级别枚举适配，审查优先级为 P1；现已按授权运行复现并完成修复。

- `src/BuiltInCommands/InitializeProjectCommand.php:830` 生成 `MLogging::setMinLogLevel(Logger::CRITICAL)`。
- `Logger::CRITICAL` 为整数，当前 `MLogging::setMinLogLevel()` 参数要求 `Monolog\Level`。
- 默认参数触发该分支，PHP 会在测试 bootstrap 阶段抛出 `TypeError`。

## 期望行为

生成项目的 PHPUnit bootstrap 使用当前日志 API 支持的类型，默认测试命令能执行到测试用例。

## 复现步骤

以下步骤保留修复前的复现条件；实际执行证据见下方记录。

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

## 原始执行约束

用户最初指定分阶段 TDD；本次执行授权及结果见下方记录。

1. 后续仅编写能复现本 Bug 的测试，不修改生产代码，不自动运行测试。
2. 由人工运行测试，确认失败源于本 Bug，并保存命令、日志及测试报告。
3. 等待人工明确启动 Bug 修复流程后，再修改实现并运行回归验证。

复现测试已编写：`tests/ut/Regression/BugGH7ATest.php`，包含 1 个场景。
测试使用生成的 bootstrap 启动最小 PHPUnit 用例；已按本次授权执行，红灯与转绿证据见下方记录。
统一运行与交接见 [复现测试交接](../../../../changes/3.2.2/v3-bug-reproduction-tests/HANDOFF.md)。

## 修复与验证记录

用户已于 2026-10-31 明确授权 Agent 执行复现、修复、回归与独立审查。
原人工执行约束已由本次授权调整，先确认有效红灯，再修改实现，未削弱原缺陷断言。

- 对应正式复现用例已确认红灯并转绿；报告见 `changes/unreleased/bug-gh7a/repair-evidence.md`。
- smart 的 lint、build、quick 通过；独立 lint 通过，记录见同目录阶段报告。
- 独立静态审查已覆盖本轮完整范围，无未解决项；结论见同目录 `code-review.md`。
- 状态仅为 fixed，等待后续整体验收与二次验证；未填写 fixed_in，未关闭 Bug。

该结论只适用于当前独立修复分支；尚未合入 develop，也未宣称其它已知缺陷已经消除。
