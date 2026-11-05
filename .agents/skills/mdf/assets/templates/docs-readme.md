# 文档

本页只做路由：按要找的主题打开一份页面，不通读目录。用 grep 或 CodeWiki
定位路径后，也只读命中的那一份。当前事实排在决策与工作记录之前；只链接已有
内容的页面，空目录不列出。Proposal、Bug 按 ID 打开，不把本页当工作清单。

## 按要做的事找文档

| 想做什么 | 打开 |
| --- | --- |
| 了解系统能做什么、边界在哪 | [系统边界](system/overview.md) |
| 核对配置、可观测性、错误、鉴权或限制与恢复 | [系统边界](system/overview.md) 核心模块表指向的一份主题叶 |
| 修改或核对某个内部结构、接口、数据或运维行为 | `system/` 下对应切面的一份主题叶 |
| 写测试、分 kind、核对失败语义与 skip | [测试约定](system/testing/index.md) 指向的一份主题叶 |
| 修改或核对对外可观察行为 | [用户指南](user-guide/README.md) 指向的一份主题叶 |
| 执行验证、了解目录例外 | [PROJECT.md](../PROJECT.md) |
| 需要某项长期取舍的理由 | `context/adr/` 中被事实页或用户点名的一份 ADR |
| 处理指定 ID 的意图或偏差 | [proposals/](proposals/)、[bugs/](bugs/) 中对应文件 |

## 当前事实

维护者事实在 `system/`：切面目录 `architecture/`、`interfaces/`、`data/`、
`operations/`、`testing/` 各放主题叶；架构问题以 `system/architecture/` 为准。

- [系统边界](system/overview.md)：边界与切面路由。
- [已知偏差](system/deviations.md)：偏差索引，细节链到 Bug 或对应主题叶。
- [用户指南](user-guide/README.md)：面向使用者；维护者默认不打开，改动对外行为时才打开。

## 决策

`context/adr/` 保存已确认的长期取舍与备选，只记录理由，不描述当前结构。按
`adr-<slug>` 打开单份，不把目录当阅读清单。

## 工作记录与调研

按 ID 或路径打开单个文件，不把本节目录当阅读清单。

- [随手记录](JOTS.md)：尚未分诊的原始记录。
- [proposals/](proposals/)：待实现意图及其状态记录。
- [bugs/](bugs/)：已观察到的偏差及其处理记录。
- [changes/](../changes/)：进行中与已交付的 Change 材料；发布后归入版本目录。
- `context/research/`：调研、候选方案和背景材料。
- `repowiki/`（存在时）：CodeWiki 生成的结构 Wiki，用于按需搜索符号与模块。
