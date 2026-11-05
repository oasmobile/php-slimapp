<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\SentinelCommand;

use Oasis\SlimApp\AbstractAlertableCommand;
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class DaemonSentinelCommandTest extends TestCase
{
    public function testDirectlyExtendsAbstractAlertableCommand(): void
    {
        $rc = new \ReflectionClass(DaemonSentinelCommand::class);
        $this->assertSame(
            AbstractAlertableCommand::class,
            $rc->getParentClass()->getName(),
            'DaemonSentinelCommand should directly extend AbstractAlertableCommand'
        );
    }

    public function testCommandName(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');
        $this->assertSame('test:sentinel', $command->getName());
    }

    public function testCommandDescription(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');
        $this->assertStringContainsStringIgnoringCase('sentinel', $command->getDescription());
    }

    public function testCommandHasFileArgument(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');
        $def     = $command->getDefinition();

        $this->assertTrue($def->hasArgument('file'));
        $this->assertTrue($def->getArgument('file')->isRequired());
    }

    public function testCommandHasAlertOption(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');
        $this->assertTrue($command->getDefinition()->hasOption('alert'));
    }

    public function testExecuteWithUnreadableFileReturnsNonZero(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:sentinel', 'file' => '/non/existent/file.yml']);
        $output = new BufferedOutput();

        $exitCode = $app->run($input, $output);

        $this->assertNotSame(0, $exitCode);
        $this->assertStringContainsString('not readable', $output->fetch());
    }

    public function testExecuteWithNonIntegerParallelThrowsException(): void
    {
        $command = new DaemonSentinelCommand('test:sentinel');

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->addCommand($command);

        // parallel 值为非整数字符串
        $tmpFile = sys_get_temp_dir() . '/sentinel_test_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "commands:\n    - name: list\n      parallel: 1.5\n");

        $input  = new ArrayInput(['command' => 'test:sentinel', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $this->expectException(\InvalidArgumentException::class);
            $this->expectExceptionMessage('parallel value is not an integer');
            $app->run($input, $output);
        } finally {
            @unlink($tmpFile);
        }
    }

}
