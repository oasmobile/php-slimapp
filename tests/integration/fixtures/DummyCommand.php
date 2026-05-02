<?php

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Oasis\SlimApp\AbstractParallelCommand;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

class DummyCommand extends AbstractParallelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('dummy:job')->setDescription('dummy command');
        $this->addArgument('a');
        $this->addOption('tt', null, InputOption::VALUE_REQUIRED);
        $this->addOption('idx', null, InputOption::VALUE_REQUIRED);
    }
    
    protected function doExecute(InputInterface $input, OutputInterface $output)
    {
        $a   = $input->getArgument('a');
        $tt  = $input->getOption('tt');
        $idx = $input->getOption('idx');
        minfo('I got a: %s', $a);
        minfo('I got tt: %s', json_encode($tt));
        minfo('I got idx: %d', $idx);
        sleep(5);
        merror("woww");
        
        return self::EXIT_CODE_OK;
    }
}
