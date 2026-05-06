<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\BuiltInCommands;

use Oasis\Mlib\Http\MicroKernel;
use Oasis\SlimApp\BuiltInCommands\ClearCacheCommand;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Filesystem\Filesystem;

class ClearCacheCommandTest extends TestCase
{
    public function testCommandNameAndDescription(): void
    {
        $command = new ClearCacheCommand();
        $this->assertEquals('slimapp:cache:clear', $command->getName());
        $this->assertNotEmpty($command->getDescription());
    }

    public function testExecuteClearsCacheDirectory(): void
    {
        $cacheDir = sys_get_temp_dir() . '/slimapp_clear_cache_test_' . uniqid();
        $fs       = new Filesystem();
        $fs->mkdir($cacheDir);
        $fs->touch($cacheDir . '/test_cache_file.php');
        $fs->touch($cacheDir . '/test_cache_file2.php');

        $this->assertFileExists($cacheDir . '/test_cache_file.php');

        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getConfigCachePath')->willReturn($cacheDir);

        $httpKernel = $this->createStub(MicroKernel::class);
        $httpKernel->method('getCacheDirectories')->willReturn([]);
        $slimapp->method('getHttpKernel')->willReturn($httpKernel);

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->addCommand(new ClearCacheCommand());

        $input  = new ArrayInput(['command' => 'slimapp:cache:clear']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertStringContainsString('removing cache', $text);
        $this->assertStringContainsString('done', $text);
        $this->assertFileDoesNotExist($cacheDir . '/test_cache_file.php');

        $fs->remove($cacheDir);
    }

    public function testExecuteWithHttpCacheDirectories(): void
    {
        $configCacheDir = sys_get_temp_dir() . '/slimapp_config_cache_' . uniqid();
        $httpCacheDir   = sys_get_temp_dir() . '/slimapp_http_cache_' . uniqid();
        $fs             = new Filesystem();
        $fs->mkdir($configCacheDir);
        $fs->mkdir($httpCacheDir);
        $fs->touch($httpCacheDir . '/http_cache_file.php');

        $slimapp = $this->createStub(SlimApp::class);
        $slimapp->method('getConfigCachePath')->willReturn($configCacheDir);

        $httpKernel = $this->createStub(MicroKernel::class);
        $httpKernel->method('getCacheDirectories')->willReturn([$httpCacheDir]);
        $slimapp->method('getHttpKernel')->willReturn($httpKernel);

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->addCommand(new ClearCacheCommand());

        $input  = new ArrayInput(['command' => 'slimapp:cache:clear']);
        $output = new BufferedOutput(OutputInterface::VERBOSITY_VERBOSE);

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertStringContainsString('removing file', $text);
        $this->assertFileDoesNotExist($httpCacheDir . '/http_cache_file.php');

        $fs->remove($configCacheDir);
        $fs->remove($httpCacheDir);
    }
}
