<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-03-29
 * Time: 11:23
 */

namespace Oasis\SlimApp\BuiltInCommands;

use Oasis\Mlib\Utils\StringUtils;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\Question;
use Symfony\Component\Filesystem\Filesystem;
use Symfony\Component\Finder\Finder;
use Symfony\Component\Finder\SplFileInfo;
use Symfony\Component\Yaml\Yaml;

class InitializeProjectCommand extends Command
{
    /** @var  Filesystem */
    protected $fs;
    
    /** @var  InputInterface */
    protected $input;
    /** @var  OutputInterface */
    protected $output;
    /** @var  string */
    protected $rootDir;
    /** @var  string */
    protected $vendorName;
    /** @var  string */
    protected $projectName;
    /** @var  string */
    protected $mainClassname;
    /** @var  string */
    protected $projectNamespace;
    /** @var  string */
    protected $projectSrcDir;
    /** @var  string */
    protected $cacheDir;
    /** @var bool */
    protected $ormSupportEnabled = false;
    /** @var bool */
    protected $odmSupportEnabled = false;
    /** @var bool */
    protected $phpunitSupportEnabled = false;
    
    protected $tempFiles = [];
    
    protected function applyTempFiles()
    {
        $helper = $this->getHelper('question');
        $this->output->writeln("All configuration accepted. Will start to generate needed files.");
        
        $overwriteAll = false;
        foreach ($this->tempFiles as $tempFile) {
            $this->output->write(
                "Generating file <comment>$tempFile</comment> ... "
            );
            if ($this->fs->exists($tempFile)) {
                $shouldOverwrite = false;
                if (!$overwriteAll && basename($tempFile) != "composer.json") {
                    $question = new Question(
                        "File <comment>$tempFile</comment> exists, overwrite? <info>[yes/no/all]</info>: ",
                        "y"
                    );
                    $this->output->writeln('');
                    $overwrite = $helper->ask($this->input, $this->output, $question);
                    if (preg_match('/^a/i', $overwrite)) {
                        $overwriteAll    = true;
                        $shouldOverwrite = true;
                    }
                    elseif (preg_match('/^y/i', $overwrite)) {
                        $shouldOverwrite = true;
                    }
                }
                else {
                    $shouldOverwrite = true;
                }
                if ($shouldOverwrite) {
                    $this->fs->remove($tempFile);
                }
                else {
                    $this->output->writeln('Skipped.');
                    continue;
                }
            }
            $this->fs->copy($tempFile . ".tmp", $tempFile);
            $this->fs->remove($tempFile . ".tmp");
            $this->output->writeln("<info>Done.</info>");
        }
    }
    
    protected function configure()
    {
        parent::configure();
        
        $this->setName('slimapp:project:init');
        $this->setDescription("Initialize project directory structure.");
        
        $this->addOption('project-root', 'p', InputOption::VALUE_REQUIRED, "Project root directory.");
    }
    
    protected function ensureProjectRoot()
    {
        if (!($this->rootDir = $this->input->getOption('project-root'))) {
            $this->rootDir = getcwd();
        }
        
        $this->rootDir = realpath($this->rootDir);
        
        $this->fs->mkdir($this->rootDir);
        
        $finder = new Finder();
        $finder->in($this->rootDir);
        $finder->depth(0);
        $finder->ignoreVCS(false);
        
        $rootFiles = [];
        /** @var SplFileInfo $splInfo */
        foreach ($finder as $splInfo) {
            $rootFiles[] = $splInfo->getFilename();
        }
        
        $requiredFiles = [
            'composer.json',
            'composer.lock',
        ];
        $requiredDirs  = [
            'vendor',
        ];
        
        foreach (array_merge($requiredFiles, $requiredDirs) as $file) {
            if (!in_array($file, $rootFiles)) {
                // possibly not root
                $this->output->writeln(
                    "<error>You should either run this script under your project root directory, or provide the '--project-root' option.</error>"
                );
                
                $this->output->writeln(
                    "The project root directory should contain at least the following files and directories:"
                );
                foreach ($requiredFiles as $requiredFile) {
                    $this->output->writeln("\t- <comment>$requiredFile</comment>");
                }
                foreach ($requiredDirs as $requiredDir) {
                    $this->output->writeln("\t- <comment>$requiredDir/</comment>");
                }
                exit(1);
            }
        }
    }
    
    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $this->fs     = new Filesystem();
        $this->input  = $input;
        $this->output = $output;
        
        $this->ensureProjectRoot();
        
        $this->prepareComposerInfo();
        $this->prepareDirectoryStructure();
        
        $this->prepareAppClassFile();
        $this->prepareConfigClassFile();
        
        $this->prepareDatabaseRelatedFiles();
        $this->prepareUnitTestFiles();
        
        $this->prepareConfigYaml();
        $this->prepareServicesYaml();
        $this->prepareRoutesYaml();
        
        $this->prepareBootstrapFile();
        $this->prepareFrontControllerFile();
        $this->prepareConsoleEntryFile();
        $this->prepareDemoControllerFile();
        
        $this->applyTempFiles();
        
        $this->updateComposerInfo();
    }
    
    protected function prepareAppClassFile()
    {
        $this->mainClassname = str_replace("-", "", ucwords($this->projectName, "-"));
        $classFilename       = $this->rootDir . "/" . $this->projectSrcDir . "/" . $this->mainClassname . ".php";
        $this->output->writeln("class file = $classFilename");
        $date = date('Y-m-d');
        $time = date('H:i');
        
        $namespaceDeclaration = trim($this->projectNamespace, "\\");
        $classSource          = <<<SRC
<?php
namespace $namespaceDeclaration;

use Oasis\\SlimApp\\SlimApp;

/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

class {$this->mainClassname} extends SlimApp
{
}


SRC;
        $this->writeToTempFile($classFilename, $classSource);
    }
    
    protected function prepareBootstrapFile()
    {
        $filename = $this->rootDir . "/bootstrap.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("bootstrap file = $filename");
        $bootstrapSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

use {$this->projectNamespace}{$this->mainClassname};
use {$this->projectNamespace}{$this->mainClassname}Configuration;

require_once __DIR__ . "/vendor/autoload.php";

define('PROJECT_DIR', __DIR__);

/** @var {$this->mainClassname} \$app */
\$app = {$this->mainClassname}::app();
\$app->init(__DIR__ . "/config", new {$this->mainClassname}Configuration(), __DIR__ . "/cache/config");

return \$app;


SRC;
        $this->writeToTempFile($filename, $bootstrapSource);
    }
    
    protected function prepareComposerInfo()
    {
        $helper           = $this->getHelper('question');
        $composerFilename = $this->rootDir . "/composer.json";
        
        $composerContent = file_get_contents($composerFilename);
        $composerJson    = json_decode($composerContent, true);
        if (!$composerJson) {
            $this->output->writeln("<error>The composer.json file is not valid!</error>");
            exit(1);
        }
        
        $suggestName = '';
        if (isset($composerJson['name'])) {
            $suggestName = $composerJson['name'];
        }
        $question = new Question(
            "Please enter the name for your project, in the format of <comment>vendor/project</comment> (all in lowercase) "
            . " <info>[$suggestName]</info>: ",
            $suggestName
        );
        $name     = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^[a-z0-9_-]+/[a-z0-9_-]+$#', $name)) {
            $this->output->writeln("<error>The name entered is not valid!</error>");
            exit(1);
        }
        $composerJson['name'] = $name;
        list($this->vendorName, $this->projectName) = explode("/", $name, 2);
        
        if (!isset($composerJson['autoload'])) {
            $composerJson['autoload'] = [];
        }
        if (!isset($composerJson['autoload']['psr-4'])) {
            $composerJson['autoload']['psr-4'] = [];
        }
        
        $namespaces = $composerJson['autoload']['psr-4'];
        
        // auto-detect if namespace is already presented
        $suggestNamespace = str_replace('-', '', ucwords($this->vendorName, '-')) . "\\"
                            . str_replace('-', '', ucwords($this->projectName, '-')) . "\\";
        $suggestSrcDir    = 'src/';
        if ($namespaces) {
            foreach ($namespaces as $namespace => $srcDir) {
                // take the first line in psr-4 as suggestion
                $suggestNamespace = $namespace;
                $suggestSrcDir    = $srcDir;
                break;
            }
        }
        
        // ask the user for confirmation
        $question  = new Question(
            "Please enter the root namespace for your project <info>[$suggestNamespace]</info>: ",
            $suggestNamespace
        );
        $namespace = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^[a-zA-Z0-9_\\\]+$#', $namespace)) {
            $this->output->writeln("<error>The namespace $namespace is not valid!</error>");
            exit(1);
        }
        $this->projectNamespace = trim($namespace, '\\') . "\\";
        
        $question = new Question(
            "Please enter the directory as your source directory <info>[$suggestSrcDir]</info>: ", $suggestSrcDir
        );
        $srcDir   = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^[a-zA-Z0-9_/]+$#', $srcDir)) {
            $this->output->writeln("<error>The source directory $srcDir is not valid!</error>");
            exit(1);
        }
        $this->projectSrcDir = trim($srcDir, "/") . "/";
        
        $namespaces[$this->projectNamespace] = $this->projectSrcDir;
        $composerJson['autoload']['psr-4']   = $namespaces;
        
        $this->writeToTempFile(
            $composerFilename,
            json_encode($composerJson, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
        );
    }
    
    protected function prepareConfigClassFile()
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
    public function getConfigTreeBuilder()
    {
        \$treeBuilder = new TreeBuilder();
        \$root        = \$treeBuilder->root('app');
        {
            \$root->children()->booleanNode('is_debug')->defaultValue(true);
            \$dir = \$root->children()->arrayNode('dir');
            {
                \$dir->children()->scalarNode('log');
                \$dir->children()->scalarNode('data');
                \$dir->children()->scalarNode('cache');
                \$dir->children()->scalarNode('template');
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
    
    protected function prepareConfigYaml()
    {
        $helper = $this->getHelper('question');
        
        $suggestLoggingDir = "/data/logs/{$this->projectName}";
        $question          = new Question(
            "Please provide the logging directory <info>[$suggestLoggingDir]</info>: ",
            $suggestLoggingDir
        );
        $loggingDir        = $helper->ask($this->input, $this->output, $question);
        
        $suggestDataDir = "/data/{$this->projectName}";
        $question       = new Question(
            "Please provide the data directory <info>[$suggestDataDir]</info>: ",
            $suggestDataDir
        );
        $dataDir        = $helper->ask($this->input, $this->output, $question);
        
        $suggestCacheDir = "{$this->rootDir}/cache";
        $question        = new Question(
            "Please provide the cache directory <info>[$suggestCacheDir]</info>: ",
            $suggestCacheDir
        );
        $cacheDir        = $helper->ask($this->input, $this->output, $question);
        
        $suggestTemplateDir = "{$this->rootDir}/templates";
        $question           = new Question(
            "Please provide the template directory <info>[$suggestTemplateDir]</info>: ",
            $suggestTemplateDir
        );
        $templateDir        = $helper->ask($this->input, $this->output, $question);
        
        $filename = $this->rootDir . "/config/tpl.config.yml";
        $config   = [
            "is_debug" => true,
            "dir"      => [
                "log"      => $loggingDir,
                "data"     => $dataDir,
                "cache"    => $cacheDir,
                "template" => $templateDir,
            ],
        ];
        if ($this->ormSupportEnabled) {
            $config['db']        = [
                'host'     => 'localhost',
                'port'     => 3306,
                'user'     => str_replace('-', '_', $this->projectName),
                'password' => $this->projectName,
                'dbname'   => str_replace('-', '_', $this->projectName),
            ];
            $config['memcached'] = [
                'host' => 'localhost',
                'port' => 11211,
            ];
        }
        if ($this->odmSupportEnabled) {
            $config['aws']      = [
                'profile' => $this->projectName,
                'region'  => 'cn-north-1',
            ];
            $config['dynamodb'] = [
                'prefix' => $this->projectName . "-",
            ];
        }
        
        $configYaml = Yaml::dump($config, 5);
        $this->writeToTempFile($filename, $configYaml);
    }
    
    protected function prepareConsoleEntryFile()
    {
        $filename = $this->rootDir . "/bin/" . strtolower($this->projectName) . ".php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("console entry file = $filename");
        $consoleEntrySource = <<<SRC
#! /usr/bin/env php
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */


use {$this->projectNamespace}{$this->mainClassname};

/** @var {$this->mainClassname} \$app */
\$app = require_once __DIR__ . "/../bootstrap.php";

\$app->getConsoleApplication()->run();


SRC;
        $this->writeToTempFile($filename, $consoleEntrySource, 0755);
    }
    
    protected function prepareDatabaseCliConfigFile()
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
 
 
use Doctrine\\ORM\\Tools\\Console\\ConsoleRunner;
use {$this->projectNamespace}Database\\{$this->mainClassname}Database;

require_once __DIR__ . "/../bootstrap.php";

return ConsoleRunner::createHelperSet({$this->mainClassname}Database::getEntityManager());

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
    
    protected function prepareDatabaseManagerFile()
    {
        $filename = $this->rootDir . "/" . $this->projectSrcDir . "/Database/" . $this->mainClassname . "Database.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("database manager file = $filename");
        $namespaceDeclaration              = trim($this->projectNamespace, "\\");
        $entityNamespaceDeclarationEscaped = addcslashes($namespaceDeclaration . "\\Entities", "\\");
        $itemNamespaceDeclarationEscaped   = addcslashes($namespaceDeclaration . "\\Items", "\\");
        $ormImports                        = <<<SRC
use Doctrine\\Common\\Cache\\MemcachedCache;
use Doctrine\\ORM\\Cache\\DefaultCacheFactory;
use Doctrine\\ORM\\Cache\\RegionsConfiguration;
use Doctrine\\ORM\\EntityManager;
use Doctrine\\ORM\\Tools\\Setup;
SRC;
        $odmImports                        = <<<SRC
use Oasis\Mlib\ODM\Dynamodb\ItemManager;
use Oasis\Mlib\Utils\DataProviderInterface;
SRC;
        $ormFunction                       = <<<SRC
    public static function getEntityManager()
    {
        static \$entityManager = null;
        if (\$entityManager instanceof EntityManager) {
            return \$entityManager;
        }
        
        \$app = {$this->mainClassname}::app();

        \$memcache = new MemcachedCache();
        /** @noinspection PhpParamsInspection */
        \$memcache->setMemcached(\$app->getService('memcached'));
        
        \$isDevMode = \$app->isDebug();
        \$config    = Setup::createAnnotationMetadataConfiguration(
            [PROJECT_DIR . "/src/Entities"],
            \$isDevMode,
            \$app->getParameter('app.dir.data') . "/proxies",
            \$memcache,
            false /* do not use simple annotation reader, so that we can understand annotations like @ORM/Table */
        );
        \$config->addEntityNamespace("{$this->mainClassname}", "{$entityNamespaceDeclarationEscaped}");
        //\$config->setSQLLogger(new \\Doctrine\\DBAL\\Logging\\EchoSQLLogger());

        \$regconfig = new RegionsConfiguration();
        \$factory   = new DefaultCacheFactory(\$regconfig, \$memcache);
        \$config->setSecondLevelCacheEnabled();
        \$config->getSecondLevelCacheConfiguration()->setCacheFactory(\$factory);

        \$conn           = \$app->getParameter('app.db');
        \$conn["driver"] = "pdo_mysql";
        \$entityManager  = EntityManager::create(\$conn, \$config);

        return \$entityManager;
    }
SRC;
        $odmFunction                       = <<<SRC
    public static function getItemManager()
    {
        /** @var ItemManager \$im */
        static \$im = null;
        
        if (\$im === null) {
            \$app = {$this->mainClassname}::app();
            
            \$cacheDir  = \$app->getMandatoryConfig('dir.cache', DataProviderInterface::STRING_TYPE);
            \$awsConfig = \$app->getMandatoryConfig('aws', DataProviderInterface::ARRAY_TYPE);
            \$prefix    = \$app->getMandatoryConfig('dynamodb.prefix', DataProviderInterface::STRING_TYPE);
            
            \$im = new ItemManager(\$awsConfig, \$prefix, \$cacheDir, \$app->isDebug());
            \$im->addNamespace("{$itemNamespaceDeclarationEscaped}", PROJECT_DIR . "/src/Items");
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
    
    protected function prepareDatabaseRelatedFiles()
    {
        $helper   = $this->getHelper('question');
        $question = new Question(
            "Do you want to enable ORM support (Doctrine/ORM)?"
            . " <info>[yes]</info>: ",
            'yes'
        );
        $answer   = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^y#i', $answer)) {
            $this->output->writeln("You chose not to enable ORM support.");
        }
        else {
            
            $this->output->writeln("ORM support enabled, related files will be populated.");
            $this->ormSupportEnabled = true;
            $entityDir               = $this->rootDir . "/" . $this->projectSrcDir . "/Entities";
            $this->fs->mkdir($entityDir);
        }
        
        $question = new Question(
            "Do you want to enable ODM support (Oasis/DynamoDb-ODM)?"
            . " <info>[yes]</info>: ",
            'yes'
        );
        $answer   = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^y#i', $answer)) {
            $this->output->writeln("You chose not to enable ODM support.");
        }
        else {
            $this->output->writeln("ODM support enabled, related files will be populated.");
            $this->odmSupportEnabled = true;
            $itemDir                 = $this->rootDir . "/" . $this->projectSrcDir . "/Items";
            $this->fs->mkdir($itemDir);
        }
        
        $this->prepareDatabaseManagerFile();
        $this->prepareDatabaseCliConfigFile();
    }
    
    protected function prepareUnitTestFiles()
    {
        $helper   = $this->getHelper('question');
        $question = new Question(
            "Do you want to enable phpunit?"
            . " <info>[yes]</info>: ",
            'yes'
        );
        $answer   = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^y#i', $answer)) {
            $this->output->writeln("You chose not to enable phpunit.");
            
            return;
        }
        
        $this->phpunitSupportEnabled = true;
        
        $this->output->writeln("phpunit support enabled, related files will be populated.");
        $utDir = $this->rootDir . "/ut";
        $this->fs->mkdir($utDir);
        
        $date            = date('Y-m-d');
        $time            = date('H:i');
        $xmlFile         = <<<XML
<!--suppress XmlUnboundNsPrefix -->
<phpunit
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="http://schema.phpunit.de/5.7/phpunit.xsd"
        bootstrap="ut/bootstrap.php"
        backupGlobals="false"
        backupStaticAttributes="false"
>
    <testsuites>
        <testsuite name="basic">
            <file><!-- add file here --></file>
        </testsuite>
    </testsuites>
</phpunit>

XML;
        $rdbmsClearCodes = <<<PHP
        
\$console = \$app->getConsoleApplication();

/** @var Symfony\\Component\\Console\\Helper\\HelperSet \$helperSet */
\$helperSet = require_once __DIR__ . "/../config/cli-config.php";
\$console->setHelperSet(\$helperSet);
\\Doctrine\\ORM\\Tools\\Console\\ConsoleRunner::addCommands(\$console);

\$output = new \\Symfony\\Component\\Console\\Output\\ConsoleOutput();
\$console->setAutoExit(false);
\$console->setCatchExceptions(false);
\$console->setLoggingEnabled(false);
\$console->run(
    new \\Symfony\\Component\\Console\\Input\\ArrayInput(
        [
            "command" => "orm:schema-tool:drop",
            "-f"      => true,
            "-vvv"    => true,
        ]
    ),
    \$output
);
\$console->run(
    new \\Symfony\\Component\\Console\\Input\\ArrayInput(
        [
            "command" => "orm:schema-tool:create",
        ]
    ),
    \$output
);
PHP;
        if (!$this->ormSupportEnabled) {
            $rdbmsClearCodes = '';
        }
        $utBootstrap = <<<PHP
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

use {$this->projectNamespace}{$this->mainClassname};

/** @var {$this->mainClassname} \$app */
\$app = require __DIR__ . "/../bootstrap.php";
if (!\$app->isDebug()) {
    die ("Never run unit test under production environment!");
}

$rdbmsClearCodes

return \$app;

PHP;
        
        $this->writeToTempFile($this->rootDir . "/phpunit.xml", $xmlFile);
        $this->writeToTempFile($this->rootDir . "/ut/bootstrap.php", $utBootstrap);
        
    }
    
    protected function prepareDemoControllerFile()
    {
        $filename = $this->rootDir . "/" . $this->projectSrcDir . "/Controllers/DemoController.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("front controller file = $filename");
        $namespaceDeclaration = trim($this->projectNamespace, "\\");
        $demoControllerSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */

namespace {$namespaceDeclaration}\\Controllers;

use Symfony\\Component\\HttpFoundation\\Response;

class DemoController
{
    public function testAction()
    {
        return new Response('Hello World!');
    }
}


SRC;
        $this->writeToTempFile($filename, $demoControllerSource);
    }
    
    protected function prepareDirectoryStructure()
    {
        $this->fs->mkdir($this->rootDir . "/bin");
        $this->fs->mkdir($this->rootDir . "/cache");
        $this->fs->mkdir($this->rootDir . "/config");
        $this->fs->mkdir($this->rootDir . "/templates");
        $this->fs->mkdir($this->rootDir . "/web");
        $this->fs->mkdir($this->rootDir . "/assets");
        $this->fs->mkdir(
            StringUtils::stringStartsWith($this->projectSrcDir, "/") ?
                $this->projectSrcDir :
                $this->rootDir . "/" . $this->projectSrcDir
        );
        
    }
    
    protected function prepareFrontControllerFile()
    {
        $filename = $this->rootDir . "/web/front.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("front controller file = $filename");
        $frontSource = <<<SRC
<?php
/**
 * Created by SlimApp.
 *
 * Date: $date
 * Time: $time
 */


use {$this->projectNamespace}{$this->mainClassname};

/** @var {$this->mainClassname} \$app */
\$app = require_once __DIR__ . "/../bootstrap.php";

\$app->getHttpKernel()->run();


SRC;
        $this->writeToTempFile($filename, $frontSource);
    }
    
    protected function prepareRoutesYaml()
    {
        $filename    = $this->rootDir . "/config/routes.yml";
        $services    = [
            "home" => [
                "path"     => "/",
                "defaults" => [
                    "_controller" => "DemoController::testAction",
                ],
            
            ],
        ];
        $serviceYaml = Yaml::dump($services, 7);
        $this->writeToTempFile($filename, $serviceYaml);
    }
    
    protected function prepareServicesYaml()
    {
        //$helper = $this->getHelper('question');
        
        $filename = $this->rootDir . "/config/services.yml";
        $services = [
            "imports"    => [
            
            ],
            "parameters" => [
                "default.namespace" => [
                    "Oasis\\Mlib\\",
                    $this->projectNamespace,
                ],
            ],
            "services"   => [
                "app" => [
                    "properties" => [
                        "logging" => [
                            "path"  => "%app.dir.log%",
                            "level" => "debug",
                        ],
                        "cli"     => [
                            "name"    => $this->projectName,
                            "version" => "0.1",
                        ],
                        "http"    => [
                            "cache_dir" => "%app.dir.cache%",
                            "routing"   => [
                                "path"       => "%app.dir.config%/routes.yml",
                                "namespaces" => [$this->projectNamespace, $this->projectNamespace . "Controllers\\"],
                            ],
                            "twig"      => [
                                "template_dir" => "%app.dir.template%",
                                "globals"      => [
                                    "app" => "@app",
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ];
        if ($this->ormSupportEnabled) {
            $services['services']['memcached']                                  = [
                "class" => "Memcached",
                "calls" => [
                    [
                        "addServer",
                        ['%app.memcached.host%', '%app.memcached.port%'],
                    ],
                ],
            ];
            $services['services']['entity_manager']                             = [
                "class"   => "Doctrine\\ORM\\EntityManager",
                "factory" => [
                    $this->projectNamespace . "Database\\" . $this->mainClassname . "Database",
                    "getEntityManager",
                ],
            ];
            $services['services']['app']['properties']['http']['injected_args'] = [
                "@entity_manager",
            ];
        }
        $serviceYaml = Yaml::dump($services, 7);
        $this->writeToTempFile($filename, $serviceYaml);
    }
    
    protected function updateComposerInfo()
    {
        $this->output->writeln("Will now update composer related files ...");
        $oldDir = getcwd();
        chdir($this->rootDir);
        
        if ($this->ormSupportEnabled) {
            system("composer require oasis/doctrine-addon", $retval);
            if ($retval == 0) {
                $this->output->writeln("<info>ORM support component updated.</info>");
            }
            else {
                $this->output->writeln("<error>Error while updating ORM support component.</error>");
                exit(1);
            }
        }
        
        if ($this->odmSupportEnabled) {
            system("composer require oasis/dynamodb-odm", $retval);
            if ($retval == 0) {
                $this->output->writeln("<info>ODM support component updated.</info>");
            }
            else {
                $this->output->writeln("<error>Error while updating ODM support component.</error>");
                exit(1);
            }
        }
        
        if ($this->phpunitSupportEnabled) {
            system("composer require --dev phpunit/phpunit:^5.7", $retval);
            if ($retval == 0) {
                $this->output->writeln("<info>phpunit component updated.</info>");
            }
            else {
                $this->output->writeln("<error>Error while updating phpunit component.</error>");
                exit(1);
            }
        }
        
        system("composer dumpautoload", $retval);
        if ($retval == 0) {
            $this->output->writeln("<info>Autoloader updated.</info>");
        }
        else {
            $this->output->writeln("<error>Error while updating autoload file.</error>");
            exit(1);
        }
        
        chdir($oldDir);
    }
    
    protected function writeToTempFile($realFilename, $content, $mode = 0644)
    {
        $dir = dirname($realFilename);
        $this->fs->mkdir($dir);
        file_put_contents($realFilename . ".tmp", $content);
        chmod($realFilename . ".tmp", $mode);
        $this->tempFiles[] = $realFilename;
    }
    
}
