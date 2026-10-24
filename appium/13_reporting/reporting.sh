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
    step "observe" "报告与失败诊断（3 条用例：2 成功 + 1 故意失败）"
    mvn -q test || true   # 故意失败不影响证据采集与报告生成
    step "observe" "生成 Allure 报告（target/allure-report）"
    if command -v allure >/dev/null 2>&1; then
        rm -rf target/allure-report
        allure generate target/allure-results -o target/allure-report --clean
        echo "  报告已生成。查看：allure serve target/allure-results"
        echo "  或直接打开 target/allure-report/index.html"
    else
        echo "  未安装 allure CLI（brew install allure），结果 JSON 在 target/allure-results"
    fi
}

do_clean() {
    step "clean" "删除构建产物、报告与证据，并复用 01 的清理"
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
