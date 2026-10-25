#!/usr/bin/env bash
# 08_actions.sh — 项目 8：Actions 交互链
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "拖拽 / hover 菜单 / Ctrl+S / 画布像素"
    cd "$SERIES"
    "$PY" -m pytest 08_actions -q -s
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/08_actions/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
