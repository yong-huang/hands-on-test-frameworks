#!/usr/bin/env bash
# =============================================================================
# matrix.sh — lab 11 主演示脚本：设备与仿真矩阵
#   ① 六 project 响应式全跑  ② 深色/浅色分组统计  ③ 仿真三件套（locale/timezone/offline）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9011
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
    step "observe" "① 六 project 全跑（3 设备 × 明暗，同一套响应式用例）"
    npx playwright test --project=desktop-light --project=desktop-dark \
        --project=iphone-light --project=iphone-dark \
        --project=pixel-light --project=pixel-dark \
        --reporter=line

    step "observe" "② 单 project 抽查：深色模式背景断言"
    npx playwright test --project=desktop-dark --project=desktop-light \
        -g '深色模式' --reporter=line

    step "observe" "③ 仿真三件套：timezone / offline / 触屏"
    npx playwright test simulation --reporter=list

    step "observe" "④ 手动体验"
    echo ">>> npx playwright test --project=iphone-dark --ui   （小屏 + 深色的组合现场）"
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
