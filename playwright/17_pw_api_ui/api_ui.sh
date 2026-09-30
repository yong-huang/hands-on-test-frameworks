#!/usr/bin/env bash
# =============================================================================
# api_ui.sh — lab 17 主演示脚本：API+UI 混合
#   ① 100 条 API 造数 ≤5s + 分页 UI 验证  ② 10 条混合用例  ③ teardown 清零
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9017
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        npx vite build "$SUT/app" --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 12 条混合用例（1 造数百条 + 10 条分页验证 + 1 条 UI 造数对照）"
    npx playwright test --project=chromium --reporter=list
}

do_clean() {
    step "clean" "清运行产物并重置 SUT 数据，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
    echo ">>> 已清理（teardown 的 /api/reset 已把数据拉回种子）"
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
