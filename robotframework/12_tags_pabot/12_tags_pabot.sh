#!/usr/bin/env bash
# 12_tags_pabot.sh — 项目 12：标签策略与套件编排（--include / pabot 并行 / --rerunfailed + rebot 合并）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"
export PATH="$SERIES/../.venv/bin:$PATH"    # pabot/rebot 子进程要能找到 robot 可执行文件

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    local out="$PWD/reports"
    rm -rf "$out"; mkdir -p "$out"

    step "observe" "① 标签选择：--include smoke 只跑冒烟"
    "$PY" -m robot --include smoke --outputdir "$out/tag_smoke" --log none --report none suites/ >/dev/null
    "$PY" - "$out/tag_smoke/output.xml" <<'EOF'
import sys
from xml.etree import ElementTree as ET
st = ET.parse(sys.argv[1]).getroot().find(".//statistics/total/stat")
print(f"    smoke 标签筛出 {st.attrib['pass']} 条，全过")
EOF

    step "observe" "② pabot 并行跑全量（7 条小套件，如实标注并行开销）"
    local t0 t1 serial parallel
    t0=$(date +%s)
    "$PY" -m robot --outputdir "$out/serial" --log none --report none suites/ >/dev/null
    t1=$(date +%s); serial=$((t1 - t0))
    pabot --processes 3 --outputdir "$out/parallel" --log none --report none suites/ >/dev/null
    t1=$(date +%s); parallel=$((t1 - t0))
    echo "    串行 ${serial}s vs pabot 并行 ${parallel}s（小套件下进程启动开销占主导——"
    echo "    并行的收益随用例数线性放大，套件越大越划算，7 条只能验证机制不能验证提速）"

    step "observe" "③ 失败重跑 + rebot 合并（INJECT=1 注 1 红 → 修好重跑 → 合并全绿）"
    INJECT=1 "$PY" -m robot --outputdir "$out/first" --log none --report none suites/ >/dev/null 2>&1 || true
    echo "    首轮：$("$PY" - "$out/first/output.xml" <<'EOF'
import sys
from xml.etree import ElementTree as ET
st = ET.parse(sys.argv[1]).getroot().find(".//statistics/total/stat")
print(f"pass={st.attrib['pass']} fail={st.attrib['fail']}", end="")
EOF
)（注入 1 条预期红）"

    INJECT=0 "$PY" -m robot --rerunfailed "$out/first/output.xml" --outputdir "$out/rerun" --log none --report none suites/ >/dev/null
    echo "    重跑：--rerunfailed 只选中失败用例（$("$PY" - "$out/rerun/output.xml" <<'EOF'
import sys
from xml.etree import ElementTree as ET
print(ET.parse(sys.argv[1]).getroot().find(".//statistics/total/stat").attrib["pass"], end="")
EOF
) 条，全部通过）"

    rebot -R --output merged.xml --outputdir "$out" "$out/first/output.xml" "$out/rerun/output.xml" >/dev/null 2>&1 || true
    "$PY" - "$out/merged.xml" <<'EOF'
import sys
from xml.etree import ElementTree as ET
st = ET.parse(sys.argv[1]).getroot().find(".//statistics/total/stat")
print(f"    合并后：pass={st.attrib['pass']} fail={st.attrib['fail']}")
assert st.attrib["fail"] == "0", "合并后应全绿"
print("    ✅ 标签选择 / 并行机制 / 重跑合并 三项验收通过")
EOF
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf reports
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
