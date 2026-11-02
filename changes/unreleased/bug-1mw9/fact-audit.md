# fact audit 范围审阅报告

## 结论

本轮审阅未通过。fact audit 保持未勾选，不能进入 close-out。
范围为 branch，基线沿用 delivery.json 的 start_commit，覆盖五项修复合入后的当前 checkout。
进入前已核对 code-review、verify branch 完成；manifest 未配置 pre-gitflow-finish hook，无需执行。

本次只读核对事实和实现，没有运行业务验证入口，也没有修改源码、测试或事实页。
调用方保存本报告；现有业务验证通过记录不因文档问题改写。

## 确定性检查

本节记录 CLI 的实际结果和完整日志位置。

| 检查 | 结果 | 主仓库日志 |
| --- | --- | --- |
| fact-audit --scope branch | 退出码 2；18 条 evidence.stale，3 条 audit.uncovered warning | `.mdf/logs/20261102T023614921988000Z-fact-audit` |
| validate --level strict | 退出码 2；18 条 evidence.stale | `.mdf/logs/20261102T023734496968000Z-validate` |

CLI 映射包含 9 个实现文件和 19 份事实文档，没有 ignore 排除。
另核对了全局检查报出的 cli-commands.md；它不在本轮 CLI 的 document_paths 中。
体积、散文结构和入口检查没有额外 CLI finding；不能据此豁免语义问题。

## 事实复核

本节记录文档陈述与源码的双向核对结论。

| 文档（docs/ 下） | 核对结论 |
| --- | --- |
| system/architecture/current.md | 组件关系成立；模板拆分后的实现引用需补齐，并处理 stale |
| system/data/cache.md | 非数组缓存回退到既有解析路径，与 SlimApp 相符 |
| system/deviations.md | 已移除本轮 ORM 旧 API 偏差，与修复后模板相符 |
| system/interfaces/errors.md | 已有异常分类未被本轮改变；evidence stale |
| system/interfaces/internal.md | 单例、属性分派、容器与 Kernel 接口相符；evidence stale |
| system/operations/configuration.md | init 装配顺序与默认缓存路径相符；evidence stale |
| system/operations/limits-and-recovery.md | 容器清理与部署边界保持；evidence stale |
| system/operations/observability.md | handler 生命周期与模式规则保持；evidence stale |
| system/testing/conventions.md | 分类与失败规则相符；需补普通 fork 的覆盖率 opt-in 说明与模板引用，evidence stale |
| system/testing/coverage-script-regression.md | 命令指向真实六场景测试，替身与真实覆盖率边界写明 |
| system/testing/index.md | 保持路由职责，新增链接有效 |
| user-guide/configuration.md | DataType 与点号配置访问示例相符；evidence stale |
| user-guide/getting-started.md | 引导、生成目录与入口相符；需核对拆分后引用，evidence stale |
| user-guide/http.md | Kernel 委托与参数注入保持；evidence stale |
| user-guide/logging.md | Level 与 verbosity 映射相符；evidence stale |
| user-guide/migration-data-and-tests.md | 当前 DataType、PHPUnit API 示例与本地依赖相符；evidence stale |
| user-guide/migration-orm.md | 已记录 DriverManager、构造函数和原生 lazy objects 修复 |
| user-guide/migration-v2-to-v3.md | ORM 限制陈述过时，拆页后的局部链接需修正；evidence stale |
| user-guide/service-container.md | 命名空间、public 与 app 工厂前提相符；evidence stale |
| user-guide/cli-commands.md（附加） | 三个命令及退出语义相符；全局检查报 evidence stale |

范围内 19 份文档及附加页面均已复核，没有应审而未触及的文档。
本轮没有扩展为全仓语义审阅；表外事实页仅由 strict validation 执行确定性检查。

## 实现覆盖与 warning 处置

本节从本轮九个实现文件反查事实页，并逐条处理三个 warning。

| 实现 | 覆盖与处置 |
| --- | --- |
| src/BuiltInCommands/InitializeProjectCommand.php | 生成入口与职责见快速开始、CLI 和架构；拆分后引用需补齐 |
| src/BuiltInCommands/Templates/ConfigurationTemplate.php | warning 1：生成 schema 有概括说明，但该文件没有直接 evidence；采纳为引用缺口 |
| src/BuiltInCommands/Templates/DatabaseTemplates.php | ORM 迁移页已引用并解释新 API；总迁移页旧限制须纠正 |
| src/BuiltInCommands/Templates/ServicesTemplate.php | warning 2：服务配置已有说明，但该文件没有直接 evidence；采纳为引用缺口 |
| src/BuiltInCommands/Templates/UnitTestTemplates.php | warning 3：缺直接 evidence，生成 bootstrap 的 Level::Critical 修正也缺事实说明；采纳 |
| src/SlimApp.php | 缓存页已解释非法缓存恢复；其余关联页需据当前源码确认并处理 stale |
| tests/run_all_coverage.sh | named suite 与测试约定覆盖退出码、输出及替身边界 |
| tests/ut/ForkProcessTest.php | 测试约定未说明 COVERAGE_FILE 显式请求边界，应补齐 |
| tests/ut/Regression/BugP4KUTest.php | 隔离 INI 与临时目录实现相符；测试约定 evidence 已过期 |

九个实现全部完成覆盖复核；三个 warning 均已裁定为文档补充项，尚未修复。
没有读取凭据 fixture 的配置值，没有新增 ignore 或降低测试门槛。

## 语义发现与后续处理

本节列出 fact update 需要处理的问题，避免将旧状态当成已修复。

1. FA-001：migration-v2-to-v3.md 末节仍称 ORM 模板使用已移除 API。
   DatabaseTemplates 已使用受支持 API，deviations 与 migration-orm 也已更新，总迁移页应同步。
2. FA-002：模板拆分后的三个实现没有直接事实 evidence；生成单测与普通 fork 的行为说明不完整。
   按职责补至现有主题页，不在路由页重复契约。
3. FA-003：strict validation 的 18 条 evidence.stale 仍存在。
   逐页核对后记录当前事实，不能只忽略检查或伪造通过。
4. FA-004：总迁移页步骤仍链接本页不存在的 `#doctrine-orm-3x` 与 `#phpunit-57--13`。
   对应内容已迁入独立主题页，应改为这些页面的真实链接。

措辞建议：将“当前限制”等泛指链接改为具体的“ORM 迁移”，避免继续暗示已修复缺陷仍存在。
本轮未发现需要新改生产实现的证据；这些结论不代替完整代码审查。

下一步执行 fact update 的 branch 范围修订，再重新进行完整事实审计。
本轮 next 在此结束；没有合入 develop、推送、发版或关闭 Bug。
