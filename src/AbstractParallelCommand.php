<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-11
 * Time: 22:01
 */

namespace Oasis\SlimApp;

use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\ConfirmationQuestion;

abstract class AbstractParallelCommand extends AbstractAlertableCommand
{
    private $parallelCount = 0;
    private $pids          = [];
    private $isFailed      = false;

    /**
     * @return int
     */
    protected function getParallelCount()
    {
        return $this->parallelCount;
    }

    protected function configure()
    {
        parent::configure();

        $this->addOption(
            'parallel',
            null,
            InputOption::VALUE_REQUIRED,
            "Num of parallel process",
            1
        );
        $this->addOption(
            'no-overflow-confirm',
            null,
            InputOption::VALUE_NONE,
            "whether to confirm if parallel given is too large ( > 10)"
        );
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $this->parallelCount = intval($input->getOption('parallel'));
        if ($this->parallelCount < 1) {
            throw new \InvalidArgumentException(
                "Num of parallel process should be at least 1, {$this->parallelCount} got"
            );
        }
        if ($this->parallelCount > 10) {
            if ($input->getOption('no-overflow-confirm') !== true) {
                $helper   = $this->getHelper('question');
                $question = new ConfirmationQuestion(
                    "Num of parallel processes is set to {$this->parallelCount}, confirm?", false
                );

                if (!$helper->ask($input, $output, $question)) {
                    return -1;
                }
            }
        }

        if ($this->parallelCount == 1) {
            return $this->doExecute($input, $output);
        }

        $this->isFailed = false;
        $this->pids     = [];
        for ($i = 0; $i < $this->parallelCount; ++$i) {
            $pid          = $this->doFork($input, $output);
            $this->pids[] = $pid;
        }

        mdebug("Child processes all started, pids: %s", implode(",", $this->pids));

        return $this->waitForBackground($input, $output);
    }

    protected function waitForBackground(InputInterface $input, OutputInterface $output)
    {
        $lastMemory = memory_get_usage(true);
        while (true) {
            $memory = memory_get_usage(true);
            if ($memory != $lastMemory) {
                $output->writeln(
                    sprintf("memory change: %d, from %d to %d", $memory - $lastMemory, $lastMemory, $memory)
                );
            }
            $lastMemory = $memory;

            $status = 0;
            $pid    = pcntl_waitpid(-1, $status, WNOHANG);

            if ($pid == 0) { // no child process has quit
                //usleep(200 * 1000);
            }
            else if ($pid > 0) { // child process with pid = $pid exits
                $exitStatus = pcntl_wexitstatus($status);
                $this->onChildProcessExit($pid, $exitStatus, $input, $output);
            }
            else { // error
                $errno = pcntl_get_last_error();
                if ($errno == PCNTL_ECHILD) {
                    // all children finished
                    mdebug("No more BackgroundProcessRunner children, continue ...");
                    break;
                }
                else {
                    // some other error
                    throw new \RuntimeException("Error waiting for process, error = " . pcntl_strerror($errno));
                }
            }
        }

        return $this->isFailed ? self::EXIT_CODE_COMMON_ERROR : self::EXIT_CODE_OK;
    }

    protected function doFork(InputInterface $input, OutputInterface $output)
    {
        $pid = pcntl_fork();
        if ($pid < 0) {
            $errno = pcntl_get_last_error();
            throw new \RuntimeException("Cannot fork process, error = " . pcntl_strerror($errno));
        }
        elseif ($pid == 0) {
            // in child process
            $ret = $this->doExecute($input, $output);
            exit(is_numeric($ret) ? $ret : 0);
        }
        else {
            return $pid;
        }
    }

    protected function onChildProcessExit($pid, $exitStatus, InputInterface $input, OutputInterface $output)
    {
        if (($key = array_search($pid, $this->pids)) !== false) {
            //mdebug("Child process $pid exit with code: %x", $exitStatus);
            array_splice($this->pids, $key, 1);

            switch ($exitStatus) {
                case self::EXIT_CODE_RESTART:
                    //mdebug("Child process $pid requires restart");
                    $newPid       = $this->doFork($input, $output);
                    $this->pids[] = $newPid;
                    mdebug("Child process $pid restarted, new pid = $newPid");
                    break;
                case self::EXIT_CODE_OK:
                    break;
                default:
                    $this->isFailed = true;
            }
        }
        else {
            mwarning("Un-managed child process $pid exit with code: %d", $exitStatus);
        }
    }

    abstract protected function doExecute(InputInterface $input, OutputInterface $output);
}
