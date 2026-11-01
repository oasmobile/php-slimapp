<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands\Templates;

use Symfony\Component\Console\Question\Question;
use Symfony\Component\Yaml\Yaml;

trait DatabaseTemplates
{
    protected function prepareDatabaseCliConfigFile(): void
    {
        if ($this->ormSupportEnabled) {
            $filename = $this->rootDir . "/config/cli-config.php";
            $date     = date('Y-m-d');
            $time     = date('H:i');
            $this->output->writeln("cli config file = $filename");
            $cliConfigSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */
 
 
use Doctrine\\ORM\\Tools\\Console\\EntityManagerProvider\\SingleManagerProvider;
use {$this->projectNamespace}Database\\{$this->mainClassname}Database;

require_once __DIR__ . "/../bootstrap.php";

return new SingleManagerProvider({$this->mainClassname}Database::getEntityManager());

SRC;
            $this->writeToTempFile($filename, $cliConfigSource);
        }
        
        if ($this->odmSupportEnabled) {
            $filename = $this->rootDir . "/config/odm-config.php";
            $date     = date('Y-m-d');
            $time     = date('H:i');
            $this->output->writeln("odm config file = $filename");
            $odmConfigSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */
use Oasis\\Mlib\\ODM\\Dynamodb\\Console\\ConsoleHelper;
use {$this->projectNamespace}Database\\{$this->mainClassname}Database;

require_once __DIR__ . '/../bootstrap.php';

\$itemManager = {$this->mainClassname}Database::getItemManager();

return new ConsoleHelper(\$itemManager);


SRC;
            $this->writeToTempFile($filename, $odmConfigSource);
        }
    }
    
    protected function prepareDatabaseManagerFile(): void
    {
        $filename = $this->rootDir . "/" . $this->projectSrcDir . "/Database/" . $this->mainClassname . "Database.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("database manager file = $filename");
        $namespaceDeclaration              = trim($this->projectNamespace, "\\");
        $itemNamespaceDeclarationEscaped   = addcslashes($namespaceDeclaration . "\\Items", "\\");
        $ormImports                        = <<<SRC
use Doctrine\\DBAL\\DriverManager;
use Doctrine\\ORM\\EntityManager;
use Doctrine\\ORM\\ORMSetup;
SRC;
        $odmImports                        = <<<SRC
use Oasis\Mlib\ODM\Dynamodb\ItemManager;
use Oasis\Mlib\Utils\DataType;
SRC;
        $ormFunction                       = <<<SRC
    public static function getEntityManager(): EntityManager
    {
        static \$entityManager = null;
        if (\$entityManager instanceof EntityManager) {
            return \$entityManager;
        }
        
        \$app = {$this->mainClassname}::app();
    
        \$isDevMode = \$app->isDebug();
        \$config    = ORMSetup::createAttributeMetadataConfiguration(
            [PROJECT_DIR . "/src/Entities"],
            \$isDevMode,
            \$app->getParameter('app.dir.data') . "/proxies"
        );

        \$config->enableNativeLazyObjects(true);

        \$conn           = \$app->getParameter('app.db');
        \$conn["driver"] = "pdo_mysql";
        \$entityManager  = new EntityManager(DriverManager::getConnection(\$conn), \$config);

        return \$entityManager;
    }
SRC;
        $odmFunction                       = <<<SRC
    public static function getItemManager(): ItemManager
    {
        static \$im = null;
        
        if (\$im === null) {
            \$app = {$this->mainClassname}::app();
            
            \$cacheDir  = \$app->getMandatoryConfig('dir.cache', DataType::String);
            \$awsConfig = \$app->getMandatoryConfig('aws', DataType::Array);
            \$prefix    = \$app->getMandatoryConfig('dynamodb.prefix', DataType::String);
            
            \$im = new ItemManager(\$awsConfig, \$prefix, \$cacheDir, \$app->isDebug());
            \$dir = PROJECT_DIR . "/src/Items";
            if (\is_dir(\$dir)) {
                \$im->addNamespace("{$itemNamespaceDeclarationEscaped}", \$dir);
            }
        }
        
        return \$im;
    }
SRC;
        if (!$this->ormSupportEnabled) {
            $ormImports = $ormFunction = '';
        }
        if (!$this->odmSupportEnabled) {
            $odmImports = $odmFunction = '';
        }
        
        $dbManagerSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

namespace {$namespaceDeclaration}\\Database;

$ormImports
$odmImports
use {$this->projectNamespace}{$this->mainClassname};


class {$this->mainClassname}Database
{
$ormFunction

$odmFunction
}

SRC;
        $this->writeToTempFile($filename, $dbManagerSource);
    }
}
