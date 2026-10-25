#!/usr/bin/env bash
# 16_flaky.sh — 项目 16：flaky 稳定性治理（检出-隔离-复验闭环）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等；本实验用纯 pytest 池子，不驱动浏览器）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "检出-隔离-复验闭环（20 轮检测 + 10 轮确认）"
    cd "$SERIES"
    # 只收集治理用例：tests/ 是猎物池，由 hunt.py 的子进程轮次驱动，不能被外层直接执行
    "$PY" -m pytest 16_flaky/governance_test.py -q -s
    step "observe" "产物：reports/flaky.json + tests/quarantine.txt"
    cat 16_flaky/tests/quarantine.txt | sed 's/^/    隔离: /'
}

do_clean() {
    step "clean" "清运行产物（保留隔离区与 flaky.json 供查阅）"
    rm -rf "$SERIES/16_flaky/reports/round_*.xml" "$SERIES/16_flaky/tests/__pycache__" "$SERIES/16_flaky/__pycache__" "$SERIES/__pycache__"
    rm -f "$SERIES/16_flaky/tests/.shared_state"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
