---
title: "运行限制与恢复"
doc_type: system-operations
evidence:
  - path: "src/SlimApp.php"
  - path: "src/AbstractParallelCommand.php"
  - path: "src/SentinelCommand/"
  - path: "src/BuiltInCommands/ClearCacheCommand.php"
---

# 运行限制与恢复

本页记录文件缓存与后台进程的运行限制。

## 运行前提

后台进程和缓存各有环境前提。

- 并行命令与 Sentinel 需要 pcntl；不能将缺少扩展视为任务成功。
- 日志目录和缓存目录需要可写权限。
- 配置、编译容器和日志目录不应由不可信用户写入。
- Sentinel 的固定频率模式允许重叠，业务任务须自行保证并发安全。
- 框架不提供业务任务的持久队列、断点或数据库迁移能力。

## 更新与恢复

部署者应避免跨版本复用已加载的编译容器。

1. 停止旧应用进程，保存需要保留的业务日志。
2. 使用旧环境可用的清缓存命令，或按已确认的部署路径清理配置与 HTTP 缓存内容。
3. 安装新版本依赖并启动新进程，让其重新构建缓存。
4. 检查启动、服务验证输出和业务测试结果。

生产模式的容器缓存不检查资源新鲜度；不能承诺升级后首次启动自动纠正旧容器缓存。
配置缓存的内容校验属于另一条路径，见[缓存数据](../data/cache.md)。
`slimapp:cache:clear` 保留缓存根目录，并删除 Finder 枚举到的直属非点号条目。
其中的子目录会递归删除；缓存根内的点号条目保持不变。
