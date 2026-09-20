#!/usr/bin/env bash
# =============================================================================
# pipeline_tiers.sh — architect 10 主演示脚本：
# act 本地复跑 tier1 快反馈层（与 CI 同源）+ 冒烟比例验收 + 三层语义说明
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
WF="architect/10_pipeline_tiers/workflows/architect-tiers.yml"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 硬前置自检：git 仓库（act 依赖）+ docker daemon + act CLI"
    git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null && echo "git 仓库 ✅"
    docker info --format 'docker daemon ✅'
    command -v act >/dev/null && echo "act $(act --version | head -1 | awk '{print $NF}') ✅"
    "$PY" -c "import yaml; yaml.safe_load(open('$REPO/$WF')); print('workflow yaml ✅')"
}

do_observe() {
    step "observe" "① act 本地复跑 tier1 快反馈层（Docker 内执行，与 CI 同源；首跑拉镜像较慢）"
    local t0=$SECONDS
    set +e
    # --pull=false：本地已有镜像缓存（labs/30 首跑已拉），绕开镜像源抽风
    # (cd $REPO)：act 以 cwd 为项目根——工作区必须挂仓库根，working-directory 才成立
    ( cd "$REPO" && act -W "$WF" -j tier1-quick-feedback --pull=false \
        -P ubuntu-latest=catthehacker/ubuntu:act-latest push 2>&1 | \
        grep -E "✅|❌|Success|Failure|tier1|passed|error" | head -14 )
    local rc=${PIPESTATUS[0]}
    set -e
    local cost=$((SECONDS - t0))
    echo ">>> act 退出码 ${rc}，tier1 耗时 ${cost}s（验收线 <300s）"

    step "observe" "② 冒烟层比例验收：smoke 圈选 ≤ 全量 20% 且覆盖 P0 下单路径"
    ( cd "$REPO/labs/13_db_tests"
      # -o addopts= 清掉 ini 自带的 -q，collect 输出恢复「N tests collected」汇总行
      total=$("$PY" -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q -o addopts= 2>/dev/null | grep -oE '[0-9]+ tests? collected' | grep -oE '[0-9]+')
      # -k 圈选在 collect-only 下摘要形如「2/10 collected」——直接数 :: 节点行最稳
      smoke=$("$PY" -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q -o addopts= -k "create_and_get_fresh or init_db_repeatable" 2>/dev/null | grep -c "::")
      echo "smoke=$smoke / 全量=$total"
      "$PY" - <<PYEOF
total, smoke = $total, $smoke
assert smoke <= total * 0.2, f"冒烟层占比超标: {smoke}/{total}"
print(f"冒烟占比 {smoke/total:.0%} ≤ 20% ✅")
PYEOF
      "$PY" -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q -o addopts= -k "create_and_get_fresh" 2>/dev/null | grep -m1 "create_and_get_fresh" >/dev/null \
        && echo "P0 下单路径在冒烟层 ✅"
    )

    step "observe" "③ 三层语义速览（定义见 workflows/architect-tiers.yml）"
    grep -E "name: \"tier" "$REPO/$WF"
    echo ">>> 验收：act 跑通 tier1 且 <5min；冒烟 ≤20% 且含 P0 路径"
}

do_clean() {
    step "clean" "删运行产物"
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
