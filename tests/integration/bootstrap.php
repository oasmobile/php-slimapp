<?php
/**
 * 集成测试环境 bootstrap
 *
 * 初始化 SlimApp，配置目录指向 tests/integration/config/
 */

use Composer\Autoload\ClassLoader;
use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;

/** @var ClassLoader $loader */
$loader = require_once __DIR__ . '/../../vendor/autoload.php';

SlimApp::app()->init(__DIR__ . '/config', new TestAppConfig());
