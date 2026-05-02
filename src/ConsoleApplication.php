<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

use Monolog\Level;
use Oasis\Mlib\Logging\ConsoleHandler;
use Oasis\Mlib\Logging\LocalErrorHandler;
use Oasis\Mlib\Logging\LocalFileHandler;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class ConsoleApplication extends Application
{
    protected ?SlimApp $slimapp = null;

    protected bool $loggingEnabled = true;
    protected ?string $loggingPath = null;
    protected string $logFilePattern = '%date%/%script%.%command%.%type%';
    protected Level $loggingLevel = Level::Debug;

    public function __construct(string $name = 'UNKNOWN', string $version = 'UNKNOWN')
    {
        parent::__construct($name, $version);
    }

    public function isLoggingEnabled(): bool
    {
        return $this->loggingEnabled;
    }

    public function setLoggingEnabled(bool $loggingEnabled): void
    {
        $this->loggingEnabled = $loggingEnabled;
    }

    public function getLogFilePattern(): string
    {
        return $this->logFilePattern;
    }

    public function setLogFilePattern(string $logFilePattern): void
    {
        $this->logFilePattern = $logFilePattern;
    }

    public function getLoggingLevel(): Level
    {
        return $this->loggingLevel;
    }

    public function setLoggingLevel(Level $loggingLevel): void
    {
        $this->loggingLevel = $loggingLevel;
    }

    public function getLoggingPath(): string
    {
        if ($this->loggingPath === null) {
            $this->loggingPath = sys_get_temp_dir() . '/logs';
        }

        return $this->loggingPath;
    }

    public function setLoggingPath(?string $loggingPath): void
    {
        $this->loggingPath = $loggingPath;
    }

    public function getSlimapp(): ?SlimApp
    {
        return $this->slimapp;
    }

    public function setSlimapp(SlimApp $slimapp): void
    {
        $this->slimapp = $slimapp;
    }

    protected function configureIO(InputInterface $input, OutputInterface $output): void
    {
        parent::configureIO($input, $output);

        $level = match ($output->getVerbosity()) {
            OutputInterface::VERBOSITY_QUIET        => Level::Critical,
            OutputInterface::VERBOSITY_NORMAL       => Level::Warning,
            OutputInterface::VERBOSITY_VERBOSE      => Level::Notice,
            OutputInterface::VERBOSITY_VERY_VERBOSE => Level::Info,
            OutputInterface::VERBOSITY_DEBUG        => Level::Debug,
            default                                 => Level::Debug,
        };

        if ($this->loggingEnabled) {
            $handler = new ConsoleHandler($level);
            $handler->install();
        }
    }

    protected function doRunCommand(Command $command, InputInterface $input, OutputInterface $output): int
    {
        if ($this->loggingEnabled) {
            $name             = $command->getName();
            $name             = strtr($name, ':', '.');
            $logFilePattern   = strtr(
                $this->logFilePattern,
                [
                    '%script%' => $name,
                    '%type%'   => 'log',
                ]
            );
            $errorFilePattern = strtr(
                $this->logFilePattern,
                [
                    '%script%' => $name,
                    '%type%'   => 'error',
                ]
            );
            $logger           = new LocalFileHandler(
                $this->getLoggingPath(), $logFilePattern, $this->getLoggingLevel()
            );
            $logger->install();
            $logger = new LocalErrorHandler(
                $this->getLoggingPath(), $errorFilePattern, $this->getLoggingLevel()
            );
            $logger->install();
        }

        return parent::doRunCommand($command, $input, $output);
    }
}
