#!/usr/bin/env bash
# 09_evidence.sh — 项目 9：截图证据链
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 跑套件——预期 1 failed（注入的失败，这就是取证素材）"
    cd "$SERIES"
    "$PY" -m pytest 09_evidence -q || true
    step "observe" "② 证据链核验：失败留 png+source，通过零附件"
    "$PY" 09_evidence/verify_evidence.py
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/09_evidence/reports" "$SERIES/09_evidence/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
