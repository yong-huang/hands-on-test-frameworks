#!/usr/bin/env bash
# =============================================================================
# k6_run.sh — lab 27 主演示脚本：smoke → ramping → 阈值门禁失败演示
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8927
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    (cd "$SUT_DIR/app" && SUT_DB="$PWD/test_orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../.sut_k6.log 2>&1 &
    echo $! > "../../labs/27_k6/${PIDFILE}"; disown)
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

stop_sut() {
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
}

do_apply() {
    step "apply" "起 SUT（${SUT_PORT}）"
    start_sut
}

do_observe() {
    step "observe" "① smoke 场景（1 VU 15s）：部署后秒级验活"
    BASE_URL="$BASE_URL" k6 run -e SCENARIO=smoke load.js 2>&1 | grep -E "scenarios|http_req_duration|checks|✓|✗" | head -8

    step "observe" "② ramping 场景（20 VU 爬升-稳态-收尾）"
    BASE_URL="$BASE_URL" k6 run -e SCENARIO=ramping load.js 2>&1 | grep -E "http_req_duration|checks" | head -6

    step "observe" "③ spike 场景（到达率 5→60/s 突刺）：复现 SUT 突刺响应"
    BASE_URL="$BASE_URL" k6 run -e SCENARIO=spike load.js 2>&1 | grep -E "http_req_duration|checks" | head -6

    step "observe" "④ thresholds 门禁演示：对 1.5s 慢接口设 p95<500 → 不达标退出码非 0（预期失败）"
    set +e
    BASE_URL="$BASE_URL" k6 run slow_threshold_demo.js 2>&1 | grep -E "thresholds|✗|✓ .*p\(95\)" | head -4
    echo ">>> 退出码 = $?（非 0：thresholds 不达标即 CI 门禁红线）"
    set -e
}

do_clean() {
    step "clean" "停 SUT、清库"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    echo "已清理"
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
