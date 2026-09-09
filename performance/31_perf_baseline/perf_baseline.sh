#!/usr/bin/env bash
# 31 · 双 SUT 靶场 + 基线压测：起栈 → 等健康 → k6 基线 → 五指标报告 → 清理
# 用法: ./perf_baseline.sh [apply|observe|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

step() { echo; echo "=====> [$1] $2"; }

wait_healthy() { # $1=URL $2=名字 $3=超时秒
    local deadline=$((SECONDS + $3))
    until curl -sf "$1" >/dev/null; do
        if [ $SECONDS -ge $deadline ]; then
            echo "❌ $2 在 ${3}s 内未就绪"; exit 1
        fi
        sleep 2
    done
    echo "✅ $2 就绪: $1"
}

do_apply() {
    step "apply" "构建并启动全栈（postgres/redis/shop/shorturl）"
    docker compose up -d --build --quiet-pull
    step "wait" "等两个 SUT 健康（首次构建+灌种子约 1-2 分钟）"
    wait_healthy "http://localhost:19331/health"  "perf-shop"  180
    wait_healthy "http://localhost:19332/healthz" "shorturl"   60
    step "verify" "抽查种子数据与核心端点"
    echo "-- 商品列表（应见 N+1 的产物：50 行带库存）--"
    curl -s "http://localhost:19331/api/products?limit=2" | head -c 300; echo
    echo "-- 短码跳转（应 301 到 example.com）--"
    curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" "http://localhost:19332/s00001"
}

do_observe() {
    step "observe" "k6 基线压测（5 VU × 30s × 两服务，数据不会说谎）"
    mkdir -p reports
    BASE=http://localhost:19331 k6 run --summary-export reports/smoke_shop.json k6/smoke_shop.js
    BASE=http://localhost:19332 k6 run --summary-export reports/smoke_shorturl.json k6/smoke_shorturl.js
    step "report" "汇总五指标 → docs/baseline.md"
    python3 gen_report.py reports/smoke_shop.json reports/smoke_shorturl.json
}

do_clean() {
    step "clean" "停栈并删除数据卷（回到实验前状态）"
    docker compose down -v --remove-orphans
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
