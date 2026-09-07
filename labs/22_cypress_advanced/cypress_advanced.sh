#!/usr/bin/env bash
# =============================================================================
# cypress_advanced.sh — lab 22 主演示脚本：intercept / session / 自定义命令
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8922
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    (cd "$SUT_DIR/app" && SUT_DB="$PWD/test_orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../.sut_cy.log 2>&1 &
    echo $! > "../../labs/22_cypress_advanced/${PIDFILE}"; disown)
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
    step "apply" "依赖与 SUT"
    [ -d node_modules/cypress ] || npm install -D cypress
    start_sut
}

do_observe() {
    step "observe" "① 网络桩 spec（intercept 三连）"
    CYPRESS_SUT_URL="$BASE_URL" npx cypress run --spec "cypress/e2e/intercept.cy.js" 2>&1 | grep -E "✔|passed|failed|All specs" | head -6

    step "observe" "② 会话复用 + 自定义命令 spec（session 三连）"
    CYPRESS_SUT_URL="$BASE_URL" npx cypress run --spec "cypress/e2e/session.cy.js" 2>&1 | grep -E "✔|passed|failed|All specs" | head -6
}

do_clean() {
    step "clean" "停 SUT、删测试库"
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
