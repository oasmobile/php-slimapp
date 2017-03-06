<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-02
 * Time: 14:31
 */

namespace Oasis\SlimApp\SentinelCommand;

use Oasis\SlimApp\AbstractAlertableCommand;
use Oasis\SlimApp\ConsoleApplication;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Yaml\Yaml;

/**
 * Class AbstractDaemonSentinelCommand
 *
 * @deprecated
 * @package Oasis\SlimApp\SentinelCommand
 */
abstract class AbstractDaemonSentinelCommand extends AbstractAlertableCommand
{
    protected $runningProcesses = [];
    
    protected function configure()
    {
        parent::configure();
        $this->setDescription("Runs as sentinel for a list of daemon commands");
        $this->addArgument('file', InputArgument::REQUIRED, "a config file holding daemon commands info");
    }
    
    protected function execute(InputInterface $input, OutputInterface $output)
    {
        $filename = $input->getArgument('file');
        if (!is_readable($filename)) {
            $output->writeln(
                sprintf(
                    "<error>File %s is not readable!</error>",
                    $filename
                )
            );
        }
        $config    = Yaml::parse(file_get_contents($filename));
        $configs   = [$config];
        $configDef = new CommandConfiguration();
        
        $processor = new Processor();
        $processed = $processor->processConfiguration($configDef, $configs);
        
        $this->runningProcesses = [];
        foreach ($processed['commands'] as $command) {
            $parallel    = $command['parallel'];
            $application = $this->getApplication();
            if ($application instanceof ConsoleApplication
                && is_string($parallel)
                && preg_match('#(%([^%].*?)%)#', $parallel, $matches, 0)
            ) {
                $key         = $matches[2];
                $replacement = $application->getSlimapp()->getParameter($key);
                if ($replacement === null) {
                    throw new \InvalidArgumentException("Cannot get config value $key");
                }
                $parallel = $replacement;
            }
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
    
    protected function waitForBackgroundProcesses()
    {
        //$lastMemory = memory_get_usage(true);
        while (true) {
            //$memory = memory_get_usage(true);
            //if ($memory != $lastMemory) {
            //    echo(
            //        sprintf("memory change: %d, from %d to %d", $memory - $lastMemory, $lastMemory, $memory)
            //        . PHP_EOL
            //    );
            //}
            //$lastMemory = $memory;
            
            pcntl_signal_dispatch();
            
            $status = 0;
            $pid    = pcntl_waitpid(-1, $status, WNOHANG);
            
            if ($pid == 0) { // no child process has quit
                usleep(200 * 1000);
            }
            else if ($pid > 0) { // child process with pid = $pid exits
                $exitStatus = pcntl_wexitstatus($status);
                $runner     = $this->runningProcesses[$pid];
                if (!$runner instanceof CommandRunner) {
                    throw new \LogicException("Cannot find command runner for process pid = %d", $pid);
                }
                unset($this->runningProcesses[$pid]);
                $runner->onProcessExit($exitStatus, $pid);
                $newPid = $runner->run();
                if ($newPid > 0) {
                    $this->runningProcesses[$newPid] = $runner;
                }
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
    }
}
