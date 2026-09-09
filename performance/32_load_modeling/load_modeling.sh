#!/usr/bin/env bash
# 32 · 负载建模：开放 vs 封闭模型。复用 lab 31 靶场，六轮压测 + 对比报告
# 用法: ./load_modeling.sh [prereq|closed|open|spike|locust|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../31_perf_baseline/docker-compose.yml"
SHOP="http://localhost:19331"
LOCUST="${LOCUST:-$HOME/.venvs/perf-lab/bin/locust}"

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "确认 lab 31 靶场在位（不在则拉起）"
    if ! curl -sf "$SHOP/health" >/dev/null 2>&1; then
        $COMPOSE up -d --quiet-pull
        local deadline=$((SECONDS + 180))
        until curl -sf "$SHOP/health" >/dev/null && curl -sf "http://localhost:19332/healthz" >/dev/null; do
            [ $SECONDS -ge $deadline ] && { echo "❌ 靶场未就绪"; exit 1; }
            sleep 3
        done
    fi
    echo "✅ 靶场就绪（shop:19331 / shorturl:19332）"
}

run_k6() { # $1=脚本 $2=导出名
    k6 run --summary-export "reports/$2" "$1" > /dev/null 2>&1 || true
    echo "  ↳ reports/$2 完成"
}

do_closed() {
    step "closed" "封闭模型：VU=10/50/100 三档（VU 收到响应才发下一单）"
    mkdir -p reports
    for vu in 10 50 100; do
        echo "-- VU=$vu --"
        VUS=$vu run_k6 k6/closed.js "closed_VU$vu.json"
    done
}

do_open() {
    step "open" "开放模型：到达率 50/150/300 it/s 三档（请求彼此独立）"
    mkdir -p reports
    for rate in 50 150 300; do
        echo "-- RATE=$rate --"
        RATE=$rate run_k6 k6/open.js "open_RATE$rate.json"
    done
}

do_spike() {
    step "spike" "尖峰场景：30→400→30 it/s（验收点：突刺复现）"
    run_k6 k6/spike.js "spike.json"
}

do_locust() {
    step "locust" "Locust 封闭等效场景 50 VU（交叉验证 k6 读数）"
    mkdir -p reports
    "$LOCUST" -f locustfile.py --headless -u 50 -r 25 -t 40s \
        --host "$SHOP" --only-summary --csv reports/locust_VU50 >/dev/null 2>&1 || true
    echo "  ↳ reports/locust_VU50_*.csv 完成"
}

do_report() {
    step "report" "汇总对比 → docs/modeling.md"
    python3 gen_compare.py
}

do_clean() {
    step "clean" "停掉 lab 31 靶场并删卷（回到实验前状态）"
    $COMPOSE down -v --remove-orphans
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; closed) do_closed ;; open) do_open ;;
        spike) do_spike ;; locust) do_locust ;; report) do_report ;;
        clean) do_clean ;;
        all) do_prereq; do_closed; do_open; do_spike; do_locust; do_report ;;
        *) echo "可用: prereq|closed|open|spike|locust|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
