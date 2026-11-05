# Adhoc

`$mdf adhoc [<工作描述>]` 在临时 worktree 中连续完成一次小工作，直到按配置收口。
其他已有分支也可归为 adhoc；没有交付账本时，pr / close-out 按 [无账本 Adhoc 收口](adhoc-change.md) 接管。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 已锁定 PR 恢复 ────→ [委托 PR 并返回]
                 ├──── 范围不明 ──────────→ [询问缺项]
                 ├──── 未就绪 ────────────→ [停止并报告]
                 │
                 ▼ 目标与范围已定
┌──────────────────────────────────┐
│ 2 Prepare                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 启动或绑定失败 ────→ [保留现场并报告]
                 │
                 ▼ owner 已绑定
┌──────────────────────────────────┐
│ 3 Select                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 未完且无账本 ──────→ 4 Execute
                 ├──── 完成或无增量 ──────→ [报告并结束]
                 ├──── 身份或账本不符 ────→ [停止并报告]
                 │
                 ▼ 下一步骤已确定
┌──────────────────────────────────┐
│ 4 Execute                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 直调完成或须补前置 ────→ 3 Select
                 ├──── 委托完成或须补前置 ────→ [返回调用方]
                 └──── 阻塞或待确认 ──────────→ [按原阶段交接]
```

## 工作流（唯一执行契约）

PR 恢复优先：按 [PR 的恢复路由](pr.md) 核原 source 的操作记录与返工备注。
命中时未 merged 恢复父 pr，已 merged 续办 close-out，不先要求 adhoc-status 通过；无 PR 恢复时才执行下表与六项账本选型。

读取 `references/common.md` 与 `references/delivery-contract.md`；本页专用条款优先于普通交付主线。
不执行 start 的 clarify、PRP 选择或 roster 确认。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve | 约束 | 先核 PR 恢复；否则核目标、work 与 ready | 记录或上下文、doctor | PR 委托并返回；其余2 | 范围不明询问；其余停 |
| 2 | Prepare | 脚本 | 复用已知 owner，或自动命名创建；运行 adhoc-status | 身份、work、绝对路径 | 3 | 保留现场并报告 |
| 3 | Select | 脚本 | adhoc-status 按模式选下一项 | 身份、材料模式、Git | 未完 4；完成或无增量结束 | 身份或账本不符则停 |
| 4 | Execute | 约束 | 按阶段表执行并交接 | 产物、账本、缺项 | 直调 3；委托返回 | 补前置同路由；阻塞交接 |

## 术语与数据结构

PR mode 的 pr 候选项已勾时仍先核平台实际状态；未 merged 继续 pr，merged 后必选无 checkbox 的 close-out。
已完成收口须有 finish-gitflow 的实际完成证据，不以 checklist 全勾跳过续办。

### PR mode 的收尾步骤

按 [交付契约](delivery-contract.md#pr-mode-的收尾步骤) 生成和续办 objectives。
PR mode 末尾为 pr checkbox 与无 checkbox 的 close-out；local 保持原顺序。

### 范围与启动

本节规定临时工作的授权、命名和工作区落点。

- 工作可以是代码、测试、文档、配置或其他已说明的需求，不绑定 PRP 或 Bug。
- 新工作描述取自本次参数或已明确的对话上下文；既有工作从 `delivery.json.work` 恢复。
  - 描述写实际工作与已有约束、验收，不只写 slug；无需再次确认。
  - 当前未完工作与新描述不一致时询问归属，不覆盖原目标。
- 显式 adhoc 授权完成六项步骤及必要本地提交、集成和收口。
  - PR mode 由 pr 提交并等待 merged；随后执行 close-out 的合并后续办。
  - objectives 内容、slug 与固定 roster 直接生成，不另做确认。
  - 目标变更与测试门槛批准仍沿用各 intent 规则。
- 已绑定本次 adhoc 时先用 adhoc-status 核对；completed 直接报告，不要求仍在原分支。
  - 当前为无账本 adhoc 时保留真实分支与工作区；步骤 3 按 status.next_step 选择 pr 或 close-out，不重新 start。
  - 步骤 4 委托所选 intent，由其调用 adhoc-change；无账本不套用下方六项账本与勾选条款。
  - detached 现场必须有上下文已知 slug；缺失或不能证明收口时停止，不猜测身份或重新 start。
  - 用户明确发起不同新工作且旧工作已完成时，用返回的 primary_worktree 新建。
    不复用旧目标或工作区。
- 新建或续办未完成工作时运行 doctor 与 branch。
  要求 ready、`normal_workflows_allowed: true`。
  - 新建前检查源工作区 clean 与本地 develop 存在。
  - 不能把已有改动搬走或提交来满足 clean；失败保留现场。
  - 已有其他交付时先明确目标，不把其改动混入新任务。
- Agent 自行选与需求相关且不冲突的 slug，不要求用户指定格式或确认。
  - CLI 将 `--name` 规范化为材料目录可用的 slug；冲突时另选相关名称，不覆盖既有材料。
- 运行 `mdf.py start --repo <仓库> --kind adhoc --name <名称> --work <工作描述>`。
  - 从本地 develop 创建 `adhoc/<slug>` 与 `<repo-name>-worktrees/adhoc/<slug>`。
  - 不 fetch、不 push；有 origin 时沿用 start 的基线覆盖检查。
  - 固定 roster `0,0,1`，`needs_design: false`；不建立 qa/dev 角色树。
- CLI 写入并提交 `changes/unreleased/<slug>/delivery.json` 与 `objectives.md`。
  - delivery 的 `work` 保存实际工作描述；跨会话续办及 code-review 均以此为准。
  - 账本直接使用 `assets/templates/adhoc-objectives.md`，初始六项均未勾。
  - 不要求 design、converge、人工工作确认或额外的 start checklist 项。
- start 返回的 command hook 已由 Core 执行。pending rule 由 Agent 在返回的 cwd 读取 path 并执行。
  - 使用返回的 new_worktree、old_worktree 上下文；执行前后记录名称、路径、cwd、结果及日志。
  - hook 失败仅汇报，保留分支、worktree 与提交，不自动重试。
- 按 common 的「切换工作区」绑定返回的绝对 owner 路径；后续只在该 worktree 工作。
  - 已有交付复用已绑定路径或 worktree 清单中的完整分支绑定；缺树时停止，不重新 start。

### 只读状态与完成证据

本节用固化 CLI 核对当前身份、下一步及 close-out 的实际结果。

- 运行 `mdf.py adhoc-status --repo <owner> [--slug <已知slug>]`，回读 `result`。
  - 活跃分支可省略 slug；detached 时必须显式传入，不从目录名或其他任务猜测。
  - `delivery` 含 work、roster、start_commit；`next_step` 来自原有六项账本。
  - CLI 拒绝缺失工作描述、非 solo、绑定对象、design 或越序勾选，具体差异报告后停止。
- `completed: true` 须同时满足：
  - 账本全勾，源分支已删除。
  - owner 已 detached，HEAD 是 develop 的 no-ff merge 非首父。
  - detached owner 须 clean；有本地改动时停止，不将改过的工作描述或账本当成已交付内容。
  - `merge_commit` 是 develop 第一父链中的实际 merge；返回 primary_worktree 供调用方复核。
  - 账本全勾且仍在源分支时：local 返回 close-out；PR mode 未核验 merged 返回 pr，已核验则 close-out。
- 状态只读原有材料与 Git，不创建 gate 或新的 workflow 状态文件。

### 六项账本与续办

本节用唯一 checklist 决定下一项工作。

objectives 的六项必须同序、完整，已勾项形成连续前缀；工作完成后由执行者勾选。

| 清单项 | 执行与完成证据 |
| --- | --- |
| 工作 | owner 完成本次范围，核对成果与必要测试，提交并自勾 |
| lint | 委托 `references/lint.md`；全部 module 工具报告与自勾 |
| code-review | 委托 `references/code-review.md`；1 人独立审查，终稿与自勾 |
| verify smart | 按下节委托 verify；通过的 smart report、自勾与提交 |
| fact audit/update | 按下节审阅，必要时更新；报告结论、自勾与提交 |
| pr（仅 PR mode） | 执行 `references/pr.md`；实际 merged 且核验通过才结束 |
| close-out | 仅此项读取并执行 `references/adhoc-close-out.md`；Change 与实际 Git 完成证据 |

- 默认从首个未勾项执行到实际收口；有效的已完成项不重复执行。
- `$mdf next` 在已启动 adhoc 上仅执行本页步骤 3–4 的一个账本项，然后返回。
  - 不新建 adhoc，不升级为连续执行。
- `$mdf deliver` 在已有 adhoc 上以本表替代普通选择表，每次完成一项返回其 Select。
  - 每次只委托 until 边界内的当前 intent，decision 与完成核验遵守 deliver；无 target 时不凭空新建 adhoc。
- 直调在当前项完成或须补前置时回 3；next / deliver 委托则返回调用方，不在本页继续循环。
  - next 本次报告完成项或返工项后结束；deliver 回自己的 Select，依账本再选下一项。
- 清单全勾仍须核对 close-out 实际成功；PR mode 先核 merged；未 merged 继续 pr，已 merged 或 local 的收尾继续 close-out。
  - 不凭全勾宣称完成，不因正常 detached 状态重新 start。

### Smart 与事实

本节规定两项验收的范围、报告与返工规则。

- verify smart 前工作、lint 与 code-review 均须已勾。按 `references/verify.md` 执行 smart。
  - 相对 start_commit 收集改动，选择涉及 module 与测试；纯文档等无法映射 module 时使用全部 module。
  - 不改用 branch 或 smoke；CLI 成败均保存 `verification-report.json`，`scope: smart`。
  - 通过且必要增量复审完成后自勾 verify smart 并提交；失败读取报告，可修复则按下条返工，外部阻塞则交接。
  - 验证期间改动实现、测试或验证配置时，退勾 code-review 及后续项。
    由 verify 的主链小 loop 在修绿后做 1 人增量复审；必要时再验。
  - code-review 内部 smart 不勾主链 verify smart；审查后仍须执行独立的本项。
- fact audit/update 在 verify smart 已勾后执行。
  - 可选 hook 每次交付只执行一次，失败也不重跑。执行状态不明时先读 CLI 日志，仍不明则询问。
  - 未配置 hook 时直接 audit；已配置且未执行时，在 clean owner 运行下面的 CLI。
    `mdf.py pre-gitflow-finish --repo <owner>`。
  - 返回 hook.status 为 pending 时，在 hook.cwd 读取 hook.path 执行 rule。再检查实际改动。
    `mdf.py pre-gitflow-finish --repo <owner> --after <before_head>`。
  - 读取 changed_paths 与 needs_recheck，并核对内容。仅文档则复核提交，无改动不制造提交。
  - 其他改动退勾 code-review 及后续项，再补审补测。增量审查左端点为原 before_head。
  - hook 失败仅汇报，仍按实际 diff 处理。CLI 现场检查失败则停止，不改分支或改写历史。
  - 按 `references/fact-audit.md` 审阅 branch scope，基线为 start_commit。
  - 需更新时委托 `references/fact-update.md`，沿用其内部审阅；不新增 checklist 项。
  - fact 审阅通过后保存 `fact-audit.md`，自勾 fact audit/update 并提交。
