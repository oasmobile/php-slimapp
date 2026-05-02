# Configuration

## 配置文件

### config.yml

应用配置文件，位于 `config/` 目录。使用 symfony/config 进行 schema 校验。

- 格式: YAML
- 校验: 使用方需实现 `Symfony\Component\Config\Definition\ConfigurationInterface`
- 缓存: 序列化到 `$cachePath/config.cache`，始终检测文件变更（`ConfigCache` debug 参数硬编码为 `true`）
- 参数化: 所有配置值以 `app.` 前缀扁平化写入 `parameterized_helper.yml`，并注入 DI 容器

典型结构:

```yaml
is_debug: true
dir:
    log: /data/logs/project
    data: /data/project
    cache: ./cache
    template: ./templates
db:
    host: localhost
    port: 3306
    user: project
    password: project
    dbname: project
memcached:
    host: localhost
    port: 11211
```

### services.yml

DI 容器定义文件，位于 `config/` 目录。

- 格式: YAML（symfony/dependency-injection 格式）
- 三部分: `imports`、`parameters`、`services`
- 参数引用: `%app.dir.log%`（配置值）、`%custom.param%`（自定义参数）
- 服务引用: `@service_id`
- `default.namespace` 参数: 数组，用于自动补全不含完整命名空间的类名
- 服务可见性: 默认 private（Symfony 标准约定），需要通过 `getService()` 获取的服务须显式声明 `public: true`；`app` 服务由框架自动设为 public

### `app` 服务

`services.yml` 中必须定义的特殊服务。构造由框架自动完成，使用方通过 `properties` 配置:

| 属性 | 说明 |
|------|------|
| `logging.path` | 日志目录 |
| `logging.level` | 日志级别（PSR-3 字符串） |
| `logging.pattern` | 日志文件名模式 |
| `logging.handlers` | 额外的 Monolog handler 数组 |
| `cli.name` | Console 应用名称 |
| `cli.version` | Console 应用版本 |
| `cli.commands` | 自定义命令数组（服务引用） |
| `http` | HTTP Kernel 配置（传递给 oasis/http） |

### Sentinel YAML

Daemon Sentinel 的命令调度配置文件，作为命令参数传入。

```yaml
commands:
    <daemon-name>:
        name: <command-name>
        args: { ... }
        parallel: 1
        once: false
        alert: true
        interval: 0
        frequency: 0
        frequency_fixed: false
```

- `args` 中支持 `%param%` 引用容器参数
- `args` 中支持 `$PARALLEL_INDEX` 特殊变量

## 配置访问

| 方式 | 方法 | 示例 |
|------|------|------|
| 配置 key | `$app->getMandatoryConfig('dir.log')` | 层级用 `.` 连接 |
| 配置 key（可选） | `$app->getOptionalConfig('dir.log', STRING_TYPE, default)` | 不存在返回默认值 |
| 参数 key | `$app->getParameter('app.dir.log')` | 加 `app.` 前缀 |
| 容器内 | `%app.dir.log%` | services.yml / twig 中使用 |
