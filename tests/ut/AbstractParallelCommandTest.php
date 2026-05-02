<?php

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\AbstractParallelCommand;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

class ConcreteParallelCommand extends AbstractParallelCommand
{
    private $executionCount = 0;
    private $returnCode     = 0;

    public function __construct($returnCode = 0)
    {
        $this->returnCode = $returnCode;
        parent::__construct('test:parallel');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output)
    {
        $this->executionCount++;

        return $this->returnCode;
    }

    public function getExecutionCount()
    {
        return $this->executionCount;
    }

    public function exposeGetParallelCount()
    {
        return $this->getParallelCount();
    }
}

class AbstractParallelCommandTest extends \PHPUnit_Framework_TestCase
{
    /** @var Application */
    private $application;

    protected function setUp()
    {
        $this->application = new Application('test', '1.0');
        $this->application->setAutoExit(false);
        $this->application->setCatchExceptions(false);
    }

    public function testCommandHasParallelOption()
    {
        $command = new ConcreteParallelCommand();
        $this->application->add($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('parallel'));
        $this->assertTrue($def->getOption('parallel')->isValueRequired());
    }

    public function testCommandHasNoOverflowConfirmOption()
    {
        $command = new ConcreteParallelCommand();
        $this->application->add($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('no-overflow-confirm'));
    }

    public function testCommandInheritsAlertOption()
    {
        $command = new ConcreteParallelCommand();
        $this->application->add($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('alert'));
    }

    public function testSingleParallelExecutesDirectly()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
        $this->assertEquals(1, $command->getExecutionCount());
    }

    public function testDefaultParallelIsOne()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
        $this->assertEquals(1, $command->getExecutionCount());
    }

    public function testParallelCountLessThanOneThrowsException()
    {
        $command = new ConcreteParallelCommand();
        $this->application->add($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '0',
        ]);
        $output = new BufferedOutput();

        $this->setExpectedException(\InvalidArgumentException::class);
        $this->application->run($input, $output);
    }

    public function testNegativeParallelCountThrowsException()
    {
        $command = new ConcreteParallelCommand();
        $this->application->add($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '-1',
        ]);
        $output = new BufferedOutput();

        $this->setExpectedException(\InvalidArgumentException::class);
        $this->application->run($input, $output);
    }

    public function testSingleParallelReturnsCustomExitCode()
    {
        $command = new ConcreteParallelCommand(42);
        $this->application->add($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(42, $exitCode);
    }

    public function testGetParallelCountAfterExecution()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $input  = new ArrayInput([
            'command'    => 'test:parallel',
            '--parallel' => '1',
        ]);
        $output = new BufferedOutput();

        $this->application->run($input, $output);
        $this->assertEquals(1, $command->exposeGetParallelCount());
    }

    public function testOnChildProcessExitWithOkStatus()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');
        $ref->setAccessible(true);

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setAccessible(true);
        $pidsRef->setValue($command, [123]);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_OK, $input, $output);

        $this->assertEmpty($pidsRef->getValue($command));
    }

    public function testOnChildProcessExitWithCommonError()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');
        $ref->setAccessible(true);

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setAccessible(true);
        $pidsRef->setValue($command, [123]);

        $failedRef = new \ReflectionProperty(AbstractParallelCommand::class, 'isFailed');
        $failedRef->setAccessible(true);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 123, AbstractParallelCommand::EXIT_CODE_COMMON_ERROR, $input, $output);

        $this->assertTrue($failedRef->getValue($command));
    }

    public function testOnChildProcessExitWithUnknownPid()
    {
        $command = new ConcreteParallelCommand(0);
        $this->application->add($command);

        $ref = new \ReflectionMethod($command, 'onChildProcessExit');
        $ref->setAccessible(true);

        $pidsRef = new \ReflectionProperty(AbstractParallelCommand::class, 'pids');
        $pidsRef->setAccessible(true);
        $pidsRef->setValue($command, [456]);

        $input  = new ArrayInput(['command' => 'test:parallel']);
        $output = new BufferedOutput();

        $ref->invoke($command, 999, 0, $input, $output);

        $this->assertEquals([456], $pidsRef->getValue($command));
    }

    public function testExitCodeConstants()
    {
        $this->assertEquals(0, AbstractParallelCommand::EXIT_CODE_OK);
        $this->assertEquals(0xe1, AbstractParallelCommand::EXIT_CODE_RESTART);
        $this->assertEquals(0xff, AbstractParallelCommand::EXIT_CODE_COMMON_ERROR);
    }
}
