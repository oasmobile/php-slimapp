<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Pbt;

use Eris\Generators;
use Eris\TestTrait;
use Oasis\SlimApp\SentinelCommand\CommandRunner;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Output\BufferedOutput;

/**
 * Feature: release-3.0, Property 2: CommandRunner 调度约束
 *
 * For any non-once CommandRunner, after onProcessExit():
 * - when frequency > 0: nextRun >= lastRun + frequency
 * - when interval > 0:  nextRun >= now + interval
 * - when frequency=0 and interval=0: nextRun ≈ now (within 2s tolerance)
 */
class CommandRunnerSchedulingPbtTest extends TestCase
{
    use TestTrait;

    public function testSchedulingConstraintsForNonOnceRunner(): void
    {
        $this
            ->limitTo(100)
            ->forAll(
                Generators::choose(0, 300),   // interval
                Generators::choose(0, 300),   // frequency
                Generators::bool(),           // frequency_fixed
                Generators::choose(0, 600),   // lastRunOffset (seconds before now)
                Generators::choose(0, 255),   // exitStatus
            )
            ->then(function (
                int $interval,
                int $frequency,
                bool $frequencyFixed,
                int $lastRunOffset,
                int $exitStatus,
            ): void {
                $app = new Application('test', '1.0');
                $app->setAutoExit(false);

                $command = [
                    'name'            => 'list',
                    'args'            => [],
                    'once'            => false,
                    'interval'        => $interval,
                    'frequency'       => $frequency,
                    'frequency_fixed' => $frequencyFixed,
                    'alert'           => false,
                ];

                $output = new BufferedOutput();
                $runner = new CommandRunner($app, 0, $command, $output);

                // Set lastRun via reflection
                $lastRun    = time() - $lastRunOffset;
                $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
                $lastRunRef->setValue($runner, $lastRun);

                $beforeTime = time();
                $runner->onProcessExit($exitStatus, 123);
                $afterTime = time();

                $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
                $nextRun    = $nextRunRef->getValue($runner);

                // Constraint 1: when frequency > 0, nextRun >= lastRun + frequency
                if ($frequency > 0) {
                    $this->assertGreaterThanOrEqual(
                        $lastRun + $frequency,
                        $nextRun,
                        "nextRun ($nextRun) should be >= lastRun ($lastRun) + frequency ($frequency)"
                    );
                }

                // Constraint 2: when interval > 0, nextRun >= now + interval
                if ($interval > 0) {
                    $this->assertGreaterThanOrEqual(
                        $beforeTime + $interval,
                        $nextRun,
                        "nextRun ($nextRun) should be >= now ($beforeTime) + interval ($interval)"
                    );
                }

                // Constraint 3: when frequency=0 and interval=0, nextRun ≈ now
                if ($frequency === 0 && $interval === 0) {
                    $this->assertGreaterThanOrEqual($beforeTime, $nextRun);
                    $this->assertLessThanOrEqual($afterTime + 1, $nextRun);
                }
            });
    }

    public function testOnceRunnerStopsAfterExit(): void
    {
        $this
            ->limitTo(100)
            ->forAll(
                Generators::choose(0, 255),  // exitStatus
            )
            ->then(function (int $exitStatus): void {
                $app = new Application('test', '1.0');
                $app->setAutoExit(false);

                $command = [
                    'name'            => 'list',
                    'args'            => [],
                    'once'            => true,
                    'interval'        => 0,
                    'frequency'       => 0,
                    'frequency_fixed' => false,
                    'alert'           => false,
                ];

                $output = new BufferedOutput();
                $runner = new CommandRunner($app, 0, $command, $output);

                $runner->onProcessExit($exitStatus, 123);

                $stoppedRef = new \ReflectionProperty($runner, 'stopped');
                $this->assertTrue(
                    $stoppedRef->getValue($runner),
                    'once=true runner should be stopped after onProcessExit'
                );
            });
    }
}
