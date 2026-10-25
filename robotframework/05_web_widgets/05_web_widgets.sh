#!/usr/bin/env bash
# 05_web_widgets.sh — 项目 5：Web 表单与控件全集
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "多选/复选/radio/文件上传 + 汇总断言"
    "$PY" -m robot --outputdir reports web_widgets.robot
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
