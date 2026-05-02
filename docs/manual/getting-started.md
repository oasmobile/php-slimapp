# Getting Started

## 安装

```bash
composer require oasis/slimapp
```

## 初始化项目

在项目根目录（已有 `composer.json` 和 `vendor/`）下运行:

```bash
./vendor/bin/slimapp slimapp:project:init
```

按提示输入:

| 提示项 | 说明 | 示例 |
|--------|------|------|
| vendor/project | Composer 包名 | `minhao/test-project` |
| root namespace | PSR-4 根命名空间 | `Minhao\TestProject\` |
| source directory | 源码目录 | `src/` |
| ORM support | 是否启用 Doctrine ORM | yes/no |
| ODM support | 是否启用 DynamoDB ODM | yes/no |
| logging directory | 日志目录 | `/data/logs/test-project` |
| data directory | 数据目录 | `/data/test-project` |
| cache directory | 缓存目录 | `./cache` |
| template directory | Twig 模板目录 | `./templates` |
| phpunit | 是否启用 phpunit | yes/no |

初始化后的目录结构:

```
PROJECT_DIR/
├── assets/
├── bin/<project>.php          # CLI 入口
├── cache/
├── config/
│   ├── tpl.config.yml         # 应用配置模板（由 init 生成，需重命名为 config.yml）
│   ├── services.yml           # DI 容器定义
│   └── routes.yml             # HTTP 路由
├── src/
│   ├── <Project>.php          # 继承 SlimApp 的主类
│   ├── <Project>Configuration.php  # 配置 schema 定义
│   ├── Controllers/
│   │   └── DemoController.php
│   └── Database/              # (如启用 ORM/ODM)
├── templates/
├── web/
│   └── front.php              # HTTP 入口
├── bootstrap.php              # 引导文件
└── composer.json
```

## 启动应用

### CLI 模式

```bash
./bin/<project>.php <command>
```

### HTTP 模式

将 Web Server 的 document root 指向 `web/` 目录，入口文件为 `front.php`。

## bootstrap.php 说明

```php
<?php
use Minhao\TestProject\TestProject;
use Minhao\TestProject\TestProjectConfiguration;

require_once __DIR__ . "/vendor/autoload.php";

define('PROJECT_DIR', __DIR__);

$app = TestProject::app();
$app->init(
    __DIR__ . "/config",
    new TestProjectConfiguration(),
    __DIR__ . "/cache/config"
);

return $app;
```

关键点:
- `PROJECT_DIR` 常量在配置定义中用于将相对路径转为绝对路径
- `init()` 的三个参数: 配置目录、配置 schema 实例、缓存目录
- 返回的 `$app` 对象是 `SlimApp` 子类的单例
