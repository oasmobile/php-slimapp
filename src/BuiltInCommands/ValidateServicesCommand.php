<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands;

use Oasis\SlimApp\ConsoleApplication;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class ValidateServicesCommand extends Command
{
    protected function configure(): void
    {
        parent::configure();

        $this->setName('slimapp:services:validate');
        $this->setDescription("Validate all services configured for slimapp.");
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $console = $this->getApplication();
        assert($console instanceof ConsoleApplication);
        $slimapp = $console->getSlimapp();
        assert($slimapp instanceof \Oasis\SlimApp\SlimApp);

        $ids = $slimapp->getServiceIds();
        foreach ($ids as $id) {
            try {
                $output->writeln("Validating <comment>$id</comment> ...");
                $slimapp->getService($id);
                $output->writeln("<info>Done.</info>");
            } catch (\Exception $e) {
                $output->writeln(
                    "<error>Service $id is misconfigured, exception = \n" . $e->getTraceAsString() . "</error>"
                );
            }
        }

        return 0;
    }
}
