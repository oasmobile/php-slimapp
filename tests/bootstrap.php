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
