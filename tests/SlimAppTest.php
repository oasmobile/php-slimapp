<?php

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\tests\TestAppConfig;

class SlimAppTest extends \PHPUnit_Framework_TestCase
{
    /** @var string */
    private $configDir;

    protected function setUp()
    {
        $this->configDir = __DIR__ . '/../ut';
    }

    private function clearUtCache()
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

    public function testAppReturnsSingleton()
    {
        $app1 = SlimApp::app();
        $app2 = SlimApp::app();
        $this->assertSame($app1, $app2);
    }

    public function testAppReturnsSlimAppInstance()
    {
        $this->assertInstanceOf(SlimApp::class, SlimApp::app());
    }

    public function testInitWithInvalidPathThrowsException()
    {
        $app = new SlimApp();
        $this->setExpectedException(\InvalidArgumentException::class, 'Config path must be a directory');
        $app->init('/non/existent/path/that/does/not/exist', new TestAppConfig());
    }

    public function testInitLoadsConfiguration()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->assertEquals($this->configDir, $app->getConfigPath());
        $this->assertNotEmpty($app->getConfigCachePath());
    }

    public function testGetMandatoryConfig()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getMandatoryConfig('name'));
    }

    public function testGetOptionalConfigWithDefault()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('default_val', $app->getOptionalConfig('nonexistent', \Oasis\Mlib\Utils\AbstractDataProvider::STRING_TYPE, 'default_val'));
    }

    public function testGetOptionalConfigExistingKey()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getOptionalConfig('name'));
    }

    public function testGetConfigCachePath()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $cachePath = $app->getConfigCachePath();
        $this->assertStringEndsWith('/cache', $cachePath);
    }

    public function testGetConfigCachePathDefault()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $ref = new \ReflectionProperty($app, 'configCachePath');
        $ref->setAccessible(true);
        $this->assertNotEmpty($ref->getValue($app));
    }

    public function testGetParameter()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('Jason', $app->getParameter('app.name'));
    }

    public function testGetServiceIds()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $ids = $app->getServiceIds();
        $this->assertInternalType('array', $ids);
        $this->assertContains('app', $ids);
    }

    public function testSetAndGetService()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj       = new \stdClass();
        $obj->test = 'value';
        $app->setService('test.custom', $obj);
        $this->assertSame($obj, $app->getService('test.custom'));
    }

    public function testGetServiceWithTypeCheck()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj = new \stdClass();
        $app->setService('test.typed', $obj);
        $this->assertSame($obj, $app->getService('test.typed', \stdClass::class));
    }

    public function testGetServiceWithWrongTypeThrowsException()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $app->setService('test.wrongtype', new \stdClass());
        $this->setExpectedException('Symfony\\Component\\DependencyInjection\\Exception\\InvalidArgumentException');
        $app->getService('test.wrongtype', SlimApp::class);
    }

    public function testResetService()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $obj = new \stdClass();
        $app->setService('test.reset', $obj);
        $this->assertSame($obj, $app->getService('test.reset'));

        $app->resetService('test.reset');
        $this->setExpectedException('Symfony\\Component\\DependencyInjection\\Exception\\ServiceNotFoundException');
        $app->getService('test.reset');
    }

    public function testMagicSetCliProperty()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'TestCLI', 'version' => '2.0'];

        $console = $app->getConsoleApplication();
        $this->assertEquals('TestCLI', $console->getName());
        $this->assertEquals('2.0', $console->getVersion());
    }

    public function testMagicSetLoggingPropertyWithPath()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['path' => '/tmp/test-logs', 'level' => 300];

        $ref = new \ReflectionProperty($app, 'loggingPath');
        $ref->setAccessible(true);
        $this->assertEquals('/tmp/test-logs', $ref->getValue($app));

        $levelRef = new \ReflectionProperty($app, 'loggingLevel');
        $levelRef->setAccessible(true);
        $this->assertEquals(300, $levelRef->getValue($app));
    }

    public function testMagicSetLoggingPropertyWithPattern()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->logging = ['pattern' => 'custom/%type%'];

        $ref = new \ReflectionProperty($app, 'loggingPattern');
        $ref->setAccessible(true);
        $this->assertEquals('custom/%type%', $ref->getValue($app));
    }

    public function testMagicSetLoggingPropertyNonArrayThrowsException()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->setExpectedException(
            'Symfony\\Component\\Config\\Definition\\Exception\\InvalidConfigurationException',
            'logging property should be an array'
        );
        $app->logging = 'not-an-array';
    }

    public function testMagicSetLoggingPropertyWithInvalidHandlerThrowsException()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->setExpectedException(
            'Symfony\\Component\\Config\\Definition\\Exception\\InvalidConfigurationException',
            'logging property should be an array of log handlers'
        );
        $app->logging = ['handlers' => ['not-a-handler']];
    }

    public function testMagicSetHttpProperty()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $httpConfig = ['routing' => ['path' => '/test']];
        $app->http  = $httpConfig;

        $ref = new \ReflectionProperty($app, 'httpConfig');
        $ref->setAccessible(true);
        $this->assertEquals($httpConfig, $ref->getValue($app));
    }

    public function testMagicSetUnknownPropertyDoesNothing()
    {
        $app = new SlimApp();
        $app->unknownProperty = 'value';
        $this->assertTrue(true);
    }

    public function testGetConsoleApplicationCreatesOnce()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'Test', 'version' => '1.0'];

        $this->assertSame($app->getConsoleApplication(), $app->getConsoleApplication());
    }

    public function testGetConsoleApplicationHasBuiltInCommands()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->cli = ['name' => 'Test', 'version' => '1.0'];

        $console = $app->getConsoleApplication();
        $this->assertTrue($console->has('slimapp:cache:clear'));
        $this->assertTrue($console->has('slimapp:services:validate'));
        $this->assertTrue($console->has('slimapp:project:init'));
    }

    public function testGetConsoleApplicationWithCustomCommands()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $customCmd = new \Symfony\Component\Console\Command\Command('custom:test');
        $app->cli  = ['name' => 'Test', 'version' => '1.0', 'commands' => [$customCmd]];

        $this->assertTrue($app->getConsoleApplication()->has('custom:test'));
    }

    public function testGetConsoleApplicationDefaultNameAndVersion()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $console = $app->getConsoleApplication();
        $this->assertEquals('UNKNOWN', $console->getName());
        $this->assertEquals('UNKNOWN', $console->getVersion());
    }

    public function testIsDebug()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertTrue($app->isDebug());
    }

    public function testInitWithCacheReusesConfig()
    {
        $app1 = new SlimApp();
        $app1->init($this->configDir, new TestAppConfig());

        $app2 = new SlimApp();
        $app2->init($this->configDir, new TestAppConfig());

        $this->assertEquals($app1->getMandatoryConfig('name'), $app2->getMandatoryConfig('name'));
    }

    public function testInitRebuildsWhenCacheCleared()
    {
        $this->clearUtCache();

        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $this->assertEquals('Jason', $app->getMandatoryConfig('name'));
        $this->assertEquals(2, $app->getMandatoryConfig('count', \Oasis\Mlib\Utils\AbstractDataProvider::INT_TYPE));
        $this->assertFileExists($this->configDir . '/cache/config.cache');
    }

    public function testMagicSetResetsConsoleApp()
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

    public function testMagicSetHttpResetsKernel()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $app->http = ['routing' => ['path' => '/first']];

        $ref = new \ReflectionProperty($app, 'silexKernel');
        $ref->setAccessible(true);
        $this->assertNull($ref->getValue($app));
    }

    public function testGetMandatoryConfigIntType()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals(2, $app->getMandatoryConfig('count', \Oasis\Mlib\Utils\AbstractDataProvider::INT_TYPE));
    }

    public function testGetMandatoryConfigBoolType()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertFalse($app->getMandatoryConfig('once', \Oasis\Mlib\Utils\AbstractDataProvider::BOOL_TYPE));
    }

    public function testGetMandatoryConfigArrayType()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $dir = $app->getMandatoryConfig('dir', \Oasis\Mlib\Utils\AbstractDataProvider::ARRAY_TYPE);
        $this->assertInternalType('array', $dir);
        $this->assertArrayHasKey('log', $dir);
    }

    public function testGetParameterNestedKey()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());
        $this->assertEquals('/data/logs/slimapp', $app->getParameter('app.dir.log'));
    }

    public function testMagicSetLoggingPropertyWithValidHandler()
    {
        $app = new SlimApp();
        $app->init($this->configDir, new TestAppConfig());

        $handler = $this->getMockBuilder(\Monolog\Handler\HandlerInterface::class)->getMock();
        $app->logging = ['handlers' => [$handler]];
        $this->assertTrue(true);
    }

    public function testGetHttpKernel()
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
        $this->assertInstanceOf(\Oasis\Mlib\Http\SilexKernel::class, $kernel);
        $this->assertSame($kernel, $app->getHttpKernel());
    }

    public function testMagicSetWithDotNotation()
    {
        $app = new SlimApp();
        $app->cli = ['name' => 'DotTest', 'version' => '1.0'];
        $this->assertTrue(true);
    }
}
