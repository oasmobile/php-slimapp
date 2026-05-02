<?php

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\AbstractAlertableCommand;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

class ConcreteAlertableCommand extends AbstractAlertableCommand
{
    private $shouldThrow = false;
    private $returnCode  = 0;

    public function __construct($shouldThrow = false, $returnCode = 0)
    {
        $this->shouldThrow = $shouldThrow;
        $this->returnCode  = $returnCode;
        parent::__construct('test:alertable');
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        if ($this->shouldThrow) {
            throw new \RuntimeException('Test exception');
        }

        return $this->returnCode;
    }
}

class AbstractAlertableCommandTest extends \PHPUnit_Framework_TestCase
{
    /** @var Application */
    private $application;

    protected function setUp()
    {
        $this->application = new Application('test', '1.0');
        $this->application->setAutoExit(false);
        $this->application->setCatchExceptions(false);
    }

    public function testExitCodeConstants()
    {
        $this->assertEquals(0, AbstractAlertableCommand::EXIT_CODE_OK);
        $this->assertEquals(0xe1, AbstractAlertableCommand::EXIT_CODE_RESTART);
        $this->assertEquals(0xff, AbstractAlertableCommand::EXIT_CODE_COMMON_ERROR);
    }

    public function testCommandHasAlertOption()
    {
        $command = new ConcreteAlertableCommand();
        $this->application->add($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('alert'));
        $this->assertFalse($def->getOption('alert')->acceptValue());
    }

    public function testRunWithoutExceptionReturnsNormally()
    {
        $command = new ConcreteAlertableCommand(false, 0);
        $this->application->add($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunWithExceptionWithoutAlertRethrows()
    {
        $command = new ConcreteAlertableCommand(true);
        $this->application->add($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $this->setExpectedException(\RuntimeException::class, 'Test exception');
        $this->application->run($input, $output);
    }

    public function testRunWithExceptionAndAlertOptionRethrows()
    {
        $command = new ConcreteAlertableCommand(true);
        $this->application->add($command);

        $input  = new ArrayInput(['command' => 'test:alertable', '--alert' => true]);
        $output = new BufferedOutput();

        $this->setExpectedException(\RuntimeException::class, 'Test exception');
        $this->application->run($input, $output);
    }

    public function testRunWithCustomReturnCode()
    {
        $command = new ConcreteAlertableCommand(false, 42);
        $this->application->add($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(42, $exitCode);
    }
}
