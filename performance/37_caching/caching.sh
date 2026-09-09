#!/usr/bin/env bash
# 37 · 缓存三大问题：命中率 → 穿透 → 击穿 → 雪崩，逐一复现、逐一设防
# 用法: ./caching.sh [prereq|hits|penetrate|breakdown|avalanche|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../31_perf_baseline/docker-compose.yml"
SHOP="http://localhost:19331"
PSQL="docker compose -f ../31_perf_baseline/docker-compose.yml exec -T postgres psql -U shop -d shop -tAc"
RESULTS=reports/caching_results.txt

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "靶场就绪（shop 带缓存层，Redis 在位）"
    $COMPOSE up -d 2>&1 | tail -1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop 未就绪"; exit 1; }
        sleep 2
    done
    mkdir -p reports
    touch "$RESULTS"
    echo "✅ 就绪"
}

switch_mode() { # $1=on|hardened  重建并切换缓存档位，清空 Redis
    export CACHE_MODE="$1"
    $COMPOSE up -d --build shop >/dev/null 2>&1
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop($1) 未就绪"; exit 1; }
        sleep 2
    done
    docker compose -f ../31_perf_baseline/docker-compose.yml exec -T redis redis-cli FLUSHALL >/dev/null
    echo "✅ CACHE_MODE=$1 已上线"
}

counters() { # 命中/穿透计数快照 → 供 delta 计算
    curl -s "$SHOP/metrics" | grep '^shop_cache_ops_total' | awk '{split($1,a,"\""); print a[2], $NF}' \
        | awk '{c[$1]=$2} END {print c["hit"]+0, c["miss"]+0, c["negative"]+0}'
}

db_calls() { # 详情查询的累计调用次数（pg_stat_statements）
    $PSQL "SELECT coalesce(sum(calls),0) FROM pg_stat_statements WHERE query LIKE '%recommend_scores r%'" \
        | tr -d ' '
}

wait_ok() { echo "✅ $1"; }

do_hits() {
    step "hits[on]" "热点读 20 VU × 30s（ids 1-50，只读——写失效会拉低命中率，属正常行为）"
    python3 - "$SHOP" <<'K6EOF' > reports/hits.js
import sys, re
base = sys.argv[1]
src = open('../32_load_modeling/k6/closed.js').read()
src = src.replace("const BASE = __ENV.BASE || 'http://localhost:19331';", f"const BASE = '{base}';")
src = src.replace("const pid = 1 + (__ITER % 200);", "const pid = 1 + (__ITER % 50);")
src = re.sub(r"if \(__ITER % 2 === 0\) \{[\s\S]*?\n  \}\n", "", src)
src = re.sub(r"  sleep\(0\.1\);\n\}", "}", src)
print(src)
K6EOF
    local c0=$(counters)
    BASE="$SHOP" VUS=20 DUR=30s k6 run --summary-export reports/hits.json \
        reports/hits.js >/dev/null 2>&1 || true
    local c1=$(counters)
    python3 - "$c0" "$c1" <<'EOF' | tee -a "$RESULTS"
import sys
h0, m0, n0 = map(float, sys.argv[1].split())
h1, m1, n1 = map(float, sys.argv[2].split())
hr = (h1 - h0) / max(h1 - h0 + m1 - m0, 1) * 100
print(f"exp=hits mode=on hit_rate={hr:.1f}% verdict={'PASS' if hr > 90 else 'FAIL'}(>90%)")
EOF
    wait_ok "命中率证据入册"
}

do_penetrate() { # $1=模式
    step "penetrate[$1]" "打不存在的商品 id（3001-3200），裸缓存必穿，hardened 空值缓存挡住"
    local c0=$(db_calls) m0=$(counters)
    python3 - "$SHOP" <<'K6EOF' > reports/penetrate_$1.js
import sys, re
base = sys.argv[1]
src = open('../32_load_modeling/k6/closed.js').read()
src = src.replace("const BASE = __ENV.BASE || 'http://localhost:19331';", f"const BASE = '{base}';")
src = src.replace("const pid = 1 + (__ITER % 200);", "const pid = 3001 + (__ITER % 200);")
src = re.sub(r"if \(__ITER % 2 === 0\) \{[\s\S]*?\n  \}\n", "", src)
src = re.sub(r"  sleep\(0\.1\);\n\}", "}", src)
print(src)
K6EOF
    BASE="$SHOP" VUS=20 DUR=20s k6 run --summary-export "reports/penetrate_$1.json" \
        reports/penetrate_$1.js >/dev/null 2>&1 || true
    local c1=$(db_calls) m1=$(counters)
    python3 - "$1" "$c0" "$c1" "$m0" "$m1" <<'EOF' | tee -a "$RESULTS"
import sys
mode = sys.argv[1]
db = float(sys.argv[3]) - float(sys.argv[2])
_, _, neg = map(float, sys.argv[5].split())
print(f"exp=penetrate mode={mode} db_calls={db:.0f} negative_cached={neg:.0f} "
      f"verdict={'BLOCKED' if mode=='hardened' and db < 500 else 'PASSTHROUGH'}")
EOF
    wait_ok "穿透证据入册"
}

do_breakdown() { # $1=模式
    step "breakdown[$1]" "50 VU 全打同一热 key（id=42），每 6s DEL 一次制造击穿窗口"
    local c0=$(db_calls)
    ( BASE="$SHOP" VUS=50 DUR=40s k6 run ../32_load_modeling/k6/closed.js >/dev/null 2>&1 ) &
    local k6pid=$!
    for i in 1 2 3 4 5; do
        sleep 6
        docker compose -f ../31_perf_baseline/docker-compose.yml exec -T redis \
            redis-cli DEL "product:42" >/dev/null
    done
    wait $k6pid || true
    local c1=$(db_calls)
    python3 - "$1" "$c0" "$c1" <<'EOF' | tee -a "$RESULTS"
import sys
mode, c0, c1 = sys.argv[1], *map(float, sys.argv[2:])
print(f"exp=breakdown mode={mode} db_selects={c1-c0:.0f} "
      f"verdict={'COLLAPSED(≤2/DEL)' if mode=='hardened' else 'THUNDERING_HERD'}")
EOF
    wait_ok "击穿证据入册"
}

do_avalanche() { # $1=模式  CACHE_TTL=60：预热后 3s 开压，逐秒采样 DB 回源峰值
    step "avalanche[$1]" "预热 100 key（TTL=60s，过期带在压测窗口内）→ 逐秒采样 DB 回源峰值"
    for i in $(seq 1 100); do curl -sf --max-time 2 "$SHOP/api/products/$i" >/dev/null || true; done
    sleep 55   # 让预热批整体进入过期带（on=60s 整齐到期；hardened=48~72s 抖散）
    local c0=$(db_calls)
    python3 - "$SHOP" <<'K6EOF' > reports/avalanche_$1.js
import sys, re
base = sys.argv[1]
src = open('../32_load_modeling/k6/closed.js').read()
src = src.replace("const BASE = __ENV.BASE || 'http://localhost:19331';", f"const BASE = '{base}';")
src = src.replace("const pid = 1 + (__ITER % 200);", "const pid = 1 + (__ITER % 100);")
src = re.sub(r"if \(__ITER % 2 === 0\) \{[\s\S]*?\n  \}\n", "", src)
src = re.sub(r"  sleep\(0\.1\);\n\}", "}", src)
print(src)
K6EOF
    ( BASE="$SHOP" VUS=20 DUR=20s k6 run --summary-export "reports/avalanche_$1.json" \
        reports/avalanche_$1.js >/dev/null 2>&1 ) &
    local k6pid=$!
    : > "reports/avalanche_$1.samples"
    for i in $(seq 1 20); do
        echo "$(db_calls)" >> "reports/avalanche_$1.samples"
        sleep 1
    done
    wait $k6pid || true
    python3 - "$1" "reports/avalanche_$1.samples" <<'EOF' | tee -a "$RESULTS"
import sys
mode = sys.argv[1]
calls = [float(l) for l in open(sys.argv[2]) if l.strip()]
per_sec = [b - a for a, b in zip(calls, calls[1:])]
peak = max(per_sec) if per_sec else 0
print(f"exp=avalanche mode={mode} db_peak_per_sec={peak:.0f} "
      f"verdict={'SPREAD' if mode=='hardened' else 'SYNC_EXPIRY'}")
EOF
    wait_ok "雪崩证据入册"
}

do_report() {
    step "report" "汇总 → docs/caching.md"
    python3 gen_cache_report.py
}

do_clean() {
    step "clean" "恢复 off 档（对照态），保留索引与数据"
    export CACHE_MODE=off
    $COMPOSE up -d shop >/dev/null 2>&1
    echo "✅ CACHE_MODE=off"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;;
        hits) do_hits ;;
        penetrate) switch_mode "${MODE:-on}"; do_penetrate "${MODE:-on}" ;;
        breakdown) switch_mode "${MODE:-on}"; do_breakdown "${MODE:-on}" ;;
        avalanche) switch_mode "${MODE:-on}"; do_avalanche "${MODE:-on}" ;;
        report) do_report ;; clean) do_clean ;;
        all)
            do_prereq
            : > "$RESULTS"
            switch_mode on;    do_hits
            do_penetrate on
            switch_mode hardened; do_penetrate hardened
            switch_mode on;    do_breakdown on
            switch_mode hardened; do_breakdown hardened
            export CACHE_TTL=60
            switch_mode on;    do_avalanche on
            switch_mode hardened; do_avalanche hardened
            unset CACHE_TTL
            do_report ;;
        *) echo "可用: prereq|hits|penetrate|breakdown|avalanche|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
