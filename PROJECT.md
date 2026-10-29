# SlimApp 项目维护

本页是维护者与 Agent 的起点；运行时事实按下方主题入口查阅。

## 验证卡片

环境要求：PHP >=8.5、Composer 2、已按 `composer.lock` 安装开发依赖；smoke/release 需要 pcntl。

| 入口 | `.mdf/modules.yaml` 中的命令 |
| --- | --- |
| lint | `vendor/bin/phpstan analyse --no-progress --debug` |
| build | `git diff --check` |
| quick | `vendor/bin/phpunit --testsuite quick --log-junit "$MDF_REPORT_DIR/junit.xml"` |
| smoke | `vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"` |
| release | `vendor/bin/phpunit --testsuite ut,pbt --log-junit "$MDF_REPORT_DIR/junit.xml"` |

MDF 创建每次运行的报告目录并设置 `MDF_REPORT_DIR`；独立运行时先设置该变量并创建目录。

## 技术栈与维护

版本与依赖以 `composer.json` 和 `composer.lock` 为准。

- PHP >=8.5；Symfony ^8.0；oasis/utils ^3.2、oasis/http ^3.8、oasis/logging ^3.0。
- PHPUnit ^13、Eris ^1.1、PHPStan ^2.1 level 8；静态分析沿用仓库 baseline。
- 用 `composer install --no-interaction --prefer-dist` 恢复锁定依赖。
- lint 使用 `--debug` 串行分析，避免受限环境下并行 worker 监听本地端口。
- 实现位于 `src/`，自动测试位于 `tests/ut/` 与 `tests/pbt/`。
- 已发布版本由 Git tag 管理；最新版本见 `CHANGELOG.md`。

## 顶层例外与生成物

本表仅列标准源码、测试与 MDF 布局以外需要解释的目录。

| 路径 | 保留理由 |
| --- | --- |
| `bin/` | Composer 分发的框架 CLI 入口 |
| `config/` | 框架 CLI 自身的容器配置 |
| `init-ut/` | 通过 Composer path 仓库验证工程生成器的独立测试工程 |
| `graphify-out/` | 可陈旧的 Graphify 辅助图谱；不作为事实或 CodeWiki |
| `.agents/`、`.cursor/`、`.kiro/` | 各宿主的项目级 Skill 与活动规则 |
| `vendor/`、`.idea/` | 已忽略的本地依赖与 IDE 状态 |

缓存、日志及测试临时文件由运行环境产生；MDF 日志、报告、临时文件不提交。

## 文档入口

按任务打开对应页面，不通读目录。

- [系统边界](docs/system/overview.md)
- [文档导航](docs/README.md)
- [测试约定](docs/system/testing/index.md)
- [领域术语](GLOSSARY.md)
- [历史工作流档案](docs/context/research/legacy-agent-workflow/README.md)
