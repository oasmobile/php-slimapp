<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-03-28
 * Time: 21:03
 */

namespace Oasis\SlimApp\BuiltInCommands;

use Oasis\SlimApp\ConsoleApplication;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class ValidateServicesCommand extends Command
{
    protected function configure()
    {
        parent::configure();

        $this->setName('slimapp:services:validate');
        $this->setDescription("Validate all services configured for slimapp.");
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        /** @var ConsoleApplication $console */
        $console = $this->getApplication();
        $slimapp = $console->getSlimapp();

        $ids = $slimapp->getServiceIds();
        foreach ($ids as $id) {
            try {
                $output->writeln("Validating <comment>$id</comment> ...");
                $slimapp->getService($id);
                $output->writeln("<info>Done.</info>");
            } catch (\Exception $e) {
                $output->writeln(
                    "<error>Service $id is misconfigured, execption = \n" . $e->getTraceAsString() . "</error>"
                );
            }
        }

    }
}
