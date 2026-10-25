#!/usr/bin/env bash
# =============================================================================
# selenium_basics.sh — lab 23 主演示脚本：起 SUT → Chrome 基础用例 → 无等待 vs 显式等待
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8923
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

safari_available() {
    # safaridriver 默认禁用（需手动 sudo safaridriver --enable），探测一下
    echo '<html></html>' > /tmp/sd_probe.html 2>/dev/null || true
    /usr/bin/safaridriver --enable 2>/dev/null && return 0
    return 1
}

do_apply() {
    step "apply" "起 SUT（${SUT_PORT}）"
    start_sut
}

do_observe() {
    step "observe" "① Chrome 基础用例（Selenium Manager 自动驱动）"
    $PY -m pytest $INI -q 2>/dev/null | tail -1

    step "observe" "② 无等待 vs 显式等待对比（上面已各自演示：一个必挂、一个稳定）"
    $PY -m pytest $INI -q -k "no_wait or explicit" 2>/dev/null | tail -1

    step "observe" "③ Safari 支持探测（macOS 原生 Safari 26）"
    if safari_available; then
        echo "✅ safaridriver 已启用：可用 --browser safari 试试（本实验默认 Chrome）"
    else
        echo "⚠️  safaridriver 未启用：需要手动执行一次 sudo safaridriver --enable"
        echo "    （系统会要求在'安全性与隐私'里确认——这是 Safari 自动化的唯一门槛，诚实标注）"
    fi
}

do_clean() {
    step "clean" "停 SUT、删测试库"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__
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
