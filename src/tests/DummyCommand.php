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
    }

    protected function doExecute(InputInterface $input, OutputInterface $output)
    {
        $a  = $input->getArgument('a');
        $tt = $input->getOption('tt');
        minfo('I got a: %s', $a);
        minfo('I got tt: %s', json_encode($tt));
        //merror("wow");

        return self::EXIT_CODE_OK;

        //mdebug("message");
        //minfo("message");
        //mnotice("message");
        //mwarning("message");
        //merror("message");
        //mcritical("message");
        ////malert("message");
        ////memergency("message");

        //$s = '';
        //for ($i = 0; $i < 100000; ++$i) {
        //    $s .= str_repeat(' ', pow(2, $i));
        //}
    }
}
