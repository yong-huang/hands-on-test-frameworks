#!/usr/bin/env bash
# =============================================================================
# selenium_grid.sh — lab 24 主演示脚本：本地套件 → Grid 起停 → 2 Chrome 并行跑批
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8924
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"
COMPOSE="docker compose -f docker-compose.grid.yml"
GRID_URL="http://localhost:4444/wd/hub"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_sel.log 2>&1 &
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
    step "observe" "① 本地执行：POM + ActionChains + JS 执行器"
    SUT_URL="$BASE_URL" $PY -m pytest $INI -q 2>/dev/null | tail -1

    step "observe" "② 起 Grid（docker）：standalone Chrome × 2 会话"
    $COMPOSE up -d
    for i in $(seq 1 60); do
        curl -sf -m 2 "http://localhost:4444/status" >/dev/null 2>&1 && break
        sleep 1
    done
    curl -s "http://localhost:4444/status" | "$PY" -c "import sys,json;d=json.load(sys.stdin);print('Grid 就绪，最大并发:', d['value']['node']['maxSessionCount'] if 'node' in d['value'] else d['value']['ready'])"

    step "observe" "③ Grid 串行 vs 2 Chrome 并行（7 条用例：3 快 + 4×1.5s 工作量）"
    # Grid 坑：Chrome 在容器里，访问宿主机 SUT 要用 host.docker.internal 而非 127.0.0.1
    GRID_SUT="http://host.docker.internal:${SUT_PORT}"
    T0=$(date +%s.%N)
    SELENIUM_REMOTE_URL="$GRID_URL" SUT_URL="$GRID_SUT" $PY -m pytest $INI -q 2>/dev/null | tail -1
    T1=$(date +%s.%N); SERIAL=$(echo "$T1 $T0" | awk '{printf "%.1f", $1-$2}')
    echo ">>> Grid 串行耗时 ${SERIAL}s"

    T0=$(date +%s.%N)
    SELENIUM_REMOTE_URL="$GRID_URL" SUT_URL="$GRID_SUT" $PY -m pytest $INI -q -n 2 2>/dev/null | tail -1
    T1=$(date +%s.%N); PAR=$(echo "$T1 $T0" | awk '{printf "%.1f", $1-$2}')
    echo ">>> Grid ×2 并行耗时 ${PAR}s（加速比 $(echo "$SERIAL $PAR" | awk '{printf "%.1f", $1/$2}')x）"
}

do_clean() {
    step "clean" "停 Grid、停 SUT、清理"
    $COMPOSE down -v 2>/dev/null || true
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__ pages/__pycache__
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
