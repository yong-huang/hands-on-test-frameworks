#!/usr/bin/env bash
# =============================================================================
# dynamic_mock.sh — mocking 04 主演示脚本：
# 起 WireMock 容器(:9400, 响应模板) → 100 次唯一订单号过 Schema → P95 延迟实测 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
WM=9400
CNT=mocking04-wiremock
IMG=wiremock/wiremock:3.13.0

step() { echo; echo "=====> [$1] $2"; }

wait_health() {
    for i in $(seq 1 120); do
        curl -sf -m 2 "http://127.0.0.1:$1/__admin/health" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "端口 $1 未就绪" >&2; return 1
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
    step "apply" "① 清场 + 起 WireMock(:$WM, response-template 模板引擎)"
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$WM"
    mkdir -p reports
    docker run -d --name "$CNT" -p "$WM":8080 \
        -v "$PWD/mappings":/home/wiremock/mappings "$IMG" >/dev/null
    wait_health "$WM"
    echo "--- 已加载的动态 stub ---"
    curl -sf "http://127.0.0.1:$WM/__admin/mappings" | "$PY" -c "
import json, sys
for m in json.load(sys.stdin)['mappings']:
    t = '模板' if 'response-template' in m['response'].get('transformers', []) else '静态'
    delay = m['response'].get('fixedDelayMilliseconds')
    print(f\"  {m.get('name', '?'):<18} [{t}]\" + (f\" 延迟 {delay}ms\" if delay else ''))"
}

do_observe() {
    step "observe" "② 动态生成/回填/延迟：dynamic_client.py 自带全部断言"
    "$PY" dynamic_client.py | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "删容器与产物——环境回到实验前状态"
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$WM"
    rm -rf reports __pycache__
    lsof -ti ":$WM" >/dev/null 2>&1 && { echo "❌ 端口 $WM 仍被占用"; exit 1; }
    echo "已清理（端口 $WM 空闲，容器 $CNT 已删）"
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
