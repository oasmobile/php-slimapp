<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SentinelCommand\CommandConfiguration;
use Oasis\SlimApp\SlimApp;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Console\Application;

class CommandConfigurationTest extends TestCase
{
    public function testGetConfigTreeBuilderReturnsTreeBuilder(): void
    {
        $app    = new Application('test', '1.0');
        $config = new CommandConfiguration($app);
        $tree   = $config->getConfigTreeBuilder();

        $this->assertInstanceOf(
            'Symfony\\Component\\Config\\Definition\\Builder\\TreeBuilder',
            $tree
        );
    }

    public function testProcessMinimalConfig(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command']]],
        ]);

        $this->assertArrayHasKey('commands', $result);
        $this->assertCount(1, $result['commands']);
        $this->assertEquals('test:command', $result['commands'][0]['name']);
        $this->assertEquals([], $result['commands'][0]['args']);
        $this->assertEquals(1, $result['commands'][0]['parallel']);
        $this->assertFalse($result['commands'][0]['once']);
        $this->assertTrue($result['commands'][0]['alert']);
        $this->assertEquals(0, $result['commands'][0]['interval']);
        $this->assertEquals(0, $result['commands'][0]['frequency']);
        $this->assertFalse($result['commands'][0]['frequency_fixed']);
    }

    public function testProcessFullConfig(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            [
                'commands' => [
                    [
                        'name'            => 'test:command',
                        'args'            => ['--verbose' => true, 'arg1' => 'value1'],
                        'parallel'        => 4,
                        'once'            => true,
                        'alert'           => false,
                        'interval'        => 10,
                        'frequency'       => 30,
                        'frequency_fixed' => true,
                    ],
                ],
            ],
        ]);

        $cmd = $result['commands'][0];
        $this->assertEquals('test:command', $cmd['name']);
        $this->assertEquals(['--verbose' => true, 'arg1' => 'value1'], $cmd['args']);
        $this->assertEquals(4, $cmd['parallel']);
        $this->assertTrue($cmd['once']);
        $this->assertFalse($cmd['alert']);
        $this->assertEquals(10, $cmd['interval']);
        $this->assertEquals(30, $cmd['frequency']);
        $this->assertTrue($cmd['frequency_fixed']);
    }

    public function testProcessMultipleCommands(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            ['commands' => [['name' => 'cmd:one'], ['name' => 'cmd:two'], ['name' => 'cmd:three']]],
        ]);

        $this->assertCount(3, $result['commands']);
    }

    public function testProcessEmptyCommands(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [['commands' => []]]);

        $this->assertCount(0, $result['commands']);
    }

    public function testArgsNonArrayThrowsException(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $this->expectException(InvalidConfigurationException::class);
        $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command', 'args' => 'not-an-array']]],
        ]);
    }

    public function testParameterReplacementWithConsoleApplication(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getParameter')
                ->willReturnMap([['app.name', 'TestApp'], ['app.count', 3]]);

        $consoleApp = new ConsoleApplication('test', '1.0');
        $consoleApp->setSlimapp($slimapp);

        $config    = new CommandConfiguration($consoleApp);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command', 'parallel' => '%app.count%']]],
        ]);

        $this->assertEquals(3, $result['commands'][0]['parallel']);
    }

    public function testParameterReplacementInArgs(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getParameter')
                ->willReturnMap([['app.name', 'TestApp']]);

        $consoleApp = new ConsoleApplication('test', '1.0');
        $consoleApp->setSlimapp($slimapp);

        $config    = new CommandConfiguration($consoleApp);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command', 'args' => ['a' => '%app.name%']]]],
        ]);

        $this->assertEquals('TestApp', $result['commands'][0]['args']['a']);
    }

    public function testNoParameterReplacementWithPlainApplication(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $result = $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command', 'parallel' => 2]]],
        ]);

        $this->assertEquals(2, $result['commands'][0]['parallel']);
    }

    public function testMissingNameThrowsException(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        $this->expectException(\Exception::class);
        $processor->processConfiguration($config, [
            ['commands' => [['parallel' => 1]]],
        ]);
    }

    public function testParameterReplacementWithNullValueThrowsException(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getParameter')->willReturn(null);

        $consoleApp = new ConsoleApplication('test', '1.0');
        $consoleApp->setSlimapp($slimapp);

        $config    = new CommandConfiguration($consoleApp);
        $processor = new Processor();

        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Cannot get config value');
        $processor->processConfiguration($config, [
            ['commands' => [['name' => 'test:command', 'parallel' => '%nonexistent.param%']]],
        ]);
    }
}
