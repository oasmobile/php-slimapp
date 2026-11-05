# PR

## 决策树

```text
┌──────────────────────────────┐
│ 1 Check                      │
└──────────────┬───────────────┘
               │
               ├──── 不符 ────→ [保留现场，停止]
               │
               ▼ 通过
┌──────────────────────────────┐
│ 2 Prepare                    │
└──────────────┬───────────────┘
               │
               ├──── 缺前置或返工未完 ────────→ [交接主链，完成后回 2]
               ├──── 已确认等待且无新提交 ────→ 4 Report
               ├──── closed 未 merged ────────→ 4 Report
               │
               ▼ 已准备或恢复
┌──────────────────────────────┐
│ 3 Finish                     │
└──────────────┬───────────────┘
               │
               ├──── finish_busy ────→ [等待持锁调用退出，回 2]
               ├──── 其他失败 ───────→ [读日志，保留现场并停止]
               │
               ▼ 返回实际状态
┌──────────────────────────────┐
│ 4 Report                     │
└──────────────┬───────────────┘
               │
               ├──── 等待合并收尾 ────────→ [等待 2 分钟，只读查询 PR 与关联 CI；收尾后回 3]
               ├──── 可修问题 ────────────→ [主链外修复、补审补测后回 3]
               ├──── 关闭但未合并 ────────→ [保留现场，报告未完成]
               ├──── 完成且核验通过 ──────→ [返回调用方]
               └──── 状态不符或缺证据 ────→ [保留现场，停止]
```

## 工作流（唯一执行契约）

本表由 `$mdf pr`、deliver、next 或 adhoc 调用；只适用于 PR mode。
读取 `references/common.md` 与 `references/delivery-contract.md`。

无账本 adhoc 的专用规则适用于本页全部准备、集成、返工与恢复步骤：

- 不读取、创建或勾退 objectives；前置与完成均核实际报告、平台及 Git 证据。
- 「PR 返工」备注写在 adhoc-status 返回目录的 `code-review.md`，保留相同身份、原验证请求与左端点。
  - 审查终稿保留尚未完成的父 PR 备注；补审补测及 fact 完成并提交候选材料时才清除。
  - 备注仅恢复调用上下文，不作为第二份进度账本；缺少必要参数时停止并报告。
- 普通无账本 source 使用 smart；dev-pr source 全程使用 named smoke，包括集成、CI 返工与 hook 后补验。
- Prepare 仅在首次或实际改动使原证据不再适用时执行 adhoc-change 步骤 1–5；已有适用证据逐项复用。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 约束 | 核边界、身份、现场并绑定 Goal | 配置与 Git 状态 | 2 | 保留现场，停止 |
| 2 | Prepare | 约束 | 核远端集成、前置与候选材料；恢复返工记录 | 账本、返工备注、平台事实 | 首次/更新/merged3；等待/关闭4 | 未完返工交接主链，完成回2 |
| 3 | Finish | 脚本 | 调用 pr 提交或续办 | CLI 状态与平台事实 | 4 | busy 等待后回2；其他读日志并停止 |
| 4 | Report | 约束 | 核结果；轮询或交回主链修复 | 平台结果、修复与合并证据 | 等待留4；修复后或合并回3；完成返回 | 外部阻塞或未合并报告未完成；缺证据停止 |

## 术语与数据结构

### 模式与入口

本页规定 `closeout.mode: pr` 时的交付与恢复。

```yaml
closeout:
  mode: pr
  provider: github # 或 gitlab
```

- 省略 closeout 时使用 local；init 保留配置，doctor 校验。
- origin fetch/push 地址须一致且唯一，支持 SSH/HTTPS 与自建 host；第一版只支持同仓 PR/MR。
- 项目安装并登录 gh/glab；MDF 不自动配置账号、CI、runner 或 branch protection。
- 首次 pr 先完成主链前置，再按下方材料准备条款生成候选材料。
  - 无账本 adhoc 在 Prepare 委托 [无账本 Adhoc 收口](adhoc-change.md) 的步骤 1–5，再返回本页 Finish。
  - 保留真实分支与 worktree，不要求 delivery/objectives；已有损坏账本不能绕过。
- PR mode 的 feature PRP 在源提交中准备 implemented，随 PR 合入 develop 后生效。
- 源分支的候选状态不代表已交付；交付完成看远端目标分支和实际合并结果。
- PR/MR 未完成时必须保留 source branch 和 owner worktree，不得 detach、删除分支或删除工作区。
  - 等待 review、返工、补验、等待合并和 closed 未 merged 都不进入清理。
  - release/hotfix 的 close-out 须完成固定 M 的 tag 发布与 backmerge，之后才可清理远端及本地 source；CLI 始终保留 owner worktree。
  - worktree 删除只在实际收口及最终核验完成后，按原清理授权执行；不能凭 checklist 全勾或 PR 已创建提前删除。
- 已有 Git common dir `mdf/finish/` 操作记录时先按下方恢复路由续办，不重新执行整套材料准备。
  - 四类 Gitflow 使用 `<source>.json`；adhoc 使用 `adhoc-<source 的 SHA256>.json`，内容保存真实 source。
- 每次 CLI 收口持有 Git common dir 的仓库级 OS lock；同源及不同源并发调用返回 finish_busy，不写恢复记录或 Git。
  - lock 只覆盖本次 CLI 操作，不覆盖 Agent 的 2 分钟等待；调用退出或中断时由 OS 释放，不删除 lock 文件。
  - finish_busy 先等待持锁调用结束再续办，不启动第二个写入流程，也不手工删除恢复记录或 lock 文件。

### Goal 与持续推进

在入口确认允许进入 pr、锁定交付身份后，先执行本节，再进行远端集成、材料准备或恢复。
独立 pr、deliver 委托、next 恢复及 adhoc 共用本节；local 模式不创建 pr Goal。

| 已有 Goal | 处理 |
| --- | --- |
| 没有未完成 Goal | 创建本次 pr Goal |
| 阶段 Goal 的完成判据已全部满足 | 先核验证据并置 complete，再创建本次 Goal |
| 未完成 Goal 已覆盖本次 pr | 复用，不重建；同范围续办沿用原 Goal |
| 未完成 Goal 范围更大 | 复用父 Goal，将本次 pr 及完成判据加入其剩余工作，保留原目标与其他未完成项 |
| 无关且未完成 Goal | 保留原 Goal，报告范围冲突；不自动 cancel、覆盖或假称完成 |

- 先读宿主实际 Goal 状态与目标；不能仅因进入 pr 就认定旧阶段已完成。
- 宿主支持更新目标或子项时，将新增收口要求写入父 Goal；仅支持状态更新时，在当前上下文记录父 Goal 与收口要求的关联。
  - 后者不得声称已修改宿主 objective；恢复时从原 Goal、交付记录与返工备注重新核对剩余工作。
  - 不为追加子工作而 complete 或重建尚未完成的父 Goal，不取消既有 Goal。
- objective 包含交付身份、source/target、已知 PR/MR、有效边界与完成判据；尚未创建 PR/MR 时不伪造 ID。
  - 持续等待当前 head 的 CI/review，解决可修反馈，补审补测并更新原 PR/MR。
  - 平台实际 merged，且 source/target/head、双亲 merge commit 与远端第一父链核验通过。
  - `pr` CLI 返回 `status=merged`、`completed=true` 是必要但不充分的证据；还须按下方轮询规则核关联 CI 收尾。
- 轮询、主链外返工与重新提交始终沿用同一个 Goal；子阶段完成不结束父流程。
  - CI 全绿或 review 通过不能完成 Goal；实际 merged 且 CLI 合并核验与关联 CI 收尾均通过后结束 pr Goal。
  - 正常 pending 保持 active；可修失败继续推进，不因一次失败结束任务。
- 仅本次创建或同范围复用的 Goal，可在 pr 合并核验与关联 CI 收尾完成后置 complete。
  - 复用更大范围 Goal 时只记录本次收口完成并返回父流程；父 Goal 仍有剩余工作时不得置 complete。
- 用户停止、预算限制、会话中断或无法自行解决的阻塞按宿主规则处理；保留恢复证据，不标完成。
- 宿主不提供 Goal 时仍按本页轮询与恢复规则推进，并如实说明缺少跨 turn 自动续办保障。
  Goal 不替代平台合并授权，也不越过 deliver 的 until、只读限制或用户暂停。

- pr Goal 完成后返回 objectives 的下一项 close-out；它有独立完成判据，不属于 pr Goal。
  独立 pr、deliver / adhoc 按该步骤继续 close-out；显式 until、用户停止或暂停仍须遵守。
- 普通 next 保持单步语义：本次若选择 pr，完成后报告 close-out 为下一步，不升级为 deliver。

### 提交前远端集成

首次创建及未合并 PR/MR 的源提交更新，都必须先完成本节；已 merged 的恢复不重新集成。
本 intent 的 Prepare 执行本节；local close-out 不使用本节。

- fetch origin 的目标分支并固定最新远端 tip；feature/bugfix/adhoc 对应 `origin/develop`，release/hotfix 对应 `origin/master`。
  - 以远端 tip 为准，不用本地 trunk 或平台的无冲突标记替代；fetch 失败或目标缺失时停止并报告。
- 用 `git merge-base --is-ancestor <远端tip> HEAD` 检查包含关系；“父节点”指 ancestor，不要求直接 parent。
  - 已包含且没有未完成返工时继续核材料；未包含则必须集成，即使试合并完全无冲突。
  - 命令异常不能当作未包含或已通过；先读日志定位。
- 集成前确认 owner clean、无已有 MERGE_HEAD，并保存下节格式的「PR 返工」备注。
  - 尚无 PR/MR 时记录 provider/source/target 与“尚未创建”，不伪造 PR ID，也不提前创建 finish 记录。
  - 固定集成前 HEAD 为增量审查左端点、远端 tip 与原验证请求；退勾 lint、code-review、verify、fact 和 pr。
  - 提交备注后先按 [squash](squash.md#pr-模式与-planning-land-的必要检查) 完成必要检查，squash 后重新固定增量审查左端点。
  - 然后运行 `mdf.py merge-no-ff --repo <owner> --commit <远端tip>`，在本分支解决冲突并提交 merge。
  - 禁止 rebase、force push、整侧覆盖或削弱测试；语义不明时保留现场并询问。
- 只要进行了上述集成，就结束 pr 内部调用栈，由当前 Agent 在主链外依次完成 lint、增量 code-review、verify 和 fact。
  - 无冲突、空树差异或仅非本交付 docs 改动均不豁免；不套用 local 模式的跳过判定。
  - 有有效上轮审查时按 1 人增量新一轮覆盖集成与冲突修复，复核上轮问题；否则按 code-review 首轮规则执行。
  - 普通交付执行 verify branch；人工 feature 执行 verify smoke；adhoc 执行 verify smart；并补原验证请求所需检查。
  - 随后完成 fact audit，必要时 fact update 并复核；人工 feature 保持 fact update 要求。
  - 审查或验证引发修复时按原主链补审补测，直到全部通过；同步报告、objectives 与交付材料并提交。
- 全部完成后再次 pr；独立调用也持续续办，不只报告待办。release/hotfix 候选目录沿用下方返工规则。
  - 创建或更新 PR/MR 前再次 fetch 并检查最新远端 tip；未包含则重复本节，不复用集成前的通过记录。
  - 清除返工备注和恢复候选勾选按下方规则执行；存在未完成返工时不得调用 pr 提交源分支。
  - 检查后远端仍可能并发前进；本节不保证未来 CI 必过，平台 CI 与合并约束仍须针对最终合并结果核验。

### 恢复路由与返工上下文

恢复先核调用边界，再按同一份 finish 操作记录选择 pr 或 close-out。

- PR 恢复优先于 doctor、branch、delivery status 和 adhoc-status；先应用当前 until。
  未 merged 选 pr，已 merged 且关联 CI 收尾通过才选 close-out；显式 until pr 不进入这两个阶段。
  merged 但关联 CI 未收尾或缺少证据时先恢复 pr，按下方轮询规则查回关联运行。
- source 来自已锁定交付、当前完整分支或用户指定；无目标时才检查唯一未完成记录。
  多个候选须澄清；不按时间猜测，不从历史 completed 记录自动启动任务。
- 核 Git common dir、origin/provider、source、target；身份不符保留现场。
- 按原 PR/MR ID 查询；创建响应丢失时按 identity/source/target 查回复用，不重复创建。
- open 且有未完成返工时先恢复「PR 返工」非 checklist 备注。
  保留父 intent、原验证请求、修复前左端点、未完成子步骤，全部完成后才允许更新 PR/MR 或恢复轮询。
- 无新提交且已确认 open 时只轮询；有新 head 时从原 source worktree 调用 `mdf.py pr --repo <owner>`。
  owner 缺失且仍需修改时报告阻塞，不在主 worktree 代写，不重新 start。
- merged 时调用 `mdf.py pr --repo <主路径> --source <原分支>` 核验合并，关联 CI 收尾通过后才结束 pr 并交接 close-out。
  已进入发布或清理的恢复直接执行 [合并后续办](pr-close-out.md)，不重开 pr Goal。
- 清理前置已全部完成、detach 或删除 source 后中断时，从主 worktree 续办 close-out。
  此恢复容错不授权任何流程提前删除 source 或 owner；发布未完而 source 缺失须核实际证据。
- `pr` 在 push 前执行 squash 必要检查；squash_required 时按返回范围整理后重试，不 force push。
- `finish_busy` 时等待持锁调用退出；不删除 lock 或操作记录，不启动第二个写入流程。

### 生命周期

本节以平台实际状态判断 pr 完成，不凭退出码或候选 checklist 判断。

| 状态 | 操作 |
| --- | --- |
| 尚无 PR/MR | 前置与材料齐全后调用 `mdf.py pr --repo <owner>`，push 并创建或查回复用 |
| open | status=waiting_for_merge、completed=false；保持 Goal active，持续轮询 |
| source 前进 | 完成补审补测与 fact，非 force push 更新原 PR/MR |
| closed，未 merged | status=closed_without_merge、completed=false；保留现场，不自动新建 |
| merged | 核身份、head、双亲 merge commit 与远端第一父链；CLI 返回 status=merged、completed=true 后仍须核关联 CI 收尾 |

- PR/MR 由用户或项目 CI 合并；pr 不批准或合并平台 PR/MR，不修改 CI policy。
- pr 完成不执行 tag、backmerge、source 清理或 detach；这些操作全部属于 close-out。
- 未 merged 必须保留 source branch 和 owner worktree；等待 review、返工、补验和 closed 均不清理。
- source/target/head 或实际 M 不符时保留现场；不 reset、覆盖 tag 或改写已合入结果。

### 当前调用内轮询

轮询由当前 Agent 执行，不创建 automation、定时任务或后台常驻服务。

- 首次返回等待时报告 PR/MR 与关联运行链接；此后每 120 秒只读查询 state、head、review/approval 与关联 CI。
  - 使用已登录的 gh/glab 查询记录中的 provider、host、project 和 PR/MR ID；不猜测其他仓库或 PR/MR。
  - 等待拆成不超过 60 秒的可中断调用；期间响应用户输入，累计 120 秒才再次查询平台。
- 关联 CI 包含发起该 PR/MR 的 workflow run / pipeline，以及当前 head 的全部关联运行，包含非 required checks。
  - 从调用上下文、PR/MR 时间线和平台运行详情核实关系，记录 provider、project、run ID、attempt、URL、head 与触发来源。
  - 发起 PR 的运行可能使用目标分支 SHA，不能仅按 PR head SHA 查找；不把同仓库无关运行纳入等待。
  - 保存已确认运行身份与链接到现有交接上下文；中断后查回复用，不以“PR 已合并”丢弃原运行。
- 每轮核完整 run / pipeline 的状态、结论和全部 job 与 step；不能只看 PR checks 摘要或负责 merge 的 job。
  - 查询须遍历分页；发现新 job、关联运行或 rerun attempt 时更新范围，不能复用旧 attempt 的成功结论。
  - PR 已 merged 但关联运行未结束时，保持 Goal active；queued、in_progress、waiting 等状态继续等待。
- open 且 CI/review 仍在运行、等待审批或等待自动合并时，继续本轮询，不结束当前 pr 或 deliver。
  - 没有新结果时不重复汇报；不设固定轮数或总等待超时。
  - 查询本身不重复调用 pr，不重复 push，也不调用 approve/merge 或修改 CI policy。
- 确认 merged 后回步骤 3，执行 `pr --repo <主路径> --source <原分支>`。
  - CLI 仅核验实际合并；`status=merged` 且 `completed=true` 后，关联运行也全部结束且结论通过才返回 pr 完成。
  - skipped / neutral 仅在项目 policy 允许且无失败、未完成 job 时接受；cancelled、timed_out、action_required 不算通过。
  - 调用方继续选择 close-out；不得将 pr 完成报告成整个交付完成。
- 关联运行失败时读取失败 job / step 的日志与报告，按证据修复或处理阻塞；不能因 PR 已 merged 忽略失败。
  - 合并后的失败不得向已合入的 source 追加提交、重开原 PR 或改写固定 M；需要代码修改时按调用边界另行交付。
  - 仅有证据支持暂时故障且已有授权时重试；否则报告运行链接、失败 job 与恢复位置，保留未完成状态。
- 查询失败、权限不足或关联不明不能当作没有 CI；先查明或报告阻塞，不完成 Goal 或进入清理。
  - 平台证据确认没有关联运行时可按无 CI 处理；完成前再次查询，确认没有新增运行或 attempt。
- review 要求修改、CI checks 失败或合并冲突时，先读取已有报告与平台详情，按下方修复流程继续推进。
- 权限不足、无法获取必要证据、身份或历史不符等无法安全自行解决的问题，报告具体阻塞并保留现场。
  - head/source/target 变化时核对来源；本轮修复产生的合法前进按修复流程处理，不覆盖他人提交或改写历史。
  - closed 未 merged 按 closed_without_merge 处理；不自动重建 PR/MR。
- 用户要求停止或会话中断时保留恢复记录、分支与 worktree；之后再次 pr 从该记录续办。

### 反馈修复与重新提交

可修问题交回主链外处理，保持当前任务持续推进；独立 pr 和 deliver 委托均适用。

- 步骤 4 的返工入口：核对反馈对应当前 PR/MR 与 head；读取完整 review、CI 日志和失败报告，定位问题，不为查看输出重复运行。
- 修改前先保存「PR 返工」非 checklist 备注，并按实际影响退勾 objectives 的受影响项及后续项，落盘后再修复。
   - 备注位于本次材料目录的 objectives，记录父 intent 与调用方、原 PR/MR 身份、source/owner/common dir/主路径。
   - 原调用方为 deliver 时保留其有效 until、yolo 与已有授权依据；新调用有显式边界或用户限制时以本次要求为准。
   - 同时记录反馈对应的旧 head、修复前左端点、原验证请求（scope/模块/选题或 suite/完整命令）及返回 PR 的位置。
   - 进度仍只由 checklist 决定；备注只恢复父流程与参数，不另加 gate 或状态协议，不改写人工工作勾选来源。
   - 冲突通过 merge 最新远端目标分支解决；不 rebase、不 force push，不覆盖他人现场。
   - CI 暂时故障仅在证据支持时重试；不降低测试、审批或 branch protection 要求。
- 结束 pr 内部调用栈，在主链外按影响恢复 lint、增量 code-review、原验证范围及 fact。
   - code-review 与 verify 可相互退回修复，直到问题解决、所需审查和验证通过；同步材料并提交。
   - 独立 pr 也由当前 Agent 续办上述阶段，不仅报告待办后结束；deliver 返回 Select 按原阶段推进。
- 全部补审补测与 fact 完成后，复核候选材料、恢复 pr 候选勾选，在更新 PR/MR 前的材料提交中移除该备注。
   - 清除备注不会提前声明实际完成；中断后按前置全勾、本地 head 与 finish 记录的差异恢复更新，不重做首次材料准备。
   - 恢复 pr，步骤 3 从原 source worktree 非 force push 合法新提交、复用原 PR/MR，继续每 2 分钟查询新 head。
   - 保留 finish 操作记录；不删除或篡改记录以绕过 CLI 核验。
   - release/hotfix 同样允许在 PR/MR 合并前更新；合并后固定 M，源工作区的新增或未提交改动须在发布前报告。

release/hotfix 的材料即使已位于 `changes/<version>/`，PR/MR 未合并时仍是候选发布材料。

- 在同一版本目录退勾 objectives、更新 code-review、verification-report、fact 与交付总结，不另建 unreleased 副本。
- CLI 的 delivery 与 verify branch 共用候选目录；不得重复 release-closeout、搬回目录或删除 finish 记录。
- 保留原版本和发布范围；按修复同步候选 CHANGE、CHANGELOG 和相关对象，检查链接及声明与实现一致。
- release 首轮审查仍从目标 master 的上一正式发布记录确定基线，不把候选 manifest 的 latest_release 当作已发布版本。
- fact 使用 paths 范围补齐受影响的事实页，避免把尚无正式 tag 的候选版本当作 branch 基线。
- 补审补测与材料提交完成后更新原 PR/MR；合并并发布后，该版本材料冻结。


### 候选材料准备

Prepare 在首次提交前完成交付材料；恢复已有候选材料时不重复发布准备。

- 普通交付与人工 feature 读取 [close-out 的材料规则](close-out.md#s3) 至步骤 9 的材料条款。
  这里只复用材料规则，不执行 close-out intent、local 集成或 Finish Gitflow。
- release/hotfix 的 bug close 返回「实现已变更」时回本页步骤 2，先补审补测与 fact。
  Bug 状态保持，补验通过后恢复 closures；不得回到合并后 close-out。
- feature/bugfix 补齐 Change 与 HTML 总结；feature 的 implemented 是合入后的候选状态。
- release/hotfix 完成 Bug closures、release-closeout 与版本材料准备；不创建 tag、不 backmerge。
- adhoc 读取 [Adhoc Close-out](adhoc-close-out.md) 的 Change 与 validate 材料条款。
  不执行该流程的 local 集成或 Finish；不要求 HTML 总结。
  - dev-pr 接管的 source 沿用 [dev-pr](dev-pr.md) 的 smoke 要求，包括集成和返工后的补验。
  - 无账本时改用 [无账本 Adhoc 收口](adhoc-change.md) 的准备步骤，不补造 checklist。
- 所有 kind 先完成主链 verify、fact 与配置的 hook；材料不替代前置验收。
- 提交前重核远端 ancestor 与 squash；目标前进则回本页集成、补审补测循环。

### 勾选与交接

pr 只维护自己的 checkbox，close-out 是其后无 checkbox 的必执行步骤。
无账本 adhoc 不创建 checkbox；pr 与 close-out 的完成仍分别核实际平台与清理结果。

- 提交候选材料前将 pr 项勾选并提交；这只表示已准备候选，不表示 intent 或 Goal 完成。
- 创建 PR、CI 全绿与候选勾选均不能结束 pr；必须等待实际 merged、合并核验与关联 CI 收尾通过。
- merged 后不追加仅为勾选的源提交；返回调用方执行 close-out，无须额外文档 PR。
- close-out 只核实际结果，不预勾、不补勾；完整交付不能因 checklist 全勾跳过续办。

### 调用边界与提交裁定

步骤 1、每次内部委托及步骤 3 提交前，先核当前调用的边界与有效授权。

- deliver 委托先核 until，再按 deliver-policy 核 pr 入口确认（yolo 跳过）；沿用其 confidence 策略。
  被截止的 pr 不绑定新 Goal、不准备材料、不 push 或轮询。
- 创建或更新 PR/MR 前按 deliver-policy 裁定源提交与 push；低 confidence 返回 deliver 步骤 6。
  yolo 不受 confidence 限制；独立 pr 沿用调用授权，不引入 deliver 的评分。
- squash、bug close、code-review、verify 与 fact 的内部返工也先核 until；被截断返回外层，不绕过边界。
- 仅 pr 的实际合并核验与关联 CI 收尾均完成才结束其同范围 Goal；随后按原调用边界交接 close-out。
