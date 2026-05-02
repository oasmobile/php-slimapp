<?php
/**
 * 独立进程测试脚本：DaemonSentinelCommand（含 CommandRunner.run）
 *
 * 测试 sentinel 读取配置 → fork 子进程 → 等待子进程退出 的完整流程。
 */

require_once __DIR__ . '/../../vendor/autoload.php';

use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Serialization\Serializer;

// ── 覆盖率收集 ──
$covFile = getenv('COVERAGE_FILE');
$coverage = null;
if ($covFile) {
    $filter = new Filter();
    $srcDir = __DIR__ . '/../../src';
    $excludes = [
        realpath($srcDir . '/BuiltInCommands/InitializeProjectCommand.php'),
    ];
    $excludeDirs = [
        realpath($srcDir . '/tests') ?: $srcDir . '/tests',
    ];
    $iterator = new \RecursiveIteratorIterator(
        new \RecursiveDirectoryIterator($srcDir, \FilesystemIterator::SKIP_DOTS),
    );
    foreach ($iterator as $file) {
        if ($file->isFile() && $file->getExtension() === 'php') {
            $realPath = $file->getRealPath();
            if (in_array($realPath, $excludes, true)) {
                continue;
            }
            $skip = false;
            foreach ($excludeDirs as $dir) {
                if (str_starts_with($realPath, $dir . '/')) {
                    $skip = true;
                    break;
                }
            }
            if ($skip) {
                continue;
            }
            $filter->includeFile($realPath);
        }
    }
    $coverage = new CodeCoverage((new Selector())->forLineCoverage($filter), $filter);
    $coverage->start('sentinel_command_test');
}

// ── 准备一个简单的 command 供 sentinel fork ──
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

// 一个立即返回的 dummy command
class SentinelDummyCommand extends Command
{
    protected function configure(): void
    {
        $this->setName('sentinel:dummy');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        return 0;
    }
}

class TestableSentinelCommand extends DaemonSentinelCommand
{
    protected function configure(): void
    {
        parent::configure();
        $this->setName('test:sentinel');
    }
}

$testCase = $argv[1] ?? 'sentinel_once';
$exitCode = 0;

try {
    switch ($testCase) {
        case 'sentinel_once':
            // 创建临时 sentinel 配置：运行 sentinel:dummy 一次
            $tmpFile = tempnam(sys_get_temp_dir(), 'sentinel_') . '.yml';
            file_put_contents($tmpFile, <<<YAML
commands:
    - name: sentinel:dummy
      once: true
      alert: false
YAML
            );

            $app = new Application('test', '1.0');
            $app->setAutoExit(false);
            $app->setCatchExceptions(false);
            $app->addCommand(new TestableSentinelCommand());
            $app->addCommand(new SentinelDummyCommand());

            $input = new ArrayInput([
                'command' => 'test:sentinel',
                'file'    => $tmpFile,
            ]);
            $output = new BufferedOutput();
            $exitCode = $app->run($input, $output);

            @unlink($tmpFile);
            break;

        case 'sentinel_parallel':
            // 测试 parallel=2
            $tmpFile = tempnam(sys_get_temp_dir(), 'sentinel_') . '.yml';
            file_put_contents($tmpFile, <<<YAML
commands:
    - name: sentinel:dummy
      parallel: 2
      once: true
      alert: false
YAML
            );

            $app = new Application('test', '1.0');
            $app->setAutoExit(false);
            $app->setCatchExceptions(false);
            $app->addCommand(new TestableSentinelCommand());
            $app->addCommand(new SentinelDummyCommand());

            $input = new ArrayInput([
                'command' => 'test:sentinel',
                'file'    => $tmpFile,
            ]);
            $output = new BufferedOutput();
            $exitCode = $app->run($input, $output);

            @unlink($tmpFile);
            break;

        default:
            fwrite(STDERR, "Unknown test case: $testCase\n");
            $exitCode = 99;
    }
} catch (\Throwable $e) {
    fwrite(STDERR, $e->getMessage() . "\n" . $e->getTraceAsString() . "\n");
    $exitCode = 98;
}

// ── 写覆盖率 ──
if ($coverage && $covFile) {
    $coverage->stop();
    (new Serializer())->serialize($covFile, $coverage);
}

exit($exitCode);
