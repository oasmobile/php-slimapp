#!/usr/bin/env bash
# 运行全量测试并合并覆盖率；任何非预期失败均返回非零状态。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COV_DIR=$(mktemp -d)
PHP="${PHP:-php}"
status=0
trap 'rm -rf "$COV_DIR"' EXIT

echo "=== 收集覆盖率到 $COV_DIR ==="
"$PHP" -v

echo "--- PHPUnit 主测试 (ut + pbt) ---"
if ! "$PHP" -d pcov.enabled=1 "$PROJECT_DIR/vendor/bin/phpunit" \
    --coverage-php "$COV_DIR/phpunit.cov"; then
    status=1
fi

run_case() {
    local script="$1" case_name="$2" expected="$3"
    local covfile="$COV_DIR/$case_name.cov" logfile="$COV_DIR/$case_name.log"
    local result=0
    COVERAGE_FILE="$covfile" "$PHP" -d pcov.enabled=1 "$SCRIPT_DIR/scripts/$script" \
        "$case_name" >"$logfile" 2>&1 || result=$?
    cat "$logfile"
    if [ "$result" -ne "$expected" ] || grep -Eq 'Fatal error|Uncaught' "$logfile"; then
        echo "Unexpected failure: $case_name, exit=$result, expected=$expected" >&2
        status=1
    fi
    if [ ! -f "$covfile" ]; then
        echo "Missing coverage: $case_name" >&2
        status=1
    fi
}

echo "--- Fork 进程测试覆盖率 ---"
run_case parallel_command_test.php parallel_ok 0
run_case parallel_command_test.php parallel_fail 255
run_case sentinel_command_test.php sentinel_once 0
run_case sentinel_command_test.php sentinel_parallel 0

echo "=== 合并覆盖率报告 ==="
if ! "$PHP" -d pcov.enabled=1 "$SCRIPT_DIR/scripts/merge_coverage.php" "$COV_DIR"/*.cov; then
    status=1
fi
exit "$status"
