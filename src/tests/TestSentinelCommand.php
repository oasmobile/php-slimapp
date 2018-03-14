<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-02-02
 * Time: 14:39
 */

namespace Oasis\SlimApp\tests;

use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class TestSentinelCommand extends DaemonSentinelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('test:daemon');
    }
}
