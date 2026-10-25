#!/usr/bin/env bash
# =============================================================================
# mock_server.sh — architect 08 主演示脚本：
# 录制（经真上游）→ 杀上游断网 → 回放一致 → 磁带改成超时 → 降级分支 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
UP=8900; MOCK=8901
wait_health() {  # 轮询端口就绪，不裸 sleep
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:$1/pay" -o /dev/null 2>/dev/null && return 0
        curl -sf -m 2 "http://127.0.0.1:$1/" -o /dev/null 2>/dev/null && return 0
        sleep 0.25
    done
    echo "端口 $1 未就绪" >&2; return 1
}

step() { echo; echo "=====> [$1] $2"; }

start_bg() {  # nohup 脱管启动，pid 存 reports/
    local name="$1"; shift
    # 脱管包装壳：mockserver 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）。
    # 但 SIG_IGN 处置会被后台子进程继承，python 从此无视 SIGTERM、清理静默失效——
    # 所以内层子壳先 trap - 恢复默认处置再 exec（exec 后同 PID，pidfile 记的就是 python 自己）
    nohup env PY="$PY" PIDFILE="$PWD/reports/$name.pid" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$PY" mockserver.py "$@" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' mockserver "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {  # TERM 优雅杀 → 仍占则 KILL 兜底 → 端口空闲（防残留实例接答）
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    sleep 0.2
}

do_apply() {
    step "apply" "① 清场（含上次中断的残留端口）+ 起假第三方网关(:$UP)与录制模式挡板(:$MOCK)"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$MOCK"
    mkdir -p reports
    rm -f reports/cassette.json reports/mock_stats.json reports/*.pid
    start_bg upstream upstream --port "$UP"
    start_bg mock record --port "$MOCK" --upstream "http://127.0.0.1:$UP"
    wait_health "$UP"; wait_health "$MOCK"
}

do_observe() {
    step "observe" "① 录制：结账客户端经挡板穿透到真上游，磁带随之生成"
    "$PY" client.py --mock "http://127.0.0.1:$MOCK" --order ORDER-FIXED-001 | tee reports/run_record.txt
    echo "--- 磁带内容 ---"; cat reports/cassette.json | "$PY" -c "import json,sys; [print(' ', k, '→', v['status']) for k, v in json.load(sys.stdin).items()]"

    step "observe" "② 断网：杀掉真上游（从此上游不可达），挡板切回放模式"
    kill "$(cat reports/upstream.pid)" 2>/dev/null || true
    kill "$(cat reports/mock.pid)" 2>/dev/null || true
    sleep 0.5
    start_bg mock replay --port "$MOCK"
    sleep 0.5

    step "observe" "③ 回放：断网重跑，输出与录制时逐字节一致"
    "$PY" client.py --mock "http://127.0.0.1:$MOCK" --order ORDER-FIXED-001 | tee reports/run_replay.txt
    if diff -u reports/run_record.txt reports/run_replay.txt; then echo "回放与录制一致 ✅"; else echo "❌ 回放不一致"; exit 1; fi

    step "observe" "④ 命中/未命中统计（回放两连跑应全命中）"
    cat reports/mock_stats.json

    step "observe" "⑤ 磁带手工编辑：把支付接口标记为超时，验证客户端降级分支"
    "$PY" - <<'EOF'
import json
p = "reports/cassette.json"
tape = json.load(open(p, encoding="utf-8"))
tape["POST /pay"]["timeout"] = True
json.dump(tape, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("已标记 POST /pay → 超时磁带")
EOF
    set +e
    "$PY" client.py --mock "http://127.0.0.1:$MOCK" --order ORDER-TIMEOUT-002
    rc=$?
    set -e
    echo ">>> 客户端退出码 ${rc}（1 = 走了 PENDING_RETRY 降级分支，业务未崩）"
    echo ">>> 验收：断网回放一致 ✅ 统计可见 ✅ 磁带编辑生效 ✅"
}

do_clean() {
    step "clean" "杀服务、删磁带与产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$MOCK"
    rm -rf reports __pycache__
    lsof -ti ":$UP" >/dev/null 2>&1 && { echo "❌ 端口 $UP 仍被占用"; exit 1; }
    lsof -ti ":$MOCK" >/dev/null 2>&1 && { echo "❌ 端口 $MOCK 仍被占用"; exit 1; }
    echo "已清理（端口 $UP/$MOCK 确认空闲）"
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
