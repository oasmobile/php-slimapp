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
}
