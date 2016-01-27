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
        $this->setName('dummy:job')->setDescription('dummy command');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output)
    {
        //mnotice("I'm started, my pid = %d", getmypid());
        $a = [1, 2, 4, 8, 16, 32];
        $k = array_search(8, $a);
        array_splice($a, $k, 1);
        //var_dump($a);

        //usleep(10000);
        return self::EXIT_CODE_RESTART;

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
