<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

use Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;

class SlimAppCompilerPass implements CompilerPassInterface
{
    public function __construct(
        protected readonly string $classname,
    ) {}

    public function process(ContainerBuilder $container): void
    {
        if ($container->hasParameter('default.namespace')) {
            $defaultNamespaces = $container->getParameter('default.namespace');
            if (is_string($defaultNamespaces)) {
                $defaultNamespaces = [$defaultNamespaces];
            }
            if (!is_array($defaultNamespaces)) {
                return;
            }

            foreach ($container->getDefinitions() as $id => $definition) {

                // We need to prepare 'app' service
                if ($id === 'app') {
                    $definition->setClass($this->classname);
                    $definition->setFactory([$this->classname, 'app']);
                    $definition->setPublic(true);
                    continue;
                }

                // Resolve class name using default namespaces
                if (($class = $definition->getClass())
                    && !class_exists($class)
                    && !class_exists('\\' . $class)
                ) {
                    $resolved = NamespaceResolver::resolve($class, $defaultNamespaces);
                    if ($resolved !== $class) {
                        $definition->setClass($resolved);
                    }
                }

                // Resolve factory class name using default namespaces
                if (($factory = $definition->getFactory())
                    && is_array($factory)
                    && is_string($factory[0])
                    && (strpos($factory[0], '@') !== 0)
                    && !class_exists($class = $factory[0])
                    && !class_exists('\\' . $class)
                ) {
                    $resolved = NamespaceResolver::resolve($class, $defaultNamespaces);
                    if ($resolved !== $class) {
                        $definition->setFactory([$resolved, $factory[1]]);
                    }
                }
            }
        }
    }
}
