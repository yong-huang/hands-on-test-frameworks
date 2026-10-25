#!/usr/bin/env bash
# =============================================================================
# wiremock.sh — mocking 02 主演示脚本：
# 起自研 mock(:9110) + WireMock 容器(:9200) → 10 场景等价对账 → verify 抓未预期 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
MOCK=9110; WM=9200
CNT=mocking02-wiremock
IMG=wiremock/wiremock:3.13.0

step() { echo; echo "=====> [$1] $2"; }

wait_health() {  # 全部 URL 就绪才放行——任一通过就返回会输给 JVM 容器的慢启动
    local urls=("$@") pending
    for i in $(seq 1 120); do
        pending=0
        for u in "${urls[@]}"; do
            curl -sf -m 2 "$u" -o /dev/null 2>/dev/null || pending=1
        done
        [ "$pending" -eq 0 ] && return 0
        sleep 0.5
    done
    echo "健康检查超时: ${urls[*]}" >&2; return 1
}

start_bg() {  # nohup 脱管启动，pid 存 reports/（SIG_IGN 继承坑的修法同 01）
    local name="$1"; shift
    nohup env PY="$PY" PIDFILE="$PWD/reports/$name.pid" SCRIPT="$1" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$PY" "$SCRIPT" "${@:2}" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' srv "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {  # TERM → KILL 兜底 → 端口空闲
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    sleep 0.2
}

do_apply() {
    step "apply" "① 清场 + 起自研 mock(:${MOCK}，复用 01 代码与 stubs) 与 WireMock 容器(:$WM)"
    [ -f reports/mock01.pid ] && kill "$(cat reports/mock01.pid)" 2>/dev/null || true
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$MOCK"; kill_port "$WM"
    mkdir -p reports
    rm -f reports/*.pid reports/servers.log

    start_bg mock01 ../01_declarative_mock/mockserver.py --port "$MOCK" --stubs ../01_declarative_mock/stubs
    docker run -d --name "$CNT" -p "$WM":8080 \
        -v "$PWD/mappings":/home/wiremock/mappings "$IMG" >/dev/null
    wait_health "http://127.0.0.1:$MOCK/__health__" "http://127.0.0.1:$WM/__admin/health" "http://127.0.0.1:$WM/__admin/"
    sleep 0.5  # 验活：防止健康检查被残留旧实例接答（01 的坑）
    kill -0 "$(cat reports/mock01.pid)" 2>/dev/null || { echo "mock01 启动即死，见 reports/servers.log" >&2; exit 1; }
    docker inspect -f '{{.State.Running}}' "$CNT" | grep -q true || { docker logs "$CNT" | tail -5 >&2; exit 1; }

    echo "--- WireMock 已加载的 mappings（priority 1 最高）---"
    curl -sf "http://127.0.0.1:$WM/__admin/mappings" | "$PY" -c "
import json, sys
for m in json.load(sys.stdin)['mappings']:
    print(f\"  P{m.get('priority', 5)}  {m.get('name', '?'):<20} {m['request']['method']} {m['request'].get('urlPath', '')}\")"
}

do_observe() {
    step "observe" "② 等价对账 + verify：diff_harness.py 自带全部断言"
    "$PY" diff_harness.py "http://127.0.0.1:$MOCK" "http://127.0.0.1:$WM" | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "杀服务、删容器与产物——环境回到实验前状态"
    [ -f reports/mock01.pid ] && kill "$(cat reports/mock01.pid)" 2>/dev/null || true
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$MOCK"; kill_port "$WM"
    rm -rf reports __pycache__
    lsof -ti ":$MOCK" >/dev/null 2>&1 && { echo "❌ 端口 $MOCK 仍被占用"; exit 1; }
    lsof -ti ":$WM" >/dev/null 2>&1 && { echo "❌ 端口 $WM 仍被占用"; exit 1; }
    echo "已清理（端口 $MOCK/$WM 空闲，容器 $CNT 已删）"
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
