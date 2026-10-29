---
title: "Doctrine ORM 迁移"
doc_type: user-guide
evidence:
  - path: "composer.json"
  - path: "src/BuiltInCommands/InitializeProjectCommand.php"
---

# Doctrine ORM 迁移

本页说明使用方从旧 ORM API 迁移的注意事项；整体步骤见[迁移指南](migration-v2-to-v3.md)。

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
