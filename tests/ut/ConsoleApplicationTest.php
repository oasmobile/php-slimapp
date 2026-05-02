<?php

namespace Oasis\SlimApp\Tests;

use Monolog\Logger;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;

class ConsoleApplicationTest extends \PHPUnit_Framework_TestCase
{
    /** @var ConsoleApplication */
    private $app;

    protected function setUp()
    {
        $this->app = new ConsoleApplication('TestApp', '1.0.0');
    }

    public function testConstructorSetsNameAndVersion()
    {
        $this->assertEquals('TestApp', $this->app->getName());
        $this->assertEquals('1.0.0', $this->app->getVersion());
    }

    public function testDefaultConstructorValues()
    {
        $app = new ConsoleApplication();
        $this->assertEquals('UNKNOWN', $app->getName());
        $this->assertEquals('UNKNOWN', $app->getVersion());
    }

    public function testLoggingEnabledByDefault()
    {
        $this->assertTrue($this->app->isLoggingEnabled());
    }

    public function testSetLoggingEnabled()
    {
        $this->app->setLoggingEnabled(false);
        $this->assertFalse($this->app->isLoggingEnabled());

        $this->app->setLoggingEnabled(true);
        $this->assertTrue($this->app->isLoggingEnabled());
    }

    public function testDefaultLogFilePattern()
    {
        $this->assertEquals('%date%/%script%.%command%.%type%', $this->app->getLogFilePattern());
    }

    public function testSetLogFilePattern()
    {
        $this->app->setLogFilePattern('custom/%script%.%type%');
        $this->assertEquals('custom/%script%.%type%', $this->app->getLogFilePattern());
    }

    public function testDefaultLoggingLevel()
    {
        $this->assertEquals(Logger::DEBUG, $this->app->getLoggingLevel());
    }

    public function testSetLoggingLevel()
    {
        $this->app->setLoggingLevel(Logger::WARNING);
        $this->assertEquals(Logger::WARNING, $this->app->getLoggingLevel());
    }

    public function testGetLoggingPathDefaultsToTempDir()
    {
        $path = $this->app->getLoggingPath();
        $this->assertEquals(sys_get_temp_dir() . '/logs', $path);
    }

    public function testSetLoggingPath()
    {
        $this->app->setLoggingPath('/custom/log/path');
        $this->assertEquals('/custom/log/path', $this->app->getLoggingPath());
    }

    public function testGetSlimappDefaultsToNull()
    {
        $this->assertNull($this->app->getSlimapp());
    }

    public function testSetSlimapp()
    {
        $slimapp = $this->getMockBuilder(SlimApp::class)
                        ->disableOriginalConstructor()
                        ->getMock();
        $this->app->setSlimapp($slimapp);
        $this->assertSame($slimapp, $this->app->getSlimapp());
    }

    public function testSetLoggingPathToNull()
    {
        $this->app->setLoggingPath(null);
        $this->assertEquals(sys_get_temp_dir() . '/logs', $this->app->getLoggingPath());
    }

    public function testSetLoggingPathPersists()
    {
        $this->app->setLoggingPath('/first/path');
        $this->assertEquals('/first/path', $this->app->getLoggingPath());

        $this->app->setLoggingPath('/second/path');
        $this->assertEquals('/second/path', $this->app->getLoggingPath());
    }

    public function testRunCommandTriggersLogging()
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list']);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithLoggingDisabled()
    {
        $this->app->setLoggingEnabled(false);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list']);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithVerboseOutput()
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '-v' => true]);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithVeryVerboseOutput()
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '-vv' => true]);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithDebugOutput()
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '-vvv' => true]);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithQuietOutput()
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new \Symfony\Component\Console\Input\ArrayInput(['command' => 'list', '-q' => true]);
        $output = new \Symfony\Component\Console\Output\BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }
}
