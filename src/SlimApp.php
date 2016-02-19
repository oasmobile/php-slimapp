<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 14:42
 */

namespace Oasis\SlimApp;

use Monolog\Handler\HandlerInterface;
use Monolog\Logger;
use Oasis\Mlib\Logging\LocalErrorHandler;
use Oasis\Mlib\Logging\LocalFileHandler;
use Oasis\Mlib\Logging\MLogging;
use Oasis\Mlib\Utils\AbstractDataProvider;
use Oasis\Mlib\Utils\ArrayDataProvider;
use Symfony\Component\Config\ConfigCache;
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\Config\Resource\FileResource;
use Symfony\Component\DependencyInjection\Container;
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
    /** @var  Container */
    protected $container;
    protected $loggingPath  = null;
    protected $loggingLevel = Logger::DEBUG;
    /** @var  ConsoleApplication */
    protected $consoleApp;
    /** @var  array */
    protected $consoleConfig;

    protected $config_file   = "config.yml";
    protected $services_file = "services.yml";

    /**
     * @return static
     */
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
        $configResources = [];
        $yamlFiles       = $locator->locate($this->config_file, null, false);
        $rawData         = [];
        foreach ($yamlFiles as $file) {
            $configResources[] = new FileResource(realpath($file));
            $config            = Yaml::parse(file_get_contents($file));
            $rawData[]         = $config;
        }
        $processor                = new Processor();
        $this->configs            = $processor->processConfiguration($configurationInterface, $rawData);
        $this->configDataProvider = new ArrayDataProvider($this->configs);

        // read container info
        $cacheFilePath        = $configPath . "/cache/container.php";
        $isDebug              = $this->configDataProvider->getOptional('is_debug', ArrayDataProvider::BOOL_TYPE, true);
        $containerConfigCache = new ConfigCache(
            $cacheFilePath,
            $isDebug
        );

        if (!$containerConfigCache->isFresh()) {
            $builder = new ContainerBuilder();
            $builder->addCompilerPass(new SlimAppCompilerPass());
            foreach ($this->configs as $k => $v) {
                $builder->setParameter("app.$k", $v);
            }

            $loader = new YamlFileLoader(
                $builder,
                $locator
            );
            $loader->load($this->services_file);

            $builder->compile();

            $dumper      = new PhpDumper($builder);
            $resources   = $builder->getResources();
            $resources[] = new FileResource(__FILE__);
            $resources   = array_merge($resources, $configResources);
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

        // NOTE: loggers below will be overriden if running in console mode
        $logger = new LocalFileHandler($this->loggingPath, "%date%/%script%.log", $this->loggingLevel);
        $logger->install();
        $logger = new LocalErrorHandler($this->loggingPath, "%date%/%script%.error", $this->loggingLevel);
        $logger->install();

        //mdebug("SlimApp [%s] initialized", static::class);
    }

    public function getServiceIds()
    {
        return $this->container->getServiceIds();
    }

    public function getService($id, $type = null)
    {
        $service = $this->container->get($id);
        if ($type && (!$service instanceof $type)) {
            throw new InvalidArgumentException(sprintf("Service %s is not of type %s", $id, $type));
        }

        return $service;
    }

    public function getParameter($k)
    {
        return $this->container->getParameter($k);
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

    /**
     * @return ConsoleApplication
     */
    public function getConsoleApplication()
    {
        if (!$this->consoleApp) {
            $this->consoleApp = new ConsoleApplication($this->consoleConfig['name'], $this->consoleConfig['version']);
            $this->consoleApp->setLoggingPath($this->loggingPath);
            $this->consoleApp->setLoggingLevel($this->loggingLevel);
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

        if (is_array($value['handlers'])) {
            foreach ($value['handlers'] as $handler) {
                if (!$handler instanceof HandlerInterface) {
                    throw new InvalidConfigurationException("logging property should be an array of log handlers!");
                }
                MLogging::addHandler($handler);
            }
        }
        if (isset($value['path'])) {
            $this->loggingPath = $value['path'];
        }
        if (isset($value['level'])) {
            $this->loggingLevel = $value['level'];
        }
    }

    protected function setCliProperty($value)
    {
        $this->consoleApp    = null;
        $this->consoleConfig = $value;
    }
}
