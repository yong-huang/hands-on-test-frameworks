#!/usr/bin/env bash
# 07_expected_failures.sh — 项目 7：期望失败与失败留证
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 跑套件——预期 1 failed（留证素材）+ 4 负向全绿"
    "$PY" -m robot --outputdir reports expected_failures.robot || true
    step "observe" "② 核验"
    "$PY" verify_expected.py
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
