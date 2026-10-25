#!/usr/bin/env bash
# 06_iframes.sh — 项目 6：iframe 嵌套作战
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "三层 iframe 购买支付 / index 切换 / alert 阻塞"
    cd "$SERIES"
    "$PY" -m pytest 06_iframes -q -s
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/06_iframes/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
