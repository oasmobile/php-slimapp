<?php

namespace Oasis\SlimApp\Tests\SentinelCommand;

use Oasis\SlimApp\SentinelCommand\AbstractDaemonSentinelCommand;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class AbstractDaemonSentinelCommandTest extends \PHPUnit_Framework_TestCase
{
    public function testCommandHasFileArgument()
    {
        $command = $this->getMockBuilder(AbstractDaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:daemon'])
                        ->getMockForAbstractClass();

        $def = $command->getDefinition();
        $this->assertTrue($def->hasArgument('file'));
        $this->assertTrue($def->getArgument('file')->isRequired());
    }

    public function testCommandHasAlertOption()
    {
        $command = $this->getMockBuilder(AbstractDaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:daemon'])
                        ->getMockForAbstractClass();

        $this->assertTrue($command->getDefinition()->hasOption('alert'));
    }

    public function testCommandDescription()
    {
        $command = $this->getMockBuilder(AbstractDaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:daemon'])
                        ->getMockForAbstractClass();

        $this->assertContains('sentinel', strtolower($command->getDescription()));
    }

    public function testExecuteWithInvalidConfigFile()
    {
        $command = $this->getMockBuilder(AbstractDaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:daemon'])
                        ->getMockForAbstractClass();

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->add($command);

        $tmpFile = sys_get_temp_dir() . '/sentinel_bad_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "invalid: [unclosed");

        $input  = new ArrayInput(['command' => 'test:daemon', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $app->run($input, $output);
        } catch (\Exception $e) {
            $this->assertNotEmpty($e->getMessage());
        } finally {
            @unlink($tmpFile);
        }
    }

    public function testExecuteWithValidEmptyConfigFile()
    {
        $command = $this->getMockBuilder(AbstractDaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:daemon'])
                        ->getMockForAbstractClass();

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->setCatchExceptions(false);
        $app->add($command);

        $tmpFile = sys_get_temp_dir() . '/sentinel_test_' . uniqid() . '.yml';
        file_put_contents($tmpFile, "commands: []\n");

        $input  = new ArrayInput(['command' => 'test:daemon', 'file' => $tmpFile]);
        $output = new BufferedOutput();

        try {
            $exitCode = $app->run($input, $output);
            $this->assertEquals(0, $exitCode);
        } finally {
            @unlink($tmpFile);
        }
    }
}
