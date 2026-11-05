# lint

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check                          │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 前置已确认
┌──────────────────────────────────┐
│ 2 Run                            │
└────────────────┬─────────────────┘
                 │
                 ├──── 缺报告或无法核验 ────→ [停止并报告]
                 │
                 ▼ 命令已执行，含非零结果
┌──────────────────────────────────┐
│ 3 Assess                         │
└────────────────┬─────────────────┘
                 │
                 ├──── deliver 授权内可修 ───────────→ 2 Run（修复后）
                 ├──── 未通过且不可修/无修复授权 ────→ [报告失败并结束]
                 │
                 ▼ 全部工具通过
┌──────────────────────────────────┐
│ 4 Record                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 记录或提交失败 ────→ [保留现场并报告]
                 └──── 成功 ──────────────→ [返回调用方]
```

## 工作流（唯一执行契约）

读取 `references/common.md`、`references/delivery-contract.md` 与 `references/repository-contract.md`。
本 intent 使用全部 module 的统一 lint 入口，检查代码规模及项目配置的工具规则。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check | 约束 | 核对 ready、范围与适用开发前置 | Git 根、module、适用 objectives | 2 | 停止并报告 |
| 2 | Run | 脚本 | 运行全部 module 的 lint，读取退出状态与报告 | 工具结果、完整日志 | 成败均 3 | 报告缺失或无法核验则停止 |
| 3 | Assess | 约束 | 核对工具结果；deliver 授权内修复后重跑 | findings、授权、修复或失败说明 | 通过 4；可修且已修 2 | 未通过且不可修/无授权则报告失败 |
| 4 | Record | 约束 | 返回报告；交付内勾选 lint 并提交 | 报告路径、适用勾选与提交 | 返回调用方 | 保留现场并报告 |

## 术语与数据结构

### 范围与前置

本节确定独立检查与交付主链的执行边界。

- 调用 `$mdf lint`，不接受额外参数；先解析当前目标 Git 根。
- 交付主链在 converge 之后、code-review 之前执行；无 converge 的人工 feature、adhoc 在工作完成后执行。
- 普通交付须已勾 converge；人工 feature 须用户显式勾人工工作；有账本 adhoc 须已勾工作。
- 无账本 adhoc 按 adhoc-change 的实际范围运行，不调用 delivery status 或创建 objectives；报告返回调用方。
- 无交付身份时检查当前 Git 根，不创建 objectives；有交付上下文时先用 delivery status 解析并绑定 owner。
- qa/dev 路径不作为交付 lint 的落盘位置；按 common 的工作区规则返回 owner，再核对对应前置。
- 独立调用只检查并保存报告，不修改源码；deliver 委托时，步骤 3 可在已有授权范围内修复后重跑。
- 步骤 2 非零但有完整工具结果时仍进入 3；无法读取报告时停止，不把缺证据视为通过。
- 工具失败不得以 LLM 判断豁免；不得降低阈值求绿。未通过时不勾选 lint，不进入 code-review。

### 执行与结果

本节定义唯一工具入口及代码、文档检查的边界。

```bash
python3 "$MDF_ROOT/scripts/mdf.py" verify --repo "$REPO_ROOT" --scope named --suites lint
```

- 每个 lint 入口都包含 MDF 内置代码规模检查与项目 lint command；任一失败则该入口失败。
- 代码文件行数、package 文件数沿用 module 的 sourceset、ignore、size_limits；package 检查完整同类成员。
- standalone lint 与 branch 检查全部 module；smart 只检查所选 module 及其触及 package。
- 文档长度、结构与事实一致性留在 fact audit；代码拆分的职责与设计合理性留在 code-review。
- jscpd 等第三方扫描器由项目自行选择、安装并接入 lint command；MDF 不要求启用。
- 阈值由内置规则或项目工具配置确定；保留各入口的原始日志、summary 与 findings。
- 全部通过后，交付内勾选 objectives 的 lint 项并提交；独立检查只返回结果与报告路径。


### 审查只读测量

本节为拆分比例提供工具证据，不增加主链步骤，也不替代 lint、smart 或 branch 验证。

```bash
python3 -B "$MDF_ROOT/scripts/measure_code.py" --repo "$REPO_ROOT" \
  --ref <本轮左端点或审查/修复终点> --path <文件或目录> [--path <另一文件或目录>] \
  [--file-target <原文件拆分目标>] [--package-target <原package拆分目标>]
```

- main Agent 在分派审查前及修复后调用；命令由 Core run 留日志，完整 stdout JSON 作为只读资料交给 reviewer。
- 不传 ref 时读取工作区源码，传 ref 时仅读取 Git 对象；策略默认读取当前已确认 modules.yaml。
- 候选拆分、目录迁移或 size_limits 变更时，先以原工具数据或 --policy-ref <已知策略快照> 确认原触发目标；
  只用当前契约解析该 modules.yaml，缺失或不兼容即失败，不探测、转换或兼容旧格式。

- 工具只读源码、Git 与配置，不生成文件或 cache，不执行项目 linter、tests 或验证入口。
- files 的 value 是物理行数；packages 的 value 是完整同类直属文件数，tests 区分实现与测试。
- 每项包含 module、limit、split_target、within_limit 与 within_split_target；ignore 沿用 module 的适用范围。
- 退出 0 只表示数据采集成功。硬限制是否通过看 within_limit；本轮超限拆分另核原目标。
- 在修改目录或配置前保存原超限对象的工具数据；只取原报告 within_limit: false 的触发项 split_target，不使用 limit 冒充拆分目标。
- 文件拆分用 --file-target，package 拆分用 --package-target；每个原触发目标各传一次，不从迁移后的新策略推回原目标。
- 传入目标后，工具输出 required_split_targets 与 within_required_split_targets；对应拆分结果必须为 true。
- 只对原对象的拆分结果及对应实现/测试类别应用原目标，同时满足新位置硬限制；未触发拆分不强套比例目标。
- 原目标调整按既有验收变更规则确认；不得仅改路径或目标数据来求绿。没有匹配源码不代表已满足拆分要求。

- 数据引用保存工具命令与日志路径；Git 标识只留工具日志或进行中稿，终稿不复制 commit hash。
- 工具失败或适用结果缺数据时停止本项验收，保留限制说明，不编造测量值。
