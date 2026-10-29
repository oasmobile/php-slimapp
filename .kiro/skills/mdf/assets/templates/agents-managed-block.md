<!-- MDF:BEGIN -->

## Mars Development Flow

- 你的角色是维护者，按需读取以下入口：
  - [README.md](README.md)：项目定位。
  - [PROJECT.md](PROJECT.md)：维护工作的起点；遵循其中的验证要求。
  - [GLOSSARY.md](GLOSSARY.md)：领域术语。
  - [docs/README.md](docs/README.md)：按主题定位，只打开本次相关的一两份页面。
  - [docs/system/overview.md](docs/system/overview.md)：系统边界。
- 当前行为以事实页为准；修改行为或发现冲突时核对源码。
  - 事实页记录当前检出版本；一条契约只住一页。
  - 架构问题读架构主题；对外可观察行为变化时同步用户指南。
  - 点名具体 ID 或事实页链接到工作上下文、ADR、Proposal、Bug 时再读取；ADR 记录理由。
  - CodeWiki 用于按需搜索符号，由 CodeWiki 管理。
- 新建或改写文档时，尽量遵循 ASD-STE100 的写作原则；按
  MDF Skill 中的文档结构与写作规则执行并人工复核。
- 执行的每条命令都要留下完整日志或报告。
  - 优先使用工具自己的日志与报告体系。
  - 工具没有落盘能力时，用 Core `run`：
    `python3 "$MDF_ROOT/scripts/mdf.py" run --repo "$REPO_ROOT" -- <命令>`；
    详见 [日志与报告]($MDF_ROOT/references/common.md#logs)。
  - Core 不可用时用 `tee` 兜底，并用 `pipefail` 保留退出码。
  - 日志保存到 `.mdf/logs/`。
  - 报告保存到 `.mdf/reports/`。
- 失败时先读已有日志、报告，拒绝为了查看输出而重跑。
- 临时脚本及其输入、输出放入 `.mdf/tmp/<日期>-<主题>/`，按需创建。
  - 使用前确认仓库根 `.gitignore` 含 `/.mdf/tmp/`，缺失时补齐；不提交临时文件。
  - 工作结束后清理，中断现场保留；不参与日志与报告的 7 天自动清理。
  - 长期复用的脚本移入项目正式目录并纳入 Git，结论和证据归入相应文档或报告。
- 沟通 Bug、Proposal、Jot、ADR 时写完整 ID（不得省略前缀或只写序号/短码/slug）。
- MDF 的调用与续办按 Skill 入口规则执行。
- 直接在 develop 上改动时，按事项创建 `changes/unreleased/<slug>/`，至少留存 `CHANGE.md`。
  - `CHANGE.md` 参照 [MDF Change 模板]($MDF_ROOT/assets/templates/change.md) 编写。

<!-- MDF:END -->
