# 3.2.2 最终发布方案

## 候选版本与发布内容

本文件供最终发布确认；它不是已经发布的记录。

- 版本：3.2.1 → 3.2.2，patch；发布记录日期拟用 2026-11-05。
- 来源：release/3.2.2，基于已验收的 develop。
- 范围：mdf-init、v3-upgrade-review-bugs、v3-bug-reproduction-tests、bug-1mw9 四份 Change。
- 不新增框架运行时功能、不升级依赖，不改变业务数据或配置缓存格式。

## 候选发布说明

本节列出本版 Fixed 内容。

- bug-2AN6：修正 ORM 工厂生成模板，使用支持的连接与构造 API。
- bug-GH7A：生成的单测 bootstrap 使用 Monolog Level::Critical。
- bug-Y68Q：损坏或非数组配置缓存能够按现有解析路径重建。
- bug-P4KU：普通 fork 测试无需覆盖率驱动，业务失败排除致命错误。
- bug-1MW9：覆盖率脚本保留非预期失败状态与输出。

## 已完成的发布准备

本节链接实际通过证据。

| 项目 | 结果 |
| --- | --- |
| 三人 partition 审查 | 通过，两项发布材料问题已修正；见 code-review.md |
| 正式 branch 验证 | lint/build 通过，quick 46/1282，release 208/2322；零失败、错误、跳过 |
| 五项 Bug 逐例证据 | 五个 testcase、16 个 test 均 passed，详见 bug-validation-readiness.json |
| 事实审计 | 25 页与30个实现已复核；零 finding，8条目录匹配 warning 均已处置 |
| strict validation | 零 finding |
| 远端预检 | origin/master 与本地上一发布一致，无 v3.2.2 tag；实际执行前仍须重新核对 |

## 确认后执行的收口操作

本节说明将修改的对象、分支与远端引用。

1. 对五项 Bug 逐个完成独立修复代码审查，复用本次明确 passed 的逐例报告；通过后关闭并写 fixed_in:3.2.2。
2. 生成 3.2.2 版本目录和 CHANGELOG，归档四份 Change、Bug 及发布报告，更新 manifest。
3. no-ff 合入本地 master，创建 v3.2.2 注释 tag。
4. 将 master 回合本地 develop。
5. 原子推送 master 与 v3.2.2 到当前 origin；不推送 develop，不删除任何远端分支。
6. 删除本地 release/3.2.2 源分支，保留其 worktree 为 detached；保留另外四条 bugfix 分支与原有 worktree。

若独立关闭或发布预检失败，保留真实现场并按 MDF 恢复，不声明已发布。
当前目录：/Users/xuchang/Projects/OAS-Git/php-slimapp-worktrees/release/3.2.2。
