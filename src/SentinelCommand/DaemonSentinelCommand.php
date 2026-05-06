<?php
declare(strict_types=1);

namespace Oasis\SlimApp\SentinelCommand;

use Oasis\SlimApp\AbstractAlertableCommand;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Yaml\Yaml;

class DaemonSentinelCommand extends AbstractAlertableCommand
{
    /** @var CommandRunner[] */
    protected array $runningProcesses = [];

    protected function configure(): void
    {
        parent::configure();
        $this->setDescription('Runs as sentinel for a list of daemon commands');
        $this->addArgument('file', InputArgument::REQUIRED, 'a config file holding daemon commands info');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $filename = $input->getArgument('file');
        if (!is_readable($filename)) {
            $output->writeln(
                sprintf(
                    '<error>File %s is not readable!</error>',
                    $filename
                )
            );

            return 1;
        }
        $config    = Yaml::parse((string)file_get_contents($filename));
        $configs   = [$config];
        $application = $this->getApplication();
        assert($application !== null);
        $configDef = new CommandConfiguration($application);

        $processor = new Processor();
        $processed = $processor->processConfiguration($configDef, $configs);

        $this->runningProcesses = [];
        foreach ($processed['commands'] as $command) {
            $parallel = $command['parallel'];
            if ($parallel != intval($parallel)) {
                throw new \InvalidArgumentException("parallel value is not an integer! <$parallel>");
            }

            for ($i = 0; $i < $parallel; ++$i) {
                $runner = new CommandRunner($application, $i, $command, $output);
                $pid    = $runner->run();

                $this->runningProcesses[$pid] = $runner;
            }
        }

        $this->waitForBackgroundProcesses();

        return 0;
    }

    protected function waitForBackgroundProcesses(): void
    {
        while (true) {
            pcntl_signal_dispatch();

            $status = 0;
            $pid    = pcntl_waitpid(-1, $status, WNOHANG);

            if ($pid == 0) { // no child process has quit
                $jumpStarted = [];
                foreach ($this->runningProcesses as $runner) {
                    if ($runner->shouldStartNextRunWhenNotFinished()) {
                        $earlyRunner                  = $runner->cloneEarlyRunner();
                        $earlyRunnerPid               = $earlyRunner->run();
                        $jumpStarted[$earlyRunnerPid] = $earlyRunner;
                    }
                }
                $this->runningProcesses = $this->runningProcesses + $jumpStarted;
                usleep(200 * 1000);
            } elseif ($pid > 0) { // child process with pid = $pid exits
                $exitStatus = pcntl_wexitstatus($status);
                if ($exitStatus === false) {
                    // @codeCoverageIgnoreStart
                    throw new \RuntimeException(\sprintf('Failed to get exit status for process pid = %d', $pid));
                    // @codeCoverageIgnoreEnd
                }
                if (!isset($this->runningProcesses[$pid])) {
                    // @codeCoverageIgnoreStart
                    throw new \LogicException(\sprintf('Cannot find command runner for process pid = %d', $pid));
                    // @codeCoverageIgnoreEnd
                }
                $runner = $this->runningProcesses[$pid];
                unset($this->runningProcesses[$pid]);
                $runner->onProcessExit($exitStatus, $pid);
                $newPid = $runner->run();
                if ($newPid > 0) {
                    $this->runningProcesses[$newPid] = $runner;
                }
            } else { // error
                $errno = pcntl_get_last_error();
                if ($errno == PCNTL_ECHILD) {
                    // all children finished
                    mdebug('No more BackgroundProcessRunner children, continue ...');
                    break;
                } else {
                    // @codeCoverageIgnoreStart
                    throw new \RuntimeException('Error waiting for process, error = ' . pcntl_strerror($errno));
                    // @codeCoverageIgnoreEnd
                }
            }
        }
    }
}
