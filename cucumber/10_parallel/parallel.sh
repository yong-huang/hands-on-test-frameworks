#!/usr/bin/env bash
# =============================================================================
# parallel.sh — lab 10 主演示脚本：并行与隔离
#   apply 起靶场 → observe 10 场景 × 4 workers 并行全绿（零串号）→ clean
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9111
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
    step "observe" "① 10 场景 × 4 workers 并行（唯一前缀防串号）"
    npx cucumber-js

    step "observe" "② 手动体验"
    echo ">>> 把 cucumber.mjs 的 parallel 改成 1 或 8，重跑对比耗时与行为"
    echo ">>> 串号实验：删掉步骤里的 lastTitle 唯一前缀，并行下计数断言会随机红"
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
