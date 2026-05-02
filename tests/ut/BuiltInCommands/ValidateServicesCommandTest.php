<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\BuiltInCommands;

use Oasis\SlimApp\BuiltInCommands\ValidateServicesCommand;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class ValidateServicesCommandTest extends TestCase
{
    public function testCommandNameAndDescription(): void
    {
        $command = new ValidateServicesCommand();
        $this->assertEquals('slimapp:services:validate', $command->getName());
        $this->assertNotEmpty($command->getDescription());
    }

    public function testExecuteValidatesServices(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getServiceIds')->willReturn(['app', 'test.service']);
        $slimapp->method('getService')->willReturn(new \stdClass());

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->addCommand(new ValidateServicesCommand());

        $input  = new ArrayInput(['command' => 'slimapp:services:validate']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertStringContainsString('Validating', $text);
        $this->assertStringContainsString('Done', $text);
    }

    public function testExecuteHandlesMisconfiguredService(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getServiceIds')->willReturn(['bad.service']);
        $slimapp->method('getService')->willThrowException(new \RuntimeException('Service misconfigured'));

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->addCommand(new ValidateServicesCommand());

        $input  = new ArrayInput(['command' => 'slimapp:services:validate']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertStringContainsString('Validating', $text);
        $this->assertStringContainsString('misconfigured', $text);
    }
}
