#!/usr/bin/env bash
# 08 · 并发模型与容量调参：worker/GOMAXPROCS × 并发矩阵实验，数据选最优工作点
# 用法: ./tune_concurrency.sh [prereq|matrix-shop|matrix-go|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
SHOP="http://localhost:19331"
SHORTURL="http://localhost:19332"
RESULTS=reports/matrix_results.txt

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "靶场就绪"
    $COMPOSE up -d 2>&1 | tail -1
    mkdir -p reports
    touch "$RESULTS"
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop 未就绪"; exit 1; }
        sleep 2
    done
    echo "✅ 就绪"
}

run_probe() { # $1=BASE $2=脚本 $3=导出名 $4=VU
    BASE="$1" VUS="$4" DUR=40s k6 run --summary-export "reports/$3" "$2" >/dev/null 2>&1 || true
    python3 - "reports/$3"
}

show() { python3 - "$1" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))['metrics']
d = m['http_req_duration']
rps = m['http_reqs'].get('rate', 0)
p95 = d['p(95)']
err = m['http_req_failed'].get('rate', m['http_req_failed'].get('value', 0)) * 100
print(f"      RPS={rps:.1f}  P95={p95:.1f}ms  err={err:.2f}%")
EOF
}

do_matrix_shop() {
    step "matrix-shop" "uvicorn workers × 并发（1/2/4 workers × 50/200 VU，读多写少场景）"
    python3 - "$SHOP" <<'K6EOF' > reports/readmost.js
import sys, re
base = sys.argv[1]
src = open('../02_load_modeling/k6/closed.js').read()
src = src.replace("const BASE = __ENV.BASE || 'http://localhost:19331';", f"const BASE = '{base}';")
src = re.sub(r"if \(__ITER % 2 === 0\) \{[\s\S]*?\n  \}\n", "", src)
src = re.sub(r"  sleep\(0\.1\);\n\}", "  sleep(0.05);\n}", src)
print(src)
K6EOF
    for w in 1 2 4; do
        export UVICORN_WORKERS=$w
        $COMPOSE up -d shop >/dev/null 2>&1
        local deadline=$((SECONDS + 90))
        until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
            [ $SECONDS -ge $deadline ] && { echo "❌ shop(w=$w) 未就绪"; exit 1; }
            sleep 2
        done
        for vu in 50 200; do
            run_probe "$SHOP" reports/readmost.js "shop_w${w}_vu${vu}.json" "$vu"
            local line
            line=$(python3 - "reports/shop_w${w}_vu${vu}.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))['metrics']
d = m['http_req_duration']
print(f"RPS={m['http_reqs'].get('rate',0):.1f} P95={d['p(95)']:.1f}")
EOF
)
            echo "exp=shop workers=$w vu=$vu $line" | tee -a "$RESULTS"
        done
    done
    unset UVICORN_WORKERS
}

do_matrix_go() {
    step "matrix-go" "GOMAXPROCS × 并发（1/2/4 P × 50/200 VU，跳转为主）"
    for p in 1 2 4; do
        export GOMAXPROCS=$p
        $COMPOSE up -d shorturl >/dev/null 2>&1
        sleep 3
        for vu in 50 200; do
            run_probe "$SHORTURL" ../01_perf_baseline/k6/smoke_shorturl.js "go_p${p}_vu${vu}.json" "$vu"
            local line
            line=$(python3 - "reports/go_p${p}_vu${vu}.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))['metrics']
d = m['http_req_duration']
print(f"RPS={m['http_reqs'].get('rate',0):.1f} P95={d['p(95)']:.1f}")
EOF
)
            echo "exp=go procs=$p vu=$vu $line" | tee -a "$RESULTS"
        done
    done
    unset GOMAXPROCS
}

do_report() {
    step "report" "最优工作点分析 → docs/tuning.md"
    python3 gen_tuning.py
}

do_clean() {
    step "clean" "恢复默认配置（workers=1 / GOMAXPROCS=默认）"
    unset UVICORN_WORKERS GOMAXPROCS
    $COMPOSE up -d shop shorturl >/dev/null 2>&1
    echo "✅ 已恢复"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; matrix-shop) do_matrix_shop ;;
        matrix-go) do_matrix_go ;; report) do_report ;; clean) do_clean ;;
        all) do_prereq; do_matrix_shop; do_matrix_go; do_report ;;
        *) echo "可用: prereq|matrix-shop|matrix-go|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
