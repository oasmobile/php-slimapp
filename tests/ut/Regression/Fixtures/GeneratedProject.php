<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Regression\Fixtures;

use Oasis\SlimApp\BuiltInCommands\InitializeProjectCommand;
use PHPUnit\Framework\Assert;
use Symfony\Component\Console\Application;
use Symfony\Component\Console\Tester\CommandTester;
use Symfony\Component\Filesystem\Filesystem;

final class GeneratedProject
{
    public static function create(string $root, bool $orm, bool $phpunit): void
    {
        $fs = new Filesystem();
        $fs->mkdir([$root . '/vendor', $root . '/data', $root . '/logs', $root . '/templates']);
        $fs->dumpFile($root . '/composer.json', '{"name":"repro/project"}');
        $fs->dumpFile($root . '/composer.lock', '{}');
        $fs->copy(__DIR__ . '/generated_autoload.php', $root . '/vendor/autoload.php');
        $command = new class extends InitializeProjectCommand {
            protected function updateComposerInfo(): void
            {
                // 复用已锁定的依赖；测试不调用 Composer 或访问网络。
            }
        };
        (new Application())->addCommand($command);
        $tester = new CommandTester($command);
        $tester->setInputs([
            'repro/project', 'Repro\\Generated\\', 'src/',
            $orm ? 'yes' : 'no', 'no', $phpunit ? 'yes' : 'no',
            $root . '/logs', $root . '/data', $root . '/cache', $root . '/templates',
        ]);
        Assert::assertSame(0, $tester->execute(['--project-root' => $root]), $tester->getDisplay());
        $fs->copy($root . '/config/tpl.config.yml', $root . '/config/config.yml');
    }
}
