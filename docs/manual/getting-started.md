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

---

## 测试 init 命令

仓库内置了 `init-ut/` 目录作为 `slimapp:project:init` 的隔离测试环境。

### 环境说明

`init-ut/` 是一个独立的 Composer 项目，通过 `path` 仓库 symlink 引用本地的 `oasis/slimapp`，因此本地未提交的代码改动也能直接测试。

`.gitignore` 已排除所有 init 命令生成的文件（`src/`、`config/`、`web/`、`bin/`、`bootstrap.php` 等），可以放心运行。

### 测试步骤

```bash
cd init-ut/

# 1. 安装依赖（首次或 composer.json 变更后）
composer install

# 2. 运行 init 命令
php vendor/bin/slimapp slimapp:project:init --project-root=.

# 3. 按提示输入项目信息，检查生成的文件

# 4. 清理生成的文件
rm -rf src/ config/ web/ bin/ bootstrap.php templates/ assets/ cache/
```

### 验证要点

- 生成的 `*Configuration.php` 应使用 `new TreeBuilder('app')` + `getRootNode()`（非 deprecated API）
- 生成的 `phpunit.xml` 应使用 PHPUnit 13 schema
- 启用 phpunit 时，`composer require --dev phpunit/phpunit:^13` 应正确执行
- 所有生成的文件应能通过 `php -l` 语法检查

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
