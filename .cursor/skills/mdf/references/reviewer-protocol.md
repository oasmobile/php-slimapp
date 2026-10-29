# 共用 Review 协议

## 执行边界

本协议供本地 code-review 的独立审查与 CI 外部复核共同使用。

- 以最严苛的白盒测试专家视角审查实现代码和测试用例，主动挑战实现逻辑与测试的充分性。
- 以证据核实逻辑正确性与测试有效性，不因测试通过就认定实现正确。
- 严格只读，不修改文件，不运行 tests，不调用会落盘的 MDF CLI；通过回复返回报告。
- reviewer 可以读取和搜索项目文件、读取 Git 对象；权限由调用方落实。
- 交付 controller 在派发前准备 lint、测量、验证报告，全部独立审查返回前不修改审查对象。
- 独立 against 审查由当前 Agent 直接执行，不要求本地审查、交付材料或 roster，不勾 objectives。
- 下方 reviewers、owner、增量与 delivery 字段仅适用于交付模式；独立模式使用独立报告 schema。
- 本地完整流程及修复窗继续按 [code-review](code-review.md) 执行。

## 上下文与范围

本节规定 controller 交付给各 reviewer 的固定输入。

| 字段 | 用途 |
| --- | --- |
| source、delivery_base | 交付身份与固定起点；默认 release 为上一正式版本 |
| review_base、review_head | 本轮实际审查范围；增量复核包括上轮问题 |
| policy_ref、rules_sha256 | 固定 target commit 与实际加载的规则内容指纹 |
| merge_base、target_paths、target_diff | 两端共同祖先与 target 独有变化；用于合入影响分析 |
| context_sha256 | 本轮输入身份；每份报告必须一致 |
| roster、paths | 冻结人数、review strategy 与需覆盖路径 |
| artifacts、incomplete | 现有交付证据与缺项；缺项不能默认为通过 |

- 实现审查先与 sourceset 并集求交，再应用 module ignore；文档与交付材料独立按契约纳入。
- 独立 against 模式直接比较历史版本与当前工作区，配置与规则均来自当前 snapshot。
  - against 为完整基线 SHA，worktree_sha256 绑定当前文件内容；paths 与 diff 已过滤。
  - 读取当前文件完整内容前核对工作区未变化，变化后重建 context。
- 交付 CI 模式继续使用固定 source 配置和 target policy，保留 target 上下文与旧 findings。
- 同时读取必要上下文，不仅审 diff、标题或文件名。
- 审查正确性、验收覆盖、测试质量、code smell、架构合理性与非必要复杂度。
- MDF rule 与 project rule 原文均须传入；冲突时 project rule 优先。
- replicate 每人覆盖全部路径；partition 由 controller 切片，所有报告覆盖并集须完整。
- 单人覆盖全部范围；同一轮的审查者不共享彼此 findings。
- `.mdf/modules.yaml` 的 ignore、规模与拆分规则遵循固定策略和测量报告，不手工重复计数。
- 默认 release 不得因 child 已审而跳过上一正式版本以来的变化；独立 against 按指定历史版本与当前工作区范围。

## 独立报告

mode=against 使用 [独立报告 schema](../assets/templates/against-review-report.schema.json)，直接返回审查结果。

- 完整覆盖 paths，记录 against、worktree_sha256、rules_sha256 与 context_sha256。
- findings 仅列有静态证据支持的问题，包含 id、path、line、priority、trigger、impact、evidence。
- 审查完整且无 P0/P1 时可 pass；有阻断问题时 changes_requested；证据不足或未完成时 needs-review。
- 工具失败使用 error；changes_requested 必须有 finding；不因未运行 tests 自动降低优先级。
- incomplete 明确记录实际缺项；不将不存在的 MDF 交付材料列为缺项，不要求补齐 delivery。
- 不要求独立 reviewer 份数、owner 裁定或旧 finding 表；修复后重新捕获工作区，重新完整审查。

## Findings 与裁定

本节区分静态发现、owner 裁定与平台动作。

1. reviewer 返回 id、path、line、priority、trigger、impact、evidence。
2. CI owner 汇总去重，逐项说明 accepted、rejected 或 needs-review 的证据和理由。
3. 需要新增复现 test、修改实现或无法核实的项交回开发侧 code-review intent。
4. 交回开发侧时沿用原优先级；复现、降级与最终修复按原 intent，不伪造运行结果。

| decision | 含义 |
| --- | --- |
| pass | 全部审查完整，已完成裁定，无采纳的 P0/P1 阻断项 |
| changes_requested | 存在已核实采纳的问题，等待开发侧处理 |
| needs-review | 缺证据、待复现、覆盖未完或需要人工决定 |
| error | reviewer、工具或报告处理失败 |

- CI owner 不按票数裁定；未完成裁定或等待复现不得 approve/merge。
- priority 使用 0–3；P0/P1 为本轮自动批准的阻断项，其他采纳项可作为建议。
- 增量报告逐项复核旧 finding：resolved、reopened 或 not_applicable，并给证据。
- reopened 旧项由原 reviewer 在 findings 保留原 ID、完整证据与原级别；缺项或未裁定时只能 needs-review/error。
- findings 可交回开发侧；范围、规则与份数符合原 intent 才可复用独立报告。
- CI 报告保存 SHA；交付终稿继续无 SHA，不互相覆盖。
- 每轮报告保留固定 delivery_base；增量仅推进 review_base/head，首次 release 的后续轮也不能改变交付基线。

## 输出与执行器

本节规定报告传输和平台授权的边界。

- schema 见 [CI 报告 schema](../assets/templates/ci-review-report.schema.json)。
- 交付 controller 先执行 `review-context`，再独立启动冻结人数份 Codex/Cursor CLI。
- controller 落盘 reviewer 回复；CI owner 接收全部报告后汇总为 schema 指定的最终 JSON。
- Codex 使用 `codex exec`；Cursor 使用 `agent -p`。两者按项目配置落实只读权限。
- Cursor 的 JSON envelope 先提取 result；必须为完整 JSON，不猜测或修补损坏输出。
- controller 执行 `review-report-check`，并核对 checkout、Git diff 及实际 head 未越界变化。
- 格式通过只表示协议完整；平台动作还须核对当前 head、规则、测试与项目 policy。
- approve、request changes、merge、notify 由后续持有平台凭据的步骤执行。
- 完整接入见 [CI 接入](ci-review.md)。
