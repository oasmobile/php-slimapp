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
            'cli.command.dummy' => 'getCli_Command_DummyService',
            'dummy' => 'getDummyService',
            'log.handler.sns' => 'getLog_Handler_SnsService',
            'memcached' => 'getMemcachedService',
            'sns.publisher' => 'getSns_PublisherService',
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

        $instance->logging = array('path' => '/data/logs/slimapp', 'level' => 'debug', 'handlers' => array(0 => $this->get('log.handler.sns')));
        $instance->cli = array('name' => 'Slim App Console', 'version' => 1.1000000000000001, 'commands' => array(0 => $this->get('cli.command.dummy')));

        return $instance;
    }

    /**
     * Gets the 'cli.command.dummy' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\SlimApp\tests\DummyCommand A Oasis\SlimApp\tests\DummyCommand instance.
     */
    protected function getCli_Command_DummyService()
    {
        return $this->services['cli.command.dummy'] = new \Oasis\SlimApp\tests\DummyCommand();
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
     * Gets the 'log.handler.sns' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\Mlib\Logging\AwsSnsHandler A Oasis\Mlib\Logging\AwsSnsHandler instance.
     */
    protected function getLog_Handler_SnsService()
    {
        return $this->services['log.handler.sns'] = new \Oasis\Mlib\Logging\AwsSnsHandler($this->get('sns.publisher'), 'message from slimapp');
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
     * Gets the 'sns.publisher' service.
     *
     * This service is shared.
     * This method always returns the same instance of the service.
     *
     * @return \Oasis\Mlib\AwsWrappers\SnsPublisher A Oasis\Mlib\AwsWrappers\SnsPublisher instance.
     */
    protected function getSns_PublisherService()
    {
        return $this->services['sns.publisher'] = new \Oasis\Mlib\AwsWrappers\SnsPublisher(array('profile' => 'minhao', 'region' => 'us-east-1'), 'arn:aws:sns:us-east-1:315771499375:dynamodb');
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
            'sns.config' => array(
                'profile' => 'minhao',
                'region' => 'us-east-1',
            ),
        );
    }
}
