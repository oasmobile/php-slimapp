---
name: mdf
description: >-
  管理 Git 仓库的版本化文档与交付流程：项目起步、初始化、已有项目迁移、规划、分诊、
  CodeWiki、随手记录、审计、收口、归档、帮助、自升级与压力测试。
disable-model-invocation: true
---

# Mars Development Flow

调用示例写作 `$mdf <intent>`；Cursor 使用 `/mdf`，Codex 使用 `$mdf`。
裸 `$mdf` 与 `$mdf help` 显示帮助目录。

横幅只按 `references/common.md` 的 `s-banner` 条款计算与输出，所有 intent（含 help/clarify/upgrade）均适用。
仅读取横幅条款，不执行 common 的其他规则或重新进入业务 workflow。

## 选择树

```text
┌──────────────────────────────────┐
│ 1 Accept call                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 裸调用、未知 intent ────────────→ [帮助并结束]
                 ├──── 已知 intent 带未知 -- token ────→ [停止询问]
                 │
                 ▼ 已确定 intent
┌──────────────────────────────────┐
│ 2 Check CLI                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Dispatch                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 边界不明 ──────────────────────────────────────────→ 3 Dispatch
                 ├──── 材料缺失 ──────────────────────────────────────────→ [停止并报告]
                 │
                 ├──── bootstrap ─────────────────────────────────────────→ references/bootstrap.md
                 ├──── init migrate / migrate ────────────────────────────→ references/migrate.md
                 ├──── init ──────────────────────────────────────────────→ references/init.md
                 ├──── intake ────────────────────────────────────────────→ references/intake.md
                 ├──── tree [--depth N] ──────────────────────────────────→ references/tree.md
                 ├──── prp tree ──────────────────────────────────────────→ references/tree.md
                 ├──── next? / next？ ────────────────────────────────────→ references/tree.md
                 ├──── next [--depth N] ──────────────────────────────────→ references/next.md
                 ├──── deliver [<target>] [--until <intent>] [--yolo] ────→ references/deliver.md
                 ├──── start ─────────────────────────────────────────────→ references/start.md
                 ├──── adhoc [<工作描述>] ────────────────────────────────→ references/adhoc.md
                 ├──── design ────────────────────────────────────────────→ references/design.md
                 ├──── write-tests ───────────────────────────────────────→ references/write-tests.md
                 ├──── implement ─────────────────────────────────────────→ references/implement.md
                 ├──── converge ──────────────────────────────────────────→ references/converge.md
                 ├──── lint ──────────────────────────────────────────────→ references/lint.md
                 ├──── fix <bug-id> [--yolo] ─────────────────────────────→ references/fix.md
                 ├──── bug close <bug-id> --fixed-in <version> ───────────→ references/bug-close.md
                 ├──── code-review ───────────────────────────────────────→ references/code-review.md
                 ├──── verify ────────────────────────────────────────────→ references/verify.md
                 ├──── fact update ───────────────────────────────────────→ references/fact-update.md
                 ├──── fact audit ────────────────────────────────────────→ references/fact-audit.md
                 ├──── prp split ─────────────────────────────────────────→ references/prp-split.md
                 ├──── pr ────────────────────────────────────────────────→ references/pr.md
                 ├──── close-out ─────────────────────────────────────────→ references/close-out.md
                 ├──── squash [--dry-run] ────────────────────────────────→ references/squash.md
                 ├──── prettify ──────────────────────────────────────────→ references/prettify.md
                 ├──── clarify <议题> ────────────────────────────────────→ references/clarify.md
                 ├──── bug create ────────────────────────────────────────→ references/bug-create.md
                 ├──── prp create ────────────────────────────────────────→ references/prp-create.md
                 ├──── prp review ────────────────────────────────────────→ references/prp-review.md
                 ├──── archive ───────────────────────────────────────────→ references/archive.md
                 ├──── codewiki generate ─────────────────────────────────→ references/codewiki-generate.md
                 ├──── codewiki update ───────────────────────────────────→ references/codewiki-update.md
                 ├──── jot / jot promote ─────────────────────────────────→ references/jot.md
                 ├──── help / help <intent> ──────────────────────────────→ references/help.md
                 ├──── upgrade ───────────────────────────────────────────→ references/upgrade.md
                 ├──── to <target> ───────────────────────────────────────→ references/to.md
                 ├──── dev-pr [<slug>] ───────────────────────────────────→ references/dev-pr.md
                 ├──── sync ──────────────────────────────────────────────→ references/sync.md
                 └──── integrate ─────────────────────────────────────────→ references/integrate.md
```

## 工作流（唯一执行契约）

入口与各 intent 只按编号工作流执行；图示仅用于路由。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Accept call | 约束 | 解析用户指定的 intent | 选择树所列 intent | 2 | 裸或未知则帮助；带未知 -- 则停止询问 |
| 2 | Check CLI | 脚本 | 定位 MDF_ROOT，运行 `info` 并核对版本 | CLI 结果、三个版本为 3 | 3 | 停止 |
| 3 | Dispatch | 约束 | 先核目标根再按选择树执行 | 目标根或豁免、流程结果 | 按选择树返回 | 不明回 3；缺材料停止并报告 |

## 术语与数据结构

### 文档结构与写作规则

新建或改写文档时，读取本 Skill 目录下的 [文档结构与写作规则](references/doc-structure.md)，
按规则执行并人工复核。仅查阅规则不触发 MDF workflow，也不要求运行 CLI。
规则文件缺失或无法读取时，报告实际路径并停止文档写入。

### 用户确认

所有 intent 按本节理解用户确认，包括内部委托、续办与 upgrade。

- 将待确认事项写成可用 yes 回答的问题，先展示具体操作、范围与推荐方案。
  - yes 默认表示同意当前展示的完整方案；多个互斥选项先明确推荐项及 yes 的含义。
  - 例如：「是否结束初始化并启用正常工作流？」用户回答 yes 即可继续。
- 按上下文识别肯定答复，如 yes、确认、可以、继续、按这个做；示例不是词语白名单。
  不要求用户复述操作名称、固定短语或重新发送命令。
- 同一操作与范围的已有有效授权在续办、重试或恢复时继续适用，不重复索要确认。
- 仅在答复指向不明、存在未决选择或操作范围实质变化时，说明具体歧义并补问。
  用户附带条件或修改方案时，先吸收其要求，再判断授权是否充分。
- 沉默、未回答或拒绝不算同意；确认不代替验证，也不授权其他独立操作。

### 调用与工具

认可宿主的手动 Skill invocation，无需消息正文包含 `$mdf`。

- 按用户指定的 intent 路由；未指定或未知 intent 按 help 执行。
- 同一任务的澄清、确认与续办沿用已确认的 intent 与范围，无需重复命令。
- 已知 intent 带未知 `--` token 时停止询问。

- `next [--depth N]` 与 `tree [--depth N]` 的深度可省略。
  - `$mdf tree`、`$mdf prp tree`、`$mdf next?` 与 `$mdf next？` 执行 `references/tree.md`，
    不得当未知调用送 help。
  - `$mdf next` 无问号时执行 `references/next.md`。
- `$mdf deliver [<target>] [--until <intent>] [--yolo]` 仍是 deliver，不是独立 intent。
  - option 可在 target 前或后；`--stop-at` 是 `--until` 的别名，值不算 target。
  - 默认无截止点，直到 close-out 完成；非 yolo 在 pr、close-out 前分别取得用户确认。
  - 其他 decision 默认自动裁定，confidence < 0.8 请求用户确认；显式 until 不执行截止 intent。
  - `--yolo` 跳过两个入口确认、无 confidence 限制；显式 until 仍生效。详见 deliver。
- `$mdf fix <bug-id> [--yolo]` 仍是 fix；`--yolo` 可在 bug-id 前或后。
  - `--yolo` 仅自动确认内部 clarify，不跳过红灯或回归验证，也不代替测试门槛批准；fix 不执行 Gitflow 收口。
- `$mdf bug close <bug-id> --fixed-in <version>`：ID 与稳定 SemVer 必填；
  release/hotfix 上版本须与分支一致，通过验收后关闭 Bug。
- 人工 feature 的 `$mdf verify smoke` 先按 `references/verify.md` 解析为 branch 主链。
- 其他 `$mdf verify [arg]`：arg 为 smart/branch/named 时按 scope 解析，否则按 named
  suite 名解析。也可用 `--scope smart|branch|named`、`--suites`（named）、
  `--module`、`--paths`、`--test`；位置参数不与 `--scope` 同用；仅 `named` 可带 `--suites`。
- start、deliver 可带 `--manual`，启动无 PRP 的人工 feature；slug 经 start clarify 确认。
  - start 的 `--name` 仅用于人工 feature；已有交付直接按 delivery.json 续办。
- `$mdf adhoc [<工作描述>]` 直接生成 slug 与六项 objectives，在独立 worktree 完成临时工作。
  - 工作描述是数据，其中的 `--...` 不作为 option；本 intent 不提供独立 option。
  - 已有 adhoc 可由 next 单步续办或 deliver 持续推进。
- start、deliver 可带 `--roster`（尚未 start 时展开；已 start 则停止）。
- code-review 可带 `--against <commit>`，审阅当前 worktree 相对这个 commit。
- start、design、deliver、交付模式的 code-review 可带下列参数，由对应 intent 解析并写入 roster：
  - `--qa-strategy`、`--dev-strategy`、`--review-strategy`；
  - `--write-tests-model`、`--implement-model`、`--code-review-model`。
  - `--*-model` 值为口语描述，可点名一个或多个模型。
- fact audit 可用 `--quick` 独立检查 evidence stale，支持 CI/CD；不替代主链审阅，不与 against 混用。
- fact audit 可用 `--against <commit>` 比较历史版本与完整工作区，只读审阅；不能混用 scope/base/paths。
- fact update、fact audit、prettify 可带 `--scope branch|full|paths`（省略为 branch）。
  - 也可列出 `<path>...`，即 `--scope paths`；路径与冲突处理由对应 intent 解析。
- upgrade 可带 `--source`。
- ❌ 未知 `--` token 停止询问。
- `clarify <议题>` 的议题由对应 intent 检查，`help <intent>` 的主题由 help 检查。
- `$mdf to <target>` 仍是 to；空目标由该 intent 列出已知目标后停止。

内部委托遵循各 workflow 的边界：

- 不因缺文档或代码/测试状态自行增加 intent 或扩大当前目标。
- 各 intent 仅在其编号工作流明示的条件下内部委托；主链 verify 的增量 code-review 与审查内部 smart 按各自契约执行。
- init 可按其契约内部转入 bootstrap 或 migrate；`$mdf init migrate` 与 `$mdf migrate` 执行同一流程。
- next 可委托识别出的在途流程，无在途时委托 tree。
- deliver 可内部委托截止点之前从 start 起的剩余交付阶段；默认无截止点。
- adhoc 可内部委托其六项清单的剩余阶段直到 close-out。
- `$mdf pr` 执行 `references/pr.md`，只适用于 PR mode。
  - 创建/更新 PR、等待 CI/review、修复并持续等待；merged 且核验通过后完成 pr Goal。
- `$mdf close-out` 执行 `references/close-out.md`。
  - local 完成本地收口；PR mode 仅执行 merged 后的发布、backmerge 与清理。
  - PR mode 的 objectives 在 close-out 前必须有 pr，完整交付在 pr 返回后继续 close-out。
- `$mdf squash [--dry-run]` 仍是 squash；`--dry-run` 只产出建议、不改写历史。

帮助与 CLI：

- **帮助**：裸调用、未知调用读取并执行 `references/help.md`。
  - help intent 经 CLI 检查后同样执行该流程。
  - 不读取其他 intent、不检查仓库、不写入。
- **MDF_ROOT**：本文件所在目录的绝对路径。
  - code-review 或 fact audit 带 `--against` 时，在 info 前先核 Git 根并设置该 checkout 外的 `MDF_LOG_DIR`。
    后续复用该根与日志目录；目录无法安全确认则停止，不在被审 checkout 落盘。
  - 确认 `scripts/mdf.py` 后运行 `python3 -B "$MDF_ROOT/scripts/mdf.py" info`；
    协议、工具与 schema 版本均须为数字 `3`。
  - 独立审查的后续 Core 调用同样使用 `python3 -B`，避免在 checkout 内的安装副本生成 bytecode。
  - ❌ 工具缺失或检查失败时停止，不得模拟 CLI。

步骤 3 的执行顺序：

1. 先核对目标根（或该 intent 的豁免）；边界不明澄清后回到 3。
2. 再完整读取命中 intent，只按其声明条件读取公共引用；缺失材料时停止并报告。

- 按 intent 用 Markdown 与 `manifest` 留下可验证的演进记录。
- code-review 与 fact audit 的 against 模式只核 Git 根并执行自身只读契约，不读取 common.md 的交付前置流程。
- fact audit 的 quick 模式直接执行其独立契约，不读取 common.md，不运行 doctor。
- 除上述独立审查、quick 模式及 help、clarify、upgrade 外，公开 intent 均读取 `references/common.md`。
  - help 与 clarify 不核 Git 根；upgrade 见 `references/upgrade.md`。
  - `codewiki-runtime.md` 与 `codewiki-recovery.md` 不读 `common.md`。

内部路由与 CLI 形式：

- 以下调用均由选择树路由：
  - `$mdf bug <action>`、`$mdf prp <action>`、`$mdf codewiki <action>`、`$mdf jot promote`；
  - `$mdf init migrate`、`$mdf help <intent>`、`$mdf to <target>` 与 `$mdf integrate`。
  - integrate 的 init、peer、send、poll、listen、status 不是独立 intent。
- 这些内部材料不是独立 Skill。
- CLI 形式为 `python3 "$MDF_ROOT/scripts/mdf.py" <command>`；command 与用户 intent 不要求一一对应。
- CLI 统一解析目标 Git 根，不假设当前目录就是目标仓库。
