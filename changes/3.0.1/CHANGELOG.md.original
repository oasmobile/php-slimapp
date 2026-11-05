# Changelog v3.0.1

本文件记录 v3.0.1 hotfix 的变更内容。

---

## 静态分析

- 引入 `phpstan/phpstan` ^2.1，配置 level 8 扫描 `src/`
- 修复全部 74 个 phpstan level 8 错误，baseline 清零
- 主要修复类型：
  - 为 array 属性/参数添加泛型标注（missingType.iterableValue）
  - 对 nullable 属性使用 assert 或局部变量确保类型安全（method.nonObject）
  - 处理 `file_get_contents`/`realpath`/`getcwd` 等返回 `string|false` 的情况（argument.type）
  - `getHelper('question')` 改用 assert QuestionHelper（method.notFound）
  - 去除冗余类型检查（function.alreadyNarrowedType, instanceof.alwaysTrue）
  - 动态生成的 SlimAppCachedContainer 使用 phpstan-ignore（class.notFound）
  - `prepareConfigYaml()` 补充 void 返回类型（missingType.return）

---

## 依赖升级

- `oasis/http` v3.1.0 → v3.2.0
  - 新增编程式路由注入 API（`MicroKernel::addRoute()` / `addRoutes()`）
  - boot 后路由冻结机制（写操作抛出 LogicException）
  - 修复 ISS-3.0-L01（编程式路由注入 API 缺失）和 ISS-3.0-L02（boot 后路由修改静默失效）
  - 对 slimapp 无 breaking change

---

## 测试覆盖

- PHPStan level 8：零错误
- 全量测试：171 tests, 2159 assertions（全部通过）
