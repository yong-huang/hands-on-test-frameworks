#!/usr/bin/env bash
# =============================================================================
# prism.sh — mocking 08 主演示脚本：
# npx 起 Prism(:9800, 契约 v1) → Schema 校验/422/example 优先级 → 换契约 v2
# （只改 YAML 不改 mock 代码）→ 旧请求红新请求绿 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
PM=9800
PRISM="@stoplight/prism-cli@5.16.0"

step() { echo; echo "=====> [$1] $2"; }

wait_up() {  # 任何 HTTP 应答都算活（未命中路径回 404 也是活）
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/orders" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "Prism 未就绪" >&2; return 1
}

start_bg() {  # nohup 脱管启动（内层 trap- 恢复信号处置，防 SIG_IGN 继承）
    local name="$1"; shift
    nohup env PIDFILE="$PWD/reports/$name.pid" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$@" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' run "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    sleep 0.2
}

start_prism() {  # $1 = 契约文件
    start_bg prism npx -y "$PRISM" mock "$1" -h 127.0.0.1 -p "$PM"
    wait_up "$PM"
    sleep 0.5
    kill -0 "$(cat reports/prism.pid)" 2>/dev/null || { echo "Prism 启动即死，见 reports/servers.log" >&2; exit 1; }
}

do_apply() {
    step "apply" "① 清场 + npx 起 Prism(:${PM}，契约 v1)"
    command -v npx >/dev/null || { echo "缺 node/npx" >&2; exit 1; }
    [ -f reports/prism.pid ] && kill "$(cat reports/prism.pid)" 2>/dev/null || true
    kill_port "$PM"
    mkdir -p reports
    start_prism contracts/orders_v1.yaml
    echo "Prism 监听 :${PM}，契约 contracts/orders_v1.yaml（mock 代码量：0 行）"
}

do_observe() {
    step "observe" "② 契约三事：Schema 校验 / example 优先级 / 422 拒绝"
    "$PY" prism_client.py | tee reports/run_v1.txt
    grep -q "❌" reports/run_v1.txt && { echo "存在失败断言"; exit 1; } || true

    step "observe" "③ 契约随动：换 v2（新增必填 channel），不改任何 mock 代码"
    kill "$(cat reports/prism.pid)" 2>/dev/null || true
    sleep 0.5
    start_prism contracts/orders_v2.yaml
    echo "契约已切换 → contracts/orders_v2.yaml"
    set +e
    OLD=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:$PM/orders" \
        -H "Content-Type: application/json" \
        -d '{"customer":"alice","amount":88.5}')
    NEW=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:$PM/orders" \
        -H "Content-Type: application/json" \
        -d '{"customer":"alice","amount":88.5,"channel":"pos"}')
    set -e
    if [ "$OLD" = "422" ] && [ "$NEW" = "201" ]; then
        echo ">>> 旧请求（无 channel）→ $OLD 红；新请求（带 channel）→ $NEW 绿"
        echo ">>> mock 行为随契约而动 ✅（全程只改了 YAML）"
    else
        echo "❌ 契约随动未生效（旧 $OLD / 新 ${NEW}）"; exit 1
    fi
}

do_clean() {
    step "clean" "杀 Prism、删产物——环境回到实验前状态"
    [ -f reports/prism.pid ] && kill "$(cat reports/prism.pid)" 2>/dev/null || true
    kill_port "$PM"
    rm -rf reports __pycache__
    lsof -ti ":$PM" >/dev/null 2>&1 && { echo "❌ 端口 $PM 仍被占用"; exit 1; }
    echo "已清理（端口 $PM 空闲）"
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
