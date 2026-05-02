<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\AbstractAlertableCommand;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

class ConcreteAlertableCommand extends AbstractAlertableCommand
{
    private bool $shouldThrow;
    private int $returnCode;

    public function __construct(bool $shouldThrow = false, int $returnCode = 0)
    {
        $this->shouldThrow = $shouldThrow;
        $this->returnCode  = $returnCode;
        parent::__construct('test:alertable');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        if ($this->shouldThrow) {
            throw new \RuntimeException('Test exception');
        }

        return $this->returnCode;
    }
}

class AbstractAlertableCommandTest extends TestCase
{
    private Application $application;

    protected function setUp(): void
    {
        $this->application = new Application('test', '1.0');
        $this->application->setAutoExit(false);
        $this->application->setCatchExceptions(false);
    }

    public function testExitCodeConstants(): void
    {
        $this->assertEquals(0, AbstractAlertableCommand::EXIT_CODE_OK);
        $this->assertEquals(0xe1, AbstractAlertableCommand::EXIT_CODE_RESTART);
        $this->assertEquals(0xff, AbstractAlertableCommand::EXIT_CODE_COMMON_ERROR);
    }

    public function testCommandHasAlertOption(): void
    {
        $command = new ConcreteAlertableCommand();
        $this->application->addCommand($command);

        $def = $command->getDefinition();
        $this->assertTrue($def->hasOption('alert'));
        $this->assertFalse($def->getOption('alert')->acceptValue());
    }

    public function testRunWithoutExceptionReturnsNormally(): void
    {
        $command = new ConcreteAlertableCommand(false, 0);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunWithExceptionWithoutAlertRethrows(): void
    {
        $command = new ConcreteAlertableCommand(true);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Test exception');
        $this->application->run($input, $output);
    }

    public function testRunWithExceptionAndAlertOptionRethrows(): void
    {
        $command = new ConcreteAlertableCommand(true);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:alertable', '--alert' => true]);
        $output = new BufferedOutput();

        $this->expectException(\RuntimeException::class);
        $this->expectExceptionMessage('Test exception');
        $this->application->run($input, $output);
    }

    public function testRunWithCustomReturnCode(): void
    {
        $command = new ConcreteAlertableCommand(false, 42);
        $this->application->addCommand($command);

        $input  = new ArrayInput(['command' => 'test:alertable']);
        $output = new BufferedOutput();

        $exitCode = $this->application->run($input, $output);
        $this->assertEquals(42, $exitCode);
    }
}
