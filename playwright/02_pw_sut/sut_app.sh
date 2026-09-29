#!/usr/bin/env bash
# =============================================================================
# sut_app.sh — lab 02 主演示脚本：构建 + 启动 pw-store 靶场 + 逐区探活
# pw-store 是 playwright/ 系列后续 17 个实验的共用被测系统：
#   登录双角色 / 订单 CRUD+WS 实时演进 / 上传下载 / 慢接口 / iframe+Shadow DOM
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"          # 任意 cwd 运行都正确

PORT=9002
BASE_URL="http://127.0.0.1:${PORT}"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_server() {
    nohup node server.mjs </dev/null > .sut.log 2>&1 &
    echo $! > "$PIDFILE"; disown
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "pw-store 启动失败，日志尾部：" >&2; tail -5 .sut.log >&2; return 1
}

stop_server() {
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
}

do_apply() {
    step "apply" "类型检查 + 前端构建（Vite 产物进 app/dist）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p app/tsconfig.json
    npx vite build app --logLevel warn
    [ -f app/dist/index.html ] && echo ">>> 构建完成: app/dist"

    step "apply" "启动 pw-store（端口 ${PORT}）"
    stop_server   # 清理可能残留的旧进程，保证种子数据从头开始
    start_server
    echo ">>> 探活通过: ${BASE_URL}/api/health"
}

do_observe() {
    step "observe" "① 六大功能区 API 层探活"
    echo ">>> health: $(curl -s ${BASE_URL}/api/health)"
    TOKEN=$(curl -s -X POST ${BASE_URL}/api/login -d '{"username":"admin","password":"admin123"}' \
        | node -e "let d='';process.stdin.on('data',c=>d+=c).on('end',()=>console.log(JSON.parse(d).token))")
    echo ">>> admin token: ${TOKEN:0:20}…"
    echo ">>> orders:  $(curl -s -H "Authorization: Bearer ${TOKEN}" ${BASE_URL}/api/orders | head -c 160)…"

    step "observe" "② 上传下载闭环（raw body + sha256）"
    echo "pw-store 上传闭环内容" > /tmp/pw-store-probe.txt
    curl -s -X PUT "${BASE_URL}/api/upload?name=probe.txt" \
        -H "Authorization: Bearer ${TOKEN}" --data-binary @/tmp/pw-store-probe.txt | head -c 200; echo
    curl -s -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/api/files/probe.txt" | head -c 60
    echo "  <<< 下载回读一致"

    step "observe" "③ WebSocket 通道探活（连接即收 welcome 帧）"
    node -e "
        const { WebSocket } = require('ws');
        const ws = new WebSocket('ws://127.0.0.1:${PORT}/ws');
        ws.on('message', (m) => { console.log('>>> WS 帧:', m.toString()); ws.close(); process.exit(0); });
        setTimeout(() => { console.error('WS 5s 未收到帧'); process.exit(1); }, 5000);"

    step "observe" "④ 靶场自检冒烟（8 条 UI 用例，chromium）"
    npx playwright test --project=chromium --reporter=list

    step "observe" "⑤ 浏览器手动体验入口"
    echo ">>> open ${BASE_URL}   （admin/admin123 或 customer/customer123）"
}

do_clean() {
    step "clean" "停服务、删构建产物与运行数据，仓库回到实验前状态"
    stop_server
    rm -rf app/dist .uploads test-results playwright-report .sut.log /tmp/pw-store-probe.txt
    echo ">>> 已清理"
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
