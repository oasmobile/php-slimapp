<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

use Symfony\Component\Config\Definition\ConfigurationInterface;
use Symfony\Component\Config\Definition\Processor;

class ConfigParser
{
    /**
     * 解析原始配置数组，返回处理后的配置。
     *
     * @param array<int, array<string, mixed>> $rawConfigs 原始配置数组（可多个，会被 merge）
     * @param ConfigurationInterface $definition 配置定义
     * @return array<string, mixed> 处理后的配置树
     */
    public static function parse(array $rawConfigs, ConfigurationInterface $definition): array
    {
        $processor = new Processor();

        return $processor->processConfiguration($definition, $rawConfigs);
    }

    /**
     * 将配置树扁平化为 key => value 的参数映射。
     *
     * @param array<string, mixed> $configs 配置树
     * @param string $prefix 前缀（默认 'app.'）
     * @return array<string, mixed> 扁平化后的参数映射
     */
    public static function flatten(array $configs, string $prefix = 'app.'): array
    {
        $result  = [];
        $recurse = function (array $value, string $prefix) use (&$result, &$recurse): void {
            foreach ($value as $k => $v) {
                $result[$prefix . $k] = $v;
                if (is_array($v)) {
                    $recurse($v, $prefix . $k . '.');
                }
            }
        };
        $recurse($configs, $prefix);

        return $result;
    }

    /**
     * 从扁平化参数中按 key 检索值。
     *
     * @param array<string, mixed> $flatParams 扁平化参数
     * @param string $key 参数 key（如 'app.dir.log'）
     * @return mixed
     */
    public static function retrieve(array $flatParams, string $key): mixed
    {
        return $flatParams[$key] ?? null;
    }
}
