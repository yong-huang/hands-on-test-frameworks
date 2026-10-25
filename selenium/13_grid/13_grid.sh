#!/usr/bin/env bash
# 13_grid.sh — 项目 13：Grid 分布式并行（串行 vs xdist 并行计时对照）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "拉起共享靶场 + Grid（standalone-chrome，4 并发会话）"
    bash "$SERIES/shop/shop.sh" apply
    if ! curl -sf -m 2 "http://127.0.0.1:4444/status" >/dev/null 2>&1; then
        docker compose up -d
        for i in $(seq 1 60); do
            ready=$("$PY" - <<'EOF'
import json, urllib.request
try:
    d = json.load(urllib.request.urlopen("http://127.0.0.1:4444/status", timeout=2))
    print(1 if d["value"]["ready"] else 0)
except Exception:
    print(0)
EOF
)
            [ "$ready" = "1" ] && break
            sleep 1
        done
        curl -sf "http://127.0.0.1:4444/status" >/dev/null || { echo "Grid 未就绪" >&2; exit 1; }
        echo "Grid 就绪（standalone，4 会话槽）"
    else
        echo "Grid 已在运行"
    fi
}

do_observe() {
    step "observe" "① 串行基线（20 条）"
    local t0 t1 serial parallel
    t0=$(date +%s)
    (cd "$SERIES" && "$PY" -m pytest 13_grid -q -p no:xdist --basetemp=.tmp_serial >/dev/null)
    t1=$(date +%s); serial=$((t1 - t0))
    echo "    串行墙钟：${serial}s"
    step "observe" "② pytest-xdist -n 4 并行"
    t0=$(date +%s)
    (cd "$SERIES" && "$PY" -m pytest 13_grid -q -n 4 --basetemp=.tmp_par >/dev/null)
    t1=$(date +%s); parallel=$((t1 - t0))
    echo "    并行墙钟：${parallel}s"
    "$PY" - "$serial" "$parallel" <<'EOF'
import sys
serial, parallel = int(sys.argv[1]), int(sys.argv[2])
if parallel <= 0:
    print("❌ 并行计时异常"); sys.exit(1)
speedup = round((1 - parallel / max(serial, 1)) * 100)
print(f"    提速 {speedup}%（验收线 ≥60%）")
sys.exit(0 if speedup >= 60 else 1)
EOF
    echo "    ✅ 并行验收通过"
}

do_clean() {
    step "clean" "停 Grid、清临时产物（靶场为公共设施保留）"
    docker compose down -v --remove-orphans >/dev/null 2>&1 || true
    rm -rf "$SERIES/.tmp_serial" "$SERIES/.tmp_par" "$SERIES/13_grid/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
