<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

use Monolog\Handler\HandlerInterface;
use Monolog\Level;
use Oasis\Mlib\Http\MicroKernel;
use Oasis\Mlib\Logging\LocalErrorHandler;
use Oasis\Mlib\Logging\LocalFileHandler;
use Oasis\Mlib\Logging\MLogging;
use Oasis\Mlib\Utils\ArrayDataProvider;
use Oasis\Mlib\Utils\DataType;
use Oasis\SlimApp\BuiltInCommands\ClearCacheCommand;
use Oasis\SlimApp\BuiltInCommands\InitializeProjectCommand;
use Oasis\SlimApp\BuiltInCommands\ValidateServicesCommand;
use Symfony\Component\Config\ConfigCache;
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
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
    protected bool $isDebugMode = false;
    /** @var array<string, mixed> */
    protected array $configs = [];
    protected ?ArrayDataProvider $configDataProvider = null;
    protected ?Container $container = null;
    protected ?string $loggingPath = null;
    protected Level $loggingLevel = Level::Debug;
    protected string $loggingPattern = '%date%/%script%.%type%';
    protected ?ConsoleApplication $consoleApp = null;
    /** @var array<string, mixed> */
    protected array $consoleConfig = [];
    protected ?MicroKernel $microKernel = null;
    /** @var array<string, mixed>|null */
    protected ?array $httpConfig = null;
    protected ?string $configPath = null;
    protected string $configFilename = 'config.yml';
    protected string $serviceFilename = 'services.yml';
    protected string $configCachePath = '';
    /** @var \Symfony\Component\Config\Resource\ResourceInterface[] */
    protected array $configRelatedResources = [];

    public static function app(): static
    {
        static $inst = null;
        if ($inst === null) {
            $inst = new static(); // @phpstan-ignore new.static
        }

        return $inst;
    }

    public function __set(string $name, mixed $value): void
    {
        $methodName = sprintf("set%sProperty", strtr(ucwords($name, "._-"), ["." => "", "_" => "", "-" => ""]));
        if (method_exists($this, $methodName)) {
            $this->$methodName($value);
        }
    }

    public function init(string $configPath, ConfigurationInterface $configurationInterface, ?string $configCachePath = null): void
    {
        if (!is_dir($configPath)) {
            throw new \InvalidArgumentException(
                "Config path must be a directory containing config file. Path given = " . $configPath
            );
        }
        $this->configPath      = $configPath;
        $this->configCachePath = $configCachePath ?: $this->configPath . "/cache";
        $locator               = new FileLocator([$this->configPath]);

        $configCacheFile              = \sprintf($this->configCachePath . "/config.cache");
        $configYamlCache              = new ConfigCache(
            $configCacheFile,
            true
        );
        $this->configRelatedResources = [];
        if ($upToDate = $configYamlCache->isFresh()) {
            $content       = \file_get_contents($configCacheFile);
            if ($content !== false) {
                $this->configs = @\unserialize($content);
            }
        }

        if (!$this->configs || !$upToDate) {
            // read config.yml first
            $yamlFiles = $locator->locate($this->configFilename, null, false);
            $rawData   = [];
            foreach ($yamlFiles as $file) {
                $realFile = realpath($file);
                if ($realFile === false) {
                    throw new \InvalidArgumentException("Cannot resolve real path for config file: $file");
                }
                $this->configRelatedResources[] = new FileResource($realFile);
                $fileContent                    = file_get_contents($file);
                if ($fileContent === false) {
                    throw new \InvalidArgumentException("Cannot read config file: $file");
                }
                $config                         = Yaml::parse($fileContent);
                $rawData[]                      = $config;
            }
            $this->configs = ConfigParser::parse($rawData, $configurationInterface);
            if (!isset($this->configs['dir.config'])) {
                $this->configs['dir.config'] = $this->configPath;
            }
            $configYamlCache->write(
                \serialize($this->configs),
                $this->configRelatedResources
            );
            $parameterizedResult = ConfigParser::flatten($this->configs);
            \file_put_contents(
                $this->configCachePath . '/parameterized_helper.yml',
                Yaml::dump(['parameters' => $parameterizedResult])
            );
        }

        $this->configDataProvider = new ArrayDataProvider($this->configs);
        $this->isDebugMode        = $this->configDataProvider->getOptional(
            'is_debug',
            DataType::Bool,
            true
        );

        // read container info
        $cacheFilePath        = $this->configCachePath . "/container.php";
        $containerConfigCache = new ConfigCache(
            $cacheFilePath,
            $this->isDebugMode
        );

        // refresh container if dirty
        if (!$containerConfigCache->isFresh()) {
            $builder = new ContainerBuilder();
            $builder->addCompilerPass(new SlimAppCompilerPass(static::class));
            $flatParams = ConfigParser::flatten($this->configs);
            foreach ($flatParams as $key => $value) {
                $builder->setParameter($key, $value);
            }

            $loader = new YamlFileLoader(
                $builder,
                $locator
            );
            $loader->load($this->serviceFilename);

            $builder->compile();

            $dumper                       = new PhpDumper($builder);
            $resources                    = $builder->getResources();
            $resources[]                  = new FileResource(__FILE__);
            $this->configRelatedResources = array_merge($resources, $this->configRelatedResources);
            $dumped = $dumper->dump(['class' => 'SlimAppCachedContainer', 'namespace' => __NAMESPACE__]);
            assert(is_string($dumped));
            $containerConfigCache->write(
                $dumped,
                $this->configRelatedResources
            );
        }

        // create container instance
        /** @noinspection PhpIncludeInspection */
        require_once $cacheFilePath;
        /**
         * @phpstan-ignore class.notFound, assign.propertyType
         */
        $this->container = new SlimAppCachedContainer();
        /** @phpstan-ignore class.notFound */
        $this->container->get('app');

        // NOTE: loggers below will be overriden if running in console mode
        $logger = new LocalFileHandler(
            $this->loggingPath,
            \strtr($this->loggingPattern, ['%type%' => 'log']),
            $this->loggingLevel
        );
        $logger->install();
        $logger = new LocalErrorHandler(
            $this->loggingPath,
            \strtr($this->loggingPattern, ['%type%' => 'error']),
            $this->loggingLevel
        );
        $logger->install();
    }

    public function isDebug(): bool
    {
        return $this->isDebugMode;
    }

    public function resetService(string $id): void
    {
        assert($this->container !== null, 'SlimApp not initialized');
        $this->container->set($id, null);
    }

    public function getConfigCachePath(): string
    {
        return $this->configCachePath;
    }

    public function getConfigPath(): ?string
    {
        return $this->configPath;
    }

    public function getConsoleApplication(): ConsoleApplication
    {
        if (!$this->consoleApp) {
            $name             = $this->consoleConfig['name'] ?? 'UNKNOWN';
            $version          = $this->consoleConfig['version'] ?? 'UNKNOWN';
            $consoleApp       = new ConsoleApplication($name, $version);
            $consoleApp->setSlimapp($this);
            $consoleApp->setLoggingPath($this->loggingPath);
            $consoleApp->setLoggingLevel($this->loggingLevel);
            $consoleApp->setLogFilePattern($this->loggingPattern);

            // Add built-in commands
            $consoleApp->addCommands(
                [
                    new ClearCacheCommand(),
                    new ValidateServicesCommand(),
                    new InitializeProjectCommand(),
                ]
            );

            // Add custom commands
            if (isset($this->consoleConfig['commands']) && is_array($this->consoleConfig['commands'])) {
                $consoleApp->addCommands($this->consoleConfig['commands']);
            }
            
            $this->consoleApp = $consoleApp;
        }

        return $this->consoleApp;
    }

    public function getHttpKernel(): MicroKernel
    {
        if (!$this->microKernel instanceof MicroKernel) {
            $container = $this->container;
            assert($container !== null, 'SlimApp not initialized');
            $kernel = new MicroKernel($this->httpConfig ?? [], $this->isDebugMode);
            $kernel->addControllerInjectedArg($this);
            $kernel->addExtraParameters($container->getParameterBag()->all());
            $this->microKernel = $kernel;
        }

        return $this->microKernel;
    }

    public function getMandatoryConfig(string $key, DataType $expectedType = DataType::String): mixed
    {
        assert($this->configDataProvider !== null, 'SlimApp not initialized');
        return $this->configDataProvider->getMandatory($key, $expectedType);
    }

    public function getOptionalConfig(string $key, DataType $expectedType = DataType::String, mixed $defaultValue = null): mixed
    {
        assert($this->configDataProvider !== null, 'SlimApp not initialized');
        return $this->configDataProvider->getOptional($key, $expectedType, $defaultValue);
    }

    public function getParameter(string $k): mixed
    {
        assert($this->container !== null, 'SlimApp not initialized');
        return $this->container->getParameter($k);
    }

    public function getService(string $id, ?string $type = null): mixed
    {
        assert($this->container !== null, 'SlimApp not initialized');
        $service = $this->container->get($id);
        if ($type && (!$service instanceof $type)) {
            throw new InvalidArgumentException(sprintf("Service %s is not of type %s", $id, $type));
        }

        return $service;
    }

    /**
     * @return string[]
     */
    public function getServiceIds(): array
    {
        assert($this->container !== null, 'SlimApp not initialized');
        return $this->container->getServiceIds();
    }

    public function setService(string $id, ?object $service): void
    {
        assert($this->container !== null, 'SlimApp not initialized');
        $this->container->set($id, $service);
    }

    protected function setCliProperty(mixed $value): void
    {
        $this->consoleApp    = null;
        $this->consoleConfig = $value;
    }

    protected function setHttpProperty(mixed $value): void
    {
        $this->microKernel = null;
        $this->httpConfig  = $value;
    }

    protected function setLoggingProperty(mixed $value): void
    {
        if (!is_array($value)) {
            throw new InvalidConfigurationException("logging property should be an array of log handlers!");
        }

        if (isset($value['handlers']) && is_array($value['handlers'])) {
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
            $level = $value['level'];
            if ($level instanceof Level) {
                $this->loggingLevel = $level;
            } elseif (is_int($level)) {
                $this->loggingLevel = Level::from($level);
            } elseif (is_string($level)) {
                $this->loggingLevel = Level::fromName(ucfirst(strtolower($level))); // @phpstan-ignore argument.type
            }
        }
        if (isset($value['pattern'])) {
            $this->loggingPattern = $value['pattern'];
        }
    }
}
