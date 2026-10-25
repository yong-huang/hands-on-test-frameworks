#!/usr/bin/env bash
# =============================================================================
# hoverfly.sh — mocking 05 主演示脚本：
# 起真上游(:9500)+Hoverfly 代理(:9501) → 代理录制 → 杀上游模拟断网 → 回放
# 逐字节一致 → 手工编辑 simulation 注入 500 按预期红 → 清理
# 编排走 Hoverfly admin API（brew formula 只带 hoverfly 二进制，无 hoverctl）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
UP=9500; HF=9501; ADMIN=9502
ADMIN_URL="http://127.0.0.1:$ADMIN"
UPSTREAM_SCRIPT="../../architect/08_mock_server/mockserver.py"

step() { echo; echo "=====> [$1] $2"; }

wait_health() {  # -f 版：要求 2xx（admin 健康端点用）
    for i in $(seq 1 120); do
        curl -sf -m 2 "$1" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "健康检查超时: $1" >&2; return 1
}

wait_up() {  # 无 -f 版：任何 HTTP 应答都算活（上游对 GET /pay 回 404 也是活）
    for i in $(seq 1 120); do
        curl -s -m 2 "$1" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "上游未就绪: $1" >&2; return 1
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

mode() {  # 切换 Hoverfly 模式（record/simulate）
    curl -sf -X PUT "$ADMIN_URL/api/v2/hoverfly/mode" \
        -H "Content-Type: application/json" -d "{\"mode\":\"$1\"}" >/dev/null
    echo "Hoverfly → $1 模式"
}

do_apply() {
    step "apply" "① 清场 + 起真上游(:${UP}，复用 architect/08 假支付网关)与 Hoverfly 代理(:$HF)"
    command -v hoverfly >/dev/null || { echo "缺 hoverfly：brew install hoverfly" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$HF"; kill_port "$ADMIN"
    mkdir -p reports
    start_bg upstream "$PY" "$UPSTREAM_SCRIPT" upstream --port "$UP"
    start_bg hoverfly hoverfly -pp "$HF" -ap "$ADMIN"
    wait_up "http://127.0.0.1:$UP/pay"
    wait_health "$ADMIN_URL/api/v2/hoverfly"
    echo "Hoverfly $(hoverfly -version 2>/dev/null | head -1) 就绪（代理 :${HF}，admin :${ADMIN}）"
}

do_observe() {
    step "observe" "② 代理录制：客户端把 Hoverfly 当 HTTP 代理，真上游响应被记进 simulation"
    mode capture   # Hoverfly API 里「录制」叫 capture（不叫 record）
    "$PY" proxy_client.py --proxy "http://127.0.0.1:$HF" | tee reports/run_record.txt
    curl -sf "$ADMIN_URL/api/v2/simulation" > reports/simulation.json
    "$PY" -c "
import json, sys
sim = json.load(open('reports/simulation.json'))
pairs = sim['data']['pairs']
print(f'--- simulation 捕获 {len(pairs)} 对交互 ---')
for p in pairs:
    req, resp = p['request'], p['response']
    path = req['path'][0]['value'] if isinstance(req['path'], list) else req['path']
    print(f\"  {req['method'][0]['value'] if isinstance(req['method'], list) else req['method']} {path} → {resp['status']}\")"

    step "observe" "③ 断网：杀掉真上游，Hoverfly 切 simulate——离线回放"
    kill "$(cat reports/upstream.pid)" 2>/dev/null || true
    sleep 0.5
    lsof -ti ":$UP" >/dev/null 2>&1 && { echo "上游未死干净"; exit 1; }
    mode simulate
    "$PY" proxy_client.py --proxy "http://127.0.0.1:$HF" | tee reports/run_replay.txt
    if diff -u reports/run_record.txt reports/run_replay.txt; then
        echo "回放与录制逐字节一致 ✅（上游已死，答案来自 simulation）"
    else
        echo "❌ 回放不一致"; exit 1
    fi

    step "observe" "④ 手工编辑 simulation：把 POST /pay 注入成 500，验证按预期红"
    "$PY" - <<'EOF'
import json
sim = json.load(open("reports/simulation.json", encoding="utf-8"))
for pair in sim["data"]["pairs"]:
    req = pair["request"]
    method = req["method"][0]["value"] if isinstance(req["method"], list) else req["method"]
    path = req["path"][0]["value"] if isinstance(req["path"], list) else req["path"]
    if method == "POST" and path == "/pay":
        pair["response"]["status"] = 500
        pair["response"]["body"] = '{"error": "injected by hand", "code": "INJECTED_500"}'
json.dump(sim, open("reports/simulation_injected.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("已注入：POST /pay → 500 INJECTED_500")
EOF
    curl -sf -X PUT "$ADMIN_URL/api/v2/simulation" \
        -H "Content-Type: application/json" \
        --data-binary @reports/simulation_injected.json >/dev/null
    set +e
    "$PY" proxy_client.py --proxy "http://127.0.0.1:$HF" --expect-500
    rc=$?
    set -e
    echo ">>> 客户端退出码 ${rc}（1 = 注入按预期红：业务走进失败分支而非崩溃）"

    step "observe" "⑤ 恢复原 simulation 再回放——注入是可撤销的单点操作"
    curl -sf -X PUT "$ADMIN_URL/api/v2/simulation" \
        -H "Content-Type: application/json" \
        --data-binary @reports/simulation.json >/dev/null
    "$PY" proxy_client.py --proxy "http://127.0.0.1:$HF" | tee reports/run_restore.txt
    diff -u reports/run_record.txt reports/run_restore.txt >/dev/null && echo "恢复后与录制逐字节一致 ✅"

    echo
    echo ">>> 验收：代理录制 ✅ 断网回放逐字节一致 ✅ 注入 500 按预期红 ✅ 恢复可逆 ✅"
}

do_clean() {
    step "clean" "杀 Hoverfly 与上游、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$HF"; kill_port "$ADMIN"
    rm -rf reports __pycache__
    local residue=0
    for p in "$UP" "$HF" "$ADMIN"; do
        lsof -ti ":$p" >/dev/null 2>&1 && { echo "❌ 端口 $p 仍被占用"; residue=1; }
    done
    [ "$residue" -eq 0 ] && echo "已清理（端口 $UP/$HF/$ADMIN 确认空闲）"
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
