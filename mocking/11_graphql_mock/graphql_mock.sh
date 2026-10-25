#!/usr/bin/env bash
# =============================================================================
# graphql_mock.sh — mocking 11 主演示脚本：
# 起 GraphQL mock(:9750, Ariadne) → 3 query 各自预设 → 结构化 errors → AB 切换 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
GM=9750

step() { echo; echo "=====> [$1] $2"; }

wait_up() {  # 任何 HTTP 应答都算活
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/graphql" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "端口 $1 未就绪" >&2; return 1
}

start_bg() {  # nohup 脱管启动（内层 trap- 恢复信号处置，防 SIG_IGN 继承）
    local name="$1"; shift
    nohup env PIDFILE="$PWD/reports/$name.pid" APP_DIR="$PWD" PORT="$GM" PY="$PY" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; ( trap - TERM INT; exec "$PY" -m uvicorn server:serve --host 127.0.0.1 --port "$PORT" --log-level warning ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
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
    step "apply" "① 依赖体检 + 清场 + 起 GraphQL mock(:${GM}，Ariadne ASGI)"
    "$PY" -c "import ariadne, uvicorn" 2>/dev/null || {
        echo "缺依赖：pip install ariadne uvicorn" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$GM"
    mkdir -p reports
    start_bg graphql
    wait_up "$GM"
    sleep 0.5
    kill -0 "$(cat reports/graphql.pid)" 2>/dev/null || { echo "启动即死，见 reports/servers.log" >&2; exit 1; }
    echo "GraphQL mock 就绪（endpoint /graphql，场景开关 X-Mock-Scene）"
}

do_observe() {
    step "observe" "② 三 query/结构化 errors/AB 切换：client 自带全部断言"
    "$PY" graphql_client.py | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "杀服务、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$GM"
    rm -rf reports __pycache__
    lsof -ti ":$GM" >/dev/null 2>&1 && { echo "❌ 端口 $GM 仍被占用"; exit 1; }
    echo "已清理（端口 $GM 确认空闲）"
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
