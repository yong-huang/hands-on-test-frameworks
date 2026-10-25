#!/usr/bin/env bash
# 01_shop_first_session.sh — 项目 1：带病靶场 + 三浏览器首会话
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "拉起共享靶场（幂等）"
    bash "$SERIES/shop/shop.sh" apply
}

do_observe() {
    step "observe" "三浏览器首会话（Chrome/Firefox 无头，Safari 有头）"
    cd "$SERIES"
    "$PY" -m pytest 01_shop_first_session -q -s
    step "observe" "靶场陷阱自检：四个陷阱在源码中逐一指认"
    grep -c 'setTimeout.*2500\|iframe id=\|alert(\|loadPage' shop/index.html shop/checkout.html | sed 's/^/    /'
}

do_clean() {
    step "clean" "清运行产物（靶场为公共设施，保留运行）"
    find "$SERIES" -name __pycache__ -maxdepth 3 -exec rm -rf {} + 2>/dev/null || true
    echo "已清理（停靶场请显式执行 bash selenium/shop/shop.sh clean）"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
