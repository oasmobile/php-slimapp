# bug-P4KU 收敛报告

## 结论

本阶段通过：已提交开发，目标回归和 smart 全部通过。
solo 无 qa/dev 角色；不执行 roster-join。bugfix 不自动执行 coverage 门槛。

## 规模前置

基线生成器 1076 行超过 1000 行硬限制，按已授权方案提取原有模板方法。
主类 647 行，四个 trait 为 99、164、90、121 行，均满足原拆分目标 700 行。
五个方法正文与原版逐字一致，不包含其它 Bug 的行为修复。

## 执行证据

以下命令均已实际执行，报告保留在 MDF 忽略目录。

| 检查 | 结果 | 报告 |
| --- | --- | --- |
| BugP4KUTest，模板提取后 | 4 tests、54 assertions，通过 | 本工作区 `.mdf/reports/bug-P4KU-post-extraction.xml` |
| smart lint | PHPStan 无错误，规模零 finding | 主仓库 `.mdf/reports/20261031T044144269164000Z-lint` |
| smart build | git diff --check 通过 | 主仓库 `.mdf/reports/20261031T044147755079000Z-build` |
| smart quick | 46 tests、1282 assertions，通过 | 主仓库 `.mdf/reports/20261031T044147800084000Z-quick` |
| 显式子进程覆盖率模式 | 4 tests、6 assertions，通过 | 本工作区 `.mdf/reports/bug-P4KU-explicit-coverage.xml` |

smart 命令为 `mdf.py verify --scope smart --module default --repo <本工作区>`。
PHPRC 使用本工作区 `.mdf/tmp/2026-10-31-p4ku-verification/php.ini`，仅为验证进程将内存设为 512M。
该配置保留当前 ARM PHP 扩展，不修改系统配置、测试断言或验证门槛。

## 显式覆盖率证据

将 COVERAGE_FILE 设为非空运行原 ForkProcessTest，验证四个场景均可生成覆盖率。
四份产物均由 Unserializer 成功读取为 ProcessedCodeCoverageData，每份包含 16 个 covered files。
证据保留在本工作区 `.mdf/reports/bug-P4KU-explicit-coverage-data/`。

- parallel_ok：11970 bytes。
- parallel_fail：11970 bytes。
- sentinel_once：14346 bytes。
- sentinel_parallel：14346 bytes。

普通模式及显式模式的完整命令和输出分别在主仓库 `.mdf/logs/` 中。
显式运行日志为 `20261031T044204376095000Z-p4ku-explicit-coverage-regression`。
产物解析日志为 `20261031T044224966275000Z-p4ku-inspect-produced-coverage`，未重跑测试。

## 边界

未运行整套 smoke、code-review 或收口，不宣称其它四项 Bug 已修复。
本阶段只勾选 converge；后续 lint 独立执行。
