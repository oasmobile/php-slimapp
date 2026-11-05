#!/usr/bin/env php
<?php
declare(strict_types=1);

// 作为 PHP 可执行文件替身，只验证 shell 编排的退出状态，不递归运行测试。
$arguments = array_slice($argv, 1);
if (($arguments[0] ?? '') === '-v') {
    echo "PHP coverage orchestration fixture\n";
    exit(0);
}
while (($arguments[0] ?? '') === '-d') {
    array_shift($arguments);
    array_shift($arguments);
}
$script = basename(array_shift($arguments) ?? '');
$case = $arguments[0] ?? '';
$scenario = getenv('REPRO_SCENARIO');
file_put_contents(getenv('REPRO_TRACE'), $script . ' ' . $case . "\n", FILE_APPEND);

if ($script === 'phpunit') {
    $index = array_search('--coverage-php', $arguments, true);
    if ($index === false || !isset($arguments[$index + 1])) {
        throw new RuntimeException('PHPUnit 调用没有指定覆盖率产物');
    }
    file_put_contents($arguments[$index + 1], 'coverage fixture');
    echo $scenario === 'phpunit_failure' ? "FAIL intentional PHPUnit failure\n" : "OK fixture\n";
    exit($scenario === 'phpunit_failure' ? 1 : 0);
}
if (in_array($script, ['parallel_command_test.php', 'sentinel_command_test.php'], true)) {
    file_put_contents(getenv('COVERAGE_FILE'), 'coverage fixture');
    if ($scenario === $case . '_failure') {
        fwrite(STDERR, "intentional fork failure: $case\n");
        exit(17);
    }
    exit($case === 'parallel_fail' ? 255 : 0);
}
if ($script === 'merge_coverage.php') {
    echo "MERGE_FIXTURE_OK\n";
    exit(0);
}
throw new RuntimeException('未预期的 PHP 调用：' . $script);
