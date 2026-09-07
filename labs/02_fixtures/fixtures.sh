#!/usr/bin/env bash
# =============================================================================
# fixtures.sh — lab 02 主演示脚本：fixture 作用域 / teardown / 工厂
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "确认 13 条用例被收集、conftest 的 fixture 全部可见"
    $PY -m pytest $INI --collect-only -q | tail -2
}

do_observe() {
    step "observe" "全量运行：注意第一条用例就证明 session 连接只建了一次"
    # FakeDB 实例化需要 0.2s，但只会出现一次——session 作用域的直接证据
    $PY -m pytest $INI -q

    step "observe" "① 只跑工厂 fixture 用例（-k 圈选）"
    $PY -m pytest $INI -k factory -q

    step "observe" "② 查看某条用例的 fixture 执行计划（--setup-show 打开 setup/teardown 幕后）"
    $PY -m pytest $INI --setup-show -k "test_add_user and not isolated" -q 2>&1 | grep -E "SETUP|TEARDOWN|PASSED" | head -12
}

do_clean() {
    step "clean" "清理缓存，回到实验前状态"
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
