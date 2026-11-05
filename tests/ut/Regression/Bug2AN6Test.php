<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression;

use Oasis\SlimApp\Tests\Regression\Fixtures\BugReproductionTestCase;
use Oasis\SlimApp\Tests\Regression\Fixtures\GeneratedProject;

final class Bug2AN6Test extends BugReproductionTestCase
{
    public function testGeneratedOrmFactoryCreatesAnEntityManager(): void
    {
        GeneratedProject::create($this->work, true, false);
        $result = $this->runProcess($this->phpFixture('generated_orm.php', $this->work));

        self::assertStringContainsString('GENERATED_FACTORY_READY', $result['output'], $result['log']);
        self::assertSame(0, $result['exit'], $result['output'] . '\n日志：' . $result['log']);
        self::assertStringContainsString('ENTITY_MANAGER_CREATED', $result['output']);
    }
}
