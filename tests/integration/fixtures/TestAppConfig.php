<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

class TestAppConfig implements ConfigurationInterface
{
    public function getConfigTreeBuilder(): TreeBuilder
    {
        $treeBuilder = new TreeBuilder('app');
        $root        = $treeBuilder->getRootNode();
        {
            $dir = $root->children()->arrayNode('dir');
            {
                $dir->children()->scalarNode('log');
                $dir->children()->scalarNode('data');
            }

            $root->children()->scalarNode('name');
            $root->children()->integerNode('count');
            $root->children()->booleanNode('once');
        }

        return $treeBuilder;
    }
}
