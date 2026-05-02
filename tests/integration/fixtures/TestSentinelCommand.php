<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Integration\Fixtures;

use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class TestSentinelCommand extends DaemonSentinelCommand
{
    protected function configure(): void
    {
        parent::configure();
        $this->setName('test:daemon');
    }
}
