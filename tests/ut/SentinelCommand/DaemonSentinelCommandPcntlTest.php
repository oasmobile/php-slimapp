<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\SentinelCommand;

use Oasis\SlimApp\AbstractAlertableCommand;
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class DaemonSentinelCommandPcntlTest extends TestCase
{
    protected function setUp(): void
    {
        self::assertTrue(function_exists('pcntl_fork'), 'pcntl extension is required');
    }

    public function testExecuteWithEmptyConfigReturnsZero(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);

        $tmpFile = sys_get_temp_dir() . '/sentinel_test_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "commands: []\n");

        $input  = new ArrayInput(['command' => 'test:sentinel', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $exitCode = $app->run($input, $output);
            $this->assertSame(0, $exitCode);
        } finally {
            @unlink($tmpFile);
        }
    }

    public function testWaitForBackgroundProcessesExitsWhenNoChildren(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);

        // Use reflection to call waitForBackgroundProcesses with empty runningProcesses
        $ref = new \ReflectionMethod($command, 'waitForBackgroundProcesses');
        $propsRef = new \ReflectionProperty($command, 'runningProcesses');
        $propsRef->setValue($command, []);

        // Should exit immediately since no children exist (ECHILD)
        $ref->invoke($command);
        $this->assertEmpty($propsRef->getValue($command));
    }

    public function testExecuteWithSingleOnceCommandForksAndCompletes(): void
    {
        // Create a dummy command that exits immediately
        $dummyCommand = new class extends \Symfony\Component\Console\Command\Command {
            protected function configure(): void
            {
                $this->setName('dummy:exit');
            }
            protected function execute(
                \Symfony\Component\Console\Input\InputInterface $input,
                \Symfony\Component\Console\Output\OutputInterface $output
            ): int {
                return 0;
            }
        };

        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);
        $app->addCommand($dummyCommand);

        $tmpFile = sys_get_temp_dir() . '/sentinel_fork_test_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "commands:\n    - name: dummy:exit\n      once: true\n      alert: false\n");

        $input  = new ArrayInput(['command' => 'test:sentinel', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $exitCode = $app->run($input, $output);
            $this->assertSame(0, $exitCode);
        } finally {
            @unlink($tmpFile);
        }
    }

    public function testExecuteWithParallelOnceCommandForksMultiple(): void
    {
        $dummyCommand = new class extends \Symfony\Component\Console\Command\Command {
            protected function configure(): void
            {
                $this->setName('dummy:exit2');
            }
            protected function execute(
                \Symfony\Component\Console\Input\InputInterface $input,
                \Symfony\Component\Console\Output\OutputInterface $output
            ): int {
                return 0;
            }
        };

        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);
        $app->addCommand($dummyCommand);

        $tmpFile = sys_get_temp_dir() . '/sentinel_fork_test_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "commands:\n    - name: dummy:exit2\n      parallel: 3\n      once: true\n      alert: false\n");

        $input  = new ArrayInput(['command' => 'test:sentinel', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $exitCode = $app->run($input, $output);
            $this->assertSame(0, $exitCode);
        } finally {
            @unlink($tmpFile);
        }
    }
}
