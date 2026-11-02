# Verification Report

## 结论与范围

scope: branch。全部 module 的正式验证通过，增量独立审查已完成。
实际 suites 为 quick、smoke；lint、build 也按原请求执行。

| 入口 | 结果 | 本工作区报告 |
| --- | --- | --- |
| lint | PHPStan 与代码规模检查通过，零 finding | `.mdf/reports/20261102T023226879256000Z-lint` |
| build | git diff --check 通过 | `.mdf/reports/20261102T023228771820000Z-build` |
| quick | 46 tests，1282 assertions | `.mdf/reports/20261102T023228815743000Z-quick` |
| smoke | 208 tests，2318 assertions，零失败、零错误、零跳过 | `.mdf/reports/20261102T023229116748000Z-smoke` |

原请求为 `python3 -B .agents/skills/mdf/scripts/mdf.py verify --repo . --scope branch`。
执行时 repo 指向当前 owner worktree；PHPRC 使用本地临时配置，将 PHPStan 内存上限设为 512M。
系统 PHP 配置未变。实际命令及退出码完整保存在 [机器报告](verification-report.json)。
named suite coverage-script-regression 另行通过 6 tests、31 assertions，不替代 branch 验证。
其报告为本工作区 `.mdf/reports/20261101T142120134945000Z-coverage-script-regression`。

## 失败修正与红绿证据

本节记录首轮环境错误和用户批准的修正。

首轮 smoke 为 207 通过、1 error。BugP4KUTest 的 parallel_fail 场景解析 JSON 时失败。
测试将主 INI 与扫描 INI 合并后，子进程未按空字符串环境变量隔离系统扫描目录。
memcached 因而重复加载，启动警告污染 JSON。

用户于 2026-11-02 批准使用每个测试专属的真实空目录。
补丁没有改动断言、预期、套件成员或失败规则；既有 tearDown 清理该目录。

| 证据 | 结果 | 本工作区路径 |
| --- | --- | --- |
| 首轮原报告副本 | 208 tests，1 error | `.mdf/reports/branch-before-ini-isolation.json` |
| 相同单场景修复前 | 复现 JSON 解析错误，退出码 2 | `.mdf/reports/ini-scan-single-red.xml` |
| 相同单场景修复后 | 1 test，19 assertions，退出码 0 | `.mdf/reports/ini-scan-single-green.xml` |
| 四场景回归 | 4 tests，58 assertions，退出码 0 | `.mdf/reports/ini-scan-regression-green.xml` |

quick 复现：已尝试用最小 proc_open --ini 探针隔离根因，证实真实空目录避免重复扫描。
该复现依赖主机扫描扩展和子进程启动环境，不适合作为纯 quick 单元测试。
正式自动回归保留在 smoke 的 BugP4KUTest；没有新增 quick 成员或声称已补 quick 测试。
探针日志位于主仓库 `.mdf/logs/20261101T142020027496000Z-diagnose-proc-open-ini-environment`。

## 架构审视与审查

本节说明修正边界与必要复审。

- ORM 与 Monolog 修正采用锁定依赖的受支持 API，不增加兼容层。
- 缓存修正先校验反序列化结果，再进入现有重建路径，不引入数据迁移。
- fork 与覆盖率脚本继续区分预期业务退出和运行时致命错误。
- INI 修正只影响测试环境隔离，保留生产逻辑和失败检查。
- 一人增量审查覆盖全部合并、配置和测试改动；未发现新问题，见 [审查终稿](code-review.md)。

本轮完成 verify branch；fact audit 与 close-out 未执行。
没有合入 develop、推送或发版。
