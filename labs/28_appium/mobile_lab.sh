#!/usr/bin/env bash
# =============================================================================
# mobile_lab.sh — lab 28 主演示脚本：环境探测（诚实记录）→ 移动 fallback 全绿
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8928
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
        </dev/null > ../.sut_mb.log 2>&1 &
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

probe_env() {
    echo "  Appium server: $(command -v appium >/dev/null && appium --version || echo '未安装')"
    if xcrun -f simctl >/dev/null 2>&1; then
        echo "  simctl: 可用"
        return 0
    else
        echo "  simctl: 不可用（xcode-select 指向 CommandLineTools，无法启动 iOS Simulator）"
        return 1
    fi
}

do_apply() {
    step "apply" "起 SUT（${SUT_PORT}）"
    start_sut
}

do_observe() {
    step "observe" "① 环境探测：Appium 完整链路（Xcode + Simulator + Appium server）"
    if probe_env; then
        echo "  ✅ 环境齐备：可运行 appium_reference.py 的 Appium 用例"
    else
        echo "  ⚠️  Appium 链路受阻（如实记录）。按清单约定，fallback 方案计入完成："
        echo "     补齐方式见 appium_reference.py 模块注释；本机先跑 ② 的 fallback"
    fi

    step "observe" "② 移动 fallback：Playwright iPhone 14 触屏 + 视口（3 条用例）"
    SUT_URL="$BASE_URL" $PY -m pytest -c configs/pytest.ini --rootdir=. -q
}

do_clean() {
    step "clean" "停 SUT、清库"
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
