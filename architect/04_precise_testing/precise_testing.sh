#!/usr/bin/env bash
# =============================================================================
# precise_testing.sh — architect 04 主演示脚本：
# 建立覆盖档案 → 对 store.py 造一行真实变更 → 推荐最小回归集 → 还原 → 降级演示
# 变更通过 cp 备份 + trap 保证还原，工作区绝不留痕。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
STORE="$REPO/labs/11_sut_app/app/store.py"
BAK="$REPO/labs/11_sut_app/app/store.py.precise_bak"

step() { echo; echo "=====> [$1] $2"; }
cleanup() {  # 任何退出路径都还原 store.py、清掉备份
    if [ -f "$BAK" ]; then
        if ! cmp -s "$STORE" "$BAK" 2>/dev/null; then cp "$BAK" "$STORE"; fi
        rm -f "$BAK"
    fi
}
trap cleanup EXIT

do_apply() {
    step "apply" "① 依赖自检 + 建立覆盖档案（跑 labs/13 套件，--cov-context=test）"
    "$PY" -c "import yaml" 2>/dev/null || "$PY" -m pip install -q pyyaml
    "$PY" precise.py --refresh | tail -1
}

do_observe() {
    step "observe" "① 对 store.py 造一行真实变更（改 list_orders 的 limit 默认分支），git diff 可见"
    cp "$STORE" "$BAK"
    STORE_PATH="$STORE" "$PY" - <<'EOF'
import os
from pathlib import Path
p = Path(os.environ["STORE_PATH"])
src = p.read_text(encoding="utf-8")
# 选一条可执行语句做最小变更：真实修改，git diff 可见、coverage 有档案
needle = 'ORDER BY id DESC LIMIT ? OFFSET ?'
assert needle in src, "锚点行不存在"
src = src.replace(needle, 'ORDER BY id DESC LIMIT ? OFFSET ?  -- precise-demo', 1)
p.write_text(src, encoding="utf-8")
print("已修改 store.py 一行（--precise-demo 注释锚点）")
EOF
    git -C "$REPO" diff --stat -- labs/11_sut_app/app/store.py | tail -1

    step "observe" "② 精准推荐：变更行反查覆盖它的用例"
    "$PY" precise.py

    step "observe" "③ 验收核对：推荐集 ≤ 全量 50% 且都是真的碰过变更行的用例"
    "$PY" - <<'EOF'
import json
r = json.load(open("reports/recommendation.json", encoding="utf-8"))
n, total = len(r["recommended"]), r["total_suite"]
print(f"推荐 {n} / 全量 {total}（压缩 {r['shrink_pct']}%）；变更行 {len(r['changed_lines'])} 个；漏测行 {len(r['uncovered_lines'])}")
assert n <= total * 0.5, "推荐集超过全量 50%"
assert n >= 1, "推荐集为空（变更行应至少被一条用例覆盖）"
print("验收断言通过 ✅")
EOF

    step "observe" "④ 还原 store.py（trap 兜底）"
    cp "$BAK" "$STORE"; rm -f "$BAK"
    git -C "$REPO" diff --quiet -- labs/11_sut_app/app/store.py && echo "工作区已还原 ✅"

    step "observe" "⑤ 降级演示：删掉覆盖档案后，工具必须拒绝瞎推荐"
    rm -f "$REPO/labs/13_db_tests/.coverage"
    set +e
    "$PY" precise.py
    rc=$?
    set -e
    echo ">>> 降级退出码 = ${rc}（2 = 无数据，需全量；不许编推荐）"
}

do_clean() {
    step "clean" "删报告与覆盖档案缓存——目录回到实验前状态"
    rm -rf reports __pycache__ "$REPO/labs/13_db_tests/.coverage" "$REPO/labs/13_db_tests/.pytest_cache" "$REPO/labs/13_db_tests/tests/__pycache__"
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
