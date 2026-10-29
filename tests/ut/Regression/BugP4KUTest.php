<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression;

use Oasis\SlimApp\Tests\Regression\Fixtures\BugReproductionTestCase;
use PHPUnit\Framework\Attributes\DataProvider;

final class BugP4KUTest extends BugReproductionTestCase
{
    /** @return array<string, array{string}> */
    public static function forkCases(): array
    {
        return [
            'parallel_ok' => ['testParallelCommandForkAndWaitSuccess'],
            'parallel_fail' => ['testParallelCommandForkWithChildFailure'],
            'sentinel_once' => ['testSentinelCommandRunOnce'],
            'sentinel_parallel' => ['testSentinelCommandRunParallel'],
        ];
    }

    #[DataProvider('forkCases')]
    public function testOrdinaryForkTestNeedsNoCoverageDriver(string $method): void
    {
        $ini = $this->withoutCoverageIni();
        $environment = ['PHPRC' => $ini, 'PHP_INI_SCAN_DIR' => '', 'COVERAGE_FILE' => ''];
        $preflight = $this->runProcess([
            PHP_BINARY, '-c', $ini, __DIR__ . '/Fixtures/coverage_environment.php',
        ], $environment);
        self::assertSame(0, $preflight['exit'], $preflight['output']);
        self::assertStringContainsString('NO_COVERAGE_DRIVER', $preflight['output']);

        $junit = $this->reports . '/fork.xml';
        $result = $this->runProcess([
            PHP_BINARY, '-c', $ini, $this->repo . '/vendor/bin/phpunit',
            '--configuration', $this->repo . '/phpunit.xml', '--no-coverage',
            '--filter', 'ForkProcessTest::' . $method . '$', '--log-junit', $junit,
            $this->repo . '/tests/ut/ForkProcessTest.php',
        ], $environment);

        self::assertFileExists($junit, $result['output']);
        self::assertStringContainsString($method, (string) file_get_contents($junit));
        self::assertSame(0, $result['exit'], $result['output'] . '\n日志：' . $result['log']);
        self::assertStringNotContainsString('NoCodeCoverageDriver', $result['output']);
        if ($method === 'testParallelCommandForkWithChildFailure') {
            $evidence = $this->runProcess([
                PHP_BINARY, '-c', $ini, __DIR__ . '/Fixtures/fork_failure_evidence.php',
            ], $environment);
            self::assertSame(0, $evidence['exit'], $evidence['output']);
            $failure = json_decode($evidence['output'], true, 512, JSON_THROW_ON_ERROR);
            self::assertSame(255, $failure['exitCode']);
            self::assertStringNotContainsString('NoCodeCoverageDriver', $failure['output']);
            self::assertStringNotContainsString('Fatal error', $failure['output']);
        }
    }

    private function withoutCoverageIni(): string
    {
        $files = [php_ini_loaded_file()];
        $scanned = php_ini_scanned_files();
        if (is_string($scanned)) {
            $files = array_merge($files, preg_split('/,\s*/', trim($scanned)) ?: []);
        }
        $contents = '';
        foreach ($files as $file) {
            if (is_string($file) && $file !== '') {
                $source = file_get_contents($file);
                self::assertIsString($source);
                $contents .= $source . "\n";
            }
        }
        // 保留其它扩展和配置，并让孙进程通过 PHPRC 使用同一环境。
        $contents = preg_replace('/^\s*(?:zend_)?extension\s*=.*(?:pcov|xdebug).*$/mi', '', $contents);
        self::assertIsString($contents);
        $path = $this->work . '/no-coverage.ini';
        file_put_contents($path, $contents . "\npcov.enabled=0\n");

        return $path;
    }
}
