---
change_kind: feature
source_branch: develop
proposals: []
fixed: []
closed: []
deferred: []
adrs: []
release_notes: none
breaking: false
evidence:
  tests:
    - "tests/ut/AbstractParallelCommandPcntlTest.php"
    - "tests/ut/CommandRunnerPcntlTest.php"
    - "tests/ut/SentinelCommand/DaemonSentinelCommandPcntlTest.php"
  commands:
    - "vendor/bin/phpunit --testsuite ut,pbt --log-junit <报告目录>/junit.xml"
    - "vendor/bin/phpstan analyse --no-progress --debug"
  artifacts: []
---

# MDF 初始化迁移

## 结果

已按用户确认方案建立 MDF 配置与文档布局；状态保持 initializing，等待事实审阅及启用确认。

- 原 state/manual 内容归入 system/user-guide，修正已核实过时陈述。
- 旧工作流原文归档，保留通用安全、Git 和 Graphify 入口。
- 历史版本说明与原 spec/Proposal 保留，不重写历史 tag 或重开历史待办。
- 恢复 lock 指定依赖，新增七类 quick 成员；完整 ut/pbt 仍供 smoke/release 使用。
- 14 个原 pcntl 测试方法归入独立类，去掉 13 处 runtime skip；不删除原测试。
- 初始化不改变框架运行实现或业务数据模型；ORM 生成器限制仅如实记录。

## 已更新的当前文档

- `GLOSSARY.md`、`PROJECT.md`、`docs/README.md`。
- `docs/user-guide/` 与 `docs/system/` 的全部当前主题。

## 已知偏差

ORM 生成模板仍调用已移除 API，详见 `docs/system/deviations.md`；本次不修复该实现。
五个配置验证入口已执行通过；quick 为 46 个测试，smoke/release 各为 192 个测试、2199 个断言。
JUnit XML 的 testcase classname 已核实；完整命令输出与报告保存在 `.mdf/logs/`。
事实审阅修正了 CLI 加载顺序、ORM 映射选择与跨页锚点等陈述，待最终严格校验。
