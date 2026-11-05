# Changelog v3.1.0

本文件记录 v3.1.0 hotfix 的变更内容。

---

## 依赖升级

- `oasis/http` v3.2.0 → v3.6.3
- `oasis/utils` v3.0.2 → v3.1.0
- `oasis/logging` v3.1.0 → v3.1.1

---

## oasis/http 变更摘要（v3.2.1 ~ v3.6.3）

| 版本 | 类型 | 内容 |
|------|------|------|
| v3.2.1 | hotfix | 修复 `AccessDecisionManager` 缺少 `AuthenticatedVoter`，`isGranted('IS_AUTHENTICATED_FULLY')` 认证后仍返回 false |
| v3.3.0 | feature | Silex 迁移行为审计 + 场景测试加固（7 模块 + 聚合层），恢复 error handler 异常类型过滤 |
| v3.3.1 | hotfix | 文档修正：channel enforcement 已恢复 |
| v3.4.0 | feature | 恢复 `render()` / `renderView()` / `path()` / `url()` 便捷方法 |
| v3.5.0 | feature | 恢复 `before()` / `after()` / `error()` 便捷方法 |
| v3.6.0 | feature | 恢复 `view()` / `abort()` / `redirect()` / `json()` / `stream()` / `sendFile()` 便捷方法 |
| v3.6.1 | patch | 测试加固，覆盖率 87.85% → 94.91% |
| v3.6.2 | patch | 提取 `createAwsIpRangesClient()` 工厂方法 |
| v3.6.3 | patch | MicroKernel 内部重构为 Kernel/ 子 namespace traits，公共 API 无变更 |

### 对 slimapp 的影响

- 无 breaking change
- 下游项目可通过 `$app->getHttpKernel()` 直接使用恢复的 Silex 便捷方法（`before()` / `after()` / `error()` / `render()` / `json()` 等）

---

## 测试覆盖

- 全量测试：192 tests, 2185 assertions（全部通过）
- phpstan level 8：零错误
- 覆盖率：97.87%
