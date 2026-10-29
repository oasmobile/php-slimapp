# 项目阶段 rule 契约

本页定义 design 与 code-review 的项目 rule 配置、merge 和证据；不提供独立用户 intent。

## 配置与加载接口

manifest 可选 `rules`，每个阶段只接受一个文件路径，不接受 command 或 type mapping。

```yaml
rules:
  design: .mdf/rules/design.md
  code-review: .mdf/rules/code-review.md
```

- 路径相对于当前 owner worktree 的 repo root，不限定目录或文件扩展名。
- 文件必须 Git tracked、UTF-8、非空且为普通文件；路径禁止绝对路径、`..` 与 symlink。
- 缺省或 `rules: {}` 表示仅用 MDF rule；已配置阶段不得用 null、空字符串或空文件禁用。
- init 保留已有配置；不自动创建 rule 文件，不提供 CLI 临时覆盖。

调用方在本阶段 Check 内运行以下只读命令，完整读取 JSON；失败则停止并报告路径与原因。

```bash
python3 "$MDF_ROOT/scripts/mdf.py" project-rules --repo "$REPO_ROOT" --stage <design|code-review>
```

- 输出 `stage` 与 `project_rule`；未配置时后者为 null。
- 已配置时返回 `path`、`content` 完整原文与文件字节的 `sha256` 内容指纹。
- CLI 只读取文件，不执行文件，也不生成合并文件；规则语义由 Agent 判断。
- doctor / validate 校验全部已配置 rule；运行本命令只加载所选阶段。

## Merge 与分派

本阶段适用规则为 MDF rule 与 project rule 的 merge，明确冲突时 project rule 优先。

- 无冲突要求共同生效，不删除 MDF rule、不以 project rule 替换整份 MDF 流程。
- 主 Agent 列明冲突及采用的 project 条款，继续按合并结果执行，无需为已规定的优先级另行询问。
- merge 只作用于对应阶段的 MDF 契约，不改变宿主权限或上级指令。
- rule 可引用必要验证命令，仍是指令文本，不作为 command hook 执行；不递归加载 include。
- 主 Agent 在讨论、裁定、修复和验收中应用同一份合并规则。
- 每份 subagent 任务携带适用的完整 MDF rule、project rule 的来源路径与完整原文。
  - 不得只传路径、摘要或依赖会话继承；未配置时明确 project rule 为无。
  - partition 也完整传递，由执行者结合切片判断适用项。
- code-review 保留固定 opening，之后附完整规则；冲突条款按 project 优先解释。
- 独立调用与 deliver、close-out 等内部委托均由阶段入口加载，不在调用方另建分支。

## 同轮证据与续办

本节规定本轮原文的一致性，以及规则变更后结果的复用边界。

- 本轮第一次加载后保留完整原文，所有分派和主 Agent 使用同一份内容。
- design.md、code-review 草稿、各 reviewer 报告与终稿记录 project rule 的 path 和 sha256。
  - 未配置明确写无；sha256 标为 rule 内容指纹，不是 commit hash。
- 续办、分派前和阶段验收前重新加载，与本轮已存 path 和指纹比对；一致才可复用原文和结果。
- 新增、删除配置、换路径或内容变化均视为规则变更；缺证据且当前有配置也不能视为一致。
- 发现变更先停止并说明差异，等用户确认；已确认同一变更则不重复询问。
  - design 确认后返回 Clarify，按新规则重新确认方案并交给 Baseline。
  - code-review 确认后从固定交付基线到当前 review_head 开新一轮完整审查，不复用旧报告。
- 未配置时以无项目 rule 核对，无需内容指纹；不要求为此补写已有报告。
- 其他无法恢复本轮原文或核对证据的情况停止报告，不推断一致，不记录通过。
- rule 在阶段完成后变化，原完成结果不证明符合新规则；再次进入本阶段先按上述规则处理。
