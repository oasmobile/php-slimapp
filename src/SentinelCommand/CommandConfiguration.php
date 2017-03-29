<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-02
 * Time: 14:37
 */

namespace Oasis\SlimApp\SentinelCommand;

use Oasis\SlimApp\ConsoleApplication;
use Symfony\Component\Config\Definition\Builder\ArrayNodeDefinition;
use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Console\Application;

class CommandConfiguration implements ConfigurationInterface
{
    /**
     * @var Application
     */
    private $application;
    
    public function __construct(Application $application)
    {
        $this->application = $application;
    }
    
    /**
     * Generates the configuration tree builder.
     *
     * @return \Symfony\Component\Config\Definition\Builder\TreeBuilder The tree builder
     */
    public function getConfigTreeBuilder()
    {
        $builder = new TreeBuilder();
        
        $root = $builder->root('daemon-monitor');
        {
            $commands = $root->children()->arrayNode('commands');
            {
                /** @var ArrayNodeDefinition $command */
                $command = $commands->prototype('array');
                {
                    $normalizer = function ($value) {
                        return $this->replaceParameterInValue($value);
                    };
                    
                    $command->children()->scalarNode('name')->isRequired();
                    $command->children()->variableNode('args')->defaultValue([])->beforeNormalization()->always(
                        function ($array) {
                            if (!is_array($array)) {
                                throw new InvalidConfigurationException("args is not an array!");
                            }
                            foreach ($array as &$value) {
                                $value = $this->replaceParameterInValue($value);
                            }
                            
                            return $array;
                        }
                    );
                    $command->children()->scalarNode('parallel')->defaultValue(1)->beforeNormalization()->always(
                        $normalizer
                    );
                    $command->children()->booleanNode('once')->defaultValue(false)->beforeNormalization()->always(
                        $normalizer
                    );
                    $command->children()->booleanNode('alert')->defaultValue(true)->beforeNormalization()->always(
                        $normalizer
                    );
                    $command->children()->integerNode('interval')->defaultValue(0)->beforeNormalization()->always(
                        $normalizer
                    );
                    $command->children()->integerNode('frequency')->defaultValue(0)->beforeNormalization()->always(
                        $normalizer
                    );
                }
            }
        }
        
        return $builder;
    }
    
    protected function replaceParameterInValue($value)
    {
        if ($this->application instanceof ConsoleApplication
            && is_string($value)
            && preg_match('#(%([^%].*?)%)#', $value, $matches, 0)
        ) {
            $key         = $matches[2];
            $replacement = $this->application->getSlimapp()->getParameter($key);
            if ($replacement === null) {
                throw new \InvalidArgumentException("Cannot get config value $key");
            }
            $value = $replacement;
        }
        
        return $value;
    }
}
