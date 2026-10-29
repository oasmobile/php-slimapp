# Adhoc Close-out

仅 adhoc 的 close-out 项或当前 adhoc 上的独立 close-out 执行本子流程。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── PR mode ─────────→ [委托 PR Close-out 恢复并返回]
                 ├──── local 无账本 ────→ [委托 Adhoc Change 并返回]
                 ├──── 已实际收口 ──────→ 7 Report
                 ├──── 已合并待清理 ────→ 4 Recheck
                 ├──── 缺前置步骤 ──────→ [交接对应账本项]
                 ├──── 身份不符 ────────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Integrate                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 需补审补测 ────────→ [交接对应账本项]
                 ├──── 现场或冲突未决 ────→ [保留现场并报告]
                 │
                 ▼ 无须补前置
┌──────────────────────────────────┐
│ 3 Materials                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 材料可修 ────→ 3 Materials
                 ├──── 其他失败 ────→ [保留现场并报告]
                 │
                 ▼ 材料已提交
┌──────────────────────────────────┐
│ 4 Recheck                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 缺前置证据 ───────────────→ [交接对应账本项]
                 ├──── 其他不符 ─────────────────→ [停止并报告]
                 ├──── 未合并且 develop 前进 ────→ 2 Integrate
                 │
                 ▼ 交付准备已完成
┌──────────────────────────────────┐
│ 5 Authorize                      │
└────────────────┬─────────────────┘
                 │
                 ├──── deliver 裁定待确认 ────→ [返回 deliver 6]
                 ├──── 确认后现场已变化 ──────→ 4 Recheck
                 │
                 ▼ 无关口或有效确认
┌──────────────────────────────────┐
│ 6 Finish                         │
└────────────────┬─────────────────┘
                 │
                 ├──── PR mode ─────────────→ [委托 PR Close-out 并返回其实际状态]
                 ├──── local 失败或不明 ────→ [保留现场并报告]
                 │
                 ▼ local close-out 成功
┌──────────────────────────────────┐
│ 7 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 完成证据不符 ────→ [报告实际状态]
                 └──── 核验通过 ────────→ [返回调用方]
```

## 工作流（唯一执行契约）

先核 manifest.closeout。PR mode 直接执行 [合并后续办](pr-close-out.md)，返回实际结果。
PR 未 merged 时交接 pr，不在 close-out 内创建 PR、轮询 CI 或准备候选材料。
本页后续编号流程仅用于 local；PR mode 的 pr 可只读取其中材料条款。

local 先运行 adhoc-status；`material_mode: change` 时委托 [无账本 Adhoc 收口](adhoc-change.md) 并返回。
有账本时执行本页后续流程；损坏账本不能改走无账本路径。

读取 [common](common.md)、[delivery-contract](delivery-contract.md) 与 [adhoc](adhoc.md) 的条款。
仅读身份、账本与调用方规则，不重新执行这些文件的工作流。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 脚本 | 核模式、恢复与材料 | status、doctor | PR或无账本委托返回；完成7；合并4；其余2 | 缺前置交接；不符停 |
| 2 | Integrate | 约束 | 核现场，必要时集成 develop | 端点、diff | 3 | 补审交接；现场未决停 |
| 3 | Materials | 约束 | 补齐 Change、validation、提交 | Change、validation | 4 | 材料可修 3；其余保留现场 |
| 4 | Recheck | 约束 | 重核前置与两端，勾 close-out | report、账本、tip | 5 | 主线前进 2；缺项交接；其余停 |
| 5 | Authorize | 约束 | 核调用授权、裁定与端点 | 调用方、裁定、确认 | 6 | 低 confidence 返回 deliver 6；现场变 4 |
| 6 | Finish | 脚本 | PR 委托子流程；local 运行 finish-gitflow | 实际状态、Git 结果 | PR 合并后续办；完成 7；local 7 | 按子流程或保留现场并报告 |
| 7 | Report | 约束 | 按 local/PR 核实际完成并交接 | 模式、completed、merge_commit、清理与路径 | 返回调用方 | 报告实际状态 |

## 术语与数据结构

### 入口与前置报告

本节核对已有工作，不在 close-out 内补做工作、verify 或 fact。

- PR mode 时，先委托 `pr-close-out.md` 恢复后返回，不再走本页首次准备。
  - 恢复仍遵守外层 until 与 decision 策略；source 不明时停止，不从 detached 目录猜测。
- 运行 `mdf.py adhoc-status --repo <owner> --slug <已知slug>`；completed 时直接到 7。
- 未 completed 但 merge_commit 已存在时，直接到 4。只续办清理，不改材料或重做集成。
- 未完成时运行 doctor，要求 ready；核对工作、lint、code-review、verify smart、fact audit/update 已勾。
- 任何退勾或提交前先只读检查 owner clean；有本地改动时保留现场并停止。
- 只查 report 已交且声称通过，不做 commit 对齐审判。
  - code-review 终稿无 commit hash、无未解决项；fact-audit 报告结论通过。
  - verification-report.json 的 branch 对应本交付。
    `scope: smart`、`all_passed: true`。
- 未合并时，缺项按最早未完成项交接；缺报告且该项仍勾选时退勾该项及后续项，有改动才提交。
  - code-review 缺失对应 code-review；smart 缺失对应 verify smart；fact 缺失对应 fact audit/update。
  - 内部委托返回调用方重新 Select；独立 close-out 报告缺项后结束，不直接执行被跳过的阶段。
- 已合并仅待清理时，前置材料缺损则停止报告状态不一致，不退勾已交付账本或补新提交。

### 集成与材料

本节在源工作区集成目标主线，并准备本地 Change。

PR mode 的 Integrate 与 Recheck 执行 [提交前远端集成](pr.md#提交前远端集成)，
使用最新 origin/develop；以下本地 develop 的包含检查与 docs 跳过规则仅适用于 local。

- 先只读检查 owner 与 develop 的实际合并工作区均 clean，无未完成 merge。
  - 有问题停止并保留现场；不 stash、reset、abort 或提交他人改动，无关工作区不检查。
- develop 尚非 owner HEAD 的祖先时，固定 develop commit 与集成前 HEAD。
  - 运行 `mdf.py merge-no-ff --repo <owner> --commit <develop-commit>`。
  - 本次冲突按既定目标尝试解决后提交；语义不明或无法解决时保留现场并交接。
- 只在增量全部为非本交付 docs 路径时跳过补审补测，并在终稿追加无 hash 的跳过说明。
  - 本交付 docs 为 start_commit 到集成前 HEAD 已改过的 docs 路径；路径不明不可跳过。
  - 其余增量退勾 code-review 及后续项。草稿保存集成前左端点，提交后交接 code-review。
  - 增量 review 为 1 人；由外层按六项账本完成补审、smart 与 fact 后再续办本流程。
- 用 `assets/templates/change.md` 补齐同目录 CHANGE.md。
  记录实际结果、outcomes、事实更新与证据。
  - `change_kind: adhoc` 或 `fix`、`source_branch: adhoc/<slug>`、`proposals: []`。
  - 小范围修正可选 fix，分支与交付步骤仍按 adhoc 执行。
  - 总结直接写入 Change；不要求 design 或 delivery-summary.html，不修改 PRP 或创建版本目录。
- 运行 `mdf.py validate --repo <owner> --level basic`。
  回读 findings 并核对 diff 后提交。
  - 失败保留材料，修正本次材料后重做 3；外部缺项或无法修正时停止，不代替业务验证。

### 确认、完成与返回

本节保留 deliver 的确认边界，并以实际 Git 结果结束交付。

- 步骤 4 先重核前置 report、连续账本与两端 clean；缺项先交接或停止，再判定主线关系。
  - 未合并时，最终 HEAD 须包含当前 develop，否则回 2；已合并时走下条清理核对。
  - 已合并仅待清理时，重核 merge_commit 仍在 develop 第一父链；不将新 develop 合回已交付源。
  - 清理续办须有已提交的规范 Change；缺损时报告状态不一致并停止，不新增源提交。
  - close-out 尚未勾时改为 `[x]` 并提交；已勾不重复提交，记录两端 tip，全勾不代表 close-out 完成。
- deliver 委托先核 until 允许进入 close-out；步骤 5 的 Gitflow decision 按其 confidence 策略裁定。
  - 低 confidence 返回 deliver 6 等待确认；yolo 无 confidence 限制；其他调用沿用实际收口授权。
  - 确认后从本流程 5 续办，重核端点；现场变化回 4，不基于过时确认直接 close-out。
  - 拒绝则保留现场，未决仍返回等待；不绕过关口或再次执行已完成的阶段。
- 步骤 6 运行 `mdf.py finish-gitflow --repo <owner>`；失败先读 CLI 日志并报告已完成操作。
  - 不声称完成，不盲目重放；续办先回 1 核现场，不能证明可继续时询问。
- 步骤 7 按模式核对完成证据，不能相互替代：
  - local：再运行相同 adhoc-status；要求 completed 为 true、merge_commit 非空。
    核对 no-ff 合入本地 develop、源分支已删、owner 保留且 detached 在交付 tip；不 fetch、不 push、不打 tag。
  - PR：按 PR Close-out 核 completed=true、目标远端 merge、remote_deleted=true 与本地 source 清理。
    不以本地 adhoc-status 或 detached 单独代替平台结果。
  - 两种模式均不删除 `.mdf/`、`docs/` 或保留的工作区。
  - deliver 返回其完成核验；直调返回 adhoc Select；独立 close-out 报告实际结果后结束。
- 独立调用只有用户明确要求才删除工作区；deliver 委托按其 confidence 策略与公共清理规则裁定。
  保留目录不影响交付完成。
