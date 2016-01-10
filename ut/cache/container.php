<?php
namespace Oasis\SlimApp;

use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\DependencyInjection\Exception\InvalidArgumentException;
use Symfony\Component\DependencyInjection\Exception\LogicException;
use Symfony\Component\DependencyInjection\Exception\RuntimeException;
use Symfony\Component\DependencyInjection\ParameterBag\FrozenParameterBag;

/**
 * SlimAppCachedContainer.
 *
 * This class has been auto-generated
 * by the Symfony Dependency Injection Component.
 */
class SlimAppCachedContainer extends Container
{
    private $parameters;
    private $targetDirs = array();

    /**
     * Constructor.
     */
    public function __construct()
    {
        $this->parameters = $this->getDefaultParameters();

        $this->services = array();
        $this->methodMap = array(
            'app' => 'getAppService',
            'dummy' => 'getDummyService',
            'log.handler.console' => 'getLog_Handler_ConsoleService',
            'log.handler.file' => 'getLog_Handler_FileService',
            'memcached' => 'getMemcachedService',
        );

        $this->aliases = array();
    }

    /**
     * {@inheritdoc}
     */
    public function compile()
    {
        throw new LogicException('You cannot compile a dumped frozen container.');
    }

    /**
     * Gets the 'app' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\SlimApp\SlimApp A Oasis\SlimApp\SlimApp instance.
     */
    protected function getAppService()
    {
        $this->services['app'] = $instance = \Oasis\SlimApp\SlimApp::app();

        $instance->logging = array(0 => $this->get('log.handler.console'), 1 => $this->get('log.handler.file'));
        $instance->cli = array('name' => 'Slim App Console', 'version' => 1.1000000000000001, 'commands' => NULL);

        return $instance;
    }

    /**
     * Gets the 'dummy' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\SlimApp\Dummy A Oasis\SlimApp\Dummy instance.
     */
    protected function getDummyService()
    {
        $this->services['dummy'] = $instance = $this->get('app')->app();

        $instance->name = 'root';

        return $instance;
    }

    /**
     * Gets the 'log.handler.console' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\Mlib\Logging\ConsoleHandler A Oasis\Mlib\Logging\ConsoleHandler instance.
     */
    protected function getLog_Handler_ConsoleService()
    {
        return $this->services['log.handler.console'] = new \Oasis\Mlib\Logging\ConsoleHandler();
    }

    /**
     * Gets the 'log.handler.file' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\Mlib\Logging\LocalFileHandler A Oasis\Mlib\Logging\LocalFileHandler instance.
     */
    protected function getLog_Handler_FileService()
    {
        return $this->services['log.handler.file'] = new \Oasis\Mlib\Logging\LocalFileHandler('/data/logs/slimapp');
    }

    /**
     * Gets the 'memcached' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Memcached A Memcached instance.
     */
    protected function getMemcachedService()
    {
        $this->services['memcached'] = $instance = new \Memcached();

        $instance->addServer('127.0.0.1', 9999);

        return $instance;
    }

    /**
     * {@inheritdoc}
     */
    public function getParameter($name)
    {
        $name = strtolower($name);

        if (!(isset($this->parameters[$name]) || array_key_exists($name, $this->parameters))) {
            throw new InvalidArgumentException(sprintf('The parameter "%s" must be defined.', $name));
        }

        return $this->parameters[$name];
    }

    /**
     * {@inheritdoc}
     */
    public function hasParameter($name)
    {
        $name = strtolower($name);

        return isset($this->parameters[$name]) || array_key_exists($name, $this->parameters);
    }

    /**
     * {@inheritdoc}
     */
    public function setParameter($name, $value)
    {
        throw new LogicException('Impossible to call set() on a frozen ParameterBag.');
    }

    /**
     * {@inheritdoc}
     */
    public function getParameterBag()
    {
        if (null === $this->parameterBag) {
            $this->parameterBag = new FrozenParameterBag($this->parameters);
        }

        return $this->parameterBag;
    }

    /**
     * Gets the default parameters.
     *
     * @return array An array of the default parameters
     */
    protected function getDefaultParameters()
    {
        return array(
            'app.logpath' => '/data/logs/slimapp',
            'app.datapath' => '/data/slimapp',
            'db.username' => 'root',
            'db.password' => 'On4aC3ub8',
            'default.namespace' => array(
                0 => 'Oasis',
                1 => 'Oasis\\SlimApp',
            ),
        );
    }
}
