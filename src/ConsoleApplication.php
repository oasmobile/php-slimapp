<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-10
 * Time: 14:57
 */

namespace Oasis\SlimApp;

use Monolog\Logger;
use Oasis\Mlib\Logging\ConsoleHandler;
use Oasis\Mlib\Logging\LocalErrorHandler;
use Oasis\Mlib\Logging\LocalFileHandler;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class ConsoleApplication extends Application
{
    /** @var SlimApp */
    protected $slimapp = null;

    protected $loggingPath  = null;
    protected $loggingLevel = Logger::DEBUG;

    /**
     * @return SlimApp
     */
    public function getSlimapp()
    {
        return $this->slimapp;
    }

    /**
     * @param SlimApp $slimapp
     */
    public function setSlimapp($slimapp)
    {
        $this->slimapp = $slimapp;
    }

    /**
     * @return int
     */
    public function getLoggingLevel()
    {
        return $this->loggingLevel;
    }

    /**
     * @param int $loggingLevel
     */
    public function setLoggingLevel($loggingLevel)
    {
        $this->loggingLevel = $loggingLevel;
    }

    /**
     * @return null
     */
    public function getLoggingPath()
    {
        if ($this->loggingPath === null) {
            $this->loggingPath = sys_get_temp_dir() . "/logs";
        }

        return $this->loggingPath;
    }

    /**
     * @param null $loggingPath
     */
    public function setLoggingPath($loggingPath)
    {
        $this->loggingPath = $loggingPath;
    }

    protected function configureIO(InputInterface $input, OutputInterface $output)
    {
        parent::configureIO($input, $output);

        $level = Logger::DEBUG;
        switch ($output->getVerbosity()) {
            case OutputInterface::VERBOSITY_VERY_VERBOSE:
                $level = Logger::INFO;
                break;
            case OutputInterface::VERBOSITY_VERBOSE:
                $level = Logger::NOTICE;
                break;
            case OutputInterface::VERBOSITY_DEBUG:
                $level = Logger::DEBUG;
                break;
            case OutputInterface::VERBOSITY_NORMAL:
                $level = Logger::WARNING;
                break;
            case OutputInterface::VERBOSITY_QUIET:
                $level = Logger::CRITICAL;
                break;
        }
        $handler = new ConsoleHandler($level);
        $handler->install();
    }

    protected function doRunCommand(Command $command, InputInterface $input, OutputInterface $output)
    {
        $name   = $command->getName();
        $name   = strtr($name, ":", ".");
        $logger = new LocalFileHandler(
            $this->getLoggingPath(), "%date%/%script%.$name.log", $this->getLoggingLevel()
        );
        $logger->install();
        $logger = new LocalErrorHandler(
            $this->getLoggingPath(), "%date%/%script%.$name.error", $this->getLoggingLevel()
        );
        $logger->install();

        return parent::doRunCommand($command, $input, $output);
    }

}
