#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_LAB="../01_ios_session"
WEB_PORT=8923
WEB_ROOT="$PWD/configs"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "复用 01 的 Appium / 模拟器 / App 环境"
    (cd "$ENV_LAB" && ./ios_session.sh apply)
    step "apply" "启动本地 WebView 测试页（http://127.0.0.1:${WEB_PORT}/）"
    # http.server 的 / 只认 index.html；仓库仅跟踪 webview-page.html，apply 时生成入口副本
    cp -f "$WEB_ROOT/webview-page.html" "$WEB_ROOT/index.html"
    lsof -ti ":${WEB_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    nohup python3 -m http.server "$WEB_PORT" --directory "$WEB_ROOT" \
        </dev/null > /dev/null 2>&1 &
    disown $! 2>/dev/null || true
    for i in $(seq 1 20); do
        curl -sf "http://127.0.0.1:${WEB_PORT}/" >/dev/null 2>&1 && break
        sleep 0.25
    done
    curl -sf "http://127.0.0.1:${WEB_PORT}/" >/dev/null \
        && echo "  本地页就绪：WebView Demo" \
        || { echo "  本地页启动失败" >&2; exit 1; }
    step "apply" "环境就绪，可以直接 observe"
}

do_observe() {
    step "observe" "WebView 混合应用（3 条用例）"
    mvn -q -Dtest=WebViewTest test
}

do_clean() {
    step "clean" "停本地页、删除构建产物，并复用 01 的清理"
    lsof -ti ":${WEB_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f "$WEB_ROOT/index.html"
    rm -rf target test-results
    (cd "$ENV_LAB" && ./ios_session.sh clean) || true
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
