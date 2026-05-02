# CLI Commands

## 内置命令

### `slimapp:project:init`

交互式初始化项目目录结构。

- 类: `Oasis\SlimApp\BuiltInCommands\InitializeProjectCommand`
- 选项: `--project-root, -p` — 项目根目录（默认 cwd）
- 行为:
  1. 检查项目根目录是否包含 `composer.json`、`composer.lock`、`vendor/`
  2. 交互式询问: vendor/project 名称、命名空间、源码目录、ORM/ODM 支持、日志/数据/缓存/模板目录、phpunit 支持
  3. 生成文件: App 类、Configuration 类、bootstrap.php、front.php、console 入口、routes.yml、services.yml、tpl.config.yml、DemoController 等
  4. 更新 composer.json 的 autoload 配置

### `slimapp:cache:clear`

清除框架缓存。

- 类: `Oasis\SlimApp\BuiltInCommands\ClearCacheCommand`
- 清除范围: 配置缓存目录 + HTTP Kernel 缓存目录

### `slimapp:services:validate`

验证所有 public 服务。

- 类: `Oasis\SlimApp\BuiltInCommands\ValidateServicesCommand`
- 行为: 遍历容器中所有 public service ID，逐个实例化，报告配置错误

## Command 基类体系

```
Symfony\Component\Console\Command\Command
  └── AbstractAlertableCommand          # --alert 选项
        ├── AbstractParallelCommand     # --parallel + pcntl_fork
        └── DaemonSentinelCommand       # 哨兵命令（读取 YAML 配置，fork 子进程调度）
```

### AbstractAlertableCommand

- 添加 `--alert` 选项
- 当命令执行抛出异常且 `--alert` 启用时，通过 `mtrace()` 发送 alert 级别日志
- Exit codes: `EXIT_CODE_OK` (0), `EXIT_CODE_RESTART` (0xe1), `EXIT_CODE_COMMON_ERROR` (0xff)

### AbstractParallelCommand

- 继承 AbstractAlertableCommand
- 添加 `--parallel` 选项（默认 1）和 `--no-overflow-confirm` 选项
- parallel > 10 时需用户确认（除非 `--no-overflow-confirm`）
- parallel = 1 时直接调用 `doExecute()`
- parallel > 1 时通过 `pcntl_fork()` 创建子进程
- 子进程退出码为 `EXIT_CODE_RESTART` 时自动重启
- 使用方需实现 `abstract doExecute(InputInterface, OutputInterface)`

### DaemonSentinelCommand

- 直接继承 `AbstractAlertableCommand`
- 接受一个 YAML 配置文件作为参数
- 按配置 fork 多个子进程，每个子进程运行一个 Console Command
- 支持调度策略: interval、frequency、frequency_fixed、once、parallel、alert
