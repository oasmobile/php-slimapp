<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-10
 * Time: 15:07
 */

namespace Oasis\SlimApp\tests;

use Oasis\SlimApp\AbstractParallelCommand;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class DummyCommand extends AbstractParallelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('dummy')->setDescription('dummy command');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output)
    {
        mdebug("message");
        return -1;
        //minfo("message");
        //mnotice("message");
        //mwarning("message");
        //merror("message");
        //mcritical("message");
        //malert("message");
        //memergency("message");
    }
}
