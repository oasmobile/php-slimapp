# 分支验收环境错误记录（已解决）

## 已完成

用户于 2026-11-01 确认新增 named suite，并将另外四条已审修复分支合入当前分支。
四条来源分支均已成为当前分支祖先，关键实现内容逐项核对一致，见 integration-sources.json。
named suite 的六个用例通过；套件文档的显式目的已补齐，basic validation 零 finding。

## 首轮验证结果

正式 branch 已执行；lint、build、quick 通过，quick 为 46 tests、1282 assertions。
smoke 为 208 tests、207 通过、1 error；原始失败保存在本工作区 `.mdf/reports/branch-before-ini-isolation.json`。
失败为 BugP4KUTest 的 parallel_fail 场景解析 JSON 时出现 Syntax error。
该单场景已独立复测并复现，报告位于本工作区 `.mdf/reports/ini-scan-single-red.xml`。

## 根因与已批准修正

proc_open 启动子进程时，空字符串形式的 PHP_INI_SCAN_DIR 未按预期隔离系统扫描目录。
测试已合并主配置与扫描配置，子进程重复扫描后再次加载 memcached，启动警告污染 JSON 输出。
独立探针证实：指定真实空目录时不再扫描系统配置，也不再出现重复加载警告。

最小补丁只将空字符串改为每个测试的专属空目录，不改断言、预期、套件成员或失败规则。
用户于 2026-11-02 批准并已应用补丁。同一失败场景通过（1 test / 19 assertions），四场景回归通过（4 tests / 58 assertions）。报告为本工作区 `.mdf/reports/ini-scan-single-green.xml` 和 `.mdf/reports/ini-scan-regression-green.xml`。

## 最终状态

环境隔离错误已解决；原完整 branch 请求已通过，一人增量审查已完成。
code-review 和 verify branch 已完成，证据见 verification-report.md。
fact audit 和 close-out 尚未执行，没有合入 develop、推送或发版。
