# MDF 初始化审阅报告

本报告记录已获用户确认的迁移结果、验证及启用方案；当前状态仍为 initializing。

## 范围与结论

本次为 migrate 内部委托的全量事实审阅，审阅已提交材料。

- 初始迁移基线：`9253667`；事实修正基线：`81453a5`。
- 24 份当前事实文档已逐页核对；根 README、PROJECT、GLOSSARY 及 Agent 入口已复核。
- 58 个实现与验证文件已按职责核对覆盖；框架 `src/` 的 13 个文件全部覆盖。
- 首轮 33 条 audit.uncovered 均已核对，相关行为由明确的事实 evidence 路径承载。
- 凭据 fixture 仅核对导入关系，不读取其值；该路径有带理由的 module ignore。
- 上游 Skills、Graphify 生成物和历史原文按已记录的 ignore 保留，不冒充当前实现事实。
- 第二轮全量 Audit：零 warning；唯一 finding 为 manifest.initializing。
- strict validation：唯一 finding 为 manifest.initializing，符合 MDF 初始化阶段允许项。
- 无未完成的语义 finding；ORM 模板限制已记录，未在此次初始化修复。

## 八项基线

八项基线均为 documented，没有使用占位页或虚构不适用理由。

| 基线 | 当前页面 |
| --- | --- |
| 术语 | [GLOSSARY.md](../../../GLOSSARY.md) |
| 用户指南 | [用户入口](../../../docs/user-guide/README.md) |
| 系统边界 | [边界与路由](../../../docs/system/overview.md) |
| 架构 | [当前架构](../../../docs/system/architecture/current.md) |
| 接口 | [内部接口](../../../docs/system/interfaces/internal.md) |
| 数据 | [缓存模型](../../../docs/system/data/cache.md) |
| 运维 | [框架运行与维护](../../../docs/system/operations/runbook.md) |
| 偏差 | [已知偏差](../../../docs/system/deviations.md) |

## 文档复核

每份主题已对照证据核对；不把历史归位视为旧版本重新验收。

| 分组 | 已复核页面 |
| --- | --- |
| 系统结构 | overview、architecture/current、interfaces/internal、interfaces/errors |
| 数据与运维 | data/cache、operations/configuration、observability、runbook、limits-and-recovery |
| 系统规则 | deviations、testing/index、testing/conventions |
| 用户入口与应用 | README、getting-started、configuration、service-container |
| 用户运行能力 | cli-commands、console、daemon-sentinel、http、logging |
| 用户升级 | migration-v2-to-v3、migration-data-and-tests、migration-orm |

## 审阅修正

本次修正仅对齐文档、验证配置和测试依赖分组，未改变框架运行实现。

- 修正 bin 的实际加载链、命名空间前提、日志模式和服务验证退出码说明。
- 缓存恢复文档明确生产容器缓存的新鲜度边界，以及清缓存保留点号条目。
- 迁移指南允许受支持的 XML 映射，修复拆页锚点，去掉无依据的兼容保证。
- HTTP 便捷方法归属 MicroKernel；原 README 的教程按主题归位。
- 历史发布、spec、Proposal 和旧规范保留原文；`.original` 不再成为活动指令入口。
- 保留 Graphify，并明确其可陈旧；不伪装成 CodeWiki。

## 验证命令与结果

五个入口已按 `.mdf/modules.yaml` 实际执行，使用 Core run 留存输出与报告。

| 入口 | 命令 | 结果 |
| --- | --- | --- |
| lint | `vendor/bin/phpstan analyse --no-progress --debug` | 无错误 |
| build | `git diff --check` | 通过 |
| quick | `vendor/bin/phpunit --testsuite quick --log-junit "$MDF_REPORT_DIR/junit.xml"` | 46 tests，1282 assertions |
| smoke | `vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"` | 192 tests，2199 assertions |
| release | `vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"` | 192 tests，2199 assertions |

JUnit 已解析核对：有 testcase、classname 非空、没有失败、错误或跳过。
运行器为 PHP 8.5.6、PHPUnit 13.1.8；依赖按现有 lock 恢复，lock 没有修改。

## 日志与排除边界

本地日志按 MDF 规则忽略，不作为必须随 Git 分发的产物。

- 验证输出及 XML：`.mdf/logs/20261029T0842*-init-entry-*/`。
- 最终全量 Audit：`.mdf/logs/20261029T084411106905000Z-fact-audit/`。
- 最终 strict validation：`.mdf/logs/20261029T084433952087000Z-validate/`。
- 语义核对日志：`.mdf/logs/*-review-*`、`*-audit-*`。
- 未运行人工工程生成、生产部署或旧版本发布验收。
- 未修改业务数据格式，不提供数据迁移脚本。

## 启用与分支方案

用户确认结束初始化后，只补验启用增量，不重新整理已确认的迁移方案。

1. 对照本报告核对提交与工作区，没有新的事实或配置变化。
2. 将 manifest.state 从 initializing 改为 ready，更新本次状态记录。
3. 运行 basic validation，要求零 finding，然后提交。
4. 保留现有本地 master 和 develop；当前 develop 不重置、不强行对齐 master。

最新已发布版本为 3.2.1，收口模式为 local；本次不推送、不修改 tag 或远端默认分支。
