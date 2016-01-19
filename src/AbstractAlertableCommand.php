<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-20
 * Time: 00:59
 */

namespace Oasis\SlimApp;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

class AbstractAlertableCommand extends Command
{
    protected function configure()
    {
        $this->addOption('alert', null, InputOption::VALUE_NONE, 'trigger alert when exception is thrown');
    }

    public function run(InputInterface $input, OutputInterface $output)
    {
        try {
            return parent::run($input, $output);
        } catch (\Exception $e) {
            if ($input->getOption('alert')) {
                mtrace($e, "Exception while running command " . $this->getName(), 'alert');
            }

            throw $e;
        }
    }

}
