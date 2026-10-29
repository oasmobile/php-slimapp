# 初始化公共规则

由 init、bootstrap 与 migrate 按各自阶段调用，不是用户 intent。完整读取
`references/common.md` 与 `references/repository-contract.md`。
调用方入口使用步骤 1；Git 准备使用 2；配置方案使用 3；材料落地及验收使用 4–5；
确认启用使用 6–8。决策树按调用方入口选用，不是单链；bootstrap/migrate 表写明
所调用的步骤号。
各段返回调用方；复用经核对仍有效的同次结果，不重复写入、审阅或确认。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check boundary                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 不明确 ────────────→ [澄清后返回 1]
                 ├──── 不符合调用条件 ────→ [按分流表返回调用方]
                 └──── 判定完成 ──────────→ [返回调用方]

步骤 2 由调用方按步骤号进入，不是步骤 1 的后续。

┌──────────────────────────────────┐
│ 2 Prepare Git                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [保留现场并报告]
                 └──── 通过 ─────────→ [返回调用方]

步骤 3 由调用方按步骤号进入，不是步骤 2 的后续。

┌──────────────────────────────────┐
│ 3 Configure                      │
└────────────────┬─────────────────┘
                 │
                 ├──── 配置或范围未确认 ────→ [返回调用方澄清]
                 └──── 通过 ────────────────→ [返回调用方落地]

步骤 4 由调用方按步骤号进入，不是步骤 3 的后续。

┌──────────────────────────────────┐
│ 4 Save baseline                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 配置不符 ──────────→ 3 Configure
                 ├──── 其他失败/缺失 ─────→ [保留现场并报告]
                 └──── 阶段成果已提交 ────→ [返回调用方]

步骤 5 由调用方按步骤号进入，不是步骤 4 的后续。

┌──────────────────────────────────┐
│ 5 Validate                       │
└────────────────┬─────────────────┘
                 │
                 ├──── 可修复的审阅或校验问题 ────→ 5 Validate
                 ├──── 无法继续 ──────────────────→ [保留现场并报告]
                 └──── 审阅及校验通过 ────────────→ [返回调用方]

步骤 6 由调用方按步骤号进入，不是步骤 5 的后续。

┌──────────────────────────────────┐
│ 6 Confirm activation             │
└────────────────┬─────────────────┘
                 │
                 ├──── 未确认 ────→ [保持 initializing，返回调用方]
                 │
                 ▼ 用户明确确认启用
┌──────────────────────────────────┐
│ 7 Enable                         │
└────────────────┬─────────────────┘
                 │
                 ├──── 全量结果缺失或无效 ────→ [返回调用方补验]
                 ├──── 事实变化 ──────────────→ [返回调用方重审]
                 ├──── 其他失败 ──────────────→ [保留现场并报告]
                 │
                 ▼ ready 校验及提交通过
┌──────────────────────────────────┐
│ 8 Prepare branches               │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [保留现场并报告]
                 └──── 通过 ─────────→ [返回调用方完成]
```

## 工作流（唯一执行契约）

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check boundary | 约束 | 写入前核对边界、事实与状态 | 项目根与分流依据 | 返回调用方 | 不明回 1；否则按分流表返回 |
| 2 | Prepare Git | 脚本 | 运行 prepare-git；再提交基线；doctor | Git、允许的 findings | 返回调用方 | 保留现场并报告 |
| 3 | Configure | 约束 | 核对基线、版本、验证、实现根及收口模式 | 配置、保留范围确认 | 返回调用方落地 | 返回调用方澄清 |
| 4 | Save baseline | 约束 | init 后核 closeout、完成材料并提交，保持 initializing | 配置、提交、diff | 返回调用方 | 配置不符3；其他保留现场并报告 |
| 5 | Validate | 约束 | 按调用方审阅并全量校验 | 按 state 允许的 finding（s5） | 返回调用方 | 可修则 5；两轮后停 |
| 6 | Confirm activation | 约束 | 展示结果与方案并确认启用 | 用户明确确认 | 7 | 保持 initializing，返回调用方 |
| 7 | Enable | 约束 | 核对增量，启用并提交 | 有效全量结果、增量校验、提交 | 8 | 全量无效返回补验；事实变化重审；其他停 |
| 8 | Prepare branches | 约束 | 按确认方案核对并补齐 master/develop | 本地分支及关系 | 返回调用方完成 | 保留现场并报告 |

## 术语与数据结构

### 项目边界与分流

<a id="s1"></a>

在任何写入前确定项目根；Git 化完成后该根即为 `REPO_ROOT`。读取起步材料并检查实际实现和运行证据。
不按仓库年龄、提交数量或文档数量判定。默认工程模板、README、需求草稿和选型材料
本身不代表已有业务；实际功能、接口、数据处理或已运行部署才构成既有项目事实。
部署配置可能只是模板，不能仅凭文件名判定；无法确定时先澄清。

先只读检查已有 `.mdf/manifest.yaml`：ready 表示已经接入 MDF，即使尚无业务也由
migrate 维护；initializing 不代表老仓库，应继续检查实际内容。

不符合当前契约的既有 MDF 内容由 migrate 收敛，即使尚无业务事实；不推断历史语义：

- 入口一律运行 `doctor`，不要求 Git 根，也不要求已有 manifest。
- 没有 manifest 时 doctor 仍报告布局 finding。
  - `layout.migrate` 即不符合契约，走 migrate，不先 bootstrap。
- 不符合当前契约只看 finding code，不看文案里有没有 `$mdf migrate`：
  - 收敛类：`manifest.schema`、`layout.migrate`、`manifest.verification`。
  - 其余非法 manifest 或布局 finding，例如 `manifest.state`、`manifest.invalid`。
- ❌ 不算不符合契约：`manifest.initializing`、`layout.testing`。
  - 前者在未 ready 时总会出现，文案同时提到 init、migrate 与 bootstrap。
  - 后者由随后的 init CLI 写入。
- init 转入 migrate，bootstrap 写入前停止并提示 `$mdf migrate`。
- 其余校验在 Git 基础准备后执行。

| 调用 | 项目状态 | 行为 |
| --- | --- | --- |
| init | 未就绪、没有实际实现或运行事实，且 MDF 内容符合当前契约 | 说明依据，内部转入 bootstrap，返回其结果 |
| init | 已有事实、已 ready，或 MDF 内容不符合当前契约 | 内部转入 migrate，返回其结果 |
| bootstrap | 已有实际实现或运行事实 | 写入前报错、列证据并提示 `$mdf migrate` |
| bootstrap | 已 ready | 停止，配置调整提示 `$mdf migrate` |
| bootstrap | MDF 内容不符合当前契约 | 写入前停止，列 finding 并提示 `$mdf migrate` |
| bootstrap | 未初始化或 initializing，且符合新仓库条件 | 建立起点或核对已有产物续办 |
| migrate | 未就绪、没有实际实现或运行事实，且 MDF 内容符合当前契约 | 写入前报错、列证据并提示 `$mdf bootstrap` |
| migrate | 已有事实、已 ready，或 MDF 内容不符合当前契约 | 继续 migrate |

### Git 基础

<a id="s2"></a>

入口允许普通目录和无提交的 Git 仓库。先用 `git rev-parse --show-toplevel` 检查边界；
位于其他仓库内部时先澄清，不直接嵌套 `git init`，不把父仓库默认为目标。
bootstrap 必须先通过新仓库判定，再执行本节，不能在拒绝老仓库前写入 `.git/`。
migrate 必须先通过已有事实、已 ready，或不符合当前契约的判定，再执行本节。
不能在拒绝符合契约的新仓库前写入 `.git/`。

确认纳管范围、忽略规则和分支调整方案后，先运行
`python3 "$MDF_ROOT/scripts/mdf.py" prepare-git --repo "$REPO_ROOT"`：

- 非 Git 目录初始化为 `master`。
- 已是 Git 根则跳过。
- 位于其他仓库内部则失败。

再由 Agent 完成身份与基线提交：

- 先提交应纳管的既有项目内容作为原始基线，再整理 MDF；空目录没有可提交内容时，
  不创建空提交，首个提交保存 MDF 起点。
- 已有 Git 历史保留。识别 staged、unstaged 和 untracked 改动，按公共规则确定归属，
  不通过提交全部改动换取 clean。没有提交身份时询问用户，不编造身份或修改全局配置。
- 新仓库在 master 上落地。既有 main、缺少 master、当前工作分支或远端默认分支
  不符合约定时，展示具体本地调整方案；不得重置已有分支、改写历史或强制对齐。
  涉及已有 master 冲突、远端默认分支或保护规则时确认方案后处理，不只提示用户自行改名。
- init CLI 要求 `refs/remotes/origin/HEAD` 未设置或指向 master：
  - 指向 main 报 `main_default_branch`，指向其他分支报 `invalid_default_branch`。
  - 本节即核对；远端已有 master 时，确认方案后运行 `git remote set-head origin master`。
  - 远端默认分支须改名时按已确认方案处理；无法完成时保留现场、报告并交接，不调用 init CLI。
- 不要求远端；保留已有远端，不自动创建托管仓库或推送。远端设置变更按已确认方案授权，
  无法完成时明确交接。开分支、切换和合并前按操作要求检查工作区。

Git 基础准备后运行 `doctor`：

- bootstrap 且尚未初始化：允许继续。
- bootstrap 且已有 manifest：仅允许 `manifest.initializing` 与 `layout.testing`。
  这两项由随后的 init CLI 消除；已变为 ready 时停止并提示 migrate，不重新初始化。其他 finding 报告后停止。
- migrate 不因 finding 拒绝：
  - 盘点清单里已有的 finding 继续。
  - 新 finding 回到 migrate 步骤 2，不在已经过完的步骤 3 补记。
  - 仅无法安全处理的状态（如非本地产物目录的 `path.symlink`）报告后停止。

CLI init 仍要求 Git 根目录，不负责语义判定、Git 化、提交或启用。
init、bootstrap 与 migrate 共用该 CLI，不新增 bootstrap 或 migrate CLI。

### 配置与完成

<a id="s3"></a>

从确认方案提供以下配置：

- 八项基线：不适用基线逐项给出真实理由，不用计划或占位事实页满足 documented。
- 最近稳定版本：从未发布时版本为 `none`。
- `verification` 的五个入口（lint、build、quick、smoke、release）：
  - lint、build 没有对应检查时可用 `git diff --check` 或 `true`。
  - quick、smoke、release 必须是把 JUnit XML 写进 `$MDF_REPORT_DIR` 的真实运行器命令。
    - 如 `pytest --junitxml="$MDF_REPORT_DIR/junit.xml"`。
  - suite 语义与预算见 `delivery-contract.md`「验证 suite」。
- 可选预算覆盖。
- 可选 `closeout`：未指定且不存在时用 local；已有值默认保留。
  - 用户要求启用或调整 PR/MR 时，确认 mode 与 provider，并读取 [PR](pr.md) 的模式与 [合并后续办](pr-close-out.md) 的 Merge 例外。
  - 仅核配置要求，不执行该子流程；provider 只接受 github/gitlab，不能唯一确定时返回调用方澄清。
- `implementation_roots`：
  - 实现根可以为空目录。
  - 单 module 默认使用 `src`，多 module 使用各 `<module>/src`。
  - 已有模板使用实际目录并在 PROJECT 说明，不为 bootstrap 重排模板。

更新与保留规则：

- 更新时核对并保留未要求改变的配置，不依赖 CLI 默认值覆盖现有设置。
  - 保留 manifest 的 `closeout`；未要求修改时不得移除或重置为 local。
  - 保留 manifest 的 `rules`；配置与文件约束见 [项目阶段 rule 契约](project-rules.md)。
- 已有根文档和 AGENTS 非 MDF 托管块必须保留；续办先检查 diff，只更新确认范围，不覆盖重建。
- 创建项目 `AGENTS.md` 时仅写标题与 MDF 托管区块；已有非托管内容仅以目标仓库实际文件为准。
- ❌ 不得将用户级、父目录或会话中继承的指令复制为项目规则，除非用户明确要求。
  - 验收时对照写入前的项目文件，确认未新增未经要求的非托管规则。
- 已有项目文档保持原位；写入 `docs/` 下同名目录前核对内容和归属，不覆盖或自动接管。
- `docs/README.md` 已存在时保留原文，仅按确认范围补充入口。
- 工作目录由 CLI 预建 `.gitkeep` 占位，文档入口直接列出各目录链接，
  不添加空目录状态或建目录提示。
- Agent 在仓库根 `.gitignore` 中补齐 `/.mdf/tmp/`，保留已有规则；不预建临时目录。
  - 临时工作文件的用途、布局与清理见 [临时工作目录](temporary-work.md)。

### 配置落地与验收

本节落实已确认配置，并返回调用方验收。

<a id="s4"></a>

步骤 2 通过后调用 `init` CLI，传入步骤 3 确认的完整配置：

- `--latest-release <稳定 SemVer|none>`。
- 重复 `--baseline`、`--implementation-root`。
- `--lint`、`--build`、`--quick`、`--smoke`、`--release`。
- 可重复的 `--budget <suite>=<秒数>`。

init CLI 没有 closeout option，只保留已有值。用户已确认变更时，在 CLI 完成后定点更新 manifest.closeout。
回读 mode/provider 并检查 diff；不符回步骤 3 澄清或修正，按步骤 5 strict validation 验收后才启用。

init CLI 仅在缺失时写入 `docs/system/testing/` 的静态模板；Agent 按确认的验证配置填写并清除模板说明：

- 当前规则与 quick、smoke、release 各一节。
- 不把尚未采用的 kind 写成事实。

完成材料与配置，保持 initializing；清除本次模板占位说明，提交可验证的阶段成果。
核对提交范围及 diff；失败保留现场并报告。

<a id="s5"></a>

按调用方验收：migrate 完成事实审阅，bootstrap 核对起步材料；均执行 strict validation，
即 `python3 "$MDF_ROOT/scripts/mdf.py" validate --repo "$REPO_ROOT" --level strict`。

- bootstrap 不调用 fact audit，strict validation 是确定性契约校验，不是事实审阅。
- migrate 的同次 fact audit 已执行 strict validation，且后续项目内容未变时，复用其结果，
  不在本段再次运行；核对仓库、scope、提交与工作区 diff，并检查完整 findings。
- `manifest.state` 为 initializing 时仅允许 `manifest.initializing` finding；
  已是 ready 时须零 finding。
- 其他 finding 修正、提交后重验；同一项两轮后无法继续。
- 通过后返回调用方验收步骤；调用方进入启用阶段时从 6 继续。
- 无法继续则保留现场并报告。

### 启用与本地分支

本节确认启用授权，核验 ready 增量并准备本地分支。

<a id="s6"></a>

1. 展示结果、八项基线、验证命令和分支方案，询问：「是否结束初始化并启用正常工作流？」
2. 按 `SKILL.md`「用户确认」识别答复；用户回答 yes 或其他明确肯定答复即可继续。
3. 未确认时保持 initializing 并返回调用方，不继续写 ready。

<a id="s7"></a>

- 先对照步骤 5 的已验内容，核对提交及 staged、unstaged、untracked 项目改动。
  不按文件数、行数或「只是 flag」判断结果是否有效。
  同次全量结果缺失、不符合步骤 5 的允许项或无法核对时，先返回调用方补验。
  bootstrap 回步骤 5，migrate 回步骤 6，取得本文件步骤 5 要求的结果。
- 同次启用增量仅含以下内容时，复用步骤 5 的 strict validation 与事实审阅：
  - `.mdf/manifest.yaml` 的 `state: initializing → ready`。
  - Change 等收口记录中对本次启用状态的说明，不包含新的事实、承诺或配置变更。
  - 这些改动不构成事实变化，不重新调用 fact update 或 fact audit，不重复执行事实审阅。
- 写 ready 后运行一次 `validate --repo "$REPO_ROOT" --level basic`，零 finding 后提交。
  - basic 仍检查 ready 状态、配置、布局、记录与 evidence 路径，不重查 Git history。
  - 它只补验上述启用增量，不能替代步骤 5 的 strict validation。
- 提交后核对实际 commit diff、manifest 的 ready 值及工作区改动与预期一致。
  没有新增变化时直接进入 8，不再次运行 doctor、validate 或事实审阅。
- 配置、布局或其他材料有新增变化时补做 strict validation；不因确定性校验而自动重做事实审阅。
- 事实发生变化时返回调用方：bootstrap 回其步骤 5，migrate 回其步骤 6，再按本页步骤 5 补审补验。
  本页步骤 5 按当前 `manifest.state` 验收。
  - 可观察契约、实现、测试、事实页、evidence 或生成源/生成器变化影响对应事实结论。
    说明具体变化及失效原因；复用只限本次初始化，不跨调用缓存。
- 其他失败保留现场并报告，不宣称已完成。

<a id="s8"></a>

确保本地 master、develop 可用：

- 新仓库从包含已提交就绪结果的 master 创建 develop。
- 已有分支保留，缺少 develop 时按确认方案从 master 创建，不重置、不强制对齐。
- 既有分支关系影响使用时报告具体问题并按确认方案处理，通过后才宣布完成。

语义确认不因提交而省略。失败保留现场和阶段提交，不宣称已完成；同次可修复继续，
同一项两轮为限。
暂停后的调用重新检查入口与已有成果，不因需要手动 commit 而要求重调。
