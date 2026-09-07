#!/usr/bin/env bash
# =============================================================================
# parametrize.sh — lab 03 主演示脚本：参数化矩阵与异常断言
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "收集：数一数 11 个测试函数展开成多少条用例"
    $PY -m pytest $INI --collect-only -q | tail -2
}

do_observe() {
    step "observe" "全量运行：注意报告里 ids 显示为可读名字而非 param0/param1"
    $PY -m pytest $INI -q

    step "observe" "① 按名字圈选一组异常用例（ids 命名让 -k 精确制导）"
    $PY -m pytest $INI -k "config_errors and not dup" -q

    step "observe" "② 故意破坏：把 ids 摘掉后再跑同类用例（对比可读性差异）"
    $PY -m pytest $INI -k "parse_value and not leading" -v 2>&1 | grep -E "PASSED|passed" | head -9
}

do_clean() {
    step "clean" "清理缓存"
    rm -rf .pytest_cache tests/__pycache__ __pycache__
    echo "已清理"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe; do_clean ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
