#! /usr/local/bin/php
<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 14:40
 */
namespace Oasis\SlimApp;

use Oasis\SlimApp\tests\TestAppConfig;

require_once __DIR__ . "/vendor/autoload.php";

SlimApp::app()->init(__DIR__ . "/ut", new TestAppConfig());
SlimApp::app()->getConsoleApplication()->run();
