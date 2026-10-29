---
title: "服务容器"
doc_type: user-guide
evidence:
  - path: "src/SlimApp.php"
  - path: "src/SlimAppCompilerPass.php"
  - path: "src/NamespaceResolver.php"
  - path: "tests/ut/SlimAppCompilerPassTest.php"
---

# 服务容器

SlimApp 使用 symfony/dependency-injection 实现服务容器。所有服务在 `services.yml` 中以 YAML 格式定义。

## 基本结构

应用以 YAML 定义导入、参数和服务。

```yaml
imports:
    - { resource: "other-services.yml" }

parameters:
    default.namespace:
        - Minhao\TestProject\

services:
    my.service:
        class: MyService
        public: true
        arguments:
            - "arg1"
            - "@another.service"
```

## 服务定义三阶段

服务定义可以配置创建、设置和装饰行为。

### 1. 构造阶段

通过构造函数或工厂方法创建对象:

```yaml
# 构造函数
services:
    user:
        class: Minhao\TestProject\User
        arguments:
            - "John"
            - 25

# 工厂方法
services:
    user:
        class: Minhao\TestProject\User
        factory: [UserProvider, getUser]
        arguments:
            - 250008
```

### 2. 设置阶段

通过属性赋值或方法调用修改对象:

```yaml
services:
    user:
        class: Minhao\TestProject\User
        arguments: ["John", 25]
        properties:
            tel: "1234567890"
        calls:
            - [setSupervisor, ["@another.user"]]
```

### 3. 装饰阶段

高级用法，参考 [Symfony 官方文档](http://symfony.com/doc/current/components/dependency_injection/advanced.html)。

## 默认命名空间

在 `parameters` 中定义 `default.namespace` 后，服务的 `class` 和 `factory` 中的类名如果不是完整命名空间，框架会自动尝试补全:

```yaml
parameters:
    default.namespace:
        - Minhao\TestProject\
        - Oasis\Mlib\

services:
    # 会自动解析为 Minhao\TestProject\User（如果该类存在）
    user:
        class: User
```

## 引用语法

服务与参数使用不同的引用语法。

| 语法 | 含义 | 示例 |
|------|------|------|
| `@service_id` | 引用另一个服务 | `@entity_manager` |
| `%param.key%` | 引用参数值 | `%app.dir.log%` |

## 访问服务

供 `getService()` 获取的服务须在 YAML 中显式配置 `public: true`。

```php
// 获取服务
$service = $app->getService('my.service');

// 获取服务（带类型检查）
$service = $app->getService('my.service', MyService::class);

// 获取所有服务 ID
$ids = $app->getServiceIds();

// 替换服务
$app->setService('my.service', $newInstance);

// 重置服务（设为 null）
$app->resetService('my.service');
```

## 应用服务

使用框架自动配置 `app` 服务时，须声明合法的 `default.namespace` 参数。

```yaml
parameters:
    default.namespace: ["App\\"]
services:
    app:
        properties:
            cli:
                name: "应用命令行"
                version: "1.0"
                commands: ["@worker"]
```

HTTP 与日志属性分别见 [HTTP](http.md) 和[日志](logging.md)。
