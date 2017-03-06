<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-02
 * Time: 14:41
 */

namespace Oasis\SlimApp\tests;

use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

class TestAppConfig implements ConfigurationInterface
{

    /**
     * Generates the configuration tree builder.
     *
     * @return \Symfony\Component\Config\Definition\Builder\TreeBuilder The tree builder
     */
    public function getConfigTreeBuilder()
    {
        $treeBuilder = new TreeBuilder();
        $root        = $treeBuilder->root('app');
        {
            $dir = $root->children()->arrayNode('dir');
            {
                $dir->children()->scalarNode('log');
                $dir->children()->scalarNode('data');
            }
            
            $root->children()->scalarNode('name');
            $root->children()->integerNode('count');
        }

        return $treeBuilder;
    }
}
