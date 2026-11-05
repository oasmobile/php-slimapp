---
id: bug-2AN6
type: bug
status: closed
severity: major
found_in: 3.2.1
fixed_in: 3.2.2
---

# 生成项目的 ORM 工厂仍调用已移除的 API

## 观察到的行为

静态审查发现生成模板未完成 Doctrine ORM 3 适配，审查优先级为 P1；现已按授权运行复现并完成修复。

- `src/BuiltInCommands/InitializeProjectCommand.php:630` 生成 `Configuration::addEntityNamespace()` 调用。
- 同文件第 634 行生成 `EntityManager::create()` 调用。
- 当前锁定的 Doctrine ORM 3.6.3 已移除上述方法，执行工厂会抛出 `Error`。

## 期望行为

启用 ORM 的生成项目能使用锁定依赖创建 EntityManager，不调用已移除的方法。

## 复现步骤

以下步骤保留修复前的复现条件；实际执行证据见下方记录。

1. 在隔离的临时目录运行项目初始化命令，启用 ORM，并使用当前锁定的依赖。
2. 加载生成的配置类，调用其 EntityManager 工厂；为配置提供临时实体目录和有效连接参数。
3. 断言工厂返回 EntityManager，记录实际异常及堆栈；避免仅检查模板字符串。

## 影响

启用 ORM 的新项目无法创建 EntityManager，依赖该工厂的数据库功能及启动入口会失败。
已有应用仅在保留同类旧 API 调用时受影响；本项不认定所有 V3 应用均无法运行。

## 所需回归证据

回归必须覆盖实际生成代码的加载与工厂调用，而非只检查命令名称和选项。

- 修复前：测试因已移除的 ORM API 调用失败，日志包含准确的异常位置。
- 修复后：相同测试成功创建 EntityManager，且不依赖真实数据库服务。
- 版本依据：当前运行代码与 `v3.2.1` 一致；尚未定位最早引入此问题的提交。

## 原始执行约束

用户最初指定分阶段 TDD；本次执行授权及结果见下方记录。

1. 后续仅编写能复现本 Bug 的测试，不修改生产代码，不自动运行测试。
2. 由人工运行测试，确认失败源于本 Bug，并保存命令、日志及测试报告。
3. 等待人工明确启动 Bug 修复流程后，再修改实现并运行回归验证。

复现测试已编写：`tests/ut/Regression/Bug2AN6Test.php`，包含 1 个场景。
测试执行真实生成的 ORM 工厂，并隔离外部服务；已按本次授权执行，红灯与转绿证据见下方记录。
统一运行与交接见 [复现测试交接](../../../../changes/3.2.2/v3-bug-reproduction-tests/HANDOFF.md)。

## 修复与验证记录

用户已于 2026-10-31 明确授权 Agent 执行复现、修复、回归与独立审查。
原人工执行约束已由本次授权调整，先确认有效红灯，再修改实现，未削弱原缺陷断言。

- 对应正式复现用例已确认红灯并转绿；报告见 `changes/unreleased/bug-2an6/repair-evidence.md`。
- smart 的 lint、build、quick 通过；独立 lint 通过，记录见同目录阶段报告。
- 独立静态审查已覆盖本轮完整范围，无未解决项；结论见同目录 `code-review.md`。
- 状态仅为 fixed，等待后续整体验收与二次验证；未填写 fixed_in，未关闭 Bug。

该结论只适用于当前独立修复分支；尚未合入 develop，也未宣称其它已知缺陷已经消除。
