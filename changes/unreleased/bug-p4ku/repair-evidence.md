# bug-P4KU 红灯与修复证据

## 修复前

Agent 按用户 2026-10-31 的明确授权执行复现，确认失败来自本 Bug。
JUnit 报告：`.mdf/reports/bug-P4KU-red.xml`。

## 修复后

同一 Bug 的正式复现用例现已通过，JUnit 报告：`.mdf/reports/bug-P4KU-green.xml`。
完整命令与进程输出保存在主仓库 `.mdf/logs/`，用例子进程日志保存在本工作区 `.mdf/reports/`。

## 验证边界

本分支只修复 bug-P4KU，不宣称其它四项已修复。
完整 smoke 仍包含其它已知缺陷；后续按实际结果记录，不降低门槛或伪造整体验收。
当前仅勾选 start 与 owner 开发，其余阶段由实际执行者核对后自勾。
