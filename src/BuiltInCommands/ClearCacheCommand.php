<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands;

use Oasis\SlimApp\ConsoleApplication;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Filesystem\Filesystem;
use Symfony\Component\Finder\Finder;
use Symfony\Component\Finder\SplFileInfo;

class ClearCacheCommand extends Command
{
    protected function configure(): void
    {
        parent::configure();

        $this->setName('slimapp:cache:clear');
        $this->setDescription("Clears cache directories used by slimapp.");
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $console = $this->getApplication();
        assert($console instanceof ConsoleApplication);
        $slimapp = $console->getSlimapp();

        $cacheDirs = [$slimapp->getConfigCachePath()];

        $httpKernel = $slimapp->getHttpKernel();
        if (method_exists($httpKernel, 'getCacheDirectories')) {
            $httpCacheDirs = $httpKernel->getCacheDirectories();
        } elseif (method_exists($httpKernel, 'getCacheDir')) {
            $httpCacheDirs = [$httpKernel->getCacheDir()];
        } else {
            $httpCacheDirs = [];
        }
        $cacheDirs = array_merge($cacheDirs, $httpCacheDirs);

        foreach ($cacheDirs as $dir) {
            $output->writeln(sprintf('<comment>removing cache in %s ...</comment>', $dir));
            $fs     = new Filesystem();
            $finder = new Finder();
            $finder->in($dir);
            $finder->depth(0);
            $finder->ignoreVCS(false);
            /** @var SplFileInfo $splInfo */
            foreach ($finder as $splInfo) {
                $output->writeln(sprintf("removing file: %s", $splInfo->getPathname()), OutputInterface::VERBOSITY_VERBOSE);
                $fs->remove($splInfo->getPathname());
            }
            $output->writeln('<info>done.</info>');
        }

        return 0;
    }
}
