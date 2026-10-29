<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Fixtures;

use Oasis\SlimApp\AbstractParallelCommand;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;


class ConcreteParallelCommand extends AbstractParallelCommand
{
    private int $executionCount = 0;
    private int $returnCode;

    public function __construct(int $returnCode = 0)
    {
        $this->returnCode = $returnCode;
        parent::__construct('test:parallel');
    }

    protected function doExecute(InputInterface $input, OutputInterface $output): int
    {
        $this->executionCount++;

        return $this->returnCode;
    }

    public function getExecutionCount(): int
    {
        return $this->executionCount;
    }

    public function exposeGetParallelCount(): int
    {
        return $this->getParallelCount();
    }
}
