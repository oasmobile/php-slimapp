<?php
declare(strict_types=1);

// 本文件复制到临时生成项目的 vendor/autoload.php。
$loader = require getenv('REPRO_REPO_ROOT') . '/vendor/autoload.php';
$loader->addPsr4('Repro\\Generated\\', dirname(__DIR__) . '/src/');

return $loader;
