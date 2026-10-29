<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\SentinelCommand\CommandRunner;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Output\BufferedOutput;

class CommandRunnerPcntlTest extends TestCase
{
    protected function setUp(): void
    {
        self::assertTrue(function_exists('pcntl_fork'), 'pcntl extension is required');
    }

    public function testRunForksAndReturnsChildPid(): void
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->addCommand(new \Symfony\Component\Console\Command\Command('list'));

        $command = [
            'name' => 'list', 'args' => [],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => false,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 0, $command, $output);

        $pid = $runner->run();
        $this->assertGreaterThan(0, $pid);

        // Clean up child process
        pcntl_waitpid($pid, $status);
    }

    public function testRunSetsLastRunAndCurrentPid(): void
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->addCommand(new \Symfony\Component\Console\Command\Command('list'));

        $command = [
            'name' => 'list', 'args' => [],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => false,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 0, $command, $output);

        $pid = $runner->run();

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $currentPidRef = new \ReflectionProperty($runner, 'currentPid');

        $this->assertGreaterThan(0, $lastRunRef->getValue($runner));
        $this->assertEquals($pid, $currentPidRef->getValue($runner));

        pcntl_waitpid($pid, $status);
    }
}
