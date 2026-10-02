#!/usr/bin/env bash
# =============================================================================
# example_mapping.sh — lab 11 主演示脚本：Example Mapping 与需求对话
#   apply 起靶场 → observe 三色卡推演的红→绿闭环（先 pending 后实现）→ clean
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9112
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
    step "observe" "① 需求卡「仅 admin 可删单」的完整场景（2 组例子）"
    npx cucumber-js

    step "observe" "② 红先绿后工作法回顾"
    echo ">>> 本特性开发时先写 .feature（全 pending）→ 逐条实现步骤 → 收敛全绿"
    echo ">>> pending 状态在报告中显示为黄色（非红）——'还没做'与'做错了'要分清"

    step "observe" "③ Example Mapping 复盘"
    echo ">>> 规则：仅 admin 可删 / 顾客无入口"
    echo ">>> 例子：admin 可见+200 / customer 不可见+403"
    echo ">>> 疑问：API 直删呢？→ 已补进场景（服务端 403）"
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
