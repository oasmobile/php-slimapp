# Develop PR

`$mdf dev-pr [<slug>]` 将本地 develop 的未共享工作移交到 adhoc，再按 PR mode 交付。
不要求先 revert；本地分支与 worktree 在检查前创建，远端分支与 PR 在检查通过后创建。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Prepare                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 已有未合并 PR ───────→ 3 Pull request
                 ├──── 已 merged 待清理 ────→ 4 Finish
                 ├──── 无本地增量 ──────────→ [结束]
                 ├──── 现场不符 ────────────→ [保留现场并报告]
                 │
                 ▼ 已保全并对齐
┌──────────────────────────────────┐
│ 2 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 检查失败 ────→ [修复并补审补测]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Pull request                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 未合并 ────→ [沿用 pr 等待与返工]
                 │
                 ▼ 合并核验通过
┌──────────────────────────────────┐
│ 4 Finish                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 未完成 ────→ [保留现场并续办]
                 └──── 已完成 ────→ [返回调用方]
```

## 工作流（唯一执行契约）

读取 `references/common.md`；只适用于 PR mode。本 intent 授权 fetch、创建本地 adhoc 与
worktree、保全后 reset 本地 develop，以及检查通过后的 source push 和 PR/MR 创建。
sync 委托时沿用已确认计划，不另要求用户重复授权。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Prepare | 脚本 | 先核恢复；否则保全并对齐 develop | 原 head、base、worktree 与记录 | 首次2；PR恢复3；清理4；无增量结束 | 保留现场并报告 |
| 2 | Check | 约束 | 补 Change，集成、lint、审查、smoke 与 fact | 实际报告与材料 | 3 | 修复并补审补测 |
| 3 | Pull request | 约束 | 委托 pr 创建或恢复同一 PR/MR | 平台状态与合并核验 | 4 | 沿用 pr 等待与返工 |
| 4 | Finish | 约束 | 委托 close-out，再返回 sync 或报告 | completed 与同步结果 | 返回调用方 | 保留现场并续办 |

## 术语与数据结构

### 本地接管

```bash
python3 "$MDF_ROOT/scripts/mdf.py" dev-pr --repo "$REPO_ROOT" --slug <slug>
```

- 步骤 1 先核 Git common dir 的 dev-pr 记录，再按 pr 的恢复路由核同一 source。
  - 已有未合并 PR 直接进入步骤 3；已 merged 待清理进入步骤 4，不重做首次检查或准备。
  - 尚无 PR 才运行上述 CLI；恢复沿用已记录 source、worktree 与 slug，身份无法核对时停止。
- slug 由 Agent 根据工作内容选定，也可使用 CLI 的稳定默认值；恢复沿用记录中的 slug。
- fetch 后固定 local develop HEAD、origin/develop HEAD 和唯一 merge-base。
  - 无本地独有 commit 返回 no_pending_commits；不创建空分支或 PR。
  - 占用 develop 的 worktree 必须 clean，无未完成 merge；不 stash 或提交他人工作。
- 先保存操作记录，再从原 HEAD 建 `adhoc/<slug>` 与独立 worktree；核对保全后才 reset。
  - reset 目标是固定 origin/develop，不是 merge-base；使用 `reset --keep` 保留意外脏改动。
  - develop 未 checkout 时使用带 expected SHA 的 update-ref。
  - 记录在 Git common dir；重复调用恢复同一 source，不重复创建分支或 PR。
- 按返回 worktree 绑定后续操作；develop 后续新增工作不自动并入本次 source。
  - reset 前检测到新提交则停止；reset 后可在 develop 开始新的工作。
  - 本次 close-out 无法 ff 同步新 develop 时保留现场，再由 sync 判断剩余增量。

### 材料与验收

步骤 2 委托 [无账本 Adhoc](adhoc-change.md) 步骤 1–5，使用本节 smoke 要求；完成后回本页步骤 3。
不执行其 Finish，也不从该页反向重新调用本 workflow。

- 首次整理 commit 后尝试补 `changes/unreleased/<slug>/CHANGE.md`，记录真实成果与范围。
  - 不补造 delivery.json、objectives 或历史阶段完成记录；材料不完整则在本地修正。
  - 材料目录以 adhoc-status 返回值为准，不覆盖继承的其他交付。
- 必要时 no-ff merge 最新 origin/develop，处理冲突后执行 lint、code-review、verify smoke、fact audit。
  - code-review 沿用无账本 adhoc 的 1 人独立 reviewer 与修复规则。
  - 本 intent 用 verify smoke 替代普通无账本 adhoc 的 smart；执行全项目 smoke，保留实际报告。
  - verify smoke 为 named suite，证据写入 Change，不伪造 smart 或 branch verification-report。
  - hook 与 fact update 沿用原流程；实现变化后补审补测，检查失败不 push、不创建 PR。
- 完善 Change evidence、validate 并提交后才委托 [pr](pr.md)。
  - pr 的准备与返工继续遵守本页 smoke 要求；目标推进后重新集成、补审补测与 fact。
  - 沿用 squash、非 force push、平台等待与 merge commit 核验；不重复另建 PR。
- merged 后委托 [close-out](pr-close-out.md) 完成清理；sync 委托时回到新的同步预览。
  - develop 已对齐不代表 PR 已完成；CLI 持续返回 dev_pr_required，直到实际 close-out 完成。

### Trivial policy

- 默认 trivial 为纯 MDF/宿主维护：`.mdf/`、宿主目录及根 `AGENTS.md`。
- 项目可用当前 `.mdf/manifest.yaml` 的 `closeout.trivial_paths` 替代默认路径规则。
  - 值为 repo-relative glob 列表，按 Python fnmatchcase 匹配；`*` 可跨 `/`，大小写敏感。
  - 例如 `["docs/*", "AGENTS.md"]`；空列表表示任何非空路径改动都不算 trivial。
  - 不固定远端 policy，不增加 policy 修改的特殊审批。
- sync 逐笔检查全部本地独有 commits，包括 rename/delete 原路径与 merge resolution。
  - 任一 non-trivial 令整串转 dev-pr；不能用最终 diff 或 revert 抵消历史改动。
  - 全 trivial 且可直接 push 时沿用同步；diverged 仍转 dev-pr，避免直接集成受保护 trunk。
  - planning/backmerge 仍沿用其专用例外；远端 branch protection 不受本规则覆盖。
