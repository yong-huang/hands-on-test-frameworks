#!/usr/bin/env bash
# =============================================================================
# config_drift.sh — architect 17 主演示脚本：
# 三环境全绿 → 变异（staging 删必填字段 + prod-like 改 invariant 字段）→ 拦截与漂移 → 清理
# 变异只写 reports/ 副本，原始配置永远不动。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检 + 基线：三环境对 schema 全部合规"
    "$PY" -c "import yaml" 2>/dev/null || "$PY" -m pip install -q pyyaml
    "$PY" drift.py
}

do_observe() {
    step "observe" "① 基线矩阵：差异全部落在 expected_diff 白名单内"
    grep -E "疑似漂移|预期差异|共 .* 处差异" reports/drift.md | tail -2

    step "observe" "② 变异演示：staging 删掉必填字段 database.url；prod-like 的重试次数被手改成 9（invariant 漂移）"
    mkdir -p reports/mutated
    cp configs/environments/*.yaml reports/mutated/
    "$PY" - <<'PYEOF'
import yaml
p = "reports/mutated/staging.yaml"
d = yaml.safe_load(open(p, encoding="utf-8"))
del d["database"]["url"]                      # 删必填字段
yaml.safe_dump(d, open(p, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
p2 = "reports/mutated/prod-like.yaml"
d2 = yaml.safe_load(open(p2, encoding="utf-8"))
d2["retry"]["max_attempts"] = 9               # invariant 漂移（三环境必须一致的字段）
yaml.safe_dump(d2, open(p2, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
print("已变异：staging 缺 database.url；prod-like retry.max_attempts=9")
PYEOF
    set +e
    "$PY" drift.py --env-dir reports/mutated --out reports/mutated
    rc=$?
    set -e
    echo ">>> 变异后退出码 ${rc}（1 = 校验拦截）"

    step "observe" "③ 拦截与漂移证据：字段名点名 + 疑似漂移标注"
    grep -E "缺少必填字段|疑似漂移" reports/mutated/drift.md | head -6

    step "observe" "④ strict 模式：连「预期差异之外的一切」都零容忍"
    "$PY" drift.py --strict | tail -1
    echo ">>> 验收：删必填字段被点名拦截 ✅ invariant 漂移被标注 ✅ 原始配置全程未动"
}

do_clean() {
    step "clean" "删报告与变异副本"
    rm -rf reports __pycache__ .pytest_cache
    echo "已清理（configs/ 原始配置全程未动）"
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
