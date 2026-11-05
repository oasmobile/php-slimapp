# 收敛（Converge）

核对 objectives **前置**已勾，跑 **verify smart** 修到达成，再自勾 converge。
❌ 此处的「验」不是 verify branch。
❌ 不以 `gates/converge.json` 为完成条件或进度账本。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Dispatch                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 已派
┌──────────────────────────────────┐
│ 2 Join                           │
└────────────────┬─────────────────┘
                 │
                 ├──── 需测试修改批准 ────→ [主会话确认后带 --test-approval 重试 2]
                 ├──── 拒绝测试修改 ──────→ [写阻塞记录并停止]
                 ├──── 失败/缺失 ─────────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Accept                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 前置未勾或 smart 可修 ────→ 3 Accept
                 ├──── 需测试修改批准 ───────────→ [确认后 resume 回 3]
                 ├──── 拒绝测试修改 ─────────────→ [写阻塞记录并停止]
                 ├──── 外部阻塞或三轮无进展 ─────→ [记录阻塞并停止]
                 │
                 ▼ 前置已勾且 smart 通过
┌──────────────────────────────────┐
│ 4 Tick                           │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [停止并报告]
```

## 工作流（唯一执行契约）

读取 `references/delivery-contract.md`、`references/common.md`。
CLI：`python3 "$MDF_ROOT/scripts/mdf.py" delivery <action> --repo "$REPO_ROOT"`。
独立调用只推进当前 intent；deliver 内部委托时完成后返回调用方。
启动恰好 1 个 owner subagent 执行步骤 2–4；当前 Agent 不得代做。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Dispatch | Subagent | 启动恰好 1 个 owner subagent 执行步骤 2–4 | 已派执行者 | 2 | 停止并报告 |
| 2 | Join | 约束 | 按需 roster-join 或检查 owner | roster-join/状态 | 3 | 待批准重试 2；拒绝停；其他停 |
| 3 | Accept | 约束 | 前置勾选 + smart + 适用 coverage；循环到达成 | checklist、smart、coverage 或未配置说明 | 4 | 可修/待批准回 3；拒绝或阻塞停 |
| 4 | Tick | 约束 | 自勾 objectives 的 converge 项并提交 | objectives、提交 | 结束 | 停止并报告 |

## 术语与数据结构

### 执行者

- 独立调用与 deliver 委托均启动恰好 1 个 owner subagent 执行步骤 2–4。
- 当前 Agent 不得代做 Join、Accept 或 Tick。不计入 roster，不可配人数。
- 无法提供 subagent 时停止，不降级代做。
- 已有 converge 执行者先等待，不对同一
  owner 另开第二个。
- subagent 绝对路径绑定 owner；禁止新建 worktree、禁止要求用户切换；
  禁止 `move_agent_to_root`。
- 绑定成功后横幅用 owner 的 worktree 路径。
- 结束后核对 objectives 的 converge 项已勾；不以 gate 文件代替。
- 需测试修改批准时 subagent 停止并交出未决；主会话确认后 resume
同一 subagent：
  - Join（步骤 2）待批准：确认后带 `--test-approval` 重试 2。
  - Accept（步骤 3）待批准：主会话确认后 resume 回 3。
- deliver 委托时 subagent 按其 confidence 策略裁定并记录批准；低 confidence 回主会话请求用户确认。

### 范围与前置条件

仅在 owner 工作。objectives 的 converge 项须仍为 `[ ]`；已勾则停止并报告已完成，
不重跑。release `has_dev: no`（该项应由 start 预勾）不得进入本 intent。

`needs_design: yes` 时：

- 按 roster 的 qa/dev strategy 合流（`best-of-n` / `partition`），规则同前。
- qa/dev ≥1 时运行 `delivery roster-join`；合并后清理角色 worktree。
  roster `0,0` 无角色，不调用 roster-join；检查 owner 产出已提交。
- 进度看 objectives：design / write-tests / implement（或 owner 开发）须已勾。

qa/dev ≥1 时的续办与清理：

- 续办仍调用同一命令；脚本核对已记录提交是 owner 的祖先，现存角色未改变，随后只清理剩余角色。
- 角色均已清理时同样核验记录，不重建角色、不再次合并。
- ❌ 缺少有效记录却缺角色时停止并报告。
- `stale_roster_join` 表示现场被其他操作改变，停止。

`needs_design: no`：无角色可合；确认 owner 干净且开发改动已提交；objectives 的
owner 开发项已勾。❌ 不因 roster `0,0` 在无 owner 开发项或该项已预勾时仍要求「开发」。

PR 模式在 roster-join 前按 [squash](squash.md#pr-模式与-planning-land-的必要检查) 检查 owner 与各待合入角色分支，
先完成分析及必要的分段 squash，无可压缩区间则 no-op。

local 模式 close-out 可选 squash 使用 `squash.md` 的安全 floor，不以开发完成项或
roster-join 材料另设地板；实际 merge commit 仍是保护边界。
local 模式下本 intent **不**询问、执行或委托 `$mdf squash`。

### Accept（前置勾选 + smart + 适用 coverage）

1. 核对 `objectives.md`：适用的 design / 开发依赖项须为 `[x]`，按 `needs_design` 与 roster 判断。
   release 联调内部委托时，integrate 的最终收口不是本步前置；不按清单位置要求它先勾选。
   未完成的开发依赖继续开发/勾选，不得虚构完成。
2. 运行 `$mdf verify --scope smart`（涉及 module 的 lint+build+quick +
   本分支相对 start_commit 新增/改动的测试；可加 Agent/Jev 选题）。
3. ❌ 不得用 verify branch（smoke/release）冒充本步。
4. 失败时遵守「测试失败工作流」（单用例复测 → 修一个复测一个 → 再继续）。
5. 可修实现则修并**提交**相关实现/测试路径后再跑 smart；改测试/门槛须批准。
6. feature/release 的 smart 通过后运行已配置的 coverage。循环直至前置已勾、smart 与适用 coverage 均绿，或阻塞停止。

阻塞写入 `changes/unreleased/<slug>/converge-blocked.md`
（目标决定、拒绝测试修改、三轮无进展）。

### Tick

1. 核对 smart 与适用 coverage 已通过（或未配置/不适用），再将 `objectives.md` 中 converge 项改为 `[x]`。
2. 提交 objectives（及本步相关已改产物）。
3. ❌ 不以 `delivery record/check --stage converge` 为完成条件。
   - 并行辅助若仍调用 `record`，语义仅为配置/指纹快照，**不是**进度。


### Coverage 检查点

本节定义可选 coverage 在收敛验收中的位置。

- 仅 feature/release 实际进入本 intent 时，在 smart 通过后运行 `$mdf verify coverage`。
- 全部已配置 module 的 targets 均须通过；repo 级覆写时只运行该完整定义一次。
- 未配置时记录未配置，继续 Tick；已配置失败时不勾 converge，修复后重跑 smart 与 coverage。
- 沿用 has_dev: no 等既有 converge 跳过规则，不为跳过项额外运行 coverage。
- 人工 feature、adhoc、bugfix、hotfix 不自动运行 coverage；可显式调用 verify coverage。
