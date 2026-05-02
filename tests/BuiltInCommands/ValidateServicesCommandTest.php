<?php

namespace Oasis\SlimApp\Tests\BuiltInCommands;

use Oasis\SlimApp\BuiltInCommands\ValidateServicesCommand;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class ValidateServicesCommandTest extends \PHPUnit_Framework_TestCase
{
    public function testCommandNameAndDescription()
    {
        $command = new ValidateServicesCommand();
        $this->assertEquals('slimapp:services:validate', $command->getName());
        $this->assertNotEmpty($command->getDescription());
    }

    public function testExecuteValidatesServices()
    {
        $slimapp = $this->getMockBuilder(SlimApp::class)
                        ->disableOriginalConstructor()
                        ->getMock();
        $slimapp->method('getServiceIds')->willReturn(['app', 'test.service']);
        $slimapp->method('getService')->willReturn(new \stdClass());

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->add(new ValidateServicesCommand());

        $input  = new ArrayInput(['command' => 'slimapp:services:validate']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertContains('Validating', $text);
        $this->assertContains('Done', $text);
    }

    public function testExecuteHandlesMisconfiguredService()
    {
        $slimapp = $this->getMockBuilder(SlimApp::class)
                        ->disableOriginalConstructor()
                        ->getMock();
        $slimapp->method('getServiceIds')->willReturn(['bad.service']);
        $slimapp->method('getService')->willThrowException(new \RuntimeException('Service misconfigured'));

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->add(new ValidateServicesCommand());

        $input  = new ArrayInput(['command' => 'slimapp:services:validate']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertContains('Validating', $text);
        $this->assertContains('misconfigured', $text);
    }
}
