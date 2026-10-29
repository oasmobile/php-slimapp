# 当前工作区对比审阅

`$mdf fact audit --against <commit>`：对当前 worktree 相对这个 commit 做 fact audit。
commit 可以是 branch start、last release，或调用方选定的任意 commit。
Codex 与 Cursor 使用同一 intent，由执行该 intent 的 Agent 加载 Skill、运行命令、读取仓库并写出报告。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 参数或配置无效 ────→ [报告 error 并停止]
                 │
                 ▼ 参数与路径已确认
┌──────────────────────────────────┐
│ 2 Context                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 命令失败或输出缺失 ────→ [读日志，报告 error 并停止]
                 │
                 ▼ 有效 context
┌──────────────────────────────────┐
│ 3 Facts                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 未完成或证据缺失 ────→ 5 Report
                 │
                 ▼ 事实复核完成，可有 findings
┌──────────────────────────────────┐
│ 4 Coverage                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 未完成或证据缺失 ────→ 5 Report
                 │
                 ▼ 覆盖与 warnings 已处置
┌──────────────────────────────────┐
│ 5 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 复核命令失败 ──────────→ [报告 error 并停止]
                 ├──── context 已变化 ────────→ 2 Context
                 ├──── 格式不符且可修 ────────→ 5 Report
                 ├──── 格式无法修正 ──────────→ [报告 error 并停止]
                 └──── 指纹一致且报告有效 ────→ [返回调用方]
```

## 工作流（唯一执行契约）

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve | 约束 | 核 Git 根、参数、当前配置与仓外产物位置 | 根、参数、配置、日志目录 | 2 | 报 error 并停止 |
| 2 | Context | 脚本 | 调用 fact-audit --against，保存 result | against 完整 SHA、指纹与范围 | 3 | 读日志，报 error 并停止 |
| 3 | Facts | 约束 | 复核当前完整事实页、evidence 与结构 | 逐页 findings | 4 | 记 incomplete，转5 |
| 4 | Coverage | 约束 | 反查覆盖并复核删除与 rename | 覆盖与 warnings | 5 | 记 incomplete，转5 |
| 5 | Report | 约束 | 复核 context 未变，生成并校验 JSON | 两次指纹、校验结果 | 有效则返回 | 变化回2；格式可修留5；其余报 error |

## 术语与数据结构

### 输入与快照

CLI 前缀为 `python3 -B "$MDF_ROOT/scripts/mdf.py"`；先将 `MDF_LOG_DIR` 指向 checkout 外。

```bash
python3 -B "$MDF_ROOT/scripts/mdf.py" fact-audit --repo "$REPO_ROOT" --against <commit>
python3 -B "$MDF_ROOT/scripts/mdf.py" fact-audit-report-check \
  --context-file /outside/context.json --report-file /outside/report.json
```

- against 不与 scope、base、路径或交付参数混用；无需 ready 或交付材料。
- 直接比较指定版本，不计算 merge-base，不要求 against 是 HEAD 的祖先。
- 当前状态包含已提交、staged、unstaged 与未被 Git ignore 的 untracked 普通文件。
- 同一文件 staged 与 unstaged 不同时，以当前磁盘内容为准；已跟踪文件不因 Git ignore 排除。
- 只读原仓库，不 checkout、commit 或修改 index、refs、objects；不运行项目 tests、hooks 或 filters。
- snapshot 位于仓外，退出时清理；symlink、submodule 与不安全路径明确报错。
- 继承原仓库 object format 与 shallow 边界，不自动 fetch；against 必须在本地可解析。

### 规则与范围

- MDF 通用协议来自当前安装位置；项目 rules、manifest、AGENTS 与 modules 来自当前工作区 snapshot。
- 实现范围为 `against → 当前工作区` 变更与当前 sourceset 并集的交集，再应用当前 module ignore。
- 未归属实现不进入 paths、diff、implementation_paths 或覆盖检查。
- 重叠归属须所有 owner 均忽略才排除；ignore 空匹配用基线与当前文件清单并集校验。
- paths 与 diff 同步过滤；文档与交付材料按各自契约独立纳入，不要求归属 module。
- document_paths 包含变化事实页，以及基线或当前 evidence 引用有效实现变更的事实页。
- 双侧映射覆盖目录 evidence、generated.source 与 generated.generator。
- 删除与 rename 的新旧路径分别判定；删除文件从 against 读取，不丢弃基线事实映射。
- 步骤 3–4 仅读取 [fact audit 的双向复核标准](fact-audit.md#s3) 至 warnings 条款，执行事实、覆盖与加载质量检查。
  - 不进入其默认 scope、ready 前置或七步主流程，不重复执行 strict validation。
- 步骤 3 还须审阅 paths 中的项目文档与交付材料结构，不能因它们不在 document_paths 就跳过。
- 当前事实页审完整陈述，不仅看 Markdown diff；新增行为须反查缺失文档。
- audit 保留当前 snapshot 的全量契约 validation 和范围结构检查，不把既有问题冒充本次引入。
- CLI 只提供确定性 context，成功不表示完成语义审阅。

### 快照身份与报告

最终 report 使用 [JSON schema](../assets/templates/against-fact-audit-report.schema.json)。
CLI envelope 的 result 才是 context；下表字段按所属对象读取或生成。

| 对象 | 字段 | 含义 |
| --- | --- | --- |
| context → report 原样复制 | schema_version / mode / operation | 固定为 3 / against / fact-audit |
| context → report 原样复制 | against | 实际比较基线的完整 SHA |
| context → report 原样复制 | worktree_sha256 | 本轮工作区文件路径、mode 与内容的指纹 |
| context → report 原样复制 | rules_sha256 / context_sha256 | 已捕获规则与完整 context 的指纹 |
| report 按实际完成范围填写 | paths / implementation_paths / document_paths | 已完成复核的范围，不超出 context |
| 仅 context | ignored | context 中有效 module ignore 排除的变更路径与理由 |
| 仅 context | base_mappings / worktree_mappings | context 中基线与当前的事实映射 |
| report | findings | 静态证据支持的问题，包含位置、触发条件、影响和 P0–P3 |
| report | warnings | CLI warning 的逐条裁定与证据 |
| report | incomplete | 未完成、证据缺失或工具失败的具体原因 |
| report | decision | pass / changes_requested / needs-review / error |

- 步骤 5 先用 context.against 的完整 SHA 重跑同一 fact-audit --against 命令，核对 context_sha256。
  - 一致才生成报告；变化则用新 context 回2，再完成步骤 3–4，不复用旧通过结论，不重新解析原符号 ref。
  - 复核命令失败或无有效 context 时，报告 error 与日志位置；不伪造 schema 必需字段。
- 按上方命令运行 fact-audit-report-check：退出 0 且 result.valid 为 true 才返回 report 的 decision。
  - 格式可修则留5，无法修正则报告 error；校验成功不等于语义 pass。
- 不把仅 context 的 ignored、mappings 或 audit 字段复制进最终 report。
- 审阅期间以捕获的规则为准；代码、文档或规则变化均需重新核对 snapshot 身份。
- 完整覆盖所有三类范围、处置全部 warnings，且无 finding/incomplete 才能 pass。
- warning disposition 为 accepted、finding 或 needs-review；accepted 须附证据与理由。
- audit.findings 不能被空语义 findings 掩盖；未完成只能 needs-review/error。
- changes_requested 要求复核完整且存在 finding；P0–P3 不豁免事实错误。
- 报告由会话返回，调用方保存到 checkout 外；不直接 approve、merge 或发消息。
- report-check 只验证结构、覆盖与指纹一致性，不证明语义判断真实。
