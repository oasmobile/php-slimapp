# To

进入目标 worktree。规划别名、deploy 与已有分支在缺树时建立 worktree。
不创建新的交付分支或角色分支。

## 决策树

```text
┌──────────────────────────────────┐
│ 1 Resolve target                 │
└────────────────┬─────────────────┘
                 │
                 ├──── 空目标 ────→ [停止并列用法]
                 │
                 ▼ 已解析
┌──────────────────────────────────┐
│ 2 Ensure worktree                │
└────────────────┬─────────────────┘
                 │
                 ├──── 失败/缺失 ────→ [停止并报告]
                 │
                 ▼ 已就绪
┌──────────────────────────────────┐
│ 3 Enter workspace                │
└────────────────┬─────────────────┘
                 │
                 ├──── 未进入 ───────→ 3 Enter workspace
                 ├──── 通过 ─────────→ [结束]
                 └──── 失败/缺失 ────→ [停止并报告]
```

## 工作流（唯一执行契约）

读取 `references/common.md`。不要求 manifest ready，不要求 clean worktree。

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve target | 约束 | 核对非空目标 | 目标 | 2 | 空则停止并列用法 |
| 2 | Ensure worktree | 脚本 | 运行 to CLI 解析并确保 worktree | 绝对路径、分支 | 3 | 停止并报告 |
| 3 | Enter workspace | 约束 | 按切换工作区进入目标 | 工作根、分支 | 结束 | 未进入留 3；其他停止并报告 |

`$mdf to <target>` 执行本流程。

## 术语与数据结构

### 目标与别名

<a id="s1"></a>

**目标**

- 空目标停止，并展示 `$mdf help to`。
- 规划别名（等价，进入 `planning`）：`plan`、`planning`、`plan-mode`。
- `develop` 进入占用 develop 的 worktree，通常是主仓库根。
- `deploy` 进入 `<repo-name>-worktrees/deploy`。
- 其余写已有 worktree 的分支名或目录名，或已有本地分支名。

验收：目标非空。

异常与交接：空目标停止并列用法。

<a id="s2"></a>

**工作区**

- 运行 `to --repo "$REPO_ROOT" --target <target>`。
- 规划别名内部 `planning ensure`，创建或复用 planning worktree。
- `develop` 复用占用 develop 的已有 worktree，不新建。
- `deploy` 创建或复用 `<repo-name>-worktrees/deploy`，检出已有 `master`。
  - 不在 master 且已跟踪改动干净时，切回 master。
  - gitignore 的文件与未跟踪文件保留，不删除、不提交。
  - 不新建分支。此别名不匹配同名分支。
  - close-out 不拆除这棵树。本树占用 master 时，release/hotfix 在此合入。
- 已有 worktree 复用；已有分支缺树则在 `<repo-name>-worktrees/` 下 `worktree add`。只补已有分支。
- 以 JSON 的 `worktree` 绝对路径与 `branch` 为准。

验收：JSON 含唯一绝对路径，且该路径当前分支等于 `branch`。

异常与交接：停止并报告，不拆除已建 worktree。

- 多项匹配时不猜测。未知、多项或无 develop 占用者的 `details` 含已知目标。
- deploy 按序停止：master 不存在；已被其他 worktree 占用；已跟踪改动不干净。
- 后两项不切换，`details` 含 worktree。
- 并行分支或 worktree 已存在，或 git 命令失败时，同样停止。

<a id="s3"></a>

**进入**

- 按 `references/common.md` 的「切换工作区」规则进入步骤 2 的路径与分支。
- 进入后重新解析 `REPO_ROOT`。
- 向用户给出该绝对路径与分支名。

验收：已按该规则进入目标；非 Cursor 已把该绝对路径绑为本次工作根。

异常与交接：未进入则留在 3。路径失效或其他失败则停止并报告，不拆除已建 worktree。
