#!/usr/bin/env bash
# =============================================================================
# fault_matrix.sh — mocking 07 主演示脚本：
# 起 WireMock(:9700) → 矩阵驱动器逐格注入 7 类场景 → 断言客户端分支 → 覆盖率报告 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
WM=9700
CNT=mocking07-wiremock
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
    step "apply" "① 清场 + 起 WireMock(:${WM}，故障注入靶场)"
    docker rm -f "$CNT" >/dev/null 2>&1 || true
    kill_port "$WM"
    mkdir -p reports
    docker run -d --name "$CNT" -p "$WM":8080 "$IMG" >/dev/null
    wait_health "$WM"
    echo "WireMock 就绪（无预置映射，故障格由驱动器逐格注入）"
}

do_observe() {
    step "observe" "② 矩阵逐格执行：7 格（基线 + 6 类故障）全部断言预期分支"
    "$PY" fault_matrix.py "http://127.0.0.1:$WM" | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在错格"; exit 1; } || true
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
