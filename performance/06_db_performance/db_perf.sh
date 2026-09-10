#!/usr/bin/env bash
# 06 · 数据库性能：慢 SQL 排行 → EXPLAIN 抓 Seq Scan → 建索引 → 连接池打满复现与调参
# 用法: ./db_perf.sh [prereq|scale|top|explain|index|pool|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f ../01_perf_baseline/docker-compose.yml"
PSQL="docker compose -f ../01_perf_baseline/docker-compose.yml exec -T postgres psql -U shop -d shop -v ON_ERROR_STOP=1"
PSQL_T="docker compose -f ../01_perf_baseline/docker-compose.yml exec -T postgres psql -U shop -d shop -tAc"
SHOP="http://localhost:19331"

mkdir -p reports

step() { echo; echo "=====> [$1] $2"; }

wait_shop() {
    local deadline=$((SECONDS + 120))
    until curl -sf --max-time 2 "$SHOP/health" >/dev/null; do
        [ $SECONDS -ge $deadline ] && { echo "❌ shop 未就绪"; exit 1; }
        sleep 2
    done
}

do_prereq() {
    step "prereq" "靶场就绪 + pg_stat_statements 生效（改了 preload 需重建 postgres）"
    local need_restart=no
    $COMPOSE up -d 2>&1 | tail -1
    # preload 生效性检查：build 里的 command 要真的跑在当前 postgres 上
    if ! $PSQL -tAc "SHOW shared_preload_libraries" 2>/dev/null | grep -q pg_stat_statements; then
        need_restart=yes
    fi
    if [ "$need_restart" = yes ]; then
        echo "  ↳ postgres 未预载 pg_stat_statements，重启 postgres 与 shop（清池）..."
        $COMPOSE up -d --build shop postgres 2>&1 | tail -1
        sleep 5
        wait_shop
        # postgres 重启后 shop 连接池可能持有尸体连接：重启清池（lab 04 踩过的坑）
        $COMPOSE restart shop >/dev/null 2>&1 && sleep 3 && wait_shop
    fi
    $PSQL < sql/setup.sql >/dev/null
    echo "✅ pg_stat_statements 就绪，慢查询阈值 50ms"
}

do_scale() {
    step "scale" "放大 stock 到 5 万行——数据量太小计划器永远选 Seq Scan，先让它说真话"
    $PSQL -tAc "SELECT count(*) FROM stock" | grep -qE '^([0-9]{1,5})$' || true
    local n=$($PSQL -tAc "SELECT count(*) FROM stock")
    if [ "$n" -lt 50000 ]; then
        $PSQL -q -c "INSERT INTO stock (product_id, qty)
            SELECT 1 + (g % 200), (random() * 1000)::int
            FROM generate_series(1, 50000) g" >/dev/null
        echo "  ↳ 已插入，当前 $n → $[$($PSQL -tAc 'SELECT count(*) FROM stock')] 行"
    else
        echo "  ↳ 已有 $n 行，跳过（幂等）"
    fi
    echo "✅ $[$($PSQL -tAc 'SELECT count(*) FROM stock')] 行库存"
}

do_top() {
    step "top[$1]" "pg_stat_statements 按总耗时排行（前 5）"
    $PSQL -c "
        SELECT round(total_exec_time::numeric, 1) AS total_ms,
               calls, round(mean_exec_time::numeric, 2) AS mean_ms,
               left(query, 60) AS query
        FROM pg_stat_statements
        ORDER BY total_exec_time DESC LIMIT 5" \
        | tee "reports/pg_stat_top_$1.txt"
}

do_explain() {
    step "explain[$1]" "商品列表 JOIN 的执行计划（ANALYZE + BUFFERS）"
    $PSQL_T "
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT p.id, p.name, p.price, COALESCE(s.qty, 0)
        FROM products p LEFT JOIN stock s ON s.product_id = p.id
        ORDER BY p.id LIMIT 50" \
        > "reports/explain_$1.json"
    python3 - "$1" <<'EOF'
import json, sys
plan = json.load(open(f"reports/explain_{sys.argv[1]}.json"))[0]["Plan"]
def find(node, kinds):
    if node["Node Type"] in kinds:
        return node
    for ch in node.get("Plans", []):
        r = find(ch, kinds)
        if r: return r
scan = find(plan, {"Seq Scan", "Index Scan", "Bitmap Heap Scan"})
print(f"  ↳ 扫描方式: {scan['Node Type']} on {scan.get('Relation Name')}")
print(f"  ↳ 该节点实际耗时: {scan['Actual Total Time']:.3f} ms，行数 {scan['Actual Rows']}")
EOF
}

do_drop_index() {
    step "drop-index" "撤掉索引恢复 D7 现场（复跑 explain-before 用）"
    $PSQL -q -c "DROP INDEX IF EXISTS idx_stock_product_id; DROP INDEX IF EXISTS idx_orders_product_id;"
    $PSQL -q -c "SELECT pg_stat_statements_reset();" >/dev/null
    echo "✅ 索引已撤、排行榜已清零"
}

do_burst() { # TAG=标签：先 reset 再压 30s，让排行榜只含本轮
    : "${TAG:=before}"
    step "burst[$TAG]" "k6 20 VU × 30s，喂饱 pg_stat_statements"
    $PSQL -q -c "SELECT pg_stat_statements_reset();" >/dev/null
    BASE="$SHOP" VUS=20 DUR=30s k6 run ../02_load_modeling/k6/closed.js >/dev/null 2>&1 || true
    echo "✅ 完成"
}

do_index() {
    step "index" "应用索引迁移（stock.product_id / orders.product_id）"
    $PSQL < sql/index_migration.sql >/dev/null
    $PSQL -c "\di idx_*" | head -6
}

do_pool() { # TAG=before/after  环境变量 POOL_MAX_SIZE 决定池上限
    : "${POOL_MAX_SIZE:=10}"
    step "pool[$TAG]" "100 VU 压 45s，每 3s 采样 PG 活跃连接数（看池顶在哪儿）"
    ( BASE="$SHOP" VUS=100 DUR=45s k6 run --summary-export \
        "reports/pool_$TAG.json" ../02_load_modeling/k6/closed.js >/dev/null 2>&1 ) &
    local k6pid=$!
    : > "reports/pg_activity_$TAG.txt"
    for i in $(seq 1 15); do
        local n
        n=$($PSQL -tAc "SELECT count(*) FROM pg_stat_activity WHERE state='active' AND query NOT LIKE '%pg_stat_activity%'" 2>/dev/null || echo "?")
        echo "t+$((i*3))s active=$n" >> "reports/pg_activity_$TAG.txt"
        sleep 3
    done
    wait $k6pid || true
    echo "  ↳ 活跃连接峰值：$(sed 's/.*active=//' reports/pg_activity_$TAG.txt | sort -n | tail -1)（池上限 ${POOL_MAX_SIZE}）"
    python3 -c "
import json
m = json.load(open('reports/pool_$TAG.json'))['metrics']
d = m['http_req_duration']
print(f\"  ↳ RPS={m['http_reqs'].get('rate',0):.1f}  P95={d['p(95)']:.1f}ms  错误率={m['http_req_failed'].get('rate', m['http_req_failed'].get('value',0))*100:.2f}%\")"
}

do_report() {
    step "report" "汇总 → docs/db_analysis.md"
    python3 gen_db_report.py
}

do_clean() {
    step "clean" "索引保留（生产正确状态）；如需复跑 explain-before：DROP INDEX idx_stock_product_id"
    echo "✅ done"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; scale) do_scale ;; top) do_top "${TAG:-before}" ;;
        drop-index) do_drop_index ;; burst) do_burst "${TAG:-before}" ;;
        explain) do_explain "${TAG:-before}" ;; index) do_index ;;
        pool) TAG="${TAG:-before}" do_pool ;; report) do_report ;; clean) do_clean ;;
        all)
            do_prereq; do_scale
            do_drop_index
            TAG=before do_burst
            do_top before; do_explain before
            do_index; do_explain after
            TAG=after do_burst; do_top after
            export POOL_MAX_SIZE=10
            $COMPOSE up -d shop >/dev/null 2>&1; sleep 3; wait_shop
            TAG=before do_pool
            export POOL_MAX_SIZE=40
            $COMPOSE up -d shop >/dev/null 2>&1; sleep 3; wait_shop
            TAG=after do_pool
            unset POOL_MAX_SIZE
            do_report ;;
        *) echo "可用: prereq|scale|top|explain|index|pool|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
