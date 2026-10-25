#!/usr/bin/env bash
# profiles_env.sh — profiles 多环境的启停脚本（dev=9108 / staging=9109）
# 用法: ./profiles_env.sh up|down|status
set -euo pipefail
cd "$(dirname "$0")"
SUT="../../playwright/02_pw_sut/server.mjs"

case "${1:-up}" in
    up)
    # 脱管包装壳：node 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
        nohup env PORT=9108 SUT="$SUT" PIDFILE="$PWD/.dev.pid" bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' </dev/null > .sut-dev.log 2>&1 &
        nohup env PORT=9109 SUT="$SUT" PIDFILE="$PWD/.staging.pid" bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' </dev/null > .sut-staging.log 2>&1 &
        sleep 1.5
        curl -sf http://127.0.0.1:9108/api/health >/dev/null && echo "dev(9108) ✓"
        curl -sf http://127.0.0.1:9109/api/health >/dev/null && echo "staging(9109) ✓"
        ;;
    down)
        for f in .dev.pid .staging.pid; do
            [ -f "$f" ] && { kill "$(cat "$f")" 2>/dev/null || true; rm -f "$f"; }
        done
        lsof -ti :9108 :9109 2>/dev/null | xargs kill 2>/dev/null || true
        echo "两环境已停止"
        ;;
    status)
        for e in 9108 9109; do
            curl -sf -m 2 "http://127.0.0.1:${e}/api/health" >/dev/null && echo "$e ✓" || echo "$e ✗"
        done
        ;;
    *) echo "用法: $0 up|down|status" >&2; exit 1 ;;
esac
