# 3.2.2 发布目标

## 流程

本次只发布已经验收并合入 develop 的修复，不增加功能或运行时代码。

- needs_design: no
- has_dev: no

## 步骤

各阶段按实际结果自勾；发布前保留独立的用户确认。

- [ ] 确认工作线与范围（start）
- [x] integrate（不联调，无需执行）
- [ ] 完成预发布工作（owner；核对四份 child Change 与五项 Bug outcomes）
- [x] owner 开发（has_dev: no，无新开发）
- [x] converge（has_dev: no，无开发分支集成）
- [ ] lint
- [ ] code-review
- [ ] verify branch
- [ ] fact audit
- [ ] close-out

## 工作线

不联调。本次只在本仓库准备 patch 发布。

## 本版范围

用户于 2026-11-05 确认版本 3.2.2，基于当前 develop 创建 release/3.2.2。

- bug-2AN6：生成 ORM 工厂的支持 API 与 PHP 8.5 lazy objects。
- bug-GH7A：生成的单测 bootstrap 使用 Monolog Level。
- bug-Y68Q：非法配置缓存恢复。
- bug-P4KU：普通 fork 测试覆盖率显式请求与致命错误判定。
- bug-1MW9：覆盖率脚本失败状态及输出保留。
- 四份 child Change：mdf-init、v3-upgrade-review-bugs、v3-bug-reproduction-tests、bug-1mw9。

## 约束与准备

采用已确认的 release roster：owner 1、qa 0、dev 0、reviewer 3。
qa/dev 策略 best-of-n，review 策略 partition，不创建 qa/dev 角色分支。
依赖保持 composer.lock，PHP >=8.5、pcntl、Composer 2；不需要真实数据库或凭据。
由 Agent 在新 worktree 准备锁定开发依赖、独立 autoload 与本地验证内存配置，首次 lint 前就绪。
origin 的访问及 master 一致性在实际发布前核对；准备计划不代表网络或权限已经可用。
用户报告已完成人工验收；仍执行本次 release 的完整审查与验证。

## 预发布工作

核对四份 child Change 的最终 outcomes，避免历史 deferred 与已修复结果冲突。
保留历史阶段说明，补充发布时的最终结果，不伪造历史通过记录。
准备 3.2.2 发布说明、SemVer 理由和五项 Bug 独立关闭验证所需证据。

## 明确不含

- 不增加新功能、不升级依赖、不引入业务数据迁移。
- 不处理另外四条保留 bugfix 分支或删除已有 worktree。
- 不在用户确认最终发布结果前合入 master、创建 tag 或推送。

## 允许在本分支改什么

只整理本版发布记录、Bug 最终状态、当前事实及审查验证报告。
如发现必须修改生产实现或测试门槛的问题，先记录并按相关流程恢复开发，不把 has_dev:no 当作已修复证据。

## 可验证验收

审查基线固定为上一正式版本 v3.2.1，三名 reviewer 按范围分工覆盖完整发布变化。
lint、build、quick、release 套件必须通过，零 warning、skip 和空选择。
完整事实审计与 strict validation 通过，五项 Bug 按独立关闭流程验证。
发布前展示版本、范围、报告、目标分支、tag、push 与保留目录，请用户确认。
批准后 no-ff 合入 master、创建 v3.2.2 注释 tag、回合 develop，并按 MDF 契约发布。
