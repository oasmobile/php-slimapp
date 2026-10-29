# 交付契约

树形：not-tree。本流程核对当前交付阶段的共同契约，阶段仍由原 intent 的编号工作流承办。

## 工作流（唯一执行契约）

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve context | 约束 | 确认调用方、当前步骤与适用事件 | 调用上下文与事件 | 2 | 缺上下文则返回缺项，不猜测 |
| 2 | Apply rules | 约束 | 核对适用规则、前置证据与边界 | 命令、产物与检查记录 | 3 | 不符或缺证据则返回失败 |
| 3 | Return | 约束 | 返回检查结论，继续调用方当前步骤 | 可追溯结论与缺项 | 返回调用方 | 缺项返回失败，不推进业务阶段 |

## 术语与数据结构

### PR mode 的收尾步骤

objectives 按 manifest.closeout.mode 固定收尾结构，local 使用原有 checklist。

- PR mode 将末尾 close-out checkbox 替换为 `- [ ] pr`。
- pr 后写普通步骤 `- close-out（pr merged 后必须续办；不设 checkbox）`。
- pr 仅勾自己的候选项；提交后仍持续等待实际 merged，不凭勾选结束 Goal。
- close-out 没有 tick，以发布、backmerge、source 清理与最终核验判定完成。
- 完整交付在 pr 完成后继续 close-out；until、暂停与普通 next 的单步边界仍有效。


适用事件包括：身份、主线、roster、底座、并行、补覆盖、验证或历史整理事件。仅读取条款不触发其中描述的其他 intent。

由 deliver 与各交付 intent（含 verify、fact、close-out）读取。
`$mdf integrate` 只读「补覆盖」。规则持续适用。
人工 feature 先读取 [专用契约](manual-feature.md) 的当前阶段条款，优先于下文普通主线。
adhoc 先读取 [专用契约](adhoc.md) 的当前阶段条款，使用其六项账本、smart report 与对应模式的收口规则。
应用条款不重新进入这两个文件的入口或续办工作流；仅由原调用方按已声明条件委托。
### 身份与材料

一个 feature 对应一个依赖满足的 active ready PRP。

- start 经 clarify（bugfix/hotfix 可精简）写入 `objectives.md`。
  并冻结 `needs_design: yes|no`（objectives 与 `delivery.json`）。
- feature 的 objectives 引用 PRP，避免复制另一个需求来源。
- release 的 objectives 写已选定工作线、本版收口范围、预发布工作、联调、
  `has_dev`、非目标与可验证验收，不引用单个 PRP。
  - 工作线只保留开分支前选定的一条，不罗列未选路径。
  - 冻结 `has_dev: yes|no`：本 release 分支是否包含预发布/开发代码改动。
    - `no`：start 写入时即将 owner 开发、converge（及无事务时的预发布工作）勾为
      `[x]`；不跑这些 intent。
    - `yes`：保留未勾，走 owner 开发 → converge。
  - checklist **必须含** integrate 项；不联调由 start 写入时勾 `[x]`；其余模式由
    `$mdf integrate` 收口自勾。deliver/next **只读该勾选**。
  - 该分支不得实施新 PRP。工作线四选一，只写选定的一条。
  - 不联调不执行 integrate intent。同 worktree 执行 integrate，不打开消息通道。
  - 跨 worktree 切到 worktree 后先开通道。只改本仓，不得改、操作、启动或终止对端。
  - collab-mode：start 完成本仓准备后交接，由接手 Agent 操作两端；见 [专用契约](collab-mode.md)。
  - 三种联调强制 Goal；Goal 完成前用户没让停就持续推进；双端验收且确认冻结、integrate 已勾才允许 code-review。
- start 后四种工作分支均须有 `objectives.md`，含 `[ ]` / `[x]` 大步骤 checklist。
  - bugfix / hotfix：roster `0,0` 也由 start 写入；roster ≥1 可由 design 修订。
  - hotfix 始终在 `changes/unreleased/<semver>/objectives.md` 记录已确认的热修复范围。

身份字段：

- slug 取自 PRP 文件名，start 固定使用，不随标题修改。
- delivery.json 记录 proposal/bug、slug、branch、start_commit、`needs_design`。
- release 的 `has_dev` 只冻结在 objectives（与 checklist 跳过预勾一致），不另写入
  delivery.json。
- 起点是创建分支前基线的完整 commit hash，不用移动的 develop/master 代替。

材料位置：

- 开发材料自 start 起位于 `changes/unreleased/<slug>/`：
  - objectives.md、delivery.json、可选 gates/（配置快照）、code-review.md；
    `needs_design: yes` 时另有 design.md。
  - close-out 在同一目录补齐 CHANGE.md，不搬迁；发布后随目录进入
    `changes/<version>/<slug>/`。
  - Gitflow 前补齐详细 `delivery-summary.html`；格式与内容见 [HTML 工作材料](html-materials.md)。
- release 材料位于 `changes/unreleased/<semver>/`：start 写入 objectives.md 与 delivery.json。
  - HTML 总结随收口材料进入 `changes/<semver>/`，不建 child Change。
- 代码、测试、fixture 留在项目原位置，大日志不要求提交。

路径写法：

- objectives/design 是受管可搬迁 Markdown；`delivery-summary.html` 是受管可搬迁 HTML。
- 仓内 Markdown 本地链接只相对当前文件（`./`、`../` 或同级文件名）；前导 `/` 是站点根，不是仓根。
- 搬迁时 CLI 改写仍有效的相对路径。
- delivery.json 与可选 gate 快照内路径一律仓库相对。
- fingerprint 规范化用仓库相对或 `@delivery/`，不是第二种 href 写法。
### 总结生成

close-out 用固定脚本生成总结外框、目录及样式，不现场拼装生成器。

- 按 `html-materials.md` 和总结正文模板写出完整 HTML 正文文件；不是 Markdown 或完整文档外框。
  - 七个必填章节均须有内容和唯一 `id`；链接相对最终总结位置，清除模板槽。
  - 源码与原始日志引用放在 `pre` / `code` 中并正确 escape，引用中的字面 marker 保留。
- 在 owner 运行以下命令；允许未提交的本次材料，不要求先获得 clean：

```bash
python3 "$MDF_ROOT/scripts/render_summary.py" --repo "$REPO_ROOT" --body-file <正文HTML文件>
```

- 脚本按当前 kind 选择 unreleased 目录；已收口 release/hotfix 使用版本根。
  - 已开始 Gitflow 发布时停止，不改写源提交；读取已有归档总结继续核对。
- 退出 0 后回读 JSON `path`，打开实际 HTML，核对详细内容与证据，再提交。
  - 静态校验不替代语义审阅；不得把未执行的 merge、tag、push 写成成功。
- 非零时读 JSON 错误与 `log`，保留原总结；正文可修则原地修正后重试，否则停止并报告。
  - 汇总阶段之后新增的对象 outcomes、收口结果与偏差，在 Gitflow 前用同一命令补齐。

### 阶段与执行责任

四种 kind **共用**主线。不按 branch kind 另写交付状态机。
并行形态与是否 design 由默认 roster 与 `needs_design` 决定；
**有无开发阶段**看 objectives checklist（及 release 的 `has_dev`）。
**不**由 roster `0,0` 推导出必须空转的 owner 开发 / converge。

主线步骤：

1. start
2. release：integrate（checklist 项；不联调已由 start 勾掉则跳过 intent）
3. 可选 design
4. write-tests / implement，或 owner 开发（无对应未勾项则跳过）
5. converge（无对应未勾项则跳过）
6. lint
7. code-review
8. verify branch
9. fact audit（必要时 fact update 后重审）；进入前执行可选 pre-gitflow-finish hook
10. close-out

- **是否 design**：start clarify 冻结 `needs_design`；deliver/next 只读该字段。
  - `roster ≥1` 必须 `needs_design: yes`；选 no 则须收成 `0,0`。
- **进度**：唯一账本是 `objectives.md` 步骤 checklist；各 intent 成功后**自勾**。
  - deliver / next 只读勾选与依赖决定下一 intent，**不**读 stage gate、**不**对 report 做过期审判。
  - roster `0,0` 只表示无 qa/dev 角色；不自动要求 owner 开发或 converge。
- **converge**：仅当 checklist 的 converge 项仍为 `[ ]` 时进入；核对前置已勾，跑
  **verify smart**，修到达成后自勾。
  - ❌ converge 的「验」不是 verify branch。
- **verify branch / code-review / fact**：独立 intent；落盘均为 **report**（非 gate）。
  - verify 默认 suite：feature/bugfix/hotfix → smoke；release → release；失败现场修到绿。
  - fact：verify branch 之后、close-out 之前 audit；未通过则 update 后重审。默认 scope=`branch`。
  - 进入 fact 前按 [pre-gitflow-finish](pre-gitflow-finish.md) 执行可选 hook。
    仅文档改动直接进入 fact；其他改动补审补测。失败仅汇报，仍按实际改动处理；续办不重跑。
- **close-out**：材料与 Gitflow 收口。
  - PR mode 的提交与恢复见 [PR](pr.md)；创建 PR/MR 不代表完成。
  - 只查 report **交没交**（有文件且声称通过）；不复验报告对不对、不做 commit 对齐审判。
  - 不内嵌、不委托 verify（branch / smart / named）；不内嵌 fact。
    bug close 不算 verify 族，release/hotfix 收口步骤可委托。
  - `release-closeout` 只复用可复用的 `verification-report.json`，永不执行验证命令。
  - PR 模式每次 roster merge、远端主线 merge 与 push 前强制执行 `references/squash.md` 的检查；local 模式可选。
- 开发迭代只用 `$mdf verify --scope smart`；branch 只用于交付验收。
- release/hotfix 可修已确认 open Bug，标 `fixed`；不另开 bugfix。
- 独立 `$mdf fix` 不走交付主线，也不由 deliver 内部委托。
- `$mdf bug close` 不作为 deliver 的直接阶段；close-out 可按本契约内部委托，不改变独立调用的边界。
- code-review 份数取冻结的 roster.reviewers；close-out 与主链 verify 修绿的增量新一轮为 1。
#### 触发与协调

- 用户手动触发主线 intent，或显式调用 next 委托下一阶段。
- 显式 deliver 按 `references/deliver.md` 串联截止点之前的剩余真实 intent。
  - 可并行阶段按 roster 分别委托 subagent。
  - 除 pr、close-out 入口确认外，默认自动裁定其他 decision，confidence 低于 0.8 请求用户确认；默认用 Jev 评分，无 Jev 时主 Agent 评分。
  - 默认无截止点，直到 close-out 完成；非 yolo 在 pr、close-out 前分别取得用户确认。
  - 显式 until 为 exclusive，`--stop-at` 为别名；yolo 跳过入口确认、无 confidence 限制。
  - 显式 until 对 yolo 仍生效；子 intent 的确认与批准统一遵守 deliver-policy 的入口确认与 confidence 策略。
- design 的 Baseline 与 converge 由各 intent 启动恰好 1 个 owner subagent，不计入 roster。
- deliver 步骤 4 只覆盖可并行的 qa/dev。
- 不新增独立 Owner 调度服务或统一状态协议。
- 当前执行者承担该阶段的协调与语义审查。
#### worktree 与 roster

- start 始终从基线在仓库同级 `<repo-name>-worktrees/<worktree-name>` 建立交付 worktree，
  路径等于分支名；不在当前目录开分支，不 fetch、不 push。
  - 有 origin 时基线的远程提交必须已在本地；本地可以更新。
- roster 在 start 开分支前展示 member、strategy 与 models 并经确认后冻结。
  - 写入 `delivery.json`（有交付材料时）与 `branch.<owner>.mdf-roster`。
  - 字段为 `qa`、`dev`、`reviewers`，以及 `qa_strategy`、`dev_strategy`、`review_strategy`；
    可选 `models`。
- owner 恒为 1。

| kind | 默认 named roster |
| --- | --- |
| feature | `min-tdd`（`1,1,2` + best-of-n） |
| release | `solo`，但 reviewers 为 3、`review_strategy` 为 `partition` |
| bugfix、hotfix | `solo`（`0,0,1`） |

- 点名 `--roster` 时不叠加该 release 默认。
- 也可用 `competing-pair`（`2,2,3` 竞争）或 `coop-pair`（`2,2,3` 分工）。
- 四种 kind 都可改人数或改名。
- qa 与 dev 只能同时为 0 或都 ≥1；一侧为 0 另一侧 ≥1 时把 0 抬成 1 再冻结。
- `0,0` 时测试与实现都在 owner 上做。
- `≥1` 时 start 按人数建立 `qa/<owner>`、`dev/<owner>`，第 2 路起为 `qa/2/<owner>`、`dev/2/<owner>`。
#### 底座、执行者与策略

- design 只在 owner 提交共用代码底座；两路不得各自再写底座。
- design 不创建角色 worktree。
- Clarify 由当前 Agent 在主会话完成；Baseline 由该 intent 启动恰好 1 个 owner subagent 写入。
- converge 由该 intent 启动恰好 1 个 owner subagent 执行 roster-join、验证与记录；测试修改批准回主会话。
- 均不可配人数；无法启动则停止，不降级由当前 Agent 代做。
- write-tests 与 implement 在对应角色树上执行，入口先 no-ff merge owner；
  `0,0` 时在 owner 上编写测试与实现。
- qa 与 dev 互不传入路径。同侧 ≥2 时并行互不知情。

| 侧 | 策略 | 规则 |
| --- | --- | --- |
| qa/dev | `best-of-n`（默认） | converge 选 base 并只合 winner，集成后在 owner 吸收其余优点 |
| qa/dev | `partition` | design 写明各 index 切片，converge 按 index 全部合入，冲突视为分工重叠并停止 |
| review | `replicate`（默认） | 每人覆盖同一份本轮范围 |
| review | `partition` | 按切片审查 |

- 各路并行产出在合入前按分支核验；同路径冲突时保留先合入的版本。
  - qa 为 `partition` 且 ≥2 时：roster-join 合完全部 qa 后，
    可写 `gates/roster-join.json` 测试 fingerprint 快照。
  - 该文件是配置/辅助，**不是**进度 gate。
- review 时 owner 仍汇总裁定，不按票数。
#### intent 参数与 models

- `$mdf start`、`$mdf deliver` 可带 `--roster <name>`，只在尚未 start 时展开；
  已 start 后再带 `--roster` 停止。
- `$mdf start`、`$mdf design`、`$mdf deliver`、`$mdf code-review` 可带下列参数：
  - `--qa-strategy`、`--dev-strategy`、`--review-strategy`。
  - `--write-tests-model`、`--implement-model`、`--code-review-model`。
- 这些是 intent 参数，不是独立 intent。start 冻结；之后由 Agent 调用 `delivery roster` 写入。
- qa/dev strategy 在 design **完成后**锁定（看 objectives 勾选，不靠 stage gate）。
- review_strategy 与 `models.code-review` 可在 code-review 覆盖。
- deliver 把 strategy / models 转交给 start、design、code-review；`--roster` 只转交 start。
- 未知 `--` token 停止询问。

models 取值：

- 每个 `--*-model` 取随后一个 token（口语整句，可含空格）；未带的 intent 不写、不问、不提。
- `models` 按 intent 可选，键只允许 `write-tests`、`implement`、`code-review`。
- 值为一句口语描述：可点名一个或多个模型，不要求官方 id 或固定分隔格式。
- Agent 分派某 intent 的 subagent 时只读取并写入该键，现场解析并选用。
  - 该路有多名执行者时可把多个模型分给他们。
  - 没有则不提模型或 effort。
  - 不得把其他 intent 的模型写入本路任务。
- 策略字段的 JSON 键为下划线形式。

Git 约束：

- 开发阶段的本地工作分支不推送；PR mode 的 pr 按 [PR](pr.md) 推送交付源分支。
- 禁止 rebase，异名分支使用 no-ff；合并冲突保留现场。
### 进度与 Report

**进度唯一账本**：`objectives.md` 步骤 checklist。各 intent 成功收尾必须自勾对应项并提交。

- deliver / next / 人工续办：只读勾选决定下一 intent。
- write-tests 写完可编译或可加载执行的测试即完成，**不要求全绿**；完成后自勾 objectives。
- ❌ 不以 `gates/<stage>.json`、`verification-report.json`、fact 审阅报告、`code-review.md` 当阶段通行证。
- ❌ 不对 report 做「相对 HEAD / 相对上游 intent」的过期 gatekeeping。

**Report**（证明做过与结果，供核对「交没交」）：

| Report | 典型路径 | 谁写 |
| --- | --- | --- |
| code-review | `…/code-review.md` 无 commit 终稿 | code-review |
| verify branch / adhoc smart | `…/verification-report.json`（及可选 `verification-report.md`） | verify |
| fact | 材料目录内审阅报告 / 会话审阅结论 | 调用方（audit 只返回审阅结果） |
| 测试框架报告 | `.mdf/reports/` 等 | verify |

close-out 只查上表是否已交且声称通过；不复验对不对。
#### CLI 确定性辅助（非进度）

`delivery status/check/record/roster-join/roster` 仍可执行。

- `record --stage design` 可写入 **design policy 配置快照**
  （protected_paths / suites）。
  - 语义是配置/report，**不是**进度 gate。
- `record/check` 其他 stage、以及 `gates/*.json` fingerprint：
  **禁止**当作进度或验收关口。
  - Agent 主链不得用其选型或卡 close-out。

测试门槛与所需 suite：

- 设计 policy 的 protected_paths 覆盖所有测试、fixture、快照和工具配置，包括 named suite 的路径。
  - modules.yaml 的分套件入口始终属于测试门槛。
  - 路径可以是仓库相对文件、目录或 glob。
- design policy 必须另含 `suites`：本交付改动涉及的全部功能块的 named suite 名。
  - 非空列表，不得使用 lint/build/quick/smoke/release/full。
- 点名执行 test case 或 test 仅用于定位，不替代所需 suite 通过。
- `$mdf verify` / 验证 report 必须写出 Core 实际跑过的 `suites`。

补验（仅在**该** intent 内）：

- 开发中与 converge 只跑 module **smart**。
- **verify branch**：无论成败均写入 `verification-report.json`（不含 commit）；未绿可修则
  先落盘再修、重跑，直至绿后勾选；未绿轮不写通过用 `verification-report.md`、不勾选。
- 只改事实文档或 module ignore：不因「报告对齐」要求机械重跑 branch
  （close-out 也不做 commit 对齐审判）。
- fact / code-review / verify 均无 delivery stage gate。
#### 测试层级与分类

- 层级：test 是含若干断言的最小测试项，通常为函数；test case 是服务于同一目标的
  一组 test，通常为类或文件；suite 是 test case 的集合。suite 成员粒度是
  test case，归属写在代码里（marker、目录等），文档只写选择规则，不逐条列举。
- kind 按测试对象划分：UT 测内部单元；IT 测产品真实开放的接口（lib 的函数、
  服务的 API 等），一般不用 mock；E2E 走用户最终入口（浏览器、模拟器、命令行
  调用、使用 lib 的 demo-app）。PT 是生成输入并断言不变式的手法，可用于任一层级。
- 依赖按是否 hermetic 划分：测试进程能自行拉起全部依赖、不需要预先存在的环境、
  凭据或网络即为 hermetic；依赖第三方资源或真实兄弟产品（如联调对端）即为
  external。第三方资源不含待测产品与兄弟产品；mock 掉兄弟产品后才算 hermetic。
#### 失败语义

五个入口出现以下任一情况都是失败：

- 非零退出。
- warning、notice、deprecated。
- skip。
- xfail 或 xpass，以及 suite 未选中任何 test。

运行时约束：

- test case 是否属于本次 target 由 suite 的成员选择规则在收集阶段决定。
  - ❌ 不得在运行时按环境变量、配置或资源是否可用去 skip 或提前返回。
- external 资源未就绪即失败。
- 已知缺陷登记为 Bug 并把对应 test 移出 suite，不用 xfail 保留。

test case 内有 test 依赖当前 suite 不具备的条件时，按依赖
拆成多个 test case 分别归入合适的 suite；不得整体移出，也不得保留 skip。

Core 判定退出码与测试报告（见下节）。

- 报告无法体现的 warning、notice、deprecated，项目须让入口命令或测试运行器非零退出，
  并把配置写进 `docs/system/testing/`；code-review 核对该配置。
- 第三方依赖产生、本项目无法修复的 warning 或 deprecated 只可精确豁免。
  - 写明类别、来源模块与理由，记在 `docs/system/testing/`，新增或放宽须用户确认。
#### 测试失败工作流

converge（smart）与 verify branch **共用**：

1. 测试运行必须有框架自带报告文件（JUnit 等），禁止靠 tee/tail 冒充报告。
2. fail 后先复测**单用例**。
3. 修一个用例 → 复测该单用例。
4. 有 side effect 的 flaky 例外（须记录依据）。
5. 相关单用例都绿后，才继续该轮 verify（smart 或 branch）。
#### 测试报告

每次运行 suite（含 named suite）都必须产出 JUnit XML 报告。

- Core 为每次运行新建 `.mdf/reports/<时间戳>-<suite>/`，以环境变量 `MDF_REPORT_DIR` 传给入口命令，
  命令把 XML 写进该目录；lint 与 build 也各有运行目录。
- 每个运行目录都保存该命令完整的 `stdout.log` 与 `stderr.log`。
- `.mdf/reports/` 由 Core 自带 `.gitignore` 忽略，7 天前的条目自动清理，见 `common.md`「日志与报告」。
- test case 取 `<testcase>` 的 `classname`，缺失时取所在 `<testsuite>` 的 `name`；
  项目须配置运行器使其对应 test case。
- Core 解析后在同目录写 `summary.json`：test case 级的结果与用时，及其下 test 级的
  结果与用时。report 与 code-review 记录报告路径与 test case 级汇总。
- 缺报告、报告无法解析、未含任何 test，或含 failure、error、skipped（含 xfail）时，
  该 suite 失败，即使命令退出码为 0。
- 点名执行 test case 或 test 只用于定位；定位复测仍应尽量落盘框架报告。
  有运行器报告则读报告；否则用 `mdf.py run` 落盘。
#### 验证 suite

| suite | 成员 | 预算 | 何时必跑 |
| --- | --- | --- | --- |
| quick | 只含 hermetic 的 UT 与 PT | 30s | 任何改动 / smart |
| smoke | 任意种类，包含 quick 的全部成员 | 300s | feature/bugfix/hotfix 的 verify branch |
| release | 发版所需的 test case，包含 smoke 的全部成员 | 无 | 仅 release 的 verify branch |
| 项目自定义 suite | 某一功能块的 test case；一 suite 一文档 | 无 | smart 选题，不默认整 suite |

- 验证入口为 lint/build/quick/smoke/release 与可选 coverage；保留名称不得用作 named suite。
- named suite 是自定义 suite 的统称；报告使用实际名称，不把它作为包含全部自定义 suite 的聚合入口。
  - 各 suite 可重叠；自定义 suite 也可含 smoke 之外的成员，完整覆盖后才可复用同一报告。
- lint 与 build 同 quick 一样必跑：smart 只跑涉及 module；branch 跑全部 module。
- 每个 **named** suite 在 `docs/system/testing/<name>.md` **独占一页**。

| 交付阶段 | Core 必须通过 | Agent 另须通过 |
| --- | --- | --- |
| 开发中 / converge smart | 涉及 module 的 lint、build、quick | 本分支新增/改动测试；可选 named 选题 |
| verify branch（feature/bugfix/hotfix） | lint、build、quick、smoke | bugfix 另有 `suites.json` 选题记录 |
| verify branch（release） | lint、build、quick、release | — |
| 主链收口前 | verify branch 绿 + fact audit 通过 | 必要时 fact update |
| 只改事实 / ignore | 不机械重跑业务验证 | — |

named suite：命令在 `docs/system/testing/<name>.md` frontmatter；用 `verify --scope named --suites <名>` 执行。
`needs_design: yes` 时 design 列出涉及的 named suite。
bugfix 的 `suites.json` 在 verify branch 前关联已文档化 named suite（≥1）。

补覆盖与 quick 复现：缺覆盖则先补 reproduce；优先放入 quick，其次 smoke。
verify branch 中非 quick 失败时尝试补 quick 复现；结论写入
`changes/unreleased/<slug>/verification-report.md`。code-review 本轮触及的非 quick 失败另在
`code-review.md` 记「quick 复现」字段（各记各的，不互替）。
### 可选历史整理（squash）

PR 模式共享动作前必须读取 `references/squash.md` 并执行安全边界检查与分析后的分段整理；无可压缩区间则 no-op。
local 模式仅调用方建议或用户显式调用时读取其可选地板、建议条件与执行契约。
所有模式的 planning land 前也执行必要检查；squash 默认自主分析执行，无需逐次确认计划。

### 修改与提交权限

调用交付 intent 授权其必要的设计基线、阶段提交和工作分支集成，提交使用中文
Conventional Commit。修复某个 Bug 的提交说明必须含该 Bug 的完整 ID。

- 只暂存当前阶段的必要路径；不得顺带提交无关用户改动。
- 可以主动提交尚未完成的阶段产出，但须准确记录未完成状态。
- 阶段提交不代表 objectives 已勾或 report 已交，不能绕过既有验收与审阅。

各 intent 对测试与验证门槛的权限：

- 首次 write-tests 按既定设计编写测试属于授权：
  - 含把用例归入 quick、smoke 或 design 声明的 named suite。
  - 含在 `docs/system/testing/` 补齐所列 named suite 的文档。
- implement 不自主修改测试；按「补覆盖」补 reproduce 用例除外。
- 按「补覆盖」把 reproduce 用例放入 quick 或 smoke 属于授权，不另走测试修改批准。
- converge 修改测试、预期、fixture、跳过规则或任何验证门槛，需用户明确批准并记录理由。
  - deliver 委托时由 converge 执行者按其 confidence 策略裁定并记录。
- code-review 可以依据既定目标和设计自主修复实现与测试；降低验收、改变目标/契约仍需用户确认。
- 非 feature 分支变更 modules.yaml 套件入口或新增 named suite：默认模式需用户确认；
  deliver 委托时由主 Agent 按其 confidence 策略裁定并记录依据。
- 架构优化可以建议；超出当前目标不直接实施。
- 修复后在当前 intent 原地重验。

fact update / fact audit 可独立运行；交付主链在 verify branch 之后、close-out 之前委托。
无 fact stage gate；进度靠 objectives 自勾。独立调用不能因此自动进入 close-out 或其他交付阶段。


### Lint 与复审检查点

本节定义工具检查与主链修复后的进度约束。

- 所有交付在 code-review 前增加 lint checklist 项；具体执行见 references/lint.md。
- 主链 verify 修绿后改了业务内容时，内部委托 1 人增量 code-review；完成后才勾验证项。
- 增量审查修复后重跑原验证范围；内部 smart 不递归开启 loop。具体范围与续办见 references/verify.md。
- reviewer 严格只读；main Agent 收齐报告后核实、复现、修复并落盘证据。
