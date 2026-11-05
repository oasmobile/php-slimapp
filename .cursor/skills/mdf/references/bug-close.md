# bug close

二次验证已 `fixed` 的 Bug：只跑该 Bug 的复现用例，失败则像 converge 一样修到
通过，并仅审查这次修复的代码。通过后标为 `closed` 并写 `fixed_in`，不跑全局
验证，不替代 `$mdf code-review`。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 ├──── 空清单 ───────→ [结束]
                 │
                 ▼ 有待验收或重验的 Bug
┌──────────────────────────────────┐
│ 2 Verify                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 可修复实现问题 ──────→ 2 Verify
                 ├──── 需测试修改批准 ──────→ [取得用户确认后回 2]
                 ├──── 测试修改批准被拒 ────→ [停止并报告]
                 ├──── 缺可执行复现命令 ────→ [停止并报告]
                 ├──── 三轮无进展 ──────────→ [停止并报告]
                 ├──── 写入分支受限 ────────→ [停止并报告]
                 │
                 ▼ 复现用例通过
┌──────────────────────────────────┐
│ 3 Review                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 有可修问题 ────→ 2 Verify
                 ├──── 需用户决定 ────→ [停止并报告]
                 │
                 ▼ 审查无问题
┌──────────────────────────────────┐
│ 4 Record                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 无需补验且记录完成 ────→ [结束]
                 ├──── 交付委托且改了实现 ────→ [按调用方返回补验]
                 └──── 失败/缺失 ─────────────→ [停止并报告]
```

## 工作流（唯一执行契约）

读取 `references/common.md` 与 `references/object-contract.md`。
复现命令对照 `references/fix.md` 的红灯与回归证据规则。
CLI 使用 `python3 "$MDF_ROOT/scripts/mdf.py"`。
独立调用只推进当前 intent；close-out 内部委托时完成后返回调用方。
PR mode 由 pr 的材料准备委托，完成或补验交接返回 pr 步骤 2，不进入合并后 close-out。
不由 deliver 直接委托。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 脚本 | 核对 ready、版本与验收清单 | doctor、list、参数 | 有清单则 2；空清单则结束 | 停止并报告 |
| 2 | Verify | 约束 | 跑复现用例；失败则修并 smart（quick suite） | 命令、结果、smart | 3 | 可修或获批回 2；否则停 |
| 3 | Review | 约束 | 只审这次修复的代码并裁定 | 范围 diff、结论 | 4 | 有可修回 2；需决定则停 |
| 4 | Record | 脚本 | 先判断补验交接；否则写记录并关闭 | 记录、对象、提交 | 无补验则结束；有则按调用方返回补验 | 停止 |

## 术语与数据结构

### 范围与前置条件

- 解析 `REPO_ROOT` 并运行 `doctor`。验收：`normal_workflows_allowed: true`。
- 独立调用：`$mdf bug close <bug-id> --fixed-in <version>`；Bug ID 与版本必填。
- `--fixed-in` 只接受稳定 SemVer；release/hotfix 上须等于分支版本。
- feature/bugfix 上传入的版本是确定的交付目标，发版时核对实际包含该修复。
- 不切分支、不 start、不创建 worktree。写入落点按 `common.md`。
- 运行 `list --repo "$REPO_ROOT" --type bug --status fixed`；交付内部重验另列 closed。
  不逐篇翻阅 `docs/bugs/`。
- 待验证清单：
  - 独立调用命中唯一 `fixed` 对象，规则同 `$mdf fix`。`open`、`closed`、`rejected` 停止。
  - 交付委托时使用调用方传入的待收入 ID 列表与发布版本，不自行扩大清单。
  - closed 记录有效时由调用方复用，不进入本流程。
    调用方仅传记录缺失/过期的 closed Bug，fixed_in 须等于本版；执行 2–3 重验，
    4 只更新记录，不重复关闭。
    版本不符或重验失败则停止；不得以 closed 状态代替验收证据。
- 修复写入前（步骤 2、3）核对分支：master 或 detached HEAD 需修实现时停止交接。
  - develop 与其他非交付分支可按本次修复范围运行 smart；不要求交付材料。
  - 只读复现验证不受此限；不自动切分支或创建 worktree。
- 交付委托模式：本次步骤 2–3 修改实现、测试或验证配置时，提交修复与记录并报告「实现已变更」。
  保留 Bug 状态，不关闭对象；按下表交回父流程完成补验后再续办本步。

| 调用方 | 修改实现后的返回位置 | 补验后继续 |
| --- | --- | --- |
| local close-out | close-out 步骤 4，交接主链补验与增量审查 | close-out 步骤 7 |
| PR mode 的 pr | pr 步骤 2，按 PR 返工规则补审补测与 fact | pr 材料准备中的 Bug closures |

- ❌ 边界：
  - 只有复现验证与修复审查都通过，才写 `closed` 与 `fixed_in`。
  - 不跑 branch/named 验证；只在本步修改实现/测试/配置后运行下方 smart，不按分支 kind 选择 suite。
  - 可只读已有 `changes/unreleased/<slug>/verification-report.json`（须 `all_passed: true`）。

### 复现验证

对清单中每个 Bug，对照其「所需回归证据」确认复现用例通过。

- 取证：
  - 本轮改过实现、测试或验证配置时，不复用修改前的报告；点名执行复现用例。
  - 否则在 bugfix/hotfix/release 上，能证明报告覆盖当前实现时可读已绿的 verification-report.json：
    - 由本次执行记录确认报告之后未改相关实现/测试/配置；无法证明则点名执行。
    - results[].report.cases 仅含 test case 汇总，不含具体 test 清单。
    - 从 results[].log 读取 summary.json，用 cases[].tests[] 的 name/result
      精确匹配复现 test（结合 case 名消歧）；case/test 明确 passed 时才引用并不重跑。
    - 报告缺失、无法唯一匹配或未 passed 时，按 testing 文档点名执行；全绿不足以证明已覆盖。
  - 其他分支按 docs/system/testing/ 的命令模板点名执行；Bug 有可执行命令则按其执行。
- 只要求这些复现用例通过。
- 本步修改实现/测试/验证配置时，另对涉及 module 跑 smart（含 quick suite），须退出 0。
  - CLI：`verify --scope smart --repo "$REPO_ROOT"`。
  - 用 `--paths` / `--module` 圈定涉及 module。
  - 成功读 stdout 的 `result`：逐项 `log` 与 quick `report`。
  - 非零读 stderr 最后一行的 `details.results[]`（`passed` / `error`）。
  - 不把进度行当结果。
  - ❌ 不调用 `$mdf verify --scope branch` 冒充本步。
- 缺可执行复现命令时停止并报告，提示先 `$mdf fix` 补红灯，不在本步新造用例。
- 失败且可修实现时原地修复并重验。
  - 可修复指同一失败连续无进展未满三轮且下一步明确；否则视为无法完成。
  - 修改已有测试的断言、预期、fixture、跳过规则或验证门槛须用户明确批准；
    取得用户确认后回到本步重验，被拒则停止并报告。
  - 不设总轮数上限；同一失败连续三轮无进展则停止。
- 逐个处理；任一 Bug 未通过则停止，不宣称清单已验证。

### 修复代码审查

验证通过后，仅审查该 Bug 这次修复的代码。

- ❌ 不调用 `$mdf code-review`，不按上一正式发布或 start_commit 做整分支审查，不派 roster.reviewers。
- 修复提交：提交说明含完整 Bug ID，且改动 `docs/` 与 `changes/` 以外路径。
  - `$mdf fix` 与 release/hotfix 上的直接修复均须含 ID。
  - 只改对象或记录的提交不计入。
  - 列出：`git log --fixed-strings --grep=<完整 Bug ID> --format=%H HEAD -- . ':(exclude)docs' ':(exclude)changes'`。
  - 按修复提交逐个运行 `git show <commit> -- <范围路径>`；不把最早到最新的整段区间当作修复 diff。
  - 提交说明只定位候选；逐块确认属于该 Bug。merge 或混合提交须定位实际修复块，不把无关增量夹入。
  - 本 intent 已有未提交修复时，另审本轮工作区 diff；范围仅含非 `docs/`、非 `changes/` 修复与复现路径。
  - 范围为空或不唯一时停止询问，不改用整分支 diff。
- 读取必要上下文，不能只看提交标题。
- 主 Agent 裁定、修复实现；修复后回到步骤 2 重跑该 Bug 的复现用例，再审新 diff。
- 降低验收或改目标须用户确认。
- 审查结论写入本步记录，须含实际依据。
- 可选加速（见 `common.md`「Jev 可选加速」）：
  - 时机：复现已绿后、裁定前；tool 可用时。
  - 调用：`noul`（证据是否支持关闭结论）。
  - state：复现结果与审查 diff 摘要。
  - 采信后仍须写入依据；未采信走主 Agent。
  - ❌ 不让 Jev 代替步骤 4 的关闭写入。

### 记录

按 Bug 追加记录，落点按当前分支：

| 分支 | 落点 |
| --- | --- |
| `release/<semver>`、`hotfix/<semver>` | `delivery status` 返回的本次材料目录下 `bug-close.md` |
| `feature/*`、`bugfix/*`（带 Bug ID） | `changes/unreleased/<当前交付 slug>/bug-close.md`，slug 同 code-review 记录 |
| develop 或其他非交付分支 | 在 Bug 正文追加验收记录 |

- release/hotfix 先用 `delivery status` 定位材料；PR 候选已归版本目录时沿用该目录，不另建 unreleased 副本。
- 按 ID 在当前版本、相关 child 的 bug-close.md 与 Bug 正文定位已有记录；歧义则停。
  重验后按上表写当前分支记录，旧记录不当作本轮证据。
- 有实现/测试/配置修复时先提交修复，再以 git rev-parse HEAD 作为记录 HEAD。
  后续只提交验收记录与对象状态，避免本轮修复提交立即使记录过期。
- 字段：ID、复现命令与退出状态（或引用的报告路径与 test 名）、结果、审查路径范围、HEAD、结论。
- 记录须使调用方能判断「该 ID 在当前 HEAD 上复现用例已通过且审查完成」。
- 有效性：记录 HEAD 到当前 HEAD 只改记录文件自身、`docs/` 或 `changes/` 材料（无代码变化）时仍有效；
  其他改动或复现命令变化则过期，须重跑步骤 2–3。
- 先判断交付委托补验分支；本轮改了实现/测试/验证配置时提交修复与记录，保留 Bug
  当前状态并按调用方返回补验；本轮不调用关闭 CLI，不声称关闭完成。
- 否则 fixed Bug 调用下方 CLI；内部重验的 closed Bug 仅更新记录。
  再按 common.md 一并提交对象与记录，不夹带无关改动。
- 无补验交接且 fixed Bug 复现与审查通过后调用 Core CLI：
  `bug close <bug-id> --fixed-in <version> --repo "$REPO_ROOT"`。
  - Core 仅做确定性字段校验与写入，不执行复现或代码审查。
  - 写入 `status: closed`、`fixed_in: <version>`；保留 found_in，发版时再归一化。
  - 任一验证失败不得调用关闭 CLI。

验收：正常完成时，每个 Bug 复现与审查通过、已 closed、fixed_in 正确，记录与对象已提交。
补验交接时仅报告已提交的修改、待关闭/重验 ID 与外部补验要求，返回调用方，不宣称完成。
