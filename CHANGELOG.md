# Changelog

## [3.2.2] - 2026-11-05

### Fixed

- 修正 PHP 8.5 工程生成器的 Doctrine ORM 工厂和 Monolog 日志级别。
- 损坏或非数组配置缓存按既有解析路径重建。
- 普通 fork 测试不再强制依赖覆盖率驱动。
- 覆盖率脚本保留失败状态，并区分预期业务退出和致命错误。

## 3.2.1 - 2026-05-10

升级 oasis/utils ^3.2、oasis/http ^3.8。详见 [3.2.1 发布记录](changes/3.2.1/CHANGE.md)。

## 3.2.0 - 2026-05-06

修复脚手架模板适配 Doctrine ORM 3.x；迁移文档全面重构。详见 [3.2.0 发布记录](changes/3.2.0/CHANGE.md)。

## 3.1.0 - 2026-05-06

升级 oasis/http v3.2.0 → v3.6.3，获得恢复的 Silex 便捷方法（before/after/error/render/json 等）。详见 [3.1.0 发布记录](changes/3.1.0/CHANGE.md)。

## 3.0.1 - 2026-05-05

引入 phpstan level 8 静态分析并修复全部 74 个错误；升级 oasis/http 至 v3.2.0。详见 [3.0.1 发布记录](changes/3.0.1/CHANGE.md)。

## 3.0.0 - 2025-07-14

PHP 8.5 大版本升级：依赖全面升级至 Symfony ^8.0 / PHPUnit ^13，源码现代化，HTTP Kernel 迁移至 MicroKernel，DI 容器改为默认 private，引入 PBT。详见 [3.0.0 发布记录](changes/3.0.0/CHANGE.md)。
