# pre-gitflow-finish

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check context                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 已执行或未配置 ────→ 5 Report
                 ├──── 状态仍不明 ────────→ [交接未决并停止]
                 ├──── 前置不符 ──────────→ [保留现场并停止]
                 │
                 ▼ 已配置且未执行
┌──────────────────────────────────┐
│ 2 Run hook                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 现场检查失败 ────→ [保留现场并停止]
                 │
                 ▼ 执行已返回，含 hook 失败
┌──────────────────────────────────┐
│ 3 Check changes                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 现场无法核验 ────→ [保留现场并停止]
                 │
                 ▼ 已核实际改动
┌──────────────────────────────────┐
│ 4 Recheck                        │
└────────────────┬─────────────────┘
                 │
                 ├──── 需要补审补测 ──────→ [交接主链并保留 hook 已执行状态]
                 ├──── 复核或提交失败 ────→ [保留现场并停止]
                 │
                 ▼ 无改动或仅文档已提交
┌──────────────────────────────────┐
│ 5 Report                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 缺必要结果 ────→ [报告未完成]
                 └──── 证据完整 ──────→ [返回主链]
```

## 工作流（唯一执行契约）

先读取 [配置接口](hooks/pre-gitflow-finish.md)，适用 common 的日志条款；不提供独立 intent。
deliver 委托时先核外层 fact 的 until，再承办本表；decision 继承其 confidence 策略。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check context | 约束 | 核前置与执行状态 | 账本、配置、证据 | 已执行/无配置5；未执行2 | 未决交接；前置不符停 |
| 2 | Run hook | 脚本 | 运行 CLI；pending 时执行 rule | before_head、hook、日志 | 成败均 3 | 现场检查失败停止 |
| 3 | Check changes | 脚本 | 核实际 diff，rule 后用 --after | changed_paths、needs_recheck | 4 | 无法核验则停止 |
| 4 | Recheck | 约束 | 按 diff 提交或退勾交接 | diff、提交、返工项 | 无/仅文档5；其他交接主链 | 保留现场并报告 |
| 5 | Report | 约束 | 汇报执行状态与后续位置 | 日志、结果、后续项 | 返回主链 | 缺必要结果报告未完成 |

## 术语与数据结构

### 触发与续办

本节确定触发位置与一次执行的证据。

- 普通交付：code-review → verify branch → 本 hook → fact audit（必要时 fact update）→ close-out。
- 人工 feature：code-review → verify smoke → 本 hook → fact update → close-out。
- adhoc：code-review → verify smart → 本 hook → fact audit/update → close-out。
- 五种 kind 共用；在 owner 上执行，不在 qa/dev 或最终 `finish-gitflow` 内执行。
- 无账本 adhoc 以实际审查、验证报告替代本页勾选前置，不读写 objectives 或依赖 roster。
  - 非文档改动返回 adhoc-change 步骤 3，由 1 人增量补审；普通 source 补 smart，dev-pr source 补 named smoke。
  - 补验通过才进入 fact；已执行的 hook 不重跑。
- deliver、next 或用户手动推进交付时，由当前 Agent 在进入 fact 阶段前承办。
  - 独立文档维护、独立 fact audit、migrate 不触发；fact update 内部 Audit 不重复触发。
  - 主链调用方须先执行本节，再进入 fact intent；fact intent 的只读、写入边界保持适用。
- 每次交付只执行一次；续办从会话上下文、CLI 日志或已有执行证据确认是否执行。
  - 已执行（含失败）则不重跑，继续尚未勾选的补审、验证或 fact。
  - 步骤 1 的已执行返回只交接未完成项；未配置时交接 fact，不跳过既有返工。
  - 执行中断、状态不明时读 CLI 日志；无法确定是否已执行时停止询问，不自动重试。
  - 不要求新建执行记录文档，不以缺少该文档阻断交付；不新增 objectives 项或统一 workflow 状态文件。

### 执行与实际改动

1. 确认审查及验证已勾；adhoc 为 verify smart，其余为 branch；提交后要求 owner clean、无未结束 merge。
2. 未配置时直接进入 fact；已配置且未执行时运行：

   ```bash
   python3 "$MDF_ROOT/scripts/mdf.py" pre-gitflow-finish --repo "$REPO_ROOT"
   ```

3. 读取 JSON 的 `before_head`、`hook`、`changed_paths`、`needs_recheck`。
   - command 的 cwd 为 owner；环境变量为 `MDF_WORKTREE`、`MDF_BRANCH`、`MDF_BEFORE_HEAD`。
   - `hook.status: pending` 表示 rule：Agent 按 `hook.cwd`、`path` 读取并执行规则。
   - rule 执行前后说明 hook 名、path、cwd、结果或失败原因，按通用日志契约记录完整证据。
   - rule 执行后用原 `before_head` 检查实际改动；本调用不再执行 hook：

     ```bash
     python3 "$MDF_ROOT/scripts/mdf.py" pre-gitflow-finish \
       --repo "$REPO_ROOT" --after <before_head>
     ```

4. 无论 hook 成功或失败，都按实际改动处理：

   | 改动 | 后续处理 |
   | --- | --- |
   | 无改动 | 直接进入 fact |
   | 仅文档 | 复核并提交实际文档改动，直接进入 fact |
   | 其他改动 | 退勾 code-review、验证及 fact；adhoc 补 smart，人工补 smoke，其余补 branch |

   - 文档路径为根目录、`docs/` 或 `changes/` 内的普通 `.md` 文件；不能有执行权限或符号链接。
   - 覆盖已提交、staged、未暂存、新增、删除和 rename 两端；其他路径保守要求补审补测。
   - Agent 另核内容确属文档；混入实现、测试或验证配置时同样按其他改动处理。
   - 失败留下的部分改动同样核对；❌ 不因失败忽略 diff，也不回滚、自动重试。
   - 本 hook 不得切换分支或改写既有历史；现场或改动无法核对时保留现场并停止。
5. Agent 汇报执行结果、原 `before_head`、路径清单、补审补测要求及 CLI 日志路径。
   - rule 按通用日志契约保留执行证据；无需另写 Markdown 执行记录。
   - 有 hook 改动或 objectives 退勾时，复核后提交实际改动；无改动不制造提交。
   - 非文档改动按 code-review 的增量新一轮补审。左端点为原 `before_head`，人数用冻结 roster。
   - 补审后 adhoc 重跑 verify smart，人工重跑 verify smoke，其余重跑 verify branch，通过后进入 fact。
   - 独立推进交付时依同一顺序承办；next 可先交接补审，由后续调用完成补测与 fact。

### 失败与日志

- command 执行前后说明和完整 stdout/stderr 进入 CLI stderr 与运行日志。
- hook 非零退出、缺文件、无执行权限或 rule 执行失败仅汇报，可继续按实际改动推进。
- hook 失败不代表补审、补测或 fact 通过；这些步骤仍遵守原验收与停止规则。
- CLI 的仓库、clean、分支或改动检查失败属于现场无法核验，停止并报告，不视为 hook 执行失败。
