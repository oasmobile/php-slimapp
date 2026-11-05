# Next

## 选择树

```text
┌──────────────────────────────────┐
│ 1 Resolve workflow               │
└────────────────┬─────────────────┘
                 │
                 ├──── 已锁定 PR 恢复 ────────────────────→ 2 Resume
                 ├──── Gitflow 交付分支（含角色分支） ────→ 2 Resume
                 ├──── 无在途流程 ────────────────────────→ 3 Delegate
                 ├──── 状态不明 ──────────────────────────→ [多候选则澄清；证据不足则报告阻塞]
                 │
                 ▼ 其余唯一在途
┌──────────────────────────────────┐
│ 2 Resume                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 仅查看或条件不足 ────→ [说明用户下一步操作]
                 ├──── 可以推进 ────────────→ [执行并交接]
                 └──── 执行失败 ────────────→ [按原流程交接]

步骤 3 仅由步骤 1「无在途流程」进入，不是步骤 2 的后续。

┌──────────────────────────────────┐
│ 3 Delegate                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 └──── 通过 ─────────→ [结束]
```

步骤 2 结束后不进入 3。步骤 3 由步骤 1「无在途流程」到达，不是步骤 2 的后续。
`$mdf next?` 与 `$mdf next？` 不进入本流程，由选择树路由到 tree。
步骤 1 的澄清是列出候选并询问，不是 `$mdf clarify`。

## 工作流（唯一执行契约）

PR 恢复优先：按 [PR 的恢复路由](pr.md) 只读核已锁定 source 的操作记录及返工备注。
命中时未 merged 恢复父 pr，已 merged 且关联 CI 收尾通过才续办 close-out。
merged 但关联 CI 未收尾或缺少证据时先恢复 pr；先应用仍在协调的 deliver 边界。
不先调用普通身份检查，不因 detached 或 source 已删除而另选任务。

adhoc 按 `references/adhoc.md` 的续办条款替代普通主线选型，一次只完成一个账本项。

无账本 adhoc 没有账本项；确认本次工作归属后，按模式委托 pr 或 close-out，由所选 intent 调用 adhoc-change.md。
本次仅完成所选 intent；pr 返回后不自动串联 close-out。
分支类别本身不证明存在在途交付；不凭普通分支名新建账本或宣称已有工作完成。
已锁定 adhoc 的 retained worktree 先用 adhoc-status 核验；completed 只报告结果，不重新 start。
人工 feature 先执行 `references/manual-feature.md` 的续办工作流，替代普通主线选型。
一次仅推进一个所选阶段；人工工作未勾则交接用户。


读取 `references/common.md`。
续办尚未 Git 化的 init/bootstrap/migrate 时读取 `references/initialization.md`；
续办任一交付时读取 `references/delivery-contract.md`；
无在途时读取并执行 `references/tree.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve workflow | 约束 | 先核 PR 恢复，再按普通规则判定 | 记录、分支、调用、证据 | 在途 2；无在途 3 | 多候选则问；证据不足则阻塞 |
| 2 | Resume | 约束 | 按原流程推进或说明下一步 | 原步骤、条件、结果 | 查看或不足则说明；可推进则执行 | 按原流程交接 |
| 3 | Delegate | 约束 | 读取并执行 tree | tree 结果 | 结束 | 停止并报告 |

## 术语与数据结构

PR mode 的 pr 候选项已勾时仍先核平台实际状态；未 merged 继续 pr，merged 后必选无 checkbox 的 close-out。
选择 close-out 前须按 [PR 轮询](pr.md#当前调用内轮询) 确认关联 CI 收尾通过。
已完成收口须有 finish-gitflow 的实际完成证据，不以 checklist 全勾跳过续办。

### 在途流程识别

先按以下顺序判定，命中即停止：

- Gitflow 交付分支（含角色分支）：当前分支为 Gitflow 交付分支，或 `qa/` / `dev/` 角色分支（如 `qa/feature/`）。
  - 此时本次肯定是该交付的步骤，进入续办。
  - 若该交付正由已显式启动的 deliver 协调，续办其未完成内部步骤后返回 deliver。
- 在途推理：其余情况按下方规则识别在途流程。

表步骤 1「在途 2」同时覆盖上述 Gitflow 交付分支（含角色分支）与其余唯一在途。

在途范围包括全部 MDF workflow 及其内部委托：

- 交付主线与 deliver。
- init、bootstrap、migrate、intake、prp review、CodeWiki、clarify、fix、bug close 等尚未完成的流程。

结合当前对话的显式调用、已确认范围、待回答问题、失败与交接记录，以及目标现场识别。
已经完成、取消或被用户替代的流程不算在途；draft PRP、open Bug 或待办事项本身不代表流程已启动。

目标与边界：

- 先核对本次目标；Git 仓库解析绝对 `REPO_ROOT` 并识别已有改动。
- 判定 Gitflow 交付分支（含角色分支）时以当前 checkout 分支名为准。
- 续办尚未 Git 化的 init/bootstrap/migrate 时按 `references/initialization.md`
  核对普通目录和父仓库边界。
- clarify 可仅依赖已确认议题，不要求 Git 仓库。
- 不得在识别前统一要求 manifest ready 或 clean。

按需核对 manifest、当前分支、相关 worktree、产物、验证与恢复记录：

- 四种 kind 的交付分支均读 `references/delivery-contract.md`，通过
  `delivery status` 查看身份、阶段记录和 worktree 路径。
  - 按下一 intent 切到对应已有 worktree，缺树则停止。
- 按原阶段要求检查证据是否支持当前工作；gate 只读作配置或并行上下文，不作进度关口。
  不能仅凭文件存在或历史 passed 判断阶段完成。
- 不能仅凭 tree CLI 的 in_progress 或当前 checkout 缺少材料断言没有在途流程。

委托与候选：

- 同一流程的内部委托先续办未完成的子步骤，再返回调用方。
- 已识别 PR 返工时，保留父 intent 与原验证请求，子阶段结束后回到原 pr 更新原 PR 并轮询。
  - 普通 next 本次选择的是该父 pr，必要补审补测属于其恢复范围；不把内部阶段结束当成父流程完成。
  - 不重复已齐 reviewer 或另开 deliver；没有该父上下文的普通交付仍按单步规则。
- 已有 verify 小 loop 时，恢复其原 scope/选题、左端点和待修绿/待复审状态，再续办 verify。
  - code-review 退勾是该 loop 的内部返工；先修绿再派增量审查，不按首个退勾项提前重开审查。
  - 只从已有调用栈、objectives 续办备注或草稿恢复父 intent，不把草稿当作进度 gate；范围缺失则停止报告。

- 多个独立候选且上下文未指定当前目标时，列出候选并询问用户选择。
- 证据冲突或不足时说明缺项，不猜测流程、初始化类型或阶段，
  也不把无法判定当作无在途而委托 tree。
- 没有统一的 workflow 状态文件；使用已有上下文与产物，不新增状态协议。

可选加速（见 `common.md`「Jev 可选加速」）：

- 仅当候选下一阶段或目标**选项已知**且 ≥2、tool 可用时。
- 调用：`choice`；state = 在途摘要与候选列表。
- 选项键与候选一一对应，另加 `ask`。
- 采信后仍按原 intent 前置与确认规则委托。
- `ask`、单候选、证据冲突或未采信走主 Agent / 询问。
- ❌ 不发明未列出的阶段。

本次正在执行的 next 不作为候选再次委托；上次 next 的协调记录只用于恢复其已锁定的原 workflow。
无法恢复唯一原流程时按证据不足报告，不递归调用 next 来重新判定。

### 续办与交接

完整读取所选 intent 及其要求的公共引用，以其编号工作流、前置条件和失败恢复规则为准。

- 先复核 `objectives.md` 勾选与 `delivery.json` 身份，从尚未勾选的下一步续办。
  - 已勾且仍有效的步骤不重做已验收且仍有效的操作。
  - ❌ 不读 stage gate 表选型；report 只证明做过，不当通行证。
- 当前交付 intent 已完成、交付未结束时，可委托下一阶段。
  - 四种 kind 共用主线；续办前读 `references/delivery-contract.md`。
  - 主线前半：start → integrate（仅 release）→ 可选 design → 开发 → converge。
  - 主线后半：lint → code-review → verify branch → fact audit → [pr（仅 PR mode）] → close-out。
    进入 fact 前按 [pre-gitflow-finish](pre-gitflow-finish.md) 执行可选 hook；
    仅文档直接进入 fact，其他改动补审补测，失败仅汇报，续办不重跑已执行 hook。
  - 无对应未勾项则跳过。
  - 是否 design 读 `delivery.json` / objectives 的 `needs_design`；不按 kind 猜。
  - 有无开发 / converge：只看 objectives checklist 勾选与 release 的 `has_dev`；
    ❌ 不因 roster `0,0` 强行进入 owner 开发或 converge。
  - release：checklist 须含 integrate；未勾则先 `$mdf integrate`；工作线正文四选一。
    - collab-mode 的 integrate 未勾且尚待接手时，按 [交接契约](collab-mode.md) 报告本仓材料并结束。
      已接手则操作两端；integrate 已勾时按本仓剩余步骤续办，不重做交接。
    - 跨 worktree 需要且通道未打开时先 `$mdf integrate`，续办已有通道不重复 init/poll。
    - 双端验收且确认不再改代码后才委托 code-review；integrate 须已勾。
  - 开发未完成时（对应 checklist 项仍为 `[ ]`）：
    - `needs_design: yes`：沿用 qa/dev 分工；无分工则先 write-tests 再 implement。
    - `needs_design: no`：在 owner 按 objectives 完成开发。
      不委托 write-tests/implement，除非 objectives 明确要求。
- 存在仍在运行的执行者时报告其进度或待交接项，不重复执行其工作。
- 缺 report 或未勾选：按原 intent 原地补做并自勾；不发明相对上游的过期 gatekeeping。

授权与确认：

- 显式 next 授权在已确认范围内续办所选 intent，或进入交付主线的下一个 intent。
- 原流程的用户确认、输入、权限与验证要求继续适用，已有有效确认无需重复取得。
- next 不代替方案确认、初始化启用确认或原流程要求的 Git 操作授权。
- 用户仅要求查看时保持只读，报告下一步。
- 条件不足时明确说明：
  - 当前流程与步骤、判定证据、阻塞原因。
  - 用户需要回答的问题、补充的材料或执行的命令。

范围与结束：

- 一次 next 只续办一个所选 intent（包含其内部委托），完成后报告实际结果和后续步骤。
- 不自动串联其余主线，不在续办结束后追加树。
- 所选 intent 为在途 deliver 时，其内部持续交付委托按 `references/deliver.md` 执行。
  - 不得将普通 next 自动升级为 deliver。
- 失败保留现场，按原流程交接。
- 无在途时不自动启动 init、start、prp review 或其他工作；只委托 tree。
- `--depth` 仅在委托 tree 时生效，不控制续办步数。
