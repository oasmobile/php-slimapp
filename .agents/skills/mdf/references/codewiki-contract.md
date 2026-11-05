# CodeWiki Wiki 契约

树形：not-tree。本流程核对本次 CodeWiki 操作适用的边界，不重开生成或更新入口。

## 工作流（唯一执行契约）

| # | 步骤 | 类型 | 做什么 | 证据 | 通过 → | 失败/缺失 → |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Resolve context | 约束 | 确认调用方、当前步骤与适用事件 | 调用上下文与事件 | 2 | 缺上下文则返回缺项，不猜测 |
| 2 | Apply rules | 约束 | 核对适用规则、前置证据与边界 | 命令、产物与检查记录 | 3 | 不符或缺证据则返回失败 |
| 3 | Return | 约束 | 返回检查结论，继续调用方当前步骤 | 可追溯结论与缺项 | 返回调用方 | 缺项返回失败，不推进业务阶段 |

## 术语与数据结构

适用事件包括：工具检查、受管写入、落盘验收、恢复或会话清理事件。仅读取条款不触发其中描述的其他 intent。

由 codewiki generate 与 codewiki update 读取。规则持续适用，不是依次执行的阶段。

### 边界

- 仅用 CodeWiki MCP 的八个工具生成或修改 Wiki：
  - `analyze_repo`、`read_code_components`、`write_doc_file`、`edit_doc_file`；
  - `save_module_tree`、`get_processing_order`、`get_prompt`、`close_session`。
- ❌ 不运行 CodeWiki CLI、`generate_docs` 或 `get_module_tree`；
  不配置 provider、model 或 API key。
- 分工：Agent 负责理解与写作；MCP 负责分析和受控写入。
- ❌ 不修改业务代码、配置、测试或 `docs/repowiki/` 以外的文档。
  - 按公共规则主动提交本次 Wiki 改动，不夹带其他文件。
  - `docs/repowiki/` 之外的 `docs/` 仍由项目的普通人工文档契约管理。
- 生成内容使用简体中文。代码、路径、标识符和必要的术语可保留原文。

### 会话与恢复边界

本节规定运行时检查、workspace 残余与受管文件的写入边界。

- 生成和更新入口读取 `references/codewiki-runtime.md` 检查工具。
  - 工具缺失时按该流程配置；用户启用后续办时重新检查八工具。
- 失败或需要新基线时读取 `references/codewiki-recovery.md`。
- 安装目录和 IDE 配置不属于目标仓库产出。
- 成功结束时，当前 session workspace 必须清理。
  - ❌ `.codewiki/` 不得留下本次残余，也不得通过忽略规则隐藏它。
- 失败时可按恢复流程暂留当前 session workspace，以免关闭未完成会话却推进基线。
  - 必须明确报告残余和续办条件。
- 受管页面与 JSON 只通过八个 MCP 工具写入。
  - 唯一搬移例外：恢复流程中用户明确确认后，
    将整个旧 Wiki 和本次 session workspace 移至指定仓外备份。
  - ❌ 不得直接编辑、删除、重排受管页面，或手工改写 metadata。
  - ❌ 其他会话的目录不得触及。

### 受管输出

唯一受管根目录是 `docs/repowiki/`，并应提交到 Git：

```text
docs/repowiki/
├── overview.md
├── <module>.md
├── hacks.md                 # 仅在发现至少一个 hack 时存在
├── first_module_tree.json
├── module_tree.json
└── metadata.json
```

- `module_tree.json` 是当前模块树，`first_module_tree.json` 是首次聚类快照。
- 只有本次成功写入或编辑过页面，`close_session` 才写入 `metadata.json` 增量基线。
  - 未写页面时只关闭会话并清理 workspace。
  - ❌ 不得仅以返回 `closed` 代替落盘验收。
- `overview.md` 与每个受管 Markdown 都以以下首行开始：

```markdown
<!-- mdf-codewiki: managed; do not edit manually -->
```

- 这三份 JSON 均须存在且可解析。
  - `metadata.json` 的 `generation_info.commit_id` 和 `generation_info.timestamp` 均非空。
- 所有受管 Markdown 都由 CodeWiki MCP 写入或编辑，不接受人工直接修改。
  - 也不设置 annotation、overlay 或人工二级目录。

📌 符合上述目录、三个 JSON、首行 marker 和基线字段的根目录才是
`MDF CodeWiki standard`。

- 任何缺项、损坏 JSON、空基线、未标记 Markdown 或其他既有 Wiki 都是非标准目录。
- ❌ 非标准目录不得用增量更新覆盖。

### 写作与事实

- 写入或改写 Wiki 前读取 `references/doc-structure.md`，采用其中的 ASD-STE100 写作约定并人工复核。
- 以当前 checkout 的代码、配置、schema、测试和已跟踪生成物为证据。已有手工文档
  或旧 Wiki 只可辅助定位，不可覆盖代码证据。
- 能由本仓查证的行为必须读完并写成事实；不得用“待确认”、TODO 或猜测代替阅读。
  矛盾实现如实说明条件和位置。
- vendor 内部、环境密钥实际值、线上调用方或其他仓外事实不属于本 Wiki；按需要省略，
  或明确写“本 Wiki 不覆盖”。
- 每个模块页说明职责、关键组件、调用或数据关系、边界与仓库相对证据。先处理 leaf，
  再处理父模块；所有交叉链接必须可解析。
- 只在 Mermaid 校验成功时保留图。校验失败或跳过时，修复运行时或删除该图，不得称其
  已校验。

### Hack 收录

`hack` 是本仓可证的特殊实现，同时满足：

- 它偏离同类功能的普通路径、公开接口契约或预期约束；
- 且省去该特殊处理会改变行为。
- 它不是笼统的“旧代码”，也不预设版本、迁移、路由或其他项目专属类别。

收录规则：

- 发现一个或多个 hack 时，创建 `hacks.md` 并从 `overview.md` 链接。
- 每项至少写明：位置、触发条件、实际行为、所偏离的普通规则、可见影响和代码证据。
- 无证据时不收录；没有 hack 时不创建空页。
