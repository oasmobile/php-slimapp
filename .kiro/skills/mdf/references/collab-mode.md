# Collab-mode 契约

本页规定 release 的 collab-mode 如何交接、接管与联调，供 start / integrate / next / deliver 读取。

执行联调前读取 `references/common.md` 与 `references/delivery-contract.md`；当前会话已完整读取则复用。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve role                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 调用上下文不明 ──────────→ [报告缺项并询问]
                 ├──── start 或尚未接管两端 ────→ 2 Handoff
                 └──── 已接管两端 ──────────────→ 3 Check pair

仅交接分支进入步骤 2；步骤 3 由步骤 1 的联调分支进入，不是步骤 2 的后续。

┌──────────────────────────────────┐
│ 2 Handoff                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 材料缺失 ────→ [保留现场并报告缺项]
                 └──── 交接完整 ────→ [结束或返回调用方]

┌──────────────────────────────────┐
│ 3 Check pair                     │
└────────────────┬─────────────────┘
                 │
                 ├──── 身份或访问条件不符 ────→ [报告缺项并保留现场]
                 │
                 ▼ 两端身份与 Goal 已确认

┌──────────────────────────────────┐
│ 4 Agree plan                     │
└────────────────┬─────────────────┘
                 │
                 ├──── 范围或计划未确认 ────→ [留在 4 澄清计划]
                 │
                 ▼ 计划与双方责任明确

┌──────────────────────────────────┐
│ 5 Run plan                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 可修复失败 ──────→ 5 Run plan
                 ├──── 不可恢复阻塞 ────→ [保留两端现场并报告]
                 │
                 ▼ 两端计划已执行

┌──────────────────────────────────┐
│ 6 Dual accept                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 用例或任一端未通过 ────→ 5 Run plan
                 │
                 ▼ 双端验收通过

┌──────────────────────────────────┐
│ 7 Freeze and report              │
└────────────────┬─────────────────┘
                 │
                 ├──── 仍需代码改动 ──────→ 5 Run plan
                 ├──── 提交或勾选失败 ────→ 7 Freeze and report
                 │
                 ▼ 报告与两端 integrate 勾选已提交

┌──────────────────────────────────┐
│ 8 Return                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 完成证据缺失 ────→ 7 Freeze and report
                 └──── 证据完整 ────────→ [报告收口并返回调用方]

```

## 工作流（唯一执行契约）

调用方为 start / next / deliver 的交接时只执行 1–2；已接手两端的 integrate 执行 1、3–8。
各端身份、目标与 roster 沿用自己的交付材料，内部联调不提前完成外层 Goal。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve role | 约束 | 确认本次是交接或已接管的联调 | 调用方、两端授权 | 交接2；联调3 | 报告缺项并询问 |
| 2 | Handoff | 约束 | 输出本仓交接材料，保留 integrate 未勾 | 完整交接材料 | 结束或返回调用方 | 保留现场并报告缺项 |
| 3 | Check pair | 脚本 | 核对两端身份，建立或复用 Goal | 身份、权限、Goal | 4 | 报告缺项并保留现场 |
| 4 | Agree plan | 约束 | 对齐场景、数据、依赖、责任与验收计划 | 已确认计划 | 5 | 留在4澄清 |
| 5 | Run plan | 约束 | 按各端 roster 执行计划与修复 | 原 intent 产物与提交 | 6 | 可修回5；不可恢复则报告 |
| 6 | Dual accept | 约束 | 执行真实调用链与两端验收 | 双端测试报告与结果 | 7 | 任一未过回5 |
| 7 | Freeze and report | 约束 | 冻结、交报告、勾选两端 integrate | 结论、报告与提交 | 8 | 需改回5；提交失败留7 |
| 8 | Return | 约束 | 核对完成证据，完成本轮 Goal 或返回外层 | 两端完成证据、Goal 归属 | 结束或返回调用方 | 缺证据回7 |

## 术语与数据结构

### 责任与范围

collab-mode 由一个接手 Agent 同时操作前后端项目的 release worktree。

- start Agent 在本仓准备 release 分支、owner worktree 与 objectives，完成后交接。
- 接手 Agent 在自己的 workspace 中访问两端，直接调度代码、测试、配置、服务与依赖。
- 本模式不 init、不 poll、不 listen、不 send，不使用 `.integration/` 消息通道。
- 两端各自保留 delivery 身份、objectives、roster、提交与报告，不新增跨仓状态文件或 CLI。
- 本模式只改变联调的操作责任；next 沿用原授权，deliver 遵守其 until 边界与 confidence 策略。

### 交接与接管

start Agent 完成本仓步骤 5 后，将以下材料交给用户或接手 Agent。

| 材料 | 内容 |
| --- | --- |
| 交付身份 | 本仓名称、release 版本、完整分支名、owner worktree 绝对路径 |
| 已确认范围 | 本版范围、允许修改的内容、非目标、可验证验收 |
| 进度 | objectives 路径、`needs_design`、`has_dev`、roster 与未勾项 |
| 对端信息 | 已知的前后端对应关系、对端仓库或 worktree 路径；未知项明确标注 |

- 本仓 objectives 工作线写 `collab-mode`，联调正文记录交接信息；integrate 保持 `[ ]`。
- start Agent 不要求访问对端，不替接手 Agent 创建对端分支、启动服务或执行联调。
- 独立 start 交接后结束；deliver 内部委托则返回调用方并说明尚待接手。
- next / deliver 尚未接管两端时，也交接并结束；不得把本仓 start 成功视为联调或交付完成。

**接管条件**

接手 Agent 执行 integrate 前，先核对前后端两份已启动的 release worktree。

- 用户已将两端 worktree 交给本 Agent，且当前 workspace 可读写两端并控制所需进程。
- 分别读取两仓 Agent 指令、MDF 配置与交付材料，沿用各自范围与验证命令。
- 用每端绝对路径核对 Git 根、`release/<semver>`、delivery 身份与 objectives。
  - 每端版本分别采用已确认值，不要求两仓版本相同，不从另一端推断版本。
  - 分别运行 `git -C <owner> rev-parse --show-toplevel` 与 `git -C <owner> branch --show-current`。
  - 再运行 `mdf.py delivery status --repo <owner>`。命令失败或身份不符则不进入联调。
- 两端工作线均为 `collab-mode`，checklist 均含 integrate；已有改动按各仓入口规则处理。
- 对端尚未 start、路径或权限缺失时，报告缺项并保留现场，等待对应 start Agent 准备。
  - 不自动创建第二套分支或 worktree，不接管未经交付的仓库。
- 对两端的每次文件、Git、测试与进程操作，均指定所属 worktree 的绝对路径。

### 执行与收口

接手 Agent 按已确认范围执行两端联调，并负责核实两端的结果。

- 步骤 3 的 Goal 覆盖两端，完成判据是双端验收、冻结、报告与两端 integrate 勾选。
  - 已有外层 Goal 时复用；内部联调完成只回报结果，不提前置外层 complete。
- 步骤 4 沿用 objectives 的已确认内容；计划未确认只澄清，不提前修改代码。
- 步骤 5 按各端 `needs_design` 与 roster 委托原 design、开发与 converge，不按模式跳过。
  - 在缺陷所属仓库按 delivery-contract「补覆盖」修复、复测与提交，不用跨仓 `bug-request`。
- 不能现场修复时按该仓 Bug 流程处理；仍阻断验收则保持未完成，报告阻塞。
- 步骤 6 分别保存两端报告；单端通过不能代替双端验收，失败不勾 integrate。
- 步骤 7 核实两端无更多代码修改，提交冻结结论、报告与两仓 objectives 的 integrate `[x]`。
  - 已有勾选与提交不重复执行；仅两端证据都完整后进入步骤 8。
- 步骤 8 独立调用报告收口；内部委托返回调用方，按已有 next / deliver 授权继续。

- 从执行联调起强制 Goal。Goal 完成前，用户没让你停，永远不许停下来。
- code-review 仍须等待双端验收、冻结与 integrate 勾选，各仓使用自己的审查基线。
- 每仓随后执行 verify branch → fact audit → close-out；独立 integrate 不自行执行 close-out。
