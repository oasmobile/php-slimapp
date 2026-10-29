# PR 合并后续办

## 决策树

```text
┌──────────────────────────────┐
│ 1 Check merged               │
└──────────────┬───────────────┘
               │
               ├──── 未 merged ────→ [交接 pr]
               ├──── 身份不符 ─────→ [保留现场，停止]
               │
               ▼ 通过
┌──────────────────────────────┐
│ 2 Finish Gitflow             │
└──────────────┬───────────────┘
               │
               ├──── finish_busy ─────→ [等待持锁调用退出，回 1]
               ├──── 本地集成冲突 ────→ [保留现场，修复并验证后回 2]
               ├──── 其他失败 ────────→ [读日志，保留现场并报告恢复位置]
               │
               ▼ 返回实际结果
┌──────────────────────────────┐
│ 3 Report                     │
└──────────────┬───────────────┘
               │
               ├──── completed 且核验通过 ────→ [返回 close-out 完成]
               ├──── 可修 backmerge ──────────→ [补审补测后回 2]
               └──── 阻塞或证据不符 ──────────→ [保留现场，报告未完成]
```

## 工作流（唯一执行契约）

本页只由 PR mode 的 close-out 调用；pr 已完成实际合并与关联 CI 收尾，不创建 pr Goal。
读取 `references/common.md`；遵守调用方 until 与既有授权。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check merged | 约束 | 锁定 source、模式与原 PR/MR，核实际 merged | 平台与恢复记录 | 2 | 未 merged 交接 pr；身份不符停止 |
| 2 | Finish Gitflow | 脚本 | 从主 worktree 调用 finish-gitflow --source | CLI 结果与实际 Git | 3 | busy 回1；本地冲突修复验证后回2；其他报恢复位置 |
| 3 | Report | 约束 | 核发布、本地集成、backmerge 与清理 | completed、merge_commit、remote_deleted | 完成返回 | 可修 backmerge 修复后回2；否则报告阻塞 |

## 术语与数据结构

### 入口与完成判据

close-out 只执行合并后的剩余工作，不创建或更新 PR/MR、不等待 CI。

- 未 merged 时不能调用 finish-gitflow；返回 pr 尚未完成，不绕过 objectives 顺序。
- merged 但关联 CI 未收尾或缺少证据时先恢复 pr，按 [PR 轮询](pr.md#当前调用内轮询) 核验；通过前不发布或清理。
- 已 merged 后不重做源分支集成、材料、审查或验证；使用固定 M 与操作记录。
  - 无账本 adhoc 的外部 PR 没有 MDF 操作记录时，可绑定已知 source tip 后首次接管。
  - 核规范 Change、平台 source/target/head、双亲 M 与目标远端第一父链，再记录并续办；未 merged 返回 pr。
- source 已删除、owner detached 或外部删除时，仍从同一 Git common dir 的主 worktree 恢复。
- `completed=true` 须同时核对 merge_commit、远端目标、remote_deleted=true 与本地 source 删除。
  owner 存在时核 detached；owner 已外部删除时如实报告，不重建。
- release/hotfix 还须核 tag 指向固定 M、远端 develop 包含已确认 backmerge HEAD。
- 部分成功只补剩余动作，不重复发布；finish_busy 等持锁调用结束，不删除 lock。
- close-out 完成后返回 deliver / adhoc；更大范围 Goal 的其他工作仍须保留。
- 工作区清理按 [close-out](close-out.md) 的清理授权执行；CLI 始终保留 owner worktree。

### Backmerge 修复

发布后的修复保持固定 M，不重新进入 pr。

- backmerge 的冲突在记录的 `backmerge.worktree` 中解决并提交，保留固定发布提交 M 和 tag。
  - 补审使用独立 `$mdf code-review --against <回合base>`，覆盖回合与修复。
  - 在该 worktree 用 verify named 执行 lint、build、quick 和原发布所需 suite（release 或 smoke），再按改动补 named suite。
  - fact audit/update 使用 paths 范围，指向受修复影响的事实页；不修改固定发布提交或已发布版本材料。
  - 审查、验证和 fact 证据保存在 checkout 外的运行报告目录；不退勾已发布版本的 objectives，不套用交付 branch 验证。
  - 所需证据齐全并通过后恢复步骤 2；修复后的完整 backmerge HEAD 必须已进入远端 develop，才能完成收口。
  - 修复后由 CLI 直接 push develop；backmerge 不创建 PR/MR，也不进入平台合并轮询。
- 每轮依据新反馈和验证结果推进；仅在用户停止、外部阻塞或无进展且不能安全继续时交接。

### 远端交付分支清理

本节只清理原 PR/MR 的 feature、bugfix、adhoc、release 或 hotfix source，不清理 master、develop、planning 或 tag。

- 合并核验与所需发布动作完成后，先清理远端 source，再 detach owner、删除本地 source；远端失败时保留本地现场。
- 删除前直接 ls-remote 查询精确 ref，tip 必须等于已确认 PR head；以显式 expected SHA 的 lease 条件删除，不依赖 tracking ref。
  - lease 仅用于删除该 source，不用于改写任何分支历史；并发前进时停止并保留新 tip。
  - 远端已由平台或用户删除时，确认缺失即复用，不重复发删除请求。
- 操作记录的 remote_cleanup 保存本次 head 与 pending/deleted；请求前落盘 pending，删除响应成功先落盘 deleted，再核远端缺失。
  - 请求中断、响应丢失或确认写入失败后，重入若远端已缺失则补记成功，再继续本地清理。
  - pending 重入时远端仍存在，即使 SHA 相同也返回 remote_cleanup_uncertain；不能自动重删可能重建的分支。
  - 已确认 deleted 后再次出现同名分支，返回 pull_state_changed 并保留，不论其 SHA 是否相同。
- 删除结果不确定时报告原 PR、source、expected head 与实际远端事实；不得清空或修改操作记录绕过保护。
  - 核实同名分支归属后，由用户或其明确授权的操作清理远端，再次 close-out 根据缺失事实继续；不自动降低保护。
- release/hotfix 在确认 tag/backmerge 均完成后、集成本地 develop 前持久化 publication_completed。
  本地集成或远端清理重试只核固定 M 和已交付 backmerge head。
  不再采用保留的 backmerge 工作区中后续新增提交，也不因该临时工作区已删除而重新发布。
- CLI 的 remote_deleted 独立表示已确认远端 source 删除，deleted 仍表示本地 source；全部清理完成后才能 completed=true。

### 发布与回合

本节固定本次发布的实际 merge commit M。

步骤 2 的 `finish-gitflow` 固化执行下列发布动作，Agent 只核结果及处理返回的冲突。

| CLI 动作 | 证据 | 失败/缺失去向 |
| --- | --- | --- |
| 核 release/hotfix 平台合并 | master 第一父链中的双亲 M | 停止并保留现场 |
| 在 M 创建 annotated `v<version>`，正文取 CHANGELOG，只 push tag | 远端 tag 指向 M | 读日志，按记录恢复；不覆盖 tag |
| 独立 worktree 将 M no-ff 回合 develop | 远端 develop 包含完整回合 HEAD | 步骤 3 处理 backmerge |
| 清理远端及本地 source，保留临时回合目录 | remote_deleted、deleted、owner 状态 | 步骤 3 核清理记录；不删除主目录 |

- 不跟随后来前进的 master HEAD；本地 master 只做同名 ff 同步，分歧时保留现场。
- 本地 develop 的集成遵循下节；远端 backmerge 始终以远端 develop 为 base，不夹带本地独有 commits。
- tag 已发布、回合未完成时返回 published_pending_backmerge。
- backmerge 是直接进入 develop 的特例；使用 no-ff merge 和非 force push，不创建回合 PR/MR。
- 冲突保留在返回的 backmerge.worktree；当前 Agent 解决、补审补测并提交后恢复 close-out，直接 push develop。
- 平台拒绝直接 push develop 时保留 tag、回合 worktree 和 push_error；可修问题自行处理，权限阻塞则报告。
- develop 前进时在回合 worktree 合入远端 develop，解冲突并按影响补审补测；恢复 close-out 后重试直接 push。
- 新 head 必须保留记录的历史和固定 M；改写历史仍停止。
- worktree 创建中断后，已有未占用回合分支与记录的 head（尚无 head 时为 base）精确一致，才复用分支建立工作区。
  分支不符、已被占用或已有 head 的分支丢失时保留现场，不重建或覆盖已记录历史。
- tag push 响应丢失时先核对远端；已存在且符合记录则复用。
- local 模式继续原子 push master + tag，develop 只在本地回合。

### 本地 develop 集成

close-out 要求本地 develop 包含远端交付结果，不要求本地与远端 tip 相同。

- 本地落后时同名 ff；已包含远端时保留本地 commits；双方分叉时将远端 no-ff merge 到本地。
- 不分类、squash 或 push 本地独有 commits，不要求先执行 dev-pr；这些工作的远端交付独立处理。
- 目标 worktree 必须 clean 且无未结束 merge；未被检出时，分叉集成在同级 develop worktree 中执行并保留。
- merge 冲突保留现场，报告 worktree、base 和 remote_head；解决并提交后恢复 close-out，不 reset、rebase 或自动 abort。
- 实际 merge 后按集成影响补审补测；原 PR 的 CI 不代表本地组合已验证，不重开原 PR 或改写固定 M。
  - 调用前记录本地 develop tip；以它为 base 核本轮集成 diff，审查和验证证据保存在 checkout 外。
- 本地集成完成后才清理 source；重入已包含远端时不重复 merge。

### Merge 例外

本节约束 MDF 的 Git 入口；平台可保留正常 push 权限。

| 操作 | PR mode |
| --- | --- |
| feature/bugfix/adhoc → develop；release/hotfix → master | PR/MR |
| planning → develop | 完整文档白名单才允许 no-ff |
| master → develop | 允许固定 master 历史提交 no-ff 回合 |
| develop 上纯 MDF/宿主维护 | 允许直接提交和 push |
| close-out 中 origin/develop → 本地 develop | 允许 no-ff 集成；不 push 本地独有 commits |
| 其他合入 master/develop | 拒绝，提示 PR/MR |
| trunk → owner、角色分支 → owner | 沿用现有集成 |

- 完整文档白名单：docs/、changes/、根 *.md、.mdf/ 及以下全部宿主目录。
- 宿主目录：.agents/、.claude/、.codex/、.cursor/、.kiro/、.openclaw/，不限定 skills/mdf。
- develop 默认直接维护仅允许 .mdf/、宿主目录、根 AGENTS.md；项目可按 [dev-pr](dev-pr.md) 覆盖 trivial policy。
- 混入其他路径须 PR/MR；master 不增加文件维护例外；禁止 rebase 或跨分支 ff-only。
- planning 检查独有普通提交、rename/delete 原路径、merge resolution 及最终增量，防止 revert 掩盖代码修改。
- sync 的 master/develop 分叉或无法证明合规的领先增量须走 PR/MR；同名 ff 同步允许。
  - 创建、等待、核验合并及继续同步见 [Sync 的 PR 提交与恢复](sync.md#pr-提交与恢复)。
- push 后审计与项目配置见 [CI 接入](ci-review.md)。
