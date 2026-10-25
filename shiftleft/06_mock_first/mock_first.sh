#!/usr/bin/env bash
# =============================================================================
# mock_first.sh — shiftleft 06 主演示脚本：起挡板 → 消费方测试全绿 → 停挡板全红
#                 → schema 校验 → 注入演示 → provider 换装 payoff → 清理
# 挡板由 mock_server.py 从契约动态生成（provider 全程不参与前三步）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
MOCK_PORT=8934
PROVIDER_PORT=8935

step() { echo; echo "=====> [$1] $2"; }

wait_up() {  # 轮询健康端点而非裸 sleep
    for _ in $(seq 1 40); do
        curl -sf -m 2 "$1" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "服务未就绪：$1" >&2; return 1
}

start_mock() {
    ( "$PY" mock_server.py >/tmp/mock06.log 2>&1 & )
    wait_up "http://127.0.0.1:${MOCK_PORT}/api/health"
    echo "挡板就绪：http://127.0.0.1:${MOCK_PORT}（provider 从未启动）"
}

do_apply() {
    step "apply" "① 依赖自检（fastapi/uvicorn/pyyaml/httpx/jsonschema，幂等）"
    "$PY" -c "import fastapi, uvicorn, yaml, httpx, jsonschema" 2>/dev/null \
        && echo "依赖就绪" || "$PY" -m pip install -q fastapi uvicorn pyyaml httpx jsonschema
}

do_observe() {
    step "observe" "① 起挡板，5 条消费方测试打挡板全绿（provider 不存在）"
    start_mock
    "$PY" -m pytest tests/ -q 2>&1 | tail -1

    step "observe" "② 验收③：挡板每个响应逐操作对契约 schema 校验（jsonschema）"
    "$PY" validate_mock.py 2>/dev/null | tail -7

    step "observe" "③ 注入演示：X-Mock-Fault: 500 / X-Mock-Delay: 1（消费方容错分支的靶子）"
    curl -s -o /dev/null -w "注入 500 → HTTP %{http_code}\n" -H "X-Mock-Fault: 500" \
        "http://127.0.0.1:${MOCK_PORT}/api/health"
    curl -s -o /dev/null -w "注入 1s 延迟 → 耗时 %{time_total}s\n" -H "X-Mock-Delay: 1" \
        "http://127.0.0.1:${MOCK_PORT}/api/items"

    step "observe" "④ 验收②：停掉挡板，同样 5 条测试全红（预期失败——挡板是唯一依赖）"
    lsof -ti ":${MOCK_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 1
    "$PY" -m pytest tests/ -q 2>&1 | tail -1 || \
        echo ">>> 已按预期全红：没有挡板也没有 provider，消费方测试无处可打"

    step "observe" "⑤ payoff：项目 5 的 app_good 当 provider（8935），消费方测试零改动接真服务"
    ( cd "$REPO/shiftleft/05_contract_first" && \
      "$PY" -m uvicorn app_good:app --host 127.0.0.1 --port "${PROVIDER_PORT}" \
            --log-level warning >/tmp/provider06.log 2>&1 & )
    wait_up "http://127.0.0.1:${PROVIDER_PORT}/api/health"
    MOCK_BASE_URL="http://127.0.0.1:${PROVIDER_PORT}" "$PY" -m pytest tests/ -q 2>&1 | tail -1
    echo ">>> 挡板与真 provider 对消费方透明——这就是契约消费方先行的意义"
}

do_clean() {  # 摘两个端口 + 删缓存
    step "clean" "摘端口、删缓存——目录回到实验前状态"
    lsof -ti ":${MOCK_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    lsof -ti ":${PROVIDER_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .pytest_cache __pycache__ tests/__pycache__ reports 2>/dev/null || true
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
