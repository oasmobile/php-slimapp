<?php

namespace Oasis\SlimApp\Tests\BuiltInCommands;

use Oasis\SlimApp\BuiltInCommands\ClearCacheCommand;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SlimApp;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Filesystem\Filesystem;

class ClearCacheCommandTest extends \PHPUnit_Framework_TestCase
{
    public function testCommandNameAndDescription()
    {
        $command = new ClearCacheCommand();
        $this->assertEquals('slimapp:cache:clear', $command->getName());
        $this->assertNotEmpty($command->getDescription());
    }

    public function testExecuteClearsCacheDirectory()
    {
        $cacheDir = sys_get_temp_dir() . '/slimapp_clear_cache_test_' . uniqid();
        $fs       = new Filesystem();
        $fs->mkdir($cacheDir);
        $fs->touch($cacheDir . '/test_cache_file.php');
        $fs->touch($cacheDir . '/test_cache_file2.php');

        $this->assertFileExists($cacheDir . '/test_cache_file.php');

        $slimapp = $this->getMockBuilder(SlimApp::class)
                        ->disableOriginalConstructor()
                        ->getMock();
        $slimapp->method('getConfigCachePath')->willReturn($cacheDir);

        $httpKernel = $this->getMockBuilder(\Oasis\Mlib\Http\SilexKernel::class)
                           ->disableOriginalConstructor()
                           ->getMock();
        $httpKernel->method('getCacheDirectories')->willReturn([]);
        $slimapp->method('getHttpKernel')->willReturn($httpKernel);

        $console = new ConsoleApplication('Test', '1.0');
        $console->setSlimapp($slimapp);
        $console->setAutoExit(false);
        $console->setCatchExceptions(false);
        $console->setLoggingEnabled(false);
        $console->add(new ClearCacheCommand());

        $input  = new ArrayInput(['command' => 'slimapp:cache:clear']);
        $output = new BufferedOutput();

        $console->run($input, $output);

        $text = $output->fetch();
        $this->assertContains('removing cache', $text);
        $this->assertContains('done', $text);
        $this->assertFileNotExists($cacheDir . '/test_cache_file.php');

        $fs->remove($cacheDir);
    }
}
