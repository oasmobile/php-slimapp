---
version: "3.2.2"
previous_version: "3.2.1"
date: "2026-11-05"
change_kind: release
source_branch: release/3.2.2
proposals: []
fixed: [bug-1MW9, bug-2AN6, bug-GH7A, bug-P4KU, bug-Y68Q]
closed: []
deferred: []
adrs: []
included_changes: [bug-1mw9, mdf-init, v3-bug-reproduction-tests, v3-upgrade-review-bugs]
release_notes:
  Fixed:
    - "修正 PHP 8.5 工程生成器的 Doctrine ORM 工厂和 Monolog 日志级别。"
    - "损坏或非数组配置缓存按既有解析路径重建。"
    - "普通 fork 测试不再强制依赖覆盖率驱动。"
    - "覆盖率脚本保留失败状态，并区分预期业务退出和致命错误。"
breaking: false
evidence:
  tests:
    - "tests/ut/Regression/Bug2AN6Test.php"
    - "tests/ut/Regression/BugGH7ATest.php"
    - "tests/ut/Regression/BugY68QTest.php"
    - "tests/ut/Regression/BugP4KUTest.php"
    - "tests/ut/Regression/Bug1MW9Test.php"
    - "tests/ut/AbstractParallelCommandPcntlTest.php"
    - "tests/ut/CommandRunnerPcntlTest.php"
    - "tests/ut/SentinelCommand/DaemonSentinelCommandPcntlTest.php"
  commands:
    - "python3 -B .agents/skills/mdf/scripts/mdf.py verify --repo . --scope branch"
    - "python3 -B .agents/skills/mdf/scripts/mdf.py verify --repo . --scope named --suites coverage-script-regression"
    - "python3 -B .agents/skills/mdf/scripts/mdf.py validate --repo . --level strict"
    - "vendor/bin/phpunit --testsuite ut,pbt --log-junit <报告目录>/junit.xml"
    - "vendor/bin/phpstan analyse --no-progress --debug"
    - "python3 -B .agents/skills/mdf/scripts/mdf.py validate --repo . --level basic"
    - "git diff --check"
    - "vendor/bin/phpunit --testsuite quick --log-junit \"$MDF_REPORT_DIR/junit.xml\""
    - "vendor/bin/phpunit --testsuite ut,pbt --log-junit \"$MDF_REPORT_DIR/junit.xml\""
  artifacts:
    - "changes/3.2.2/bug-1mw9/code-review.md"
    - "changes/3.2.2/bug-1mw9/verification-report.json"
    - "changes/3.2.2/bug-1mw9/verification-report.md"
    - "changes/3.2.2/bug-1mw9/fact-audit.md"
    - "changes/3.2.2/bug-1mw9/integration-sources.json"
    - "changes/3.2.2/v3-bug-reproduction-tests/HANDOFF.md"
    - "docs/bugs/archive/3.2/bug-2AN6-generated-orm-removed-api.md"
    - "docs/bugs/archive/3.2/bug-GH7A-generated-bootstrap-log-level.md"
    - "docs/bugs/archive/3.2/bug-Y68Q-corrupted-config-cache-recovery.md"
    - "docs/bugs/archive/3.2/bug-P4KU-fork-tests-require-coverage-driver.md"
    - "docs/bugs/archive/3.2/bug-1MW9-coverage-script-masks-test-failures.md"
audit: passed
---

# Release 3.2.2

## 结果

发布收口已完成。

## 包含的 Change

- [bug-1mw9](bug-1mw9/CHANGE.md)
- [mdf-init](mdf-init/CHANGE.md)
- [v3-bug-reproduction-tests](v3-bug-reproduction-tests/CHANGE.md)
- [v3-upgrade-review-bugs](v3-upgrade-review-bugs/CHANGE.md)

## 已更新的当前文档

已生成 CHANGELOG.md 与版本根目录中的 CHANGE.md。

## 已知偏差

无。

## 收口结果

### Proposal

无。

### 已关闭的 Proposal

无。

### 已修复的 Bug

- `bug-1MW9`
- `bug-2AN6`
- `bug-GH7A`
- `bug-P4KU`
- `bug-Y68Q`

### 已关闭的 Bug

无。

### 延后的 Bug

无。

## found-in 转换

None.

## 延后接受理由

None.

## SemVer 决策

- 观察到的类别：Fixed
- 破坏性变更：否
- 最低升级幅度：patch
- 实际升级幅度：patch
- 选定版本：`3.2.2`

## 审计

- 确定性的全量审计：已通过（由 Core 验证）。
- 验证命令：
  - `vendor/bin/phpstan analyse --no-progress --debug` → exit 0
  - `git diff --check` → exit 0
  - `vendor/bin/phpunit --testsuite quick --log-junit "$MDF_REPORT_DIR/junit.xml"` → exit 0
  - `vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"` → exit 0

## 验证命令

```text
vendor/bin/phpstan analyse --no-progress --debug
git diff --check
vendor/bin/phpunit --testsuite quick --log-junit "$MDF_REPORT_DIR/junit.xml"
vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"
```
