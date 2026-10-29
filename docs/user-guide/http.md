---
title: "HTTP 接入"
doc_type: user-guide
evidence:
  - path: "src/SlimApp.php"
  - path: "composer.json"
  - path: "tests/integration/http.php"
  - path: "tests/integration/fixtures/TestController.php"
---

# HTTP 接入

SlimApp 将 HTTP 请求处理委托给 oasis/http 的 MicroKernel。

## 配置与启动

在 `app` 服务的 `http` 属性传入 MicroKernel 配置。

```yaml
services:
    app:
        properties:
            http:
                routing:
                    path: "%app.dir.config%/routes.yml"
                    namespaces: ["App\\Controllers\\"]
```

Web 入口从使用方引导文件取得应用并运行 Kernel。

```php
$app = require __DIR__ . '/../bootstrap.php';
$app->getHttpKernel()->run();
```

## 使用 Kernel

HTTP 方法调用在 `getHttpKernel()` 返回的对象上，而非 SlimApp 本身。

- SlimApp 将自身注入控制器参数，并向 Kernel 提供容器参数。
- routing、Twig、middleware、CORS 和 security 由 oasis/http 处理。
- 模板、URL 和响应便捷方法也属于 MicroKernel。
- 具体配置与升级兼容性以已安装 oasis/http 的接口及使用方测试为准。

框架仓库的 `tests/integration/http.php` 是人工集成入口，不等于生产部署配置。
