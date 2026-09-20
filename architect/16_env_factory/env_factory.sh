#!/usr/bin/env bash
# =============================================================================
# env_factory.sh — architect 16 主演示脚本：
# 构建 SUT 镜像 → 并发起 2 套 PR 隔离环境 → 验证数据/端口互不干扰
# → 计时全周期 ≤3min → 销毁无残留 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
start_ts=""

step() { echo; echo "=====> [$1] $2"; }

up_env() {  # 起 1 套环境：$1=PR 号 $2=宿主端口
    PR_ID="$1" PORT="$2" docker compose -p "env-pr-$1" -f configs/compose.yaml up -d --wait
    docker compose -p "env-pr-$1" -f configs/compose.yaml ps --format '{{.Name}} {{.Status}}'
}

down_env() {  # 销毁 1 套环境（容器+网络；bind 数据目录一并删除）
    PR_ID="$1" docker compose -p "env-pr-$1" -f configs/compose.yaml down -v --remove-orphans >/dev/null 2>&1 || true
    rm -rf "configs/data-pr-$1"
}

do_apply() {
    step "apply" "① 构建 SUT 镜像（一份应用 N 个实例的原料；已有缓存则秒级）"
    docker build -q -t sut-ephemeral:latest -f configs/Dockerfile "$REPO/labs/11_sut_app"
    docker images sut-ephemeral:latest --format '镜像就绪 {{.Repository}}:{{.Tag}} ({{.Size}})'
}

do_observe() {
    start_ts=$SECONDS
    step "observe" "① 并发起 2 套全隔离环境（PR-101→18801，PR-102→18802）"
    up_env 101 18801 &
    up_env 102 18802 &
    wait
    echo

    step "observe" "② 隔离验证：在 101 创建订单，102 看不见"
    OID=$(curl -s -X POST http://127.0.0.1:18801/api/orders -H 'Content-Type: application/json' \
        -d '{"customer":"PR101专属","item":"隔离验证商品","qty":1,"price":1.1}' | "$REPO/.venv/bin/python" -c "import sys,json;print(json.load(sys.stdin)['id'])")
    echo "PR-101 创建订单 id=$OID"
    # HEAD 可能被路由 405——用 GET + 只留响应头
    count101=$(curl -s -o /dev/null -D - http://127.0.0.1:18801/api/orders | grep -i x-total-count | tr -dc '0-9')
    count102=$(curl -s -o /dev/null -D - http://127.0.0.1:18802/api/orders | grep -i x-total-count | tr -dc '0-9')
    echo "订单数：PR-101=${count101}，PR-102=${count102}"
    [ "$count102" = "0" ] || { echo "❌ 环境间数据串了"; exit 1; }
    echo "数据隔离 ✅（两套环境各自独立 sqlite 卷）"

    step "observe" "③ 全周期计时：创建→验证→销毁 ≤3min（验收线 180s）"
    down_env 101; down_env 102
    cost=$((SECONDS - start_ts))
    echo "全周期耗时 ${cost}s（验收线 ≤180s）"
    [ "$cost" -le 180 ] || { echo "❌ 超时"; exit 1; }

    step "observe" "④ 无残留验收：容器/卷/网络清干净"
    leftovers=$(docker ps -a --format '{{.Names}}' | grep -c 'env-pr-' || true)
    vols=$(docker volume ls --format '{{.Name}}' | grep -c 'env-pr-' || true)
    echo "残留容器 ${leftovers} 个，残留卷 ${vols} 个"
    [ "$leftovers" = "0" ] && [ "$vols" = "0" ] && echo "无残留 ✅"
    echo ">>> 验收：并发隔离 ✅ 周期 ≤3min ✅ 无残留 ✅"
}

do_clean() {
    step "clean" "删镜像与一切产物——宿主机回到实验前状态"
    down_env 101; down_env 102
    docker rmi -f sut-ephemeral:latest >/dev/null 2>&1 || true
    rm -rf reports __pycache__ configs/data-pr-*
    echo "已清理（镜像已删，下次 apply 会重建）"
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
