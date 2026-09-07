#!/usr/bin/env bash
# =============================================================================
# sut_app.sh — lab 11 主演示脚本：起服务 → 种子数据 → 自测冒烟 → 停服清理
# 端口默认 8765，可用 SUT_PORT 覆盖；后续实验通过 SUT_BASE_URL 复用本服务。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT="${SUT_PORT:-8899}"
BASE_URL="http://127.0.0.1:${SUT_PORT}"
DB="app/orders.db"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_server() {  # 起服务并等健康检查（轮询而非裸 sleep）
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "服务已在运行 (pid $(cat "$PIDFILE"))"; return 0
    fi
    # nohup + </dev/null + disown：完全脱离脚本的控制台、管道与作业表
    cd app
    SUT_DB="$PWD/$(basename "$DB")" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../../.sut.log 2>&1 &
    echo $! > "../${PIDFILE}"
    disown
    cd ..
    # 轮询健康检查：就绪即返回（上限 10s），绝不裸 sleep
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "服务启动失败，日志尾部：" >&2; tail -5 "$PWD/../../.sut.log" >&2; return 1
}

stop_server() {
    if [ -f "$PIDFILE" ]; then
        kill "$(cat "$PIDFILE")" 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    # 兜底：按端口清残留（pid 文件丢失也能停干净）
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    echo "服务已停止"
}

do_apply() {
    step "apply" "初始化数据库 + 种子数据（幂等：重复执行不会重复插入吗？会——先清库再种）"
    rm -f "$DB"
    "$PY" app/seed.py --db "$DB"
    "$PY" -c "import sys; sys.path.insert(0, 'app'); import store; print('当前订单数:', store.count('$DB'))"
}

do_observe() {
    step "observe" "① 起服务（uvicorn）并等待健康检查通过"
    start_server

    step "observe" "② API 快速走查：健康/下单/查列表/删单"
    curl -s "${BASE_URL}/api/health"; echo
    OID=$(curl -s -X POST "${BASE_URL}/api/orders" -H 'Content-Type: application/json' \
        -d '{"customer":"脚本走查","item":"curl 商品","qty":1,"price":9.9}' | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])")
    echo "已创建订单 ${OID}；列表总数：$(curl -s -D - -o /dev/null "${BASE_URL}/api/orders" | grep -i x-total-count | tr -d '\r')"
    curl -s -X DELETE "${BASE_URL}/api/orders/$OID" -o /dev/null -w "删除订单 ${OID} -> HTTP %{http_code}\n"

    step "observe" "③ 静态页可达性：下单页 / 慢加载页 / 登录页 / Admin 页"
    for p in / /slow.html /login.html /admin.html; do
        curl -s -o /dev/null -w "GET $p -> HTTP %{http_code}\n" "${BASE_URL}$p"
    done
    echo ">>> 用浏览器打开 ${BASE_URL} 可手动下单体验；${BASE_URL}/slow.html 是 lab 17 的等待训练页"

    step "observe" "④ SUT 自测冒烟（tests/test_sut_smoke.py）"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. -q
    echo ">>> observe 完成（服务保留运行中，探索完可执行 ./sut_app.sh clean）"
}

do_clean() {
    step "clean" "停服务、删库删日志——目录回到实验前状态"
    stop_server
    rm -f "$DB" "$DB-journal"
    rm -rf .pytest_cache tests/__pycache__ app/__pycache__
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
