#!/usr/bin/env bash
# =============================================================================
# incremental_selector.sh — architect 12 主演示脚本：
# 对 store.py 造真实变更 → 静态选择（理由链）→ 无关不选断言 → 与项目 4 运行时对比 → 还原
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
STORE="$REPO/labs/11_sut_app/app/store.py"
BAK="$STORE.selector_bak"

step() { echo; echo "=====> [$1] $2"; }
cleanup() {
    if [ -f "$BAK" ]; then
        cmp -s "$STORE" "$BAK" 2>/dev/null || cp "$BAK" "$STORE"
        rm -f "$BAK"
    fi
}
trap cleanup EXIT

do_apply() {
    step "apply" "① 扫描全仓建 AST import 注册表（零执行，毫秒级）"
    "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, ".")
from selector import scan
registry, tests = scan()
print(f"注册 {len(registry)} 个模块名，候选测试/conftest {len(tests)} 个")
PYEOF
}

do_observe() {
    step "observe" "① 对 store.py 造真实变更（备份 + trap 还原）"
    cp "$STORE" "$BAK"
    STORE_PATH="$STORE" "$PY" - <<'PYEOF'
import os
from pathlib import Path
p = Path(os.environ["STORE_PATH"])
src = p.read_text(encoding="utf-8")
needle = "ORDER BY id DESC LIMIT ? OFFSET ?"
assert needle in src
p.write_text(src.replace(needle, needle + "  -- selector-demo", 1), encoding="utf-8")
print("store.py 已变更 1 行")
PYEOF

    step "observe" "② 静态选择：选中直接/间接 import store 的测试，附理由链"
    "$PY" selector.py

    step "observe" "③ 验收断言：相关测试选中、无关测试不选"
    "$PY" - <<'PYEOF'
import json
sel = json.load(open("reports/selection.json", encoding="utf-8"))["selected"]
joined = "\n".join(sel)
assert any(s.startswith("labs/13_db_tests") for s in sel), "labs/13 直接 import store 却未选中"
unrelated = [s for s in sel if s.startswith(("labs/02_", "labs/05_", "labs/06_"))]
assert not unrelated, f"无关模块测试被误选: {unrelated}"
print(f"选中 {len(sel)} 条；labs/13（直接 import store）在列 ✅；无关 labs（02/05/06）未误选 ✅")
PYEOF

    step "observe" "④ 还原 store.py，引用项目 4 的运行时推荐做两路线对比"
    cleanup
    trap - EXIT
    ( cd ../04_precise_testing && ./precise_testing.sh apply >/dev/null 2>&1 )
    cp "$STORE" "$BAK"
    trap cleanup EXIT
    STORE_PATH="$STORE" "$PY" - <<'PYEOF'
import os
from pathlib import Path
p = Path(os.environ["STORE_PATH"])
src = p.read_text(encoding="utf-8")
p.write_text(src.replace("ORDER BY id DESC LIMIT ? OFFSET ?",
                         "ORDER BY id DESC LIMIT ? OFFSET ?  -- selector-demo", 1), encoding="utf-8")
print("store.py 重新变更（对比运行时路线需要同一变更）")
PYEOF
    # 运行时路线先对同一变更出推荐（项目 4）
    ( cd ../04_precise_testing && "$PY" precise.py >/dev/null )
    "$PY" selector.py --compare-p4 | sed -n '/与运行时路线/,$p' | head -8
    echo ">>> 验收：相关选中/无关不选/理由链/两路线对比 全部落地"
}

do_clean() {
    step "clean" "删报告与缓存（store.py 由 trap 保证还原）"
    cleanup
    rm -rf reports __pycache__ .pytest_cache
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
