#!/usr/bin/env bash
# =============================================================================
# cypress_basics.sh — lab 21 主演示脚本：起 SUT → cypress run 三条 spec → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8921
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_cy.log 2>&1 &
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
    step "apply" "依赖与 SUT：node_modules 就位（npm install -D cypress）+ 起 SUT"
    [ -d node_modules/cypress ] || npm install -D cypress
    start_sut
}

do_observe() {
    step "observe" "① headless 跑三条 spec（与 Playwright 项目 16 同语义）"
    CYPRESS_SUT_URL="$BASE_URL" npx cypress run --spec "cypress/e2e/orders.cy.js" 2>&1 | grep -E "✔|✓|passed|failed|Running:|All specs" | head -12

    step "observe" "② 调试体验（交互式运行器，请手动体验）："
    echo ">>> CYPRESS_SUT_URL=$BASE_URL npx cypress open"

    step "observe" "③ 第一印象对比（详见 README）：Cypress 在浏览器里跑、链式命令、自带重试"
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
