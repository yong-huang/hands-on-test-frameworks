#!/usr/bin/env bash
# =============================================================================
# files.sh — lab 14 主演示脚本：文件上传下载
#   ① 四条用例（多文件/sha256 完整性/拖拽/大文件）  ② 服务端落盘核对
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9014
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
    step "observe" "① 四条文件用例（多文件 / 下载 sha256 / 拖拽 / 5MB）"
    npx playwright test --project=chromium --reporter=list

    step "observe" "② 服务端落盘核对（.uploads/ 里应有本轮上传的实物）"
    ls -la "$SUT/.uploads" 2>/dev/null | grep 'lab14' | head -5 \
        && echo ">>> 上传实物在服务端落盘 ✓" || echo ">>> （clean 已清空属正常）"

    step "observe" "③ 手动体验"
    echo ">>> open http://127.0.0.1:9014   （上传页拖文件进去试试）"
}

do_clean() {
    step "clean" "清运行产物与服务端上传目录，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
    rm -rf "$SUT/.uploads"
    echo ">>> 已清理（.uploads 是运行数据）"
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
