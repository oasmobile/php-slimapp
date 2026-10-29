<?php
declare(strict_types=1);

use Oasis\SlimApp\SlimApp;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;
use Symfony\Component\Config\ConfigCache;
use Symfony\Component\Filesystem\Filesystem;
use Symfony\Component\Yaml\Yaml;

require getenv('REPRO_REPO_ROOT') . '/vendor/autoload.php';
$root = $argv[1];
$variant = $argv[2];
$fs = new Filesystem();
$fs->mkdir($root . '/config');
$fs->dumpFile($root . '/config/config.yml', "name: cache-repro\n");
$fs->dumpFile($root . '/config/services.yml', Yaml::dump([
    'parameters' => ['default.namespace' => ['Oasis\\SlimApp\\']],
    'services' => ['app' => ['properties' => ['logging' => ['path' => $root . '/logs']]]],
], 8));
$app = new SlimApp();
$app->init($root . '/config', new TestAppConfig());
$cache = $app->getConfigCachePath() . '/config.cache';
if ($app->getMandatoryConfig('name') !== 'cache-repro') {
    throw new RuntimeException('有效配置对照失败');
}
if ($variant !== 'valid') {
    $fs->dumpFile($cache, match ($variant) {
        'truncated' => 'a:2:{',
        'scalar' => serialize('not-an-array'),
        'false' => serialize(false),
    });
}
clearstatcache();
if (!(new ConfigCache($cache, true))->isFresh()) {
    throw new RuntimeException('复现前置条件不成立：缓存必须被判定为 fresh');
}
echo "CACHE_FRESH\n";
$restored = new SlimApp();
$restored->init($root . '/config', new TestAppConfig());
$contents = unserialize((string) file_get_contents($cache));
if ($restored->getMandatoryConfig('name') !== 'cache-repro'
    || !is_array($contents) || ($contents['name'] ?? null) !== 'cache-repro') {
    throw new RuntimeException('应用未恢复原始配置或未重建合法缓存');
}
echo "CONFIGURATION_RECOVERED\n";
