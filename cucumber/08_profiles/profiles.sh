#!/usr/bin/env bash
# =============================================================================
# profiles.sh — lab 08 主演示脚本：配置与多环境
#   apply 起双环境 → observe 同一套用例 × 两 profile + 双浏览器 → clean
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + 双环境就绪）"
    npx tsc -p tsconfig.json
    ./profiles_env.sh up
}

do_observe() {
    step "observe" "① --profile dev：默认 profile 指向 9108"
    npx cucumber-js --profile dev

    step "observe" "② BASE_URL 覆盖演示：staging profile 指向 9109"
    # staging 环境需要单独起服务（profile 只切 URL，不起进程）
    PORT=9109 lsof -ti :9109 >/dev/null 2>&1 || ./profiles_env.sh up >/dev/null
    npx cucumber-js --profile staging

    step "observe" "③ 双浏览器核：chromium 与 firefox 同套件"
    npx cucumber-js --profile dev --name "双浏览器"

    step "observe" "④ 手动体验"
    echo ">>> PROFILE 切换只动 cucumber.mjs 里的 env 段——用例代码零改动"
}

do_clean() {
    step "clean" "停双环境、清运行产物"
    ./profiles_env.sh down
    rm -rf .sut-dev.log .sut-staging.log
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
