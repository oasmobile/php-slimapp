<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Monolog\Level;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;

class ConsoleApplicationTest extends TestCase
{
    private ConsoleApplication $app;

    protected function setUp(): void
    {
        $this->app = new ConsoleApplication('TestApp', '1.0.0');
    }

    public function testConstructorSetsNameAndVersion(): void
    {
        $this->assertEquals('TestApp', $this->app->getName());
        $this->assertEquals('1.0.0', $this->app->getVersion());
    }

    public function testDefaultConstructorValues(): void
    {
        $app = new ConsoleApplication();
        $this->assertEquals('UNKNOWN', $app->getName());
        $this->assertEquals('UNKNOWN', $app->getVersion());
    }

    public function testLoggingEnabledByDefault(): void
    {
        $this->assertTrue($this->app->isLoggingEnabled());
    }

    public function testSetLoggingEnabled(): void
    {
        $this->app->setLoggingEnabled(false);
        $this->assertFalse($this->app->isLoggingEnabled());

        $this->app->setLoggingEnabled(true);
        $this->assertTrue($this->app->isLoggingEnabled());
    }

    public function testDefaultLogFilePattern(): void
    {
        $this->assertEquals('%date%/%script%.%command%.%type%', $this->app->getLogFilePattern());
    }

    public function testSetLogFilePattern(): void
    {
        $this->app->setLogFilePattern('custom/%script%.%type%');
        $this->assertEquals('custom/%script%.%type%', $this->app->getLogFilePattern());
    }

    public function testDefaultLoggingLevel(): void
    {
        $this->assertEquals(Level::Debug, $this->app->getLoggingLevel());
    }

    public function testSetLoggingLevel(): void
    {
        $this->app->setLoggingLevel(Level::Warning);
        $this->assertEquals(Level::Warning, $this->app->getLoggingLevel());
    }

    public function testGetLoggingPathDefaultsToTempDir(): void
    {
        $path = $this->app->getLoggingPath();
        $this->assertEquals(sys_get_temp_dir() . '/logs', $path);
    }

    public function testSetLoggingPath(): void
    {
        $this->app->setLoggingPath('/custom/log/path');
        $this->assertEquals('/custom/log/path', $this->app->getLoggingPath());
    }

    public function testGetSlimappDefaultsToNull(): void
    {
        $this->assertNull($this->app->getSlimapp());
    }

    public function testSetSlimapp(): void
    {
        $slimapp = $this->createStub(SlimApp::class);
        $this->app->setSlimapp($slimapp);
        $this->assertSame($slimapp, $this->app->getSlimapp());
    }

    public function testSetLoggingPathToNull(): void
    {
        $this->app->setLoggingPath(null);
        $this->assertEquals(sys_get_temp_dir() . '/logs', $this->app->getLoggingPath());
    }

    public function testSetLoggingPathPersists(): void
    {
        $this->app->setLoggingPath('/first/path');
        $this->assertEquals('/first/path', $this->app->getLoggingPath());

        $this->app->setLoggingPath('/second/path');
        $this->assertEquals('/second/path', $this->app->getLoggingPath());
    }

    public function testRunCommandTriggersLogging(): void
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list']);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithLoggingDisabled(): void
    {
        $this->app->setLoggingEnabled(false);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list']);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithVerboseOutput(): void
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list', '-v' => true]);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithVeryVerboseOutput(): void
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list', '-vv' => true]);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithDebugOutput(): void
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list', '-vvv' => true]);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }

    public function testRunCommandWithQuietOutput(): void
    {
        $this->app->setLoggingEnabled(true);
        $this->app->setAutoExit(false);
        $this->app->setCatchExceptions(false);

        $input  = new ArrayInput(['command' => 'list', '-q' => true]);
        $output = new BufferedOutput();

        $exitCode = $this->app->run($input, $output);
        $this->assertEquals(0, $exitCode);
    }
}
