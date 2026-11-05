# Intake

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check entry                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Resolve source                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 需澄清或消歧 ────→ 2 Resolve source
                 │
                 ▼ 输入唯一且完整
┌──────────────────────────────────┐
│ 3 Classify                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 全部候选被剔除 ────→ [停止并交接]
                 ├──── 无法判定 ──────────→ 2 Resolve source
                 │
                 ▼ 分类明确
┌──────────────────────────────────┐
│ 4 Clarify                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [不写对象，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 5 Confirm list                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 取消或拒绝 ──────────────→ [停止]
                 ├──── 来源采用范围变化 ────────→ 2 Resolve source
                 ├──── 对象事实或边界需澄清 ────→ 4 Clarify
                 ├──── 未确认且内容未变 ────────→ 5 Confirm list
                 │
                 ▼ 用户确认清单
┌──────────────────────────────────┐
│ 6 Create objects                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 未切换 ───────→ 6 Create objects
                 ├──── 失败/缺失 ────→ [保留现场，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 7 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [停止]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

完整读取 `references/common.md`、`references/repository-contract.md` 与
`references/object-contract.md`。
步骤 4 读取并内部执行 `references/clarify.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check entry | 脚本 | 解析 REPO_ROOT 并运行 doctor | doctor 结构化结果 | 2 | 停止 |
| 2 | Resolve source | 约束 | 确认一次性来源及采用范围 | 来源、已确认范围 | 3 | 等待澄清，2 |
| 3 | Classify | 脚本 | `list` 查重，按状态剔除或转回归 | list 结果、对象清单 | 4 | 全部剔除停；无法判定回 2 |
| 4 | Clarify | 约束 | 内部 clarify 补齐各 Proposal/Bug 必填事实 | 完整必填事实 | 5 | 不写对象，停止 |
| 5 | Confirm list | 约束 | 展示清单、边界、排除项与依赖并确认 | 明确确认 | 6 | 未确认留 5；取消停；来源变 2；事实变 4 |
| 6 | Create objects | 脚本 | Bug 按归属写；Proposal 取 ID | 对象、零 finding、diff | 7 | 未切换留 6；校验失败则停 |
| 7 | Report | 约束 | 报告对象、范围、依赖和后续显式入口 | 结果摘要 | 结束 | 停止 |

## 术语与数据结构

### 入口与来源

<a id="s1"></a>

**入口**

解析 `REPO_ROOT` 并运行 `doctor`。本步不切换工作区；写入落点在步骤 6
按对象类型确定。

验收：`normal_workflows_allowed: true`。

异常与交接：manifest 未就绪时提示 `$mdf init`；`normal_workflows_allowed: false` 时报告
findings 后停止。

<a id="s2"></a>

**来源**

接收一句话、当前聊天上下文或外部文档为一次性来源；确认采用范围；
除非用户明确要求保留，不得复制、归档或链接到仓库。

验收：确认的来源采用范围。

### 对象分类与确认

<a id="s3"></a>

**分类**

先运行 `list --repo "$REPO_ROOT"`。
取得 active Proposal 与 Bug 的 `id`、`title`、`status`。
对照来源查重，按命中对象的 `status` 处理：

| 命中 | 处理 |
| --- | --- |
| draft/ready Proposal | 剔除该候选项，不新建，提示 `$mdf prp review` |
| 其他状态 Proposal | 剔除该候选项，不新建，报告命中对象与状态，由用户决定 |
| open/fixed/rejected Bug | 剔除该候选项，不新建，提示在既有 Bug 中补充 |
| closed Bug | 保留为新 Bug 候选项，正文写明回归自该旧 Bug 的完整 ID |

- 其余候选项继续分类；全部候选项都被剔除时停止并交接。
- 不逐篇翻阅 `docs/proposals/` 与 `docs/bugs/`。

从来源和仓库证据判定对象类型、数量与独立交付边界：

- 偏差建 Bug，待实现意图建一个或多个 Proposal。
- 优先拆成尽可能小的 Proposal，以依赖满足后能独立实现、验收和合入为下限。
  - 能分开验收的结果优先拆开；不按文件或开发步骤机械拆分，不扩张来源范围。
  - 已足够小的交付单元无需继续拆分。

可选加速（见 `common.md`「Jev 可选加速」）：

- 时机：查重后、定稿清单前；tool 可用时。
- 调用：对每个未剔除候选项 `choice`，或一次 `run` 多题。
- state：来源摘录与查重命中。
- 选项：`bug` / `proposal` / `drop`（应剔除或无法独立交付）。
- 采信后写入同结构清单；未采信或边界仍不明走主 Agent，必要时回 2。

验收：对象清单与剔除项。

异常与交接：全部候选项都被剔除时停止并交接，不回到 2。无法判定类型或边界时回到 2。

### 澄清与确认

<a id="s4"></a>

**澄清**

使用内部 clarify intent 澄清成稿必要事实：

- Proposal 收敛 Problem、Desired Outcome、Scope、可验证 Acceptance Criteria。
- Bug 收敛：
  - Observed/Expected Behavior、Reproduction、Impact、Regression Evidence Required。
  - `found_in` 与 active severity。

验收：完整必填事实。

异常与交接：必填事实仍无法确认时停止，不得写入任何对象。

<a id="s5"></a>

**确认**

展示对象清单、边界、排除范围、步骤 3 剔除项与 Proposal 依赖。

- `depends_on` 仅列以下三类值：
  - 直接依赖的 draft、ready 或 implemented/released Proposal ID。
  - 需要等待整阶段完成时的已有 milestone 值。
  - 本次清单中另一新 Proposal 的临时引用 `new:<slug>`（尚无 ID，步骤 6 替换）。
- 候选 ID 与 milestone 取自步骤 3 的 `list` 输出。
- 逐条说明需要上游提供的结果；优先顺序不能作为依赖依据。
- 同属一个阶段不能写成对其中单个 PRP 的依赖。
- 可建议 milestone 分组，由用户决定是否采用。
  - 不默认一次 intake 对应一个 milestone，不自动把最先实施的一两个 PRP 标为 MVP。
- 有归属时展示并确认 `milestone`，无归属不强求补齐。

验收：只有用户明确确认清单才继续。

异常与交接：

- 取消或拒绝则停止。
- 来源采用范围变化时回到 2；对象必填事实或边界需澄清时回到 4。
- 来源变化与事实澄清同时成立时，以来源变化为准回到 2。
- 未取得明确确认且内容未变时留在 5 等待，不把未答复视为事实变化。

### 对象写入与交接

<a id="s6"></a>

**创建**

为每项提议并确认英文 ASCII kebab-case slug；须在 active Proposal 与 Bug
中唯一，且不得与对象 ID 同形。

写入落点按对象类型确定：

- Bug：按 `references/common.md` 的归属规则确定写入分支。
  - 与当前交付分支工作相关在当前分支，无关在 develop。
  - 使用 `make-id --type bug --repo "$REPO_ROOT" --slug <slug>` 生成 ID，以模板写入 `docs/bugs/`。
- Proposal：在 planning 工作区写入。
  1. 运行 `planning ensure --repo "$REPO_ROOT"`。
  2. 按 `references/common.md` 的「切换工作区」规则进入 JSON `worktree`
     （分支 `planning`），重新解析目标根。
  3. 一次调用 `make-id --type proposal --repo "$REPO_ROOT" --slug <a> --slug <b> …`。
     它为全部新 Proposal 随机生成 ID，并避开已有及本批 ID。
     - 多项时从返回的 `items` 取 ID 与 filename；仅一项时取顶层 `id` 与 `filename`。
     - ❌ 不得逐项取 ID 后再写入，也不得先写占位对象。
  4. 把确认清单中的 `new:<slug>` 替换为对应 ID，以模板写入 `docs/proposals/`。
  5. 完成下方写入校验与回读核对后提交，再运行 `planning land --repo "$REPO_ROOT"` 合入 develop。
- 清单同时含两类时，先按归属完成 Bug 并提交，再切换 planning 完成 Proposal。

Proposal 初始状态为 `draft`，Bug 初始状态为 `open`。
Proposal 仅在已确认阶段归属时写入非空字符串 `milestone`；否则省略字段，不写 `null`。

每处写入后在该工作区完成以下核对：

1. 运行 `validate --repo "$REPO_ROOT" --level basic`。
2. 回读对象并对照模板、确认清单与完整 diff。
3. 核对 schema、必填章节、初始状态和依赖；`depends_on` 不得残留 `new:` 临时引用。

验收：所有新建对象、校验退出 0 且零 finding、回读结果与 diff。

异常与交接：校验、回读或核对失败时停止并保留现场，报告 findings 与实际已写对象。

- 不得宣称创建验收通过，不进入步骤 7 的成功报告。
- 尚未进入 planning 工作区时留在本步，按 `common.md` 进入。

<a id="s7"></a>

**报告**

展示新建对象、确认事实、排除范围、依赖，以及步骤 3 剔除的命中项与其交接入口。

验收：会话摘要。

异常与交接：本步展示步骤 6 已验收对象；无法展示时停止。

- Proposal 后续显式调用 `$mdf prp review`，经 draft basic validation 后转为 `ready`。
- Bug 创建后即为 `open`，不得关闭普通对象或填写 `released_in`/`fixed_in`。
