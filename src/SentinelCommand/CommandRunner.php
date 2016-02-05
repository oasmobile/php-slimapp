<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-05
 * Time: 14:42
 */

namespace Oasis\SlimApp\SentinelCommand;

use Symfony\Component\Console\Application;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class CommandRunner
{
    /** @var  Application */
    protected $application;

    protected $name;
    /** @var  InputInterface */
    protected $input;
    /** @var  OutputInterface */
    protected $output;

    protected $once      = false;
    protected $interval  = 0;
    protected $frequency = 0;

    protected $lastRun = 0;
    protected $nextRun = 0;
    protected $alert   = true;
    protected $stopped = false;

    public function __construct(Application $application, array $command, OutputInterface $output)
    {
        $this->application = $application;
        $this->output      = $output;
        $this->name        = $command['name'];
        $args              = ['command' => $this->name];
        $args              = array_merge($args, $command['args']);
        $this->input       = new ArrayInput($args);

        $this->once      = $command['once'];
        $this->interval  = $command['interval'];
        $this->frequency = $command['frequency'];
        $this->alert     = $command['alert'];

        $this->nextRun = time();
    }

    public function run()
    {
        if ($this->stopped) {
            return 0;
        }

        $pid = pcntl_fork();
        if ($pid < 0) {
            $errno = pcntl_get_last_error();
            throw new \RuntimeException("Cannot fork process, error = " . pcntl_strerror($errno));
        }
        elseif ($pid == 0) {
            // in child process
            $now = time();
            if ($now < $this->nextRun) {
                mnotice("Will wait %d seconds for next run of %s", $this->nextRun - $now, $this->name);
                sleep($this->nextRun - $now);
            }
            $this->application->setAutoExit(false); // we will handle exit on our own
            $ret = $this->application->run($this->input, $this->output);
            if ($ret != AbstractDaemonSentinelCommand::EXIT_CODE_OK
                && $this->alert
            ) {
                // alert in child process is better, because we can get more trace here
                malert("Daemon command %s failed with exit code = %d", $this->name, $ret);

                exit(AbstractDaemonSentinelCommand::EXIT_CODE_OK); // exit OK because alert is already sent
            }
            else {
                exit($ret);
            }
        }
        else {
            $this->lastRun = $this->nextRun;

            return $pid;
        }
    }

    public function onProcessExit($exitStatus, $pid)
    {
        mdebug(
            "Process [%d] exits for command %s, exit code = %d, last run = %d, next run = %d",
            $pid,
            $this->name,
            $exitStatus,
            $this->lastRun,
            $this->nextRun
        );

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
            if ($this->interval) {
                $this->nextRun = $this->nextRun + $this->interval;
            }
            if ($this->frequency) {
                if ($this->nextRun - $this->lastRun < $this->frequency) {
                    $this->nextRun = $this->lastRun + $this->frequency;
                }
            }
        }
    }
}
