<?php
/**
 * 集成测试：HTTP 入口
 *
 * 用法: php -S localhost:8080 tests/integration/http.php
 */

use Oasis\SlimApp\SlimApp;

require_once __DIR__ . '/bootstrap.php';

mdebug(getcwd());
SlimApp::app()->getHttpKernel()->run();
