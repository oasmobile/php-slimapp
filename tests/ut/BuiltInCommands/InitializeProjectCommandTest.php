<?php

namespace Oasis\SlimApp\Tests\BuiltInCommands;

use Oasis\SlimApp\BuiltInCommands\InitializeProjectCommand;

class InitializeProjectCommandTest extends \PHPUnit\Framework\TestCase
{
    public function testCommandNameAndDescription()
    {
        $command = new InitializeProjectCommand();
        $this->assertEquals('slimapp:project:init', $command->getName());
        $this->assertNotEmpty($command->getDescription());
    }

    public function testCommandHasProjectRootOption()
    {
        $command = new InitializeProjectCommand();
        $def     = $command->getDefinition();
        $this->assertTrue($def->hasOption('project-root'));
        $this->assertEquals('p', $def->getOption('project-root')->getShortcut());
    }
}
