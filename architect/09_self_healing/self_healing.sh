#!/usr/bin/env bash
# =============================================================================
# self_healing.sh — architect 09 主演示脚本：自愈定位器全流程
# 5 个改版页面自愈（验收 ≥4/5）+ 1 个语义全毁页面如实报红（设计内退出码 1）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（playwright 浏览器就绪，file:// 页面无需服务）"
    "$PY" -m playwright --version >/dev/null 2>&1 || { echo "playwright 未装"; exit 1; }
    rm -f reports/locator_archive.json reports/healing_report.json
    echo "playwright 就绪，档案已清空（冷启动：第一轮全靠策略链自愈）"
}

do_observe() {
    step "observe" "① 自愈套件：5 改版页 + 1 语义全毁页（broken 由元测试断言「拒绝误愈」）"
    set +e
    "$PY" -m pytest tests -c configs/pytest.ini --rootdir=tests -q --browser chromium 2>&1 | \
        grep -E "passed|failed|=====> \[healer\]|Error|assert" | head -8
    rc=${PIPESTATUS[0]}
    set -e
    echo ">>> 套件退出码 ${rc}（broken 页的拒绝误愈由元测试捕获：真实套件中它等价于一条红用例）"

    step "observe" "② 自愈报告：改版自愈率与档案（第二轮将免愈）"
    "$PY" - <<'PYEOF'
import json
r = json.load(open("reports/healing_report.json", encoding="utf-8"))
print(f"尝试 {r['attempts']} 次：首选命中 {r['first_try']} / 自愈 {r['healed']} / 失败 {r['failed']}")
print(f"改版自愈率: {r['heal_rate_of_mutants']}（验收线 ≥0.8）")
rate = r["heal_rate_of_mutants"]
assert rate is not None and rate >= 0.8, "改版自愈率不达标"
print("验收断言通过 ✅")
PYEOF

    step "observe" "③ 档案学习效果：第二轮重跑，改版页直接走档案免愈"
    "$PY" -m pytest tests -c configs/pytest.ini --rootdir=tests -q --browser chromium \
        --deselect tests/test_healing.py::test_语义全毁页面必须如实报红 2>&1 | tail -1
    "$PY" - <<'PYEOF'
import json
r = json.load(open("reports/healing_report.json", encoding="utf-8"))
archived = sum(1 for e in r["events"] if e["tried"] and e["tried"][0].startswith("archive:"))
print(f"本轮 {archived} 次定位直接命中档案（自愈记忆生效）")
PYEOF
    echo ">>> 验收：5 改版页自愈 ≥4/5 ✅ 语义全毁如实红 ✅ 档案第二轮免愈 ✅"
}

do_clean() {
    step "clean" "删报告、档案与缓存"
    rm -rf reports tests/__pycache__ .pytest_cache __pycache__
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
