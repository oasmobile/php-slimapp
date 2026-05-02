<?php

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\SentinelCommand\CommandRunner;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Output\BufferedOutput;

class CommandRunnerTest extends \PHPUnit_Framework_TestCase
{
    private function createRunner(array $commandOverrides = [], $traceEnabled = false)
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

    public function testShouldStartNextRunWhenNotFinishedReturnsFalseByDefault()
    {
        $runner = $this->createRunner();
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenOnce()
    {
        $runner = $this->createRunner(['once' => true, 'frequency' => 1, 'frequency_fixed' => true]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenNoFrequency()
    {
        $runner = $this->createRunner(['frequency' => 0, 'frequency_fixed' => true]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenNotFrequencyFixed()
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => false]);
        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsTrueWhenFrequencyReached()
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setAccessible(true);
        $ref->setValue($runner, time() - 10);

        $this->assertTrue($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testShouldStartNextRunReturnsFalseWhenFrequencyNotReached()
    {
        $runner = $this->createRunner(['frequency' => 9999, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setAccessible(true);
        $ref->setValue($runner, time());

        $this->assertFalse($runner->shouldStartNextRunWhenNotFinished());
    }

    public function testCloneEarlyRunnerResetsState()
    {
        $runner = $this->createRunner(['frequency' => 1, 'frequency_fixed' => true]);

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setAccessible(true);
        $ref->setValue($runner, time() - 10);

        $earlyRunner = $runner->cloneEarlyRunner();

        $onceRef = new \ReflectionProperty($runner, 'once');
        $onceRef->setAccessible(true);
        $this->assertTrue($onceRef->getValue($runner));

        $lastRunRef = new \ReflectionProperty($earlyRunner, 'lastRun');
        $lastRunRef->setAccessible(true);
        $this->assertEquals(0, $lastRunRef->getValue($earlyRunner));

        $currentPidRef = new \ReflectionProperty($earlyRunner, 'currentPid');
        $currentPidRef->setAccessible(true);
        $this->assertEquals(0, $currentPidRef->getValue($earlyRunner));
    }

    public function testCloneResetsFields()
    {
        $runner = $this->createRunner();

        $ref = new \ReflectionProperty($runner, 'lastRun');
        $ref->setAccessible(true);
        $ref->setValue($runner, 12345);

        $pidRef = new \ReflectionProperty($runner, 'currentPid');
        $pidRef->setAccessible(true);
        $pidRef->setValue($runner, 999);

        $cloned = clone $runner;

        $this->assertEquals(0, $ref->getValue($cloned));
        $this->assertEquals(0, $pidRef->getValue($cloned));
    }

    public function testOnProcessExitSetsStoppedWhenOnce()
    {
        $runner = $this->createRunner(['once' => true]);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $this->assertTrue($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitDoesNotStopWhenNotOnce()
    {
        $runner = $this->createRunner(['once' => false]);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithFrequencyAdjustsNextRun()
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 60]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setAccessible(true);
        $lastRunRef->setValue($runner, time());

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $nextRunRef->setAccessible(true);
        $this->assertGreaterThanOrEqual(time() + 59, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithIntervalAdjustsNextRun()
    {
        $runner = $this->createRunner(['once' => false, 'interval' => 30]);
        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $nextRunRef->setAccessible(true);
        $this->assertGreaterThanOrEqual(time() + 29, $nextRunRef->getValue($runner));
    }

    public function testRunReturnsZeroWhenStopped()
    {
        $runner = $this->createRunner(['once' => true]);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $stoppedRef->setValue($runner, true);

        $this->assertEquals(0, $runner->run());
    }

    public function testParallelIndexSubstitution()
    {
        $runner = $this->createRunner();
        $this->assertPropertyEquals($runner, 'parallelIndex', 0);
    }

    public function testConstructorSetsProperties()
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

    public function testOnProcessExitWithNonZeroExitAndAlertTrue()
    {
        $runner = $this->createRunner(['once' => false, 'alert' => true]);
        $runner->onProcessExit(1, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithNonZeroExitAndAlertFalse()
    {
        $runner = $this->createRunner(['once' => false, 'alert' => false]);
        $runner->onProcessExit(1, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testOnProcessExitWithBothFrequencyAndInterval()
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 5, 'interval' => 30]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setAccessible(true);
        $lastRunRef->setValue($runner, time());

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $nextRunRef->setAccessible(true);
        $this->assertGreaterThanOrEqual(time() + 29, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithZeroExitNoFrequencyNoInterval()
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 0, 'interval' => 0]);
        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $nextRunRef->setAccessible(true);
        $this->assertLessThanOrEqual(time() + 1, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitFrequencyNotYetReached()
    {
        $runner = $this->createRunner(['once' => false, 'frequency' => 60]);

        $lastRunRef = new \ReflectionProperty($runner, 'lastRun');
        $lastRunRef->setAccessible(true);
        $lastRunRef->setValue($runner, time() - 1);

        $runner->onProcessExit(0, 123);

        $nextRunRef = new \ReflectionProperty($runner, 'nextRun');
        $nextRunRef->setAccessible(true);
        $this->assertGreaterThanOrEqual(time() + 58, $nextRunRef->getValue($runner));
    }

    public function testOnProcessExitWithTraceEnabled()
    {
        $runner = $this->createRunner(['once' => false], true);
        $runner->onProcessExit(0, 123);

        $stoppedRef = new \ReflectionProperty($runner, 'stopped');
        $stoppedRef->setAccessible(true);
        $this->assertFalse($stoppedRef->getValue($runner));
    }

    public function testNamePropertyIsSet()
    {
        $runner = $this->createRunner(['name' => 'custom:command']);
        $this->assertPropertyEquals($runner, 'name', 'custom:command');
    }

    public function testInputIsBuiltWithCommandName()
    {
        $runner   = $this->createRunner(['name' => 'list']);
        $inputRef = new \ReflectionProperty($runner, 'input');
        $inputRef->setAccessible(true);
        $this->assertInstanceOf(\Symfony\Component\Console\Input\ArrayInput::class, $inputRef->getValue($runner));
    }

    public function testInputIncludesArgs()
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
        $inputRef->setAccessible(true);
        $input = $inputRef->getValue($runner);

        $this->assertEquals('json', $input->getParameterOption('--format'));
    }

    private function assertPropertyEquals($object, $property, $expected)
    {
        $ref = new \ReflectionProperty($object, $property);
        $ref->setAccessible(true);
        $this->assertEquals($expected, $ref->getValue($object));
    }
}
