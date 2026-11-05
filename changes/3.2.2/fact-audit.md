# 3.2.2 Fact Audit Report

## 结论与范围

审阅通过。scope: branch，基线固定为上一正式版本 v3.2.1。
25 份事实页与 30 个实现文件均已完成双向复核，没有未触及项或未解决 finding。
入口文档保持导航职责，未把工作记录或计划写成当前行为。
按 module ignore 排除安装的上游 Skill、历史材料和可陈旧图谱；凭据 fixture 仅核加载关系。

## CLI 与校验

本节保留工具实际结果及日志，不把 warning 隐藏为零。

| 检查 | 结果 | 主仓库日志 |
| --- | --- | --- |
| fact-audit --scope branch | 零 finding；8 条精确路径匹配 warning，均逐项完成处置 | `.mdf/logs/20261105T081721700473000Z-fact-audit` |
| validate --level strict | 退出码 0，零 finding | `.mdf/logs/20261105T081736110016000Z-validate` |

首轮发现八个回归 fixture 引用缺口后，已在测试约定补充真实目录 evidence，并提交后重审同一范围。
Core coverage 的 covered 集合仅按文件路径精确相等计算，不展开目录，因此仍输出八条 warning。
主 Agent 核对了目录中的每个文件、调用关系和测试约定，确认均被该目录 evidence 支持。
这是按 fact audit 契约处置 warning，没有新增 ignore、删除检查或修改上游工具。
仅修改文档引用，不重跑已经通过的业务 suite。

## 逐页事实复核

本节记录文档到实现的语义结论；evidence 及 Git 新鲜度由 CLI 与人工共同核对。

| 页面 | 复核结论 |
| --- | --- |
| docs/system/architecture/current.md | 四个模板职责与当前装配关系一致 |
| docs/system/data/cache.md | 数组校验、配置缓存重建与容器缓存边界一致 |
| docs/system/deviations.md | 已撤下本轮修复的旧 ORM API 偏差 |
| docs/system/interfaces/errors.md | 异常与命令失败分类准确 |
| docs/system/interfaces/internal.md | 单例、属性、编译 Pass 与 Kernel 契约准确 |
| docs/system/operations/configuration.md | 配置加载与注入顺序准确 |
| docs/system/operations/limits-and-recovery.md | 进程前提与容器清理要求准确 |
| docs/system/operations/observability.md | handler、Level 与模式生命周期准确 |
| docs/system/operations/runbook.md | 库入口、人工集成入口与使用方责任清楚 |
| docs/system/overview.md | 只路由切面；五行核心模块及鉴权不适用理由属实 |
| docs/system/testing/conventions.md | suite、失败门槛与回归 fixture 证据完整 |
| docs/system/testing/coverage-script-regression.md | 六场景与命令替身边界准确 |
| docs/system/testing/index.md | 只导航测试规则与入口 |
| docs/user-guide/README.md | 只导航使用方任务 |
| docs/user-guide/cli-commands.md | 三个命令、生成器与服务验证退出语义准确 |
| docs/user-guide/configuration.md | 配置和参数访问、类型规则准确 |
| docs/user-guide/console.md | Console注册、告警与并行退出规则准确 |
| docs/user-guide/daemon-sentinel.md | 调度配置、默认值、并行和参数替换准确 |
| docs/user-guide/getting-started.md | 生成结构、引导与数据库验收边界准确 |
| docs/user-guide/http.md | Kernel委托与复用边界准确 |
| docs/user-guide/logging.md | Level输入与verbosity映射准确 |
| docs/user-guide/migration-data-and-tests.md | DataType与PHPUnit迁移示例准确 |
| docs/user-guide/migration-orm.md | 受支持 ORM API、构造与原生 lazy objects 准确 |
| docs/user-guide/migration-v2-to-v3.md | 旧限制与拆页链接已修正，保留缓存清理要求 |
| docs/user-guide/service-container.md | 命名空间、工厂和public服务前提准确 |

## 实现覆盖与 warning

本节从全部实现反查事实归属，并逐项处理 warning。

八项回归辅助实现的作用如下；均位于测试约定明确引用的目录中。

| fixture | 作用与处置 |
| --- | --- |
| BugReproductionTestCase.php | 隔离临时目录、子进程日志与清理；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| GeneratedProject.php | 执行真实生成器，复用锁定依赖并禁用网络安装；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| GeneratedSmokeCase.php | 确认生成 bootstrap 后实际进入测试函数；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| config_cache.php | fresh 前提、四种缓存及磁盘重建核对；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| coverage_environment.php | 确认 pcntl 与未启用覆盖率驱动的前置条件；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| fork_failure_evidence.php | 提取真实 fork 结果，验证业务 255 与致命错误边界；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| generated_autoload.php | 临时生成工程的本地 PSR-4 加载桥接；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |
| generated_orm.php | 执行生成 ORM 工厂而不连接真实数据库；已由测试约定的 Fixtures/ 目录 evidence 覆盖 |

其余 22 个实现均被现有事实页直接 evidence 引用。
完整的实现到文档映射见本目录 fact-audit-findings.json；没有未覆盖行为或未处置 warning。
人工核对短句、主题归属和当前行为表述，没有新增结构 finding；未作 ASD-STE100 符合性声明。

## 交接

本节区分发布准备与实际发布。

没有配置 pre-gitflow-finish hook，无需执行。
三人代码审查与正式 release 验证通过，事实审计已完成。
五项 Bug 的逐例报告已经准备，独立关闭及版本目录归档在用户确认后的 close-out 执行。
尚未修改 master、创建 tag 或推送。
