<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-10
 * Time: 14:57
 */

namespace Oasis\SlimApp;

use Monolog\Logger;
use Oasis\Mlib\Logging\MLogging;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class ConsoleApplication extends Application
{
    protected function configureIO(InputInterface $input, OutputInterface $output)
    {
        parent::configureIO($input, $output);

        switch ($output->getVerbosity()) {
            case OutputInterface::VERBOSITY_VERY_VERBOSE:
                MLogging::setMinLogLevel(Logger::INFO);
                break;
            case OutputInterface::VERBOSITY_VERBOSE:
                MLogging::setMinLogLevel(Logger::NOTICE);
                break;
            case OutputInterface::VERBOSITY_DEBUG:
                MLogging::setMinLogLevel(Logger::DEBUG);
                break;
            case OutputInterface::VERBOSITY_NORMAL:
                MLogging::setMinLogLevel(Logger::WARNING);
                break;
            case OutputInterface::VERBOSITY_QUIET:
                MLogging::setMinLogLevel(Logger::CRITICAL);
                break;
        }
    }
    
}
