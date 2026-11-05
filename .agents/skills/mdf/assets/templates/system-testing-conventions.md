---
title: "测试约定"
doc_type: system-testing
evidence:
  - path: PROJECT.md
---

# 测试约定

本页是项目级测试规则的起步叶。测试层级、kind、hermetic 与 suite 语义以 MDF
契约为准，本页只写本项目的落地规则。主题混杂或超过 450 行时拆到 `kinds.md`、
`failure.md`、`suites.md`、`environment.md`；本页改为链接。

## Kind 与归属

写明本项目 UT、PT、IT、E2E 各自的目录或 marker，以及 test case 如何归入各 suite。
尚未有对应测试时不把该 kind 写成已采用。

## 失败语义

非零退出、warning、notice、deprecated、skip、xfail、xpass 与空选择都是失败。
写明各入口如何保证这些情况非零退出（如运行器参数或配置文件）。

## 豁免

逐条列出第三方依赖 warning 的精确豁免：类别、来源模块、理由与用户确认记录。
没有豁免时写「无」。

## 不在 target 内的 test

test case 不属于某 suite 时由成员选择规则排除，不在运行时 skip。

## Suite

每个 suite 一节，named suite 按同样格式追加。每节写明：

- 目的
- 入口命令：须把 JUnit XML 写进 `$MDF_REPORT_DIR`
- 成员选择规则、预算与环境
- 点名执行 test case / test 的命令模板

### quick

只含 hermetic 的 UT 与 PT；任何改动都跑。

### smoke

包含 quick；feature、bugfix、hotfix 的 verify branch 跑到此。

### release

包含 smoke，发版所需的 test case；仅 release 的 verify branch 跑到此。全部 test
case 的集合通常没有独立入口。
