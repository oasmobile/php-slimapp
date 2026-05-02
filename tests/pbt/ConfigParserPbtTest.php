<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Pbt;

use Eris\Generators;
use Eris\TestTrait;
use Oasis\SlimApp\ConfigParser;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

/**
 * Feature: release-3.0, Property 3: 配置解析 Round-Trip
 *
 * For any valid configuration tree, for each leaf node path,
 * ConfigParser::retrieve(ConfigParser::flatten($config), 'app.' + path)
 * SHALL equal the original value.
 */
class ConfigParserPbtTest extends TestCase
{
    use TestTrait;

    public function testFlattenRetrieveRoundTripForScalarValues(): void
    {
        $this
            ->limitTo(100)
            ->forAll(
                Generators::names(),                    // strVal
                Generators::choose(-1000, 1000),        // intVal
                Generators::bool(),                     // boolVal
            )
            ->then(function (string $strVal, int $intVal, bool $boolVal): void {
                $config = [
                    'alpha' => $strVal,
                    'beta'  => $intVal,
                    'gamma' => $boolVal,
                ];

                $flat = ConfigParser::flatten($config);

                $this->assertSame(
                    $strVal,
                    ConfigParser::retrieve($flat, 'app.alpha'),
                    'Round-trip failed for string value'
                );
                $this->assertSame(
                    $intVal,
                    ConfigParser::retrieve($flat, 'app.beta'),
                    'Round-trip failed for int value'
                );
                $this->assertSame(
                    $boolVal,
                    ConfigParser::retrieve($flat, 'app.gamma'),
                    'Round-trip failed for bool value'
                );
            });
    }

    public function testFlattenRetrieveRoundTripForNestedConfig(): void
    {
        // Use predefined key pools to avoid regex generator
        $keyPool = [
            'alpha', 'beta', 'gamma', 'delta', 'epsilon',
            'config', 'settings', 'options', 'params', 'data',
            'level1', 'level2', 'level3', 'node', 'item',
        ];
        $valuePool = [
            'hello', 'world', 'test', 'value', 'foo', 'bar',
            '/var/log', '/tmp/data', 'true_str', '12345', '',
        ];

        $this
            ->limitTo(100)
            ->forAll(
                Generators::elements($keyPool),     // key1
                Generators::elements($keyPool),     // key2
                Generators::elements($keyPool),     // key3
                Generators::elements($valuePool),   // leaf value
            )
            ->then(function (
                string $key1,
                string $key2,
                string $key3,
                string $leafValue,
            ): void {
                // Build a 3-level nested config
                $config = [
                    $key1 => [
                        $key2 => [
                            $key3 => $leafValue,
                        ],
                    ],
                ];

                $flat = ConfigParser::flatten($config);

                $path = "app.{$key1}.{$key2}.{$key3}";
                $this->assertSame(
                    $leafValue,
                    ConfigParser::retrieve($flat, $path),
                    "Round-trip failed for nested path: $path"
                );
            });
    }

    public function testFlattenRetrieveRoundTripWithProcessedConfig(): void
    {
        $this
            ->limitTo(100)
            ->forAll(
                Generators::names(),                 // name
                Generators::choose(0, 10000),        // count
                Generators::bool(),                  // once
            )
            ->then(function (string $name, int $count, bool $once): void {
                // Use a real ConfigurationInterface to parse, then round-trip
                $definition = new PbtTestAppConfig();
                $rawConfig  = [
                    'dir'   => ['log' => '/var/log', 'data' => '/var/data'],
                    'name'  => $name,
                    'count' => $count,
                    'once'  => $once,
                ];

                $parsed = ConfigParser::parse([$rawConfig], $definition);
                $flat   = ConfigParser::flatten($parsed);

                $this->assertSame($name, ConfigParser::retrieve($flat, 'app.name'));
                $this->assertSame($count, ConfigParser::retrieve($flat, 'app.count'));
                $this->assertSame($once, ConfigParser::retrieve($flat, 'app.once'));
                $this->assertSame('/var/log', ConfigParser::retrieve($flat, 'app.dir.log'));
                $this->assertSame('/var/data', ConfigParser::retrieve($flat, 'app.dir.data'));
            });
    }
}

/**
 * Minimal ConfigurationInterface for PBT — mirrors TestAppConfig structure.
 */
class PbtTestAppConfig implements ConfigurationInterface
{
    public function getConfigTreeBuilder(): TreeBuilder
    {
        $treeBuilder = new TreeBuilder('app');
        $root        = $treeBuilder->getRootNode();

        $dir = $root->children()->arrayNode('dir');
        $dir->children()->scalarNode('log');
        $dir->children()->scalarNode('data');

        $root->children()->scalarNode('name');
        $root->children()->integerNode('count');
        $root->children()->booleanNode('once');

        return $treeBuilder;
    }
}
