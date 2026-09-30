#!/usr/bin/env bash
# =============================================================================
# reports.sh — lab 12 主演示脚本：报告与产物体系
#   跑套件（含 1 条人为失败）→ 验 HTML/JUnit/trace/截图/视频 五类产物在位
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9012
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
    step "observe" "① 跑套件：2 绿 + 1 红（人为失败标本，预期容忍）"
    npx playwright test --project=chromium || true

    step "observe" "② JUnit 报告合法性：xmllint --noout 校验"
    [ -f report.xml ] || { echo "report.xml 缺失" >&2; exit 1; }
    xmllint --noout report.xml && echo ">>> report.xml 结构合法 ✓"
    echo ">>> JUnit 内容抽样："
    grep -o 'tests="[0-9]*"\|failures="[0-9]*"\|<failure' report.xml | sort | uniq -c | head -4

    step "observe" "③ 失败用例的三产物齐备性（trace / 截图 / 视频）"
    DIR=$(find test-results -maxdepth 1 -type d -name '*人为失败*' | head -1)
    [ -n "$DIR" ] || { echo "未找到失败用例产物目录" >&2; exit 1; }
    echo ">>> 产物目录: $DIR"
    find "$DIR" -name 'trace.zip'  | head -1 | xargs -I{} echo ">>> trace   ✓ {}"
    find "$DIR" -name '*.png'      | head -1 | xargs -I{} echo ">>> 截图    ✓ {}"
    find "$DIR" -name '*.webm'     | head -1 | xargs -I{} echo ">>> 视频    ✓ {}"

    step "observe" "④ HTML 报告在位（GUI，请手动打开）"
    [ -f playwright-report/index.html ] && echo ">>> npx playwright show-report  （失败条目下可直接回放 trace/视频）"
}

do_clean() {
    step "clean" "清全部报告产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report report.xml
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
