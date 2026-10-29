# Migrate

它接入已有项目或调整现有 MDF 配置，将既有材料收敛到当前结构，
经`当前事实文档`的事实复核后使 `manifest` 进入 `ready`。
接受 `$mdf init migrate` 或 `$mdf migrate` 显式调用，或 init 依据公共分流规则的内部委托。
新项目停止并提示 `$mdf bootstrap`。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check entry                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 未就绪、无事实且符合契约 ────→ [停止并提示 bootstrap]
                 ├──── 边界不明 ────────────────────→ [澄清后返回 1]
                 ├──── 其他异常 ────────────────────→ [停止并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Inventory                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 无法分类 ────→ [澄清后返回 2]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Clarify layout                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 无法分类 ────→ 2 Inventory
                 ├──── 未解决 ──────→ 3 Clarify layout
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 4 Confirm plan                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 分类变化 ────────→ 2 Inventory
                 ├──── 其他方案变化 ────→ 3 Clarify layout
                 ├──── 未确认 ──────────→ 4 Confirm plan
                 │
                 ▼ 用户确认
┌──────────────────────────────────┐
│ 5 Initialize                     │
└────────────────┬─────────────────┘
                 │
                 ├──── 新 finding ────→ 2 Inventory
                 ├──── 失败/缺失 ─────→ [保留现场，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 6 Audit facts                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 审阅或校验未通过且可修复 ────→ 6 Audit facts
                 ├──── 无法继续 ────────────────────→ [保留现场并报告]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 7 Enable workflows               │
└────────────────┬─────────────────┘
                 │
                 ├──── 需补验或事实变化 ────→ 6 Audit facts
                 ├──── 未确认 ──────────────→ [保持 initializing，结束]
                 ├──── 其他失败 ────────────→ [保留现场，停止]
                 └──── 通过 ────────────────→ [结束]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

- 完整读取以下文档：
  - `references/initialization.md`、`references/common.md`
  - `references/clarify.md` 与 `references/repository-contract.md`
- 接受用户显式调用 `$mdf init migrate` 或 `$mdf migrate`，或 init 依据公共分流规则的
  内部委托；复用已确认信息，不重复提问。
- 步骤 6 读取并内部委托 `references/fact-audit.md`。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check entry | 约束 | 只读判定分流 | 边界、事实、MDF 状态 | 2 | 不明回 1；无事实且符合契约提示 bootstrap；其他停 |
| 2 | Inventory | 约束 | 盘点全部顶层项、文档与 finding，按职责分类 | 分类与 finding 清单 | 3 | 无法分类则澄清后回 2 |
| 3 | Clarify layout | 约束 | 确认配置并处置 finding | 逐项决定、完整配置 | 4 | 无法分类回 2；否则留 3 |
| 4 | Confirm plan | 约束 | 展示源、目标、保留内容与初始化方案并确认 | 用户明确确认 | 5 | 未确认留在 4；分类 2；其他 3 |
| 5 | Initialize | 约束 | 调用 #2+#4：init、归位并提交 | 归位表、根文档、提交 | 6 | 新 finding 回 2；否则停 |
| 6 | Audit facts | 约束 | 比较事实；审阅后 initialization #5 校验 | 事实复核、仅允许项 | 7 | 可修复则重验；否则停 |
| 7 | Enable workflows | 约束 | initialization #6-8 | 确认、校验、提交 | 结束 | 补验或事实变化 6；未确认则结束；否则停 |

## 术语与数据结构

### 入口与盘点

<a id="s1"></a>

**入口**

先按 `initialization.md` 只读确认项目边界、新旧与 MDF 状态。

- 未就绪、没有事实且符合当前契约时停止，列依据并提示 `$mdf bootstrap`（或 `$mdf init`）。
  - 提示前不写入 `.git/`。
- 已 ready 的空仓库仍在 migrate 调整配置。
- MDF 内容不符合当前契约时，即使尚无业务事实也继续 migrate。
- 入口一律运行 doctor，不要求已是 Git 根，也不要求已有 manifest；finding 记入盘点。
- 没有 manifest 时 doctor 只报布局 finding。`layout.migrate` 继续 migrate，不提示 bootstrap。
- 不因普通目录、无提交或 dirty 一概拒绝。
- doctor finding 不是拒绝理由：本 intent 正是收敛这些 finding。
  - 全部 finding 记入盘点清单，由步骤 3 逐项处置。
  - 如 `manifest.schema`、`layout.migrate`、`manifest.verification` 由步骤 3 决定目录去处并重写 manifest。

验收：明确项目根与判定依据；doctor finding 已全部记入盘点，无 migrate 无法安全处理的状态。

异常与交接：

- 边界或改动归属不明时澄清。
- migrate 无法读取或安全处理的状态（如非本地产物目录的纳管路径 `path.symlink`）报告后停止。
- 中间反馈继续本次流程，不重查入口。

<a id="s2"></a>

**盘点**

盘点全部顶层项目项并检查项目原有的全部文档，区分 MDF 固定项、治理/生态入口、实现、测试、
生成物与文档；登记入口 doctor 的全部 finding。

可选加速（见 `common.md`「Jev 可选加速」）：

- 时机：材料已列全、写定分类清单前；tool 可用时。
- 调用：对每个待分类项 `choice`，或一次 `run` 多题。
- state：路径、职责摘要与 doctor finding 摘录。
- 选项键见下表；采信后写入同结构分类清单。
- `ask` 或未采信走主 Agent，必要时澄清后回 2。
- 路径职责已由契约或 doctor 明确时 ❌ 不调。
- ❌ 不替代步骤 3–4 的去处澄清与用户确认，不因 Jev 移动或删除。

| 键 | 含义 |
| --- | --- |
| `mdf_fixed` | MDF 固定项 |
| `governance` | 治理或生态入口、构建配置 |
| `implementation` | 业务实现 |
| `tests` | 测试 |
| `generated` | 生成物 |
| `user_guide` | → `docs/user-guide/` |
| `system` | → `docs/system/` 对应切面 |
| `adr` | → `docs/context/adr/` |
| `research` | → `docs/context/research/` |
| `repowiki` | 符合 CodeWiki 契约，留原处 |
| `exception` | 顶层或布局例外，方案单列 |
| `ask` | 无法定型 |

验收：分类清单与 finding 清单。

异常与交接：

- 无法分类时澄清后回到 2。
- 不得仅凭目录名或 README 保留。
- 符合 CodeWiki 契约的 `docs/repowiki/` 留在原处且不纳入当前事实、ADR 或调研分类。
- 此步骤不做`事实复核`。

### 配置与确认方案

<a id="s3"></a>

**布局**

使用内部 clarify intent，议题为材料去处、顶层例外、基线与验证。

- 盘点中的每项 doctor finding 在方案中写明处置。
- 确认非生态必需且非 MDF 固定顶层目录的去处或顶层例外。
- 调研与决策材料：
  - 本地或外部调研材料归入 `docs/context/research/`。
  - 已确认决策归入 `docs/context/adr/`。
- 从仓库证据收敛八项 `基线`、最近稳定版本与 `verification` 的五个入口。
- `docs/` 内材料按 `repository-documents.md`「文档分类与按需加载」归位：
  - 面向使用者的页面进 `docs/user-guide/`（`README.md` 只路由，主题各一页）。
  - 边界、架构、接口、数据、运维进 `docs/system/` 对应切面的主题叶。
  - 测试约定进 `docs/system/testing/`（已有根 `docs/testing.md` 则迁入该切面）。
  - 缺 `index.md` 或主题叶时按模板补齐并按仓库证据填写。
  - `overview.md` 核心模块表按已有材料填链接或「不适用」，不批量创建空主题叶。
  - 仍生效的架构约束从 ADR 抽到 `docs/system/architecture/`，ADR 只留理由。
  - `docs/product/`、`docs/adr/` 等不属于当前布局的目录在方案中列出逐文件去处，
    落地后不得残留。
- manifest 字段：
  - `baselines` 键与路径按当前契约重写（含 `user_guide`），`schema_version` 写为当前值。
  - 不符合当前形状的 `verification`（如 `commands` 列表、`suites` 映射）：
    - 按 `delivery-contract.md`「验证 suite」重新归入 lint、build、quick、smoke、release。
  - 原 named 分组只写进 `docs/system/testing/`，不写回 manifest。
- 既有运行时 skip、提前返回或 xfail 在方案中逐个列出处置，经用户确认后落地。
  - 处置为按依赖拆分 test case、移出 suite 或登记 Bug。
- 📌 quick、smoke、release 必须是把 JUnit XML 写进 `$MDF_REPORT_DIR` 的真实运行器命令：
  - 既有 suite 命令未产出报告时，在方案中写明为其运行器增加以下两项：
    - JUnit 输出（如 pytest `--junitxml`、PHPUnit `--log-junit`、Vitest `--reporter=junit`、
      Jest `jest-junit`）
    - test case 分组配置（`classname` 对应 test case）。

验收：逐项决定、finding 处置与验证命令。

异常与交接：

- 无法分类时回到 2。其他未解决留在 3 澄清。
- 仅含 `.gitkeep` 的占位目录按其未来职责迁移。
  - 迁移目标已有实际内容时，在同一方案中移除 `.gitkeep`，否则保留。
- 单 module 的业务实现与测试建议迁入 `src/` 与 `tests/`。
- 多 module 建议迁入或保留 `<module>/src/` 与 `<module>/tests/`，
  不得摊平为仓库根 `src/<module>/` 与 `tests/<module>/`。
- ❌ 不得在未经确认时迁移或删除。
- 已接入 MDF 但暂无业务检查时 lint、build 可用 `git diff --check`。
- 从未发布时最近稳定版本为 `none`。

<a id="s4"></a>

**方案**

形成`初始化方案`：路径、材料去处、保留内容、顶层允许清单、实现/测试目录、
拟补字段、基线、验证命令与预期 `validation`。

验收：用户明确确认。

异常与交接：

- 用户尚未确认且方案未改时留在 4。
- 材料分类有误时回到 2；去处、基线或验证命令需调整时回到 3。
- 移动/删除必须列出源、目标和无信息损失理由，且不得覆盖既有内容。
- 不处理待实现意图；完成后用户可按输入形态显式
  `$mdf intake` 或 `$mdf bug create` 或 `$mdf prp create`。
- 本次完成后的配置调整须再次显式调用 `$mdf init migrate`、`$mdf migrate` 或 `$mdf init`。

### 落地与启用

<a id="s5"></a>

**落地**

- 执行 `init` 建立或更新完整 scaffold 前，按 `initialization.md` 段 2
  依已确认方案准备 Git 基础并运行 doctor。
- 按 `initialization.md` 段 4 调用 `init` CLI，保持 manifest `initializing`，
  传入核对后的完整配置与验证命令。
- 只按方案归位/保留/排除原材料与顶层项。
- 配置更新保留未要求修改的字段，续办核对已有产物，不覆盖重建。
- 完成材料后创建本地阶段提交，再审阅事实。

验收：

- 固定布局、完整归位核对表。
- `README.md`、`PROJECT.md`、`AGENTS.md` 与 `GLOSSARY.md` 各自符合`根文档职责`且入口可达。
- 没有未说明的遗留文件。

异常与交接：

- 新 finding（盘点清单里没有的）回到步骤 2，不在本步补记。
- 其余失败保留现场与 findings，不自动回退；停止并报告。
- 项目原有文档与经确认迁移的顶层项目项只可按方案归位、保留或排除。
- 保留 `AGENTS.md` 非 MDF 托管块。
- 完成当前事实文档、ADR、`README.md`、`PROJECT.md` 与验证命令。
- 在 `PROJECT.md` 记录仅含例外的顶层允许清单与目录约定。
- 方案调整仓库结构时，审视 `README.md` 的用户/维护入口、`PROJECT.md` 的维护手册
  与当前事实文档，消除重复。
  - 此后新增或更新文档时保持该分工，根文档不复述当前事实页的契约。

<a id="s6"></a>

**审阅**

- 步骤 5 的阶段提交就是审阅基线。本步不再另做一次提交。
- 比较调用前后的 `GLOSSARY.md`、`docs/user-guide/**`、`docs/system/**` 与 `docs/context/adr/**`。
- 内部委托 `fact audit` 执行`全量审阅`（`--scope full`），审的是已提交内容。
- 按 `initialization.md` 段 5 核对 strict validation；同次 fact audit 已校验且内容未变时复用结果。
- 审阅发现问题时修正、提交并重验，不要求用户手动 commit 后重调。

验收：事实复核、diff 与 strict validation；仅允许 `manifest.initializing` finding。

通过条件：审阅与校验通过后进入 7。

异常与交接：

- 未确认的语义问题继续澄清。
- 其他 finding 修正后重验，同一项两轮后仍在则无法继续。
- 无法继续时保留现场并报告。
- 提交不替代事实复核或用户确认。

<a id="s7"></a>

**就绪**

1. 按 `initialization.md` 的公共完成规则展示当前事实复核、八项基线、验证命令和分支方案。
2. 按 initialization 段 6 询问是否启用，依 `SKILL.md`「用户确认」接受 yes 等明确肯定答复后收口。
   核对增量、改 ready、校验并提交，再核对本地 master/develop。

验收：事实审阅与 strict validation 仍有效，启用增量校验零 finding、就绪结果已提交、本地分支可用。

异常与交接：

- initialization 返回需补验或事实变化时回到 6，保留有效确认，只补缺失或失效的审阅与校验。
  仅修改 manifest.state 与本次启用记录不触发补审，沿用 initialization 段 7 的结果复用规则。
- 用户未确认启用则保持 initializing 并结束，不写 ready。
- 其他失败保留现场并报告，未通过不得宣称完成。
