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
        $config    = Yaml::parse(file_get_contents($filename));
        $configs   = [$config];
        $configDef = new CommandConfiguration($this->getApplication());

        $processor = new Processor();
        $processed = $processor->processConfiguration($configDef, $configs);

        $this->runningProcesses = [];
        foreach ($processed['commands'] as $command) {
            $parallel = $command['parallel'];
            if ($parallel != intval($parallel)) {
                throw new \InvalidArgumentException("parallel value is not an integer! <$parallel>");
            }

            for ($i = 0; $i < $parallel; ++$i) {
                $runner = new CommandRunner($this->getApplication(), $i, $command, $output);
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
                if (!isset($this->runningProcesses[$pid])
                    || !(($runner = $this->runningProcesses[$pid]) instanceof CommandRunner)
                ) {
                    throw new \LogicException(\sprintf('Cannot find command runner for process pid = %d', $pid));
                }
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
                    // some other error
                    throw new \RuntimeException('Error waiting for process, error = ' . pcntl_strerror($errno));
                }
            }
        }
    }
}
