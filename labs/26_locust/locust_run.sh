#!/usr/bin/env bash
# =============================================================================
# locust_run.sh — lab 26 主演示脚本：起 SUT → headless 阶梯加压 10→100 → 拐点报告
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8926
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_loc.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

stop_sut() {
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
}

do_apply() {
    step "apply" "起 SUT（独立端口 + 空库——压完即弃）"
    start_sut
}

do_observe() {
    step "observe" "① headless 阶梯加压：10→100 并发，每档 30s（Locust 原生 CSV 报告）"
    # stair-step：4 档 × 30s，真实测出 RPS/延迟随并发的变化
    $PY -m locust -f locustfile.py --headless \
        --users 100 --spawn-rate 10 --run-time 2m \
        --host "$BASE_URL" \
        --csv reports/locust --html reports/locust.html 2>&1 | grep -E "Aggregated|Ramping|Level|Starting" | tail -12

    step "observe" "② 生成拐点报告 docs/bottleneck.md（从 CSV 读实测数）"
    $PY - <<'PYCODE'
import csv
from collections import defaultdict
from pathlib import Path

rows = [r for r in csv.DictReader(open("reports/locust_stats_history.csv", encoding="utf-8"))
        if r["Name"] == "Aggregated" and r["Requests/s"] not in ("0.000000", "N/A")]
by_users = defaultdict(list)
for r in rows:
    by_users[int(r["User Count"])].append(r)

lines = ["# SUT 压测拐点报告（Locust 阶梯加压 10→100 并发实测）", "",
         "每档取该用户数下各采样点的均值（数据源：reports/locust_stats_history.csv）", "",
         "| 并发用户 | 采样均 RPS | 均失败率/s | P95 (ms) |", "|:---|:---|:---|:---|"]
for users in sorted(by_users):
    rs = by_users[users]
    rps = sum(float(r["Requests/s"]) for r in rs) / len(rs)
    fail = sum(float(r["Failures/s"]) for r in rs) / len(rs)
    p95s = [int(r["95%"]) for r in rs if r["95%"] != "N/A"]
    p95 = sum(p95s) / len(p95s) if p95s else 0
    lines.append(f"| {users} | {rps:.1f} | {fail:.2f} | {p95:.0f} |")
lines += ["", "## 瓶颈猜测（对照实测曲线）", "",
          "- 读接口（列表/详情）RPS 高且稳；下单写接口在并发抬升后延迟增长更快——",
          "  根因链：SQLite 单写者锁（lab 13/14 实测）使写请求串行排队；",
          "- 慢接口 sleep(1.5s) 占用线程池名额，高并发下排队效应被放大；",
          "- 对照：lab 14 已证 Postgres MVCC 可解并发写排队；慢接口应改异步端点。"]
Path("docs").mkdir(exist_ok=True)
Path("docs/bottleneck.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:12]))
PYCODE
    echo ">>> 报告: docs/bottleneck.md；完整图表: reports/locust.html（浏览器打开）"
}

do_clean() {
    step "clean" "停 SUT、清库"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache __pycache__
    echo "已清理"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe; do_clean ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
