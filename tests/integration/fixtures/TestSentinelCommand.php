<?php

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class TestSentinelCommand extends DaemonSentinelCommand
{
    protected function configure()
    {
        parent::configure();
        $this->setName('test:daemon');
    }
}
