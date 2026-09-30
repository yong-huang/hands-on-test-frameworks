#!/usr/bin/env bash
# =============================================================================
# run_suite.sh — lab 19 🏁 终极串联：一条命令跑通全系列回归套件
#   15 个套件按序执行（刻意排除 08/12 的"设计好的红"与 18 的容器依赖），
#   末尾质量门禁：失败数 = 0、flaky ≤ 2、总时长 ≤ 20 分钟，超限返回非零。
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")"

SERIES_ROOT=$(cd .. && pwd)
LOG_DIR="logs"
THRESHOLD_MINUTES=20
ALLOWED_FLAKY=2
START=$(date +%s)
mkdir -p "$LOG_DIR"

step() { echo; echo "=====> [$1] $2"; }

# 套件清单：名称 | 工作目录 | 命令
SUITES=(
    "01 TS 原生栈            | 01_pw_ts_stack      | npx playwright test --project=chromium --project=firefox --project=webkit"
    "02 靶场冒烟             | 02_pw_sut           | npx playwright test --project=chromium"
    "03 定位深水区           | 03_pw_locators_pro  | npx playwright test --project=chromium"
    "04 认证矩阵             | 04_pw_auth          | npx playwright test --project=admin --project=customer"
    "05 网络控制（离线跳过） | 05_pw_network_pro   | npx playwright test tests/network_pro.spec.ts tests/har_record.spec.ts --project=chromium"
    "06 视觉回归             | 06_pw_visual        | npx playwright test --project=chromium"
    "07 组件测试             | 07_pw_component     | npx playwright test -c playwright-ct.config.ts --project=chromium"
    "09 fixture+POM          | 09_pw_fixtures_pom  | npx playwright test --project=chromium"
    "10 并行与隔离           | 10_pw_parallel      | npx playwright test --project=chromium"
    "11 设备与仿真矩阵       | 11_pw_matrix        | npx playwright test"
    "13 flaky 治理           | 13_pw_flaky         | npx playwright test --project=chromium"
    "14 文件上传下载         | 14_pw_files         | npx playwright test --project=chromium"
    "15 WebSocket 实时       | 15_pw_realtime      | npx playwright test --project=chromium"
    "16 i18n 与无障碍        | 16_pw_i18n_a11y     | npx playwright test --project=chromium"
    "17 API+UI 混合          | 17_pw_api_ui        | npx playwright test --project=chromium"
)

declare -a RESULT_ROWS
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_FLAKY=0
SUITE_FAIL=0

run_one() {
    local row="$1"
    local name="${row%% | *}"
    local rest="${row#* | }"
    local dir cmd
    dir=$(echo "${rest%% | *}" | xargs)
    cmd=$(echo "${rest#* | }" | xargs)

    local log="$LOG_DIR/$(echo "$name" | awk '{print $1}').log"
    ( cd "$SERIES_ROOT/$dir" && eval "$cmd" ) > "$log" 2>&1
    local rc=$?

    local passed failed flaky
    passed=$(grep -oE '[0-9]+ passed' "$log" | grep -oE '[0-9]+' | paste -sd+ - | bc 2>/dev/null || echo 0)
    failed=$(grep -oE '[0-9]+ failed' "$log" | grep -oE '[0-9]+' | paste -sd+ - | bc 2>/dev/null || echo 0)
    flaky=$(grep -oE '[0-9]+ flaky' "$log" | grep -oE '[0-9]+' | paste -sd+ - | bc 2>/dev/null || echo 0)
    passed=${passed:-0}; failed=${failed:-0}; flaky=${flaky:-0}

    TOTAL_PASSED=$((TOTAL_PASSED + passed))
    TOTAL_FAILED=$((TOTAL_FAILED + failed))
    TOTAL_FLAKY=$((TOTAL_FLAKY + flaky))
    [ "$rc" -ne 0 ] && SUITE_FAIL=1

    RESULT_ROWS+=("$(printf '%-24s %3s passed %3s failed %3s flaky  %s' "$name" "$passed" "$failed" "$flaky" "$([ $rc -eq 0 ] && echo ✓ || echo ✗)")")
}

main() {
    echo "# 🏁 playwright/ 系列终极串联套件（$(date '+%F %T')）"
    step "run" "按序执行 15 个套件（02-17 的代表面 + 01 三浏览器全矩阵）"
    for row in "${SUITES[@]}"; do run_one "$row"; done

    echo
    step "report" "套件结果总表"
    printf '%s\n' "${RESULT_ROWS[@]}"
    echo "--------------------------------------------------------------"
    echo "合计: ${TOTAL_PASSED} passed, ${TOTAL_FAILED} failed, ${TOTAL_FLAKY} flaky"

    END=$(date +%s)
    MINUTES=$(( (END - START) / 60 ))
    echo "总时长: $((END - START)) s（约 ${MINUTES} 分钟，阈值 ${THRESHOLD_MINUTES} 分钟）"

    step "gate" "质量门禁"
    local gate=0
    if [ "$SUITE_FAIL" -ne 0 ] || [ "$TOTAL_FAILED" -ne 0 ]; then
        echo "❌ 存在失败用例（failed=${TOTAL_FAILED}）"; gate=1
    fi
    if [ "$TOTAL_FLAKY" -gt "$ALLOWED_FLAKY" ]; then
        echo "❌ flaky 超阈值（${TOTAL_FLAKY} > ${ALLOWED_FLAKY}）"; gate=1
    fi
    if [ "$MINUTES" -gt "$THRESHOLD_MINUTES" ]; then
        echo "❌ 超时（${MINUTES} 分钟 > ${THRESHOLD_MINUTES}）"; gate=1
    fi
    if [ "$gate" -eq 0 ]; then
        echo "✅ 门禁通过：0 failed、flaky ${TOTAL_FLAKY}/${ALLOWED_FLAKY}、时长达标 —— 全系列回归 GREEN 🏁"
    else
        echo "（日志见 $LOG_DIR/）" >&2
    fi
    exit $gate
}

main "$@"
