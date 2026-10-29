---
change_kind: fix
source_branch: develop
proposals: []
fixed: []
closed: []
deferred:
  - bug-2AN6
  - bug-GH7A
  - bug-Y68Q
  - bug-P4KU
  - bug-1MW9
adrs: []
release_notes: none
breaking: false
evidence:
  tests: []
  commands:
    - python3 -B .agents/skills/mdf/scripts/mdf.py validate --repo . --level basic
    - git diff --check
  artifacts:
    - docs/bugs/bug-2AN6-generated-orm-removed-api.md
    - docs/bugs/bug-GH7A-generated-bootstrap-log-level.md
    - docs/bugs/bug-Y68Q-corrupted-config-cache-recovery.md
    - docs/bugs/bug-P4KU-fork-tests-require-coverage-driver.md
    - docs/bugs/bug-1MW9-coverage-script-masks-test-failures.md
---

# V3 升级审查问题登记

## 结果

按用户要求，将 V3 升级静态审查发现的五项问题登记为 open Bug。

| Bug | 审查优先级 | 主题 |
| --- | --- | --- |
| bug-2AN6 | P1 | ORM 生成模板调用已移除的 API |
| bug-GH7A | P1 | 测试 bootstrap 生成模板传入整数日志级别 |
| bug-Y68Q | P2 | 损坏配置缓存无法进入重建分支 |
| bug-P4KU | P2 | 普通进程测试依赖覆盖率驱动 |
| bug-1MW9 | P2 | 覆盖率脚本吞掉测试失败状态 |

审查以 `v2.6.3` 为基线，核对当前运行代码与 `v3.2.1` 一致。
各 Bug 的 `found_in` 记录为 `3.2.1`，不代表已经定位首次引入版本。
MDF severity 均为 major，表示功能或验证可靠性受影响，不等同于审查优先级。

## 已更新的当前文档

本次仅新增 Bug 工作记录，不修改当前行为事实页、实现或测试。

## 已知偏差

五项均有静态证据，但尚未通过执行测试复现，不宣称已完成红灯验证。

1. 后续先编写复现测试，不修改实现，不自动运行测试。
2. 由人工运行并确认 Bug 现象，保存命令、日志和报告。
3. 由人工明确启动修复流程，再修改实现并执行回归。

本次登记不启动测试编写或修复，五项均保留 open 状态。
