---
title: "自定义命令"
doc_type: user-guide
evidence:
  - path: "src/ConsoleApplication.php"
  - path: "src/AbstractAlertableCommand.php"
  - path: "src/AbstractParallelCommand.php"
  - path: "tests/ut/AbstractParallelCommandPcntlTest.php"
---

# 自定义命令

使用 Symfony Console 编写命令，并将实例注册到应用 Console。

## 编写并注册命令

命令通过参数和选项接收输入，通过 OutputInterface 输出，并返回整数退出码。

```php
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

class GreetingCommand extends Command
{
    protected function configure(): void
    {
        $this->setName('greet')
            ->addArgument('name', InputArgument::REQUIRED, '称呼')
            ->addOption('mood', 'm', InputOption::VALUE_REQUIRED, '语气', 'happy');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $sign = $input->getOption('mood') === 'happy' ? '!' : '.';
        $output->writeln('Hello, ' . $input->getArgument('name') . $sign);
        return 0;
    }
}

$console = $app->getConsoleApplication();
$console->addCommand(new GreetingCommand());
$console->run();
```

也可通过 `app.cli.commands` 注入命令服务；配置方式见[服务容器](service-container.md)。

```bash
./bin/project.php greet Alice --mood=happy
```

必填参数应放在可选参数之前；选项可写为 `--mood happy` 或 `--mood=happy`。

## 异常告警命令

继承 AbstractAlertableCommand 可获得 `--alert` 选项。

- 命令抛出 Exception 且启用 `--alert` 时记录 alert trace。
- Exception 随后重新抛出，由 Console 处理。
- 退出常量为成功 0、重启 225、普通错误 255。

## 并行命令

继承 AbstractParallelCommand，并实现 `doExecute(InputInterface, OutputInterface): int`。

| 条件 | 行为 |
| --- | --- |
| `--parallel=1` | 在当前进程直接执行 |
| `--parallel>1` | 用 pcntl 创建并等待子进程 |
| `--parallel<1` | 抛出 InvalidArgumentException |
| `--parallel>10` | 默认询问；`--no-overflow-confirm` 跳过询问 |
| 拒绝超额并行 | 返回 -1 |
| 子进程返回 225 | 重启该实例 |
| 其他非零子进程退出 | 父命令返回 255 |

多进程命令需要 pcntl；长期调度任务使用 [Daemon Sentinel](daemon-sentinel.md)。
