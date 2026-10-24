#!/usr/bin/env bash
# 🏁 终极回归流水线：双模拟器并行跑 smoke + regression，支持 N 连跑与汇总
set -uo pipefail
cd "$(dirname "$0")"

RUNS="${1:-1}"
ENV_LAB="../01_ios_session"
UDID1="137A9ECA-508D-4B98-BCE1-18B96C09EE0D"
UDID2="5DBEB73E-2CD2-4F57-9A9D-6BD5718E146F"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"

step() { echo; echo "=====> [$1] $2"; }

setup() {
    step "setup" "启动双模拟器"
    xcrun simctl boot "$UDID1" 2>/dev/null || true
    xcrun simctl boot "$UDID2" 2>/dev/null || true
    xcrun simctl bootstatus "$UDID1" -b >/dev/null 2>&1
    xcrun simctl bootstatus "$UDID2" -b >/dev/null 2>&1
    step "setup" "两台模拟器上安装/更新被测 App"
    APP="/tmp/Payload/My Demo App.app"
    [ -d "$APP" ] || { unzip -q -o /tmp/SauceLabs-Demo-App.Simulator.zip -d /tmp; }
    xcrun simctl install "$UDID1" "$APP"
    xcrun simctl install "$UDID2" "$APP"
    xcrun simctl launch "$UDID1" com.saucelabs.mydemo.app.ios >/dev/null 2>&1 || true
    xcrun simctl terminate "$UDID1" com.saucelabs.mydemo.app.ios 2>/dev/null || true
    xcrun simctl launch "$UDID2" com.saucelabs.mydemo.app.ios >/dev/null 2>&1 || true
    xcrun simctl terminate "$UDID2" com.saucelabs.mydemo.app.ios 2>/dev/null || true
    step "setup" "起本地 WebView 页（8923）"
    mkdir -p configs/webroot
    cat > configs/webroot/index.html <<'HTML'
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>WebView Demo</title></head>
<body><h1 id="hello">Hello WebView</h1><p id="info">这是本地测试页</p></body></html>
HTML
    lsof -ti :8923 2>/dev/null | xargs kill 2>/dev/null || true
    nohup python3 -m http.server 8923 --directory "$PWD/configs/webroot" \
        </dev/null >/dev/null 2>&1 &
    disown $! 2>/dev/null || true
    curl -sf http://127.0.0.1:8923/ >/dev/null && echo "  本地页就绪"
}

run_once() {
    local i="$1"
    step "run $i/$RUNS" "双模拟器并行：smoke（iPhone 17）+ regression（iPhone 17 · 2）"
    rm -rf target/surefire-reports
    mvn -q test -DsuiteXmlFile=configs/final-suite.xml > "target/run-$i.log" 2>&1
    local rc=$?
    local total passed failed
    total=$(grep -hoE "Tests run: [0-9]+" target/surefire-reports/*.txt 2>/dev/null |
            grep -oE "[0-9]+" | paste -sd+ - | bc)
    failed=$(grep -hoE "Failures: [0-9]+" target/surefire-reports/*.txt 2>/dev/null |
            grep -oE "[0-9]+" | paste -sd+ - | bc)
    passed=$((total - failed))
    mkdir -p "target/archive/run-$i"
    cp -r target/surefire-reports "target/archive/run-$i/" 2>/dev/null || true
    echo "  ── 第 ${i} 轮：总用例 ${total}，通过 ${passed}，失败 ${failed}（含重试前失败）"
    return $rc
}

aggregate() {
    echo
    step "summary" "$RUNS 轮总汇"
    local grand_total=0 grand_failed=0
    for d in $(find target/archive -name "*.txt" | xargs dirname | sort -u); do
        local t f
        t=$(grep -hoE "Tests run: [0-9]+" "$d"/*.txt 2>/dev/null | grep -oE "[0-9]+" | paste -sd+ - | bc)
        f=$(grep -hoE "Failures: [0-9]+" "$d"/*.txt 2>/dev/null | grep -oE "[0-9]+" | paste -sd+ - | bc)
        t=${t:-0}; f=${f:-0}
        grand_total=$((grand_total + t))
        grand_failed=$((grand_failed + f))
    done
    local grand_passed=$((grand_total - grand_failed))
    echo "  总用例数：${grand_total}"
    echo "  通过：${grand_passed}"
    echo "  失败：${grand_failed}"
    local flaky
    flaky=$(grep -ah "flaky：" target/run-*.log 2>/dev/null | wc -l)
    echo "  flaky（重试后通过）：${flaky}"
    if [ "$grand_failed" -eq 0 ]; then
        echo "  🏁 ${RUNS} 轮连续全绿"
    else
        echo "  ⚠️ 存在失败轮，详见 target/archive/"
    fi
}

main() {
    setup
    mkdir -p target/archive
    local final_rc=0
    for i in $(seq 1 "$RUNS"); do
        run_once "$i" || final_rc=1
    done
    aggregate
    exit $final_rc
}
main
