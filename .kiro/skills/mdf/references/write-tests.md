# Write Tests

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
│ 2 Cases                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 可执行测试已编写
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
| 1 | Check | 约束 | 按 roster 进入 qa/owner 并核对底座 | worktree、底座 | 2 | 缺底座提示 `$mdf design`；其他停止 |
| 2 | Cases | 约束 | 按设计编写测试，确认可执行并审查覆盖 | 可执行性、覆盖、named suite 已文档化 | 3 | 停止并报告 |
| 3 | Record | 约束 | 自勾 objectives 并提交本阶段产出 | 勾选、覆盖摘要、提交 | 结束 | 停止并报告 |

## 术语与数据结构

### 范围与前置条件

先运行 `delivery status --repo <owner 绝对路径>`。
角色分支合入 owner 前没有 delivery.json。
读取 `roster`，按下表确定编写位置。

| `roster.qa` | 编写位置 |
| --- | --- |
| `roster.qa == 0` | 在 owner 编写测试，不切角色树 |
| `roster.qa ≥ 1` | 读取 `worktrees.qa` 列表；缺对应树则停止 |

- 独立调用时列表仅一项则用该项的 `path` 与 `branch`；≥2 项时用会话当前所在的 qa worktree，
  不在任一 qa worktree 中则询问 index。
- deliver 只续办一路时用该路；对列表每一项分派独立 subagent，不把兄弟路径传入任务。
- 用 `git -C <该绝对路径>` 与该路径下的绝对文件路径操作；delivery CLI 的 `--repo` 也传该绝对路径。
- 角色树先运行下列命令合入 owner；已在该 worktree 时仍先合并。冲突保留现场。
  - `python3 "$MDF_ROOT/scripts/mdf.py" merge-no-ff --repo <该绝对路径> --commit <owner 完整分支名>`
- ❌ `roster.qa ≥ 1` 时不得在 feature 上编写或补写测试（指 owner，不是 kind）。

路径与会话根按调用方式处理（目标为该 qa 绝对路径与分支；index 1 形如
`qa/feature/<slug>`，不是 owner）：

- subagent（含 deliver 步骤 4）与非 Cursor 主 Agent：按 `common.md`「切换工作区」
  绝对路径绑定该 qa；禁止新建 worktree、禁止切到 owner、禁止要求用户切换；
  禁止 `move_agent_to_root`。
  - 用 `git -C`、`--repo` 与该路径下绝对文件路径；核对该路径 toplevel 与分支。
- 独立调用的 Cursor 主 Agent：按 `common.md`「切换工作区」`move_agent_to_root`
  进入该 qa。
- deliver 步骤 3 主 Agent 续办时禁止切会话与 `move_agent_to_root`，保持 owner；
  用 `git -C` 与绝对路径操作。
- 绑定或切换成功后横幅用该 qa 的 worktree 路径；相对上一处变化时打印切换三行。

再遵守：

- `qa_strategy` 为 `partition` 时只做 design 派给本 index 的切片，仍不看兄弟代码。
- roster.models 含 `write-tests` 时把该值写入本路任务，按口语描述现场解析（可多个模型）。
  - 没有则不提模型或 effort。
  - 不得写入其他 intent 的模型。
- 与 implement 互不前置，可并行。
- 独立调用不自动分派 Agent；deliver 可按其契约分派本阶段。
- 只使用 design 基线已提交的共享代码底座。
  - 发现类型、接口、stub 或测试设施缺失时停止，并提示 `$mdf design` 补底座，不得本路自行创建。
- 错误输入与可预见的错误行为表达为输入—期望输出测试用例。
  - 不要求针对具体实现进行错误注入，也不强制先产生红灯。

### 测试与交接证据

编写前读取事实页，按 suite 归类用例，确认可执行后自勾进度。

- 编写前按 design 的当前事实锚点读取对应事实页。
  - 已记载的当前行为以事实页为准，不从源码重新推断契约。
  - 项目级 kind、失败语义与 skip 以 `docs/system/testing/` 为准，不在 design 复述。

用例归类依据 design 与 `delivery-contract.md`「测试层级与分类」。据此把用例归入 quick、smoke 或
design policy `suites` 所列 named suite；归属写在代码里（marker、目录等）。

- design 所列 named suite 尚无文档时，新建独立的 `docs/system/testing/<suite>.md`。
  - 这属于本阶段授权。
- 收尾前核对每个声明的 named suite 都已文档化且有成员，并有独立文件和可解析的命令 frontmatter。
- ❌ 不得降低项目门槛；非 hermetic 的 test case 不进 quick，超预算的 test case 不进 quick 或 smoke。
- 新写的 test case 按依赖切分，同一 test case 内的 test 依赖一致，不写运行时 skip。
- implement 不得擅自改测试。

可执行性与全绿的边界：

- 测试须能编译或加载执行；环境或导入故障不是有效完成证据。
- 因尚未实现而产生的断言失败可以接受。
- 本阶段不要求项目全绿，也不得因断言失败拒绝完成。
- 全绿由 converge 负责，且相对所需 suite。
- 逐项审查 objectives 覆盖与断言。
- 首次按确认设计编写测试与配置属于本 intent 的授权；不得改变目标或降低项目门槛。
- 成功后将 `objectives.md` 的 write-tests 项改为 `[x]` 并提交。
  - 并行多路时由 converge 前 owner 统一勾，
    或各路在交接说明中声明本路完成、由 owner 勾选。
- ❌ 不以 `delivery record/check --stage write-tests` 为完成条件；
  可选 record 仅为并行辅助快照。
