#!/usr/bin/env bash
# =============================================================================
# locators_pro.sh — lab 03 主演示脚本：定位引擎深水区
#   复用 lab 02 的 pw-store（独立端口 9003），十条用例 × 稳定性 10 连跑
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9003
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    # pw-store 前端没构建过就先构建（产物被 02-19 各实验共享）
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        step "apply" "pw-store 未构建，执行 vite build"
        npx vite build "$SUT/app" --logLevel warn
    fi
    $PW --version 2>/dev/null || npx playwright --version
}
PW="npx playwright"

do_observe() {
    step "observe" "① 十条定位深水区用例（chromium，webServer 托管 :${PORT}）"
    $PW test --project=chromium --reporter=list

    step "observe" "② 稳定性 10 连跑（验收线：连续 10 次全绿）"
    fail=0
    for i in $(seq 1 10); do
        if $PW test --project=chromium --reporter=line >/dev/null 2>&1; then
            echo ">>> 第 ${i}/10 轮：绿"
        else
            echo ">>> 第 ${i}/10 轮：红（验收失败）"; fail=1
        fi
    done
    [ "$fail" -eq 0 ] && echo ">>> 10 连跑全绿 ✓" || { echo ">>> 存在红轮，稳定性不达标" >&2; exit 1; }
}

do_clean() {
    step "clean" "清理运行产物，杀掉可能残留的 :${PORT} 服务"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report
    echo ">>> 已清理。lab 02 的 SUT 构建产物保留（后续实验还要用）"
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
