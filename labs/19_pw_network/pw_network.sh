#!/usr/bin/env bash
# =============================================================================
# pw_network.sh — lab 19 主演示脚本
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8919
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    (cd "$SUT_DIR/app" && SUT_DB="$PWD/test_orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../.sut_pw.log 2>&1 &
    echo $! > "../../labs/19_pw_network/${PIDFILE}"; disown)
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
    step "apply" "起 SUT（独立端口 ${SUT_PORT} + 空测试库）"
    start_sut
}

do_observe() {
    step "observe" "① 网络桩：不启动后端响应也能跑前端交互（route 全拦 /api/*）"
    $PY -m pytest $INI --base-url "$BASE_URL" -q tests/test_route_mock.py 2>/dev/null | tail -1

    step "observe" "② 错误注入：500/断网 下 UI 优雅降级"
    $PY -m pytest $INI --base-url "$BASE_URL" -q -k "inject" 2>/dev/null | tail -1

    step "observe" "③ 登录态复用：storageState 保存 admin/user 双会话，互不串号"
    $PY -m pytest $INI --base-url "$BASE_URL" -q tests/test_sessions.py 2>/dev/null | tail -1
    ls -la .auth/ 2>/dev/null | tail -3
}

do_clean() {
    step "clean" "停 SUT、删测试库与产物"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__ pages/__pycache__ test-results
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
