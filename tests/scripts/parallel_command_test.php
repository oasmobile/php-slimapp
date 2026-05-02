<?php
/**
 * 独立进程测试脚本：AbstractParallelCommand 多进程分支
 *
 * 在独立进程中运行，避免 fork 干扰 PHPUnit。
 * 手动收集代码覆盖率并写入 .cov 文件供 PHPUnit 合并。
 */

require_once __DIR__ . '/../../vendor/autoload.php';

use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;

// ── 覆盖率收集 ──
$covFile = getenv('COVERAGE_FILE');
$coverage = null;
if ($covFile) {
    $filter = new Filter();
    $srcDir = __DIR__ . '/../../src';
    $iterator = new \RecursiveIteratorIterator(
        new \RecursiveDirectoryIterator($srcDir, \FilesystemIterator::SKIP_DOTS),
    );
    foreach ($iterator as $file) {
        if ($file->isFile() && $file->getExtension() === 'php') {
            $filter->includeFile($file->getRealPath());
        }
    }
    $coverage = new CodeCoverage((new Selector())->forLineCoverage($filter), $filter);
    $coverage->start('parallel_command_test');
}

// ── 测试逻辑 ──
use Oasis\SlimApp\AbstractParallelCommand;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

class ForkTestCommand extends AbstractParallelCommand
{
    protected function configure(): void
    {
        parent::configure();
        $this->setName('fork:test');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output): int
    {
        // 子进程里简单返回 OK
        return self::EXIT_CODE_OK;
    }
}

$testCase = $argv[1] ?? 'parallel_ok';
$exitCode = 0;

try {
    switch ($testCase) {
        case 'parallel_ok':
            // 测试 parallel=2 正常 fork 并等待
            $app = new Application('test', '1.0');
            $app->setAutoExit(false);
            $app->setCatchExceptions(false);
            $app->addCommand(new ForkTestCommand());

            $input = new ArrayInput([
                'command'    => 'fork:test',
                '--parallel' => '2',
            ]);
            $output = new BufferedOutput();
            $exitCode = $app->run($input, $output);
            break;

        case 'parallel_fail':
            // 测试子进程返回错误码
            $failCmd = new class extends AbstractParallelCommand {
                protected function configure(): void
                {
                    parent::configure();
                    $this->setName('fork:fail');
                }
                protected function doExecute(InputInterface $input, OutputInterface $output): int
                {
                    return self::EXIT_CODE_COMMON_ERROR;
                }
            };

            $app = new Application('test', '1.0');
            $app->setAutoExit(false);
            $app->setCatchExceptions(false);
            $app->addCommand($failCmd);

            $input = new ArrayInput([
                'command'    => 'fork:fail',
                '--parallel' => '2',
            ]);
            $output = new BufferedOutput();
            $exitCode = $app->run($input, $output);
            break;

        default:
            fwrite(STDERR, "Unknown test case: $testCase\n");
            $exitCode = 99;
    }
} catch (\Throwable $e) {
    fwrite(STDERR, $e->getMessage() . "\n");
    $exitCode = 98;
}

// ── 写覆盖率 ──
if ($coverage && $covFile) {
    $coverage->stop();
    file_put_contents($covFile, serialize($coverage));
}

exit($exitCode);
