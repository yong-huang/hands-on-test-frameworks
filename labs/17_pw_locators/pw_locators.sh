#!/usr/bin/env bash
# =============================================================================
# pw_locators.sh — lab 17 主演示脚本
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8917
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"
RUNS="${STABILITY_RUNS:-10}"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_pw.log 2>&1 &
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
    step "observe" "① 稳定写法全绿：竞态/延迟渲染/慢接口全部 expect 自动等待"
    $PY -m pytest $INI --base-url "$BASE_URL" -q --ignore=tests/test_antipattern.py 2>/dev/null | tail -1

    step "observe" "② 反模式演示：sleep(0.5)+不等待断言，当场必挂（预期失败）"
    set +e
    $PY -m pytest $INI --base-url "$BASE_URL" -q tests/test_antipattern.py::test_sleep_too_short 2>/dev/null | tail -1
    echo ">>> 退出码非 0：固定 sleep 是赌博，expect 是契约"
    set -e

    step "observe" "③ 稳定性证明：同一套稳定用例连跑 $RUNS 次全绿（次数可用 STABILITY_RUNS 覆盖）"
    for i in $(seq 1 "$RUNS"); do
        $PY -m pytest $INI --base-url "$BASE_URL" -q --ignore=tests/test_antipattern.py 2>/dev/null | tail -1 | sed "s/^/  run $i: /"
    done

    step "observe" "④ --durations 定位：慢在哪一目了然"
    $PY -m pytest $INI --base-url "$BASE_URL" -o addopts="" --durations=3 -q --ignore=tests/test_antipattern.py 2>/dev/null | grep -A4 "slowest" | head -6
}

do_clean() {
    step "clean" "停 SUT、删测试库与产物"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__ test-results
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
