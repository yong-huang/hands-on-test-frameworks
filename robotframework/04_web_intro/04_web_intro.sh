#!/usr/bin/env bash
# 04_web_intro.sh — 项目 4：SeleniumLibrary 入门
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 无头模式跑主流程 + 慢元素"
    "$PY" -m robot --variable BROWSER:headlesschrome --outputdir reports/headless web_intro.robot
    step "observe" "② 有头模式同参同过（会弹浏览器窗口）"
    "$PY" -m robot --variable BROWSER:chrome --outputdir reports/headful web_intro.robot
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
