#!/usr/bin/env bash
# =============================================================================
# network_pro.sh — lab 05 主演示脚本：网络控制进阶
#   ① 录 HAR  ② 注入套件（500/慢接口/断连/waitForResponse）  ③ 停后端 → 离线回放
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9005
SUT="../02_pw_sut"
PW="npx playwright"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        step "apply" "pw-store 未构建，执行 vite build"
        npx vite build "$SUT/app" --logLevel warn
    fi
    $PW --version
}

do_observe() {
    step "observe" "① 录制 HAR（真实后端 + update 模式，产物 har/pw-store.har）"
    rm -rf har && $PW test har_record --project=chromium --reporter=line
    ls -la har/pw-store.har

    step "observe" "② 注入套件：500 / 3s 慢接口 / 断连 / waitForResponse"
    $PW test tests/network_pro.spec.ts --project=chromium --reporter=list

    step "observe" "③ 离线回放：先杀掉后端，再用 HAR 跑通同一条下单路径"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 0.5
    if curl -sf -m 2 "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        echo "后端仍在运行，无法证明离线" >&2; exit 1
    fi
    echo ">>> 后端已确认下线（/api/health 不可达），开始离线回放："
    $PW test -c configs/offline.config.ts --project=chromium --reporter=line
    echo ">>> 后端不在线，回放套件全绿 ✓"
}

do_clean() {
    step "clean" "清运行产物与 HAR（运行时产物，可随时重录），杀残留服务"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report har
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
