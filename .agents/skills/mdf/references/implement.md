# Implement

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 缺底座 ───────→ [停止，提示 $mdf design]
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Implement                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 未满三轮且下一步明确 ────→ 2 Implement
                 ├──── 测试争议 ────────────────→ [交接未决并返回调用方]
                 ├──── 目标不明或无法完成 ──────→ [停止并报告]
                 │
                 ▼ 实现完成且自检已记录
┌──────────────────────────────────┐
│ 3 Record                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [停止并报告]
```

## 工作流（唯一执行契约）

读取 `references/delivery-contract.md`、`references/common.md`；涉及 PRP 时读取 `references/object-contract.md`。
CLI 使用 `python3 "$MDF_ROOT/scripts/mdf.py" delivery <action> --repo "$REPO_ROOT"`；角色模式下为角色 worktree 路径。
独立调用只推进当前 intent；deliver 内部委托时完成后返回调用方，由其选择下一阶段。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 约束 | 按 roster 进入 dev/owner 并核对底座 | worktree、底座 | 2 | 缺底座提示 `$mdf design`；其他停止 |
| 2 | Implement | 约束 | 按目标与设计实现并自检 | 自检命令、结果、待验项 | 3 | 未满三轮且下一步明确则 2；测试争议交回；否则停 |
| 3 | Record | 约束 | 自勾 objectives 并提交实现 | 勾选、自检摘要、提交 | 结束 | 停止并报告 |

## 术语与数据结构

### 范围与前置条件

先运行 `delivery status --repo <owner 绝对路径>`。
角色分支合入 owner 前没有 delivery.json。
读取 `roster`，按下表确定实现位置。

| `roster.dev` | 实现位置 |
| --- | --- |
| `roster.dev == 0` | 在 owner 实现，不切角色树 |
| `roster.dev ≥ 1` | 读取 `worktrees.dev` 列表；缺对应树则停止 |

- 独立调用时列表仅一项则用该项的 `path` 与 `branch`；≥2 项时用会话当前所在的 dev worktree，
  不在任一 dev worktree 中则询问 index。
- deliver 只续办一路时用该路；对列表每一项分派独立 subagent，不把兄弟路径传入任务。
- 用 `git -C <该绝对路径>` 与该路径下的绝对文件路径操作；delivery CLI 的 `--repo` 也传该绝对路径。
- 角色树先运行下列命令合入 owner；已在该 worktree 时仍先合并。冲突保留现场。
  - `python3 "$MDF_ROOT/scripts/mdf.py" merge-no-ff --repo <该绝对路径> --commit <owner 完整分支名>`
- ❌ `roster.dev ≥ 1` 时不得在 feature 上实现（指 owner，不是 kind）。

路径与会话根按调用方式处理（目标为该 dev 绝对路径与分支；index 1 形如
`dev/feature/<slug>`，不是 owner）：

- subagent（含 deliver 步骤 4）与非 Cursor 主 Agent：按 `common.md`「切换工作区」
  绝对路径绑定该 dev；禁止新建 worktree、禁止切到 owner、禁止要求用户切换；
  禁止 `move_agent_to_root`。
  - 用 `git -C`、`--repo` 与该路径下绝对文件路径；核对该路径 toplevel 与分支。
- 独立调用的 Cursor 主 Agent：按 `common.md`「切换工作区」`move_agent_to_root`
  进入该 dev。
- deliver 步骤 3 主 Agent 续办时禁止切会话与 `move_agent_to_root`，保持 owner；
  用 `git -C` 与绝对路径操作。
- 绑定或切换成功后横幅用该 dev 的 worktree 路径；相对上一处变化时打印切换三行。

再遵守：

- `dev_strategy` 为 `partition` 时只做 design 派给本 index 的切片，仍不看兄弟代码。
- roster.models 含 `implement` 时把该值写入本路任务，按口语描述现场解析（可多个模型）。
  - 没有则不提模型或 effort。
  - 不得写入其他 intent 的模型。
- 测试完成不是前置条件。
- 独立调用不自动分派 Agent；deliver 可按其契约分派本阶段。
- 只修改实现；只使用 design 基线已提交的共享代码底座。
  - 发现缺失时停止并提示 `$mdf design`，不得本路自行创建底座。
- 测试争议：在交接中记录争议的测试、断言与理由，以未决返回调用方，不改断言或配置绕过验证。
  - deliver 委托时由主 Agent 按其 confidence 策略裁定；独立调用询问用户。

### 自检与交接证据

实现前读取事实页，自检后自勾进度。

- 实现前按 design 的当前事实锚点读取对应事实页。
  - 已记载的当前行为以事实页为准，不从源码重新推断契约。
  - 本次要修改已记载行为时先读对应事实页再改实现，文档同步由主链 fact update 完成。
  - 发现事实页与实现冲突时停止并报告。
- 收尾前逐项对照 objectives 与 design 检查实现路径、接口和错误语义。
- 执行当前实现适用且可运行的自检，记录命令、退出状态、结果及对应验收项。
  - 不要求测试先完成或项目全绿。
  - 无法执行的自检逐项说明原因及留给 converge 的验证项。
- 自检发现本阶段可修复的实现问题时原地修复并重查。
  - 可修复指同一失败未满三轮且下一步修复动作明确；否则视为无法完成。
- ❌ 目标或设计不明、实现未完成时停止并报告，不勾选通过。
- 摘要须区分已验证结论与未验证项，不把后续验证项写成已通过。
- 成功后将 `objectives.md` 的 implement 项改为 `[x]` 并提交（并行多路规则同 write-tests）。
- ❌ 不以 `delivery record/check --stage implement` 为完成条件；可选 record 仅为并行辅助快照。
