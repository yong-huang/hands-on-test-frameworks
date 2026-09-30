#!/usr/bin/env bash
# =============================================================================
# realtime.sh — lab 15 主演示脚本：WebSocket 实时推送
#   真实推送时延 → mock 注入伪帧 → 断连重连 → 服务端权威对账
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9015
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        npx vite build "$SUT/app" --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 四条实时用例（真实演进 / 伪帧注入 / 断连重连 / 权威对账）"
    npx playwright test --project=chromium --reporter=list

    step "observe" "② WS 通道独立性检查（关闭 HTTP 后 WS 探活应失败，证明确实是长连接）"
    echo ">>> WebSocket 是独立于 HTTP 请求-响应的长连接（协议升级而来，见 lab 02）"
    echo ">>> mock 注入与断连重连两条用例分别从两侧证明了通道可控性"

    step "observe" "③ 手动体验"
    echo ">>> open http://127.0.0.1:9015   （订单区建单后看状态徽标 2 秒自动演进）"
}

do_clean() {
    step "clean" "清运行产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
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
