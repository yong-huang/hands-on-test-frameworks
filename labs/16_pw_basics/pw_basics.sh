#!/usr/bin/env bash
# =============================================================================
# pw_basics.sh — lab 16 主演示脚本：起 SUT → 三条 E2E → trace 留痕演示
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"          # 仓库标准环境（load_resources.sh 建）
[ -x "$PY" ] || PY="$(command -v python3)"  # 回退：CI/裸克隆等无 venv 环境用系统 python3
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8916
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
    step "observe" "① 三条 E2E 全绿（自动等待，全程无 sleep）"
    $PY -m pytest $INI --base-url "$BASE_URL" --browser chromium -q

    step "observe" "② trace 留痕：--tracing on 记录执行过程，可用 trace viewer 回放"
    rm -rf test-results
    $PY -m pytest $INI --base-url "$BASE_URL" --browser chromium --tracing on -q
    TRACE=$(find test-results -name "trace.zip" | head -1)
    echo ">>> trace 已生成: $TRACE"
    echo ">>> 回放命令: $PY -m playwright show-trace ${TRACE}（GUI 工具，请手动执行查看）"

    step "observe" "③ codegen 录制器（生成代码骨架，请手动体验）："
    echo ">>> $PY -m playwright codegen ${BASE_URL}   # 浏览器会打开，操作即生成代码"
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
