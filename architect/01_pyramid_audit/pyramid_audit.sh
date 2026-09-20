#!/usr/bin/env bash
# =============================================================================
# pyramid_audit.sh — architect 01 主演示脚本：起 SUT → 分层审计（计数+实测）→ 清理
# 审计工具本体在 audit.py，本脚本负责给它一个「服务就绪」的运行环境。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"
SUT_PORT=8899
BASE_URL="http://127.0.0.1:${SUT_PORT}"
PIDFILE=".sut.pid"
LOG=".sut.log"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（venv + pyyaml，幂等）"
    "$PY" -c "import yaml" 2>/dev/null && echo "pyyaml 就绪" || "$PY" -m pip install -q pyyaml

    step "apply" "② 种子数据并启动 SUT（复用 labs/11 的应用，端口 ${SUT_PORT}）"
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    start_server

    step "apply" "③ 健康检查（轮询而非裸 sleep）"
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo "SUT 就绪：${BASE_URL}"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败，日志尾部：" >&2; tail -5 "$LOG" >&2; return 1
}

start_server() {  # 同 labs/11 的脱管方式：nohup + </dev/null + disown
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "SUT 已在运行 (pid $(cat "$PIDFILE"))"; return 0
    fi
    local here="$PWD"
    cd "$SUT_DIR/app"
    SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > "$here/$LOG" 2>&1 &
    echo $! > "$here/$PIDFILE"
    disown 2>/dev/null || true
    cd "$here"
    echo "已启动 SUT (pid $(cat "$PIDFILE"))"
}

do_observe() {
    step "observe" "① 快速画像（--no-timed，秒级：只数家底不跑用例）"
    "$PY" audit.py --no-timed | sed -n '1,20p'

    step "observe" "② 全量审计（计数 + 实测计时，E2E 层真开浏览器跑）"
    "$PY" audit.py

    step "observe" "③ 产物清点"
    ls -l reports/
    echo ">>> 完整画像见 reports/pyramid_report.md；结构化数据在 reports/pyramid.json（喂后续看板/门禁项目）"
}

do_clean() {  # 删干净无残留：停服 + 删报告 + 清缓存
    step "clean" "停 SUT、删报告与缓存——目录回到实验前状态"
    if [ -f "$PIDFILE" ]; then
        kill "$(cat "$PIDFILE")" 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports .pytest_cache __pycache__ "$LOG"
    ( cd "$SUT_DIR" && rm -rf .pytest_cache tests/__pycache__ app/__pycache__ app/orders.db app/orders.db-journal 2>/dev/null ) || true
    echo "已清理（SUT 数据库一并还原，labs/11 不受影响）"
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
