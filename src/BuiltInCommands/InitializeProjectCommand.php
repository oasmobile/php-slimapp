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
    protected $projectName;
    /** @var  string */
    protected $mainClassname;
    /** @var  string */
    protected $projectNamespace;
    /** @var  string */
    protected $projectSrcDir;
    /** @var  string */
    protected $cacheDir;
    
    protected $tempFiles = [];
    
    protected function configure()
    {
        parent::configure();
        
        $this->setName('slimapp:project:init');
        $this->setDescription("Initialize project directory structure.");
        
        $this->addOption('project-root', 'p', InputOption::VALUE_REQUIRED, "Project root directory.");
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
        
        $this->prepareConfigYaml();
        $this->prepareServicesYaml();
        $this->prepareRoutesYaml();
        
        $this->prepareBootstrapFile();
        $this->prepareFrontControllerFile();

        $this->applyTempFiles();
        $this->dumpComposerAutoload();
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
        list(, $this->projectName) = explode("/", $name, 2);
        
        if (!isset($composerJson['autoload'])) {
            $composerJson['autoload'] = [];
        }
        if (!isset($composerJson['autoload']['psr-4'])) {
            $composerJson['autoload']['psr-4'] = [];
        }
        
        $namespaces = $composerJson['autoload']['psr-4'];
        
        // auto-detect if namespace is already presented
        $suggestNamespace = '';
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
    
    protected function prepareDirectoryStructure()
    {
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

use Oasis\SlimApp\SlimApp;

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

use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

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
            \$dir = \$root->children()->arrayNode('dir');
            {
                \$dir->children()->scalarNode('log');
                \$dir->children()->scalarNode('data');
                \$dir->children()->scalarNode('cache');
                \$dir->children()->scalarNode('template');
            }
        }

        return \$treeBuilder;
    }
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

    protected function prepareFrontControllerFile()
    {
        $filename = $this->rootDir . "/web/front.php";
        $date     = date('Y-m-d');
        $time     = date('H:i');
        $this->output->writeln("front controller file = $filename");
        $bootstrapSource = <<<SRC
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
        $this->writeToTempFile($filename, $bootstrapSource);
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
        
        $filename = $this->rootDir . "/config/config.yml";
        $config   = [
            "dir" => [
                "log"      => $loggingDir,
                "data"     => $dataDir,
                "cache"    => $cacheDir,
                "template" => $templateDir,
            ],
        ];
        
        $configYaml = Yaml::dump($config, 5);
        $this->writeToTempFile($filename, $configYaml);
    }
    
    protected function prepareServicesYaml()
    {
        //$helper = $this->getHelper('question');
        
        $filename    = $this->rootDir . "/config/services.yml";
        $services    = [
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
                                "namespaces" => [$this->projectNamespace],
                            ],
                            "twig"      => [
                                "template_dir" => "%app.dir.template%",
                            ],
                        ],
                    ],
                ],
            ],
        ];
        $serviceYaml = Yaml::dump($services, 7);
        $this->writeToTempFile($filename, $serviceYaml);
    }

    protected function prepareRoutesYaml()
    {
        $filename    = $this->rootDir . "/config/routes.yml";
        $services    = [
            "home" => [
                "path"     => "/",
                "defaults" => [
                    "controller" => "--- write your controller here ---",
                ],

            ],
        ];
        $serviceYaml = Yaml::dump($services, 7);
        $this->writeToTempFile($filename, $serviceYaml);
    }

    protected function writeToTempFile($realFilename, $content)
    {
        $dir = dirname($realFilename);
        $this->fs->mkdir($dir);
        file_put_contents($realFilename . ".tmp", $content);
        $this->tempFiles[] = $realFilename;
    }
    
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
                    $question  = new Question(
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

    protected function dumpComposerAutoload()
    {
        $this->output->writeln("Will now update autoload file ...");
        $oldDir = getcwd();
        chdir($this->rootDir);
        system("composer dumpautoload", $retval);
        chdir($oldDir);

        if ($retval == 0) {
            $this->output->writeln("<info>Done.</info>");
        }
        else {
            $this->output->writeln("<error>Error while updating autoload file.</error>");
            exit(1);
        }
    }
    
}
