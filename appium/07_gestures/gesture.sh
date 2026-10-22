#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_LAB="../01_ios_session"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "复用 01 的 Appium / 模拟器 / App 环境"
    (cd "$ENV_LAB" && ./ios_session.sh apply)
    step "apply" "预授权照片权限（Drawing 画布 Save 需要，弹窗会吞掉后续点击）"
    if [ -n "${DEVELOPER_DIR:-}" ] || [ -x "/Applications/Xcode.app/Contents/Developer/usr/bin/xcrun" ]; then
        export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
        UDID="$(xcrun simctl list devices booted | grep 'iPhone 17' | grep -o '[0-9A-F-]\{36\}' | head -1)"
        if [ -n "${UDID:-}" ]; then
            xcrun simctl privacy "$UDID" grant photos com.saucelabs.mydemo.app.ios || true
            echo "  已 grant photos（UDID=$UDID）"
        else
            echo "  未找到已启动的模拟器，跳过授权（observe 时首次 Save 会弹系统权限）"
        fi
    fi
    step "apply" "环境就绪，可以直接 observe"
}

do_observe() {
    step "observe" "手势与滚动（4 条用例）"
    mvn -q -Dtest=GestureTest test
}

do_clean() {
    step "clean" "删除构建产物，并复用 01 的清理"
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
