#!/usr/bin/env bash
#
# 运行全量测试并合并覆盖率（含 fork 进程的覆盖率）
#
# 用法: bash tests/run_all_coverage.sh
#   或: PHP=/path/to/php bash tests/run_all_coverage.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COV_DIR=$(mktemp -d)
PHP="${PHP:-php}"

echo "=== 收集覆盖率到 $COV_DIR ==="
echo "PHP: $($PHP -v | head -1)"

# 1) PHPUnit 主测试 — ut + pbt（输出覆盖率到 .cov 文件）
echo ""
echo "--- PHPUnit 主测试 (ut + pbt) ---"
$PHP -d pcov.enabled=1 "$PROJECT_DIR/vendor/bin/phpunit" \
    --coverage-php "$COV_DIR/phpunit.cov" \
    2>&1 | grep -E "^(OK|FAIL|Tests:|Time:)" || true

# 2) Fork 脚本覆盖率
echo ""
echo "--- Fork 进程测试覆盖率 ---"
for case in parallel_ok parallel_fail; do
    covfile="$COV_DIR/parallel_${case}.cov"
    COVERAGE_FILE="$covfile" $PHP -d pcov.enabled=1 "$SCRIPT_DIR/scripts/parallel_command_test.php" "$case" 2>/dev/null || true
    [ -f "$covfile" ] && echo "  collected: $case"
done

for case in sentinel_once sentinel_parallel; do
    covfile="$COV_DIR/sentinel_${case}.cov"
    COVERAGE_FILE="$covfile" $PHP -d pcov.enabled=1 "$SCRIPT_DIR/scripts/sentinel_command_test.php" "$case" 2>/dev/null || true
    [ -f "$covfile" ] && echo "  collected: $case"
done

# 3) 合并所有 .cov 文件
echo ""
echo "=== 合并覆盖率报告 ==="
$PHP -d pcov.enabled=1 "$SCRIPT_DIR/scripts/merge_coverage.php" "$COV_DIR"/*.cov

# 清理
rm -rf "$COV_DIR"
