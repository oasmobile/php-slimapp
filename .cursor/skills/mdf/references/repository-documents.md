# 文档组织与规模

仓库布局与事实元数据见 [仓库契约](repository-contract.md)。

## 文档分类与按需加载

`docs/` 按读者与用途分类；audit 扫描全部 `docs/**` 与根 `README.md`、
`PROJECT.md`、`AGENTS.md`、`GLOSSARY.md`，但只有当前事实按实现对齐。

| 类 | 路径 | 默认加载 |
| --- | --- | --- |
| 用户入口 | 根 `README.md` | 非维护者从这里进；链到 `docs/user-guide/README.md` |
| 文档入口 | `docs/README.md` | 维护者路由页；不是用户入口，也不是工作对象清单 |
| 维护者事实 | `docs/system/`（组成见下） | 地图 → 一份主题叶 |
| 用户事实 | `docs/user-guide/`：`README.md` 路由 + 主题叶；不强制分类目录 | 维护者默认不开；改对外行为时必开 |
| 决策 | `docs/context/adr/` | 只经 `adr-<slug>` 或事实页链接 |
| 工作对象 | `docs/proposals/`、`docs/bugs/`、`docs/JOTS.md` | 只经 ID 或直达链接 |
| 调研与 Wiki | `docs/context/research/`、`docs/repowiki/` | research 按需；Wiki 搜符号 |

- `docs/system/` 组成：`overview.md` 路由；切面目录放主题叶；`deviations.md` 偏差索引；`testing/` 测试约定。
- 切面目录为 `architecture/`、`interfaces/`、`data/`、`operations/`、`testing/`。
  - `testing/` 不是产品运行时切面，也不进入核心模块表或 `manifest.baselines`。

两条加载路径（读者不同，入口不同）：

| 读者 | 路径 |
| --- | --- |
| 用户（非维护者） | 根 `README.md` → `user-guide/README.md` → 一份主题叶 |
| 维护者 / Agent | `AGENTS.md` → `PROJECT.md` → `docs/system/overview.md` |

- 维护者需要按主题找文档或打开工作对象时，再打开 `docs/README.md`，然后只打开一份主题叶或对应 ID 的文件。
- `user_guide` 为 `not_applicable` 时，根 `README.md` 仍是用户入口，改为链到 `PROJECT.md` 或 `docs/system/`。
- grep 与 CodeWiki 只用于定位路径，定位后只读命中的那一份。

**唯一归属**：一条可观察契约只住一页。

| 契约 | 所住页面 |
| --- | --- |
| 对外能力 | `user-guide/<topic>` |
| 内部结构与仍生效约束 | `system/architecture/<topic>` |
| 内部契约与兼容性 | `system/interfaces/<topic>` |
| 部署与观测 | `system/operations/<topic>` |
| 运行时配置 | `system/operations/configuration.md`（超 450 再拆，下四行同） |
| 可观测性 | `system/operations/observability.md` |
| 错误模型 | `system/interfaces/errors.md` |
| 鉴权 | `system/interfaces/auth.md` |
| 限制与恢复 | `system/operations/limits-and-recovery.md` |
| 测试分类、失败语义、skip 与各 suite | `system/testing/<topic>` |

- `system/testing/`：`index.md` 只路由；起步叶为 `conventions.md`，
  主题混杂或超 450 再拆 `kinds.md`、`failure.md`、`suites.md`、`environment.md`。
  - 每个 suite（含 named suite）必须有一节或一页。
- `overview.md` 用核心模块表：五行是配置、可观测性、错误、鉴权、限制与恢复。
  - 每行链到对应五类专用叶或写「不适用：」加理由。
  - 切面路由另链 `testing/index.md`。
- 不预建空页（`testing/` 的 init 起步叶除外）。
- 对外可见行为仍只住 user-guide，只链接。其他页面只链接，不复述。
- 架构问题以 `system/architecture/` 为准，ADR 不作为当前结构来源。

**体积**（物理行；超出为 `size.hard` finding，由 fact-audit CLI 检查）：

| 角色 | 限制 |
| --- | --- |
| 路由页（见下）、`AGENTS.md` 托管块、`PROJECT.md` | 100 |
| 根 `README.md` | 200 |
| `user-guide/`、`system/` 主题叶 | 450 |
| `context/adr/<slug>.md` | 300 |
| Bug | 500 |
| Proposal、`JOTS.md`、HTML、`GLOSSARY.md`、`changes/` 材料 | 不检查 |

- 路由页指 `docs/README.md`、`user-guide/README.md`、`system/overview.md` 与切面 `index.md`。
- 文件拆分先确定设计边界，再验收体积；默认 70% 是拆分后的上限，不作为切割位置。
  - 源代码与 package 可用 module `size_limits` override；文档角色上限及其 70% 拆分要求不受该配置影响。
  - 源代码按职责、模块边界与依赖方向分析，采用适合问题的设计模式；每个结果职责单一、接口清晰。
  - 测试源代码按被测行为、依赖与 fixture 边界组织；不为套用模式引入无必要的抽象。
  - 文档按角色、主题、读者与任务组织，主题叶保持唯一归属，路由页只保留入口与链接。
  - 文件名表达实际职责或主题；不得机械切成 `part1`、`part2`，仅改名也不能替代结构拆分。
  - 合理设计允许迁移入口与调整导出，不强求在原文件或路径保留 facade、re-export 或转发壳。
  - 原文件位置本身不构成兼容性要求；是否保留入口依据明确的对外契约与设计，不因路径变化自动新增兼容层。
  - 迁移入口须同步更新调用方、import、导出、测试、文档与链接，验收设计依据及引用完整性。
  - 验收须说明各结果的职责或主题、边界依据及依赖或导航关系；仅行数达标不能通过。
- 超出限制必须拆页或下沉到主题叶，每个结果不得超过其角色硬限制的 70%，整数向下取整。
  - 上限 100 / 200 / 450 / 300 / 500 行分别对应拆分后 70 / 140 / 315 / 210 / 350 行。
  - 不得用压缩措辞或删除空行代替拆分；审查按改写前内容复核结果。
- 源代码与测试源代码单文件默认最多 1000 行；超限必须拆分，默认每个结果最多 700 行。
  - 实际使用所有适用 module 的 `max_file_lines` 与 `split_percent`，未配置字段沿用默认值。
  - 统一 lint 检查已跟踪的源代码与测试源代码，超限报 `code.size` finding。
  - 不对配置、数据、文档或 lockfile 应用代码行数限制；代码类型按 `code_size.py` 的扩展名识别。
- package 按目录统计直属源文件，实现文件与测试文件分开计数，子 package 独立计数。
  - 每类默认最多 50 个文件；超限按职责、依赖与设计模式拆分，默认每个结果同类最多 35 个。
  - 实际使用适用 module 的 `max_package_files` 与 `split_percent`，逐项满足全部配置。
  - 只统计已跟踪源代码，含 `__init__.py`；配置、数据与文档不计，module `ignore` 命中文件排除。
  - 测试按 `test/`、`tests/`、`__tests__/` 目录，或 `test_*`、`*_test`、`*Test`、`*Tests`、`.test.`、`.spec.` 文件名识别。
  - 同目录混放实现和测试时两类不相加；`src` 与 `tests` 分别统计，不合并到共同父目录。
  - 统一 lint 超限报 `package.size`；全部 module 检查全部 package，smart 对选中 module 触及的 package 统计完整成员。
  - 不得机械切成 `part1`、`part2` 或空壳子包；入口可按合理设计迁移，并同步调用方与文档引用。
- `AGENTS.md` 只检查 MDF 托管块的 100 行硬限制，不对整份文件另设行数 warning。
