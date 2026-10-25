#!/usr/bin/env bash
# =============================================================================
# ios_session.sh — 01 主演示脚本：环境准备 → 首会话 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

ENV_DIR="../00_env"
APPIUM_BIN="$ENV_DIR/node_modules/.bin/appium"
APPIUM_PORT="${APPIUM_PORT:-4723}"
APPIUM_BASE_PATH="${APPIUM_BASE_PATH:-/wd/hub}"
APPIUM_URL="http://127.0.0.1:${APPIUM_PORT}${APPIUM_BASE_PATH}"

SIM_NAME="${SIM_NAME:-iPhone 17}"
DEVICE_NAME="${DEVICE_NAME:-$SIM_NAME}"
PLATFORM_VERSION="${PLATFORM_VERSION:-26.5}"
BUNDLE_ID="${BUNDLE_ID:-com.saucelabs.mydemo.app.ios}"

APP_VERSION="2.3.0"
APP_URL="https://github.com/saucelabs/my-demo-app-ios/releases/download/${APP_VERSION}/SauceLabs-Demo-App.Simulator.zip"
CACHE="$PWD/.cache"
APP_ZIP="$CACHE/SauceLabs-Demo-App-${APP_VERSION}.zip"
APP_BUNDLE="$CACHE/Payload/My Demo App.app"

PIDFILE="$PWD/.appium.pid"
LOG="$PWD/.appium.log"
SIM_MARKER="$PWD/.sim_booted_by_us"

step() { echo; echo "=====> [$1] $2"; }

ensure_xcode() {
    if [ ! -d /Applications/Xcode.app/Contents/Developer ]; then
        echo "未找到完整 Xcode：/Applications/Xcode.app" >&2
        exit 1
    fi
    export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
    xcrun simctl list devices >/dev/null
}

ensure_appium() {
    command -v mvn >/dev/null 2>&1 || { echo "需要 Maven（brew install maven）" >&2; exit 1; }
    if [ ! -x "$APPIUM_BIN" ]; then
        step "setup" "首次运行：安装 Appium 3.8 + XCUITest driver（约 1 分钟）"
        bash "$ENV_DIR/setup.sh"
    fi
    if ! "$APPIUM_BIN" driver list --installed 2>&1 | grep -c xcuitest >/dev/null; then
        step "setup" "补装 XCUITest driver"
        "$APPIUM_BIN" driver install xcuitest
    fi
}

is_appium_up() {
    curl -sf -m 2 "$APPIUM_URL/status" >/dev/null 2>&1
}

start_appium() {
    if is_appium_up; then
        echo "  Appium 已在运行：$APPIUM_URL"
        return 0
    fi
    step "apply" "启动 Appium server（端口 ${APPIUM_PORT}）"
    # 脱管包装壳：appium 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env APPIUM_BIN="$APPIUM_BIN" APPIUM_PORT="$APPIUM_PORT" APPIUM_BASE_PATH="$APPIUM_BASE_PATH" \
        LOG="$LOG" PIDFILE="$PIDFILE" \
        bash -c 'trap "" TERM INT; "$APPIUM_BIN" server --port "$APPIUM_PORT" --base-path "$APPIUM_BASE_PATH" > "$LOG" 2>&1 & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null &
    for _ in $(seq 1 40); do
        if is_appium_up; then
            echo "  Appium 就绪：$APPIUM_URL"
            return 0
        fi
        sleep 0.5
    done
    echo "Appium 启动失败，日志尾部：" >&2
    tail -20 "$LOG" >&2
    return 1
}

stop_appium() {
    if [ -f "$PIDFILE" ]; then
        kill "$(cat "$PIDFILE")" 2>/dev/null || true
        rm -f "$PIDFILE"
        echo "  Appium 已停止"
    fi
}

ensure_simulator() {
    step "apply" "准备 iOS Simulator：${SIM_NAME}"
    local booted
    booted="$(xcrun simctl list devices booted)"
    if grep -qF "${SIM_NAME} (" <<< "$booted"; then
        echo "  模拟器已在运行"
    else
        xcrun simctl boot "$SIM_NAME" >/dev/null 2>&1 || true
        touch "$SIM_MARKER"
    fi
    xcrun simctl bootstatus "$SIM_NAME" -b >/dev/null
    echo "  模拟器就绪"
}

ensure_app() {
    # 每次强制重装：App 容器/Keychain 的陈旧状态 clearApp 清不掉，多轮 noReset 会话
    # 累积后会卡死生物识别等依赖持久状态的流程（2026-10-25 全量回归实测：重装即愈）
    if xcrun simctl get_app_container "$SIM_NAME" "$BUNDLE_ID" app >/dev/null 2>&1; then
        xcrun simctl uninstall "$SIM_NAME" "$BUNDLE_ID" >/dev/null 2>&1 || true
    fi
    step "apply" "安装被测 App：SauceLabs My Demo App ${APP_VERSION}"
    mkdir -p "$CACHE"
    if [ ! -f "$APP_ZIP" ]; then
        echo "  下载 $(basename "$APP_ZIP")（约 6 MB）"
        curl -fL --retry 3 --retry-delay 2 -o "$APP_ZIP" "$APP_URL"
    fi
    if [ ! -d "$APP_BUNDLE" ]; then
        (cd "$CACHE" && unzip -q -o "$APP_ZIP")
    fi
    xcrun simctl install "$SIM_NAME" "$APP_BUNDLE"
    echo "  App 安装完成"
}

do_apply() {
    ensure_xcode
    ensure_appium
    ensure_simulator
    ensure_app
    start_appium
    step "apply" "环境就绪"
    echo "  Appium: $APPIUM_URL"
    echo "  设备:   $SIM_NAME / iOS $PLATFORM_VERSION"
    echo "  App:    $BUNDLE_ID"
}

do_observe() {
    step "observe" "运行 FirstSessionTest：建立会话 → 启动 App → 断言 Catalog tab"
    mvn -q test \
        -Dappium.url="$APPIUM_URL" \
        -Ddevice.name="$DEVICE_NAME" \
        -Dplatform.version="$PLATFORM_VERSION" \
        -Dbundle.id="$BUNDLE_ID"
}

do_clean() {
    step "clean" "停止 Appium、删除构建产物"
    stop_appium
    rm -rf target
    rm -f "$LOG"
    if [ -f "$SIM_MARKER" ]; then
        xcrun simctl shutdown "$SIM_NAME" >/dev/null 2>&1 || true
        rm -f "$SIM_MARKER"
        echo "  已关闭本次启动的模拟器"
    fi
    echo "  清理完成（App 与下载缓存保留，供下次秒开）"
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
