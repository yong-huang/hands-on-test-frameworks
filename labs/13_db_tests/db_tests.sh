#!/usr/bin/env bash
# =============================================================================
# db_tests.sh — lab 13 主演示脚本：两种隔离对比 + 迁移幂等 + 并发冲突
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "收集 10 条数据层用例（隔离 5 + 迁移 3 + 并发 2）"
    $PY -m pytest $INI --collect-only -q | tail -2
}

do_observe() {
    step "observe" "① 全量：隔离/迁移/并发一次跑齐（数据层直测，不起 HTTP 服务）"
    $PY -m pytest $INI -q

    step "observe" "② 只跑 truncate 策略（共享库 + 截表）"
    $PY -m pytest $INI -q -k "truncate"

    step "observe" "③ 只跑 fresh 策略（每用例全新库）对比"
    $PY -m pytest $INI -q -k "fresh"

    step "observe" "④ 并发写冲突演示：裸 SQLite 必锁，应用层串行化全成功"
    $PY -m pytest $INI -v -q -k concurrent 2>&1 | grep -E "PASSED|passed" | head -4
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
