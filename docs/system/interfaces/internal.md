---
title: "内部接口"
doc_type: system-interfaces
evidence:
  - path: "src/SlimApp.php"
  - path: "src/SlimAppCompilerPass.php"
  - path: "src/NamespaceResolver.php"
  - path: "src/ConfigParser.php"
  - path: "tests/ut/SlimAppCompilerPassTest.php"
---

# 内部接口

本页定义组件协作契约；对外操作示例保留在用户指南。

## 应用与容器

SlimApp 使用编译后的 Symfony 容器，并保留当前应用单例。

- `app()` 首次调用时创建静态实例，后续调用复用该实例。
- `__set()` 将点号、下划线和连字符属性名映射为 `set<Name>Property()`。
- 只有对应 setter 存在时才应用该属性。
- `getService()` 从容器取对象，可选校验对象类型。
- `setService()`、`resetService()` 委托容器设置服务值。
- `getServiceIds()` 返回容器的服务 ID；private 服务并不因此变为 public。

## 编译期命名空间

编译 Pass 的行为受 `default.namespace` 参数约束。

| 输入 | 行为 |
| --- | --- |
| 参数不存在 | 不遍历定义，也不自动配置 app |
| 参数为字符串 | 作为一个候选命名空间 |
| 参数为数组 | 按其顺序解析 |
| 参数为其他类型 | 提前返回 |
| app 定义且参数有效 | 设置当前 SlimApp 类、app() 工厂及 public |
| 已存在的完整类名 | 保持不变 |
| 不存在的短类名 | 按候选命名空间取首个存在类 |
| 仍未找到类 | 返回去除前导反斜线后的原名 |

非 app 服务的可见性仍由 Symfony 服务定义决定；factory 中以 `@` 开头的服务引用不按类名解析。

## 配置工具与 Kernel

ConfigParser 和 HTTP 适配器各负责独立的转换边界。

- `parse()` 把多份配置交给 Symfony Processor 按 schema 合并校验。
- `flatten()` 递归生成点号键，同时保留中间数组项；默认前缀为 `app.`。
- `retrieve()` 对缺失的扁平 key 返回 null。
- `getHttpKernel()` 惰性构建 MicroKernel，注入当前 SlimApp 与容器参数。
- HTTP 便捷方法属于 MicroKernel，SlimApp 不转发这些方法。

异常类型与失败行为见[错误模型](errors.md)。
