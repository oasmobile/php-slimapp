<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands\Templates;

use Symfony\Component\Console\Question\Question;
use Symfony\Component\Yaml\Yaml;

trait UnitTestTemplates
{
    protected function prepareUnitTestFiles(): void
    {
        $helper   = $this->getQuestionHelper();
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
<phpunit
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/13.0/phpunit.xsd"
        bootstrap="ut/bootstrap.php"
        backupGlobals="false"
        colors="true"
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

\$provider = require_once __DIR__ . "/../config/cli-config.php";
\\Doctrine\\ORM\\Tools\\Console\\ConsoleRunner::addCommands(\$console, \$provider);

\$output = new \\Symfony\\Component\\Console\\Output\\ConsoleOutput();
\$console->setAutoExit(false);
\$console->setCatchExceptions(false);
\$console->setLoggingEnabled(false);
\$console->run(
    new \\Symfony\\Component\\Console\\Input\\ArrayInput(
        [
            "command" => "orm:schema-tool:drop",
            "--force" => true,
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
use Monolog\\Level;
use Oasis\\Mlib\\Logging\\ConsoleHandler;
use Oasis\\Mlib\\Logging\\MLogging;

/** @var {$this->mainClassname} \$app */
\$app = require __DIR__ . "/../bootstrap.php";
if (!\$app->isDebug()) {
    die ("Never run unit test under production environment!");
}

(new ConsoleHandler())->install();
if (!in_array('-v', \$_SERVER['argv'])
    && !in_array('--verbose', \$_SERVER['argv'])
) {
    MLogging::setMinLogLevel(Level::Critical);
}


$rdbmsClearCodes


return \$app;

PHP;
        
        $this->writeToTempFile($this->rootDir . "/phpunit.xml", $xmlFile);
        $this->writeToTempFile($this->rootDir . "/ut/bootstrap.php", $utBootstrap);
        
    }
}
