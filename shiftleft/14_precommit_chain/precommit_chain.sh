#!/usr/bin/env bash
# =============================================================================
# precommit_chain.sh — shiftleft 14 主演示脚本：搭建独立链仓库 → 快层全绿实测 →
#                      坏提交真实阻断（证据留档）→ 重层手动触发 → 本地 vs CI 对比
# 门禁链编排 .pre-commit-config.yaml 复用项目 10/11/12 的检查引擎；labs/11 零接触。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
export PATH="$REPO/.venv/bin:$PATH"   # language: system 的钩子从这里找 ruff/semgrep/gitleaks
CHAIN="chain_repo"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pre-commit/ruff/mypy/semgrep/gitleaks，缺则补装）"
    command -v pre-commit >/dev/null || "$PY" -m pip install -q pre-commit
    "$PY" -c "import mypy" 2>/dev/null || "$PY" -m pip install -q mypy
    command -v semgrep >/dev/null || "$PY" -m pip install -q semgrep
    command -v gitleaks >/dev/null || brew install -q gitleaks
    echo "pre-commit $(pre-commit --version) / 四道检查引擎就绪"
}

build_chain_repo() {
    rm -rf "$CHAIN"
    mkdir -p "$CHAIN/rules"
    cp .pre-commit-config.yaml fixtures/clean_sample.py "$CHAIN/"
    cp ../12_sast_rules/rules/fastapi_rules.yaml "$CHAIN/rules/"
    ( cd "$CHAIN"
      git init -q -b main
      git config user.name precommit-chain
      git config user.email chain@local
      pre-commit install >/dev/null
      git add -A
      git -c user.name=precommit-chain -c user.email=chain@local \
          commit -qm "chore: 初始提交（干净样本）" )
}

do_observe() {
    mkdir -p reports   # 证据文件在第③步就要写，不能等第⑤步才建目录
    step "observe" "① 搭建独立链仓库并安装钩子（git commit 从此自动过门禁）"
    build_chain_repo
    echo "链仓库就绪：$CHAIN"

    step "observe" "② 验收①：快层全量实测（ruff+mypy+gitleaks，预期 <15s 全绿）"
    start=$SECONDS
    # 必须在链仓库内跑：pre-commit --all-files 的边界 = 所在 git 仓库，
    # 在外层仓库根跑会把 labs/performance 全库都拉进来扫
    ( cd "$CHAIN" && pre-commit run --all-files )
    echo ">>> 快层实测耗时 $((SECONDS - start))s（<15s 达标；精确口径见 measure.py）" 

    step "observe" "③ 验收②：提交含假密钥的文件 → git commit 被真实阻断（证据留档）"
    cp fixtures/bad_sample.py "$CHAIN/bad_sample.py"
    set +e
    # 不用 PIPESTATUS（bash 3.2 的 set -u 下不可靠）：先落文件再展示，退出码单独取
    ( cd "$CHAIN" && git add bad_sample.py \
        && git -c user.name=precommit-chain -c user.email=chain@local \
             commit -m "feat: 带着假密钥想混进来" ) > /tmp/commit_out.txt 2>&1
    bcode=$?
    cat /tmp/commit_out.txt | tee reports/blocked_evidence.txt >/dev/null
    set -e
    if [ "${bcode:-1}" -ne 0 ] && grep -q "gitleaks" reports/blocked_evidence.txt; then
        echo ">>> 已按预期阻断（exit ${bcode}，gitleaks 出手）——终端证据在 reports/blocked_evidence.txt"
    fi
    # 移走违禁文件并退出暂存区——只删工作区文件的话，staged blob 还会继续触发 gitleaks
    ( cd "$CHAIN" && git restore --staged bad_sample.py ) 2>/dev/null || true
    rm -f "$CHAIN/bad_sample.py"

    step "observe" "④ 验收③前置：重层手动触发（反模式检测 + semgrep SAST）"
    ( cd "$CHAIN" && pre-commit run --hook-stage manual --all-files ) 2>&1 \
        | grep -E "重层|Passed|Failed" | head -4 || true
    echo ">>> 重层不挡提交、按需深查——快重分层是反馈速度与覆盖面的平衡"

    step "observe" "⑤ 验收③：本地 vs CI 反馈延迟对比（快层实测 + 文档化估算口径）"
    "$PY" measure.py
}

do_clean() {  # 删链仓库与报告（每次重跑重建）
    step "clean" "删链仓库、报告与缓存——目录回到实验前状态"
    rm -rf "$CHAIN" reports .pytest_cache __pycache__ 2>/dev/null || true
    echo "已清理（labs/11 全程未被触碰）"
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
