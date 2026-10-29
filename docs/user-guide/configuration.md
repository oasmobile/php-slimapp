---
title: "配置访问"
doc_type: user-guide
evidence:
  - path: "src/SlimApp.php"
  - path: "src/ConfigParser.php"
---

# 配置访问

本页说明应用代码如何取得配置和容器参数。

## 读取应用配置

配置由使用方的 ConfigurationInterface 定义。
框架从 `init()` 指定的配置目录读取 `config.yml`；生成工程通常使用 `config/config.yml`。

```php
use Oasis\Mlib\Utils\DataType;

$debug = $app->getMandatoryConfig('is_debug', DataType::Bool);
$port = $app->getOptionalConfig('db.port', DataType::Int, 3306);
```

- 配置 key 使用点号访问层级，例如 `dir.log`。
- 必填值和类型由数据提供器及使用方配置定义检查。
- 可选值缺失时返回传入的默认值；默认参数类型为 `DataType::String`。

## 读取容器参数

应用配置会被映射为带 `app.` 前缀的容器参数。

```php
$logDir = $app->getParameter('app.dir.log');
```

在服务定义中将参数表达式写成带引号的 YAML 标量。

```yaml
services:
    worker:
        class: App\Worker
        arguments: ["%app.dir.log%"]
```

配置解析、文件和缓存规则见[运行时配置](../system/operations/configuration.md)。
