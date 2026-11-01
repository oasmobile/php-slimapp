---
title: "覆盖率脚本回归"
doc_type: system-testing
command: 'vendor/bin/phpunit tests/ut/Regression/Bug1MW9Test.php --log-junit "$MDF_REPORT_DIR/junit.xml"'
evidence:
  - path: "tests/ut/Regression/Bug1MW9Test.php"
  - path: "tests/ut/Regression/Fixtures/coverage_php.php"
  - path: "tests/run_all_coverage.sh"
---

# 覆盖率脚本回归

本套件验证覆盖率 shell 脚本能保留非预期失败状态，并接受约定的业务失败。

## 构成

套件运行 Bug1MW9Test 的六个场景，不修改既有断言或其它套件成员。

- 正常执行及预期 parallel_fail 退出码的成功对照。
- PHPUnit 断言失败。
- parallel_ok、parallel_fail、sentinel_once、sentinel_parallel 非预期退出。

## 依赖与报告

套件依赖 PHP 8.5、Bash、锁定的开发依赖及临时目录写权限，不需要外部服务。
用例以 PHP 命令替身执行真实 shell 编排，不证明真实覆盖率数据可以合并。
MDF 提供 MDF_REPORT_DIR 并保存 JUnit；子进程证据位置按测试约定执行。

## 边界

本套件是交付选题记录，不替代 lint、build、quick 或完整 smoke。
完整分支验证仍按项目原有入口执行，已知失败不得跳过或视为通过。
