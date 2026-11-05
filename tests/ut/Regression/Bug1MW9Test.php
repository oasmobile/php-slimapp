<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression;

use Oasis\SlimApp\Tests\Regression\Fixtures\BugReproductionTestCase;
use PHPUnit\Framework\Attributes\DataProvider;
use Symfony\Component\Filesystem\Filesystem;

final class Bug1MW9Test extends BugReproductionTestCase
{
    /** @return array<string, array{string, string, bool}> */
    public static function commandOutcomes(): array
    {
        return [
            '成功及预期业务失败对照' => ['all_ok', 'merge_coverage.php', true],
            'PHPUnit失败' => ['phpunit_failure', 'phpunit', false],
            'parallel异常' => ['parallel_ok_failure', 'parallel_command_test.php parallel_ok', false],
            'parallel_fail非预期错误' => ['parallel_fail_failure', 'parallel_command_test.php parallel_fail', false],
            'sentinel_once异常' => ['sentinel_once_failure', 'sentinel_command_test.php sentinel_once', false],
            'sentinel_parallel异常' => ['sentinel_parallel_failure', 'sentinel_command_test.php sentinel_parallel', false],
        ];
    }

    #[DataProvider('commandOutcomes')]
    public function testCoverageScriptPreservesUnexpectedFailures(string $scenario, string $stage, bool $success): void
    {
        $php = $this->work . '/php-fixture';
        (new Filesystem())->copy(__DIR__ . '/Fixtures/coverage_php.php', $php);
        chmod($php, 0755);
        $trace = $this->reports . '/coverage-commands.log';
        $result = $this->runProcess(['bash', $this->repo . '/tests/run_all_coverage.sh'], [
            'PHP' => $php, 'REPRO_SCENARIO' => $scenario, 'REPRO_TRACE' => $trace,
        ]);

        self::assertFileExists($trace, $result['output']);
        self::assertStringContainsString($stage, (string) file_get_contents($trace));
        if ($success) {
            self::assertSame(0, $result['exit'], $result['output']);
            self::assertStringContainsString('MERGE_FIXTURE_OK', $result['output']);
        } else {
            self::assertNotSame(0, $result['exit'], $result['output'] . '\n日志：' . $result['log']);
        }
    }
}
