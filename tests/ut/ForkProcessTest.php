<?php
/**
 * 通过独立进程测试 pcntl_fork 相关代码。
 *
 * 每个测试启动一个独立 PHP 进程运行脚本，脚本内部 fork。
 * 脚本同时收集覆盖率写入 .cov 文件，由 CoverageCollector listener 合并。
 */

namespace Oasis\SlimApp\Tests;

class ForkProcessTest extends \PHPUnit\Framework\TestCase
{
    private static string $covDir;

    public static function setUpBeforeClass(): void
    {
        self::$covDir = sys_get_temp_dir() . '/slimapp_fork_cov';
        if (!is_dir(self::$covDir)) {
            mkdir(self::$covDir, 0777, true);
        }
    }

    private function runScript($script, $testCase)
    {
        $covFile = self::$covDir . '/' . $testCase . '_' . uniqid() . '.cov';
        $php     = defined('PHP_BINARY') ? PHP_BINARY : 'php';

        // 用当前 PHP 二进制运行脚本
        $cmd = sprintf(
            'COVERAGE_FILE=%s %s %s %s 2>&1',
            escapeshellarg($covFile),
            escapeshellarg($php),
            escapeshellarg(__DIR__ . '/../scripts/' . $script),
            escapeshellarg($testCase)
        );

        $output   = [];
        $exitCode = 0;
        exec($cmd, $output, $exitCode);

        return [
            'exitCode' => $exitCode,
            'output'   => implode("\n", $output),
            'covFile'  => $covFile,
        ];
    }

    // ── AbstractParallelCommand 测试 ──

    public function testParallelCommandForkAndWaitSuccess()
    {
        $result = $this->runScript('parallel_command_test.php', 'parallel_ok');
        $this->assertEquals(0, $result['exitCode'], 'parallel_ok should exit 0. Output: ' . $result['output']);
    }

    public function testParallelCommandForkWithChildFailure()
    {
        $result = $this->runScript('parallel_command_test.php', 'parallel_fail');
        // 子进程返回 EXIT_CODE_COMMON_ERROR，父进程应返回 EXIT_CODE_COMMON_ERROR (0xff = 255)
        $this->assertEquals(255, $result['exitCode'], 'parallel_fail should exit 255. Output: ' . $result['output']);
    }

    // ── DaemonSentinelCommand + CommandRunner.run() 测试 ──

    public function testSentinelCommandRunOnce()
    {
        $result = $this->runScript('sentinel_command_test.php', 'sentinel_once');
        $this->assertEquals(0, $result['exitCode'], 'sentinel_once should exit 0. Output: ' . $result['output']);
    }

    public function testSentinelCommandRunParallel()
    {
        $result = $this->runScript('sentinel_command_test.php', 'sentinel_parallel');
        $this->assertEquals(0, $result['exitCode'], 'sentinel_parallel should exit 0. Output: ' . $result['output']);
    }
}
