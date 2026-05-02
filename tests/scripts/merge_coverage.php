<?php
/**
 * 合并多个覆盖率文件，输出文本报告。
 */

require_once __DIR__ . '/../../vendor/autoload.php';

use SebastianBergmann\CodeCoverage\CodeCoverage;
use SebastianBergmann\CodeCoverage\Filter;
use SebastianBergmann\CodeCoverage\Report\Text;

$srcDir = realpath(__DIR__ . '/../../src');

// 手动列出要统计的文件（排除 InitializeProjectCommand 和 src/tests/）
$filter = new Filter();
$files = [
    $srcDir . '/AbstractAlertableCommand.php',
    $srcDir . '/AbstractParallelCommand.php',
    $srcDir . '/ConsoleApplication.php',
    $srcDir . '/SlimApp.php',
    $srcDir . '/SlimAppCompilerPass.php',
    $srcDir . '/BuiltInCommands/ClearCacheCommand.php',
    $srcDir . '/BuiltInCommands/ValidateServicesCommand.php',
    $srcDir . '/SentinelCommand/AbstractDaemonSentinelCommand.php',
    $srcDir . '/SentinelCommand/CommandConfiguration.php',
    $srcDir . '/SentinelCommand/CommandRunner.php',
    $srcDir . '/SentinelCommand/DaemonSentinelCommand.php',
];
foreach ($files as $f) {
    $filter->addFileToWhitelist($f);
}

$merged = new CodeCoverage(null, $filter);

foreach ($argv as $i => $file) {
    if ($i === 0) continue;
    if (!file_exists($file)) continue;

    $content = file_get_contents($file);

    if (strpos($content, '<?php') === 0) {
        $coverage = null;
        include $file;
        if ($coverage instanceof CodeCoverage) {
            $merged->merge($coverage);
        }
    } else {
        $data = @unserialize($content);
        if ($data instanceof CodeCoverage) {
            $merged->merge($data);
        }
    }
}

$report = new Text(50, 90, false, false);
echo $report->process($merged, true); // showOnlySummary=true 不行，还是手动算

// 手动计算只包含目标文件的覆盖率
$data = $merged->getData();
$totalLines = 0;
$coveredLines = 0;
$totalMethods = 0;
$coveredMethods = 0;

foreach ($files as $file) {
    $realFile = realpath($file);
    if (!$realFile || !isset($data[$realFile])) continue;

    foreach ($data[$realFile] as $line => $info) {
        if ($info === null) continue; // not executable
        $totalLines++;
        if (is_array($info) ? count($info) > 0 : $info > 0) {
            $coveredLines++;
        }
    }
}

echo "\n";
echo sprintf("目标文件覆盖率: %.2f%% (%d/%d lines)\n", 
    $totalLines > 0 ? ($coveredLines / $totalLines * 100) : 0,
    $coveredLines, $totalLines
);
