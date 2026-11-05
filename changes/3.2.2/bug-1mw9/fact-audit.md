# fact audit 范围审阅报告

## 结论与范围

审阅通过。fact update 完成事实对齐后，已按同一 branch 范围执行完整内部审计。
基线沿用 delivery.json 的 start_commit，覆盖五项修复合入后的当前 checkout。
20 份事实文档、9 个实现文件均已完成双向复核；无未触及项、未解决项或未处置 warning。

本次仅更新 15 份事实文档，没有修改实现、测试、验证配置或 ignore。
manifest 未配置 pre-gitflow-finish hook，无需执行。
本轮没有触发结构返工；内部审计第 1 轮即通过。

## 确定性检查

本节记录实际检查与完整日志位置，日志位于主仓库。

| 检查 | 结果 | 日志 |
| --- | --- | --- |
| fact-audit --scope branch | 退出码 0，零 finding、零 warning | `.mdf/logs/20261102T024923441461000Z-fact-audit` |
| validate --level strict | 退出码 0，零 finding | `.mdf/logs/20261102T024938569662000Z-validate` |
| git diff --check | 退出码 0 | `.mdf/logs/20261102T024919753079000Z-facts-diff-check` |

事实页在审计前已提交，evidence 新鲜度按提交历史核对，没有用文件时间伪造确认。
只改事实文档，按 fact update 契约无需重跑业务 suite；既有 branch 验证通过记录保留。
实现与文档范围均未被 ignore 排除。

## 文档复核

本节记录各页事实、证据、主题归属与写作结构的复核结论。

| 文档（docs/ 下） | 结论 |
| --- | --- |
| system/architecture/current.md | 四个模板 trait 的职责与入口一致，引用齐全 |
| system/data/cache.md | 非法或非数组缓存进入既有配置重建路径 |
| system/deviations.md | 本轮 ORM 已移除 API 偏差已撤下 |
| system/interfaces/errors.md | 异常分类保留，缓存恢复链接指向数据主题 |
| system/interfaces/internal.md | 单例、setter、容器和 Kernel 协作与源码一致 |
| system/operations/configuration.md | 配置装配、默认路径和缓存主题链接准确 |
| system/operations/limits-and-recovery.md | 区分配置缓存恢复与生产容器缓存清理 |
| system/operations/observability.md | Level 传递、handler 生命周期和文件模式准确 |
| system/testing/conventions.md | 覆盖率显式请求、INI 隔离、致命错误检查及生成 bootstrap 已记录 |
| system/testing/coverage-script-regression.md | 六场景命令与替身边界准确，未替代 smoke |
| system/testing/index.md | 仅作测试入口路由 |
| user-guide/cli-commands.md | 三条命令行为与退出语义准确，ORM 链接已修正 |
| user-guide/configuration.md | DataType 和参数访问示例准确，缓存恢复链接已补 |
| user-guide/getting-started.md | 生成目录和引导步骤准确，新增模板 evidence |
| user-guide/http.md | Kernel 创建、复用和属性重设语义准确 |
| user-guide/logging.md | Level 输入与 Console verbosity 映射准确 |
| user-guide/migration-data-and-tests.md | 枚举与 PHPUnit API 示例准确，未改变缓存格式 |
| user-guide/migration-orm.md | DriverManager、EntityManager 构造与原生 lazy objects 对齐 |
| user-guide/migration-v2-to-v3.md | ORM 旧限制与拆页链接已纠正，容器清理边界保留 |
| user-guide/service-container.md | 字符串或数组命名空间、工厂、public 前提对齐 |

已人工复核短句、术语一致性、证据和链接；没有把已修复问题或未执行计划写成当前事实。
未新增主题页或拆页；路由页继续只导航，可观察契约保留在主题叶。

## 实现覆盖与旧 warning

本节从全部九个实现文件反查文档覆盖，并核对旧警告。

| 实现 | 当前覆盖 |
| --- | --- |
| InitializeProjectCommand | 架构、快速开始、CLI 命令与迁移页 |
| ConfigurationTemplate | 架构与快速开始，直接 evidence 已补齐 |
| DatabaseTemplates | 架构、ORM 迁移与已知偏差 |
| ServicesTemplate | 架构与快速开始，直接 evidence 已补齐 |
| UnitTestTemplates | 架构与测试约定，Level::Critical 及直接 evidence 已补齐 |
| SlimApp | 缓存、接口、运维及使用方配置、日志、HTTP 页面 |
| run_all_coverage.sh | 测试约定与 coverage-script-regression |
| ForkProcessTest | 测试约定中的覆盖率请求与退出规则 |
| BugP4KUTest | 测试约定中的回归分类、INI 隔离及证据路径 |

三个旧 audit.uncovered warning 均已通过真实文档与 evidence 补齐解决，没有添加排除规则。
凭据 fixture 只核对加载关系，没有读取或写入配置值。

## 发现处置与交接

本节保留上轮失败到本轮通过的处置结果。

| 发现 | 处置 |
| --- | --- |
| FA-001：ORM 旧限制陈述 | 已改为现有 ORM 迁移规则链接，保留使用方数据库验证要求 |
| FA-002：模板引用与行为说明缺口 | 补齐三个模板引用、生成单测日志级别与 fork 请求边界 |
| FA-003：18 条 evidence.stale | 逐页按当前源码确认并提交；完整审计和 strict validation 均已消除 |
| FA-004：迁移页局部链接失效 | 改为实际拆出页面及其章节链接 |

首轮失败摘要为 18 条 stale、3 条 warning；原始输出仍保留在主仓库日志中。
失败日志为 `.mdf/logs/20261102T023614921988000Z-fact-audit`，没有删除或改写失败证据。
当前发现清单见 [机器记录](fact-audit-findings.json)。

fact audit 已完成；下一阶段为 close-out。
本轮没有合入 develop、推送、发版或关闭 Bug。
