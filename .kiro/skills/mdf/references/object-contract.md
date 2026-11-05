# 工作对象与 Change Schema

本文只定义 Proposal、Bug 和 Change 的持久化 schema、允许值与对象间不变量。
创建、评审、状态转换、版本收口和归档的时机与步骤由各工作流定义。

## Proposal

Proposal 字段为 id、type: proposal、status、depends_on。
Markdown 使用 YAML frontmatter，HTML 使用 YAML metadata comment；
评审输出与已有材料的格式边界见 [HTML 工作材料](html-materials.md)。

### milestone

- 可选属性 `milestone` 为单个非空字符串，表示用户确定的阶段归属。
  - 无归属时省略整个字段，不得写 `milestone: null`、空字符串或列表。
  - 同一 milestone 使用相同值；milestone 值不得与对象 ID 同形。
- 不要求独立 milestone 对象；阶段目标及其是否为 MVP 由用户实践决定。
- 不根据组内 PRP 状态自动宣告阶段达成。

### Proposal 状态

状态为 draft、ready、implemented、released、rejected、replaced。

- 正常路径 draft → ready → implemented → released。
  - implemented 表示验收后合入 develop。
    PR mode 允许在源分支准备 implemented 候选状态，合入 develop 后才算实际交付。
  - released 必须记录稳定 SemVer released_in；其他状态不得使用 released_in。
- rejected 必须有 reject-reason: wont-do/obsolete/duplicate。
  - duplicate 还须有 duplicate_of，直接指向同类型的 canonical 非 duplicate PRP，
    不允许自指或重复链。
- replaced 必须有至少两个唯一 replaced_by ID；替代关系不得缺失、自指或成环。
- 不使用持久化 resolution。
- released、rejected、replaced 可以归档，implemented 不归档。

### 依赖

依赖 depends_on 为唯一的直接条目列表，每项为 PRP ID 或已有 milestone 值。

| 依赖项 | 允许 | 已满足 |
| --- | --- | --- |
| PRP | draft、ready、implemented、released | implemented/released |
| milestone | 已有 milestone 值 | 该值下不存在 draft 或 ready PRP |

- ❌ 禁止重复、自指、循环、缺失、跨类型及其他终态。
- ❌ PRP 不得依赖自身所属 milestone。
- 拆分必须同时改写所有原下游 PRP 引用；replaced 不表示依赖已满足。

### ID 与 slug

- 新生成的 Proposal ID 为 `prp-` 加四位随机字符：
  - 前两位为数字，后两位为数字或大写字母，最多包含一个字母；字母排除 `I`、`O`。
  - 数字允许 `0` 至 `9`，包括前导零；例如 `prp-01A2`、`prp-012A`、`prp-0001`。
  - 生成时避开当前 checkout 的 `docs/proposals/`（含 archive）已有 ID 及本批 ID。
  - 本地生成不预占 ID；合入后须校验唯一性，跨 checkout 的重复仍须解决。
  - 新建 Proposal 只能在 planning 工作区分配 ID、写入并提交，再合入 develop。
- 已有数字 Proposal ID（`prp-001` 至 `prp-999`、`prp-1000` 起不补零）继续有效，无需改名。
- Bug 和 Jot 的 ID 仍为前缀后接四位字符，每位取自大写英文（排除 I、O）与数字 0 至 9。
- 📌 沟通、引用与展示时必须写完整 ID，如 `prp-0001`、`bug-C4D5`、`jot-E6F7`、`adr-use-sqlite`。
  - ❌ 不得省略类型前缀或只写序号/短码/slug。
- 文件名 `<PRP ID>-<slug>.md|html` / `bug-<4 位字符>-<slug>.md` 中的 slug 为英文 ASCII kebab-case。
  - active（非 archive）Proposal 与 Bug 的 slug 必须全局唯一。
  - slug 不得与对象 ID 同形（如 `prp-0001`、`bug-c4d5`、`adr-use-sqlite`）。
- 分支命名：
  - 绑定 PRP 的 feature 分支与 `changes/unreleased/<slug>/` 使用 PRP 文件名 slug。
  - 人工 feature 不绑定 PRP；slug 在 start clarify 时由用户确认，Change 使用 `proposals: []`。
  - adhoc 不绑定 PRP；Agent 自行选 slug，Change 使用 `proposals: []`。
  - bugfix 的分支为 `bugfix/<bug-id>`，使用该 Bug 的完整 ID，不使用文件名 slug。

### 关联与正文

- 一般关联只写正文；上述重复与替代字段是明确的结构关系。
- 正文必须含“问题”“期望结果”“范围”“验收标准”四个非空章节。
  - “范围”含“包含”“不包含”非空三级子节。
  - HTML 章节用可见 `h2` / `h3`；不得把正文只保存在 comment 或隐藏元素中。

## Bug

Bug frontmatter 至少包含：

```yaml
id: bug-<4 位字符>
type: bug
status: open
severity: critical | major | trivial
found_in: unreleased | <stable-semver>
```

- Bug 不使用 `depends_on`。一般关联只在正文中说明。
- 正文必须包含“观察到的行为”“期望行为”“复现步骤”“影响”和“所需回归证据”。
- `found_in: unreleased` 表示当前未发布线中的稳定关联；它不是 SemVer。
- `fixed_in` 只接受稳定 SemVer。

### Bug 状态

Bug 的 `status` 只允许 `open`、`fixed`、`closed`、`rejected`。

| 状态 | 含义与约束 |
| --- | --- |
| `open` | 待修复 |
| `fixed` | 已修复、等待独立二次验证 |
| `closed` | 由 bug close 二次验证与修复审查通过后转入 |
| `rejected` | 终态，必须有 `reject-reason` |

- 可在当前 checkout 把 Bug 标为 `fixed`，包括 bugfix、feature、release 或 hotfix 交付。
- release 与 hotfix 上直接修复时不创建 bugfix 分支或 bugfix child Change。
  - 该 Bug 进入版本根 Change 或 hotfix 结果的 `fixed` outcome。
  - 独立修复不写 child Change。
- `reject-reason` 取值：`wont-fix`、`not-a-bug`、`cannot-reproduce`、`obsolete` 或 `duplicate`。
- 非 duplicate 的 `open`、`fixed`、`closed` Bug
  必须有 `critical`、`major` 或 `trivial` 三值 severity。
- `fixed_in` 只允许在 `closed` Bug 中且必填，必须是稳定 SemVer；发版前代表确定的交付目标版本。

duplicate 是被拒绝的 Bug：

```yaml
status: rejected
reject-reason: duplicate
duplicate_of: bug-<canonical>
```

- `duplicate_of` 只能直接指向 canonical、非 duplicate Bug；禁止自指和链式 duplicate。
- duplicate 不需要 `found_in`/`fixed_in`。
  - ❌ 也不得出现在 Change 的 `fixed`、`closed` 或 `deferred` 中。
- canonical 与其 duplicate 子项构成一个 group。

## Change

未版本化的子 Change 位于 `changes/unreleased/<slug>/CHANGE.md`。

- 该目录在 CHANGE.md 出现前即可保存交付身份与材料，包括 `code-review.md`。
- CHANGE.md 是完成后的 Change 记录：

```yaml
change_kind: feature | bugfix | fix | adhoc
source_branch: feature/<slug> | bugfix/<bug-id> | adhoc/<slug> | develop
proposals: [prp-...]
fixed: [bug-...]
closed: [bug-...]
deferred: [bug-...]
adrs: [adr-use-sqlite]
release_notes: none | {Added/Changed/Deprecated/Removed/Fixed/Security: [text]}
breaking: false
evidence:
  tests: []
  commands: []
  artifacts: []
```

- `source_branch: feature/<slug>` / `bugfix/<bug-id>` / `adhoc/<slug>`：独立分支交付；
  feature/bugfix 的目录 slug 必须与分支后缀的 kebab 形式对齐，change_kind 与分支类型一致。
  - adhoc 分支也允许 `change_kind: fix`；两种类型均要求 `proposals: []`。
- 除四类 Gitflow 及 master/main/develop/planning 外的合法分支均归 adhoc，source_branch 保留真实名称。
  - adhoc 材料目录可独立命名；按 source 精确定位，冲突不覆盖；内部角色与 backmerge 仍走所属 workflow。
  - 无账本 adhoc 不要求 delivery/objectives；规范 Change 可独立进入 pr / close-out 与后续 release 聚合。
- `source_branch: develop`：无独立交付分支的直合 Change；目录自选 kebab slug，
  不与分支名对齐；change_kind 允许 feature、bugfix 或 fix；不经 close-out，只由后续 release 作 child 聚合。
- `fix` 表示比 feature、bugfix 更轻的小范围修正，可涉及代码、测试、文档或配置，不要求先建 Bug 或 Proposal。
  - 只用于 develop 直合或 adhoc 交付；独立 worktree 使用现有 adhoc 流程。
- 一个 Bug 只能出现在三个 outcome 列表之一。
  - `closed` 只存 `rejected` Bug 的 ID；拒绝原因由该 Bug 的 `reject-reason` 声明。
  - ❌ duplicate ID 不得出现在任何 outcome 列表。
- `evidence.tests`、`evidence.commands` 与 `evidence.artifacts` 都是列表；
  每个元素必须是非空字符串。
  - 无账本 adhoc 可用 `evidence.range` 固定 base、source_head 与 target_head，值为完整 commit hash。
  - 范围记录不替代实际验收；业务 source_head 与材料提交后的合并 tip 分开。
- 正文必须包含“结果”“已更新的当前文档”和“已知偏差”章节。

## 版本根 Change

`changes/<version>/CHANGE.md` 包含：

- 字段：
  - `change_kind: release|hotfix`、`source_branch`、`version`、`previous_version`；
  - `included_changes`、Proposal/Bug outcomes、release notes、`evidence`、审阅记录。
- 章节：“结果”“包含的 Change”“收口结果”“found-in 转换”、
  “SemVer 决策”“审计”“验证命令”等。
- 📌 每个稳定版本只有一个版本根 Change。
