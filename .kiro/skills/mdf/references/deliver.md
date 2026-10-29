# Deliver

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 已锁定 PR 恢复 ────────────→ 2 Select
                 ├──── 尚未 start 且委托成功 ─────→ 1 Resolve
                 ├──── start 失败 ────────────────→ [按 start 交接]
                 ├──── 已到 until start ──────────→ 5 Report
                 ├──── decision 待确认 ───────────→ 6 Confirm decision
                 ├──── 不可恢复错误或死硬阻塞 ────→ [停止并报告]
                 │
                 ▼ 唯一交付目标
┌──────────────────────────────────┐
│ 2 Select                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 已到 until 或 close-out 已完成 ────→ 5 Report
                 ├──── PR 恢复且未到截止点 ───────────────→ 3 Execute
                 ├──── collab-mode 联调未完且待接手 ──────→ [交接并结束]
                 ├──── 可并行阶段 ────────────────────────→ 4 Parallel
                 ├──── 证据冲突或阻塞 ────────────────────→ [保留现场并报告]
                 ├──── decision 待确认 ───────────────────→ 6 Confirm decision
                 │
                 ▼ 单个待办阶段
┌──────────────────────────────────┐
│ 3 Execute                        │
└────────────────┬─────────────────┘
                 │
                 ├──── PR 正常等待 ────────────────→ [留在 pr 子流程轮询]
                 ├──── 阶段完成 ───────────────────→ 2 Select
                 ├──── 内部委托到 until ───────────→ 5 Report
                 ├──── 非 yolo decision 待确认 ────→ 6 Confirm decision
                 └──── 失败或外部阻塞 ─────────────→ [按原流程交接]

仅步骤 2「可并行阶段」进入，不是步骤 3 的后续。

┌──────────────────────────────────┐
│ 4 Parallel                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 全部交接通过 ───────→ 2 Select
                 ├──── 任一路到 until ─────→ 5 Report
                 ├──── decision 待确认 ────→ 6 Confirm decision
                 └──── 失败或外部阻塞 ─────→ [保留各路现场并报告]

到 until（含内部返回）或 close-out 已完成时进入步骤 5，不是步骤 4 的后续。

┌──────────────────────────────────┐
│ 5 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 完成证据有效 ────────────→ [结束]
                 ├──── 清理 decision 待确认 ────→ 6 Confirm decision
                 └──── 证据不足 ────────────────→ [报告实际状态]

步骤 1–5 中入口待确认或低 confidence 的 decision 均进入步骤 6；不是步骤 5 的后续。

┌──────────────────────────────────┐
│ 6 Confirm decision               │
└────────────────┬─────────────────┘
                 │
                 ├──── 未决 ────────→ 6 Confirm decision
                 ├──── 拒绝 ────────→ [按原 intent 拒绝去向返回或停止]
                 ├──── 确认 ────────→ [返回原 decision 继续]
                 └──── 修改方案 ────→ [重新评估 decision]
```

## 工作流（唯一执行契约）

- PR mode 的 pr 在当前调用内等待平台合并，每 2 分钟查询结果，合并后按入口确认策略续办 close-out。
  正常等待不属于外部阻塞；`waiting_for_merge` 时不结束当前调用、不进入步骤 5，也不要求用户再次调用。
  completed=false 时不声明交付/Goal 完成；等待与恢复细则见 [PR](pr.md)。

- PR 恢复优先：先核当前 until，再按 [PR 的恢复路由](pr.md) 核已锁定 source 的操作记录及返工备注。
  命中时先恢复父 PR 流程；未命中才进入下方特殊身份或普通选择，不能先要求 owner 当前仍在交付分支。

- 已有 adhoc 在步骤 2–3 执行 `references/adhoc.md` 的步骤 3–4，不走普通选择表。
  - 无账本 adhoc 按 adhoc-status 返回的实际范围与模式进入 pr 或 close-out；边界外不准备材料。
  - 不把分支类别当作已启动流程，不生成虚拟 objectives；归属不明先询问。
- 人工 feature 在步骤 2 执行 `references/manual-feature.md` 的步骤 1–2，替代普通选择表。
- 尚未 start 时将 `--manual` 转交 start，不要求 target 或选择 PRP。
- 人工工作未勾时交接用户，所有模式均不得代勾。
  已勾后，经本表步骤 3 执行该续办工作流的步骤 3，完成后回 Select；先核 until 边界。

读取 `references/common.md`、`references/delivery-contract.md` 与 `references/deliver-policy.md`。
步骤 4 只由 Select 分派；到截止点或实际收口进入 5；任一步的入口待确认或低 confidence decision 均进入 6。
按所选阶段完整读取其 intent 及声明的公共引用，执行原编号工作流，不以本流程摘要替代。
审查阶段读取 `references/code-review.md`；fact 阶段读取 fact-audit，须修复时另读 fact-update。

本 intent 是持续交付的外层协调者，不新增 deliver CLI、交付阶段 gate 或统一 workflow 状态文件。
不按 branch kind 另写交付流程；靠 `needs_design`、roster 与 objectives
checklist 勾选选型（release 另读 `has_dev`；不靠 `0,0` 发明开发阶段）。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve | 约束 | 解析策略；先核 PR 恢复，再锁定 owner | 参数、目标、记录、路径 | 锁定2；截止5；start 返回1 | 低分6；失败交接；死硬停 |
| 2 | Select | 约束 | 先核 until；PR 恢复优先，再选步骤 | 记录、进度、截止点 | 截止或完成5；交接结束；并行4；其他3 | 待确认6；其余保留现场 |
| 3 | Execute | 约束 | 按原 intent 续办单阶段 | 原流程证据 | PR 等待留子流程；完成2；截止5 | 待确认6；其余按原流程交接 |
| 4 | Parallel | Subagent | 分派、核路径并等待交接 | 各路提交与勾选意向 | 交接2；截止5 | 待确认6；其余保留现场 |
| 5 | Report | 约束 | 核对范围、Goal 与收尾清理 | 截止证据或实际 Git 结果 | 结束 | 清理低分6；缺证据报告实际状态 |
| 6 | Confirm decision | 约束 | 展示操作范围与确认原因（入口确认或评分） | 答复、返回位置 | 确认返回；修改重评 | 拒绝按原流程；未决留 6 |

## 术语与数据结构

PR mode 的 pr 候选项已勾时仍先核平台实际状态；未 merged 继续 pr，merged 后必选无 checkbox 的 close-out。
merged 但关联 CI 未收尾或缺少证据时先恢复 pr，按 [PR 轮询](pr.md#当前调用内轮询) 核验，通过后才选择 close-out。
已完成收口须有 finish-gitflow 的实际完成证据，不以 checklist 全勾跳过续办。

### 目标与持续授权

调用 `$mdf deliver [<target>] [--until <intent>] [--yolo]` 授权连续推进本次交付。
除 pr、close-out 入口确认外，默认自动裁定其他 decision，直到指定 intent 之前；无截止点时直到 close-out 完成。

- 授权含截止点之前尚未完成的 start、本地提交、并行委托与集成；允许进入 close-out 时含 Gitflow 操作。
- target 是唯一位置参数，不是 `--` option；option 可在其前或后，option 的值不算 target。
- target 与这些 option 都省略时仍是 deliver。

完成范围：

- 无截止点时，local 模式的 feature/bugfix/adhoc 完成本地 develop 合并；
  PR mode 核对远端目标合并与清理。release/hotfix 包含 close-out 规定的 tag 与发版推送。
- 只完成当前一个交付，不自动启动下一个 PRP、Bug 或 release。
- 用户明确限制提交、推送或只读时遵守限制。
  - 与 close-out 完成条件冲突时说明并询问，不能声称完成。

确认与暂停：

- 已有有效确认继续适用。
- 除 pr、close-out 入口确认外，其他 decision 按下方 confidence 策略处理，包括目标选择、clarify、设计、roster、测试修改批准与目标调整。
- 低 confidence 需要用户决定时暂停，收到回答后从本次暂停处续办，不要求用户重复调用每个阶段。
- 步骤 6 保存原步骤、内部 intent/subagent、具体 decision 与端点；答复只授权该 decision。
  - 回复后先核现场；端点、方案或范围已变化则重新评分，不复用过时确认。
  - 只拒绝 squash 等可选操作时按原 intent 跳过；拒绝本次交付才保留现场并停止。
- 截止点是本次调用的正常完成边界，不是等待确认；不得自动越过或自动续办被排除的 intent。

步骤 1 先解析策略参数并只读判定路径，核对该路径的 until 合法性；随后才能委托 start 或写入。
先只读核 PR 恢复记录；已命中者进入步骤 2 的恢复路由，不先运行普通身份检查。
未命中且已锁定 adhoc 时先运行 adhoc-status；detached 传入已知 slug，completed 进入 2 的完成路由。
其余情况解析目标 Git 根并运行 doctor、branch，要求 ready。按下列顺序锁定交付：

1. 先由当前 feature/qa/dev、bugfix、hotfix、release 或 adhoc 分支推导在途交付。
   - 任一 kind 的 qa/dev 角色分支归属其 owner；使用 `delivery status` 返回的 `worktrees.owner.path`。
   - 其他分支使用 `git worktree list --porcelain` 中完整分支名对应的已有路径。
2. 再解析本次调用的 target（见下）；有唯一对象时按下文 target 规则锁定或停止。
3. 无 target 时优先锁定用户在对话中指定的交付，否则沿用当前已锁定的交付。

- 从其他目录进入时，只有上下文明确唯一交付目标才可切到它。
  - 多个候选按 confidence 策略选择，不按最近目录猜测；证据仍无法锁定唯一交付则停止并报告。

尚未存在本次交付时委托 `references/start.md`：

- 委托前先核 until；until start 直接进入 5，只报告解析结果，不创建 worktree。
- 已由 target 或用户指定 kind 与 PRP/Bug/版本则直接使用；未指定则按其步骤 1 列出候选。
- 主 Agent 按仓库证据与对话上下文选定唯一目标，按 confidence 策略裁定。
- 不调用初始化或规划流程，不发明 release/hotfix 版本。
- start 成功后回到 1；collab-mode 尚待接手由步骤 2 交接；start 失败或停止则按其交接结束，不回 1。
  - start 内部到 until 时直接进入 5，不重复委托 start；已完成的启动产物如实保留。

已有交付与 start 返回后：

- ❌ 已有交付缺少 worktree 时停止，不能重新 start、抢占 checkout 或临时创建另一套分支绕过。
  - 该限制用于仍需 owner 写入或补验的交付；PR 已合并后的清理、发布或 backmerge 按恢复记录从主路径续办。
- start 返回后使用其 owner 与 roles，再创建 Goal。
- 记录 owner 分支与仓库的绝对路径、Git common dir，以及不会被 close-out 删除的主 worktree 路径。

### target

位置参数至多一个；第二个及以后的非 option token 停止并询问。

已知 option 为 `--manual`、`--until`、`--stop-at`、`--yolo` 与下表各项。
除这些外，以 `--` 开头的 token 不是 target，视为未知调用参数并停止。

| option | 取值 |
| --- | --- |
| `--roster` | `solo` / `min-tdd` / `competing-pair` / `coop-pair` |
| `--qa-strategy` / `--dev-strategy` / `--review-strategy` | 后跟一个取值 |
| `--write-tests-model` / `--implement-model` / `--code-review-model` | 每个 `--*-model` 后跟一个 token |

- 尚未 start 时把 `--roster` 转交给 start；已有交付再带 `--roster` 则停止。
- 委托 start、design、code-review 时原样转交细项。
- `--manual` 与 target 互斥；已有交付仅当 `manual: true` 时允许沿用该参数，否则停止。
- 省略 target 时不在此步选型，继续上方既有锁定规则。

按下列顺序自动分辨 Proposal 与 Bug，命中唯一对象即停止：

1. 完整 ID：符合 `prp-<4 位字符>` 则为 Proposal；符合 `bug-<4 位字符>` 则为 Bug。
2. 否则运行 `list --repo "$REPO_ROOT"`（proposal 与 bug，不限 status），在返回的 `id` 中精确匹配。
   - 仍无则用去掉 `prp-`/`bug-` 前缀的本体、以及 `path` 文件名中的 slug 各匹配一次。
   - 不匹配 title，不把 jot ID、SemVer 或路径当成功值。
3. 按唯一命中的对象处理：
   - 唯一命中 Proposal → feature，将该 PRP ID 交给 start。Proposal 对象
     已有在途交付则报告错误并停止，不续办、不重新 start；以 `list` 的 `in_progress` 为准。
   - 唯一命中 Bug：本地已存在 `bugfix/<Bug ID>` 或其 worktree 时，该 bugfix 为在途交付；
     若当前已锁定另一交付则报告错误并停止，不续办、不重新 start。
   - 唯一命中 Bug，当前已锁定 release 或 hotfix、Bug 为 active `open` 且无上述 bugfix 分支；
     此时不 start、不改绑，将该 Bug 记入本次剩余开发工作。
   - 唯一命中 Bug 的其他情况 → bugfix，将该 Bug ID 交给 start。

- 零命中、跨类型或多对象命中时按 confidence 策略裁定；关键事实缺失时停止，不猜测。
- 完整 ID 形态合法但 `list` 无此对象时报告缺失并停止。
- target 与当前已锁定的另一交付冲突时报告错误并停止，不改绑。

### 截止点与自动裁定

入口先读取 `references/deliver-policy.md`，解析 until / stop-at / yolo，再执行任何委托。
在每次内部委托、并行分派和 decision 前应用同一策略；传入当前事件、调用栈与有效截止点。
Jev 可选加速与 confidence 的输入、阈值、fallback 和确认返回均由该策略规定。

### Goal

Goal 指宿主提供的目标/待办设施（如 Cursor 的 CreateGoal/UpdateGoal）。
宿主没有该设施时跳过本节全部 Goal 操作，改在步骤 5 的最终报告中说明进度与完成判据。

- 锁定交付与 owner 后，为本次调用创建 Goal；until start 不创建 owner 或交付 Goal。
- objective 写明交付标识、有效 until 与完成判据；含父 intent 内部被截止的实际子步骤。
- 每次 deliver 会话只创建一次；同范围续办时不重建。已有同一交付、同一范围的未完成 Goal 时复用。
- 已有其他或更大范围的 active Goal 时不覆盖、不提前完成、不另建冲突 Goal；只报告本次范围进度。
  - 允许进入 pr 时，按 [Goal 与持续推进](pr.md#goal-与持续推进) 核验阶段完成或复用父 Goal。
  - 更大范围 Goal 纳入本次收口及完成判据，保留其余目标；close-out 完成不代表父 Goal 完成。
- 内部委托传入该 Goal，子 intent 不得提前将它置 complete；正常等待保持 active；暂停、预算限制与阻塞按宿主规则处理，不假称完成。
- 仅本次创建或同范围复用的 Goal 可在步骤 5 置 complete：核验允许工作已完成且未越过截止点。
  无截止点时核对 close-out 实际成功后才置 complete；证据不足或部分失败时保持 active。
- 到 until 仅表示本次范围完成，不声称交付已收口，也不勾选因内部截止而未完成的父 intent。

### 从当前证据选择剩余工作

步骤 2 结合 `objectives.md` 勾选、`delivery.json` 身份、对话确认、未完成子步骤、
产物、Git 历史及执行者状态判断。按下表自上而下命中即停止，不并行套用多行。
先应用 until 截止点，再查表；进入 pr、close-out 前按 deliver-policy 核用户确认；任何表内委托、回退或重试都不得越过截止点。

- **进度只认 objectives 勾选**；不以 `gates/*.json` 或一次 `delivery check` 选型。
  - report（code-review.md / verification-report.json / fact-audit.md）只证明做过与声称结果。
- 角色尚在时从对应 qa/dev worktree 读取各路提交与交接说明，不因 owner 尚未合入就重复分派。
- 角色已集成并清理时读取 owner 的两路证据，不把正常清理当作缺失而重建角色。
- 已有执行者先接续并等待，不另起第二个 Agent 操作同一角色 worktree。

选型含语义 decision 时按上方 confidence 策略评分；objectives 已明确的确定性选型直接查表。

- Execute 已打开 verify 小 loop 时，先恢复其原 scope/选题与待修绿/待复审状态，完成后才返回 Select。
- 不因 code-review 退勾提前选择该 intent；原 verify 负责先修绿再派 1 人增量审查。
- 恢复使用已有调用栈、objectives 续办备注或草稿，不新增 gate；无法恢复原范围时停止报告。
- PR 已提交但尚未完成收口时，即使 objectives 全勾，也按 PR 恢复路由续办，不进入完成报告。
- PR 返工上下文优先于普通选择表；每次仍先核当前 until，再补齐该父流程的未完成子步骤。
  - 保留原 PR/MR 与返回位置；补审补测完成后恢复 pr 更新原 PR 并轮询，不重新准备整套发布材料。
  - 原 source 已删除或 owner detached 的清理恢复从主 worktree 带原 source 续办，不要求缺失的 owner branch。


| 当前状态 | 后续处理 |
| --- | --- |
| start 未完成 | 续办 start，锁定其返回路径 |
| release 缺 integrate checklist 项或正文未写工作线 | 停止；须有 integrate 项且工作线四选一 |
| release collab-mode 联调未完成且尚待接手 | 按 `collab-mode.md` 交接并结束；保留未完成进度与 Goal |
| release integrate 未勾 | 执行 `$mdf integrate`；同 worktree / collab-mode 不开通道；不联调不得留未勾 |
| `needs_design: yes` 且 design 未勾 | 在 owner 委托 `references/design.md` |
| roster ≥1、未完成路数 ≥2 且前置满足 | 并行委托 write-tests / implement |
| roster ≥1 且全部 qa/dev 中恰好一路未完成 | 主 Agent 用 git -C 续办，不切会话 |
| `needs_design: yes` 且 roster `0,0`，write-tests/implement 未勾 | owner 串行 write-tests → implement |
| objectives 的 owner 开发项未勾 | owner 按 objectives 完成开发（`has_dev: no` 时该项须已由 start 预勾） |
| owner 开发（或等价开发项）已勾且 converge 未勾 | 在 owner 委托 `references/converge.md` |
| release 跨 worktree 联调且对端验收未通过 | 保持通道，send 本端结果并等对端；不进入审查 |
| release 联调且尚未确认无更多代码修改 | 按所选模式确认两端冻结；collab-mode 由接手 Agent 核实；不进入审查 |
| converge 已勾（或无未勾 converge 项）、lint 未勾 | owner 委托 `references/lint.md` |
| lint 已勾、code-review 未勾 | owner 委托 `code-review.md`（release 另须 integrate 已勾） |
| code-review 已勾、verify branch 未勾 | 委托 `references/verify.md`（branch；失败现场修到绿） |
| verify branch 已勾、配置了 hook 但尚未执行 | 按 pre-gitflow-finish 执行；按实际改动补审补测或进入 fact |
| verify branch 已勾、fact audit 未勾且无待修复结论 | 核 hook 状态；委托 fact-audit，返回 Select |
| fact audit 已报告可修 finding，尚未通过 | 核 until 后委托 fact-update，按其内部审阅交接 |
| fact 已勾、PR mode 且 pr 尚未完成 | 委托 `references/pr.md`，等待 merged、合并核验与关联 CI 收尾通过；完成后回 Select |
| fact 已勾、local 或 pr 已实际完成，close-out 尚未实际完成 | 在 owner 委托 `references/close-out.md`；全勾但 Git 未完成也续办 |
| close-out 实际完成 | 进入 5，不因 owner 已 detached 而重新识别新任务 |

剩余工作与失败处理：

- fact 前的 hook 读取 [pre-gitflow-finish](pre-gitflow-finish.md)；失败仅汇报，
  非文档改动退勾后回到本表补审补测；已执行的 hook 不因补测或 fact 重审而重跑。
- release/hotfix 可修 Bug：不另开 bugfix，不写 bugfix child Change。
- 步骤 3 的被委托 intent 完成后返回 2；各 intent 的“结束”只结束该次内部委托，不结束 deliver。
- close-out 返回「待主链外续办」时结束该调用栈并返回 Select；保留已齐审查与修复窗。
  - 在 close-out 外恢复 code-review、原验证与 fact 后再续办收口，不在 close-out 内绕跑 verify。
  - PR/MR 轮询收到可修 review/CI 反馈或冲突时同样返回 Select；修复并补审补测后更新原 PR/MR，继续轮询。

- 内部委托到 until 时逐层返回截止点与未完成子步骤，直接进入 5；不把截止当作失败或自动重试。
- fact audit 的可修 finding 交回 Select；外部阻塞、缺证据或低 confidence 待确认不擅自启动 fact update。
- 步骤失败时遵守原流程的恢复和停止条件，不无限重试无进展的失败。

### 并行委托与 worktree 身份

并行阶段读取 `references/write-tests.md` 与 `references/implement.md`。

步骤 4：所有在 until 边界内、当前可并行且互不依赖的 intent 必须分别交给 subagent，不由主 Agent 串行代做。

- roster ≥1 时并行组合为全部 qa 的 write-tests 与全部 dev 的 implement。
  - 须已确认并提交同一 design 与共享底座。
- qa 与 dev 互不传入路径；同侧多路亦互不传入兄弟路径。
- 两路已有一条运行时，等待其结果并启动另一条可执行的空闲路；不得重复创建执行者。
- 仅一路未完成走步骤 3，由主 Agent 用该角色绝对路径与 `git -C` 续办，不走步骤 4。
  - 禁止把主 Agent 会话切离 owner，禁止 `move_agent_to_root`。
- 步骤 4 的 subagent 按其 intent 用角色绝对路径操作，不切会话根；禁止新建
  worktree、禁止切到 owner、禁止要求用户切换；禁止 `move_agent_to_root`。
  - roster `0,0` 不走步骤 4。
- 不把有前后依赖的 converge、code-review、fact update、close-out 并行；同一可写 worktree 不并发派工。
  - code-review 的 reviewer 严格只读，通过会话返回独立报告；全部齐全后 main Agent 才核实、修复。
- design 与 converge 不走步骤 4；由各 intent 自行启动恰好 1 个 owner subagent。
  - 主 Agent 委托原 intent 后等待其完成，期间不写入 owner。
- code-review 内部按其契约的本轮应派人数启动独立 subagent 审查，按其契约执行，主 Agent 汇总修复。
  - reviewer 不写文件、不运行 tests；main Agent 核实 finding 并构建 failing test。
- 分派时只把该 intent 在 roster.models 中的值写入对应任务，按口语描述现场解析（可多个模型）。
  - 没有该键则该路不提模型或 effort。
  - 不得把其他 intent 的模型写入本路任务。
- 资源不足时等待已有执行者释放；无法提供所需 subagent 能力时报告阻塞，不悄悄降级串行。

分派前主 Agent 从 owner 的 `delivery status` 取得现有绝对路径与分支名：

- 规范化后的 owner、qa、dev 路径必须两两不同，且与 Git worktree 清单中的分支绑定一致。
- 固定本轮 owner 的 design 基线提交；并行期间不推进 owner，不修改目标、设计或共享底座。
- 每个任务明确传入下列内容，不能只给相对目录或角色名称：
  - MDF_ROOT、owner 路径及分支、角色绝对 worktree、预期完整分支名。
  - Git common dir、设计提交、对应 intent、读写边界与完成证据。

| subagent | 必须使用的路径与分支 | 写入职责 |
| --- | --- | --- |
| write-tests | `worktrees.qa` 项的 path/branch（index 1 如 `qa/feature/<slug>`） | 测试、配置及阶段证据 |
| implement | `worktrees.dev` 项的 path/branch（index 1 如 `dev/feature/<slug>`） | 实现及阶段证据 |
| code-review 的审查者 | owner 的同一绝对路径与固定 review_head | 严格只读；不运行 tests，由 main Agent 落盘报告，不建立角色 worktree |

主 Agent 分派前，以及 qa/dev 首次操作时运行内部 CLI：

- `worktree-check --repo <角色绝对路径> --owner <owner绝对路径> --role <qa|dev> [--index N]`。
- 脚本核对 Git 根、完整分支名、worktree 清单绑定与 Git common dir；不匹配则停止，不写入。
- 角色依原 intent no-ff merge owner 后，追加 `--design-commit <固定设计提交>`
  再检查共同基线与 fingerprint。
- main Agent 替审查者核对 `--role owner --expected-head <review_head>`；reviewer 仅接收只读任务。

路径约束：

- 所有命令显式指定该 worktree 的工作目录或 `git -C`，文件写入使用该 worktree 下的绝对路径。
- 不得假设 subagent 继承主 Agent cwd；工具自动分配的其他 worktree 不替代 MDF 角色树。
- 仅 Cursor 主 Agent 可按 `common.md` 调用 `move_agent_to_root`；其他宿主与
  subagent 一律绝对路径绑定，横幅随绑定的 worktree 更新。
- 不能绑定并验证指定路径时停止，不在默认目录开工。
- main Agent 验证 reviewer 的 owner 与 review_head；reviewer 严格只读，main Agent 负责复现与报告落盘。

### 等待、交接与收口

等待：

- 主 Agent 等待所有已派阶段完成或明确阻塞，不在任一路仍运行时执行 converge 或删除角色 worktree。
- 任一路到 until 时，先等其他已派写入者完成或暂停到可交接点，再进入 Report；不跨界续办。
- 子 intent 的低 confidence decision 返回主 Agent 的步骤 6；保留其任务与精确 resume 位置。
  - 无依赖的其他路可继续；共用设计、目标或测试契约的 decision 未决时，先暂停受影响的写入者。
  - 用户确认后 resume 同一 subagent，不创建第二个执行者，也不由主 Agent 代写。
- 一条失败时保留另一条已完成产物；如需修改共同设计，先暂停所有仍在写入的执行者。

交接：

- 各路交接报告实际绝对路径、分支、最终提交 hash、验证/自检结果及未解决项。
- 主 Agent 对各路再次调用同一 worktree-check，传入固定设计提交并追加 `--handoff`。
  - 脚本检查 clean、共同设计，以及 tests（qa）或 implementation（dev）内容是否已提交。
  - ❌ 不以 gate 文件是否存在判定阶段完成。
- 失败保留现场，不以 subagent 的“完成”摘要替代检查；全部交接通过后返回 2 进入 converge。
  - owner 在进入 converge 前确认 write-tests / implement 已在 objectives 勾选。
- implement 以未决交回测试争议时由主 Agent 按 confidence 策略裁定，
  按裁定续办对应路；改测试按 `delivery-contract.md`「修改与提交权限」取得批准。
- 合并、测试修改批准、worktree 清理均委托 converge 原流程，不手工 cherry-pick 或删除角色来冒充集成。

完成判定：到 until 与交付实际收口分别核验，单阶段结束不能代替其余范围的完成证据。

- 到 until 时核对允许操作的证据与仍在运行的执行者，报告已完成阶段、截止点与剩余工作。
  - 内部截止时列出尚未完成的父 intent 与 resume 子步骤，不要求父 intent 冒充完成。
  - 不勾选被排除 intent、不执行 close-out、不声称交付已收口；不自动调用 next 或另开 deliver 越过截止点。
- 无截止点时，步骤 5 必须取得 close-out 的实际成功结果。
  - 按分支核对合并、源分支删除，以及 release/hotfix 的 tag 和推送；owner 仍存在时核对其 detached 状态。
  - PR mode 另核远端 source 已删除及 remote_deleted=true；远端清理失败或不确定时不完成 Goal、不删除保留的 owner。
  - owner 已被外部删除时如实报告，以操作记录与实际 Git 完成证据核收口，不重建工作区，也不再执行删除。
  - 用步骤 1 固定的主 worktree 核对，不依赖 owner 的分支身份。
- 若 close-out 部分失败，记录已完成操作与未完成项，按其恢复规则交接，不重放已经发生的发布操作。
- 报告本次完成的阶段、验证、Git 结果或具体阻塞，以及所有仍存活的 subagent 和未完成交接。
- 仅在实际 close-out 完成且核验、Goal 与报告完成后，按 confidence 策略决定是否删除保留的 owner 工作区。
  - 拒绝或未决时保留，不影响交付完成；到 until 时不清理尚在交付中的 owner。
  - 自动裁定或用户确认删除后，按 `references/close-out.md` 将删除命令作为最后一次 tool call，
    并说明本对话不要再继续。
- 上下文恢复时用上述现有产物与实际 Git 状态重新核验，不依赖未落地的内存完成标志。
