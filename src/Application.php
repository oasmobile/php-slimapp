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
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Exception\InvalidArgumentException;
use Symfony\Component\DependencyInjection\Loader\YamlFileLoader;
use Symfony\Component\Yaml\Yaml;

class Application
{
    /** @var array */
    protected $configs;
    /** @var  ArrayDataProvider */
    protected $configDataProvider;
    /** @var  ContainerBuilder */
    protected $container;

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
        $processor = new Processor();
        $locator   = new FileLocator([$configPath]);
        $yamlFiles = $locator->locate($this->config_file, null, false);

        $rawData = [];
        foreach ($yamlFiles as $file) {
            $config    = Yaml::parse(file_get_contents($file));
            $rawData[] = $config;
        }
        $this->configs            = $processor->processConfiguration($configurationInterface, $rawData);
        $this->configDataProvider = new ArrayDataProvider($this->configs);
        $this->configDataProvider->setCascadeDelimiter(".");

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

        $this->container->get('app');

        //mdebug("Application [%s] initialized", static::class);
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

    function __set($name, $value)
    {
        $methodName = sprintf("set%sProperty", ucfirst($name));
        if (method_exists($this, $methodName)) {
            call_user_func([$this, $methodName], $value);
        }
    }

}
