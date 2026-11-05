# Upgrade

`$mdf upgrade` 从上游 Git 默认分支拉取最新 MDF Skill：

- 替换当前仓库中已安装的 `mdf` 副本。
- 更新已有 `AGENTS.md` 的 MDF 托管区块。
- 不修改 `.mdf/` 的受跟踪内容、`docs/` 或业务文件，不覆盖源仓库的 `skills/mdf`。
  - 被忽略的 CLI 运行日志 `.mdf/logs/` 与报告 `.mdf/reports/` 除外。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check tools                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Preview fetch                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 有安装目标
┌──────────────────────────────────┐
│ 3 Confirm replace                │
└────────────────┬─────────────────┘
                 │
                 ├──── 拒绝 ────────────────→ [结束]
                 ├──── 未决或非明确答复 ────→ 3 Confirm replace
                 │
                 ▼ 用户确认替换
┌──────────────────────────────────┐
│ 4 Apply replace                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 上游已变化 ────→ 2 Preview fetch
                 ├──── 其他失败 ──────→ [保留现场，停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 5 Report result                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 通过 ────────────→ [结束]
                 ├──── 无法重读副本 ────→ [报告旧副本并结束]
                 └──── 无法展示结果 ────→ [停止]
```

## 工作流（唯一执行契约）

表中操作与证据按下方同名条目核对；顺序与跳转只由本表规定。

除根 SKILL.md 指定的横幅条款外，不读取 `references/common.md`，不执行其公共 workflow。
本 intent 替换已安装 Skill，并更新已有
`AGENTS.md` 托管区块；不按文档归属选择分支；替换后在当前分支提交本次路径，
不 push。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check tools | 脚本 | 运行 `info`，解析 Git 根 | 三个版本为 3、REPO_ROOT | 2 | 停止 |
| 2 | Preview fetch | 脚本 | dry-run 拉取并列出目标、history 与区块 | 旧/新基线、目标、history、区块计划 | 3 | 停止 |
| 3 | Confirm replace | 约束 | 展示计划、提交摘要并取得明确替换确认 | 用户确认 | 4 | 拒绝则结束；未决留在 3 |
| 4 | Apply replace | 脚本 | 绑定确认 commit 后替换并提交 | 基线、目录、区块、提交 | 5 | 源变化回 2；其他停止 |
| 5 | Report result | 约束 | 报告、重读，建议 migrate | 摘要、提交 | 结束；读不到则报旧副本 | 无法展示则停 |

## 术语与数据结构

### 工具与预览

<a id="s1"></a>

**工具**

用 `git -C <目标> rev-parse --show-toplevel` 解析 `REPO_ROOT`，并核对它就是用户要升级的目标仓库；
不符或不是 Git 仓库时停止。运行
`python3 "$MDF_ROOT/scripts/mdf.py" info`，协议、工具与 schema 版本均须为
数字 `3`。不要求 manifest、ready 或 clean worktree。

验收：Git 根为用户目标、三个版本为 3。

通过条件：进入预览。异常与交接：停止，不得模拟 CLI。

<a id="s2"></a>

**预览**

默认源为 `http://10.1.5.65:8929/mars/mdf`，取远程默认分支 HEAD。仅当用户给出
其他源时传 `--source`。

```bash
python3 "$MDF_ROOT/scripts/mdf.py" upgrade --repo "$REPO_ROOT" --dry-run
```

有 `--source` 时追加 `--source <url>`。

- CLI 只扫描已存在的 Agent Skills 目录中的 `mdf`，不创建未安装位置，不触碰 `skills/mdf`。
- 输出须含 `source`、`new_commit`、`targets`、`agents`、`history`、`commit`
  与每项目标的当前基线。
- 无安装目标或拉取失败时停止。
- `history` 按当前基线分组：
  - 基线可对照时列出 `old..new` 中触及 `skills/mdf` 的提交（新→旧）及文件 `name-status`。
  - 无 `.version`、基线不是完整 commit hash、或不在上游历史时写入对应 `status`，
    不因此失败。
- `AGENTS.md` 托管区块：
  - 有唯一托管区块时报告将更新或已相同；无 `AGENTS.md` 或无区块则 `skip`。
  - 标记错误或重复时停止。

验收：结构化预览、至少一个目标。

通过条件：进入确认。异常与交接：不写入。

### 确认与替换

<a id="s3"></a>

**确认**

向用户展示以下内容：

- 源、新 commit、将替换的路径、当前 `.version`。
- `history` 中的提交摘要与将改动的 Skill 文件。
- `AGENTS.md` 区块计划。

说明与确认：

- 有提交时用说明陈述会得到什么；`status` 不是 `ok` 时说明无法列出历史的原因，不得编造。
- ⚠️ 说明已安装 Skill 的本地改动会丢失。
- 已有托管区块会被上游模板替换，非托管内容保留；不改 `.mdf/` 与 `docs/`。
- 确认替换即同意在当前分支提交这些路径，不夹带其他改动，不 push。
- 📌 必须取得明确替换确认；拒绝则结束且不写入。不得把沉默当作同意。

验收：用户明确确认或明确拒绝。

通过条件：确认后进入替换。异常与交接：拒绝则结束；未决或非明确答复留在 3，
不得把沉默当作同意。

<a id="s4"></a>

**替换**

```bash
python3 "$MDF_ROOT/scripts/mdf.py" upgrade --repo "$REPO_ROOT" --expected-commit <步骤2确认的new_commit>
```

预览用过 `--source` 时这里使用同一源。

- 必须传入预览确认的完整 commit。
  - CLI 在任何替换前比对上游 HEAD，变化返回 `upgrade_source_changed`，
    回到 2 重新预览并确认。
- CLI 用上游 `skills/mdf` 替换每个已安装副本，并写入完整 commit 到 `references/.version`。
- 已有唯一 `AGENTS.md` 托管区块时，用上游 `agents-managed-block.md` 替换该区块。
  - 无文件或无区块则跳过，不新建或追加。
- 失败时保留现场；逐个读取各目标的 `references/.version`，等于 `new_commit` 的为已替换，
  其余为未替换，分别报告路径。
- ❌ 不得删除目标仓库的 `.mdf/` 或 `docs/`。
- 写入后仅暂存并 `commit --only` 本次路径，不夹带其他暂存或工作区改动，不 push。
  - 无变更则不创建提交。

验收：各目标目录存在、`.version` 等于 `new_commit`，`agents` 与 `commit`
结果已落实。

通过条件：进入报告。异常与交接：保留现场并停止。

### 报告与重读

<a id="s5"></a>

**报告**

报告旧基线、新基线、替换路径、`AGENTS.md` 区块结果和本地提交。不 push。

替换后运行 `doctor --repo "$REPO_ROOT"`：

- 出现以下 finding code 时，建议用户运行 `$mdf migrate`：
  - `manifest.schema`、`layout.migrate`、`manifest.verification`。
  - 其余非法 manifest 或布局 finding，例如 `manifest.state`、`manifest.invalid`。
  - ❌ 不因 `manifest.initializing` 或 `layout.testing` 建议 migrate。
- `history` 摘要显示文档契约有变化时，同样建议 `$mdf migrate`。
  - 含模板、布局、根文档职责或事实页契约。
- 已在当前布局上的仓库可改用 `$mdf fact update --scope full` 整理结构。
- upgrade 本身不改 `.mdf/` 的受跟踪内容与 `docs/`。

重读新 Skill：

- 重读前核对本次 `MDF_ROOT` 是否为已替换的某个 `targets[].path`：
  - 是则从 `MDF_ROOT` 完整重读 `SKILL.md`。
  - 否则从已替换目标完整重读；无法重读时报告本会话仍在使用旧副本。
- 若更新了托管区块，同时重读 `AGENTS.md`。
- 丢弃本次已读入的旧副本。
- 重读成功时，同会话内后续 `$mdf` 调用按新 Skill 执行，不得要求新会话。
- 本 intent 仍在报告后结束，不自动串联其他入口。

验收：结果摘要与 CLI 产物一致，新 Skill 已重读。

通过条件：结束。

- 无法展示结果时停止。
- 无法重读 Skill 时报告本会话仍在使用旧副本并结束。
  不要求同会话按新流程执行。
doctor finding 只建议 migrate，不构成本步失败。
