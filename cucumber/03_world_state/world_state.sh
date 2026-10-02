#!/usr/bin/env bash
# =============================================================================
# world_state.sh — lab 03 主演示脚本：World 与步骤状态
#   apply 起靶场 → observe 隔离三场景 + 登录计数审计 → clean 清场
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9103
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 就绪）"
    npx tsc -p tsconfig.json
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    PORT=${PORT} nohup node "$SUT" </dev/null > .sut.log 2>&1 &
    echo $! > "$PIDFILE"; disown
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; exit 1
}

do_observe() {
    step "observe" "① 场景隔离三场景（每场景前 /api/reset + 全新上下文）"
    npx cucumber-js

    step "observe" "② 登录计数审计：World 预登录走 token 直写，零 UI 登录请求"
    echo ">>> asRole() 用 base64 token 写 localStorage（lab 04 思路的雏形）"
    echo ">>> grep 本 lab 步骤层无一次 /api/login UI 表单提交"

    step "observe" "③ 手动体验"
    echo ">>> 在 world.ts 的 Before 里故意去掉 /api/reset，重跑观察'探针甲'泄漏"
}

do_clean() {
    step "clean" "停靶场、清运行产物"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .sut.log
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
