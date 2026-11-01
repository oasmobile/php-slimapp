# 分支验收现场

## 已完成

用户于 2026-11-01 确认新增 named suite，并将另外四条已审修复分支合入当前分支。
四条来源分支均已成为当前分支祖先，关键实现内容逐项核对一致，见 integration-sources.json。
named suite 的六个用例通过；套件文档的显式目的已补齐，basic validation 零 finding。

## 首轮验证结果

正式 branch 已执行；lint、build、quick 通过，quick 为 46 tests、1282 assertions。
smoke 为 208 tests、207 通过、1 error；原始失败保存在 verification-report.json。
失败为 BugP4KUTest 的 parallel_fail 场景解析 JSON 时出现 Syntax error。
该单场景已独立复测并复现，报告位于本工作区 `.mdf/reports/ini-scan-single-red.xml`。

## 根因与待批准修正

proc_open 启动子进程时，空字符串形式的 PHP_INI_SCAN_DIR 未按预期隔离系统扫描目录。
测试已合并主配置与扫描配置，子进程重复扫描后再次加载 memcached，启动警告污染 JSON 输出。
独立探针证实：指定真实空目录时不再扫描系统配置，也不再出现重复加载警告。

最小补丁只将空字符串改为每个测试的专属空目录，不改断言、预期、套件成员或失败规则。
补丁已准备并通过 apply --check；因 MDF verify 要求修改既有测试设施先取得批准，暂未应用。

## 边界与续办

verify branch、code-review 和后续阶段保持未勾，没有合入 develop、推送或发版。
取得测试修改批准后，先复测同一单场景，再运行原完整 branch 请求，转绿后做一人增量复审。
原 scope、原命令和最早待审左端点保存在 objectives，不能用 named 或临时副本通过代替。
