# 人工 feature 续办

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check delivery                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 已锁定 PR 恢复 ────→ [委托 PR 并返回]
                 ├──── 身份或清单不符 ────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Select step                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 人工工作未勾 ──────→ [交接用户并返回调用方]
                 ├──── 已实际完成收口 ────→ [返回调用方核验实际收口]
                 ├──── 前置未完成 ────────→ [停止并报告]
                 │
                 ▼ 可执行阶段已确定
┌──────────────────────────────────┐
│ 3 Delegate                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败或待确认 ────→ [按原 intent 交接]
                 └──── 阶段完成 ────────→ [返回调用方]
```

## 工作流（唯一执行契约）

PR 恢复优先：调用方先按 [PR 的恢复路由](pr.md) 核原 source 的操作记录与返工备注。
命中时未 merged 恢复父 pr，已 merged 续办 close-out，不运行下表的 delivery status；没有 PR 恢复时才按人工七项清单续办。

仅 next / deliver 在 `delivery.json` 的 `manual` 为 true 时内部执行本工作流。
start 与各阶段 intent 只读取下文对应条款，不执行本续办工作流。
读取 `references/common.md`；当前会话已完整读取则复用。
next 在 Resume 内执行本表；deliver 在 Select 内执行 1–2，再在 Execute 内执行 3。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check delivery | 脚本 | 先核 PR 恢复；否则核身份与七项清单 | 记录或 status、账本 | PR 委托并返回；其余2 | 停止并报告 |
| 2 | Select step | 约束 | 核人工工作、PR 实际状态与剩余步骤 | 勾选、平台、收口证据 | 阶段 3；已收口返回 | 人工未勾交接；不符停止 |
| 3 | Delegate | 约束 | 按阶段表执行一个原 intent 并交接 | 原 intent 产物与勾选 | 返回调用方 | 按原 intent 交接 |

## 术语与数据结构

PR mode 的 pr 候选项已勾时仍先核平台实际状态；未 merged 继续 pr，merged 后必选无 checkbox 的 close-out。
已完成收口须有 finish-gitflow 的实际完成证据，不以 checklist 全勾跳过续办。

### PR mode 的收尾步骤

按 [交付契约](delivery-contract.md#pr-mode-的收尾步骤) 生成和续办 objectives。
PR mode 末尾为 pr checkbox 与无 checkbox 的 close-out；local 保持原顺序。

### 身份与启动

`$mdf start --manual` 按 feature 处理，不绑定 PRP；`delivery.json` 写入 `manual: true`。
本页规定人工 feature 的主线；普通交付的 design、开发与 converge 规则不适用。

- start 通过 clarify 确认工作范围及 slug；独立调用先询问再建议，deliver 按其 confidence 策略裁定。
- 从 develop 创建 `feature/<slug>` 与独立 owner worktree；roster 固定为 `0,0,1`。
- objectives 使用 `assets/templates/manual-objectives.md`。
  - 顺序：start → 人工工作 → lint → code-review → verify smoke → fact update → [pr（仅 PR mode）] → close-out。
- start 自勾 start；人工工作仅由用户显式勾选，Agent 不得代勾。
  - 用户可要求 Agent 介入实现与测试；介入不代表人工工作已完成。
  - next / deliver 在人工工作未勾时交接给用户；所有模式同样不得代勾或越过。
  - 用户显式勾选后，由 next 单步续办或 deliver 串联剩余阶段。
- code-review 用 1 个 reviewer；前置为人工工作已勾，不要求 converge。
- verify smoke 执行 feature 的 branch 验证（lint/build/quick/smoke），
  写入 `verification-report.json`；通过且必要增量复审完成后自勾 verify smoke。
- fact update 直接对齐当前事实，沿用其内部审阅与验证，通过后自勾 fact update。
  - deliver 的 until 排除内部 fact audit 时，fact update 返回截止点与未完成步骤，不代勾 fact update。
  - 进入前按 [pre-gitflow-finish](pre-gitflow-finish.md) 执行可选 hook；仅文档继续，
    其他改动先补 code-review 与 verify smoke；失败仅汇报，续办不重跑。
- close-out 核对上述前置项及报告；不要求 design、converge 或独立 fact audit 项。
  - Change 的 `proposals: []`；无 PRP 状态更新。
  - local 模式沿用 feature 的 no-ff 合入 develop、源分支删除及 worktree 保留规则。
    PR mode 先执行 pr，merged 后再执行 close-out。

### 续办与验收

步骤 1 调用 `mdf.py delivery status --repo <owner>`，核对：

- `manual: true`、`feature/<slug>` 与 `needs_design: false`。
- 无 proposal，roster 为 `0,0,1`。
objectives 须与模式对应的固定顺序一致且没有缺项；不符则报告具体差异并停止。

步骤 2 先核对 start 已勾；未勾或人工工作勾选来源不明时停止并询问。
人工工作未勾时返回用户交接，不委托开发，也不自动勾选。
人工工作已勾后，先核 PR 与实际收口状态，再按以下阶段表选择；各项前置必须已勾。
PR mode 尚未 merged 时，即使 pr 候选项已勾仍选 pr；merged 后选无 checkbox 的 close-out。

| 清单项 | 委托 intent | 完成证据 |
| --- | --- | --- |
| lint | `references/lint.md` | 全部 module lint 通过、勾选与提交 |
| code-review | `references/code-review.md` | 1 人审查终稿、勾选与提交 |
| verify smoke | `references/verify.md`，branch scope | 通过的 branch 报告、必要增量复审、勾选与提交 |
| fact update | 先可选 hook，再 `references/fact-update.md` | 适用补审补测、事实同步、内部审阅、勾选与提交 |
| pr（仅 PR mode） | `references/pr.md` | 实际 merged 且核验通过 |
| close-out | `references/close-out.md` | Change、实际 Gitflow 结果 |

步骤 3 完整读取所选 intent 后执行；不同时委托多个阶段。
next 完成一个阶段后结束；deliver 返回 Select，继续选下一阶段。
deliver 委托时先核 until 截止点；只执行边界内的当前 intent，各项 decision 按其 confidence 策略裁定。
清单全勾但尚未实际收口时仍选择对应 pr 或 close-out；只有实际收口完成才返回完成结果。
