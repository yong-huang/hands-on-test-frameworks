#!/usr/bin/env bash
# 04 · Python 热点剖析：py-spy 在共享 PID 命名空间的容器里拍容器化 shop，
#      火焰图定位缺陷 → 修复重建 → 同场景对比，数据说话
# 用法: ./profile_python.sh [prereq|profile|verify|fix|restore|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
SHOP="http://localhost:19331"
SHOP_CONTAINER=01_perf_baseline-shop-1
TAG="${TAG:-before}"   # profile/verify 的产物后缀

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "靶场就绪（容器化 shop 为剖析对象）"
    $COMPOSE up -d 2>&1 | tail -1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop 未就绪"; exit 1; }
        sleep 2
    done
    echo "✅ $SHOP_CONTAINER 就绪"
}

do_profile() {
    step "profile[$TAG]" "py-spy 采样 50s（--idle 连 off-CPU），同时 k6 压 60s"
    ( BASE="$SHOP" VUS=5 DUR=60s k6 run --summary-export \
        "reports/profile_$TAG.json" ../02_load_modeling/k6/closed.js >/dev/null 2>&1 ) &
    local k6pid=$!
    sleep 2
    # mac 上 py-spy 要 root：改在 Linux 侧跑——共享 shop 的 PID namespace，
    # SYS_PTRACE 允许 ptrace；wheel 已离线下载，容器内不碰外网
    docker run --rm --pid=container:$SHOP_CONTAINER --cap-add SYS_PTRACE \
        -v "$PWD/.py-spy-pkgs:/pkgs:ro" -v "$PWD/reports:/out" \
        python:3.13-slim bash -c \
        "pip install --no-index --find-links /pkgs -q py-spy \
         && PID=\$(for p in /proc/[0-9]*; do read -r c < \$p/comm 2>/dev/null; \
                   case \$c in python*|uvicorn*) basename \$p; break;; esac; done) \
         && [ -n \"\$PID\" ] || { echo '未找到 python 进程' >&2; exit 1; } \
         && py-spy record --pid \$PID --idle --duration 50 --rate 50 \
            --format flamegraph -o /out/flame_$TAG.svg" \
        > /dev/null 2>&1 \
    || { echo "❌ 容器内 py-spy 失败（首次运行检查 wheel 与 PID namespace）"; exit 1; }
    wait $k6pid || true
    echo "✅ 火焰图: reports/flame_$TAG.svg（浏览器打开可交互折叠）"
}

do_verify() {
    step "verify[$TAG]" "k6 基线场景 30s（5 VU，与项目 1 同口径）"
    BASE="$SHOP" k6 run --summary-export "reports/verify_$TAG.json" \
        ../01_perf_baseline/k6/smoke_shop.js >/dev/null 2>&1 || true
    python3 -c "
import json
m = json.load(open('reports/verify_$TAG.json'))['metrics']
d = m['http_req_duration']
print(f\"  RPS={m['http_reqs'].get('rate',0):.1f}  P50={d['med']:.1f}ms  P95={d['p(95)']:.1f}ms  错误率={m['http_req_failed'].get('rate', m['http_req_failed'].get('value',0))*100:.1f}%\")"
}

do_fix() {
    step "fix" "应用修复（JOIN 消 N+1 / 打分预计算 / 砍假风控）并重建 shop"
    TAG=after
    cp fixes/shop_main.py ../01_perf_baseline/shop/app/main.py
    $COMPOSE exec -T postgres psql -U shop -d shop -c "
        CREATE TABLE IF NOT EXISTS recommend_scores (
            product_id INT PRIMARY KEY, score INT NOT NULL DEFAULT 0)" >/dev/null
    $COMPOSE up -d --build shop 2>&1 | tail -1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ 修复版 shop 未就绪"; exit 1; }
        sleep 2
    done
    echo "✅ 修复版已上线"
}

do_restore() {
    step "restore" "恢复带缺陷原版并重建（复跑实验用）"
    TAG=before
    cp fixes/shop_main_original.py ../01_perf_baseline/shop/app/main.py
    $COMPOSE up -d --build shop 2>&1 | tail -1
}

do_report() {
    step "report" "前后对比 → docs/analysis.md"
    python3 gen_analysis.py
}

do_clean() {
    step "clean" "无残留（容器栈归 lab 01 管，宿主零进程）"
    echo "✅ done"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; profile) TAG="${TAG:-before}" do_profile ;;
        verify) TAG="${TAG:-before}" do_verify ;; fix) do_fix ;;
        restore) do_restore ;; report) do_report ;; clean) do_clean ;;
        all) do_prereq; do_profile; do_verify; do_fix; do_profile; do_verify; do_report ;;
        *) echo "可用: prereq|profile|verify|fix|restore|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
