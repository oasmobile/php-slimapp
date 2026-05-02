# Project: oasis/slimapp

## 概述

SlimApp 是一个 PHP 全栈微框架，支持 Web（HTTP Kernel）和 CLI（Console）两种运行模式。基于 Symfony 组件构建，提供依赖注入容器、YAML 配置、日志、Daemon Sentinel 等能力。

## 技术栈

- **语言**: PHP >= 7.0
- **包管理**: Composer
- **核心依赖**:
  - `symfony/dependency-injection` ^4.0（服务容器）
  - `symfony/config` ^4.0（配置定义与解析）
  - `symfony/console` ^4.0（CLI 框架）
  - `symfony/finder` ^4.0
  - `symfony/filesystem` ^4.0
  - `oasis/logging` ^1.2.0（日志，基于 Monolog）
  - `oasis/utils` ^1.6
  - `oasis/http` ^2.0（HTTP Kernel，基于 Silex）
- **开发依赖**:
  - `phpunit/phpunit` ^5.7
  - `doctrine/orm` ^2.5
  - `oasis/aws-wrappers` ^2.2.1
  - `oasis/dynamodb-odm` ^1.0
  - `oasis/doctrine-addon` ^2.0.2

## 命名空间

```
Oasis\SlimApp\  →  src/
```

## 构建 / 测试命令

```bash
# 安装依赖
composer install

# 运行测试（项目根目录下）
./vendor/bin/phpunit

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
├── AbstractAlertableCommand.php   # 支持 --alert 选项的 Command 基类
├── AbstractParallelCommand.php    # 支持 pcntl_fork 并行执行的 Command 基类
├── BuiltInCommands/          # 内置命令
│   ├── ClearCacheCommand.php          # slimapp:cache:clear
│   ├── InitializeProjectCommand.php   # slimapp:project:init
│   └── ValidateServicesCommand.php    # slimapp:services:validate
├── SentinelCommand/          # Daemon Sentinel 子系统
│   ├── AbstractDaemonSentinelCommand.php  # (deprecated) 抽象哨兵命令
│   ├── DaemonSentinelCommand.php          # 哨兵命令（推荐使用）
│   ├── CommandConfiguration.php           # 哨兵 YAML 配置定义
│   └── CommandRunner.php                  # 子进程 fork/管理/调度
└── tests/                    # 框架自身的测试辅助类
ut/                           # 集成测试 / 手动测试配置
```
