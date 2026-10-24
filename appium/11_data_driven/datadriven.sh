#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_LAB="../01_ios_session"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "复用 01 的 Appium / 模拟器 / App 环境"
    (cd "$ENV_LAB" && ./ios_session.sh apply)
    step "apply" "环境就绪，可以直接 observe"
}

do_observe() {
    step "observe" "数据驱动结算（5 组数据 × 完整结算）"
    mvn -q -Dtest=CheckoutDataDrivenTest test
}

do_clean() {
    step "clean" "删除构建产物，并复用 01 的清理"
    rm -rf target test-results
    (cd "$ENV_LAB" && ./ios_session.sh clean) || true
    echo "已清理"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe; do_clean ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
