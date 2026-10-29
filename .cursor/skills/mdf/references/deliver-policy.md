# Deliver Policy

树形：not-tree。由 deliver 的入口、intent 委托与 decision 事件触发；不执行交付阶段。

## 工作流（唯一执行契约）

读取 `references/common.md` 的 Jev 条款；只应用本页条款，不执行 common 的业务工作流。
本页随 deliver 上下文传给所有内部 intent 与 subagent；独立 intent / 普通 next 不应用。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve context | 约束 | 核调用参数、路径与当前事件 | 调用、交付身份、事件 | 2 | 参数错误或缺上下文则停止 |
| 2 | Apply policy | 约束 | 应用截止或 decision 策略 | 边界、评分、确认 | 3 | 截止返回；待确认交 deliver 6；阻塞停 |
| 3 | Return | 约束 | 返回允许、截止或实际阻塞 | 裁定、依据、返回位置 | 返回原步骤 | 缺证据不允许执行 |

## 术语与数据结构

### until 截止点

本节在任何写入或分派前确定本次调用的执行边界。

- `--until <intent>` 与 `--stop-at <intent>` 是同一个 option；截止点为 exclusive，不执行该 intent。
- 默认 local 与 PR mode 均无截止点，直到 close-out 完成；非 yolo 的入口确认见下节。
- 显式 `--until pr` 排除 pr 及 close-out；显式 `--until close-out` 允许 pr 等到 merged 后停止。
- local 不接受 `--until pr`；pr 不在该路径中。
- `--yolo` 未显式指定 until 时无截止点；显式 until 仍生效，包括 `--yolo --until close-out`。
- 缺值、未知 intent、重复指定（含混用两个别名）均停止并说明参数错误；写入或 start 之前完成解析。
- 多词 intent 须作为单个值传入，如 `--until "fact audit"`。

| 交付路径 | 可用截止点与调用关系 |
| --- | --- |
| 普通交付前段 | start（联调时内部 integrate）→ design → write-tests / implement → converge |
| 普通交付后段 | lint → code-review → verify → fact audit → 必要时 fact update（内部 fact audit）→ [pr（仅 PR mode）] → close-out |
| 人工 feature | start → lint → code-review → verify → fact update（内部 fact audit）→ [pr（仅 PR mode）] → close-out |
| 已有 adhoc | 工作 → lint → code-review → verify → fact audit → 必要时 fact update（内部 fact audit）→ [pr（仅 PR mode）] → close-out |
| 条件性子 intent | clarify（start/design）；squash（local close-out / pr）；bug close（release/hotfix 的 local close-out / pr） |

- 只读解析目标时确定路径；不适用该路径的 intent 报参数错误，不悄悄忽略，不先执行 start。
  - 工作是 adhoc 的账本项，不是 intent；子 intent 按括号中的调用位置判断边界，不另启动调用方。
- 可选阶段未启用时仍保留其顺序位置：到该位置即停，不越过它进入后续 intent。
- 无独立 implement 项的 owner 开发项对应 implement 的边界位置，不改变原阶段执行方式。
- qa/dev 的截止先后按 write-tests → implement 判断；只用于边界，不改变两路可并行的执行规则。
- 边界包括嵌套 intent；禁止用父 intent 包装来执行被排除的 intent。
  - until integrate 允许 start 建树，但 start 进入内部 integrate 前须返回截止点。
  - until verify 也排除 converge、code-review 等内部调用的 verify，父 intent 保留未完成子步骤。
  - manual 的 until fact audit 允许 fact update 对齐并提交事实页，在内部 Audit 前返回截止点。
- 普通/adhoc 的 until fact update 可完成前置 audit，需要 update 时先停住。
  - audit 无须修复时也在 update 的顺序位置停住，不继续 close-out；manual 则不进入 fact update。
  - audit 有 finding 时如实报告未解决项，不把到达截止点当作 fact 已通过，不代勾 fact。
  - 正常允许 update 时，修复后仍返回 audit 重审；返工也逐次检查 until，不豁免被排除的 intent。
- fact 之前的 hook 归该路径的外层 fact 入口：普通/adhoc 为 audit，manual 为 update。
  until 排除该外层入口时也不执行 hook；内部 audit 截止不回滚此前合法的 hook 或事实提交。
- 每次 Select、内部委托和并行分派前先核边界；只允许截止点之前的 intent 运行。
  - until implement 时可完成 write-tests，不启动 implement；until write-tests 时两路都不分派。
  - 同时允许 qa/dev 时仍按步骤 4 并行；只剩一路在边界内时走步骤 3。
  - 人工与 adhoc 的替代选择表同样受边界约束，不得一次委托整个剩余流程绕过截止点。
- 续办时已到或超过截止点则只核验并报告，不重做已完成阶段、不回退或继续写入。
  until start 时仅解析与只读检查，不启动 start。
- 所有内部 intent 遇到边界都返回「到 until」、调用栈与 resume 位置，不勾选被截断的父阶段。
  不把该返回当作失败，不重试或换另一入口继续；deliver 直接到 Report。

### pr 与 close-out 入口确认

先核 until，再核本节确认；被截止的 intent 不询问、不执行。

- 非 yolo 在进入 pr、close-out 前分别取得用户明确确认，不以高 confidence 自动通过。
  - PR mode 需要两次独立确认；local 只需 close-out 入口确认。
  - 调用 deliver 本身不代替入口确认；pr 的确认不授权后续 close-out。
- 进入前展示当前成果、验证结果、目标分支及该 intent 将执行的操作，然后返回 deliver 步骤 6 等待答复。
  - pr 确认发生在候选材料准备、push、创建或更新 PR/MR、轮询之前。
  - close-out 确认发生在其材料、发布、backmerge、清理或 Gitflow 操作之前；PR mode 先完成 pr 的合并与 CI 核验。
- 确认记入现有交接材料，绑定当前交付、intent 与操作范围，不新增状态文件。
  - 同一范围的返工、重试或中断恢复复用已有有效确认，不逐轮重复询问；范围变化须重新确认。
  - 用户未确认或拒绝进入时保留现场并暂停；不得换用 next、独立 intent 或内部委托绕过。
- `--yolo` 跳过这两个入口确认；显式 until、用户限制、验收要求与死硬阻塞仍生效。
- 本节适用于普通、manual、adhoc 及 PR 恢复路由；独立 pr / close-out 与普通 next 不增加这些确认。

### 自动裁定与 confidence

所有 deliver 默认启用本策略；独立 intent 与普通 next 不受影响。

- 每项 decision 记录问题、候选方案、选定方案、证据、理由、评分来源及 confidence（有限数，范围 `[0,1]`）。
  - 写入现有阶段材料、objectives 交接说明或最终摘要，不新增统一状态文件。
  - decision 指目标、方案、确认、批准、选择等语义裁定；确定性 CLI 结果读取不需重复评分。
  - 主 Agent 对最终裁定负责；内部 intent / subagent 的新 decision 同样适用，不得以委托绕过评分。
  - 沿用有效确认，不对同一未变化的 decision 反复评分；新证据、范围或方案变化时重新评分。
- 默认用 Jev `score` 计算 confidence；state 含问题、候选、所选方案、支持/反对证据、约束与不确定项。
  - 评分任务明确为所选 decision 满足目标与约束的 confidence，标尺为 `[0,1]`；不拿偏好或质量分替代。
  - 属本 intent 声明的可选加速，遵守 common.md 的可用性规则；不空探测。
  - 无 Jev、认证/调用失败或结果缺失、越界、非有限数时，由主 Agent 计算并记录 confidence。
  - Jev 有效评分低于阈值时不得改用主 Agent 重新打高分来绕过确认。
- `confidence >= 0.8` 自动确认并继续；`confidence < 0.8` 进入步骤 6，请求用户确认后才执行。
  - 用原始分数比较，不四舍五入抬过阈值；布尔值、字符串或不符合工具 schema 的结果不算有效评分。
  - 无法形成有效评分时也进入步骤 6；不把缺失评分当作高 confidence。
  - 展示方案、分数、关键依据与不确定项；用户确认后续办原 decision，拒绝按原 intent 的拒绝去向处理。
- `--yolo` 无 confidence 限制：不要求评分、不因低 confidence 询问，由主 Agent 自裁定并记录理由。
- 内部 clarify、manual slug、Gitflow 收口与收尾删除 worktree 的决定均遵守本策略。
  - squash 默认按其契约自主分析执行，不增加逐次计划确认；范围或归属不明仍须澄清。
  - pr、close-out 的入口确认优先于 confidence 策略；进入后不增加固定 Gitflow 确认关口。
  - 人工实际工作仍须由用户完成并显式勾选，所有模式均不得代勾。
  - converge 的 `--test-approval` 记录该裁定、评分或用户确认与理由。
- 本策略覆盖子 intent 的询问与确认要求，不覆盖用户明令禁止、关键事实缺失、外部条件与验收要求。
  ❌ 不得削弱验收或把未实现目标判为完成。
- 进入子 intent 时明确传入本策略与 yolo 状态；低 confidence 不得交给其普通用户询问循环或强行自裁定。
  子 intent/subagent 向 deliver 步骤 6 交出未决与精确 resume 位置，确认后续办同一执行者。

不可恢复的死硬阻塞仍停止：

- CLI/Git/工具不可恢复失败。
- 无可启动目标（未指定人工 feature，且无合格 ready PRP、无合格 open Bug，
  也未指定合法 release/hotfix 版本）。
- 已有交付缺少 worktree。
  - 仅指仍需 owner 修改或提交的交付；PR 已合并后的清理、发布或 backmerge 可按原操作记录从主路径恢复。
- 用户明确只读或禁止提交/推送且与完成条件冲突。
- 必须切换 worktree 但宿主无法由 Agent 完成。
- 当前允许执行的步骤所必需的凭据、origin 一致性等仓库外条件缺失。
  - start 已确认准备安排、仅后续阶段首次使用的资源不提前阻塞；到首次使用时仍未就绪则停止。
  - 准备安排按 [start 的前置条件盘点](start.md#前置条件盘点) 记录；confidence 与 `--yolo` 不替代实际资源。
- 同一失败连续三轮无进展。
- 不改写用户明确禁止的范围就无法继续。

多个在途交付仍无法唯一锁定时也停止；yolo 不凭空补造版本、目标或凭据。
