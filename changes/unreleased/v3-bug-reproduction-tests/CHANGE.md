---
change_kind: fix
source_branch: develop
proposals: []
fixed: []
closed: []
deferred: [bug-2AN6, bug-GH7A, bug-Y68Q, bug-P4KU, bug-1MW9]
adrs: []
release_notes: none
breaking: false
evidence:
  tests:
    - tests/ut/Regression/Bug2AN6Test.php
    - tests/ut/Regression/BugGH7ATest.php
    - tests/ut/Regression/BugY68QTest.php
    - tests/ut/Regression/BugP4KUTest.php
    - tests/ut/Regression/Bug1MW9Test.php
  commands:
    - python3 -B .agents/skills/mdf/scripts/mdf.py validate --repo . --level basic
    - git diff --check
  artifacts:
    - changes/unreleased/v3-bug-reproduction-tests/HANDOFF.md
---

# V3 升级 Bug 复现测试

## 结果

按用户要求，连续为五项 Bug 编写复现测试，共 16 个场景；保持实现和原测试工具不变。
测试使用现有 PHPUnit、Console Tester 和 Filesystem，不新增依赖。

- bug-2AN6：实际生成 ORM 工厂，验证 EntityManager 创建。
- bug-GH7A：实际生成 PHPUnit bootstrap，启动最小用例。
- bug-Y68Q：正常、截断、标量和 false 配置缓存。
- bug-P4KU：无覆盖率驱动时的四个原进程测试，额外排除预期失败用例的假通过。
- bug-1MW9：成功对照，以及 PHPUnit、parallel 和 sentinel 的非预期失败。

## 已更新的当前文档

测试约定增加复现测试的分类入口；五份 Bug 保留 open，并记录测试路径和人工执行门槛。

## 已知偏差

本阶段只完成测试编写和静态检查，尚未执行测试，不能宣称已复现或已验证通过。
人工执行和现象确认后，仍须由人工明确启动修复，不能自动进入实现阶段。
运行命令、判定依据及日志位置见 [交接说明](HANDOFF.md)。
