<?php

namespace Oasis\SlimApp\Tests\SentinelCommand;

use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;

class DaemonSentinelCommandTest extends \PHPUnit_Framework_TestCase
{
    public function testIsInstanceOfAbstractDaemonSentinelCommand()
    {
        $command = $this->getMockBuilder(DaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:sentinel'])
                        ->getMock();

        $this->assertInstanceOf(
            'Oasis\\SlimApp\\SentinelCommand\\AbstractDaemonSentinelCommand',
            $command
        );
    }

    public function testInheritsFromAbstractAlertableCommand()
    {
        $command = $this->getMockBuilder(DaemonSentinelCommand::class)
                        ->setConstructorArgs(['test:sentinel'])
                        ->getMock();

        $this->assertInstanceOf(
            'Oasis\\SlimApp\\AbstractAlertableCommand',
            $command
        );
    }
}
