# Archive

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check epoch                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 首次缺失 ────────→ 1 Check epoch
                 ├──── 询问后仍缺失 ────→ [停止]
                 ├──── 格式无效 ────────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Check entry                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Preview                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 预览成功 ────→ [展示预览并结束]
                 ├──── 预览失败 ────→ [停止]
                 │
                 ▼ 非预览
┌──────────────────────────────────┐
│ 4 Check group                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 5 Archive                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [保留现场，停止]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

完整读取 `references/common.md`、`references/repository-contract.md` 与 `references/object-contract.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check epoch | 约束 | 校验 RELEASE_EPOCH 为精确 MAJOR.MINOR | 有效 epoch | 2 | 首次缺询问回 1；仍缺或无效停 |
| 2 | Check entry | 脚本 | 在目标根运行 `doctor`，确认 ready | doctor 结果 | 3 | 停止 |
| 3 | Preview | 脚本 | 仅预览请求：确认 clean 并运行 dry-run | 预览结果或非预览跳过 | 预览结束；非预览 4 | 停止 |
| 4 | Check group | 脚本 | 用 `list` 列终态对象，核对 duplicate/canonical 完整组 | list 结果、archive group | 5 | 停止 |
| 5 | Archive | 脚本 | 确认 clean，归档、全量校验并复核提交 | 产物、零 finding、diff | 结束 | 保留现场，停止 |

## 术语与数据结构

### 版本与入口

<a id="s1"></a>

**版本**

要求精确 `MAJOR.MINOR` 的 `RELEASE_EPOCH`，拒绝 patch、预发布、 构建元数据和 `unreleased`。
首次缺失时询问用户并留在本步，不猜测当前 minor；询问后仍未提供或格式无效则停止。

验收：有效 epoch。

<a id="s2"></a>

**入口**

解析 `REPO_ROOT`、运行 `doctor --repo "$REPO_ROOT"`。

验收：`normal_workflows_allowed: true`。

### 预览与归档

<a id="s3"></a>

**预览**

- `archive` CLI（包括 dry-run）要求操作前 clean。
  - ❌ 预览不得为满足 clean 而提交改动。
- 仅在用户要求预览时运行 `archive --repo "$REPO_ROOT" --epoch "$RELEASE_EPOCH" --dry-run`。
  - 预览成功即展示结果并结束，不进入实际归档。
  - 未要求预览时跳过本步操作。
- 验收：稳定移动与 canonical 引用重写预览。
- 通过条件：预览结束。
- 异常与交接：非预览进入 4；停止。预览不构成确认或参数绑定。

<a id="s4"></a>

**分组**

- 运行以下命令取得候选：
  - `list --repo "$REPO_ROOT" --type proposal --status released --status rejected --status replaced`
  - `list --repo "$REPO_ROOT" --type bug --status closed --status rejected`
- 按输出的 `reject-reason` 与 `duplicate_of` 核对分组，不逐篇翻阅对象目录。
- released/rejected/replaced Proposal 可归档。
- 📌 Bug 的 duplicate 必须随 canonical 组成 archive group。
- 可选加速（见 `common.md`「Jev 可选加速」）：
  - 时机：分组后对争议 group；tool 可用时。
  - 调用：`noul`（终态齐全且 duplicate 随 canonical 是否可归档）。
  - 采信 yes 仅辅助核对清单；实际移动仍须步骤 5 与 CLI。
  - 未采信或 no 走主 Agent，不得单独移动。
- 验收：候选清单与 archive group 关系。
- 异常与交接：停止，不得单独移动。

<a id="s5"></a>

**归档**

- 非预览操作前按公共规则整理本次改动并确认 clean。
  - 范围不明或存在无关改动时澄清，不夹带提交。
- 仅非预览调用授权运行 `archive --repo "$REPO_ROOT" --epoch "$RELEASE_EPOCH"`。
  - 之后运行 `validate --repo "$REPO_ROOT" --level strict`。
- 验收：对象、`moves`、`rewrites` 数量与 validation。
- 异常与交接：
  - `duplicate_group_open` 时停止且不得单独移动。
  - 其他失败保留现场并报告 findings。
  - 成功后复核并提交本次归档改动。
