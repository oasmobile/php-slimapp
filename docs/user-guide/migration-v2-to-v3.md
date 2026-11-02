---
title: "从 SlimApp 2.x 升级"
doc_type: user-guide
evidence:
  - path: "composer.lock"
  - path: "composer.json"
  - path: "src/SlimApp.php"
  - path: "src/SlimAppCompilerPass.php"
  - path: "src/SentinelCommand/DaemonSentinelCommand.php"
  - path: "src/BuiltInCommands/InitializeProjectCommand.php"
---

# 从 SlimApp 2.x 升级

本文档面向 `oasis/slimapp` 下游项目维护者，提供从 2.x 升级到 3.0 的完整迁移指引。

---

## 前置条件

| 条件 | 要求 | 验证方式 |
|------|------|----------|
| PHP 版本 | >=8.5 | `php -v` |
| Composer | >=2.x | `composer --version` |

---

## 升级步骤

按顺序执行。每步标注了对应的详细说明章节。

1. 确认 PHP >=8.5
2. 更新 `composer.json` 中的依赖版本（→ [附录：依赖版本对照表](#附录依赖版本对照表)）
3. `composer update`
4. 替换代码中的 `SilexKernel` → `MicroKernel`（→ [SilexKernel → MicroKernel](#silexkernel--microkernel)）
5. 为 `getService()` 获取的服务添加 `public: true`（→ [DI 容器 private-by-default](#di-容器-private-by-default)）
6. 适配 Doctrine ORM 3.x（如启用 ORM）（→ [Doctrine ORM 迁移](migration-orm.md)）
7. 适配 Sentinel 基类移除（如有子类）（→ [AbstractDaemonSentinelCommand 移除](#abstractdaemonsentinelcommand-移除)）
8. 给 `sentinel.yml` 中的 `%param%` 值加双引号（→ [sentinel.yml 引号](#sentinelyml-引号)）
9. 适配 PHPUnit 13（→ [数据访问和测试迁移](migration-data-and-tests.md#phpunit-57--13)）
10. 清除旧缓存：`./bin/<project>.php slimapp:cache:clear`
11. 验证服务：`./bin/<project>.php slimapp:services:validate`
12. 运行业务测试套件，确认无回归

---

## 框架 API 变更

### SilexKernel → MicroKernel

`oasis/http` v3.0 将基于 Silex 的 `SilexKernel` 替换为基于 Symfony HttpKernel 的 `MicroKernel`。

将所有 `SilexKernel` 引用替换为 `MicroKernel`：

```php
// Before
use Oasis\Mlib\Http\SilexKernel;

// After
use Oasis\Mlib\Http\MicroKernel;
```

以下是迁移时应核对的 MicroKernel 接口；使用方仍须运行自己的兼容性测试：

| 方法 | 说明 |
|------|------|
| `addControllerInjectedArg(object $arg): void` | 注入控制器参数 |
| `addExtraParameters(array $params): void` | 注入额外参数 |
| `run(?Request $request = null): void` | 启动 HTTP 处理 |
| `getCacheDirectories(): array` | 返回缓存目录列表 |

当前安装的 `oasis/http` 提供以下便捷方法；使用方仍须核对签名和业务兼容性：

| 方法 | 说明 |
| --- | --- |
| `render($view, $params, $response)` | 渲染 Twig 模板返回 Response |
| `renderView($view, $params)` | 渲染 Twig 模板返回字符串 |
| `path($route, $params)` | 生成相对 URL |
| `url($route, $params)` | 生成绝对 URL |
| `before($callback, $priority, $masterRequestOnly)` | 注册 before 过滤器 |
| `after($callback, $priority, $masterRequestOnly)` | 注册 after 过滤器 |
| `error($callback, $priority)` | 注册 error handler |
| `view($callback)` | 注册 view handler |
| `abort($statusCode, $message, $headers)` | 抛出 HttpException |
| `redirect($url, $status)` | 创建重定向响应 |
| `json($data, $status, $headers)` | 创建 JSON 响应 |
| `stream($callback, $status, $headers)` | 创建流式响应 |
| `sendFile($file, $status, $headers, $contentDisposition)` | 创建文件下载响应 |

**自查**：`grep -rn 'SilexKernel' src/`

---

### DI 容器 private-by-default

2.x 中所有服务自动 public。3.0 遵循 Symfony 标准，服务默认 private。

**影响**：通过 `$app->getService('xxx')` 获取的服务，如果 `services.yml` 中未声明 `public: true`，会抛出 `ServiceNotFoundException`。

```yaml
# 需要通过 getService() 获取的服务，须显式声明
services:
    my.service:
        class: App\MyService
        public: true
```

> `app` 服务保持 public，无需改动。纯通过构造函数注入使用的服务也无需改动。

**自查**：

```bash
grep -rn 'getService(' src/
```

列出所有被获取的 service ID，逐一确认 `services.yml` 中是否声明了 `public: true`。

---

### AbstractDaemonSentinelCommand 移除

`AbstractDaemonSentinelCommand` 已被移除，`DaemonSentinelCommand` 直接继承 `AbstractAlertableCommand`。

```php
// Before
use Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand;
class MySentinel extends AbstractDaemonSentinelCommand { ... }

// After
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;
class MySentinel extends DaemonSentinelCommand { ... }
```

> 如果直接使用 `DaemonSentinelCommand`（未继承），无需改动。

---

## 配置文件变更

### `services.yml`

见上方 [DI 容器 private-by-default](#di-容器-private-by-default)。

---

### `sentinel.yml` 引号

Symfony 8.0 YAML 解析器对 `%` 保留字符更严格。以 `%` 开头的标量必须加引号；`$PARALLEL_INDEX` 也建议加引号：

```yaml
# Before — 3.0 中会抛出解析异常
commands:
    my_command:
        args:
            a: %app.name%
            --idx: $PARALLEL_INDEX
        once: %app.once%

# After
commands:
    my_command:
        args:
            a: "%app.name%"
            --idx: "$PARALLEL_INDEX"
        once: "%app.once%"
```

功能不变，仅语法要求更严格。

---

## 上游依赖变更

### Doctrine ORM

数据库适配步骤见[Doctrine ORM 迁移](migration-orm.md)。

### 数据访问与测试 API

DataType 与 PHPUnit 升级见[数据访问和测试迁移](migration-data-and-tests.md)。

## 常见报错速查

| 报错信息 | 原因 | 解决 |
|----------|------|------|
| `Class "Oasis\Mlib\Http\SilexKernel" not found` | oasis/http 3.0 移除了 SilexKernel | → [SilexKernel → MicroKernel](#silexkernel--microkernel) |
| `ServiceNotFoundException: ... has been removed from the container` | 服务未声明 public | → [DI 容器 private-by-default](#di-容器-private-by-default) |
| `The reserved indicator "%" cannot start a plain scalar` | sentinel.yml 中 `%param%` 未加引号 | → [sentinel.yml 引号](#sentinelyml-引号) |
| `Class "Doctrine\ORM\Tools\Setup" not found` | ORM 3.x 移除了 Setup 类 | → [Annotation → Attribute](migration-orm.md#annotation--attribute) |
| `Class "Doctrine\Common\Cache\MemcachedCache" not found` | doctrine/cache 已移除 | → [Doctrine\Common\Cache 移除](migration-orm.md#doctrinecommoncache-移除) |
| `ConsoleRunner::createHelperSet() not found` | ORM 3.x 移除了该方法 | → [ORM 命令集注册](migration-orm.md#orm-命令集注册) |
| `DataProviderInterface::STRING_TYPE not found` | oasis/utils 3.0 改为枚举 | → [oasis/utils DataType 枚举](migration-data-and-tests.md#oasisutils-datatype-枚举) |
| `Class "Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand" not found` | 基类已移除 | → [AbstractDaemonSentinelCommand 移除](#abstractdaemonsentinelcommand-移除) |

---

## 附录：依赖版本对照表

### require

| 依赖 | 2.x 版本 | 3.0 版本 |
|------|----------|----------|
| `php` | >=7.0 | >=8.5 |
| `symfony/dependency-injection` | ^4.0 | ^8.0 |
| `symfony/config` | ^4.0 | ^8.0 |
| `symfony/console` | ^4.0 | ^8.0 |
| `symfony/finder` | ^4.0 | ^8.0 |
| `symfony/filesystem` | ^4.0 | ^8.0 |
| `oasis/logging` | ^1.2.0 | ^3.0 |
| `oasis/utils` | ^1.6 | ^3.0 |
| `oasis/http` | ^2.0 | ^3.0 |

### require-dev

| 依赖 | 2.x 版本 | 3.0 版本 |
|------|----------|----------|
| `phpunit/phpunit` | ^5.7 | ^13 |
| `doctrine/orm` | ^2.5 | ^3.6 |
| `oasis/aws-wrappers` | ^2.2.1 | ^3.0 |
| `oasis/dynamodb-odm` | ^1.0 | ^2.0 |
| `oasis/doctrine-addon` | ^2.0.2 | ^3.1 |
| `giorgiosironi/eris` | — | ^1.1（新增） |

### 配置文件兼容性

| 配置文件 | 兼容性 | 说明 |
|----------|--------|------|
| `config.yml` | ✅ 无缝兼容 | 格式由使用方 `ConfigurationInterface` 定义，框架侧无变化 |
| `routes.yml` | 需核对 | 按安装版本的 MicroKernel 路由格式及使用方测试核对 |
| `sentinel.yml` | ⚠️ 需加引号 | 详见 [sentinel.yml 引号](#sentinelyml-引号) |
| `services.yml` | ⚠️ 需加 public | 详见 [DI 容器 private-by-default](#di-容器-private-by-default) |

> 升级前清理旧配置与 HTTP 缓存，再启动新版本。生产模式下容器缓存不检查资源变更，不能依赖首次启动自动重建。

## 工程生成器与缓存核对

当前生成器的 ORM 工厂适配规则见[ORM 迁移](migration-orm.md#entitymanager-工厂)。
生成后仍须验证使用方数据库适配，不能仅凭生成成功认定业务工程可运行。
配置缓存的内容校验见[缓存数据](../system/data/cache.md)；它不替代升级时的容器缓存清理。
