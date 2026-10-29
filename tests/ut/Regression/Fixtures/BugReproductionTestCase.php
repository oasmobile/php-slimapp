<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression\Fixtures;

use PHPUnit\Framework\TestCase;
use Symfony\Component\Filesystem\Filesystem;

abstract class BugReproductionTestCase extends TestCase
{
    protected string $repo;
    protected string $work;
    protected string $reports;

    protected function setUp(): void
    {
        $this->repo = dirname(__DIR__, 4);
        $run = (new \ReflectionClass($this))->getShortName()
            . '-' . date('Ymd-His') . '-' . bin2hex(random_bytes(5));
        $this->work = $this->repo . '/.mdf/tmp/' . date('Y-m-d') . '-v3-bug-repro/' . $run;
        $this->reports = $this->repo . '/.mdf/reports/v3-bug-repro-' . $run;
        (new Filesystem())->mkdir([$this->work, $this->reports]);
    }

    protected function tearDown(): void
    {
        (new Filesystem())->remove($this->work);
    }

    /** @param list<string> $command
     *  @param array<string, string> $environment
     *  @return array{exit: int, output: string, log: string}
     */
    protected function runProcess(array $command, array $environment = []): array
    {
        $log = $this->reports . '/' . bin2hex(random_bytes(4)) . '.log';
        $process = proc_open($command, [
            0 => ['file', '/dev/null', 'r'],
            1 => ['file', $log, 'w'],
            2 => ['redirect', 1],
        ], $pipes, $this->repo, array_replace(getenv(), [
            'REPRO_REPO_ROOT' => $this->repo,
            'TMPDIR' => $this->work,
        ], $environment));
        self::assertIsResource($process, '无法创建复现子进程');
        $exit = proc_close($process);
        $output = file_get_contents($log);
        self::assertIsString($output);
        file_put_contents($log . '.json', json_encode([
            'command' => $command, 'environment' => $environment, 'exit' => $exit,
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR));

        return ['exit' => $exit, 'output' => $output, 'log' => $log];
    }

    /** @return list<string> */
    protected function phpFixture(string $filename, string ...$arguments): array
    {
        return [PHP_BINARY, __DIR__ . '/' . $filename, ...$arguments];
    }
}
