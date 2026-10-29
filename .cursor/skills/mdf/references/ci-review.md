# 交付 CI 外部审查接入

## 决策树

```text
┌──────────────────────────────┐
│ 1 Configure                  │
└──────────────┬───────────────┘
               │
               ├──── 缺配置或权限 ────→ [报告缺项并停止]
               │
               ▼ 项目配置齐全
┌──────────────────────────────┐
│ 2 Route                      │
└──────────────┬───────────────┘
               │
               ├──── 事件或参数不明 ────→ [停止并报告]
               ├──── trunk push ────────→ 5 Audit
               │
               ▼ review
┌──────────────────────────────┐
│ 3 Review                     │
└──────────────┬───────────────┘
               │
               ├──── 执行或报告无效 ────→ [保留日志，报告 error]
               │
               ▼ 已校验报告
┌──────────────────────────────┐
│ 4 Publish                    │
└──────────────┬───────────────┘
               │
               ├──── 端点变化 ────→ 3 Review
               ├──── 发布失败 ────→ [保留报告，报告阻塞]
               └──── 发布成功 ────→ [返回实际平台结果]

步骤 5 仅由步骤 2 的 trunk push 分支进入。

┌──────────────────────────────┐
│ 5 Audit                      │
└──────────────┬───────────────┘
               │
               ├──── pass ──────────────→ [审计通过]
               └──── 非 pass 或失败 ────→ [报告阻塞，不撤销 push]
```

## 工作流（唯一执行契约）

本表供项目显式配置 CI 时使用；读取本页不授权安装 CI、发布评论、approve 或 merge。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Configure | 约束 | 核依赖、固定工具来源、只读权限与项目 policy | runner 配置、身份、固定 ref | 2 | 缺项报告并停止 |
| 2 | Route | 约束 | 按事件选择 review 或 trunk push 审计 | 事件、参数、固定 SHA | review 3；push 5 | 不明停止，不猜 SHA |
| 3 | Review | 脚本 | 调用 review.py；核 context、checkout 与 checked.json | 固定上下文、有效报告、完整日志 | 有效报告4 | error 保留日志并停止；无效不发布 |
| 4 | Publish | 脚本 | 交付报告按 policy 调用 publish.py | 已校验报告、当前端点、平台结果 | 返回实际结果 | 端点变化回3；其他阻塞停止 |
| 5 | Audit | 脚本 | 调用 audit-push 并核 result.verdict | 固定 before/after、平台证据、verdict | pass 返回 | 非 pass 或调用失败报告阻塞 |

## 术语与数据结构

### 项目与 MDF 的职责

本页说明如何在项目 CI 运行共用审查，不自动安装平台设施。

| MDF 提供 | 项目配置 |
| --- | --- |
| audit-push、review-context、review-report-check | 事件、runner、完整 fetch 与必需测试 |
| 共用 Review 协议和报告 schema | Codex/Cursor CLI、模型、登录凭据与只读权限 |
| GitHub/GitLab CI 和发布示例 | approve/merge policy、平台写身份、通知和 artifact |

- Python3、Git、MDF 为必需依赖；平台采集另需已登录的 gh/glab。
- LLM 工具执行发生在 runner；模型推理使用所选服务，不要求原生平台 reviewer。
- 工具从项目当前安装位置加载。
- 第一版支持 origin 同仓；平台权限、分支保护、必需检查与通知由项目负责。
- 项目提供 checkout 外已存在且可写的绝对 `CI_ARTIFACT_DIR`；context、audit 与运行日志均置于该目录。
  每次调用 Core 前设置 `MDF_LOG_DIR="$CI_ARTIFACT_DIR/mdf-logs"`，Python 使用 `-B`；不把输入、日志或 bytecode 写进被审 checkout。

### 固定上下文

交付模式从固定 Git 对象生成上下文。

```bash
MDF_LOG_DIR="$CI_ARTIFACT_DIR/mdf-logs" python3 -B "$MDF_ROOT/scripts/mdf.py" review-context \
  --repo "$REPO_ROOT" --source feature/example --head "$HEAD_SHA" \
  --policy-ref "$TARGET_SHA" > "$CI_ARTIFACT_DIR/context-output.json"
```

- CLI 返回 result；报告校验接受该 result 内容保存为 context.json，不接受整个 envelope。
- source 决定交付目录；release/hotfix 同时识别已归档版本目录。
- codex/backmerge/<version> 使用 annotated 发布 tag 和首次回合双亲定位固定 base/M，复用 M 中的交付证据与 roster。
- delivery_base 来自已提交的 delivery.json；release 来自 policy_ref 所指 manifest 的上一正式版本 tag。
- 首次 release 无上一版本时，传入用户确认的 --review-base；不猜测首次基线。
- 可传 --review-base 与 --previous-report 开增量轮；上轮 review_head 必须等于本轮左端点。
- review.py 同样接受这两个参数；CI 可用 MDF_REVIEW_BASE、MDF_PREVIOUS_REPORT 注入基线与已下载的报告路径。
- policy_ref 为本轮开始的目标 commit；project rule 与根 AGENTS 原文从该 commit 读取。
- review_head、roster、材料来自 source 的固定 commit，不依赖开发机 Git config。
- 缺交付身份或基线时命令失败；缺主链材料时 incomplete 非空，不得批准。

### CLI 执行与报告

本节是交付模式的可选 CI 执行器示例；backend 选择示例内部的宿主 CLI。

```bash
python3 -B "$MDF_ROOT/assets/ci/review.py" \
  --repo "$REPO_ROOT" --source feature/example --head "$HEAD_SHA" \
  --policy-ref "$TARGET_SHA" --backend codex --output-dir "$CI_ARTIFACT_DIR"
```

- 项目先运行 lint/tests，保存完整报告；CI checkout 固定在 review_head。
- controller 生成 context.json，按 roster 分别启动独立 reviewer，partition 时分配路径切片。
- CI owner 读取全部独立报告，按静态证据逐项裁定，需要复现或修复时交回开发侧。
- controller 校验最终报告，保存 checked.json；非 pass 退出非零，保留全部日志。

- backend 可选 codex 或 cursor；Cursor 使用 agent 的 ask print mode，Codex 使用 read-only exec。
- 输出目录须在 checkout 外；controller 检查每路执行前后 HEAD、status 和 tracked diff。
- 每路保存 stdout/stderr 和 JSON；不会从无效文本中猜测 JSON。
- report.json 使用 ci-review-report.schema.json。
- error.json 是执行失败，不等于有效 review 报告。
- 供外部执行器接入时，使用 [schema](../assets/templates/ci-review-report.schema.json) 和 [Review 协议](reviewer-protocol.md)。
- 外部执行器输出可用 `review-report-check --context-file context.json --report-file report.json` 校验。
- Cursor result envelope 会先解包；仍须通过完整字段、固定范围、规则、人数、覆盖及裁定检查。
- 报告校验只验契约，不推理结论，不授予平台 merge 权限。

### Push 审计

本节审计 develop/master 的完整新增第一父链，不撤销已经接受的 push。

```bash
MDF_LOG_DIR="$CI_ARTIFACT_DIR/mdf-logs" python3 -B "$MDF_ROOT/scripts/mdf.py" audit-push \
  --repo "$REPO_ROOT" --branch develop --before "$BEFORE_SHA" \
  --after "$AFTER_SHA" --collect-evidence > "$CI_ARTIFACT_DIR/audit.json"
```

- 不传 --collect-evidence 时离线运行；可通过 --evidence-file 传 controller 采集的平台事实。
- --collect-evidence 使用 before 的 provider、origin、平台合并记录及已 fetch 的 planning/master 历史。
- evidence 为 object：pull_requests 数组和 sources mapping；不得根据 commit message 手写伪造证明。
- pull_requests 每项含 id、url、source、target、head、state、merge_commit；state 需为 merged。
- sources 的 planning/master 为对应 origin ref 历史内的固定 SHA，缺失时不猜来源。
- PR mode 使用 before；即使 after 修改了 closeout mode，也按 before 审查本次 push。
  - trivial 路径使用当前 checkout 的项目定义，缺省为 MDF 默认值，见 [dev-pr](dev-pr.md)。
- 全零 before、缺对象、无法读取策略或平台故障时 needs-review；trunk 历史改写为 violation。
- verdict 为 pass、violation、needs-review；调用成功不等于通过，CI 须显式检查 result.verdict。

### 发布 review 与合并

本节的发布示例消费交付模式报告。

```bash
python3 -B "$MDF_ROOT/assets/ci/publish.py" \
  --repo "$REPO_ROOT" --provider github --number 123 \
  --context-file "$CI_ARTIFACT_DIR/context.json" \
  --report-file "$CI_ARTIFACT_DIR/report.json"
```

| 结果 | 默认动作 |
| --- | --- |
| pass | 发布总结；显式 --approve 才批准 |
| changes_requested | GitHub request changes；GitLab 发布 findings 并撤回该身份的 approval |
| needs-review / error | 报告缺项或失败，不批准、不合并 |

- 默认不 merge。项目核实必需检查后，显式传 --approve --merge --checks-passed 才请求平台合并。
- --checks-passed 是项目声明，不会跳过平台审批、冲突或其他必需检查。
- 发布前重新 fetch，核 source/target/head、目标 policy_ref 与规则；目标变化须重新审查和验证。
- 后续发布 job 在审查非 pass 时也应读取 artifact；只发布已校验的 report，error 仅通知。
- merge 请求携带源 SHA；GitHub 使用 merge 方法，GitLab 禁 squash 并等待平台 auto_merge 条件。
- GitHub 作者不能自批，项目应配置符合平台资格的独立审批身份。
- GitLab findings note 本身不保证阻断；项目必须把 review CI 配成所需检查。
- notify、自动关闭 PR/MR、部署不在示例中启用；项目自行配置。
- 模板见 [GitHub Actions](../assets/ci/github-actions.yml) 与 [GitLab CI](../assets/ci/gitlab-ci.yml)。
