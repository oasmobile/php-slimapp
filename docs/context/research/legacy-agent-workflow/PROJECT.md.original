# Project: oasis/slimapp

## 概述

SlimApp 是一个 PHP 全栈微框架，支持 Web（HTTP Kernel）和 CLI（Console）两种运行模式。基于 Symfony 组件构建，提供依赖注入容器、YAML 配置、日志、Daemon Sentinel 等能力。

## 技术栈

- **语言**: PHP >= 8.5
- **包管理**: Composer
- **核心依赖**:
  - `symfony/dependency-injection` ^8.0（服务容器）
  - `symfony/config` ^8.0（配置定义与解析）
  - `symfony/console` ^8.0（CLI 框架）
  - `symfony/finder` ^8.0
  - `symfony/filesystem` ^8.0
  - `oasis/logging` ^3.0（日志，基于 Monolog）
  - `oasis/utils` ^3.0
  - `oasis/http` ^3.0（HTTP Kernel，MicroKernel）
- **开发依赖**:
  - `phpunit/phpunit` ^13
  - `phpstan/phpstan` ^2.1（静态分析，level 8）
  - `doctrine/orm` ^3.6
  - `oasis/aws-wrappers` ^3.0
  - `oasis/dynamodb-odm` ^2.0
  - `oasis/doctrine-addon` ^3.1
  - `giorgiosironi/eris` ^1.1（Property-Based Testing）

## 命名空间

```
Oasis\SlimApp\  →  src/
```

## 构建 / 测试命令

```bash
# 安装依赖
composer install

# 运行单元测试
./vendor/bin/phpunit --testsuite ut

# 运行 Property-Based Testing
./vendor/bin/phpunit --testsuite pbt

# 运行全量测试（ut + pbt）
./vendor/bin/phpunit

# 运行静态分析
./vendor/bin/phpstan analyse

# 运行 CLI 入口（开发用）
php test.php <command>
```

## 运行入口

| 入口 | 路径 | 说明 |
|------|------|------|
| CLI（开发） | `test.php` | 使用 `ut/` 下的测试配置启动 Console |
| CLI（bin） | `bin/slimapp` | 作为 Composer bin 分发的 CLI 入口 |
| HTTP | 由使用方项目提供 `web/front.php` | 通过 `$app->getHttpKernel()->run()` 启动 |

## 版本号位置

- `composer.json` → `version` 字段（当前未显式声明，由 Packagist / tag 管理）
- `services.yml` → `app.cli.version`（使用方项目自行定义）

## 敏感文件

- `ut/credentials.yml` — 测试用凭据（已被 services.yml import）
- `config/` 目录下的配置文件可能包含数据库密码等

## 目录结构概览

```
src/                          # 框架源码（Oasis\SlimApp 命名空间）
├── SlimApp.php               # 核心类，单例，初始化容器/配置/日志
├── ConsoleApplication.php    # CLI Application，扩展 Symfony Console
├── SlimAppCompilerPass.php   # DI 编译器 Pass（默认命名空间解析、app 服务注册）
├── ConfigParser.php          # 配置解析工具（parse/flatten/retrieve）
├── NamespaceResolver.php     # 命名空间解析工具（短类名 → FQCN）
├── AbstractAlertableCommand.php   # 支持 --alert 选项的 Command 基类
├── AbstractParallelCommand.php    # 支持 pcntl_fork 并行执行的 Command 基类
├── BuiltInCommands/          # 内置命令
│   ├── ClearCacheCommand.php          # slimapp:cache:clear
│   ├── InitializeProjectCommand.php   # slimapp:project:init
│   └── ValidateServicesCommand.php    # slimapp:services:validate
├── SentinelCommand/          # Daemon Sentinel 子系统
│   ├── DaemonSentinelCommand.php          # 哨兵命令（直接继承 AbstractAlertableCommand）
│   ├── CommandConfiguration.php           # 哨兵 YAML 配置定义
│   └── CommandRunner.php                  # 子进程 fork/管理/调度
└── tests/                    # 框架自身的测试辅助类
tests/                        # 测试目录
├── ut/                       # 单元测试
├── pbt/                      # Property-Based Testing（Eris）
├── integration/              # 集成测试
└── scripts/                  # 覆盖率合并等脚本
ut/                           # 集成测试 / 手动测试配置
```
