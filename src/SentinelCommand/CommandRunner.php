<?php
declare(strict_types=1);

namespace Oasis\SlimApp\SentinelCommand;

use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class CommandRunner
{
    protected Application $application;
    protected int $parallelIndex;
    protected string $name;
    protected InputInterface $input;
    protected OutputInterface $output;

    protected bool $once = false;
    protected int $interval = 0;
    protected int $frequency = 0;
    protected bool $frequencyFixed = false;

    protected int $lastRun = 0;
    protected int $nextRun = 0;
    protected int $currentPid = 0;
    protected bool $alert = true;
    protected bool $stopped = false;
    protected bool $traceEnabled = false;

    /**
     * @param array<string, mixed> $command
     */
    public function __construct(
        Application $application,
        int $parallelIndex,
        array $command,
        OutputInterface $output,
        bool $traceEnabled = false,
    ) {
        $this->application   = $application;
        $this->parallelIndex = $parallelIndex;

        $this->output = $output;

        $this->name = $command['name'];
        $args       = ['command' => $this->name];
        $args       = array_merge($args, $command['args']);
        $args = array_map(
            function (mixed $argValue): mixed {
                if ($argValue === "\$PARALLEL_INDEX") {
                    return $this->parallelIndex;
                }
                else {
                    return $argValue;
                }
            },
            $args
        );
        $this->input = new ArrayInput($args);

        $this->once           = $command['once'];
        $this->interval       = $command['interval'];
        $this->frequency      = $command['frequency'];
        $this->frequencyFixed = $command['frequency_fixed'];
        $this->alert          = $command['alert'];

        $this->nextRun      = time();
        $this->traceEnabled = $traceEnabled;
    }

    public function shouldStartNextRunWhenNotFinished(): bool
    {
        if (!$this->frequencyFixed || !$this->frequency || $this->once) {
            return false;
        }

        if ($this->lastRun + $this->frequency <= time()) {
            return true;
        }
        else {
            return false;
        }
    }

    /**
     * clones an early runner when frequency is reached before current run finishes
     */
    public function cloneEarlyRunner(): self
    {
        $ret          = clone $this;
        $ret->nextRun = time();
        $this->once   = true;

        return $ret;
    }

    public function __clone(): void
    {
        $this->lastRun    = 0;
        $this->nextRun    = 0;
        $this->currentPid = 0;
    }

    public function onProcessExit(int $exitStatus, int $pid): void
    {
        if ($exitStatus != 0) {
            if ($this->alert) {
                malert("Daemon command %s failed with exit code = %d", $this->name, $exitStatus);
            }
            else {
                mwarning("Daemon command %s failed with exit code = %d", $this->name, $exitStatus);
            }
        }

        if ($this->once) {
            $this->stopped = true;
        }
        else {
            $this->nextRun = time();

            if ($this->frequency) {
                if ($this->nextRun - $this->lastRun < $this->frequency) {
                    $this->nextRun = $this->lastRun + $this->frequency;
                }
            }

            if ($this->interval && $this->nextRun - time() < $this->interval) {
                $this->nextRun = time() + $this->interval;
            }
        }

        if ($this->traceEnabled) {
            mdebug(
                "Process [%d] exits for command %s, exit code = %d, last run = %d, next run = %d",
                $pid,
                $this->name,
                $exitStatus,
                $this->lastRun,
                $this->nextRun
            );
        }
    }

    public function run(): int
    {
        if ($this->stopped) {
            return 0;
        }

        $pid = pcntl_fork();
        if ($pid < 0) {
            // @codeCoverageIgnoreStart
            $errno = pcntl_get_last_error();
            throw new \RuntimeException("Cannot fork process, error = " . pcntl_strerror($errno));
            // @codeCoverageIgnoreEnd
        }
        elseif ($pid == 0) {
            // @codeCoverageIgnoreStart — child process; covered by tests/scripts/sentinel_command_test.php
            $now = time();
            if ($now < $this->nextRun) {
                if ($this->traceEnabled) {
                    mdebug("Will wait %d seconds for next run of %s", $this->nextRun - $now, $this->name);
                }
                sleep($this->nextRun - $now);
            }

            // run using application
            $this->application->setAutoExit(false); // we will handle exit on our own
            $this->application->setCatchExceptions(false); // we will catch on our own
            try {
                $ret = $this->application->run($this->input, $this->output);
            } catch (\Exception $e) {
                mtrace($e, "Exception while running command {$this->name}", "error");
                $ret = DaemonSentinelCommand::EXIT_CODE_COMMON_ERROR;
            }

            // Check if we should alert
            if ($ret != DaemonSentinelCommand::EXIT_CODE_OK
                && $this->alert
            ) {
                // alert in child process is better, because we can get more trace here
                malert("Daemon command %s failed with exit code = %d", $this->name, $ret);

                exit(DaemonSentinelCommand::EXIT_CODE_OK); // exit OK because alert is already sent
            }
            else {
                exit($ret);
            }
            // @codeCoverageIgnoreEnd
        }
        else {
            $this->lastRun    = $this->nextRun;
            $this->currentPid = $pid;

            return $pid;
        }
    }
}
