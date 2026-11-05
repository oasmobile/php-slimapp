<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression;

use Oasis\SlimApp\Tests\Regression\Fixtures\BugReproductionTestCase;
use Oasis\SlimApp\Tests\Regression\Fixtures\GeneratedProject;

final class BugGH7ATest extends BugReproductionTestCase
{
    public function testGeneratedBootstrapCanRunAMinimalTest(): void
    {
        GeneratedProject::create($this->work, false, true);
        $junit = $this->reports . '/generated-project.xml';
        $result = $this->runProcess([
            PHP_BINARY, $this->repo . '/vendor/bin/phpunit', '--no-configuration', '--no-coverage',
            '--bootstrap', $this->work . '/ut/bootstrap.php', '--log-junit', $junit,
            __DIR__ . '/Fixtures/GeneratedSmokeCase.php',
        ]);

        self::assertSame(0, $result['exit'], $result['output'] . '\n日志：' . $result['log']);
        self::assertFileExists($junit);
        self::assertStringContainsString('testBootstrapReachedTheTest', (string) file_get_contents($junit));
    }
}
