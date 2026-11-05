# pre-gitflow-finish

## 配置

```yaml
hooks:
  pre-gitflow-finish:
    type: command
    path: scripts/pre-finish.sh
```

- hook 可省略；每项只含 `type` 与 `path`。
- `type`：`command` 由 Core 执行；`rule` 由 Agent 读取规则文件并执行。
- `path`：repo root 相对路径，须指向 owner worktree 内的文件；不得为绝对路径或含 `..`。
- command 文件须有执行权限与 shebang；不追加位置参数。
- 不提供独立 intent；下面的 CLI 仅为主链的执行辅助。

执行步骤见 [workflow](../pre-gitflow-finish.md)；本页只定义配置与调用接口。
