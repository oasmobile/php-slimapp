# Daemon Sentinel

Daemon Sentinel 用于管理多个需要按计划执行的后台命令。它本身也是一个 Console Command，通过 `pcntl_fork` 创建子进程来运行配置中的命令。

## 创建 Sentinel 命令

```php
<?php
namespace Minhao\TestProject\Console\Commands;

use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class MySentinelCommand extends DaemonSentinelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('my:daemon');
    }
}
```

> 注意: 使用 `DaemonSentinelCommand`，不要使用已废弃的 `AbstractDaemonSentinelCommand`。

## 配置文件

Sentinel 命令接受一个 YAML 配置文件作为参数:

```bash
./bin/project.php my:daemon /path/to/sentinel.yml
```

配置文件格式:

```yaml
commands:
    worker:
        name: queue:process        # 要执行的命令名
        args:                      # 命令参数
            queue-name: emails
            --timeout: 30
            -vvv:
        parallel: 3                # 并行实例数（默认 1）
        once: false                # 是否只执行一次（默认 false）
        alert: true                # 异常退出时发送 alert（默认 true）
        interval: 2                # 上次结束到下次开始的最小间隔秒数（默认 0）
        frequency: 5               # 两次开始之间的最小间隔秒数（默认 0）
        frequency_fixed: false     # 上次未结束时是否仍按频率启动新实例（默认 false）
```

## 调度策略

### interval vs frequency

- `interval`: 保证上一次执行**结束**后至少等待 N 秒才开始下一次
- `frequency`: 保证两次执行**开始**之间至少间隔 N 秒
- 两者可同时使用，取较大的等待时间

### frequency_fixed

- `false`（默认）: 上一次执行未结束时，等待其结束后再按 interval/frequency 调度
- `true`: 即使上一次未结束，也在达到 frequency 时启动新实例（适用于允许重叠执行的场景）

### parallel

- 指定同时运行的实例数
- 每个实例通过 `$PARALLEL_INDEX`（从 0 开始）区分

## 特殊变量

| 变量 | 说明 |
|------|------|
| `$PARALLEL_INDEX` | 在 `args` 中使用，表示当前并行实例的索引（0-based） |
| `%param.key%` | 在 `args` 中使用，引用 DI 容器参数值 |

## 示例

```yaml
commands:
    email-sender:
        name: email:send
        args:
            --batch-size: 100
            --idx: $PARALLEL_INDEX
        parallel: 2
        interval: 5
        frequency: 10
        alert: true

    report-generator:
        name: report:generate
        once: true
        alert: true
```
