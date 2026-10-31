<?php
declare(strict_types=1);

namespace Oasis\SlimApp\BuiltInCommands\Templates;

use Symfony\Component\Console\Question\Question;
use Symfony\Component\Yaml\Yaml;

trait ServicesTemplate
{
    protected function prepareServicesYaml(): void
    {
        //$helper = $this->getHelper('question');
        
        $filename = $this->rootDir . "/config/services.yml";
        $services = [
            "imports"    => [
            
            ],
            "parameters" => [
                "default.namespace" => [
                    "Oasis\\Mlib\\",
                    $this->projectNamespace,
                ],
            ],
            "services"   => [
                "app" => [
                    "properties" => [
                        "logging" => [
                            "path"  => "%app.dir.log%",
                            "level" => "debug",
                        ],
                        "cli"     => [
                            "name"    => $this->projectName,
                            "version" => "0.1",
                        ],
                        "http"    => [
                            "cache_dir" => "%app.dir.cache%",
                            "routing"   => [
                                "path"       => "%app.dir.config%/routes.yml",
                                "namespaces" => [$this->projectNamespace, $this->projectNamespace . "Controllers\\"],
                            ],
                            "twig"      => [
                                "template_dir" => "%app.dir.template%",
                                "globals"      => [
                                    "app" => "@app",
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ];
        if ($this->ormSupportEnabled) {
            $services['services']['memcached']                                  = [
                "class" => "Memcached",
                "calls" => [
                    [
                        "addServer",
                        ['%app.memcached.host%', '%app.memcached.port%'],
                    ],
                ],
            ];
            $services['services']['entity_manager']                             = [
                "class"   => "Doctrine\\ORM\\EntityManager",
                "factory" => [
                    $this->projectNamespace . "Database\\" . $this->mainClassname . "Database",
                    "getEntityManager",
                ],
            ];
            $services['services']['app']['properties']['http']['injected_args'] = [
                "@entity_manager",
            ];
        }
        if ($this->odmSupportEnabled) {
            $services['services']['item_manager']                               = [
                "class"   => "Oasis\\Mlib\\ODM\\Dynamodb\\ItemManager",
                "factory" => [
                    $this->projectNamespace . "Database\\" . $this->mainClassname . "Database",
                    "getItemManager",
                ],
            ];
            $services['services']['app']['properties']['http']['injected_args'] = [
                "@item_manager",
            ];
        }
        $serviceYaml = Yaml::dump($services, 7);
        $this->writeToTempFile($filename, $serviceYaml);
    }
}
