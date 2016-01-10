<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-10
 * Time: 15:07
 */

namespace Oasis\SlimApp\tests;

use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class DummyCommand extends Command
{
    protected function configure()
    {
        $this->setName('dummy')->setDescription('dummy command');
    }

    protected function execute(InputInterface $input, OutputInterface $output)
    {
        mdebug("message");
        minfo("message");
        mnotice("message");
        mwarning("message");
        merror("message");
        mcritical("message");
        malert("message");
        memergency("message");
    }
    
}
