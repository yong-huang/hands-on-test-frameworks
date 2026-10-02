#!/usr/bin/env bash
# =============================================================================
# gherkin_basics.sh — lab 01 主演示脚本：Gherkin 最小闭环
#   apply 起靶场 → observe 三场景 + 关键字写错演示 → clean 清场
# 与 @playwright/test 的区别：cucumber 没有 webServer 概念，
# SUT 的启停与探活由本脚本负责（这也是 BDD 工具链的第一课）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"          # 任意 cwd 运行都正确

PORT=9101
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + 靶场构建产物）"
    [ -d ../node_modules/@cucumber/cucumber ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT" ] && [ ! -f "../../playwright/02_pw_sut/app/dist/index.html" ]; then
        echo "pw-store 未构建：bash ../load_resources.sh 会自动补" >&2; exit 1
    fi
    [ -f "../../playwright/02_pw_sut/app/dist/index.html" ] || {
        echo "pw-store 未构建，先构建"; (cd ../.. && npx vite build playwright/02_pw_sut/app --logLevel warn); }
    npx cucumber-js --version | head -1

    step "apply" "启动 pw-store（端口 ${PORT}，脚本托管——cucumber 无 webServer 概念）"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    PORT=${PORT} nohup node "$SUT" </dev/null > .sut.log 2>&1 &
    echo $! > "$PIDFILE"; disown
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; tail -5 .sut.log >&2; exit 1
}

do_observe() {
    step "observe" "① 中文 Gherkin 三场景（真 Chromium，locale 钉 zh-CN）"
    npx cucumber-js

    step "observe" "② 关键字写错演示：Givens 被当成描述文本——步骤静默消失（BDD 的静默失效危险）"
    cat > features/broken_demo.feature <<'EOF'
# language: zh-CN
功能: 关键字写错演示
  场景: 步骤关键字拼错
    Givens 打开 pw-store 首页
EOF
    OUT=$(npx cucumber-js 2>&1 || true)
    echo "$OUT" | grep -E 'scenarios|steps' | head -2
    echo ">>> 退出码 0、场景 3→4；steps 14→16 多出的 2 个只是该空场景的 Before/After"
    echo ">>> 钩子计数——真实步骤一个没加。拼错的行被 Gherkin 当成场景描述文本"
    echo ">>> 静默消失，空场景照常通过：这就是 BDD 套件最大的隐性风险。"
    echo ">>> 对策：review .feature 时盯紧步骤数；unmatched 提示只在措辞近似时出现。"
    rm -f features/broken_demo.feature
    npx cucumber-js --format summary >/dev/null 2>&1 && echo ">>> 恢复后复跑：3 scenarios / 14 steps ✓"

    step "observe" "③ 手动体验"
    echo ">>> npx cucumber-js --format progress   （逐字符进度视图）"
    echo ">>> 修改 features/login.feature 里的措辞，观察 unmatched step 提示"
}

do_clean() {
    step "clean" "停靶场、清运行产物，仓库回到实验前状态"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .sut.log .reports
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
