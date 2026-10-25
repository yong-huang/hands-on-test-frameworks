#!/usr/bin/env bash
# =============================================================================
# scan.sh — shiftleft 13 主演示脚本：一条命令复现全部四项验收——
#   ① CVE 靶场（pip-audit 报 CVE 编号、退出码非零）
#   ② 干净依赖基线（零告警）
#   ③ 密钥泄漏靶场（gitleaks 报红）④ 干净密钥对照（零告警）
# 全部发现以 JSON/文本留档 reports/。工具：pip-audit + gitleaks。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
BIN="$REPO/.venv/bin"
OUT="reports"
mkdir -p "$OUT"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pip-audit 入 venv、gitleaks 在 PATH，缺则补装）"
    "$BIN/pip-audit" --version >/dev/null 2>&1 || "$PY" -m pip install -q pip-audit
    command -v gitleaks >/dev/null || brew install -q gitleaks
    echo "pip-audit $("$BIN/pip-audit" --version) / gitleaks $(gitleaks version)"
}

do_observe() {
    step "observe" "① CVE 靶场：钉住 requests==2.19.1，pip-audit -s osv 报出 CVE 编号（预期退出码非零）"
    set +e
    "$BIN/pip-audit" -r fixtures/requirements_vuln.txt -s osv --aliases on \
        --format json -o "$OUT/pip_audit_vuln.json"
    vcode=$?
    set -e
    vcve=$(grep -o "CVE-[0-9-]*" "$OUT/pip_audit_vuln.json" | sort -u | head -4 | tr '\n' ' ')
    if [ -n "${vcve}" ]; then
        echo "  ⛔ 退出码 ${vcode}（非零即为红）；CVE 编号样例：${vcve}"
    fi

    step "observe" "② 干净依赖基线：requests==2.33.0，零告警（预期退出码 0）"
    set +e
    "$BIN/pip-audit" -r fixtures/requirements_clean.txt -s osv --aliases on \
        --format json -o "$OUT/pip_audit_clean.json"
    ccode=$?
    set -e
    if [ "${ccode}" -eq 0 ]; then
        echo "  ✅ 退出码 0，无已知漏洞"
    fi

    step "observe" "③ 密钥泄漏靶场：AWS 文档示例密钥埋点，gitleaks 报红（预期退出码非零）"
    set +e
    gitleaks detect --no-git --source secrets --report-format json \
        --report-path "$OUT/gitleaks.json" --redact >/dev/null 2>&1
    gcode=$?
    set -e
    gcount=$("$PY" -c "import json;print(len(json.load(open('$OUT/gitleaks.json'))))" 2>/dev/null || echo 0)
    if [ "${gcode}" -ne 0 ]; then
        echo "  ⛔ 退出码 ${gcode}（非零即为红）；gitleaks 命中 ${gcount} 处泄漏"
    fi

    step "observe" "④ 干净密钥对照：凭据全部来自环境变量，零告警（预期退出码 0）"
    set +e
    gitleaks detect --no-git --source secrets/clean.py \
        --report-format json --report-path "$OUT/gitleaks_clean.json" --redact >/dev/null 2>&1
    gclean=$?
    set -e
    if [ "${gclean}" -eq 0 ]; then
        echo "  ✅ 退出码 0，零告警"
    fi

    step "observe" "⑤ 四项验收汇总"
    {
        echo "① CVE 靶场退出码 ${vcode}（非零即红），CVE 编号样例：${vcve}"
        echo "② 干净依赖基线退出码 ${ccode}（应为 0）"
        echo "③ gitleaks 靶场退出码 ${gcode}（非零即红），命中 ${gcount} 处"
        echo "④ 干净密钥对照退出码 ${gclean}（应为 0）"
    } | tee "$OUT/acceptance_summary.txt"
    echo ">>> 全部留档在 reports/（pip_audit_*.json、gitleaks*.json、acceptance_summary.txt）"
}

do_clean() {  # 删报告与 pip-audit 临时环境（secrets/fixtures 是源码保留）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ 2>/dev/null || true
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
