<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Pbt;

use Eris\Generators;
use Eris\TestTrait;
use Oasis\SlimApp\SentinelCommand\CommandConfiguration;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Config\Definition\Processor;
use Symfony\Component\Console\Application;

/**
 * Feature: release-3.0, Property 1: CommandConfiguration 处理幂等性
 *
 * For any valid command configuration array, processing once to get R1,
 * then re-processing R1 to get R2, R1 SHALL equal R2.
 */
class CommandConfigurationPbtTest extends TestCase
{
    use TestTrait;

    public function testCommandConfigurationProcessingIsIdempotent(): void
    {
        $app       = new Application('test', '1.0');
        $config    = new CommandConfiguration($app);
        $processor = new Processor();

        // Generate command names from a predefined set of valid names
        $nameGenerator = Generators::elements([
            'app:run', 'cache:clear', 'db:migrate', 'queue:work', 'test:exec',
            'daemon:start', 'cron:tick', 'mail:send', 'log:rotate', 'user:sync',
        ]);

        $this
            ->limitTo(100)
            ->forAll(
                $nameGenerator,                                 // name
                Generators::choose(1, 10),                      // parallel
                Generators::bool(),                             // once
                Generators::bool(),                             // alert
                Generators::choose(0, 300),                     // interval
                Generators::choose(0, 300),                     // frequency
                Generators::bool(),                             // frequency_fixed
            )
            ->then(function (
                string $name,
                int $parallel,
                bool $once,
                bool $alert,
                int $interval,
                int $frequency,
                bool $frequencyFixed,
            ) use ($config, $processor): void {
                $input = [
                    'commands' => [
                        [
                            'name'            => $name,
                            'args'            => [],
                            'parallel'        => $parallel,
                            'once'            => $once,
                            'alert'           => $alert,
                            'interval'        => $interval,
                            'frequency'       => $frequency,
                            'frequency_fixed' => $frequencyFixed,
                        ],
                    ],
                ];

                // First pass
                $r1 = $processor->processConfiguration($config, [$input]);

                // Second pass: feed R1 back as input
                $r2 = $processor->processConfiguration($config, [$r1]);

                $this->assertSame($r1, $r2, 'CommandConfiguration processing should be idempotent');
            });
    }
}
