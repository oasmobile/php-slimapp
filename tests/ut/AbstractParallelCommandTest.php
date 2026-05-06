<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\AbstractParallelCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

class ConcreteParallelCommand extends AbstractParallelCommand
{
    private int $executionCount = 0;
    private int $returnCode;

    public function __construct(int $returnCode = 0)
    {
        $this->returnCode = $returnCode;
        parent::__construct('test:parallel');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output): int
    {
        $this->executionCount++;

        return $this->returnCode;
    }

    public function getExecutionCount(): int
    {
        return $this->executionCount;
    }

    public function exposeGetParallelCount(): int
    {
        return $this->getParallelCount();
    }
}

class AbstractParallelCommandTest extends TestCase
{
    private Application $application;

    protected function setUp(): void
    {
        $this->application = new Application('test', '1.0');
        $this->application->setAutoExit(false);
        $this->application->setCatchExceptions(false);
    }

    public function testCommandHasParallelOption(): void
    {
        $command = new ConcreteParallelCommand();
        $this->application->addCommand($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('parallel'));
        $this->assertTrue($def->getOption('parallel')->isValueRequired());
    }

    public function testCommandHasNoOverflowConfirmOption(): void
    {
        $command = new ConcreteParallelCommand();
        $this->application->addCommand($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('no-overflow-confirm'));
    }

    public function testCommandInheritsAlertOption(): void
    {
        $command = new ConcreteParallelCommand();
        $this->application->addCommand($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('alert'));
    }

    public function testSingleParallelExecutesDirectly(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
        $this->assertEquals(1, $command->getExecutionCount());
    }

    public function testDefaultParallelIsOne(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
        $this->assertEquals(1, $command->getExecutionCount());
    }

    public function testParallelCountLessThanOneThrowsException(): void
    {
        $command = new ConcreteParallelCommand();
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '0',
        ]);
        $output = new BufferedOutput();

        $this->expectException(\InvalidArgumentException::class);
        $this->application->run($input, $output);
    }

    public function testNegativeParallelCountThrowsException(): void
    {
        $command = new ConcreteParallelCommand();
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '-1',
        ]);
        $output = new BufferedOutput();

        $this->expectException(\InvalidArgumentException::class);
        $this->application->run($input, $output);
    }

    public function testSingleParallelReturnsCustomExitCode(): void
    {
        $command = new ConcreteParallelCommand(42);
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(42, $exitCode);
    }

    public function testGetParallelCountAfterExecution(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $this->application->run($input, $output);
        $this->assertEquals(1, $command->exposeGetParallelCount());
    }

    public function testOnChildProcessExitWithOkStatus(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setValue($command, [123]);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_OK, $input, $output);

        $this->assertEmpty($pidsRef->getValue($command));
    }

    public function testOnChildProcessExitWithCommonError(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setValue($command, [123]);

        $failedRef = new \ReflectionProperty(AbstractParallelCommand::class, 'isFailed');

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_COMMON_ERROR, $input, $output);

        $this->assertTrue($failedRef->getValue($command));
    }

    public function testOnChildProcessExitWithUnknownPid(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setValue($command, [456]);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 999, 0, $input, $output);

        $this->assertEquals([456], $pidsRef->getValue($command));
    }

    public function testExitCodeConstants(): void
    {
        $this->assertEquals(0, AbstractParallelCommand::EXIT_CODE_OK);
        $this->assertEquals(0xe1, AbstractParallelCommand::EXIT_CODE_RESTART);
        $this->assertEquals(0xff, AbstractParallelCommand::EXIT_CODE_COMMON_ERROR);
    }

    public function testOverflowParallelWithNoConfirmOptionSkipsPrompt(): void
    {
        if (!function_exists('pcntl_fork')) {
            $this->markTestSkipped('pcntl not available');
        }

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

    public function testOverflowParallelWithoutConfirmDenied(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        // Simulate user denying the confirmation (input stream with "n")
        $input = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '15',
        ]);
        $input->setInteractive(true);

        // Create an input stream that answers "n"
        $stream = fopen('php://memory', 'r+');
        assert($stream !== false);
        fwrite($stream, "n\n");
        rewind($stream);
        $input->setStream($stream);

        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(-1, $exitCode);
        fclose($stream);
    }

    public function testOverflowParallelWithConfirmAccepted(): void
    {
        // Use a command that tracks whether doExecute was reached via fork path
        // Since we can't fork in PHPUnit, we test the non-fork path indirectly
        // by verifying the confirmation prompt is shown and accepted
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

        // This will try to fork, which will fail or succeed depending on pcntl
        // The important thing is it passes the confirmation check
        if (function_exists('pcntl_fork')) {
            $exitCode = $this->application->run($input, $output);
            // With pcntl available, it will fork and wait — should succeed
            $this->assertEquals(0, $exitCode);
        } else {
            $this->markTestSkipped('pcntl not available');
        }
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
        if (function_exists('pcntl_fork')) {
            $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_RESTART, $input, $output);
            // After restart, pids should have a new entry (the restarted child)
            $pids = $pidsRef->getValue($command);
            $this->assertNotEmpty($pids);
            // Wait for the child to finish
            foreach ($pids as $pid) {
                pcntl_waitpid($pid, $status);
            }
        } else {
            $this->markTestSkipped('pcntl not available');
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
        if (function_exists('pcntl_fork')) {
            $ref = new \ReflectionMethod($command, 'waitForBackground');
            $result = $ref->invoke($command, $input, $output);
            // isFailed is false by default, so should return EXIT_CODE_OK
            $this->assertEquals(AbstractParallelCommand::EXIT_CODE_OK, $result);
        } else {
            $this->markTestSkipped('pcntl not available');
        }
    }

    public function testWaitForBackgroundReturnErrorWhenFailed(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        if (function_exists('pcntl_fork')) {
            // Set isFailed to true
            $failedRef = new \ReflectionProperty(AbstractParallelCommand::class, 'isFailed');
            $failedRef->setValue($command, true);

            $ref = new \ReflectionMethod($command, 'waitForBackground');
            $result = $ref->invoke($command, $input, $output);
            $this->assertEquals(AbstractParallelCommand::EXIT_CODE_COMMON_ERROR, $result);
        } else {
            $this->markTestSkipped('pcntl not available');
        }
    }

    public function testDoForkReturnsChildPid(): void
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        if (function_exists('pcntl_fork')) {
            $ref = new \ReflectionMethod($command, 'doFork');
            $pid = $ref->invoke($command, $input, $output);
            $this->assertGreaterThan(0, $pid);
            // Clean up child
            pcntl_waitpid($pid, $status);
        } else {
            $this->markTestSkipped('pcntl not available');
        }
    }

    public function testParallelExecutionWithMultipleProcesses(): void
    {
        if (!function_exists('pcntl_fork')) {
            $this->markTestSkipped('pcntl not available');
        }

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
        if (!function_exists('pcntl_fork')) {
            $this->markTestSkipped('pcntl not available');
        }

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
