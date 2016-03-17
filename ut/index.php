<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-03-17
 * Time: 20:24
 */
use Oasis\SlimApp\SlimApp;

require_once __DIR__ . "/bootstrap.php";

mdebug(getcwd());
SlimApp::app()->getHttpKernel()->run();
