#!/usr/bin/env bash
# =============================================================================
# stateful_mock.sh — mocking 03 主演示脚本：
# 起 WireMock 容器(:9300, scenario 状态机) → happy path 流转 → 终态拒绝
# → 9 格非法跳转全表 → 重置复用 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

WM=9300
CNT=mocking03-wiremock
IMG=wiremock/wiremock:3.13.0

step() { echo; echo "=====> [$1] $2"; }

wait_health() {  # 轮询 admin 健康端点，不裸 sleep
    for i in $(seq 1 120); do
        curl -sf -m 2 "http://127.0.0.1:$1/__admin/health" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "端口 $1 未就绪" >&2; return 1
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
    step "apply" "① 清场（容器含上次的场景状态）+ 起 WireMock(:$WM, order-lifecycle 状态机)"
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$WM"
    mkdir -p reports
    docker run -d --name "$CNT" -p "$WM":8080 \
        -v "$PWD/mappings":/home/wiremock/mappings "$IMG" >/dev/null
    wait_health "$WM"
    echo "--- 场景初始状态 ---"
    curl -sf "http://127.0.0.1:$WM/__admin/scenarios" | ../../.venv/bin/python -c "
import json, sys
for s in json.load(sys.stdin)['scenarios']:
    print(f\"  {s['name']}: {s['state']}（映射 {len(s['mappings'])} 条）\")
"
}

do_observe() {
    step "observe" "② 状态机四幕：流转/终态/非法跳转/重置——client 自带全部断言"
    ../../.venv/bin/python stateful_client.py | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "删容器（场景状态随之消亡）与产物——环境回到实验前状态"
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
