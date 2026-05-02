<?php

namespace Oasis\SlimApp\Tests;

use Oasis\SlimApp\SlimAppCompilerPass;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Definition;

class SlimAppCompilerPassTest extends \PHPUnit_Framework_TestCase
{
    public function testProcessSetsAppServiceClassAndFactory()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Oasis\\SlimApp']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals('Oasis\\SlimApp\\SlimApp', $appDef->getClass());
        $this->assertEquals(['Oasis\\SlimApp\\SlimApp', 'app'], $appDef->getFactory());
        $this->assertTrue($appDef->isPublic());
    }

    public function testProcessResolvesClassWithDefaultNamespace()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Symfony\\Component\\DependencyInjection']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('ContainerBuilder');
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $def->getClass()
        );
        $this->assertTrue($def->isPublic());
    }

    public function testProcessDoesNotChangeExistingFullyQualifiedClass()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Oasis\\SlimApp']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('Symfony\\Component\\DependencyInjection\\ContainerBuilder');
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $def->getClass()
        );
    }

    public function testProcessWithStringDefaultNamespace()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', 'Symfony\\Component\\DependencyInjection');

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('ContainerBuilder');
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $def->getClass()
        );
    }

    public function testProcessWithoutDefaultNamespaceParameter()
    {
        $builder = new ContainerBuilder();

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('SomeNonExistentClass');
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals('SomeNonExistentClass', $def->getClass());
    }

    public function testProcessResolvesFactoryClassWithDefaultNamespace()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Symfony\\Component\\DependencyInjection']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('ContainerBuilder');
        $def->setFactory(['ContainerBuilder', 'someMethod']);
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $factory = $def->getFactory();
        $this->assertEquals('Symfony\\Component\\DependencyInjection\\ContainerBuilder', $factory[0]);
        $this->assertEquals('someMethod', $factory[1]);
    }

    public function testProcessDoesNotResolveServiceReferenceFactory()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Oasis\\SlimApp']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('Oasis\\SlimApp\\SlimApp');
        $def->setFactory(['@some_service', 'someMethod']);
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $factory = $def->getFactory();
        $this->assertEquals('@some_service', $factory[0]);
    }

    public function testProcessWithMultipleDefaultNamespaces()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', [
            'NonExistent\\Namespace',
            'Symfony\\Component\\DependencyInjection',
        ]);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $def->setClass('ContainerBuilder');
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertEquals(
            'Symfony\\Component\\DependencyInjection\\ContainerBuilder',
            $def->getClass()
        );
    }

    public function testConstructorStoresClassname()
    {
        $pass = new SlimAppCompilerPass('My\\Custom\\App');
        $ref  = new \ReflectionProperty($pass, 'classname');
        $ref->setAccessible(true);
        $this->assertEquals('My\\Custom\\App', $ref->getValue($pass));
    }

    public function testProcessSetsAllServicesPublic()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Oasis\\SlimApp']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def1 = new Definition('Oasis\\SlimApp\\SlimApp');
        $builder->setDefinition('service1', $def1);

        $def2 = new Definition('Oasis\\SlimApp\\ConsoleApplication');
        $def2->setPublic(false);
        $builder->setDefinition('service2', $def2);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertTrue($def1->isPublic());
        $this->assertTrue($def2->isPublic());
    }

    public function testProcessWithNoClassDefinition()
    {
        $builder = new ContainerBuilder();
        $builder->setParameter('default.namespace', ['Oasis\\SlimApp']);

        $appDef = new Definition();
        $builder->setDefinition('app', $appDef);

        $def = new Definition();
        $builder->setDefinition('test.service', $def);

        $pass = new SlimAppCompilerPass('Oasis\\SlimApp\\SlimApp');
        $pass->process($builder);

        $this->assertNull($def->getClass());
    }
}
