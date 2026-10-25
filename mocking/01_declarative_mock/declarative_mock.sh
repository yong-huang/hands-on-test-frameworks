#!/usr/bin/env bash
# =============================================================================
# declarative_mock.sh — mocking 01 主演示脚本：
# 起声明式 mock(:9100) → 特异度阶梯 → 响亮未命中 → 并发零错答 → 统计对账 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
MOCK=9100

step() { echo; echo "=====> [$1] $2"; }

wait_health() {  # 轮询 /__health__ 就绪，不裸 sleep
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:$1/__health__" -o /dev/null 2>/dev/null && return 0
        sleep 0.25
    done
    echo "端口 $1 未就绪" >&2; return 1
}

start_bg() {  # nohup 脱管启动，pid 存 reports/
    # 包装壳 trap "" 吸收信号死亡防 Terminated 噪声；但 SIG_IGN 会被子进程继承，
    # 导致 python 无视 SIGTERM、清理静默失效——所以内层子壳先 trap - 恢复默认处置
    # 再 exec python（exec 后同 PID，pidfile 记的就是 python 自己）
    local name="$1"; shift
    nohup env PY="$PY" PIDFILE="$PWD/reports/$name.pid" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$PY" mockserver.py "$@" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' mockserver "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {  # TERM 优雅杀 → 仍占则 KILL 兜底 → 等端口真正空闲（防双绑定的静默串味）
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && { echo "  TERM 无效，升级 KILL: $pids"; kill -9 $pids 2>/dev/null || true; }
    sleep 0.2
}

do_apply() {
    step "apply" "① 清场（含上次中断的残留端口）+ 加载 stubs/ 规则起 mock(:$MOCK)"
    [ -f reports/mock.pid ] && kill "$(cat reports/mock.pid)" 2>/dev/null || true
    kill_port "$MOCK"
    mkdir -p reports
    rm -f reports/*.pid reports/servers.log
    start_bg mock --port "$MOCK" --stubs stubs
    wait_health "$MOCK"
    sleep 0.5  # 给「绑定失败即死」留暴露窗口，防止健康检查被残留旧进程接答
    kill -0 "$(cat reports/mock.pid)" 2>/dev/null || { echo "mock 启动即死，见 reports/servers.log" >&2; exit 1; }
    echo "--- 已加载的规则表 ---"
    curl -sf "http://127.0.0.1:$MOCK/__stubs__" | "$PY" -c "
import json, sys
for s in json.load(sys.stdin):
    print(f\"  {s['id']:<20} {s['score']:>3} 分  ({s['source']}) {s['description'][:38]}\")"
}

do_observe() {
    step "observe" "② 阶梯/未命中/并发/统计：client.py 自带全部断言，输出即验收"
    "$PY" client.py "http://127.0.0.1:$MOCK" | tee reports/run.txt
    grep -q "❌" reports/run.txt && { echo "存在失败断言"; exit 1; } || true
}

do_clean() {
    step "clean" "杀服务、删产物——环境回到实验前状态"
    [ -f reports/mock.pid ] && kill "$(cat reports/mock.pid)" 2>/dev/null || true
    kill_port "$MOCK"
    rm -rf reports __pycache__
    lsof -ti ":$MOCK" >/dev/null 2>&1 && { echo "❌ 端口 $MOCK 仍被占用"; exit 1; }
    echo "已清理（端口 $MOCK 确认空闲）"
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
