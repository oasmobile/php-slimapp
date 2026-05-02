# Migration Guide: slimapp 2.x → 3.0

本文档面向 `oasis/slimapp` 下游项目维护者，提供从 2.x 升级到 3.0 的完整迁移指引。

---

## 依赖变更清单

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

---

## 配置文件兼容性

| 配置文件 | 兼容性 | 说明 |
|----------|--------|------|
| `config.yml` | ✅ 无缝兼容 | 格式由使用方 `ConfigurationInterface` 定义，框架侧无变化 |
| `routes.yml` | ✅ 无缝兼容 | MicroKernel 保持与 SilexKernel 等价的路由解析接口 |
| `sentinel.yml` | ⚠️ 可能需调整引号 | CommandConfiguration schema 无变化，但 YAML 语法要求更严格（详见下方说明） |
| `services.yml` | ⚠️ 需手动调整 | 通过 `getService()` 获取的服务须显式声明 `public: true`（详见 Breaking Change 3） |

> 缓存文件（`container.php`、`config.cache`）因 Symfony 8.0 序列化格式变化不兼容旧缓存，升级后首次运行会自动重建，或手动执行 `slimapp:cache:clear`。

### `sentinel.yml` 引号问题

Symfony 8.0 的 YAML 解析器对 `%` 保留字符的处理更严格。2.x 中可以不加引号的 `%param%` 参数引用和 `$PARALLEL_INDEX` 变量，在 3.0 中必须用双引号包裹，否则 `Yaml::parse()` 会抛出异常：

```
The reserved indicator "%" cannot start a plain scalar; you need to quote the scalar
```

**Before (2.x)** — 不加引号可正常解析：

```yaml
commands:
    my_command:
        name: my:command
        args:
            a: %app.name%
            --idx: $PARALLEL_INDEX
        once: %app.once%
```

**After (3.0)** — 必须用双引号包裹含 `%` 或 `$` 的值：

```yaml
commands:
    my_command:
        name: my:command
        args:
            a: "%app.name%"
            --idx: "$PARALLEL_INDEX"
        once: "%app.once%"
```

> `%param%` 参数替换和 `$PARALLEL_INDEX` 变量替换的功能本身不变，仅 YAML 语法要求更严格。

---

## Breaking Changes

### 1. PHP 版本要求

PHP 最低版本从 >=7.0 提升至 >=8.5。

升级前请确认运行环境的 PHP 版本：

```bash
php -v
```

### 2. HTTP Kernel 变更（SilexKernel → MicroKernel）

`oasis/http` v3.0 将基于 Silex 的 `SilexKernel` 替换为基于 Symfony HttpKernel 的 `MicroKernel`。

**影响范围**：

- `SlimApp::getHttpKernel()` 返回类型从 `Oasis\Mlib\Http\SilexKernel` 改为 `Oasis\Mlib\Http\MicroKernel`
- 使用方代码中对 `SilexKernel` 的类型提示、`instanceof` 检查、import 语句均需更新

**迁移方式**：

将所有 `SilexKernel` 引用替换为 `MicroKernel`：

```php
// Before (2.x)
use Oasis\Mlib\Http\SilexKernel;
$kernel = $app->getHttpKernel(); // 返回 SilexKernel

// After (3.0)
use Oasis\Mlib\Http\MicroKernel;
$kernel = $app->getHttpKernel(); // 返回 MicroKernel
```

MicroKernel 提供与 SilexKernel 等价的公共 API：

| 方法 | 说明 |
|------|------|
| `addControllerInjectedArg(object $arg): void` | 注入控制器参数 |
| `addExtraParameters(array $params): void` | 注入额外参数 |
| `run(?Request $request = null): void` | 启动 HTTP 处理 |
| `getCacheDirectories(): array` | 返回缓存目录列表 |

### 3. DI 容器可见性变更（private-by-default）

2.x 中 `SlimAppCompilerPass` 会将所有服务强制设为 public。3.0 移除了此行为，服务可见性遵循 Symfony 标准的 private-by-default 约定。

**影响范围**：

- `getService()` 仅能获取显式声明为 `public: true` 的服务
- 调用 `getService()` 获取未声明为 public 的服务将抛出 `ServiceNotFoundException`
- `getServiceIds()` 仅返回 public 服务的 ID 列表

**`app` 服务**：`app` 服务保持 public，`getService('app')` 仍可正常使用。但建议逐步迁移到构造函数注入：

```yaml
# 推荐：通过构造函数注入获取 app 实例
services:
    my.service:
        class: App\MyService
        arguments:
            - "@app"
```

#### `services.yml` 升级示例

**Before (2.x)** — 所有服务自动 public，可直接通过 `getService()` 获取：

```yaml
services:
    my.service:
        class: App\MyService
        arguments:
            - "@another.service"
```

**After (3.0)** — 如果代码中通过 `$app->getService('my.service')` 获取，须显式声明 `public: true`：

```yaml
services:
    my.service:
        class: App\MyService
        public: true
        arguments:
            - "@another.service"
```

> 纯通过构造函数注入使用的服务无需改动。

#### 自查 Checklist

1. 在项目代码中搜索所有 `getService(` 调用：
   ```bash
   grep -rn 'getService(' src/
   ```
2. 列出所有被获取的 service ID
3. 逐一确认这些 service ID 在 `services.yml` 中是否声明了 `public: true`
4. 未声明的须添加 `public: true`，或改为构造函数注入（推荐）

### 4. AbstractDaemonSentinelCommand 移除

`AbstractDaemonSentinelCommand` 已被移除。`DaemonSentinelCommand` 现在直接继承 `AbstractAlertableCommand`，并内联了所有 sentinel 执行逻辑。

**迁移方式**：

- 如果项目中有自定义类继承 `AbstractDaemonSentinelCommand`，改为继承 `DaemonSentinelCommand`
- 如果直接使用 `DaemonSentinelCommand`（未继承），无需改动

```php
// Before (2.x)
use Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand;

class MySentinel extends AbstractDaemonSentinelCommand { ... }

// After (3.0)
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class MySentinel extends DaemonSentinelCommand { ... }
```

### 5. PHPUnit 升级（5.7 → 13）

使用方项目的测试套件需要适配 PHPUnit 13 API。主要变更：

| 旧 API (PHPUnit 5.7) | 新 API (PHPUnit 13) |
|----------------------|---------------------|
| `\PHPUnit_Framework_TestCase` | `\PHPUnit\Framework\TestCase` |
| `setExpectedException(Class)` | `expectException(Class)` |
| `setExpectedException(Class, msg)` | `expectException(Class)` + `expectExceptionMessage(msg)` |
| `assertInternalType('array', $v)` | `assertIsArray($v)` |
| `assertInternalType('string', $v)` | `assertIsString($v)` |
| `assertInternalType('int', $v)` | `assertIsInt($v)` |
| `assertInternalType('bool', $v)` | `assertIsBool($v)` |
| `assertContains($needle, $string)` | `assertStringContainsString($needle, $string)` |
| `assertFileNotExists($path)` | `assertFileDoesNotExist($path)` |
| `getMockBuilder(X)->getMock()` | `createMock(X)` 或 `createStub(X)` |
| `setUp()` (无返回类型) | `setUp(): void` |
| `setUpBeforeClass()` (无返回类型) | `setUpBeforeClass(): void` |
| `tearDown()` (无返回类型) | `tearDown(): void` |

`phpunit.xml` 配置格式也需要更新：

```xml
<!-- Before (PHPUnit 5.7) -->
<phpunit bootstrap="tests/bootstrap.php">
    <filter>
        <whitelist>
            <directory suffix=".php">src</directory>
        </whitelist>
    </filter>
</phpunit>

<!-- After (PHPUnit 13) -->
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/13.0/phpunit.xsd"
         bootstrap="tests/bootstrap.php">
    <source>
        <include>
            <directory suffix=".php">src</directory>
        </include>
    </source>
</phpunit>
```

---

## 升级步骤

1. **更新 `composer.json`**：按「依赖变更清单」更新所有依赖版本
2. **执行 `composer update`**：解析并安装新版本依赖
3. **适配 PHP 8.5 语法**：添加 `declare(strict_types=1)`、类型声明等（按需）
4. **替换 SilexKernel 引用**：将所有 `SilexKernel` 类型提示和 import 改为 `MicroKernel`
5. **调整 `services.yml`**：为通过 `getService()` 获取的服务添加 `public: true`
6. **适配 AbstractDaemonSentinelCommand 移除**：如有自定义子类，改为继承 `DaemonSentinelCommand`
7. **升级测试套件**：按 PHPUnit 13 API 变更清单适配测试代码和 `phpunit.xml`
8. **清除旧缓存**：
   ```bash
   ./bin/<project>.php slimapp:cache:clear
   ```
9. **验证 public 服务**：
   ```bash
   ./bin/<project>.php slimapp:services:validate
   ```
10. **运行业务测试套件**：确认无回归
