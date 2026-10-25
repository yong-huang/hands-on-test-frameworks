#!/usr/bin/env bash
# =============================================================================
# run_all.sh — lab 25 一键对比：Playwright / Cypress / Selenium 各跑 ROUNDS 轮
# 产出 docs/results.csv（framework,round,duration_s,passed,failed）
# 用量：ROUNDS=3 ./run_all.sh（默认 3 轮；验收场景可调到 20）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
ROUNDS="${ROUNDS:-3}"
SUT_PORT=8925
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
CY_DIR="../21_cypress_basics"          # 复用 21 的 node_modules（同一台机不重复装 Cypress）
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_cmp.log 2>&1 &
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

run_rounds() {  # $1=框架名 $2=执行命令（模板，含 {NONE} 占位）
    local name="$1"; shift
    for r in $(seq 1 "$ROUNDS"); do
        T0=$(date +%s.%N)
        set +e
        OUT=$("$@" 2>/dev/null)
        RC=$?
        set -e
        T1=$(date +%s.%N)
        DUR=$(echo "$T1 $T0" | awk '{printf "%.2f", $1-$2}')
        PASS=$(echo "$OUT" | grep -oE '[0-9]+ passed' | grep -oE '^[0-9]+' | head -1 || true)
        FAIL=$(echo "$OUT" | grep -oE '[0-9]+ failed' | grep -oE '^[0-9]+' | head -1 || true)
        echo "${name},${r},${DUR},${PASS:-0},${FAIL:-0}" >> docs/results.csv
        echo "  ${name} 第 ${r} 轮: ${DUR}s (passed=${PASS:-0} failed=${FAIL:-0})"
    done
}

do_apply() {
    step "apply" "起 SUT（${SUT_PORT}）+ 初始化 CSV"
    start_sut
    mkdir -p docs
    echo "framework,round,duration_s,passed,failed" > docs/results.csv
}

do_observe() {
    step "observe" "Playwright（Chromium）× ${ROUNDS} 轮"
    run_rounds playwright $PY -m pytest -c configs/pytest.ini --rootdir=. \
        --base-url "$BASE_URL" -o addopts= -q tests/pw_suite.py

    step "observe" "Cypress（Electron）× ${ROUNDS} 轮"
    # Cypress 要求 spec 在其项目根内：把 25 的 suite 拷进 21 跑，跑完删除
    cp cypress/e2e/suite.cy.js "$CY_DIR/cypress/e2e/suite_25.cy.js"
    (cd "$CY_DIR" && for r in $(seq 1 "$ROUNDS"); do
        T0=$(date +%s.%N)
        OUT=$(CYPRESS_SUT_URL="$BASE_URL" npx cypress run --spec \
            "cypress/e2e/suite_25.cy.js" --config baseUrl="$BASE_URL" 2>/dev/null || true)
        T1=$(date +%s.%N)
        DUR=$(echo "$T1 $T0" | awk '{printf "%.2f", $1-$2}')
        PASS=$(echo "$OUT" | grep -oE '[0-9]+ passing' | grep -oE '[0-9]+' | head -1 || true)
        FAIL=$(echo "$OUT" | grep -oE '[0-9]+ failing' | grep -oE '[0-9]+' | head -1 || true)
        echo "cypress,${r},${DUR},${PASS:-0},${FAIL:-0}" >> "$OLDPWD/docs/results.csv"
        echo "  cypress 第 ${r} 轮: ${DUR}s (passed=${PASS:-0} failed=${FAIL:-0})"
    done)
    rm -f "$CY_DIR/cypress/e2e/suite_25.cy.js"

    step "observe" "Selenium（Chrome）× ${ROUNDS} 轮"
    run_rounds selenium $PY -m pytest -c configs/pytest.ini --rootdir=. \
        -o addopts= -q tests/sel_suite.py
    # selenium 的 driver 输出格式与上面一致

    step "observe" "结果落盘 docs/results.csv"
    column -t -s, docs/results.csv 2>/dev/null || cat docs/results.csv
}

do_clean() {
    step "clean" "停 SUT、删测试库"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__
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
