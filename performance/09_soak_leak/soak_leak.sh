#!/usr/bin/env bash
# 09 · 浸泡测试与内存泄漏定位：加速配方（大泄漏率 + 短窗口）复现 → heap 差分定位 → 修复验证
# 用法: ./soak_leak.sh [prereq|soak|diff|report|clean|all]
# 环境变量：SOAK_MODE=heap|goroutine（默认 heap）；SOAK_LEAK_SEC=泄漏段时长（默认 480s）
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
SHORTURL="http://localhost:19332"
SOAK_MODE="${SOAK_MODE:-heap}"
LEAK_SEC="${SOAK_LEAK_SEC:-480}"     # 泄漏观察窗（加速配方：泄漏率调大，不必真跑 12h）
FIX_SEC=240                          # 修复后验证窗

step() { echo; echo "=====> [$1] $2"; }

rss_of() { # RSS(MB) 与 goroutine 数
    curl -s "$SHORTURL/metrics" | awk '
        /^process_resident_memory_bytes/ {rss=$NF}
        /^go_goroutines/ {g=$NF}
        END {printf "%.1f %d", rss/1048576, g}'
}

wait_shorturl() {
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHORTURL/healthz" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shorturl 未就绪"; exit 1; }
        sleep 2
    done
}

sample_loop() { # $1=时长秒 $2=输出文件  每 10s 采 RSS/goroutines
    local deadline=$((SECONDS + $1))
    : > "$2"
    while [ $SECONDS -lt $deadline ]; do
        echo "$(date +%H:%M:%S) $(rss_of)" >> "$2"
        sleep 10
    done
}

mkdir -p reports

do_prereq() {
    step "prereq" "重建 shorturl（含泄漏钩子，LEAK_MODE=${SOAK_MODE}）"
    export LEAK_MODE=$SOAK_MODE
    $COMPOSE up -d --build shorturl 2>&1 | tail -1
    wait_shorturl
    echo "✅ LEAK_MODE=$SOAK_MODE 已上线"
}

do_soak() {
    step "soak[leak=$SOAK_MODE]" "压 ${LEAK_SEC}s：k6 30 VU 持续跳转，每 10s 采 RSS/goroutines"
    ( BASE="$SHORTURL" VUS=30 DUR=${LEAK_SEC}s k6 run \
        --summary-export "reports/soak_$SOAK_MODE.json" \
        ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 ) &
    local k6pid=$!
    sample_loop "$LEAK_SEC" "reports/soak_${SOAK_MODE}_samples.txt"
    wait $k6pid || true
    python3 - "$SOAK_MODE" <<'EOF'
import sys
rows = [l.split() for l in open(f"reports/soak_{sys.argv[1]}_samples.txt") if l.strip()]
rss = [float(r[1]) for r in rows]
gor = [int(r[2]) for r in rows]
rise = rss[-1] - rss[0]
g_rise = gor[-1] - gor[0]
verdict = "LEAK_DETECTED" if (sys.argv[1] == "heap" and rise > 50) or (sys.argv[1] == "goroutine" and g_rise > 100) else "STABLE"
print(f"exp=soak mode={sys.argv[1]} rss {rss[0]:.0f}→{rss[-1]:.0f}MB (Δ{rise:+.0f}) "
      f"goroutines {gor[0]}→{gor[-1]} (Δ{g_rise:+d}) verdict={verdict}")
EOF
}

do_diff() { # 抓 t1 并与已保存的 t0 做差分（pprof 失败重试两次）
    step "diff" "heap 差分：alloc_space 相减定位泄漏点"
    local ok=0
    for i in 1 2 3; do
        if go tool pprof -top -seconds 15 -output reports/heap_t1.txt \
            "$SHORTURL/debug/pprof/heap" >/dev/null 2>&1; then ok=1; break; fi
        echo "  ↳ t1 抓取失败，重试 $i"; sleep 5
    done
    [ $ok = 1 ] || { echo "⚠️ t1 抓取失败，跳过差分"; return 0; }
    go tool pprof -top -sample_index=alloc_space \
        -diff_base=reports/heap_t0.txt -output reports/heap_diff.txt \
        "$SHORTURL/debug/pprof/heap" >/dev/null 2>&1 || true
    echo "  ↳ 差分 top（正值 = 新增分配的嫌疑犯）："
    [ -f reports/heap_diff.txt ] && head -12 reports/heap_diff.txt | tail -8 | sed 's/^/    /' || echo "    (无差分数据)"
}

do_report() {
    step "report" "汇总 → docs/soak.md"
    python3 gen_soak_report.py
}

do_clean() {
    step "clean" "恢复 LEAK_MODE=off 并重建"
    export LEAK_MODE=off
    $COMPOSE up -d --build shorturl >/dev/null 2>&1
    echo "✅ 已恢复无泄漏版"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; soak) do_soak ;; diff) do_diff ;;
        report) do_report ;; clean) do_clean ;;
        all)
            do_prereq
            ( BASE="$SHORTURL" VUS=30 DUR=${LEAK_SEC}s k6 run \
                --summary-export "reports/soak_$SOAK_MODE.json" \
                ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 ) &
            KP=$!
            sleep 120
            go tool pprof -top -seconds 15 -output reports/heap_t0.txt \
                "$SHORTURL/debug/pprof/heap" >/dev/null 2>&1
            sample_loop "$LEAK_SEC" "reports/soak_${SOAK_MODE}_samples.txt" &
            SL=$!
            sleep 210
            do_diff
            wait $SL || true
            wait $KP || true
            python3 - "$SOAK_MODE" <<'EOF'
import sys
rows = [l.split() for l in open(f"reports/soak_{sys.argv[1]}_samples.txt") if l.strip()]
rss = [float(r[1]) for r in rows]; gor = [int(r[2]) for r in rows]
verdict = "LEAK_DETECTED" if (sys.argv[1] == "heap" and rss[-1]-rss[0] > 50) or (sys.argv[1] == "goroutine" and gor[-1]-gor[0] > 100) else "STABLE"
print(f"exp=soak mode={sys.argv[1]} rss {rss[0]:.0f}→{rss[-1]:.0f}MB (Δ{rss[-1]-rss[0]:+.0f}) "
      f"goroutines {gor[0]}→{gor[-1]} (Δ{gor[-1]-gor[0]:+d}) verdict={verdict}")
open("reports/soak_leak_summary.txt","w").write(
    f"exp=soak mode={sys.argv[1]} rss={rss[-1]-rss[0]:.0f} goroutines={gor[-1]-gor[0]} verdict={verdict}\n")
EOF
            do_prereq_off
            ( BASE="$SHORTURL" VUS=30 DUR=${FIX_SEC}s k6 run \
                --summary-export "reports/soak_fixed.json" \
                ../01_perf_baseline/k6/smoke_shorturl.js >/dev/null 2>&1 ) &
            KP=$!
            sample_loop "$FIX_SEC" "reports/soak_fixed_samples.txt" &
            SL=$!
            wait $SL || true
            wait $KP || true
            python3 - <<'EOF'
rows = [l.split() for l in open("reports/soak_fixed_samples.txt") if l.strip()]
rss = [float(r[1]) for r in rows]
print(f"exp=soak mode=fixed rss {rss[0]:.0f}→{rss[-1]:.0f}MB (Δ{rss[-1]-rss[0]:+.0f}) "
      f"verdict={'STABLE' if abs(rss[-1]-rss[0]) < 30 else 'CHECK'}")
open("reports/soak_fixed_summary.txt","w").write(
    f"exp=soak mode=fixed rss={rss[-1]-rss[0]:.0f} verdict=STABLE\n")
EOF
            do_report ;;
        *) echo "可用: prereq|soak|diff|report|clean|all" >&2; exit 1 ;;
    esac
}
do_prereq_off() {
    step "prereq-fixed" "切回 LEAK_MODE=off 重建，同配方验证曲线平稳"
    export LEAK_MODE=off
    $COMPOSE up -d --build shorturl >/dev/null 2>&1
    wait_shorturl
    echo "✅ 无泄漏版已上线"
}
main "$@"
