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
    /** @var  int */
    protected $parallelIndex;
    
    protected $name;
    /** @var  InputInterface */
    protected $input;
    /** @var  OutputInterface */
    protected $output;
    
    protected $once      = false;
    protected $interval  = 0;
    protected $frequency = 0;
    
    protected $lastRun      = 0;
    protected $nextRun      = 0;
    protected $currentPid   = 0;
    protected $alert        = true;
    protected $stopped      = false;
    protected $traceEnabled = false;
    
    public function __construct(Application $application,
                                $parallelIndex,
                                array $command,
                                OutputInterface $output,
                                $traceEnabled = false)
    {
        $this->application   = $application;
        $this->parallelIndex = $parallelIndex;
        
        $this->output = $output;
        
        $this->name = $command['name'];
        $args       = ['command' => $this->name];
        $args       = array_merge($args, $command['args']);
        //mdebug("args = %s", json_encode($args));
        $args = array_map(
            function ($argValue) {
                if ($argValue === "\$PARALLEL_INDEX") {
                    return $this->parallelIndex;
                }
                else {
                    return $argValue;
                }
            },
            $args
        );
        //mdebug("args = %s", json_encode($args));
        $this->input = new ArrayInput($args);
        
        $this->once      = $command['once'];
        $this->interval  = $command['interval'];
        $this->frequency = $command['frequency'];
        $this->alert     = $command['alert'];
        
        $this->nextRun      = time();
        $this->traceEnabled = $traceEnabled;
    }
    
    public function shouldStartNextRunWhenNotFinished()
    {
        if (!$this->frequency || $this->once) {
            return false;
        }
        
        if ($this->lastRun + $this->frequency <= time()) {
            //\mnotice("will start early: %d + %d <= %d", $this->lastRun, $this->frequency, time());
            
            return true;
        }
        else {
            return false;
        }
    }
    
    /**
     * clones an early runner when frequency is reached before current run finishes
     */
    public function cloneEarlyRunner()
    {
        $ret          = clone $this;
        $ret->nextRun = time();
        $this->once   = true;
        //\mdebug('Cloned early runner for process [%d]', $this->currentPid);
        
        return $ret;
    }
    
    public function __clone()
    {
        $this->lastRun    = 0;
        $this->nextRun    = 0;
        $this->currentPid = 0;
    }
    
    public function onProcessExit($exitStatus, $pid)
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
            if ($this->interval) {
                $this->nextRun = $this->nextRun + $this->interval;
            }
            //if ($this->frequency) {
            //    if ($this->nextRun - $this->lastRun < $this->frequency) {
            //        $this->nextRun = $this->lastRun + $this->frequency;
            //    }
            //}
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
        }
        else {
            $this->lastRun    = $this->nextRun;
            $this->currentPid = $pid;
            //\mdebug("Started process %d", $pid);
            
            return $pid;
        }
    }
}
