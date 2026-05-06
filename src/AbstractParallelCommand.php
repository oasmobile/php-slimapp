<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

use Symfony\Component\Console\Helper\QuestionHelper;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Question\ConfirmationQuestion;

abstract class AbstractParallelCommand extends AbstractAlertableCommand
{
    private int $parallelCount = 0;
    /** @var int[] */
    private array $pids = [];
    private bool $isFailed = false;

    protected function getParallelCount(): int
    {
        return $this->parallelCount;
    }

    protected function configure(): void
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

    protected function execute(InputInterface $input, OutputInterface $output): int
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
                assert($helper instanceof QuestionHelper);
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

    protected function waitForBackground(InputInterface $input, OutputInterface $output): int
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
            elseif ($pid > 0) { // child process with pid = $pid exits
                $exitStatus = pcntl_wexitstatus($status);
                if ($exitStatus === false) {
                    // @codeCoverageIgnoreStart
                    throw new \RuntimeException("Failed to get exit status for process $pid");
                    // @codeCoverageIgnoreEnd
                }
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
                    // @codeCoverageIgnoreStart
                    throw new \RuntimeException("Error waiting for process, error = " . pcntl_strerror($errno));
                    // @codeCoverageIgnoreEnd
                }
            }
        }

        return $this->isFailed ? self::EXIT_CODE_COMMON_ERROR : self::EXIT_CODE_OK;
    }

    protected function doFork(InputInterface $input, OutputInterface $output): int
    {
        $pid = pcntl_fork();
        if ($pid < 0) {
            // @codeCoverageIgnoreStart
            $errno = pcntl_get_last_error();
            throw new \RuntimeException("Cannot fork process, error = " . pcntl_strerror($errno));
            // @codeCoverageIgnoreEnd
        }
        elseif ($pid == 0) {
            // @codeCoverageIgnoreStart — child process; covered by tests/scripts/parallel_command_test.php
            $ret = $this->doExecute($input, $output);
            exit($ret);
            // @codeCoverageIgnoreEnd
        }
        else {
            return $pid;
        }
    }

    protected function onChildProcessExit(int $pid, int $exitStatus, InputInterface $input, OutputInterface $output): void
    {
        $key = array_search($pid, $this->pids);
        if ($key !== false) {
            //mdebug("Child process $pid exit with code: %x", $exitStatus);
            array_splice($this->pids, (int)$key, 1);

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
        } else {
            mwarning("Un-managed child process $pid exit with code: %d", $exitStatus);
        }
    }

    abstract protected function doExecute(InputInterface $input, OutputInterface $output): int;
}
