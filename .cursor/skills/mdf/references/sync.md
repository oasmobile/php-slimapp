# Sync

`$mdf sync` 将 `master`、`develop`、`planning` 三大 trunk 与 `origin` 对齐：
先对三大分支全部 pull，再全部 push。PR mode 的受保护增量先走本页的 PR 恢复流程。
其他本地或远端分支只报告，不操作。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Check root                     │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 2 Preview branches               │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 3 Confirm sync                   │
└────────────────┬─────────────────┘
                 │
                 ├──── 未确认 ────→ 3 Confirm sync
                 ├──── 取消 ──────→ [停止]
                 │
                 ▼ 确认或恢复核对通过
┌──────────────────────────────────┐
│ 4 Sync trunks                    │
└────────────────┬─────────────────┘
                 │
                 ├──── 计划变化 ─────────────────→ 2 Preview branches
                 ├──── conflict 已解决并提交 ────→ 2 Preview branches
                 ├──── conflict 无法处理 ────────→ [保留现场并询问]
                 ├──── pr_required ──────────────→ [PR 提交与恢复]
                 ├──── dev_pr_required ──────────→ [委托 dev-pr 检查与交付]
                 ├──── waiting_for_pr ───────────→ [等待平台合并后续办]
                 ├──── ready_to_sync ────────────→ 2 Preview branches
                 ├──── 其他失败 ─────────────────→ [报告现场并停止]
                 │
                 ▼ 通过
┌──────────────────────────────────┐
│ 5 Report result                  │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止]
                 │
                 └──── 通过 ─────────→ [结束]
```

## 工作流（唯一执行契约）

读取 `references/common.md`。不要求 manifest ready。
本 intent 先授权 fetch；用户确认计划后才授权三大 trunk 的 merge（含 no-ff）与 push；
不授权删 trunk、rebase 或 force-push；dev-pr 的保全后 reset 与合并后 source 清理属于已确认 PR 计划。
PR mode 的计划确认还可授权创建本次 sync source branch、push source 与创建或恢复 PR/MR。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Check root | 脚本 | 运行 `info`，解析 Git 根 | 三个版本为 3、REPO_ROOT | 2 | 停止 |
| 2 | Preview branches | 脚本 | fetch 并展示分支关系图与同步计划 | JSON branches、confirmation | 3 | 停止 |
| 3 | Confirm sync | 约束 | 确认或核对恢复授权 | 授权快照、核对 | 4 | 未确认留 3；取消停止 |
| 4 | Sync trunks | 脚本 | 按已确认计划同步、处理 conflict 或 PR | trunks、现场 | 5 | 变化/解决回 2；PR 走本页恢复；其余停 |
| 5 | Report result | 约束 | 报告 trunks 与多余分支 | 摘要含 extras | 结束 | 停止 |

`$mdf sync` 执行本流程。

## 术语与数据结构

### 根与对齐

<a id="s1"></a>

**根**

用 `git -C <目标> rev-parse --show-toplevel` 解析 `REPO_ROOT`，并核对它就是
用户要同步的目标仓库；不符或不是 Git 仓库时停止。运行
`python3 "$MDF_ROOT/scripts/mdf.py" info`，协议、工具与 schema 版本均须为
数字 `3`。不要求 manifest、ready。

验收：Git 根为用户目标、三个版本为 3。

通过条件：进入步骤 2 预览。异常与交接：停止，不得模拟 CLI。

<a id="s2"></a>

### 预览

```bash
python3 "$MDF_ROOT/scripts/mdf.py" sync --repo "$REPO_ROOT"
```

默认只 `fetch --prune` 并输出预览，不 checkout、merge 或 push。

- 三大 trunk 固定为 `master`、`develop`、`planning`；两侧 refs 都必须已存在。
- JSON `branches` 覆盖本地与 `origin` 分支的并集；每项含 local / remote tip SHA、
  ahead / behind（local 相对 remote）、relation、graph 与是否参与同步的 `sync`。
- 向用户展示每个分支的 `graph`：始终包含双方 tip，路径上的 commit 用数量折叠；
  分叉图标出共同祖先。`refs/heads/<branch>` 为 local，`refs/remotes/origin/<branch>` 为 remote。
- 按下表解释关系，并列出三大 trunk 的操作计划；其他分支只报告。

有 PR mode 时先应用 [PR Close-out](pr-close-out.md) 的同步限制，再展示允许执行的计划：

- 当前 checkout 或远端 master/develop 的 manifest 启用 PR mode 时，master/develop 分叉不得自动合并。
- 本地领先的 master/develop 增量须由 CLI 证明合规；无法证明时报告阻塞，不承诺 push。
- 以下表格的 diverged 合并只适用于未被上述规则禁止的分支；用户确认不覆盖 PR mode 限制。
- JSON `pull_plan` 列出须创建或恢复 PR/MR 的 master/develop；处理见下文「PR 提交与恢复」。

| relation | local / remote 关系 | 三大 trunk 计划与 conflict 风险 |
| --- | --- | --- |
| equal | tip 相同 | noop |
| behind | local 是 remote 祖先 | pull ff，无 merge conflict |
| ahead | remote 是 local 祖先 | pull noop、push ff，无 merge conflict |
| diverged | 双方各有独有 commit | no-ff merge 后 push；可能 conflict，不能保证无冲突 |
| local_only / remote_only | 只存在于一侧 | 其他分支仅报告，不创建另一侧 |

<a id="s3"></a>

### 确认

- 用户明确确认展示的计划后，记录确认原话与授权快照，不得自行代答。
  - 快照含目标仓库、origin fetch / push URL、三大 trunk 的 local / remote 完整 tip 与 `confirmation`。
  - 从预览 JSON 取 tip；用 `git remote get-url --all origin` 与 `git remote get-url --push --all origin` 取 URL。
- 未确认时留在步骤 3 等待，取消则停止。
- conflict 恢复回到本步时，对照原授权快照及本次 pull / resolution 记录：
  - 仅已授权 pull / merge resolution 改变 local tip，且原 remote tip、仓库与两组 URL 均未变，才复用授权。
  - 否则重新确认新图与计划；缺原快照或无法证明变更来源时也须重新确认。

<a id="s4"></a>

### 执行与 conflict

使用通过步骤 3 核对的本次预览 `confirmation`：

```bash
python3 "$MDF_ROOT/scripts/mdf.py" sync --repo "$REPO_ROOT" --confirm "$CONFIRMATION"
```

- confirmation 绑定目标仓库、origin fetch / push URL 与三大 trunk tip。
- 执行前再次 fetch；任一绑定项变化，CLI 以 `sync_plan_changed` 返回新预览。
  - 回步骤 2 展示新图与计划，再按步骤 3 核对授权；不得只换 token 自动重试。
- 占用任一 trunk 的 worktree 必须干净；缺占用者时主 worktree 须干净。
- CLI 返回 `pr_required` 时保留现场，按「PR 提交与恢复」重新预览；不得手工 merge 或直接 push trunk 绕过。
- 按序全部 pull：remote 已是祖先则 noop；可 fast-forward 则 ff；已分叉则 no-ff merge。
  - merge 与 push 使用完整 ref；全部 pull 成功后才原子 push 三者，不顺带推送 tag。
  - 禁止 rebase、force-push、删分支。
- conflict 返回 `merge_conflict`，details 含 branch、worktree、conflicts 与 Git 输出。
  - 保留 `MERGE_HEAD`、index 与文件现场，不 abort、不切走；已完成的 pull 保留。
  - Agent 在返回的 worktree 读取 base / ours / theirs 与双方 diff，先尝试保留双方意图。
  - 不得一律选 ours / theirs；意图不明或无法验证正确结果时，说明文件、分歧与方案再问用户。
  - 只暂存解决的 conflict 文件，确认无 unmerged entry，并按目标项目要求验证相关改动。
  - 验证通过后提交 `chore(sync): 合并 origin/<branch> 到 <branch>`，回步骤 2 预览新关系。
  - 步骤 3 核对恢复条件后才继续；完成所有 pull 后才 push。
- 非 conflict 的 Git 失败读日志并报告，不当作 conflict 擅自改文件。
- `extra_local` / `extra_remote` 只报告，不拉取、不推送、不删除。

验收：执行 JSON `ok` 为 true，且含三大 trunk 的 `pull` / `push` 结果。

异常与交接：无法处理的 conflict 才向用户提问；其他失败报告现场，不声称整体完成。

### PR 提交与恢复

develop 的 non-trivial 本地增量及分叉委托 [dev-pr](dev-pr.md)。

- 预览 pull_plan 的 action 为 dev_pr；同样先用 `sync --pr` 重新预览并确认，再执行 `sync --pr --confirm`。
  - 普通 sync 的确认只返回 pr_required，不能直接接管；不得复用普通 sync 的 token。
  - PR 计划执行后 CLI 先保全到本地 adhoc，再 reset develop 对齐远端。
- 返回 dev_pr_required 时按返回 worktree 内部执行 dev-pr 的检查、pr 与 close-out，不直接 push source。
- 直到 close-out 完成，恢复记录始终参与计划；不得因 develop 已 equal 就跳过未完成 PR。
- 项目 trivial policy 与整串判定见 dev-pr；默认纯维护直接同步，任一 non-trivial 则整串接管。

以下 `--pr` 预览与确认入口由 master/develop 共用。
其中 master 使用下述创建 source、平台等待与同名 ff 恢复流程；develop 使用上述 dev-pr 流程。
普通 sync 返回 `pr_required` 时，Agent 进入以下预览并展示 source、target、local tip 与审计结果：

```bash
python3 "$MDF_ROOT/scripts/mdf.py" sync --repo "$REPO_ROOT" --pr
python3 "$MDF_ROOT/scripts/mdf.py" sync --repo "$REPO_ROOT" --pr --confirm "$CONFIRMATION"
```

1. 用户确认 PR 计划后执行第二条命令；confirmation 另绑定 `--pr` 与恢复记录。
   - 不复用普通 sync 的 token；恢复时重新预览并确认，或按步骤 3 核对已有授权。
   - 沿用 `closeout.provider` 的 gh/glab 同仓接口；origin fetch/push 地址须唯一且一致。
2. CLI 为每个 target 保存原 head、remote base、origin 身份与 PR/MR 到 Git common dir 的恢复记录。
   - 先落盘，再创建 `codex/sync/<target>-<唯一标识>`，精确 push 已记录 head；不直接 push target。
   - target trunk 保留原现场；master 创建 sync PR；develop 返回 dev_pr_required，其余 trunk 等待。
   - 重试通过已记录 source 查找或读取 PR/MR；push 或 create 响应丢失时不重复创建。
   - 原 trunk tip 保持固定；等待期间的本地 trunk 新增提交或平台 source/target 异常变化均保留并停止。
   - source 需解冲突或返工时，先运行 `mdf.py to --repo "$REPO_ROOT" --target <source>`，确保已有 source branch 的 worktree。
     按返回 worktree/branch 及 common 的切换规则绑定；不新建另一 source branch，不改原 trunk。
     合入前核对 source worktree clean、无未完成 merge；不为清场提交或丢弃他人改动。
   - 在该 worktree 合入 target、修复并提交；用项目验证命令补测，再以本次 sync 恢复记录的 base 调用 `code-review --against <base>` 补审。
     base 缺失或无法解析时停止并报告，不改用移动的 target tip。
     不要求 source 具备 delivery.json、roster 或交付 branch 验证前置；修复完成后再预览 sync 计划。
   - 重新预览会绑定 source 新 tip；用户确认后，仅允许保留原 source 历史的后继提交非 force push 到同一 PR/MR。
   - 更新前落盘候选 head；push 响应丢失时核对平台 head 恢复；不允许 rebase 或改写 source 历史。
3. CLI 返回 `waiting_for_pr` 与每个 PR/MR 的 URL、source、head、status；此时整体 sync 未完成。
   - open 为 `waiting_for_merge`；closed 未 merged 为 `closed_without_merge`，保留记录，不自动重建。
   - 等平台合并后，再执行上述预览及确认；不得自动 approve 或 merge PR/MR。
4. CLI 核验平台 source/target/head 与记录一致，并 fetch 目标历史。
   - merge commit 必须为双亲，第二父为本次确认的 source head，且位于目标远端第一父链；原 base 须仍在目标历史。
   - 恢复时再次 fetch；任一 trunk remote tip 与确认快照不同则返回 `sync_plan_changed`，先重新预览确认。
   - 沿用 PR mode 的 merge commit 契约；squash/rebase/ff merge 均停止，不 reset、改写或丢弃本地历史。
   - 占用 trunk 的 worktree 必须干净；仅允许原 head 或已包含它的远端历史同名 fast-forward。
   - ff 后中断可继续；仓库级锁避免并发 sync 或 PR close-out 重复操作。
5. 所有 PR/MR 完成后返回 `ready_to_sync` 与新 `preview`；这仍不是整体 sync 完成。
   - 展示新图，按步骤 3 确认新计划，再按步骤 4 完成三大 trunk 的常规同步。
   - 后续调用可不带 `--pr`；不自动复用旧 token 或绕过变化的 tip。
   - 保留本地及远端 sync source branch 作为历史备份，不删除 branch 或 worktree，不创建 tag 或发版。

验收：master PR 与 develop 的 dev-pr 均可独立或同时续办；最终以普通 sync 的 trunks 结果为完成证据。
平台或 Git 失败先读日志；身份、历史或现场无法证明一致时停止并报告，不手工改写恢复记录。

<a id="s5"></a>

**报告**

向用户展示：

- 各 trunk 的 `pull`（`noop` / `ff` / `merged`）与 `push`（`noop` / `updated`）
- `extra_local` 与 `extra_remote`（可为空）；明确未对其操作

验收：摘要含三大 trunk 与两组 extras。

通过条件：结束。异常与交接：无法展示则停止。
