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

