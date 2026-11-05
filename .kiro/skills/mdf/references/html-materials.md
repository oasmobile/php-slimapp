# HTML 工作材料

本页规定 PRP 与交付总结的 HTML 格式、信息完整性和展示检查。

## 格式与展示

HTML 是可独立打开的完整文档，正文必须放在唯一的 `<main>` 中。

- 两类材料统一使用 [深色终端文档模板](../assets/templates/document.html)。
  - 深色背景、浅绿章节、等宽文字、章节目录；窄屏目录换行，宽表与代码独立滚动。
- 把实际正文填入 `MDF_DOCUMENT_CONTENT`，标题填入 `MDF_DOCUMENT_TITLE`。
  - `MDF_DOCUMENT_OUTLINE` 为可见章节的锚点链接，必须与正文 `h2` 的 `id` 对齐。
  - `MDF_METADATA_COMMENT` 在 PRP 中写下方 metadata；总结中留空。
- `html_documents.render_document(content, title, metadata=None)` 可从 HTML 正文生成完整文件。
  - PRP 的 `prp-format` 自动套用模板；不保留模板槽，不引入外部 stylesheet 或 script。
- 使用 `<!doctype html>`、`lang="zh-CN"`、UTF-8、viewport 与可读的内嵌 CSS。
- 以标题、列表、表格和代码块组织信息；宽表与代码块允许滚动。
- 不依赖网络、外部字体或 JavaScript；离线打开也能阅读全部正文。
- 内容与 attribute 必须正确 escape；证据链接相对当前文件，外部链接保持原地址。
- 按 [写作规则](doc-structure.md) 复核 ASD-STE100 可适用原则。
  - 详细信息按主题展开，不以摘要代替正文；不得删去条件、例外、取舍或证据。
- HTML 不设文件行数上限；可见正文仍按写作规则检查结构。
- 展示前在宿主 browser / HTML preview 打开实际文件，检查标题、完整正文、表格和链接。
  - 无可用预览时报告限制并提供文件路径；不得声称已完成视觉检查。

## PRP 存储

PRP 的可见 HTML 正文是唯一正文，metadata 使用 YAML comment。

- draft：`docs/proposals/prp-<4 位字符>-<slug>.md`，使用原有 YAML frontmatter。
- review：同目录 `<stem>.review.html`，由当前 draft 生成，尚不构成对象或 ready。
- 本次 review 确认并转为 ready：同目录 `<stem>.html`；不保留对应 Markdown 副本。
- 已有 ready / implemented / released PRP 保留原格式，含 archive 中的 PRP。
  - doctor / validate 不按状态追溯 HTML 格式要求，不要求批量转换或补写过去的评审材料。
- rejected / replaced 保留裁定时的原格式；archive 保留扩展名。
- HTML metadata 位于 doctype 后，格式如下；只放对象字段，不嵌入 Markdown 正文。

```html
<!doctype html>
<!-- MDF:METADATA
id: prp-0001
type: proposal
status: ready
depends_on: []
-->
```

- 必填章节与 scope 子节沿用 [对象契约](object-contract.md)，在可见正文用 `h2` / `h3` 表达。
- review 前把已确认事实与依据、约束、依赖、取舍、风险和验收方法补进 draft。
  - 对已有 PRP 补充本次变更与原稿 diff；无变更或不适用项说明理由，不留占位符。
- 内部 CLI `prp-format preview --repo <root> --proposal <id>` 生成 review HTML。
- 用户确认当前 HTML 后运行 `prp-format ready --repo <root> --proposal <id> --confirmed`。
  - CLI 核对 preview 与当前 draft 一致，转换为 ready HTML，删除 Markdown 与临时 preview。
  - 同时改写仓内指向原 Markdown 的链接；失败报告实际状态，不声称 ready。
- 未开工 ready PRP 再次 review 时运行 `prp-format draft --repo <root> --proposal <id>`。
  - 回到 Markdown draft 并改写引用，再修改、生成 HTML 和取得确认。
- 后续交付只更新 metadata 并保留正文与格式；split 保留原正文并追加拆分依据。

## 设计与开发总结

每次 close-out 在 Gitflow 前留存 `delivery-summary.html`，按模板记录完整交付。

- 使用 [总结正文模板](../assets/templates/delivery-summary.html)，涵盖所有交付 kind 与人工 feature。
  - 填写实际内容后套用上述文档模板，保存完整 HTML；不得把正文 fragment 当作最终文件。
- feature / bugfix：`changes/unreleased/<slug>/delivery-summary.html`。
- release / hotfix：先写 `changes/unreleased/<semver>/delivery-summary.html`。
  - `release-closeout` 随材料搬入 `changes/<semver>/delivery-summary.html`。
- feature / bugfix 的总结随 child Change 进入 `changes/<version>/<slug>/`。
  - HTML 链接由 CLI 随材料与对象 archive 改写；搬迁后核对链接仍有效。
- 每节使用实际结果、具体路径和理由；“完成开发 / 测试通过”不能替代完整记录。
- 内容要求如下；未执行的阶段明确写跳过原因，无法取得的历史证据如实标记缺失。

| 内容 | 必须记录 |
| --- | --- |
| 范围与结果 | 交付 kind、完整对象 ID、起点、目标、非目标、约束与实际验收结果 |
| 完整过程 | start、design、开发 / 测试、converge、审查、验证、hook、fact、close-out 的实际顺序 |
| 执行细节 | 参与者、并行分工、交接、失败、修复、重试、暂停与续办，以及阶段产物链接 |
| 设计决策 | 问题、候选、选择、理由、代价、确认依据；未采用方案与不需要 design 的理由 |
| 开发与测试 | 实现行为、关键路径、边界 / 错误处理、验收与 testcase 映射、未覆盖项 |
| 偏差与变更 | 计划与实际、原因、影响、接受记录、遗留风险、Bug / follow-up；无偏差也明确记录 |
| 审查与证据 | 各轮问题、裁定、修复复核、命令、suite、结果、报告路径与事实文档更新 |
| 收口与后续 | 集成 / 冲突处理、对象 outcomes、版本决策、目标分支 / tag / push 计划、后续事项 |

- Gitflow 前记录已完成过程与待执行收口；不得提前声称合并、tag 或 push 成功。
  - Gitflow 结果以实际命令及宿主最终报告为证据；总结链接 Change 和已有收口证据。
- 总结不替代 objectives 进度账本、当前事实文档、ADR 或测试报告。
- 主线前进或 bug close 导致补审补测时更新总结，再核对、提交并继续 Gitflow。
  - 已收口 release / hotfix 续办复用已归档总结，不覆盖已开始发布的源提交。
