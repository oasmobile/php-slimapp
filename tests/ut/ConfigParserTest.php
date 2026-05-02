<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\ConfigParser;
use Oasis\SlimApp\Tests\Integration\Fixtures\TestAppConfig;
use PHPUnit\Framework\TestCase;

class ConfigParserTest extends TestCase
{
    public function testParseProcessesConfiguration(): void
    {
        $rawConfigs = [
            [
                'dir'   => ['log' => '/var/log', 'data' => '/var/data'],
                'name'  => 'TestApp',
                'count' => 5,
                'once'  => true,
            ],
        ];

        $result = ConfigParser::parse($rawConfigs, new TestAppConfig());

        $this->assertIsArray($result);
        $this->assertEquals('TestApp', $result['name']);
        $this->assertEquals(5, $result['count']);
        $this->assertTrue($result['once']);
        $this->assertEquals('/var/log', $result['dir']['log']);
        $this->assertEquals('/var/data', $result['dir']['data']);
    }

    public function testParseMergesMultipleConfigs(): void
    {
        $rawConfigs = [
            [
                'dir'   => ['log' => '/var/log', 'data' => '/var/data'],
                'name'  => 'First',
                'count' => 1,
                'once'  => false,
            ],
            [
                'dir'   => ['log' => '/tmp/log', 'data' => '/tmp/data'],
                'name'  => 'Second',
                'count' => 2,
                'once'  => true,
            ],
        ];

        $result = ConfigParser::parse($rawConfigs, new TestAppConfig());

        // Symfony Processor merges configs; later values override earlier ones
        $this->assertEquals('Second', $result['name']);
        $this->assertEquals(2, $result['count']);
        $this->assertTrue($result['once']);
    }

    public function testFlattenSimpleConfig(): void
    {
        $config = [
            'name'  => 'TestApp',
            'count' => 5,
            'once'  => true,
        ];

        $flat = ConfigParser::flatten($config);

        $this->assertEquals('TestApp', $flat['app.name']);
        $this->assertEquals(5, $flat['app.count']);
        $this->assertTrue($flat['app.once']);
    }

    public function testFlattenNestedConfig(): void
    {
        $config = [
            'dir' => [
                'log'  => '/var/log',
                'data' => '/var/data',
            ],
            'name' => 'TestApp',
        ];

        $flat = ConfigParser::flatten($config);

        $this->assertEquals('TestApp', $flat['app.name']);
        $this->assertIsArray($flat['app.dir']);
        $this->assertEquals('/var/log', $flat['app.dir.log']);
        $this->assertEquals('/var/data', $flat['app.dir.data']);
    }

    public function testFlattenWithCustomPrefix(): void
    {
        $config = ['key' => 'value'];

        $flat = ConfigParser::flatten($config, 'custom.');

        $this->assertEquals('value', $flat['custom.key']);
        $this->assertArrayNotHasKey('app.key', $flat);
    }

    public function testFlattenEmptyConfig(): void
    {
        $flat = ConfigParser::flatten([]);

        $this->assertIsArray($flat);
        $this->assertEmpty($flat);
    }

    public function testRetrieveExistingKey(): void
    {
        $flatParams = [
            'app.name'     => 'TestApp',
            'app.dir.log'  => '/var/log',
        ];

        $this->assertEquals('TestApp', ConfigParser::retrieve($flatParams, 'app.name'));
        $this->assertEquals('/var/log', ConfigParser::retrieve($flatParams, 'app.dir.log'));
    }

    public function testRetrieveNonExistentKeyReturnsNull(): void
    {
        $flatParams = ['app.name' => 'TestApp'];

        $this->assertNull(ConfigParser::retrieve($flatParams, 'app.nonexistent'));
    }

    public function testRoundTripParseAndFlattenAndRetrieve(): void
    {
        $rawConfigs = [
            [
                'dir'   => ['log' => '/data/logs', 'data' => '/data/app'],
                'name'  => 'RoundTrip',
                'count' => 42,
                'once'  => false,
            ],
        ];

        $parsed = ConfigParser::parse($rawConfigs, new TestAppConfig());
        $flat   = ConfigParser::flatten($parsed);

        // Verify leaf values are retrievable via their flattened key
        $this->assertEquals('RoundTrip', ConfigParser::retrieve($flat, 'app.name'));
        $this->assertEquals(42, ConfigParser::retrieve($flat, 'app.count'));
        $this->assertFalse(ConfigParser::retrieve($flat, 'app.once'));
        $this->assertEquals('/data/logs', ConfigParser::retrieve($flat, 'app.dir.log'));
        $this->assertEquals('/data/app', ConfigParser::retrieve($flat, 'app.dir.data'));
    }

    public function testFlattenDeeplyNestedConfig(): void
    {
        $config = [
            'level1' => [
                'level2' => [
                    'level3' => 'deep_value',
                ],
            ],
        ];

        $flat = ConfigParser::flatten($config);

        $this->assertEquals('deep_value', $flat['app.level1.level2.level3']);
        // Intermediate arrays are also present
        $this->assertIsArray($flat['app.level1']);
        $this->assertIsArray($flat['app.level1.level2']);
    }
}
