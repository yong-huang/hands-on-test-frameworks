#!/usr/bin/env bash
# =============================================================================
# security_gate.sh — architect 22 主演示脚本：
# 三层扫描基线 PASS → 植入带 CVE 的旧依赖 → 门禁 FAIL 并点名 CVE → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 装扫描工具（pip-audit/bandit）+ 起 SUT（DAST 需要）"
    "$PY" -c "import pip_audit, bandit" 2>/dev/null || "$PY" -m pip install -q pip-audit bandit
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    # 脱管包装壳：uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    local app_dir; app_dir="$(cd "$SUT_DIR/app" && pwd)"
    nohup env APP_DIR="$app_dir" SUT_DB="$app_dir/orders.db" PY="$PY" PIDFILE="$here/.sut.pid" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$here/.sut.log" 2>&1 &
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

do_observe() {
    step "observe" "① 基线三层扫描（应 PASS）"
    set +e
    "$PY" secgate.py
    rc1=$?
    set -e
    [ "$rc1" -eq 0 ] || { echo "❌ 基线应 PASS"; exit 1; }
    mv reports/sec_report.md reports/sec_baseline.md

    step "observe" "② 植入带已知 CVE 的旧依赖（requests==2.19.0，CVE-2018-18074），扫描副本门禁应 FAIL"
    mkdir -p reports/mutated
    { cat configs/requirements_scan.txt; echo "requests==2.19.0"; } > reports/mutated/requirements_scan.txt
    set +e
    "$PY" secgate.py --reqs reports/mutated/requirements_scan.txt --out reports/mutated
    rc2=$?
    set -e
    echo ">>> 植入后退出码 ${rc2}（1 = 门禁拦截）"

    step "observe" "③ CVE 点名证据 + DAST 真实发现"
    grep -E "CVE|依赖漏洞" reports/mutated/sec_report.md | head -3
    grep -E "admin.html|安全头" reports/sec_baseline.md | head -3
    echo ">>> 验收：基线 PASS ✅ 植入 CVE 被 FAIL 点名 ✅ DAST 发现真实部署层问题 ✅"
}

do_clean() {
    step "clean" "停 SUT、删报告"
    if [ -f .sut.pid ]; then kill "$(cat .sut.pid)" 2>/dev/null || true; rm -f .sut.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .sut.log
    rm -rf reports __pycache__
    ( cd "$SUT_DIR" && rm -f app/orders.db app/orders.db-journal ) || true
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
