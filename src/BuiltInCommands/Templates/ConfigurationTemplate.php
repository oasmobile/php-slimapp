<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands\Templates;

use Symfony\Component\Console\Question\Question;
use Symfony\Component\Yaml\Yaml;

trait ConfigurationTemplate
{
    protected function prepareConfigClassFile(): void
    {
        $classname     = $this->mainClassname . "Configuration";
        $classFilename = $this->rootDir . "/" . $this->projectSrcDir . "/" . $classname . ".php";
        $this->output->writeln("config class file = $classFilename");
        $date = date('Y-m-d');
        $time = date('H:i');
        
        $namespaceDeclaration = trim($this->projectNamespace, "\\");
        $classSource          = <<<SRC
<?php
namespace $namespaceDeclaration;

use Oasis\\Mlib\\Utils\\StringUtils;
use Symfony\\Component\\Config\\Definition\\Builder\\TreeBuilder;
use Symfony\\Component\\Config\\Definition\\ConfigurationInterface;

/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

class $classname implements ConfigurationInterface
{

    /**
     * Generates the configuration tree builder.
     *
     * @return TreeBuilder The tree builder
     */
    public function getConfigTreeBuilder(): TreeBuilder
    {
        \$treeBuilder = new TreeBuilder('app');
        \$root        = \$treeBuilder->getRootNode();
        {
            \$root->children()->booleanNode('is_debug')->defaultValue(true);
            \$dir = \$root->children()->arrayNode('dir');
            {
                \$makeAbsolute = function (\$path) {
                    return StringUtils::stringStartsWith(\$path, \DIRECTORY_SEPARATOR)
                        ? \$path
                        : \PROJECT_DIR . \DIRECTORY_SEPARATOR . \$path;
                };

                \$dir->children()->scalarNode('log')->beforeNormalization()->always(\$makeAbsolute);
                \$dir->children()->scalarNode('data')->beforeNormalization()->always(\$makeAbsolute);
                \$dir->children()->scalarNode('cache')->beforeNormalization()->always(\$makeAbsolute);
                \$dir->children()->scalarNode('template')->beforeNormalization()->always(\$makeAbsolute);
            }
            
            \$db = \$root->children()->arrayNode('db');
            {
                \$db->children()->scalarNode('host')->isRequired();
                \$db->children()->integerNode('port')->defaultValue(3306);
                \$db->children()->scalarNode('user')->isRequired();
                \$db->children()->scalarNode('password')->isRequired();
                \$db->children()->scalarNode('dbname')->isRequired();
            }

            \$memcached = \$root->children()->arrayNode('memcached');
            {
                \$memcached->children()->scalarNode('host')->isRequired();
                \$memcached->children()->integerNode('port')->isRequired();
                \$memcached->children()->scalarNode('namespace')->isRequired();
            }
            
            \$aws = \$root->children()->arrayNode('aws');
            {
                \$aws->children()->scalarNode('profile')->isRequired();
                \$aws->children()->scalarNode('region')->isRequired();
            }
            
            \$dynamodb = \$root->children()->arrayNode('dynamodb');
            {
                \$dynamodb->children()->scalarNode('prefix')->isRequired();
            }
        }

        return \$treeBuilder;
    }
}


SRC;
        $this->writeToTempFile($classFilename, $classSource);
    }
}
