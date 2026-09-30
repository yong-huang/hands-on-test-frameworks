#!/usr/bin/env bash
# =============================================================================
# component.sh — lab 07 主演示脚本：组件测试 vs E2E 的耗时对照
#   ct 用例不起 SUT、不走网络，毫秒级挂载——脚本用真实计时数据说明分层收益
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查）"
    [ -d ../node_modules/@playwright/experimental-ct-react ] || {
        echo "ct 包缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    # observe ② 的 E2E 对照需要 pw-store 构建产物，缺了就地补
    if [ ! -f ../02_pw_sut/app/dist/index.html ]; then
        npx vite build ../02_pw_sut/app --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 组件测试八条用例（ct runner，mount 直挂真浏览器）"
    npx playwright test -c playwright-ct.config.ts --project=chromium --reporter=list

    step "observe" "② 耗时对照：ct 套件 vs lab 02 的 E2E 冒烟套件"
    CT_MS=$( { /usr/bin/time -p npx playwright test -c playwright-ct.config.ts \
        --project=chromium --reporter=line >/dev/null; } 2>&1 | awk '/real/{print int($2*1000)}' )
    cd ../02_pw_sut
    E2E_MS=$( { /usr/bin/time -p npx playwright test --project=chromium \
        --reporter=line >/dev/null; } 2>&1 | awk '/real/{print int($2*1000)}' )
    cd ../07_pw_component
    echo ">>> ct  套件（8 用例，无网络）: ${CT_MS} ms"
    echo ">>> E2E 套件（8 用例，含 SUT+浏览器流程）: ${E2E_MS} ms"
    echo ">>> 对照结论：ct 免去 SUT 启停与页面导航，墙钟时间占比见上方原始数据"

    step "observe" "③ 手动体验"
    echo ">>> npx playwright test -c playwright-ct.config.ts --ui   （UI Mode 里看组件挂载过程）"
}

do_clean() {
    step "clean" "清 ct 运行产物与 dev server 残留"
    lsof -ti :9007 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
    echo ">>> 已清理"
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
