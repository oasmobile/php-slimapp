# 3.2.2 Bug 独立关闭记录

## 证据复用依据

本页记录逐项复现验证和修复审查；本轮没有修改实现、测试或验证配置。

- 验证报告：`verification-report.json`，all_passed 为 true，release 命令退出 0。
- 命令：`vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"`。
- 原始逐例报告：`.mdf/reports/20261105T081432022548000Z-release/summary.json`。
- 从验证 HEAD 到各记录 HEAD，非 docs/changes 路径无变化。
- 审查按含完整 Bug ID 的实际修复提交逐块进行；模板提取和 merge 不当作额外业务修复。

## bug-2AN6

本项复现通过，主 Agent 已独立审查对应修复。

- HEAD：`fe7382e53bd23c6c4dadbb598338362e2c62a6af`。
- 审查路径：`src/BuiltInCommands/Templates/DatabaseTemplates.php`。
- 修复提交：`3b1dd37150943806829160867a8ca76670a31d34`。
- 结果：1 个复现场景 passed；复用退出 0 的 release 报告。
- `Bug2AN6Test::testGeneratedOrmFactoryCreatesAnEntityManager`：passed。

ORM 工厂移除旧 API，使用 DriverManager 和 EntityManager 构造器，并启用 PHP 原生 lazy objects。真实生成工厂创建 EntityManager；不连接真实数据库。

无未解决问题，允许关闭并写入 fixed_in: 3.2.2。

## bug-GH7A

本项复现通过，主 Agent 已独立审查对应修复。

- HEAD：`5a17024ddbc25795ce65fa1226faedc6d01b069d`。
- 审查路径：`src/BuiltInCommands/Templates/UnitTestTemplates.php`。
- 修复提交：`dfb5027f4ad21c9e58077c0912acd9bb44c92725`。
- 结果：1 个复现场景 passed；复用退出 0 的 release 报告。
- `BugGH7ATest::testGeneratedBootstrapCanRunAMinimalTest`：passed。

默认 bootstrap 将整数级别改为 Level::Critical，匹配锁定日志 API。生成 bootstrap 已执行最小用例。

无未解决问题，允许关闭并写入 fixed_in: 3.2.2。

## bug-Y68Q

本项复现通过，主 Agent 已独立审查对应修复。

- HEAD：`8129c59928823689d535fc6dc43923ee7f6215b8`。
- 审查路径：`src/SlimApp.php`。
- 修复提交：`bded35fef6807578e0ac327b9ac213dd5b677081`。
- 结果：4 个复现场景 passed；复用退出 0 的 release 报告。
- `BugY68QTest::testConfigurationRemainsAvailable with data set "正常缓存对照"`：passed。
- `BugY68QTest::testConfigurationRemainsAvailable with data set "截断缓存"`：passed。
- `BugY68QTest::testConfigurationRemainsAvailable with data set "标量缓存"`：passed。
- `BugY68QTest::testConfigurationRemainsAvailable with data set "false缓存"`：passed。

反序列化结果先检查数组类型，非法值回到已有配置重建路径。四场景覆盖合法缓存、截断、标量、false。

无未解决问题，允许关闭并写入 fixed_in: 3.2.2。

## bug-P4KU

本项复现通过，主 Agent 已独立审查对应修复。

- HEAD：`03a426a9c32b6fdb17a21f45dfe195dedc192b5a`。
- 审查路径：`tests/ut/ForkProcessTest.php、tests/ut/Regression/BugP4KUTest.php`。
- 修复提交：`6e434f178cb1ec90b94cf317787bd0a7b499060f`, `6eedd33760c6c6e47c40b3378cd301c4aabce0b8`。
- 结果：4 个复现场景 passed；复用退出 0 的 release 报告。
- `BugP4KUTest::testOrdinaryForkTestNeedsNoCoverageDriver with data set "parallel_ok"`：passed。
- `BugP4KUTest::testOrdinaryForkTestNeedsNoCoverageDriver with data set "parallel_fail"`：passed。
- `BugP4KUTest::testOrdinaryForkTestNeedsNoCoverageDriver with data set "sentinel_once"`：passed。
- `BugP4KUTest::testOrdinaryForkTestNeedsNoCoverageDriver with data set "sentinel_parallel"`：passed。

普通 fork 仅在显式请求时设置 COVERAGE_FILE；预期 255 额外排除 fatal/uncaught。复现环境使用真实空 INI 扫描目录，未削弱断言。显式覆盖率历史证据见 ../bug-1mw9/source-deliveries/bug-p4ku/converge-report.md；四份产物已成功反序列化。

无未解决问题，允许关闭并写入 fixed_in: 3.2.2。

## bug-1MW9

本项复现通过，主 Agent 已独立审查对应修复。

- HEAD：`a26bf64e1fac5762700e4b2127d1aaffdcd68bf7`。
- 审查路径：`tests/run_all_coverage.sh`。
- 修复提交：`26df9b5aa58667e01095d98b07a8626f77114aaf`。
- 结果：6 个复现场景 passed；复用退出 0 的 release 报告。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "成功及预期业务失败对照"`：passed。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "PHPUnit失败"`：passed。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "parallel异常"`：passed。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "parallel_fail非预期错误"`：passed。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "sentinel_once异常"`：passed。
- `Bug1MW9Test::testCoverageScriptPreservesUnexpectedFailures with data set "sentinel_parallel异常"`：passed。

保留各阶段输出和累计失败状态，区分 parallel_fail 预期 255 与致命异常，检查覆盖率产物并传播合并失败。六场景包含成功对照与五种失败。

无未解决问题，允许关闭并写入 fixed_in: 3.2.2。

