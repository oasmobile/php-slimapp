<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-03-17
 * Time: 20:24
 */

use Composer\Autoload\ClassLoader;
use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\tests\TestAppConfig;
use Symfony\Component\Debug\Debug;

/** @var ClassLoader $loader */
$loader = require_once __DIR__ . "/../vendor/autoload.php";
$loader->addPsr4("Oasis\\SlimApp\\Ut\\", __DIR__);

SlimApp::app()->init(__DIR__ . "/", new TestAppConfig());

//Debug::enable();
