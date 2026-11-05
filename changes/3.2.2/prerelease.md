# 3.2.2 预发布核对

## 版本与范围

本节记录用户于 2026-11-05 确认的 patch 发布范围。

- 上一正式版本：3.2.1；目标版本：3.2.2。
- 包含 mdf-init、v3-upgrade-review-bugs、v3-bug-reproduction-tests、bug-1mw9 四份 child Change。
- 五项 Bug 的最终 fixed outcome 统一由 bug-1mw9 Change 持有。
- 旧登记与测试阶段 Change 的 deferred 已清空，历史叙述保留并补充最终归类说明。
- 不新增运行时功能，不改变 composer.json、composer.lock 或业务数据格式。

## SemVer 判断

本节说明采用 patch 的依据。

运行时变化修复已有生成器与缓存恢复错误，没有引入新的对外能力或声明新的破坏性契约。
模板职责拆分、回归测试与 MDF 工具、文档材料随本版发布，不改变依赖版本。
四份 child Change 均声明 breaking:false；MDF 初始化的 feature 标签不代表新增框架运行时功能。
用户明确要求 patch，并已确认 3.2.2。

## 验证准备与边界

本节记录新 worktree 的准备方式与发布前剩余工作。

锁定 vendor 从本地已安装目录复制，并在新 worktree 重新生成 autoload。
PHPStan 使用本地 PHPRC 的 512M 内存上限，不修改系统配置。
三名 reviewer 按 partition 覆盖从 v3.2.1 起的全部适用变化，不复用 child 审查代替发布审查。
必须通过 lint、build、quick、release 与事实审计。
五项 Bug 的正式复现报告将供收口阶段独立关闭流程逐例核对，不在此提前改状态。
实际 master 合并、tag、回合 develop 与推送，均等待最终发布确认。

## 历史与材料复核

本节记录发布审查前后确认的历史结构问题。

本地 v3.2.1 在 master 历史，但未在原 develop 祖先链中。
已仅向 release 合入该正式发布历史；与合入前文件树完全相同，没有覆盖修复。
四份没有独立 CHANGE.md 的来源修复材料已移入 bug-1mw9/source-deliveries，保持四份正式 child Change 范围。
文件链接按搬迁后的真实位置改写，来源分支及独立 worktree 未变。
