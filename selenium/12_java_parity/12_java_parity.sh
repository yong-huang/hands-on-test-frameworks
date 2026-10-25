#!/usr/bin/env bash
# 12_java_parity.sh — 项目 12：Java 双栈对照（Maven + TestNG 重写项目 10 套件）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "mvn test：TestNG 驱动同一套件（断言语义等价）"
    mvn -q test -DHEADLESS=1
    step "observe" "双栈差异表见 README.md（≥8 行）"
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf target
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
