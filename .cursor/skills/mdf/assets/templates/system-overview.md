---
title: "系统边界"
doc_type: system-boundary
evidence:
  - path: "{{MDF_EVIDENCE_PATH}}"
---

# 系统边界

本页只描述边界并路由到各切面主题叶，不复述叶子契约。

## 目的

{{MDF_CURRENT_SYSTEM_PURPOSE}}

## 用户与参与方

{{MDF_CURRENT_ACTORS}}

## 范围内

{{MDF_CURRENT_IN_SCOPE}}

## 范围外

{{MDF_CURRENT_OUT_OF_SCOPE_AND_NOT_YET_ASSEMBLED}}

## 外部依赖

{{MDF_CURRENT_EXTERNAL_DEPENDENCIES}}

## 边界证据

{{MDF_HOW_TO_VERIFY_THE_BOUNDARY}}

## 切面路由

- 架构：{{MDF_ARCHITECTURE_TOPIC_LINKS}}
- 接口：{{MDF_INTERFACE_TOPIC_LINKS}}
- 数据：{{MDF_DATA_TOPIC_LINKS}}
- 运行与运维：{{MDF_OPERATIONS_TOPIC_LINKS}}
- 测试：[测试约定](testing/index.md)

## 核心模块

每行必须是主题叶链接，或「不适用：」加一句理由。不预建空页。

| 模块 | 打开 |
| --- | --- |
| 配置 | 不适用：尚无运行时配置面 |
| 可观测性 | 不适用：尚无可观测实现 |
| 错误 | 不适用：尚无独立错误模型 |
| 鉴权 | 不适用：尚无鉴权面 |
| 限制与恢复 | 不适用：尚无运行限制或恢复面 |

特性开关、多租户、i18n、插件点按需建叶；缺页不构成 finding。
