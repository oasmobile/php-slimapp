<?php
declare(strict_types=1);

use Oasis\SlimApp\Tests\ForkProcessTest;

require getenv('REPRO_REPO_ROOT') . '/vendor/autoload.php';
ForkProcessTest::setUpBeforeClass();
$test = new ForkProcessTest('testParallelCommandForkWithChildFailure');
$result = (new ReflectionMethod(ForkProcessTest::class, 'runScript'))
    ->invoke($test, 'parallel_command_test.php', 'parallel_fail');
echo json_encode($result, JSON_THROW_ON_ERROR);
