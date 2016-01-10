<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 14:42
 */

namespace Oasis\SlimApp;

use Monolog\Handler\HandlerInterface;
use Oasis\Mlib\Logging\MLogging;
use Oasis\Mlib\Utils\AbstractDataProvider;
use Oasis\Mlib\Utils\ArrayDataProvider;
use Symfony\Component\Config\ConfigCache;
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\Config\Resource\FileResource;
use Symfony\Component\Console\Application;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Dumper\PhpDumper;
use Symfony\Component\DependencyInjection\Exception\InvalidArgumentException;
use Symfony\Component\DependencyInjection\Loader\YamlFileLoader;
use Symfony\Component\Yaml\Yaml;

class SlimApp
{
    /** @var array */
    protected $configs;
    /** @var  ArrayDataProvider */
    protected $configDataProvider;
    /** @var  ContainerBuilder */
    protected $container;
    /** @var  Application */
    protected $consoleApp;
    /** @var  array */
    protected $consoleConfig;

    protected $config_file   = "config.yml";
    protected $services_file = "services.yml";

    public static function app()
    {
        static $inst = null;
        if ($inst == null) {
            $inst = new static;
        }

        return $inst;
    }

    public function init($configPath, ConfigurationInterface $configurationInterface)
    {
        $locator = new FileLocator([$configPath]);

        // read config.yml first
        $yamlFiles = $locator->locate($this->config_file, null, false);
        $rawData   = [];
        foreach ($yamlFiles as $file) {
            $config    = Yaml::parse(file_get_contents($file));
            $rawData[] = $config;
        }
        $processor                = new Processor();
        $this->configs            = $processor->processConfiguration($configurationInterface, $rawData);
        $this->configDataProvider = new ArrayDataProvider($this->configs);
        $this->configDataProvider->setCascadeDelimiter(".");

        // read container info
        $cacheFilePath        = $configPath . "/cache/container.php";
        $isDebug              = $this->configDataProvider->getOptional('is_debug', ArrayDataProvider::BOOL_TYPE, true);
        $containerConfigCache = new ConfigCache(
            $cacheFilePath,
            $isDebug
        );

        if (!$containerConfigCache->isFresh()) {
            $this->container = new ContainerBuilder();
            $this->container->addCompilerPass(new SlimAppCompilerPass());
            foreach ($this->configs as $k => $v) {
                $this->container->setParameter("app.$k", $v);
            }

            $loader = new YamlFileLoader(
                $this->container,
                $locator
            );
            $loader->load($this->services_file);

            $this->container->compile();

            $dumper      = new PhpDumper($this->container);
            $resources   = $this->container->getResources();
            $resources[] = new FileResource(__FILE__);
            $containerConfigCache->write(
                $dumper->dump(['class' => 'SlimAppCachedContainer', 'namespace' => __NAMESPACE__]),
                $resources
            );
            //mdebug("container dumped");

        }
        /** @noinspection PhpIncludeInspection */
        require_once $cacheFilePath;
        /** @noinspection PhpUndefinedClassInspection */
        $this->container = new SlimAppCachedContainer;

        $this->container->get('app');

        //mdebug("SlimApp [%s] initialized", static::class);
    }

    public function getService($id, $type = null)
    {
        $service = $this->container->get($id);
        if ($type && (!$service instanceof $type)) {
            throw new InvalidArgumentException(sprintf("Service %s is not of type %s", $id, $type));
        }

        return $service;
    }

    public function getMandatoryConfig($key, $expectedType = AbstractDataProvider::STRING_TYPE)
    {
        // normalize key
        $key = strtr($key, ['-' => "_"]);

        return $this->configDataProvider->getMandatory($key, $expectedType);
    }

    public function getOptionalConfig($key, $expectedType = AbstractDataProvider::STRING_TYPE, $defaultValue = null)
    {
        // normalize key
        $key = strtr($key, ['-' => "_"]);

        return $this->configDataProvider->getOptional($key, $expectedType, $defaultValue);
    }

    public function getConsoleApplication()
    {
        if (!$this->consoleApp) {
            $this->consoleApp = new ConsoleApplication($this->consoleConfig['name'], $this->consoleConfig['version']);
            if (is_array($this->consoleConfig['commands'])) {
                $this->consoleApp->addCommands($this->consoleConfig['commands']);
            }
        }

        return $this->consoleApp;
    }

    function __set($name, $value)
    {
        $methodName = sprintf("set%sProperty", strtr(ucwords($name, "._-"), ["." => "", "_" => "", "-" => ""]));
        if (method_exists($this, $methodName)) {
            call_user_func([$this, $methodName], $value);
        }
    }

    protected function setLoggingProperty($value)
    {
        if (!is_array($value)) {
            throw new InvalidConfigurationException("logging property should be an array of log handlers!");
        }

        foreach ($value as $handler) {
            if (!$handler instanceof HandlerInterface) {
                throw new InvalidConfigurationException("logging property should be an array of log handlers!");
            }
            MLogging::addHandler($handler, get_class($handler));
        }
    }

    protected function setCliProperty($value)
    {
        $this->consoleApp    = null;
        $this->consoleConfig = $value;
    }

}
