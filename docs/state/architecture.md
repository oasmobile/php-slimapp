# Architecture

## 分层结构

SlimApp 采用单体框架设计，核心类 `SlimApp` 作为单例入口，统一管理配置、容器、日志、HTTP Kernel 和 CLI Application。

```
┌─────────────────────────────────────────────┐
│                 使用方项目                     │
│  (bootstrap.php / front.php / bin/xxx.php)  │
├─────────────────────────────────────────────┤
│              SlimApp (单例)                   │
│  ┌──────────┬──────────┬──────────────────┐ │
│  │  Config  │   DI     │    Logging       │ │
│  │  (YAML)  │Container │  (Monolog)       │ │
│  └──────────┴──────────┴──────────────────┘ │
│  ┌──────────────────┬─────────────────────┐ │
│  │  HTTP Kernel      │  Console App       │ │
│  │  (oasis/http)     │  (symfony/console) │ │
│  └──────────────────┴─────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │         Daemon Sentinel                │ │
│  │  (pcntl_fork 多进程调度)                │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## 核心组件

### SlimApp（单例）

- 命名空间: `Oasis\SlimApp\SlimApp`
- 通过 `SlimApp::app()` 获取单例
- 属性注入机制: `__set()` 魔术方法将属性名转换为 `set<Name>Property()` 方法调用（如 `logging` → `setLoggingProperty()`），这是 DI 容器 `properties` 配置生效的底层机制
- `init($configPath, ConfigurationInterface, $cachePath)` 完成初始化：
  1. 解析 `config.yml`（使用 symfony/config 的 ConfigurationInterface 做 schema 校验）
  2. 将配置扁平化为 `app.*` 参数
  3. 构建 DI 容器（解析 `services.yml`，应用 `SlimAppCompilerPass`）
  4. 安装默认日志 handler（LocalFileHandler + LocalErrorHandler）

### DI 容器

- 基于 `symfony/dependency-injection`
- 通过 `services.yml`（YAML 格式）定义服务
- `SlimAppCompilerPass` 提供：
  - `default.namespace` 参数支持：类名不含完整命名空间时自动补全
  - `app` 服务自动注册为当前 SlimApp 子类的单例
  - 所有服务设为 public

### 配置系统

- 配置文件: `config.yml`（YAML）
- 配置定义: 使用方实现 `ConfigurationInterface`
- 配置缓存: 序列化到 `$cachePath/config.cache`，始终检测文件变更
- 容器缓存: 编译为 PHP 类到 `$cachePath/container.php`，仅 debug 模式下检测文件变更
- 参数化: 配置值以 `app.` 前缀扁平化为容器参数（如 `app.dir.log`）
- 访问方式:
  - `$app->getMandatoryConfig('dir.log')` — 按配置 key
  - `$app->getParameter('app.dir.log')` — 按参数 key

### 日志

- 基于 `oasis/logging`（Monolog 封装）
- 默认安装两个 handler:
  - `LocalFileHandler` — 按日期分目录的文件日志
  - `LocalErrorHandler` — 仅记录 error 及以上级别
- CLI 模式额外安装 `ConsoleHandler`（输出到 STDERR，带 ANSI 颜色）
- 日志路径模式: `%date%/%script%.%type%`（CLI 模式为 `%date%/%script%.%command%.%type%`）

### HTTP Kernel

- 基于 `oasis/http`（Silex 扩展）
- 通过 `app` 服务的 `http` 属性配置
- 支持: routing、twig 模板、CORS、error handler、view handler
- 入口: `$app->getHttpKernel()->run()`

### Console Application

- 基于 `symfony/console`
- 通过 `app` 服务的 `cli` 属性配置（name、version、commands）
- 内置命令:
  - `slimapp:cache:clear` — 清除配置和 HTTP 缓存
  - `slimapp:project:init` — 交互式初始化项目目录结构
  - `slimapp:services:validate` — 逐个实例化服务以验证配置
- 入口: `$app->getConsoleApplication()->run()`

### Command 基类

| 类 | 说明 |
|----|------|
| `AbstractAlertableCommand` | 添加 `--alert` 选项，异常时触发 alert 日志 |
| `AbstractParallelCommand` | 继承 AlertableCommand，支持 `--parallel` 选项，通过 `pcntl_fork` 并行执行 `doExecute()` |

### Daemon Sentinel

- 类: `DaemonSentinelCommand`（推荐）/ `AbstractDaemonSentinelCommand`（deprecated）
- 功能: 读取 YAML 配置文件，按配置 fork 子进程执行多个命令
- 调度参数:
  - `parallel` — 并行实例数
  - `once` — 是否只执行一次
  - `interval` — 上次结束到下次开始的最小间隔（秒）
  - `frequency` — 两次开始之间的最小间隔（秒）
  - `frequency_fixed` — 是否在上次未结束时也按频率启动新实例
  - `alert` — 异常退出时是否发送 alert
- 特殊变量: `$PARALLEL_INDEX`（args 中使用，表示并行实例索引，从 0 开始）
- 配置值支持 `%param%` 引用容器参数

## 初始化流程

使用方项目的典型初始化流程:

```
composer require oasis/slimapp
  ↓
./vendor/bin/slimapp slimapp:project:init
  ↓
生成: bootstrap.php, config/, src/, bin/, web/ 等
  ↓
编辑 config.yml + services.yml
  ↓
通过 bootstrap.php 启动应用
```
