#!/usr/bin/env bash
# 04_forms.sh — 项目 4：表单控件全集
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "拉起靶场（本实验改过 server.py，强制重启加载新接口）"
    bash "$SERIES/shop/shop.sh" restart
}

do_observe() {
    step "observe" "8 类控件全操作 + 回读逐字段断言"
    cd "$SERIES"
    "$PY" -m pytest 04_forms -q -s
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/04_forms/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
