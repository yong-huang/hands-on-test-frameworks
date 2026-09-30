#!/usr/bin/env bash
# =============================================================================
# i18n_a11y.sh — lab 16 主演示脚本：i18n 与无障碍
#   双语文案矩阵 → axe 三页扫描 → 纯键盘走完下单
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9016
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + axe 依赖 + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    [ -d ../node_modules/@axe-core ] || {
        echo "axe 依赖缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        npx vite build "$SUT/app" --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 双语文案矩阵（中/英各 2-3 条）"
    npx playwright test i18n --project=chromium --reporter=list

    step "observe" "② axe 无障碍扫描（登录/订单/上传三页，critical=serious=0）+ 纯键盘流程"
    npx playwright test a11y --project=chromium --reporter=list

    step "observe" "③ 手动体验"
    echo ">>> open http://127.0.0.1:9016   （右上角 English/中文 切换；全程 Tab 走一遍表单）"
}

do_clean() {
    step "clean" "清运行产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
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
