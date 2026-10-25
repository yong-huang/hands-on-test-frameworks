#!/usr/bin/env bash
# 03_waits.sh — 项目 3：等待机制全集
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "sleep 下注 / 显式 10 连 / FluentWait / 隐式叠加陷阱"
    cd "$SERIES"
    "$PY" -m pytest 03_waits -q -s
    step "observe" "产物：reports/waits_report.csv"
    cat 03_waits/reports/waits_report.csv | sed 's/^/    /'
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/03_waits/reports" "$SERIES/03_waits/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
