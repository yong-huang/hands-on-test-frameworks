#!/usr/bin/env bash
# =============================================================================
# sharding_scheduler.sh — architect 11 主演示脚本：
# 建历史档案 → 4 片 LPT 并行执行 → 提速/均衡验收 → 无历史兜底演示 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 串行全量跑池子（labs/09+03+13 共 246 条），junit 建历史耗时档案"
    "$PY" sharding.py --collect-history
}

do_observe() {
    step "observe" "① LPT 分 4 片并行执行（提速 ≥60% 且片间比 ≤1.3 为验收线）"
    set +e
    "$PY" sharding.py --shards 4
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 分片验收未过"; exit 1; }

    step "observe" "② 无历史兜底演示（删除档案后：降级为均分并如实标注）"
    mv reports/history.json /tmp/history_backup.json
    "$PY" sharding.py --shards 4 --no-history
    mv /tmp/history_backup.json reports/history.json
    echo ">>> 验收：提速/均衡双达标；无历史时如实降级不装准"
}

do_clean() {
    step "clean" "删档案与报告"
    rm -rf reports __pycache__ .pytest_cache
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
