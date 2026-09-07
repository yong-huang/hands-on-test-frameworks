#!/usr/bin/env bash
# =============================================================================
# mock_lab.sh — lab 04 主演示脚本：mock / fake / monkeypatch / freezegun
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "确认 12 条用例收集齐全，且没有任何一条会真的联网发信"
    $PY -m pytest $INI --collect-only -q | tail -2
}

do_observe() {
    step "observe" "全量运行：mock/fake 两版同场景各自通过"
    $PY -m pytest $INI -q

    step "observe" "① 只跑 fake 相关用例（InMemoryMailer 的故障注入能力）"
    $PY -m pytest $INI -k "fake or broadcast_continues" -q

    step "observe" "② 只跑时间冻结用例——无论真实日期是哪天，结果永远确定"
    $PY -m pytest $INI -k "campaign" -v 2>&1 | grep -E "PASSED|passed" | head -5
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
