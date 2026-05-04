<?php
declare(strict_types=1);

namespace Oasis\SlimApp;

class NamespaceResolver
{
    /**
     * 给定一个短类名和命名空间列表，尝试解析为完整类名。
     * 如果在任何命名空间下找到存在的类，返回 FQCN；否则返回原始输入。
     *
     * @param string[] $namespaces
     */
    public static function resolve(string $className, array $namespaces): string
    {
        $className = ltrim($className, '\\');

        if (class_exists($className) || class_exists('\\' . $className)) {
            return $className;
        }

        foreach ($namespaces as $ns) {
            $ns = trim($ns, '\\');
            $fullClass = $ns . '\\' . $className;
            if (class_exists($fullClass)) {
                return $fullClass;
            }
        }

        return $className;
    }
}
