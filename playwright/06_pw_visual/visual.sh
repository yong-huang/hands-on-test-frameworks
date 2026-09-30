#!/usr/bin/env bash
# =============================================================================
# visual.sh — lab 06 主演示脚本：视觉回归完整生命周期
#   基线生成 → 比对全绿 → 注入 1px 变异看红 → 还原转绿（变异是设计好的教学点）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9006
SUT="../02_pw_sut"
DIST="$SUT/app/dist/index.html"
PW="npx playwright"
SNAP_DIR="tests/visual.spec.ts-snapshots"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$DIST" ]; then
        step "apply" "pw-store 未构建，执行 vite build"
        npx vite build "$SUT/app" --logLevel warn
    fi
    $PW --version
}

do_observe() {
    step "observe" "① 基线准备（无基线则 --update-snapshots 生成，png 应入库）"
    if ! ls "$SNAP_DIR"/*.png >/dev/null 2>&1; then
        $PW test --project=chromium --update-snapshots --reporter=line
        echo ">>> 基线已生成："
        ls -la "$SNAP_DIR"
        echo ">>> git 状态（基线 png 应作为入库文件出现）："
        git status --short "$SNAP_DIR" 2>/dev/null | head -6 || true
    else
        echo ">>> 基线已存在（$(ls "$SNAP_DIR" | grep -c png) 张），跳过生成"
    fi

    step "observe" "② 基线比对：4 条截图断言全绿"
    $PW test --project=chromium --reporter=line

    step "observe" "③ 变异演示：注入一条改背景色的 CSS → 预期变红"
    # 变异选"大面积换色"是有意的：视觉断言有两层感知阈值（像素颜色距离 + 差异占比），
    # 2px 位移这类小改动在稀疏页面上差异占比不足 2%，测不出来——这正是阈值的语义
    cp "$DIST" "$DIST.bak"
    sed -i '' 's|</head>|<style>body { background: #607d8b; }</style></head>|' "$DIST"
    if [ "$(grep -c '607d8b' "$DIST")" != "1" ]; then
        echo "注入失败，中止" >&2; mv "$DIST.bak" "$DIST" 2>/dev/null; exit 1
    fi
    if $PW test --project=chromium --reporter=line >/tmp/visual-mutation.log 2>&1; then
        echo ">>> 变异未被抓住——视觉回归失效！" >&2; mv "$DIST.bak" "$DIST"; exit 1
    else
        echo ">>> 变异被抓住（预期红）："
        grep -E '✘|failed' /tmp/visual-mutation.log | head -4 || true
        echo ">>> diff/actual/expected 三联图见 test-results/*-diff.png"
    fi
    mv "$DIST.bak" "$DIST"
    [ "$(grep -c '607d8b' "$DIST")" = "0" ] || { echo "还原失败" >&2; exit 1; }

    step "observe" "④ 还原后复跑：回到全绿（基线未变，变的是世界）"
    $PW test --project=chromium --reporter=line

    echo ">>> 手动体验：改完样式确认无误后，npx playwright test --update-snapshots 刷新基线并随代码一起提交"
}

do_clean() {
    step "clean" "清比对产物（基线保留！），杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report /tmp/visual-mutation.log
    echo ">>> 已清理。$SNAP_DIR 基线是入库资产，clean 不碰它"
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
