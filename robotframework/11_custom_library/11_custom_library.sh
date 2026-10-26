#!/usr/bin/env bash
# 11_custom_library.sh — 项目 11：自定义 Python 关键字库（PythonLibCore）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① libdoc 生成关键字 API 文档（造的轮子要有说明书）"
    "$PY" -m robot.libdoc ShopLibrary.py reports/ShopLibrary.html
    [ -f reports/ShopLibrary.html ] && echo "    ✅ API 文档已生成"
    step "observe" "② 关键字用例套件"
    "$PY" -m robot --outputdir reports shop_library_test.robot
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
