#!/usr/bin/env bash
# 06_web_complex.sh — 项目 6：复杂页面三难
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "拉起靶场（本实验加过 /api/recs，强制重启）"
    bash "$SERIES/shop/shop.sh" restart
}

do_observe() {
    step "observe" "iframe / 多窗口 / 懒加载"
    "$PY" -m robot --outputdir reports web_complex.robot
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf reports
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
