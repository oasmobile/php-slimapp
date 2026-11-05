# 无账本 Adhoc 收口

本页处理已有分支的实际成果；不创建 `delivery.json`、`objectives.md` 或虚拟 start 记录。
由 pr 的准备阶段或 local close-out 委托；PR 已 merged 时只执行合并后续办。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 内部角色或有账本 ────→ [返回所属 workflow]
                 ├──── 损坏或范围不明 ──────→ [保留现场并报告]
                 ├──── 无未合入提交 ────────→ [报告并结束]
                 ├──── 已有合并记录 ────────→ 6 Finish
                 │
                 ▼ 有待合入工作
┌──────────────────────────────────┐
│ 2 Integrate                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 冲突未决 ────→ [修复；语义不明询问]
                 │
                 ▼ 已集成
┌──────────────────────────────────┐
│ 3 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 检查失败 ────→ [修复并补审补测]
                 │
                 ▼ 报告通过
┌──────────────────────────────────┐
│ 4 Facts                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 实现改动 ────→ 3 Check
                 ├──── 未通过 ──────→ [返回未通过与阻断原因]
                 │
                 ▼ 事实审阅通过
┌──────────────────────────────────┐
│ 5 Materials                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 材料不完整 ────→ [修正并重验]
                 │
                 ▼ 已校验提交
┌──────────────────────────────────┐
│ 6 Finish                         │
└────────────────┬─────────────────┘
                 │
                 ├──── PR 未 merged ────→ [返回 pr 推进]
                 ├──── 部分成功 ────────→ [按原操作记录续办]
                 └──── 实际完成 ────────→ [核验并返回]
```

## 工作流（唯一执行契约）

读取 `references/common.md`；本页只在当前 intent 及外层 until 授权范围内执行。
分支分类不等于已启动交付；没有账本时不得推断历史阶段已完成。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve | 脚本 | 核 source、状态、范围与材料目录 | adhoc-status、Git、上下文 | 有增量2；合并恢复6；无增量结束 | 账本返回原流程；歧义停 |
| 2 | Integrate | 约束 | 固定范围，必要时 no-ff 集成目标 | 固定端点与 diff | 3 | 冲突修复；语义不明询问 |
| 3 | Check | 约束 | lint、1 人审查、普通 source smart 或 dev-pr smoke | 实际报告 | 4 | 可修回3；否则报告阻塞 |
| 4 | Facts | 约束 | hook、fact audit，必要时 update | hook 结果、审阅报告 | 5 | 修改代码回3；其他按原流程 |
| 5 | Materials | 约束 | 完成 Change、validate 并提交 | Change 与 evidence | 6 | 修正材料后重验 |
| 6 | Finish | 脚本 | local finish；PR 返回 pr 或合并后续办 | 实际 merge 与清理结果 | 核验后返回 | 保留现场，按记录恢复 |

## 术语与数据结构

### 身份、材料与范围

- `feature/*`、`bugfix/*`、`release/*`、`hotfix/*` 沿用各自流程及命名校验。
- 精确名 master、main、develop、planning 不归 adhoc；其他合法分支均为 adhoc。
  - qa/dev 角色及 backmerge 先按其所属 workflow 路由，不能独立收口。
  - 保留真实分支名与当前 worktree；不改名、不搬走已有工作。
- Resolve 先识别本次未提交成果；归属明确时按 common 提交相关路径，无法归属时停止，不提交他人工作。
  - 有未提交成果时不能仅凭 no_pending_commits 结束；处理后重读 status，再核范围和无增量结论。
- 运行 `mdf.py adhoc-status --repo <owner>`，回读 material_mode、source、path、range、paths。
  - `material_mode: ledger` 返回原账本流程；属于本 source 的损坏账本必须修正，不能绕过。
  - `material_mode: change` 使用返回的 path；不自行从分支前缀再次推导。
  - 继承的其他交付不是本次身份；默认目录冲突时 Core 选择带 source hash 的目录。
  - 多份匹配材料或已知 slug 不符时停止，不覆盖其他工作。
- local 的目标为本地 develop；PR 准备前 fetch origin，目标为 origin/develop。
  - 首次范围为唯一 merge-base 到 source HEAD；无共同祖先或多个 merge-base 时明确范围后再继续。
  - 范围代表待合入内容，不冒称分支创建点；包含其他工作时先核对归属。
  - `no_pending_commits: true` 时报告无未合入提交，不制造 Change 或删除分支。
  - 有独占 commits 但 tree diff 为空时展示实际情况，明确是否记录本次工作。
- 首次 squash 在冻结范围前执行；随后将 status 返回的 range 写入 Change 的 `evidence.range`。
  - `base`、`source_head` 为完整 commit hash；`target_head` 记录当次目标端点。
  - source_head 为写入材料前的工作端点；合并使用最终 source tip，避免 Change 自引用。
  - range 可独立于账本存在；已有规范 Change 未记录 range 时先读 status，再补记范围。
  - 固定 base 不随目标推进重算；squash 保护已记录 source_head，不能改写该端点。
  - range 不记录阶段完成状态；只有实际报告才能证明检查结果。

### 检查与事实

本节是无账本 adhoc 的收口准备，不套用其他交付缺少前置时的停止规则。

- local 按实际目标关系 no-ff 集成 develop；PR 沿用 pr 的提交前远端集成与 squash 规则。
  - 目标推进、冲突修复或其他实现改动后补审补测，保留原 base。
  - 两端 worktree 须 clean；已有未提交工作先按已授权范围处理，不提交他人改动。
- 先按 `lint.md` 执行项目 lint，再由 1 个独立 reviewer 审查固定 base 到当前 head。
  - 读取 `reviewer-protocol.md`，从最新目标 policy_ref 加载项目 rule 与 AGENTS.md。
  - 分派时分别给出 base、head、policy_ref 与实际工作；不依赖 roster 配置或 objectives。
  - 按 code-review 的问题裁定、修复与增量复核规则处理，终稿写入返回 path 下的 code-review.md。
  - 不把固定 base 伪装成最新目标来调用 standalone review，避免误用旧 policy。
- dev-pr 接管的 source 仅读 [dev-pr](dev-pr.md) 的「材料与验收」条款，执行 smoke 并保存 named suite 证据。
  - 替代本节 smart，不重新进入 dev-pr 工作流；恢复时按 Git common dir 的 dev-pr 记录核 source 身份。
- 其他 source 按 `verify.md` 执行 smart；按固定范围选 module 与 test，成败均保存报告。
  - 不要求 objectives checkbox；报告须对应真实分支，`scope: smart`、`all_passed: true`。
  - 修复实现、测试或验证配置后补必要审查与验证；已有适用报告可复用，不伪造完成。
- hook 沿用 `pre-gitflow-finish` 的一次执行与日志恢复规则；实现改动返回 Check。
- 按 `fact-audit.md` 使用固定 base 的 branch scope；必要时执行 fact update。
  - 按 fact 审阅结果保存报告，保存在同一材料目录。
  - 不创建 objectives，也不向其他交付的 checklist 追加或补勾。

### Change、平台与完成

- 按 `assets/templates/change.md` 在返回 path 完成 CHANGE.md，填实际成果与 evidence。
  - `change_kind: adhoc` 或 `fix`，`source_branch` 为真实名称，`proposals: []`。
  - 保留 evidence.range 与适用报告；不要求 design、delivery-summary.html 或 PRP。
  - 运行 `mdf.py validate --repo <owner> --level basic`，修正本次材料并提交。
- local 运行 `mdf.py finish-gitflow --repo <owner>`，以返回的实际 merge 与清理状态核验。
  - no-ff 合入 develop、按预期 SHA 删除 source ref；不 fetch、不 push、不打 tag。
  - 保留工作目录；主 worktree 能切回 develop 时切回，被其他 worktree 占用则 detach 保留。
  - 完成不以 owner detached 为唯一条件；核 completed、merge_commit 与源 ref 已删除。
  - 部分成功按操作记录续办，可从同一仓库使用 `--source <真实source>` 恢复。
  - 没有匹配记录不能仅靠 --source 猜测恢复；同名源分支重建或端点变化时保留现场。
- PR 准备完成后返回 pr，沿用其 Goal、等待、返工与实际 merged 判据。
  - 未 merged 不清理；已 merged 的 close-out 只核平台结果并续办，不重跑本页检查。
  - 外部创建并已 merged 的 PR 可由 close-out 接管：绑定已知 source tip，核规范 Change 与平台事实。
  - 首次接管仍核 source/target/head、双亲 merge commit 及远端第一父链，不能只凭本地包含关系。
  - 恢复记录只保存 Git/平台操作结果，不创建阶段状态机或第二份账本。
