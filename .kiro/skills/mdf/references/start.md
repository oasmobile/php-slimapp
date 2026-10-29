# Start

一次只启动一个交付 kind。start 按 roster 建立 owner 与可选 qa/dev 角色分支。
开分支前展示并确认将冻结的 roster。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve branch                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [留在 1 询问]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Clarify objectives             │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [不写目标，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Confirm roster                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 未决 ────────────────────→ [留在 3]
                 ├──── 拒绝 ────────────────────→ [停止]
                 ├──── 与 needs_design 冲突 ────→ 2 Clarify objectives
                 │
                 ▼ 确认
┌──────────────────────────────────┐
│ 4 Start branch                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 创建前检查失败 ────→ [报告 finding，不创建分支]
                 ├──── 创建中失败 ────────→ [CLI 已回滚，报告并停止]
                 │
                 ▼ 创建成功
┌──────────────────────────────────┐
│ 5 Switch worktree                │
└────────────────┬─────────────────┘
                 │
                 ├──── 未切到 ─────────────────────→ [留在 5 等待]
                 ├──── collab-mode 已交接 ─────────→ [结束]
                 ├──── 已切到且 release 需联调 ────→ 6 Open integrate
                 └──── 已切到 ─────────────────────→ [结束]

步骤 5 先处理 collab-mode 交接；其余 release 需联调才进入 6，不是步骤 4 的后续。

┌──────────────────────────────────┐
│ 6 Open integrate                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 按 integrate 停止 ────→ [按 integrate 交接]
                 └──── 已进入 ───────────────→ [结束]
```

## 工作流（唯一执行契约）

人工 feature 使用 `--manual`，只读取 `references/manual-feature.md`「身份与启动」。
按本表创建交付，不执行该文件的续办工作流。

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

完整读取 `references/common.md` 与 `references/delivery-contract.md`。
deliver 委托时继承 `references/deliver-policy.md`；进入内部 intent 前核 until，decision 按该策略处理。
步骤 2：feature/release 内部执行 `references/clarify.md`；bugfix/hotfix 写精简 checklist，
可不走 grilling。对照 `assets/templates/objectives.md` 或 `release-objectives.md`。
步骤 6 读取并执行 `references/integrate.md`。
独立调用只推进当前 intent；deliver 内部委托时完成后返回调用方，由其选择下一阶段。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve branch | 脚本 | 确认 kind；普通 feature 选 PRP，人工 feature 确认 manual | 参数、list | 2 | 留在 1 询问 |
| 2 | Clarify objectives | 约束 | 盘点前置条件，写/确认 objectives checklist（含大步骤） | 确认目标与准备说明 | 3 | 不写目标，停止 |
| 3 | Confirm roster | 约束 | 确认 member、strategy 与 models | 明确确认、与步骤2的 needs_design 一致 | 冲突2；否则4 | 拒绝停止；未决留3 |
| 4 | Start branch | 脚本 | 运行 start，核对分支与 worktree | 分支、worktree | 5 | 检查失败不创建；中途失败已回滚并停 |
| 5 | Switch worktree | 约束 | 切到 owner；交接 | 路径、交接 | 同/跨→6；collab 交接结束；其他结束 | 留在 5 等待 |
| 6 | Open integrate | 约束 | 立即执行 `$mdf integrate` | Goal；跨 worktree 另有通道与 poll | 结束 | 按 integrate 交接 |

## 术语与数据结构

### PR mode 的收尾步骤

按 [交付契约](delivery-contract.md#pr-mode-的收尾步骤) 生成和续办 objectives。
PR mode 末尾为 pr checkbox 与无 checkbox 的 close-out；local 保持原顺序。

### 分支参数

<a id="s1"></a>

**参数**

一次只要求一个分支的类型和必要标识：

- 普通 feature 要 PRP ID；人工 feature 要 `--manual` 与已确认 slug。
  bugfix 要 Bug ID，release/hotfix 要稳定 SemVer。
- 四种 kind 均须有 objectives checklist（含 `[ ]`/`[x]` 大步骤）；roster `0,0` 也写。
  - 在步骤 2 确认并写入临时文件，步骤 4 由 CLI 经 `--objectives-file` 落入 `objectives.md`。
  - hotfix 始终记录已确认的热修复范围；roster ≥1 可由 design 修订。
- 普通 feature 必须绑定一个 active ready 且依赖满足、未 start 的 PRP。
  - 分支与交付目录 slug 取自该 PRP 文件名，不得另选，也不得使用对象 ID。
- bugfix 必须绑定一个 active open Bug；分支名为 `bugfix/<Bug ID>`，不得另选 slug。
  - ⚠️ 已锁定的 release 或 hotfix 上修复 Bug 不走本 intent，不创建 bugfix 分支。
- release 必须绑定稳定 SemVer；本版范围是 start 时已在 develop 的 child Change。
  - 不得把新 PRP 当作本版实现范围。
- 普通 feature 用户未指定 PRP 时运行 `list --repo "$REPO_ROOT" --type proposal --status ready`：
  - 只把 `blocked_by` 为空且 `in_progress` 为 `false` 的条目作为候选。
  - 按 `id` 与 `title` 供用户选择；不逐篇翻阅 `docs/proposals/`。
- 用户未指定 Bug 时运行 `list --repo "$REPO_ROOT" --type bug --status open`：
  - 按 `id` 与 `title` 供用户选择；不逐篇翻阅 `docs/bugs/`。

验收：明确参数；feature 另确认 PRP，bugfix 另确认 Bug，release 另确认版本。

异常与交接：询问。不得从自然语言猜测版本。

### 目标澄清

<a id="s2"></a>

**澄清**

所有 kind（含人工 feature）先执行下方「前置条件盘点」，将结果纳入本步的共同理解与确认文本。

人工 feature 先执行内部 clarify，议题为工作范围、验收与 slug。
独立调用必须先询问用户，再依据回答给 slug 建议并确认；deliver 委托按其 confidence 策略裁定。
采用 `manual-objectives.md`，start 已勾，其余六项未勾，不添加 design / converge。
`needs_design: false` 由 CLI 写入 delivery.json，objectives 不要求该字段。
下列普通交付的 needs_design、PRP 与阶段要求不适用于人工 feature。

feature、release、bugfix 与 hotfix 均按下列规则写入 objectives checklist；
feature 与 release 另经 clarify 确认目标；bugfix/hotfix 可用精简确认。

- 📌 必须明确并写入 `needs_design: yes` 或 `needs_design: no`（objectives 与随后
  `delivery.json`）。deliver/next 只读该字段。
  - `roster ≥1` 必须为 yes；选 no 则须把 roster 收成 `0,0`。
  - deliver 委托时由主 Agent 按其 confidence 策略裁定。
- feature：
  - 对照 ready PRP 与 `assets/templates/objectives.md`。
  - 使用内部 clarify intent，议题固定为「本次 feature 交付的目标、非目标、约束、
    是否需要 design，与可验证验收」。
  - objectives 用 `[prp-0001](../../../docs/proposals/<filename>)` 引用 PRP。
  - PRP 不足时停止，提示 `$mdf prp review`。
- release：
  - 对照 child Change 与 `assets/templates/release-objectives.md`。
  - clarify 议题含工作线、是否联调、是否需要 design、是否有开发（`has_dev`）。
  - 📌 必须写入 `has_dev: yes` 或 `has_dev: no`（本分支是否含预发布/开发代码改动）。
  - checklist **必须含** integrate、owner 开发、converge 项；跳过项在写入临时文件时
    即勾 `[x]`（不联调 → integrate；`has_dev: no` → owner 开发与 converge；无预发布
    事务 → 预发布工作）。不得靠缺席表示跳过。
  - 工作线四选一；只写入已选定的那一条；不罗列未选路径；不写「本版选定…」；必须写明四种之一：
    - 不联调：不执行 integrate intent（checklist 项已勾）。
    - 同 worktree：执行 integrate，不打开消息通道。
    - 跨 worktree：先开通道；写本侧可碰范围；只改本仓；
      不得改、操作、启动或终止对端。
    - collab-mode：由接手 Agent 直接调度前后端 worktree；本 Agent 完成本仓 start 后交接。
      交接规则见 [collab-mode](collab-mode.md)；本步只确认本仓范围与已知的对端信息。
  - 主链收口前为 verify branch → fact audit → close-out（不内嵌在 close-out）。
  - ❌ 不得实施新 PRP。
  - ❌ 不得因 roster `0,0` 强行保留未勾的 owner 开发 / converge。
- bugfix / hotfix：
  - 对照 Bug 与 `assets/templates/objectives.md`。
  - 精简 checklist 至少含：修复/范围、converge、lint、code-review、verify branch、
    fact audit、close-out；并含 `needs_design`。
  - 可不走 grilling；必须落盘临时文件供 `--objectives-file`。
- 共同理解确认后，将确认文本放在仓外临时文件，保持开分支前 clean。

验收：确认目标、前置条件与准备安排、`needs_design`（release 另含联调工作线与 `has_dev`）以及共同理解。
人工 feature 按专用规则确认，不要求 `needs_design`。

异常与交接：不写目标、不创建分支。

### 前置条件盘点

本条属于步骤 2，覆盖内部 clarify、精简确认与人工 feature；调用 clarify 时作为必须落地的事实传入。

- 先查仓库与已有对话：运行说明、配置样例、runtime/dependency 声明、启动与测试入口、CI 和已配置 hook。
  只盘点本次实现与验收需要的条件；已有证据或有效确认直接复用，只询问剩余未知项。
- 按实际需要核对以下内容；没有额外依赖时一句说明即可，不强制空表或逐类提问。
  - 配置：必填项、用途、已有默认值与待决定的值。
  - credential：名称、用途、权限、可用状态与注入来源或方式。
  - 环境与资源：runtime 版本、服务、数据库、网络、测试账号、测试数据与联调对端。
- 区分未知事实与未就绪资源：
  - 缺项影响目标可行性、方案选择、验收范围或当前步骤时，先查证或向用户确认；无法获得则停止。
  - 条件与准备方式明确、仅后续阶段使用的资源，可确认准备方与最晚就绪阶段后继续。
    最晚就绪阶段按首次使用确定，可能早于 verify；到时未就绪则报告阻塞，不跳过必要验证。
  - 用户认可准备计划、confidence 或 `--yolo` 均不代表资源已可用。
- 核对新 worktree 的准备范围：不假定旧工作区的 gitignored 配置、本地文件或 virtual environment 自动可用。
  qa/dev 并行需要独立端口、数据库或账号时，确认相应准备方式；owner hook 的结果不代表 qa/dev 已就绪。
- 在既有 objectives 的约束或准备说明中记录所需条件、已知状态、准备方式、准备方与最晚就绪阶段。
  不新增阶段 checkbox；不要求用户在对话中粘贴 secret，不将密钥值写入 objectives、报告、日志或 Git。
- 不因盘点自动复制 `.env` 或 credential；post-start hook 仍按原契约执行，失败仅汇报。

### Roster 确认

<a id="s3"></a>

**确认**

解析将冻结的 roster：

- 人工 feature 固定 `0,0,1`，参数与之冲突时停止；不建立 qa/dev 角色分支。
- 其他交付未指定 `--roster` 时的默认值：
  - feature 默认 `min-tdd`。
  - release 默认 `solo` 加 3 名 partition reviewer。
  - bugfix 与 hotfix 默认 `solo`。
- 再叠加本次以下参数与对话中已确认的人数：
  - `--qa-strategy`、`--dev-strategy`、`--review-strategy`
  - `--write-tests-model`、`--implement-model`、`--code-review-model`
- 对话里口语点名的模型（可多个、不要求官方 id）写入对应 `--*-model` 一句字符串。
- 一侧为 0 另一侧 ≥1 时把 0 抬成 1。
- 未指定细项策略时随 named roster：
  - solo/min-tdd/competing-pair 为 `best-of-n`+`replicate`。
  - coop-pair 为 qa/dev `partition`。
- `--roster` 取值：`solo` / `min-tdd` / `competing-pair` / `coop-pair`。

向用户展示以下内容：

- named roster（显式名称或 kind 默认）。
- member：owner 恒为 1，以及 `qa`、`dev`、`reviewers` 人数与将创建的 qa/dev 角色分支。
  - `0,0` 只建 owner。
- strategy：`qa_strategy`、`dev_strategy`、`review_strategy`。
- 若本次带了任一 `--*-model`，按 intent 展示对应字符串（口语，可多个模型）。
  - 未带的 intent 不写、不问、不提。

确认规则：

- 用户可改人数或策略；改后按上列规则重新展示，不得静默沿用旧值。
- qa/dev 改动与已确认 needs_design 冲突时回步骤 2，仅重确认受影响内容并更新临时 objectives。
  不用未更新的旧文件进入 start CLI；此前未变的目标、slug 与其他确认直接复用。
- roster 改动影响端口、数据库、账号等资源需求时，同样回步骤 2，仅更新并重确认受影响的准备说明。
- 📌 必须取得明确确认才进入创建；不得把沉默当作同意。
- 由 deliver 委托时，本步按已给参数与上述默认值、其 confidence 策略裁定。

验收：用户明确确认将冻结的 roster。

异常与交接：拒绝则停止，不创建分支；未决或非明确答复留在 3。

### 创建与切换

<a id="s4"></a>

**创建**

解析目标 Git 根为 `REPO_ROOT`；运行 `start --repo "$REPO_ROOT" --kind <kind>`，按 kind 追加参数：

| kind | 追加参数 | 说明 |
| --- | --- | --- |
| 人工 feature | `--manual --name <确认slug> --objectives-file <确认文件>` | 不传 `--proposal` |
| 普通 feature | `--proposal <PRP-ID> --objectives-file <步骤 2 确认文件>` | 不传 `--name`；CLI 从 PRP 文件名取出 slug |
| bugfix | `--bug <Bug-ID> --objectives-file <checklist 文件>` | 不传 `--name`；CLI 用该 ID 作为分支名 |
| release | `--version <semver> --objectives-file <步骤 2 确认文件>` | — |
| hotfix | `--version <semver> --objectives-file <checklist 文件>` | — |

- 将步骤 3 确认的 roster 传给 CLI，不得改写已确认值：
  - 选用 named 时传 `--roster`。
  - 人数以 `--qa`、`--dev`、`--reviewers` 传入。
  - 策略以 `--qa-strategy`、`--dev-strategy`、`--review-strategy` 传入。
  - 有某 intent 的 model 时传对应
    `--write-tests-model` / `--implement-model` / `--code-review-model`。
- CLI 仍把一侧为 0 另一侧 ≥1 的 0 抬成 1；步骤 3 展示的须是抬成后的值。
- 未带的 `--*-model` 不写入 roster.models 对应键。
- `--roster` 只展开为人数与策略，不写入 delivery.json。
- CLI 要求 clean，且本地基线分支存在；不 fetch、不要求 origin、不 push。
- 有 origin 时，开分支前用 `ls-remote` 核对基线，不更新远程跟踪分支。
  - 远程提交已在本地（相同或本地更新）才通过。
  - 远程有本地没有的提交则停止，不创建分支。
  - 无 origin，或 origin 上没有该基线分支，则跳过。
- feature/bugfix/release 从本地 develop 创建，hotfix 从本地 master 创建。
- 本地已有同名分支则失败，不检查远端。
- 始终从基线在仓库同级 `<repo-name>-worktrees/<worktree-name>` 建立 worktree：
  - 路径等于分支名，`/` 为嵌套目录。
  - 不在当前目录开分支、不抢占当前 checkout。
- roster ≥1 时按人数建立 `qa/<owner>`、`dev/<owner>`，
  第 2 路起为 `qa/2/<owner>`、`dev/2/<owner>`；`0,0` 只建 owner。
- 成功 JSON 含 `worktree`（owner）、冻结后的 `roster` 与 `roles.qa` / `roles.dev` 列表。
- CLI 成功后按 [post-gitflow-start](post-gitflow-start.md) 执行 hook。
  - command 已由 CLI 执行，Agent 汇报前后说明与结果。
  - JSON 的 `hook.status: pending` 表示 rule；切到 owner 后读取并执行规则，
    执行前说明名称、path 与 cwd，执行后汇报成功或失败；失败不影响 start。
- 创建中失败时 CLI 自动回滚本次已建的全部 worktree 与分支，Agent 不再手工拆除。

验收：检查、本地分支与实际工作目录。

异常与交接：

- 创建前检查失败时不创建分支并报告 finding；创建中失败时 CLI 已回滚，报告并停止。
- 不推送，不设置 upstream。
- CLI 在本地 Git config 中：
  - 以 `branch.<完整分支名>.mdf-start-commit` 固定起点完整 hash，供 bugfix/hotfix code-review 使用。
  - 以 `branch.<owner>.mdf-roster` 冻结人数与策略。
  - 删除分支时该配置随分支删除，不设置 upstream。
- 人工 feature 写入 `manual: true`，不写 proposal。
  材料与人工清单按专用契约。
- 其他交付阶段材料：
  - 普通 feature 与 release 的 owner 写入 `changes/unreleased/<slug>/delivery.json`
    （含 roster）及 `objectives.md` 并提交。
  - bugfix/hotfix 同样写入 `delivery.json`（含 roster）与含 checklist 的 `objectives.md`。
  - 写入后将「确认目标与约束 / 确认工作线与范围」项改为 `[x]`（start 自勾）。
  - roster ≥1 时 design 可修订 objectives；roster `0,0` 亦须有 objectives。
  - bugfix 的 named suite 关联由主链 `$mdf verify`（branch）前写入，本步不写。
- roster ≥1 时后续 write-tests / implement 使用 `roles` 列表中的路径。
- 创建成功进入 5，本步不结束。

<a id="s5"></a>

**切换**

目标固定为步骤 4 JSON 的 owner：`worktree` 绝对路径与 `branch` 完整分支名。

- qa/dev 不在本步切换。
- 按 `references/common.md` 的「切换工作区」规则进入该路径与分支。
- 向用户给出目标绝对路径与分支名。
- Cursor 未进入则留在 5，重复切换；其他宿主绑定绝对路径后即通过。
- 不拆除已建 worktree 与分支。
- 已切到后看 objectives，release 的 collab-mode 先按 [交接契约](collab-mode.md) 输出本仓材料并结束。
  - deliver 内部委托时返回调用方并说明待接手，不进入 6、不接管另一仓的 start 或联调。
- release 且为同 worktree 或跨 worktree 则进入 6，不得先结束。
- 其他 kind，或不联调的 release：
  - 独立调用结束，由用户手动触发 design 或通过 next 委托。
  - deliver 内部委托时返回调用方。

验收：已切到 owner；collab-mode 已交接；同/跨 worktree 联调进入 6，否则结束或返回。

异常与交接：未切到则留在 5。

<a id="s6"></a>

**通道**

仅 release 且 objectives 写明同 worktree 或跨 worktree 时进入。不联调不进入。
切到 owner 后立即执行，不得先做其他预发布工作。

- 完整读取并执行 `references/integrate.md`。
- deliver 的 until 排除 integrate 时在委托前返回截止点与当前 resume 位置，不打开通道或启动 poll。
- 同 worktree 不打开消息通道。跨 worktree 从其步骤 2 打开通道。
- 从其步骤 2 起强制 Goal。Goal 完成前，用户没让你停，永远不许停下来。
- 跨 worktree 等待对端按 15、30、45、60 秒输出正在等什么，不得只盯 `waiting`。
- 跨 worktree 本侧只 poll 本侧 `--repo`；对端 inbox 由对端自己的 agent 消费。
- 独立调用：integrate 结束后本 intent 结束。
- deliver 内部委托：integrate 结束后返回调用方。

验收：Goal 已创建。跨 worktree 另要求通道已打开且 poll 在后台。

异常与交接：按 `references/integrate.md` 交接。
