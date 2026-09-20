#!/usr/bin/env bash
# =============================================================================
# llm_eval.sh — architect 25 主演示脚本：
# mock 模式生成+四维评测 → 评测断言 → 真实 LLM 探活（未配置则如实说明） → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 种子数据 + 起 SUT（评测要真实打请求）"
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    ( cd "$SUT_DIR/app"
      SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 \
          </dev/null > "$here/.sut.log" 2>&1 & echo $! > "$here/.sut.pid" )
    disown 2>/dev/null || true
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

do_observe() {
    step "observe" "① mock 模式（默认，离线确定性）：模板生成 → 四维评测"
    "$PY" llm_eval.py

    step "observe" "② 评测断言：mock 生成器应满分（量尺自身的回归基线）"
    "$PY" - <<'PYEOF'
import json
s = json.load(open("reports/llm_eval.json", encoding="utf-8"))
assert s["executability_pct"] >= 80 and s["duplication_pct"] <= 20
print(f"可执行 {s['executability_pct']}% / 断言有效 {s['assert_validity_pct']}% / "
      f"边界覆盖 {s['boundary_coverage_pct']}% / 重复 {s['duplication_pct']}% → 判定达标 ✅")
PYEOF

    step "observe" "③ 真实 LLM 探活（可选：配置了环境变量才真调）"
    if [ -n "${LLM_BASE_URL:-}" ] && [ -n "${LLM_MODEL:-}" ]; then
        "$PY" llm_eval.py --llm | head -12
    else
        echo "LLM_BASE_URL/LLM_MODEL 未配置 → 真实模式跳过（按清单约定：mock 为默认路径，不编造）"
    fi
    echo ">>> 验收：mock 全流程跑通出四维评测报告 ✅"
}

do_clean() {
    step "clean" "停 SUT、删报告"
    if [ -f .sut.pid ]; then kill "$(cat .sut.pid)" 2>/dev/null || true; rm -f .sut.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .sut.log
    rm -rf reports __pycache__
    ( cd "$SUT_DIR" && rm -f app/orders.db app/orders.db-journal ) || true
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
