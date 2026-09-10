#!/usr/bin/env bash
# 🏁 10 · 性能回归门禁：采基线 → 绿 → 注入回归 → 红 → 修复 → 绿
# 用法: ./gate_run.sh [prereq|baseline|gate|inject|fix|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
SHOP="http://localhost:19331"
FIXED_MAIN=../01_perf_baseline/shop/app/main.py
DEFECT_MAIN=../04_python_profiling/fixes/shop_main_original.py

step() { echo; echo "=====> [$1] $2"; }

wait_shop() {
    local deadline=$((SECONDS + 180))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop 未就绪"; exit 1; }
        sleep 2
    done
}

do_prereq() {
    step "prereq" "靶场就绪（当前健康版本）"
    $COMPOSE up -d 2>&1 | tail -1
    wait_shop
    echo "✅ 就绪"
}

do_baseline() {
    step "baseline" "用当前健康版本采集门禁基线（5 VU × 30s，与项目 1 同口径）"
    mkdir -p reports/baseline
    BASE="$SHOP" k6 run --summary-export reports/baseline/smoke_shop.json \
        ../01_perf_baseline/k6/smoke_shop.js >/dev/null 2>&1 || true
    BASE="http://localhost:19332" k6 run --summary-export reports/baseline/smoke_shorturl.json \
        ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 || true
    echo "✅ 基线已固化（reports/baseline/，01 号实验的历史基线不受影响）"
}

do_gate() { # TAG=阶段标签
    : "${TAG:=green}"
    step "gate[$TAG]" "门禁判定（相对基线，预算见 budget.yaml）"
    BASE="$SHOP" k6 run --summary-export reports/gate_shop.json \
        ../01_perf_baseline/k6/smoke_shop.js >/dev/null 2>&1 || true
    BASE="http://localhost:19332" k6 run --summary-export reports/gate_shorturl.json \
        ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 || true
    set +e
    python3 regression_gate.py shop
    local s1=$?
    python3 regression_gate.py shorturl
    local s2=$?
    set -e
    echo "$TAG $((s1 + s2))" > reports/.gate_last
    [ $((s1 + s2)) = 0 ] && echo "🟢 总判定：通过" || echo "🔴 总判定：不通过"
    return 0
}

do_inject() {
    step "inject" "注入性能回归：换回 lab 04 的缺陷版 main（md5 热点 + sleep + N+1）"
    cp "$DEFECT_MAIN" "$FIXED_MAIN"
    $COMPOSE up -d --build shop >/dev/null 2>&1
    wait_shop
    echo "✅ 回归已注入"
}

do_fix() {
    step "fix" "恢复健康版本"
    cp ../04_python_profiling/fixes/shop_main.py "$FIXED_MAIN"
    $COMPOSE up -d --build shop >/dev/null 2>&1
    wait_shop
    echo "✅ 已恢复"
}

do_report() {
    step "report" "容量评估报告 → docs/capacity.md"
    python3 gen_capacity.py
}

do_clean() {
    step "clean" "无残留（靶场为公共设施）"
    echo "✅ done"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; baseline) do_baseline ;; gate) do_gate "${TAG:-green}" ;;
        inject) do_inject ;; fix) do_fix ;; report) do_report ;; clean) do_clean ;;
        all)
            do_prereq
            do_baseline
            TAG=green do_gate
            do_inject
            TAG=red do_gate
            do_fix
            TAG=green-after do_gate
            do_report ;;
        *) echo "可用: prereq|baseline|gate|inject|fix|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
