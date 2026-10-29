<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression;

use Oasis\SlimApp\Tests\Regression\Fixtures\BugReproductionTestCase;
use PHPUnit\Framework\Attributes\DataProvider;

final class BugY68QTest extends BugReproductionTestCase
{
    /** @return array<string, array{string}> */
    public static function cacheVariants(): array
    {
        return ['正常缓存对照' => ['valid'], '截断缓存' => ['truncated'],
            '标量缓存' => ['scalar'], 'false缓存' => ['false']];
    }

    #[DataProvider('cacheVariants')]
    public function testConfigurationRemainsAvailable(string $variant): void
    {
        $result = $this->runProcess($this->phpFixture('config_cache.php', $this->work, $variant));

        self::assertStringContainsString('CACHE_FRESH', $result['output'], $result['output']);
        self::assertSame(0, $result['exit'], $result['output'] . '\n日志：' . $result['log']);
        self::assertStringContainsString('CONFIGURATION_RECOVERED', $result['output']);
    }
}
