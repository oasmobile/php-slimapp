# 领域术语

本页统一 SlimApp 的领域用语，不记录计划或交付状态。

| 术语 | 含义与区别 |
| --- | --- |
| SlimApp | 应用级入口；整合配置、服务容器和运行入口 |
| 使用方项目 | 安装 oasis/slimapp 的业务工程；不同于框架仓库本身 |
| 配置定义 | Symfony ConfigurationInterface；定义使用方配置的结构与校验 |
| 配置 key | 应用配置树中的点号路径，例如 dir.log |
| 参数 key | 容器参数名；应用配置参数通常带 app. 前缀 |
| 服务 | 由 Symfony DI 容器管理的对象 |
| MicroKernel | oasis/http 的 HTTP 处理入口；通过 SlimApp 获取 |
| Console | Symfony Console 应用，注册并执行命令 |
| Sentinel | 读取调度配置并管理子进程的守护命令 |
| CommandRunner | Sentinel 对单个命令实例的调度状态与子进程执行器 |
| parallel index | 同一调度命令的实例索引，从 0 开始 |
| MDF init | 本仓库文档与交付流程的初始化；不同于 slimapp:project:init |
