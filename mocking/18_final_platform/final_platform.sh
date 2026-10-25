#!/usr/bin/env bash
# =============================================================================
# final_platform.sh — mocking 18 🏁 主演示脚本：
# docker compose 一键冷启动全家桶（WireMock/GraphQL/gRPC/Redpanda/BFF）
# → 五路冒烟全绿 → 漂移注入门禁抓红 → 恢复归零 → 看板落盘 → compose down
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① compose 一键冷启动全家桶（--build 首次较慢）"
    if ! docker info >/dev/null 2>&1; then
        open -a OrbStack 2>/dev/null || true
        for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
    fi
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
    docker compose up -d --build
    echo "--- 等待全家桶就绪 ---"
    for i in $(seq 1 60); do
        ok=1
        curl -sf -m 2 http://127.0.0.1:9820/__admin/health >/dev/null 2>&1 || ok=0
        curl -sf -m 2 -X POST http://127.0.0.1:9821/graphql \
            -H "Content-Type: application/json" -d '{"query":"{__typename}"}' >/dev/null 2>&1 || ok=0
        curl -s -m 2 -X POST http://127.0.0.1:9824/checkout \
            -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1 || ok=0
        [ "$ok" -eq 1 ] && break
        sleep 1
    done
    [ "$ok" -eq 1 ] || { echo "全家桶未就绪" >&2; exit 1; }
    mkdir -p reports results
    docker compose ps --format '{{.Name}} {{.Status}}'
}

do_observe() {
    step "observe" "② 五路冒烟 + 漂移门禁演示（smoke.py 自带全部断言与看板生成）"
    "$PY" smoke.py 2>&1 | tee reports/smoke.txt
    grep -q "❌" reports/smoke.txt && { echo "存在失败探针"; exit 1; } || true
}

do_clean() {
    step "clean" "compose down -v（连卷一起删）——环境回到实验前状态"
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
    rm -rf reports results __pycache__
    local residue=0
    for p in 9820 9821 9822 9824; do
        lsof -ti ":$p" >/dev/null 2>&1 && { echo "❌ 端口 $p 仍被占用"; residue=1; }
    done
    [ "$residue" -eq 0 ] && echo "已清理（compose 全家桶已销毁，端口确认空闲）"
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
