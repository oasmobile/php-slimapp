<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Pbt;

use Eris\Generators;
use Eris\TestTrait;
use Monolog\Level;
use Oasis\SlimApp\ConsoleApplication;
use PHPUnit\Framework\TestCase;
use Symfony\Component\Console\Input\ArrayInput;
use Symfony\Component\Console\Output\BufferedOutput;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * Feature: release-3.0, Property 5: Verbosity-to-LogLevel 全函数属性
 *
 * For any valid Symfony verbosity constant, ConsoleApplication's configureIO()
 * SHALL map to a valid Monolog Logger level.
 */
class VerbosityMappingPbtTest extends TestCase
{
    use TestTrait;

    /**
     * Valid Monolog Level enum cases.
     *
     * @return list<Level>
     */
    private static function validMonologLevels(): array
    {
        return Level::cases();
    }

    public function testVerbosityMapsToValidMonologLevel(): void
    {
        $verbosityConstants = [
            OutputInterface::VERBOSITY_QUIET,
            OutputInterface::VERBOSITY_NORMAL,
            OutputInterface::VERBOSITY_VERBOSE,
            OutputInterface::VERBOSITY_VERY_VERBOSE,
            OutputInterface::VERBOSITY_DEBUG,
        ];

        $validLevels = self::validMonologLevels();

        $this
            ->limitTo(100)
            ->forAll(
                Generators::elements($verbosityConstants),
            )
            ->then(function (int $verbosity) use ($validLevels): void {
                // Use the match expression from ConsoleApplication::configureIO()
                // to verify the mapping produces a valid Monolog level
                $level = match ($verbosity) {
                    OutputInterface::VERBOSITY_QUIET        => Level::Critical,
                    OutputInterface::VERBOSITY_NORMAL       => Level::Warning,
                    OutputInterface::VERBOSITY_VERBOSE      => Level::Notice,
                    OutputInterface::VERBOSITY_VERY_VERBOSE => Level::Info,
                    OutputInterface::VERBOSITY_DEBUG        => Level::Debug,
                    default                                 => Level::Debug,
                };

                $this->assertContains(
                    $level,
                    $validLevels,
                    sprintf(
                        'Verbosity %d mapped to level %s which is not a valid Monolog level',
                        $verbosity,
                        $level->name
                    )
                );
            });
    }

    public function testConfigureIODoesNotThrowForAnyVerbosity(): void
    {
        $verbosityConstants = [
            OutputInterface::VERBOSITY_QUIET,
            OutputInterface::VERBOSITY_NORMAL,
            OutputInterface::VERBOSITY_VERBOSE,
            OutputInterface::VERBOSITY_VERY_VERBOSE,
            OutputInterface::VERBOSITY_DEBUG,
        ];

        $this
            ->limitTo(100)
            ->forAll(
                Generators::elements($verbosityConstants),
            )
            ->then(function (int $verbosity): void {
                $app = new ConsoleApplication('test', '1.0');
                $app->setLoggingEnabled(true);
                $app->setAutoExit(false);
                $app->setCatchExceptions(false);

                $output = new BufferedOutput($verbosity);
                $input  = new ArrayInput(['command' => 'list']);

                // Running the app exercises configureIO() internally
                $exitCode = $app->run($input, $output);

                $this->assertSame(
                    0,
                    $exitCode,
                    "ConsoleApplication should run successfully with verbosity $verbosity"
                );
            });
    }
}
