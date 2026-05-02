<?php
declare(strict_types=1);

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\NamespaceResolver;
use PHPUnit\Framework\TestCase;

class NamespaceResolverTest extends TestCase
{
    public function testFullyQualifiedClassNameReturnedDirectly(): void
    {
        $result = NamespaceResolver::resolve(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            ['Some\\Namespace']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }

    public function testFullyQualifiedClassNameWithLeadingBackslash(): void
    {
        $result = NamespaceResolver::resolve(
            '\\Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            ['Some\\Namespace']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }

    public function testShortClassNameResolvedUnderNamespace(): void
    {
        $result = NamespaceResolver::resolve(
            'ContainerBuilder',
            ['Symfony\\Component\\DependencyInjection']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }

    public function testNonExistentClassNameReturnedAsIs(): void
    {
        $result = NamespaceResolver::resolve(
            'CompletelyNonExistentClassName',
            ['Symfony\\Component\\DependencyInjection', 'Oasis\\SlimApp']
        );

        $this->assertEquals('CompletelyNonExistentClassName', $result);
    }

    public function testMultipleNamespacesFirstMatchWins(): void
    {
        // ContainerBuilder exists under Symfony\Component\DependencyInjection
        // but not under NonExistent\Namespace
        $result = NamespaceResolver::resolve(
            'ContainerBuilder',
            ['NonExistent\\Namespace', 'Symfony\\Component\\DependencyInjection']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }

    public function testEmptyNamespacesArrayReturnsOriginal(): void
    {
        $result = NamespaceResolver::resolve('SomeClass', []);

        $this->assertEquals('SomeClass', $result);
    }

    public function testNamespaceWithTrailingBackslash(): void
    {
        $result = NamespaceResolver::resolve(
            'ContainerBuilder',
            ['Symfony\\Component\\DependencyInjection\\']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }

    public function testClassNameWithLeadingBackslashAndNamespaceResolution(): void
    {
        $result = NamespaceResolver::resolve(
            '\\ContainerBuilder',
            ['Symfony\\Component\\DependencyInjection']
        );

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $result
        );
    }
}
