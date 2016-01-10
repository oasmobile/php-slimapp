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
SlimApp::app()->init(__DIR__ . "/ut", new TestConfig());

/** @var \Memcached $memcached */
$memcached = SlimApp::app()->getService('memcached', \Memcached::class);
$memcached->set('abc', 88);
var_dump($memcached->get('abc'));

$configValue = SlimApp::app()->getMandatoryConfig('datapath');
var_dump($configValue);

$dummy = SlimApp::app()->getService('dummy');
var_dump($dummy);


var_dump(strtr(ucwords("a.nice.t-shirt", "._-"), ["." => "", "_" => "", "-" => ""]));

SlimApp::app()->getConsoleApplication()->run();
