# Code Review

## 独立 against 审查

`$mdf code-review --against <commit>`：审阅当前 worktree 相对这个 commit。
commit 可以是 branch start、last release，或调用方选定的任意 commit。
Codex 与 Cursor 使用同一 intent，由执行该 intent 的 Agent 加载 Skill 并完成步骤 5–8。

出现 `--against` 时，步骤 1 直接转 5，不运行交付前置检查。
步骤 5–8 是独立只读审查，不进入 Repair 或 Record；未传 against 时执行步骤 1–4。

## 决策树

步骤 1 按参数分流；步骤 5–8 仅由against 参数进入。

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 指定 against     ────────→ 5 Resolve
                 ├──── 来源 verify 且待修绿 ────→ [返回原 verify；独立调用报告待续办]
                 ├──── 已齐审查且修复续办 ──────→ 3 Repair
                 ├──── 已齐审查但勾选未完成 ────→ 4 Record
                 ├──── 已齐审查且无新改动 ──────→ [结束]
                 ├──── 失败或缺失 ──────────────→ [停止并报告]
                 │
                 ▼ 新审查、增量新一轮或首轮未齐
┌──────────────────────────────────┐
│ 2 Review                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 审查未完成 ────→ [停止并报告]
                 │
                 ▼ 本轮审查完成
┌──────────────────────────────────┐
│ 3 Repair                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 修复或验证可修 ────────→ 3 Repair
                 ├──── 需要用户决定 ──────────→ [保留现场并报告]
                 ├──── 外部条件或无法继续 ────→ [保留现场并报告]
                 │
                 ▼ finding 已裁定且无阻断项
┌──────────────────────────────────┐
│ 4 Record                         │
└────────────────┬─────────────────┘
                 │
                 ├──── close-out 委托且需 smart ────→ [交接主链外续办修复窗]
                 ├──── smart 失败且可修 ────────────→ 3 Repair
                 ├──── 其他失败或缺失 ──────────────→ [停止并报告]
                 │
                 ▼ 通过
                 [结束]

步骤 5 仅由步骤 1 的 against 参数分支进入。

┌──────────────────────────────┐
│ 5 Resolve                    │
└──────────────┬───────────────┘
               │
               ├──── 参数不符 ────→ [停止并报告]
               │
               ▼ 参数已核对
┌──────────────────────────────┐
│ 6 Context                    │
└──────────────┬───────────────┘
               │
               ├──── 失败或缺失 ────→ [报告缺项，不继续审查]
               │
               ▼ 上下文完整
┌──────────────────────────────┐
│ 7 Review                     │
└──────────────┬───────────────┘
               │
               ├──── 未完成或工具失败 ────→ 8 Report
               │
               ▼ 记录 findings 与缺项
┌──────────────────────────────┐
│ 8 Report                     │
└──────────────┬───────────────┘
               │
               ├──── 复核命令失败 ──────────→ [报告 error 并停止]
               ├──── context 已变化 ────────→ 6 Context
               ├──── 格式不符且可修 ────────→ 8 Report
               ├──── 格式无法修正 ──────────→ [报告 error 并停止]
               └──── 指纹一致且报告有效 ────→ [返回调用方]
```

## 工作流（唯一执行契约）

步骤 1–4 适用于交付审查；步骤 5–8 适用于独立审查，共用 [Review 协议](reviewer-protocol.md)。
外部报告须核对固定范围、rule、冻结份数和覆盖；不符时仅作补充，不凭 CI pass 自动勾选。

仅交付模式按以下边界读取并执行本阶段；独立模式只读取本页「独立输入与只读边界」。

- 读取 `references/common.md` 与 `references/delivery-contract.md`；涉及 PRP 或 Bug 时读取 `references/object-contract.md`。
- 读取 [项目阶段 rule 契约](project-rules.md)，本阶段按 merge 后规则执行，冲突时 project 优先。
- CLI 使用 `python3 "$MDF_ROOT/scripts/mdf.py"`。
- 独立调用只推进当前 intent；deliver 内部委托时完成后返回调用方，由其选择下一阶段。
- close-out 内部委托时返回 close-out；需要 smart 时返回待主链外续办，不在该调用内补验或 fact。
- 主链 verify 内部委托时返回原 verify 的步骤 5；不接管父阶段的 branch/smart 勾选。
- 覆盖终稿时不得删除 objectives 中父 verify 的非 checklist 续办备注。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 约束 | 先分流，再核交付前置与续办 | 参数或范围、rule、报告 | against参数5；verify待修绿返回；漏勾4；修复续办 3；无新则结束；否则 2 | 停止并报告 |
| 2 | Review | Subagent | 按本轮应派人数启动严格只读 subagent 覆盖本轮 | N 份静态审查、范围与证据 | 3 | 停止并报告 |
| 3 | Repair | 约束 | 主 Agent 裁定、修复、整理 tests 并复核 | 裁定、修复与 suite 验证，无阻断项 | 4 | 可修则留在 3；否则保留现场并报告 |
| 4 | Record | 约束 | 按需 smart；裁定收口则洗成无 commit 终稿并勾选 | 终稿、smart、提交 | 结束 | close-out 需 smart 返回待续办；可修则 3；否则停 |
| 5 | Resolve | 约束 | 核 Git 根、against 参数与仓外日志；拒绝交付与增量参数 | 根、参数、日志目录 | 6 | 停止并报告 |
| 6 | Context | 脚本 | 调用下方 review-context，日志置于 checkout 外 | context.result、范围与规则 | 7 | 读日志，报告缺项并停止 |
| 7 | Review | 约束 | 按固定 context.rules 与 Review 协议静态审查全部 paths | findings、覆盖、incomplete | 8 | 未完成标 needs-review；工具失败标 error，转8 |
| 8 | Report | 约束 | 复核 context 未变，生成并校验 JSON | 两次 context 指纹、校验结果 | 有效则返回 | 变化回6；格式可修留8；其余报 error |

close-out 或主链 verify 已将 code-review 退回 `[ ]` 且传入或保存左端点时，按该范围开启增量新一轮。
旧终稿或目标主线已包含都不代替此轮；进行中草稿只存范围和审查证据，进度仍看 objectives。

## 术语与数据结构

### 独立输入与只读边界

步骤 6 在当前 worktree 调用 `review-context --repo <repo> --against <commit>`。
步骤 7 由执行该 intent 的 Agent 读取仓库，步骤 8 写出报告。
CLI 只提供确定性 context；MDF 不包装额外 Agent，也不把 context 作为 stdin 审阅材料。
CLI 前缀为 `python3 -B "$MDF_ROOT/scripts/mdf.py"`；日志与报告保存在 checkout 外。
步骤 7 使用 [Review 协议](reviewer-protocol.md) 的独立模式，步骤 8 使用
[独立报告 schema](../assets/templates/against-review-report.schema.json)。

- against 解析为固定 SHA，直接比较该版本与当前工作区，不计算 merge-base。
- 包含 staged、unstaged 和未被 Git ignore 的 untracked 普通文件；同一路径以磁盘内容为准。
- rules、sourceset 和 module ignore 均读取当前工作区 snapshot，MDF 协议来自当前安装位置。
- 实现变更先与当前 sourceset 并集求交，再应用 module ignore；文档和交付材料独立按契约纳入。
- 不接受交付、review-base、previous-report 或 backend 参数；无需 ready 或本地交付材料。
- snapshot 在仓外构建并清理，不修改原仓库 HEAD、index、refs、objects，不运行项目 hooks 或 filters。
- 全程只读，不修复、不运行 tests、不 commit、不勾 objectives，不进入交付 Repair/Record。
- findings 提供位置、触发条件、影响、证据与 P0–P3；未完成写 incomplete。
- context/report 记录 against、worktree_sha256、rules_sha256 与 context_sha256。
- 步骤 6 保存 CLI 的 `result` 为 context.json；所有输入、日志和报告均置于 checkout 外。
- 步骤 8 先用原 context.against 的完整 SHA 重跑同一 review-context 命令，核对 context_sha256。
  - 一致才生成报告；不一致则以新 context 回6，再完整审阅；不重新解析原符号 ref，也不复用旧通过结论。
  - 命令失败或无法解析时读取日志并报告 error；没有有效 context 时不伪造 schema 所需字段。
- 调用 `review-report-check --context-file <context.json> --report-file <report.json>` 校验最终报告。
  - 退出 0 且 result.valid 为 true 才返回；格式可修则留8，无法修正则报告 error，不伪造证据。
  - 返回的 decision 原样保留；校验通过不等于语义 pass。
- 经校验的 JSON 通过会话返回，调用方按需保存；不直接 approve 或 merge。


### 项目 rule 的阶段接入

步骤 1 切回 owner 并核对 ready 与范围后，以 `--stage code-review` 加载项目 rule，再判定续办。

- 本步在修复续办、无新改动和仅漏勾等快速出口前执行；规则变化不能沿用旧通过结论。
- 每次分派前核对 rule，每份任务在固定 opening 后完整携带 MDF rule 与 project rule 原文。
- reviewer 报告、进行中草稿与终稿记录来源、内容指纹；主 Agent 按相同规则裁定与修复。
- 已配置时验收每份报告的 rule 来源与指纹，缺失或不一致不得视为完整报告。
  - 未配置时以无项目 rule 核对，无需内容指纹。
- 步骤 4 与无新改动出口验收前重新加载核对，变化先停止说明并等待确认。
- 规则变化确认后走首轮：从固定交付基线审到新 review_head，使用冻结 roster.reviewers。
  - 不复用旧报告，不沿用原增量范围或修复窗；旧问题清单仍传入作复核上下文。

### 范围与前置条件

进入步骤 2 前，objectives 的 lint 项须已勾选并提交；增量轮核对最近验证中的 lint 结果。

本节确定审查人数、记录位置、轮次、固定基线与各分支前置条件。

无账本 adhoc 的收口审查按 adhoc-change.md 的 Check 条款执行；不套用本节的账本、roster 配置或勾选前置。
独立 against 审查始终执行步骤 5–8。

- 步骤 1 支持 feature、bugfix、hotfix、release、adhoc；cwd 为 qa/dev 时切回 owner。
- 先确认目标仓库 ready，读取已有审查记录，识别相关未提交改动并按公共规则提交。
- 审查人数取冻结 roster.reviewers：
  - 有 `delivery.json` 时用 `delivery status`，否则读 `branch.<owner>.mdf-roster`；未冻结则停止。
  - 本轮应派人数默认同 roster.reviewers。
  - close-out 集成或主链 verify 修绿产生的增量新一轮为 1，不改冻结 roster。
  - 无有效上轮记录而走首轮时仍用 roster.reviewers。
- 审查记录写在 `changes/unreleased/<slug>/code-review.md`：
  - PR mode 的 release/hotfix 若已准备 `changes/<version>/delivery.json`，本轮使用该版本目录的材料、objectives 和报告。
    PR/MR 合并前可补审修订；不另建 unreleased 副本。候选流程见 [PR](pr.md)。
  - feature/adhoc 用 delivery.json 的 slug；bugfix 用 Bug ID 的 kebab-case。
    release/hotfix 用该分支的稳定 SemVer，不用 slugify。
  - 无该 Markdown 视为无记录。进行中可为带 tip 的草稿；裁定收口后覆盖为无
    commit 终稿。branch 验证证据是主链 `verification-report.json`，不写
    `code-review.verification.json`。
  - ❌ 不在 `docs/context/research/` 保存审查报告。

步骤 1 按已有记录判定本轮走向：

- 主链 verify 交接优先识别：已有有效上轮终稿与汇总清单，且传入了修复前左端点时，按 1 人增量处理。
  - 来源 verify 的草稿仍待修绿时，返回原 verify 修绿；不得提前派审查。
  - 草稿已待复审时固定 review_head；不能因存在新草稿误判为无首轮记录。
  - 未齐报告只补齐同一范围；无有效上轮时补完整首轮，不以 1 人替代冻结 roster。

- 首轮：无记录或仅有不完整草稿时走首轮；首次审查才固定当前 HEAD 为
  review_head（写入进行中草稿或仅会话/派发参数，供本轮操作）。
  - 首轮未齐时进入 2 补齐。报告未齐前不改审查对象。
  - 已出现新的交付改动也不重新固定 review_head，不重派。
  - 报告齐后进入修复窗，由步骤 3 复核原 review_head 以来的改动。
- 修复窗：本轮应派报告已齐，且修复终点尚未与当前代码指纹对齐。
  - 窗内只修复已记录问题，保留原 review_head，不覆盖原报告。
  - 直接进入 3。不开增量新一轮，不重派 subagent；不提前跑 verify branch。
  - 本轮若改了实现/测试/验证配置：步骤 4 按调用方边界处理 smart；失败且可修时只回 3。
- 修复窗在本轮修复已提交、且（若本轮改过实现、测试或验证配置）smart 已通过时关闭。
  - 此后改实现、测试或验证配置才可进入增量新一轮。
  - 主链 verify 修绿改动由 verify 记录原左端点，开启 1 人增量新一轮，不复用旧修复窗。
- 无新改动：已有声称通过的终稿（或本轮已可收口）、无待修问题，且相对操作左端点到
  HEAD 没有新的交付改动时，核对后结束。
  - 不进入 2。
  - 此出口另须 objectives 的 code-review 已勾且已提交；仅漏勾或未提交则进 4 补齐。
  - 记录文件、纯事实、收口文档、以及非本交付 `docs/` 不是新的交付改动。
- 增量新一轮：修复窗已关闭（或终稿已在），且其后改了实现、测试或验证配置时进入
  （含 close-out 集成以及主链 verify 修绿后的增量）。
  - 完整上轮：应派份数报告已齐（或已有终稿）、已采纳与未解决问题清单齐全。
  - 操作左端点不从终稿读 hash：close-out 集成用集成前 HEAD（当场记录）；其它增量用
    终稿落盘提交 `git log -1 --format=%H -- <code-review.md>`；无法判定则走首轮。
    pre-gitflow-finish 补审用其执行时返回的原 `before_head`，可从上下文或 CLI 日志恢复。
    主链 verify 修绿轮人数为 1；其他普通增量仍为冻结 roster.reviewers。
  - 重新固定 review_head 为当前 HEAD，进入 2。
  - 主链 verify 传入其修复前左端点；从已有草稿续办，不从新终稿提交倒推修复前范围。
  - ❌ 不得从 start_commit 重扫已审区间（走首轮时除外）。
  - 上轮残缺（缺份数、缺问题清单）时不得假装增量，停止并要求补记录。
    无记录走首轮。
- 范围无法判定时停止询问。
- 不得把未提交改动遗漏在审查范围外；存在无关改动且无法隔离时停止。

| 分支 | 固定基线 |
| --- | --- |
| feature、adhoc | delivery.json 的 start_commit |
| bugfix、hotfix | start 保存的 `branch.<完整分支名>.mdf-start-commit` |
| release | 上一正式发布版本的 master commit/tag，解析为完整 commit hash |

基线读取与审查区间：

- bugfix/hotfix 用 `git config --local --get "branch.<完整分支名>.mdf-start-commit"` 读取起点。
- release 首轮依据正式发布记录确认上一版本，核对其 `v<version>` tag 指向的 commit 位于 master 历史。
  - PR 候选已更新本地 manifest 时，从目标 master 的正式发布记录确定上一版本，不取候选 latest_release。
  - 不取 master 合回 develop 的合并提交，也不使用移动的 master/develop HEAD 代替发布基线。
  - 首次发布没有上一版本时，须用户明确确认初始基线。
  - 基线缺失、歧义或对象不可解析时停止询问。
- 默认交付基线及增量操作左端点必须是 review_head 的祖先；against 模式不受此限制。
- 审查内容：
  - 首轮：`git diff <base_commit> <review_head>`，按步骤 3 的 sourceset 与 ignore 过滤。
  - 增量：`git diff <操作左端点> <review_head>`（操作左端点按上方规则，不读终稿
    hash）。
  - 并读取必要上下文，不能仅按提交标题或文件名审查。
- release 首轮覆盖上一版本以来的完整变化：
  - 不得仅审 release 分支创建后的改动，也不得因某个 child 已审查而跳过其代码。
- 后续轮次只覆盖操作左端点以来的增量，仍须复核上轮问题。
- 步骤 1 仅在新审查或增量新一轮时将本轮左端点与 review_head 记入进行中草稿
  （或派发参数），明确尚未通过，再启动审查。
- 交付起点 base_commit 在本轮操作中固定，续办沿用，不重新追随分支或 tag；
  裁定收口写入终稿时不得保留任何 commit hash。

各分支前置条件：

- 人工 feature：仅要求用户显式勾选人工工作，不要求 converge；使用 1 个 reviewer。
- adhoc：工作项已勾即可，不要求 converge；使用 1 个 reviewer。
  - 目标取自 delivery.work；重开审查时退勾 code-review 及后续项，成功后仅勾本项。
- 其他交付进度只认 `objectives.md`：converge 项须已 `[x]`（含 start 对 `has_dev: no` 的预勾）；
  未勾停止，提示先 `$mdf converge`。
  - `needs_design: yes` 时可读 design.md 作审查上下文；不以 design/converge gate 文件为通行证。
  - 修复续办进入 3；步骤 4 按需补 smart，不在本 intent 强制 verify branch。
- release 读取 `objectives.md` 对照本版目标与验收；超出计划的新能力不在本轮实现。
  - 审查基线仍为上一正式发布。
  - 📌 integrate 项须已 `[x]`；未勾停止，提示先 `$mdf integrate`（或不联调应由 start 预勾）。
  - 📌 联调时（含 collab-mode），进入 2 前须双端验收通过，且已确认此后不再改代码。
    未双端验收通过则不派审查。
- hotfix/bugfix 读取 `objectives.md` checklist 与对应 Bug。
- bugfix 的 `suites.json` 在后续 verify branch 前关联；本步不强制。

### 独立审查

主 Agent 向每个审查 subagent 派发任务时，必须以以下文字作为提示词 opening，
随后提供本次审查上下文及现有执行与输出约束：

> 以最严苛的白盒测试专家视角审查实现代码和测试用例，主动挑战实现逻辑与测试的充分性，
> 寻找隐藏缺陷和覆盖盲区。以证据核实逻辑正确性与测试有效性，不因测试通过就认定实现正确。
> 严格只读 worktree，不写文件、不运行 tests；返回位置、触发条件、影响、静态证据和建议优先级，由主 Agent 核实。

派发：

- 步骤 2 按本轮应派人数启动独立 subagent。默认为冻结的 roster.reviewers；close-out 集成增量轮与主链 verify 修绿轮为 1。
- `review_strategy` 默认 `replicate`：
  - 各审查者收到相同的交付 base_commit、本轮左端点、review_head、工作目录、目标、验收、
    适用设计材料与相关当前事实页。
  - 均覆盖本轮范围检查正确性、验收覆盖、测试质量、code smell、架构合理性及非必要复杂度。
  - 不安排分工，不按文件、模块或领域拆分，不共享其他审查者结论。
- 本轮只有 1 人时覆盖整个本轮 diff，不受冻结 partition 切片限制；仍核对相关旧 finding。
- 多人 `partition` 时 owner 按 design 已有切片或本步切开的范围派工，每人只审自己那片；
  仍不共享其他审查者结论。
- 覆盖冻结值与模型：
  - 调用可带 `--review-strategy` / `--code-review-model` 覆盖冻结值，派工前运行 `delivery roster` 写入。
  - roster.models 含 `code-review` 时写入该值，按口语描述现场解析；
    可多个模型，可分给本轮多名审查者。没有则不提。
  - ❌ 不得写入其他 intent 的模型。
- 增量新一轮还必须带上轮已采纳项与未解决项；不能只看新 diff 假装旧问题消失。
  - close-out 集成增量轮（1 人）只使用该已汇总清单，
    不得把上轮多份独立报告交给本轮 reviewer 自行合并。
- 已记载的当前行为以事实页为回归基线：与本次目标无关的行为变化按问题报告。
- 每份任务均包含 `repository-documents.md` 的体积与 `modules.md` 的 ignore 条款以及 lint 工具报告；涉及文档时另含 `doc-structure.md`。
  - 本地与 against 按当前配置、交付 CI context 按 source 配置，将实现变更与 sourceset 并集求交，再排除 module ignore。
  - paths 与 diff 同步过滤；未归属实现不审阅，项目文档和交付材料仍按契约检查。
  - 读取 lint 报告，按 `sourceset` 核对全部适用 module 的 `size_limits`；各字段默认 1000/50/70，未归属文件用默认策略。
  - 单文件行数与触及 package 的完整同类成员数分别满足各配置；package 实现/测试不相加。
  - 源代码/package 超限按各触发配置的 `split_percent` 向下取整验收；文档仍按角色上限及 70%。
  - 文件拆分按职责、依赖与适用设计模式审代码，按角色、主题、读者与导航审文档。
    不得把 `part1`、`part2` 或仅改名的机械切分验收为通过。
  - 合理设计可迁移入口；不得仅因入口改变或未在原位置保留 facade、re-export、转发壳而提出问题。
    核对设计依据、明确的对外契约，以及调用方、测试、文档和链接是否同步更新。
- 📌 reviewer 严格只读，不修改实现、tests、配置或报告，不运行 tests，不建立角色 worktree。
  - main Agent 在派发前核对 owner 与 review_head，完整传入规则与范围；reviewer 不调用会落盘日志的 MDF CLI。
  - reviewer 通过会话返回报告；main Agent 负责各份独立报告落盘，报告齐全前不修改审查对象。
  - main Agent 对照 HEAD 与 worktree diff 核对只读边界；发现越界改动则停止，保留现场并说明差异。
- 本轮进度由 main Agent 记录，不以 reviewer 写文件作为报告完成条件。
- main Agent 分派前用只读 measure_code.py 准备本轮范围的文件/package 实测数据；修复后由 main Agent 重测。
  - 仅读取 references/lint.md 的「审查只读测量」条款，不重新执行 lint 工作流。
  - 初审使用 --ref <review_head>；修改前使用 --ref <本轮左端点>，需原触发策略时显式传 --policy-ref <策略快照>。
  - 修复后使用 --ref <已提交修复终点 HEAD>，不覆盖本轮固定 review_head。

  - 数据通过任务原文或已有工具日志交给 reviewer，不让 reviewer 执行脚本、运行 tests 或写入报告。


### 缺陷复现

全部独立报告齐全后，由 main Agent 汇总去重，构建并运行 failing test，再裁定 finding。

- 步骤 3 由 main Agent 从目标、验收、设计或当前事实页确定预期行为，构建最小的自动化复现 test，优先放在 quick 层。
  - test 断言正确行为；不得断言错误行为、使用无条件失败或 mock 掉被审查逻辑来制造失败。
  - 复用已有 failing test 时也须亲自运行并核对失败原因，不要求重复编写同一用例。
- main Agent 的核实记录包含 test 路径或原文、运行命令、退出码、完整报告路径，以及预期与实际结果；未运行时不得编造执行结果。

| 复现结果 | 证据与去向 |
| --- | --- |
| 因所指行为缺陷失败 | 附失败报告，进入步骤 3 裁定与修复。 |
| test 通过 | 说明未复现；已有证据排除 finding 时建议不采纳，否则保留证据交步骤 3 降级裁定。 |
| test 或环境错误 | 由 main Agent 在步骤 3 修正复现方法；无法继续则记录尝试、限制及其他证据，交步骤 3 降级裁定。 |
| 无法构建 test | 说明原因与其他证据，交步骤 3 降级裁定；不得仅报告猜测。 |

- 步骤 3 汇总去重后按合并证据裁定，无有效 failing test 的 finding 按既有优先级降低一级，最低级仍保留。
  - 记录原级别、有效级别与降级理由；同一 finding 不因多份报告或续办重复降级，补齐有效 failing test 后按原级别重新裁定。
  - 级别与采纳决定分别记录，不因缺少 test 判为无效或直接不采纳；未定义优先级时按下表处理。

| 原级别 | 无 failing test 时的处理级别 |
| --- | --- |
| 必须修 | 建议修 |
| 建议修 | 待跟进 |
| 待跟进 | 待跟进（最低级） |

- code smell、架构、体积与文档类问题提供对应契约及实测或具体结构证据，不伪造 failing test。
  - 无法构建 failing test 时同样降一级；声称会导致错误行为时仍须尝试复现。
- 降级不豁免既定目标、契约或验证门槛；主 Agent 结合剩余证据裁定是否修复或待跟进，并记录理由。
  - 待跟进仅限不阻断既定验收的问题，单独列出，不混入未解决的阻断项。

报告内容（进行中 / 分报告）：

- 每份报告均声明审查种类（首轮 | 增量）、派发所用 tip（base / 左端点 /
  review_head）、已完成的审查范围及未完成项；无未完成项时明确写无。
- 增量轮次须有上轮问题复核表，逐项写明仍解决 / 复开 / 不适用。
- 发现问题时列出问题位置、触发条件、影响与证据；无问题时明确说明未发现问题。
- reviewer 为 finding 附建议原级别和静态证据；行为复现与降级记录由 main Agent 在步骤 3 补入草稿与终稿。
  - reviewer 没有 failing test 不影响报告完整性，也不提前触发降级。
- 代码规模以 lint 及只读测量数据为证据；reviewer 审查拆分职责、依赖及设计合理性，不重复手工计数。
  - lint 未通过时不得开始本轮审查；工具硬限制不得以 LLM 判断豁免。
  - 原超限拆分须保留触发时工具报告中的目标；修复后通过 --file-target/--package-target 传入所有原触发目标。
  - 适用结果须有 within_required_split_targets: true，且满足新位置硬限制；不能用迁入较宽松 module 后的目标替代原目标。

  - 只对本轮确属超限拆分结果的路径验该标记；未发生拆分的文件不能仅因超过拆分目标被要求改写。
  - 缺少适用结果的数据时由 main Agent 补测；无法取得证据则未完成，不把缺数据或空列表当通过。


报告验收：

- 主 Agent 核对每份报告与派发的左端点、review_head 和本轮范围一致，且无未完成项，
  才验收为完整报告。
- reviewer 提供位置、触发条件、影响、静态证据和建议优先级即可完成 finding 报告。
  - 证据或范围不足时退回补齐；复现是 main Agent 的职责，不能据此将 reviewer 报告列为未完成。
- 范围声明缺失、端点不一致或存在未完成项时，要求补齐或重新独立审查；无法补齐则停止。
- 不足本轮应派人数、启动失败、结果缺失或未覆盖本轮范围时，补齐独立审查；
  无法补齐则停止，不记录通过。
- 续办只复用同一左端点与 review_head 的完整报告；本轮未凑齐应派份数时不得进入修复或收口。
  - 增量新一轮不复用上轮分报告去覆盖新 diff；收口终稿另见步骤 4。

### 汇总、修复与复核

步骤 3 由主 Agent 汇总去重，逐项核实，记录采纳或不采纳的依据；以证据裁定，不按票数决定。

可选加速（见 `common.md`「Jev 可选加速」）：

- 时机：汇总去重后；tool 可用时。
- 每项：`score`（0=不采纳 / 1=建议修 / 2=必须修）。
- 收口：`choice`（`continue_fix` / `ready_to_close` / `need_human`）。
- state：问题摘要、证据指针与降级记录；score 是采纳建议，不代替 finding 的优先级，也不因降级自动减分。
- 采信后仍须主 Agent 核实依据并写入记录；未采信走原汇总。
- ❌ 不按 Jev 票数代替证据。

- 修复权限：
  - 允许自主修复实现，或依据已确认目标/设计纠正、补充、删除错误或重复测试，记录依据。
  - ❌ 不得削弱验收或验证门槛；目标/契约变更须用户确认。
- main Agent 在修复前按被测行为、依赖与 fixture 边界构建复现 tests，归入合适的现有 suite，必要时新建 suite。
  - 有效 test 纳入正式 regression tests；重复或错误 test 可合并、纠正或删除，逐项记录依据，完成临时文件整理。
  - 按既有授权边界同步成员选择、入口配置与 named suite 文档。
  - 移动或合并 test 时保留原缺陷断言与复现能力，记录 finding、正式 test、所属 suite 与执行报告的对应关系。
- 对采纳且复现成功的行为缺陷，在正式 test 位置确认修复前失败，再修复实现并运行同一 test 至通过。
  - 保留失败与通过报告，核对原失败原因已消除；不得通过削弱断言让 test 通过。
- 整理与修复后运行归属 suite 的正式入口，核对报告包含这些 tests。
  - 未被收集、仍有临时 test 未裁定或 suite 失败时留在步骤 3 修复；无法继续则保留现场报告，不进入步骤 4。
- adhoc 按 smart 选题核对覆盖；其余核对 design policy `suites` 或 `suites.json` 覆盖本轮功能块。
  缺漏按问题提出。
- 审查测试时核对 `delivery-contract.md`「失败语义」：
  - 无运行时 skip、提前返回或 xfail。
  - 入口配置能让 warning、skip 与空选择非零退出。
  - 豁免已记录且经用户确认。
  - 混合依赖的 test case 按问题提出，可依既定目标自主拆分，不得改成 skip。
- 更好的架构可以建议，超出目标不直接实施。
- 修复后由主 Agent 复核问题是否解决及是否引入回归，不强制再次启动审查 subagent。
  - 本步触及的代码与超限拆分读取 lint 与只读测量结果，核对目标标记并复核拆分职责。
- 同一范围内的修复、复核及 smart 循环留在步骤 3–4，不重新执行本轮多人审查。
  - 这是修复窗。报告已齐时不提前跑 verify branch、不开增量新一轮。
- 需要用户决定、外部条件或无法继续时报告阻塞，不记录通过的结果。

### 验证与持久证据

步骤 4：按是否改动实现、测试或验证配置决定是否跑 smart；裁定本 intent 可收口时洗成终稿。

- 本步不跑 verify branch（留给主链下一 intent）；也不写 `gates/code-review.json`。
- close-out 委托且本轮修复需要 smart 时，保留草稿与修复窗，返回「待主链外续办」；不运行 verify，不洗终稿、不勾选。
  - close-out 交接后，由 next/deliver 或独立 code-review 在主链外恢复本轮步骤 3–4；不重派已齐 reviewer。
  - 主链外完成 smart 与终稿后，再由原主链完成所需验证与 fact；旧通过报告不代替本轮结果。

本轮 smart 按以下互斥条件处理，不越过调用方边界。

| 调用与改动 | 处理 |
| --- | --- |
| close-out 委托且本轮修复改了实现/测试/验证配置 | 返回待主链外续办，保留修复窗，不洗终稿 |
| 其他调用且本轮改了实现/测试/验证配置 | 跑 `$mdf verify --scope smart`；失败回 3 修 |
| 本轮未改实现/测试/验证配置 | 跳过 smart |

- close-out 集成后的增量审查仍按下方「close-out 核对」；branch 验证证据由主链
  `verification-report.json` 负责，不在本步伪造。
- ❌ 不能用仅检查文档结构的 strict validation 代替业务验证。
- 非 quick 用例在 converge 之后失败且本轮触及：
  - 必须尝试补一条 quick 复现用例。
  - 结果写入终稿「quick 复现」字段。

进行中草稿（未裁定收口前）可按轮保留 tip，便于续办；每轮操作内容包括：

- round、审查种类（首轮 | 增量）、base_commit、左端点、review_head。
- 本轮应派人数份独立审查及其身份、本轮新发现、上轮问题复核表。
- 逐项裁定、修复与复核、本轮修复终点 tip。
- smart（已跑 <命令/路径> / 未改实现、测试或验证配置跳过）。
- quick 复现（已补 <用例位置> / 未补 <原因> / 无非 quick 失败）、未解决项。

裁定收口（所有 finding 已裁定、无未解决阻断项，且若本轮改过实现、测试或验证配置则 smart 已通过）时：

1. 合并各轮/各份进行中材料，在本轮已定位的交付材料目录覆盖写入一份
   `code-review.md` **终稿**（**report**，非 gate）；候选发布沿用版本目录。
2. 终稿须含：结论（声称通过）、已采纳与未解决清单（未解决须为空）、各轮要点与
   裁定摘要、smart、quick 复现；路径与证据指针用仓库相对路径，不用 commit hash。
   - 复现成功的采纳项关联正式 regression test、所属 suite 及修复前失败、修复后通过的报告。
   - 无法构建 failing test 的 finding 保留降级、替代证据和最终裁定；待跟进项说明后续处理，不伪记为已修复。
3. rule 内容指纹须明确标注，不属于 commit hash；终稿保留该证据。
   ❌ 终稿不得出现任何 commit hash（含 base_commit / review_head / final_head /
   左端点 tip、完整或缩写 SHA）。
4. 进行中带 tip 的段落不得留在终稿；分报告已合并后不再作为核对对象。
5. 提交终稿，将 `objectives.md` 的 code-review 项改为 `[x]` 并提交。
   - 只清理本轮审查草稿；不得删除父 PR 返工备注，完成后按其返回位置交还调用方。
6. ❌ 报告未齐或仍在修复窗时不得洗稿、不得勾选。

- ❌ 不运行 `delivery record --stage code-review`；不以 gate 文件为进度。
- 语义审查由 Agent 负责；CLI 不推理各份结论。
- 首轮未写清已采纳/未解决问题清单时，第二轮不得增量，停止并要求补记录。
- 主链 verify 修绿改了代码：内部委托本 intent 做 1 人增量审查，完成后返回 verify；范围与复跑规则见 verify。
- 勾选后又改实现/测试/验证配置：终稿作废，重新进入本 intent（增量或首轮），再出新终稿。

close-out 核对：

- 终稿存在且声称通过；已采纳/未解决清单齐全（未解决为空）。
- 不使实现审查过期、也不强制重开审查的改动（事实仍须另审）：
  - 记录文件自身、纯事实、收口文档。
  - local close-out 集成引入的非本交付 `docs/` 改动；PR mode 的远端集成不适用此豁免。
- close-out 集成 develop/master 产生新提交后：
  - local 模式仅非本交付 `docs/` 增量不新开审查；按 close-out 契约追加跳过说明。
  - PR mode 的每次远端集成都补审补测，按 `pr.md` 执行，不因仅文档或空 tree diff 跳过。
  - 其他集成增量一律作为增量新一轮从 1 开始，左端点为集成前 HEAD（当场记录）。
    - 以集成后的 HEAD 重做 1 份本轮范围审查；需 smart 时按上方边界交接，不复用集成前终稿当增量差。
    - 本轮完成后再次洗成无 commit 终稿并勾选。
  - 无有效上轮（无终稿或清单残缺）时按首轮从交付起点审到集成后 HEAD，人数仍为
    roster.reviewers。
- 记录或提交失败时保留现场并报告；不把阶段提交视为审查通过。
