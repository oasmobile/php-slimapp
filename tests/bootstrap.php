<?php

// Suppress PHPUnit 5.7 mock compatibility warnings on PHP 7.4
// (ReflectionType::__toString() deprecation in mock generation)
$previousHandler = set_error_handler(function ($errno, $errstr) use (&$previousHandler) {
    if ($errno === E_DEPRECATED && strpos($errstr, 'ReflectionType::__toString()') !== false) {
        return true;
    }
    if ($previousHandler) {
        return call_user_func_array($previousHandler, func_get_args());
    }
    return false;
});

require_once __DIR__ . '/../vendor/autoload.php';

// 抑制测试过程中 oasis/logging 的全局日志输出（mtrace/malert/mwarning/mdebug 等）
// 必须先安装一个 handler（否则 MLogging::log 会自动安装 ConsoleHandler），再设最高级别
$nullHandler = new Monolog\Handler\NullHandler(Monolog\Logger::DEBUG);
Oasis\Mlib\Logging\MLogging::addHandler($nullHandler, 'test_null');
Oasis\Mlib\Logging\MLogging::setMinLogLevel(Monolog\Logger::EMERGENCY + 1);
