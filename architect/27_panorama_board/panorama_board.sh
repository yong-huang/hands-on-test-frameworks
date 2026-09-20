#!/usr/bin/env bash
# =============================================================================
# panorama_board.sh — architect 27 主演示脚本（⛓️ 集成点）：
# auto 模式聚合全部项目产物（含自动生成缺失源）→ no-auto 缺失明示演示 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {  # 20 压测容量需要 SUT
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    ( cd "$SUT_DIR/app"
      SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 \
          </dev/null > "$here/.sut.log" 2>&1 & echo $! > "$here/.sut.pid" )
    disown 2>/dev/null || true
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

do_apply() {
    step "apply" "① 起 SUT（20 压测容量的前置）+ 清空旧看板"
    start_sut
    rm -rf reports
}

do_observe() {
    step "observe" "① auto 聚合：缺失的兄弟项目产物自动以轻量模式再生成"
    set +e
    "$PY" panorama.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 指标不足 8"; exit 1; }

    step "observe" "② no-auto 演示：只读现有产物，缺失的面板明示原因"
    rm -f ../../architect/20_load_model/reports/capacity.json
    "$PY" panorama.py --no-auto --out reports/noauto 2>&1 | grep -E "数据缺失" | head -2
    mv "$REPO/architect/20_load_model/reports/capacity.json" reports/ 2>/dev/null || \
        ( cd "$REPO/architect/20_load_model" && "$PY" load_model.py >/dev/null 2>&1 )

    step "observe" "③ 根 Makefile 一键入口（校验目标存在；完整执行会递归本实验，故不在此跑）"
    grep -q "^architect-report:" "$REPO/Makefile" && echo "make architect-report 入口已配置 ✅"
    echo ">>> 验收：一条命令 ≥8 指标 ✅ 缺失明示 ✅ make 入口可用 ✅"
}

do_clean() {
    step "clean" "停 SUT、清各兄弟项目产物与本目录产物"
    if [ -f .sut.pid ]; then kill "$(cat .sut.pid)" 2>/dev/null || true; rm -f .sut.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .sut.log
    for d in 01_pyramid_audit 02_risk_strategy 03_quality_gate 13_flaky_platform \
             20_load_model 22_security_gate; do
        rm -rf "../$d/reports"
    done
    rm -rf reports __pycache__
    ( cd "$SUT_DIR" && rm -f app/orders.db app/orders.db-journal ) || true
    echo "已清理（各项目 reports 由本实验生成，clean 一并还原）"
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
