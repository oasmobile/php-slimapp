# Migration Guide: slimapp 2.x → 3.0

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
6. 适配 Doctrine ORM 3.x（如启用 ORM）（→ [Doctrine ORM 3.x](#doctrine-orm-3x)）
7. 适配 Sentinel 基类移除（如有子类）（→ [AbstractDaemonSentinelCommand 移除](#abstractdaemonsentinelcommand-移除)）
8. 给 `sentinel.yml` 中的 `%param%` 值加双引号（→ [sentinel.yml 引号](#sentinelyml-引号)）
9. 适配 PHPUnit 13（→ [PHPUnit 5.7 → 13](#phpunit-57--13)）
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

MicroKernel 提供与 SilexKernel 等价的公共 API，无需修改调用代码：

| 方法 | 说明 |
|------|------|
| `addControllerInjectedArg(object $arg): void` | 注入控制器参数 |
| `addExtraParameters(array $params): void` | 注入额外参数 |
| `run(?Request $request = null): void` | 启动 HTTP 处理 |
| `getCacheDirectories(): array` | 返回缓存目录列表 |

此外，`oasis/http` v3.4+ 已恢复以下 Silex 时代的便捷方法，下游无需为这些调用做额外迁移：

| 方法 | 恢复版本 | 说明 |
|------|----------|------|
| `render($view, $params, $response)` | v3.4 | 渲染 Twig 模板返回 Response |
| `renderView($view, $params)` | v3.4 | 渲染 Twig 模板返回字符串 |
| `path($route, $params)` | v3.4 | 生成相对 URL |
| `url($route, $params)` | v3.4 | 生成绝对 URL |
| `before($callback, $priority, $masterRequestOnly)` | v3.5 | 注册 before 过滤器 |
| `after($callback, $priority, $masterRequestOnly)` | v3.5 | 注册 after 过滤器 |
| `error($callback, $priority)` | v3.5 | 注册 error handler |
| `view($callback)` | v3.6 | 注册 view handler |
| `abort($statusCode, $message, $headers)` | v3.6 | 抛出 HttpException |
| `redirect($url, $status)` | v3.6 | 创建重定向响应 |
| `json($data, $status, $headers)` | v3.6 | 创建 JSON 响应 |
| `stream($callback, $status, $headers)` | v3.6 | 创建流式响应 |
| `sendFile($file, $status, $headers, $contentDisposition)` | v3.6 | 创建文件下载响应 |

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

Symfony 8.0 YAML 解析器对 `%` 保留字符更严格。含 `%` 或 `$` 的值必须用双引号包裹：

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

### Doctrine ORM 3.x

> **快速判断**：项目中是否有 `config/cli-config.php`、`src/Database/` 目录、或 `composer.json` 中依赖了 `doctrine/orm`？如果都没有，跳过本节。

#### Annotation → Attribute

ORM 3.x 移除了 Annotation 元数据驱动。Entity 映射必须使用 PHP 8 Attribute。

```php
// Before — Database 类中
use Doctrine\ORM\Tools\Setup;

$config = Setup::createAnnotationMetadataConfiguration(
    [PROJECT_DIR . "/src/Entities"],
    $isDevMode,
    $proxyDir,
    $cache,
    false
);

// After
use Doctrine\ORM\ORMSetup;

$config = ORMSetup::createAttributeMetadataConfiguration(
    [PROJECT_DIR . "/src/Entities"],
    $isDevMode,
    $proxyDir
);
```

Entity 类中的注解也需改为 Attribute：

```php
// Before
/** @ORM\Entity @ORM\Table(name="users") */
class User { /** @ORM\Column(type="string") */ public $name; }

// After
#[ORM\Entity]
#[ORM\Table(name: "users")]
class User { #[ORM\Column(type: "string")] public string $name; }
```

#### `Doctrine\Common\Cache` 移除

ORM 3.x 不再依赖 `doctrine/cache`。`Doctrine\Common\Cache\MemcachedCache` 不可用。

**最简路径**（大多数项目不用二级缓存）：

1. 删除 `services.yml` 中的 `memcached_cache` 服务定义
2. 从 `Database` 类的 `getEntityManager()` 中移除 `DefaultCacheFactory` / `RegionsConfiguration` / `setSecondLevelCacheEnabled()` 相关代码

**如果确实需要二级缓存**，改用 PSR-6 适配器（需 `composer require symfony/cache`）：

```php
use Psr\Cache\CacheItemPoolInterface;
use Doctrine\ORM\Cache\DefaultCacheFactory;
use Doctrine\ORM\Cache\RegionsConfiguration;

/** @var CacheItemPoolInterface $cachePool */
$cachePool = $app->getService('cache.pool');
$factory = new DefaultCacheFactory(new RegionsConfiguration(), $cachePool);
$config->setSecondLevelCacheEnabled();
$config->getSecondLevelCacheConfiguration()->setCacheFactory($factory);
```

#### ORM 命令集注册

`ConsoleRunner::addCommands()` 签名变更，必须传入 `EntityManagerProvider`；`ConsoleRunner::createHelperSet()` 已移除。

**`config/cli-config.php`**：

```php
// Before
use Doctrine\ORM\Tools\Console\ConsoleRunner;
return ConsoleRunner::createHelperSet(AppDatabase::getEntityManager());

// After
use Doctrine\ORM\Tools\Console\EntityManagerProvider\SingleManagerProvider;
return new SingleManagerProvider(AppDatabase::getEntityManager());
```

**`bin/<project>.php`**（console 入口）：

```php
// Before
$helperSet = require_once __DIR__ . "/../config/cli-config.php";
$console->setHelperSet($helperSet);
\Doctrine\ORM\Tools\Console\ConsoleRunner::addCommands($console);

// After
$provider = require_once __DIR__ . "/../config/cli-config.php";
\Doctrine\ORM\Tools\Console\ConsoleRunner::addCommands($console, $provider);
```

> 如果 console 入口从未注册过 ORM 命令（没有上述代码），则 `orm:*` 命令本来就不可用，无需改动。

#### 自查 Checklist

```bash
grep -rn 'ConsoleRunner' src/ bin/ config/ ut/
grep -rn 'createAnnotationMetadataConfiguration' src/
grep -rn 'Doctrine\\Common\\Cache' src/ config/
```

---

### `oasis/utils` DataType 枚举

`oasis/utils` 3.0 将 `DataProviderInterface::STRING_TYPE` 等常量替换为 `DataType` 枚举。

```php
// Before
use Oasis\Mlib\Utils\DataProviderInterface;
$val = $app->getMandatoryConfig('key', DataProviderInterface::STRING_TYPE);

// After
use Oasis\Mlib\Utils\DataType;
$val = $app->getMandatoryConfig('key', DataType::String);
```

| 旧常量 | 新枚举 |
|--------|--------|
| `DataProviderInterface::STRING_TYPE` | `DataType::String` |
| `DataProviderInterface::INT_TYPE` | `DataType::Int` |
| `DataProviderInterface::BOOL_TYPE` | `DataType::Bool` |
| `DataProviderInterface::ARRAY_TYPE` | `DataType::Array` |

**自查**：`grep -rn 'DataProviderInterface::' src/`

---

### PHPUnit 5.7 → 13

| 旧 API | 新 API |
|--------|--------|
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
| `tearDown()` (无返回类型) | `tearDown(): void` |

`phpunit.xml` 格式变更：

```xml
<!-- Before -->
<phpunit bootstrap="tests/bootstrap.php">
    <filter>
        <whitelist>
            <directory suffix=".php">src</directory>
        </whitelist>
    </filter>
</phpunit>

<!-- After -->
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

## 常见报错速查

| 报错信息 | 原因 | 解决 |
|----------|------|------|
| `Class "Oasis\Mlib\Http\SilexKernel" not found` | oasis/http 3.0 移除了 SilexKernel | → [SilexKernel → MicroKernel](#silexkernel--microkernel) |
| `ServiceNotFoundException: ... has been removed from the container` | 服务未声明 public | → [DI 容器 private-by-default](#di-容器-private-by-default) |
| `The reserved indicator "%" cannot start a plain scalar` | sentinel.yml 中 `%param%` 未加引号 | → [sentinel.yml 引号](#sentinelyml-引号) |
| `Class "Doctrine\ORM\Tools\Setup" not found` | ORM 3.x 移除了 Setup 类 | → [Annotation → Attribute](#annotation--attribute) |
| `Class "Doctrine\Common\Cache\MemcachedCache" not found` | doctrine/cache 已移除 | → [Doctrine\Common\Cache 移除](#doctrinecommoncache-移除) |
| `ConsoleRunner::createHelperSet() not found` | ORM 3.x 移除了该方法 | → [ORM 命令集注册](#orm-命令集注册) |
| `DataProviderInterface::STRING_TYPE not found` | oasis/utils 3.0 改为枚举 | → [oasis/utils DataType 枚举](#oasisutils-datatype-枚举) |
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
| `routes.yml` | ✅ 无缝兼容 | MicroKernel 保持与 SilexKernel 等价的路由解析接口 |
| `sentinel.yml` | ⚠️ 需加引号 | 详见 [sentinel.yml 引号](#sentinelyml-引号) |
| `services.yml` | ⚠️ 需加 public | 详见 [DI 容器 private-by-default](#di-容器-private-by-default) |

> 缓存文件（`container.php`、`config.cache`）因 Symfony 8.0 序列化格式变化不兼容旧缓存，升级后首次运行会自动重建，或手动执行 `slimapp:cache:clear`。
