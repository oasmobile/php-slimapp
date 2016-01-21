#! /usr/local/bin/php
<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 14:40
 */
namespace Oasis\SlimApp;

use Oasis\SlimApp\SlimApp;
use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

require_once __DIR__ . "/vendor/autoload.php";

class TestConfig implements ConfigurationInterface
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
            $root->children()->scalarNode('logpath');
            $root->children()->scalarNode('datapath');
        }

        return $treeBuilder;
    }
}
class Dummy {
    public $name;
}

//register_shutdown_function(
//    function () {
//        //SlimApp::app()->monitorMemoryUsage();
//        malert('jj');
//        $error = error_get_last();
//        if (null !== $error) {
//            echo 'Caught at shutdown';
//        }
//    }
//);


SlimApp::app()->init(__DIR__ . "/ut", new TestConfig());

SlimApp::app()->getConsoleApplication()->run();
