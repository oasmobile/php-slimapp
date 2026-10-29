<?php
declare(strict_types=1);

require getenv('REPRO_REPO_ROOT') . '/vendor/autoload.php';
if (!function_exists('pcntl_fork') || !function_exists('pcntl_waitpid')) {
    throw new RuntimeException('复现环境必须提供 pcntl');
}
if (extension_loaded('xdebug') || (extension_loaded('pcov') && ini_get('pcov.enabled') === '1')) {
    throw new RuntimeException('复现环境仍有启用的覆盖率驱动');
}
echo "NO_COVERAGE_DRIVER\n";
