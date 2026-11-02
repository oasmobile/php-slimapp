<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands;

use Oasis\Mlib\Utils\StringUtils;
use RuntimeException;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Helper\QuestionHelper;
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
    use Templates\DatabaseTemplates;
    use Templates\UnitTestTemplates;
    use Templates\ConfigurationTemplate;
    use Templates\ServicesTemplate;

    protected Filesystem $fs;
    protected InputInterface $input;
    protected OutputInterface $output;
    protected string $rootDir = '';
    protected string $vendorName = '';
    protected string $projectName = '';
    protected string $mainClassname = '';
    protected string $projectNamespace = '';
    protected string $projectSrcDir = '';
    protected string $cacheDir = '';
    protected bool $ormSupportEnabled = false;
    protected bool $odmSupportEnabled = false;
    protected bool $phpunitSupportEnabled = false;
    /** @var string[] */
    protected array $tempFiles = [];
    
    private function getQuestionHelper(): QuestionHelper
    {
        $helper = $this->getHelper('question');
        assert($helper instanceof QuestionHelper);
        return $helper;
    }
    
    protected function applyTempFiles(): void
    {
        $helper = $this->getQuestionHelper();
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
    
    protected function configure(): void
    {
        parent::configure();
        
        $this->setName('slimapp:project:init');
        $this->setDescription("Initialize project directory structure.");
        
        $this->addOption('project-root', 'p', InputOption::VALUE_REQUIRED, "Project root directory.");
    }
    
    protected function ensureProjectRoot(): void
    {
        $projectRoot = $this->input->getOption('project-root');
        if (!is_string($projectRoot) || $projectRoot === '') {
            $cwd = getcwd();
            if ($cwd === false) {
                throw new RuntimeException('Cannot determine current working directory.');
            }
            $this->rootDir = $cwd;
        } else {
            $this->rootDir = $projectRoot;
        }
        
        $realRoot = realpath($this->rootDir);
        if ($realRoot !== false) {
            $this->rootDir = $realRoot;
        }
        
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
                throw new RuntimeException('Project root directory is missing required files.');
            }
        }
    }
    
    protected function execute(InputInterface $input, OutputInterface $output): int
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

        return 0;
    }
    
    protected function prepareAppClassFile(): void
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
    
    protected function prepareBootstrapFile(): void
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
    
    protected function prepareComposerInfo(): void
    {
        $helper           = $this->getQuestionHelper();
        $composerFilename = $this->rootDir . "/composer.json";
        
        $composerContent = file_get_contents($composerFilename);
        if ($composerContent === false) {
            throw new RuntimeException("Cannot read $composerFilename");
        }
        $composerJson    = json_decode($composerContent, true);
        if (!is_array($composerJson)) {
            $this->output->writeln("<error>The composer.json file is not valid!</error>");
            throw new RuntimeException('The composer.json file is not valid!');
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
            throw new RuntimeException('The name entered is not valid!');
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
            throw new RuntimeException("The namespace $namespace is not valid!");
        }
        $this->projectNamespace = trim($namespace, '\\') . "\\";
        
        $question = new Question(
            "Please enter the directory as your source directory <info>[$suggestSrcDir]</info>: ", $suggestSrcDir
        );
        $srcDir   = $helper->ask($this->input, $this->output, $question);
        if (!preg_match('#^[a-zA-Z0-9_/]+$#', $srcDir)) {
            $this->output->writeln("<error>The source directory $srcDir is not valid!</error>");
            throw new RuntimeException("The source directory $srcDir is not valid!");
        }
        $this->projectSrcDir = trim($srcDir, "/") . "/";
        
        $namespaces[$this->projectNamespace] = $this->projectSrcDir;
        $composerJson['autoload']['psr-4']   = $namespaces;
        
        $this->writeToTempFile(
            $composerFilename,
            (string)json_encode($composerJson, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
        );
    }
    
    protected function prepareConfigYaml(): void
    {
        $helper = $this->getQuestionHelper();
        
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
        
        $suggestCacheDir = "./cache";
        $question        = new Question(
            "Please provide the cache directory <info>[$suggestCacheDir]</info>: ",
            $suggestCacheDir
        );
        $cacheDir        = $helper->ask($this->input, $this->output, $question);
        
        $suggestTemplateDir = "./templates";
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
                'host'      => 'localhost',
                'port'      => 11211,
                'namespace' => $this->projectName,
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
    
    protected function prepareConsoleEntryFile(): void
    {
        $filename = $this->rootDir . "/bin/" . strtolower($this->projectName) . ".php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("console entry file = $filename");
        
        $ormRegistration = '';
        if ($this->ormSupportEnabled) {
            $ormRegistration = <<<ORM


// Register Doctrine ORM commands
\$provider = require_once __DIR__ . "/../config/cli-config.php";
\\Doctrine\\ORM\\Tools\\Console\\ConsoleRunner::addCommands(\$app->getConsoleApplication(), \$provider);
ORM;
        }
        
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
$ormRegistration

\$app->getConsoleApplication()->run();


SRC;
        $this->writeToTempFile($filename, $consoleEntrySource, 0755);
    }
    
    protected function prepareDatabaseRelatedFiles(): void
    {
        $helper   = $this->getQuestionHelper();
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
    
    protected function prepareDemoControllerFile(): void
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
    
    protected function prepareDirectoryStructure(): void
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
    
    protected function prepareFrontControllerFile(): void
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
    
    protected function prepareRoutesYaml(): void
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
    
    protected function updateComposerInfo(): void
    {
        $this->output->writeln("Will now update composer related files ...");
        $oldDir = getcwd();
        if ($oldDir === false) {
            throw new RuntimeException('Cannot determine current working directory.');
        }
        chdir($this->rootDir);
        
        try {
            if ($this->ormSupportEnabled) {
                system("composer require oasis/doctrine-addon", $retval);
                if ($retval === 0) {
                    $this->output->writeln("<info>ORM support component updated.</info>");
                } else {
                    throw new RuntimeException('Error while updating ORM support component.');
                }
            }
            
            if ($this->odmSupportEnabled) {
                system("composer require oasis/dynamodb-odm", $retval);
                if ($retval === 0) {
                    $this->output->writeln("<info>ODM support component updated.</info>");
                } else {
                    throw new RuntimeException('Error while updating ODM support component.');
                }
            }
            
            if ($this->phpunitSupportEnabled) {
                system("composer require --dev phpunit/phpunit:^13", $retval);
                if ($retval === 0) {
                    $this->output->writeln("<info>phpunit component updated.</info>");
                } else {
                    throw new RuntimeException('Error while updating phpunit component.');
                }
            }
            
            system("composer dumpautoload", $retval);
            if ($retval === 0) {
                $this->output->writeln("<info>Autoloader updated.</info>");
            } else {
                throw new RuntimeException('Error while updating autoload file.');
            }
        } finally {
            chdir($oldDir);
        }
    }
    
    protected function writeToTempFile(string $realFilename, string $content, int $mode = 0644): void
    {
        $dir = dirname($realFilename);
        $this->fs->mkdir($dir);
        file_put_contents($realFilename . ".tmp", $content);
        chmod($realFilename . ".tmp", $mode);
        $this->tempFiles[] = $realFilename;
    }
    
}
