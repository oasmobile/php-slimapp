# 项目维护

本文件面向项目维护者（含 Agent），是 `AGENTS.md` 之后的第一份项目文档。

## 验证卡片

Agent 执行维护改动时只读本节。列出环境要求与 `.mdf/manifest.yaml` 的五个验证
入口；命令以仓库配置和脚本为准。named suite、点名执行与 kind、失败语义、skip 见
`docs/system/testing/index.md`，不在此复述。

| 入口 | 命令 | 何时跑 |
| --- | --- | --- |
| lint | 待填 | 任何改动 |
| build | 待填 | 任何改动 |
| quick | 待填 | 任何改动 |
| smoke | 待填 | feature、bugfix、hotfix 收口 |
| release | 待填 | 仅 release 收口 |

## 技术栈

一行级列出语言、构建与主要运行时；细节下沉到 `docs/system/`。

## 维护约束

记录项目专属的目录、生成物、发布和维护约束。仅维护者需要的内容写在本文件或
下沉到 `docs/system/`，不写入根 `README.md`。运行时配置属于
`docs/system/operations/configuration.md`。接口、数据与运行时行为不复述
`docs/system/` 事实页，只保留指向对应页面的链接。

## 目录约定

- 记录业务实现与测试的实际目录：单 module 为 `src/` 与 `tests/`；多 module 为各
  `<module>/src/` 与 `<module>/tests/`。并记录生成物目录。
- 仅列出允许处于仓库顶层的例外项目项及其理由。

## 文档入口

- 系统边界：`docs/system/overview.md`
- `docs/README.md`
- 测试约定：`docs/system/testing/index.md`
