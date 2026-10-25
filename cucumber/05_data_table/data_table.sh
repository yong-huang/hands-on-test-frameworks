#!/usr/bin/env bash
# =============================================================================
# data_table.sh — lab 05 主演示脚本：DataTable 表格参数
#   apply 起靶场 → observe 批量建单 + 对象映射 → clean 清场
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9105
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 就绪）"
    npx tsc -p tsconfig.json
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    # 脱管包装壳：node 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env PORT="${PORT}" SUT="$SUT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > .sut.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; exit 1
}

do_observe() {
    step "observe" "① 两个表格场景（rows 数组形态 + hashes 对象形态）"
    npx cucumber-js

    step "observe" "② DataTable 两种消费形态速查"
    echo ">>> table.rows()   → string[][]（每行数组，适合列位置固定）"
    echo ">>> table.hashes() → {表头: 值}[]（适合字段自解释、可增列）"
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
