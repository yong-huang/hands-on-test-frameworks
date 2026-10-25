#!/usr/bin/env bash
# 10_pom.sh — 项目 10：POM 分层重构
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 硬规则：测试层零 find_element"
    hits=$({ grep -rn "find_element" tests/ || true; } | wc -l | tr -d ' ')
    echo "    tests/ 内 find_element 命中数: ${hits}（要求 0）"
    [ "$hits" = "0" ] || { echo "❌ 测试层混入了定位细节"; exit 1; }
    step "observe" "② 下单支付全流程（页面/编排/测试三层）"
    cd "$SERIES"
    "$PY" -m pytest 10_pom -q -s
}

do_clean() {
    step "clean" "清运行产物"
    find "$SERIES/10_pom" -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    rm -rf "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
