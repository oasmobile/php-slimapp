# PRP Create

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check entry                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 未切换 ───────→ 1 Check entry
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Resolve proposal               │
└────────────────┬─────────────────┘
                 │
                 ├──── draft/ready ─────→ [停止并交接]
                 ├──── 其他状态 ────────→ [只报告并停止]
                 ├──── 需澄清或消歧 ────→ 2 Resolve proposal
                 │
                 ▼ 输入唯一且完整
┌──────────────────────────────────┐
│ 3 Clarify                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [不写对象，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 4 Confirm                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 取消或拒绝 ────────────→ [停止]
                 ├──── 输入对象或来源变化 ────→ 2 Resolve proposal
                 ├──── 既定对象需澄清 ────────→ 3 Clarify
                 ├──── 未确认且内容未变 ──────→ 4 Confirm
                 │
                 ▼ 用户确认 draft
┌──────────────────────────────────┐
│ 5 Create draft                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [保留现场，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 6 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [停止]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

完整读取 `references/common.md`、`references/repository-contract.md` 与
`references/object-contract.md`。
步骤 3 读取并内部执行 `references/clarify.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check entry | 脚本 | 运行 doctor 与 planning ensure，切换至 planning | doctor、工作区 | 2 | 未切换留 1；其他停止 |
| 2 | Resolve proposal | 脚本 | 用 `list` 查重单个 Proposal | list、唯一对象 | 3 | draft/ready 交接；其他状态停；留 2 |
| 3 | Clarify | 约束 | 内部 clarify 补齐目标、范围、验收与直接依赖 | 完整必填事实 | 4 | 不写对象，停止 |
| 4 | Confirm | 约束 | 展示边界、排除项与依赖并确认 draft | 用户明确确认 | 5 | 未确认留 4；取消停；来源变 2；事实变 3 |
| 5 | Create draft | 脚本 | 写 draft、校验、提交并 planning land | 零 finding、diff、land | 6 | 保留现场，停止 |
| 6 | Report | 约束 | 报告 draft、事实、排除项与后续评审入口 | 结果摘要、依赖 | 结束 | 停止 |

## 术语与数据结构

### 入口与输入

<a id="s1"></a>

**入口**

1. 解析 `REPO_ROOT` 并运行 `doctor`；先核对 `normal_workflows_allowed: true`。
   未通过时按下方异常规则停止，不运行 `planning ensure`。
2. 运行 `planning ensure --repo "$REPO_ROOT"`。
3. 按 `references/common.md` 的「切换工作区」规则进入 JSON `worktree`（分支 `planning`）。
4. 再重新解析目标根。

验收：`normal_workflows_allowed: true`，当前分支为 `planning`。

异常与交接：manifest 未就绪时提示 `$mdf init`；`normal_workflows_allowed: false` 时报告
findings 后停止。尚未切到 planning 工作区时留在本步。

<a id="s2"></a>

**对象**

- 接收用户手动提供的单个 Proposal 事实；一次不得创建多个对象。
- 运行 `list --repo "$REPO_ROOT" --type proposal`，以用户输入的标题与正文对照输出中的 `title` 查重；
  不读取既有对象正文。
  - 命中既有 PRP 时不新建：
    - `draft` 或 `ready`：停止并交接 `$mdf prp review`。
    - 其他状态：只报告命中对象与状态，不交接 `prp review`。
  - 该输出同时作为步骤 3、4 依赖候选与 milestone 值的来源，不逐篇翻阅 `docs/proposals/`。
- 外部想法、当前聊天上下文或外部文档必须显式调用 `$mdf intake`。

验收：确认的 Proposal 与采用范围。

异常与交接：`draft` / `ready` 停止并交接；其他状态只报告后停止；范围不明时留在 2。

### 事实与确认

<a id="s3"></a>

**澄清**

使用内部 clarify intent 澄清 Problem、Desired Outcome、Scope、可验证 Acceptance Criteria 与直接依赖。

验收：完整必填事实。

异常与交接：必填事实仍无法确认时停止，不得写入任何对象。

<a id="s4"></a>

**确认**

展示 Proposal、边界、排除范围和依赖。

- `depends_on` 仅列：
  - 直接依赖的 draft、 ready 或 implemented/released Proposal ID；
  - 需要等待整阶段完成时的已有 milestone 值。
- 如有阶段归属，同时确认可选 `milestone`；无归属不要求补齐。

验收：只有用户明确确认 draft 才继续。

异常与交接：

- 取消或拒绝则停止。
- 输入对象或来源变化时回到 2。
- 既定对象的事实、范围或验收需澄清时回到 3。
- 未取得明确确认且内容未变时留在 4 等待，不把未答复视为事实变化。
- 来源变化与事实变化同时成立时，优先回到 2。

### 对象写入与交接

<a id="s5"></a>

**创建**

- 为 Proposal 提议并确认英文 ASCII kebab-case slug。
  - 须在 active Proposal 与 Bug 中唯一，且不得与对象 ID 同形。
- 使用 `make-id --type proposal --repo "$REPO_ROOT" --slug <slug>` 生成随机 ID
  与规范化文件名，避开已有 ID。
  - 以模板写入 `docs/proposals/`，初始状态为 `draft`。
- 仅在已确认阶段归属时添加非空字符串 `milestone`；否则省略字段，不写 `null`。
- 写入后运行 `validate --repo "$REPO_ROOT" --level basic`。
  - 回读对象并对照模板、确认事实与完整 diff。
  - 核对 schema、必填章节、`draft` 状态和依赖。
- 通过后提交本次 draft，并运行 `planning land --repo "$REPO_ROOT"` 合入 develop。

验收：draft Proposal、校验退出 0 且零 finding、回读结果与 diff。

异常与交接：校验、回读或核对失败时：

- 停止并保留现场，报告 findings 与实际已写对象。
- ❌ 不得宣称创建验收通过，不进入步骤 6 的成功报告。

<a id="s6"></a>

**报告**

展示 draft Proposal、确认事实、排除范围和依赖。

验收：会话摘要。

异常与交接：停止。后续显式调用 `$mdf prp review`，经 draft basic validation 后转为 `ready`；
不得关闭普通对象或填写 `released_in`。
