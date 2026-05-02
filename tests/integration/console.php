#!/usr/bin/env php
<?php
/**
 * 集成测试：控制台入口
 *
 * 用法: php tests/integration/console.php [command] [args...]
 * 示例: php tests/integration/console.php dummy:job hello --tt=world --parallel=1
 *       php tests/integration/console.php test:daemon tests/integration/config/sentinel.yml
 */

use Oasis\Mlib\Logging\ConsoleHandler;
use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;

require_once __DIR__ . '/../../vendor/autoload.php';

(new ConsoleHandler())->install();

SlimApp::app()->init(__DIR__ . '/config', new TestAppConfig());
SlimApp::app()->getConsoleApplication()->run();
