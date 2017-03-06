<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-02
 * Time: 14:37
 */

namespace Oasis\SlimApp\SentinelCommand;

use Symfony\Component\Config\Definition\Builder\ArrayNodeDefinition;
use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

class CommandConfiguration implements ConfigurationInterface
{
    
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
                    $command->children()->scalarNode('name')->isRequired();
                    $command->children()->variableNode('args')->defaultValue([]);
                    $command->children()->scalarNode('parallel')->defaultValue(1);
                    $command->children()->booleanNode('once')->defaultValue(false);
                    $command->children()->booleanNode('alert')->defaultValue(true);
                    $command->children()->integerNode('interval')->defaultValue(0);
                    $command->children()->integerNode('frequency')->defaultValue(0);
                }
            }
        }

        return $builder;
    }
}
