<?php
/**
 * Created by PhpStorm.
 * User: minhao
 * Date: 2016-01-09
 * Time: 18:08
 */

namespace Oasis\SlimApp;

use Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;

class SlimAppCompilerPass implements CompilerPassInterface
{
    
    /**
     * You can modify the container here before it is dumped to PHP code.
     *
     * @param ContainerBuilder $container
     */
    public function process(ContainerBuilder $container)
    {
        if ($container->hasParameter('default.namespace')) {
            $defaultNamespaces = $container->getParameter('default.namespace');
            if (is_string($defaultNamespaces)) {
                $defaultNamespaces = [$defaultNamespaces];
            }

            foreach ($container->getDefinitions() as $definition) {
                if (($class = $definition->getClass())
                    && !class_exists($class)
                ) {
                    foreach ($defaultNamespaces as $ns) {
                        $full_class = "$ns\\$class";
                        if (class_exists($full_class)) {
                            $definition->setClass($full_class);
                            break;
                        }
                    }
                }

                if (($factory = $definition->getFactory())
                    && is_array($factory)
                    && (0 !== strpos($factory[0], "@"))
                    && !class_exists($class = $factory[0])
                ) {
                    foreach ($defaultNamespaces as $ns) {
                        $full_class = "$ns\\$class";
                        if (class_exists($full_class)) {
                            $definition->setFactory([$full_class, $factory[1]]);
                            break;
                        }
                    }
                }
            }
        }
    }
}
