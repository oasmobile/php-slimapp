<?php
/**
 * 合并多个覆盖率文件，输出文本报告。
 *
 * 适配 phpunit/php-code-coverage 14.x（PHPUnit 13）。
 * 使用 Serializer/Unserializer API 替代 raw serialize/unserialize。
 *
 * 用法: php tests/scripts/merge_coverage.php <cov-file1> [cov-file2] ...
 */

declare(strict_types=1);

require_once __DIR__ . '/../../vendor/autoload.php';

use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Driver\Selector;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Report\Text;
use SebastianBergmann\CodeCoverage\Report\Thresholds;
use SebastianBergmann\CodeCoverage\Serialization\Unserializer;

$srcDir = realpath(__DIR__ . '/../../src');

// 手动列出要统计的文件（排除 InitializeProjectCommand 和 src/tests/）
$files = [
    $srcDir . '/AbstractAlertableCommand.php',
    $srcDir . '/AbstractParallelCommand.php',
    $srcDir . '/ConfigParser.php',
    $srcDir . '/ConsoleApplication.php',
    $srcDir . '/NamespaceResolver.php',
    $srcDir . '/SlimApp.php',
    $srcDir . '/SlimAppCompilerPass.php',
    $srcDir . '/BuiltInCommands/ClearCacheCommand.php',
    $srcDir . '/BuiltInCommands/ValidateServicesCommand.php',
    $srcDir . '/SentinelCommand/CommandConfiguration.php',
    $srcDir . '/SentinelCommand/CommandRunner.php',
    $srcDir . '/SentinelCommand/DaemonSentinelCommand.php',
];

// 创建 filter 并注册目标文件
$filter = new Filter();
foreach ($files as $f) {
    if (file_exists($f)) {
        $filter->includeFile($f);
    }
}

// 创建基础 CodeCoverage 对象用于合并
$merged = new CodeCoverage((new Selector())->forLineCoverage($filter), $filter);

$unserializer = new Unserializer();

foreach ($argv as $i => $file) {
    if ($i === 0) {
        continue;
    }
    if (!file_exists($file)) {
        continue;
    }

    try {
        $data = $unserializer->unserialize($file);
        $covData = $data['codeCoverage'];
        $basePath = $data['basePath'] ?? '';

        // 将相对路径转为绝对路径（Unserializer 返回的路径是相对于 basePath 的）
        if ($basePath !== '') {
            foreach ($covData->coveredFiles() as $relFile) {
                // 跳过已经是绝对路径的文件
                if (str_starts_with($relFile, '/')) {
                    continue;
                }
                $absFile = $basePath . '/' . $relFile;
                $covData->renameFile($relFile, $absFile);
            }
        }

        // 从反序列化数据重建 CodeCoverage 对象
        $itemFilter = new Filter();
        foreach ($files as $f) {
            if (file_exists($f)) {
                $itemFilter->includeFile($f);
            }
        }
        $itemCoverage = new CodeCoverage(
            (new Selector())->forLineCoverage($itemFilter),
            $itemFilter,
        );
        $itemCoverage->setData($covData);
        $itemCoverage->setTests($data['testResults']);
        $merged->merge($itemCoverage);
    } catch (\Throwable $e) {
        fwrite(STDERR, "Warning: could not load $file: " . $e->getMessage() . "\n");
    }
}

// 输出文本报告
$report = new Text(Thresholds::from(50, 90));
echo $report->process($merged->getReport(), false);

// 输出目标文件覆盖率摘要
$directory = $merged->getReport();
$totalLines   = $directory->numberOfExecutableLines();
$coveredLines = $directory->numberOfExecutedLines();

echo "\n";
echo sprintf(
    "目标文件覆盖率: %.2f%% (%d/%d lines)\n",
    $totalLines > 0 ? ($coveredLines / $totalLines * 100) : 0,
    $coveredLines,
    $totalLines,
);
