# 3.2.2 Lint Report

## 结论

完整 lint 入口通过。PHPStan 无错误，MDF 代码规模检查零 finding。
报告位于本 worktree `.mdf/reports/20261105T080452892549000Z-lint`。

## 规模证据

原超限生成器按职责拆分；入口 647 行，四个 trait 分别为 99、165、90、121 行。
原 700 行拆分目标均满足，within_required_split_targets 为 true。
其余源码和测试文件及所属 package 均满足当前硬限制。
只读测量日志位于主仓库 `.mdf/logs/20261105T080520777178000Z-measure-release-template-split`。
其它实现测量日志为 `.mdf/logs/20261105T080521285950000Z-measure-release-other-code`。

## 环境

PHPStan 使用临时 PHPRC 的 512M 内存配置；未修改项目验证入口、测试门槛或系统配置。
本次不因历史阶段材料有变化而重跑无关入口。
