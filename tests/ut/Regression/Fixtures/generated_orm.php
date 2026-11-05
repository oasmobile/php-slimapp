<?php
declare(strict_types=1);

use Doctrine\ORM\EntityManager;
use Oasis\SlimApp\SlimApp;
use Repro\Generated\Database\ProjectDatabase;
use Repro\Generated\Project;
use Symfony\Component\DependencyInjection\Container;

$root = $argv[1];
require $root . '/vendor/autoload.php';
define('PROJECT_DIR', $root);

// 只执行真实生成的 ORM 工厂；排除 Memcached、HTTP 和数据库服务依赖。
$container = new Container();
$container->setParameter('app.dir.data', $root . '/data');
$container->setParameter('app.db', [
    'host' => '127.0.0.1', 'user' => 'repro', 'password' => 'unused', 'dbname' => 'repro',
]);
(new ReflectionProperty(SlimApp::class, 'container'))->setValue(Project::app(), $container);
(new ReflectionProperty(SlimApp::class, 'isDebugMode'))->setValue(Project::app(), true);

echo "GENERATED_FACTORY_READY\n";
$manager = ProjectDatabase::getEntityManager();
if (!$manager instanceof EntityManager || $manager->getConnection()->isConnected()) {
    throw new RuntimeException('工厂必须创建 EntityManager，且不连接真实数据库');
}
echo "ENTITY_MANAGER_CREATED\n";
