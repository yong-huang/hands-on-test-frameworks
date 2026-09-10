#!/usr/bin/env bash
# 05 · Go 剖析：pprof 抓 CPU/heap，benchmem 判 allocs，修复前后同尺对比
# 用法: ./go_profiling.sh [prereq|pprof|bench|fix|restore|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
SHORTDIR=../01_perf_baseline/shorturl
SHORTURL="http://localhost:19332"
TAG="${TAG:-before}"

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "靶场就绪（容器化 shorturl 带 /debug/pprof）"
    $COMPOSE up -d 2>&1 | tail -1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHORTURL/healthz" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shorturl 未就绪"; exit 1; }
        sleep 2
    done
    curl -sf --max-time 2 "$SHORTURL/debug/pprof/" >/dev/null \
        && echo "✅ pprof 端点在位" || { echo "❌ /debug/pprof 不可达"; exit 1; }
}

do_pprof() {
    step "pprof[$TAG]" "k6 施压 45s，同时抓 30s CPU profile 与 heap"
    ( BASE="$SHORTURL" DUR=45s k6 run ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 ) &
    local k6pid=$!
    sleep 3
    go tool pprof -top -seconds 25 -output "reports/cpu_$TAG.txt" \
        "$SHORTURL/debug/pprof/profile" >/dev/null 2>&1
    go tool pprof -top -sample_index=alloc_space -output "reports/heap_$TAG.txt" \
        "$SHORTURL/debug/pprof/heap" >/dev/null 2>&1
    wait $k6pid || true
    echo "  ↳ CPU top5："
    grep -vE '^\s*$' "reports/cpu_$TAG.txt" | sed -n '3,7p' | sed 's/^/    /'
    echo "  ↳ alloc_space top3："
    grep -vE '^\s*$' "reports/heap_$TAG.txt" | sed -n '3,5p' | sed 's/^/    /'
}

do_bench() {
    step "bench[$TAG]" "go test -benchmem（宿主机直跑，与容器同架构 arm64）"
    ( cd "$SHORTDIR" && go test -bench . -benchmem -run XXX -count 1 ) \
        | tee "reports/bench_$TAG.txt" | grep -E 'Benchmark|ok'
}

do_fix() {
    step "fix" "应用修复（map 消线性扫 / byte-slice 消 Sprintf 风暴 / RWMutex）并重建"
    TAG=after
    cp fixes/main_fixed.go "$SHORTDIR/main.go"
    ( cd "$SHORTDIR" && go vet . && go mod vendor )
    $COMPOSE up -d --build shorturl 2>&1 | tail -1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHORTURL/healthz" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ 修复版未就绪"; exit 1; }
        sleep 2
    done
    echo "✅ 修复版已上线"
}

do_restore() {
    step "restore" "恢复缺陷原版并重建（复跑实验用）"
    TAG=before
    cp fixes/main_original.go "$SHORTDIR/main.go"
    ( cd "$SHORTDIR" && go mod vendor )
    $COMPOSE up -d --build shorturl 2>&1 | tail -1
}

do_report() {
    step "report" "bench 前后对比 → docs/pprof_analysis.md"
    python3 gen_pprof_report.py
}

do_clean() {
    step "clean" "无残留"
    echo "✅ done"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; pprof) TAG="${TAG:-before}" do_pprof ;;
        bench) TAG="${TAG:-before}" do_bench ;; fix) do_fix ;;
        restore) do_restore ;; report) do_report ;; clean) do_clean ;;
        all) do_prereq; do_pprof; do_bench; do_fix; do_pprof; do_bench; do_report ;;
        *) echo "可用: prereq|pprof|bench|fix|restore|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
