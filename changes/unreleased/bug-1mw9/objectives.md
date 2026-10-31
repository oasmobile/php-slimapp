# bug-1MW9 修复交付

## 流程

- needs_design: no

## 步骤

按序执行，每项完成后才勾选；已有测试不代表已确认红灯。

- [x] 确认目标与约束（start）
- [x] owner 开发：确认有效红灯，修复 bug-1MW9 并让对应回归转绿
- [x] converge
- [ ] lint
- [ ] code-review
- [ ] verify branch
- [ ] fact audit
- [ ] close-out

## 需求来源

范围来自 [bug-1MW9](../../../docs/bugs/bug-1MW9-coverage-script-masks-test-failures.md)。

## 目标与非目标

目标：覆盖率脚本保留非预期失败状态，并正确识别预期业务失败。
仅修复本 Bug，不改其它已登记 Bug，不推送、不发版、不关闭 Bug。

## 约束

用户已于 2026-10-31 确认五项统一方案，授权 Agent 执行红灯、修复与回归。
采用 solo：owner 1、qa 0、dev 0、reviewers 1，qa/dev best-of-n，review replicate。
PHP >=8.5、pcntl 和锁定开发依赖为首次测试前所需条件。
Agent 在新 worktree 准备本地依赖和独立 autoload，无需凭据或外部服务。
当前五项复现用例均在 smoke；其余未修 Bug 的失败须明确记录，不能伪造全套通过。

## 可验证验收

修复前记录针对本 Bug 的有效红灯；修复后相同用例通过，quick 与静态检查通过。
审查只覆盖本 Bug，状态更新为 fixed，记录实际验证范围与未完成阶段。
未执行收口或分支整体验收时，不勾选对应阶段，不宣称已合入 develop。
