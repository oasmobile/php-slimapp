<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\Mlib\Http\MicroKernel;
use Oasis\Mlib\Utils\DataType;
use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;
use PHPUnit\Framework\TestCase;

class SlimAppTest extends TestCase
{
    private string $configDir;

    protected function setUp(): void
    {
        $this->configDir = __DIR__ . '/../integration/config';
    }

    private function clearUtCache(): void
    {
        $cacheDir = $this->configDir . '/cache';
        if (is_dir($cacheDir)) {
            $files = glob($cacheDir . '/*');
            foreach ($files as $file) {
                if (is_file($file)) {
                    unlink($file);
                }
            }
        }
    }

    public function testAppReturnsSingleton(): void
    {
        $app1 = SlimApp::app();
        $app2 = SlimApp::app();
        $this->assertSame($app1, $app2);
    }

    public function testAppReturnsSlimAppInstance(): void
    {
        $this->assertInstanceOf(SlimApp::class, SlimApp::app());
    }

    public function testInitWithInvalidPathThrowsException(): void
    {
        $app = new SlimApp();
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Config path must be a directory');
        $app->init('/non/existent/path/that/does/not/exist', new TestAppConfig());
    }

    public function testInitLoadsConfiguration(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->assertEquals($this->configDir, $app->getConfigPath());
        $this->assertNotEmpty($app->getConfigCachePath());
    }

    public function testGetMandatoryConfig(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getMandatoryConfig('name'));
    }

    public function testGetOptionalConfigWithDefault(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals(
            'default_val',
            $app->getOptionalConfig('nonexistent', DataType::String, 'default_val')
        );
    }

    public function testGetOptionalConfigExistingKey(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getOptionalConfig('name'));
    }

    public function testGetConfigCachePath(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $cachePath = $app->getConfigCachePath();
        $this->assertStringEndsWith('/cache', $cachePath);
    }

    public function testGetConfigCachePathDefault(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $ref = new \ReflectionProperty($app, 'configCachePath');
        $this->assertNotEmpty($ref->getValue($app));
    }

    public function testGetParameter(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getParameter('app.name'));
    }

    public function testGetServiceIds(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $ids = $app->getServiceIds();
        $this->assertIsArray($ids);
        $this->assertContains('app', $ids);
    }

    public function testSetAndGetService(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj       = new \stdClass();
        $obj->test = 'value';
        $app->setService('test.custom', $obj);
        $this->assertSame($obj, $app->getService('test.custom'));
    }

    public function testGetServiceWithTypeCheck(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj = new \stdClass();
        $app->setService('test.typed', $obj);
        $this->assertSame($obj, $app->getService('test.typed', \stdClass::class));
    }

    public function testGetServiceWithWrongTypeThrowsException(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $app->setService('test.wrongtype', new \stdClass());
        $this->expectException(\Symfony\Component\DependencyInjection\Exception\InvalidArgumentException::class);
        $app->getService('test.wrongtype', SlimApp::class);
    }

    public function testResetService(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj = new \stdClass();
        $app->setService('test.reset', $obj);
        $this->assertSame($obj, $app->getService('test.reset'));

        $app->resetService('test.reset');
        $this->expectException(\Symfony\Component\DependencyInjection\Exception\ServiceNotFoundException::class);
        $app->getService('test.reset');
    }

    public function testMagicSetCliProperty(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'TestCLI', 'version' => '2.0'];

        $console = $app->getConsoleApplication();
        $this->assertEquals('TestCLI', $console->getName());
        $this->assertEquals('2.0', $console->getVersion());
    }

    public function testMagicSetLoggingPropertyWithPath(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['path' => '/tmp/test-logs', 'level' => 300];

        $ref = new \ReflectionProperty($app, 'loggingPath');
        $this->assertEquals('/tmp/test-logs', $ref->getValue($app));

        $levelRef = new \ReflectionProperty($app, 'loggingLevel');
        $this->assertEquals(\Monolog\Level::Warning, $levelRef->getValue($app));
    }

    public function testMagicSetLoggingPropertyWithLevelInstance(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['level' => \Monolog\Level::Error];

        $levelRef = new \ReflectionProperty($app, 'loggingLevel');
        $this->assertEquals(\Monolog\Level::Error, $levelRef->getValue($app));
    }

    public function testMagicSetLoggingPropertyWithLevelString(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['level' => 'warning'];

        $levelRef = new \ReflectionProperty($app, 'loggingLevel');
        $this->assertEquals(\Monolog\Level::Warning, $levelRef->getValue($app));
    }

    public function testMagicSetLoggingPropertyWithPattern(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['pattern' => 'custom/%type%'];

        $ref = new \ReflectionProperty($app, 'loggingPattern');
        $this->assertEquals('custom/%type%', $ref->getValue($app));
    }

    public function testMagicSetLoggingPropertyNonArrayThrowsException(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->expectException(
            \Symfony\Component\Config\Definition\Exception\InvalidConfigurationException::class
        );
        $this->expectExceptionMessage('logging property should be an array');
        $app->logging = 'not-an-array';
    }

    public function testMagicSetLoggingPropertyWithInvalidHandlerThrowsException(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->expectException(
            \Symfony\Component\Config\Definition\Exception\InvalidConfigurationException::class
        );
        $this->expectExceptionMessage('logging property should be an array of log handlers');
        $app->logging = ['handlers' => ['not-a-handler']];
    }

    public function testMagicSetHttpProperty(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $httpConfig = ['routing' => ['path' => '/test']];
        $app->http  = $httpConfig;

        $ref = new \ReflectionProperty($app, 'httpConfig');
        $this->assertEquals($httpConfig, $ref->getValue($app));
    }

    public function testMagicSetUnknownPropertyDoesNothing(): void
    {
        $app = new SlimApp();
        $app->unknownProperty = 'value';
        $this->assertTrue(true);
    }

    public function testGetConsoleApplicationCreatesOnce(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'Test', 'version' => '1.0'];

        $this->assertSame($app->getConsoleApplication(), $app->getConsoleApplication());
    }

    public function testGetConsoleApplicationHasBuiltInCommands(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'Test', 'version' => '1.0'];

        $console = $app->getConsoleApplication();
        $this->assertTrue($console->has('slimapp:cache:clear'));
        $this->assertTrue($console->has('slimapp:services:validate'));
        $this->assertTrue($console->has('slimapp:project:init'));
    }

    public function testGetConsoleApplicationWithCustomCommands(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $customCmd = new \Symfony\Component\Console\Command\Command('custom:test');
        $app->cli  = ['name' => 'Test', 'version' => '1.0', 'commands' => [$customCmd]];

        $this->assertTrue($app->getConsoleApplication()->has('custom:test'));
    }

    public function testGetConsoleApplicationDefaultNameAndVersion(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $console = $app->getConsoleApplication();
        $this->assertEquals('UNKNOWN', $console->getName());
        $this->assertEquals('UNKNOWN', $console->getVersion());
    }

    public function testIsDebug(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertTrue($app->isDebug());
    }

    public function testInitWithCacheReusesConfig(): void
    {
        $app1 = new SlimApp();
        $app1->init($this->configDir, new TestAppConfig());

        $app2 = new SlimApp();
        $app2->init($this->configDir, new TestAppConfig());

        $this->assertEquals($app1->getMandatoryConfig('name'), $app2->getMandatoryConfig('name'));
    }

    public function testInitRebuildsWhenCacheCleared(): void
    {
        $this->clearUtCache();

        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->assertEquals('Jason', $app->getMandatoryConfig('name'));
        $this->assertEquals(2, $app->getMandatoryConfig('count', DataType::Int));
        $this->assertFileExists($this->configDir . '/cache/config.cache');
    }

    public function testMagicSetResetsConsoleApp(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $app->cli = ['name' => 'First', 'version' => '1.0'];
        $console1 = $app->getConsoleApplication();
        $this->assertEquals('First', $console1->getName());

        $app->cli = ['name' => 'Second', 'version' => '2.0'];
        $console2 = $app->getConsoleApplication();
        $this->assertEquals('Second', $console2->getName());
        $this->assertNotSame($console1, $console2);
    }

    public function testMagicSetHttpResetsKernel(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->http = ['routing' => ['path' => '/first']];

        $ref = new \ReflectionProperty($app, 'microKernel');
        $this->assertNull($ref->getValue($app));
    }

    public function testGetMandatoryConfigIntType(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals(2, $app->getMandatoryConfig('count', DataType::Int));
    }

    public function testGetMandatoryConfigBoolType(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertFalse($app->getMandatoryConfig('once', DataType::Bool));
    }

    public function testGetMandatoryConfigArrayType(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $dir = $app->getMandatoryConfig('dir', DataType::Array);
        $this->assertIsArray($dir);
        $this->assertArrayHasKey('log', $dir);
    }

    public function testGetParameterNestedKey(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('/data/logs/slimapp', $app->getParameter('app.dir.log'));
    }

    public function testMagicSetLoggingPropertyWithValidHandler(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $handler      = $this->createStub(\Monolog\Handler\HandlerInterface::class);
        $app->logging = ['handlers' => [$handler]];
        $this->assertTrue(true);
    }

    public function testGetHttpKernel(): void
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->http = [
            'routing' => [
                'path'       => $this->configDir . '/routes.yml',
                'namespaces' => ['Oasis\\SlimApp\\Ut\\'],
            ],
        ];

        $kernel = $app->getHttpKernel();
        $this->assertInstanceOf(MicroKernel::class, $kernel);
        $this->assertSame($kernel, $app->getHttpKernel());
    }

    public function testMagicSetWithDotNotation(): void
    {
        $app = new SlimApp();
        $app->cli = ['name' => 'DotTest', 'version' => '1.0'];
        $this->assertTrue(true);
    }
}
