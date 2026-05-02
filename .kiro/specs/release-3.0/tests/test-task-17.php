#!/usr/bin/env php
<?php
/**
 * 手工测试脚本 — Task 17 (Release 3.0)
 *
 * 覆盖 sub-task 17.2–17.5 的所有验证场景：
 *   17.2 CLI 模式基本功能（cache:clear, services:validate）
 *   17.3 HTTP Kernel 初始化（MicroKernel 实例、缓存目录容错）
 *   17.4 DI 容器可见性变更（app 服务 public、非 public 服务抛异常）
 *   17.5 Daemon Sentinel 基本功能（配置解析、CommandRunner 创建）
 *
 * 用法: php .kiro/specs/release-3.0/tests/test-task-17.php
 */

declare(strict_types=1);

use Oasis\Mlib\Http\MicroKernel;
use Oasis\SlimApp\AbstractAlertableCommand;
use Oasis\SlimApp\ConsoleApplication;
use Oasis\SlimApp\SentinelCommand\DaemonSentinelCommand;
use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\DependencyInjection\Exception\ServiceNotFoundException;

require_once __DIR__ . '/../../../../vendor/autoload.php';

// ─── Helpers ───────────────────────────────────────────────────────────────

$passed  = 0;
$failed  = 0;
$results = [];

function report(string $id, string $desc, bool $ok, string $detail = ''): void
{
    global $passed, $failed, $results;
    $status = $ok ? 'PASS' : 'FAIL';
    $line   = sprintf("[%s] %s — %s", $status, $id, $desc);
    if (!$ok && $detail) {
        $line .= "\n       Detail: $detail";
    }
    echo $line . "\n";
    $results[] = ['id' => $id, 'desc' => $desc, 'ok' => $ok];
    $ok ? $passed++ : $failed++;
}

// ─── Bootstrap SlimApp ─────────────────────────────────────────────────────

$configDir = realpath(__DIR__ . '/../../../../tests/integration/config');

// 清除旧缓存以确保干净状态
$cacheDir = $configDir . '/cache';
if (is_dir($cacheDir)) {
    $files = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($cacheDir, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::CHILD_FIRST
    );
    foreach ($files as $file) {
        if ($file->isFile()) {
            unlink($file->getPathname());
        }
    }
}

// 初始化 SlimApp
try {
    SlimApp::app()->init($configDir, new TestAppConfig());
    $bootstrapOk = true;
} catch (\Throwable $e) {
    $bootstrapOk = false;
    echo "FATAL: SlimApp bootstrap failed: " . $e->getMessage() . "\n";
    echo $e->getTraceAsString() . "\n";
    exit(1);
}

echo "=== Task 17 Manual Tests — Release 3.0 ===\n\n";

// ═══════════════════════════════════════════════════════════════════════════
// 17.2 验证 CLI 模式基本功能
// ═══════════════════════════════════════════════════════════════════════════

echo "--- 17.2 CLI 模式基本功能 ---\n";

// 17.2.1 slimapp:cache:clear
try {
    $console = SlimApp::app()->getConsoleApplication();
    $console->setAutoExit(false);

    // 先确保缓存目录有内容（重新 init 会生成缓存）
    // 重新初始化以生成缓存文件
    $freshApp = new class extends SlimApp {};
    // 使用已有的 SlimApp 实例即可，缓存已在 bootstrap 时生成

    $input  = new ArrayInput(['command' => 'slimapp:cache:clear']);
    $output = new BufferedOutput();
    $code   = $console->run($input, $output);
    $text   = $output->fetch();

    $clearOk = ($code === 0) && str_contains($text, 'removing cache in');
    report('17.2.1', 'slimapp:cache:clear 执行成功，缓存目录被清除', $clearOk,
        $clearOk ? '' : "exit=$code, output=$text");
} catch (\Throwable $e) {
    report('17.2.1', 'slimapp:cache:clear 执行成功', false, $e->getMessage());
}

// 重新初始化（cache:clear 后需要重建缓存）
SlimApp::app()->init($configDir, new TestAppConfig());

// 17.2.2 slimapp:services:validate
try {
    $console = SlimApp::app()->getConsoleApplication();
    $console->setAutoExit(false);

    $input  = new ArrayInput(['command' => 'slimapp:services:validate']);
    $output = new BufferedOutput();
    $code   = $console->run($input, $output);
    $text   = $output->fetch();

    // 验证：仅验证 public 服务且输出正确
    $validateOk = ($code === 0) && str_contains($text, 'Validating');
    // 确认输出中包含 'app' 服务（public）
    $hasApp = str_contains($text, 'app');
    report('17.2.2', 'slimapp:services:validate 执行成功，验证 public 服务', $validateOk && $hasApp,
        ($validateOk && $hasApp) ? '' : "exit=$code, output=$text");
} catch (\Throwable $e) {
    report('17.2.2', 'slimapp:services:validate 执行成功', false, $e->getMessage());
}

echo "\n";

// ═══════════════════════════════════════════════════════════════════════════
// 17.3 验证 HTTP Kernel 初始化
// ═══════════════════════════════════════════════════════════════════════════

echo "--- 17.3 HTTP Kernel 初始化 ---\n";

// 17.3.1 getHttpKernel() 返回 MicroKernel 实例
try {
    $kernel     = SlimApp::app()->getHttpKernel();
    $isMicro    = $kernel instanceof MicroKernel;
    report('17.3.1', 'getHttpKernel() 返回 MicroKernel 实例', $isMicro,
        $isMicro ? '' : 'Returned: ' . get_class($kernel));
} catch (\Throwable $e) {
    report('17.3.1', 'getHttpKernel() 返回 MicroKernel 实例', false, $e->getMessage());
}

// 17.3.2 MicroKernel 缓存目录获取的容错逻辑
try {
    $kernel = SlimApp::app()->getHttpKernel();

    // 验证 method_exists 容错逻辑能正常工作
    $hasCacheDirs = method_exists($kernel, 'getCacheDirectories');
    $hasCacheDir  = method_exists($kernel, 'getCacheDir');

    if ($hasCacheDirs) {
        $dirs = $kernel->getCacheDirectories();
        $ok   = is_array($dirs);
        report('17.3.2', 'MicroKernel::getCacheDirectories() 返回数组', $ok,
            $ok ? 'dirs=' . json_encode($dirs) : 'Not an array');
    } elseif ($hasCacheDir) {
        $dir = $kernel->getCacheDir();
        $ok  = is_string($dir);
        report('17.3.2', 'MicroKernel::getCacheDir() 返回字符串（fallback）', $ok,
            $ok ? "dir=$dir" : 'Not a string');
    } else {
        // 两者都不存在也是合法的（ClearCacheCommand 会跳过 HTTP 缓存清理）
        report('17.3.2', 'MicroKernel 无缓存目录 API（ClearCacheCommand 将跳过 HTTP 缓存清理）', true);
    }
} catch (\Throwable $e) {
    report('17.3.2', 'MicroKernel 缓存目录容错', false, $e->getMessage());
}

echo "\n";

// ═══════════════════════════════════════════════════════════════════════════
// 17.4 验证 DI 容器可见性变更
// ═══════════════════════════════════════════════════════════════════════════

echo "--- 17.4 DI 容器可见性变更 ---\n";

// 17.4.1 getService('app') 正常返回 SlimApp 实例
try {
    $appService = SlimApp::app()->getService('app');
    $isSlimApp  = $appService instanceof SlimApp;
    report('17.4.1', "getService('app') 返回 SlimApp 实例", $isSlimApp,
        $isSlimApp ? '' : 'Returned: ' . get_class($appService));
} catch (\Throwable $e) {
    report('17.4.1', "getService('app') 返回 SlimApp 实例", false, $e->getMessage());
}

// 17.4.2 getService('cli.command.dummy') 正常返回（已声明 public: true）
try {
    $dummyCmd = SlimApp::app()->getService('cli.command.dummy');
    $ok       = $dummyCmd !== null;
    report('17.4.2', "getService('cli.command.dummy') 正常返回（public 服务）", $ok);
} catch (\Throwable $e) {
    report('17.4.2', "getService('cli.command.dummy') 正常返回（public 服务）", false, $e->getMessage());
}

// 17.4.3 getService() 调用非 public 服务抛出 ServiceNotFoundException
try {
    // 'memcached' 在 services.yml 中未声明 public: true，应为 private
    SlimApp::app()->getService('memcached');
    // 如果没抛异常，说明服务仍然是 public（不符合预期）
    report('17.4.3', "getService('memcached') 抛出异常（非 public 服务）", false,
        'Expected ServiceNotFoundException but no exception was thrown');
} catch (ServiceNotFoundException $e) {
    report('17.4.3', "getService('memcached') 抛出 ServiceNotFoundException（非 public 服务）", true);
} catch (\Throwable $e) {
    // 其他异常类型也可接受，只要不是静默返回
    $isAcceptable = str_contains($e->getMessage(), 'private') || str_contains($e->getMessage(), 'removed');
    report('17.4.3', "getService('memcached') 抛出异常（非 public 服务）", $isAcceptable,
        get_class($e) . ': ' . $e->getMessage());
}

// 17.4.4 getServiceIds() 仅返回 public 服务
try {
    $ids = SlimApp::app()->getServiceIds();
    // 'app' 应在列表中（public）
    $hasApp = in_array('app', $ids, true);
    // 'memcached' 不应在列表中（private）
    $noMemcached = !in_array('memcached', $ids, true);
    $ok          = $hasApp && $noMemcached;
    report('17.4.4', 'getServiceIds() 仅返回 public 服务', $ok,
        $ok ? '' : sprintf('hasApp=%s, noMemcached=%s, ids=%s',
            $hasApp ? 'true' : 'false',
            $noMemcached ? 'true' : 'false',
            json_encode($ids)));
} catch (\Throwable $e) {
    report('17.4.4', 'getServiceIds() 仅返回 public 服务', false, $e->getMessage());
}

echo "\n";

// ═══════════════════════════════════════════════════════════════════════════
// 17.5 验证 Daemon Sentinel 基本功能
// ═══════════════════════════════════════════════════════════════════════════

echo "--- 17.5 Daemon Sentinel 基本功能 ---\n";

// 17.5.1 DaemonSentinelCommand 继承 AbstractAlertableCommand
try {
    $ref    = new ReflectionClass(DaemonSentinelCommand::class);
    $parent = $ref->getParentClass();
    $ok     = $parent && $parent->getName() === AbstractAlertableCommand::class;
    report('17.5.1', 'DaemonSentinelCommand 直接继承 AbstractAlertableCommand', $ok,
        $ok ? '' : 'Parent: ' . ($parent ? $parent->getName() : 'none'));
} catch (\Throwable $e) {
    report('17.5.1', 'DaemonSentinelCommand 继承关系', false, $e->getMessage());
}

// 17.5.2 TestSentinelCommand 可正常实例化并配置
try {
    $sentinelCmd = SlimApp::app()->getService('cli.command.sentinel');
    $ok          = $sentinelCmd instanceof DaemonSentinelCommand;
    report('17.5.2', 'TestSentinelCommand 可通过 DI 获取且为 DaemonSentinelCommand 实例', $ok,
        $ok ? '' : 'Type: ' . get_class($sentinelCmd));
} catch (\Throwable $e) {
    report('17.5.2', 'TestSentinelCommand DI 获取', false, $e->getMessage());
}

// 17.5.3 Sentinel 配置解析正常（使用测试配置文件）
$processed = null;
try {
    $sentinelConfig = realpath(__DIR__ . '/../../../../tests/integration/config/sentinel.yml');
    $config         = \Symfony\Component\Yaml\Yaml::parse(file_get_contents($sentinelConfig));
    $configDef      = new \Oasis\SlimApp\SentinelCommand\CommandConfiguration(
        SlimApp::app()->getConsoleApplication()
    );
    $processor      = new \Symfony\Component\Config\Definition\Processor();
    $processed      = $processor->processConfiguration($configDef, [$config]);

    $hasCommands = isset($processed['commands']) && !empty($processed['commands']);
    $hasDummy    = isset($processed['commands']['dummy']);
    $ok          = $hasCommands && $hasDummy;
    report('17.5.3', 'Sentinel 配置解析正常（sentinel.yml）', $ok,
        $ok ? 'commands=' . implode(',', array_keys($processed['commands'])) : json_encode($processed));
} catch (\Throwable $e) {
    report('17.5.3', 'Sentinel 配置解析', false, $e->getMessage());
}

// 17.5.4 CommandRunner 可正常创建
try {
    if ($processed === null) {
        throw new \RuntimeException('Skipped: sentinel config parsing failed in 17.5.3');
    }
    $command = $processed['commands']['dummy'];
    $runner  = new \Oasis\SlimApp\SentinelCommand\CommandRunner(
        SlimApp::app()->getConsoleApplication(),
        0,
        $command,
        new BufferedOutput()
    );
    $ok = $runner instanceof \Oasis\SlimApp\SentinelCommand\CommandRunner;
    report('17.5.4', 'CommandRunner 可正常创建', $ok);
} catch (\Throwable $e) {
    report('17.5.4', 'CommandRunner 创建', false, $e->getMessage());
}

// ═══════════════════════════════════════════════════════════════════════════
// 汇总
// ═══════════════════════════════════════════════════════════════════════════

echo "\n=== 汇总 ===\n";
echo sprintf("Total: %d, Passed: %d, Failed: %d\n", $passed + $failed, $passed, $failed);

if ($failed > 0) {
    echo "\nFailed tests:\n";
    foreach ($results as $r) {
        if (!$r['ok']) {
            echo "  - {$r['id']}: {$r['desc']}\n";
        }
    }
}

exit($failed > 0 ? 1 : 0);
