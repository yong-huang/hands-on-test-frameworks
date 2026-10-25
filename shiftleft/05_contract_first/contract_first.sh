#!/usr/bin/env bash
# =============================================================================
# contract_first.sh — shiftleft 05 主演示脚本：依赖自检 → 好实现全绿 → 坏实现报红
#                     → 契约领先实现报红 → 清理
# 契约在 contract.yaml（source of truth），测试入口 test_contract.py，
# 被测实现由 APP_IMPL 切换（good/bad），本脚本负责串出演示动线。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（schemathesis ≥4 + fastapi + uvicorn + pyyaml，幂等）"
    "$PY" -c "import schemathesis, fastapi, uvicorn, yaml" 2>/dev/null \
        && echo "依赖就绪（schemathesis $("$PY" -c 'import schemathesis; print(schemathesis.__version__)')）" \
        || "$PY" -m pip install -q schemathesis fastapi uvicorn pyyaml
}

do_observe() {
    step "observe" "① 忠实实现 × 契约：property-based 生成案例全绿（看规模统计）"
    "$PY" -m pytest test_contract.py -q 2>&1 | tail -4

    step "observe" "② 篡改实现（响应缺 price + 未声明的 400）→ 报红并给出违反点与 curl 复现"
    APP_IMPL=bad "$PY" -m pytest test_contract.py -q 2>&1 | \
        grep -E "ST10[38]|curl -X|failed, " | head -8 || true

    step "observe" "③ 契约领先实现（v2 新增必填 createdAt，实现未跟进）→ 报红指认漂移点"
    APP_IMPL=good CONTRACT=contract_v2.yaml "$PY" -m pytest test_contract.py -q 2>&1 | \
        grep -E "ST108|required property|failed, " | head -6 || true

    step "observe" "④ 演示动线跑完，契约与实现恢复一致（再跑一次确认全绿）"
    "$PY" -m pytest test_contract.py -q 2>&1 | tail -1
    echo ">>> 契约文件进 git：改实现不改契约（②）或改契约不改实现（③）都会红，这就是防漂移"
}

do_clean() {  # 摘端口 + 删缓存；本实验产物只有 pytest 缓存
    step "clean" "摘掉 8933 端口残留，删缓存——目录回到实验前状态"
    lsof -ti :8933 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .pytest_cache __pycache__ reports 2>/dev/null || true
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
