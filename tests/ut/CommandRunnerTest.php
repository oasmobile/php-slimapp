<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\SentinelCommand\CommandRunner;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Output\BufferedOutput;

class CommandRunnerTest extends TestCase
{
    private function createRunner(array $commandOverrides = [], bool $traceEnabled = false): CommandRunner
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);

        $command = array_merge([
            'name'            => 'list',
            'args'            => [],
            'once'            => false,
            'interval'        => 0,
            'frequency'       => 0,
            'frequency_fixed' => false,
            'alert'           => true,
        ], $commandOverrides);

        $output = new BufferedOutput();

        return new CommandRunner($app, 0, $command, $output, $traceEnabled);
    }

    public function testShouldStartNextRunWhenNotFinishedReturnsFalseByDefault(): void
    {
        $runner = $this->createRunner();
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenOnce(): void
    {
        $runner = $this->createRunner(['once' => true, 'frequency' => 1, 'frequency_fixed' => true]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenNoFrequency(): void
    {
        $runner = $this->createRunner(['frequency' => 0, 'frequency_fixed' => true]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenNotFrequencyFixed(): void
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => false]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsTrueWhenFrequencyReached(): void
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setValue($runner, time() - 10);

        $this->assertTrue($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenFrequencyNotReached(): void
    {
        $runner = $this->createRunner(['frequency' => 9999, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setValue($runner, time());

        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testCloneEarlyRunnerResetsState(): void
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setValue($runner, time() - 10);

        $earlyRunner = $runner->cloneEarlyRunner();

        $onceRef = new \ReflectionProperty($runner, 'once');
        $this->assertTrue($onceRef->getValue($runner));

        $lastRunRef = new \ReflectionProperty($earlyRunner, 'lastRun');
        $this->assertEquals(0, $lastRunRef->getValue($earlyRunner));

        $currentPidRef = new \ReflectionProperty($earlyRunner, 'currentPid');
        $this->assertEquals(0, $currentPidRef->getValue($earlyRunner));
    }

    public function testCloneResetsFields(): void
    {
        $runner = $this->createRunner();

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setValue($runner, 12345);

        $pidRef = new \ReflectionProperty($runner, 'currentPid');
        $pidRef->setValue($runner, 999);

        $cloned = clone $runner;

        $this->assertEquals(0, $ref->getValue($cloned));
        $this->assertEquals(0, $pidRef->getValue($cloned));
    }

    public function testOnProcessExitSetsStoppedWhenOnce(): void
    {
        $runner = $this->createRunner(['once' => true]);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertTrue($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitDoesNotStopWhenNotOnce(): void
    {
        $runner = $this->createRunner(['once' => false]);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithFrequencyAdjustsNextRun(): void
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 60]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setValue($runner, time());

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $this->assertGreaterThanOrEqual(time() + 59, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithIntervalAdjustsNextRun(): void
    {
        $runner = $this->createRunner(['once' => false, 'interval' => 30]);
        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $this->assertGreaterThanOrEqual(time() + 29, $nextRunRef->getValue($runner));
    }

    public function testRunReturnsZeroWhenStopped(): void
    {
        $runner = $this->createRunner(['once' => true]);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setValue($runner, true);

        $this->assertEquals(0, $runner->run());
    }

    public function testParallelIndexSubstitution(): void
    {
        $runner = $this->createRunner();
        $this->assertPropertyEquals($runner, 'parallelIndex', 0);
    }

    public function testConstructorSetsProperties(): void
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);

        $command = [
            'name' => 'list', 'args' => [],
            'once' => true, 'interval' => 15, 'frequency' => 30,
            'frequency_fixed' => true, 'alert' => false,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 2, $command, $output, true);

        $this->assertPropertyEquals($runner, 'once', true);
        $this->assertPropertyEquals($runner, 'interval', 15);
        $this->assertPropertyEquals($runner, 'frequency', 30);
        $this->assertPropertyEquals($runner, 'frequencyFixed', true);
        $this->assertPropertyEquals($runner, 'alert', false);
        $this->assertPropertyEquals($runner, 'parallelIndex', 2);
        $this->assertPropertyEquals($runner, 'traceEnabled', true);
    }

    public function testOnProcessExitWithNonZeroExitAndAlertTrue(): void
    {
        $runner = $this->createRunner(['once' => false, 'alert' => true]);
        $runner->onProcessExit(1, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithNonZeroExitAndAlertFalse(): void
    {
        $runner = $this->createRunner(['once' => false, 'alert' => false]);
        $runner->onProcessExit(1, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithBothFrequencyAndInterval(): void
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 5, 'interval' => 30]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setValue($runner, time());

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $this->assertGreaterThanOrEqual(time() + 29, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithZeroExitNoFrequencyNoInterval(): void
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 0, 'interval' => 0]);
        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $this->assertLessThanOrEqual(time() + 1, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitFrequencyNotYetReached(): void
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 60]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setValue($runner, time() - 1);

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $this->assertGreaterThanOrEqual(time() + 58, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithTraceEnabled(): void
    {
        $runner = $this->createRunner(['once' => false], true);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testNamePropertyIsSet(): void
    {
        $runner = $this->createRunner(['name' => 'custom:command']);
        $this->assertPropertyEquals($runner, 'name', 'custom:command');
    }

    public function testInputIsBuiltWithCommandName(): void
    {
        $runner   = $this->createRunner(['name' => 'list']);
        $inputRef = new \ReflectionProperty($runner, 'input');
        $this->assertInstanceOf(\Symfony\Component\Console\Input\ArrayInput::class, $inputRef->getValue($runner));
    }

    public function testInputIncludesArgs(): void
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);

        $command = [
            'name' => 'list', 'args' => ['--format' => 'json'],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => true,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 0, $command, $output);

        $inputRef = new \ReflectionProperty($runner, 'input');
        $input = $inputRef->getValue($runner);

        $this->assertEquals('json', $input->getParameterOption('--format'));
    }

    public function testParallelIndexSubstitutionInArgs(): void
    {
        $app = new Application('test', '1.0');
        $app->setAutoExit(false);

        $command = [
            'name' => 'list', 'args' => ['--idx' => '$PARALLEL_INDEX'],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => true,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 3, $command, $output);

        $inputRef = new \ReflectionProperty($runner, 'input');
        $input = $inputRef->getValue($runner);

        $this->assertEquals(3, $input->getParameterOption('--idx'));
    }

    public function testRunForksAndReturnsChildPid(): void
    {
        if (!function_exists('pcntl_fork')) {
            $this->markTestSkipped('pcntl not available');
        }

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->addCommand(new \Symfony\Component\Console\Command\Command('list'));

        $command = [
            'name' => 'list', 'args' => [],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => false,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 0, $command, $output);

        $pid = $runner->run();
        $this->assertGreaterThan(0, $pid);

        // Clean up child process
        pcntl_waitpid($pid, $status);
    }

    public function testRunSetsLastRunAndCurrentPid(): void
    {
        if (!function_exists('pcntl_fork')) {
            $this->markTestSkipped('pcntl not available');
        }

        $app = new Application('test', '1.0');
        $app->setAutoExit(false);
        $app->addCommand(new \Symfony\Component\Console\Command\Command('list'));

        $command = [
            'name' => 'list', 'args' => [],
            'once' => false, 'interval' => 0, 'frequency' => 0,
            'frequency_fixed' => false, 'alert' => false,
        ];

        $output = new BufferedOutput();
        $runner = new CommandRunner($app, 0, $command, $output);

        $pid = $runner->run();

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $currentPidRef = new \ReflectionProperty($runner, 'currentPid');

        $this->assertGreaterThan(0, $lastRunRef->getValue($runner));
        $this->assertEquals($pid, $currentPidRef->getValue($runner));

        pcntl_waitpid($pid, $status);
    }

    public function testOnProcessExitWithFrequencyAlreadyReached(): void
    {
        // When lastRun + frequency <= time(), nextRun should be set to time()
        $runner = $this->createRunner(['once' => false, 'frequency' => 1, 'interval' => 0]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setValue($runner, time() - 100);

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        // nextRun should be approximately now (since lastRun + frequency < time())
        $this->assertLessThanOrEqual(time() + 1, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithTraceEnabledLogsDebug(): void
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 0, 'interval' => 0], true);
        // Just verify it doesn't throw — trace logging is a side effect
        $runner->onProcessExit(0, 456);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitOnceWithNonZeroExitAndAlert(): void
    {
        $runner = $this->createRunner(['once' => true, 'alert' => true]);
        $runner->onProcessExit(1, 789);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertTrue($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitOnceWithNonZeroExitNoAlert(): void
    {
        $runner = $this->createRunner(['once' => true, 'alert' => false]);
        $runner->onProcessExit(1, 789);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $this->assertTrue($stoppedRef->getValue($runner));
    }

    private function assertPropertyEquals(object $object, string $property, mixed $expected): void
    {
        $ref = new \ReflectionProperty($object, $property);
        $this->assertEquals($expected, $ref->getValue($object));
    }
}
