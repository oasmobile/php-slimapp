# PRP Review

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
│ 2 Select proposal                │
└────────────────┬─────────────────┘
                 │
                 ├──── 需澄清或消歧 ────→ 2 Select proposal
                 │
                 ▼ 输入唯一且完整
┌──────────────────────────────────┐
│ 3 Check state                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 已开工 ───────→ [保留对象，停止]
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 4 Clarify                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 需补稿 ───────→ 4 Clarify
                 ├──── 失败/缺失 ────→ [保留 draft，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 5 Confirm                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [保留 draft，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 6 Validate and ready             │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ──────────────────────→ [结束]
                 ├──── 确认稿已变 ────────────────→ 5 Confirm
                 ├──── 校验失败 ──────────────────→ [保留 draft，停止]
                 └──── 写回、提交或 land 失败 ────→ [报告实际状态，停止]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

完整读取以下契约：

- `references/common.md` 与 `references/repository-contract.md`。
- `references/object-contract.md` 与 `references/html-materials.md`。

步骤 4 读取并内部执行 `references/clarify.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check entry | 脚本 | 运行 doctor 与 planning ensure，切换至 planning | doctor、工作区 | 2 | 未切换留 1；其他停止 |
| 2 | Select proposal | 脚本 | 按 ID 或路径确定唯一 PRP；未指定时用 `list` 列候选 | 唯一对象 | 3 | 留在 2 消歧 |
| 3 | Check state | 脚本 | 判定未开工才转 draft | list 结果、状态检查 | 4 | 已开工保留对象；其他停止 |
| 4 | Clarify | 约束 | 查证并内部 clarify 目标、范围与验收 | 完整 draft、证据 | 5 | 需补稿留 4；其余保留 draft，停止 |
| 5 | Confirm | 约束 | 展示详细 HTML 并确认 | HTML、用户确认 | 6 | 保留 draft，停止 |
| 6 | Validate and ready | 脚本 | 校验、转 HTML、提交、land | ready、land | 结束 | 稿变回 5；校验停；其后报状态 |

## 术语与数据结构

### 入口与未开工检查

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

**选择**

- 一次只接受一个 Proposal 的 canonical `prp-` ID 或仓库相对路径。
- 用户未指定时运行 `list --repo "$REPO_ROOT" --type proposal --status draft --status ready`。
  - 按输出的 `id`、`title`、`status`、`blocked_by` 与 `in_progress` 列出候选供用户选择。
  - 不逐篇翻阅 `docs/proposals/`。

验收：唯一对象。

异常与交接：无法确定唯一对象时留在 2。

<a id="s3"></a>

**状态**

❌ released/rejected/replaced/implemented 或 archive Proposal 拒绝修改。

在修改状态或正文前，以 `list --repo "$REPO_ROOT" --type proposal` 输出中
目标 PRP 的 `status` 与 `in_progress` 为准：

- `in_progress` 已覆盖以下记录，任一记录的 `proposal` 命中目标 ID 即为 `true`：
  - 当前 checkout 的 `changes/` 下全部 `delivery.json`；
  - 本地 `feature/*` 和 `origin/feature/*` 引用中的同类记录。
- ⚠️ 不能仅凭当前 checkout 没有开发材料或 `tree` 未显示进行中，就判定未开工。

| 情形 | 处理 |
| --- | --- |
| 已开工 | 报告关联分支与材料位置，保留对象和交付基线并停止；本入口不修改已开工 PRP |
| `list` 因记录损坏失败或目标不在输出中 | 同样在写入前停止，报告缺失证据 |
| 仅 active draft/ready 且已确认未开工 | 继续；ready 用 `prp-format draft` 转为 Markdown draft |

取消、暂停、未确认或 validation 失败均保持 `draft`，不恢复 ready；写回后失败按步骤 6 报告实际状态。

验收：原状态、检查过的引用与材料范围、未开工结论，以及写回后的 draft 状态。

### 草稿与确认

<a id="s4"></a>

**澄清**

先查仓库证据，使用内部 clarify intent 澄清 Problem、Desired Outcome、 Scope 与可验证 Acceptance Criteria。

验收：完整 draft。

- 按 `html-materials.md` 补齐事实依据、约束、依赖、设计取舍、风险与逐条验收方法。
- 详细内容先写入 Markdown draft；HTML 由该稿生成，不在 preview 中单独维护另一份正文。

异常与交接：需要补稿时留在 4；其他失败保持 draft 并停止。

可选加速（见 `common.md`「Jev 可选加速」）：

- 时机：clarify 完成后、展示确认前；tool 可用时。
- 调用：`noul`（是否达 ready 质量），或 `score`
  （0=可确认 / 1=小补 / 2=须回澄清）。
- state：draft 与证据摘要。
- 采信「可确认」仅用于整理展示材料。
- ❌ 不替代步骤 5 用户确认，不得因 Jev 直接写 `ready`。
- 需补稿时留在步骤 4；完整 draft 才进入步骤 5。
  未采信时由主 Agent 按同一条件裁定。

<a id="s5"></a>

**确认**

按 `html-materials.md` 生成并检查详细 HTML，展示实际文件供用户确认。

1. 运行 `prp-format preview --repo "$REPO_ROOT" --proposal <完整 PRP ID>`。
2. 打开返回的 `.review.html`，检查全部正文、表格和证据链接。
3. 向用户展示 HTML 文件，明确确认事实、排除范围、取舍、验收方法与既有对象 diff。
4. 取得对该 HTML 内容的明确确认；改稿后重新生成、检查并确认，不沿用旧稿确认。

验收：用户明确确认。

异常与交接：未确认则保持 draft 并停止。阶段提交不构成确认；续办须再次进入本步取得确认。
只有用户明确确认才转 `ready`。

### 就绪条件

<a id="s6"></a>

**就绪**

- 先在 `draft` 状态运行 `basic validation`。
- 通过后执行以下命令，把已确认内容写成唯一 ready `.html`。

```bash
python3 "$MDF_ROOT/scripts/mdf.py" prp-format ready --repo "$REPO_ROOT" --proposal <PRP-ID> --confirmed
```

- 该 CLI 删除对应 Markdown 与临时 preview，并改写仓内引用；Agent 回读结果，不再手动重复这些写入。

回读确认状态为 `ready` 后提交，并运行 `planning land --repo "$REPO_ROOT"` 合入 develop。

验收：validation 通过；回读 HTML 对象确认 `ready`，对应 Markdown 已不存在，引用仍有效。

异常与交接：

- `basic validation` 失败：保持 `draft` 与现场并停止。
- `preview_changed`：保持 draft，回步骤 5 重新生成、检查 HTML 并取得本稿确认。
- 写回 `ready`、回读、提交或 `planning land` 失败：保留现场并停止。
  - 报告对象实际状态：是否已写 `ready`、是否已提交、是否已合入 develop。
  - 只报告已经核实的状态；未核实 ready 或 land 成功时不得声称对应步骤完成，不宣称整体完成。
- 不得关闭对象或填写 `released_in`。
