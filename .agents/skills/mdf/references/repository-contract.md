# 仓库与当前事实文档契约
## 核心术语

- `当前事实文档`：描述当前 checkout 已成立行为的版本化 Markdown 文档。它只能
  陈述可由仓库内 `evidence` 支持的内容，不包含计划、候选方案或工作状态。
- `事实复核`：人基于 `evidence` 判断 `当前事实文档` 是否准确、完整且未将未知
  内容写成事实的语义判断。
- `审阅`：基于`事实复核`的人工语义检查。
- `validation`（契约校验）：对目录、`manifest`、文档结构、链接、对象关系与
  `evidence`执行的确定性检查，输出 findings。它只校验`验证命令`的配置，不执行
  命令，也不替代`事实复核`。
- `evidence`：`当前事实文档` 中指向仓库内已跟踪证据路径的元数据（仅 path）。
- `基线`：`manifest.baselines` 对八项当前状态主题的声明；每项为有证据的文档，
  或带理由的 `not_applicable`。
- `验证命令`：`.mdf/modules.yaml` 中按 module 声明的五个入口：`lint`、`build`；
  以及 `quick`、`smoke`、`release` 三个 suite。repo 级默认按 module **串行展开**；
  可用顶层 `verification` 覆写其中一项或多项为单命令。
- `验证 suite`：test case 的具名集合。全局 suite 由 modules 声明并由 Core 执行；
  named suite 隶属 module，每个 suite 必须有 `docs/system/testing/<name>.md`。
- `module`：`.mdf/modules.yaml` 中的交付单元，含 sourceset、ignore 与分套件命令。
- `initializing`：`manifest.state` 的初始化态，表示初始化尚未完成。
- `ready`：`manifest.state` 的就绪态，表示仓库已完成初始化。
## 固定布局

```text
/
├── README.md                 # 用户入口：项目是干什么 → user-guide
├── .mdf/manifest.yaml
├── .mdf/modules.yaml
├── AGENTS.md
├── PROJECT.md
├── GLOSSARY.md
├── CHANGELOG.md
├── changes/
│   ├── unreleased/<slug>/              # feature/bugfix 材料；release/hotfix 用 <semver>/
│   └── <major.minor.patch>/
│       ├── CHANGE.md
│       └── <slug>/                    # 材料与 CHANGE.md 同级
└── docs/
    ├── README.md             # 文档入口
    ├── JOTS.md
    ├── user-guide/           # 用户事实：README.md 路由 + 主题叶
    ├── system/               # 维护者事实：overview.md + 切面/主题叶 + deviations.md + testing/
    ├── context/
    │   ├── adr/<slug>.md     # 已确认取舍的理由；不是当前事实
    │   └── research/
    ├── repowiki/             # 可选；CodeWiki 受管生成物
    ├── proposals/
    │   ├── prp-<4 位字符>-<slug>.md|html  # draft 用 md；评审定稿生成 html；已有材料保留格式
    │   └── archive/<major.minor>/
    └── bugs/
        ├── bug-<4 位字符>-<slug>.md
        └── archive/<major.minor>/
```

- `docs/README.md` 是文档入口：按要找的主题指向**一份**页面，当前事实排在决策与工作记录之前。
  - 只链接已有内容的页面，空目录不链接；不是 Proposal、Bug 的工作清单。
- 初始化预建工作目录，以 `.gitkeep` 保留空目录。
  - 占位仅建立目录结构，不表示已有工作记录或业务事实。
- `docs/system/testing/` 是必要的测试约定切面：init 写入 `index.md` 与起步叶 `conventions.md`。
  - 它陈述当前验证规则，不承载运行时行为事实。
- 已有项目文档保持原位；同名目录须核对内容和归属，不得覆盖或自动接管。
- ⚠️ `docs/product/`、`docs/adr/` 与根 `docs/testing.md` 不属于当前布局；
  存在即为 `layout.migrate` finding，由 `$mdf migrate` 收敛。
- ⚠️ 缺少 `docs/system/testing/index.md` 或其主题叶时为 `layout.testing` finding。
## 文档分类与按需加载

文档分类、加载路径、唯一归属与体积规则见 [文档组织与规模](repository-documents.md)。

`changes/unreleased/` 保存未版本化的子 Change 及其交付材料。

- 进行中的 feature/adhoc 目录有交付身份即可存在，不必先有 CHANGE.md。
- release 的 `changes/unreleased/<semver>/` 自 start 起即可存在（objectives.md 与 delivery.json）。
  - hotfix 仅 roster ≥1 时写入 delivery.json。
- code-review 终稿写在对应 `changes/unreleased/<slug>/code-review.md`（无 commit
  hash；进行中草稿同路径，收口时覆盖）：
  - feature/bugfix/adhoc 用交付 kebab-case slug；release/hotfix 用该分支稳定 SemVer。
- 📌 每个稳定版本目录始终只有一个根 `CHANGE.md`。

`docs/repowiki/` 存在时，只保存 CodeWiki 生成的仓库结构 Wiki、模块树和增量 metadata。

- 它不是`当前事实文档`、工作上下文或 ADR，不填入`基线`，也不要求 fact frontmatter。
- 该目录由 CodeWiki intent 受管，项目其他文档仍可按各自契约人工维护。

## Jots

`docs/JOTS.md` 是未分诊的随手记录本。每条 Jot 可保留任意 Markdown 正文，尚不属于
Proposal、Bug 或 Change，也不应被当作当前事实或任务清单。

每条 Jot 使用不可变 ID 与成对 marker，以便提升为 Proposal 或 Bug 后可精确删除：

```markdown
<!-- jot: jot-<4 位字符> -->
## <短标题>

<自由正文>
<!-- /jot -->
```

文件可为空，但非空内容必须位于上述条目中。ID 的每一位均独立从大写英文字母
（排除 `I`、`O`）与数字 `2` 至 `9` 中等概率选择。Jot ID 只用于定位和 Git 追溯，
不是工作对象 ID。

## 顶层布局

顶层只保留项目入口、构建或包管理或部署配置、仓库治理文件和 MDF 固定项。
MDF 工作记录统一位于 `docs/`，配置位于 `.mdf/`；`.mdf/logs/` 与 `.mdf/reports/` 是
被忽略的本地日志与报告，保留 7 天。临时工作文件见 [临时工作目录](temporary-work.md)。业务实现与测试按仓库形态分目录：

- 单 module：业务实现归入 `src/`，测试归入 `tests/`。
- 多 module：每个 module 保持可构建单元，业务实现归入 `<module>/src/`，
  测试归入 `<module>/tests/`。module 目录（含各自包清单）属于顶层允许项，
  不得摊平进仓库根 `src/<module>/` 与 `tests/<module>/`。

托管路径的 symlink 检查不递归扫描 `.mdf/logs/`、`.mdf/reports/` 与 `.mdf/tmp/` 内部；
仍检查这三个目录本身；目录本身为 symlink 时仅报 `path.symlink` warning，不阻断任何工作。
日志与报告允许写入链接目录，过期清理跳过链接目录；创建时仍检查父目录和 `.gitignore`。

生成物应归入名称明确的子目录。生态惯例要求其他目录名时，须在 `PROJECT.md`
中说明。

MDF 不自动迁移或删除顶层项目项。`PROJECT.md` 必须记录仅含例外的顶层允许清单、
每项的理由，以及业务实现、测试和生成物的实际目录。

## 文档结构

MDF 生成或管理的全部 Markdown 遵守 `references/doc-structure.md` 的结构规则与
ASD-STE100 写作约定。CLI `fact-audit` 对结构硬限制报 `prose.*` finding。

## 根文档职责

- `README.md` 面向项目用户，说明项目是干什么，并链到用户文档入口（`docs/user-guide/README.md`）。
  - 不写最短可运行路径（住 user-guide 主题叶），不写维护者入口（`AGENTS.md` 已指向 `PROJECT.md`）。
  - 可保留定位性概览，但不重复`当前事实文档`中的用户或系统行为。
  - 环境变量表、接口形状、错误文案等可观察契约只写在对应事实页。
  - ❌ 仅维护者需要的环境、验证、lint、CI、目录例外、发布与仓库治理不得写入，改放 `PROJECT.md`。
  - 内部结构、接口与运维等当前事实按渐进式披露下沉到 `docs/system/` 主题叶。
- `PROJECT.md` 仅面向项目维护者（含 Agent），是读完 `AGENTS.md` 后的第一份项目文档。
  - 记录技术栈、环境、lint、test、build、CI 等价检查、生成物与目录约定。
  - 命令的可执行事实来源始终是仓库配置与脚本。
  - 运行时配置属于 `docs/system/operations/configuration.md`；
    测试分类、失败语义、skip 与各 suite 属于 `docs/system/testing/`。
  - 开头一张验证卡片只列环境要求与 `.mdf/modules.yaml` 的五个验证入口。
    - 默认按 module 串行；不列 named suite 或单个测试的命令。
    - 须含 `docs/system/overview.md`、`docs/README.md` 与
      `docs/system/testing/index.md`，不展开核心模块表。
  - 接口、数据与运行时行为不复述 `docs/system/` 事实页。
  - 超过体积限制时下沉到 `docs/system/`，不扩写进 `README.md`。
- `AGENTS.md` 仅面向在仓库中工作的 Agent。
  - MDF 托管区块必须项目无关：Agent 默认按维护者角色工作，第一跳是 `PROJECT.md`；
    再打开 `docs/system/overview.md`，或从 `docs/README.md` 只打开一份主题叶。
  - 用 grep/CodeWiki 定位后只读命中的那一份。
  - 根 `README.md` 与 `docs/user-guide/` 是用户入口，不是 Agent 默认起点。
  - `README.md` 只用于项目定位，`GLOSSARY.md` 用于领域术语；不通读文档目录，不把根文档当作行为事实来源。
  - 不要求写项目例外；托管块外若写入栈、配置或行为契约，fact audit 记 `agents.project_content`。
  - MDF 只维护其中带 marker 的区块，其余内容由仓库维护者负责。
- `GLOSSARY.md` 面向所有读者维护稳定的领域词典，包括术语、同义词和易混淆概念；
  不记录实现细节、计划或工作状态。

## 模板映射

| 模板                                | 用途                             |
| ----------------------------------- | -------------------------------- |
| `manifest.yaml`                     | `.mdf/manifest.yaml` scaffold    |
| `glossary.md`                       | `GLOSSARY.md`                    |
| `project.md`                        | `PROJECT.md`                     |
| `agents-managed-block.md`           | `AGENTS.md` MDF marker           |
| `docs-readme.md`                   | `docs/README.md` 文档入口        |
| `jots.md`                           | `docs/JOTS.md` 草稿本                 |
| `changelog.md`                      | `CHANGELOG.md`                   |
| `user-guide-readme.md`              | `docs/user-guide/README.md` 路由 |
| `user-guide-topic.md` / `system-*`  | `当前事实文档`主题叶             |
| `system-configuration.md` 等五类专用叶 | fact update 建页时用，init 不落地 |
| `system-testing-index.md` / `system-testing-conventions.md` | init 写入 `testing/` |
| `system-testing.md` | testing 主题叶拆页时用 |
| `adr.md`                            | `docs/context/adr/<slug>.md`     |
| `proposal.md`                       | Proposal                      |
| `bug.md`                            | Bug                              |
| `change.md`                         | unreleased 子 Change             |

## Manifest

可选 [start hook](hooks/post-gitflow-start.md) 与 [close-out hook](hooks/pre-gitflow-finish.md)。
可选 `rules.design` 与 `rules.code-review` 指向项目 rule 文件；只接受 rule，不接受 command。
加载、project 优先的 merge、完整分派与续办证据见 [项目阶段 rule 契约](project-rules.md)。

Manifest 控制面可选 `logo`：横幅 emoji 字符串；缺省、`null` 或空字符串用 `📍`，init 保留配置。

- `schema_version` 必须为 `3`；`versioning.latest_release` 只能是稳定 SemVer 或 `null`，`unreleased` 不是版本线值。
- 八项`基线`键为 `glossary`、`user_guide`、`system_boundary`、`architecture`；
  以及 `interfaces`、`data`、`operations`、`deviations`。
  - `user_guide` 默认路径 `docs/user-guide/README.md`，其余 system 基线默认指向对应切面的路由页。
- 验证命令**不在** manifest；写在 `.mdf/modules.yaml`。manifest 若仍含 `verification`
  报 `manifest.verification_moved`，由 `$mdf migrate` 收敛。
- `implementation_roots` 是非空、互不重叠的仓库相对目录列表。
  - 每个目录必须存在、不为符号链接且位于仓库内；`fact audit` 只覆盖其中 Git 跟踪的常规文件。
  - 单 module 通常为 `[src]`；多 module 列出各 `<module>/src`。

## Modules

配置、ignore 范围、规模 override 与 coverage 见 [Module 配置](modules.md)。

## YAML 子集

Core 用内置解析器（`scripts/mdf_core/foundation/yamlutil.py`）解析 `manifest` 与全部 MDF 文档 frontmatter，
不依赖 PyYAML。只支持以下子集，写法不要超出：

- 空格缩进的映射与 `- ` 列表；缩进含 tab 报 `invalid_yaml`。
- `key:` 后无值表示嵌套映射或列表（由下一行是否为 `- `
  决定），不是 null；要写 null 必须显式写 `null` 或 `~`。
- 标量：
  - `null`/`~` 解析为 null；`true/yes/on` 与 `false/no/off`（大小写不敏感）解析为布尔。
  - 纯整数解析为数字；`{}` 为空映射；`[a, b]` 为 flow list，元素递归按标量解析。
  - 单双引号字符串去引号（双引号支持 `\\` 与 `\"` 转义）；其余内容原样保留为字符串。
- 井号前有空格或 tab 的 `#` 起为行内注释；引号内的 `#` 不算注释。
- ❌ 不支持 block scalar（`|`、`>`）、多行字符串、锚点与别名；多行内容用列表或多个字段表达。

Core 按解析后的 `status` 与 `found_in` 判断。因此 `status: "ready" # note` 和
`found_in: 'unreleased' # note` 与裸值语义相同；Core 写回这些字段时使用规范裸值。

## 当前事实文档

一个 Git 仓库只对应一个 MDF 当前上下文和一条版本线。

- `docs/user-guide/` 与 `docs/system/` 页面表达当前 checkout 的实际行为；
  用代码、配置、schema、测试或生成物作为 `evidence`。
- ❌ 计划、Proposal、Bug 和 Change 不得冒充`当前事实文档`。
- `docs/user-guide/**` 的 `doc_type` 为 `user-guide`；`docs/system/` 按切面目录取 `system-*` 类型。
- 每份主题叶独立可加载：正文自洽描述该主题的输入、输出、错误与不变量，不要求先读其他页面。
  - 但不复述其他页已归属的契约（见「唯一归属」）。
- `overview.md`、`user-guide/README.md` 与切面 `index.md` 等路由页只做路由与边界。
  - 不复述叶子页的契约，也不为整个子系统集中承担 evidence。
- 正文面向工作中的读者描述可观察行为。
  - 「代码在哪里」由 `docs/repowiki/` 或短路径列表承担，不写逐文件 walkthrough。
- `user_guide` 基线为 `not_applicable` 时（如无终端用户面的后端），`docs/README.md` 不展示 user-guide；
  并写明行为参考面是 `docs/system/` 对应页面。

## 工作上下文

`docs/context/` 不属于 SSOT，不填入`基线`，也不要求 fact frontmatter。
`docs/context/research/` 保存本地或外部调研报告、候选方案和对比。`intake` 的来源只用于
本次分诊，不保存为工作上下文。已确认的长期取舍写入 `docs/context/adr/`；实现后的
当前行为另写 `user-guide` 或 `system` `当前事实文档`。

## ADR

`docs/context/adr/` 保存已确认的长期取舍：问题、备选、为何选、被推翻的历史。
它不是`当前事实文档`，不填入`基线`，不描述「现在系统长什么样」；仍生效的约束与
后果写入 `docs/system/architecture/` 主题叶，ADR 只留理由并链接过去。按主题打开
单份，不顺序通读；ADR 复述当前结构，或某条仍生效约束只存在于 ADR，都是 audit 的
语义 finding。

文件名为 `<slug>.md`，frontmatter `id` 必须为 `adr-<slug>`。slug 为英文 ASCII
kebab-case，须含字母、不得为纯数字序号，且不得与对象 ID 同形。accepted 之后
slug 不可改；推翻该取舍时将旧记录标为 superseded，并另写新主题文件。status 为
accepted、superseded 或 deprecated。沟通时写完整 ID，如 `adr-use-sqlite`。

## Fact frontmatter：evidence 与 generated

每个`当前事实文档`至少声明一条 `evidence`，仅为 path 列表：

```yaml
evidence:
  - "<repo-relative-path>"
# 或
evidence:
  - path: "<repo-relative-path>"
```

- `evidence` 路径必须仓库相对、存在且被 Git 跟踪。
- ❌ 不再在 evidence 上声明 `verification`；怎么验归 `.mdf/modules.yaml` 的套件与 `$mdf verify`。
- `strict validation` 下 `evidence` 在文档之后变更会报 `evidence.stale`。
- ❌ 发版流程会改写的记录不能作为 evidence（`evidence.record`）：
  `.mdf/manifest.yaml`、`CHANGELOG.md`、`docs/JOTS.md`；`changes/**`、`docs/proposals/**`、`docs/bugs/**`。
- evidence 为另一份当前事实文档时只核对存在与已跟踪，不比较提交先后。
- 过期只相对实现、测试、配置等非事实文件判定，同一次提交中的文件互不算「晚于」。
- 无需为消除 warning 把不承载行为的文件写入 evidence；用适用范围内的 `ignore` 排除。

由脚本生成的文档额外声明 `generated`：

```yaml
generated:
  source: "<repo-relative-source>"
  generator: "<repo-relative-executable>"
```

- `source` 必须是仓库内存在且被跟踪的文件；`generator` 必须是仓库内可执行文件。
- `strict validation` 校验这些元数据及 Git 陈旧性。
  - 但不复制仓库、不运行 generator，也不自动比较生成内容；内容一致性属于`事实复核`。
- 模板见 `assets/templates/generated-fact.md`。

## CHANGELOG

根 `CHANGELOG.md` 只列稳定版本，不含 Unreleased 章节。版本目录的根 `CHANGE.md`
记录该版本的结果、outcome、found-in 转换、SemVer 和审阅结果；CHANGELOG 只做读者索引。
