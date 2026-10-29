# MDF 公共意图规则

树形：not-tree。调用事件与当前证据决定适用约束，不重新执行调用方的业务阶段。

## 工作流（唯一执行契约）

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve context | 约束 | 确认调用方、当前步骤与适用事件 | 调用上下文与事件 | 2 | 缺上下文则返回缺项，不猜测 |
| 2 | Apply rules | 约束 | 核对适用规则、前置证据与边界 | 命令、产物与检查记录 | 3 | 不符或缺证据则返回失败 |
| 3 | Return | 约束 | 返回检查结论，继续调用方当前步骤 | 可追溯结论与缺项 | 返回调用方 | 缺项返回失败，不推进业务阶段 |

## 术语与数据结构

适用事件包括：CLI、目标根、工作区、写入、反馈、日志、提交或可选判断事件。仅读取条款不触发其中描述的其他 intent。

由调用方读取；这些规则按事件持续适用，不是依次执行的阶段。
进入 intent、收到反馈、调用 CLI、写入失败或提交时应用对应规则；
返回调用方不解除其他适用约束，完成后继续调用方当前步骤。
upgrade 不读取本文件。

### 工具

需要确定性操作时使用 `python3 "$MDF_ROOT/scripts/mdf.py"`，语义判断留给 intent。

每次 CLI 调用记录实际命令、输入、退出状态与结构化结果，并按当前步骤检查预期产物。
除 intent 明确声明的例外外，非零退出或产物缺失均走该步骤的失败去向，不以摘要代替检查。

验收：CLI 调用、产物检查与 intent 判断各自可追溯。非零退出或产物缺失走该步失败去向。
「异常」仅指禁止用 CLI 模拟语义判断；此时停止，不另走失败去向。

- 存在 deliver 外层上下文时，读取并继承 `references/deliver-policy.md`，不新开 deliver 工作流。
  - 每次委托（含嵌套 intent / subagent）前检查 until；被排除就逐层返回截止点，不继续子流程。
  - 每项新 decision 按同一 confidence 策略处理；低分交回外层步骤 6，确认后 resume 原位置。
  - CLI 内部操作不是独立 intent；不把一次已授权的确定性命令拆开来模拟新的截止点。

- intent 要求正常流程可用时，以 `doctor` 的 `normal_workflows_allowed` 为准。
  - `evidence.stale`、`generated.stale` 只报告，不单独阻断正常流程。
  - `severity: warning` 的 finding 仅报告，不阻断任何工作；验收中的零 finding 要求仅计 error。
  - 其他 findings 与各操作的 clean 要求仍按原规则处理。
  - `validate full` 与 fact audit 仍严格检查 stale，不因此放宽验收。

### 执行进度

适用于读取本文件的 intent；进度播报描述执行现场，不替代 objectives、证据或验收。

- 开始执行时说明当前 intent、scope（适用时）与第一步；进入每个工作流步骤前播报阶段。
- 先列出工作流的固定阶段总数与完整清单；每次播报保留最外层 intent、当前阶段 i/N 与阶段名。
  - 阶段数表示流程位置，不表示耗时百分比；分支跳过的阶段标为无需执行。
  - 局部 n/m 必须标明统计对象与所属阶段；范围确定后先列出有多少个计数组、各组总量及执行顺序或并行关系。
  - 尚未扫描的计数组数量或总量标为待确定；扫描后补齐，新增或取消计数组时说明数量变化与原因。
  - 委托 intent、CLI、单页 evidence 是当前阶段的子任务，保留父阶段并标明子阶段或路径，不另起全局进度。
  - 局部 n/n 仅表示该组结束；报告下一组与剩余阶段，最外层全部完成后才报告整体完成。
- 局部计数组使用本次执行内稳定且唯一的组编号；全局与子阶段 i/N 不另计为局部组。
  - 先登记已知组，列出编号、名称与已知总量；未知子组明确标为待扫描，已登记总数不是最终总数。
  - 每条局部进度显示 `组 G：名称 n/m`，同时汇总 `共 K 组｜完成 D｜运行 R｜待开始 P`。
  - 并行时列出所有运行中的组编号；剩余未结束为运行中与待开始之和，不用当前编号推算剩余。
  - 跳过与中断另列数量；各状态数量之和必须等于已登记总组数，跳过与中断不计完成。
  - 扫描新增组只追加编号，保留已有编号与状态，并报告总组数的前后变化及新增清单。
  - 委托 CLI 的本地组编号映射到父级组清单；重复调用、重审与返工按新的执行实例追加组，不清零已有完成数。
- 完成阶段时简述已核实的结果与下一步；连续短步骤可合并，避免逐条复述工具输出。
- 长阶段在可取得中间结果时至少每 60 秒更新一次，说明已处理范围、当前工作与剩余项。
  - 单次工具调用尚未返回时不虚构进展；可等待输出的工具使用有限等待，返回后及时播报。
- 重审或返工说明轮次和原因；阻断时说明停在哪一步与缺项，不声称完成。
- CLI 的 stderr 进度与最终 JSON 一同读取；stdout 保持 JSON，进度不作为通过依据。

### Jev 可选加速

<a id="s-jev"></a>

#### 角色

- MCP tool：`choice` / `noul` / `score` / `run`，只加速「选项已知」的定型判断。
- 无 Jev 时主 Agent 路径与未引入前完全一致；deliver 的 decision 仍由主 Agent 评分并遵守 confidence 阈值。
- Jev 缺失本身不阻塞流程；deliver fallback 评分仍低于阈值时按其策略请求用户确认。
- ❌ 不是硬依赖，不是 gate。
- ❌ 不替代生成或确定性 CLI；普通 intent 不替代用户确认或 clarify。
  deliver 的 decision 评分与确认边界以 `references/deliver.md`「自动裁定与 confidence」为准。

#### 文档与执行顺序

1. 先按该步骤完整主 Agent 规则准备材料并写清分支。
2. 仅当本步声明「可选加速」、会话未记 `jev=unavailable`、且 tool 列表含上列
   之一时，才做业务调用。
   - 禁止空探测。
   - 禁止推理「要不要用 Jev」。
3. 采信 → 落入该步**已有**分支；不采信 / 无 tool → 仍走上文主路径。
4. 各 intent 只写死本题的 tool、state、选项与阈值；协议以本节为准。

#### 会话可用性

| 情况 | 当步 | 本会话后续 |
| --- | --- | --- |
| 无上列 tool | 主 Agent；见下方首次提示 | 记 `jev=unavailable`，不再调用 |
| 认证失败（缺 key / 401 等） | 主 Agent；见下方首次提示 | 粘性 `unavailable` |
| 非认证失败或结果畸形 | 主 Agent | 不粘性禁用 |
| 低置信度（低于该步阈值） | 普通判断交主 Agent；非 yolo 的 deliver decision 请求用户确认 | 不禁用 |
| 合法结果且达阈值 | 仅已枚举定型分支 | 保持可用 |

默认阈值：

- `choice` / `score`：confidence ≥ 0.8。
- `noul`：yes ≥ 0.8，no ≤ 0.2；中间带走主 Agent。
- intent 可写更严阈值，不得更松除非写明。

#### 首次不可用提示

每会话至多一行。第一次因「无 tool」或「认证失败」记 `jev=unavailable` 时，
在当步输出中恰好加一行：

- 文案固定为：
  `未检测到可用的 Jev MCP；定型判断将由主 Agent 完成，可能更慢。安装见 Skill 所在仓库 README「Jev 可选加速」。`
- ❌ 不得追问、不得停、不得再展开安装教程正文。
- 同一会话后续步骤 ❌ 不再重复该行。
- 非认证失败、低置信度、未声明可选加速的步骤：不发此提示。

### 目标根

<a id="s-root"></a>

本节规定各 intent 如何确定目标仓库根。

- next 先按其流程识别目标，允许续办尚未 Git 化的初始化与无需仓库的 clarify。
- 除 init/bootstrap/migrate/next 外，执行仓库操作的 intent 在本次调用中：
  1. 用 `git -C <目标目录> rev-parse --show-toplevel` 将用户指定目标或当前目录
     解析为绝对 `REPO_ROOT`。
  2. 再读取并执行对应流程。
  3. 核对解析出的仓库确为用户目标；边界不明先澄清，澄清后重做本条。
  4. 命令失败则报告并停止，不使用空值或上次调用的变量。
- 以下 intent 另有规则：
  - clarify 与 help 不要求 Git 仓库。
  - init/bootstrap/migrate 由 initialization 公共流程处理普通目录与父仓库边界。
  - upgrade 解析 Git 根且不要求 manifest ready，规则见 `references/upgrade.md`。
  - integrate 解析 Git 根且不要求 manifest ready，规则见 `references/integrate.md`。
  - sync 解析 Git 根且不要求 manifest ready，规则见 `references/sync.md`。

### 工作区横幅

<a id="s-banner"></a>

横幅标识当前工作区，不在回复开头打印。单行格式固定：

`<logo_emoji> <main-repo-name>@<worktree-path>`

- `<logo_emoji>`：当前目标项目 `.mdf/manifest.yaml` 的顶层 `logo`；
  manifest 不存在、字段缺省、`null` 或空字符串时用 `📍`。
- `<main-repo-name>`：主仓库目录名（`git-common-dir` 的父目录名）。
  - 非 Git 工作根取该工作目录名；空目录与 Git 化前也使用同一规则，不等待仓库建立。
- 工作根：本会话当前绑定的目标 worktree 绝对路径；未绑定则
  `git rev-parse --show-toplevel`，非 Git 时用当前工作目录。
- `<worktree-path>`：工作根为 Git 主 worktree 时显示字面量 `git 主工作区`；
  其他 worktree 显示相对于主仓库同级 `<main-repo-name>-worktrees/` 的路径，
  用 `/` 连接并保留完整层级；非 Git 时显示工作根绝对路径。
- 进入或重新绑定目标后，横幅必须用新路径与新项目 logo，不得沿用上一处绑定。
- 相对上一处横幅，worktree 变化时立刻连续打印恰好三行（硬换行）：

  ```text
  <旧横幅>
  ⬇️
  <新横幅>
  ```

  - 实际输出为裸三行硬换行，不包代码围栏。
  - 中间一行只有 `⬇️`，前后无空格、无其它字符。
  - ❌ 禁止把 `⬇️` 与旧/新横幅写在同一行。
  - ❌ 禁止在这三行之间插入空行或其它文字。
  - 含仅改绝对路径绑定、未调用 `move_agent_to_root` 的情况。
- 没有上一处横幅时不打印切换三行。
- 本轮输出结束、等待用户回复时，最后一行必须是当前横幅。
  - 切换后的横幅已是最后一行时，不再重复。
- ❌ 不得在回复开头打印。
- 对任何 agent 都生效。help、clarify、upgrade 也必须在结尾打印；规则见 `SKILL.md`。

### 切换工作区

<a id="s-switch"></a>

进入已有 worktree 时，目标为绝对路径与完整分支名。
已在该路径且当前分支正确即通过；不得再 `git worktree add`，不得只在原根 `cd` 冒充已进入。

判定当前 agent：先看本会话可用工具，再看 `$MDF_ROOT` 是否位于下列目录之一。
工具与路径冲突时以工具为准。

- `.cursor/skills`、`.codex/skills`、`.kiro/skills`、`.claude/skills` 或 `.openclaw/skills`。

按角色进入目标：

- 仅 Cursor 主 Agent：立即对目标路径调用 `move_agent_to_root`（参数 `rootPath`）。
  - ❌ 禁止 `move_agent_to_cloned_root`（会 fetch origin，本地未推送分支会失败）。
  - 调用后必须新开 shell 再核对，不得沿用切换前的终端 cwd。
  - 无该工具时报告缺失并留在当前步骤，要求用户把工作区根打开为该路径。
  - 核对必须在切换后的环境、新 shell 执行：
    - `git rev-parse --show-toplevel` 等于目标路径。
    - `git branch --show-current` 等于目标分支。
- 其他（非 Cursor 主 Agent，以及全部 subagent；含 Codex、Kiro、Claude Code、
  OpenClaw）：
  - 全程用该绝对路径操作；禁止新建 worktree、禁止 `move_agent_to_root`、
    禁止要求用户切换；qa/dev 另禁止切到 owner。
  - 后续全部读写、Git 与 CLI 都用该路径：`git -C <路径>`、`--repo <路径>`、
    绝对文件路径。
  - ❌ 禁止只在原根 `cd` 冒充已进入，禁止再创建多余 worktree。
  - 核对：`git -C <路径> rev-parse --show-toplevel` 等于目标路径，
    `git -C <路径> branch --show-current` 等于目标分支。

未满足则留在当前步骤：Cursor 主 Agent 重复切换；其他核对该绝对路径。
不拆除已建 worktree 与分支。进入或绑定成功且 worktree 或 branch 已变化时，
按「工作区横幅」打印切换三行；结尾横幅必须反映当前绑定。

### 入口

<a id="s2"></a>

入口识别已有 staged、unstaged、untracked 改动，不普遍要求 clean worktree。
无关且不冲突的改动保留并继续；与任务重叠、归属或处理方式不明时先澄清，澄清后重做本条；
无法判定归属则停止。
clean 以 `git status --porcelain` 输出为空为准；不为 Skill 写入的文件设置额外豁免。

写入或提交前读取当前分支，按本次工作与文档的归属确定落点，不按 intent 名称分配
交付分支：

- deploy 工作区是仓库同级 `<repo-name>-worktrees/deploy`，`$mdf to deploy` 检出 master。
  - 只放 gitignore 的 deploy config，不在此修改或提交已跟踪文件。
  - 已跟踪改动干净才切回 master。close-out 不拆除这棵树。
- master 不直接修改或提交内容，包括文档；hotfix 的修改也在 hotfix 分支完成。
  init/bootstrap/migrate 的初始化落地及 close-out 的 Gitflow 合并按各自专门契约执行。
  upgrade 替换已安装 Skill 并提交本次路径时，可在当前分支（含 master）提交这些路径，
  不改 `.mdf/` 与 `docs/`；该例外只约束 upgrade，见 `references/upgrade.md`。
- 与当前交付分支工作相关的文档在当前分支更新，随该分支交付；包括规划记录、事实文档
  和 CodeWiki。当前事实文档和 CodeWiki 必须反映该 checkout 的实际状态，不把未实现
  的计划写成事实。调研、已确认决策与当前事实文档分开，不把候选方案当作已实现行为，
  不替代任务管理。
- 规划写入使用唯一的 `planning` 分支与仓库同级 `<repo-name>-worktrees/planning` worktree。
  - 覆盖 `prp create`、`prp review`、`prp split`、intake 中的 Proposal、
    以及 `jot promote` 为 Proposal。
  - 不在当前目录开分支，不占用 develop checkout。
  - 调用 `planning ensure --repo "$REPO_ROOT"` 创建或复用；当前根不是该 worktree 时，
    按「切换工作区」规则切过去，重新解析目标根。
  - 提交后运行 `planning land --repo "$REPO_ROOT"`，在占用 develop 的
    worktree（须 clean）上合入；local 模式可 fast-forward 时用 ff，已分叉时 no-ff。
    PR mode 按 [PR Close-out](pr-close-out.md) 的文档白名单核对，并使用 no-ff。
    所有模式合入前按 [squash](squash.md) 检查 planning；squash_required 时自主分析执行后重试，不逐次确认。
  - 新建 Proposal 的 ID 在该工作区随机生成，并避开当前 checkout 的 `docs/proposals/`（含 archive）及本批已有 ID；
    合入 develop 后才对 `$mdf start` 可见。
- 与当前交付分支工作无关、且不属于规划工作区的文档在 develop 更新；独立记录和公共
  文档维护也按此规则处理。develop 不存在时先明确创建基线，不擅自从未交付分支创建。
- 已有 Proposal 的修改若属于当前交付分支工作，仍在该交付分支更新；否则在 planning
  工作区更新并合入 develop。
- 归属不明确时先询问。需改用 develop 或 planning 时，在写入前选择安全切换或独立
  worktree，重新解析目标根并复查前置条件；不得自动搬运、暂存或提交已有改动来切换
  分支。无法安全准备目标时保留现场并停止。detached HEAD 下不写入或提交。

只读查询、审计和预览不受上述写入分支限制，报告其实际 checkout；
各交付阶段的角色分支与身份限制仍须满足，不因文档相关而绕过。
进度只认 objectives 勾选，不以 gate 文件当通行证。

验收：已有改动、当前任务范围和写入分支归属明确。
开分支、合并、版本收口及 CLI 明确要求 clean 的具体操作，
在执行前检查；不通过自动提交全部改动清场。只读与预览不整理、暂存或提交已有改动。

### 反馈

<a id="s3"></a>

同次 intent 接受用户对中间产物的反馈；不得仅因本次产物尚未提交而拒绝修改。
具体操作的前置条件仍须满足。

验收：用户反馈已被本步吸收，或明确无反馈。
异常与交接：边界不明则报告并停止；澄清后重做调用方当前步骤。

### 失败

<a id="s4"></a>

写入失败时保留现场并报告 findings，等待用户处理。

验收：失败现场、findings 与等待状态已报告。
异常与交接：本条即失败汇；不自行回滚，除非当前 intent 另有恢复规则。

### 测试失败工作流

converge（smart）与 verify branch 共用（详见 `delivery-contract.md`）：

1. 测试运行必须有框架自带报告文件（JUnit 等），禁止靠 tee/tail 冒充报告。
2. fail 后先复测单用例。
3. 修一个用例 → 复测该单用例。
4. 有 side effect 的 flaky 例外（须记录依据）。
5. 相关单用例都绿后，才继续该轮 verify。

### 日志与报告

<a id="logs"></a>

凡在 MDF 引导下执行的命令都必须留下足以诊断失败的完整日志或报告。
优先用命令或系统自己写出的日志与报告，不要再用 tee 复制一份。

- ⚠️ 失败时先读已有日志与报告，不为查看输出而重跑。
- 已有下列产物时，不 tee：
  - Core CLI 自动写的 `.mdf/logs/<时间戳>-<命令>/`
    （`stdout.log`、`stderr.log`、`meta.json`）。
  - Core 代跑验证的 `.mdf/reports/<时间戳>-<入口>/`
    （含 stdout/stderr、JUnit、`summary.json`）。
  - 工具按本次调用参数自己写的日志或报告（如 `--junitxml`、`--log`）。
- Core CLI 日志位于主仓库，交付 worktree 被删除后仍在；失败 JSON 的 `log` 给出路径。
  - 尚无 `.mdf/` 的目录写到 `MDF_LOG_DIR`，未设时为 `~/.mdf/logs/`。
- 调用有日志能力的工具时打开其落盘参数，读那份产物。
  - pytest / JUnit 写 `$MDF_REPORT_DIR` 或 `--junitxml`，不 tee。
- Agent 直接运行、且没有任何落盘产物时，用 Core `run` 代跑，不要 tee。
  - 写法：`python3 "$MDF_ROOT/scripts/mdf.py" run --repo "$REPO_ROOT"`
    `[--name <名称>] -- <命令>`
  - 日志在 `.mdf/logs/<时间戳>-<名称>/`；失败 JSON 的 `log` 给出路径。
  - `run` 设置 `MDF_REPORT_DIR` 与 `NO_COLOR=1`。
- Core 不可用、且没有任何落盘产物时，才写入主仓库
  `.mdf/logs/<时间戳>-<名称>.log`，并在汇报中给出路径。
  - 主仓库为 `git rev-parse --path-format=absolute --git-common-dir` 结果的父目录。
  - ❌ 不写入 owner/qa/dev 等交付 worktree 内的 `.mdf/logs/`。
  - 该目录不存在时先创建。忽略规则在仓库根 `.gitignore`（`.mdf/logs/`、`.mdf/reports/`）。
  - 写法如 `<命令> 2>&1 | tee <文件>`。
  - 能关颜色就关（`NO_COLOR=1`、`--no-color`）。
  - 落盘文本去掉 CSI/OSC 等终端控制符；进度条回车覆盖不得当正文。
- 用 grep、head、tail 等过滤或截断输出时，完整输出须先落盘再截取。
  - 写法如 `set -o pipefail; <命令> 2>&1 | tee <文件> | tail -n 50`。
  - ❌ 不得直接把命令输出管道给截断命令。
  - 判定成败以原命令的退出码为准，不以截断命令的退出码为准。
- Core 每次运行删除 `.mdf/logs/` 与 `.mdf/reports/` 中 7 天前的条目。

### 交接

<a id="s5"></a>

本节规定提交时机、提交范围、Git 操作授权与提交后的返回。

**提交时机**

- Agent 可以主动创建本地提交，并应在形成有意义、可解释的阶段成果时及时提交。
- 允许如实标注未完成状态的阶段提交。
  - 提交不代表验收通过，也不替代用户对方案、状态或启用的确认。
- 用户明确要求暂不提交时遵从；无改动不创建空提交。
- 中文 Conventional Commit 应准确描述内容和必要的未完成状态。
- 修复某个 Bug 的提交说明必须含该 Bug 的完整 ID（如 `bug-AB12`）。
  - 供 bug close 用 `git log --fixed-strings --grep=<Bug ID>` 定位。
  - 只改 `docs/` 与 `changes/` 的提交不要求。

**提交范围**

- 只暂存当前任务的明确路径或改动块，不夹带无关用户改动。
  - 同一文件混有无关改动也不能整文件顺带提交。
- 提交前核对完整 staged diff，已有无关暂存项也必须隔离，不能直接 commit 一并带入。
- 内部委托由外层 intent 统筹提交；各阶段要求的已提交基线和必须同批提交的产物仍有效。
- 只读、预览不产生提交。
- 失败保留现场，可保存有价值且状态明确的阶段成果，不以 commit 冒充完成。

**Git 操作授权**

- push、merge、tag 和删分支仍按各自流程授权，不从 commit 权限推导。
- `$mdf sync` 先 fetch 并展示分支关系图；用户确认计划后才对
  `master` / `develop` / `planning` 执行 merge 与 push；
  不授权删分支或 force-push。
- ❌ 禁止 rebase，不擅自改写已有历史；异名分支使用 no-ff。
  - local 模式的 `develop` 与 `planning` 互相同步允许 fast-forward；已分叉仍 no-ff。
    PR mode 的例外与禁止项按 [PR Close-out](pr-close-out.md) 核对。
- 阶段基线和集成要求见 `references/delivery-contract.md`。
- 规划 intent 在本次规划提交后运行 `planning land --repo "$REPO_ROOT"`，
  把 `planning` 合入占用 develop 的 worktree。
  - local 模式可 fast-forward 时用 ff；已分叉时 no-ff；PR mode 始终 no-ff。
  - 无新提交则该命令为 no-op。
  - 合入前检查 planning 未共享尾段；须整理时按 `squash.md` 自主执行，保留共享历史。
  - squash_required 的专用恢复先于调用方的一般失败分支；整理后仅重试原 planning land，不重新生成 ID、写对象或删除 Jot。
  - 无法完成整理或 land 仍有其他错误时，按调用方的失败分支保留现场并报告。
  - develop 或 planning 占用者 dirty 时停止并报告，不改 checkout。

**返回与委托**

- 阶段提交后返回调用方继续当前流程；当前 intent 全部完成后才结束。
  - 不仅为手动 commit 要求重调，也不自动触发下一个用户入口。
- deliver 按 `references/deliver.md` 串联剩余真实 intent 到 close-out。
  子 intent 完成后返回 deliver 继续。
- init 依据 `references/initialization.md` 自动转入 bootstrap 或 migrate 是明确的内部委托，
  不自动串联交付主线。

验收：提交范围、staged diff 与 Conventional Commit 可追溯，或明确无改动。
异常与交接：提交失败保留现场；只读、预览不产生提交。

### 语言

<a id="s6"></a>

核对简体中文、英文保留范围与完整前缀 ID。
生成的 Markdown 正文、标题与列表使用简体中文；
仅代码、路径、标识符、 命令、 标准名称及无法准确翻译的专有术语保留英文原文。
对用户沟通及产出中的 Proposal、Bug、Jot 须写完整前缀 ID，不得省略前缀或只写序号/短码。
不符合时改写后再继续。

- MDF 生成或管理的文档按 `references/doc-structure.md` 的 ASD-STE100 写作约定编写并人工复核。

### 按需读取

按操作需要读取：`references/repository-contract.md` 定义仓库目录、`manifest` 与 `基线`；
`references/object-contract.md` 定义 Proposal、Bug 与 Change 的 schema 和不变量。
intent 声明读取的契约或模板缺失时停止并报告，不猜测内容。

- 写入源代码或测试源代码前，读取 `repository-documents.md` 的体积条款及 `modules.md` 的 ignore 条款。
  - 先核对 `.mdf/modules.yaml`；命中 ignore 的文件报告 pattern 与 reason，不要求长度或拆分验收。
  - 其余文件按 `sourceset` 读取所有适用 module 的 `size_limits`，缺省字段用 1000/50/70。
  - 实测物理行数及所在 package 的实现/测试文件数，分别满足所有适用上限；未归属成员用默认策略。
  - 大 package 按职责与设计模式拆分，各结果满足触发配置的拆分目标，实现与测试不相加。
  - 保留改写前大小、module、硬上限与 `split_percent`；目标向下取整，文档仍按角色上限及 70%。
  - 未满足时留在当前步骤修复；无法拆分则报告缺项，不勾选完成。

| 材料 | 位置 | 读取条件 |
| --- | --- | --- |
| 意图 | `references/` | 读取已确认 intent 的流程及其声明委托的内部流程 |
| 公共契约 | `references/` | 按 intent 指定读取目录、对象或 CodeWiki 契约 |
| 模板 | `assets/` | intent 要求写入仓库产出物时读取对应模板 |
| 代码体积 | `references/repository-documents.md` | 写入源代码或测试源代码前读取体积条款 |
| 文档结构与写作 | `references/doc-structure.md` | 写入或改写任何 Markdown 产出物前读取 |
| 确定性 CLI | `scripts/` | intent 要求确定性操作时调用 |
