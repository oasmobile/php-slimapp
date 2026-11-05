---
title: "数据访问和测试迁移"
doc_type: user-guide
evidence:
  - path: "composer.json"
  - path: "src/SlimApp.php"
  - path: "phpunit.xml"
---

# 数据访问和测试迁移

本页迁移旧数据类型常量和 PHPUnit API；整体升级步骤见[迁移指南](migration-v2-to-v3.md)。
SlimApp 配置访问方法的类型参数使用 DataType 枚举；这不改变配置缓存的文件格式。

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
