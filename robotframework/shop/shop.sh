#!/usr/bin/env bash
# shop.sh — robot 系列共享靶场生命周期（apply/restart/clean/status），端口 8952
set -euo pipefail
cd "$(dirname "$0")"

PORT=8952
PIDFILE="$PWD/.server.pid"
LOG="$PWD/.server.log"
REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

is_up() { curl -sf -m 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; }

case "${1:-apply}" in
  apply)
    if is_up; then echo "靶场已在运行：http://127.0.0.1:$PORT"; exit 0; fi
    lsof -ti ":$PORT" 2>/dev/null | xargs kill 2>/dev/null || true
    nohup env PY="$PY" PORT="$PORT" PIDFILE="$PIDFILE" LOG="$LOG" \
        bash -c 'trap "" TERM INT; "$PY" server.py --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$LOG" 2>&1 &
    for i in $(seq 1 40); do
        is_up && { echo "靶场就绪：http://127.0.0.1:$PORT"; exit 0; }
        sleep 0.25
    done
    echo "靶场启动失败，日志尾部：" >&2; tail -5 "$LOG" >&2; exit 1
    ;;
  restart) bash "$0" clean && bash "$0" apply ;;
  clean)
    [ -f "$PIDFILE" ] && PID=$(cat "$PIDFILE") || PID=""
    case "$PID" in ''|*[!0-9]*) PID="";; esac
    [ -n "$PID" ] && kill "$PID" 2>/dev/null || true
    lsof -ti ":$PORT" 2>/dev/null | xargs kill 2>/dev/null || true
    for i in $(seq 1 20); do is_up || break; sleep 0.25; done
    is_up && { lsof -ti ":$PORT" 2>/dev/null | xargs kill -9 2>/dev/null || true; sleep 0.5; }
    is_up && { echo "❌ 端口 $PORT 仍被占用"; exit 1; }
    rm -f "$PIDFILE" "$LOG"
    echo "靶场已停止（端口 $PORT 确认空闲）"
    ;;
  status) is_up && echo running || echo stopped ;;
  *) echo "可用: apply | restart | clean | status" >&2; exit 1;;
esac
