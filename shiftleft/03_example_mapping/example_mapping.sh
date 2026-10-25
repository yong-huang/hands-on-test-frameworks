#!/usr/bin/env bash
# =============================================================================
# example_mapping.sh — shiftleft 03 主演示脚本：依赖自检 → 干净故事转化与校验 →
#                      脏故事告警演示 → 产物清点 → 清理
# 转化引擎在 example_mapping.py，gherkin 校验复用 cucumber/ 共享的官方解析器。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pyyaml + node + gherkin 42 可达，幂等）"
    "$PY" -c "import yaml" 2>/dev/null && echo "pyyaml 就绪" || "$PY" -m pip install -q pyyaml
    node validate_feature.mjs /dev/null >/dev/null 2>&1 && true
    node -e "import('../../cucumber/node_modules/@cucumber/gherkin/dist/index.js').then(()=>console.log('gherkin 42 就绪'))"
}

do_observe() {
    step "observe" "① 干净故事（3 规则 6 例子）→ feature + 疑问清单 → 官方解析器校验"
    "$PY" example_mapping.py --story configs/story_clean.yaml
    node validate_feature.mjs reports/US-201.feature

    step "observe" "② 看一眼骨架：规则→场景大纲，例子→Examples 表"
    sed -n '1,14p' reports/US-201.feature

    step "observe" "③ 未决问题清单：逐条带 owner 占位与状态，评审会现场认领"
    cat reports/US-201-questions.md

    step "observe" "④ 脏故事演示：空规则 + 无例子 → 两条告警，strict 模式退出码 1（预期失败）"
    "$PY" example_mapping.py --story configs/story_dirty.yaml --strict || \
        echo ">>> 已按预期退出非零：卡片没画完的故事不能进迭代"
    node validate_feature.mjs reports/US-202.feature   # 脏故事的骨架照样结构合法

    step "observe" "⑤ 产物清点"
    ls -l reports/
    echo ">>> feature 喂给 cucumber 线即可执行（步骤实现不在本实验范围）；问题清单留评审会认领"
}

do_clean() {  # 删产物与缓存，无进程残留（本实验不起服务）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports __pycache__ 2>/dev/null || true
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
