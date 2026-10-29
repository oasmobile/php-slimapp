# Design

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Clarify                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Baseline                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 缺确认 ─────────────────→ 2 Clarify
                 ├──── policy/suite 可修正 ────→ 3 Baseline
                 ├──── 通过 ───────────────────→ [结束]
                 └──── 其他失败/缺失 ──────────→ [停止并报告]
```

## 工作流（唯一执行契约）

读取 `references/delivery-contract.md`、`references/common.md`；
涉及 PRP 时读取 `references/object-contract.md`。
读取 [项目阶段 rule 契约](project-rules.md)，本阶段按 merge 后规则执行，冲突时 project 优先。

- CLI 使用 `python3 "$MDF_ROOT/scripts/mdf.py" delivery <action> --repo "$REPO_ROOT"`。
- 独立调用只推进当前 intent；deliver 内部委托时完成后返回调用方，由其选择下一阶段。
- 步骤 2 读取并内部执行 `references/clarify.md`；确认的是方案稿，底座文件由步骤 3 写入。
- 确认后，本 intent 启动恰好 1 个 owner subagent 执行步骤 3。
  - 该 subagent 按 `assets/templates/design.md` 写入设计、共用代码底座并自勾 objectives。
  - 独立调用与 deliver 委托都如此；不计入 roster，不可配人数。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 约束 | 确认 start、kind 并加载核对项目 rule | start、kind、objectives、rule 原文与指纹 | 2 | 停止并报告 |
| 2 | Clarify | 约束 | 委托 clarify，确认设计、测试策略及双方共用代码底座 | 用户确认的设计与底座方案 | 3 | 停止并报告 |
| 3 | Baseline | Subagent | 写设计、底座并提交基线 | design、底座、勾选、提交 | 结束 | 缺确认回 2；可修正则 3；否则停 |

## 术语与数据结构

### 项目 rule 的阶段接入

步骤 1 完成 start 与 kind 检查后，以 `--stage design` 加载项目 rule，成功后才进入步骤 2。

- 步骤 2 的 Clarify 使用 merge 后规则，确认稿包含 rule 来源与内容指纹。
- 步骤 3 分派前再核对规则，向 owner subagent 完整传递适用 MDF rule 与 project rule 原文。
- subagent 将来源与内容指纹写入 design.md；主 Agent 验收前重新加载核对。
- 规则变更按项目阶段 rule 契约停止；确认后回步骤 2，不沿用旧方案或旧 Baseline 通过结论。

### 范围与前置条件

本节规定 design.md 的内容与结束前必须落地的共享代码底座。

- 在 design.md 中明确目标、非目标、接口、错误语义、
  验收到 quick、smoke 与本交付 named suite 的映射。
- 测试仅对 objectives 负责。
- 项目级 kind、失败语义与各 suite 以 `docs/system/testing/` 为准；
  本页只写本次交付到 suite 的映射。
  - 必须声明涉及功能块的 named suite 名称，供 write-tests 把用例归入对应 suite。
- 设计前从 `docs/README.md` 定位并读取相关当前事实页，
  在 design.md 列出当前事实锚点（页面路径）。
  - 没有对应事实页时写明本次将新增哪些页面。
  - 不得把计划写进既有事实页，事实更新由主链 fact update（verify branch 之后）完成。
- 提交前 Agent 自检 objectives.md 与 design.md 的本地链接目标存在。
- 步骤 1 按 kind 核对依据：feature 为 PRP；bugfix 为 Bug；release 为版本与 objectives；
  hotfix 只核对版本，热修复范围在步骤 2 确认。
- 四种 kind 的 objectives 均由 start 写入，步骤 1 缺失即停止并报告。
- `needs_design: no` 或人工 feature 不进入本 intent，不添加 design 清单项。
- design 已勾或 design.md 已存在时（如 release/hotfix 经 target 记入新 Bug），步骤 2 确认修订。
  - 步骤 3 原地修订 objectives 与 design 并重新勾选/提交。
  - deliver 委托按其 confidence 策略裁定。

结束前必须把 write-tests 与 implement 后续都会依赖的共享代码底座写入仓库，
使两路从同一提交继续：

- 底座包括类型、接口、错误语义、明确未实现的 stub 和最小测试设施。
- ❌ 不得各自再写一份底座。
- 纯文档改动不制造代码；底座未就绪不得勾选 design 完成。

### Baseline 分派

当前 Agent 执行步骤 1–2 与交接核验，不得代写 design.md、底座或勾选 design。
无法提供 subagent 时停止，不降级代做。已有 Baseline 执行者先等待，不对同一
owner 另开第二个。

分派前：

- 调用可带 `--qa-strategy`、`--dev-strategy`、`--review-strategy`；
  以及 `--write-tests-model`、`--implement-model`、`--code-review-model`。
  - 若与已冻结值不同，启动步骤 3 前运行 `delivery roster` 写入。
  - design 已完成后不能改 qa/dev strategy（看 objectives 勾选）。
- 分派前与结束后运行
  `worktree-check --repo <owner绝对路径> --owner <owner绝对路径> --role owner`。
- 任务写入 MDF_ROOT、owner 绝对路径与分支、Git common dir，
  以及步骤 2 已确认的设计与底座方案原文。
  - hotfix 另写入已确认的热修复范围。
- subagent 按 `common.md`「切换工作区」绝对路径绑定 owner；禁止新建 worktree、
  禁止要求用户切换；禁止 `move_agent_to_root`。
  - 绑定成功后横幅用 owner 的 worktree 路径；相对上一处变化时打印切换三行。

执行约束：

- 不得要求重新 clarify，不得把未确认内容当作已确认。
- 缺确认则停止该 subagent 并回步骤 2，不在 subagent 内 grilling。
- policy/suite 可修正时由该 subagent 内部留在步骤 3。
- deliver 的 confidence 策略适用于步骤 2 与步骤 3 的新 decision；已确认的共同理解直接复用。
- subagent 只写 design.md、policy、共用代码底座、既有 objectives 的本阶段勾选、可选快照与提交；
  不代 start 补建缺失的 objectives。

结束后当前 Agent 核对 objectives 的 design 项已勾、底座已进同一基线提交；
不以 `delivery check --stage design` 为完成条件。

### 设计 policy 与基线

在 `changes/unreleased/<slug>/design-policy.json` 写入 policy JSON。
必须同时给出 `protected_paths` 与 `suites`；与设计、底座一起提交，不作为进度账本。

| 返回 | 条件 |
| --- | --- |
| `invalid_policy` | 字段不符 |
| `invalid_delivery_suite` | suite 名无效或占用固定入口/其他保留名称（含 coverage） |

两者均停止并修正 policy 后重试。

- `protected_paths` 列全项目实际的测试、fixture、快照、测试发现、覆盖率和告警配置路径，
  包括 named suite。
  - 必须列入 `.mdf/modules.yaml`；命令/预算进入 fingerprint 不代替 roster-join 的审批保护。
    roster-join 按 protected_paths 保护测试配置，不假定 Core 自动加入全部验证文件。
  - 多 module 列出各 `<module>/tests/` 及各 module 的测试配置，不要只抄仓库根 `tests/`。
- `suites` 列出本交付改动涉及的每个功能块的 named suite，按功能块而非本次 feature 命名。
  - 已在 `docs/system/testing/` 文档化，或仅在出现新功能块时写明由 write-tests 新增其文档。

形成基线：

1. 可选：运行 `delivery record --stage design --policy-file <文件> --summary <摘要>`
   写入 **配置快照**（非进度 gate）。
2. 将 `objectives.md` 的 design 项改为 `[x]`。
3. 提交 objectives.md、design.md、delivery.json、design-policy.json 与共享代码底座。
   可选快照一起提交，形成同一基线。

底座未写入该基线则不得结束。角色 worktree 已由 start 建立，本步不创建。

- qa 或 dev 为 `partition` 时，design.md 必须写明各 index 的切片（做什么、不做什么）；
  各路仍互不看代码。
- review 的 `partition` 可在本步预写切片计划，code-review 仍可覆盖。
