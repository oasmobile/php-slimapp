---
change_kind: bugfix
source_branch: bugfix/bug-1MW9
proposals: []
fixed: [bug-2AN6, bug-GH7A, bug-Y68Q, bug-P4KU, bug-1MW9]
closed: []
deferred: []
adrs: []
release_notes:
  Fixed:
    - "修正 PHP 8.5 工程生成器的 Doctrine ORM 工厂和 Monolog 日志级别。"
    - "损坏或非数组配置缓存按既有解析路径重建。"
    - "普通 fork 测试不再强制依赖覆盖率驱动。"
    - "覆盖率脚本保留失败状态，并区分预期业务退出和致命错误。"
breaking: false
evidence:
  tests:
    - tests/ut/Regression/Bug2AN6Test.php
    - tests/ut/Regression/BugGH7ATest.php
    - tests/ut/Regression/BugY68QTest.php
    - tests/ut/Regression/BugP4KUTest.php
    - tests/ut/Regression/Bug1MW9Test.php
  commands:
    - "python3 -B .agents/skills/mdf/scripts/mdf.py verify --repo . --scope branch"
    - "python3 -B .agents/skills/mdf/scripts/mdf.py verify --repo . --scope named --suites coverage-script-regression"
    - "python3 -B .agents/skills/mdf/scripts/mdf.py validate --repo . --level strict"
  artifacts:
    - changes/unreleased/bug-1mw9/code-review.md
    - changes/unreleased/bug-1mw9/verification-report.json
    - changes/unreleased/bug-1mw9/verification-report.md
    - changes/unreleased/bug-1mw9/fact-audit.md
    - changes/unreleased/bug-1mw9/integration-sources.json
---

# V3 升级缺陷修复

## 结果

本分支汇入五项已独立修复的 Bug，并完成统一验收。

| Bug | 结果 |
| --- | --- |
| bug-2AN6 | ORM 模板使用 DBAL 连接、EntityManager 构造和原生 lazy objects |
| bug-GH7A | 生成的单测 bootstrap 使用 Level::Critical |
| bug-Y68Q | 非数组缓存不再直接赋给数组属性，进入既有重建路径 |
| bug-P4KU | 覆盖率显式请求；预期失败测试排除致命错误，回归隔离 INI 扫描 |
| bug-1MW9 | 覆盖率脚本记录失败、保留输出并检查预期退出 |

完整 branch 验证通过：quick 46 tests、1282 assertions；smoke 208 tests、2318 assertions，零跳过。
lint、build、独立审查和事实审计均通过；详情见 [验证报告](verification-report.md)与[事实审计](fact-audit.md)。
本 Change 记录修复结果，Bug 保持 fixed；没有声明独立 bug close 或已发布版本。
用户于 2026-11-02 批准本地 develop 合并；Gitflow 将随后执行，结果以实际命令日志为准。
不推送、不创建 tag、不发版；源 worktree 保留为 detached，另外四条分支和 worktree 保留。

## 已更新的当前文档

本节列出对应行为与结构的事实入口。

- [当前架构](../../../docs/system/architecture/current.md)：模板职责及直接 evidence。
- [缓存数据](../../../docs/system/data/cache.md)：非法缓存重建。
- [测试约定](../../../docs/system/testing/conventions.md)：fork、覆盖率请求和测试隔离。
- [覆盖率脚本回归](../../../docs/system/testing/coverage-script-regression.md)：六场景 named suite。
- [ORM 迁移](../../../docs/user-guide/migration-orm.md)：当前 ORM 工厂 API。
- [V3 迁移](../../../docs/user-guide/migration-v2-to-v3.md)：修正旧限制与拆页链接。
- 其余受影响接口、运维与用户指南的逐页核对见 [事实审计](fact-audit.md)。

## 已知偏差

本轮修复无未解决阻断项；五项 Bug 等待后续版本的独立关闭与发布。
ORM 回归验证工厂可创建对象，不代表已验证使用方真实数据库连接。
覆盖率脚本 named suite 验证真实 shell 编排，PHP 命令替身不证明真实覆盖率数据可合并。
保留来源四条分支及 worktree，便于追溯；本次不代其执行独立收口或清理。
