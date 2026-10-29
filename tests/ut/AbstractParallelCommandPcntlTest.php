<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\AbstractParallelCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

use Oasis\SlimApp\Tests\Fixtures\ConcreteParallelCommand;

class AbstractParallelCommandPcntlTest extends TestCase
{
    private Application $application;

    protected function setUp(): void
    {
        self::assertTrue(function_exists('pcntl_fork'), 'pcntl extension is required');
        $this->application = new Application('test', '1.0');
        $this->application->setAutoExit(false);
        $this->application->setCatchExceptions(false);
    }

    public function testOverflowParallelWithNoConfirmOptionSkipsPrompt(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'              => 'test:parallel',
            '--parallel'           => '15',
            '--no-overflow-confirm' => true,
        ]);
        $output = new BufferedOutput();

        // With --no-overflow-confirm and parallel > 10, it skips confirmation and forks
        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
        $this->assertEquals(15, $command->exposeGetParallelCount());
    }

    public function testOverflowParallelWithConfirmAccepted(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '15',
        ]);
        $input->setInteractive(true);

        $stream = fopen('php://memory', 'r+');
        assert($stream !== false);
        fwrite($stream, "y\n");
        rewind($stream);
        $input->setStream($stream);

        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);

        fclose($stream);
    }

    public function testOnChildProcessExitWithRestartCode(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setValue($command, [123]);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        // onChildProcessExit with RESTART code will call doFork — which requires pcntl
        $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_RESTART, $input, $output);
        // After restart, pids should have a new entry (the restarted child)
        $pids = $pidsRef->getValue($command);
        $this->assertNotEmpty($pids);
        // Wait for the child to finish
        foreach ($pids as $pid) {
            pcntl_waitpid($pid, $status);
        }

    }

    public function testWaitForBackgroundWithAllChildrenFinished(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        // Simulate: no children running (pcntl_waitpid returns -1 with ECHILD)
        // This happens when pids is empty and we call waitForBackground
        $ref = new \ReflectionMethod($command, 'waitForBackground');
        $result = $ref->invoke($command, $input, $output);
        // isFailed is false by default, so should return EXIT_CODE_OK
        $this->assertEquals(AbstractParallelCommand::EXIT_CODE_OK, $result);

    }

    public function testWaitForBackgroundReturnErrorWhenFailed(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        // Set isFailed to true
        $failedRef = new \ReflectionProperty(AbstractParallelCommand::class, 'isFailed');
        $failedRef->setValue($command, true);

        $ref = new \ReflectionMethod($command, 'waitForBackground');
        $result = $ref->invoke($command, $input, $output);
        $this->assertEquals(AbstractParallelCommand::EXIT_CODE_COMMON_ERROR, $result);

    }

    public function testDoForkReturnsChildPid(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref = new \ReflectionMethod($command, 'doFork');
        $pid = $ref->invoke($command, $input, $output);
        $this->assertGreaterThan(0, $pid);
        // Clean up child
        pcntl_waitpid($pid, $status);

    }

    public function testParallelExecutionWithMultipleProcesses(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '3',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testParallelExecutionWithChildFailure(): void
    {
        $command = new ConcreteParallelCommand(255); // EXIT_CODE_COMMON_ERROR
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '2',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(AbstractParallelCommand::EXIT_CODE_COMMON_ERROR, $exitCode);
    }
}
