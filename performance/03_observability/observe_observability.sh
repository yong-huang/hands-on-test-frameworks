#!/usr/bin/env bash
# 03 · 监控栈与黄金信号：叠加监控 → 边压边看 → 告警触发 → 证据入册
# 用法: ./observe_observability.sh [prereq|apply|load|report|clean|all]
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE01="docker compose -f ../01_perf_baseline/docker-compose.yml"
MON="docker compose -f docker-compose.monitor.yml"
PROM="http://localhost:19090"

step() { echo; echo "=====> [$1] $2"; }

do_prereq() {
    step "prereq" "确认 lab 01 靶场在位"
    if ! curl -sf http://localhost:19331/health >/dev/null 2>&1; then
        $COMPOSE01 up -d --quiet-pull
        local deadline=$((SECONDS + 180))
        until curl -sf http://localhost:19331/health >/dev/null && curl -sf http://localhost:19332/healthz >/dev/null; do
            [ $SECONDS -ge $deadline ] && { echo "❌ 靶场未就绪"; exit 1; }
            sleep 3
        done
    fi
    echo "✅ 靶场就绪"
}

wait_targets() { # 等 Prometheus 全部 target 就绪
    local deadline=$((SECONDS + 60))
    while :; do
        local up
        up=$(curl -s "$PROM/api/v1/targets" | python3 -c "
import json,sys
d=json.load(sys.stdin)
ts=d['data']['activeTargets']
ok=[t for t in ts if t['health']=='up']
print(f'{len(ok)}/{len(ts)}')" 2>/dev/null || echo "?")
        echo "  targets up: $up"
        [ "$up" = "4/4" ] && break
        [ $SECONDS -ge $deadline ] && { echo "⚠️ targets 未全部就绪，继续（可能 exporter 慢启动）"; break; }
        sleep 3
    done
}

do_apply() {
    step "apply" "起监控栈（prometheus + grafana + pg/redis exporter）"
    $MON up -d --quiet-pull
    local deadline=$((SECONDS + 90))
    until curl -sf "$PROM/-/ready" >/dev/null 2>&1; do
        [ $SECONDS -ge $deadline ] && { echo "❌ prometheus 未就绪"; exit 1; }
        sleep 2
    done
    wait_targets
    echo "✅ Grafana: http://localhost:13000（匿名只读）· Prometheus: $PROM"
}

do_load() {
    step "load" "开压（开放模型 150 it/s × 90s），期间盯告警"
    ( BASE=http://localhost:19331 RATE=150 VUPOOL=400 DUR=90s \
        k6 run --summary-export ../02_load_modeling/reports/obs_load.json \
        ../02_load_modeling/k6/open.js >/dev/null 2>&1 ) &
    local k6pid=$!
    local fired=no
    for i in $(seq 1 24); do
        sleep 5
        local alerts
        alerts=$(curl -s "$PROM/api/v1/alerts" | python3 -c "
import json,sys
d=json.load(sys.stdin)
f=[a for a in d['data']['alerts'] if a['state']=='firing']
print(','.join(a['labels']['alertname'] for a in f) or 'none')" 2>/dev/null || echo none)
        echo "  [t+$((i*5))s] firing: $alerts"
        [ "$alerts" != "none" ] && fired=yes
    done
    wait $k6pid || true
    echo "fired=$fired" > reports/.alert_fired
    echo "✅ 压测结束，告警触发: $fired"
}

do_report() {
    step "report" "查询黄金信号 → docs/golden.md"
    local fired=yes
    [ -f reports/.alert_fired ] && fired=$(sed 's/fired=//' reports/.alert_fired)
    python3 gen_golden.py "$fired"
}

do_clean() {
    step "clean" "停监控栈（靶场保留，实验 01 是公共设施）"
    $MON down --remove-orphans
}

main() {
    local target="${1:-all}"
    case "${target}" in
        prereq) do_prereq ;; apply) do_apply ;; load) do_load ;;
        report) do_report ;; clean) do_clean ;;
        all) do_prereq; do_apply; do_load; do_report ;;
        *) echo "可用: prereq|apply|load|report|clean|all" >&2; exit 1 ;;
    esac
}
main "$@"
