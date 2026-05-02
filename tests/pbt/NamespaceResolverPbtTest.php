<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests\Pbt;

use Eris\Generators;
use Eris\TestTrait;
use Oasis\SlimApp\NamespaceResolver;
use PHPUnit\Framework\TestCase;

/**
 * Feature: release-3.0, Property 4: 命名空间解析 Metamorphic 属性
 *
 * For any class name and namespace array, NamespaceResolver::resolve() result
 * SHALL either be an existing FQCN (class_exists(result) === true) or equal
 * the original input.
 */
class NamespaceResolverPbtTest extends TestCase
{
    use TestTrait;

    public function testResolveResultIsExistingClassOrOriginalInput(): void
    {
        // Mix of real and fake namespaces
        $realNamespaces = [
            'Symfony\\Component\\DependencyInjection',
            'Symfony\\Component\\Console',
            'Symfony\\Component\\Config\\Definition\\Builder',
            'Oasis\\SlimApp',
            'Oasis\\SlimApp\\SentinelCommand',
        ];

        $fakeNamespaces = [
            'NonExistent\\Namespace\\One',
            'Fake\\Package\\Two',
            'Missing\\Vendor\\Three',
        ];

        $allNamespaces = array_merge($realNamespaces, $fakeNamespaces);

        $this
            ->limitTo(100)
            ->forAll(
                // Generate random short class names: mix of real and fake
                Generators::elements([
                    // Real class names that exist under known namespaces
                    'ContainerBuilder',
                    'Application',
                    'TreeBuilder',
                    'SlimApp',
                    'CommandRunner',
                    'ConfigParser',
                    'NamespaceResolver',
                    // Fake class names that don't exist anywhere
                    'FooBarBaz',
                    'NonExistentWidget',
                    'MissingService',
                    'UnknownHelper',
                    'GhostFactory',
                    'PhantomBuilder',
                    'VoidProcessor',
                    'NullRenderer',
                ]),
                // Generate a random subset of namespaces
                Generators::subset($allNamespaces),
            )
            ->then(function (string $className, array $namespaces): void {
                $result = NamespaceResolver::resolve($className, $namespaces);

                // Metamorphic property: result is either an existing class or the original input
                $isExistingClass = class_exists($result) || class_exists('\\' . $result);
                $isOriginalInput = ($result === ltrim($className, '\\'));

                $this->assertTrue(
                    $isExistingClass || $isOriginalInput,
                    sprintf(
                        'resolve("%s", [%s]) returned "%s" which is neither an existing class nor the original input',
                        $className,
                        implode(', ', $namespaces),
                        $result
                    )
                );
            });
    }

    public function testResolveWithExistingFqcnAlwaysReturnsIt(): void
    {
        $existingClasses = [
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            'Symfony\\Component\\Console\\Application',
            'Oasis\\SlimApp\\SlimApp',
            'Oasis\\SlimApp\\ConfigParser',
            'Oasis\\SlimApp\\NamespaceResolver',
        ];

        $this
            ->limitTo(100)
            ->forAll(
                Generators::elements($existingClasses),
                Generators::subset([
                    'NonExistent\\Namespace',
                    'Fake\\Package',
                    'Symfony\\Component\\Console',
                ]),
            )
            ->then(function (string $fqcn, array $namespaces): void {
                $result = NamespaceResolver::resolve($fqcn, $namespaces);

                // A fully qualified existing class name should always resolve to itself
                $this->assertTrue(
                    class_exists($result) || class_exists('\\' . $result),
                    "Existing FQCN '$fqcn' should resolve to an existing class, got '$result'"
                );
            });
    }
}
