#!/usr/bin/env bash
# =============================================================================
# flaky_platform.sh — architect 13 主演示脚本：
# 植入 2 个 flaky → 10 轮检测全检出 → 自动 quarantine → 门禁联动（主干 PASS）
# → 连续 3 次主干 PASS → 摘牌恢复监视 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 清空隔离区与历史报告（植入的 flaky 用例常驻 tests/，注释即声明）"
    rm -f reports/quarantine.yaml reports/flaky.json
    # 顺序依赖靶子靠 .shared_state 残留制造「首轮绿、后续红」；上次中止留下的残留会让 10 轮全红而漏检
    rm -f tests/.shared_state
    mkdir -p reports
    echo "植入清单：test_random_flake（随机失败）+ test_order_dependent_victim（顺序依赖）"
}

do_observe() {
    step "observe" "① 10 轮重跑检测：结果不一致的用例 = flaky"
    "$PY" flaky_platform.py detect --rounds 10

    step "observe" "② 检测验收断言：2 个植入 flaky 全部检出，稳定对照零误报"
    "$PY" - <<'PYEOF'
import json
s = json.load(open("reports/flaky.json", encoding="utf-8"))
detected = set(s["detected"])
assert any("random_flake" in k for k in detected), "随机 flaky 未检出"
assert any("order_dependent_victim" in k for k in detected), "顺序依赖 flaky 未检出"
stable = {k for k in s["stable"]}
assert len(stable) == 3, f"稳定对照被误伤: {stable}"
print(f"检出 {len(detected)}/{s['rounds']} 轮内全部植入 flaky ✅；3 条稳定对照零误报 ✅；flaky 率 {s['flaky_rate_pct']}%")
PYEOF

    step "observe" "③ 门禁联动：quarantined 失败不挡主干（但亮灯）"
    "$PY" flaky_platform.py gate | head -8

    step "observe" "④ 主干连续 3 次全绿（隔离生效后 CI 不再被 flaky 劫持）"
    for i in 1 2 3; do
        "$PY" flaky_platform.py gate >/dev/null 2>&1 && echo "主干第 ${i} 次：PASS ✅" || { echo "第 ${i} 次FAIL"; exit 1; }
    done

    step "observe" "⑤ 摘牌演示：修复后 remove 恢复全量监视（该用例失败会重新阻断）"
    "$PY" flaky_platform.py remove --test random_flake
    set +e
    "$PY" flaky_platform.py gate | tail -4
    set -e
    echo ">>> 验收：检出→隔离→主干 3 连绿→摘牌恢复监视 全闭环"
}

do_clean() {
    step "clean" "删隔离区/报告/共享状态标记"
    rm -rf reports tests/.shared_state tests/__pycache__ .pytest_cache __pycache__
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
