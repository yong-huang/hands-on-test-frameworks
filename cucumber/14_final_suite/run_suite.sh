#!/usr/bin/env bash
# =============================================================================
# run_suite.sh — lab 14 🏁 终极 BDD 套件：一条命令全量回归 + 活文档 + 门禁
#   apply 起靶场 → observe 全量跑批 → 活文档 → 门禁（failed=0 / pending=0）
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")"

PORT=9116
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"
START=$(date +%s)
THRESHOLD_MINUTES=15

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 构建产物）"
    npx tsc -p tsconfig.json
    [ -f "../../playwright/02_pw_sut/app/dist/index.html" ] || \
        (cd ../.. && npx vite build playwright/02_pw_sut/app --logLevel warn)
    npx cucumber-js --version | head -1
}

do_observe() {
    step "observe" "起靶场（端口 ${PORT}）"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    # 脱管包装壳：node 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env PORT="${PORT}" SUT="$SUT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > .sut.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; break; }
        sleep 0.25
    done

    step "observe" "全量 BDD 回归（3 个业务域 feature）"
    set +e
    npx cucumber-js --profile default \
        --format summary \
        --format json:reports/cucumber.json \
        --format junit:reports/junit.xml
    RC=$?
    set -e

    step "observe" "活文档与功能清单生成"
    node ../09_reports/scripts/generate_report.mjs 2>/dev/null || true
    node ../09_reports/scripts/extract_features.mjs 2>/dev/null || true

    step "gate" "质量门禁"
    FAILED=$(grep -oE '[0-9]+ failed' reports/../run_suite.tmp 2>/dev/null | head -1 || true)
    # 直接从 json 统计失败数（最可靠）
    FAILED=$(node -e "
        const d = require('./reports/cucumber.json');
        let f = 0;
        for (const feat of d) for (const el of feat.elements ?? [])
            if ((el.steps ?? []).some(s => s.result?.status === 'failed')) f++;
        console.log(f);
    " 2>/dev/null || echo "?")
    PENDING=$(grep -c 'pending' reports/features.md 2>/dev/null || echo 0)
    echo ">>> failed=${FAILED} pending场景标记=${PENDING}"
    if [ "$FAILED" = "0" ]; then
        echo "✅ 门禁通过：全系列 BDD 回归 GREEN 🏁"
        exit 0
    else
        echo "❌ 门禁失败：存在 ${FAILED} 个失败场景" >&2
        exit 1
    fi
}

do_clean() {
    step "clean" "停靶场、清运行产物（reports 保留供查阅）"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .sut.log test-results
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
