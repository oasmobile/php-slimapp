# V3 升级 Bug 复现测试交接

## 当前阶段

五项 Bug 的复现测试已编写，尚未执行；等待人工运行并确认红灯原因。
Bug 仍为 open，生产代码和原有测试工具均未修复。

## 人工运行

在项目根目录使用 PHP 8.5 和现有锁定依赖执行，进程测试要求 pcntl。
本阶段所有测试都使用隔离目录，不连接真实数据库、Memcached 或其它外部服务。

```bash
export MDF_REPORT_DIR="$PWD/.mdf/reports/manual-v3-bug-repro-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$MDF_REPORT_DIR"
vendor/bin/phpunit tests/ut/Regression --log-junit "$MDF_REPORT_DIR/junit.xml"
```

逐项运行时使用同一报告目录，并给各项分配独立 JUnit 文件。

| Bug | 文件 | 场景数 | 目标现象 |
| --- | --- | --- | --- |
| bug-2AN6 | tests/ut/Regression/Bug2AN6Test.php | 1 | ORM 工厂已就绪，随后因移除的 API 报错 |
| bug-GH7A | tests/ut/Regression/BugGH7ATest.php | 1 | 生成 bootstrap 的日志级别参数触发 TypeError |
| bug-Y68Q | tests/ut/Regression/BugY68QTest.php | 4 | 正常缓存对照通过，非法缓存因 array 属性赋值报错 |
| bug-P4KU | tests/ut/Regression/BugP4KUTest.php | 4 | 无驱动环境预检通过，原进程测试失败或暴露假通过 |
| bug-1MW9 | tests/ut/Regression/Bug1MW9Test.php | 6 | 成功对照通过，非预期失败仍被总脚本返回为零 |

```bash
vendor/bin/phpunit tests/ut/Regression/Bug2AN6Test.php --log-junit "$MDF_REPORT_DIR/bug-2AN6.xml"
vendor/bin/phpunit tests/ut/Regression/BugGH7ATest.php --log-junit "$MDF_REPORT_DIR/bug-GH7A.xml"
vendor/bin/phpunit tests/ut/Regression/BugY68QTest.php --log-junit "$MDF_REPORT_DIR/bug-Y68Q.xml"
vendor/bin/phpunit tests/ut/Regression/BugP4KUTest.php --log-junit "$MDF_REPORT_DIR/bug-P4KU.xml"
vendor/bin/phpunit tests/ut/Regression/Bug1MW9Test.php --log-junit "$MDF_REPORT_DIR/bug-1MW9.xml"
```

## 判断与证据

红灯必须来自表中的目标现象；环境、自动加载或 fixture 错误不算成功复现。

- 所有子进程的完整输出、命令和退出状态保存在 `.mdf/reports/v3-bug-repro-Bug*`。
- JUnit 记录外层断言，子进程日志保留生成代码异常和覆盖率脚本的完整输出。
- 临时文件位于 `.mdf/tmp/<日期>-v3-bug-repro/`，用例结束后清理，报告独立保留。
- bug-P4KU 使用临时合并的 PHP 配置禁用驱动，不修改系统 PHP 配置；孙进程继承相同配置。
- bug-1MW9 的命令替身只测试 shell 编排，不证明真实覆盖率数据可以合并。

## 后续门槛

人工确认现象后再明确启动修复，不能将单纯的测试失败当作修复授权。

1. 记录每项实际命令、失败原因、正常对照和报告路径。
2. 人工确认哪些 Bug 已成功复现；先修正任何测试设施或环境故障。
3. 人工明确启动对应 Bug 的修复流程，再修改实现并运行回归验证。
