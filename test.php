#! /usr/local/bin/php
<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 14:40
 */
namespace Oasis\SlimApp;

use Oasis\Mlib\Logging\ConsoleHandler;
use Oasis\Mlib\Logging\LocalErrorHandler;
use Oasis\Mlib\Logging\LocalFileHandler;
use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Console\Output\ConsoleOutput;

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

SlimApp::app()->init(__DIR__ . "/ut", new TestConfig());

SlimApp::app()->getConsoleApplication()->run();
//
//(new LocalFileHandler('/tmp/slimapp'))->install();
//(new LocalErrorHandler('/tmp/slimapp'))->install();
//$x = (new ConsoleHandler());
//$x->install();
//$x->setLevel('warning');
//
//$lastMemory = memory_get_usage(true);
//$output     = new ConsoleOutput();
//while (true) {
//    $memory = memory_get_usage(true);
//    if ($memory != $lastMemory) {
//        $output->writeln(
//            sprintf("memory change: %d, from %d to %d", $memory - $lastMemory, $lastMemory, $memory)
//        );
//    }
//    $lastMemory = $memory;
//    mdebug(1);
//}
