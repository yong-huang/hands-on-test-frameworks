#!/usr/bin/env bash
# 02_locators.sh — 项目 2：八种定位策略实战
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "八种定位策略 + 健壮性打分表"
    cd "$SERIES"
    "$PY" -m pytest 02_locators -q -s
    step "observe" "产物：reports/locator_scores.csv"
    head -6 02_locators/reports/locator_scores.csv | sed 's/^/    /'
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/02_locators/reports" "$SERIES/02_locators/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
