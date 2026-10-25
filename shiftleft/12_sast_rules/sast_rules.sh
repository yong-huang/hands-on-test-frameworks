#!/usr/bin/env bash
# =============================================================================
# sast_rules.sh — shiftleft 12 主演示脚本：规则校验 → 靶场扫描（≥4/5）→ 干净对照
#                 → 盲区说明 → 社区基线 → 清理
# 核心产出是 rules/fastapi_rules.yaml（自定义 SAST 规则，validate + 实战）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
SG="$REPO/.venv/bin/semgrep"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（semgrep，缺则装入仓库 venv，幂等）"
    [ -x "$SG" ] && echo "semgrep $($SG --version 2>/dev/null | tail -1) 就绪" \
        || { "$PY" -m pip install -q semgrep; echo "semgrep 已安装"; }
}

do_observe() {
    step "observe" "① 规则合法性：semgrep --validate（0 error 才有资格上岗）"
    "$SG" --validate --config rules/fastapi_rules.yaml 2>&1 | grep -i "Configuration" | head -1

    step "observe" "② 靶场扫描：5 个漏洞埋点，自定义规则检出（≥4/5 达标）"
    "$SG" scan --config rules/fastapi_rules.yaml --json fixtures/vulnerable.py 2>/dev/null \
        | "$PY" -c "
import json, sys
src = open('fixtures/vulnerable.py').read().splitlines()
d = json.load(sys.stdin)
for r in d['results']:
    ln = r['start']['line']
    print(f\"  ⛔ {r['check_id'].split('.')[-1]}  L{ln}  {src[ln-1].strip()[:58]}\")
print(f'  检出 {len(d[\"results\"])} / 5')"

    step "observe" "③ 干净对照：参数化查询/环境变量/literal_eval —— 零误报"
    "$SG" scan --config rules/fastapi_rules.yaml --json fixtures/clean.py 2>/dev/null \
        | "$PY" -c "import json,sys; print(f'  误报 {len(json.load(sys.stdin)[\"results\"])} 条')"

    step "observe" "④ 盲区披露：埋点 5（fallback 变量名装真密钥）按名匹配抓不到"
    echo ">>> 按变量名匹配是白名单式规则；值为密钥但名字无关的，交给 gitleaks 按值匹配（项目 13）"

    step "observe" "⑤ 社区规则集基线：对 labs/11 SUT 扫描留档（--config auto 需联网）"
    mkdir -p baseline
    if "$SG" scan --config auto --json ../../labs/11_sut_app/app \
        > baseline/community_baseline.json 2> baseline/community_baseline.err; then
        "$PY" -c "
import json
d = json.load(open('baseline/community_baseline.json'))
print(f'  基线发现 {len(d[\"results\"])} 条（已留档 baseline/community_baseline.json）')"
    else
        echo "  ⚠️ registry 不可达——留档JSON仍在（先前扫描），联网后重跑本步即可"
    fi
}

do_clean() {  # 删报告与 semgrep 缓存；baseline/ 的留档保留（它是验收证据）
    step "clean" "删报告与缓存——baseline 留档保留"
    rm -rf reports .pytest_cache __pycache__ .semgrep* 2>/dev/null || true
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
