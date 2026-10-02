#!/usr/bin/env bash
# =============================================================================
# outline_examples.sh — lab 04 主演示脚本：Scenario Outline 与 Examples
#   apply 起靶场 → observe 登录矩阵（4 组 Examples）+ 失败定位演示 → clean
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9104
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 就绪）"
    npx tsc -p tsconfig.json
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    PORT=${PORT} nohup node "$SUT" </dev/null > .sut.log 2>&1 &
    echo $! > "$PIDFILE"; disown
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; exit 1
}

do_observe() {
    step "observe" "① 登录矩阵：1 个场景大纲 × 4 组例子 = 4 次执行"
    npx cucumber-js

    step "observe" "② 失败定位演示：把第 3 组密码改错位重跑，看报告定位到哪组"
    python3 - <<'PYEOF'
t = open('features/login_matrix.feature').read()
t = t.replace('| admin    | wrong-pass    |', '| admin    | wrong-pass-x  |')
open('features/login_matrix.feature', 'w').write(t)
PYEOF
    if npx cucumber-js --format summary >/tmp/outline-fail.log 2>&1; then
        echo ">>> 变异未被抓住" >&2
    else
        grep -E '失败|Scenario|✗|failed' /tmp/outline-fail.log | head -4
        echo ">>> 报告将失败定位到「以 admin/wrong-pass-x 登录应 失败」这一组例子 ✓"
    fi
    python3 - <<'PYEOF'
t = open('features/login_matrix.feature').read()
t = t.replace('| admin    | wrong-pass-x  |', '| admin    | wrong-pass    |')
open('features/login_matrix.feature', 'w').write(t)
PYEOF
    npx cucumber-js --format summary >/dev/null 2>&1 && echo ">>> 恢复后复跑：4 组全绿 ✓"

    step "observe" "③ 方言教学点"
    echo ">>> zh-CN 方言下：场景大纲（非 场景模板）、例子（非 Examples）——"
    echo ">>> 关键字以 gherkin-languages.json 为准，勿凭印象翻译"
}

do_clean() {
    step "clean" "停靶场、清运行产物"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .sut.log
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
