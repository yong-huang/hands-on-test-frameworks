#!/usr/bin/env bash
# =============================================================================
# locators.sh — 02 主演示脚本：定位策略矩阵 → XPath 演示 → 纪律检查
# =============================================================================
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
    step "observe" "① 六类元素 × 两种定位策略（12 次定位）"
    mvn -q -Dtest=LocatorStrategyTest test

    step "observe" "② XPath 演示（单独执行，不进主套件）"
    mvn -q -Dtest=XPathDemoTest test

    step "observe" "③ XPath 纪律检查：主用例必须 0 次"
    if grep -n "xpath(" src/test/java/dev/handson/appium/LocatorStrategyTest.java; then
        echo "❌ 主用例出现 XPath，违反定位纪律" >&2
        exit 1
    else
        echo "✅ LocatorStrategyTest 中 XPath = 0（演示只在 XPathDemoTest）"
    fi
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
