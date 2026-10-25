#!/usr/bin/env bash
# =============================================================================
# ws_mock.sh — mocking 13 主演示脚本：
# 起 WS 替身(:9751) → 全量接收 → 断线重连续传 → 心跳踢线 4000 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
WS=9751

step() { echo; echo "=====> [$1] $2"; }

wait_up() {
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/docs" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "端口 $1 未就绪" >&2; return 1
}

start_bg() {  # nohup 脱管启动（内层 trap- 恢复信号处置，防 SIG_IGN 继承）
    local name="$1"; shift
    nohup env PIDFILE="$PWD/reports/$name.pid" APP_DIR="$PWD" PORT="$WS" PY="$PY" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; ( trap - TERM INT; exec "$PY" -m uvicorn ws_server:app --host 127.0.0.1 --port "$PORT" --log-level warning ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    sleep 0.2
}

do_apply() {
    step "apply" "① 依赖体检 + 清场 + 起 WS 替身(:${WS}，FastAPI WebSocket)"
    "$PY" -c "import fastapi, websockets, uvicorn" 2>/dev/null || {
        echo "缺依赖：pip install fastapi websockets uvicorn" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$WS"
    mkdir -p reports
    start_bg wsserver
    wait_up "$WS"
    sleep 0.5
    kill -0 "$(cat reports/wsserver.pid)" 2>/dev/null || { echo "启动即死，见 reports/servers.log" >&2; exit 1; }
    echo "WS 替身就绪（/ws 双向推送 + /sse/orders/{id} 单向只读）"
}

do_observe() {
    step "observe" "② 三场景：全量接收 / 断线重连续传 / 心跳踢线——client 自带全部断言"
    "$PY" ws_client.py | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
    step "observe" "③ SSE 变体：同一预设序列的单向只读流（curl 可直接消费）"
    set +e  # curl 会被 --max-time 掐断（exit 28），不算失败
    curl -sN --max-time 2 "http://127.0.0.1:$WS/sse/orders/ORD-1" | head -6 | tee reports/sse.txt
    set -e
    echo ">>> SSE 前几帧如上（text/event-stream，Ctrl-C 或 head 截断即止）"
    echo
    echo ">>> 验收：预设序列全收 ✅ 断点续传 ✅ 心跳踢线 4000 ✅"
}

do_clean() {
    step "clean" "杀服务、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$WS"
    rm -rf reports __pycache__
    lsof -ti ":$WS" >/dev/null 2>&1 && { echo "❌ 端口 $WS 仍被占用"; exit 1; }
    echo "已清理（端口 $WS 确认空闲）"
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
