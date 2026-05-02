<?php
declare(strict_types=1);

require_once __DIR__ . '/../vendor/autoload.php';

// 抑制测试过程中 oasis/logging 的全局日志输出（mtrace/malert/mwarning/mdebug 等）
// 必须先安装一个 handler（否则 MLogging::log 会自动安装 ConsoleHandler），再设最高级别
$nullHandler = new Monolog\Handler\NullHandler(Monolog\Level::Debug);
Oasis\Mlib\Logging\MLogging::addHandler($nullHandler, 'test_null');
Oasis\Mlib\Logging\MLogging::setMinLogLevel(Monolog\Level::Emergency);
